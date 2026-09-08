import math
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import (  # noqa: E402
    CustomDimension,
    FixedPanelConfiguration,
    FixedPanelPosition,
    GridAxis,
    LeafGrid,
    LeafSystem,
    SlidingConfiguration,
    StructuralReinforcement,
    TransomOrientation,
    build_order_purchase_plan,
    calculate_sliding,
)


def configuration(**overrides):
    values = {
        "width_mm": 2000,
        "height_mm": 2000,
        "quantity": 1,
        "leaf_count": 2,
        "leaf_system": LeafSystem.PRIME_WINDOW_42x66,
        # Estes acabamentos reproduzem os casos recalculados no XLSM.
        "internal_finish": "BARRA CHATA DE 30MM",
        "external_finish": "BARRA CHATA DE 30MM",
    }
    values.update(overrides)
    return SlidingConfiguration(**values)


def matching(result, role, material_code=None):
    return [
        component
        for component in result.unit_bom
        if component.role == role
        and (material_code is None or component.material_code == material_code)
    ]


def quantity(result, role, material_code=None):
    return sum(
        component.quantity_per_unit
        for component in matching(result, role, material_code)
    )


def linear_consumption_mm(result, role, material_code=None):
    return sum(
        component.length_mm * component.quantity_per_unit
        for component in matching(result, role, material_code)
    )


