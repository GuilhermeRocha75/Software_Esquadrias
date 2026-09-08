import math
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import (  # noqa: E402
    ApplicationType,
    FixedPanelConfiguration,
    LeafGrid,
    LeafSystem,
    ShutterConfiguration,
    ShutterMode,
    SlidingConfiguration,
    StructuralReinforcement,
    SHUTTER_MODES,
    build_order_purchase_plan,
    calculate_sliding,
)


SYSTEMS = tuple(LeafSystem)
LEAF_COUNTS = (2, 3, 4, 6)
ACTIVE_SHUTTER_MODES = tuple(mode for mode in ShutterMode if mode != ShutterMode.NONE)
SHUTTER_BAR_CODES = {
    "321040", "327201", "327204", "327019", "326015_F", "311712", "375021",
}


def config(**overrides):
    values = {
        "width_mm": 3000,
        "height_mm": 3200,
        "quantity": 1,
        "leaf_count": 2,
        "leaf_system": LeafSystem.PRIME_WINDOW_42x66,
        "application": ApplicationType.WINDOW,
        "glass_description": "04mm FLOAT INCOLOR",
    }
    values.update(overrides)
    return SlidingConfiguration(**values)


def components_by_role(result):
    return {component.role: component for component in result.unit_bom}


class CRPhase2ShutterExcelRegressionTests(unittest.TestCase):
    def test_l2_m2_n2_inventory_is_exposed_without_invented_options(self):
        self.assertEqual(len(SHUTTER_MODES), 10)
        self.assertEqual(SHUTTER_MODES[0], "SEM PERSIANA")
        self.assertEqual(set(SHUTTER_MODES), {mode.value for mode in ShutterMode})
        self.assertEqual(
            ShutterConfiguration(ShutterMode.MANUAL_SINGLE).box_description,
            "CAIXA DE 200MM",
        )
        self.assertEqual(
            ShutterConfiguration(ShutterMode.MANUAL_SINGLE).slat_description,
            "TALA DE PVC 40MM",
        )

    def test_excel_cr_rows_54_to_60_match_independent_shaft_geometry(self):
        cfg = config(
            width_mm=2400,
            height_mm=2200,
            shutter=ShutterConfiguration(
                ShutterMode.MANUAL_DOUBLE_INDEPENDENT_SHAFTS
            ),
        )
        result = calculate_sliding(cfg)
        components = components_by_role(result)

        # CR!D54:D60; as duas correções físicas são quantidade inteira de
        # talas e dois eixos independentes.
        expected = {
            "SHUTTER_BOX": ("321040", 2385.0, 1.0),
            "SHUTTER_SIDE_GUIDE": ("327201", 2000.0, 2.0),
            "SHUTTER_CENTRAL_GUIDE": ("327204", 2000.0, 1.0),
            "SHUTTER_SLAT": ("326015_F", 1143.0, 110.0),
            "SHUTTER_TERMINAL": ("311712", 1143.0, 2.0),
            "SHUTTER_SHAFT": ("375021", 1160.0, 2.0),
            "SHUTTER_GUIDE_EXTENDER": ("327019", 2000.0, 2.0),
        }
        for role, (code, length, quantity) in expected.items():
            with self.subTest(role=role):
                component = components[role]
                self.assertEqual(component.material_code, code)
                self.assertAlmostEqual(component.length_mm, length)
                self.assertAlmostEqual(component.quantity_per_unit, quantity)
                self.assertTrue(component.source.startswith("CR!"))

        self.assertIn("SHUTTER_INDEPENDENT_SHAFT_DIVIDER", components)
        self.assertNotIn("SHUTTER_SHARED_SHAFT_DIVIDER", components)
        self.assertEqual(components["SHUTTER_END_CAP"].quantity_per_unit, 2)
        self.assertNotIn("SHUTTER_END_PLATE", components)
        self.assertIn(
            "LEGACY-SHUTTER-INDEPENDENT-SHAFT",
            {warning.code for warning in result.warnings},
        )

    def test_all_excel_shutter_modes_select_the_proven_accessories(self):
        for mode in ACTIVE_SHUTTER_MODES:
            with self.subTest(mode=mode.value):
                result = calculate_sliding(config(
                    shutter=ShutterConfiguration(mode),
                ))
                components = components_by_role(result)
                panel_count = 1 if "PAINEL ÚNICO" in mode.value else (
                    3 if "3 PAINÉIS" in mode.value else 2
                )
                self.assertEqual(
                    components["SHUTTER_FIRST_SLAT_COUPLING"].quantity_per_unit,
                    2 * panel_count,
                )
                self.assertEqual(
                    components["SHUTTER_OPENING_LIMITER"].quantity_per_unit,
                    2 * panel_count,
                )
                if "CONTROLE REMOTO" in mode.value:
                    self.assertEqual(components["SHUTTER_REMOTE_MOTOR"].material_code, "MOT1")
                    self.assertNotIn("SHUTTER_BUTTON_MOTOR", components)
                elif "BOTOEIRA" in mode.value:
                    self.assertEqual(components["SHUTTER_BUTTON_MOTOR"].material_code, "MOT2")
                    self.assertNotIn("SHUTTER_REMOTE_MOTOR", components)
                else:
                    self.assertIn("SHUTTER_RECESSED_WINDER", components)
                    self.assertNotIn("SHUTTER_REMOTE_MOTOR", components)
                    self.assertNotIn("SHUTTER_BUTTON_MOTOR", components)

    def test_system_leaf_and_shutter_on_off_matrix_reaches_bom_and_ffd(self):
        for system in SYSTEMS:
            for leaf_count in LEAF_COUNTS:
                for enabled in (False, True):
                    with self.subTest(system=system.value, leaves=leaf_count, enabled=enabled):
                        shutter = ShutterConfiguration(
                            ShutterMode.REMOTE_DOUBLE if enabled else ShutterMode.NONE
                        )
                        cfg = config(
                            width_mm=2800 + leaf_count * 100,
                            height_mm=2800 + leaf_count * 40,
                            leaf_count=leaf_count,
                            leaf_system=system,
                            shutter=shutter,
                        )
                        result = calculate_sliding(cfg)
                        shutter_components = [
                            component for component in result.unit_bom
                            if component.category == "PERSIANA"
                        ]
                        self.assertEqual(bool(shutter_components), enabled)
                        expected_height = cfg.height_mm - (200 if enabled else 0)
                        self.assertEqual(result.geometry["frame_height_final_mm"], expected_height)
                        if enabled:
                            plan = build_order_purchase_plan([(cfg, result)])
                            plan_codes = {line.material_code for line in plan.lines}
                            self.assertTrue(SHUTTER_BAR_CODES <= plan_codes)
                            for line in plan.lines:
                                for bar in line.bars:
                                    self.assertLessEqual(bar.used_mm, 5900.0 + 1e-7)

    def test_shutter_plus_two_fixed_panels_uses_excel_discount_sequence(self):
        cfg = config(
            height_mm=3400,
            bottom_fixed_panel=FixedPanelConfiguration(400),
            top_fixed_panel=FixedPanelConfiguration(450),
            shutter=ShutterConfiguration(ShutterMode.BUTTON_SINGLE),
        )
        result = calculate_sliding(cfg)
        self.assertEqual(result.geometry["frame_height_final_mm"], 2350)
        self.assertEqual(components_by_role(result)["SHUTTER_SIDE_GUIDE"].length_mm, 3200)

    def test_nonphysical_shutter_combinations_fail_explicitly(self):
        cases = [
            config(height_mm=200, shutter=ShutterConfiguration(ShutterMode.MANUAL_SINGLE)),
            config(
                height_mm=900,
                bottom_fixed_panel=FixedPanelConfiguration(400),
                top_fixed_panel=FixedPanelConfiguration(350),
                shutter=ShutterConfiguration(ShutterMode.BUTTON_SINGLE),
            ),
            config(width_mm=70, shutter=ShutterConfiguration(ShutterMode.REMOTE_TRIPLE)),
        ]
        for cfg in cases:
            with self.subTest(cfg=cfg):
                with self.assertRaises(ValueError):
                    calculate_sliding(cfg)

    def test_legacy_boolean_remains_geometry_compatible(self):
        cfg = config(shutter_enabled=True)
        result = calculate_sliding(cfg)
        self.assertEqual(result.geometry["frame_height_final_mm"], cfg.height_mm - 200)
        self.assertFalse(any(c.category == "PERSIANA" for c in result.unit_bom))
        self.assertIn("V0.2-SHUTTER-PARTIAL", {w.code for w in result.warnings})


