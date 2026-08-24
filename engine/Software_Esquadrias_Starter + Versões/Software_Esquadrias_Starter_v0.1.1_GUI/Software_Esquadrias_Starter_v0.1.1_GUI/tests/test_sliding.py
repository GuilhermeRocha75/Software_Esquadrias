import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from esquadrias_engine import LeafSystem, SlidingConfiguration, calculate_sliding

class SlidingEngineTests(unittest.TestCase):
    def test_prime_window_two_leaves_geometry(self):
        cfg = SlidingConfiguration(1500, 1200, 1, 2, LeafSystem.PRIME_WINDOW_42x66)
        r = calculate_sliding(cfg)
        # D10 = (1500 - 2*52 + 2*8 + 66) / 2 = 739
        self.assertAlmostEqual(r.geometry["leaf_width_final_mm"], 739.0, places=6)
        # D11 = 1200 - (2*52 - 2*8) = 1112
        self.assertAlmostEqual(r.geometry["leaf_height_final_mm"], 1112.0, places=6)
        self.assertEqual(r.calculation_version, "CR_ENGINE_0.1.0")
        self.assertFalse(any(w.code.startswith("DT-CR-004") for w in r.warnings))

    def test_prime_door_four_leaves_central_closure(self):
        cfg = SlidingConfiguration(2400, 2100, 2, 4, LeafSystem.PRIME_DOOR_42x88)
        r = calculate_sliding(cfg)
        roles = [x.role for x in r.unit_bom]
        self.assertIn("CENTRAL_CLOSURE", roles)
        central = next(x for x in r.unit_bom if x.role == "CENTRAL_CLOSURE")
        self.assertEqual(central.quantity_order, 2.0)

    def test_design_six_leaves_surfaces_legacy_warning(self):
        cfg = SlidingConfiguration(3600, 2200, 1, 6, LeafSystem.DESIGN_DOOR_60x111)
        r = calculate_sliding(cfg)
        codes = {w.code for w in r.warnings}
        self.assertIn("DT-CR-003", codes)
        self.assertIn("DT-CR-004", codes)
        self.assertIn("LEAF_COVER", [x.role for x in r.unit_bom])

    def test_order_bom_quantity_multiplies_commercial_quantity(self):
        cfg = SlidingConfiguration(1500, 1200, 3, 2, LeafSystem.PRIME_WINDOW_42x66)
        r = calculate_sliding(cfg)
        leaf_h = next(x for x in r.unit_bom if x.role == "LEAF_HORIZONTAL")
        self.assertEqual(leaf_h.quantity_per_unit, 4.0)
        self.assertEqual(leaf_h.quantity_order, 12.0)

    def test_invalid_leaf_count(self):
        with self.assertRaises(ValueError):
            calculate_sliding(SlidingConfiguration(1000, 1000, 1, 5, LeafSystem.PRIME_WINDOW_42x66))

if __name__ == "__main__":
    unittest.main()
