from __future__ import annotations

from dataclasses import dataclass, fields, replace
import math

from . import gr_v06 as v06
from . import gr_v10 as v10
from .catalog import MATERIALS
from .models import (
    BomComponent,
    CalculationResult,
    EngineeringWarning,
    ShutterConfiguration,
    ShutterMode,
)


GR_ENGINE_VERSION = "GR_ENGINE_0.11.0"

GR_SHUTTER_BOX = "CAIXA DE 200MM"
GR_SHUTTER_SLAT = "TALA DE PVC 40MM"


@dataclass(frozen=True)
class GrConfiguration(v10.GrConfiguration):
    """Contrato GR v0.11 com primeiro recorte completo de persiana."""

    shutter: ShutterConfiguration | None = None


def _v10_config(cfg: GrConfiguration, **overrides) -> v10.GrConfiguration:
    data = {field.name: getattr(cfg, field.name) for field in fields(v10.GrConfiguration)}
    data.update(overrides)
    return v10.GrConfiguration(**data)


def _promote(result: CalculationResult) -> CalculationResult:
    return CalculationResult(
        model_description=result.model_description,
        geometry=result.geometry,
        unit_bom=result.unit_bom,
        cost_breakdown=result.cost_breakdown,
        unit_cost=result.unit_cost,
        leaf_openings=result.leaf_openings,
        transoms=result.transoms,
        fixed_panels=result.fixed_panels,
        glass_panels=result.glass_panels,
        warnings=result.warnings,
        calculation_version=GR_ENGINE_VERSION,
    )


def _linear_shutter(
    code: str,
    role: str,
    length_mm: float,
    quantity: float,
    order_quantity: int,
    source: str,
) -> BomComponent:
    material = MATERIALS[code]
    if not math.isfinite(length_mm) or length_mm <= 0:
        raise ValueError(f"Comprimento inválido para {role}: {length_mm:g} mm.")
    if not math.isfinite(quantity) or quantity <= 0:
        raise ValueError(f"Quantidade inválida para {role}: {quantity:g}.")
    cost = length_mm / 1000.0 * quantity * material.unit_price
    return BomComponent(
        category="PERSIANA",
        role=role,
        material_code=code,
        description=material.description,
        unit="m",
        length_mm=round(length_mm, 6),
        width_mm=None,
        height_mm=None,
        area_m2=None,
        quantity_per_unit=float(quantity),
        quantity_order=float(quantity * order_quantity),
        unit_price=material.unit_price,
        cost_per_unit_product=round(cost, 6),
        source=source,
    )


def _unit_shutter(
    code: str,
    role: str,
    quantity: float,
    order_quantity: int,
    source: str,
) -> BomComponent:
    material = MATERIALS[code]
    if not math.isfinite(quantity) or quantity <= 0:
        raise ValueError(f"Quantidade inválida para {role}: {quantity:g}.")
    return BomComponent(
        category="PERSIANA",
        role=role,
        material_code=code,
        description=material.description,
        unit="un",
        length_mm=None,
        width_mm=None,
        height_mm=None,
        area_m2=None,
        quantity_per_unit=float(quantity),
        quantity_order=float(quantity * order_quantity),
        unit_price=material.unit_price,
        cost_per_unit_product=round(quantity * material.unit_price, 6),
        source=source,
    )


def _restore_full_height_finishes(
    bom: list[BomComponent],
    overall_height_mm: float,
    order_quantity: int,
) -> list[BomComponent]:
    lengths = {
        "INTERNAL_FINISH_HEIGHT": overall_height_mm + 140.0,
        "EXTERNAL_FINISH_HEIGHT": overall_height_mm + 60.0,
    }
    result = []
    for item in bom:
        if item.role not in lengths:
            result.append(item)
            continue
        length = lengths[item.role]
        cost = length / 1000.0 * item.quantity_per_unit * item.unit_price
        result.append(replace(
            item,
            length_mm=round(length, 6),
            quantity_order=item.quantity_per_unit * order_quantity,
            cost_per_unit_product=round(cost, 6),
            source=(item.source or "") + " / altura externa total preservada com persiana",
        ))
    return result


