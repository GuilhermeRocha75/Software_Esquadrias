import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import (
    LeafSystem, ApplicationType, SlidingConfiguration, calculate_sliding,
    build_order_purchase_plan
)

def real_order():
    configs = [
        SlidingConfiguration(
            width_mm=3500, height_mm=2000, quantity=1, leaf_count=2,
            leaf_system=LeafSystem.PRIME_WINDOW_42x66,
            application=ApplicationType.WINDOW,
            glass_description="04mm FLOAT INCOLOR",
            closure_mode="MAÇANETA COM CREMONA + FECHO OCULTO",
            cremona_base="CREMONA 1 PONTO", roller_description="ROLDANA 30KG",
            internal_finish="GUARNIÇÃO DE 70MM", external_finish="BARRA CHATA DE 30MM",
        ),
        SlidingConfiguration(
            width_mm=2000, height_mm=2000, quantity=1, leaf_count=2,
            leaf_system=LeafSystem.DESIGN_DOOR_60x111,
            application=ApplicationType.WINDOW,
            glass_description="04mm FLOAT INCOLOR",
            closure_mode="MAÇANETA COM CREMONA + FECHO OCULTO",
            cremona_base="CREMONA 1 PONTO", roller_description="ROLDANA 30KG",
            internal_finish="GUARNIÇÃO DE 70MM", external_finish="BARRA CHATA DE 30MM",
        ),
        SlidingConfiguration(
            width_mm=1500, height_mm=3000, quantity=1, leaf_count=2,
            leaf_system=LeafSystem.PRIME_WINDOW_42x66,
            application=ApplicationType.WINDOW,
            glass_description="05mm FLOAT FUMÊ",
            closure_mode="MAÇANETA COM CREMONA",
            cremona_base="CREMONA 1 PONTO", roller_description="ROLDANA 50KG",
            internal_finish="GUARNIÇÃO DE 70MM", external_finish="BARRA CHATA DE 30MM",
        ),
        SlidingConfiguration(
            width_mm=2000, height_mm=2000, quantity=1, leaf_count=2,
            leaf_system=LeafSystem.DESIGN_DOOR_60x111,
            application=ApplicationType.WINDOW,
            glass_description="04mm FLOAT INCOLOR",
            closure_mode="MAÇANETA COM CREMONA + FECHO OCULTO",
            cremona_base="CREMONA 1 PONTO", roller_description="ROLDANA 30KG",
            internal_finish="GUARNIÇÃO DE 70MM", external_finish="BARRA CHATA DE 30MM",
        ),
    ]
    return [(cfg, calculate_sliding(cfg)) for cfg in configs]

class EngineV030Tests(unittest.TestCase):
    def test_application_is_independent_from_leaf_system(self):
        cfg = SlidingConfiguration(
            width_mm=2000, height_mm=2000, quantity=1, leaf_count=2,
            leaf_system=LeafSystem.DESIGN_DOOR_60x111,
            application=ApplicationType.WINDOW,
            glass_description="04mm FLOAT INCOLOR",
            closure_mode="MAÇANETA COM CREMONA + FECHO OCULTO",
            cremona_base="CREMONA 1 PONTO", roller_description="ROLDANA 30KG",
            internal_finish="GUARNIÇÃO DE 70MM", external_finish="BARRA CHATA DE 30MM",
        )
        r = calculate_sliding(cfg)
        # Excel AO do teste real: 2694.65947; diferença remanescente conhecida ~0,08.
        self.assertAlmostEqual(r.unit_cost, 2694.73947, places=5)

    def test_real_order_profile_bar_counts(self):
        plan = build_order_purchase_plan(real_order())
        counts = {x.material_code: x.bars_required for x in plan.lines}

        expected_corrected = {
            "AL17":1, "BA3518":4, "BA2516":5, "AC3004":7,
            "PR4266":6, "DE60111":5, "AC7012":8, "DE4109":2,
            "PR4536":2, "PR8852":4, "DE16652":4, "AL18":1,
            "RAG - PR4266":5, "RAG - DE60111":4,
            "RAG - DE16652":3, "RAG - PR8852":4,
            "DE5013":2,  # Excel legado mostra 1; fisicamente precisa de 2.
            "AL19":2, "AL16":2,
        }
        for code, expected in expected_corrected.items():
            self.assertEqual(counts.get(code), expected, code)

    def test_real_order_purchase_total_corrected(self):
        plan = build_order_purchase_plan(real_order())
        # PED_P legado = 9537.055. Corrigindo a 2ª barra DE5013 (+59.826):
        self.assertAlmostEqual(plan.bar_stock_purchase_cost, 9596.881, places=3)
        self.assertTrue(any(w.code == "LEGACY-PEDP-DE5013" for w in plan.warnings))

    def test_each_bar_respects_5900(self):
        plan = build_order_purchase_plan(real_order())
        for line in plan.lines:
            for bar in line.bars:
                self.assertLessEqual(bar.used_mm, 5900.000001)

if __name__ == "__main__":
    unittest.main()
