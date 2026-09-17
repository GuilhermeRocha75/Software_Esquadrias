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
WINDOW_CREMONA = "MAÇANETA COM CREMONA SEM CHAVE"
CREMONA_800 = "CREMONA 2 PONTOS COMP. 800mm E:15mm"
INTERNAL = "FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN"
EXTERNAL = "FOLHA DE PORTA ABERTURA EXTERNA 60X104MM - DESIGN"
WINDOW = "FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN"


def configuration(**overrides):
    values = {"width_mm": 900, "height_mm": 2100, "quantity": 1}
    values.update(overrides)
    return GrConfiguration(**values)


def two_leaf_configuration(**overrides):
    values = {
        "width_mm": 1600,
        "height_mm": 2100,
        "quantity": 1,
        "leaf_count": 2,
        "leaf_system": INTERNAL,
        "application": "PORTA",
        "closure_mode": MONO,
    }
    values.update(overrides)
    return GrConfiguration(**values)


def window_configuration(**overrides):
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
    return GrConfiguration(**values)


class GrPhase5Tests(unittest.TestCase):
    def test_version_and_door_model(self):
        result = calculate_gr(configuration())
        self.assertEqual(result.calculation_version, "GR_ENGINE_0.5.0")
        self.assertEqual(result.model_description, "PORTA 1 FOLHA DE GIRO COM PAINEL HORIZONTAL")

    def test_one_leaf_door_geometry_remains_frozen(self):
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

    def test_squaring_blocks_follow_physical_rule_per_leaf(self):
        one = calculate_gr(configuration())
        two = calculate_gr(two_leaf_configuration())
        window = calculate_gr(window_configuration())
        one_block = next(x for x in one.unit_bom if x.material_code == "AC0312")
        two_block = next(x for x in two.unit_bom if x.material_code == "AC0312")
        window_block = next(x for x in window.unit_bom if x.material_code == "AC0312")
        self.assertEqual(one_block.role, "SQUARING_BLOCK")
        self.assertEqual(one_block.quantity_per_unit, 4)
        self.assertEqual(two_block.quantity_per_unit, 8)
        self.assertEqual(window_block.quantity_per_unit, 4)
        self.assertIn("RESOLVED_PHYSICAL", two_block.source)

    def test_two_leaf_geometry_matches_xlsm_dimensions(self):
        result = calculate_gr(two_leaf_configuration())
        self.assertEqual(result.model_description, "PORTA 2 FOLHAS DE GIRO COM PAINEL HORIZONTAL")
        self.assertEqual(result.geometry, {
            "frame_width_final_mm": 1600.0,
            "frame_width_cut_mm": 1605.0,
            "frame_height_final_mm": 2100.0,
            "frame_height_cut_mm": 2103.0,
            "leaf_width_final_mm": 758.0,
            "leaf_width_cut_mm": 763.0,
            "leaf_height_final_mm": 2063.0,
            "leaf_height_cut_mm": 2068.0,
            "panel_bead_width_mm": 586.0,
            "panel_bead_height_mm": 1891.0,
            "panel_fill_strip_length_mm": 586.0,
            "panel_fill_strip_quantity": 25.528571,
            "frame_reinforcement_width_mm": 1484.0,
            "frame_reinforcement_height_mm": 1984.0,
            "leaf_reinforcement_width_mm": 638.0,
            "leaf_reinforcement_height_mm": 1943.0,
        })

    def test_two_leaf_panel_quantity_corrects_confirmed_legacy_bug(self):
        result = calculate_gr(two_leaf_configuration())
        panel = next(x for x in result.unit_bom if x.material_code == "DE20150")
        one_leaf_vertical_count = (1891.0 - 104.0) / 140.0
        self.assertAlmostEqual(panel.quantity_per_unit, one_leaf_vertical_count * 2, places=6)
        self.assertEqual(panel.quantity_per_unit, 25.52857142857143)
        self.assertIn("LEGACY_BUG_CONFIRMED_2026-09-17", panel.source)
        legacy_cost = one_leaf_vertical_count * 586.0 / 1000.0 * 20.27
        physical_cost = panel.cost_per_unit_product
        self.assertEqual(round(physical_cost - legacy_cost, 6), 151.616994)

    def test_two_leaf_passive_hardware_is_exact_and_has_no_extra_par1(self):
        result = calculate_gr(two_leaf_configuration())
        fec7 = next(x for x in result.unit_bom if x.material_code == "FEC7")
        con3 = next(x for x in result.unit_bom if x.material_code == "CON3")
        par1 = next(x for x in result.unit_bom if x.material_code == "PAR1")
        self.assertEqual(fec7.quantity_per_unit, 2)
        self.assertEqual(con3.quantity_per_unit, 2)
        self.assertEqual(par1.quantity_per_unit, 52)
        self.assertIn("RESOLVED_PHYSICAL_2026-09-17", fec7.source)
        self.assertIn("RESOLVED_PHYSICAL_2026-09-17", con3.source)
        self.assertIn("RESOLVED_PHYSICAL_2026-09-17", par1.source)

    def test_two_leaf_current_physical_cost_is_frozen(self):
        result = calculate_gr(two_leaf_configuration())
        self.assertEqual(result.unit_cost, 2223.252898)
        self.assertEqual(result.cost_breakdown, {
            "PERFIS PRINCIPAIS": 1154.016538,
            "BAGUETES": 106.21376,
            "ACABAMENTOS": 110.3738,
            "REFORÇOS": 301.716,
            "VIDROS": 0.0,
            "TELA": 0.0,
            "VEDAÇÕES": 0.0,
            "ACESSÓRIOS": 3.8,
            "FERRAGENS": 547.1328,
            "TOTAL": 2223.252898,
        })

    def test_window_panel_geometry_matches_xlsm_formulas(self):
        result = calculate_gr(window_configuration())
        self.assertEqual(result.model_description, "JANELA 1 FOLHA DE GIRO COM PAINEL HORIZONTAL")
        self.assertEqual(result.geometry, {
            "frame_width_final_mm": 800.0,
            "frame_width_cut_mm": 805.0,
            "frame_height_final_mm": 1300.0,
            "frame_height_cut_mm": 1305.0,
            "leaf_width_final_mm": 736.0,
            "leaf_width_cut_mm": 741.0,
            "leaf_height_final_mm": 1236.0,
            "leaf_height_cut_mm": 1241.0,
            "panel_bead_width_mm": 616.0,
            "panel_bead_height_mm": 1116.0,
            "panel_fill_strip_length_mm": 616.0,
            "panel_fill_strip_quantity": 7.414286,
            "frame_reinforcement_width_mm": 720.0,
            "frame_reinforcement_height_mm": 1220.0,
            "leaf_reinforcement_width_mm": 616.0,
            "leaf_reinforcement_height_mm": 1116.0,
        })

    def test_window_baseline_includes_physically_confirmed_800mm_cremona(self):
        result = calculate_gr(window_configuration())
        self.assertEqual(result.unit_cost, 827.722384)
        codes = {x.material_code for x in result.unit_bom}
        self.assertIn("DE6078", codes)
        self.assertIn("RAG - DE6078", codes)
        self.assertIn("MAC1", codes)
        self.assertIn("CRE12", codes)
        self.assertIn("CON1", codes)
        cremona = next(x for x in result.unit_bom if x.material_code == "CRE12")
        self.assertEqual(cremona.description, CREMONA_800)
        self.assertIn("RESOLVED_PHYSICAL_2026-09-16", cremona.source)
        screws = next(x for x in result.unit_bom if x.role == "HARDWARE_SCREWS")
        self.assertEqual(screws.quantity_per_unit, 32)

    def test_window_none_cremona_normalizes_to_physical_800mm_baseline(self):
        explicit = calculate_gr(window_configuration(cremona_description=CREMONA_800))
        implicit = calculate_gr(window_configuration(cremona_description=None))
        self.assertEqual(implicit.geometry, explicit.geometry)
        self.assertEqual(implicit.cost_breakdown, explicit.cost_breakdown)
        self.assertEqual(implicit.unit_cost, explicit.unit_cost)

    def test_current_catalog_window_reference_cases(self):
        cases = (
            (17975, 800, 1300, 827.722384),
            (18400, 1120, 1850, 1178.777293),
        )
        for row, width, height, expected in cases:
            with self.subTest(orcs_row=row):
                result = calculate_gr(window_configuration(width_mm=width, height_mm=height))
                self.assertEqual(result.unit_cost, expected)

    def test_cost_is_exact_sum_of_bom_and_groups(self):
        cases = [
            configuration(closure_mode=closure, leaf_system=leaf_system)
            for closure in (MONO, MULTI)
            for leaf_system in (INTERNAL, EXTERNAL)
        ]
        cases.extend([two_leaf_configuration(), two_leaf_configuration(closure_mode=MULTI), window_configuration()])
        for cfg in cases:
            with self.subTest(application=cfg.application, leaves=cfg.leaf_count, leaf_system=cfg.leaf_system):
                result = calculate_gr(cfg)
                self.assertEqual(result.unit_cost, round(sum(x.cost_per_unit_product for x in result.unit_bom), 6))
                self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)

    def test_quantity_scales_order_bom_not_unit_cost(self):
        for maker in (configuration, two_leaf_configuration, window_configuration):
            with self.subTest(maker=maker.__name__):
                one = calculate_gr(maker(quantity=1))
                three = calculate_gr(maker(quantity=3))
                self.assertEqual(one.unit_cost, three.unit_cost)
                for item in three.unit_bom:
                    self.assertEqual(item.quantity_order, item.quantity_per_unit * 3)

    def test_previous_goldens_remain_numerically_frozen_after_version_bump(self):
        for filename in ("gr_golden_v0_3.json", "gr_golden_v0_4.json"):
            golden = json.loads((ROOT / "test_cases" / filename).read_text(encoding="utf-8"))
            for case in golden["cases"]:
                with self.subTest(file=filename, case=case["id"]):
                    result = calculate_gr(GrConfiguration(**case["input"]))
                    self.assertEqual(result.geometry, case["geometry"])
                    self.assertEqual(result.cost_breakdown, case["cost_by_group"])
                    self.assertEqual(result.unit_cost, case["unit_cost"])

    def test_golden_v05_is_frozen(self):
        golden = json.loads((ROOT / "test_cases" / "gr_golden_v0_5.json").read_text(encoding="utf-8"))
        for case in golden["cases"]:
            with self.subTest(case=case["id"]):
                result = calculate_gr(GrConfiguration(**case["input"]))
                self.assertEqual(result.calculation_version, golden["engine_version"])
                self.assertEqual(result.geometry, case["geometry"])
                self.assertEqual(result.cost_breakdown, case["cost_by_group"])
                self.assertEqual(result.unit_cost, case["unit_cost"])

    def test_out_of_scope_variants_are_blocked(self):
        invalid = (
            {"leaf_count": 3},
            {"application": "JANELA"},
            {"panel_mode": ""},
            {"closure_mode": WINDOW_CREMONA},
            {"screen_enabled": True},
            {"shutter_enabled": True},
            {"bottom_flag_height_mm": 600},
            {"leaf_horizontal_transoms": 1},
            {"structural_reinforcement": "ALUM10238"},
        )
        for override in invalid:
            with self.subTest(override=override), self.assertRaises(ValueError):
                calculate_gr(configuration(**override))

        window_invalid = (
            {"leaf_count": 2},
            {"application": "PORTA"},
            {"closure_mode": MONO},
            {"cremona_description": "CREMONA 2 PONTOS COMP. 1000mm E:15mm"},
            {"hinge_description": "DOBRADIÇA SISTEMA OB"},
        )
        for override in window_invalid:
            with self.subTest(override=override), self.assertRaises(ValueError):
                calculate_gr(window_configuration(**override))

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
        with self.assertRaisesRegex(ValueError, "tecnicamente impossíveis"):
            calculate_gr(two_leaf_configuration(width_mm=500))
        with self.assertRaisesRegex(ValueError, "tecnicamente impossíveis"):
            calculate_gr(window_configuration(width_mm=180))
        with self.assertRaisesRegex(ValueError, "tecnicamente impossíveis"):
            calculate_gr(window_configuration(height_mm=250))


if __name__ == "__main__":
    unittest.main()
