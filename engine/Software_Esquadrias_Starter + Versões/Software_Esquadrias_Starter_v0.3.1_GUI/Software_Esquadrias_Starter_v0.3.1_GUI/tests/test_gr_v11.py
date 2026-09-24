import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import (  # noqa: E402
    GrConfiguration,
    ShutterConfiguration,
    ShutterMode,
    calculate_gr,
)

INTERNAL = "FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN"
WINDOW = "FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN"
MONO = "MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE"
WINDOW_CREMONA = "MAÇANETA COM CREMONA SEM CHAVE"
CREMONA_800 = "CREMONA 2 PONTOS COMP. 800mm E:15mm"


def manual_shutter():
    return ShutterConfiguration(
        mode=ShutterMode.MANUAL_SINGLE,
        box_description="CAIXA DE 200MM",
        slat_description="TALA DE PVC 40MM",
    )


def door(**overrides):
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
        "shutter": manual_shutter(),
    }
    values.update(overrides)
    return GrConfiguration(**values)


def window(**overrides):
    values = {
        "width_mm": 500,
        "height_mm": 1100,
        "quantity": 1,
        "leaf_count": 1,
        "leaf_system": WINDOW,
        "application": "JANELA",
        "panel_mode": "VIDRO INTEIRO",
        "glass_description": "06mm TEMPERADO INCOLOR",
        "closure_mode": WINDOW_CREMONA,
        "cremona_description": CREMONA_800,
        "hinge_description": "DOBRADIÇA 90MM",
        "shutter": manual_shutter(),
    }
    values.update(overrides)
    return GrConfiguration(**values)


