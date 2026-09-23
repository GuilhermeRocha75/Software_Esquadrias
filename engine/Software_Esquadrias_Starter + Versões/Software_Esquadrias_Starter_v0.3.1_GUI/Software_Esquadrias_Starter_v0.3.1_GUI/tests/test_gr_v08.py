import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine.gr_v08 import GrConfiguration, calculate_gr  # noqa: E402

MONO = "MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE"
WINDOW_CREMONA = "MAÇANETA COM CREMONA SEM CHAVE"
CREMONA_800 = "CREMONA 2 PONTOS COMP. 800mm E:15mm"
INTERNAL = "FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN"
WINDOW = "FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN"


def window_glass(**overrides):
    values = {
        "width_mm": 700,
        "height_mm": 2500,
        "quantity": 1,
        "leaf_count": 1,
        "leaf_system": WINDOW,
        "application": "JANELA",
        "panel_mode": "VIDRO INTEIRO",
        "glass_description": "06mm TEMPERADO INCOLOR",
        "closure_mode": WINDOW_CREMONA,
        "cremona_description": CREMONA_800,
        "hinge_description": "DOBRADIÇA 90MM",
    }
    values.update(overrides)
    return GrConfiguration(**values)


def inherited_door(**overrides):
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


class GrPhase8Tests(unittest.TestCase):
    def test_version_is_v08(self):
        self.assertEqual(calculate_gr(window_glass()).calculation_version, "GR_ENGINE_0.8.0")
        self.assertEqual(calculate_gr(inherited_door()).calculation_version, "GR_ENGINE_0.8.0")

    def test_orcs_11480_geometry_and_current_physical_cost_are_frozen(self):
        result = calculate_gr(window_glass())
        self.assertEqual(result.model_description, "JANELA 1 FOLHA DE GIRO")
        self.assertEqual(result.geometry["leaf_width_final_mm"], 636.0)
        self.assertEqual(result.geometry["leaf_height_final_mm"], 2436.0)
        self.assertEqual(result.geometry["glass_bead_width_mm"], 516.0)
        self.assertEqual(result.geometry["glass_bead_height_mm"], 2316.0)
        self.assertEqual(result.geometry["glass_width_mm"], 508.0)
        self.assertEqual(result.geometry["glass_height_mm"], 2308.0)
        self.assertEqual(result.geometry["glass_panel_count"], 1.0)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 29.856)
        self.assertEqual(result.unit_cost, 1214.70516)

    def test_window_glass_uses_90mm_hinges_and_confirmed_800mm_cremona(self):
        result = calculate_gr(window_glass())
        hinges = next(x for x in result.unit_bom if x.role == "HINGE_90MM")
        cremona = next(x for x in result.unit_bom if x.material_code == "CRE12")
        screws = next(x for x in result.unit_bom if x.role == "HARDWARE_SCREWS")
        self.assertEqual(hinges.quantity_per_unit, 3.0)
        self.assertEqual(cremona.quantity_per_unit, 1.0)
        self.assertEqual(cremona.description, CREMONA_800)
        self.assertEqual(screws.quantity_per_unit, 32.0)

    def test_window_glass_none_cremona_normalizes_to_same_800mm_baseline(self):
        explicit = calculate_gr(window_glass(cremona_description=CREMONA_800))
        implicit = calculate_gr(window_glass(cremona_description=None))
        self.assertEqual(implicit.geometry, explicit.geometry)
        self.assertEqual(implicit.cost_breakdown, explicit.cost_breakdown)
        self.assertEqual(implicit.unit_cost, explicit.unit_cost)
        self.assertIn("CRE12", {x.material_code for x in implicit.unit_bom})

    def test_6mm_window_uses_ba3518_and_physical_seals(self):
        result = calculate_gr(window_glass())
        bead_codes = {
            x.material_code
            for x in result.unit_bom
            if x.role in {"GLASS_BEAD_WIDTH", "GLASS_BEAD_HEIGHT"}
        }
        self.assertEqual(bead_codes, {"BA3518"})
        glass = next(x for x in result.unit_bom if x.role == "GLASS_PANEL")
        self.assertEqual(glass.material_code, "6TI")
        self.assertEqual(glass.width_mm, 508.0)
        self.assertEqual(glass.height_mm, 2308.0)
        self.assertEqual(glass.area_m2, 1.172464)
        self.assertEqual(glass.cost_per_unit_product, 146.558)
        seals = [x for x in result.unit_bom if x.category == "VEDAÇÕES"]
        self.assertEqual(len(seals), 3)
        self.assertEqual({x.material_code for x in seals}, {"ACB606", "AC0002"})

    def test_20mm_reference_uses_ba2018(self):
        result = calculate_gr(window_glass(
            width_mm=400,
            height_mm=1500,
            glass_description="20mm DUPLO FLOAT INCOLOR/TEMPERADO INCOLOR (4/10/6)",
        ))
        bead_codes = {
            x.material_code
            for x in result.unit_bom
            if x.role in {"GLASS_BEAD_WIDTH", "GLASS_BEAD_HEIGHT"}
        }
        self.assertEqual(bead_codes, {"BA2018"})
        self.assertEqual(result.geometry["glass_width_mm"], 208.0)
        self.assertEqual(result.geometry["glass_height_mm"], 1308.0)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 16.856)
        self.assertEqual(result.unit_cost, 765.11532)

    def test_panel_fill_is_not_present_in_window_glass_bom(self):
        result = calculate_gr(window_glass())
        codes = {x.material_code for x in result.unit_bom}
        self.assertNotIn("DE20150", codes)
        self.assertNotIn("panel_fill_strip_quantity", result.geometry)
        self.assertEqual(len(result.glass_panels), 1)
        self.assertEqual(result.glass_panels[0].material_code, "6TI")

    def test_v07_two_leaf_door_glass_is_preserved(self):
        result = calculate_gr(inherited_door())
        self.assertEqual(result.unit_cost, 2071.84485)
        self.assertEqual(result.geometry["glass_width_mm"], 378.0)
        self.assertEqual(result.geometry["glass_height_mm"], 1883.0)
        self.assertEqual(result.geometry["glass_panel_count"], 2.0)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 49.9432)

    def test_window_glass_scope_rejects_wrong_closure_or_cremona(self):
        with self.assertRaises(ValueError):
            calculate_gr(window_glass(closure_mode=MONO))
        with self.assertRaises(ValueError):
            calculate_gr(window_glass(cremona_description="CREMONA 2 PONTOS COMP. 1000mm E:15mm"))

    def test_window_glass_quantity_scales_order_bom_only(self):
        one = calculate_gr(window_glass(quantity=1))
        three = calculate_gr(window_glass(quantity=3))
        self.assertEqual(one.unit_cost, three.unit_cost)
        for item in three.unit_bom:
            self.assertEqual(item.quantity_order, item.quantity_per_unit * 3)

    def test_cost_is_exact_sum_of_bom(self):
        for cfg in [
            window_glass(),
            window_glass(width_mm=400, height_mm=1500,
                         glass_description="20mm DUPLO FLOAT INCOLOR/TEMPERADO INCOLOR (4/10/6)"),
            inherited_door(),
        ]:
            with self.subTest(cfg=cfg):
                result = calculate_gr(cfg)
                self.assertEqual(
                    result.unit_cost,
                    round(sum(item.cost_per_unit_product for item in result.unit_bom), 6),
                )
                self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)

    def test_golden_v08_is_frozen(self):
        golden = json.loads(
            (ROOT / "test_cases" / "gr_golden_v0_8.json").read_text(encoding="utf-8")
        )
        self.assertEqual(golden["engine_version"], "GR_ENGINE_0.8.0")
        for case in golden["cases"]:
            with self.subTest(case=case["id"]):
                result = calculate_gr(GrConfiguration(**case["input"]))
                self.assertEqual(result.calculation_version, golden["engine_version"])
                self.assertEqual(result.unit_cost, case["unit_cost"])
                self.assertEqual(result.cost_breakdown["VEDAÇÕES"], case["sealing_cost"])
                for key, expected in case["geometry"].items():
                    self.assertEqual(result.geometry[key], expected)


if __name__ == "__main__":
    unittest.main()
