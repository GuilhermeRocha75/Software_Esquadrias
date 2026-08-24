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

if __name__ == "__main__":
    unittest.main()
