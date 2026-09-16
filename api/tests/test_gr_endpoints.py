import sys
from pathlib import Path
import unittest

from fastapi import HTTPException


API_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = API_ROOT.parent
sys.path.insert(0, str(REPO_ROOT))

from api.app.main import calculate_gr_endpoint, gr_options, health  # noqa: E402
from api.app.schemas import GrItemRequest  # noqa: E402

MONO = "MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE"
MULTI = "MAÇANETA DUPLA COM FECHADURA MULTIPONTO E CHAVE"


def request(**overrides):
    values = {
        "width_mm": 900,
        "height_mm": 2100,
        "quantity": 1,
    }
    values.update(overrides)
    return GrItemRequest(**values)


class GrEndpointTests(unittest.TestCase):
    def test_health_exposes_gr_candidate_engine(self):
        response = health()
        self.assertEqual(response["engine"], "CR_ENGINE_0.5.0")
        self.assertEqual(
            response["engines"],
            ["CR_ENGINE_0.5.0", "MX_ENGINE_0.3.0", "GR_ENGINE_0.2.0"],
        )

    def test_options_expose_only_proven_phase2_scope(self):
        response = gr_options()
        self.assertEqual(response["engine_version"], "GR_ENGINE_0.2.0")
        self.assertEqual(response["leaf_counts"], [1])
        self.assertEqual(response["panel_modes"], ["PAINEL COMPLETO"])
        self.assertEqual(response["closures"], [MONO, MULTI])
        self.assertFalse(response["screen"]["supported"])
        self.assertFalse(response["shutter"]["supported"])
        self.assertFalse(response["purchase_plan"]["supported"])
        self.assertEqual(response["technical_gate"]["status"], "CANDIDATO À AUDITORIA")

    def test_calculate_serializes_gr_monopoint_golden(self):
        response = calculate_gr_endpoint(request(closure_mode=MONO))
        self.assertEqual(response["engine_version"], "GR_ENGINE_0.2.0")
        self.assertEqual(response["geometry"]["leaf_width_final_mm"], 836)
        self.assertEqual(response["geometry"]["panel_bead_width_mm"], 664)
        self.assertEqual(response["unit_technical_cost"], 1384.723645)
        self.assertEqual(response["order_technical_cost"], 1384.723645)
        self.assertIn("FEC6", {row["material_code"] for row in response["bom"]})

    def test_calculate_serializes_gr_multipoint_golden(self):
        response = calculate_gr_endpoint(request(closure_mode=MULTI))
        self.assertEqual(response["engine_version"], "GR_ENGINE_0.2.0")
        self.assertEqual(response["unit_technical_cost"], 1452.523645)
        self.assertIn("FEC5", {row["material_code"] for row in response["bom"]})
        self.assertIn("CON1", {row["material_code"] for row in response["bom"]})
        screws = next(row for row in response["bom"] if row["role"] == "HARDWARE_SCREWS")
        self.assertEqual(screws["quantity_per_unit"], 36)

    def test_quantity_scales_serialized_order_cost(self):
        response = calculate_gr_endpoint(request(quantity=3))
        self.assertEqual(response["quantity"], 3)
        self.assertEqual(response["order_technical_cost"], 3 * response["unit_technical_cost"])
        hinge = next(row for row in response["bom"] if row["role"] == "HINGE_90MM")
        self.assertEqual(hinge["quantity_order"], 9)

    def test_impossible_dimensions_return_http_422(self):
        with self.assertRaises(HTTPException) as context:
            calculate_gr_endpoint(request(width_mm=230))
        self.assertEqual(context.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
