import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import GrConfiguration, calculate_gr  # noqa: E402

WINDOW = "FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN"
CREMONA = "MAÇANETA COM CREMONA SEM CHAVE"


def orcs_16527(**overrides):
    values = {
        "width_mm": 3000,
        "height_mm": 2000,
        "quantity": 1,
        "leaf_count": 2,
        "leaf_system": WINDOW,
        "application": "JANELA",
        "panel_mode": "VIDRO INTEIRO",
        "glass_description": "05mm TEMPERADO INCOLOR",
        "closure_mode": CREMONA,
        "hinge_description": "DOBRADIÇA 90MM",
        "bottom_flag_height_mm": 600,
        "bottom_flag_vertical_transoms": 1,
        "screen_enabled": True,
    }
    values.update(overrides)
    return GrConfiguration(**values)


def phase21_case():
    return GrConfiguration(
        width_mm=4200,
        height_mm=1900,
        leaf_count=2,
        leaf_system=WINDOW,
        application="JANELA",
        panel_mode="VIDRO INTEIRO",
        glass_description="20mm DUPLO FLOAT INCOLOR/TEMPERADO INCOLOR (4/10/6)",
        closure_mode=CREMONA,
        hinge_description="DOBRADIÇA 90MM",
        bottom_flag_height_mm=700,
        bottom_flag_vertical_transoms=3,
    )


