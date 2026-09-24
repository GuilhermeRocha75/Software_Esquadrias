from __future__ import annotations

from dataclasses import fields
import math

from . import gr_v06 as v06
from . import gr_v10 as v10
from . import gr_v11 as v11
from .models import CalculationResult, EngineeringWarning, ShutterMode


GR_ENGINE_VERSION = "GR_ENGINE_0.12.0"
GrConfiguration = v11.GrConfiguration

_AUTOMATED_SINGLE_MODES = {
    ShutterMode.BUTTON_SINGLE,
    ShutterMode.REMOTE_SINGLE,
}


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


def _validate_automated_single(cfg: GrConfiguration) -> None:
    shutter = cfg.shutter
    if shutter is None or shutter.mode not in _AUTOMATED_SINGLE_MODES:
        raise ValueError("Configuração automatizada de painel único inválida.")
    if shutter.box_description != v11.GR_SHUTTER_BOX:
        raise ValueError(f"Caixa GR fora do escopo v0.12: {shutter.box_description}")
    if shutter.slat_description != v11.GR_SHUTTER_SLAT:
        raise ValueError(f"Tala GR fora do escopo v0.12: {shutter.slat_description}")
    if cfg.panel_mode != v06.GR_GLASS_MODE:
        raise ValueError(
            "GR_ENGINE_0.12.0 libera persiana automatizada inicialmente somente com VIDRO INTEIRO."
        )

    effective_height = float(cfg.height_mm) - 200.0
    if effective_height <= 0:
        raise ValueError("Altura GR insuficiente para caixa de persiana de 200 mm.")

    # Mantém exatamente os gates da Fase 10 no vão útil abaixo da caixa.
    v10.calculate_gr(v11._v10_config(
        cfg,
        height_mm=effective_height,
        shutter_enabled=False,
    ))


def _calculate_automated_single(cfg: GrConfiguration) -> CalculationResult:
    _validate_automated_single(cfg)
    shutter = cfg.shutter
    assert shutter is not None

    width = float(cfg.width_mm)
    overall_height = float(cfg.height_mm)
    effective_height = overall_height - 200.0

    base = v10.calculate_gr(v11._v10_config(
        cfg,
        height_mm=effective_height,
        shutter_enabled=False,
    ))
    bom = v11._restore_full_height_finishes(
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
        v11._linear_shutter(
            "321040", "SHUTTER_BOX", box_length, 1.0, cfg.quantity,
            "GR!D47/G47",
        ),
        v11._linear_shutter(
            "327201", "SHUTTER_SIDE_GUIDE", guide_length, 2.0, cfg.quantity,
            "GR!D48/G48",
        ),
        v11._linear_shutter(
            "326015_F", "SHUTTER_SLAT", slat_width, slat_qty, cfg.quantity,
            "GR!D50/G50 + PHYSICAL_ROUND_UP inherited from homologated CR shutter",
        ),
        v11._linear_shutter(
            "311712", "SHUTTER_TERMINAL", slat_width, 1.0, cfg.quantity,
            "GR!D51/G51",
        ),
        v11._linear_shutter(
            "375021", "SHUTTER_SHAFT", shaft_length, 1.0, cfg.quantity,
            "GR!D52/G52",
        ),
    ])

    motor_code = (
        "MOT1"
        if shutter.mode == ShutterMode.REMOTE_SINGLE
        else "MOT2"
    )
    accessory_lines = [
        ("370113", "SHUTTER_LATERAL_COVER", 1.0, "GR!86 + CR!G120"),
        ("371513_2", "SHUTTER_END_PLATE", 1.0, "GR!88 + CR!G122"),
        ("370141", "SHUTTER_MOTOR_COVER", 1.0, "GR!89 + CR!G123"),
        ("371553", "SHUTTER_MOTOR_PLATE", 1.0, "GR!90 + CR!G124"),
        ("375213", "SHUTTER_END_CAP", 1.0, "GR!94 + CR!G128"),
        ("375234", "SHUTTER_END_CAP_ADAPTER", 1.0, "GR!95 + CR!G129"),
        (motor_code, "SHUTTER_MOTOR", 1.0, "GR!97:98 + CR!G131:G132"),
        ("373128", "SHUTTER_GUIDE_INVITATION_PAIR", 1.0, "GR!99 + CR!G133"),
        ("375678", "SHUTTER_FIRST_SLAT_COUPLING", 2.0, "GR!100 + CR!G134"),
        ("375441", "SHUTTER_OPENING_LIMITER", 2.0, "GR!102 + CR!G136"),
    ]
    for code, role, quantity, source in accessory_lines:
        bom.append(v11._unit_shutter(
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
            "GR!85:102 referencia auxiliares 143:156 inexistentes. As quantidades do kit automatizado de painel único foram recuperadas da CR homologada, que usa os mesmos códigos.",
        ),
        EngineeringWarning(
            "LEGACY-GR-SHUTTER-SUBTOTAL-CORRECTED",
            "GR!I103 omite os acessórios da persiana; a v0.12 inclui tampa/placa do motor, motor e demais componentes físicos.",
        ),
    ])
    if shutter.mode == ShutterMode.BUTTON_SINGLE:
        warnings.append(EngineeringWarning(
            "LEGACY-GR-SHUTTER-BUTTON-MOTOR-CORRECTED",
            "GR!B98 aponta incorretamente para LISTAFERRA!A48 (MOT1 controle remoto). A CR homologada e LISTAFERRA!A49 comprovam MOT2 para botoeira.",
        ))
    if slat_qty != legacy_slat_qty:
        warnings.append(EngineeringWarning(
            "LEGACY-GR-SHUTTER-SLAT-FRACTION",
            "O XLSM usa altura/40 como quantidade fracionária de talas; a Engine arredonda para cima por se tratar de peças físicas.",
        ))

    suffix = (
        " COM PERSIANA AUTOMATIZADA CONTROLE REMOTO"
        if shutter.mode == ShutterMode.REMOTE_SINGLE
        else " COM PERSIANA AUTOMATIZADA BOTOEIRA"
    )
    return CalculationResult(
        model_description=base.model_description + suffix,
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
    """GR v0.12: v0.11 + persiana automatizada em painel único."""
    if cfg.shutter is not None and cfg.shutter.mode in _AUTOMATED_SINGLE_MODES:
        return _calculate_automated_single(cfg)
    return _promote(v11.calculate_gr(cfg))
