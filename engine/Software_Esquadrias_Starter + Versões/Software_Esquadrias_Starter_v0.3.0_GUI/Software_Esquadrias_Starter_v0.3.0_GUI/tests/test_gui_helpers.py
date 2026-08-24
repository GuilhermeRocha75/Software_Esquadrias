import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("tester_gui", ROOT / "tester_gui.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class GuiHelpers(unittest.TestCase):
    def test_decimal_comma(self):
        self.assertEqual(MODULE.parse_number("1500,5", "largura"), 1500.5)
    def test_money(self):
        self.assertEqual(MODULE.money(1234.5), "R$ 1.234,50")

if __name__ == "__main__":
    unittest.main()
