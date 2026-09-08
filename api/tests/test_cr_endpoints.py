import sys
from pathlib import Path
import unittest

from fastapi import HTTPException


API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parent
sys.path.insert(0, str(REPO_ROOT))

from api.app.main import calculate_cr, calculate_purchase_plan, cr_options, health  # noqa: E402
from api.app.schemas import CRItemRequest, PurchasePlanRequest  # noqa: E402


COMMON = {
    "quantity": 1,
    "leaf_count": 2,
    "application": "JANELA",
    "closure_mode": "MACANETA COM CREMONA + FECHO OCULTO",
    "cremona_base": "CREMONA 1 PONTO",
    "roller_description": "ROLDANA 30KG",
    "internal_finish": "GUARNICAO DE 70MM",
    "external_finish": "BARRA CHATA DE 30MM",
}


def golden_payload():
    specifications = [
        (3500, 2000, "PRIME_WINDOW_42x66", "04mm FLOAT INCOLOR", {}),
        (2000, 2000, "DESIGN_DOOR_60x111", "04mm FLOAT INCOLOR", {}),
        (
            1500,
            3000,
            "PRIME_WINDOW_42x66",
            "05mm FLOAT FUME",
            {
                "closure_mode": "MACANETA COM CREMONA",
                "roller_description": "ROLDANA 50KG",
            },
        ),
        (2000, 2000, "PRIME_WINDOW_42x66", "04mm FLOAT INCOLOR", {}),
    ]
    return PurchasePlanRequest(
        items=[
            CRItemRequest(
                width_mm=width,
                height_mm=height,
                leaf_system=system,
                glass_description=glass,
                **(COMMON | overrides),
            )
            for width, height, system, glass, overrides in specifications
        ]
    )


class CREndpointTests(unittest.TestCase):
    def test_calculate_serializes_geometry_bom_costs_and_warnings(self):
        response = calculate_cr(
            CRItemRequest(
                width_mm=2000,
                height_mm=2000,
                leaf_system="DESIGN_DOOR_60x111",
                glass_description="04mm FLOAT INCOLOR",
                **COMMON,
            )
        )
        self.assertEqual(response["engine_version"], "CR_ENGINE_0.5.0")
        self.assertEqual(response["geometry"]["leaf_width_final_mm"], 1011.5)
        self.assertEqual(response["geometry"]["glass_width_mm"], 817.5)
        self.assertAlmostEqual(response["unit_technical_cost"], 2694.73947, places=5)
        self.assertEqual(response["order_technical_cost"], response["unit_technical_cost"])
        self.assertIn("DE5013", {component["material_code"] for component in response["bom"]})
        self.assertIn("DT-CR-003", {warning["code"] for warning in response["warnings"]})

    def test_purchase_endpoint_preserves_current_golden(self):
        response = calculate_purchase_plan(golden_payload())
        plan = response["purchase_plan"]
        self.assertEqual(len(response["items"]), 4)
        self.assertAlmostEqual(plan["technical_total"], 8317.53971, places=5)
        self.assertAlmostEqual(plan["bar_stock_purchase_cost"], 8201.531, places=3)
        self.assertAlmostEqual(plan["procurement_total_estimate"], 10091.36931, places=5)
        self.assertEqual(
            next(line for line in plan["lines"] if line["material_code"] == "DE5013")[
                "bars_required"
            ],
            1,
        )

    def test_invalid_hardware_returns_http_422_instead_of_partial_quote(self):
        item = CRItemRequest(
            width_mm=1500,
            height_mm=1200,
            leaf_count=2,
            leaf_system="PRIME_WINDOW_42x66",
            roller_description="ROLDANA INEXISTENTE",
        )
        with self.assertRaises(HTTPException) as caught:
            calculate_cr(item)
        self.assertEqual(caught.exception.status_code, 422)
        self.assertIn("Roldana", caught.exception.detail)

    def test_phase1_grid_fixed_panels_and_glass_are_serialized(self):
        response = calculate_cr(CRItemRequest(
            width_mm=2400,
            height_mm=2800,
            quantity=2,
            leaf_count=4,
            leaf_system="DESIGN_DOOR_60x111",
            leaf_grid={
                "horizontal_transoms": 1,
                "vertical_transoms": 1,
                "custom_dimensions": [],
            },
            bottom_fixed_panel={
                "height_mm": 400,
                "horizontal_transoms": 1,
                "vertical_transoms": 1,
            },
            top_fixed_panel={"height_mm": 450},
            structural_reinforcement={"material_code": "ALUM10238"},
        ))

        self.assertEqual(response["engine_version"], "CR_ENGINE_0.5.0")
        self.assertEqual(response["geometry"]["frame_height_final_mm"], 1950)
        self.assertEqual(len(response["fixed_panels"]), 2)
        self.assertEqual(response["fixed_panels"][0]["frame_height_mm"], 350)
        self.assertEqual(response["fixed_panels"][1]["frame_height_mm"], 400)
        self.assertEqual(response["geometry"]["total_glass_panel_count"], 21)
        self.assertEqual(
            sum(panel["quantity"] for panel in response["glass_panels"]),
            21,
        )
        self.assertTrue(any(
            component["role"] == "STRUCTURAL_REINFORCEMENT"
            and component["material_code"] == "ALUM10238"
            for component in response["bom"]
        ))

    def test_purchase_api_exposes_zero_kerf_premise(self):
        payload = golden_payload()
        response = calculate_purchase_plan(payload)
        self.assertEqual(response["purchase_plan"]["kerf_mm"], 0)
        self.assertTrue(all(
            line["kerf_loss_mm"] == 0
            for line in response["purchase_plan"]["lines"]
        ))

    def test_phase2_options_expose_complete_excel_shutter_inventory(self):
        options = cr_options()
        self.assertIs(options["shutter"]["supported"], True)
        self.assertEqual(len(options["shutter"]["modes"]), 10)
        self.assertEqual(options["shutter"]["boxes"], ["CAIXA DE 200MM"])
        self.assertEqual(options["shutter"]["slats"], ["TALA DE PVC 40MM"])
        self.assertEqual(health()["engine"], "CR_ENGINE_0.5.0")

    def test_phase2_explicit_shutter_is_converted_and_serialized(self):
        response = calculate_cr(CRItemRequest(
            width_mm=2400,
            height_mm=2600,
            leaf_count=3,
            leaf_system="PRIME_DOOR_42x88",
            screen_enabled=True,
            shutter={
                "mode": "AUTOMATIZADA COM CONTROLE REMOTO EM 2 PAINÉIS",
                "box_description": "CAIXA DE 200MM",
                "slat_description": "TALA DE PVC 40MM",
            },
        ))
        roles = {component["role"] for component in response["bom"]}
        self.assertEqual(response["engine_version"], "CR_ENGINE_0.5.0")
        self.assertEqual(response["geometry"]["frame_height_final_mm"], 2400)
        self.assertEqual(response["geometry"]["screen_frame_count"], 2)
        self.assertIn("SHUTTER_BOX", roles)
        self.assertIn("SHUTTER_REMOTE_MOTOR", roles)
        self.assertIn("PERSIANA", response["cost_by_group"])


if __name__ == "__main__":
    unittest.main()
