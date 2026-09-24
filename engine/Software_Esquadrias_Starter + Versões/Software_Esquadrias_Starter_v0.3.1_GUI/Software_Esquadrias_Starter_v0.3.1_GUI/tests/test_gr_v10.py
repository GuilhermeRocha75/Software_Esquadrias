import json
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine.gr_v10 import GrConfiguration, calculate_gr  # noqa: E402

MIXED = "SUPERIOR VIDRO/INFERIOR PAINEL"
INTERNAL = "FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN"
EXTERNAL = "FOLHA DE PORTA ABERTURA EXTERNA 60X104MM - DESIGN"
MONO = "MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE"
MULTI = "MAÇANETA DUPLA COM FECHADURA MULTIPONTO E CHAVE"


def mixed(**overrides):
    values = {
        "width_mm": 800,
        "height_mm": 2100,
        "quantity": 1,
        "leaf_count": 1,
        "leaf_system": INTERNAL,
        "application": "PORTA",
        "panel_mode": MIXED,
        "glass_description": "04mm FLOAT INCOLOR",
        "mixed_split_from_bottom_mm": 900,
        "closure_mode": MONO,
        "hinge_description": "DOBRADIÇA 90MM",
    }
    values.update(overrides)
    return GrConfiguration(**values)


class GrPhase10Tests(unittest.TestCase):
    def test_version_is_v010(self):
        self.assertEqual(calculate_gr(mixed()).calculation_version, "GR_ENGINE_0.10.0")

    def test_orcs_270_geometry_and_physical_cost_are_frozen(self):
        result = calculate_gr(mixed())
        self.assertEqual(result.model_description, "PORTA 1 FOLHA DE GIRO SUPERIOR VIDRO / INFERIOR PAINEL")
        self.assertEqual(result.geometry["leaf_width_final_mm"], 736.0)
        self.assertEqual(result.geometry["leaf_height_final_mm"], 2063.0)
        self.assertEqual(result.geometry["mixed_split_from_bottom_mm"], 900.0)
        self.assertEqual(result.geometry["mixed_common_bead_width_mm"], 564.0)
        self.assertEqual(result.geometry["upper_glass_bead_height_mm"], 1041.0)
        self.assertEqual(result.geometry["lower_panel_bead_height_mm"], 778.0)
        self.assertEqual(result.geometry["horizontal_transom_length_mm"], 576.0)
        self.assertEqual(result.geometry["glass_width_mm"], 556.0)
        self.assertEqual(result.geometry["glass_height_mm"], 1033.0)
        self.assertEqual(result.geometry["panel_fill_strip_quantity"], 5.557143)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 28.5228)
        self.assertEqual(result.unit_cost, 1368.725685)

    def test_orcs_285_multipoint_is_frozen(self):
        result = calculate_gr(mixed(
            width_mm=900,
            mixed_split_from_bottom_mm=1050,
            glass_description="06mm TEMPERADO INCOLOR",
            closure_mode=MULTI,
        ))
        self.assertEqual(result.geometry["mixed_common_bead_width_mm"], 664.0)
        self.assertEqual(result.geometry["upper_glass_bead_height_mm"], 891.0)
        self.assertEqual(result.geometry["lower_panel_bead_height_mm"], 928.0)
        self.assertEqual(result.geometry["horizontal_transom_length_mm"], 676.0)
        self.assertEqual(result.geometry["glass_width_mm"], 656.0)
        self.assertEqual(result.geometry["glass_height_mm"], 883.0)
        self.assertEqual(result.geometry["panel_fill_strip_quantity"], 6.628571)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 29.8828)
        self.assertEqual(result.unit_cost, 1524.181563)

    def test_orcs_3560_two_leaf_is_frozen(self):
        result = calculate_gr(mixed(
            width_mm=1670,
            height_mm=2050,
            leaf_count=2,
            mixed_split_from_bottom_mm=510,
            glass_description="06mm TEMPERADO INCOLOR",
        ))
        self.assertEqual(result.model_description, "PORTA 2 FOLHAS DE GIRO SUPERIOR VIDRO / INFERIOR PAINEL")
        self.assertEqual(result.geometry["leaf_width_final_mm"], 793.0)
        self.assertEqual(result.geometry["leaf_height_final_mm"], 2013.0)
        self.assertEqual(result.geometry["mixed_common_bead_width_mm"], 621.0)
        self.assertEqual(result.geometry["upper_glass_bead_height_mm"], 1381.0)
        self.assertEqual(result.geometry["lower_panel_bead_height_mm"], 388.0)
        self.assertEqual(result.geometry["glass_width_mm"], 613.0)
        self.assertEqual(result.geometry["glass_height_mm"], 1373.0)
        self.assertEqual(result.geometry["panel_fill_strip_quantity"], 5.542857)
        self.assertEqual(result.geometry["glass_panel_count"], 2.0)
        self.assertEqual(result.geometry["transom_count"], 2.0)
        self.assertEqual(result.geometry["transom_reinforcement_screws_added"], 4.0)
        self.assertEqual(result.cost_breakdown["VEDAÇÕES"], 57.596)
        self.assertEqual(result.unit_cost, 2353.000615)

    def test_transom_and_reinforcement_are_one_per_leaf(self):
        one = calculate_gr(mixed())
        two = calculate_gr(mixed(width_mm=1670, height_mm=2050, leaf_count=2,
                                 mixed_split_from_bottom_mm=510,
                                 glass_description="06mm TEMPERADO INCOLOR"))
        for result, expected in [(one, 1.0), (two, 2.0)]:
            transom = next(x for x in result.unit_bom if x.role == "MIXED_HORIZONTAL_TRANSOM")
            reinforcement = next(
                x for x in result.unit_bom
                if x.role == "MIXED_HORIZONTAL_TRANSOM_REINFORCEMENT"
            )
            self.assertEqual(transom.material_code, "DE6072")
            self.assertEqual(reinforcement.material_code, "RAG - DE6072")
            self.assertEqual(transom.quantity_per_unit, expected)
            self.assertEqual(reinforcement.quantity_per_unit, expected)
            self.assertEqual(len(result.transoms), 1)
            self.assertEqual(result.transoms[0].quantity, expected)

    def test_par2_adds_ceil_one_screw_each_400mm_per_transom(self):
        result = calculate_gr(mixed())
        screws = next(x for x in result.unit_bom if x.role == "REINFORCEMENT_SCREWS")
        # Base v0.9 = 34.104; travessa 576 mm => ceil(576/400)=2.
        self.assertAlmostEqual(screws.quantity_per_unit, 36.104, places=9)
        self.assertEqual(result.geometry["transom_reinforcement_screws_added"], 2.0)
        warnings = {x.code for x in result.warnings}
        self.assertIn("LEGACY-GR-TRANSOM-REINFORCEMENT-SCREWS-CORRECTED", warnings)

    def test_split_is_flexible_and_measured_from_finished_leaf_bottom(self):
        lower = calculate_gr(mixed(mixed_split_from_bottom_mm=800))
        higher = calculate_gr(mixed(mixed_split_from_bottom_mm=1000))
        self.assertEqual(lower.geometry["mixed_split_from_bottom_mm"], 800.0)
        self.assertEqual(higher.geometry["mixed_split_from_bottom_mm"], 1000.0)
        self.assertEqual(
            higher.geometry["lower_panel_bead_height_mm"] - lower.geometry["lower_panel_bead_height_mm"],
            200.0,
        )
        self.assertEqual(
            lower.geometry["upper_glass_bead_height_mm"] - higher.geometry["upper_glass_bead_height_mm"],
            200.0,
        )

    def test_glass_and_panel_have_separate_baguettes_and_same_seal_family(self):
        result = calculate_gr(mixed())
        codes = {x.material_code for x in result.unit_bom}
        self.assertIn("BA3518", codes)
        self.assertIn("BA2516", codes)
        self.assertIn("DE20150", codes)
        self.assertIn("4FI", codes)
        upper = next(x for x in result.unit_bom if x.role == "UPPER_GLASS_SEAL")
        lower = next(x for x in result.unit_bom if x.role == "LOWER_LAMBRI_SEAL")
        self.assertEqual(upper.material_code, "ACB606")
        self.assertEqual(lower.material_code, "ACB606")

    def test_four_squaring_blocks_remain_per_leaf(self):
        one = calculate_gr(mixed())
        two = calculate_gr(mixed(width_mm=1670, height_mm=2050, leaf_count=2,
                                 mixed_split_from_bottom_mm=510,
                                 glass_description="06mm TEMPERADO INCOLOR"))
        self.assertEqual(
            next(x for x in one.unit_bom if x.role == "SQUARING_BLOCK").quantity_per_unit,
            4.0,
        )
        self.assertEqual(
            next(x for x in two.unit_bom if x.role == "SQUARING_BLOCK").quantity_per_unit,
            8.0,
        )

    def test_external_opening_reuses_only_external_leaf_profile(self):
        internal = calculate_gr(mixed())
        external = calculate_gr(mixed(leaf_system=EXTERNAL))
        internal_codes = {x.material_code for x in internal.unit_bom}
        external_codes = {x.material_code for x in external.unit_bom}
        self.assertIn("DE60104", internal_codes)
        self.assertNotIn("DE60104-E", internal_codes)
        self.assertIn("DE60104-E", external_codes)
        self.assertNotIn("DE60104", external_codes)
        for key in (
            "mixed_common_bead_width_mm",
            "upper_glass_bead_height_mm",
            "lower_panel_bead_height_mm",
            "horizontal_transom_length_mm",
            "glass_width_mm",
            "glass_height_mm",
        ):
            self.assertEqual(internal.geometry[key], external.geometry[key])

    def test_impossible_split_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_gr(mixed(mixed_split_from_bottom_mm=100))
        with self.assertRaises(ValueError):
            calculate_gr(mixed(mixed_split_from_bottom_mm=2000))

    def test_split_field_is_rejected_outside_mixed_mode(self):
        with self.assertRaises(ValueError):
            calculate_gr(GrConfiguration(
                width_mm=900,
                height_mm=2100,
                mixed_split_from_bottom_mm=900,
            ))

    def test_cost_is_exact_sum_of_bom(self):
        for cfg in [
            mixed(),
            mixed(width_mm=900, mixed_split_from_bottom_mm=1050,
                  glass_description="06mm TEMPERADO INCOLOR", closure_mode=MULTI),
            mixed(width_mm=1670, height_mm=2050, leaf_count=2,
                  mixed_split_from_bottom_mm=510,
                  glass_description="06mm TEMPERADO INCOLOR"),
        ]:
            result = calculate_gr(cfg)
            self.assertEqual(
                result.unit_cost,
                round(sum(x.cost_per_unit_product for x in result.unit_bom), 6),
            )
            self.assertEqual(result.cost_breakdown["TOTAL"], result.unit_cost)

    def test_golden_v010_is_frozen(self):
        golden = json.loads(
            (ROOT / "test_cases" / "gr_golden_v0_10.json").read_text(encoding="utf-8")
        )
        self.assertEqual(golden["engine_version"], "GR_ENGINE_0.10.0")
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
