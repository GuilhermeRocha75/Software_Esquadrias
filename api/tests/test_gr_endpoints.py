import sys
from pathlib import Path
import unittest

from fastapi import HTTPException
from pydantic import ValidationError

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
    values = {"width_mm": 900, "height_mm": 2100, "quantity": 1}
    values.update(overrides)
    return GrItemRequest(**values)


def window_request(**overrides):
    values = {
        "width_mm": 800, "height_mm": 1300, "quantity": 1,
        "leaf_system": WINDOW, "application": "JANELA",
        "closure_mode": WINDOW_CREMONA, "cremona_description": CREMONA_800,
    }
    values.update(overrides)
    return GrItemRequest(**values)


def window_glass_request(**overrides):
    values = {
        "width_mm": 700, "height_mm": 2500, "quantity": 1,
        "leaf_system": WINDOW, "application": "JANELA",
        "panel_mode": "VIDRO INTEIRO",
        "glass_description": "06mm TEMPERADO INCOLOR",
        "closure_mode": WINDOW_CREMONA,
        "cremona_description": CREMONA_800,
        "hinge_description": "DOBRADIÇA 90MM",
    }
    values.update(overrides)
    return GrItemRequest(**values)


def ob_window_glass_request(**overrides):
    values = {
        "width_mm": 800, "height_mm": 1000, "quantity": 1,
        "leaf_system": WINDOW, "application": "JANELA",
        "panel_mode": "VIDRO INTEIRO",
        "glass_description": "06mm TEMPERADO INCOLOR",
        "closure_mode": WINDOW_CREMONA,
        "cremona_description": "CREMONA OSCILO/GIRO COMP. 1100mm E:15mm",
        "hinge_description": "DOBRADIÇA SISTEMA OB",
    }
    values.update(overrides)
    return GrItemRequest(**values)


def mixed_request(**overrides):
    values = {
        "width_mm": 800, "height_mm": 2100, "quantity": 1,
        "leaf_count": 1, "leaf_system": INTERNAL, "application": "PORTA",
        "panel_mode": "SUPERIOR VIDRO/INFERIOR PAINEL",
        "glass_description": "04mm FLOAT INCOLOR",
        "mixed_split_from_bottom_mm": 900,
        "closure_mode": MONO,
        "hinge_description": "DOBRADIÇA 90MM",
    }
    values.update(overrides)
    return GrItemRequest(**values)


def two_leaf_glass_request(**overrides):
    values = {
        "width_mm": 1200, "height_mm": 2100, "quantity": 1,
        "leaf_count": 2, "leaf_system": INTERNAL, "application": "PORTA",
        "panel_mode": "VIDRO INTEIRO",
        "glass_description": "06mm TEMPERADO INCOLOR", "closure_mode": MONO,
    }
    values.update(overrides)
    return GrItemRequest(**values)


