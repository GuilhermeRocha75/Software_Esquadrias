import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine.gr_v24 import (  # noqa: E402
    GR_COVERAGE_AUDIT,
    GrConfiguration,
    calculate_gr,
)


INTERNAL = "FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN"
WINDOW = "FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN"
MONO = "MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE"
WINDOW_CREMONA = "MAÇANETA COM CREMONA SEM CHAVE"
CREMONA_800 = "CREMONA 2 PONTOS COMP. 800mm E:15mm"


def door_case(application: str):
    return GrConfiguration(
        width_mm=1000,
        height_mm=2100,
        leaf_system=INTERNAL,
        application=application,
        closure_mode=MONO,
    )


def window_case(application: str):
    return GrConfiguration(
        width_mm=1000,
        height_mm=1200,
        leaf_system=WINDOW,
        application=application,
        closure_mode=WINDOW_CREMONA,
        cremona_description=CREMONA_800,
    )


class GrPhase24Tests(unittest.TestCase):
    def assert_physical_result_equal(self, expected, actual):
        self.assertEqual(actual.geometry, expected.geometry)
        self.assertEqual(actual.unit_bom, expected.unit_bom)
        self.assertEqual(actual.cost_breakdown, expected.cost_breakdown)
        self.assertEqual(actual.unit_cost, expected.unit_cost)
        self.assertEqual(actual.glass_panels, expected.glass_panels)
        self.assertEqual(actual.fixed_panels, expected.fixed_panels)
        self.assertEqual(actual.transoms, expected.transoms)

    def test_door_leaf_accepts_window_application_without_physical_change(self):
        canonical = calculate_gr(door_case("PORTA"))
        independent = calculate_gr(door_case("JANELA"))
        self.assert_physical_result_equal(canonical, independent)
        self.assertTrue(independent.model_description.startswith("JANELA "))
        self.assertIn(
            "GR-APPLICATION-INDEPENDENT",
            {warning.code for warning in independent.warnings},
        )

    def test_window_leaf_accepts_door_application_without_physical_change(self):
        canonical = calculate_gr(window_case("JANELA"))
        independent = calculate_gr(window_case("PORTA"))
        self.assert_physical_result_equal(canonical, independent)
        self.assertTrue(independent.model_description.startswith("PORTA "))
        self.assertIn(
            "GR-APPLICATION-INDEPENDENT",
            {warning.code for warning in independent.warnings},
        )

    def test_application_does_not_change_frame_cut_or_cost(self):
        door = calculate_gr(door_case("PORTA"))
        classified_as_window = calculate_gr(door_case("JANELA"))
        frame_roles = {
            "FRAME_WIDTH",
            "FRAME_HEIGHT",
            "FRAME_REINFORCEMENT_WIDTH",
            "FRAME_REINFORCEMENT_HEIGHT",
        }
        self.assertEqual(
            [item for item in door.unit_bom if item.role in frame_roles],
            [item for item in classified_as_window.unit_bom if item.role in frame_roles],
        )

    def test_invalid_application_remains_explicitly_rejected(self):
        with self.assertRaisesRegex(ValueError, "aplicação fora do escopo"):
            calculate_gr(door_case("FACHADA"))

    def test_phase24_audit_closes_only_application_independence(self):
        self.assertEqual(GR_COVERAGE_AUDIT["audit_version"], "GR_COVERAGE_AUDIT_0.24.0")
        self.assertNotIn(
            "application_leaf_system_independence",
            GR_COVERAGE_AUDIT["pending_real"],
        )
        resolved = GR_COVERAGE_AUDIT["resolved_or_prohibited"][
            "application_leaf_system_independence"
        ]
        self.assertEqual(resolved["status"], "RESOLVED_PHYSICAL")
        self.assertEqual(resolved["count"], 47)
        self.assertEqual(
            GR_COVERAGE_AUDIT["gate"]["status"],
            "FASE_24_INDEPENDENCIA_APLICACAO_RESOLVIDA_COM_PENDENCIAS",
        )
        self.assertFalse(GR_COVERAGE_AUDIT["gate"]["main_ready"])


if __name__ == "__main__":
    unittest.main()