class GrPhase11Tests(unittest.TestCase):
    def test_version_is_v011(self):
        self.assertEqual(calculate_gr(door()).calculation_version, "GR_ENGINE_0.11.0")
        self.assertEqual(calculate_gr(window()).calculation_version, "GR_ENGINE_0.11.0")

    def test_orcs_18132_door_golden(self):
        result = calculate_gr(door())
        self.assertEqual(result.model_description, "PORTA 1 FOLHA DE GIRO COM PERSIANA")
        self.assertEqual(result.geometry["overall_height_mm"], 2160.0)
        self.assertEqual(result.geometry["shutter_main_opening_height_mm"], 1960.0)
        self.assertEqual(result.geometry["leaf_width_final_mm"], 806.0)
        self.assertEqual(result.geometry["leaf_height_final_mm"], 1923.0)
        self.assertEqual(result.geometry["glass_width_mm"], 626.0)
        self.assertEqual(result.geometry["glass_height_mm"], 1743.0)
        self.assertEqual(result.geometry["shutter_box_length_mm"], 855.0)
        self.assertEqual(result.geometry["shutter_side_guide_length_mm"], 1960.0)
        self.assertEqual(result.geometry["shutter_slat_width_mm"], 796.0)
        self.assertEqual(result.geometry["shutter_slat_quantity"], 54.0)
        self.assertEqual(result.geometry["shutter_shaft_length_mm"], 830.0)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 26.0516)
        self.assertEqual(result.cost_breakdown["PERSIANA"], 706.53125)
        self.assertEqual(result.unit_cost, 2049.99025)

    def test_orcs_11111_window_golden_and_fractional_slat_fix(self):
        result = calculate_gr(window())
        self.assertEqual(result.model_description, "JANELA 1 FOLHA DE GIRO COM PERSIANA")
        self.assertEqual(result.geometry["overall_height_mm"], 1100.0)
        self.assertEqual(result.geometry["shutter_main_opening_height_mm"], 900.0)
        self.assertEqual(result.geometry["leaf_width_final_mm"], 436.0)
        self.assertEqual(result.geometry["leaf_height_final_mm"], 836.0)
        self.assertEqual(result.geometry["glass_width_mm"], 308.0)
        self.assertEqual(result.geometry["glass_height_mm"], 708.0)
        self.assertEqual(result.geometry["shutter_slat_quantity"], 28.0)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 11.856)
        self.assertEqual(result.cost_breakdown["PERSIANA"], 412.94925)
        self.assertEqual(result.unit_cost, 1015.78641)
        warning_codes = {x.code for x in result.warnings}
        self.assertIn("LEGACY-GR-SHUTTER-SLAT-FRACTION", warning_codes)

    def test_manual_single_uses_complete_recovered_accessory_kit(self):
        result = calculate_gr(door())
        codes = {x.material_code for x in result.unit_bom if x.category == "PERSIANA"}
        expected = {
            "321040", "327201", "326015_F", "311712", "375021",
            "370113", "371513_4", "371513_2", "375110", "375213",
            "375234", "375339", "373128", "375678", "375415", "375441",
        }
        self.assertEqual(codes, expected)
        self.assertNotIn("327019", codes)
        warnings = {x.code for x in result.warnings}
        self.assertIn("LEGACY-GR-SHUTTER-HELPERS-RECOVERED", warnings)
        self.assertIn("LEGACY-GR-SHUTTER-SUBTOTAL-CORRECTED", warnings)

    def test_manual_single_accessory_quantities_match_homologated_cr_kit(self):
        result = calculate_gr(door())
        expected = {
            "SHUTTER_LATERAL_COVER": 2.0,
            "SHUTTER_PULLEY_PLATE": 1.0,
            "SHUTTER_END_PLATE": 1.0,
            "SHUTTER_PULLEY": 1.0,
            "SHUTTER_END_CAP": 1.0,
            "SHUTTER_END_CAP_ADAPTER": 1.0,
            "SHUTTER_RECESSED_WINDER": 1.0,
            "SHUTTER_GUIDE_INVITATION_PAIR": 1.0,
            "SHUTTER_FIRST_SLAT_COUPLING": 2.0,
            "SHUTTER_FRONT_PIN": 1.0,
            "SHUTTER_OPENING_LIMITER": 2.0,
        }
        by_role = {x.role: x for x in result.unit_bom}
        for role, quantity in expected.items():
            with self.subTest(role=role):
                self.assertEqual(by_role[role].quantity_per_unit, quantity)

    def test_box_reserves_200mm_only_from_main_frame_not_finishes(self):
        result = calculate_gr(door())
        self.assertEqual(result.geometry["frame_height_final_mm"], 1960.0)
        internal = next(x for x in result.unit_bom if x.role == "INTERNAL_FINISH_HEIGHT")
        external = next(x for x in result.unit_bom if x.role == "EXTERNAL_FINISH_HEIGHT")
        self.assertEqual(internal.length_mm, 2300.0)
        self.assertEqual(external.length_mm, 2220.0)

    def test_quantity_scales_order_bom_only(self):
        one = calculate_gr(door(quantity=1))
        three = calculate_gr(door(quantity=3))
        self.assertEqual(one.unit_cost, three.unit_cost)
        for item in three.unit_bom:
            self.assertEqual(item.quantity_order, item.quantity_per_unit * 3)

    def test_other_shutter_modes_remain_blocked_in_v011(self):
        for mode in (
            ShutterMode.MANUAL_DOUBLE_SHARED_SHAFT,
            ShutterMode.MANUAL_DOUBLE_INDEPENDENT_SHAFTS,
            ShutterMode.BUTTON_SINGLE,
            ShutterMode.REMOTE_SINGLE,
        ):
            with self.subTest(mode=mode):
                with self.assertRaises(ValueError):
                    calculate_gr(door(shutter=ShutterConfiguration(mode=mode)))

    def test_panel_and_mixed_modes_with_shutter_remain_blocked(self):
        with self.assertRaises(ValueError):
            calculate_gr(door(panel_mode="PAINEL COMPLETO", glass_description=None))
        with self.assertRaises(ValueError):
            calculate_gr(door(
                panel_mode="SUPERIOR VIDRO/INFERIOR PAINEL",
                mixed_split_from_bottom_mm=900,
            ))

    def test_no_shutter_preserves_v010_cost(self):
        result = calculate_gr(GrConfiguration(
            width_mm=800,
            height_mm=2100,
            leaf_count=1,
            leaf_system=INTERNAL,
            application="PORTA",
            panel_mode="SUPERIOR VIDRO/INFERIOR PAINEL",
            glass_description="04mm FLOAT INCOLOR",
            mixed_split_from_bottom_mm=900,
            closure_mode=MONO,
        ))
        self.assertEqual(result.calculation_version, "GR_ENGINE_0.11.0")
        self.assertEqual(result.unit_cost, 1368.725685)

    def test_cost_is_exact_sum_of_bom(self):
        for cfg in (door(), window()):
            result = calculate_gr(cfg)
            self.assertEqual(
                result.unit_cost,
                round(sum(x.cost_per_unit_product for x in result.unit_bom), 6),
            )
            self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)

    def test_golden_v011_is_frozen(self):
        golden = json.loads(
            (ROOT / "test_cases" / "gr_golden_v0_11.json").read_text(encoding="utf-8")
        )
        self.assertEqual(golden["engine_version"], "GR_ENGINE_0.11.0")
        for case in golden["cases"]:
            with self.subTest(case=case["id"]):
                raw = dict(case["input"])
                raw["shutter"] = ShutterConfiguration(
                    mode=ShutterMode(raw["shutter"]["mode"]),
                    box_description=raw["shutter"]["box_description"],
                    slat_description=raw["shutter"]["slat_description"],
                )
                result = calculate_gr(GrConfiguration(**raw))
                self.assertEqual(result.calculation_version, golden["engine_version"])
                self.assertEqual(result.unit_cost, case["unit_cost"])
                self.assertEqual(result.cost_breakdown["VEDAÇÕES"], case["sealing_cost"])
                self.assertEqual(result.cost_breakdown["PERSIANA"], case["shutter_cost"])
                for key, expected in case["geometry"].items():
                    self.assertEqual(result.geometry[key], expected)


if __name__ == "__main__":
    unittest.main()
