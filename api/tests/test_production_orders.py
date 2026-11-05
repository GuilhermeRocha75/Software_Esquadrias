import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient
from pydantic import ValidationError

from api.app.main import app
from api.app.production_assets import ProductionAsset, ProductionAssetIndex
from api.app.production_schemas import ProductionOrderRequest, ProductionOrder
from api.app.production_service import build_production_order, canonical_json
from api.app.engine_bridge import calculate_fixo, FixoConfiguration

COMPANY = "00000000-0000-0000-0000-000000000001"


def payload(**technical):
    return {"company_id": COMPANY, "order_id": "ANON-001", "items": [
        {"item_id": "item-1", "finish_key": "BRANCO", "technical_input": {
            "family": "FX", "width_mm": 1200, "height_mm": 1000, **technical}}]}


class ProductionOrderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_http_preview_validates_and_serializes_document(self):
        response = self.client.post("/api/v1/production-orders/preview", json=payload())
        self.assertEqual(response.status_code, 200)
        document = ProductionOrder.model_validate(response.json())
        self.assertEqual(document.items[0].lines[0].final_length_mm, 1200)
        self.assertEqual(document.audit_status, "PENDING_INDEPENDENT_AUDIT")

    def test_mixed_order_keeps_ids_order_and_distinct_versions(self):
        data = payload()
        for family, extra in (("CR", {"leaf_count": 2, "leaf_system": "PRIME_WINDOW_42x66"}),
                              ("MAXIM_AR", {"leaf_system": "DESIGN_WINDOW_60x78"}), ("GR", {})):
            data["items"].append({"item_id": family, "finish_key": "BRANCO", "technical_input": {
                "family": family, "width_mm": 1200, "height_mm": 1800, **extra}})
        response = self.client.post("/api/v1/production-orders/preview", json=data)
        self.assertEqual(response.status_code, 200)
        items = response.json()["items"]
        self.assertEqual([i["family"] for i in items], ["FX", "CR", "MAXIM_AR", "GR"])
        self.assertEqual([i["position"] for i in items], [1, 2, 3, 4])
        self.assertEqual(len({i["engine_version"] for i in items}), 4)

    def test_snapshot_is_detached_frozen_and_includes_defaults(self):
        data = payload()
        request = ProductionOrderRequest.model_validate(data)
        document = build_production_order(request)
        data["items"][0]["technical_input"]["width_mm"] = 99
        self.assertEqual(json.loads(document.items[0].input_snapshot_json)["width_mm"], 1200)
        self.assertIn("glass_description", json.loads(document.items[0].input_snapshot_json))
        with self.assertRaises(ValidationError):
            document.items[0].lines[0].final_length_mm = 99
        with self.assertRaises(ValidationError):
            document.items[0].engine_version = "changed"
        self.assertEqual(ProductionOrder.model_validate_json(document.model_dump_json()), document)

    def test_digest_is_deterministic_includes_versions_and_is_not_only_request(self):
        request = ProductionOrderRequest.model_validate(payload())
        document = build_production_order(request)
        self.assertEqual(document, build_production_order(request))
        expected = hashlib.sha256(canonical_json(document.model_dump(mode="json", exclude={"snapshot_sha256"})).encode()).hexdigest()
        self.assertEqual(document.snapshot_sha256, expected)
        changed = payload(width_mm=1300)
        self.assertNotEqual(document.snapshot_sha256, build_production_order(ProductionOrderRequest.model_validate(changed)).snapshot_sha256)

    def test_no_commercial_values_purchase_plan_or_customer_paths(self):
        text = build_production_order(ProductionOrderRequest.model_validate(payload())).model_dump_json()
        for forbidden in ("unit_price", "unit_cost", "cost_by_group", "purchase_plan", "bars_required", "C:\\\\Users"):
            self.assertNotIn(forbidden, text)

    def test_assets_missing_are_distinct_from_missing_technical_data(self):
        request = ProductionOrderRequest.model_validate(payload())
        document = build_production_order(request)
        self.assertTrue(document.technical_data_complete)
        self.assertFalse(document.assets_complete)
        self.assertTrue(any(v.code == "MISSING_ASSET" for v in document.validations))
        self.assertFalse(any(v.code == "MISSING_TECHNICAL_DATA" for v in document.validations))
        data = payload()
        data["items"][0].pop("finish_key")
        missing = build_production_order(ProductionOrderRequest.model_validate(data))
        self.assertFalse(missing.technical_data_complete)
        self.assertTrue(any(v.code == "MISSING_TECHNICAL_DATA" and v.field.startswith("assets.") for v in missing.validations))

    def test_asset_index_resolves_metadata_and_respects_company(self):
        request = ProductionOrderRequest.model_validate(payload())
        document = build_production_order(request)
        # One physical file may satisfy frame and generic profile references.
        keys = {ref.key for ref in document.items[0].assets}
        entries = tuple(ProductionAsset(key, f"assets/test-{n}.png", "a" * 64) for n, key in enumerate(sorted(keys)))
        index = ProductionAssetIndex(UUID(COMPANY), entries)
        resolved = build_production_order(request, asset_index=index)
        self.assertTrue(resolved.assets_complete)
        self.assertTrue(all(ref.status == "AVAILABLE" for ref in resolved.items[0].assets))
        self.assertNotEqual(document.snapshot_sha256, resolved.snapshot_sha256)
        with self.assertRaisesRegex(ValueError, "outra empresa"):
            build_production_order(request, asset_index=ProductionAssetIndex(UUID(int=2), entries))

    def test_absolute_traversal_url_and_duplicate_asset_metadata_rejected(self):
        for path in ("C:/Users/client/a.png", "C:\\Users\\client\\a.png", "/tmp/a", "../a.png",
                     "assets/../a", "https://example.com/a", "assets//a", "assets/./a", ""):
            with self.subTest(path=path), self.assertRaises(ValueError):
                ProductionAsset("profile/known", path, "a" * 64)
        with self.assertRaises(ValueError):
            ProductionAsset("a", "assets/a", "invalid")
        entry = ProductionAsset("a", "assets/a.png", "a" * 64)
        with self.assertRaises(ValueError):
            ProductionAssetIndex(UUID(COMPANY), (entry, entry))

    def test_unknown_profile_is_technical_gap_instead_of_only_missing_image(self):
        result = calculate_fixo(FixoConfiguration(1200, 1000))
        result.unit_bom[0] = replace(result.unit_bom[0], material_code="UNKNOWN-PROFILE")
        with patch("api.app.production_service.engine_bridge.calculate_fixo", return_value=result):
            document = build_production_order(ProductionOrderRequest.model_validate(payload()))
        self.assertEqual(document.items[0].lines[0].code, "UNKNOWN-PROFILE")
        self.assertTrue(any(ref.status == "MISSING_TECHNICAL_DATA" and "UNKNOWN-PROFILE" in ref.key for ref in document.items[0].assets))

    def test_blank_legacy_lines_are_retained_with_field_validation(self):
        result = calculate_fixo(FixoConfiguration(1200, 1000))
        result.unit_bom[0] = replace(result.unit_bom[0], material_code="0", description="")
        with patch("api.app.production_service.engine_bridge.calculate_fixo", return_value=result):
            document = build_production_order(ProductionOrderRequest.model_validate(payload()))
        self.assertEqual(document.items[0].lines[0].code, "0")
        self.assertEqual(document.items[0].lines[0].description, "")
        self.assertTrue(any(v.field == "description" and v.position == 1 for v in document.validations))

    def test_pv_gd_unknown_or_implicit_family_return_422(self):
        for family in ("PV", "GD", "MX", "UNKNOWN", None):
            with self.subTest(family=family):
                data = payload(family=family)
                if family is None:
                    data["items"][0]["technical_input"].pop("family")
                self.assertEqual(self.client.post("/api/v1/production-orders/preview", json=data).status_code, 422)

    def test_empty_duplicate_company_and_unknown_fields_return_422(self):
        variants = []
        for field, value in (("items", []), ("company_id", ""), ("company_id", None), ("commercial_quote", {})):
            data = payload()
            data[field] = value
            variants.append(data)
        duplicate = payload()
        duplicate["items"].append(copy.deepcopy(duplicate["items"][0]))
        variants.append(duplicate)
        variants.append(payload(unrecognized_engine_option=1))
        for data in variants:
            with self.subTest(data=data):
                self.assertEqual(self.client.post("/api/v1/production-orders/preview", json=data).status_code, 422)

    def test_nested_unknown_fields_are_rejected(self):
        for family, extra in (("CR", {"leaf_count": 2, "leaf_system": "PRIME_WINDOW_42x66"}),
                              ("MAXIM_AR", {"leaf_system": "DESIGN_WINDOW_60x78"})):
            data = payload(family=family, leaf_grid={"invented": True}, **extra)
            self.assertEqual(self.client.post("/api/v1/production-orders/preview", json=data).status_code, 422)

    def test_valid_nested_cr_request_keeps_grid_flags_shutter_and_counts(self):
        response = self.client.post("/api/v1/production-orders/preview", json=payload(
            family="CR", width_mm=2400, height_mm=2800, quantity=2,
            leaf_count=4, leaf_system="DESIGN_DOOR_60x111", screen_enabled=True,
            leaf_grid={"horizontal_transoms": 1, "vertical_transoms": 1,
                       "custom_dimensions": [{"axis": "COLUMNS", "index": 0, "clear_span_mm": 100}]},
            bottom_fixed_panel={"height_mm": 400}, top_fixed_panel={"height_mm": 450},
            structural_reinforcement={"material_code": "ALUM10238"},
            shutter={"mode": "AUTOMATIZADA COM CONTROLE REMOTO EM 2 PAINÉIS"},
        ))
        self.assertEqual(response.status_code, 200, response.text)
        item = response.json()["items"][0]
        snapshot = json.loads(item["input_snapshot_json"])
        self.assertEqual(snapshot["leaf_grid"]["custom_dimensions"][0]["clear_span_mm"], 100)
        roles = {line["utilization"] for line in item["lines"]}
        self.assertTrue({"SHUTTER_REMOTE_MOTOR", "BOTTOM_FIXED_FRAME_VERTICAL", "STRUCTURAL_REINFORCEMENT"} <= roles)
        frame = next(line for line in item["lines"] if line["utilization"] == "FRAME_VERTICAL")
        self.assertEqual(frame["final_length_mm"], 1750)

    def test_all_families_reject_nonfinite_fractional_boolean_and_negative_input(self):
        for family, extra in (("CR", {"leaf_count": 2, "leaf_system": "PRIME_WINDOW_42x66"}),
                              ("MAXIM_AR", {"leaf_system": "DESIGN_WINDOW_60x78"}), ("GR", {}), ("FX", {})):
            for field, invalid in (("width_mm", float("nan")), ("height_mm", float("inf")),
                                   ("width_mm", True), ("quantity", True), ("quantity", 1.5),
                                   ("quantity", 0), ("width_mm", -1)):
                with self.subTest(family=family, field=field, value=invalid), self.assertRaises(ValidationError):
                    ProductionOrderRequest.model_validate(payload(family=family, **extra, **{field: invalid}))

    def test_invalid_engine_configuration_returns_item_specific_422(self):
        response = self.client.post("/api/v1/production-orders/preview", json=payload(width_mm=50))
        self.assertEqual(response.status_code, 422)
        self.assertIn("item-1", response.json()["detail"])

    def test_snapshot_can_be_reprinted_without_calling_current_engine(self):
        document = build_production_order(ProductionOrderRequest.model_validate(payload()))
        with patch("api.app.production_service.engine_bridge.calculate_fixo", side_effect=AssertionError("must not recalculate")):
            restored = ProductionOrder.model_validate_json(document.model_dump_json())
        self.assertEqual(restored, document)

    def test_order_stock_settings_are_snapshotted_and_do_not_split_pieces(self):
        data = payload(width_mm=6500)
        data["stock_lengths_mm"] = {"DE6058": 5900}
        document = build_production_order(ProductionOrderRequest.model_validate(data))
        self.assertEqual(json.loads(document.request_snapshot_json)["stock_lengths_mm"]["DE6058"], 5900)
        self.assertEqual(document.items[0].lines[0].cut_length_mm, 6505)
        self.assertEqual(document.items[0].lines[0].splice_status, "MANUAL_SPLICE_REQUIRED")
        for invalid in (0, -1, float("nan"), True):
            data["stock_lengths_mm"] = {"DE6058": invalid}
            with self.subTest(stock=invalid), self.assertRaises(ValidationError):
                ProductionOrderRequest.model_validate(data)

    def test_openapi_documents_all_new_schemas(self):
        schema = self.client.get("/openapi.json").json()
        operation = schema["paths"]["/api/v1/production-orders/preview"]["post"]
        self.assertIn("requestBody", operation)
        self.assertIn("200", operation["responses"])
        for name in ("ProductionOrderRequest", "ProductionOrder", "ProductionOrderLine", "ProductionValidation", "ProductionAssetReference"):
            self.assertIn(name, schema["components"]["schemas"])


if __name__ == "__main__":
    unittest.main()
