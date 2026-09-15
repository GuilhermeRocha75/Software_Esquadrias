import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import (
    FixedPanelConfiguration, MaximArConfiguration, MaximArLeafSystem,
    MaximArSealingConfiguration, calculate_maxim_ar, build_order_purchase_plan,
)
from mx_golden_support import configuration_from_json, snapshot


class MaximArFinalAuditTests(unittest.TestCase):
    def test_audited_prime_03_exact_component_costs_and_excel_delta(self):
        result = calculate_maxim_ar(MaximArConfiguration(
            width_mm=1000, height_mm=3000, quantity=1,
            leaf_system=MaximArLeafSystem.PRIME_WINDOW_42x63,
            bottom_fixed_panel=FixedPanelConfiguration(1000, 3),
            sealing=MaximArSealingConfiguration(unit_price_per_meter=1.8),
        ))
        # Excel recalculado: I85=1300.84718, I70=45.28; 4 -> 20 calços.
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 47.6208)
        self.assertEqual(result.unit_cost, round(1300.84718 - 45.28 + 47.6208 + 16 * 0.35, 6))
        horizontal = [x for x in result.unit_bom if x.role == "BOTTOM_BEAD_HORIZONTAL"]
        self.assertEqual(sum(x.cost_per_unit_product for x in horizontal), 99.428)
        fixed_glass = [x for x in result.glass_panels if x.source == "BOTTOM"]
        self.assertEqual(sum(x.total_cost for x in fixed_glass), 90.0519)
        # A correção de 6 mm não encurta o perfil nem seu reforço.
        self.assertEqual(
            [(x.length_mm, x.quantity_per_unit) for x in result.unit_bom
             if x.role in ("BOTTOM_BOUNDARY_TRANSOM_HORIZONTAL", "BOTTOM_FIXED_DIVIDER_HORIZONTAL")],
            [(950, 1), (950, 3)],
        )

    def test_exact_integrated_dimensions_both_positions_and_systems(self):
        # Independent constants: XLSM D14/D16:D19, PFAB B18/B19.
        # V/H generalizes the approved topology using the same clear span.
        for system, boundary, spans in (
            (MaximArLeafSystem.PRIME_WINDOW_42x63, 950,
             ((0, 0, 938, 958, 930, 950), (3, 0, 938, 218.5, 930, 210.5),
              (2, 1, 455, 300.666667, 447, 292.666667))),
            (MaximArLeafSystem.DESIGN_WINDOW_60x78, 932,
             ((0, 0, 920, 942, 912, 934), (3, 0, 920, 208.5, 912, 200.5),
              (2, 1, 442, 290, 434, 282))),
        ):
            for position in ("bottom", "top"):
                for h, v, ow, oh, gw, gh in spans:
                    with self.subTest(system=system, position=position, h=h, v=v):
                        cfg = MaximArConfiguration(
                            width_mm=1000, height_mm=3000, quantity=2, leaf_system=system,
                            **{position + "_fixed_panel": FixedPanelConfiguration(1000, h, v)},
                        )
                        result = calculate_maxim_ar(cfg)
                        panel = result.fixed_panels[0]
                        self.assertEqual(len(panel.openings), (v + 1) * (h + 1))
                        for opening in panel.openings:
                            self.assertEqual((opening.width_mm, opening.height_mm), (ow, oh))
                        for glass in result.glass_panels:
                            if glass.source == position.upper():
                                self.assertEqual((glass.width_mm, glass.height_mm), (gw, gh))
                        cut = next(t for t in result.transoms if t.source.endswith("_BOUNDARY"))
                        self.assertEqual(cut.length_mm, boundary)
                        self.assertEqual(cut.quantity, 1)
                        beads = [x for x in result.unit_bom if x.role == position.upper() + "_BEAD_HORIZONTAL"]
                        self.assertEqual(len(beads), (v + 1) * (h + 1))
                        self.assertTrue(all(x.length_mm == ow for x in beads))
                        plan = build_order_purchase_plan([(cfg, result)], kerf_mm=3)
                        cuts = [p.length_mm for line in plan.lines for bar in line.bars
                                for p in bar.pieces if p.source_role == position.upper() + "_BEAD_HORIZONTAL"]
                        self.assertEqual(cuts, [ow] * (4 * (v + 1) * (h + 1)))

    def test_historical_prime_integrated_dimensions(self):
        # ORCS rows selected from 17 MX PRIME integrated records; no customer fields.
        for row, width, height, flag, opening_width, glass_width in (
            (1240, 350, 1200, 400, 288, 280),
            (2054, 400, 1400, 300, 338, 330),
            (8206, 800, 1800, 800, 738, 730),
        ):
            with self.subTest(orcs=row):
                result = calculate_maxim_ar(MaximArConfiguration(
                    width_mm=width, height_mm=height, quantity=1,
                    leaf_system=MaximArLeafSystem.PRIME_WINDOW_42x63,
                    bottom_fixed_panel=FixedPanelConfiguration(flag),
                ))
                self.assertEqual(result.fixed_panels[0].openings[0].width_mm, opening_width)
                self.assertEqual(result.glass_panels[1].width_mm, glass_width)

    def test_current_golden_all_outputs_cost_reconciliation_and_ffd(self):
        golden = json.loads((ROOT / "test_cases/maxim_ar_golden_v0_3.json").read_text(encoding="utf-8"))
        self.assertEqual(golden["engine_version"], "MX_ENGINE_0.3.0")
        self.assertEqual(golden["source_workbook_sha256"], "96514D7818BCBBC1DB86F94F86D8ED0239675E9F8D3A6B64DF651F30FD90C160")
        for case in golden["cases"]:
            with self.subTest(case=case["id"]):
                cfg = configuration_from_json(case["input"])
                result = calculate_maxim_ar(cfg)
                plan = build_order_purchase_plan([(cfg, result)],
                                                 stock_length_mm=case["stock_length_mm"],
                                                 kerf_mm=case["kerf_mm"])
                self.assertEqual(result.calculation_version, golden["engine_version"])
                self.assertEqual(snapshot(result, plan), case["expected"])
                reconciliation = case["excel_comparison"]
                self.assertEqual(result.unit_cost, reconciliation["engine_unit_cost"])
                self.assertEqual(
                    round(reconciliation["reference_unit_cost"] + sum(x["delta"] for x in reconciliation["changes"]), 6),
                    result.unit_cost,
                )
                self.assertEqual(reconciliation["delta"], round(result.unit_cost - reconciliation["reference_unit_cost"], 6))
                for change in reconciliation["changes"]:
                    self.assertEqual(round(change["engine"] - change["excel"], 6), change["delta"])
                seals = [x for x in result.unit_bom if x.category == "VEDAÇÕES"]
                self.assertEqual(len(seals), 3)
                self.assertEqual(cfg.sealing.unit_price_per_meter, 1.8)
                self.assertEqual(result.cost_breakdown["VEDAÇÕES"], round(sum(x.cost_per_unit_product for x in seals), 6))
                self.assertTrue(all("RESOLVED_PHYSICAL" in x.source for x in seals))
                blocks = next(x for x in result.unit_bom if x.role == "GLAZING_BLOCK")
                self.assertEqual(blocks.quantity_order, 4 * sum(p.quantity for p in result.glass_panels) * cfg.quantity)
                self.assertEqual(plan.technical_total, round(result.unit_cost * cfg.quantity, 6))
                for line in plan.lines:
                    for bar in line.bars:
                        self.assertLessEqual(sum(p.length_mm + case["kerf_mm"] for p in bar.pieces), case["stock_length_mm"] + 1e-6)


if __name__ == "__main__":
    unittest.main()
