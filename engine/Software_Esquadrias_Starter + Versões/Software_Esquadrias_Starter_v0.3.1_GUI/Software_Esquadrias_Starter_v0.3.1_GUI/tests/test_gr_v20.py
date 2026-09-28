import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import GrConfiguration, calculate_gr  # noqa: E402

EXTERNAL = "FOLHA DE PORTA ABERTURA EXTERNA 60X104MM - DESIGN"
INTERNAL = "FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN"
MONO = "MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE"


def divided_bottom_flag(**overrides):
    values = {
        "width_mm": 1980,
        "height_mm": 2150,
        "quantity": 1,
        "leaf_count": 1,
        "leaf_system": EXTERNAL,
        "application": "PORTA",
        "panel_mode": "VIDRO INTEIRO",
        "glass_description": "06mm TEMPERADO INCOLOR",
        "closure_mode": MONO,
        "hinge_description": "DOBRADIÇA SISTEMA OB",
        "bottom_flag_height_mm": 850,
        "bottom_flag_vertical_transoms": 2,
    }
    values.update(overrides)
    return GrConfiguration(**values)


def phase19_case():
    return GrConfiguration(
        width_mm=1610,
        height_mm=5220,
        quantity=1,
        leaf_count=2,
        leaf_system=INTERNAL,
        application="PORTA",
        panel_mode="VIDRO INTEIRO",
        glass_description="10mm TEMPERADO INCOLOR",
        closure_mode=MONO,
        hinge_description="DOBRADIÇA 90MM",
        top_flag_height_mm=2790,
        top_flag_vertical_transoms=1,
    )