def _validate_manual_single(cfg: GrConfiguration) -> None:
    shutter = cfg.shutter
    if shutter is None:
        raise ValueError("Configuração de persiana ausente.")
    if shutter.mode != ShutterMode.MANUAL_SINGLE:
        raise ValueError(
            "GR_ENGINE_0.11.0 suporta inicialmente somente MANUAL EM PAINEL ÚNICO."
        )
    if shutter.box_description != GR_SHUTTER_BOX:
        raise ValueError(f"Caixa GR fora do escopo v0.11: {shutter.box_description}")
    if shutter.slat_description != GR_SHUTTER_SLAT:
        raise ValueError(f"Tala GR fora do escopo v0.11: {shutter.slat_description}")
    if cfg.panel_mode != v06.GR_GLASS_MODE:
        raise ValueError(
            "GR_ENGINE_0.11.0 libera persiana inicialmente somente com VIDRO INTEIRO."
        )

    effective_height = float(cfg.height_mm) - 200.0
    if effective_height <= 0:
        raise ValueError("Altura GR insuficiente para caixa de persiana de 200 mm.")

    # Reaproveita todos os gates já homologados da v0.10 no vão útil abaixo
    # da caixa, neutralizando o flag legado que a v0.5 bloqueava.
    v10.calculate_gr(_v10_config(
        cfg,
        height_mm=effective_height,
        shutter_enabled=False,
    ))


