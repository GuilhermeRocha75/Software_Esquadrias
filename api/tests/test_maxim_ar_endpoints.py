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
        self.assertEqual(response["engines"], ["CR_ENGINE_0.5.0", "MX_ENGINE_0.1.0"])

    def test_options_expose_only_phase1_proven_variants(self):
        response = maxim_ar_options()
        self.assertEqual(response["engine_version"], "MX_ENGINE_0.1.0")
        self.assertEqual(response["leaf_counts"], [1])
        self.assertEqual(response["orientations"], ["HORIZONTAL"])
        self.assertFalse(response["screen"]["supported"])
        self.assertEqual(
            {row["value"] for row in response["leaf_systems"]},
            {"PRIME_WINDOW_42x63", "DESIGN_WINDOW_60x78"},
        )

    def test_calculate_serializes_excel_golden(self):
        response = calculate_maxim_ar_endpoint(request())
        self.assertEqual(response["engine_version"], "MX_ENGINE_0.1.0")
        self.assertEqual(response["geometry"]["glass_width_mm"], 660)
        self.assertEqual(response["cost_by_group"]["TOTAL"], 419.7804)
        self.assertEqual(response["unit_technical_cost"], 419.7804)
        self.assertEqual(response["order_technical_cost"], 419.7804)
        self.assertIn("AC0002", {row["material_code"] for row in response["bom"]})

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

    def test_design_warning_is_serialized(self):
        response = calculate_maxim_ar_endpoint(request(
            leaf_system="DESIGN_WINDOW_60x78",
        ))
        self.assertIn(
            "LEGACY-MX-DESIGN-SEALING-OMITTED",
            {warning["code"] for warning in response["warnings"]},
        )

    def test_purchase_endpoint_returns_bars_and_zero_kerf(self):
        response = calculate_maxim_ar_purchase_plan(MaximArPurchasePlanRequest(
            items=[request()],
        ))
        plan = response["purchase_plan"]
        self.assertEqual(plan["kerf_mm"], 0)
        self.assertEqual(plan["technical_total"], 419.7804)
        self.assertEqual(plan["procurement_total_estimate"], 637.159)
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
            ["CR_ENGINE_0.5.0", "MX_ENGINE_0.1.0"],
        )
        self.assertGreater(
            response["purchase_plan"]["technical_total"],
            response["items"][0]["unit_technical_cost"],
        )


if __name__ == "__main__":
    unittest.main()
