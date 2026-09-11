import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import (
    FixedPanelConfiguration, LeafGrid, MaximArConfiguration,
    MaximArLeafSystem, MaximArModuleMode, MaximArSealingConfiguration,
    StructuralReinforcement, build_order_purchase_plan, calculate_maxim_ar,
)


def cfg(**changes):
    values = dict(width_mm=1000, height_mm=1000, quantity=1,
                  leaf_system=MaximArLeafSystem.PRIME_WINDOW_42x63,
                  sealing=MaximArSealingConfiguration("SEAL-01", "Borracha configurada", 2.5))
    values.update(changes)
    return MaximArConfiguration(**values)


class MaximArPhase3BTests(unittest.TestCase):
    def test_prime_and_design_have_three_real_sealing_paths(self):
        for system in MaximArLeafSystem:
            result = calculate_maxim_ar(cfg(leaf_system=system))
            seals = [x for x in result.unit_bom if x.category == "VEDAÇÕES"]
            self.assertEqual([x.role for x in seals], ["GLASS_SEATING_SEAL", "LEAF_EXTERNAL_SEAL", "FRAME_CONTACT_SEAL"])
            self.assertTrue(all(x.material_code == "SEAL-01" and x.unit_price == 2.5 for x in seals))
            self.assertAlmostEqual(result.cost_breakdown["VEDAÇÕES"], sum(x.length_mm / 1000 * 2.5 for x in seals), 6)

    def test_one_by_one_uses_real_geometry_not_nominal_twelve_meters(self):
        result = calculate_maxim_ar(cfg())
        seals = {x.role: x.length_mm for x in result.unit_bom if x.category == "VEDAÇÕES"}
        self.assertEqual(seals["GLASS_SEATING_SEAL"], 3472)
        self.assertEqual(seals["LEAF_EXTERNAL_SEAL"], 3824)
        self.assertEqual(seals["FRAME_CONTACT_SEAL"], 3824)
        self.assertNotEqual(sum(seals.values()), 12000)

    def test_multiple_leaf_paths_are_per_leaf(self):
        result = calculate_maxim_ar(cfg(width_mm=3000, leaf_count=3))
        seals = {x.role: x.length_mm for x in result.unit_bom if x.category == "VEDAÇÕES"}
        expected = 2 * 3 * (result.geometry["leaf_width_final_mm"] + result.geometry["leaf_height_final_mm"])
        self.assertAlmostEqual(seals["LEAF_EXTERNAL_SEAL"], expected, 5)
        self.assertAlmostEqual(seals["FRAME_CONTACT_SEAL"], expected, 5)

    def test_af_and_ag_are_rejected(self):
        for grid in (LeafGrid(horizontal_transoms=1), LeafGrid(vertical_transoms=1)):
            with self.assertRaisesRegex(ValueError, "fisicamente inválidas"):
                calculate_maxim_ar(cfg(leaf_grid=grid))

    def test_separate_modules_reject_internal_transoms(self):
        with self.assertRaisesRegex(ValueError, "fisicamente inválidos"):
            calculate_maxim_ar(cfg(height_mm=2200, module_mode=MaximArModuleMode.SEPARATE,
                                    bottom_fixed_panel=FixedPanelConfiguration(600, 1, 0)))

    def test_03_and_generic_grid_generate_exact_panels_and_dividers(self):
        result = calculate_maxim_ar(cfg(height_mm=3000, bottom_fixed_panel=FixedPanelConfiguration(1000, 3, 0)))
        self.assertEqual(len(result.fixed_panels[0].openings), 4)
        self.assertEqual(sum(t.quantity for t in result.transoms if t.source == "BOTTOM_FIXED_DIVIDER"), 3)
        grid = calculate_maxim_ar(cfg(width_mm=2000, height_mm=3000,
                                      bottom_fixed_panel=FixedPanelConfiguration(1000, 2, 1)))
        self.assertEqual(len(grid.fixed_panels[0].openings), 6)
        self.assertEqual(grid.geometry["total_glass_panel_count"], 7)

    def test_four_blocks_per_real_glass_and_order_quantity(self):
        result = calculate_maxim_ar(cfg(height_mm=3000, quantity=3,
                                        bottom_fixed_panel=FixedPanelConfiguration(1000, 3, 0)))
        blocks = next(x for x in result.unit_bom if x.role == "GLAZING_BLOCK")
        self.assertEqual(blocks.quantity_per_unit, 20)
        self.assertEqual(blocks.quantity_order, 60)

    def test_structural_reinforcement_is_optional_and_separate_only(self):
        with self.assertRaisesRegex(ValueError, "somente em módulos separados"):
            calculate_maxim_ar(cfg(bottom_fixed_panel=FixedPanelConfiguration(500),
                                    structural_reinforcement=StructuralReinforcement("ALUM10238")))
        base = dict(height_mm=2200, module_mode=MaximArModuleMode.SEPARATE,
                    bottom_fixed_panel=FixedPanelConfiguration(600))
        without = calculate_maxim_ar(cfg(**base))
        self.assertFalse(any(x.material_code.startswith("ALUM") for x in without.unit_bom))
        for code in ("ALUM10238", "ALUM15338"):
            configured = cfg(**base, structural_reinforcement=StructuralReinforcement(code))
            result = calculate_maxim_ar(configured)
            structural = next(x for x in result.unit_bom if x.role == "STRUCTURAL_REINFORCEMENT")
            self.assertEqual((structural.material_code, structural.length_mm, structural.quantity_per_unit), (code, 1000, 1))
            plan = build_order_purchase_plan([(configured, result)])
            self.assertIn(code, {line.material_code for line in plan.lines})


if __name__ == "__main__":
    unittest.main()