def _calculate_manual_single(cfg: GrConfiguration) -> CalculationResult:
    _validate_manual_single(cfg)

    width = float(cfg.width_mm)
    overall_height = float(cfg.height_mm)
    effective_height = overall_height - 200.0

    base = v10.calculate_gr(_v10_config(
        cfg,
        height_mm=effective_height,
        shutter_enabled=False,
    ))
    bom = _restore_full_height_finishes(
        list(base.unit_bom), overall_height, cfg.quantity
    )

    box_length = width - 15.0
    guide_length = overall_height - 200.0
    slat_width = width - 2.0 * 32.0 - 10.0
    shaft_length = width - 40.0
    if min(box_length, guide_length, slat_width, shaft_length) <= 0:
        raise ValueError("Dimensões da persiana GR ficaram inválidas.")

    legacy_slat_qty = overall_height / 40.0
    slat_qty = float(math.ceil(legacy_slat_qty))

    bom.extend([
        _linear_shutter(
            "321040", "SHUTTER_BOX", box_length, 1.0, cfg.quantity,
            "GR!D47/G47",
        ),
        _linear_shutter(
            "327201", "SHUTTER_SIDE_GUIDE", guide_length, 2.0, cfg.quantity,
            "GR!D48/G48",
        ),
        _linear_shutter(
            "326015_F", "SHUTTER_SLAT", slat_width, slat_qty, cfg.quantity,
            "GR!D50/G50 + PHYSICAL_ROUND_UP inherited from homologated CR shutter",
        ),
        _linear_shutter(
            "311712", "SHUTTER_TERMINAL", slat_width, 1.0, cfg.quantity,
            "GR!D51/G51",
        ),
        _linear_shutter(
            "375021", "SHUTTER_SHAFT", shaft_length, 1.0, cfg.quantity,
            "GR!D52/G52",
        ),
    ])

    # GR!85:102 é uma cópia incompleta do kit de persiana: várias quantidades
    # apontam para auxiliares inexistentes (143:156), e GR!I103 soma apenas I83:I84.
    # As mesmas peças/códigos estão integralmente parametrizadas na CR já homologada.
    # Para MANUAL EM PAINEL ÚNICO, as quantidades físicas são determinísticas.
    accessory_lines = [
        ("370113", "SHUTTER_LATERAL_COVER", 2.0, "GR!86 + CR!G120"),
        ("371513_4", "SHUTTER_PULLEY_PLATE", 1.0, "GR!87 + CR!G121"),
        ("371513_2", "SHUTTER_END_PLATE", 1.0, "GR!88 + CR!G122"),
        ("375110", "SHUTTER_PULLEY", 1.0, "GR!93 + CR!G127"),
        ("375213", "SHUTTER_END_CAP", 1.0, "GR!94 + CR!G128"),
        ("375234", "SHUTTER_END_CAP_ADAPTER", 1.0, "GR!95 + CR!G129"),
        ("375339", "SHUTTER_RECESSED_WINDER", 1.0, "GR!96 + CR!G130"),
        ("373128", "SHUTTER_GUIDE_INVITATION_PAIR", 1.0, "GR!99 + CR!G133"),
        ("375678", "SHUTTER_FIRST_SLAT_COUPLING", 2.0, "GR!100 + CR!G134"),
        ("375415", "SHUTTER_FRONT_PIN", 1.0, "GR!101 + CR!G135"),
        ("375441", "SHUTTER_OPENING_LIMITER", 2.0, "GR!102 + CR!G136"),
    ]
    for code, role, quantity, source in accessory_lines:
        bom.append(_unit_shutter(
            code,
            role,
            quantity,
            cfg.quantity,
            source + " / LEGACY_GR_HELPERS_RECOVERED",
        ))

    groups = (*v06._GROUPS, "PERSIANA")
    breakdown = {
        group: round(
            sum(item.cost_per_unit_product for item in bom if item.category == group),
            6,
        )
        for group in groups
    }
    total = round(sum(item.cost_per_unit_product for item in bom), 6)
    breakdown["TOTAL"] = total

    geometry = dict(base.geometry)
    geometry.update({
        "overall_height_mm": round(overall_height, 6),
        "shutter_box_height_mm": 200.0,
        "shutter_main_opening_height_mm": round(effective_height, 6),
        "shutter_panel_count": 1.0,
        "shutter_box_length_mm": round(box_length, 6),
        "shutter_side_guide_length_mm": round(guide_length, 6),
        "shutter_slat_width_mm": round(slat_width, 6),
        "shutter_slat_quantity": slat_qty,
        "shutter_shaft_length_mm": round(shaft_length, 6),
    })

    warnings = list(base.warnings)
    warnings.extend([
        EngineeringWarning(
            "LEGACY-GR-SHUTTER-HELPERS-RECOVERED",
            "GR!85:102 referencia auxiliares 143:156 inexistentes. As quantidades do kit manual de painel único foram recuperadas da família CR homologada, que usa os mesmos códigos e a mesma estrutura de fórmulas.",
        ),
        EngineeringWarning(
            "LEGACY-GR-SHUTTER-SUBTOTAL-CORRECTED",
            "GR!I103 soma apenas I83:I84 e omite os acessórios da persiana. A v0.11 inclui o kit físico completo no custo técnico.",
        ),
    ])
    if slat_qty != legacy_slat_qty:
        warnings.append(EngineeringWarning(
            "LEGACY-GR-SHUTTER-SLAT-FRACTION",
            "O XLSM usa altura/40 como quantidade fracionária de talas; a Engine arredonda para cima por se tratar de peças físicas.",
        ))

    return CalculationResult(
        model_description=base.model_description + " COM PERSIANA",
        geometry=geometry,
        unit_bom=bom,
        cost_breakdown=breakdown,
        unit_cost=total,
        leaf_openings=list(base.leaf_openings),
        transoms=list(base.transoms),
        fixed_panels=list(base.fixed_panels),
        glass_panels=list(base.glass_panels),
        warnings=warnings,
        calculation_version=GR_ENGINE_VERSION,
    )


def calculate_gr(cfg: GrConfiguration) -> CalculationResult:
    """GR v0.11: v0.10 + persiana manual em painel único."""
    if cfg.shutter is not None:
        return _calculate_manual_single(cfg)
    if cfg.shutter_enabled:
        raise ValueError(
            "shutter_enabled legado não é aceito isoladamente na GR; informe shutter completo."
        )
    return _promote(v10.calculate_gr(_v10_config(cfg)))
