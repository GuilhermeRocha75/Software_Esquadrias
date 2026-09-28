import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import GrConfiguration, calculate_gr  # noqa: E402

WINDOW = "FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN"
CREMONA = "MAÇANETA COM CREMONA SEM CHAVE"
CREMONA_800 = "CREMONA 2 PONTOS COMP. 800mm E:15mm"


def dual_flag(**overrides):
    values = {
        "width_mm": 400,
        "height_mm": 2000,
        "quantity": 1,
        "leaf_count": 1,
        "leaf_system": WINDOW,
        "application": "JANELA",
        "panel_mode": "VIDRO INTEIRO",
        "glass_description": "04mm MINI BOREAL",
        "closure_mode": CREMONA,
        "cremona_description": CREMONA_800,
        "hinge_description": "DOBRADIÇA 90MM",
        "bottom_flag_height_mm": 400,
        "top_flag_height_mm": 400,
    }
    values.update(overrides)
    return GrConfiguration(**values)


class GrPhase18Tests(unittest.TestCase):
    def test_version_is_v018(self):
        self.assertEqual(calculate_gr(dual_flag()).calculation_version, "GR_ENGINE_0.18.0")

    def test_orcs_16482_geometry_is_frozen(self):
        result = calculate_gr(dual_flag())
        self.assertEqual(result.geometry["frame_height_final_mm"], 2000.0)
        self.assertEqual(result.geometry["frame_height_cut_mm"], 2005.0)
        self.assertEqual(result.geometry["leaf_width_final_mm"], 336.0)
        self.assertEqual(result.geometry["leaf_height_final_mm"], 1158.0)
        self.assertEqual(result.geometry["glass_width_mm"], 208.0)
        self.assertEqual(result.geometry["glass_height_mm"], 1030.0)
        self.assertEqual(result.geometry["bottom_flag_height_mm"], 400.0)
        self.assertEqual(result.geometry["top_flag_height_mm"], 400.0)
        self.assertEqual(result.geometry["bottom_flag_boundary_transom_length_mm"], 332.0)
        self.assertEqual(result.geometry["top_flag_boundary_transom_length_mm"], 332.0)
        self.assertEqual(result.geometry["bottom_flag_bead_width_mm"], 320.0)
        self.assertEqual(result.geometry["bottom_flag_bead_height_mm"], 342.0)
        self.assertEqual(result.geometry["top_flag_bead_width_mm"], 320.0)
        self.assertEqual(result.geometry["top_flag_bead_height_mm"], 342.0)
        self.assertEqual(result.geometry["bottom_flag_glass_width_mm"], 312.0)
        self.assertEqual(result.geometry["bottom_flag_glass_height_mm"], 334.0)
        self.assertEqual(result.geometry["top_flag_glass_width_mm"], 312.0)
        self.assertEqual(result.geometry["top_flag_glass_height_mm"], 334.0)
        self.assertEqual(result.geometry["flag_boundary_transom_count"], 2.0)

    def test_two_fixed_panels_and_two_boundaries_are_explicit(self):
        result = calculate_gr(dual_flag())
        self.assertEqual(len(result.fixed_panels), 2)
        self.assertEqual(
            {panel.position.value for panel in result.fixed_panels},
            {"BOTTOM", "TOP"},
        )
        self.assertEqual(len(result.transoms), 2)
        self.assertTrue(all(t.material_code == "DE6072" for t in result.transoms))
        self.assertTrue(all(t.reinforcement_material_code == "RAG - DE6072" for t in result.transoms))
        self.assertTrue(all(t.length_mm == 332.0 for t in result.transoms))

    def test_window_frame_keeps_two_outer_horizontals_plus_two_boundaries(self):
        result = calculate_gr(dual_flag())
        by_role = {x.role: x for x in result.unit_bom}
        self.assertEqual(by_role["FRAME_WIDTH"].quantity_per_unit, 2.0)
        self.assertEqual(by_role["FRAME_REINFORCEMENT_WIDTH"].quantity_per_unit, 2.0)
        self.assertEqual(by_role["DRAIN_CAP"].quantity_per_unit, 2.0)
        self.assertEqual(by_role["BOTTOM_FLAG_BOUNDARY_TRANSOM"].quantity_per_unit, 1.0)
        self.assertEqual(by_role["TOP_FLAG_BOUNDARY_TRANSOM"].quantity_per_unit, 1.0)

    def test_reinforcement_screws_follow_gr_g118_with_two_boundaries(self):
        result = calculate_gr(dual_flag())
        screws = next(x for x in result.unit_bom if x.role == "REINFORCEMENT_SCREWS")
        self.assertEqual(screws.quantity_per_unit, 33.968)

    def test_dual_flag_adds_glass_seal_for_each_fixed_panel(self):
        result = calculate_gr(dual_flag())
        by_role = {x.role: x for x in result.unit_bom}
        self.assertEqual(by_role["BOTTOM_FLAG_GLASS_SEAL"].material_code, "ACB606")
        self.assertEqual(by_role["TOP_FLAG_GLASS_SEAL"].material_code, "ACB606")

    def test_legacy_dual_subtraction_warning_is_present(self):
        warnings = {x.code for x in calculate_gr(dual_flag()).warnings}
        self.assertIn("LEGACY-GR-DUAL-FLAG-HEIGHT-DOUBLE-SUBTRACTION-CORRECTED", warnings)
        self.assertIn("LEGACY-GR-FLAG-E40-REFERENCE-CORRECTED", warnings)

    def test_orcs_16482_current_physical_cost_is_frozen(self):
        result = calculate_gr(dual_flag())
        self.assertEqual(result.unit_cost, 849.55152)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 18.8424)

    def test_screen_shutter_ob_and_two_leaf_remain_blocked_in_phase18(self):
        with self.assertRaises(ValueError):
            calculate_gr(dual_flag(screen_enabled=True))
        with self.assertRaises(ValueError):
            calculate_gr(dual_flag(leaf_count=2))
        with self.assertRaises(ValueError):
            calculate_gr(dual_flag(
                hinge_description="DOBRADIÇA SISTEMA OB",
                cremona_description="CREMONA OSCILO/GIRO COMP. 1100mm E:15mm",
            ))

    def test_golden_v018_is_frozen(self):
        golden = json.loads(
            (ROOT / "test_cases" / "gr_golden_v0_18.json").read_text(encoding="utf-8")
        )
        self.assertEqual(golden["engine_version"], "GR_ENGINE_0.18.0")
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
        result = calculate_gr(dual_flag())
        self.assertEqual(
            result.unit_cost,
            round(sum(x.cost_per_unit_product for x in result.unit_bom), 6),
        )
        self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)


if __name__ == "__main__":
    unittest.main()