class GrPhase22Tests(unittest.TestCase):
    def test_version_is_v022(self):
        self.assertEqual(
            calculate_gr(orcs_16527()).calculation_version,
            "GR_ENGINE_0.22.0",
        )

    def test_orcs_16527_geometry_is_frozen(self):
        result = calculate_gr(orcs_16527())
        expected = {
            "leaf_width_final_mm": 1458.0,
            "leaf_height_final_mm": 1358.0,
            "glass_width_mm": 1330.0,
            "glass_height_mm": 1230.0,
            "glass_panel_count": 2.0,
            "bottom_flag_height_mm": 600.0,
            "bottom_flag_boundary_transom_length_mm": 2932.0,
            "bottom_flag_vertical_transoms": 1.0,
            "bottom_flag_opening_count": 2.0,
            "bottom_flag_bead_width_mm": 1442.0,
            "bottom_flag_bead_height_mm": 542.0,
            "bottom_flag_glass_width_mm": 1434.0,
            "bottom_flag_glass_height_mm": 534.0,
            "bottom_flag_internal_vertical_transom_length_mm": 554.0,
            "bottom_flag_internal_vertical_reinforcement_screws_added": 2.0,
            "bottom_flag_glass_panel_count": 2.0,
            "screen_width_mm": 3000.0,
            "screen_height_mm": 2000.0,
            "screen_panel_count": 1.0,
        }
        for key, value in expected.items():
            self.assertEqual(result.geometry[key], value)

    def test_bottom_grid_has_two_openings_and_one_internal_vertical(self):
        result = calculate_gr(orcs_16527())
        panel = result.fixed_panels[0]
        self.assertEqual(panel.position.value, "BOTTOM")
        self.assertEqual(panel.vertical_transoms, 1)
        self.assertEqual(len(panel.openings), 2)
        self.assertTrue(all(row.width_mm == 1442.0 for row in panel.openings))
        self.assertTrue(all(row.height_mm == 542.0 for row in panel.openings))
        divider = next(row for row in result.transoms if row.source == "BOTTOM_FLAG_INTERNAL")
        self.assertEqual(divider.length_mm, 554.0)
        self.assertEqual(divider.quantity, 1.0)

    def test_screen_is_one_full_frame_tl3_assembly(self):
        result = calculate_gr(orcs_16527())
        screen = next(row for row in result.unit_bom if row.role == "RETRACTABLE_SCREEN_ASSEMBLY")
        self.assertEqual(screen.material_code, "TL3")
        self.assertEqual(screen.width_mm, 3000.0)
        self.assertEqual(screen.height_mm, 2000.0)
        self.assertEqual(screen.quantity_per_unit, 1.0)
        self.assertEqual(screen.cost_per_unit_product, 660.0)

    def test_leaf_and_flag_glass_counts_are_physical(self):
        result = calculate_gr(orcs_16527())
        by_role = {row.role: row for row in result.unit_bom}
        for number in (1, 2):
            leaf = by_role[f"GLASS_PANEL_{number}"]
            self.assertEqual(leaf.width_mm, 1330.0)
            self.assertEqual(leaf.height_mm, 1230.0)
            flag = by_role[f"BOTTOM_FLAG_GLASS_PANEL_{number}"]
            self.assertEqual(flag.width_mm, 1434.0)
            self.assertEqual(flag.height_mm, 534.0)
        self.assertEqual(len(result.glass_panels), 4)

    def test_flag_baguettes_seal_and_reinforcement_are_physical(self):
        result = calculate_gr(orcs_16527())
        by_role = {row.role: row for row in result.unit_bom}
        self.assertEqual(by_role["BOTTOM_FLAG_BEAD_HORIZONTAL"].quantity_per_unit, 4.0)
        self.assertEqual(by_role["BOTTOM_FLAG_BEAD_VERTICAL"].quantity_per_unit, 4.0)
        self.assertEqual(by_role["BOTTOM_FLAG_GLASS_SEAL"].length_mm, 7936.0)
        self.assertEqual(by_role["REINFORCEMENT_SCREWS"].quantity_per_unit, 99.024)

    def test_orcs_16527_current_physical_cost_is_frozen(self):
        result = calculate_gr(orcs_16527())
        self.assertEqual(result.cost_breakdown["TELA"], 660.0)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 68.8768)
        self.assertEqual(result.unit_cost, 3316.78472)

    def test_phase21_is_unchanged_and_promoted(self):
        result = calculate_gr(phase21_case())
        self.assertEqual(result.calculation_version, "GR_ENGINE_0.22.0")
        self.assertEqual(result.unit_cost, 4131.00088)
        self.assertEqual(result.geometry["bottom_flag_opening_count"], 4.0)

    def test_other_screen_grid_combinations_remain_blocked(self):
        for overrides in (
            {"bottom_flag_vertical_transoms": 2},
            {"bottom_flag_vertical_transoms": 3},
            {"top_flag_height_mm": 200},
            {"shutter_enabled": True},
            {"leaf_count": 1},
            {"application": "PORTA"},
            {"hinge_description": "DOBRADIÇA SISTEMA OB"},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    calculate_gr(orcs_16527(**overrides))

    def test_ah1_without_screen_remains_blocked(self):
        with self.assertRaises(ValueError):
            calculate_gr(orcs_16527(screen_enabled=False))

    def test_golden_v022_is_frozen(self):
        golden = json.loads(
            (ROOT / "test_cases" / "gr_golden_v0_22.json").read_text(encoding="utf-8")
        )
        self.assertEqual(golden["engine_version"], "GR_ENGINE_0.22.0")
        for case in golden["cases"]:
            result = calculate_gr(GrConfiguration(**case["input"]))
            self.assertEqual(result.calculation_version, golden["engine_version"])
            self.assertEqual(result.unit_cost, case["unit_cost"])
            self.assertEqual(result.cost_breakdown["TELA"], case["screen_cost"])
            self.assertEqual(result.cost_breakdown["VEDAÇÕES"], case["sealing_cost"])
            screws = next(row for row in result.unit_bom if row.role == "REINFORCEMENT_SCREWS")
            self.assertEqual(screws.quantity_per_unit, case["reinforcement_screws"])
            for key, expected in case["geometry"].items():
                self.assertEqual(result.geometry[key], expected)

    def test_cost_is_exact_sum_of_bom(self):
        result = calculate_gr(orcs_16527())
        self.assertEqual(
            result.unit_cost,
            round(sum(row.cost_per_unit_product for row in result.unit_bom), 6),
        )
        self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)


if __name__ == "__main__":
    unittest.main()
