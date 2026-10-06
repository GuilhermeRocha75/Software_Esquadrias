import itertools
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import (
    GR_COVERAGE_AUDIT,
    GR_ENGINE_VERSION,
    GrConfiguration,
    ShutterConfiguration,
    ShutterMode,
    build_order_purchase_plan,
    calculate_gr,
)
from esquadrias_engine import gr_v06 as v06
from esquadrias_engine import gr_v24 as v24
from esquadrias_engine.gr_v25 import (
    GR_CLOSURE_KEY_CREMONA,
    GR_HINGE_PERNIO,
)


INTERNAL = v06.GR_LEAF_SYSTEM_INTERNAL
EXTERNAL = v06.GR_LEAF_SYSTEM_EXTERNAL
WINDOW = v06.GR_LEAF_SYSTEM_WINDOW_EXTERNAL
MONO = v06.GR_CLOSURE_MONOPOINT
MULTI = v06.GR_CLOSURE_MULTIPOINT
CREMONA = v06.GR_CLOSURE_WINDOW_CREMONA


def door(**overrides):
    values = dict(
        width_mm=1000,
        height_mm=2100,
        leaf_system=INTERNAL,
        application="PORTA",
        panel_mode=v06.GR_PANEL_MODE,
        closure_mode=MONO,
    )
    values.update(overrides)
    return GrConfiguration(**values)


def window(**overrides):
    values = dict(
        width_mm=900,
        height_mm=1400,
        leaf_system=WINDOW,
        application="JANELA",
        panel_mode=v06.GR_GLASS_MODE,
        glass_description="06mm TEMPERADO INCOLOR",
        closure_mode=CREMONA,
        cremona_description="CREMONA 2 PONTOS COMP. 800mm E:15mm",
    )
    values.update(overrides)
    return GrConfiguration(**values)


