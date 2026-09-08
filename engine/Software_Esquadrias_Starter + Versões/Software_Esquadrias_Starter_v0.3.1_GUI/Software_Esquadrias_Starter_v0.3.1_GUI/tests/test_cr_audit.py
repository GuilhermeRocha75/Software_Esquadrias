import math
import sys
from collections import defaultdict
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import (  # noqa: E402
    ApplicationType,
    BAR_STOCK_CODES,
    LeafSystem,
    SlidingConfiguration,
    build_order_purchase_plan,
    calculate_sliding,
)


STOCK_LENGTH_MM = 5900.0

CLOSURE_WITH_HIDDEN_LATCH = "MACANETA COM CREMONA + FECHO OCULTO"
CLOSURE_WITH_HIDDEN_HANDLE = "MACANETA COM CREMONA + MACANETA OCULTA COM CREMONA"
CLOSURE_CREMONA_ONLY = "MACANETA COM CREMONA"

CREMONA_BASES = [
    "CREMONA 1 PONTO",
    "CREMONA 2 PONTOS COMP. 400MM",
    "CREMONA 2 PONTOS COMP. 600MM",
    "CREMONA 2 PONTOS COMP. 800MM",
    "CREMONA 2 PONTOS COMP. 1000MM",
    "CREMONA 2 PONTOS COMP. 1200MM",
    "CREMONA 2 PONTOS COMP. 1400MM",
    "CREMONA 2 PONTOS COMP. 1600MM",
]

SYSTEM_REFERENCE = {
    LeafSystem.PRIME_WINDOW_42x66: {
        "leaf_code": "PR4266",
        "leaf_dim_mm": 66.0,
        "glazing_rebate_mm": 50.0,
        "interlock_code": "PR4536",
        "leaf_reinforcement": "RAG - PR4266",
        "rubber": "ACB606",
        "brush": "ACE606",
        "wind_stop": "AC0012",
    },
    LeafSystem.PRIME_DOOR_42x88: {
        "leaf_code": "PR4288",
        "leaf_dim_mm": 88.0,
        "glazing_rebate_mm": 72.0,
        "interlock_code": "PR4550",
        "leaf_reinforcement": "RAG - PR4288",
        "rubber": "ACB606",
        "brush": "ACE606",
        "wind_stop": "AC0012",
    },
    LeafSystem.DESIGN_DOOR_60x111: {
        "leaf_code": "DE60111",
        "leaf_dim_mm": 111.0,
        "glazing_rebate_mm": 93.0,
        "interlock_code": "DE4109",
        "leaf_reinforcement": "RAG - DE60111",
        "rubber": "AC0708",
        "brush": "AC0710",
        "wind_stop": "AC0009",
    },
}

GLASS_REFERENCE = {
    "04mm FLOAT INCOLOR": (4.0, "4FI"),
    "05mm FLOAT FUME": (5.0, "5FF"),
    "06mm FLOAT INCOLOR": (6.0, "6FI"),
    "08mm FLOAT INCOLOR": (8.0, "8FI"),
}

ROLLER_CODES = {
    "ROLDANA 30KG": "ROL1",
    "ROLDANA 50KG": "ROL2",
    "ROLDANA 80KG": "ROL3",
    "ROLDANA 120KG": "ROL4",
    "ROLDANA 150KG": "ROL5",
}

