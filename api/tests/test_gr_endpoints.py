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
WINDOW_CREMONA = "MAÇANETA COM CREMONA SEM CHAVE"
CREMONA_800 = "CREMONA 2 PONTOS COMP. 800mm E:15mm"
INTERNAL = "FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN"
EXTERNAL = "FOLHA DE PORTA ABERTURA EXTERNA 60X104MM - DESIGN"
WINDOW = "FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN"


def request(**overrides):
    values = {
        "width_mm": 900,
        "height_mm": 2100,
        "quantity": 1,
    }
    values.update(overrides)
    return GrItemRequest(**values)


def window_request(**overrides):
    values = {
        "width_mm": 800,
        "height_mm": 1300,
        "quantity": 1,
        "leaf_system": WINDOW,
        "application": "JANELA",
        "closure_mode": WINDOW_CREMONA,
        "cremona_description": CREMONA_800,
    }
    values.update(overrides)
    return GrItemRequest(**values)


def glass_request(**overrides):
    values = {
        "width_mm": 800,
        "height_mm": 2100,
        "quantity": 1,
        "panel_mode": "VIDRO INTEIRO",
        "glass_description": "06mm TEMPERADO INCOLOR",
    }
    values.update(overrides)
    return GrItemRequest(**values)


def two_leaf_glass_request(**overrides):
    values = {
        "width_mm": 1200,
        "height_mm": 2100,
        "quantity": 1,
        "leaf_count": 2,
        "leaf_system": INTERNAL,
        "application": "PORTA",
        "panel_mode": "VIDRO INTEIRO",
        "glass_description": "06mm TEMPERADO INCOLOR",
        "closure_mode": MONO,
    }
    values.update(overrides)
    return GrItemRequest(**values)


