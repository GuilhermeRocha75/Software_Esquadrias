from __future__ import annotations

import math

from .catalog import GLASSES, HARDWARE, MATERIALS, normalize
from .models import (
    BomComponent,
    CalculationResult,
    EngineeringWarning,
    GlassPanel,
    MaximArConfiguration,
    MaximArLeafSystem,
)


MAXIM_AR_ENGINE_VERSION = "MX_ENGINE_0.1.0"
MAXIM_AR_CLOSURE_OPTIONS = (
    "FECHO 1 PONTO",
    "MAÇANETA COM CREMONA",
)
MAXIM_AR_CREMONA_OPTIONS = (
    "CREMONA MAXIM-AR 2 PONTOS COMP. 300mm",
    "CREMONA MAXIM-AR 2 PONTOS COMP. 400mm",
    "CREMONA MAXIM-AR 2 PONTOS COMP. 600mm",
    "CREMONA MAXIM-AR 2 PONTOS COMP. 800mm",
)
MAXIM_AR_INTERNAL_FINISH_OPTIONS = ("GUARNIÇÃO DE 70MM",)
MAXIM_AR_EXTERNAL_FINISH_OPTIONS = ("BARRA CHATA DE 30MM",)

_GROUPS = (
    "PERFIS PRINCIPAIS",
    "BAGUETES",
    "ACABAMENTOS",
    "REFORÇOS",
    "VIDROS",
    "VEDAÇÕES",
    "ACESSÓRIOS",
    "FERRAGENS",
)


def _linear_component(
    category: str,
    role: str,
    material_code: str,
    length_mm: float,
    quantity_per_unit: float,
    order_quantity: int,
    source: str,
) -> BomComponent:
    if not math.isfinite(length_mm) or length_mm <= 0:
        raise ValueError(f"Comprimento inválido para {role}: {length_mm} mm.")
    if not math.isfinite(quantity_per_unit) or quantity_per_unit <= 0:
        raise ValueError(f"Quantidade inválida para {role}: {quantity_per_unit}.")
    material = MATERIALS[material_code]
    cost = length_mm / 1000.0 * quantity_per_unit * material.unit_price
    return BomComponent(
        category=category,
        role=role,
        material_code=material.code,
        description=material.description,
        unit="m",
        length_mm=round(length_mm, 6),
        width_mm=None,
        height_mm=None,
        area_m2=None,
        quantity_per_unit=float(quantity_per_unit),
        quantity_order=float(quantity_per_unit * order_quantity),
        unit_price=material.unit_price,
        cost_per_unit_product=round(cost, 6),
        source=source,
    )


def _meter_consumable(
    role: str,
    material_code: str,
    total_length_mm: float,
    order_quantity: int,
    source: str,
) -> BomComponent:
    return _linear_component(
        "VEDAÇÕES",
        role,
        material_code,
        total_length_mm,
        1.0,
        order_quantity,
        source,
    )


def _unit_component(
    role: str,
    material,
    quantity_per_unit: float,
    order_quantity: int,
    source: str,
    category: str = "FERRAGENS",
) -> BomComponent:
    if not math.isfinite(quantity_per_unit) or quantity_per_unit <= 0:
        raise ValueError(f"Quantidade inválida para {role}: {quantity_per_unit}.")
    return BomComponent(
        category=category,
        role=role,
        material_code=material.code,
        description=material.description,
        unit="un",
        length_mm=None,
        width_mm=None,
        height_mm=None,
        area_m2=None,
        quantity_per_unit=float(quantity_per_unit),
        quantity_order=float(quantity_per_unit * order_quantity),
        unit_price=material.unit_price,
        cost_per_unit_product=round(quantity_per_unit * material.unit_price, 6),
        source=source,
    )