SCENARIOS = [
    {
        "case_id": "prime_window_2f",
        "width_mm": 1500,
        "height_mm": 1200,
        "quantity": 1,
        "leaf_count": 2,
        "leaf_system": LeafSystem.PRIME_WINDOW_42x66,
        "application": ApplicationType.WINDOW,
        "glass_description": "04mm FLOAT INCOLOR",
        "closure_mode": CLOSURE_WITH_HIDDEN_LATCH,
        "cremona_base": CREMONA_BASES[0],
        "roller_description": "ROLDANA 30KG",
        "internal_finish": "SEM ACABAMENTO",
        "external_finish": "SEM ACABAMENTO",
        "screen_enabled": False,
        "shutter_enabled": False,
    },
    {
        "case_id": "prime_window_3f",
        "width_mm": 2400,
        "height_mm": 1500,
        "quantity": 2,
        "leaf_count": 3,
        "leaf_system": LeafSystem.PRIME_WINDOW_42x66,
        "application": ApplicationType.DOOR,
        "glass_description": "05mm FLOAT FUME",
        "closure_mode": CLOSURE_WITH_HIDDEN_HANDLE,
        "cremona_base": CREMONA_BASES[1],
        "roller_description": "ROLDANA 50KG",
        "internal_finish": "GUARNICAO DE 70MM",
        "external_finish": "SEM ACABAMENTO",
        "screen_enabled": False,
        "shutter_enabled": False,
    },
    {
        "case_id": "prime_window_4f",
        "width_mm": 3200,
        "height_mm": 1800,
        "quantity": 1,
        "leaf_count": 4,
        "leaf_system": LeafSystem.PRIME_WINDOW_42x66,
        "application": ApplicationType.WINDOW,
        "glass_description": "06mm FLOAT INCOLOR",
        "closure_mode": CLOSURE_CREMONA_ONLY,
        "cremona_base": CREMONA_BASES[2],
        "roller_description": "ROLDANA 80KG",
        "internal_finish": "SEM ACABAMENTO",
        "external_finish": "BARRA CHATA DE 30MM",
        "screen_enabled": True,
        "shutter_enabled": False,
    },
    {
        "case_id": "prime_window_6f",
        "width_mm": 4800,
        "height_mm": 2200,
        "quantity": 2,
        "leaf_count": 6,
        "leaf_system": LeafSystem.PRIME_WINDOW_42x66,
        "application": ApplicationType.DOOR,
        "glass_description": "08mm FLOAT INCOLOR",
        "closure_mode": CLOSURE_WITH_HIDDEN_LATCH,
        "cremona_base": CREMONA_BASES[5],
        "roller_description": "ROLDANA 120KG",
        "internal_finish": "GUARNICAO DE 70MM",
        "external_finish": "BARRA CHATA DE 30MM",
        "screen_enabled": False,
        "shutter_enabled": True,
    },
    {
        "case_id": "prime_door_2f",
        "width_mm": 1800,
        "height_mm": 2100,
        "quantity": 1,
        "leaf_count": 2,
        "leaf_system": LeafSystem.PRIME_DOOR_42x88,
        "application": ApplicationType.DOOR,
        "glass_description": "04mm FLOAT INCOLOR",
        "closure_mode": CLOSURE_WITH_HIDDEN_HANDLE,
        "cremona_base": CREMONA_BASES[3],
        "roller_description": "ROLDANA 150KG",
        "internal_finish": "GUARNICAO DE 70MM",
        "external_finish": "SEM ACABAMENTO",
        "screen_enabled": True,
        "shutter_enabled": False,
    },
    {
        "case_id": "prime_door_3f",
        "width_mm": 2700,
        "height_mm": 2300,
        "quantity": 2,
        "leaf_count": 3,
        "leaf_system": LeafSystem.PRIME_DOOR_42x88,
        "application": ApplicationType.WINDOW,
        "glass_description": "05mm FLOAT FUME",
        "closure_mode": CLOSURE_CREMONA_ONLY,
        "cremona_base": CREMONA_BASES[4],
        "roller_description": "ROLDANA 30KG",
        "internal_finish": "SEM ACABAMENTO",
        "external_finish": "BARRA CHATA DE 30MM",
        "screen_enabled": True,
        "shutter_enabled": False,
    },
    {
        "case_id": "prime_door_4f",
        "width_mm": 3600,
        "height_mm": 2400,
        "quantity": 1,
        "leaf_count": 4,
        "leaf_system": LeafSystem.PRIME_DOOR_42x88,
        "application": ApplicationType.WINDOW,
        "glass_description": "06mm FLOAT INCOLOR",
        "closure_mode": CLOSURE_WITH_HIDDEN_LATCH,
        "cremona_base": CREMONA_BASES[6],
        "roller_description": "ROLDANA 50KG",
        "internal_finish": "SEM ACABAMENTO",
        "external_finish": "SEM ACABAMENTO",
        "screen_enabled": False,
        "shutter_enabled": True,
    },
    {
        "case_id": "prime_door_6f",
        "width_mm": 5000,
        "height_mm": 2500,
        "quantity": 3,
        "leaf_count": 6,
        "leaf_system": LeafSystem.PRIME_DOOR_42x88,
        "application": ApplicationType.DOOR,
        "glass_description": "08mm FLOAT INCOLOR",
        "closure_mode": CLOSURE_WITH_HIDDEN_HANDLE,
        "cremona_base": CREMONA_BASES[7],
        "roller_description": "ROLDANA 80KG",
        "internal_finish": "GUARNICAO DE 70MM",
        "external_finish": "BARRA CHATA DE 30MM",
        "screen_enabled": True,
        "shutter_enabled": False,
    },
    {
        "case_id": "design_2f",
        "width_mm": 2000,
        "height_mm": 2000,
        "quantity": 1,
        "leaf_count": 2,
        "leaf_system": LeafSystem.DESIGN_DOOR_60x111,
        "application": ApplicationType.WINDOW,
        "glass_description": "04mm FLOAT INCOLOR",
        "closure_mode": CLOSURE_WITH_HIDDEN_LATCH,
        "cremona_base": CREMONA_BASES[0],
        "roller_description": "ROLDANA 120KG",
        "internal_finish": "GUARNICAO DE 70MM",
        "external_finish": "BARRA CHATA DE 30MM",
        "screen_enabled": False,
        "shutter_enabled": False,
    },
    {
        "case_id": "design_3f",
        "width_mm": 3000,
        "height_mm": 2100,
        "quantity": 2,
        "leaf_count": 3,
        "leaf_system": LeafSystem.DESIGN_DOOR_60x111,
        "application": ApplicationType.DOOR,
        "glass_description": "05mm FLOAT FUME",
        "closure_mode": CLOSURE_WITH_HIDDEN_HANDLE,
        "cremona_base": CREMONA_BASES[1],
        "roller_description": "ROLDANA 150KG",
        "internal_finish": "SEM ACABAMENTO",
        "external_finish": "SEM ACABAMENTO",
        "screen_enabled": False,
        "shutter_enabled": False,
    },
    {
        "case_id": "design_4f",
        "width_mm": 4000,
        "height_mm": 2300,
        "quantity": 1,
        "leaf_count": 4,
        "leaf_system": LeafSystem.DESIGN_DOOR_60x111,
        "application": ApplicationType.WINDOW,
        "glass_description": "06mm FLOAT INCOLOR",
        "closure_mode": CLOSURE_CREMONA_ONLY,
        "cremona_base": CREMONA_BASES[3],
        "roller_description": "ROLDANA 30KG",
        "internal_finish": "SEM ACABAMENTO",
        "external_finish": "BARRA CHATA DE 30MM",
        "screen_enabled": True,
        "shutter_enabled": False,
    },
    {
        "case_id": "design_6f",
        "width_mm": 5200,
        "height_mm": 2600,
        "quantity": 2,
        "leaf_count": 6,
        "leaf_system": LeafSystem.DESIGN_DOOR_60x111,
        "application": ApplicationType.DOOR,
        "glass_description": "08mm FLOAT INCOLOR",
        "closure_mode": CLOSURE_WITH_HIDDEN_LATCH,
        "cremona_base": CREMONA_BASES[5],
        "roller_description": "ROLDANA 50KG",
        "internal_finish": "GUARNICAO DE 70MM",
        "external_finish": "SEM ACABAMENTO",
        "screen_enabled": False,
        "shutter_enabled": True,
    },
]