class GrPhase20Tests(unittest.TestCase):
    def test_version_is_v020(self):
        self.assertEqual(
            calculate_gr(divided_bottom_flag()).calculation_version,
            "GR_ENGINE_0.20.0",
        )

    def test_orcs_10024_geometry_is_frozen(self):
        result = calculate_gr(divided_bottom_flag())
        expected = {
            "frame_height_final_mm": 2150.0,
            "frame_height_cut_mm": 2153.0,
            "frame_reinforcement_height_mm": 2034.0,
            "leaf_width_final_mm": 1916.0,
            "leaf_height_final_mm": 1285.0,
            "glass_width_mm": 1736.0,
            "glass_height_mm": 1105.0,
            "bottom_flag_height_mm": 850.0,
            "bottom_flag_boundary_transom_length_mm": 1912.0,
            "bottom_flag_vertical_transoms": 2.0,
            "bottom_flag_opening_count": 3.0,
            "bottom_flag_bead_width_mm": 609.333333,
            "bottom_flag_bead_height_mm": 792.0,
            "bottom_flag_glass_width_mm": 601.333333,
            "bottom_flag_glass_height_mm": 784.0,
            "bottom_flag_internal_vertical_transom_length_mm": 804.0,
            "bottom_flag_internal_vertical_reinforcement_screws_added": 6.0,
            "bottom_flag_glass_panel_count": 3.0,
        }
        for key, value in expected.items():
            self.assertEqual(result.geometry[key], value)

    def test_bottom_grid_has_three_openings_and_two_internal_verticals(self):
        result = calculate_gr(divided_bottom_flag())
        self.assertEqual(len(result.fixed_panels), 1)
        panel = result.fixed_panels[0]
        self.assertEqual(panel.position.value, "BOTTOM")
        self.assertEqual(panel.vertical_transoms, 2)
        self.assertEqual(panel.horizontal_transoms, 0)
        self.assertEqual(len(panel.openings), 3)
        self.assertTrue(all(row.width_mm == 609.333333 for row in panel.openings))
        self.assertTrue(all(row.height_mm == 792.0 for row in panel.openings))
        divider = next(row for row in result.transoms if row.source == "BOTTOM_FLAG_INTERNAL")
        self.assertEqual(divider.orientation.value, "VERTICAL")
        self.assertEqual(divider.material_code, "DE6072")
        self.assertEqual(divider.reinforcement_material_code, "RAG - DE6072")
        self.assertEqual(divider.length_mm, 804.0)
        self.assertEqual(divider.quantity, 2.0)

    def test_baguettes_glass_and_seal_are_physical_per_opening(self):
        result = calculate_gr(divided_bottom_flag())
        by_role = {row.role: row for row in result.unit_bom}
        self.assertEqual(by_role["BOTTOM_FLAG_BEAD_HORIZONTAL"].quantity_per_unit, 6.0)
        self.assertEqual(by_role["BOTTOM_FLAG_BEAD_HORIZONTAL"].length_mm, 609.333333)
        self.assertEqual(by_role["BOTTOM_FLAG_BEAD_VERTICAL"].quantity_per_unit, 6.0)
        self.assertEqual(by_role["BOTTOM_FLAG_BEAD_VERTICAL"].length_mm, 792.0)
        for number in (1, 2, 3):
            glass = by_role[f"BOTTOM_FLAG_GLASS_PANEL_{number}"]
            self.assertEqual(glass.width_mm, 601.333333)
            self.assertEqual(glass.height_mm, 784.0)
        self.assertEqual(by_role["BOTTOM_FLAG_GLASS_SEAL"].length_mm, 8408.0)

    def test_ob_door_hardware_and_screws_follow_excel(self):
        result = calculate_gr(divided_bottom_flag())
        by_role = {row.role: row for row in result.unit_bom}
        for role in (
            "OB_FALSE_COMPASS",
            "OB_HINGE_BODY",
            "OB_UPPER_HINGE_BODY_PIN",
            "OB_LOWER_HINGE",
            "OB_LOWER_HINGE_SUPPORT",
            "OB_HINGE_COVERS",
        ):
            self.assertEqual(by_role[role].quantity_per_unit, 1.0)
        self.assertNotIn("HINGE_90MM", by_role)
        self.assertEqual(by_role["HARDWARE_SCREWS"].quantity_per_unit, 20.0)
        self.assertEqual(by_role["REINFORCEMENT_SCREWS"].quantity_per_unit, 55.888)

    def test_orcs_10024_current_physical_cost_is_frozen(self):
        result = calculate_gr(divided_bottom_flag())
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 45.906)
        self.assertEqual(result.unit_cost, 2010.312591)

    def test_phase19_is_unchanged_and_promoted(self):
        result = calculate_gr(phase19_case())
        self.assertEqual(result.calculation_version, "GR_ENGINE_0.20.0")
        self.assertEqual(result.unit_cost, 5594.46035)
        self.assertEqual(result.geometry["top_flag_opening_count"], 2.0)

    def test_unapproved_bottom_grid_cases_remain_blocked(self):
        for count in (1, 3):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    calculate_gr(divided_bottom_flag(bottom_flag_vertical_transoms=count))

    def test_screen_shutter_two_leaf_and_wrong_hinge_remain_blocked(self):
        for overrides in (
            {"screen_enabled": True},
            {"leaf_count": 2},
            {"hinge_description": "DOBRADIÇA 90MM"},
            {"top_flag_height_mm": 200},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    calculate_gr(divided_bottom_flag(**overrides))

    def test_golden_v020_is_frozen(self):
        golden = json.loads(
            (ROOT / "test_cases" / "gr_golden_v0_20.json").read_text(encoding="utf-8")
        )
        self.assertEqual(golden["engine_version"], "GR_ENGINE_0.20.0")
        for case in golden["cases"]:
            result = calculate_gr(GrConfiguration(**case["input"]))
            self.assertEqual(result.calculation_version, golden["engine_version"])
            self.assertEqual(result.unit_cost, case["unit_cost"])
            self.assertEqual(result.cost_breakdown["VEDAÇÕES"], case["sealing_cost"])
            screws = next(row for row in result.unit_bom if row.role == "REINFORCEMENT_SCREWS")
            self.assertEqual(screws.quantity_per_unit, case["reinforcement_screws"])
            for key, expected in case["geometry"].items():
                self.assertEqual(result.geometry[key], expected)

    def test_cost_is_exact_sum_of_bom(self):
        result = calculate_gr(divided_bottom_flag())
        self.assertEqual(
            result.unit_cost,
            round(sum(row.cost_per_unit_product for row in result.unit_bom), 6),
        )
        self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)


if __name__ == "__main__":
    unittest.main()