def _glass_component(
    glass,
    width_mm: float,
    height_mm: float,
    order_quantity: int,
) -> BomComponent:
    area_m2 = width_mm / 1000.0 * height_mm / 1000.0
    return BomComponent(
        category="VIDROS",
        role="GLASS_PANEL",
        material_code=glass.code,
        description=glass.description,
        unit="m²",
        length_mm=None,
        width_mm=round(width_mm, 6),
        height_mm=round(height_mm, 6),
        area_m2=round(area_m2, 6),
        quantity_per_unit=1.0,
        quantity_order=float(order_quantity),
        unit_price=glass.unit_price,
        cost_per_unit_product=round(area_m2 * glass.unit_price, 6),
        source="MX-VID-001 / MX!D59:I59",
    )


def _glass_and_bead(cfg: MaximArConfiguration):
    glass = GLASSES.get(normalize(cfg.glass_description))
    if glass is None or glass.code == "0" or glass.thickness_mm is None:
        raise ValueError(f"Vidro não suportado no Maxim-Ar Fase 1: {cfg.glass_description}")

    thickness = float(glass.thickness_mm)
    if cfg.leaf_system == MaximArLeafSystem.PRIME_WINDOW_42x63:
        ranges = (
            (8, "BA2516"),
            (12, "BA2018"),
            (16, "BA1816"),
            (17, "BA1216"),
            (24, "BA1016"),
            (25, "BA0716"),
        )
    else:
        ranges = (
            (8, "BA3518"),
            (12, "BA3218"),
            (19, "BA2516"),
            (22, "BA2018"),
            (26, "BA1816"),
            (31, "BA1216"),
            (34, "BA1016"),
            (35, "BA0716"),
        )

    bead_code = next((code for upper, code in ranges if thickness < upper), None)
    if bead_code is None:
        raise ValueError(
            f"Espessura de vidro {thickness:g} mm sem baguete comprovada para "
            f"{cfg.leaf_system.value}."
        )
    return glass, bead_code


def _hardware_by_description(description: str):
    material = HARDWARE.get(normalize(description))
    if material is None:
        raise ValueError(f"Ferragem Maxim-Ar não encontrada por igualdade exata: {description}")
    return material


def _arm_material(system: MaximArLeafSystem, leaf_height_mm: float):
    if leaf_height_mm <= 500:
        suffix = 1
    elif leaf_height_mm <= 600:
        suffix = 2
    elif leaf_height_mm <= 800:
        suffix = 3
    elif leaf_height_mm <= 1000:
        suffix = 4
    else:
        suffix = 5
    if system == MaximArLeafSystem.DESIGN_WINDOW_60x78:
        suffix += 5
    return _hardware_by_description(f"BRAÇO MAXIM-AR CX {'16' if suffix > 5 else '14'}mm DT{(10, 12, 16, 20, 24)[(suffix - 1) % 5]}")


def _validate_configuration(cfg: MaximArConfiguration) -> None:
    if not math.isfinite(float(cfg.width_mm)) or not math.isfinite(float(cfg.height_mm)):
        raise ValueError("Largura e altura do Maxim-Ar devem ser finitas.")
    if cfg.width_mm <= 0 or cfg.height_mm <= 0:
        raise ValueError("Largura e altura do Maxim-Ar devem ser positivas.")
    if isinstance(cfg.quantity, bool) or not isinstance(cfg.quantity, int) or cfg.quantity < 1:
        raise ValueError("A quantidade do Maxim-Ar deve ser um inteiro maior ou igual a 1.")
    if normalize(cfg.internal_finish) != normalize(MAXIM_AR_INTERNAL_FINISH_OPTIONS[0]):
        raise ValueError("Acabamento interno não comprovado no Maxim-Ar Fase 1.")
    if normalize(cfg.external_finish) != normalize(MAXIM_AR_EXTERNAL_FINISH_OPTIONS[0]):
        raise ValueError("Acabamento externo não comprovado no Maxim-Ar Fase 1.")
    if normalize(cfg.closure_mode) not in {
        normalize(value) for value in MAXIM_AR_CLOSURE_OPTIONS
    }:
        raise ValueError(f"Fechamento Maxim-Ar não suportado: {cfg.closure_mode}")


