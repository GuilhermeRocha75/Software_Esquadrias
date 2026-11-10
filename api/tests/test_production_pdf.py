"""B2 integrity and release-gate tests; no private sources are needed in CI."""
import copy
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient
from PIL import Image
from pypdf import PdfReader
import pymupdf

from api.app.main import app, _production_image_store
from api.app.production_images import ImageSelector, ProductionImageManifest, ProductionImageStore, StoredProductionImage, image_metadata
from api.app.production_layout import ProductionLayoutRequest, ProductionLayoutContext, prepare_production_layout
from api.app.production_pdf import render_production_pdf, production_pdf_readiness, pdf_model_headings, pdf_number, printable_text, PdfModelHeading, PdfReviewNote
from api.app.production_schemas import ProductionOrderRequest
from api.app.production_service import canonical_json
from tools.generate_op_review_pdfs import reference_request, classify_b1_differences, private_output_dir
from tools.inspect_op_pdf import inspect_pdf
from tools.compare_op_pdf_numeric import compare_numeric_reference

ROOT = Path(__file__).resolve().parents[2]
INPUTS = json.loads((ROOT / "api/tests/fixtures/op_reference_inputs.json").read_text(encoding="utf-8"))["cases"]
COMPANY = UUID("00000000-0000-0000-0000-000000000001")


def fixture_request(family="CR"):
    if family == "FX":
        case = {"id": "FX-OWN", "finish_key": "BRANCO", "technical_input": {"family": "FX", "width_mm": 1200, "height_mm": 1000}}
    else:
        case = next(c for c in INPUTS if c["technical_input"]["family"] == family)
    return reference_request(case, 1)


def rehash(layout):
    return layout.model_copy(update={"layout_sha256": hashlib.sha256(canonical_json(layout.model_dump(mode="json", exclude={"layout_sha256"})).encode()).hexdigest()})


def test_store(root, layout):
    # Distinct tiny format-only rasters in a temporary directory. Never imported
    # as production fallbacks, committed, or used in the real review documents.
    references = [layout.pages[0].model_image, layout.pages[0].frame_section, layout.pages[0].leaf_section]
    entries, images = [], {}
    (root / "objects").mkdir()
    for n, ref in enumerate(r for r in references if r is not None):
        buffer = BytesIO()
        Image.new("RGB", (4 + n, 3 + n), (40 + n * 40, 90, 160)).save(buffer, "JPEG")
        data = buffer.getvalue()
        digest = hashlib.sha256(data).hexdigest()
        media, width, height = image_metadata(data)
        relative = f"objects/{digest}.jpg"
        (root / relative).write_bytes(data)
        entries.append(StoredProductionImage(selector=ref.selector, relative_path=relative, sha256=digest,
                      media_type=media, width_px=width, height_px=height, finish_policy="EXACT"))
        images[digest] = data
    manifest = ProductionImageManifest(company_id=layout.company_id, source_workbook_sha256="a" * 64, entries=tuple(entries))
    return ProductionImageStore(root, manifest), images


