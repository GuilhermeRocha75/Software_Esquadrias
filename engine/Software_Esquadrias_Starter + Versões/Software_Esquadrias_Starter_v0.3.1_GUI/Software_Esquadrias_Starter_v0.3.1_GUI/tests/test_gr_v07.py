import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine.gr_v07 import GrConfiguration, calculate_gr  # noqa: E402

MONO = "MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE"
MULTI = "MAÇANETA DUPLA COM FECHADURA MULTIPONTO E CHAVE"
WINDOW_CREMONA = "MAÇANETA COM CREMONA SEM CHAVE"
CREMONA_800 = "CREMONA 2 PONTOS COMP. 800mm E:15mm"
INTERNAL = "FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN"
EXTERNAL = "FOLHA DE PORTA ABERTURA EXTERNA 60X104MM - DESIGN"
WINDOW = "FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN"


def panel_door(**overrides):
    values = {
        "width_mm": 900,
        "height_mm": 2100,
        "quantity": 1,
        "leaf_system": INTERNAL,
        "application": "PORTA",
        "panel_mode": "PAINEL COMPLETO",
        "closure_mode": MONO,
    }
    values.update(overrides)
    return GrConfiguration(**values)


def glass_door(**overrides):
    values = {
        "width_mm": 800,
        "height_mm": 2100,
        "quantity": 1,
        "leaf_system": INTERNAL,
        "application": "PORTA",
        "panel_mode": "VIDRO INTEIRO",
        "glass_description": "06mm TEMPERADO INCOLOR",
        "closure_mode": MONO,
    }
    values.update(overrides)
    return GrConfiguration(**values)


def two_leaf_glass(**overrides):
    values = {
        "width_mm": 1200,
        "height_mm": 2100,
        "quantity": 1,
        "leaf_count": 2,
        "leaf_system": INTERNAL,
        "application": "PORTA",
        "panel_mode": "VIDRO INTEIRO",
        "glass_description": "06mm TEMPERADO INCOLOR",
        "closure_mode": MONO,
    }
    values.update(overrides)
    return GrConfiguration(**values)


def window(**overrides):
    values = {
        "width_mm": 800,
        "height_mm": 1300,
        "quantity": 1,
        "leaf_system": WINDOW,
        "application": "JANELA",
        "closure_mode": WINDOW_CREMONA,
        "cremona_description": CREMONA_800,
    }
    values.update(overrides)
    return GrConfiguration(**values)


