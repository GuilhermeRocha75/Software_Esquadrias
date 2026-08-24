from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class LayoutRegressionTests(unittest.TestCase):
    def test_no_empty_expand_frame_in_tree_attachment(self):
        text = (ROOT / "tester_gui.py").read_text(encoding="utf-8")
        self.assertNotIn(
            'frame = ttk.Frame(parent)\\n        frame.pack(fill="both", expand=True)',
            text
        )
        self.assertIn("def _attach_tree", text)

    def test_warning_sections_exist(self):
        text = (ROOT / "tester_gui.py").read_text(encoding="utf-8")
        self.assertIn("INFORMAÇÕES DE COMPATIBILIDADE", text)
        self.assertIn("DIVERGÊNCIAS / CORREÇÕES DO EXCEL LEGADO", text)

if __name__ == "__main__":
    unittest.main()