class ProductionPdfTests(unittest.TestCase):
    def test_decimal_printing_preserves_fraction_and_does_not_round(self):
        for value, expected in ((12.835714285714285, "12,835714285714285"), (40.25, "40,25"),
                                 (84.224, "84,224"), (1000.0, "1000"), (0, "0"), (None, "—")):
            self.assertEqual(pdf_number(value), expected)
        with self.assertRaises(ValueError):
            pdf_number(float("nan"))

    def test_cr_review_has_a4_pages_fields_dimensions_codes_and_no_release(self):
        request = fixture_request()
        layout = prepare_production_layout(request)
        result = render_production_pdf(layout, model_headings=pdf_model_headings(request))
        report = inspect_pdf(result.content, result.audit)
        self.assertTrue(report["integrity_valid"], report)
        self.assertEqual(result.audit.page_count, 2)
        self.assertEqual(result.audit.row_count, 32)
        self.assertEqual(report["embedded_images"], 0)
        text = "\n".join(p.extract_text() for p in PdfReader(BytesIO(result.content)).pages)
        for field in ("Cód. Cliente", "Nome", "Item", "Largura", "Altura", "Quant.", "Med. Final", "Med. Corte",
                      "PR13852", "PR4266", "1930", "1935", "954", "959", "846", "1294", "84,224",
                      "CONFERÊNCIA", "NÃO FABRICAR", "Imagem", "não disponível", "TELA MOSQUITEIRA"):
            self.assertIn(field, text)
        self.assertFalse(result.audit.readiness.fabrication_allowed)

    def test_four_families_render_and_keep_every_technical_row(self):
        for family in ("CR", "MAXIM_AR", "GR", "FX"):
            with self.subTest(family=family):
                request = fixture_request(family)
                layout = prepare_production_layout(request)
                result = render_production_pdf(layout, model_headings=pdf_model_headings(request))
                report = inspect_pdf(result.content, result.audit)
                self.assertTrue(report["integrity_valid"], report)
                self.assertEqual(report["rows"], sum(len(b.rows) for p in layout.pages for b in p.blocks))
                self.assertGreaterEqual(report["pages"], 2)

    def test_saved_layout_rendering_never_recalculates_engine_and_is_deterministic(self):
        layout = prepare_production_layout(fixture_request())
        with patch("api.app.production_service.engine_bridge.calculate_sliding", side_effect=AssertionError("must not calculate")):
            first = render_production_pdf(layout)
            second = render_production_pdf(layout)
        self.assertEqual(first.content, second.content)
        self.assertEqual(first.audit, second.audit)

    def test_real_image_bytes_and_placements_are_verified_in_pdf(self):
        request = fixture_request()
        with TemporaryDirectory() as directory:
            store, images = test_store(Path(directory), prepare_production_layout(request))
            layout = prepare_production_layout(request, image_store=store)
            result = render_production_pdf(layout, image_store=store)
            report = inspect_pdf(result.content, result.audit, expected_images=images)
            self.assertTrue(report["integrity_valid"], report)
            self.assertEqual(report["embedded_images"], 3)
            self.assertEqual(report["verified_image_placements"], 7)
            placement = result.audit.images[0]
            moved = placement.model_copy(update={"bbox": tuple(value + 15 for value in placement.bbox)})
            altered = result.audit.model_copy(update={"images": (moved,) + result.audit.images[1:]})
            bad = inspect_pdf(result.content, altered, expected_images=images)
            self.assertTrue(any(e["code"] == "IMAGE_PLACEMENT_MISMATCH" for e in bad["errors"]))

    def test_deleted_asset_after_snapshot_is_reported_without_fictional_image(self):
        request = fixture_request()
        with TemporaryDirectory() as directory:
            store, _ = test_store(Path(directory), prepare_production_layout(request))
            layout = prepare_production_layout(request, image_store=store)
            (Path(directory) / store.manifest.entries[0].relative_path).unlink()
            result = render_production_pdf(layout, image_store=store)
            self.assertTrue(any(b.code == "MISSING_OR_INVALID_PDF_ASSET" for b in result.audit.readiness.blockers))
            self.assertEqual(len(result.audit.images), 6)
            self.assertTrue(inspect_pdf(result.content, result.audit)["integrity_valid"])

    def test_foreign_manifest_changed_manifest_and_modified_layout_are_rejected(self):
        request = fixture_request()
        with TemporaryDirectory() as directory:
            store, _ = test_store(Path(directory), prepare_production_layout(request))
            layout = prepare_production_layout(request, image_store=store)
            bad_company = ProductionImageStore(Path(directory), store.manifest.model_copy(update={"company_id": UUID(int=2)}))
            with self.assertRaises(ValueError):
                render_production_pdf(layout, image_store=bad_company)
            changed = ProductionImageStore(Path(directory), store.manifest.model_copy(update={"entries": ()}))
            with self.assertRaises(ValueError):
                render_production_pdf(layout, image_store=changed)
        with self.assertRaises(ValueError):
            render_production_pdf(layout.model_copy(update={"order_id": "tampered"}))

    def test_pagination_keeps_more_than_eighty_rows_in_original_order(self):
        request = fixture_request().model_dump(mode="json")
        request["production_order"]["items"][0]["technical_input"].update(
            width_mm=4000, height_mm=3000, leaf_grid={"horizontal_transoms": 4, "vertical_transoms": 4})
        layout = prepare_production_layout(ProductionLayoutRequest.model_validate(request))
        result = render_production_pdf(layout)
        report = inspect_pdf(result.content, result.audit)
        self.assertTrue(report["integrity_valid"], report)
        self.assertGreater(result.audit.row_count, 80)
        self.assertGreater(report["table_pages"], 1)
        expected = [r.engine_position for b in layout.pages[0].blocks for r in b.rows]
        actual = [r.engine_position for r in result.audit.rows if r.fragment == 1]
        self.assertEqual(actual, expected)

    def test_oversized_row_splits_without_truncating_start_middle_or_end(self):
        layout = prepare_production_layout(fixture_request("FX"))
        page = layout.pages[0]
        blocks = list(page.blocks)
        rows = list(blocks[0].rows)
        description = "INICIO_LONGO " + "conteudo " * 2400 + "FIM_LONGO"
        rows[0] = rows[0].model_copy(update={"technical": rows[0].technical.model_copy(update={"description": description})})
        blocks[0] = blocks[0].model_copy(update={"rows": tuple(rows)})
        layout = rehash(layout.model_copy(update={"pages": (page.model_copy(update={"blocks": tuple(blocks)}),)}))
        result = render_production_pdf(layout)
        report = inspect_pdf(result.content, result.audit)
        self.assertTrue(report["integrity_valid"], report)
        self.assertGreater(report["row_fragments"], report["rows"])
        text = "\n".join(p.extract_text() for p in PdfReader(BytesIO(result.content)).pages)
        self.assertIn("INICIO_LONGO", text)
        self.assertIn("FIM_LONGO", text)
        self.assertEqual(text.count("conteudo"), 2400)
        reader = PdfReader(BytesIO(result.content))
        continued = [fragment for fragment in result.audit.rows if fragment.engine_position == rows[0].engine_position and fragment.fragment > 1]
        self.assertTrue(continued)
        self.assertTrue(all("DE6058" in reader.pages[fragment.page_number - 1].extract_text() for fragment in continued))

    def test_gr_fraction_remains_unrounded_and_unit_is_marked_pending(self):
        result = render_production_pdf(prepare_production_layout(fixture_request("GR")))
        text = "\n".join(p.extract_text() for p in PdfReader(BytesIO(result.content)).pages)
        self.assertIn("12,835714285714285", text)
        self.assertIn("Unidade física pendente", text)
        self.assertIn("unid. pendente", text)
        self.assertTrue(inspect_pdf(result.content, result.audit)["integrity_valid"])

    def test_order_and_bom_quantity_distinctions_are_visible_in_main_table_or_annex(self):
        request = fixture_request().model_dump(mode="json")
        request["production_order"]["items"][0]["technical_input"].update(
            width_mm=2400, leaf_count=3, quantity=2)
        layout = prepare_production_layout(ProductionLayoutRequest.model_validate(request))
        result = render_production_pdf(layout)
        text = "\n".join(p.extract_text() for p in PdfReader(BytesIO(result.content)).pages)
        self.assertIn("Fator BOM: 1,5/esq.; 3 total.", text)
        self.assertIn("2/esquadria; 4 total (un)", text)
        self.assertTrue(inspect_pdf(result.content, result.audit)["integrity_valid"])

    def test_paths_sentinel_and_markup_are_handled_without_printing_local_paths(self):
        layout = prepare_production_layout(fixture_request("FX"))
        page = layout.pages[0]
        blocks = list(page.blocks)
        rows = list(blocks[0].rows)
        rows[0] = rows[0].model_copy(update={"utilization_label": "A", "technical": rows[0].technical.model_copy(update={
            "description": "<script>literal</script> C:\\Users\\private\\Croquis\\customer.jpg"})})
        blocks[0] = blocks[0].model_copy(update={"rows": tuple(rows)})
        page = page.model_copy(update={"blocks": tuple(blocks)})
        result = render_production_pdf(rehash(layout.model_copy(update={"pages": (page,)})))
        text = "\n".join(p.extract_text() for p in PdfReader(BytesIO(result.content)).pages)
        self.assertNotIn("C:\\", text)
        self.assertNotIn("customer.jpg", text)
        self.assertIn("<script>literal</script>", text)
        self.assertIn("resíduo legado omitido", text)
        self.assertTrue(any(b.code == "LEGACY_TEXT_REDACTED" for b in result.audit.readiness.blockers))
        self.assertTrue(inspect_pdf(result.content, result.audit)["integrity_valid"])

    def test_missing_description_and_zero_code_row_is_not_discarded(self):
        layout = prepare_production_layout(fixture_request("FX"))
        p = layout.pages[0]
        blocks = list(p.blocks)
        rows = list(blocks[0].rows)
        rows[0] = rows[0].model_copy(update={"technical": rows[0].technical.model_copy(update={"description": "", "code": "0"})})
        blocks[0] = blocks[0].model_copy(update={"rows": tuple(rows)})
        result = render_production_pdf(rehash(layout.model_copy(update={"pages": (p.model_copy(update={"blocks": tuple(blocks)}),)})))
        text = "\n".join(p.extract_text() for p in PdfReader(BytesIO(result.content)).pages)
        self.assertIn("[sem descrição]", text)
        self.assertEqual(result.audit.row_count, 13)

    def test_model_heading_must_match_snapshot_and_notes_must_reference_existing_item(self):
        layout = prepare_production_layout(fixture_request())
        with self.assertRaises(ValueError):
            render_production_pdf(layout, model_headings=(PdfModelHeading(item_id=layout.pages[0].item_id, model_key="wrong", description="wrong"),))
        with self.assertRaises(ValueError):
            render_production_pdf(layout, review_notes=(PdfReviewNote(item_id="foreign", classification="test", message="test"),))

    def test_mixed_order_starts_each_item_on_a_new_table_page(self):
        request = fixture_request().model_dump(mode="json")
        request["production_order"]["items"].append(fixture_request("FX").production_order.items[0].model_dump(mode="json"))
        result = render_production_pdf(prepare_production_layout(ProductionLayoutRequest.model_validate(request)))
        table_pages = [p for p in result.audit.pages if p.kind == "TABLE"]
        self.assertEqual(len({p.item_id for p in table_pages}), 2)
        self.assertGreaterEqual(result.audit.page_count, 4)
        self.assertTrue(inspect_pdf(result.content, result.audit)["integrity_valid"])

    def test_inspector_detects_truncated_pdf_wrong_cell_and_wrong_image_position(self):
        result = render_production_pdf(prepare_production_layout(fixture_request("FX")))
        self.assertFalse(inspect_pdf(result.content[:200], result.audit)["integrity_valid"])
        row = result.audit.rows[0]
        cell = row.cells[0].model_copy(update={"text": "VALUE_NOT_PRINTED"})
        altered = result.audit.model_copy(update={"rows": (row.model_copy(update={"cells": (cell,) + row.cells[1:]}),) + result.audit.rows[1:]})
        report = inspect_pdf(result.content, altered)
        self.assertTrue(any(e["code"] == "CELL_TEXT_MISMATCH" for e in report["errors"]))

    def test_b1_divergence_classification_keeps_all_13_34_26_occurrences(self):
        report = json.loads((ROOT / "docs/audits/op_b1/layout_comparison.json").read_text(encoding="utf-8"))
        values = [d for c in report["cases"] for d in classify_b1_differences(c)]
        self.assertEqual(sum(d["kind"] == "ENGINE_ADDITIONAL_ROW" for d in values), 13)
        self.assertEqual(sum(d["kind"] == "REFERENCE_ROW_ABSENT" for d in values), 34)
        self.assertEqual(sum(d["kind"] == "CODE_DIFFERENCE" for d in values), 26)
        self.assertEqual(sum(d["classification"] == "INCOMPLETE_RECONSTRUCTED_INPUT" for d in values), 32)
        self.assertTrue(any(d["classification"] == "POSSIBLE_ENGINEERING_OR_LEGACY_VARIANT" for d in values))

    def test_private_pdf_writer_refuses_public_repository_destination(self):
        with self.assertRaises(ValueError):
            private_output_dir(ROOT / "web/public/op-reviews")

    def test_full_printed_numeric_audit_does_not_hide_new_par2_and_shaft_differences(self):
        b1 = json.loads((ROOT / "docs/audits/op_b1/layout_comparison.json").read_text(encoding="utf-8"))["cases"]
        source = {c["id"]: c for c in json.loads((ROOT / "api/tests/fixtures/op_pdf_numeric_reference_v1.json").read_text(encoding="utf-8"))["cases"]}
        inputs = {c["id"]: c for c in INPUTS}
        from collections import Counter
        counts = Counter()
        differences = []
        for case in b1:
            layout = prepare_production_layout(reference_request(inputs[case["id"]], 1))
            report = compare_numeric_reference(case, source[case["id"]], layout)
            counts.update(report["counts"])
            differences += report["differences"]
            self.assertFalse(report["full_equivalence"])
        self.assertEqual(counts, {"MATCH": 670, "DIVERGENT": 27, "PRINTED_PRECISION_DIFFERENCE": 1})
        self.assertEqual(sum(d["role"] == "REINFORCEMENT_SCREWS" for d in differences), 8)
        shaft = next(d for d in differences if d["role"] == "SHUTTER_SHAFT" and d["field"] == "cut_length_mm")
        self.assertEqual((shaft["pdf_printed"], shaft["engine"], shaft["classification"]), ("950", 1940, "INPUT_SHUTTER_MODE_UNCONFIRMED"))

    def test_unsupported_glyph_fails_instead_of_silently_dropping_customer_text(self):
        payload = fixture_request().model_dump(mode="json")
        payload["context"]["client_name"] = "CLIENTE \U0001f600"
        layout = prepare_production_layout(ProductionLayoutRequest.model_validate(payload))
        with self.assertRaisesRegex(ValueError, "glifo"):
            render_production_pdf(layout)


