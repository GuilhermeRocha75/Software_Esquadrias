import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import (  # noqa: E402
    GrConfiguration,
    ShutterConfiguration,
    ShutterMode,
    calculate_gr,
)

INTERNAL = "FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN"
EXTERNAL = "FOLHA DE PORTA ABERTURA EXTERNA 60X104MM - DESIGN"
MONO = "MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE"


def independent(**overrides):
    values = {
        "width_mm": 2550,
        "height_mm": 2260,
        "quantity": 1,
        "leaf_count": 2,
        "leaf_system": INTERNAL,
        "application": "PORTA",
        "panel_mode": "VIDRO INTEIRO",
        "glass_description": "06mm TEMPERADO INCOLOR",
        "closure_mode": MONO,
        "hinge_description": "DOBRADIÇA 90MM",
        "shutter": ShutterConfiguration(
            mode=ShutterMode.MANUAL_DOUBLE_INDEPENDENT_SHAFTS,
            box_description="CAIXA DE 200MM",
            slat_description="TALA DE PVC 40MM",
        ),
    }
    values.update(overrides)
    return GrConfiguration(**values)


class GrPhase13Tests(unittest.TestCase):
    def test_version_is_v013(self):
        self.assertEqual(
            calculate_gr(independent()).calculation_version,
            "GR_ENGINE_0.13.0",
        )

    def test_orcs_4109_geometry_and_cost_are_frozen(self):
        result = calculate_gr(independent())
        self.assertEqual(
            result.model_description,
            "PORTA 2 FOLHAS DE GIRO COM PERSIANA MANUAL 2 PAINÉIS EIXOS INDEPENDENTES",
        )
        self.assertEqual(result.geometry["shutter_main_opening_height_mm"], 2060.0)
        self.assertEqual(result.geometry["leaf_width_final_mm"], 1233.0)
        self.assertEqual(result.geometry["leaf_height_final_mm"], 2023.0)
        self.assertEqual(result.geometry["glass_width_mm"], 1053.0)
        self.assertEqual(result.geometry["glass_height_mm"], 1843.0)
        self.assertEqual(result.geometry["shutter_panel_count"], 2.0)
        self.assertEqual(result.geometry["shutter_box_length_mm"], 2535.0)
        self.assertEqual(result.geometry["shutter_side_guide_length_mm"], 2060.0)
        self.assertEqual(result.geometry["shutter_central_guide_length_mm"], 2060.0)
        self.assertEqual(result.geometry["shutter_slat_width_mm"], 1218.0)
        self.assertEqual(result.geometry["shutter_slat_quantity"], 114.0)
        self.assertEqual(result.geometry["shutter_shaft_length_mm"], 1235.0)
        self.assertEqual(result.geometry["shutter_shaft_quantity"], 2.0)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 62.6432)
        self.assertEqual(result.cost_breakdown["PERSIANA"], 1783.63425)
        self.assertEqual(result.unit_cost, 4503.65075)

    def test_two_independent_shafts_and_only_independent_divider(self):
        result = calculate_gr(independent())
        shaft = next(x for x in result.unit_bom if x.role == "SHUTTER_SHAFT")
        self.assertEqual(shaft.material_code, "375021")
        self.assertEqual(shaft.quantity_per_unit, 2.0)
        codes = {x.material_code for x in result.unit_bom if x.category == "PERSIANA"}
        self.assertIn("371127", codes)
        self.assertNotIn("371143", codes)
        warnings = {x.code for x in result.warnings}
        self.assertIn("LEGACY-GR-SHUTTER-INDEPENDENT-SHAFT-QTY-CORRECTED", warnings)
        self.assertIn("LEGACY-GR-SHUTTER-DIVIDER-TYPO-CORRECTED", warnings)

    def test_independent_manual_kit_quantities(self):
        result = calculate_gr(independent())
        by_role = {x.role: x for x in result.unit_bom}
        expected = {
            "SHUTTER_SIDE_GUIDE": 2.0,
            "SHUTTER_CENTRAL_GUIDE": 1.0,
            "SHUTTER_TERMINAL": 2.0,
            "SHUTTER_SHAFT": 2.0,
            "SHUTTER_LATERAL_COVER": 2.0,
            "SHUTTER_PULLEY_PLATE": 2.0,
            "SHUTTER_INDEPENDENT_SHAFT_DIVIDER": 1.0,
            "SHUTTER_PULLEY": 2.0,
            "SHUTTER_END_CAP": 2.0,
            "SHUTTER_END_CAP_ADAPTER": 2.0,
            "SHUTTER_RECESSED_WINDER": 2.0,
            "SHUTTER_GUIDE_INVITATION_PAIR": 1.0,
            "SHUTTER_FIRST_SLAT_COUPLING": 4.0,
            "SHUTTER_FRONT_PIN": 2.0,
            "SHUTTER_OPENING_LIMITER": 4.0,
        }
        for role, quantity in expected.items():
            with self.subTest(role=role):
                self.assertEqual(by_role[role].quantity_per_unit, quantity)

    def test_fractional_legacy_slat_count_rounds_each_panel_up(self):
        result = calculate_gr(independent())
        # legado: (2260 / 40) * 2 = 113; físico: ceil(56.5) * 2 = 114.
        self.assertEqual(result.geometry["shutter_slat_quantity"], 114.0)
        warnings = {x.code for x in result.warnings}
        self.assertIn("LEGACY-GR-SHUTTER-SLAT-FRACTION", warnings)

    def test_external_door_reuses_same_shutter_geometry(self):
        internal = calculate_gr(independent())
        external = calculate_gr(independent(leaf_system=EXTERNAL))
        for key in (
            "shutter_panel_count",
            "shutter_box_length_mm",
            "shutter_side_guide_length_mm",
            "shutter_central_guide_length_mm",
            "shutter_slat_width_mm",
            "shutter_slat_quantity",
            "shutter_shaft_length_mm",
            "shutter_shaft_quantity",
        ):
            self.assertEqual(internal.geometry[key], external.geometry[key])
        self.assertIn("DE60104-E", {x.material_code for x in external.unit_bom})

    def test_wrong_leaf_count_or_application_is_blocked(self):
        with self.assertRaises(ValueError):
            calculate_gr(independent(leaf_count=1))
        with self.assertRaises(ValueError):
            calculate_gr(independent(application="JANELA"))

    def test_quantity_scales_order_bom_only(self):
        one = calculate_gr(independent(quantity=1))
        three = calculate_gr(independent(quantity=3))
        self.assertEqual(one.unit_cost, three.unit_cost)
        for item in three.unit_bom:
            self.assertEqual(item.quantity_order, item.quantity_per_unit * 3)

    def test_cost_is_exact_sum_of_bom(self):
        result = calculate_gr(independent())
        self.assertEqual(
            result.unit_cost,
            round(sum(x.cost_per_unit_product for x in result.unit_bom), 6),
        )
        self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)

    def test_golden_v013_is_frozen(self):
        golden = json.loads(
            (ROOT / "test_cases" / "gr_golden_v0_13.json").read_text(encoding="utf-8")
        )
        self.assertEqual(golden["engine_version"], "GR_ENGINE_0.13.0")
        for case in golden["cases"]:
            with self.subTest(case=case["id"]):
                raw = dict(case["input"])
                raw["shutter"] = ShutterConfiguration(
                    mode=ShutterMode(raw["shutter"]["mode"]),
                    box_description=raw["shutter"]["box_description"],
                    slat_description=raw["shutter"]["slat_description"],
                )
                result = calculate_gr(GrConfiguration(**raw))
                self.assertEqual(result.calculation_version, golden["engine_version"])
                self.assertEqual(result.unit_cost, case["unit_cost"])
                self.assertEqual(result.cost_breakdown["VEDAÇÕES"], case["sealing_cost"])
                self.assertEqual(result.cost_breakdown["PERSIANA"], case["shutter_cost"])
                for key, expected in case["geometry"].items():
                    self.assertEqual(result.geometry[key], expected)


if __name__ == "__main__":
    unittest.main()