class CRPhase1ExcelRegressionTests(unittest.TestCase):
    def assert_cost_consistent(self, result):
        self.assertAlmostEqual(
            result.unit_cost,
            sum(component.cost_per_unit_product for component in result.unit_bom),
            places=6,
        )
        self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)
        self.assertTrue(all(value >= 0 for value in result.cost_breakdown.values()))

    def test_t26_prime_horizontal_transom_matches_excel(self):
        cfg = configuration(leaf_grid=LeafGrid(horizontal_transoms=1))
        result = calculate_sliding(cfg)

        self.assertEqual(result.geometry["leaf_grid_rows"], 2)
        self.assertEqual(result.geometry["leaf_grid_columns"], 1)
        self.assertEqual(result.geometry["baguette_width_mm"], 889)
        self.assertEqual(result.geometry["baguette_height_mm"], 892)
        self.assertEqual(result.geometry["glass_width_mm"], 881)
        self.assertEqual(result.geometry["glass_height_mm"], 884)
        self.assertEqual(result.geometry["total_glass_panel_count"], 4)
        self.assertEqual(quantity(result, "GLAZING_BEAD_HORIZONTAL"), 8)
        self.assertEqual(quantity(result, "GLAZING_BEAD_VERTICAL"), 8)
        self.assertEqual(quantity(result, "LEAF_TRANSOM_HORIZONTAL", "PR4263"), 2)
        self.assertEqual(
            linear_consumption_mm(result, "LEAF_TRANSOM_HORIZONTAL", "PR4263"),
            1778,
        )
        self.assertEqual(
            quantity(result, "LEAF_TRANSOM_REINFORCEMENT_HORIZONTAL", "RAG - PR4263"),
            2,
        )
        self.assertAlmostEqual(
            matching(result, "LEAF_TRANSOM_HORIZONTAL", "PR4263")[0]
            .cost_per_unit_product,
            45.23232,
            places=6,
        )
        self.assertAlmostEqual(
            matching(
                result,
                "LEAF_TRANSOM_REINFORCEMENT_HORIZONTAL",
                "RAG - PR4263",
            )[0].cost_per_unit_product,
            12.446,
            places=6,
        )
        self.assertEqual(quantity(result, "GLAZING_BLOCK"), 8)
        self.assertEqual(matching(result, "LEAF_RUBBER")[0].length_mm, 14248)
        self.assertEqual(result.cost_breakdown["BAGUETES"], 152.73856)
        self.assertEqual(result.cost_breakdown["VIDROS"], 233.6412)
        self.assertEqual(
            [(panel.area_m2, panel.total_cost) for panel in result.glass_panels],
            [(0.778804, 116.8206), (0.778804, 116.8206)],
        )
        # Excel 1528.83176 + correção PAR2 sem bandeiras (0.08).
        self.assertAlmostEqual(result.unit_cost, 1528.91176, places=5)
        self.assert_cost_consistent(result)

    def test_t26_design_two_horizontal_transoms_matches_excel(self):
        cfg = configuration(
            width_mm=2400,
            height_mm=2200,
            leaf_count=4,
            leaf_system=LeafSystem.DESIGN_DOOR_60x111,
            leaf_grid=LeafGrid(horizontal_transoms=2),
        )
        result = calculate_sliding(cfg)

        self.assertEqual(result.geometry["baguette_width_mm"], 445.5)
        self.assertEqual(result.geometry["baguette_height_mm"], 618)
        self.assertEqual(result.geometry["glass_width_mm"], 437.5)
        self.assertEqual(result.geometry["glass_height_mm"], 610)
        self.assertEqual(result.geometry["total_glass_panel_count"], 12)
        self.assertEqual(quantity(result, "LEAF_TRANSOM_HORIZONTAL", "DE6072"), 8)
        self.assertEqual(
            quantity(result, "LEAF_TRANSOM_REINFORCEMENT_HORIZONTAL", "RAG - DE6072"),
            8,
        )
        self.assertEqual(quantity(result, "GLAZING_BLOCK"), 24)
        self.assertAlmostEqual(result.unit_cost, 4320.21218, places=5)
        self.assert_cost_consistent(result)

    def test_t27_prime_vertical_transom_matches_excel(self):
        cfg = configuration(
            leaf_system=LeafSystem.PRIME_DOOR_42x88,
            leaf_grid=LeafGrid(vertical_transoms=1),
        )
        result = calculate_sliding(cfg)

        self.assertEqual(result.geometry["baguette_width_mm"], 414)
        self.assertEqual(result.geometry["baguette_height_mm"], 1768)
        self.assertEqual(result.geometry["glass_width_mm"], 406)
        self.assertEqual(result.geometry["glass_height_mm"], 1760)
        self.assertEqual(quantity(result, "LEAF_TRANSOM_VERTICAL", "PR4263"), 2)
        self.assertEqual(
            linear_consumption_mm(result, "LEAF_TRANSOM_VERTICAL", "PR4263"),
            3536,
        )
        self.assertAlmostEqual(result.unit_cost, 1779.86072, places=5)
        self.assert_cost_consistent(result)

    def test_t27_design_two_vertical_transoms_matches_excel(self):
        cfg = configuration(
            width_mm=2400,
            height_mm=2200,
            leaf_count=4,
            leaf_system=LeafSystem.DESIGN_DOOR_60x111,
            leaf_grid=LeafGrid(vertical_transoms=2),
        )
        result = calculate_sliding(cfg)

        self.assertEqual(result.geometry["baguette_width_mm"], 124.5)
        self.assertEqual(result.geometry["baguette_height_mm"], 1926)
        self.assertEqual(result.geometry["glass_width_mm"], 116.5)
        self.assertEqual(result.geometry["glass_height_mm"], 1918)
        self.assertEqual(result.geometry["total_glass_panel_count"], 12)
        self.assertEqual(quantity(result, "LEAF_TRANSOM_VERTICAL", "DE6072"), 8)
        self.assertEqual(quantity(result, "GLAZING_BLOCK"), 24)
        self.assertAlmostEqual(result.unit_cost, 5184.11354, places=5)
        self.assert_cost_consistent(result)

    def test_t28_bottom_fixed_panel_without_transoms(self):
        cfg = configuration(
            width_mm=2200,
            height_mm=2400,
            bottom_fixed_panel=FixedPanelConfiguration(height_mm=400),
        )
        result = calculate_sliding(cfg)
        panel = result.fixed_panels[0]

        self.assertEqual(panel.position, FixedPanelPosition.BOTTOM)
        self.assertEqual(result.geometry["frame_height_final_mm"], 2000)
        self.assertEqual(panel.frame_height_mm, 400)
        self.assertEqual((panel.openings[0].width_mm, panel.openings[0].height_mm), (2120, 320))
        fixed_glass = next(p for p in result.glass_panels if p.source == "FIXED_PANEL_BOTTOM")
        self.assertEqual((fixed_glass.width_mm, fixed_glass.height_mm), (2112, 312))
        self.assertEqual(quantity(result, "BOTTOM_FIXED_FRAME_HORIZONTAL", "DE6058"), 2)
        self.assertEqual(quantity(result, "BOTTOM_FIXED_FRAME_VERTICAL", "DE6058"), 2)
        self.assertEqual(
            matching(result, "BOTTOM_FIXED_FRAME_HORIZONTAL", "DE6058")[0]
            .length_mm,
            2205,
        )
        self.assertEqual(
            matching(
                result,
                "BOTTOM_FIXED_FRAME_REINFORCEMENT_HORIZONTAL",
                "RAG - DE6058",
            )[0].length_mm,
            2084,
        )
        self.assertEqual(quantity(result, "DRAIN_CAP"), 4)
        self.assertEqual(quantity(result, "GLAZING_BLOCK"), 6)
        self.assertEqual(fixed_glass.area_m2, 0.658944)
        self.assertEqual(fixed_glass.total_cost, 49.4208)
        self.assertEqual(matching(result, "FIXED_PANEL_RUBBER")[0].length_mm, 4880)
        # Excel 1866.84176 + vedação física ausente (8.784) + PAR2 fantasma (0.04).
        self.assertAlmostEqual(result.unit_cost, 1875.66576, places=5)
        self.assert_cost_consistent(result)

    def test_t28b_bottom_fixed_panel_grid(self):
        cfg = configuration(
            width_mm=2200,
            height_mm=2600,
            leaf_system=LeafSystem.DESIGN_DOOR_60x111,
            bottom_fixed_panel=FixedPanelConfiguration(
                height_mm=600,
                horizontal_transoms=1,
                vertical_transoms=1,
            ),
        )
        result = calculate_sliding(cfg)
        panel = result.fixed_panels[0]

        self.assertEqual(len(panel.openings), 4)
        self.assertTrue(all(o.width_mm == 1042 and o.height_mm == 242 for o in panel.openings))
        self.assertEqual(quantity(result, "FIXED_PANEL_TRANSOM_HORIZONTAL", "DE6072"), 2)
        self.assertEqual(quantity(result, "FIXED_PANEL_TRANSOM_VERTICAL", "DE6072"), 1)
        self.assertEqual(quantity(result, "FIXED_PANEL_TRANSOM_REINFORCEMENT_HORIZONTAL"), 2)
        self.assertEqual(quantity(result, "FIXED_PANEL_TRANSOM_REINFORCEMENT_VERTICAL"), 1)
        self.assertEqual(result.geometry["fixed_glass_panel_count"], 4)
        self.assertEqual(quantity(result, "GLAZING_BLOCK"), 12)
        self.assertAlmostEqual(result.unit_cost, 3338.88903, places=5)
        self.assert_cost_consistent(result)

    def test_t29_top_fixed_panel_without_transoms(self):
        cfg = configuration(
            width_mm=2200,
            height_mm=2400,
            top_fixed_panel=FixedPanelConfiguration(height_mm=400),
        )
        result = calculate_sliding(cfg)
        panel = result.fixed_panels[0]

        self.assertEqual(panel.position, FixedPanelPosition.TOP)
        self.assertEqual(result.geometry["frame_height_final_mm"], 2000)
        self.assertEqual((panel.openings[0].width_mm, panel.openings[0].height_mm), (2120, 320))
        self.assertEqual(quantity(result, "TOP_FIXED_FRAME_HORIZONTAL"), 2)
        self.assertEqual(quantity(result, "TOP_FIXED_FRAME_VERTICAL"), 2)
        self.assertAlmostEqual(result.unit_cost, 1875.66576, places=5)
        self.assert_cost_consistent(result)

    def test_t29b_top_fixed_panel_grid(self):
        cfg = configuration(
            width_mm=2200,
            height_mm=2600,
            leaf_system=LeafSystem.DESIGN_DOOR_60x111,
            top_fixed_panel=FixedPanelConfiguration(
                height_mm=600,
                horizontal_transoms=1,
                vertical_transoms=1,
            ),
        )
        result = calculate_sliding(cfg)

        self.assertEqual(result.fixed_panels[0].position, FixedPanelPosition.TOP)
        self.assertEqual(len(result.fixed_panels[0].openings), 4)
        self.assertEqual(quantity(result, "FIXED_PANEL_TRANSOM_HORIZONTAL"), 2)
        self.assertEqual(quantity(result, "FIXED_PANEL_TRANSOM_VERTICAL"), 1)
        self.assertAlmostEqual(result.unit_cost, 3338.88903, places=5)
        self.assert_cost_consistent(result)

    def test_t34_without_structural_reinforcement(self):
        cfg = configuration(
            width_mm=2400,
            height_mm=2800,
            leaf_count=4,
            bottom_fixed_panel=FixedPanelConfiguration(height_mm=400),
            top_fixed_panel=FixedPanelConfiguration(height_mm=450),
        )
        result = calculate_sliding(cfg)

        self.assertEqual(result.geometry["frame_height_final_mm"], 1950)
        self.assertEqual([panel.frame_height_mm for panel in result.fixed_panels], [400, 450])
        self.assertFalse(matching(result, "STRUCTURAL_REINFORCEMENT"))
        self.assertAlmostEqual(result.unit_cost, 2847.6391, places=5)
        self.assert_cost_consistent(result)

    def test_t34b_structural_reinforcement_reduces_each_panel_50mm(self):
        cfg = configuration(
            width_mm=2400,
            height_mm=2800,
            leaf_count=4,
            bottom_fixed_panel=FixedPanelConfiguration(height_mm=400),
            top_fixed_panel=FixedPanelConfiguration(height_mm=450),
            structural_reinforcement=StructuralReinforcement("ALUM10238"),
        )
        result = calculate_sliding(cfg)

        self.assertEqual(result.geometry["frame_height_final_mm"], 1950)
        self.assertEqual([panel.frame_height_mm for panel in result.fixed_panels], [350, 400])
        structural = matching(result, "STRUCTURAL_REINFORCEMENT", "ALUM10238")[0]
        self.assertEqual(structural.length_mm, 2400)
        self.assertEqual(structural.quantity_per_unit, 2)
        self.assertAlmostEqual(result.unit_cost, 3038.7191, places=5)
        self.assert_cost_consistent(result)

    def test_manual_dimensions_are_explicit_clear_spans(self):
        cfg = configuration(
            width_mm=2400,
            height_mm=2200,
            leaf_grid=LeafGrid(
                horizontal_transoms=2,
                vertical_transoms=2,
                custom_dimensions=(
                    CustomDimension(GridAxis.COLUMNS, 0, 500),
                    CustomDimension(GridAxis.COLUMNS, 1, 300),
                    CustomDimension(GridAxis.ROWS, 0, 600),
                    CustomDimension(GridAxis.ROWS, 1, 650),
                ),
            ),
        )
        result = calculate_sliding(cfg)
        first_leaf = [o for o in result.leaf_openings if o.row_index == 0]
        first_column = [o for o in result.leaf_openings if o.column_index == 0]

        self.assertEqual([o.width_mm for o in first_leaf], [500, 300, 233])
        self.assertEqual([o.height_mm for o in first_column], [600, 650, 706])
        self.assertEqual(len(result.leaf_openings), 9)
        self.assertEqual(result.geometry["total_glass_panel_count"], 18)
        self.assertEqual(quantity(result, "GLAZING_BLOCK"), 36)
        self.assertTrue(all(panel.width_mm > 0 and panel.height_mm > 0 for panel in result.glass_panels))
        self.assert_cost_consistent(result)

    def test_invalid_manual_dimensions_fail_instead_of_creating_negative_panels(self):
        cfg = configuration(
            leaf_grid=LeafGrid(
                vertical_transoms=1,
                custom_dimensions=(
                    CustomDimension(GridAxis.COLUMNS, 0, 900),
                ),
            )
        )
        with self.assertRaisesRegex(ValueError, "não deixam vão positivo"):
            calculate_sliding(cfg)

    def test_subdivided_screen_updates_mesh_beads_and_rubber(self):
        cfg = configuration(
            leaf_count=4,
            screen_enabled=True,
            leaf_grid=LeafGrid(horizontal_transoms=1, vertical_transoms=1),
        )
        result = calculate_sliding(cfg)

        self.assertEqual(result.geometry["leaf_glass_panel_count"], 16)
        self.assertEqual(quantity(result, "SCREEN_MESH"), 8)
        self.assertEqual(quantity(result, "SCREEN_BEAD_HORIZONTAL"), 16)
        self.assertEqual(quantity(result, "SCREEN_BEAD_VERTICAL"), 16)
        self.assertGreater(matching(result, "SCREEN_RUBBER")[0].length_mm, 0)
        self.assert_cost_consistent(result)

    def test_combined_design_quantity_two_reaches_bom_and_cut_plan(self):
        cfg = configuration(
            width_mm=3000,
            height_mm=3000,
            quantity=2,
            leaf_count=4,
            leaf_system=LeafSystem.DESIGN_DOOR_60x111,
            leaf_grid=LeafGrid(horizontal_transoms=1, vertical_transoms=1),
            bottom_fixed_panel=FixedPanelConfiguration(
                height_mm=450, horizontal_transoms=1, vertical_transoms=1
            ),
            top_fixed_panel=FixedPanelConfiguration(
                height_mm=500, horizontal_transoms=1, vertical_transoms=2
            ),
        )
        result = calculate_sliding(cfg)
        plan = build_order_purchase_plan([(cfg, result)])

        self.assertEqual(result.geometry["frame_height_final_mm"], 2050)
        self.assertEqual(result.geometry["total_glass_panel_count"], 26)
        self.assertEqual(quantity(result, "GLAZING_BLOCK"), 52)
        self.assertEqual(quantity(result, "LEAF_TRANSOM_HORIZONTAL"), 8)
        self.assertEqual(quantity(result, "LEAF_TRANSOM_VERTICAL"), 4)
        self.assertTrue({"DE6072", "RAG - DE6072", "DE6058"}.issubset(
            {line.material_code for line in plan.lines}
        ))
        for component in result.unit_bom:
            self.assertAlmostEqual(
                component.quantity_order,
                component.quantity_per_unit * 2,
                places=6,
            )
        for line in plan.lines:
            self.assertEqual(line.purchased_length_mm, line.bars_required * 5900)
            self.assertAlmostEqual(
                line.waste_length_mm,
                line.purchased_length_mm - line.consumed_length_mm,
                places=6,
            )
            for bar in line.bars:
                self.assertLessEqual(bar.used_mm, bar.stock_length_mm + 1e-7)
        self.assertEqual(len(plan.lines), 16)
        self.assertEqual(sum(line.pieces_count for line in plan.lines), 444)
        self.assertEqual(sum(line.bars_required for line in plan.lines), 101)
        self.assertAlmostEqual(
            sum(line.consumed_length_mm for line in plan.lines),
            484043.999988,
            places=6,
        )
        self.assertAlmostEqual(
            sum(line.waste_length_mm for line in plan.lines),
            111856.000012,
            places=6,
        )
        transom_line = next(
            line for line in plan.lines if line.material_code == "DE6072"
        )
        self.assertTrue(all(
            piece.source_position
            for bar in transom_line.bars
            for piece in bar.pieces
        ))
        self.assertAlmostEqual(plan.technical_total, 12889.430356, places=6)
        self.assertAlmostEqual(plan.bar_stock_purchase_cost, 13416.01, places=5)
        self.assertAlmostEqual(plan.procurement_total_estimate, 14926.7564, places=4)

    def test_new_geometries_never_emit_negative_values(self):
        configs = [
            configuration(leaf_grid=LeafGrid(horizontal_transoms=2, vertical_transoms=2)),
            configuration(
                width_mm=2600,
                height_mm=2800,
                bottom_fixed_panel=FixedPanelConfiguration(500, 1, 2),
                top_fixed_panel=FixedPanelConfiguration(450, 2, 1),
                structural_reinforcement=StructuralReinforcement("ALUM15338"),
            ),
        ]
        for cfg in configs:
            with self.subTest(cfg=cfg):
                result = calculate_sliding(cfg)
                for component in result.unit_bom:
                    self.assertGreater(component.quantity_per_unit, 0)
                    self.assertGreaterEqual(component.cost_per_unit_product, 0)
                    if component.length_mm is not None:
                        self.assertGreater(component.length_mm, 0)
                    if component.area_m2 is not None:
                        self.assertGreater(component.area_m2, 0)
                self.assertTrue(all(
                    math.isfinite(panel.area_m2) and panel.area_m2 > 0
                    for panel in result.glass_panels
                ))

    def test_kerf_zero_is_the_formal_default_and_nonzero_is_supported(self):
        cfg = configuration(leaf_grid=LeafGrid(horizontal_transoms=1))
        result = calculate_sliding(cfg)
        default_plan = build_order_purchase_plan([(cfg, result)])
        explicit_zero = build_order_purchase_plan([(cfg, result)], kerf_mm=0)

        self.assertEqual(default_plan.kerf_mm, 0)
        self.assertEqual(
            [line.bars_required for line in default_plan.lines],
            [line.bars_required for line in explicit_zero.lines],
        )
        self.assertTrue(all(line.kerf_loss_mm == 0 for line in default_plan.lines))
        with_kerf = build_order_purchase_plan([(cfg, result)], kerf_mm=3)
        self.assertEqual(with_kerf.kerf_mm, 3)
        self.assertTrue(all(
            line.kerf_loss_mm == line.pieces_count * 3
            for line in with_kerf.lines
        ))
        for line in with_kerf.lines:
            for bar in line.bars:
                self.assertAlmostEqual(
                    bar.used_mm,
                    sum(piece.length_mm for piece in bar.pieces)
                    + len(bar.pieces) * 3,
                    places=6,
                )
        with self.assertRaisesRegex(ValueError, "perda de serra"):
            build_order_purchase_plan([(cfg, result)], kerf_mm=-1)


if __name__ == "__main__":
    unittest.main()
