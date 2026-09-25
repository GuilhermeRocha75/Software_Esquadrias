import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import ShutterConfiguration, ShutterMode  # noqa: E402
from esquadrias_engine.gr_v14 import GrConfiguration, calculate_gr  # noqa: E402

INTERNAL = "FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN"
EXTERNAL = "FOLHA DE PORTA ABERTURA EXTERNA 60X104MM - DESIGN"
MONO = "MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE"


def panel_screen(**overrides):
    values = {
        "width_mm": 900,
        "height_mm": 2100,
        "quantity": 1,
        "leaf_count": 1,
        "leaf_system": EXTERNAL,
        "application": "PORTA",
        "panel_mode": "PAINEL COMPLETO",
        "closure_mode": MONO,
        "hinge_description": "DOBRADIÇA 90MM",
        "screen_enabled": True,
    }
    values.update(overrides)
    return GrConfiguration(**values)


def shutter_screen(**overrides):
    values = {
        "width_mm": 870,
        "height_mm": 2160,
        "quantity": 1,
        "leaf_count": 1,
        "leaf_system": INTERNAL,
        "application": "PORTA",
        "panel_mode": "VIDRO INTEIRO",
        "glass_description": "06mm TEMPERADO INCOLOR",
        "closure_mode": MONO,
        "hinge_description": "DOBRADIÇA 90MM",
        "screen_enabled": True,
        "shutter": ShutterConfiguration(
            mode=ShutterMode.MANUAL_SINGLE,
            box_description="CAIXA DE 200MM",
            slat_description="TALA DE PVC 40MM",
        ),
    }
    values.update(overrides)
    return GrConfiguration(**values)


