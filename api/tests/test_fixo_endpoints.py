import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from fastapi import HTTPException
from pydantic import ValidationError
from api.app.main import (calculate_fixo_endpoint, calculate_fixo_purchase_plan,
                          calculate_unified_purchase_plan, fixo_options, health)
from api.app.schemas import FixoItemRequest, FixoPurchasePlanRequest, UnifiedPurchasePlanRequest


class FixoEndpointTests(unittest.TestCase):
    def test_options_and_health_expose_fixo_with_pending_homologation(self):
        options = fixo_options()
        self.assertIn(options["engine_version"], health()["engines"])
        self.assertEqual(options["family"], "FX")
        self.assertFalse(options["technical_gate"]["main_ready"])
        self.assertTrue(options["transoms"]["horizontal"])

    def test_calculation_serializes_full_grid_and_scales_order_cost(self):
        result = calculate_fixo_endpoint(FixoItemRequest(width_mm=2000, height_mm=2200, quantity=3,
                                                       vertical_transoms=2, horizontal_transoms=3))
        self.assertEqual(result["geometry"]["glass_quantity"], 12)
        self.assertEqual(len(result["leaf_openings"]), 12)
        self.assertEqual(result["order_technical_cost"], result["unit_technical_cost"] * 3)
        self.assertTrue(all(component["source"].startswith("FX!") for component in result["bom"]))

    def test_request_rejects_nonfinite_fractional_bool_and_unknown_fields(self):
        for extra in ({"width_mm": float("inf")}, {"quantity": True}, {"quantity": 1.1},
                      {"horizontal_transoms": -1}, {"vertical_transoms": True},
                      {"screen_enabled": True}, {"shutter": {}}, {"leaf_count": 2}):
            with self.subTest(extra=extra), self.assertRaises(ValidationError):
                FixoItemRequest(**{"width_mm": 1200, "height_mm": 1000, **extra})

    def test_source_errors_and_impossible_openings_return_422(self):
        for extra in ({"glass_description": "VIDRO NÃO CADASTRADO"}, {"width_mm": 150, "vertical_transoms": 2},
                      {"width_mm": 1e200, "height_mm": 1e200}):
            with self.subTest(extra=extra), self.assertRaises(HTTPException) as caught:
                calculate_fixo_endpoint(FixoItemRequest(**{"width_mm": 1200, "height_mm": 1000, **extra}))
            self.assertEqual(caught.exception.status_code, 422)

    def test_mixed_order_dispatch_keeps_fx_cr_mx_and_gr_types(self):
        request = UnifiedPurchasePlanRequest(items=[
            {"family": "FX", "width_mm": 1200, "height_mm": 1000},
            {"family": "CR", "width_mm": 2000, "height_mm": 1200, "leaf_count": 2, "leaf_system": "PRIME_WINDOW_42x66"},
            {"family": "MAXIM_AR", "width_mm": 800, "height_mm": 800, "leaf_system": "PRIME_WINDOW_42x63"},
            {"family": "GR", "width_mm": 900, "height_mm": 2100},
        ])
        self.assertIsInstance(request.items[0], FixoItemRequest)
        result = calculate_unified_purchase_plan(request)
        self.assertEqual(len(result["items"]), 4)
        self.assertTrue(result["items"][0]["engine_version"].startswith("FX_"))
        self.assertAlmostEqual(result["purchase_plan"]["technical_total"], sum(item["order_technical_cost"] for item in result["items"]), places=5)

    def test_fixo_purchase_supports_stock_length_and_rejects_oversized_cut(self):
        item = FixoItemRequest(width_mm=7500, height_mm=2500, vertical_transoms=3)
        with self.assertRaises(HTTPException) as caught:
            calculate_fixo_purchase_plan(FixoPurchasePlanRequest(items=[item]))
        self.assertEqual(caught.exception.status_code, 422)
        result = calculate_fixo_purchase_plan(FixoPurchasePlanRequest(items=[item], stock_length_mm=8000, kerf_mm=3))
        self.assertTrue(all(line["stock_length_mm"] == 8000 for line in result["purchase_plan"]["lines"]))


if __name__ == "__main__":
    unittest.main()
