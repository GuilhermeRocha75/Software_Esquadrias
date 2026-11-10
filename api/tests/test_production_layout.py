import copy
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import sys
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient
from PIL import Image
from pydantic import ValidationError

from api.app.main import app, _production_image_store
from api.app.production_images import (
    ImageSelector, ProductionImageManifest, ProductionImageStore, StoredProductionImage,
    finish_identity, model_identity, image_metadata, import_legacy_images,
)
from api.app.production_layout import (
    ProductionLayoutContext, ProductionLayoutDocument, build_production_layout,
)
from api.app.production_schemas import ProductionOrderRequest
from api.app.production_service import build_production_order, canonical_json
from tools.compare_op_layout import build_report, compare_layout_case
from tools.audit_op_layout_sources import technical_pdf_rows

COMPANY = UUID("00000000-0000-0000-0000-000000000001")
FIXTURES = Path(__file__).parent / "fixtures"
REFERENCES = json.loads((FIXTURES / "op_layout_reference_v1.json").read_text(encoding="utf-8"))["cases"]
INPUTS = {r["id"]: r for r in json.loads((FIXTURES / "op_reference_inputs.json").read_text(encoding="utf-8"))["cases"]}


def request(case_id="OP-GOLDEN-01"):
    source = INPUTS[case_id]
    return ProductionOrderRequest(company_id=COMPANY, order_id="ANON", items=[{
        "item_id": case_id, "finish_key": source["finish_key"], "technical_input": source["technical_input"]}])


def context(**overrides):
    return ProductionLayoutContext(company_id=COMPANY, **overrides)


def raster():
    # Format-only test raster; never a production sketch or a committed asset.
    buffer = BytesIO()
    Image.new("RGB", (3, 2), "white").save(buffer, "JPEG")
    return buffer.getvalue()


def entry(selector, data, policy="EXACT", path=None):
    digest = hashlib.sha256(data).hexdigest()
    media, width, height = image_metadata(data)
    return StoredProductionImage(selector=selector, relative_path=path or f"objects/{digest}.jpg", sha256=digest,
                                 media_type=media, width_px=width, height_px=height, finish_policy=policy)


def store_in(root, entries, company=COMPANY):
    return ProductionImageStore(root, ProductionImageManifest(company_id=company,
          source_workbook_sha256="a" * 64, entries=tuple(entries)))


