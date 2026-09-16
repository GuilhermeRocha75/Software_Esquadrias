import json
import math
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import GrConfiguration, calculate_gr  # noqa: E402


def configuration(**overrides):
    values = {"width_mm": 900, "height_mm": 2100, "quantity": 1}
    values.update(overrides)
    return GrConfiguration(**values)


class GrPhase1Tests(unittest.TestCase):
    def test_version_and_model(self):
        result = calculate_gr(configuration())
        self.assertEqual(result.calculation_version, "GR_ENGINE_0.1.0")
        self.assertEqual(result.model_description, "PORTA 1 FOLHA DE GIRO COM PAINEL HORIZONTAL")

    def test_geometry_matches_gr_sheet_formulas(self):
        result = calculate_gr(configuration())
        expected = {
            "frame_width_final_mm": 900.0,
            "frame_width_cut_mm": 905.0,
            "frame_height_final_mm": 2100.0,
            "frame_height_cut_mm": 2103.0,
            "leaf_width_final_mm": 836.0,
            "leaf_width_cut_mm": 841.0,
            "leaf_height_final_mm": 2063.0,
            "leaf_height_cut_mm": 2068.0,
            "panel_bead_width_mm": 664.0,
            "panel_bead_height_mm": 1891.0,
            "panel_fill_strip_length_mm": 664.0,
            "panel_fill_strip_quantity": 12.764286,
            "frame_reinforcement_width_mm": 784.0,
            "frame_reinforcement_height_mm": 1984.0,
            "leaf_reinforcement_width_mm": 716.0,
            "leaf_reinforcement_height_mm": 1943.0,
        }
        self.assertEqual(result.geometry, expected)

    def test_current_xlsm_formula_totals_match_real_orcs_snapshots(self):
        cases = (
            (17386, 700, 2100, 1283.4252311428572, 0.0),
            (17173, 800, 2100, 1334.0744382857142, 0.0),
            # ORCS!18542 is stored rounded to cents; current GR formulas produce the exact total below.
            (18542, 900, 2100, 1384.7236454285714, 0.005),
            (17374, 1100, 2100, 1486.022059714286, 0.0),
        )
        for row, width, height, expected, tolerance in cases:
            with self.subTest(orcs_row=row):
                actual = calculate_gr(configuration(width_mm=width, height_mm=height)).unit_cost
                self.assertLessEqual(abs(actual - expected), max(tolerance, 1e-6))

    def test_cost_is_exact_sum_of_bom_and_groups(self):
        result = calculate_gr(configuration())
        self.assertEqual(result.unit_cost, round(sum(x.cost_per_unit_product for x in result.unit_bom), 6))
        self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)
        self.assertEqual(result.unit_cost, 1384.723645)

    def test_quantity_scales_order_bom_not_unit_cost(self):
        one = calculate_gr(configuration(quantity=1))
        three = calculate_gr(configuration(quantity=3))
        self.assertEqual(one.unit_cost, three.unit_cost)
        for item in three.unit_bom:
            self.assertEqual(item.quantity_order, item.quantity_per_unit * 3)

    def test_baseline_bom_has_expected_codes(self):
        result = calculate_gr(configuration())
        self.assertEqual(
            {x.material_code for x in result.unit_bom},
            {"DE6058", "DE60104", "BA2516", "DE20150", "AC7012", "AC3004",
             "RAG - DE6058", "RAG - DE60104", "AC0312", "AC0001", "DOB3",
             "MAC4", "FEC6", "CIL1", "CON2", "PAR2", "PAR1"},
        )
        self.assertTrue(all(x.source for x in result.unit_bom))
        self.assertTrue(all(x.cost_per_unit_product >= 0 for x in result.unit_bom))

    def test_golden_case_is_frozen(self):
        golden = json.loads((ROOT / "test_cases" / "gr_golden_v0_1.json").read_text(encoding="utf-8"))
        case = golden["cases"][0]
        result = calculate_gr(configuration(**case["input"]))
        self.assertEqual(result.calculation_version, golden["engine_version"])
        self.assertEqual(result.geometry, case["geometry"])
        self.assertEqual(result.cost_breakdown, case["cost_by_group"])
        self.assertEqual(result.unit_cost, case["unit_cost"])
        self.assertEqual(
            [[x.role, x.material_code, x.length_mm, x.quantity_per_unit, x.unit_price, x.cost_per_unit_product]
             for x in result.unit_bom],
            case["bom"],
        )

    def test_out_of_scope_variants_are_blocked(self):
        invalid = (
            {"leaf_count": 2},
            {"application": "JANELA"},
            {"panel_mode": ""},
            {"leaf_system": "FOLHA DE PORTA ABERTURA EXTERNA 60X104MM - DESIGN"},
            {"screen_enabled": True},
            {"shutter_enabled": True},
            {"bottom_flag_height_mm": 600},
            {"leaf_horizontal_transoms": 1},
            {"structural_reinforcement": "ALUM10238"},
        )
        for override in invalid:
            with self.subTest(override=override), self.assertRaises(ValueError):
                calculate_gr(configuration(**override))

    def test_nonfinite_and_impossible_dimensions_are_rejected(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                calculate_gr(configuration(width_mm=value))
        with self.assertRaises(ValueError):
            calculate_gr(configuration(quantity=0))
        with self.assertRaisesRegex(ValueError, "tecnicamente impossíveis"):
            calculate_gr(configuration(width_mm=230))
        with self.assertRaisesRegex(ValueError, "tecnicamente impossíveis"):
            calculate_gr(configuration(height_mm=300))


if __name__ == "__main__":
    unittest.main()