class GrEndpointTests(unittest.TestCase):
    def test_health_exposes_v010(self):
        response = health()
        self.assertEqual(response["engine"], "CR_ENGINE_0.5.0")
        self.assertEqual(response["engines"], ["CR_ENGINE_0.5.0", "MX_ENGINE_0.3.0", "GR_ENGINE_0.10.0"])

    def test_options_expose_phase10_and_mixed_scope(self):
        response = gr_options()
        self.assertEqual(response["engine_version"], "GR_ENGINE_0.10.0")
        self.assertEqual(response["phase"], 10)
        self.assertTrue(response["glass_mode"]["window_glass"]["supported"])
        self.assertEqual(response["glass_mode"]["window_glass"]["hinge_description"], "DOBRADIÇA 90MM")
        self.assertEqual(response["glass_mode"]["window_glass"]["cremona_default"], CREMONA_800)
        self.assertEqual(response["glass_mode"]["window_glass"]["historical_clean_90mm_cases"], 12)
        self.assertTrue(response["glass_mode"]["window_glass"]["ob_hinge_supported"])
        self.assertEqual(
            response["glass_mode"]["window_glass"]["ob_hinge_description"],
            "DOBRADIÇA SISTEMA OB",
        )
        self.assertTrue(response["glass_mode"]["window_glass"]["ob_cremona_required"])
        self.assertFalse(response["glass_mode"]["window_glass"]["ob_auto_selection"])
        self.assertEqual(response["glass_mode"]["window_glass"]["historical_ob_glass_cases"], 48)
        self.assertEqual(response["glass_mode"]["window_glass"]["ob_reference_orcs_row"], 4572)
        self.assertEqual(len(response["glass_mode"]["window_glass"]["ob_cremonas"]), 5)
        self.assertEqual(response["glass_mode"]["window_glass"]["ob_evidence_status"], "RESOLVED_PHYSICAL")
        self.assertEqual(response["technical_gate"]["status"], "APROVADO_NO_ESCOPO_DA_FASE_10")
        self.assertEqual(response["technical_gate"]["open_questions"], [])
        self.assertIn("DOBRADIÇA SISTEMA OB", response["hinges"])
        self.assertTrue(response["mixed_mode"]["supported"])
        self.assertTrue(response["mixed_mode"]["split_is_flexible"])
        self.assertEqual(response["mixed_mode"]["transom_profile"], "DE6072")
        self.assertEqual(response["mixed_mode"]["transom_reinforcement"], "RAG - DE6072")
        self.assertEqual(response["mixed_mode"]["explicit_reference_orcs_rows"], [270, 285, 3560])
        self.assertEqual(response["sealing"]["status"], "LEGACY_BUG_CONFIRMED")
        self.assertFalse(response["purchase_plan"]["supported"])

    def test_panel_regression_remains_physical(self):
        response = calculate_gr_endpoint(request(closure_mode=MONO))
        self.assertEqual(response["engine_version"], "GR_ENGINE_0.10.0")
        self.assertEqual(response["unit_technical_cost"], 1412.475245)
        self.assertEqual(response["cost_by_group"]["VEDAÇÕES"], 27.7516)

    def test_external_and_multipoint_regression(self):
        mono = calculate_gr_endpoint(request(closure_mode=MONO))
        multi = calculate_gr_endpoint(request(closure_mode=MULTI))
        self.assertEqual(round(multi["unit_technical_cost"] - mono["unit_technical_cost"], 6), 67.8)
        external = calculate_gr_endpoint(request(width_mm=800, height_mm=2150, leaf_system=EXTERNAL, closure_mode=MULTI))
        self.assertEqual(external["unit_technical_cost"], 1445.782455)

    def test_window_panel_regression(self):
        response = calculate_gr_endpoint(window_request())
        self.assertEqual(response["engine_version"], "GR_ENGINE_0.10.0")
        self.assertEqual(response["unit_technical_cost"], 846.578384)
        self.assertEqual(response["cost_by_group"]["VEDAÇÕES"], 18.856)

    def test_two_leaf_door_glass_regression(self):
        response = calculate_gr_endpoint(two_leaf_glass_request())
        self.assertEqual(response["engine_version"], "GR_ENGINE_0.10.0")
        self.assertEqual(response["unit_technical_cost"], 2071.84485)
        self.assertEqual(response["geometry"]["glass_panel_count"], 2.0)
        self.assertEqual(response["cost_by_group"]["VEDAÇÕES"], 49.9432)

    def test_window_glass_6mm_serializes_v08_golden(self):
        response = calculate_gr_endpoint(window_glass_request())
        self.assertEqual(response["engine_version"], "GR_ENGINE_0.10.0")
        self.assertEqual(response["model_description"], "JANELA 1 FOLHA DE GIRO")
        self.assertEqual(response["geometry"]["glass_width_mm"], 508)
        self.assertEqual(response["geometry"]["glass_height_mm"], 2308)
        self.assertEqual(response["cost_by_group"]["VEDAÇÕES"], 29.856)
        self.assertEqual(response["unit_technical_cost"], 1214.70516)
        self.assertEqual(response["glass_panels"][0]["material_code"], "6TI")
        codes = {row["material_code"] for row in response["bom"]}
        self.assertIn("BA3518", codes)
        self.assertIn("CRE12", codes)
        self.assertNotIn("DE20150", codes)

    def test_window_glass_20mm_serializes_correct_baguette(self):
        response = calculate_gr_endpoint(window_glass_request(
            width_mm=400, height_mm=1500,
            glass_description="20mm DUPLO FLOAT INCOLOR/TEMPERADO INCOLOR (4/10/6)",
        ))
        self.assertEqual(response["unit_technical_cost"], 765.11532)
        self.assertEqual(response["geometry"]["glass_width_mm"], 208)
        self.assertEqual(response["geometry"]["glass_height_mm"], 1308)
        self.assertIn("BA2018", {row["material_code"] for row in response["bom"]})

    def test_window_glass_wrong_cremona_is_rejected_by_schema(self):
        with self.assertRaises(ValidationError):
            window_glass_request(
                cremona_description="CREMONA 2 PONTOS COMP. 1000mm E:15mm"
            )

    def test_ob_window_glass_serializes_v09_golden(self):
        response = calculate_gr_endpoint(ob_window_glass_request())
        self.assertEqual(response["engine_version"], "GR_ENGINE_0.10.0")
        self.assertEqual(response["geometry"]["glass_width_mm"], 608)
        self.assertEqual(response["geometry"]["glass_height_mm"], 808)
        self.assertEqual(response["cost_by_group"]["VEDAÇÕES"], 15.856)
        self.assertEqual(response["unit_technical_cost"], 656.42716)
        codes = {row["material_code"] for row in response["bom"]}
        for code in {"DOB6", "DOB7", "DOB8", "DOB9", "DOB10", "DOB11", "CRE23"}:
            self.assertIn(code, codes)
        self.assertNotIn("DOB3", codes)
        self.assertNotIn("CRE12", codes)
        screws = next(row for row in response["bom"] if row["role"] == "HARDWARE_SCREWS")
        self.assertEqual(screws["quantity_per_unit"], 16)
        warning_codes = {row["code"] for row in response["warnings"]}
        self.assertIn("GR-OB-CREMONA-EXPLICIT", warning_codes)

    def test_ob_window_requires_explicit_ob_cremona(self):
        with self.assertRaises(HTTPException) as context:
            calculate_gr_endpoint(ob_window_glass_request(cremona_description=None))
        self.assertEqual(context.exception.status_code, 422)

    def test_mixed_orcs_270_serializes_v010_golden(self):
        response = calculate_gr_endpoint(mixed_request())
        self.assertEqual(response["engine_version"], "GR_ENGINE_0.10.0")
        self.assertEqual(response["model_description"], "PORTA 1 FOLHA DE GIRO SUPERIOR VIDRO / INFERIOR PAINEL")
        self.assertEqual(response["geometry"]["mixed_split_from_bottom_mm"], 900)
        self.assertEqual(response["geometry"]["horizontal_transom_length_mm"], 576)
        self.assertEqual(response["geometry"]["glass_width_mm"], 556)
        self.assertEqual(response["geometry"]["glass_height_mm"], 1033)
        self.assertEqual(response["geometry"]["transom_reinforcement_screws_added"], 2)
        self.assertEqual(response["cost_by_group"]["VEDAÇÕES"], 28.5228)
        self.assertEqual(response["unit_technical_cost"], 1368.725685)
        self.assertEqual(response["transoms"][0]["material_code"], "DE6072")
        self.assertEqual(response["transoms"][0]["reinforcement_material_code"], "RAG - DE6072")

    def test_mixed_two_leaf_serializes_per_leaf_rules(self):
        response = calculate_gr_endpoint(mixed_request(
            width_mm=1670, height_mm=2050, leaf_count=2,
            mixed_split_from_bottom_mm=510,
            glass_description="06mm TEMPERADO INCOLOR",
        ))
        self.assertEqual(response["unit_technical_cost"], 2353.000615)
        self.assertEqual(response["geometry"]["glass_panel_count"], 2)
        self.assertEqual(response["geometry"]["transom_count"], 2)
        self.assertEqual(response["geometry"]["transom_reinforcement_screws_added"], 4)
        blocks = next(row for row in response["bom"] if row["role"] == "SQUARING_BLOCK")
        self.assertEqual(blocks["quantity_per_unit"], 8)

    def test_mixed_without_split_is_422(self):
        with self.assertRaises(HTTPException) as context:
            calculate_gr_endpoint(mixed_request(mixed_split_from_bottom_mm=None))
        self.assertEqual(context.exception.status_code, 422)

    def test_two_leaf_window_is_422(self):
        with self.assertRaises(HTTPException) as context:
            calculate_gr_endpoint(window_request(leaf_count=2))
        self.assertEqual(context.exception.status_code, 422)

    def test_quantity_scales_serialized_order_cost(self):
        response = calculate_gr_endpoint(window_glass_request(quantity=3))
        self.assertEqual(response["order_technical_cost"], 3 * response["unit_technical_cost"])
        glass = next(row for row in response["bom"] if row["role"] == "GLASS_PANEL")
        self.assertEqual(glass["quantity_order"], 3)

    def test_impossible_dimensions_return_422(self):
        with self.assertRaises(HTTPException) as context:
            calculate_gr_endpoint(request(width_mm=230))
        self.assertEqual(context.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
