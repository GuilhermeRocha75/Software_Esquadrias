import json
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parents[3]
sys.path.insert(0, str(REPOSITORY / "tools"))

import audit_gr_phase25 as audit  # noqa: E402


SNAPSHOT = ROOT / "test_cases" / "gr_hardware_audit_v0_25.json"


class GrPhase25AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(SNAPSHOT.read_text(encoding="utf-8"))

    def test_official_sha_is_frozen(self):
        self.assertEqual(
            audit.OFFICIAL_SHA,
            "96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160",
        )
        self.assertEqual(self.report["official_xlsm_sha256"], audit.OFFICIAL_SHA)

    def test_reproduces_gr_total_and_phase23_pending_counts(self):
        self.assertEqual(self.report["orcs_gr_rows"], 1684)
        reproduced = self.report["phase23_reproduction"]
        self.assertEqual(reproduced["closure_application_compatibility"]["count"], 66)
        self.assertEqual(reproduced["special_closures"]["count"], 18)
        self.assertEqual(reproduced["hinge_pernio_or_invalid"]["count"], 5)

    def test_application_independence_does_not_hide_physical_pending_cases(self):
        effect = self.report["phase24_effect_on_the_66"]
        self.assertEqual(effect["resolved_automatically_count"], 0)
        self.assertEqual(sum(effect["remaining_classifications"].values()), 66)

    def test_classifications_are_complete_unique_and_known(self):
        summary = self.report["classification_summary"]
        self.assertEqual(set(summary), set(audit.CLASSIFICATIONS))
        rows = [line for item in summary.values() for line in item["orcs_rows"]]
        self.assertEqual(sum(item["count"] for item in summary.values()), 1684)
        self.assertEqual(self.report["classification_total"], 1684)
        self.assertEqual(len(rows), len(set(rows)))
        self.assertEqual(len(rows), 1684)

    def test_combination_groups_have_no_loss_or_duplication(self):
        combinations = self.report["combinations"]
        rows = [line for item in combinations for line in item["orcs_rows"]]
        self.assertEqual(sum(item["count"] for item in combinations), 1684)
        self.assertEqual(len(rows), len(set(rows)))
        self.assertEqual(len(rows), 1684)
        self.assertTrue({item["panel_mode"] for item in combinations})
        self.assertTrue({item["flag_mode"] for item in combinations})

    def test_formula_audit_freezes_par1_and_catalog_sources(self):
        formulas = self.report["formula_audit"]
        self.assertEqual(
            formulas["par1_rule"]["formula"],
            "(G105*8)+(G111+G112+G114)*2",
        )
        self.assertEqual(
            formulas["catalog_references"]["LISTAFERRA!A61:C61"]["material_code"],
            "DOB6",
        )
        self.assertEqual(len(formulas["lines_105_119"]), 15)

    def test_report_schema_has_no_private_fields(self):
        forbidden = {
            "client", "cliente", "customer", "address", "endereco", "endereço",
            "phone", "telefone", "contact", "contato", "location", "local",
            "commercial", "comercial", "name", "nome",
        }

        def walk(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    self.assertNotIn(key.casefold(), forbidden)
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(self.report)


if __name__ == "__main__":
    unittest.main()
