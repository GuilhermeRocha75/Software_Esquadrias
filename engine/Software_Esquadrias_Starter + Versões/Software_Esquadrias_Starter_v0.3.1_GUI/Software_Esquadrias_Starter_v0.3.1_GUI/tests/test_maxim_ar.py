import json
import math
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import (  # noqa: E402
    MaximArConfiguration,
    MaximArLeafSystem,
    build_order_purchase_plan,
    calculate_maxim_ar,
)


def configuration(**overrides):
    values = {
        "width_mm": 800,
        "height_mm": 800,
        "quantity": 1,
        "leaf_system": MaximArLeafSystem.PRIME_WINDOW_42x63,
        "glass_description": "04mm MINI BOREAL",
        "closure_mode": "FECHO 1 PONTO",
        "internal_finish": "GUARNIÇÃO DE 70MM",
        "external_finish": "BARRA CHATA DE 30MM",
    }
    values.update(overrides)
    return MaximArConfiguration(**values)


class MaximArExcelRegressionTests(unittest.TestCase):
    def test_five_real_orcs_cases_match_recalculated_excel(self):
        cases = (
            # ORCS row, width, height, qty, system, Excel MX!I85
            (7, 680, 690, 2, MaximArLeafSystem.PRIME_WINDOW_42x63, 358.1772),
            (11, 550, 550, 2, MaximArLeafSystem.DESIGN_WINDOW_60x78, 378.12602),
            (24, 1150, 700, 2, MaximArLeafSystem.DESIGN_WINDOW_60x78, 645.06852),
            (16942, 800, 800, 1, MaximArLeafSystem.PRIME_WINDOW_42x63, 419.7804),
            (18712, 600, 600, 1, MaximArLeafSystem.DESIGN_WINDOW_60x78, 409.29252),
        )
        for row, width, height, quantity, system, expected in cases:
            with self.subTest(orcs_row=row):
                result = calculate_maxim_ar(configuration(
                    width_mm=width,
                    height_mm=height,
                    quantity=quantity,
                    leaf_system=system,
                ))
                self.assertAlmostEqual(result.unit_cost, expected, places=6)

    def test_prime_geometry_matches_mx_formulas(self):
        result = calculate_maxim_ar(configuration())
        self.assertEqual(result.geometry["leaf_width_final_mm"], 756)
        self.assertEqual(result.geometry["leaf_height_final_mm"], 756)
        self.assertEqual(result.geometry["baguette_width_mm"], 668)
        self.assertEqual(result.geometry["glass_width_mm"], 660)

    def test_design_geometry_matches_mx_formulas(self):
        result = calculate_maxim_ar(configuration(
            width_mm=600,
            height_mm=600,
            leaf_system=MaximArLeafSystem.DESIGN_WINDOW_60x78,
        ))
        self.assertEqual(result.geometry["leaf_width_final_mm"], 536)
        self.assertEqual(result.geometry["baguette_width_mm"], 416)
        self.assertEqual(result.geometry["glass_width_mm"], 408)

    def test_quantity_scales_order_bom_but_not_unit_cost(self):
        one = calculate_maxim_ar(configuration(quantity=1))
        three_cfg = configuration(quantity=3)
        three = calculate_maxim_ar(three_cfg)
        self.assertEqual(one.unit_cost, three.unit_cost)
        for component in three.unit_bom:
            self.assertEqual(
                component.quantity_order,
                component.quantity_per_unit * 3,
            )
        plan = build_order_purchase_plan([(three_cfg, three)])
        self.assertEqual(
            next(line for line in plan.lines if line.material_code == "PR4263").pieces_count,
            24,
        )

    def test_different_glass_selects_excel_bead_band(self):
        result = calculate_maxim_ar(configuration(
            width_mm=580,
            height_mm=590,
            glass_description="08mm LAMINADO MINI BOREAL",
        ))
        bead_codes = {
            item.material_code for item in result.unit_bom if item.category == "BAGUETES"
        }
        self.assertEqual(bead_codes, {"BA2018"})
        # ORCS!15766 recalculada na versão corrente do XLSM.
        self.assertAlmostEqual(result.unit_cost, 359.84084, places=6)

    def test_cremona_hardware_matches_recalculated_excel(self):
        result = calculate_maxim_ar(configuration(
            width_mm=1030,
            height_mm=1890,
            leaf_system=MaximArLeafSystem.DESIGN_WINDOW_60x78,
            closure_mode="MAÇANETA COM CREMONA",
            cremona_description="CREMONA MAXIM-AR 2 PONTOS COMP. 600mm",
        ))
        codes = {item.material_code for item in result.unit_bom}
        self.assertTrue({"MAC3", "CRE19", "CON1"}.issubset(codes))
        # Caso derivado de ORCS!3194, removendo a bandeira inferior para
        # isolar o baseline de módulo único desta fase.
        self.assertAlmostEqual(result.unit_cost, 1074.43182, places=6)

    def test_hardware_lookup_rejects_substring(self):
        with self.assertRaisesRegex(ValueError, "exige uma cremona"):
            calculate_maxim_ar(configuration(
                closure_mode="MAÇANETA COM CREMONA",
                cremona_description="600",
            ))

    def test_design_sealing_omission_is_explicit(self):
        result = calculate_maxim_ar(configuration(
            leaf_system=MaximArLeafSystem.DESIGN_WINDOW_60x78,
        ))
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 0)
        self.assertIn(
            "LEGACY-MX-DESIGN-SEALING-OMITTED",
            {warning.code for warning in result.warnings},
        )

    def test_prime_contains_all_required_groups(self):
        result = calculate_maxim_ar(configuration())
        self.assertEqual(
            {item.category for item in result.unit_bom},
            {
                "PERFIS PRINCIPAIS", "BAGUETES", "ACABAMENTOS", "REFORÇOS",
                "VIDROS", "VEDAÇÕES", "ACESSÓRIOS", "FERRAGENS",
            },
        )
        self.assertTrue(all(item.source for item in result.unit_bom))

    def test_cost_is_sum_of_bom_and_groups(self):
        result = calculate_maxim_ar(configuration())
        self.assertAlmostEqual(
            result.unit_cost,
            sum(item.cost_per_unit_product for item in result.unit_bom),
            places=6,
        )
        self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)

    def test_invalid_dimensions_fail_instead_of_clamping(self):
        with self.assertRaisesRegex(ValueError, "tecnicamente impossível"):
            calculate_maxim_ar(configuration(width_mm=140))
        with self.assertRaisesRegex(ValueError, "tecnicamente impossível"):
            calculate_maxim_ar(configuration(
                width_mm=192,
                leaf_system=MaximArLeafSystem.DESIGN_WINDOW_60x78,
            ))

    def test_nonfinite_and_invalid_quantity_are_rejected(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                calculate_maxim_ar(configuration(width_mm=value))
        with self.assertRaises(ValueError):
            calculate_maxim_ar(configuration(quantity=0))

    def test_unproved_finish_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Acabamento interno"):
            calculate_maxim_ar(configuration(internal_finish="SEM ACABAMENTO"))

    def test_purchase_plan_uses_configurable_stock_and_zero_kerf(self):
        cfg = configuration()
        result = calculate_maxim_ar(cfg)
        default = build_order_purchase_plan([(cfg, result)])
        shorter = build_order_purchase_plan([(cfg, result)], stock_length_mm=3000)
        self.assertEqual(default.kerf_mm, 0)
        self.assertGreaterEqual(
            sum(line.bars_required for line in shorter.lines),
            sum(line.bars_required for line in default.lines),
        )

    def test_golden_contains_bom_cost_cut_and_purchase(self):
        golden = json.loads((ROOT / "test_cases" / "maxim_ar_golden_v0_1.json").read_text(encoding="utf-8"))
        cfg = configuration()
        result = calculate_maxim_ar(cfg)
        plan = build_order_purchase_plan([(cfg, result)])

        self.assertEqual(result.calculation_version, "MX_ENGINE_0.1.0")
        self.assertEqual(result.geometry, golden["geometry"])
        self.assertEqual(result.cost_breakdown, golden["cost_by_group"])
        actual_bom = [
            [item.role, item.material_code, item.length_mm, item.quantity_per_unit, item.cost_per_unit_product]
            for item in result.unit_bom
        ]
        self.assertEqual(actual_bom, golden["bom"])
        self.assertEqual(plan.technical_total, golden["purchase"]["technical_total"])
        self.assertEqual(plan.bar_stock_purchase_cost, golden["purchase"]["bar_stock_purchase_cost"])
        self.assertEqual(plan.procurement_total_estimate, golden["purchase"]["procurement_total_estimate"])
        actual_lines = {
            line.material_code: [line.pieces_count, line.consumed_length_mm, line.bars_required]
            for line in plan.lines
        }
        self.assertEqual(actual_lines, golden["purchase"]["lines"])

    def test_matrix_never_emits_negative_physical_values(self):
        for system in MaximArLeafSystem:
            for width, height in ((300, 300), (600, 800), (1200, 1800)):
                with self.subTest(system=system, width=width, height=height):
                    result = calculate_maxim_ar(configuration(
                        width_mm=width,
                        height_mm=height,
                        leaf_system=system,
                    ))
                    self.assertTrue(all(value > 0 for value in result.geometry.values()))
                    self.assertTrue(all(item.quantity_per_unit > 0 for item in result.unit_bom))
                    self.assertTrue(all(item.cost_per_unit_product >= 0 for item in result.unit_bom))


if __name__ == "__main__":
    unittest.main()