def _configuration(case):
    values = {key: value for key, value in case.items() if key != "case_id"}
    return SlidingConfiguration(**values)


def _reference_ffd(lengths, stock_length_mm=STOCK_LENGTH_MM):
    bars = []
    for length in sorted(lengths, reverse=True):
        for bar in bars:
            if sum(bar) + length <= stock_length_mm + 1e-7:
                bar.append(length)
                break
        else:
            bars.append([length])
    return bars


def _golden_order():
    common = {
        "quantity": 1,
        "leaf_count": 2,
        "application": ApplicationType.WINDOW,
        "closure_mode": CLOSURE_WITH_HIDDEN_LATCH,
        "cremona_base": CREMONA_BASES[0],
        "roller_description": "ROLDANA 30KG",
        "internal_finish": "GUARNICAO DE 70MM",
        "external_finish": "BARRA CHATA DE 30MM",
    }
    specifications = [
        (3500, 2000, LeafSystem.PRIME_WINDOW_42x66, "04mm FLOAT INCOLOR", {}),
        (2000, 2000, LeafSystem.DESIGN_DOOR_60x111, "04mm FLOAT INCOLOR", {}),
        (
            1500,
            3000,
            LeafSystem.PRIME_WINDOW_42x66,
            "05mm FLOAT FUME",
            {
                "closure_mode": CLOSURE_CREMONA_ONLY,
                "roller_description": "ROLDANA 50KG",
            },
        ),
        (2000, 2000, LeafSystem.PRIME_WINDOW_42x66, "04mm FLOAT INCOLOR", {}),
    ]
    configs = [
        SlidingConfiguration(
            width_mm=width,
            height_mm=height,
            leaf_system=system,
            glass_description=glass,
            **(common | overrides),
        )
        for width, height, system, glass, overrides in specifications
    ]
    return [(cfg, calculate_sliding(cfg)) for cfg in configs]


