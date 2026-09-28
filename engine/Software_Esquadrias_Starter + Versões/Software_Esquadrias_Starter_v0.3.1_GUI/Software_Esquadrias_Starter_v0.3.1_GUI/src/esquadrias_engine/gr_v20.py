from __future__ import annotations

from dataclasses import fields, replace
import math

from . import gr_v06 as v06
from . import gr_v09 as v09
from . import gr_v14 as v14
from . import gr_v15 as v15
from . import gr_v19 as v19
from .models import (
    CalculationResult,
    EngineeringWarning,
    FixedPanelGeometry,
    FixedPanelPosition,
    GridOpening,
    Transom,
    TransomOrientation,
)


GR_ENGINE_VERSION = "GR_ENGINE_0.20.0"
GrConfiguration = v19.GrConfiguration


def _v14_config(cfg: GrConfiguration, **overrides) -> v14.GrConfiguration:
    data = {field.name: getattr(cfg, field.name) for field in fields(v14.GrConfiguration)}
    data.update(overrides)
    return v14.GrConfiguration(**data)


def _v19_config(cfg: GrConfiguration) -> v19.GrConfiguration:
    return v19.GrConfiguration(**{
        field.name: getattr(cfg, field.name) for field in fields(v19.GrConfiguration)
    })


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


def _is_phase20_bottom_grid(cfg: GrConfiguration) -> bool:
    return (
        cfg.bottom_flag_vertical_transoms == 2
        and cfg.bottom_flag_horizontal_transoms == 0
        and cfg.top_flag_vertical_transoms == 0
        and cfg.top_flag_horizontal_transoms == 0
    )


def _validate_phase20(cfg: GrConfiguration) -> None:
    counts = (
        cfg.bottom_flag_vertical_transoms,
        cfg.bottom_flag_horizontal_transoms,
        cfg.top_flag_vertical_transoms,
        cfg.top_flag_horizontal_transoms,
    )
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in counts):
        raise ValueError("Divisões de bandeira GR devem ser inteiros maiores ou iguais a zero.")
    if not _is_phase20_bottom_grid(cfg):
        raise ValueError(
            "GR_ENGINE_0.20.0 homologa na bandeira inferior somente 2 divisões verticais."
        )
    if cfg.bottom_flag_height_mm <= 0 or cfg.top_flag_height_mm != 0:
        raise ValueError("Fase 20 exige somente bandeira inferior.")
    if cfg.application != v06.GR_APPLICATION_DOOR:
        raise ValueError("Fase 20 exige aplicação PORTA.")
    if cfg.leaf_count != 1:
        raise ValueError("Fase 20 exige porta de 1 folha.")
    if cfg.leaf_system != v06.GR_LEAF_SYSTEM_EXTERNAL:
        raise ValueError("Fase 20 homologa porta externa Design 60x104.")
    if cfg.panel_mode != v06.GR_GLASS_MODE:
        raise ValueError("Fase 20 exige VIDRO INTEIRO.")
    if cfg.hinge_description != v09.GR_HINGE_OB:
        raise ValueError("Fase 20 exige DOBRADIÇA SISTEMA OB.")
    if cfg.closure_mode != v06.GR_CLOSURE_MONOPOINT:
        raise ValueError("Fase 20 exige fechadura monoponto.")
    if cfg.cremona_description is not None:
        raise ValueError("Porta monoponto da Fase 20 não usa cremona.")
    if cfg.shutter is not None or cfg.shutter_enabled or cfg.screen_enabled:
        raise ValueError("Fase 20 não combina subdivisão da bandeira com persiana/tela.")
    if cfg.leaf_horizontal_transoms or cfg.leaf_vertical_transoms:
        raise ValueError("Fase 20 exige folha sem travessas internas adicionais.")
    if cfg.structural_reinforcement is not None:
        raise ValueError("Fase 20 não combina reforço estrutural opcional.")
    if not cfg.glass_description:
        raise ValueError("Fase 20 exige vidro informado.")
    v06._glass_and_bead(cfg.glass_description)

    bottom = float(cfg.bottom_flag_height_mm)
    if not math.isfinite(bottom) or bottom <= 66.0:
        raise ValueError("Altura da bandeira inferior deve gerar vidro positivo.")
    synthetic_height = float(cfg.height_mm) - bottom + 22.0
    if synthetic_height <= 0:
        raise ValueError("Altura útil da porta ficou inválida com a bandeira inferior.")

    # O conjunto OB é aplicado depois. A geometria-base usa a dobradiça 90 mm
    # homologada, sem bandeira, na altura sintética equivalente.
    v14.calculate_gr(_v14_config(
        cfg,
        height_mm=synthetic_height,
        top_flag_height_mm=0.0,
        bottom_flag_height_mm=0.0,
        hinge_description=v09.GR_HINGE_90,
        screen_enabled=False,
    ))


