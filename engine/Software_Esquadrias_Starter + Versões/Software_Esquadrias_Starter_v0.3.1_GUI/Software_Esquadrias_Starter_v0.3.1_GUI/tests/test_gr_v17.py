import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import GrConfiguration, calculate_gr  # noqa: E402

WINDOW = "FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN"
CREMONA = "MAÇANETA COM CREMONA SEM CHAVE"
OB_1100 = "CREMONA OSCILO/GIRO COMP. 1100mm E:15mm"


def bottom_flag(**overrides):
    values = {
        "width_mm": 800,
        "height_mm": 2100,
        "quantity": 1,
        "leaf_count": 1,
        "leaf_system": WINDOW,
        "application": "JANELA",
        "panel_mode": "VIDRO INTEIRO",
        "glass_description": "06mm TEMPERADO INCOLOR",
        "closure_mode": CREMONA,
        "cremona_description": OB_1100,
        "hinge_description": "DOBRADIÇA SISTEMA OB",
        "bottom_flag_height_mm": 600,
    }
    values.update(overrides)
    return GrConfiguration(**values)


class GrPhase17Tests(unittest.TestCase):
    def test_version_is_v017(self):
        self.assertEqual(calculate_gr(bottom_flag()).calculation_version, "GR_ENGINE_0.17.0")

    def test_orcs_10588_geometry_is_frozen(self):
        result = calculate_gr(bottom_flag())
        self.assertEqual(result.geometry["frame_height_final_mm"], 2100.0)
        self.assertEqual(result.geometry["frame_height_cut_mm"], 2105.0)
        self.assertEqual(result.geometry["leaf_width_final_mm"], 736.0)
        self.assertEqual(result.geometry["leaf_height_final_mm"], 1458.0)
        self.assertEqual(result.geometry["glass_width_mm"], 608.0)
        self.assertEqual(result.geometry["glass_height_mm"], 1330.0)
        self.assertEqual(result.geometry["bottom_flag_height_mm"], 600.0)
        self.assertEqual(result.geometry["bottom_flag_boundary_transom_length_mm"], 732.0)
        self.assertEqual(result.geometry["bottom_flag_bead_width_mm"], 720.0)
        self.assertEqual(result.geometry["bottom_flag_bead_height_mm"], 542.0)
        self.assertEqual(result.geometry["bottom_flag_glass_width_mm"], 712.0)
        self.assertEqual(result.geometry["bottom_flag_glass_height_mm"], 534.0)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 25.6192)

    def test_bottom_flag_is_explicit_fixed_panel(self):
        result = calculate_gr(bottom_flag())
        self.assertEqual(len(result.fixed_panels), 1)
        panel = result.fixed_panels[0]
        self.assertEqual(panel.position.value, "BOTTOM")
        self.assertEqual(panel.openings[0].width_mm, 720.0)
        self.assertEqual(panel.openings[0].height_mm, 542.0)
        self.assertEqual(result.transoms[-1].material_code, "DE6072")
        self.assertEqual(result.transoms[-1].reinforcement_material_code, "RAG - DE6072")
        self.assertEqual(result.transoms[-1].length_mm, 732.0)

    def test_window_frame_keeps_two_outer_horizontals_plus_boundary(self):
        result = calculate_gr(bottom_flag())
        by_role = {x.role: x for x in result.unit_bom}
        self.assertEqual(by_role["FRAME_WIDTH"].quantity_per_unit, 2.0)
        self.assertEqual(by_role["FRAME_REINFORCEMENT_WIDTH"].quantity_per_unit, 2.0)
        self.assertEqual(by_role["DRAIN_CAP"].quantity_per_unit, 2.0)
        self.assertEqual(by_role["BOTTOM_FLAG_BOUNDARY_TRANSOM"].quantity_per_unit, 1.0)

    def test_reinforcement_screws_follow_gr_g118_topology(self):
        result = calculate_gr(bottom_flag())
        screws = next(x for x in result.unit_bom if x.role == "REINFORCEMENT_SCREWS")
        self.assertEqual(screws.quantity_per_unit, 43.84)

    def test_legacy_double_subtraction_warning_is_present(self):
        warnings = {x.code for x in calculate_gr(bottom_flag()).warnings}
        self.assertIn("LEGACY-GR-BOTTOM-FLAG-HEIGHT-DOUBLE-SUBTRACTION-CORRECTED", warnings)
        self.assertIn("LEGACY-GR-FLAG-E40-REFERENCE-CORRECTED", warnings)

    def test_current_cost_probe(self):
        result = calculate_gr(bottom_flag())
        self.assertEqual(result.unit_cost, -1.0)

    def test_shutter_screen_and_two_leaf_remain_blocked(self):
        with self.assertRaises(ValueError):
            calculate_gr(bottom_flag(screen_enabled=True))
        with self.assertRaises(ValueError):
            calculate_gr(bottom_flag(leaf_count=2))

    def test_cost_is_exact_sum_of_bom(self):
        result = calculate_gr(bottom_flag())
        self.assertEqual(
            result.unit_cost,
            round(sum(x.cost_per_unit_product for x in result.unit_bom), 6),
        )
        self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)


if __name__ == "__main__":
    unittest.main()