class CRRegressionMatrixTests(unittest.TestCase):
    maxDiff = None

    def assert_component(self, components, role, code, length, quantity):
        self.assertIn(role, components)
        component = components[role]
        self.assertEqual(component.material_code, code)
        self.assertAlmostEqual(component.length_mm, length, places=6)
        self.assertAlmostEqual(component.quantity_per_unit, quantity, places=6)
        return component

    def assert_scenario(self, case):
        cfg = _configuration(case)
        result = calculate_sliding(cfg)
        system = SYSTEM_REFERENCE[cfg.leaf_system]
        n = cfg.leaf_count

        frame_code = (
            "DE16652"
            if cfg.leaf_system == LeafSystem.DESIGN_DOOR_60x111
            else ("PR13852" if n in {3, 6} or cfg.screen_enabled else "PR8852")
        )
        frame_reinforcement = {
            "PR8852": "RAG - PR8852",
            "PR13852": "RAG - PR13852",
            "DE16652": "RAG - DE16652",
        }[frame_code]
        frame_quantity = (
            4.0
            if (
                cfg.leaf_system == LeafSystem.PRIME_DOOR_42x88
                and cfg.screen_enabled
                and n in {3, 6}
            )
            else 2.0
        )

        useful_height = cfg.height_mm - (200.0 if cfg.shutter_enabled else 0.0)
        overlap_count = {2: 1, 3: 2, 4: 2, 6: 4}[n]
        central_meeting = 8.0 if n in {4, 6} else 0.0
        leaf_width = (
            cfg.width_mm
            - central_meeting
            - 2 * 52.0
            + 2 * 8.0
            + overlap_count * system["leaf_dim_mm"]
        ) / n
        leaf_height = useful_height - (2 * 52.0 - 2 * 8.0)
        frame_width_cut = cfg.width_mm + 5.0
        frame_height_cut = useful_height + 5.0
        leaf_width_cut = leaf_width + 5.0
        leaf_height_cut = leaf_height + 5.0
        baguette_width = leaf_width - 2 * system["glazing_rebate_mm"]
        baguette_height = leaf_height - 2 * system["glazing_rebate_mm"]
        glass_width = baguette_width - 8.0
        glass_height = baguette_height - 8.0

        expected_geometry = {
            "frame_width_final_mm": cfg.width_mm,
            "frame_height_final_mm": useful_height,
            "frame_width_cut_mm": frame_width_cut,
            "frame_height_cut_mm": frame_height_cut,
            "leaf_width_final_mm": leaf_width,
            "leaf_height_final_mm": leaf_height,
            "leaf_width_cut_mm": leaf_width_cut,
            "leaf_height_cut_mm": leaf_height_cut,
            "baguette_width_mm": baguette_width,
            "baguette_height_mm": baguette_height,
            "glass_width_mm": glass_width,
            "glass_height_mm": glass_height,
        }
        for key, expected in expected_geometry.items():
            self.assertAlmostEqual(result.geometry[key], expected, places=6, msg=key)

        components = {component.role: component for component in result.unit_bom}
        self.assertEqual(len(components), len(result.unit_bom), "papel duplicado na BOM")

        self.assert_component(
            components, "FRAME_HORIZONTAL", frame_code, frame_width_cut, frame_quantity
        )
        self.assert_component(
            components, "FRAME_VERTICAL", frame_code, frame_height_cut, frame_quantity
        )
        self.assert_component(
            components,
            "LEAF_HORIZONTAL",
            system["leaf_code"],
            leaf_width_cut,
            2.0 * n,
        )
        self.assert_component(
            components,
            "LEAF_VERTICAL",
            system["leaf_code"],
            leaf_height_cut,
            2.0 * n,
        )

        interlock_quantity = {
            2: 3.0 if cfg.screen_enabled else 2.0,
            3: 4.0,
            4: 6.0 if cfg.screen_enabled else 4.0,
            6: 12.0,
        }[n]
        interlock_length = leaf_height - 10.0
        self.assert_component(
            components,
            "INTERLOCK",
            system["interlock_code"],
            interlock_length,
            interlock_quantity,
        )

        if cfg.leaf_system == LeafSystem.DESIGN_DOOR_60x111:
            self.assert_component(
                components,
                "LEAF_COVER",
                "DE5013",
                interlock_length,
                interlock_quantity,
            )
            self.assert_component(components, "DESIGN_Z_PROFILE", "AL18", cfg.width_mm, 1.0)
            self.assert_component(components, "DESIGN_Z_TRIM", "AL17", cfg.width_mm, 1.0)
        else:
            self.assertNotIn("LEAF_COVER", components)
            self.assertNotIn("DESIGN_Z_PROFILE", components)
            self.assertNotIn("DESIGN_Z_TRIM", components)

        if n in {4, 6}:
            self.assert_component(
                components, "CENTRAL_CLOSURE", "AC4222", leaf_height, 1.0
            )
        else:
            self.assertNotIn("CENTRAL_CLOSURE", components)

        rail_code = "AL19" if frame_code == "DE16652" else "AL16"
        rail_quantity = 2.0 if frame_code == "PR8852" else 3.0
        self.assert_component(
            components,
            "ALUMINUM_RAIL",
            rail_code,
            cfg.width_mm - 2 * 52.0,
            rail_quantity,
        )

        thickness, glass_code = GLASS_REFERENCE[cfg.glass_description]
        if cfg.leaf_system == LeafSystem.DESIGN_DOOR_60x111:
            baguette_code = "BA3518" if thickness < 8.0 else "BA3218"
        else:
            baguette_code = "BA2516" if thickness < 8.0 else "BA2018"
        self.assert_component(
            components,
            "GLAZING_BEAD_HORIZONTAL",
            baguette_code,
            baguette_width,
            2.0 * n,
        )
        self.assert_component(
            components,
            "GLAZING_BEAD_VERTICAL",
            baguette_code,
            baguette_height,
            2.0 * n,
        )

        glass = components["GLASS_PANEL"]
        self.assertEqual(glass.material_code, glass_code)
        self.assertAlmostEqual(glass.width_mm, glass_width, places=6)
        self.assertAlmostEqual(glass.height_mm, glass_height, places=6)
        self.assertAlmostEqual(glass.area_m2, glass_width * glass_height / 1_000_000, places=6)
        self.assertAlmostEqual(glass.quantity_per_unit, float(n), places=6)

        # CR!G12/G13 e CR!G69 produzem grandezas fracionárias para 3 folhas.
        # A Fase 2 separa o fator de malha da quantidade física de quadros.
        screen_frame_count = math.ceil(n / 2) if cfg.screen_enabled else 0
        screen_profile_quantity = float(2 * screen_frame_count)
        if cfg.screen_enabled:
            self.assert_component(
                components,
                "SCREEN_LEAF_HORIZONTAL",
                system["leaf_code"],
                leaf_width_cut,
                screen_profile_quantity,
            )
            self.assert_component(
                components,
                "SCREEN_LEAF_VERTICAL",
                system["leaf_code"],
                leaf_height_cut,
                screen_profile_quantity,
            )
            self.assert_component(
                components,
                "SCREEN_BEAD_HORIZONTAL",
                "BA3218",
                baguette_width,
                screen_profile_quantity,
            )
            self.assert_component(
                components,
                "SCREEN_BEAD_VERTICAL",
                "BA3218",
                baguette_height,
                screen_profile_quantity,
            )
            screen = components["SCREEN_MESH"]
            self.assertEqual(screen.material_code, "TL1")
            self.assertAlmostEqual(screen.width_mm, glass_width, places=6)
            self.assertAlmostEqual(screen.height_mm, glass_height, places=6)
            self.assertAlmostEqual(screen.quantity_per_unit, n / 2.0, places=6)
            self.assert_component(
                components,
                "SCREEN_RUBBER",
                "TL2",
                2.0 * (baguette_width + baguette_height) * screen_frame_count,
                1.0,
            )
        else:
            for role in (
                "SCREEN_LEAF_HORIZONTAL",
                "SCREEN_LEAF_VERTICAL",
                "SCREEN_BEAD_HORIZONTAL",
                "SCREEN_BEAD_VERTICAL",
                "SCREEN_MESH",
                "SCREEN_RUBBER",
            ):
                self.assertNotIn(role, components)

        finish_quantity = 1.0 if cfg.application == ApplicationType.DOOR else 2.0
        finish_specs = (
            ("INTERNAL", cfg.internal_finish, 140.0),
            ("EXTERNAL", cfg.external_finish, 60.0),
        )
        for side, description, extra in finish_specs:
            if description == "SEM ACABAMENTO":
                self.assertNotIn(f"{side}_FINISH_HORIZONTAL", components)
                self.assertNotIn(f"{side}_FINISH_VERTICAL", components)
                continue
            finish_code = "AC7012" if description == "GUARNICAO DE 70MM" else "AC3004"
            self.assert_component(
                components,
                f"{side}_FINISH_HORIZONTAL",
                finish_code,
                cfg.width_mm + extra,
                finish_quantity,
            )
            self.assert_component(
                components,
                f"{side}_FINISH_VERTICAL",
                finish_code,
                cfg.height_mm + extra,
                2.0,
            )

        reinforced_leaf_quantity = 2.0 * n + screen_profile_quantity
        self.assert_component(
            components,
            "FRAME_REINFORCEMENT_HORIZONTAL",
            frame_reinforcement,
            cfg.width_mm - 2 * 52.0,
            frame_quantity,
        )
        self.assert_component(
            components,
            "FRAME_REINFORCEMENT_VERTICAL",
            frame_reinforcement,
            useful_height - 2 * 52.0,
            frame_quantity,
        )
        self.assert_component(
            components,
            "LEAF_REINFORCEMENT_HORIZONTAL",
            system["leaf_reinforcement"],
            leaf_width - 2 * 52.0,
            reinforced_leaf_quantity,
        )
        self.assert_component(
            components,
            "LEAF_REINFORCEMENT_VERTICAL",
            system["leaf_reinforcement"],
            leaf_height - 2 * 52.0,
            reinforced_leaf_quantity,
        )

        self.assert_component(
            components,
            "LEAF_RUBBER",
            system["rubber"],
            (baguette_width + baguette_height) * 2.0 * n,
            1.0,
        )
        self.assert_component(
            components,
            "LEAF_BRUSH",
            system["brush"],
            (leaf_width_cut + leaf_height_cut) * (4.0 * n + 2.0 * screen_profile_quantity),
            1.0,
        )

        roller_quantity = 2.0 * n + screen_profile_quantity
        expected_unit_quantities = {
            "WIND_STOP": (system["wind_stop"], 2.0 * n - 2.0 + screen_profile_quantity),
            "GLAZING_BLOCK": ("AC0312", 2.0 * n),
            "DRAIN_CAP": ("AC0001", frame_quantity),
            "OPENING_LIMITER": ("375441", roller_quantity),
            "ROLLERS": (ROLLER_CODES[cfg.roller_description], roller_quantity),
        }
        for role, (code, quantity) in expected_unit_quantities.items():
            component = components[role]
            self.assertEqual(component.material_code, code)
            self.assertAlmostEqual(component.quantity_per_unit, quantity, places=6)

        cremona_index = CREMONA_BASES.index(cfg.cremona_base)
        cremona_code_number = cremona_index + (
            1 if cfg.leaf_system == LeafSystem.PRIME_WINDOW_42x66 else 9
        )
        cremona_quantity = (
            1.0
            if cfg.closure_mode == CLOSURE_WITH_HIDDEN_LATCH
            else (2.0 if n < 4 else 3.0)
        )
        cremona = components["CREMONA"]
        self.assertEqual(cremona.material_code, f"CRE{cremona_code_number}")
        self.assertAlmostEqual(cremona.quantity_per_unit, cremona_quantity, places=6)

        handle_quantity = (
            (2.0 if n < 4 else 3.0)
            if cfg.closure_mode == CLOSURE_CREMONA_ONLY
            else 1.0
        )
        self.assertEqual(components["HANDLE_STANDARD"].material_code, "MAC1")
        self.assertAlmostEqual(
            components["HANDLE_STANDARD"].quantity_per_unit, handle_quantity, places=6
        )

        hidden_latch_quantity = (
            (1.0 if n < 4 else 2.0)
            if cfg.closure_mode == CLOSURE_WITH_HIDDEN_LATCH
            else 0.0
        )
        hidden_handle_quantity = (
            (1.0 if n < 4 else 2.0)
            if cfg.closure_mode == CLOSURE_WITH_HIDDEN_HANDLE
            else 0.0
        )
        if hidden_latch_quantity:
            hidden_latch_code = (
                "FEC1" if cremona_index == 0 else ("FEC2" if cremona_index <= 4 else "FEC3")
            )
            self.assertEqual(components["HIDDEN_LATCH"].material_code, hidden_latch_code)
            self.assertAlmostEqual(
                components["HIDDEN_LATCH"].quantity_per_unit,
                hidden_latch_quantity,
                places=6,
            )
        else:
            self.assertNotIn("HIDDEN_LATCH", components)
        if hidden_handle_quantity:
            self.assertEqual(components["HANDLE_HIDDEN"].material_code, "MAC2")
            self.assertAlmostEqual(
                components["HANDLE_HIDDEN"].quantity_per_unit,
                hidden_handle_quantity,
                places=6,
            )
        else:
            self.assertNotIn("HANDLE_HIDDEN", components)

        counter_latch_quantity = (
            (2.0 if n < 4 else 3.0)
            if cremona_index == 0
            else (4.0 if n < 4 else 6.0)
        )
        self.assertEqual(components["COUNTER_LATCH"].material_code, "CON1")
        self.assertAlmostEqual(
            components["COUNTER_LATCH"].quantity_per_unit,
            counter_latch_quantity,
            places=6,
        )

        reinforcement_screws = (
            ((frame_width_cut + frame_height_cut) / 1000.0) * frame_quantity * 4.0
            + ((leaf_width_cut + leaf_height_cut) / 1000.0)
            * roller_quantity
            * 4.0
        )
        hardware_screws = (
            roller_quantity + hidden_latch_quantity + cremona_quantity
        ) * 3.0
        self.assertAlmostEqual(
            components["REINFORCEMENT_SCREWS"].quantity_per_unit,
            reinforcement_screws,
            places=6,
        )
        self.assertGreaterEqual(
            components["REINFORCEMENT_SCREWS"].quantity_per_unit, 0.0
        )
        self.assertAlmostEqual(
            components["HARDWARE_SCREWS"].quantity_per_unit,
            hardware_screws,
            places=6,
        )

        for component in result.unit_bom:
            self.assertGreater(component.quantity_per_unit, 0.0)
            self.assertAlmostEqual(
                component.quantity_order,
                component.quantity_per_unit * cfg.quantity,
                places=6,
            )
            if component.unit == "m":
                expected_cost = (
                    component.length_mm
                    / 1000.0
                    * component.quantity_per_unit
                    * component.unit_price
                )
            elif component.area_m2 is not None:
                expected_cost = (
                    component.width_mm
                    / 1000.0
                    * (component.height_mm / 1000.0)
                    * component.quantity_per_unit
                    * component.unit_price
                )
            else:
                expected_cost = component.quantity_per_unit * component.unit_price
            self.assertAlmostEqual(
                component.cost_per_unit_product,
                expected_cost,
                places=5,
                msg=component.role,
            )

        expected_by_group = defaultdict(float)
        for component in result.unit_bom:
            expected_by_group[component.category] += component.cost_per_unit_product
        self.assertEqual(set(result.cost_breakdown), set(expected_by_group) | {"TOTAL"})
        for category, expected in expected_by_group.items():
            self.assertAlmostEqual(result.cost_breakdown[category], expected, places=5)
        self.assertAlmostEqual(
            result.unit_cost,
            sum(component.cost_per_unit_product for component in result.unit_bom),
            places=5,
        )
        self.assertAlmostEqual(result.cost_breakdown["TOTAL"], result.unit_cost, places=6)

        plan = build_order_purchase_plan([(cfg, result)])
        expected_cut_lengths = defaultdict(list)
        for component in result.unit_bom:
            if component.unit == "m" and component.material_code in BAR_STOCK_CODES:
                quantity = int(round(component.quantity_order))
                expected_cut_lengths[component.material_code].extend(
                    [component.length_mm] * quantity
                )
        self.assertEqual({line.material_code for line in plan.lines}, set(expected_cut_lengths))

        for line in plan.lines:
            lengths = expected_cut_lengths[line.material_code]
            reference_bars = _reference_ffd(lengths)
            self.assertEqual(line.pieces_count, len(lengths))
            self.assertEqual(line.bars_required, len(reference_bars))
            self.assertEqual(len(line.bars), line.bars_required)
            self.assertAlmostEqual(line.consumed_length_mm, sum(lengths), places=6)
            self.assertAlmostEqual(
                line.purchased_length_mm, line.bars_required * STOCK_LENGTH_MM, places=6
            )
            self.assertAlmostEqual(
                line.waste_length_mm,
                line.purchased_length_mm - line.consumed_length_mm,
                places=6,
            )
            self.assertAlmostEqual(
                line.utilization_pct,
                line.consumed_length_mm / line.purchased_length_mm * 100.0,
                places=5,
            )
            self.assertAlmostEqual(
                line.consumption_cost,
                line.consumed_length_mm / 1000.0 * line.unit_price_per_m,
                places=5,
            )
            self.assertAlmostEqual(
                line.purchase_cost,
                line.purchased_length_mm / 1000.0 * line.unit_price_per_m,
                places=5,
            )
            actual_bars = [[piece.length_mm for piece in bar.pieces] for bar in line.bars]
            self.assertEqual(actual_bars, reference_bars)
            for bar in line.bars:
                self.assertAlmostEqual(bar.used_mm + bar.leftover_mm, STOCK_LENGTH_MM, places=6)
                self.assertLessEqual(bar.used_mm, STOCK_LENGTH_MM + 1e-7)
                self.assertEqual(bar.used_mm, sum(piece.length_mm for piece in bar.pieces))
                self.assertTrue(all(piece.source_item == 1 for piece in bar.pieces))

        self.assertAlmostEqual(
            plan.technical_total, result.unit_cost * cfg.quantity, places=5
        )
        self.assertAlmostEqual(
            plan.bar_stock_consumption_cost,
            sum(line.consumption_cost for line in plan.lines),
            places=5,
        )
        self.assertAlmostEqual(
            plan.procurement_total_estimate,
            plan.bar_stock_purchase_cost + plan.exact_nonbar_cost,
            places=5,
        )
        self.assertAlmostEqual(
            plan.purchase_increment_vs_consumption,
            plan.procurement_total_estimate - plan.technical_total,
            places=5,
        )

        warning_codes = {warning.code for warning in result.warnings}
        if cfg.shutter_enabled:
            self.assertIn("V0.2-SHUTTER-PARTIAL", warning_codes)
        if cfg.leaf_system == LeafSystem.DESIGN_DOOR_60x111:
            self.assertIn("DT-CR-003", warning_codes)
            if n == 6:
                self.assertIn("DT-CR-004", warning_codes)


