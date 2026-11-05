import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.compare_op_golden import build_report, compare_case

FIXTURES = Path(__file__).parent / "fixtures"
CASES = json.loads((FIXTURES / "op_golden_12_partial.json").read_text(encoding="utf-8"))["cases"]
INPUTS = {c["id"]: c for c in json.loads((FIXTURES / "op_reference_inputs.json").read_text(encoding="utf-8"))["cases"]}


class PartialGoldenTests(unittest.TestCase):
    def test_report_covers_every_case_field_and_supplemental_reference(self):
        report = build_report()
        self.assertEqual(len(report["cases"]), 12)
        self.assertEqual(report["case_counts"], {"igual": 10, "input insuficiente": 2})
        self.assertEqual(report["field_counts"], {"igual": 141, "divergente": 2})
        fixture_fields = [r for c in report["cases"] for r in c["fields"] if r["origin"] == "op_golden_12_partial.json"]
        self.assertEqual(len(fixture_fields), 129)
        self.assertTrue(all(r["status"] == "igual" for r in fixture_fields))

    def test_comparison_reports_both_values_and_does_not_mask_a_new_divergence(self):
        changed = copy.deepcopy(CASES[0])
        changed["assertions"]["frame_width"]["cut_length_mm"] = 1936
        report = compare_case(changed, INPUTS[changed["id"]])
        row = next(r for r in report["fields"] if r["field"] == "frame_width.cut_length_mm")
        self.assertEqual((row["pdf"], row["engine"], row["status"]), (1936, 1935, "divergente"))
        self.assertEqual(row["reason"], "UNEXPLAINED_ENGINE_PDF_DIFFERENCE")


def golden_test(case):
    def test(self):
        result = compare_case(case, INPUTS[case["id"]])
        original = [r for r in result["fields"] if r["origin"] == "op_golden_12_partial.json"]
        self.assertTrue(all(r["status"] == "igual" for r in original), original)
        self.assertEqual(result["source"], case["source"])
        if case["id"] in {"OP-GOLDEN-05", "OP-GOLDEN-12"}:
            self.assertEqual(result["status"], "input insuficiente")
            diff = next(r for r in result["fields"] if r["field"] == "slat.quantity_total")
            self.assertEqual(diff["status"], "divergente")
            self.assertEqual((diff["pdf"], diff["engine"]), (40.25, 41) if case["id"] == "OP-GOLDEN-05" else (59, 60))
            self.assertIn("CONDITIONAL", diff["reason"])
        else:
            self.assertEqual(result["status"], "igual")
    return test


for case in CASES:
    setattr(PartialGoldenTests, f"test_{case['id'].lower().replace('-', '_')}", golden_test(case))


if __name__ == "__main__":
    unittest.main()
