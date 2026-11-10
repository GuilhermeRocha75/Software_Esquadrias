import copy
import json
from dataclasses import asdict, replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT.parents[3] / "tools"))

from esquadrias_engine import (
    SlidingConfiguration, LeafSystem, calculate_sliding,
    MaximArConfiguration, MaximArLeafSystem, MaximArModuleMode, calculate_maxim_ar,
    FixedPanelConfiguration, LeafGrid, FixoConfiguration, calculate_fixo,
    GrConfiguration, calculate_gr,
)
from esquadrias_engine.production import build_production_item
from fixo_formula_oracle import FixoFormulaOracle


def sliding(**overrides):
    return SlidingConfiguration(**dict(width_mm=1930, height_mm=1490, quantity=1,
                                      leaf_count=2, leaf_system=LeafSystem.PRIME_WINDOW_42x66,
                                      screen_enabled=True) | overrides)


class ProductionProjectionTests(unittest.TestCase):
    def test_cr_frame_leaf_and_screen_final_cut_are_distinct(self):
        result = calculate_sliding(sliding())
        rows = {line.utilization: line for line in build_production_item("CR", result).lines}
        for role, final, cut, count in (("FRAME_HORIZONTAL", 1930, 1935, 2),
                                       ("LEAF_HORIZONTAL", 954, 959, 4),
                                       ("SCREEN_LEAF_HORIZONTAL", 954, 959, 2)):
            with self.subTest(role=role):
                row = rows[role]
                self.assertEqual((row.final_length_mm, row.cut_length_mm, row.quantity_total), (final, cut, count))

    def test_maxim_ar_design_and_quantity_two(self):
        result = calculate_maxim_ar(MaximArConfiguration(510, 1040, 2, MaximArLeafSystem.DESIGN_WINDOW_60x78))
        rows = {line.utilization: line for line in build_production_item("MAXIM_AR", result).lines}
        self.assertEqual((rows["LEAF_HORIZONTAL"].final_length_mm, rows["LEAF_HORIZONTAL"].cut_length_mm), (446, 451))
        self.assertEqual(rows["FRAME_HORIZONTAL"].quantity_total, 4)
        self.assertEqual(rows["GLASS_PANEL"].quantity_total, 2)

    def test_gr_asymmetric_allowance_and_fraction_are_preserved(self):
        result = calculate_gr(GrConfiguration(1160, 2110, 1))
        projection = build_production_item("GR", result)
        rows = {line.utilization: line for line in projection.lines}
        self.assertEqual((rows["FRAME_HEIGHT"].final_length_mm, rows["FRAME_HEIGHT"].cut_length_mm), (2110, 2113))
        self.assertAlmostEqual(rows["PANEL_FILL"].quantity_total, 12.835714285714285)
        self.assertEqual(rows["PANEL_FILL"].quantity_unit, "unresolved")
        self.assertTrue(any(issue.field == "quantity_unit" for issue in projection.issues))

    def test_gr_mixed_panel_has_explicit_unit_gap_and_structured_lengths(self):
        result = calculate_gr(GrConfiguration(1160, 2110, 1, panel_mode="SUPERIOR VIDRO/INFERIOR PAINEL",
                              glass_description="04mm FLOAT INCOLOR", mixed_split_from_bottom_mm=800))
        projection = build_production_item("GR", result)
        rows = {r.utilization: r for r in projection.lines}
        self.assertEqual(rows["LOWER_PANEL_FILL"].quantity_unit, "unresolved")
        for role in ("MIXED_HORIZONTAL_TRANSOM", "UPPER_GLASS_BEAD_WIDTH", "LOWER_PANEL_BEAD_HEIGHT"):
            self.assertEqual(rows[role].final_length_mm, rows[role].cut_length_mm)

    def test_fixo_own_case_including_final_reinforcement_against_frozen_d_cells(self):
        cfg = FixoConfiguration(1200, 1000, 2, 1, 1)
        projection = build_production_item("FX", calculate_fixo(cfg))
        rows = {line.utilization: line for line in projection.lines}
        self.assertEqual((rows["Marco Largura"].final_length_mm, rows["Marco Largura"].cut_length_mm), (1200, 1205))
        self.assertEqual(rows["Vidros"].quantity_total, 8)
        oracle = FixoFormulaOracle.from_snapshot(json.loads((ROOT / "test_cases/fixo_formula_snapshot_v0_1.json").read_text(encoding="utf-8")))
        oracle.set_inputs({"D": 1200, "E": 1000, "F": 2, "K": cfg.glass_description, "S": cfg.internal_finish,
                           "T": cfg.external_finish, "AJ": 1, "AK": 1})
        self.assertEqual(rows["Ref. Marco Largura"].final_length_mm, oracle.value("FX", "D20"))
        self.assertEqual(rows["Ref. Marco Altura"].final_length_mm, oracle.value("FX", "D21"))

    def test_projection_keeps_every_bom_position_group_and_does_not_mutate_result(self):
        for family, result in (("CR", calculate_sliding(sliding())),
                               ("GR", calculate_gr(GrConfiguration(1160, 2110, 1))),
                               ("FX", calculate_fixo(FixoConfiguration(1200, 1000)))):
            with self.subTest(family=family):
                before = copy.deepcopy(asdict(result))
                lines = build_production_item(family, result).lines
                self.assertEqual(len(lines), len(result.unit_bom))
                self.assertEqual([(r.position, r.group, r.utilization, r.code, r.cut_length_mm,
                                   r.bom_quantity_total, r.source) for r in lines],
                                 [(n, b.category, b.role, b.material_code, b.length_mm, b.quantity_order, b.source)
                                  for n, b in enumerate(result.unit_bom, 1)])
                self.assertEqual(asdict(result), before)

    def test_all_fixo_frozen_golden_final_and_cut_cells_are_preserved(self):
        cases = json.loads((ROOT / "test_cases/fixo_golden_v0_1.json").read_text(encoding="utf-8"))["cases"]
        for case in cases:
            with self.subTest(orcs_row=case["orcs_row"]):
                result = calculate_fixo(FixoConfiguration(**case["configuration"]))
                rows = build_production_item("FX", result).lines
                expected = {row["source"]: row for row in case["expected_bom"]}
                for row in rows:
                    if row.cut_length_mm is not None:
                        self.assertEqual(row.final_length_mm, expected[row.source]["D"], row.source)
                        self.assertEqual(row.cut_length_mm, expected[row.source]["E"], row.source)

    def test_three_leaf_mesh_count_is_not_area_factor(self):
        result = calculate_sliding(sliding(width_mm=2400, leaf_count=3, quantity=2))
        mesh = next(r for r in build_production_item("CR", result).lines if r.utilization == "SCREEN_MESH")
        self.assertEqual(mesh.bom_quantity_per_unit, 1.5)
        self.assertEqual(mesh.quantity_per_unit, result.geometry["screen_frame_count"])
        self.assertEqual(mesh.quantity_per_unit, 2)
        self.assertEqual(mesh.quantity_total, 4)

    def test_missing_code_description_unit_and_final_are_not_invented(self):
        result = calculate_sliding(sliding())
        result.unit_bom = [replace(result.unit_bom[0], role="UNKNOWN_FUTURE_ROLE", material_code="0", description="", unit="")]
        projection = build_production_item("CR", result)
        self.assertEqual(projection.lines[0].code, "0")
        self.assertEqual(projection.lines[0].description, "")
        self.assertIsNone(projection.lines[0].final_length_mm)
        self.assertTrue({"code", "description", "material_unit", "final_length_mm"} <= {i.field for i in projection.issues})

    def test_unknown_role_has_no_final_equals_cut_fallback(self):
        result = calculate_fixo(FixoConfiguration(1200, 1000))
        result.unit_bom = [replace(result.unit_bom[0], role="UNKNOWN_FUTURE_ROLE")]
        projection = build_production_item("FX", result)
        self.assertIsNone(projection.lines[0].final_length_mm)
        self.assertTrue(any(i.field == "final_length_mm" for i in projection.issues))

    def test_fractional_screws_keep_value_and_explicit_unit(self):
        result = calculate_sliding(sliding())
        projection = build_production_item("CR", result)
        row = next(r for r in projection.lines if r.utilization == "REINFORCEMENT_SCREWS")
        self.assertEqual(row.quantity_total, 84.224)
        self.assertEqual(row.material_unit, "un")
        self.assertEqual(row.quantity_unit, "piece")
        self.assertTrue(any(i.position == row.position and i.field == "quantity_total" for i in projection.issues))

    def test_cr_and_separate_mx_fixed_frames_read_final_from_existing_geometry(self):
        cr = calculate_sliding(sliding(height_mm=2400, bottom_fixed_panel=FixedPanelConfiguration(400)))
        mx = calculate_maxim_ar(MaximArConfiguration(1200, 2000, 1, MaximArLeafSystem.DESIGN_WINDOW_60x78,
                                  module_mode=MaximArModuleMode.SEPARATE, bottom_fixed_panel=FixedPanelConfiguration(400)))
        for family, result, role in (("CR", cr, "BOTTOM_FIXED_FRAME_VERTICAL"), ("MAXIM_AR", mx, "BOTTOM_FRAME_VERTICAL")):
            with self.subTest(family=family):
                row = next(r for r in build_production_item(family, result).lines if r.utilization == role)
                self.assertEqual(row.final_length_mm, result.fixed_panels[0].frame_height_mm)
                self.assertEqual(row.cut_length_mm, row.final_length_mm + 5)

    def test_dynamic_cr_grid_keeps_all_glass_and_screen_rows(self):
        result = calculate_sliding(sliding(height_mm=2400, leaf_grid=LeafGrid(horizontal_transoms=1, vertical_transoms=1)))
        rows = build_production_item("CR", result).lines
        self.assertEqual(sum(r.quantity_total for r in rows if r.group == "VIDROS"), 8)
        self.assertEqual(sum(r.quantity_total for r in rows if r.utilization == "SCREEN_MESH"), 4)
        self.assertTrue(all(r.source is not None for r in rows if r.group == "VIDROS"))

    def test_oversized_fixo_keeps_integral_piece_and_configurable_stock(self):
        result = calculate_fixo(FixoConfiguration(6500, 1000))
        row = build_production_item("FX", result, stock_lengths_mm={"DE6058": 5900}).lines[0]
        self.assertEqual((row.final_length_mm, row.cut_length_mm), (6500, 6505))
        self.assertEqual(row.splice_status, "MANUAL_SPLICE_REQUIRED")
        self.assertIsNone(build_production_item("FX", result, stock_lengths_mm={"DE6058": 7000}).lines[0].splice_status)
        self.assertIsNone(build_production_item("FX", result).lines[0].splice_status)

    def test_oversized_other_family_requires_review_without_inventing_splice(self):
        projection = build_production_item("CR", calculate_sliding(sliding()), stock_lengths_mm={"PR13852": 1000})
        self.assertEqual(projection.lines[0].splice_status, "REQUIRES_ENGINEERING_REVIEW")

    def test_invalid_family_version_stock_and_nonfinite_output_are_rejected(self):
        result = calculate_fixo(FixoConfiguration(1200, 1000))
        for family in ("PV", "GD", "CR"):
            with self.subTest(family=family), self.assertRaises(ValueError):
                build_production_item(family, result)
        for value in (0, -1, float("nan"), float("inf"), True):
            with self.subTest(stock=value), self.assertRaises(ValueError):
                build_production_item("FX", result, stock_lengths_mm={"DE6058": value})
        result.unit_bom = [replace(result.unit_bom[0], quantity_order=float("nan"))]
        with self.assertRaises(ValueError):
            build_production_item("FX", result)


if __name__ == "__main__":
    unittest.main()