def _make_matrix_test(case):
    def test(self):
        self.assert_scenario(case)

    test.__name__ = f"test_matrix_{case['case_id']}"
    return test


for _case in SCENARIOS:
    setattr(
        CRRegressionMatrixTests,
        f"test_matrix_{_case['case_id']}",
        _make_matrix_test(_case),
    )


class CRGoldenAndSafetyTests(unittest.TestCase):
    def test_current_four_item_golden_and_negative_screw_exception(self):
        order = _golden_order()
        results = [result for _, result in order]
        expected_unit_costs = [2108.90036, 2694.73947, 1984.92952, 1528.97036]
        self.assertEqual(len(results), 4)
        for result, expected in zip(results, expected_unit_costs):
            self.assertAlmostEqual(result.unit_cost, expected, places=5)
            par2 = next(
                component
                for component in result.unit_bom
                if component.material_code == "PAR2"
            )
            self.assertGreaterEqual(par2.quantity_per_unit, 0.0)

        plan = build_order_purchase_plan(order)
        excel_legacy_total = 8317.21971
        engine_physical_total = 8317.53971
        self.assertAlmostEqual(plan.technical_total, engine_physical_total, places=5)
        self.assertAlmostEqual(
            plan.technical_total - excel_legacy_total,
            4 * 0.08,
            places=5,
            msg="O Excel desconta 0,8 PAR2 (R$ 0,08) por item sem bandeira.",
        )
        self.assertAlmostEqual(
            sum(result.unit_cost - 0.08 for result in results),
            excel_legacy_total,
            places=5,
        )

        expected_bar_counts = {
            "AL17": 1,
            "BA3518": 2,
            "BA2516": 7,
            "AC3004": 7,
            "PR4266": 8,
            "DE60111": 3,
            "AC7012": 8,
            "DE4109": 1,
            "PR4536": 3,
            "PR8852": 6,
            "DE16652": 2,
            "AL18": 1,
            "RAG - PR4266": 7,
            "RAG - DE60111": 2,
            "RAG - DE16652": 2,
            "RAG - PR8852": 5,
            "DE5013": 1,
            "AL19": 1,
            "AL16": 3,
        }
        self.assertEqual(
            {line.material_code: line.bars_required for line in plan.lines},
            expected_bar_counts,
        )
        self.assertAlmostEqual(plan.bar_stock_consumption_cost, 6427.7014, places=4)
        self.assertAlmostEqual(plan.bar_stock_purchase_cost, 8201.531, places=3)
        self.assertAlmostEqual(plan.exact_nonbar_cost, 1889.83831, places=5)
        self.assertAlmostEqual(plan.procurement_total_estimate, 10091.36931, places=5)
        self.assertAlmostEqual(plan.purchase_increment_vs_consumption, 1773.8296, places=4)

    @staticmethod
    def _design_config(leaf_count=2, quantity=1):
        return SlidingConfiguration(
            width_mm=2000,
            height_mm=2000,
            quantity=quantity,
            leaf_count=leaf_count,
            leaf_system=LeafSystem.DESIGN_DOOR_60x111,
            application=ApplicationType.WINDOW,
        )

    def test_de5013_historical_multi_item_consolidation_is_two_bars(self):
        configs = [self._design_config(), self._design_config()]
        order = [(cfg, calculate_sliding(cfg)) for cfg in configs]
        plan = build_order_purchase_plan(order)
        line = next(line for line in plan.lines if line.material_code == "DE5013")

        self.assertEqual(line.pieces_count, 4)
        self.assertEqual(line.consumed_length_mm, 4 * 1902.0)
        self.assertEqual(line.bars_required, 2)
        self.assertTrue(all(bar.used_mm <= STOCK_LENGTH_MM for bar in line.bars))
        self.assertTrue(
            any({piece.source_item for piece in bar.pieces} == {1, 2} for bar in line.bars)
        )
        self.assertIn(
            "LEGACY-PEDP-DE5013", {warning.code for warning in plan.warnings}
        )

    def test_de5013_single_four_leaf_item_is_correct_without_legacy_warning(self):
        cfg = self._design_config(leaf_count=4)
        result = calculate_sliding(cfg)
        plan = build_order_purchase_plan([(cfg, result)])
        line = next(line for line in plan.lines if line.material_code == "DE5013")

        self.assertEqual(line.pieces_count, 4)
        self.assertEqual(line.consumed_length_mm, 4 * 1902.0)
        self.assertEqual(line.bars_required, 2)
        self.assertNotIn(
            "LEGACY-PEDP-DE5013", {warning.code for warning in plan.warnings}
        )

    def test_de5013_quantity_two_in_one_item_is_not_historical_multi_item_case(self):
        cfg = self._design_config(quantity=2)
        result = calculate_sliding(cfg)
        plan = build_order_purchase_plan([(cfg, result)])
        line = next(line for line in plan.lines if line.material_code == "DE5013")

        self.assertEqual(line.pieces_count, 4)
        self.assertEqual(line.bars_required, 2)
        self.assertNotIn(
            "LEGACY-PEDP-DE5013", {warning.code for warning in plan.warnings}
        )

    def test_stock_length_is_configurable_for_the_engine_plan(self):
        cfg = SlidingConfiguration(
            width_mm=2000,
            height_mm=2000,
            quantity=1,
            leaf_count=2,
            leaf_system=LeafSystem.PRIME_WINDOW_42x66,
        )
        result = calculate_sliding(cfg)
        plan = build_order_purchase_plan([(cfg, result)], stock_length_mm=6500.0)
        self.assertTrue(plan.lines)
        self.assertTrue(all(line.stock_length_mm == 6500.0 for line in plan.lines))
        self.assertTrue(
            all(bar.stock_length_mm == 6500.0 for line in plan.lines for bar in line.bars)
        )

    def test_oversize_cut_is_rejected_by_purchase_plan(self):
        cfg = SlidingConfiguration(
            width_mm=6000,
            height_mm=2000,
            quantity=1,
            leaf_count=2,
            leaf_system=LeafSystem.PRIME_WINDOW_42x66,
        )
        result = calculate_sliding(cfg)
        with self.assertRaisesRegex(ValueError, "maior que a barra"):
            build_order_purchase_plan([(cfg, result)])

    def test_invalid_catalog_selections_are_rejected(self):
        base = {
            "width_mm": 1500,
            "height_mm": 1200,
            "quantity": 1,
            "leaf_count": 2,
            "leaf_system": LeafSystem.PRIME_WINDOW_42x66,
        }
        invalid_fields = {
            "closure_mode": "FECHAMENTO INEXISTENTE",
            "cremona_base": "CREMONA INEXISTENTE",
            "roller_description": "ROLDANA INEXISTENTE",
        }
        for field, value in invalid_fields.items():
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    calculate_sliding(SlidingConfiguration(**base, **{field: value}))

    def test_long_cremona_uses_1200mm_hidden_latch_not_600mm_latch(self):
        for length in (1200, 1400, 1600):
            with self.subTest(length=length):
                cfg = SlidingConfiguration(
                    width_mm=2400,
                    height_mm=2200,
                    quantity=1,
                    leaf_count=4,
                    leaf_system=LeafSystem.PRIME_DOOR_42x88,
                    closure_mode=CLOSURE_WITH_HIDDEN_LATCH,
                    cremona_base=f"CREMONA 2 PONTOS COMP. {length}MM",
                )
                result = calculate_sliding(cfg)
                hidden_latch = next(
                    component
                    for component in result.unit_bom
                    if component.role == "HIDDEN_LATCH"
                )
                self.assertEqual(hidden_latch.material_code, "FEC3")

    def test_non_finite_dimensions_and_invalid_stock_lengths_are_rejected(self):
        for field, value in (("width_mm", math.nan), ("height_mm", math.inf)):
            values = {
                "width_mm": 1500,
                "height_mm": 1200,
                "quantity": 1,
                "leaf_count": 2,
                "leaf_system": LeafSystem.PRIME_WINDOW_42x66,
                field: value,
            }
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError):
                    calculate_sliding(SlidingConfiguration(**values))

        cfg = SlidingConfiguration(
            width_mm=1500,
            height_mm=1200,
            quantity=1,
            leaf_count=2,
            leaf_system=LeafSystem.PRIME_WINDOW_42x66,
        )
        result = calculate_sliding(cfg)
        for stock_length in (0.0, -5900.0, math.nan, math.inf):
            with self.subTest(stock_length=stock_length):
                with self.assertRaises(ValueError):
                    build_order_purchase_plan(
                        [(cfg, result)], stock_length_mm=stock_length
                    )

    def test_non_physical_glass_dimensions_are_rejected_instead_of_clamped_to_zero(self):
        invalid_dimensions = ((230, 1200), (1500, 190))
        for width_mm, height_mm in invalid_dimensions:
            with self.subTest(width_mm=width_mm, height_mm=height_mm):
                cfg = SlidingConfiguration(
                    width_mm=width_mm,
                    height_mm=height_mm,
                    quantity=1,
                    leaf_count=2,
                    leaf_system=LeafSystem.PRIME_WINDOW_42x66,
                )
                with self.assertRaisesRegex(ValueError, "vidro ficaram inválidas"):
                    calculate_sliding(cfg)

    def test_deterministic_192_case_cross_product_has_consistent_physical_plan(self):
        order = []
        systems = list(LeafSystem)
        applications = list(ApplicationType)
        dimensions = ((2400, 1800), (4800, 2600))
        glasses = list(GLASS_REFERENCE)
        closures = (
            CLOSURE_WITH_HIDDEN_LATCH,
            CLOSURE_WITH_HIDDEN_HANDLE,
            CLOSURE_CREMONA_ONLY,
        )
        rollers = list(ROLLER_CODES)

        index = 0
        for system in systems:
            for leaf_count in (2, 3, 4, 6):
                for application in applications:
                    for screen_enabled in (False, True):
                        for shutter_enabled in (False, True):
                            for width_mm, height_mm in dimensions:
                                cfg = SlidingConfiguration(
                                    width_mm=width_mm,
                                    height_mm=height_mm,
                                    quantity=index % 3 + 1,
                                    leaf_count=leaf_count,
                                    leaf_system=system,
                                    application=application,
                                    glass_description=glasses[index % len(glasses)],
                                    closure_mode=closures[index % len(closures)],
                                    cremona_base=CREMONA_BASES[index % len(CREMONA_BASES)],
                                    roller_description=rollers[index % len(rollers)],
                                    internal_finish=(
                                        "GUARNICAO DE 70MM"
                                        if index % 2
                                        else "SEM ACABAMENTO"
                                    ),
                                    external_finish=(
                                        "BARRA CHATA DE 30MM"
                                        if index % 3
                                        else "SEM ACABAMENTO"
                                    ),
                                    screen_enabled=screen_enabled,
                                    shutter_enabled=shutter_enabled,
                                )
                                result = calculate_sliding(cfg)
                                self.assertTrue(
                                    all(math.isfinite(value) and value > 0 for value in result.geometry.values())
                                )
                                self.assertTrue(result.unit_bom)
                                self.assertTrue(
                                    all(
                                        component.quantity_per_unit > 0
                                        and component.quantity_order > 0
                                        and component.cost_per_unit_product >= 0
                                        for component in result.unit_bom
                                    )
                                )
                                self.assertAlmostEqual(
                                    result.unit_cost,
                                    sum(
                                        component.cost_per_unit_product
                                        for component in result.unit_bom
                                    ),
                                    places=5,
                                )
                                order.append((cfg, result))
                                index += 1

        self.assertEqual(index, 192)
        plan = build_order_purchase_plan(order)
        self.assertTrue(plan.lines)
        for line in plan.lines:
            self.assertEqual(line.bars_required, len(line.bars))
            self.assertGreaterEqual(line.waste_length_mm, -1e-7)
            self.assertGreaterEqual(line.utilization_pct, 0.0)
            self.assertLessEqual(line.utilization_pct, 100.0 + 1e-7)
            for bar in line.bars:
                self.assertLessEqual(bar.used_mm, STOCK_LENGTH_MM + 1e-7)
                self.assertGreaterEqual(bar.leftover_mm, -1e-7)

        self.assertAlmostEqual(
            plan.technical_total,
            sum(result.unit_cost * cfg.quantity for cfg, result in order),
            places=5,
        )


if __name__ == "__main__":
    unittest.main()