class GrPhase7Tests(unittest.TestCase):
    def test_version_is_v07(self):
        self.assertEqual(calculate_gr(panel_door()).calculation_version, "GR_ENGINE_0.7.0")
        self.assertEqual(calculate_gr(two_leaf_glass()).calculation_version, "GR_ENGINE_0.7.0")

    def test_v06_panel_costs_are_preserved_after_version_promotion(self):
        mono = calculate_gr(panel_door())
        multi = calculate_gr(panel_door(closure_mode=MULTI))
        two_leaf = calculate_gr(panel_door(width_mm=1600, leaf_count=2))
        self.assertEqual(mono.unit_cost, 1412.475245)
        self.assertEqual(multi.unit_cost, 1480.275245)
        self.assertEqual(two_leaf.unit_cost, 2277.196098)
        self.assertEqual(mono.cost_breakdown["VEDAÇÕES"], 27.7516)

    def test_v06_one_leaf_glass_cost_is_preserved(self):
        result = calculate_gr(glass_door())
        self.assertEqual(result.unit_cost, 1358.19195)
        self.assertEqual(result.geometry["glass_width_mm"], 556.0)
        self.assertEqual(result.geometry["glass_height_mm"], 1883.0)
        self.assertEqual(result.geometry["glass_panel_count"], 1.0)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 26.7516)

    def test_orcs_17138_two_leaf_glass_geometry_and_physical_total(self):
        result = calculate_gr(two_leaf_glass())
        self.assertEqual(result.model_description, "PORTA 2 FOLHAS DE GIRO")
        self.assertEqual(result.geometry["leaf_width_final_mm"], 558.0)
        self.assertEqual(result.geometry["leaf_height_final_mm"], 2063.0)
        self.assertEqual(result.geometry["glass_bead_width_mm"], 386.0)
        self.assertEqual(result.geometry["glass_bead_height_mm"], 1891.0)
        self.assertEqual(result.geometry["glass_width_mm"], 378.0)
        self.assertEqual(result.geometry["glass_height_mm"], 1883.0)
        self.assertEqual(result.geometry["glass_panel_count"], 2.0)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 49.9432)
        self.assertEqual(result.unit_cost, 2071.84485)

    def test_orcs_17138_legacy_parity_is_exact_before_physical_sealing_fix(self):
        result = calculate_gr(two_leaf_glass())
        legacy_without_seals = round(result.unit_cost - result.cost_breakdown["VEDAÇÕES"], 6)
        self.assertEqual(legacy_without_seals, 2021.90165)

    def test_two_leaf_glass_bom_quantities_are_per_leaf(self):
        result = calculate_gr(two_leaf_glass())
        bead_width = next(x for x in result.unit_bom if x.role == "GLASS_BEAD_WIDTH")
        bead_height = next(x for x in result.unit_bom if x.role == "GLASS_BEAD_HEIGHT")
        glass = next(x for x in result.unit_bom if x.role == "GLASS_PANEL")
        blocks = next(x for x in result.unit_bom if x.material_code == "AC0312")
        hinges = next(x for x in result.unit_bom if x.role == "HINGE_90MM")
        fec7 = next(x for x in result.unit_bom if x.material_code == "FEC7")
        con3 = next(x for x in result.unit_bom if x.material_code == "CON3")
        self.assertEqual(bead_width.material_code, "BA3518")
        self.assertEqual(bead_width.quantity_per_unit, 4.0)
        self.assertEqual(bead_height.quantity_per_unit, 4.0)
        self.assertEqual(glass.quantity_per_unit, 2.0)
        self.assertEqual(glass.area_m2, 0.711774)
        self.assertEqual(glass.cost_per_unit_product, 177.9435)
        self.assertEqual(blocks.quantity_per_unit, 8.0)
        self.assertEqual(hinges.quantity_per_unit, 6.0)
        self.assertEqual(fec7.quantity_per_unit, 2.0)
        self.assertEqual(con3.quantity_per_unit, 2.0)

    def test_two_leaf_glass_fasteners_follow_xlsm_and_factory_rules(self):
        result = calculate_gr(two_leaf_glass())
        par2 = next(x for x in result.unit_bom if x.material_code == "PAR2")
        par1 = next(x for x in result.unit_bom if x.material_code == "PAR1")
        self.assertAlmostEqual(par2.quantity_per_unit, 55.328, places=9)
        self.assertEqual(par1.quantity_per_unit, 52.0)
        self.assertIn("RESOLVED_PHYSICAL", par1.source)

    def test_two_leaf_glass_multipoint_keeps_exact_67_80_delta(self):
        mono = calculate_gr(two_leaf_glass(closure_mode=MONO))
        multi = calculate_gr(two_leaf_glass(closure_mode=MULTI))
        self.assertEqual(round(multi.unit_cost - mono.unit_cost, 6), 67.8)
        self.assertEqual(multi.unit_cost, 2139.64485)

    def test_two_leaf_external_glass_uses_external_leaf_profile(self):
        result = calculate_gr(two_leaf_glass(leaf_system=EXTERNAL))
        leaf_codes = {
            x.material_code
            for x in result.unit_bom
            if x.role in {"LEAF_WIDTH", "LEAF_HEIGHT"}
        }
        self.assertEqual(leaf_codes, {"DE60104-E"})
        self.assertEqual(result.geometry["glass_panel_count"], 2.0)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 49.9432)

    def test_two_leaf_glass_quantity_scales_order_bom_only(self):
        one = calculate_gr(two_leaf_glass(quantity=1))
        three = calculate_gr(two_leaf_glass(quantity=3))
        self.assertEqual(one.unit_cost, three.unit_cost)
        for item in three.unit_bom:
            self.assertEqual(item.quantity_order, item.quantity_per_unit * 3)
        glass = next(x for x in three.unit_bom if x.role == "GLASS_PANEL")
        self.assertEqual(glass.quantity_order, 6.0)

    def test_window_glass_remains_blocked(self):
        with self.assertRaises(ValueError):
            calculate_gr(window(
                panel_mode="VIDRO INTEIRO",
                glass_description="06mm TEMPERADO INCOLOR",
            ))

    def test_missing_glass_remains_blocked(self):
        with self.assertRaises(ValueError):
            calculate_gr(two_leaf_glass(glass_description=None))

    def test_cost_is_exact_sum_of_bom_for_v07_scope(self):
        cases = [
            panel_door(),
            panel_door(width_mm=1600, leaf_count=2),
            glass_door(),
            two_leaf_glass(),
            two_leaf_glass(closure_mode=MULTI),
            two_leaf_glass(leaf_system=EXTERNAL),
        ]
        for cfg in cases:
            with self.subTest(cfg=cfg):
                result = calculate_gr(cfg)
                self.assertEqual(
                    result.unit_cost,
                    round(sum(item.cost_per_unit_product for item in result.unit_bom), 6),
                )
                self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)

    def test_golden_v07_is_frozen(self):
        golden = json.loads(
            (ROOT / "test_cases" / "gr_golden_v0_7.json").read_text(encoding="utf-8")
        )
        self.assertEqual(golden["engine_version"], "GR_ENGINE_0.7.0")
        for case in golden["cases"]:
            with self.subTest(case=case["id"]):
                result = calculate_gr(GrConfiguration(**case["input"]))
                self.assertEqual(result.calculation_version, golden["engine_version"])
                self.assertEqual(result.unit_cost, case["unit_cost"])
                self.assertEqual(result.cost_breakdown["VEDAÇÕES"], case["sealing_cost"])
                for key, expected in case["geometry"].items():
                    self.assertEqual(result.geometry[key], expected)
                if "legacy_orcs_cost_without_seals" in case:
                    self.assertEqual(
                        round(result.unit_cost - result.cost_breakdown["VEDAÇÕES"], 6),
                        case["legacy_orcs_cost_without_seals"],
                    )


if __name__ == "__main__":
    unittest.main()