def _replace_door_hardware_with_ob(cfg: GrConfiguration, bom):
    hardware_screws = next(item for item in bom if item.role == "HARDWARE_SCREWS")
    result = [
        item for item in bom if item.role not in {"HINGE_90MM", "HARDWARE_SCREWS"}
    ]
    for code, description, price, role, source in v09._OB_HINGE_COMPONENTS:
        result.append(v09._unit_component(
            code, description, price, role, 1.0, cfg.quantity, source
        ))

    # GR!G119, ORCS 10024: U3=1, P3=1, G5=1.
    # (G105*8)+(G111+G112+G114)*2 = 8+(1+1+4)*2 = 20.
    result.append(replace(
        hardware_screws,
        quantity_per_unit=20.0,
        quantity_order=20.0 * cfg.quantity,
        cost_per_unit_product=round(20.0 * hardware_screws.unit_price, 6),
        source="GR!G119 / ORCS 10024: U3=1, P3=1 => 20 PAR1",
    ))
    return result


def _calculate_phase20(cfg: GrConfiguration) -> CalculationResult:
    _validate_phase20(cfg)

    width = float(cfg.width_mm)
    height = float(cfg.height_mm)
    bottom = float(cfg.bottom_flag_height_mm)
    synthetic_height = height - bottom + 22.0
    divider_count = cfg.bottom_flag_vertical_transoms
    opening_count = divider_count + 1

    base = v14.calculate_gr(_v14_config(
        cfg,
        height_mm=synthetic_height,
        top_flag_height_mm=0.0,
        bottom_flag_height_mm=0.0,
        hinge_description=v09.GR_HINGE_90,
        screen_enabled=False,
    ))

    bom = []
    for item in base.unit_bom:
        if item.role == "FRAME_HEIGHT":
            bom.append(v15._replace_linear(
                item,
                length_mm=height + 3.0,
                source_suffix=" / GR!D9/E9 mantém altura externa total",
            ))
        elif item.role == "INTERNAL_FINISH_HEIGHT":
            bom.append(v15._replace_linear(item, length_mm=height + 140.0))
        elif item.role == "EXTERNAL_FINISH_HEIGHT":
            bom.append(v15._replace_linear(item, length_mm=height + 60.0))
        elif item.role == "FRAME_REINFORCEMENT_HEIGHT":
            bom.append(v15._replace_linear(
                item,
                length_mm=height - 116.0,
                source_suffix=" / GR!D59 com altura total",
            ))
        elif item.role == "REINFORCEMENT_SCREWS":
            continue
        else:
            bom.append(item)
    bom = _replace_door_hardware_with_ob(cfg, bom)

    boundary_length = width - 68.0
    divider_face_mm = 36.0
    total_clear_width = width - 80.0
    opening_width = (
        total_clear_width - divider_count * divider_face_mm
    ) / opening_count
    opening_height = bottom - 58.0
    divider_length = opening_height + 12.0
    glass_width = opening_width - 8.0
    glass_height = opening_height - 8.0

    for name, value in {
        "boundary_length": boundary_length,
        "opening_width": opening_width,
        "opening_height": opening_height,
        "divider_length": divider_length,
        "glass_width": glass_width,
        "glass_height": glass_height,
    }.items():
        if not math.isfinite(value) or value <= 0:
            raise ValueError(
                f"Geometria inválida da subdivisão inferior: {name}={value:g} mm."
            )

    glass, bead_code = v06._glass_and_bead(cfg.glass_description or "")
    bom.extend([
        v06._linear_component(
            "DE6072", "BOTTOM_FLAG_BOUNDARY_TRANSOM", boundary_length, 1.0,
            cfg.quantity, "GR!D19/G19 / AA2>0", category="PERFIS PRINCIPAIS",
        ),
        v06._linear_component(
            "RAG - DE6072", "BOTTOM_FLAG_BOUNDARY_REINFORCEMENT", boundary_length,
            1.0, cfg.quantity, "GR!D63/G63 + LISTAPERFIS!A44", category="REFORÇOS",
        ),
        v06._linear_component(
            "DE6072", "BOTTOM_FLAG_INTERNAL_VERTICAL_TRANSOM", divider_length,
            float(divider_count), cfg.quantity, "GR!D22/G22 / AH2=2",
            category="PERFIS PRINCIPAIS",
        ),
        v06._linear_component(
            "RAG - DE6072", "BOTTOM_FLAG_INTERNAL_VERTICAL_REINFORCEMENT",
            divider_length, float(divider_count), cfg.quantity,
            "PHYSICAL_RULE_DE6072_REINFORCEMENT + GR!D22/G22", category="REFORÇOS",
        ),
        v06._linear_component(
            bead_code, "BOTTOM_FLAG_BEAD_HORIZONTAL", opening_width,
            float(2 * opening_count), cfg.quantity,
            "3 vãos x 2 baguetes horizontais / LEGACY_GR_G25_COUNT_CORRECTED",
        ),
        v06._linear_component(
            bead_code, "BOTTOM_FLAG_BEAD_VERTICAL", opening_height,
            float(2 * opening_count), cfg.quantity,
            "3 vãos x 2 baguetes verticais / LEGACY_GR_G26_COUNT_CORRECTED",
        ),
    ])

    flag_panels = []
    for column in range(opening_count):
        component, raw_panel = v06._glass_component(
            glass, glass_width, glass_height, cfg.quantity
        )
        component = replace(
            component,
            role=f"BOTTOM_FLAG_GLASS_PANEL_{column + 1}",
            source="GR!69 intent + AH2=2 / LEGACY_GR_FLAG_GRID_GLASS_COUNT_CORRECTED",
        )
        bom.append(component)
        flag_panels.append(replace(
            raw_panel,
            source="BOTTOM_FLAG",
            position=f"BOTTOM:R1C{column + 1}",
        ))

    total_glazing_perimeter = (
        2.0 * (opening_width + opening_height) * opening_count
    )
    bom.append(v06._seal_component(
        "ACB606", "BOTTOM_FLAG_GLASS_SEAL", total_glazing_perimeter, 1.0,
        cfg.quantity, "RESOLVED_PHYSICAL_2026-09-22 + 3 fixed glazing perimeters",
    ))

    leaf_width_item = next(item for item in bom if item.role == "LEAF_WIDTH")
    leaf_height_item = next(item for item in bom if item.role == "LEAF_HEIGHT")
    frame_width_cut = width + 5.0
    frame_height_cut = height + 3.0
    base_screws = 4.0 * (
        (frame_width_cut + frame_height_cut) / 1000.0
        + ((leaf_width_item.length_mm + leaf_height_item.length_mm) / 1000.0)
        * leaf_width_item.quantity_per_unit
        + boundary_length / 1000.0
    )
    divider_screws_each = float(math.ceil(divider_length / 400.0))
    total_screws = round(base_screws + divider_count * divider_screws_each, 6)
    screw_template = next(
        item for item in base.unit_bom if item.role == "REINFORCEMENT_SCREWS"
    )
    bom.append(replace(
        screw_template,
        quantity_per_unit=total_screws,
        quantity_order=total_screws * cfg.quantity,
        cost_per_unit_product=round(total_screws * screw_template.unit_price, 6),
        source=(
            "GR!G118 / porta módulo único + bandeira inferior + "
            "PHYSICAL_RULE 2x DE6072 interno: ceil(length/400)"
        ),
    ))

    geometry = dict(base.geometry)
    geometry.update({
        "frame_height_final_mm": round(height, 6),
        "frame_height_cut_mm": round(height + 3.0, 6),
        "frame_reinforcement_height_mm": round(height - 116.0, 6),
        "bottom_flag_height_mm": round(bottom, 6),
        "bottom_flag_boundary_transom_length_mm": round(boundary_length, 6),
        "bottom_flag_vertical_transoms": float(divider_count),
        "bottom_flag_horizontal_transoms": 0.0,
        "bottom_flag_opening_count": float(opening_count),
        "bottom_flag_bead_width_mm": round(opening_width, 6),
        "bottom_flag_bead_height_mm": round(opening_height, 6),
        "bottom_flag_glass_width_mm": round(glass_width, 6),
        "bottom_flag_glass_height_mm": round(glass_height, 6),
        "bottom_flag_internal_vertical_transom_length_mm": round(divider_length, 6),
        "bottom_flag_internal_vertical_reinforcement_screws_added": (
            float(divider_count) * divider_screws_each
        ),
        "bottom_flag_glass_panel_count": float(opening_count),
    })

    openings = tuple(
        GridOpening(
            source="BOTTOM_FLAG",
            row_index=0,
            column_index=column,
            width_mm=round(opening_width, 6),
            height_mm=round(opening_height, 6),
            quantity=1.0,
        )
        for column in range(opening_count)
    )
    fixed = FixedPanelGeometry(
        position=FixedPanelPosition.BOTTOM,
        width_mm=round(width, 6),
        nominal_height_mm=round(bottom, 6),
        frame_height_mm=round(bottom, 6),
        horizontal_transoms=0,
        vertical_transoms=divider_count,
        openings=openings,
    )
    boundary = Transom(
        source="BOTTOM_FLAG_BOUNDARY",
        orientation=TransomOrientation.HORIZONTAL,
        material_code="DE6072",
        reinforcement_material_code="RAG - DE6072",
        length_mm=round(boundary_length, 6),
        quantity=1.0,
    )
    internal_divider = Transom(
        source="BOTTOM_FLAG_INTERNAL",
        orientation=TransomOrientation.VERTICAL,
        material_code="DE6072",
        reinforcement_material_code="RAG - DE6072",
        length_mm=round(divider_length, 6),
        quantity=float(divider_count),
    )

    breakdown = {
        group: round(
            sum(item.cost_per_unit_product for item in bom if item.category == group),
            6,
        )
        for group in v06._GROUPS
    }
    total = round(sum(item.cost_per_unit_product for item in bom), 6)
    breakdown["TOTAL"] = total

    warnings = list(base.warnings)
    warnings.extend([
        EngineeringWarning(
            "LEGACY-GR-BOTTOM-FLAG-HEIGHT-DOUBLE-SUBTRACTION-CORRECTED",
            "GR!D9/K11 subtrai AA2 duas vezes. A v0.20 usa H_folha = H_total - H_bandeira - 15 para porta.",
        ),
        EngineeringWarning(
            "LEGACY-GR-BOTTOM-FLAG-GRID-BAGUETTE-COUNT-CORRECTED",
            "GR!G25/G26 não representa o perímetro físico completo dos três vãos com AH2=2. A v0.20 usa 6 baguetes horizontais e 6 verticais.",
        ),
        EngineeringWarning(
            "LEGACY-GR-BOTTOM-FLAG-GRID-REINFORCEMENT-CORRECTED",
            "GR!G118 omite as travessas verticais internas. A v0.20 inclui 2 RAG-DE6072 e PAR2 a cada 400 mm.",
        ),
        EngineeringWarning(
            "GR-OB-DOOR-HARDWARE-SCOPE",
            "ORCS 10024 comprova porta externa monoponto com DOBRADIÇA SISTEMA OB; GR!105:110 e G119 determinam o conjunto e 20 PAR1.",
        ),
        EngineeringWarning(
            "GR-BOTTOM-FLAG-VERTICAL-GRID-SCOPE",
            "Fase 20 homologa somente 2 divisões verticais na bandeira inferior da porta externa de 1 folha do ORCS 10024.",
        ),
    ])

    return CalculationResult(
        model_description=(
            base.model_description
            + " + BANDEIRA INFERIOR COM 2 DIVISÕES VERTICAIS + DOBRADIÇA SISTEMA OB"
        ),
        geometry=geometry,
        unit_bom=bom,
        cost_breakdown=breakdown,
        unit_cost=total,
        leaf_openings=list(base.leaf_openings),
        transoms=[*base.transoms, boundary, internal_divider],
        fixed_panels=[*base.fixed_panels, fixed],
        glass_panels=[*base.glass_panels, *flag_panels],
        warnings=warnings,
        calculation_version=GR_ENGINE_VERSION,
    )


def calculate_gr(cfg: GrConfiguration) -> CalculationResult:
    """GR v0.20: v0.19 + AH=2 na bandeira inferior do ORCS 10024."""
    if _is_phase20_bottom_grid(cfg):
        return _calculate_phase20(cfg)
    return _promote(v19.calculate_gr(_v19_config(cfg)))
