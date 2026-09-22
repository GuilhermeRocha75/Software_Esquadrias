import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine.gr_v06 import GrConfiguration, calculate_gr  # noqa: E402

MONO = "MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE"
MULTI = "MAÇANETA DUPLA COM FECHADURA MULTIPONTO E CHAVE"
WINDOW_CREMONA = "MAÇANETA COM CREMONA SEM CHAVE"
CREMONA_800 = "CREMONA 2 PONTOS COMP. 800mm E:15mm"
INTERNAL = "FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN"
EXTERNAL = "FOLHA DE PORTA ABERTURA EXTERNA 60X104MM - DESIGN"
WINDOW = "FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN"


def door(**overrides):
    values = {
        "width_mm": 900,
        "height_mm": 2100,
        "quantity": 1,
        "leaf_system": INTERNAL,
        "application": "PORTA",
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


class GrPhase6Tests(unittest.TestCase):
    def test_version_is_v06(self):
        self.assertEqual(calculate_gr(door()).calculation_version, "GR_ENGINE_0.6.0")

    def test_panel_one_leaf_receives_three_physically_confirmed_seals(self):
        result = calculate_gr(door())
        seals = {item.role: item for item in result.unit_bom if item.category == "VEDAÇÕES"}
        self.assertEqual(set(seals), {
            "GLASS_OR_LAMBRI_SEAL",
            "ROUND_SEAL_LEAF",
            "ROUND_SEAL_FRAME",
        })
        self.assertEqual(seals["GLASS_OR_LAMBRI_SEAL"].material_code, "ACB606")
        self.assertEqual(seals["GLASS_OR_LAMBRI_SEAL"].description, "BORRACHA DE VIDRO / LAMBRI")
        self.assertEqual(seals["GLASS_OR_LAMBRI_SEAL"].length_mm, 5110.0)
        self.assertEqual(seals["ROUND_SEAL_LEAF"].material_code, "AC0002")
        self.assertEqual(seals["ROUND_SEAL_LEAF"].description, "BORRACHA REDONDA")
        self.assertEqual(seals["ROUND_SEAL_LEAF"].length_mm, 5798.0)
        self.assertEqual(seals["ROUND_SEAL_FRAME"].length_mm, 5798.0)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 27.7516)
        self.assertEqual(result.unit_cost, 1412.475245)
        self.assertIn("LEGACY-GR-SEALING-CORRECTED", {w.code for w in result.warnings})

    def test_panel_multipoint_preserves_exact_hardware_delta(self):
        mono = calculate_gr(door(closure_mode=MONO))
        multi = calculate_gr(door(closure_mode=MULTI))
        self.assertEqual(mono.unit_cost, 1412.475245)
        self.assertEqual(multi.unit_cost, 1480.275245)
        self.assertEqual(round(multi.unit_cost - mono.unit_cost, 6), 67.8)

    def test_external_panel_receives_same_physical_sealing_rule(self):
        result = calculate_gr(door(
            width_mm=800,
            height_mm=2150,
            leaf_system=EXTERNAL,
            closure_mode=MULTI,
        ))
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 27.2516)
        self.assertEqual(result.unit_cost, 1445.782455)
        self.assertEqual(
            {x.material_code for x in result.unit_bom if x.role in {"LEAF_WIDTH", "LEAF_HEIGHT"}},
            {"DE60104-E"},
        )

    def test_window_panel_receives_same_three_sealing_paths(self):
        result = calculate_gr(window())
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 18.856)
        self.assertEqual(result.unit_cost, 846.578384)
        seals = [x for x in result.unit_bom if x.category == "VEDAÇÕES"]
        self.assertEqual(len(seals), 3)
        self.assertEqual({x.material_code for x in seals}, {"ACB606", "AC0002"})

    def test_two_leaf_panel_scales_each_seal_per_leaf(self):
        result = calculate_gr(door(width_mm=1600, leaf_count=2))
        self.assertEqual(result.unit_cost, 2277.196098)
        seals = {x.role: x for x in result.unit_bom if x.category == "VEDAÇÕES"}
        self.assertEqual(seals["GLASS_OR_LAMBRI_SEAL"].length_mm, 4954.0)
        self.assertEqual(seals["GLASS_OR_LAMBRI_SEAL"].quantity_per_unit, 2.0)
        self.assertEqual(seals["ROUND_SEAL_LEAF"].length_mm, 5642.0)
        self.assertEqual(seals["ROUND_SEAL_LEAF"].quantity_per_unit, 2.0)
        self.assertEqual(seals["ROUND_SEAL_FRAME"].quantity_per_unit, 2.0)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 53.9432)

    def test_glass_door_geometry_baguette_glass_and_seals_are_frozen(self):
        result = calculate_gr(glass_door())
        self.assertEqual(result.model_description, "PORTA 1 FOLHA DE GIRO")
        self.assertEqual(result.geometry["glass_bead_width_mm"], 564.0)
        self.assertEqual(result.geometry["glass_bead_height_mm"], 1891.0)
        self.assertEqual(result.geometry["glass_width_mm"], 556.0)
        self.assertEqual(result.geometry["glass_height_mm"], 1883.0)
        self.assertNotIn("panel_fill_strip_quantity", result.geometry)

        bead_codes = {x.material_code for x in result.unit_bom if x.role in {"GLASS_BEAD_WIDTH", "GLASS_BEAD_HEIGHT"}}
        self.assertEqual(bead_codes, {"BA3518"})
        self.assertNotIn("DE20150", {x.material_code for x in result.unit_bom})

        glass = next(x for x in result.unit_bom if x.role == "GLASS_PANEL")
        self.assertEqual(glass.material_code, "6TI")
        self.assertEqual(glass.width_mm, 556.0)
        self.assertEqual(glass.height_mm, 1883.0)
        self.assertEqual(glass.area_m2, 1.046948)
        self.assertEqual(glass.cost_per_unit_product, 130.8685)

        self.assertEqual(len(result.glass_panels), 1)
        self.assertEqual(result.glass_panels[0].material_code, "6TI")
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 26.7516)
        self.assertEqual(result.unit_cost, 1358.19195)

    def test_glass_baguette_changes_with_thickness(self):
        thin = calculate_gr(glass_door(glass_description="06mm TEMPERADO INCOLOR"))
        thick = calculate_gr(glass_door(glass_description="08mm TEMPERADO INCOLOR"))
        thin_codes = {x.material_code for x in thin.unit_bom if x.role.startswith("GLASS_BEAD")}
        thick_codes = {x.material_code for x in thick.unit_bom if x.role.startswith("GLASS_BEAD")}
        self.assertEqual(thin_codes, {"BA3518"})
        self.assertEqual(thick_codes, {"BA3218"})

    def test_glass_scope_is_deliberately_narrow(self):
        with self.assertRaises(ValueError):
            calculate_gr(glass_door(leaf_count=2))
        with self.assertRaises(ValueError):
            calculate_gr(window(panel_mode="VIDRO INTEIRO", glass_description="06mm TEMPERADO INCOLOR"))
        with self.assertRaises(ValueError):
            calculate_gr(glass_door(glass_description=None))
        with self.assertRaises(ValueError):
            calculate_gr(door(glass_description="06mm TEMPERADO INCOLOR"))

    def test_quantity_scales_bom_but_not_unit_cost(self):
        one = calculate_gr(glass_door(quantity=1))
        three = calculate_gr(glass_door(quantity=3))
        self.assertEqual(one.unit_cost, three.unit_cost)
        for item in three.unit_bom:
            self.assertEqual(item.quantity_order, item.quantity_per_unit * 3)

    def test_all_v06_costs_equal_exact_bom_sum(self):
        cases = [
            door(),
            door(closure_mode=MULTI),
            door(leaf_system=EXTERNAL),
            door(width_mm=1600, leaf_count=2),
            window(),
            glass_door(),
            glass_door(leaf_system=EXTERNAL, closure_mode=MULTI),
        ]
        for cfg in cases:
            with self.subTest(cfg=cfg):
                result = calculate_gr(cfg)
                self.assertEqual(result.unit_cost, round(sum(x.cost_per_unit_product for x in result.unit_bom), 6))
                self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)

    def test_golden_v06_is_frozen(self):
        golden = json.loads((ROOT / "test_cases" / "gr_golden_v0_6.json").read_text(encoding="utf-8"))
        self.assertEqual(golden["engine_version"], "GR_ENGINE_0.6.0")
        for case in golden["cases"]:
            with self.subTest(case=case["id"]):
                result = calculate_gr(GrConfiguration(**case["input"]))
                self.assertEqual(result.calculation_version, golden["engine_version"])
                self.assertEqual(result.unit_cost, case["unit_cost"])
                for key, expected in case["geometry"].items():
                    self.assertEqual(result.geometry[key], expected)
                self.assertEqual(result.cost_breakdown["VEDAÇÕES"], case["sealing_cost"])


if __name__ == "__main__":
    unittest.main()
