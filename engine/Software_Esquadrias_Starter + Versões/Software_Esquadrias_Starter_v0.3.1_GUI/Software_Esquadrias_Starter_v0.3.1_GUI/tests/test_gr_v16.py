import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine.gr_v16 import GrConfiguration, calculate_gr  # noqa: E402

INTERNAL = "FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN"
EXTERNAL = "FOLHA DE PORTA ABERTURA EXTERNA 60X104MM - DESIGN"
MONO = "MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE"


def two_leaf_flag(**overrides):
    values = {
        "width_mm": 1472,
        "height_mm": 2700,
        "quantity": 1,
        "leaf_count": 2,
        "leaf_system": INTERNAL,
        "application": "PORTA",
        "panel_mode": "VIDRO INTEIRO",
        "glass_description": "06mm TEMPERADO INCOLOR",
        "closure_mode": MONO,
        "hinge_description": "DOBRADIÇA 90MM",
        "top_flag_height_mm": 400,
    }
    values.update(overrides)
    return GrConfiguration(**values)


class GrPhase16Tests(unittest.TestCase):
    def test_version_is_v016(self):
        self.assertEqual(calculate_gr(two_leaf_flag()).calculation_version, "GR_ENGINE_0.16.0")

    def test_orcs_14051_geometry_and_cost_are_frozen(self):
        result = calculate_gr(two_leaf_flag())
        self.assertEqual(result.geometry["frame_height_final_mm"], 2700.0)
        self.assertEqual(result.geometry["leaf_width_final_mm"], 694.0)
        self.assertEqual(result.geometry["leaf_height_final_mm"], 2285.0)
        self.assertEqual(result.geometry["glass_width_mm"], 514.0)
        self.assertEqual(result.geometry["glass_height_mm"], 2105.0)
        self.assertEqual(result.geometry["glass_panel_count"], 2.0)
        self.assertEqual(result.geometry["top_flag_boundary_transom_length_mm"], 1404.0)
        self.assertEqual(result.geometry["top_flag_glass_width_mm"], 1384.0)
        self.assertEqual(result.geometry["top_flag_glass_height_mm"], 334.0)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 63.3456)
        self.assertEqual(result.unit_cost, 2576.57885)

    def test_two_leaf_top_flag_preserves_one_frame_horizontal(self):
        result = calculate_gr(two_leaf_flag())
        by_role = {x.role: x for x in result.unit_bom}
        self.assertEqual(by_role["FRAME_WIDTH"].quantity_per_unit, 1.0)
        self.assertEqual(by_role["FRAME_REINFORCEMENT_WIDTH"].quantity_per_unit, 1.0)
        self.assertEqual(by_role["DRAIN_CAP"].quantity_per_unit, 1.0)
        self.assertEqual(by_role["TOP_FLAG_BOUNDARY_TRANSOM"].quantity_per_unit, 1.0)

    def test_gr_g118_uses_four_leaf_profile_pieces(self):
        result = calculate_gr(two_leaf_flag())
        by_role = {x.role: x for x in result.unit_bom}
        self.assertEqual(by_role["LEAF_WIDTH"].quantity_per_unit, 4.0)
        self.assertEqual(by_role["LEAF_HEIGHT"].quantity_per_unit, 4.0)
        self.assertEqual(by_role["REINFORCEMENT_SCREWS"].quantity_per_unit, 70.16)

    def test_passive_leaf_hardware_and_blocks_are_preserved(self):
        result = calculate_gr(two_leaf_flag())
        by_role = {x.role: x for x in result.unit_bom}
        self.assertEqual(by_role["SQUARING_BLOCK"].quantity_per_unit, 8.0)
        self.assertEqual(by_role["PASSIVE_LEAF_COUNTER_CLAW"].quantity_per_unit, 2.0)
        self.assertEqual(by_role["PASSIVE_LEAF_CLAW_LOCK"].quantity_per_unit, 2.0)

    def test_top_flag_is_single_fixed_opening_across_full_width(self):
        result = calculate_gr(two_leaf_flag())
        self.assertEqual(len(result.fixed_panels), 1)
        panel = result.fixed_panels[0]
        self.assertEqual(panel.position.value, "TOP")
        self.assertEqual(len(panel.openings), 1)
        self.assertEqual(panel.openings[0].width_mm, 1392.0)
        self.assertEqual(panel.openings[0].height_mm, 342.0)
        self.assertEqual(result.transoms[-1].material_code, "DE6072")
        self.assertEqual(result.transoms[-1].quantity, 1.0)

    def test_external_two_leaf_top_flag_remains_blocked_without_clean_orcs(self):
        with self.assertRaises(ValueError):
            calculate_gr(two_leaf_flag(leaf_system=EXTERNAL))

    def test_screen_and_shutter_remain_blocked_with_two_leaf_flag(self):
        with self.assertRaises(ValueError):
            calculate_gr(two_leaf_flag(screen_enabled=True))

    def test_one_leaf_v015_top_flag_regression_is_preserved(self):
        result = calculate_gr(GrConfiguration(
            width_mm=1200,
            height_mm=2700,
            quantity=1,
            leaf_count=1,
            leaf_system=INTERNAL,
            application="PORTA",
            panel_mode="VIDRO INTEIRO",
            glass_description="08mm TEMPERADO INCOLOR",
            closure_mode=MONO,
            hinge_description="DOBRADIÇA 90MM",
            top_flag_height_mm=600,
        ))
        self.assertEqual(result.calculation_version, "GR_ENGINE_0.16.0")
        self.assertEqual(result.unit_cost, 1863.30363)

    def test_cost_is_exact_sum_of_bom(self):
        result = calculate_gr(two_leaf_flag())
        self.assertEqual(
            result.unit_cost,
            round(sum(x.cost_per_unit_product for x in result.unit_bom), 6),
        )
        self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)

    def test_golden_v016_is_frozen(self):
        golden = json.loads(
            (ROOT / "test_cases" / "gr_golden_v0_16.json").read_text(encoding="utf-8")
        )
        self.assertEqual(golden["engine_version"], "GR_ENGINE_0.16.0")
        for case in golden["cases"]:
            result = calculate_gr(GrConfiguration(**case["input"]))
            self.assertEqual(result.calculation_version, golden["engine_version"])
            self.assertEqual(result.unit_cost, case["unit_cost"])
            self.assertEqual(result.cost_breakdown["VEDAÇÕES"], case["sealing_cost"])
            for key, expected in case["geometry"].items():
                self.assertEqual(result.geometry[key], expected)


if __name__ == "__main__":
    unittest.main()