class GrEndpointTests(unittest.TestCase):
    def test_health_exposes_gr_candidate_engine(self):
        response = health()
        self.assertEqual(response["engine"], "CR_ENGINE_0.5.0")
        self.assertEqual(
            response["engines"],
            ["CR_ENGINE_0.5.0", "MX_ENGINE_0.3.0", "GR_ENGINE_0.7.0"],
        )

    def test_options_expose_phase7_physical_scope(self):
        response = gr_options()
        self.assertEqual(response["engine_version"], "GR_ENGINE_0.7.0")
        self.assertEqual(response["phase"], 7)
        self.assertEqual(response["applications"], ["PORTA", "JANELA"])
        self.assertEqual(response["leaf_counts"], [1, 2])
        self.assertEqual(
            {row["value"] for row in response["leaf_systems"]},
            {INTERNAL, EXTERNAL, WINDOW},
        )
        self.assertEqual(response["panel_modes"], ["PAINEL COMPLETO", "VIDRO INTEIRO"])
        self.assertTrue(response["glass_mode"]["supported"])
        self.assertEqual(response["glass_mode"]["applications"], ["PORTA"])
        self.assertEqual(response["glass_mode"]["leaf_counts"], [1, 2])
        self.assertEqual(response["glass_mode"]["historical_one_leaf_cases"], 125)
        self.assertEqual(response["glass_mode"]["historical_two_leaf_cases"], 58)
        self.assertEqual(response["glass_mode"]["two_leaf_reference_orcs_row"], 17138)
        self.assertFalse(response["glass_mode"]["window_glass"]["supported"])
        self.assertIn("6TI", {row["code"] for row in response["glass_mode"]["glasses"]})
        self.assertEqual(response["closures"], [MONO, MULTI, WINDOW_CREMONA])
        self.assertEqual(response["cremonas"]["window_default"], CREMONA_800)
        self.assertEqual(response["panel_squaring_blocks"]["quantity_per_leaf"], 4)
        self.assertEqual(response["panel_squaring_blocks"]["status"], "RESOLVED_PHYSICAL")
        self.assertEqual(response["sealing"]["status"], "LEGACY_BUG_CONFIRMED")
        self.assertEqual(
            [row["catalog_code"] for row in response["sealing"]["paths"]],
            ["ACB606", "AC0002", "AC0002"],
        )
        self.assertEqual(response["two_leaf_door"]["historical_glass_cases"], 58)
        self.assertEqual(response["two_leaf_door"]["panel_rule_status"], "LEGACY_BUG_CONFIRMED")
        self.assertFalse(response["screen"]["supported"])
        self.assertFalse(response["shutter"]["supported"])
        self.assertFalse(response["purchase_plan"]["supported"])
        self.assertEqual(response["technical_gate"]["status"], "CANDIDATO À AUDITORIA")
        self.assertEqual(response["technical_gate"]["open_questions"], [])

    def test_panel_monopoint_uses_physical_sealing_cost(self):
        response = calculate_gr_endpoint(request(closure_mode=MONO))
        self.assertEqual(response["engine_version"], "GR_ENGINE_0.7.0")
        self.assertEqual(response["geometry"]["leaf_width_final_mm"], 836)
        self.assertEqual(response["geometry"]["panel_bead_width_mm"], 664)
        self.assertEqual(response["cost_by_group"]["VEDAÇÕES"], 27.7516)
        self.assertEqual(response["unit_technical_cost"], 1412.475245)
        self.assertEqual(response["order_technical_cost"], 1412.475245)
        roles = {row["role"] for row in response["bom"]}
        self.assertIn("GLASS_OR_LAMBRI_SEAL", roles)
        self.assertIn("ROUND_SEAL_LEAF", roles)
        self.assertIn("ROUND_SEAL_FRAME", roles)

    def test_panel_multipoint_preserves_hardware_delta(self):
        mono = calculate_gr_endpoint(request(closure_mode=MONO))
        multi = calculate_gr_endpoint(request(closure_mode=MULTI))
        self.assertEqual(multi["unit_technical_cost"], 1480.275245)
        self.assertEqual(round(multi["unit_technical_cost"] - mono["unit_technical_cost"], 6), 67.8)
        self.assertIn("FEC5", {row["material_code"] for row in multi["bom"]})
        screws = next(row for row in multi["bom"] if row["role"] == "HARDWARE_SCREWS")
        self.assertEqual(screws["quantity_per_unit"], 36)

    def test_external_opening_uses_physical_sealing(self):
        response = calculate_gr_endpoint(request(
            width_mm=800,
            height_mm=2150,
            leaf_system=EXTERNAL,
            closure_mode=MULTI,
        ))
        self.assertEqual(response["engine_version"], "GR_ENGINE_0.7.0")
        self.assertEqual(response["cost_by_group"]["VEDAÇÕES"], 27.2516)
        self.assertEqual(response["unit_technical_cost"], 1445.782455)
        leaf_codes = {row["material_code"] for row in response["bom"] if row["role"] in {"LEAF_WIDTH", "LEAF_HEIGHT"}}
        self.assertEqual(leaf_codes, {"DE60104-E"})

    def test_window_panel_receives_same_confirmed_sealing_roles(self):
        response = calculate_gr_endpoint(window_request())
        self.assertEqual(response["engine_version"], "GR_ENGINE_0.7.0")
        self.assertEqual(response["model_description"], "JANELA 1 FOLHA DE GIRO COM PAINEL HORIZONTAL")
        self.assertEqual(response["cost_by_group"]["VEDAÇÕES"], 18.856)
        self.assertEqual(response["unit_technical_cost"], 846.578384)
        seals = [row for row in response["bom"] if row["category"] == "VEDAÇÕES"]
        self.assertEqual(len(seals), 3)
        self.assertEqual({row["material_code"] for row in seals}, {"ACB606", "AC0002"})

    def test_two_leaf_door_includes_panel_fix_and_physical_sealing(self):
        response = calculate_gr_endpoint(request(
            width_mm=1600,
            height_mm=2100,
            leaf_count=2,
            leaf_system=INTERNAL,
            closure_mode=MONO,
        ))
        self.assertEqual(response["engine_version"], "GR_ENGINE_0.7.0")
        self.assertEqual(response["geometry"]["panel_fill_strip_quantity"], 25.528571)
        self.assertEqual(response["cost_by_group"]["VEDAÇÕES"], 53.9432)
        self.assertEqual(response["unit_technical_cost"], 2277.196098)
        codes = {row["material_code"] for row in response["bom"]}
        self.assertIn("FEC7", codes)
        self.assertIn("CON3", codes)
        block = next(row for row in response["bom"] if row["material_code"] == "AC0312")
        self.assertEqual(block["quantity_per_unit"], 8)

    def test_one_leaf_glass_remains_frozen(self):
        response = calculate_gr_endpoint(glass_request())
        self.assertEqual(response["engine_version"], "GR_ENGINE_0.7.0")
        self.assertEqual(response["model_description"], "PORTA 1 FOLHA DE GIRO")
        self.assertEqual(response["geometry"]["glass_bead_width_mm"], 564)
        self.assertEqual(response["geometry"]["glass_bead_height_mm"], 1891)
        self.assertEqual(response["geometry"]["glass_width_mm"], 556)
        self.assertEqual(response["geometry"]["glass_height_mm"], 1883)
        self.assertEqual(response["geometry"]["glass_panel_count"], 1.0)
        self.assertEqual(response["cost_by_group"]["VEDAÇÕES"], 26.7516)
        self.assertEqual(response["unit_technical_cost"], 1358.19195)
        self.assertEqual(len(response["glass_panels"]), 1)
        self.assertEqual(response["glass_panels"][0]["material_code"], "6TI")
        codes = {row["material_code"] for row in response["bom"]}
        self.assertIn("BA3518", codes)
        self.assertNotIn("DE20150", codes)
        warning_codes = {row["code"] for row in response["warnings"]}
        self.assertIn("LEGACY-GR-SEALING-CORRECTED", warning_codes)

    def test_orcs_17138_two_leaf_glass_is_serialized_with_physical_sealing(self):
        response = calculate_gr_endpoint(two_leaf_glass_request())
        self.assertEqual(response["engine_version"], "GR_ENGINE_0.7.0")
        self.assertEqual(response["model_description"], "PORTA 2 FOLHAS DE GIRO")
        self.assertEqual(response["geometry"]["leaf_width_final_mm"], 558)
        self.assertEqual(response["geometry"]["glass_bead_width_mm"], 386)
        self.assertEqual(response["geometry"]["glass_bead_height_mm"], 1891)
        self.assertEqual(response["geometry"]["glass_width_mm"], 378)
        self.assertEqual(response["geometry"]["glass_height_mm"], 1883)
        self.assertEqual(response["geometry"]["glass_panel_count"], 2.0)
        self.assertEqual(response["cost_by_group"]["VEDAÇÕES"], 49.9432)
        self.assertEqual(response["unit_technical_cost"], 2071.84485)
        self.assertEqual(round(response["unit_technical_cost"] - response["cost_by_group"]["VEDAÇÕES"], 6), 2021.90165)
        glass = next(row for row in response["bom"] if row["role"] == "GLASS_PANEL")
        self.assertEqual(glass["quantity_per_unit"], 2.0)
        self.assertEqual(glass["area_m2"], 0.711774)
        self.assertEqual(glass["cost_per_unit_product"], 177.9435)
        block = next(row for row in response["bom"] if row["material_code"] == "AC0312")
        self.assertEqual(block["quantity_per_unit"], 8.0)
        self.assertEqual(response["glass_panels"][0]["quantity"], 2.0)

    def test_window_glass_remains_rejected(self):
        with self.assertRaises(HTTPException) as context:
            calculate_gr_endpoint(window_request(
                panel_mode="VIDRO INTEIRO",
                glass_description="06mm TEMPERADO INCOLOR",
            ))
        self.assertEqual(context.exception.status_code, 422)

    def test_two_leaf_window_is_rejected_by_engine(self):
        payload = window_request(leaf_count=2)
        with self.assertRaises(HTTPException) as context:
            calculate_gr_endpoint(payload)
        self.assertEqual(context.exception.status_code, 422)

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
