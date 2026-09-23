import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import GrConfiguration, calculate_gr  # noqa: E402

WINDOW = "FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN"
WINDOW_CREMONA = "MAÇANETA COM CREMONA SEM CHAVE"
HINGE_OB = "DOBRADIÇA SISTEMA OB"
HINGE_90 = "DOBRADIÇA 90MM"
CREMONA_800 = "CREMONA 2 PONTOS COMP. 800mm E:15mm"
OB_400 = "CREMONA OSCILO/GIRO COMP. 400mm E:15mm"
OB_900 = "CREMONA OSCILO/GIRO COMP. 900mm E:15mm"
OB_1100 = "CREMONA OSCILO/GIRO COMP. 1100mm E:15mm"
OB_1400 = "CREMONA OSCILO/GIRO COMP. 1400mm E:15mm"
OB_1900 = "CREMONA OSCILO/GIRO COMP. 1900mm E:15mm"


def ob_window(**overrides):
    values = {
        "width_mm": 800,
        "height_mm": 1000,
        "quantity": 1,
        "leaf_count": 1,
        "leaf_system": WINDOW,
        "application": "JANELA",
        "panel_mode": "VIDRO INTEIRO",
        "glass_description": "06mm TEMPERADO INCOLOR",
        "closure_mode": WINDOW_CREMONA,
        "cremona_description": OB_1100,
        "hinge_description": HINGE_OB,
    }
    values.update(overrides)
    return GrConfiguration(**values)


def window_90(**overrides):
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
        "hinge_description": HINGE_90,
    }
    values.update(overrides)
    return GrConfiguration(**values)


class GrPhase9Tests(unittest.TestCase):
    def test_version_is_v09(self):
        self.assertEqual(calculate_gr(ob_window()).calculation_version, "GR_ENGINE_0.9.0")
        self.assertEqual(calculate_gr(window_90()).calculation_version, "GR_ENGINE_0.9.0")

    def test_orcs_4572_geometry_and_current_physical_cost_are_frozen(self):
        result = calculate_gr(ob_window())
        self.assertEqual(result.model_description, "JANELA 1 FOLHA DE GIRO")
        self.assertEqual(result.geometry["leaf_width_final_mm"], 736.0)
        self.assertEqual(result.geometry["leaf_height_final_mm"], 936.0)
        self.assertEqual(result.geometry["glass_bead_width_mm"], 616.0)
        self.assertEqual(result.geometry["glass_bead_height_mm"], 816.0)
        self.assertEqual(result.geometry["glass_width_mm"], 608.0)
        self.assertEqual(result.geometry["glass_height_mm"], 808.0)
        self.assertEqual(result.geometry["glass_panel_count"], 1.0)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 15.856)
        self.assertEqual(result.unit_cost, 656.42716)

    def test_ob_replaces_90mm_hinge_with_six_excel_components(self):
        result = calculate_gr(ob_window())
        codes = {x.material_code for x in result.unit_bom}
        self.assertNotIn("DOB3", codes)
        self.assertNotIn("CRE12", codes)
        for code in {"DOB6", "DOB7", "DOB8", "DOB9", "DOB10", "DOB11", "CRE23"}:
            self.assertIn(code, codes)
        ob_parts = [
            x for x in result.unit_bom
            if x.material_code in {"DOB6", "DOB7", "DOB8", "DOB9", "DOB10", "DOB11"}
        ]
        self.assertEqual(len(ob_parts), 6)
        self.assertTrue(all(x.quantity_per_unit == 1.0 for x in ob_parts))

    def test_ob_hardware_screws_follow_gr_g119(self):
        result = calculate_gr(ob_window())
        screws = next(x for x in result.unit_bom if x.role == "HARDWARE_SCREWS")
        self.assertEqual(screws.material_code, "PAR1")
        self.assertEqual(screws.quantity_per_unit, 16.0)
        self.assertEqual(screws.cost_per_unit_product, 2.4)

    def test_ob_requires_explicit_oscilo_giro_cremona(self):
        with self.assertRaises(ValueError):
            calculate_gr(ob_window(cremona_description=None))
        with self.assertRaises(ValueError):
            calculate_gr(ob_window(cremona_description=CREMONA_800))

    def test_all_catalog_ob_cremonas_are_explicitly_supported(self):
        expected = {
            OB_400: ("CRE21", 15.00, 653.42716),
            OB_900: ("CRE22", 17.00, 655.42716),
            OB_1100: ("CRE23", 18.00, 656.42716),
            OB_1400: ("CRE24", 20.68, 659.10716),
            OB_1900: ("CRE24", 25.52, 663.94716),
        }
        for description, (code, price, total) in expected.items():
            with self.subTest(description=description):
                result = calculate_gr(ob_window(cremona_description=description))
                cremona = next(x for x in result.unit_bom if x.role == "OB_CREMONA")
                self.assertEqual(cremona.material_code, code)
                self.assertEqual(cremona.description, description)
                self.assertEqual(cremona.unit_price, price)
                self.assertEqual(result.unit_cost, total)

    def test_ob_does_not_change_glass_or_sealing_geometry(self):
        ob = calculate_gr(ob_window())
        normal = calculate_gr(window_90(width_mm=800, height_mm=1000))
        for key in (
            "leaf_width_final_mm", "leaf_height_final_mm",
            "glass_bead_width_mm", "glass_bead_height_mm",
            "glass_width_mm", "glass_height_mm", "glass_panel_count",
        ):
            self.assertEqual(ob.geometry[key], normal.geometry[key])
        self.assertEqual(ob.cost_breakdown["VEDAÇÕES"], normal.cost_breakdown["VEDAÇÕES"])
        self.assertEqual(ob.glass_panels, normal.glass_panels)

    def test_v08_90mm_window_regression_is_preserved(self):
        result = calculate_gr(window_90())
        self.assertEqual(result.unit_cost, 1214.70516)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 29.856)
        self.assertIn("DOB3", {x.material_code for x in result.unit_bom})
        self.assertIn("CRE12", {x.material_code for x in result.unit_bom})

    def test_ob_quantity_scales_order_bom_only(self):
        one = calculate_gr(ob_window(quantity=1))
        three = calculate_gr(ob_window(quantity=3))
        self.assertEqual(one.unit_cost, three.unit_cost)
        for item in three.unit_bom:
            self.assertEqual(item.quantity_order, item.quantity_per_unit * 3)

    def test_ob_warning_documents_no_auto_sizing(self):
        result = calculate_gr(ob_window())
        codes = {x.code for x in result.warnings}
        self.assertIn("GR-OB-CREMONA-EXPLICIT", codes)

    def test_cost_is_exact_sum_of_bom(self):
        for cfg in [
            ob_window(),
            ob_window(cremona_description=OB_400),
            ob_window(cremona_description=OB_1900),
            window_90(),
        ]:
            with self.subTest(cfg=cfg):
                result = calculate_gr(cfg)
                self.assertEqual(
                    result.unit_cost,
                    round(sum(item.cost_per_unit_product for item in result.unit_bom), 6),
                )
                self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)

    def test_golden_v09_is_frozen(self):
        golden = json.loads(
            (ROOT / "test_cases" / "gr_golden_v0_9.json").read_text(encoding="utf-8")
        )
        self.assertEqual(golden["engine_version"], "GR_ENGINE_0.9.0")
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