def golden_pdf_test(case):
    def test(self):
        request = reference_request(case, int(case["id"][-2:]))
        layout = prepare_production_layout(request)
        result = render_production_pdf(layout, model_headings=pdf_model_headings(request))
        report = inspect_pdf(result.content, result.audit)
        self.assertTrue(report["integrity_valid"], report)
        self.assertEqual(report["rows"], sum(len(b.rows) for p in layout.pages for b in p.blocks))
        text = "\n".join(p.extract_text() for p in PdfReader(BytesIO(result.content)).pages)
        for p in layout.pages:
            for block in p.blocks:
                for row in block.rows:
                    t = row.technical
                    if t.code:
                        self.assertIn(t.code, text)
                    for number in (t.final_length_mm, t.cut_length_mm, t.width_mm, t.height_mm, t.quantity_total):
                        if number is not None:
                            self.assertIn(pdf_number(number), text)
    return test


for case in INPUTS:
    setattr(ProductionPdfTests, "test_pdf_" + case["id"].lower().replace("-", "_"), golden_pdf_test(case))


class ProductionPdfEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        app.dependency_overrides[_production_image_store] = lambda: None

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_review_pdf_response_is_private_marked_and_integrable_with_web(self):
        response = self.client.post("/api/v1/production-orders/pdf", json={"layout_request": fixture_request().model_dump(mode="json")})
        self.assertEqual(response.status_code, 200, response.text[:150])
        self.assertEqual(response.headers["Content-Type"], "application/pdf")
        self.assertEqual(response.headers["X-OP-Mode"], "REVIEW")
        self.assertEqual(response.headers["X-OP-Fabrication-Allowed"], "false")
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertEqual(int(response.headers["X-OP-Pages"]), len(PdfReader(BytesIO(response.content)).pages))

    def test_production_mode_is_always_409_and_does_not_render(self):
        with patch("api.app.main.render_production_pdf", side_effect=AssertionError("must not render")):
            response = self.client.post("/api/v1/production-orders/pdf", json={
                "layout_request": fixture_request().model_dump(mode="json"), "purpose": "PRODUCTION"})
        self.assertEqual(response.status_code, 409)
        self.assertFalse(response.json()["detail"]["fabrication_allowed"])
        self.assertEqual(response.json()["detail"]["code"], "FABRICATION_BLOCKED")

    def test_even_fully_populated_fixo_with_verified_assets_has_no_release_bypass(self):
        request = fixture_request("FX")
        with TemporaryDirectory() as directory:
            store, _ = test_store(Path(directory), prepare_production_layout(request))
            app.dependency_overrides[_production_image_store] = lambda: store
            response = self.client.post("/api/v1/production-orders/pdf", json={"layout_request": request.model_dump(mode="json"), "purpose": "PRODUCTION"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual([b["code"] for b in response.json()["detail"]["blockers"]], ["INDEPENDENT_DOCUMENT_AUDIT_PENDING"])

    def test_readiness_identifies_missing_assets_and_does_not_authorize_manufacturing(self):
        response = self.client.post("/api/v1/production-orders/pdf-readiness", json=fixture_request().model_dump(mode="json"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["review_allowed"])
        self.assertFalse(response.json()["fabrication_allowed"])
        self.assertTrue(any(b["code"] == "MISSING_OR_INVALID_PDF_ASSET" for b in response.json()["blockers"]))

    def test_company_mismatch_and_client_release_override_are_rejected(self):
        payload = {"layout_request": fixture_request().model_dump(mode="json")}
        payload["fabrication_allowed"] = True
        self.assertEqual(self.client.post("/api/v1/production-orders/pdf", json=payload).status_code, 422)
        payload.pop("fabrication_allowed")
        payload["layout_request"]["context"]["company_id"] = str(UUID(int=2))
        self.assertEqual(self.client.post("/api/v1/production-orders/pdf", json=payload).status_code, 422)

    def test_pdf_contract_and_headers_are_exposed_in_openapi_and_cors(self):
        response = self.client.post("/api/v1/production-orders/pdf", headers={"Origin": "http://localhost:5173"},
                         json={"layout_request": fixture_request().model_dump(mode="json")})
        self.assertIn("X-OP-Fabrication-Allowed", response.headers["Access-Control-Expose-Headers"])
        schema = self.client.get("/openapi.json").json()
        operation = schema["paths"]["/api/v1/production-orders/pdf"]["post"]
        self.assertIn("application/pdf", operation["responses"]["200"]["content"])
        self.assertIn("409", operation["responses"])


if __name__ == "__main__":
    unittest.main()
