import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine.gr_v15 import GrConfiguration, calculate_gr  # noqa: E402

INTERNAL = "FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN"
EXTERNAL = "FOLHA DE PORTA ABERTURA EXTERNA 60X104MM - DESIGN"
MONO = "MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE"


def top_flag(**overrides):
    values = {
        "width_mm": 1200,
        "height_mm": 2700,
        "quantity": 1,
        "leaf_count": 1,
        "leaf_system": INTERNAL,
        "application": "PORTA",
        "panel_mode": "VIDRO INTEIRO",
        "glass_description": "08mm TEMPERADO INCOLOR",
        "closure_mode": MONO,
        "hinge_description": "DOBRADIÇA 90MM",
        "top_flag_height_mm": 600,
    }
    values.update(overrides)
    return GrConfiguration(**values)


class GrPhase15Tests(unittest.TestCase):
    def test_version_is_v015(self):
        self.assertEqual(calculate_gr(top_flag()).calculation_version, "GR_ENGINE_0.15.0")

    def test_orcs_14891_internal_top_flag_golden(self):
        result = calculate_gr(top_flag())
        self.assertEqual(result.geometry["frame_height_final_mm"], 2700.0)
        self.assertEqual(result.geometry["leaf_width_final_mm"], 1136.0)
        self.assertEqual(result.geometry["leaf_height_final_mm"], 2085.0)
        self.assertEqual(result.geometry["glass_width_mm"], 956.0)
        self.assertEqual(result.geometry["glass_height_mm"], 1905.0)
        self.assertEqual(result.geometry["top_flag_boundary_transom_length_mm"], 1132.0)
        self.assertEqual(result.geometry["top_flag_glass_width_mm"], 1112.0)
        self.assertEqual(result.geometry["top_flag_glass_height_mm"], 534.0)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 36.9548)
        self.assertEqual(result.unit_cost, 1863.30363)

    def test_orcs_11251_external_top_flag_golden(self):
        result = calculate_gr(top_flag(
            width_mm=1100,
            leaf_system=EXTERNAL,
        ))
        self.assertEqual(result.geometry["leaf_width_final_mm"], 1036.0)
        self.assertEqual(result.geometry["top_flag_boundary_transom_length_mm"], 1032.0)
        self.assertEqual(result.geometry["top_flag_glass_width_mm"], 1012.0)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 35.5948)
        self.assertEqual(result.unit_cost, 1790.84127)
        codes = {x.material_code for x in result.unit_bom}
        self.assertIn("DE60104-E", codes)
        self.assertNotIn("DE60104", codes)

    def test_integrated_door_keeps_single_frame_horizontal(self):
        result = calculate_gr(top_flag())
        by_role = {x.role: x for x in result.unit_bom}
        self.assertEqual(by_role["FRAME_WIDTH"].quantity_per_unit, 1.0)
        self.assertEqual(by_role["FRAME_REINFORCEMENT_WIDTH"].quantity_per_unit, 1.0)
        self.assertEqual(by_role["DRAIN_CAP"].quantity_per_unit, 1.0)
        self.assertEqual(by_role["TOP_FLAG_BOUNDARY_TRANSOM"].quantity_per_unit, 1.0)

    def test_flag_boundary_and_fixed_panel_are_explicit(self):
        result = calculate_gr(top_flag())
        self.assertEqual(len(result.fixed_panels), 1)
        self.assertEqual(result.fixed_panels[0].position.value, "TOP")
        self.assertEqual(result.fixed_panels[0].openings[0].width_mm, 1120.0)
        self.assertEqual(result.fixed_panels[0].openings[0].height_mm, 542.0)
        self.assertEqual(len(result.transoms), 1)
        self.assertEqual(result.transoms[0].material_code, "DE6072")
        self.assertEqual(result.transoms[0].reinforcement_material_code, "RAG - DE6072")

    def test_flag_uses_same_glass_baguette_and_extra_glass_seal(self):
        result = calculate_gr(top_flag())
        roles = {x.role: x for x in result.unit_bom}
        self.assertEqual(roles["TOP_FLAG_BEAD_HORIZONTAL"].material_code, "BA3218")
        self.assertEqual(roles["TOP_FLAG_BEAD_VERTICAL"].material_code, "BA3218")
        self.assertEqual(roles["TOP_FLAG_GLASS_PANEL"].material_code, "8TI")
        self.assertEqual(roles["TOP_FLAG_GLASS_SEAL"].material_code, "ACB606")

    def test_legacy_e40_reference_warning_is_present(self):
        warnings = {x.code for x in calculate_gr(top_flag()).warnings}
        self.assertIn("LEGACY-GR-FLAG-E40-REFERENCE-CORRECTED", warnings)

    def test_bottom_flag_and_combined_flag_remain_blocked(self):
        with self.assertRaises(ValueError):
            calculate_gr(top_flag(top_flag_height_mm=0, bottom_flag_height_mm=500))
        with self.assertRaises(ValueError):
            calculate_gr(top_flag(bottom_flag_height_mm=300))

    def test_screen_shutter_and_two_leaf_combinations_remain_blocked(self):
        with self.assertRaises(ValueError):
            calculate_gr(top_flag(screen_enabled=True))
        with self.assertRaises(ValueError):
            calculate_gr(top_flag(leaf_count=2))

    def test_no_flag_preserves_v014_regression(self):
        result = calculate_gr(GrConfiguration(
            width_mm=900,
            height_mm=2100,
            quantity=1,
            leaf_count=1,
            leaf_system=EXTERNAL,
            application="PORTA",
            panel_mode="PAINEL COMPLETO",
            closure_mode=MONO,
            hinge_description="DOBRADIÇA 90MM",
        ))
        self.assertEqual(result.calculation_version, "GR_ENGINE_0.15.0")
        self.assertEqual(result.unit_cost, 1409.391705)

    def test_cost_is_exact_sum_of_bom(self):
        result = calculate_gr(top_flag())
        self.assertEqual(
            result.unit_cost,
            round(sum(x.cost_per_unit_product for x in result.unit_bom), 6),
        )
        self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)

    def test_golden_v015_is_frozen(self):
        golden = json.loads(
            (ROOT / "test_cases" / "gr_golden_v0_15.json").read_text(encoding="utf-8")
        )
        self.assertEqual(golden["engine_version"], "GR_ENGINE_0.15.0")
        for case in golden["cases"]:
            with self.subTest(case=case["id"]):
                result = calculate_gr(GrConfiguration(**case["input"]))
                self.assertEqual(result.calculation_version, golden["engine_version"])
                self.assertEqual(result.unit_cost, case["unit_cost"])
                self.assertEqual(result.cost_breakdown["VEDAÇÕES"], case["sealing_cost"])
                for key, expected in case["geometry"].items():
                    self.assertEqual(result.geometry[key], expected)


if __name__ == "__main__":
    unittest.main()
