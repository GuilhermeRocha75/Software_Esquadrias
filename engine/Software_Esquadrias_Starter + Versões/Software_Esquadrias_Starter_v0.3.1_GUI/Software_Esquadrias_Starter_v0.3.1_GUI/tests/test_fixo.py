import json
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parents[3] / "tools"))

from esquadrias_engine import FixoConfiguration, calculate_fixo, build_order_purchase_plan
from esquadrias_engine.fixo import _bead_code, FIXO_GLASS_OPTIONS
from fixo_formula_oracle import FixoFormulaOracle, FormulaError, FX_INPUT_COLUMNS
from compare_fixo_formula_engine import compare, audit


def load(name):
    return json.loads((ROOT / "test_cases" / name).read_text(encoding="utf-8"))


class FixoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = load("fixo_formula_snapshot_v0_1.json")
        cls.golden = load("fixo_golden_v0_1.json")
        cls.oracle = FixoFormulaOracle.from_snapshot(cls.snapshot)

    def test_frozen_excel_cases_compare_every_bom_line(self):
        for case in self.golden["cases"]:
            with self.subTest(orcs_row=case["orcs_row"]):
                cfg = FixoConfiguration(**case["configuration"])
                result = calculate_fixo(cfg)
                self.assertAlmostEqual(result.unit_cost, case["expected_total"], places=7)
                self.oracle.set_inputs(case["inputs"])
                self.assertEqual(self.oracle.bom(), case["expected_bom"])
                self.assertEqual(compare(self.oracle, cfg), [])

    def test_all_catalog_glasses_and_grid_topologies_against_formula_snapshot(self):
        for glass in FIXO_GLASS_OPTIONS:
            for vertical, horizontal in ((0, 0), (2, 0), (0, 3), (2, 3)):
                with self.subTest(glass=glass["description"], grid=(vertical, horizontal)):
                    cfg = FixoConfiguration(2000, 2200, 3, vertical, horizontal, glass["description"])
                    self.oracle.set_inputs({"D": 2000, "E": 2200, "F": 3, "K": glass["description"],
                                            "S": cfg.internal_finish, "T": cfg.external_finish,
                                            "AJ": vertical, "AK": horizontal})
                    self.assertEqual(compare(self.oracle, cfg), [])

    def test_baguete_thresholds_are_fx_thresholds(self):
        for value, expected in ((4, "BA3518"), (7, "BA3518"), (8, "BA3218"), (11, "BA3218"),
                                (12, "BA2516"), (18, "BA2516"), (19, "BA2018"), (21, "BA2018"),
                                (22, "BA1816"), (25, "BA1816"), (26, "BA1216"), (30, "BA1216"),
                                (31, "BA1016"), (33, "BA1016"), (34, "BA0716")):
            with self.subTest(thickness=value):
                self.assertEqual(_bead_code(value), expected)
        with self.assertRaises(ValueError):
            _bead_code(35)

    def test_horizontal_transoms_are_segmented_vertical_transoms_are_full_height(self):
        result = calculate_fixo(FixoConfiguration(2000, 2200, vertical_transoms=2, horizontal_transoms=3))
        by_source = {item.source: item for item in result.unit_bom}
        self.assertEqual(by_source["FX!10"].quantity_per_unit, 9)
        self.assertEqual(by_source["FX!11"].quantity_per_unit, 2)
        self.assertEqual(by_source["FX!11"].length_mm, 2120)
        self.assertEqual(by_source["FX!27"].quantity_per_unit, 12)
        self.assertEqual(by_source["FX!30"].quantity_per_unit, 24)
        self.assertEqual(len(result.leaf_openings), 12)

    def test_frame_reinforcement_keeps_fx_cut_allowance(self):
        result = calculate_fixo(FixoConfiguration(1200, 1000))
        by_source = {item.source: item for item in result.unit_bom}
        self.assertEqual(by_source["FX!20"].length_mm, 1089)
        self.assertEqual(by_source["FX!21"].length_mm, 889)
        self.assertEqual(by_source["FX!8"].length_mm, 1205)
        self.assertEqual(by_source["FX!9"].length_mm, 1005)
        self.assertNotIn("PAR2", [item.material_code for item in result.unit_bom])

    def test_quantity_changes_order_not_unit_cost(self):
        one = calculate_fixo(FixoConfiguration(1200, 1000))
        four = calculate_fixo(FixoConfiguration(1200, 1000, quantity=4))
        self.assertEqual(one.unit_cost, four.unit_cost)
        for a, b in zip(one.unit_bom, four.unit_bom):
            self.assertEqual(b.quantity_order, a.quantity_order * 4)

    def test_purchase_cost_is_separate_from_technical_cost_and_stock_is_configurable(self):
        cfg = FixoConfiguration(1200, 1000, quantity=2, vertical_transoms=1)
        result = calculate_fixo(cfg)
        plan = build_order_purchase_plan([(cfg, result)], stock_length_mm=6000, kerf_mm=3)
        self.assertAlmostEqual(plan.technical_total, result.unit_cost * 2, places=5)
        self.assertGreater(plan.procurement_total_estimate, plan.technical_total)
        self.assertTrue(all(line.stock_length_mm == 6000 for line in plan.lines))
        for line in plan.lines:
            for bar in line.bars:
                self.assertLessEqual(bar.used_mm, bar.stock_length_mm)

    def test_purchase_preserves_integral_oversize_and_reserves_real_stock(self):
        from esquadrias_engine.models import ManualSpliceAllocation
        for width in (5900, 7500, 12000):
            cfg = FixoConfiguration(width, 2500, quantity=2, vertical_transoms=3)
            result = calculate_fixo(cfg)
            original_bom = list(result.unit_bom)
            plan = build_order_purchase_plan([(cfg, result)], kerf_mm=3)
            self.assertAlmostEqual(plan.technical_total, result.unit_cost * 2, places=5)
            self.assertEqual(result.unit_bom, original_bom)
            self.assertTrue(any(w.code == "FX-MANUAL-SPLICE" for w in plan.warnings))
            for line in plan.lines:
                pieces = [piece for bar in line.bars for piece in bar.pieces]
                expected = [comp.length_mm for comp in result.unit_bom
                            if comp.material_code == line.material_code
                            for _ in range(int(comp.quantity_order))]
                self.assertEqual(sorted(p.length_mm for p in pieces), sorted(expected))
                count = 0
                for bar in line.bars:
                    if isinstance(bar, ManualSpliceAllocation):
                        self.assertEqual(len(bar.pieces), 1)
                        self.assertEqual(bar.stock_bars_required, math.ceil(bar.used_mm / 5900))
                        count += bar.stock_bars_required
                        self.assertGreaterEqual(bar.leftover_mm, 0)
                    else:
                        count += 1
                        self.assertLessEqual(bar.used_mm, 5900)
                self.assertEqual(line.bars_required, count)
                self.assertAlmostEqual(line.purchased_length_mm, count * 5900)
                self.assertGreaterEqual(line.purchased_length_mm, line.consumed_length_mm + line.kerf_loss_mm)
                self.assertAlmostEqual(line.purchase_cost, count * 5.9 * line.unit_price_per_m, places=5)
        cfg = FixoConfiguration(7500, 2500, vertical_transoms=3)
        plan = build_order_purchase_plan([(cfg, calculate_fixo(cfg))], stock_length_mm=8000)
        self.assertFalse(any(w.code == "FX-MANUAL-SPLICE" for w in plan.warnings))

    def test_invalid_engine_inputs_are_rejected(self):
        cases = [{"width_mm": value} for value in (0, -1, float("nan"), float("inf"), True)]
        cases += [{"height_mm": 100}, {"width_mm": 150, "vertical_transoms": 2},
                  {"quantity": True}, {"quantity": 1.5}, {"vertical_transoms": -1},
                  {"vertical_transoms": True}, {"horizontal_transoms": 0.5},
                  {"glass_description": "VIDRO DESCONHECIDO"}, {"glass_description": None},
                  {"internal_finish": "SEM ACABAMENTO"}]
        for changes in cases:
            with self.subTest(changes=changes):
                values = {"width_mm": 1200, "height_mm": 1000, **changes}
                with self.assertRaises(ValueError):
                    calculate_fixo(FixoConfiguration(**values))

    def test_missing_glass_produces_excel_error_and_unknown_glass_is_not_substituted(self):
        self.oracle.set_inputs({"D": 1200, "E": 1000, "F": 1, "K": None,
                                "S": "GUARNIÇÃO DE 70MM", "T": "BARRA CHATA DE 30MM", "AJ": 0, "AK": 0})
        total = self.oracle.value("FX", "I34")
        self.assertIsInstance(total, FormulaError)
        self.assertEqual(total.code, "#VALUE!")
        with self.assertRaises(ValueError):
            calculate_fixo(FixoConfiguration(1200, 1000, glass_description="08mm TEMPERADO INCOLOR "))

    def test_source_evidence_has_no_private_sheets_or_orcs_columns(self):
        self.assertEqual(set(self.snapshot["sheets"]), {"FX", "PFAB", "LISTAPERFIS", "LISTAVIDROS"})
        self.assertEqual(set(self.snapshot["sheets"]["PFAB"]), {"B12", "B14", "B15"})
        self.assertFalse(set(FX_INPUT_COLUMNS) & {"A", "B", "C", "J"})
        self.assertEqual(self.snapshot["source_sha256"], self.golden["source_sha256"])
        self.assertEqual(self.oracle.verify_cached_fx()["mismatches"], [])

    def test_historical_coverage_requires_review_of_all_source_exceptions(self):
        report = load("fixo_coverage_v0_1.json")
        self.assertEqual(report["rows_evaluated"], 1612)
        self.assertEqual(report["counts"], {"PARITY_OK": 1538, "SOURCE_FORMULA_ERROR": 73,
                                           "INVALID_SOURCE_GEOMETRY_OR_INPUT": 1})
        self.assertEqual(sum(report["counts"].values()), report["rows_evaluated"])
        self.assertFalse(report["gate"]["main_ready"])
        invalid = [case for case in report["cases"] if case["status"] == "INVALID_SOURCE_GEOMETRY_OR_INPUT"]
        self.assertEqual([case["orcs_row"] for case in invalid], [8152])
        self.assertLess(report["max_total_absolute_delta"], 1e-7)

    def test_audit_does_not_hide_engine_regressions_as_source_errors(self):
        oracle = FixoFormulaOracle.from_snapshot(self.snapshot)
        from fixo_formula_oracle import CellData
        inputs = self.golden["cases"][0]["inputs"]
        oracle.sheets["ORCS"] = {f"{column}14": CellData(value) for column, value in inputs.items()}
        oracle.sheets["ORCS"]["X14"] = CellData("FX")
        with patch("compare_fixo_formula_engine.calculate_fixo", side_effect=ValueError("regressão simulada")):
            report, _ = audit(oracle)
        self.assertEqual(report["counts"], {"UNEXPECTED_ENGINE_REJECTION": 1})

    def test_extreme_finite_dimensions_reject_overflow_instead_of_returning_infinity(self):
        for width, height in ((1e200, 1e200), (1e308, 1e308)):
            with self.subTest(dimensions=(width, height)), self.assertRaisesRegex(ValueError, "capacidade numérica"):
                calculate_fixo(FixoConfiguration(width, height))


if __name__ == "__main__":
    unittest.main()
