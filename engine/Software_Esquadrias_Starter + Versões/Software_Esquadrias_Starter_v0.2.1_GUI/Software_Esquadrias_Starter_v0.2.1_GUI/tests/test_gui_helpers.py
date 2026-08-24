import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("tester_gui", ROOT / "tester_gui.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class GuiHelperTests(unittest.TestCase):
    def test_parse_number_accepts_decimal_comma(self):
        self.assertEqual(MODULE.parse_number("1500,5", "largura"), 1500.5)
    def test_parse_number_integer(self):
        self.assertEqual(MODULE.parse_number("3", "quantidade", integer=True), 3)
    def test_money_ptbr(self):
        self.assertEqual(MODULE.money(1234.5), "R$ 1.234,50")

    def test_comparison_uses_order_total(self):
        total, diff, pct = MODULE.compare_order_total(100.0, 3, 290.0)
        self.assertEqual(total, 300.0)
        self.assertEqual(diff, 10.0)
        self.assertAlmostEqual(pct, 3.448275862, places=6)

if __name__ == "__main__":
    unittest.main()