class GrPhase14Tests(unittest.TestCase):
    def test_version_is_v014(self):
        self.assertEqual(
            calculate_gr(panel_screen()).calculation_version,
            "GR_ENGINE_0.14.0",
        )

    def test_orcs_9894_screen_price_and_total_are_frozen(self):
        result = calculate_gr(panel_screen())
        self.assertEqual(result.geometry["screen_width_mm"], 900.0)
        self.assertEqual(result.geometry["screen_height_mm"], 2100.0)
        self.assertEqual(result.geometry["screen_panel_count"], 1.0)
        self.assertEqual(result.cost_breakdown["TELA"], 440.0)
        self.assertEqual(result.unit_cost, 1849.391705)
        screen = next(x for x in result.unit_bom if x.role == "RETRACTABLE_SCREEN_ASSEMBLY")
        self.assertEqual(screen.material_code, "TL3")
        self.assertEqual(screen.width_mm, 900.0)
        self.assertEqual(screen.height_mm, 2100.0)
        self.assertEqual(screen.unit_price, 440.0)
        self.assertEqual(screen.cost_per_unit_product, 440.0)

    def test_screen_formula_is_110_per_meter_each_axis_plus_110_fixed(self):
        result = calculate_gr(panel_screen(width_mm=1000, height_mm=2000))
        screen = next(x for x in result.unit_bom if x.role == "RETRACTABLE_SCREEN_ASSEMBLY")
        self.assertEqual(screen.cost_per_unit_product, 440.0)

    def test_screen_with_shutter_uses_frame_height_below_200mm_box(self):
        result = calculate_gr(shutter_screen())
        self.assertEqual(result.geometry["overall_height_mm"], 2160.0)
        self.assertEqual(result.geometry["frame_height_final_mm"], 1960.0)
        self.assertEqual(result.geometry["screen_width_mm"], 870.0)
        self.assertEqual(result.geometry["screen_height_mm"], 1960.0)
        self.assertEqual(result.cost_breakdown["TELA"], 421.3)
        self.assertEqual(result.unit_cost, 2471.29025)

    def test_screen_does_not_change_base_engineering_geometry_or_non_screen_cost(self):
        with_screen = calculate_gr(panel_screen())
        without_screen = calculate_gr(panel_screen(screen_enabled=False))
        for key in (
            "frame_width_final_mm",
            "frame_height_final_mm",
            "leaf_width_final_mm",
            "leaf_height_final_mm",
            "panel_bead_width_mm",
            "panel_bead_height_mm",
        ):
            self.assertEqual(with_screen.geometry[key], without_screen.geometry[key])
        self.assertEqual(
            round(with_screen.unit_cost - without_screen.unit_cost, 6),
            440.0,
        )

    def test_screen_is_one_assembly_even_for_two_leaf_supported_door(self):
        result = calculate_gr(panel_screen(
            width_mm=1600,
            height_mm=2100,
            leaf_count=2,
            leaf_system=INTERNAL,
        ))
        screen = next(x for x in result.unit_bom if x.role == "RETRACTABLE_SCREEN_ASSEMBLY")
        self.assertEqual(screen.quantity_per_unit, 1.0)
        self.assertEqual(result.geometry["screen_panel_count"], 1.0)
        self.assertEqual(screen.width_mm, 1600.0)
        self.assertEqual(screen.height_mm, 2100.0)

    def test_quantity_scales_screen_order_quantity_only(self):
        result = calculate_gr(panel_screen(quantity=3))
        screen = next(x for x in result.unit_bom if x.role == "RETRACTABLE_SCREEN_ASSEMBLY")
        self.assertEqual(screen.quantity_per_unit, 1.0)
        self.assertEqual(screen.quantity_order, 3.0)
        self.assertEqual(result.cost_breakdown["TELA"], 440.0)

    def test_legacy_reference_warning_is_present(self):
        result = calculate_gr(panel_screen())
        warnings = {x.code for x in result.warnings}
        self.assertIn("LEGACY-GR-SCREEN-REFERENCE-CORRECTED", warnings)

    def test_no_screen_preserves_v013_total(self):
        result = calculate_gr(GrConfiguration(
            width_mm=2550,
            height_mm=2260,
            quantity=1,
            leaf_count=2,
            leaf_system=INTERNAL,
            application="PORTA",
            panel_mode="VIDRO INTEIRO",
            glass_description="06mm TEMPERADO INCOLOR",
            closure_mode=MONO,
            hinge_description="DOBRADIÇA 90MM",
            shutter=ShutterConfiguration(
                mode=ShutterMode.MANUAL_DOUBLE_INDEPENDENT_SHAFTS,
                box_description="CAIXA DE 200MM",
                slat_description="TALA DE PVC 40MM",
            ),
        ))
        self.assertEqual(result.calculation_version, "GR_ENGINE_0.14.0")
        self.assertEqual(result.unit_cost, 4503.65075)

    def test_cost_is_exact_sum_of_bom(self):
        for cfg in (panel_screen(), shutter_screen()):
            result = calculate_gr(cfg)
            self.assertEqual(
                result.unit_cost,
                round(sum(x.cost_per_unit_product for x in result.unit_bom), 6),
            )
            self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)

    def test_golden_v014_is_frozen(self):
        golden = json.loads(
            (ROOT / "test_cases" / "gr_golden_v0_14.json").read_text(encoding="utf-8")
        )
        self.assertEqual(golden["engine_version"], "GR_ENGINE_0.14.0")
        for case in golden["cases"]:
            with self.subTest(case=case["id"]):
                raw = dict(case["input"])
                if raw.get("shutter") is not None:
                    raw["shutter"] = ShutterConfiguration(
                        mode=ShutterMode(raw["shutter"]["mode"]),
                        box_description=raw["shutter"]["box_description"],
                        slat_description=raw["shutter"]["slat_description"],
                    )
                result = calculate_gr(GrConfiguration(**raw))
                self.assertEqual(result.calculation_version, golden["engine_version"])
                self.assertEqual(result.unit_cost, case["unit_cost"])
                self.assertEqual(result.cost_breakdown["TELA"], case["screen_cost"])
                for key, expected in case["geometry"].items():
                    self.assertEqual(result.geometry[key], expected)


if __name__ == "__main__":
    unittest.main()
