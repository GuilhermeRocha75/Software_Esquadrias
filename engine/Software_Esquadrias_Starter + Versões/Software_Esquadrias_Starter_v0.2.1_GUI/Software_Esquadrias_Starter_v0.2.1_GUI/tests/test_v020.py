import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import LeafSystem, SlidingConfiguration, calculate_sliding

class SlidingEngineV020Tests(unittest.TestCase):
    def test_prime_door_2000_full_baseline(self):
        cfg = SlidingConfiguration(
            width_mm=2000, height_mm=2000, quantity=1, leaf_count=2,
            leaf_system=LeafSystem.PRIME_DOOR_42x88,
            glass_description="04mm FLOAT INCOLOR",
            closure_mode="MAÇANETA COM CREMONA + FECHO OCULTO",
            cremona_base="CREMONA 1 PONTO",
            roller_description="ROLDANA 30KG",
            internal_finish="GUARNIÇÃO DE 70MM",
            external_finish="BARRA CHATA DE 30MM",
        )
        r = calculate_sliding(cfg)
        self.assertAlmostEqual(r.geometry["leaf_width_final_mm"], 1000.0, places=6)
        self.assertAlmostEqual(r.geometry["leaf_height_final_mm"], 1912.0, places=6)
        self.assertAlmostEqual(r.geometry["baguette_width_mm"], 856.0, places=6)
        self.assertAlmostEqual(r.geometry["glass_width_mm"], 848.0, places=6)
        # Valor reconstruído a partir das fórmulas/catálogos do Excel para esse recorte.
        self.assertAlmostEqual(r.unit_cost, 1645.63348, places=5)
        self.assertIn("VIDROS", r.cost_breakdown)
        self.assertIn("REFORÇOS", r.cost_breakdown)
        self.assertIn("FERRAGENS", r.cost_breakdown)
        self.assertIn("VEDAÇÕES", r.cost_breakdown)
        self.assertIn("BAGUETES", r.cost_breakdown)

    def test_screen_adds_screen_components(self):
        cfg = SlidingConfiguration(
            width_mm=1500, height_mm=1200, quantity=1, leaf_count=2,
            leaf_system=LeafSystem.PRIME_WINDOW_42x66,
            screen_enabled=True,
        )
        r = calculate_sliding(cfg)
        roles = {x.role for x in r.unit_bom}
        self.assertIn("SCREEN_MESH", roles)
        self.assertIn("SCREEN_RUBBER", roles)
        self.assertIn("SCREEN_LEAF_HORIZONTAL", roles)

    def test_quantity_multiplies_order_bom(self):
        cfg = SlidingConfiguration(
            width_mm=1500, height_mm=1200, quantity=3, leaf_count=2,
            leaf_system=LeafSystem.PRIME_WINDOW_42x66,
        )
        r = calculate_sliding(cfg)
        first = r.unit_bom[0]
        self.assertEqual(first.quantity_order, first.quantity_per_unit * 3)

    def test_shutter_warns_partial(self):
        cfg = SlidingConfiguration(
            width_mm=1500, height_mm=1600, quantity=1, leaf_count=2,
            leaf_system=LeafSystem.PRIME_WINDOW_42x66,
            shutter_enabled=True,
        )
        r = calculate_sliding(cfg)
        self.assertEqual(r.geometry["frame_height_final_mm"], 1400.0)
        self.assertTrue(any(w.code == "V0.2-SHUTTER-PARTIAL" for w in r.warnings))

if __name__ == "__main__":
    unittest.main()
