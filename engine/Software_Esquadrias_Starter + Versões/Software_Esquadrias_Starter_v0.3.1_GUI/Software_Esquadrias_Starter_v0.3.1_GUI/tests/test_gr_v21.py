import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine.gr_v21 import GrConfiguration, calculate_gr  # noqa: E402

WINDOW = "FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN"
CREMONA = "MAÇANETA COM CREMONA SEM CHAVE"
GLASS = "20mm DUPLO FLOAT INCOLOR/TEMPERADO INCOLOR (4/10/6)"


def orcs_14179(**overrides):
    values = {
        "width_mm": 4200,
        "height_mm": 1900,
        "quantity": 1,
        "leaf_count": 2,
        "leaf_system": WINDOW,
        "application": "JANELA",
        "panel_mode": "VIDRO INTEIRO",
        "glass_description": GLASS,
        "closure_mode": CREMONA,
        "hinge_description": "DOBRADIÇA 90MM",
        "bottom_flag_height_mm": 700,
        "bottom_flag_vertical_transoms": 3,
    }
    values.update(overrides)
    return GrConfiguration(**values)


class GrPhase21Tests(unittest.TestCase):
    def test_version_is_v021(self):
        self.assertEqual(
            calculate_gr(orcs_14179()).calculation_version,
            "GR_ENGINE_0.21.0",
        )

    def test_orcs_14179_geometry_is_frozen(self):
        result = calculate_gr(orcs_14179())
        expected = {
            "frame_height_final_mm": 1900.0,
            "frame_height_cut_mm": 1905.0,
            "leaf_width_final_mm": 2058.0,
            "leaf_height_final_mm": 1158.0,
            "glass_bead_width_mm": 1938.0,
            "glass_bead_height_mm": 1038.0,
            "glass_width_mm": 1930.0,
            "glass_height_mm": 1030.0,
            "glass_panel_count": 2.0,
            "bottom_flag_height_mm": 700.0,
            "bottom_flag_boundary_transom_length_mm": 4132.0,
            "bottom_flag_vertical_transoms": 3.0,
            "bottom_flag_opening_count": 4.0,
            "bottom_flag_bead_width_mm": 1003.0,
            "bottom_flag_bead_height_mm": 642.0,
            "bottom_flag_glass_width_mm": 995.0,
            "bottom_flag_glass_height_mm": 634.0,
            "bottom_flag_internal_vertical_transom_length_mm": 654.0,
            "bottom_flag_internal_vertical_reinforcement_screws_added": 6.0,
            "bottom_flag_glass_panel_count": 4.0,
        }
        for key, value in expected.items():
            self.assertEqual(result.geometry[key], value)

    def test_bottom_grid_has_four_openings_and_three_internal_verticals(self):
        result = calculate_gr(orcs_14179())
        self.assertEqual(len(result.fixed_panels), 1)
        panel = result.fixed_panels[0]
        self.assertEqual(panel.position.value, "BOTTOM")
        self.assertEqual(panel.vertical_transoms, 3)
        self.assertEqual(panel.horizontal_transoms, 0)
        self.assertEqual(len(panel.openings), 4)
        self.assertTrue(all(row.width_mm == 1003.0 for row in panel.openings))
        self.assertTrue(all(row.height_mm == 642.0 for row in panel.openings))
        divider = next(row for row in result.transoms if row.source == "BOTTOM_FLAG_INTERNAL")
        self.assertEqual(divider.orientation.value, "VERTICAL")
        self.assertEqual(divider.material_code, "DE6072")
        self.assertEqual(divider.reinforcement_material_code, "RAG - DE6072")
        self.assertEqual(divider.length_mm, 654.0)
        self.assertEqual(divider.quantity, 3.0)

    def test_two_leaf_window_has_two_leaf_glasses_and_passive_hardware(self):
        result = calculate_gr(orcs_14179())
        by_role = {row.role: row for row in result.unit_bom}
        self.assertEqual(by_role["LEAF_WIDTH"].quantity_per_unit, 4.0)
        self.assertEqual(by_role["LEAF_HEIGHT"].quantity_per_unit, 4.0)
        self.assertEqual(by_role["HINGE_90MM"].quantity_per_unit, 6.0)
        self.assertEqual(by_role["PASSIVE_LEAF_COUNTER_CLAW"].quantity_per_unit, 2.0)
        self.assertEqual(by_role["PASSIVE_LEAF_CLAW_LOCK"].quantity_per_unit, 2.0)
        for number in (1, 2):
            glass = by_role[f"GLASS_PANEL_{number}"]
            self.assertEqual(glass.width_mm, 1930.0)
            self.assertEqual(glass.height_mm, 1030.0)

    def test_flag_baguettes_glass_and_seal_are_physical_per_opening(self):
        result = calculate_gr(orcs_14179())
        by_role = {row.role: row for row in result.unit_bom}
        self.assertEqual(by_role["BOTTOM_FLAG_BEAD_HORIZONTAL"].quantity_per_unit, 8.0)
        self.assertEqual(by_role["BOTTOM_FLAG_BEAD_HORIZONTAL"].length_mm, 1003.0)
        self.assertEqual(by_role["BOTTOM_FLAG_BEAD_VERTICAL"].quantity_per_unit, 8.0)
        self.assertEqual(by_role["BOTTOM_FLAG_BEAD_VERTICAL"].length_mm, 642.0)
        for number in (1, 2, 3, 4):
            glass = by_role[f"BOTTOM_FLAG_GLASS_PANEL_{number}"]
            self.assertEqual(glass.width_mm, 995.0)
            self.assertEqual(glass.height_mm, 634.0)
        self.assertEqual(by_role["BOTTOM_FLAG_GLASS_SEAL"].length_mm, 13160.0)

    def test_reinforcement_and_hardware_screws_are_frozen(self):
        result = calculate_gr(orcs_14179())
        by_role = {row.role: row for row in result.unit_bom}
        self.assertEqual(by_role["REINFORCEMENT_SCREWS"].quantity_per_unit, 123.024)
        self.assertEqual(by_role["HARDWARE_SCREWS"].quantity_per_unit, 56.0)

    def test_orcs_14179_current_physical_cost_is_frozen(self):
        result = calculate_gr(orcs_14179())
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 86.28)
        self.assertEqual(result.unit_cost, 4131.00088)

    def test_phase20_is_unchanged_and_promoted(self):
        result = calculate_gr(GrConfiguration(
            width_mm=1980,
            height_mm=2150,
            leaf_count=1,
            leaf_system="FOLHA DE PORTA ABERTURA EXTERNA 60X104MM - DESIGN",
            application="PORTA",
            panel_mode="VIDRO INTEIRO",
            glass_description="06mm TEMPERADO INCOLOR",
            closure_mode="MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE",
            hinge_description="DOBRADIÇA SISTEMA OB",
            bottom_flag_height_mm=850,
            bottom_flag_vertical_transoms=2,
        ))
        self.assertEqual(result.calculation_version, "GR_ENGINE_0.21.0")
        self.assertEqual(result.unit_cost, 2010.312591)

    def test_screen_and_non_orcs_combinations_remain_blocked(self):
        for overrides in (
            {"screen_enabled": True},
            {"leaf_count": 1},
            {"application": "PORTA"},
            {"hinge_description": "DOBRADIÇA SISTEMA OB"},
            {"top_flag_height_mm": 200},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    calculate_gr(orcs_14179(**overrides))

    def test_ah1_window_with_screen_remains_blocked(self):
        with self.assertRaises(ValueError):
            calculate_gr(orcs_14179(
                width_mm=3000,
                height_mm=2000,
                bottom_flag_height_mm=600,
                bottom_flag_vertical_transoms=1,
                screen_enabled=True,
                glass_description="05mm TEMPERADO INCOLOR",
            ))

    def test_golden_v021_is_frozen(self):
        golden = json.loads(
            (ROOT / "test_cases" / "gr_golden_v0_21.json").read_text(encoding="utf-8")
        )
        self.assertEqual(golden["engine_version"], "GR_ENGINE_0.21.0")
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
        result = calculate_gr(orcs_14179())
        self.assertEqual(
            result.unit_cost,
            round(sum(row.cost_per_unit_product for row in result.unit_bom), 6),
        )
        self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)


if __name__ == "__main__":
    unittest.main()