class GrPhase25FinalTests(unittest.TestCase):
    def test_gate_and_version_close_final_phase(self):
        self.assertEqual(GR_ENGINE_VERSION, "GR_ENGINE_0.25.0")
        self.assertEqual(GR_COVERAGE_AUDIT["pending_real"], {})
        self.assertTrue(GR_COVERAGE_AUDIT["gate"]["historical_coverage_closed"])
        self.assertTrue(GR_COVERAGE_AUDIT["gate"]["purchase_plan_supported"])
        self.assertTrue(GR_COVERAGE_AUDIT["gate"]["main_ready"])

    def test_v24_standard_result_is_numerically_preserved(self):
        cfg = door()
        previous = v24.calculate_gr(v24.GrConfiguration(
            width_mm=cfg.width_mm,
            height_mm=cfg.height_mm,
            leaf_system=cfg.leaf_system,
            application=cfg.application,
            panel_mode=cfg.panel_mode,
            closure_mode=cfg.closure_mode,
        ))
        current = calculate_gr(cfg)
        self.assertEqual(current.unit_cost, previous.unit_cost)
        self.assertEqual(current.geometry, previous.geometry)

    def test_pernio_uses_dob5_three_per_leaf_and_excel_screws(self):
        result = calculate_gr(door(hinge_description=GR_HINGE_PERNIO))
        parts = {item.role: item for item in result.unit_bom}
        self.assertEqual(parts["HINGE_PERNIO"].material_code, "DOB5")
        self.assertEqual(parts["HINGE_PERNIO"].quantity_per_unit, 3)
        self.assertEqual(parts["HARDWARE_SCREWS"].quantity_per_unit, 28)

    def test_cremona_is_selected_per_quote_for_door(self):
        result = calculate_gr(door(
            closure_mode=CREMONA,
            cremona_description="CREMONA 2 PONTOS COMP. 1000mm E:15mm",
        ))
        parts = {item.role: item for item in result.unit_bom}
        self.assertEqual(parts["CREMONA"].material_code, "CRE13")
        self.assertEqual(parts["STANDARD_COUNTER_LOCK"].quantity_per_unit, 2)

    def test_keyed_handle_plus_cremona_uses_xlsm_else_branch(self):
        result = calculate_gr(door(
            closure_mode=GR_CLOSURE_KEY_CREMONA,
            cremona_description="CREMONA 2 PONTOS COMP. 1200mm E:7,5mm",
        ))
        parts = {item.role: item for item in result.unit_bom}
        self.assertEqual(parts["KEYED_HANDLE"].material_code, "MAC5")
        self.assertEqual(parts["CREMONA"].material_code, "CRE6")
        self.assertNotIn("CYLINDER_45X45", parts)

    def test_window_lock_has_length_and_no_key_or_cylinder(self):
        with self.assertRaisesRegex(ValueError, "exige window_lock_length_mm"):
            calculate_gr(window(closure_mode=MULTI, cremona_description=None))
        result = calculate_gr(window(
            closure_mode=MULTI,
            cremona_description=None,
            window_lock_length_mm=1200,
        ))
        parts = {item.role: item for item in result.unit_bom}
        self.assertIn("COMP. 1200MM", parts["WINDOW_MULTIPOINT_LOCK"].description)
        self.assertNotIn("CYLINDER_45X45", parts)
        self.assertIn("GR-WINDOW-LOCK-NO-CYLINDER", {warning.code for warning in result.warnings})

    def test_window_rejects_keyed_cremona(self):
        with self.assertRaisesRegex(ValueError, "não recebe maçaneta com chave"):
            calculate_gr(window(
                closure_mode=GR_CLOSURE_KEY_CREMONA,
                cremona_description="CREMONA 2 PONTOS COMP. 800mm E:15mm",
            ))

    def test_two_leaf_window_is_generalized_without_flag(self):
        result = calculate_gr(window(leaf_count=2, width_mm=1600))
        self.assertEqual(result.geometry["leaf_width_final_mm"], 758)
        self.assertEqual(result.geometry["glass_panel_count"], 2)
        self.assertEqual(len(result.glass_panels), 1)
        self.assertEqual(result.glass_panels[0].quantity, 2)

    def test_remaining_flag_matrix_uses_one_glass_per_opening(self):
        result = calculate_gr(door(
            width_mm=1800,
            height_mm=2600,
            leaf_count=2,
            leaf_system=EXTERNAL,
            panel_mode=v06.GR_GLASS_MODE,
            glass_description="06mm TEMPERADO INCOLOR",
            top_flag_height_mm=500,
            top_flag_vertical_transoms=1,
        ))
        self.assertEqual(result.geometry["top_flag_opening_count"], 2)
        self.assertEqual(result.fixed_panels[0].vertical_transoms, 1)
        self.assertEqual(len([p for p in result.glass_panels if p.source == "TOP_FLAG"]), 2)

    def test_uncatalogued_glass_requires_explicit_price_contract(self):
        with self.assertRaisesRegex(ValueError, "não consta na LISTAVIDROS"):
            calculate_gr(door(
                panel_mode=v06.GR_GLASS_MODE,
                glass_description="08mm JATEADO",
            ))
        result = calculate_gr(door(
            panel_mode=v06.GR_GLASS_MODE,
            glass_description="08mm JATEADO",
            custom_glass_code="8JAT",
            custom_glass_unit_price=500,
            custom_glass_thickness_mm=8,
        ))
        glass = next(item for item in result.unit_bom if item.category == "VIDROS")
        self.assertEqual(glass.material_code, "8JAT")
        self.assertEqual(glass.unit_price, 500)
        self.assertIn("GR-CUSTOM-GLASS-PRICED", {warning.code for warning in result.warnings})

    def test_historical_glass_alias_uses_catalog_without_inventing_price(self):
        result = calculate_gr(door(
            panel_mode=v06.GR_GLASS_MODE,
            glass_description="06mm LAMINADO LEITOSO",
        ))
        glass = next(item for item in result.unit_bom if item.category == "VIDROS")
        self.assertEqual(glass.material_code, "6LL")
        self.assertEqual(glass.unit_price, 332)

    def test_purchase_plan_includes_gr_profile_bars(self):
        cfg = door(quantity=2)
        result = calculate_gr(cfg)
        plan = build_order_purchase_plan([(cfg, result)], kerf_mm=3)
        codes = {line.material_code for line in plan.lines}
        self.assertIn("DE6058", codes)
        self.assertIn("DE60104", codes)
        self.assertGreater(plan.procurement_total_estimate, 0)

    def test_costs_are_exact_bom_sums(self):
        cases = [
            door(hinge_description=GR_HINGE_PERNIO),
            window(closure_mode=MULTI, cremona_description=None, window_lock_length_mm=1200),
            window(leaf_count=2, width_mm=1600),
        ]
        for cfg in cases:
            with self.subTest(cfg=cfg):
                result = calculate_gr(cfg)
                self.assertAlmostEqual(
                    result.unit_cost,
                    sum(item.cost_per_unit_product for item in result.unit_bom),
                    places=6,
                )

    def test_final_valid_matrix_has_no_hidden_phase_scope(self):
        systems = (INTERNAL, EXTERNAL, WINDOW)
        closures = (MONO, MULTI, CREMONA, GR_CLOSURE_KEY_CREMONA)
        hinges = ("DOBRADIÇA 90MM", "DOBRADIÇA SISTEMA OB", GR_HINGE_PERNIO)
        scenarios = ("PLAIN", "FLAGS", "SCREEN_FLAGS", "SHUTTER_FLAGS")
        for system, leaves, closure, hinge, scenario in itertools.product(
            systems, (1, 2), closures, hinges, scenarios
        ):
            physical_window = system == WINDOW
            if physical_window and closure == GR_CLOSURE_KEY_CREMONA:
                continue
            cremona = None
            if closure in (CREMONA, GR_CLOSURE_KEY_CREMONA):
                cremona = (
                    "CREMONA OSCILO/GIRO COMP. 1100mm E:15mm"
                    if hinge == "DOBRADIÇA SISTEMA OB"
                    else "CREMONA 2 PONTOS COMP. 1000mm E:15mm"
                )
            cfg = GrConfiguration(
                width_mm=1800,
                height_mm=2800,
                leaf_count=leaves,
                leaf_system=system,
                application="JANELA" if physical_window else "PORTA",
                panel_mode=v06.GR_GLASS_MODE,
                glass_description="06mm TEMPERADO INCOLOR",
                closure_mode=closure,
                cremona_description=cremona,
                hinge_description=hinge,
                window_lock_length_mm=(
                    1200 if physical_window and closure in (MONO, MULTI) else None
                ),
                top_flag_height_mm=400 if scenario != "PLAIN" else 0,
                top_flag_vertical_transoms=1 if scenario != "PLAIN" else 0,
                screen_enabled=scenario == "SCREEN_FLAGS",
                shutter=(
                    ShutterConfiguration(mode=ShutterMode.MANUAL_SINGLE)
                    if scenario == "SHUTTER_FLAGS"
                    else None
                ),
            )
            with self.subTest(
                system=system,
                leaves=leaves,
                closure=closure,
                hinge=hinge,
                scenario=scenario,
            ):
                result = calculate_gr(cfg)
                self.assertGreater(result.unit_cost, 0)
                self.assertAlmostEqual(
                    result.unit_cost,
                    sum(item.cost_per_unit_product for item in result.unit_bom),
                    places=6,
                )

    def test_incomplete_special_closure_and_unseen_horizontal_flag_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "item manual"):
            calculate_gr(door(closure_mode="FECHADURA IMAB"))
        with self.assertRaisesRegex(ValueError, "divisão horizontal"):
            calculate_gr(door(
                panel_mode=v06.GR_GLASS_MODE,
                glass_description="06mm TEMPERADO INCOLOR",
                top_flag_height_mm=500,
                top_flag_horizontal_transoms=1,
            ))

    def test_double_independent_shutter_requires_two_leaves(self):
        shutter = ShutterConfiguration(mode=ShutterMode.MANUAL_DOUBLE_INDEPENDENT_SHAFTS)
        with self.assertRaisesRegex(ValueError, "exige GR de 2 folhas"):
            calculate_gr(door(
                panel_mode=v06.GR_GLASS_MODE,
                glass_description="06mm TEMPERADO INCOLOR",
                shutter=shutter,
            ))


if __name__ == "__main__":
    unittest.main()
