import json
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parents[3]
sys.path.insert(0, str(REPOSITORY / "tools"))

from gr_formula_oracle import (  # noqa: E402
    CellData,
    GrFormulaOracle,
    RangeValue,
    TECHNICAL_COLUMNS,
)
from compare_gr_formula_engine import CANONICAL_CASES  # noqa: E402


def small_oracle():
    oracle = object.__new__(GrFormulaOracle)
    oracle.names = {"LISTAP": RangeValue("CAT", 1, 1, 2, 10)}
    oracle.sheets = {
        "CAT": {
            "A1": CellData("X"),
            "B1": CellData(2.5),
        },
        "GR": {
            "A1": CellData(10),
            "A2": CellData(7),
            "B1": CellData(
                None,
                'IF(AND(A1>5,A1<20),VLOOKUP("X",LISTAP,2,FALSE),0)',
                "B1",
            ),
            "B2": CellData(None, "A1+1", "B1"),
            "C1": CellData(None, "SUM(A1:B1)", "C1"),
            "D1": CellData(None, 'LEFT("06mm",2)&"mm"', "D1"),
            "E1": CellData(None, "IF(TRUE,5,1/0)", "E1"),
        },
    }
    oracle._ast_cache = {}
    oracle._value_cache = {}
    oracle._active = set()
    return oracle


class GrFormulaOracleTests(unittest.TestCase):
    def test_supported_excel_subset_is_evaluated_independently(self):
        oracle = small_oracle()
        self.assertEqual(oracle.value("GR", "B1"), 2.5)
        self.assertEqual(oracle.value("GR", "C1"), 12.5)
        self.assertEqual(oracle.value("GR", "D1"), "06mm")
        self.assertEqual(oracle.value("GR", "E1"), 5)

    def test_shared_formula_moves_only_relative_references(self):
        oracle = small_oracle()
        self.assertEqual(oracle.value("GR", "B2"), 8)

    def test_canonical_deltas_are_explicit_and_justified(self):
        self.assertEqual(set(CANONICAL_CASES), {270, 11480, 14891, 15295, 16527, 18132, 18545})
        for row, case in CANONICAL_CASES.items():
            with self.subTest(orcs_row=row):
                self.assertNotEqual(case["formula_total"], case["engine_total"])
                self.assertTrue(case["corrections"])

    def test_full_formula_audit_is_frozen_and_complete(self):
        audit = json.loads(
            (ROOT / "test_cases/gr_formula_audit_v0_25.json").read_text(encoding="utf-8")
        )
        self.assertEqual(audit["rows_evaluated"], 1684)
        self.assertEqual(audit["numeric_total_rows"], 1659)
        self.assertEqual(audit["formula_error_rows"], 25)
        self.assertEqual(audit["errors"]["#N/A"]["count"], 24)
        self.assertEqual(audit["errors"]["#VALUE!"]["orcs_rows"], [15816])
        self.assertEqual(audit["canonical_comparison"]["failed"], 0)

    def test_private_orcs_columns_are_not_loaded(self):
        self.assertNotIn("A", TECHNICAL_COLUMNS)
        self.assertNotIn("B", TECHNICAL_COLUMNS)
        self.assertNotIn("C", TECHNICAL_COLUMNS)
        self.assertNotIn("J", TECHNICAL_COLUMNS)
        self.assertIn("D", TECHNICAL_COLUMNS)
        self.assertIn("AK", TECHNICAL_COLUMNS)


if __name__ == "__main__":
    unittest.main()