def calculate_maxim_ar(cfg: MaximArConfiguration) -> CalculationResult:
    """Calcula o baseline MX comprovado por MX!8:85 do XLSM de referência."""

    _validate_configuration(cfg)
    glass, bead_code = _glass_and_bead(cfg)
    width = float(cfg.width_mm)
    height = float(cfg.height_mm)
    weld = 5.0  # PFAB!B1
    glass_clearance = 8.0  # PFAB!B12

    if cfg.leaf_system == MaximArLeafSystem.PRIME_WINDOW_42x63:
        frame_code = leaf_code = "PR4263"
        frame_face = 28.0  # LISTAPERFIS!E6
        leaf_face = 44.0  # LISTAPERFIS!D7
        overlap = 6.0  # PFAB!B5
        frame_reinforcement = leaf_reinforcement = "RAG - PR4263"
    elif cfg.leaf_system == MaximArLeafSystem.DESIGN_WINDOW_60x78:
        frame_code = "DE6058"
        leaf_code = "DE6078"
        frame_face = 40.0  # LISTAPERFIS!E19
        leaf_face = 60.0  # LISTAPERFIS!D16
        overlap = 8.0  # PFAB!B17
        frame_reinforcement = "RAG - DE6058"
        leaf_reinforcement = "RAG - DE6078"
    else:
        raise ValueError(f"Sistema Maxim-Ar não suportado: {cfg.leaf_system}")

    frame_width_final = width
    frame_height_final = height
    frame_width_cut = frame_width_final + weld
    frame_height_cut = frame_height_final + weld
    leaf_width_final = width - 2 * frame_face + 2 * overlap
    leaf_height_final = height - 2 * frame_face + 2 * overlap
    leaf_width_cut = leaf_width_final + weld
    leaf_height_cut = leaf_height_final + weld
    bead_width = leaf_width_final - 2 * leaf_face
    bead_height = leaf_height_final - 2 * leaf_face
    glass_width = bead_width - glass_clearance
    glass_height = bead_height - glass_clearance
    frame_reinforcement_width = width - 2 * (44.0 if frame_code == "PR4263" else 58.0)
    frame_reinforcement_height = height - 2 * (44.0 if frame_code == "PR4263" else 58.0)
    leaf_reinforcement_width = bead_width
    leaf_reinforcement_height = bead_height

    physical_dimensions = {
        "leaf_width_final_mm": leaf_width_final,
        "leaf_height_final_mm": leaf_height_final,
        "baguette_width_mm": bead_width,
        "baguette_height_mm": bead_height,
        "glass_width_mm": glass_width,
        "glass_height_mm": glass_height,
        "frame_reinforcement_width_mm": frame_reinforcement_width,
        "frame_reinforcement_height_mm": frame_reinforcement_height,
        "leaf_reinforcement_width_mm": leaf_reinforcement_width,
        "leaf_reinforcement_height_mm": leaf_reinforcement_height,
    }
    invalid = [(name, value) for name, value in physical_dimensions.items() if value <= 0]
    if invalid:
        name, value = invalid[0]
        raise ValueError(
            f"Dimensão tecnicamente impossível para Maxim-Ar: {name}={value:g} mm."
        )

    quantity = cfg.quantity
    bom: list[BomComponent] = []
    bom.extend((
        _linear_component("PERFIS PRINCIPAIS", "FRAME_HORIZONTAL", frame_code, frame_width_cut, 2, quantity, "MX-GEO-001 / MX!E8:G8"),
        _linear_component("PERFIS PRINCIPAIS", "FRAME_VERTICAL", frame_code, frame_height_cut, 2, quantity, "MX-GEO-001 / MX!E9:G9"),
        _linear_component("PERFIS PRINCIPAIS", "LEAF_HORIZONTAL", leaf_code, leaf_width_cut, 2, quantity, "MX-GEO-002 / MX!E10:G10"),
        _linear_component("PERFIS PRINCIPAIS", "LEAF_VERTICAL", leaf_code, leaf_height_cut, 2, quantity, "MX-GEO-002 / MX!E11:G11"),
        _linear_component("BAGUETES", "GLAZING_BEAD_HORIZONTAL", bead_code, bead_width, 2, quantity, "MX-GEO-003 / MX!D12:G12"),
        _linear_component("BAGUETES", "GLAZING_BEAD_VERTICAL", bead_code, bead_height, 2, quantity, "MX-GEO-003 / MX!D13:G13"),
        _linear_component("ACABAMENTOS", "INTERNAL_FINISH_HORIZONTAL", "AC7012", width + 140.0, 2, quantity, "MX-ACA-001 / MX!D33:G33"),
        _linear_component("ACABAMENTOS", "INTERNAL_FINISH_VERTICAL", "AC7012", height + 140.0, 2, quantity, "MX-ACA-001 / MX!D34:G34"),
        _linear_component("ACABAMENTOS", "EXTERNAL_FINISH_HORIZONTAL", "AC3004", width + 60.0, 2, quantity, "MX-ACA-002 / MX!D35:G35"),
        _linear_component("ACABAMENTOS", "EXTERNAL_FINISH_VERTICAL", "AC3004", height + 60.0, 2, quantity, "MX-ACA-002 / MX!D36:G36"),
        _linear_component("REFORÇOS", "FRAME_REINFORCEMENT_HORIZONTAL", frame_reinforcement, frame_reinforcement_width, 2, quantity, "MX-REF-001 / MX!D42:G42"),
        _linear_component("REFORÇOS", "FRAME_REINFORCEMENT_VERTICAL", frame_reinforcement, frame_reinforcement_height, 2, quantity, "MX-REF-001 / MX!D43:G43"),
        _linear_component("REFORÇOS", "LEAF_REINFORCEMENT_HORIZONTAL", leaf_reinforcement, leaf_reinforcement_width, 2, quantity, "MX-REF-002 / MX!D44:G44"),
        _linear_component("REFORÇOS", "LEAF_REINFORCEMENT_VERTICAL", leaf_reinforcement, leaf_reinforcement_height, 2, quantity, "MX-REF-002 / MX!D45:G45"),
    ))
    glass_component = _glass_component(glass, glass_width, glass_height, quantity)
    bom.append(glass_component)

    warnings: list[EngineeringWarning] = []
    if cfg.leaf_system == MaximArLeafSystem.PRIME_WINDOW_42x63:
        bom.extend((
            _meter_consumable("GLASS_RUBBER", "ACB606", 2 * (bead_width + bead_height), quantity, "MX-VED-001 / MX!G67:I67"),
            _meter_consumable("LEAF_RUBBER", "AC0002", 2 * (leaf_width_final + leaf_height_final), quantity, "MX-VED-002 / MX!G68:I68"),
            _meter_consumable("FRAME_RUBBER", "AC0002", 2 * (leaf_width_final + leaf_height_final), quantity, "MX-VED-003 / MX!G69:I69"),
        ))
    else:
        warnings.append(EngineeringWarning(
            "LEGACY-MX-DESIGN-SEALING-OMITTED",
            "MX!B67:B69 condiciona as três vedações somente à folha PRIME. "
            "A Fase 1 preserva custo zero no DESIGN até que o material correto seja comprovado.",
        ))

    bom.extend((
        _unit_component("GLAZING_BLOCK", MATERIALS["AC0312"], 4, quantity, "MX-ACE-001 / MX!G72:I72", "ACESSÓRIOS"),
        _unit_component("DRAIN_CAP", MATERIALS["AC0001"], 2, quantity, "MX-ACE-002 / MX!G73:I73", "ACESSÓRIOS"),
    ))

    arm = _arm_material(cfg.leaf_system, leaf_height_final)
    bom.append(_unit_component("MAXIM_AR_ARM", arm, 1, quantity, "MX-FER-001 / MX!B76:I76"))

    closure = normalize(cfg.closure_mode)
    if closure == normalize("FECHO 1 PONTO"):
        if cfg.cremona_description:
            raise ValueError("FECHO 1 PONTO não utiliza cremona no baseline do XLSM.")
        bom.append(_unit_component(
            "MAXIM_AR_LATCH",
            _hardware_by_description("FECHO MAXIM-AR 1 PONTO"),
            1,
            quantity,
            "MX-FER-002 / MX!B77:I77",
        ))
        hardware_screws = 10.0
    else:
        if cfg.cremona_description is None or normalize(cfg.cremona_description) not in {
            normalize(value) for value in MAXIM_AR_CREMONA_OPTIONS
        }:
            raise ValueError("MAÇANETA COM CREMONA exige uma cremona Maxim-Ar exata.")
        bom.extend((
            _unit_component("MAXIM_AR_HANDLE", _hardware_by_description("MAÇANETA ESTREITA MAXIM-AR"), 1, quantity, "MX-FER-003 / MX!B77:I77"),
            _unit_component("CREMONA", _hardware_by_description(cfg.cremona_description), 1, quantity, "MX-FER-004 / MX!B78:I78"),
            _unit_component("COUNTER_LATCH", _hardware_by_description("CONTRA FECHO STANDARD"), 2, quantity, "MX-FER-005 / MX!B79:I79"),
        ))
        hardware_screws = 16.0

    reinforcement_screws = (
        8.0
        * (frame_width_cut + frame_height_cut + leaf_width_cut + leaf_height_cut)
        / 1000.0
    )
    bom.extend((
        _unit_component("REINFORCEMENT_SCREWS", MATERIALS["PAR2"], reinforcement_screws, quantity, "MX-FER-006 / MX!G80:I80"),
        _unit_component("HARDWARE_SCREWS", MATERIALS["PAR1"], hardware_screws, quantity, "MX-FER-007 / MX!G81:I81"),
    ))

    breakdown = {
        group: round(sum(item.cost_per_unit_product for item in bom if item.category == group), 6)
        for group in _GROUPS
    }
    total = round(sum(breakdown.values()), 6)
    breakdown["TOTAL"] = total
    geometry = {
        "frame_width_final_mm": round(frame_width_final, 6),
        "frame_height_final_mm": round(frame_height_final, 6),
        "frame_width_cut_mm": round(frame_width_cut, 6),
        "frame_height_cut_mm": round(frame_height_cut, 6),
        "leaf_width_final_mm": round(leaf_width_final, 6),
        "leaf_height_final_mm": round(leaf_height_final, 6),
        "leaf_width_cut_mm": round(leaf_width_cut, 6),
        "leaf_height_cut_mm": round(leaf_height_cut, 6),
        "baguette_width_mm": round(bead_width, 6),
        "baguette_height_mm": round(bead_height, 6),
        "glass_width_mm": round(glass_width, 6),
        "glass_height_mm": round(glass_height, 6),
    }
    glass_panel = GlassPanel(
        source="MAIN_LEAF",
        position="MAIN",
        width_mm=round(glass_width, 6),
        height_mm=round(glass_height, 6),
        quantity=1.0,
        material_code=glass.code,
        material_description=glass.description,
        area_m2=glass_component.area_m2 or 0.0,
        unit_cost=glass.unit_price,
        total_cost=glass_component.cost_per_unit_product,
    )
    label = "Prime 42x63" if cfg.leaf_system == MaximArLeafSystem.PRIME_WINDOW_42x63 else "Design 60x78"
    return CalculationResult(
        model_description=f"JANELA 1 FOLHA MAXIM-AR ({label})",
        geometry=geometry,
        unit_bom=bom,
        cost_breakdown=breakdown,
        unit_cost=total,
        glass_panels=[glass_panel],
        warnings=warnings,
        calculation_version=MAXIM_AR_ENGINE_VERSION,
    )