class CRPhase2ScreenCertificationTests(unittest.TestCase):
    def test_three_leaf_screen_separates_frames_from_mesh_factor(self):
        cfg = config(leaf_count=3, screen_enabled=True)
        result = calculate_sliding(cfg)
        components = components_by_role(result)
        self.assertEqual(result.geometry["screen_panel_count"], 2)
        self.assertEqual(result.geometry["screen_frame_count"], 2)
        self.assertEqual(components["SCREEN_LEAF_HORIZONTAL"].quantity_per_unit, 4)
        self.assertEqual(components["SCREEN_LEAF_VERTICAL"].quantity_per_unit, 4)
        self.assertEqual(components["SCREEN_MESH"].quantity_per_unit, 1.5)
        self.assertAlmostEqual(
            result.geometry["screen_mesh_area_m2"],
            components["SCREEN_MESH"].area_m2 * 1.5,
            places=5,
        )
        self.assertIn(
            "LEGACY-SCREEN-3-LEAF-FRACTION",
            {warning.code for warning in result.warnings},
        )

    def test_final_screen_matrix_all_systems_leaves_and_combinations(self):
        variants = {
            "A_SIMPLE": {},
            "B_HORIZONTAL": {"leaf_grid": LeafGrid(horizontal_transoms=1)},
            "C_VERTICAL": {"leaf_grid": LeafGrid(vertical_transoms=1)},
            "D_BOTH": {"leaf_grid": LeafGrid(horizontal_transoms=1, vertical_transoms=1)},
            "E_BOTTOM": {"bottom_fixed_panel": FixedPanelConfiguration(400)},
            "F_TOP": {"top_fixed_panel": FixedPanelConfiguration(450)},
            "G_TWO_FLAGS": {
                "bottom_fixed_panel": FixedPanelConfiguration(400),
                "top_fixed_panel": FixedPanelConfiguration(450),
            },
            "H_FLAG_GRID": {
                "bottom_fixed_panel": FixedPanelConfiguration(500, 1, 1),
            },
            "I_SHUTTER": {
                "shutter": ShutterConfiguration(ShutterMode.REMOTE_DOUBLE),
            },
        }
        for system in SYSTEMS:
            for leaf_count in LEAF_COUNTS:
                for variant, extra in variants.items():
                    with self.subTest(system=system.value, leaves=leaf_count, variant=variant):
                        cfg = config(
                            width_mm=3200 + leaf_count * 120,
                            height_mm=3600,
                            leaf_count=leaf_count,
                            leaf_system=system,
                            screen_enabled=True,
                            **extra,
                        )
                        result = calculate_sliding(cfg)
                        self.assertEqual(
                            result.geometry["screen_frame_count"], math.ceil(leaf_count / 2)
                        )
                        self.assertGreater(result.geometry["screen_mesh_area_m2"], 0)
                        self.assertFalse(any(
                            component.quantity_per_unit <= 0
                            or (component.length_mm is not None and component.length_mm <= 0)
                            for component in result.unit_bom
                        ))
                        self.assertFalse(any(
                            panel.width_mm <= 0 or panel.height_mm <= 0
                            for panel in result.glass_panels
                        ))
                        plan = build_order_purchase_plan([(cfg, result)])
                        self.assertGreater(len(plan.lines), 0)

    def test_stress_design_screen_shutter_grid_flags_reinforcement_quantity_two(self):
        cfg = config(
            width_mm=4200,
            height_mm=3900,
            quantity=2,
            leaf_count=4,
            leaf_system=LeafSystem.DESIGN_DOOR_60x111,
            application=ApplicationType.DOOR,
            glass_description="08mm FLOAT INCOLOR",
            screen_enabled=True,
            shutter=ShutterConfiguration(ShutterMode.REMOTE_TRIPLE),
            leaf_grid=LeafGrid(horizontal_transoms=1, vertical_transoms=1),
            bottom_fixed_panel=FixedPanelConfiguration(450, 1, 1),
            top_fixed_panel=FixedPanelConfiguration(500, 1, 1),
            structural_reinforcement=StructuralReinforcement("ALUM10238"),
        )
        result = calculate_sliding(cfg)
        plan = build_order_purchase_plan([(cfg, result)], kerf_mm=3.0)
        self.assertEqual(result.calculation_version, "CR_ENGINE_0.5.0")
        self.assertEqual(result.geometry["frame_height_final_mm"], 2750)
        self.assertEqual(result.geometry["screen_frame_count"], 2)
        self.assertIn("PERSIANA", result.cost_breakdown)
        self.assertTrue(any(c.role == "STRUCTURAL_REINFORCEMENT" for c in result.unit_bom))
        self.assertTrue(any(c.material_code == "DE5013" for c in result.unit_bom))
        self.assertGreater(plan.bar_stock_purchase_cost, plan.bar_stock_consumption_cost)
        self.assertEqual(plan.kerf_mm, 3.0)
        self.assertTrue(all(piece.source_role for line in plan.lines for bar in line.bars for piece in bar.pieces))
        self.assertTrue(all(bar.used_mm <= 5900.0 + 1e-7 for line in plan.lines for bar in line.bars))


if __name__ == "__main__":
    unittest.main()
