import json
import math
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import GrConfiguration, calculate_gr  # noqa: E402

MONO = "MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE"
MULTI = "MAÇANETA DUPLA COM FECHADURA MULTIPONTO E CHAVE"
INTERNAL = "FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN"
EXTERNAL = "FOLHA DE PORTA ABERTURA EXTERNA 60X104MM - DESIGN"


def configuration(**overrides):
    values = {"width_mm": 900, "height_mm": 2100, "quantity": 1}
    values.update(overrides)
    return GrConfiguration(**values)


class GrPhase3Tests(unittest.TestCase):
    def test_version_and_model(self):
        result = calculate_gr(configuration())
        self.assertEqual(result.calculation_version, "GR_ENGINE_0.3.0")
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

    def test_monopoint_formula_totals_match_real_orcs_snapshots(self):
        cases = (
            (17386, 700, 2100, 1283.4252311428572, 0.0),
            (17173, 800, 2100, 1334.0744382857142, 0.0),
            (18542, 900, 2100, 1384.7236454285714, 0.005),
            (17374, 1100, 2100, 1486.022059714286, 0.0),
        )
        for row, width, height, expected, tolerance in cases:
            with self.subTest(orcs_row=row):
                actual = calculate_gr(configuration(width_mm=width, height_mm=height, closure_mode=MONO)).unit_cost
                self.assertLessEqual(abs(actual - expected), max(tolerance, 1e-6))

    def test_multipoint_formula_totals_match_current_real_orcs(self):
        cases = (
            (18237, 800, 2100, 1401.8744382857144),
            (18361, 900, 2100, 1452.5236454285714),
            (18590, 900, 2100, 1452.5236454285714),
            (18695, 900, 2150, 1472.9345311428572),
            (18700, 750, 2150, 1395.8748275714288),
        )
        for row, width, height, expected in cases:
            with self.subTest(orcs_row=row):
                actual = calculate_gr(configuration(width_mm=width, height_mm=height, closure_mode=MULTI)).unit_cost
                self.assertLessEqual(abs(actual - expected), 1e-6)

    def test_external_opening_matches_current_real_orcs(self):
        for row in (18545, 18547, 18558):
            with self.subTest(orcs_row=row):
                result = calculate_gr(configuration(
                    width_mm=800,
                    height_mm=2150,
                    leaf_system=EXTERNAL,
                    closure_mode=MULTI,
                ))
                self.assertEqual(result.unit_cost, 1418.530855)
                leaf_codes = {x.material_code for x in result.unit_bom if x.role in {"LEAF_WIDTH", "LEAF_HEIGHT"}}
                self.assertEqual(leaf_codes, {"DE60104-E"})

    def test_external_and_internal_opening_keep_same_geometry(self):
        internal = calculate_gr(configuration(width_mm=800, height_mm=2150, leaf_system=INTERNAL, closure_mode=MULTI))
        external = calculate_gr(configuration(width_mm=800, height_mm=2150, leaf_system=EXTERNAL, closure_mode=MULTI))
        self.assertEqual(internal.geometry, external.geometry)
        self.assertEqual(internal.unit_cost, 1421.561395)
        self.assertEqual(external.unit_cost, 1418.530855)
        self.assertEqual(round(internal.unit_cost - external.unit_cost, 6), 3.03054)

    def test_multipoint_delta_is_explained_by_exact_xlsm_hardware_rules(self):
        mono = calculate_gr(configuration(closure_mode=MONO))
        multi = calculate_gr(configuration(closure_mode=MULTI))
        self.assertEqual(round(multi.unit_cost - mono.unit_cost, 6), 67.8)
        self.assertEqual(mono.unit_cost, 1384.723645)
        self.assertEqual(multi.unit_cost, 1452.523645)
        multi_codes = {x.material_code for x in multi.unit_bom}
        self.assertIn("FEC5", multi_codes)
        self.assertIn("CON1", multi_codes)
        self.assertNotIn("FEC6", multi_codes)
        screws = next(x for x in multi.unit_bom if x.role == "HARDWARE_SCREWS")
        self.assertEqual(screws.quantity_per_unit, 36)

    def test_cost_is_exact_sum_of_bom_and_groups(self):
        for closure in (MONO, MULTI):
            for leaf_system in (INTERNAL, EXTERNAL):
                with self.subTest(closure=closure, leaf_system=leaf_system):
                    result = calculate_gr(configuration(closure_mode=closure, leaf_system=leaf_system))
                    self.assertEqual(result.unit_cost, round(sum(x.cost_per_unit_product for x in result.unit_bom), 6))
                    self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)

    def test_quantity_scales_order_bom_not_unit_cost(self):
        one = calculate_gr(configuration(quantity=1))
        three = calculate_gr(configuration(quantity=3))
        self.assertEqual(one.unit_cost, three.unit_cost)
        for item in three.unit_bom:
            self.assertEqual(item.quantity_order, item.quantity_per_unit * 3)

    def test_golden_v03_is_frozen(self):
        golden = json.loads((ROOT / "test_cases" / "gr_golden_v0_3.json").read_text(encoding="utf-8"))
        for case in golden["cases"]:
            with self.subTest(case=case["id"]):
                result = calculate_gr(configuration(**case["input"]))
                self.assertEqual(result.calculation_version, golden["engine_version"])
                self.assertEqual(result.geometry, case["geometry"])
                self.assertEqual(result.cost_breakdown, case["cost_by_group"])
                self.assertEqual(result.unit_cost, case["unit_cost"])

    def test_out_of_scope_variants_are_blocked(self):
        invalid = (
            {"leaf_count": 2},
            {"application": "JANELA"},
            {"panel_mode": ""},
            {"leaf_system": "FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN"},
            {"closure_mode": "MAÇANETA COM CREMONA SEM CHAVE"},
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
