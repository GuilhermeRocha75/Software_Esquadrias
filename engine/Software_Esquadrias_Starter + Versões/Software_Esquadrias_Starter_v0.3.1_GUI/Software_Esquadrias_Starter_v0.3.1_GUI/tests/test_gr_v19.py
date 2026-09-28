import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine.gr_v19 import GrConfiguration, calculate_gr  # noqa: E402

INTERNAL = "FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN"
MONO = "MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE"


def divided_top_flag(**overrides):
    values = {
        "width_mm": 1610,
        "height_mm": 5220,
        "quantity": 1,
        "leaf_count": 2,
        "leaf_system": INTERNAL,
        "application": "PORTA",
        "panel_mode": "VIDRO INTEIRO",
        "glass_description": "10mm TEMPERADO INCOLOR",
        "closure_mode": MONO,
        "hinge_description": "DOBRADIÇA 90MM",
        "top_flag_height_mm": 2790,
        "top_flag_vertical_transoms": 1,
    }
    values.update(overrides)
    return GrConfiguration(**values)


class GrPhase19Tests(unittest.TestCase):
    def test_version_is_v019(self):
        self.assertEqual(
            calculate_gr(divided_top_flag()).calculation_version,
            "GR_ENGINE_0.19.0",
        )

    def test_orcs_15295_geometry_is_frozen(self):
        result = calculate_gr(divided_top_flag())
        self.assertEqual(result.geometry["frame_height_final_mm"], 5220.0)
        self.assertEqual(result.geometry["leaf_width_final_mm"], 763.0)
        self.assertEqual(result.geometry["leaf_height_final_mm"], 2415.0)
        self.assertEqual(result.geometry["glass_width_mm"], 583.0)
        self.assertEqual(result.geometry["glass_height_mm"], 2235.0)
        self.assertEqual(result.geometry["glass_panel_count"], 2.0)
        self.assertEqual(result.geometry["top_flag_height_mm"], 2790.0)
        self.assertEqual(result.geometry["top_flag_vertical_transoms"], 1.0)
        self.assertEqual(result.geometry["top_flag_opening_count"], 2.0)
        self.assertEqual(result.geometry["top_flag_bead_width_mm"], 747.0)
        self.assertEqual(result.geometry["top_flag_bead_height_mm"], 2732.0)
        self.assertEqual(result.geometry["top_flag_glass_width_mm"], 739.0)
        self.assertEqual(result.geometry["top_flag_glass_height_mm"], 2724.0)
        self.assertEqual(
            result.geometry["top_flag_internal_vertical_transom_length_mm"],
            2744.0,
        )
        self.assertEqual(result.geometry["top_flag_glass_panel_count"], 2.0)

    def test_top_flag_grid_has_two_openings_and_internal_vertical(self):
        result = calculate_gr(divided_top_flag())
        self.assertEqual(len(result.fixed_panels), 1)
        panel = result.fixed_panels[0]
        self.assertEqual(panel.position.value, "TOP")
        self.assertEqual(panel.vertical_transoms, 1)
        self.assertEqual(panel.horizontal_transoms, 0)
        self.assertEqual(len(panel.openings), 2)
        self.assertTrue(all(x.width_mm == 747.0 for x in panel.openings))
        self.assertTrue(all(x.height_mm == 2732.0 for x in panel.openings))
        self.assertEqual(len(result.transoms), 2)
        divider = next(x for x in result.transoms if x.source == "TOP_FLAG_INTERNAL")
        self.assertEqual(divider.orientation.value, "VERTICAL")
        self.assertEqual(divider.material_code, "DE6072")
        self.assertEqual(divider.reinforcement_material_code, "RAG - DE6072")
        self.assertEqual(divider.length_mm, 2744.0)

    def test_baguettes_and_glass_are_physical_per_opening(self):
        result = calculate_gr(divided_top_flag())
        by_role = {x.role: x for x in result.unit_bom}
        self.assertEqual(by_role["TOP_FLAG_BEAD_HORIZONTAL"].quantity_per_unit, 4.0)
        self.assertEqual(by_role["TOP_FLAG_BEAD_HORIZONTAL"].length_mm, 747.0)
        self.assertEqual(by_role["TOP_FLAG_BEAD_VERTICAL"].quantity_per_unit, 4.0)
        self.assertEqual(by_role["TOP_FLAG_BEAD_VERTICAL"].length_mm, 2732.0)
        self.assertEqual(by_role["TOP_FLAG_GLASS_PANEL_1"].width_mm, 739.0)
        self.assertEqual(by_role["TOP_FLAG_GLASS_PANEL_1"].height_mm, 2724.0)
        self.assertEqual(by_role["TOP_FLAG_GLASS_PANEL_2"].width_mm, 739.0)
        self.assertEqual(by_role["TOP_FLAG_GLASS_PANEL_2"].height_mm, 2724.0)
        self.assertEqual(by_role["TOP_FLAG_GLASS_SEAL"].material_code, "ACB606")

    def test_vertical_divider_reinforcement_and_screws_are_corrected(self):
        result = calculate_gr(divided_top_flag())
        by_role = {x.role: x for x in result.unit_bom}
        self.assertEqual(
            by_role["TOP_FLAG_INTERNAL_VERTICAL_REINFORCEMENT"].material_code,
            "RAG - DE6072",
        )
        self.assertEqual(
            by_role["TOP_FLAG_INTERNAL_VERTICAL_REINFORCEMENT"].length_mm,
            2744.0,
        )
        self.assertEqual(
            result.geometry["top_flag_internal_vertical_reinforcement_screws_added"],
            7.0,
        )
        self.assertEqual(by_role["REINFORCEMENT_SCREWS"].quantity_per_unit, 91.528)

    def test_legacy_grid_warnings_are_present(self):
        warnings = {x.code for x in calculate_gr(divided_top_flag()).warnings}
        self.assertIn("LEGACY-GR-TOP-FLAG-GRID-BAGUETTE-COUNT-CORRECTED", warnings)
        self.assertIn("LEGACY-GR-TOP-FLAG-GRID-REINFORCEMENT-CORRECTED", warnings)
        self.assertIn("LEGACY-GR-FLAG-E40-REFERENCE-CORRECTED", warnings)

    def test_orcs_15295_current_physical_cost_is_frozen(self):
        result = calculate_gr(divided_top_flag())
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 86.132)
        self.assertEqual(result.unit_cost, 5594.46035)

    def test_other_flag_grids_remain_blocked(self):
        with self.assertRaises(ValueError):
            calculate_gr(divided_top_flag(top_flag_vertical_transoms=2))
        with self.assertRaises(ValueError):
            calculate_gr(divided_top_flag(
                top_flag_vertical_transoms=0,
                top_flag_horizontal_transoms=1,
            ))
        with self.assertRaises(ValueError):
            calculate_gr(divided_top_flag(
                top_flag_vertical_transoms=0,
                bottom_flag_vertical_transoms=1,
                bottom_flag_height_mm=500,
                top_flag_height_mm=0,
            ))

    def test_golden_v019_is_frozen(self):
        golden = json.loads(
            (ROOT / "test_cases" / "gr_golden_v0_19.json").read_text(encoding="utf-8")
        )
        self.assertEqual(golden["engine_version"], "GR_ENGINE_0.19.0")
        for case in golden["cases"]:
            result = calculate_gr(GrConfiguration(**case["input"]))
            self.assertEqual(result.calculation_version, golden["engine_version"])
            self.assertEqual(result.unit_cost, case["unit_cost"])
            self.assertEqual(result.cost_breakdown["VEDAÇÕES"], case["sealing_cost"])
            screws = next(x for x in result.unit_bom if x.role == "REINFORCEMENT_SCREWS")
            self.assertEqual(screws.quantity_per_unit, case["reinforcement_screws"])
            for key, expected in case["geometry"].items():
                self.assertEqual(result.geometry[key], expected)

    def test_cost_is_exact_sum_of_bom(self):
        result = calculate_gr(divided_top_flag())
        self.assertEqual(
            result.unit_cost,
            round(sum(x.cost_per_unit_product for x in result.unit_bom), 6),
        )
        self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)


if __name__ == "__main__":
    unittest.main()
