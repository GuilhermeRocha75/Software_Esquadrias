import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import ShutterConfiguration, ShutterMode  # noqa: E402
from esquadrias_engine.gr_v12 import GrConfiguration, calculate_gr  # noqa: E402

WINDOW = "FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN"
WINDOW_CREMONA = "MAÇANETA COM CREMONA SEM CHAVE"
CREMONA_800 = "CREMONA 2 PONTOS COMP. 800mm E:15mm"


def automated(mode: ShutterMode, **overrides):
    values = {
        "width_mm": 800,
        "height_mm": 1800,
        "quantity": 1,
        "leaf_count": 1,
        "leaf_system": WINDOW,
        "application": "JANELA",
        "panel_mode": "VIDRO INTEIRO",
        "glass_description": "06mm TEMPERADO INCOLOR",
        "closure_mode": WINDOW_CREMONA,
        "cremona_description": CREMONA_800,
        "hinge_description": "DOBRADIÇA 90MM",
        "shutter": ShutterConfiguration(
            mode=mode,
            box_description="CAIXA DE 200MM",
            slat_description="TALA DE PVC 40MM",
        ),
    }
    values.update(overrides)
    return GrConfiguration(**values)


class GrPhase12Tests(unittest.TestCase):
    def test_version_is_v012(self):
        for mode in (ShutterMode.REMOTE_SINGLE, ShutterMode.BUTTON_SINGLE):
            self.assertEqual(
                calculate_gr(automated(mode)).calculation_version,
                "GR_ENGINE_0.12.0",
            )

    def test_orcs_11417_remote_single_golden(self):
        result = calculate_gr(automated(ShutterMode.REMOTE_SINGLE))
        self.assertEqual(
            result.model_description,
            "JANELA 1 FOLHA DE GIRO COM PERSIANA AUTOMATIZADA CONTROLE REMOTO",
        )
        self.assertEqual(result.geometry["shutter_main_opening_height_mm"], 1600.0)
        self.assertEqual(result.geometry["leaf_width_final_mm"], 736.0)
        self.assertEqual(result.geometry["leaf_height_final_mm"], 1536.0)
        self.assertEqual(result.geometry["glass_width_mm"], 608.0)
        self.assertEqual(result.geometry["glass_height_mm"], 1408.0)
        self.assertEqual(result.geometry["shutter_slat_quantity"], 45.0)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 21.856)
        self.assertEqual(result.cost_breakdown["PERSIANA"], 1073.83925)
        self.assertEqual(result.unit_cost, 2034.04641)
        motor = next(x for x in result.unit_bom if x.role == "SHUTTER_MOTOR")
        self.assertEqual(motor.material_code, "MOT1")
        self.assertEqual(motor.unit_price, 500.0)

    def test_orcs_12395_button_single_golden_and_motor_fix(self):
        result = calculate_gr(automated(
            ShutterMode.BUTTON_SINGLE,
            width_mm=300,
            height_mm=1200,
            glass_description="04mm FLOAT INCOLOR",
        ))
        self.assertEqual(
            result.model_description,
            "JANELA 1 FOLHA DE GIRO COM PERSIANA AUTOMATIZADA BOTOEIRA",
        )
        self.assertEqual(result.geometry["shutter_main_opening_height_mm"], 1000.0)
        self.assertEqual(result.geometry["leaf_width_final_mm"], 236.0)
        self.assertEqual(result.geometry["leaf_height_final_mm"], 936.0)
        self.assertEqual(result.geometry["glass_width_mm"], 108.0)
        self.assertEqual(result.geometry["glass_height_mm"], 808.0)
        self.assertEqual(result.geometry["shutter_slat_quantity"], 30.0)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 10.856)
        self.assertEqual(result.cost_breakdown["PERSIANA"], 574.08925)
        self.assertEqual(result.unit_cost, 1128.45121)
        motor = next(x for x in result.unit_bom if x.role == "SHUTTER_MOTOR")
        self.assertEqual(motor.material_code, "MOT2")
        self.assertEqual(motor.unit_price, 250.0)
        warnings = {x.code for x in result.warnings}
        self.assertIn("LEGACY-GR-SHUTTER-BUTTON-MOTOR-CORRECTED", warnings)

    def test_automated_single_has_motor_side_kit_not_manual_pulley_kit(self):
        result = calculate_gr(automated(ShutterMode.REMOTE_SINGLE))
        roles = {x.role for x in result.unit_bom if x.category == "PERSIANA"}
        self.assertIn("SHUTTER_MOTOR_COVER", roles)
        self.assertIn("SHUTTER_MOTOR_PLATE", roles)
        self.assertIn("SHUTTER_MOTOR", roles)
        self.assertNotIn("SHUTTER_PULLEY_PLATE", roles)
        self.assertNotIn("SHUTTER_PULLEY", roles)
        self.assertNotIn("SHUTTER_RECESSED_WINDER", roles)
        self.assertNotIn("SHUTTER_FRONT_PIN", roles)

    def test_remote_minus_button_cost_is_exact_motor_delta(self):
        remote = calculate_gr(automated(ShutterMode.REMOTE_SINGLE))
        button = calculate_gr(automated(ShutterMode.BUTTON_SINGLE))
        self.assertEqual(
            round(remote.unit_cost - button.unit_cost, 6),
            250.0,
        )
        self.assertEqual(
            round(remote.cost_breakdown["PERSIANA"] - button.cost_breakdown["PERSIANA"], 6),
            250.0,
        )

    def test_manual_v011_regression_is_preserved(self):
        cfg = automated(ShutterMode.MANUAL_SINGLE)
        result = calculate_gr(cfg)
        self.assertEqual(result.calculation_version, "GR_ENGINE_0.12.0")
        # Mesmo input da janela, mas kit manual.
        self.assertNotIn(
            "SHUTTER_MOTOR",
            {x.role for x in result.unit_bom},
        )

    def test_double_panel_modes_remain_blocked(self):
        for mode in (
            ShutterMode.MANUAL_DOUBLE_SHARED_SHAFT,
            ShutterMode.MANUAL_DOUBLE_INDEPENDENT_SHAFTS,
            ShutterMode.BUTTON_DOUBLE,
            ShutterMode.REMOTE_DOUBLE,
        ):
            with self.subTest(mode=mode):
                with self.assertRaises(ValueError):
                    calculate_gr(automated(mode))

    def test_cost_is_exact_sum_of_bom(self):
        for mode in (ShutterMode.REMOTE_SINGLE, ShutterMode.BUTTON_SINGLE):
            result = calculate_gr(automated(mode))
            self.assertEqual(
                result.unit_cost,
                round(sum(x.cost_per_unit_product for x in result.unit_bom), 6),
            )
            self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)

    def test_golden_v012_is_frozen(self):
        golden = json.loads(
            (ROOT / "test_cases" / "gr_golden_v0_12.json").read_text(encoding="utf-8")
        )
        self.assertEqual(golden["engine_version"], "GR_ENGINE_0.12.0")
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
