import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine.gr_v23 import (  # noqa: E402
    GR_COVERAGE_AUDIT,
    GrConfiguration,
    calculate_gr,
)
from esquadrias_engine.gr_v22 import calculate_gr as calculate_gr_v22  # noqa: E402


def base_case():
    return GrConfiguration(width_mm=900, height_mm=2100, quantity=1)


class GrPhase23Tests(unittest.TestCase):
    def test_version_is_v023_without_formula_change(self):
        current = calculate_gr(base_case())
        previous = calculate_gr_v22(base_case())
        self.assertEqual(current.calculation_version, "GR_ENGINE_0.23.0")
        self.assertEqual(current.unit_bom, previous.unit_bom)
        self.assertEqual(current.geometry, previous.geometry)
        self.assertEqual(current.cost_breakdown, previous.cost_breakdown)
        self.assertEqual(current.unit_cost, previous.unit_cost)

    def test_coverage_gate_does_not_claim_historical_closure(self):
        gate = GR_COVERAGE_AUDIT["gate"]
        self.assertEqual(gate["status"], "FASE_23_AUDITADA_COM_PENDENCIAS_REAIS")
        self.assertFalse(gate["historical_coverage_closed"])
        self.assertFalse(gate["purchase_plan_supported"])
        self.assertFalse(gate["main_ready"])

    def test_orcs_inventory_and_absent_branches_are_frozen(self):
        self.assertEqual(GR_COVERAGE_AUDIT["source"]["orcs_gr_rows"], 1684)
        self.assertEqual(
            GR_COVERAGE_AUDIT["historically_absent"],
            {"separate_modules": 0, "structural_reinforcement": 0},
        )
        prohibited = GR_COVERAGE_AUDIT["resolved_or_prohibited"]["leaf_grid_inside_mobile_leaf"]
        self.assertEqual(prohibited["status"], "PROHIBITED_PHYSICAL")
        self.assertEqual(prohibited["reference_orcs_rows"], [9155])

    def test_pending_counts_match_phase23_snapshot(self):
        snapshot = json.loads((ROOT / "test_cases" / "gr_coverage_v0_23.json").read_text())
        expected = {
            name: detail["count"]
            for name, detail in snapshot["pending_real"].items()
        }
        self.assertEqual(GR_COVERAGE_AUDIT["pending_real"], expected)
        self.assertEqual(snapshot["source_data_review"]["rows"], [543, 914])


if __name__ == "__main__":
    unittest.main()