class ImageIdentityTests(unittest.TestCase):
    def test_image_key_excludes_sizes_quantity_prices_glass_and_hardware(self):
        inputs = request().items[0].technical_input.model_dump(mode="json")
        changed = copy.deepcopy(inputs)
        changed.update(width_mm=4000, height_mm=2800, quantity=3, glass_description="06mm FLOAT INCOLOR", roller_description="ROLDANA 80KG")
        self.assertEqual(model_identity(inputs, "BRANCO"), model_identity(changed, "BRANCO"))

    def test_model_shape_and_finish_are_distinct(self):
        inputs = request().items[0].technical_input.model_dump(mode="json")
        key, white = model_identity(inputs, "BRANCO")
        other, _ = model_identity({**inputs, "screen_enabled": False}, "BRANCO")
        self.assertNotEqual(key, other)
        self.assertNotEqual(white, model_identity(inputs, "PRETO")[1])
        self.assertEqual(finish_identity(" branco "), "BRANCO")

    def test_minimal_and_effective_inputs_have_same_identity(self):
        minimal = {"family": "FX", "width_mm": 1200, "height_mm": 1000}
        effective = ProductionOrderRequest(company_id=COMPANY, order_id="FX", items=[{"item_id": "FX", "technical_input": minimal}]).items[0].technical_input.model_dump(mode="json")
        self.assertEqual(model_identity(minimal, "BRANCO"), model_identity(effective, "BRANCO"))

    def test_model_name_rejects_path_in_finish_and_unknown_profile(self):
        for color in ("C:/Users/client", "../BRANCO", "BRANCO\nCLIENT"):
            with self.subTest(color=color), self.assertRaises(ValueError):
                model_identity(request().items[0].technical_input.model_dump(mode="json"), color)
        for code in ("0", "UNKNOWN", None):
            with self.subTest(code=code), self.assertRaises(ValidationError):
                ImageSelector(kind="PROFILE_SECTION", code=code)

    def test_fixo_source_basename_is_exact(self):
        _, name = model_identity({"family": "FX", "width_mm": 1200, "height_mm": 1000}, "BRANCO")
        self.assertEqual(name, "PAINEL  FIXO - 00 (BRANCO).jpg")

    def test_explicit_no_shutter_does_not_select_a_shutter_sketch(self):
        inputs = request().items[0].technical_input.model_dump(mode="json")
        inputs.update(shutter_enabled=True, shutter={"mode": "SEM PERSIANA"})
        _, name = model_identity(inputs, "BRANCO")
        self.assertNotIn("COM PERSIANA", name)

    def test_verified_bytes_detect_tampering_and_deleted_files(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = entry(ImageSelector(kind="PROFILE_SECTION", code="PR8852"), raster(), "NEUTRAL_LEGACY_SECTION")
            path = root / image.relative_path
            path.parent.mkdir()
            path.write_bytes(raster())
            store = store_in(root, [image])
            selector = ImageSelector(kind="PROFILE_SECTION", code="PR8852", finish_key="BRANCO")
            self.assertEqual(store.resolve(selector, COMPANY).status, "VERIFIED")
            path.write_bytes(b"corrupted")
            self.assertEqual(store.resolve(selector, COMPANY).status, "INVALID_ASSET")
            path.unlink()
            self.assertEqual(store.resolve(selector, COMPANY).status, "INVALID_ASSET")

    def test_model_never_falls_back_to_another_finish_or_company(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            white = entry(ImageSelector(kind="MODEL_SKETCH", model_key="CR/example", finish_key="BRANCO"), raster())
            (root / "objects").mkdir()
            (root / white.relative_path).write_bytes(raster())
            store = store_in(root, [white])
            self.assertEqual(store.resolve(ImageSelector(kind="MODEL_SKETCH", model_key="CR/example", finish_key="PRETO"), COMPANY).status, "MISSING_ASSET")
            with self.assertRaises(ValueError):
                store.resolve(white.selector, UUID(int=2))

    def test_only_explicit_neutral_policy_allows_cross_finish_sections(self):
        neutral = ImageSelector(kind="PROFILE_SECTION", code="PR8852")
        with self.assertRaises(ValidationError):
            entry(neutral, raster(), "EXACT")
        with self.assertRaises(ValidationError):
            entry(ImageSelector(kind="MODEL_SKETCH", model_key="CR/test", finish_key="BRANCO"), raster(), "NEUTRAL_LEGACY_SECTION")

    def test_duplicate_selectors_invalid_path_format_and_hash_are_rejected(self):
        image = entry(ImageSelector(kind="MODEL_SKETCH", model_key="CR/test", finish_key="BRANCO"), raster())
        with self.assertRaises(ValidationError):
            ProductionImageManifest(company_id=COMPANY, source_workbook_sha256="a" * 64, entries=(image, image))
        for path in ("../a.jpg", "/a.jpg", "C:/Users/client/a.jpg", "objects/a\n.jpg"):
            with self.subTest(path=path), self.assertRaises(ValidationError):
                StoredProductionImage.model_validate({**image.model_dump(), "relative_path": path})
        with self.assertRaises(ValueError):
            image_metadata(b"<svg>not a raster</svg>")
        with self.assertRaises(ValueError):
            image_metadata(b"")

    def test_image_dimensions_are_checked_against_bytes(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = entry(ImageSelector(kind="PROFILE_SECTION", code="PR8852"), raster(), "NEUTRAL_LEGACY_SECTION")
            (root / "objects").mkdir()
            (root / image.relative_path).write_bytes(raster())
            changed = image.model_copy(update={"width_px": 99})
            self.assertEqual(store_in(root, [changed]).resolve(image.selector, COMPANY).status, "INVALID_ASSET")

    def test_private_import_copies_exact_bytes_reports_missing_and_deduplicates(self):
        with TemporaryDirectory() as tmp:
            source, dest = Path(tmp) / "source", Path(tmp) / "dest"
            (source / "CROQUIS").mkdir(parents=True)
            (source / "CROQUIS_PERFIS").mkdir()
            name = "JANELA 2 FOLHAS DE CORRER (BRANCO).jpg"
            (source / "CROQUIS" / name).write_bytes(raster())
            (source / "CROQUIS_PERFIS/PR8852.jpg").write_bytes(raster())
            selector = ImageSelector(kind="MODEL_SKETCH", model_key="CR/test", finish_key="BRANCO")
            manifest, missing = import_legacy_images(source, dest, COMPANY, "a" * 64,
                               ((selector, name), (selector, name)), ("PR8852", "PR4266"))
            self.assertEqual(len(manifest.entries), 2)
            self.assertEqual(len(missing), 1)
            self.assertEqual(len(list((dest / "objects").iterdir())), 1)
            for image in manifest.entries:
                self.assertEqual(store_in(dest, manifest.entries).read_verified(image), raster())

    def test_import_rejects_public_destination_and_source_traversal(self):
        with TemporaryDirectory() as tmp:
            source = Path(tmp)
            public = Path(__file__).resolve().parents[2] / "web/public/op-test-import"
            with self.assertRaises(ValueError):
                import_legacy_images(source, public, COMPANY, "a" * 64, (), ())
            selector = ImageSelector(kind="MODEL_SKETCH", model_key="CR/test", finish_key="BRANCO")
            with TemporaryDirectory() as destination:
                with self.assertRaises(ValueError):
                    import_legacy_images(source, Path(destination), COMPANY, "a" * 64, ((selector, "../image.jpg"),), ())

    def test_git_ignores_private_imports_and_original_documents(self):
        paths = [".private/op-b1/images/manifest.json", ".private/op-b1/images/objects/test.jpg", "private-customer.pdf", "private-source.xlsm", "private-archive.rar"]
        root = Path(__file__).resolve().parents[2]
        ignored = subprocess.check_output(["git", "check-ignore", "--no-index", "--", *paths], cwd=root, text=True).splitlines()
        self.assertEqual(ignored, paths)

    def test_symlink_escape_from_image_store_is_rejected(self):
        with TemporaryDirectory() as tmp:
            root, outside = Path(tmp) / "root", Path(tmp) / "outside"
            root.mkdir()
            outside.mkdir()
            image = entry(ImageSelector(kind="PROFILE_SECTION", code="PR8852"), raster(), "NEUTRAL_LEGACY_SECTION")
            (outside / Path(image.relative_path).name).write_bytes(raster())
            try:
                (root / "objects").symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("Windows sem privilégio para criar symlink; CI Linux executa esta verificação.")
            self.assertEqual(store_in(root, [image]).resolve(image.selector, COMPANY).status, "INVALID_ASSET")
            source = Path(tmp) / "source"
            (source / "CROQUIS_PERFIS").mkdir(parents=True)
            (source / "CROQUIS_PERFIS/PR8852.jpg").write_bytes(raster())
            before = (outside / Path(image.relative_path).name).read_bytes()
            with self.assertRaises(ValueError):
                import_legacy_images(source, root, COMPANY, "a" * 64, (), ("PR8852",))
            self.assertEqual((outside / Path(image.relative_path).name).read_bytes(), before)


class LayoutAssemblyTests(unittest.TestCase):
    def test_private_header_dimensions_and_item_identity_are_assembled(self):
        technical = build_production_order(request("OP-GOLDEN-06"))
        ctx = context(client_code="TEST-CLIENT", client_name="CLIENTE DE TESTE", work_code="TEST-WORK",
                      work_name="OBRA DE TESTE", item_labels=[{"item_id": "OP-GOLDEN-06", "label": "03"}])
        page = build_production_layout(technical, ctx).pages[0]
        self.assertEqual((page.header.width_mm, page.header.height_mm, page.header.quantity), (1160, 2100, 2))
        self.assertEqual((page.header.client_code, page.header.work_name, page.header.item_label), ("TEST-CLIENT", "OBRA DE TESTE", "03"))
        self.assertEqual(page.page_format, "A4")
        self.assertEqual(page.orientation, "PORTRAIT")

    def test_source_order_changes_only_positions_and_keeps_every_value(self):
        technical = build_production_order(request())
        layout = build_production_layout(technical, context())
        rows = [r for b in layout.pages[0].blocks for r in b.rows]
        self.assertEqual(len(rows), len(technical.items[0].lines))
        self.assertEqual({r.engine_position: r.technical for r in rows}, {r.position: r for r in technical.items[0].lines})
        roles = [r.technical.utilization for r in rows]
        self.assertLess(roles.index("GLAZING_BEAD_HORIZONTAL"), roles.index("INTERLOCK"))
        self.assertLess(roles.index("LEAF_RUBBER"), roles.index("SCREEN_RUBBER"))
        self.assertEqual([r.print_position for r in rows], list(range(1, len(rows) + 1)))

    def test_hidden_handle_keeps_its_proven_hardware_anchor(self):
        data = request().model_dump(mode="json")
        data["items"][0]["technical_input"]["closure_mode"] = "MAÇANETA COM CREMONA + MAÇANETA OCULTA COM CREMONA"
        page = build_production_layout(build_production_order(ProductionOrderRequest.model_validate(data)), context()).pages[0]
        row = next(r for b in page.blocks for r in b.rows if r.technical.utilization == "HANDLE_HIDDEN")
        self.assertEqual(row.legacy_row, 141)
        self.assertEqual(page.ordering_status, "SOURCE_ORDER_MAPPED")

    def test_blocks_keep_cut_surface_and_quantity_semantics(self):
        page = build_production_layout(build_production_order(request()), context()).pages[0]
        blocks = {b.kind: b for b in page.blocks}
        self.assertIn("Med. Final (mm)", blocks["CUTS"].columns)
        self.assertIn("Med. Corte (mm)", blocks["CUTS"].columns)
        self.assertIn("Largura (mm)", blocks["SURFACES"].columns)
        self.assertIn("Altura (mm)", blocks["SURFACES"].columns)
        self.assertIn("CONSUMABLES", blocks)
        self.assertIn("SCREWS", blocks)
        self.assertTrue(any(f.code == "CONSUMPTION_PRESENTATION_REVIEW" for f in page.findings))

    def test_gr_fractional_panel_is_not_rounded_and_keeps_unit_review(self):
        page = build_production_layout(build_production_order(request("OP-GOLDEN-03")), context()).pages[0]
        row = next(r for b in page.blocks for r in b.rows if r.technical.utilization == "PANEL_FILL")
        self.assertAlmostEqual(row.technical.quantity_total, 12.835714285714285)
        self.assertEqual(row.technical.quantity_unit, "unresolved")
        self.assertTrue(any(f.code == "FRACTIONAL_UNIT_REVIEW" and f.engine_position == row.engine_position for f in page.findings))

    def test_existing_shutter_differences_and_warnings_survive(self):
        for case_id, quantity in (("OP-GOLDEN-05", 41), ("OP-GOLDEN-12", 60)):
            with self.subTest(case_id=case_id):
                page = build_production_layout(build_production_order(request(case_id)), context()).pages[0]
                slat = next(r.technical for b in page.blocks for r in b.rows if r.technical.utilization == "SHUTTER_SLAT")
                self.assertEqual(slat.quantity_total, quantity)
                self.assertTrue(any(f.code == "ENGINE_WARNING" and "SLAT" in f.field for f in page.findings))

    def test_unknown_engine_row_remains_visible_in_extension_block(self):
        technical = build_production_order(request())
        unknown = technical.items[0].lines[-1].model_copy(update={"position": 999, "utilization": "NEW_UNKNOWN_ROLE", "source": None})
        changed_item = technical.items[0].model_copy(update={"lines": technical.items[0].lines + (unknown,)})
        changed = technical.model_copy(update={"items": (changed_item,)})
        changed = changed.model_copy(update={"snapshot_sha256": hashlib.sha256(canonical_json(changed.model_dump(mode="json", exclude={"snapshot_sha256"})).encode()).hexdigest()})
        page = build_production_layout(changed, context()).pages[0]
        self.assertEqual(page.ordering_status, "PARTIALLY_MAPPED")
        self.assertEqual(page.blocks[-1].kind, "ENGINE_EXTENSION")
        self.assertEqual(page.blocks[-1].rows[-1].technical, unknown)

    def test_duplicate_unknown_header_labels_and_foreign_company_fail(self):
        technical = build_production_order(request())
        with self.assertRaises(ValueError):
            build_production_layout(technical, ProductionLayoutContext(company_id=UUID(int=2)))
        with self.assertRaises(ValueError):
            build_production_layout(technical, context(item_labels=[{"item_id": "unknown", "label": "1"}]))
        with self.assertRaises(ValidationError):
            context(item_labels=[{"item_id": "x", "label": "1"}, {"item_id": "x", "label": "2"}])
        for value in (" ", "PRIVATE\nHEADER"):
            with self.assertRaises(ValidationError):
                context(client_name=value)

    def test_missing_header_is_explicit_and_paths_never_appear(self):
        result = build_production_layout(build_production_order(request()), context())
        self.assertTrue(any(f.code == "MISSING_HEADER_DATA" for f in result.pages[0].findings))
        text = result.model_dump_json()
        for forbidden in ("C:\\", "C:/Users", "ThisWorkbook", "Croquis\\", "unit_price", "purchase_plan"):
            self.assertNotIn(forbidden, text)

    def test_saved_snapshot_layout_is_deterministic_frozen_and_not_recalculated(self):
        technical = build_production_order(request())
        with patch("api.app.production_service.engine_bridge.calculate_sliding", side_effect=AssertionError("must not recalculate")):
            first = build_production_layout(technical, context())
            second = build_production_layout(technical, context())
        self.assertEqual(first, second)
        self.assertEqual(ProductionLayoutDocument.model_validate_json(first.model_dump_json()), first)
        with self.assertRaises(ValidationError):
            first.pages[0].header.quantity = 99
        changed = technical.model_copy(update={"order_id": "modified"})
        with self.assertRaises(ValueError):
            build_production_layout(changed, context())

    def test_fixo_own_case_mixed_order_keeps_all_items_and_has_no_leaf_section(self):
        req = request().model_dump(mode="json")
        req["items"].append({"item_id": "FX-OWN", "finish_key": "BRANCO", "technical_input": {
            "family": "FX", "width_mm": 1200, "height_mm": 1000, "quantity": 2, "vertical_transoms": 1}})
        result = build_production_layout(build_production_order(ProductionOrderRequest.model_validate(req)), context())
        self.assertEqual([p.item_id for p in result.pages], ["OP-GOLDEN-01", "FX-OWN"])
        self.assertIsNone(result.pages[1].leaf_section)
        self.assertEqual(result.pages[1].ordering_status, "SOURCE_ORDER_MAPPED")

    def test_large_grid_is_not_truncated_at_eighty_rows_or_mislabeled_as_verified(self):
        req = request().model_dump(mode="json")
        req["items"][0]["technical_input"].update(width_mm=4000, height_mm=3000, leaf_grid={"horizontal_transoms": 4, "vertical_transoms": 4})
        technical = build_production_order(ProductionOrderRequest.model_validate(req))
        page = build_production_layout(technical, context()).pages[0]
        rows = [r for b in page.blocks for r in b.rows]
        self.assertGreater(len(rows), 80)
        self.assertEqual(len(rows), len(technical.items[0].lines))
        self.assertEqual(page.ordering_status, "PARTIALLY_MAPPED")
        self.assertTrue(all(b.allow_continuation and b.repeat_columns_on_continuation for b in page.blocks))

    def test_public_source_extraction_omits_all_customer_header_and_paths(self):
        text = "PRIVATE CUSTOMER 123\nC:\\Users\\PRIVATE\\secret\nUtilização  Descrição  Código  Med. Final  Med. Corte  Quant.\nMarco Largura  MARCO  PR8852  1200  1205  2\nPRIVATE CUSTOMER  123  456\nA\n"
        rows = technical_pdf_rows(text, {"Marco Largura"})
        self.assertEqual(rows, [{"label": "Marco Largura", "code": "PR8852"}])
        self.assertNotIn("PRIVATE", json.dumps(rows))

    def test_layout_report_does_not_claim_full_parity_or_hide_missing_materials(self):
        report = build_report()
        self.assertEqual(report["relative_order_counts"], {"MATCH": 12})
        self.assertEqual(report["model_identity_matches"], 12)
        self.assertEqual(report["engine_rows"], report["presentation_rows"])
        self.assertTrue(any(c["reference_rows_without_engine_match"] for c in report["cases"]))
        self.assertTrue(any(c["code_differences"] for c in report["cases"]))

    def test_reversed_reference_sequence_is_reported_as_divergent(self):
        altered = copy.deepcopy(REFERENCES[0])
        altered["rows"] = list(reversed(altered["rows"]))
        self.assertEqual(compare_layout_case(altered, INPUTS[altered["id"]])["relative_order"], "DIVERGENT")


def reference_test(case):
    def test(self):
        result = compare_layout_case(case, INPUTS[case["id"]])
        self.assertEqual(result["relative_order"], "MATCH", result)
        self.assertTrue(result["model_basename_matches"])
        self.assertEqual(result["engine_row_count"], result["presentation_row_count"])
    return test


for case in REFERENCES:
    setattr(LayoutAssemblyTests, "test_source_" + case["id"].lower().replace("-", "_"), reference_test(case))


class LayoutEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        app.dependency_overrides[_production_image_store] = lambda: None

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_http_layout_preview_and_openapi(self):
        payload = {"production_order": request().model_dump(mode="json"), "context": context().model_dump(mode="json")}
        response = self.client.post("/api/v1/production-orders/layout-preview", json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["schema_version"], "OP_LAYOUT_B1_0.1.0")
        self.assertIn("/api/v1/production-orders/layout-preview", self.client.get("/openapi.json").json()["paths"])

    def test_foreign_company_and_unknown_fields_are_422(self):
        payload = {"production_order": request().model_dump(mode="json"), "context": context().model_dump(mode="json")}
        payload["context"]["company_id"] = str(UUID(int=2))
        self.assertEqual(self.client.post("/api/v1/production-orders/layout-preview", json=payload).status_code, 422)
        payload["context"] = {**context().model_dump(mode="json"), "source_path": "C:/Users/private"}
        self.assertEqual(self.client.post("/api/v1/production-orders/layout-preview", json=payload).status_code, 422)

    def test_invalid_server_manifest_is_503_without_path_leak(self):
        app.dependency_overrides.clear()
        with patch.dict(os.environ, {"OP_IMAGE_MANIFEST": "C:/private-do-not-expose/missing.json"}):
            response = self.client.post("/api/v1/production-orders/layout-preview", json={
                "production_order": request().model_dump(mode="json"), "context": context().model_dump(mode="json")})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private-do-not-expose", response.text)

    def test_server_manifest_resolves_verified_images_without_exposing_storage_root(self):
        app.dependency_overrides.clear()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "objects").mkdir()
            technical = request().items[0].technical_input.model_dump(mode="json")
            key, _ = model_identity(technical, "BRANCO")
            images = [entry(ImageSelector(kind="MODEL_SKETCH", model_key=key, finish_key="BRANCO"), raster())]
            images += [entry(ImageSelector(kind="PROFILE_SECTION", code=code), raster(), "NEUTRAL_LEGACY_SECTION") for code in ("PR13852", "PR4266")]
            manifest = store_in(root, images).manifest
            (root / images[0].relative_path).write_bytes(raster())
            path = root / "manifest.json"
            path.write_text(manifest.model_dump_json(), encoding="utf-8")
            with patch.dict(os.environ, {"OP_IMAGE_MANIFEST": str(path), "OP_IMAGE_STORAGE_ROOT": str(root)}):
                response = self.client.post("/api/v1/production-orders/layout-preview", json={
                    "production_order": request().model_dump(mode="json"), "context": context().model_dump(mode="json")})
            self.assertEqual(response.status_code, 200, response.text)
            page = response.json()["pages"][0]
            self.assertEqual([page[k]["status"] for k in ("model_image", "frame_section", "leaf_section")], ["VERIFIED"] * 3)
            self.assertNotIn(str(root), response.text)


if __name__ == "__main__":
    unittest.main()
