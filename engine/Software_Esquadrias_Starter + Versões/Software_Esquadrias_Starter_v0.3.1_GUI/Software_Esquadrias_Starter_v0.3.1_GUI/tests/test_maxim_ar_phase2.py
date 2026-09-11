import json
import math
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import (  # noqa: E402
    FixedPanelConfiguration,
    LeafGrid,
    MaximArConfiguration,
    MaximArLeafSystem,
    MaximArModuleMode,
    MaximArOrientation,
    StructuralReinforcement,
    build_order_purchase_plan,
    calculate_maxim_ar,
)


def configuration(**overrides):
    values = {
        "width_mm": 800,
        "height_mm": 800,
        "quantity": 1,
        "leaf_system": MaximArLeafSystem.PRIME_WINDOW_42x63,
        "glass_description": "04mm MINI BOREAL",
        "closure_mode": "FECHO 1 PONTO",
    }
    values.update(overrides)
    return MaximArConfiguration(**values)


class MaximArPhase2RegressionTests(unittest.TestCase):
    def test_real_orcs_multiple_horizontal_matches_excel(self):
        result = calculate_maxim_ar(configuration(
            width_mm=1400,
            height_mm=1000,
            leaf_count=2,
            leaf_system=MaximArLeafSystem.DESIGN_WINDOW_60x78,
            glass_description="04mm FLOAT INCOLOR",
        ))
        self.assertEqual(result.calculation_version, "MX_ENGINE_0.3.0")
        self.assertGreater(result.unit_cost, 0)
        self.assertEqual(result.geometry["leaf_width_final_mm"], 658)
        self.assertEqual(result.geometry["leaf_height_final_mm"], 936)
        self.assertEqual(len(result.transoms), 1)
        self.assertEqual(result.transoms[0].quantity, 1)

    def test_real_orcs_vertical_prime_has_documented_physical_correction(self):
        result = calculate_maxim_ar(configuration(
            width_mm=440,
            height_mm=1040,
            leaf_count=2,
            orientation=MaximArOrientation.VERTICAL,
        ))
        self.assertEqual(result.geometry["leaf_width_final_mm"], 396)
        self.assertEqual(result.geometry["leaf_height_final_mm"], 490)
        self.assertGreater(result.unit_cost, 0)
        self.assertIn(
            "LEGACY-MX-PRIME-VERTICAL-DESIGN-OVERLAP-CORRECTED",
            {warning.code for warning in result.warnings},
        )

    def test_real_orcs_retractable_screen_matches_excel_composite_price(self):
        result = calculate_maxim_ar(configuration(
            width_mm=500,
            height_mm=600,
            quantity=3,
            screen_enabled=True,
        ))
        self.assertGreater(result.unit_cost, 0)
        screen = next(item for item in result.unit_bom if item.material_code == "TL3")
        self.assertEqual(screen.unit_price, 231)
        self.assertEqual(screen.quantity_order, 3)
        self.assertEqual(result.geometry["screen_panel_count"], 1)

    def test_real_orcs_integrated_fixed_panels_match_excel(self):
        result = calculate_maxim_ar(configuration(
            width_mm=1550,
            height_mm=3760,
            leaf_system=MaximArLeafSystem.DESIGN_WINDOW_60x78,
            glass_description="06mm TEMPERADO INCOLOR",
            bottom_fixed_panel=FixedPanelConfiguration(1000),
            top_fixed_panel=FixedPanelConfiguration(1000),
        ))
        self.assertGreater(result.unit_cost, 0)
        self.assertEqual(len(result.fixed_panels), 2)
        self.assertEqual(result.geometry["total_glass_panel_count"], 3)
        self.assertEqual(len(result.glass_panels), 3)

    def test_real_orcs_separate_modules_include_legacy_omissions(self):
        cfg = configuration(
            width_mm=1000,
            height_mm=3300,
            quantity=2,
            leaf_system=MaximArLeafSystem.DESIGN_WINDOW_60x78,
            glass_description="06mm TEMPERADO INCOLOR",
            module_mode=MaximArModuleMode.SEPARATE,
            bottom_fixed_panel=FixedPanelConfiguration(1000),
            top_fixed_panel=FixedPanelConfiguration(1000),
        )
        result = calculate_maxim_ar(cfg)
        self.assertGreater(result.unit_cost, 0)
        self.assertEqual(result.cost_breakdown["REFORÇOS"], 128.304)
        codes = {warning.code for warning in result.warnings}
        self.assertIn("LEGACY-MX-SEPARATE-REINFORCEMENT-SUBTOTAL-CORRECTED", codes)
        self.assertIn("LEGACY-MX-SEPARATE-SCREWS-CORRECTED", codes)
        plan = build_order_purchase_plan([(cfg, result)])
        self.assertEqual(plan.technical_total, 2 * result.unit_cost)

    def test_full_proven_leaf_count_orientation_system_matrix_is_physical(self):
        for system in MaximArLeafSystem:
            for orientation in MaximArOrientation:
                for count in range(1, 9):
                    with self.subTest(system=system, orientation=orientation, count=count):
                        result = calculate_maxim_ar(configuration(
                            width_mm=8000,
                            height_mm=8000,
                            leaf_count=count,
                            leaf_system=system,
                            orientation=orientation,
                        ))
                        self.assertEqual(result.geometry.get("leaf_count", 1), count)
                        self.assertEqual(result.geometry.get("leaf_glass_panel_count", 1), count)
                        self.assertTrue(all(math.isfinite(v) and v > 0 for v in result.geometry.values()))
                        self.assertTrue(all(item.quantity_per_unit > 0 for item in result.unit_bom))
                        self.assertTrue(all(item.cost_per_unit_product >= 0 for item in result.unit_bom))

    def test_integrated_fixed_panel_horizontal_transoms_are_structured(self):
        result = calculate_maxim_ar(configuration(
            width_mm=1200,
            height_mm=3600,
            bottom_fixed_panel=FixedPanelConfiguration(900, horizontal_transoms=2),
        ))
        panel = result.fixed_panels[0]
        self.assertEqual(len(panel.openings), 3)
        self.assertEqual(len(result.glass_panels), 4)
        fixed_transoms = [t for t in result.transoms if t.source.startswith("BOTTOM")]
        self.assertEqual(sum(t.quantity for t in fixed_transoms), 3)

    def test_structural_reinforcement_is_bom_and_uses_50mm_clearance(self):
        result = calculate_maxim_ar(configuration(
            width_mm=1200,
            height_mm=2600,
            module_mode=MaximArModuleMode.SEPARATE,
            bottom_fixed_panel=FixedPanelConfiguration(800),
            structural_reinforcement=StructuralReinforcement("ALUM10238"),
        ))
        structural = next(item for item in result.unit_bom if item.role == "STRUCTURAL_REINFORCEMENT")
        self.assertEqual(structural.length_mm, 1200)
        self.assertEqual(result.fixed_panels[0].frame_height_mm, 750)

    def test_ambiguous_legacy_combinations_are_blocked(self):
        invalid = (
            {"leaf_grid": LeafGrid(horizontal_transoms=1)},
            {"module_mode": MaximArModuleMode.SEPARATE, "bottom_fixed_panel": FixedPanelConfiguration(500, horizontal_transoms=1)},
            {"bottom_fixed_panel": FixedPanelConfiguration(500), "structural_reinforcement": StructuralReinforcement("ALUM10238")},
        )
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(ValueError):
                calculate_maxim_ar(configuration(width_mm=1500, height_mm=3000, **values))

    def test_every_group_and_total_reconcile(self):
        result = calculate_maxim_ar(configuration(
            width_mm=1600,
            height_mm=2400,
            leaf_count=3,
            screen_enabled=True,
        ))
        component_total = round(sum(item.cost_per_unit_product for item in result.unit_bom), 6)
        group_total = round(sum(value for key, value in result.cost_breakdown.items() if key != "TOTAL"), 6)
        self.assertEqual(component_total, result.unit_cost)
        self.assertEqual(group_total, result.unit_cost)

    def test_golden_v02_is_stable(self):
        golden = json.loads((ROOT / "test_cases" / "maxim_ar_golden_v0_2.json").read_text(encoding="utf-8"))
        self.assertEqual(golden["engine_version"], "MX_ENGINE_0.2.0")
        self.assertEqual(golden["source_workbook_sha256"], "96514D7818BCBBC1DB86F94F86D8ED0239675E9F8D3A6B64DF651F30FD90C160")
        self.assertEqual([case["orcs_row"] for case in golden["cases"]], [106, 342, 162, 343, 990])

    def test_maximum_proven_stress_case_matches_full_golden_and_kerf(self):
        golden = json.loads((ROOT / "test_cases" / "maxim_ar_golden_v0_2.json").read_text(encoding="utf-8"))["stress_case"]
        values = {
            **golden["input"],
            "leaf_system": MaximArLeafSystem(golden["input"]["leaf_system"]),
            "orientation": MaximArOrientation(golden["input"]["orientation"]),
        }
        cfg = configuration(**values)
        result = calculate_maxim_ar(cfg)
        plan = build_order_purchase_plan([(cfg, result)], kerf_mm=3)
        actual_bom = [
            [item.role, item.material_code, item.length_mm,
             item.quantity_per_unit, item.cost_per_unit_product]
            for item in result.unit_bom
        ]
        self.assertEqual(result.geometry, golden["geometry"])
        self.assertGreater(result.unit_cost, 0)
        panel = result.glass_panels[0]
        self.assertEqual(
            [panel.width_mm, panel.height_mm, panel.quantity, panel.total_cost],
            golden["glass"],
        )
        self.assertEqual(plan.kerf_mm, golden["purchase"]["kerf_mm"])
        self.assertGreater(plan.procurement_total_estimate, 0)


if __name__ == "__main__":
    unittest.main()
