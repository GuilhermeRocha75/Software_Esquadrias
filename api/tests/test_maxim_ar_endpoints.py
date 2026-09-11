import sys
from pathlib import Path
import unittest

from fastapi import HTTPException


API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parent
sys.path.insert(0, str(REPO_ROOT))

from api.app.main import (  # noqa: E402
    calculate_maxim_ar_endpoint,
    calculate_maxim_ar_purchase_plan,
    calculate_unified_purchase_plan,
    health,
    maxim_ar_options,
)
from api.app.schemas import (  # noqa: E402
    CRItemRequest,
    MaximArItemRequest,
    MaximArPurchasePlanRequest,
    UnifiedPurchasePlanRequest,
)


def request(**overrides):
    values = {
        "width_mm": 800,
        "height_mm": 800,
        "quantity": 1,
        "leaf_system": "PRIME_WINDOW_42x63",
        "glass_description": "04mm MINI BOREAL",
        "closure_mode": "FECHO 1 PONTO",
        "internal_finish": "GUARNIÇÃO DE 70MM",
        "external_finish": "BARRA CHATA DE 30MM",
    }
    values.update(overrides)
    return MaximArItemRequest(**values)


class MaximArEndpointTests(unittest.TestCase):
    def test_health_exposes_both_engines_without_changing_cr_version(self):
        response = health()
        self.assertEqual(response["engine"], "CR_ENGINE_0.5.0")
        self.assertEqual(response["engines"], ["CR_ENGINE_0.5.0", "MX_ENGINE_0.3.0"])

    def test_options_expose_phase2_proven_variants_and_gate(self):
        response = maxim_ar_options()
        self.assertEqual(response["engine_version"], "MX_ENGINE_0.3.0")
        self.assertEqual(response["phase"], 3)
        self.assertEqual(response["leaf_counts"], list(range(1, 9)))
        self.assertEqual(response["orientations"], ["HORIZONTAL", "VERTICAL"])
        self.assertTrue(response["screen"]["supported"])
        self.assertFalse(response["leaf_grid"]["supported"])
        self.assertTrue(response["technical_gate"]["approved"])
        self.assertEqual(
            {row["value"] for row in response["leaf_systems"]},
            {"PRIME_WINDOW_42x63", "DESIGN_WINDOW_60x78"},
        )

    def test_calculate_serializes_excel_golden(self):
        response = calculate_maxim_ar_endpoint(request())
        self.assertEqual(response["engine_version"], "MX_ENGINE_0.3.0")
        self.assertEqual(response["geometry"]["glass_width_mm"], 660)
        self.assertGreater(response["unit_technical_cost"], 0)
        self.assertEqual(response["order_technical_cost"], response["unit_technical_cost"])
        self.assertIn("MX-SEALING-CONFIGURABLE", {row["material_code"] for row in response["bom"]})

    def test_quantity_is_serialized_and_scaled(self):
        response = calculate_maxim_ar_endpoint(request(quantity=3))
        self.assertEqual(response["quantity"], 3)
        self.assertEqual(response["order_technical_cost"], 3 * response["unit_technical_cost"])
        frame = next(row for row in response["bom"] if row["role"] == "FRAME_HORIZONTAL")
        self.assertEqual(frame["quantity_order"], 6)

    def test_invalid_glass_returns_http_422(self):
        with self.assertRaises(HTTPException) as context:
            calculate_maxim_ar_endpoint(request(glass_description="VIDRO INVENTADO"))
        self.assertEqual(context.exception.status_code, 422)

    def test_design_sealing_is_serialized(self):
        response = calculate_maxim_ar_endpoint(request(
            leaf_system="DESIGN_WINDOW_60x78",
        ))
        self.assertEqual(len([row for row in response["bom"] if row["category"] == "VEDAÇÕES"]), 3)

    def test_purchase_endpoint_returns_bars_and_zero_kerf(self):
        response = calculate_maxim_ar_purchase_plan(MaximArPurchasePlanRequest(
            items=[request()],
        ))
        plan = response["purchase_plan"]
        self.assertEqual(plan["kerf_mm"], 0)
        self.assertGreater(plan["technical_total"], 0)
        self.assertGreater(plan["procurement_total_estimate"], 0)
        pr4263 = next(line for line in plan["lines"] if line["material_code"] == "PR4263")
        self.assertEqual(pr4263["bars_required"], 2)

    def test_unified_endpoint_combines_cr_and_maxim_ar_in_engine_ffd(self):
        cr = CRItemRequest(
            width_mm=2000,
            height_mm=2000,
            quantity=1,
            leaf_count=2,
            leaf_system="PRIME_WINDOW_42x66",
        )
        response = calculate_unified_purchase_plan(UnifiedPurchasePlanRequest(
            items=[cr, request()],
        ))
        self.assertEqual(
            [item["engine_version"] for item in response["items"]],
            ["CR_ENGINE_0.5.0", "MX_ENGINE_0.3.0"],
        )
        self.assertGreater(
            response["purchase_plan"]["technical_total"],
            response["items"][0]["unit_technical_cost"],
        )

    def test_phase2_multiple_vertical_request_is_serialized(self):
        response = calculate_maxim_ar_endpoint(request(
            width_mm=440,
            height_mm=1040,
            leaf_count=2,
            orientation="VERTICAL",
        ))
        self.assertEqual(response["geometry"]["leaf_count"], 2)
        self.assertEqual(response["geometry"]["leaf_height_final_mm"], 490)
        self.assertEqual(len(response["transoms"]), 1)

    def test_phase2_screen_and_fixed_panels_are_conditional(self):
        response = calculate_maxim_ar_endpoint(request(
            width_mm=1200,
            height_mm=3000,
            screen_enabled=True,
            module_mode="MÓDULOS SEPARADOS",
            bottom_fixed_panel={"height_mm": 700},
            structural_reinforcement={"material_code": "ALUM10238"},
        ))
        self.assertEqual(response["geometry"]["screen_panel_count"], 1)
        self.assertEqual(len(response["fixed_panels"]), 1)
        self.assertIn("TL3", {item["material_code"] for item in response["bom"]})
        self.assertIn("ALUM10238", {item["material_code"] for item in response["bom"]})

    def test_ambiguous_fixed_panel_formula_returns_422(self):
        with self.assertRaises(HTTPException) as context:
            calculate_maxim_ar_endpoint(request(
                width_mm=1800,
                height_mm=3000,
                leaf_grid={"horizontal_transoms": 1},
            ))
        self.assertEqual(context.exception.status_code, 422)

    def test_unified_plan_accepts_cr_plus_complex_maxim_ar(self):
        cr = CRItemRequest(
            width_mm=2000,
            height_mm=2000,
            quantity=1,
            leaf_count=2,
            leaf_system="PRIME_WINDOW_42x66",
        )
        mx = request(
            width_mm=1600,
            height_mm=5000,
            quantity=2,
            leaf_count=8,
            leaf_system="DESIGN_WINDOW_60x78",
            orientation="VERTICAL",
            glass_description="20mm DUPLO FLOAT INCOLOR (4/10/6)",
            closure_mode="MAÇANETA COM CREMONA",
            cremona_description="CREMONA MAXIM-AR 2 PONTOS COMP. 800mm",
            screen_enabled=True,
        )
        response = calculate_unified_purchase_plan(UnifiedPurchasePlanRequest(
            items=[cr, mx],
            kerf_mm=3,
        ))
        self.assertEqual(response["purchase_plan"]["kerf_mm"], 3)
        self.assertEqual(
            [item["engine_version"] for item in response["items"]],
            ["CR_ENGINE_0.5.0", "MX_ENGINE_0.3.0"],
        )
        self.assertIn(
            "DE6072",
            {line["material_code"] for line in response["purchase_plan"]["lines"]},
        )

    def test_maxim_ar_purchase_plan_consolidates_distinct_phase2_items(self):
        response = calculate_maxim_ar_purchase_plan(MaximArPurchasePlanRequest(
            items=[
                request(width_mm=500, height_mm=600, screen_enabled=True),
                request(
                    width_mm=1550,
                    height_mm=3760,
                    leaf_system="DESIGN_WINDOW_60x78",
                    glass_description="06mm TEMPERADO INCOLOR",
                    bottom_fixed_panel={"height_mm": 1000},
                    top_fixed_panel={"height_mm": 1000},
                ),
            ],
        ))
        self.assertEqual(len(response["items"]), 2)
        self.assertEqual(
            [item["engine_version"] for item in response["items"]],
            ["MX_ENGINE_0.3.0", "MX_ENGINE_0.3.0"],
        )
        self.assertGreater(response["purchase_plan"]["lines"][0]["pieces_count"], 0)


if __name__ == "__main__":
    unittest.main()
