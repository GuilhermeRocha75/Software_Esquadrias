from __future__ import annotations

from dataclasses import fields, replace
import math

from . import gr_v06 as v06
from . import gr_v14 as v14
from . import gr_v15 as v15
from .models import (
    CalculationResult,
    EngineeringWarning,
    FixedPanelGeometry,
    FixedPanelPosition,
    GridOpening,
    Transom,
    TransomOrientation,
)


GR_ENGINE_VERSION = "GR_ENGINE_0.16.0"
GrConfiguration = v15.GrConfiguration

GR_GLASS_MODE = v06.GR_GLASS_MODE
GR_APPLICATION_DOOR = v06.GR_APPLICATION_DOOR
GR_LEAF_SYSTEM_INTERNAL = v06.GR_LEAF_SYSTEM_INTERNAL
GR_HINGE_90 = v06.GR_HINGE


def _v14_config(cfg: GrConfiguration, **overrides) -> v14.GrConfiguration:
    data = {field.name: getattr(cfg, field.name) for field in fields(v14.GrConfiguration)}
    data.update(overrides)
    return v14.GrConfiguration(**data)


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


def _is_two_leaf_top_flag(cfg: GrConfiguration) -> bool:
    return cfg.top_flag_height_mm > 0 and cfg.bottom_flag_height_mm == 0 and cfg.leaf_count == 2


def _validate_two_leaf_top_flag(cfg: GrConfiguration) -> None:
    if cfg.application != GR_APPLICATION_DOOR:
        raise ValueError("Fase 16 exige aplicação PORTA.")
    if cfg.leaf_system != GR_LEAF_SYSTEM_INTERNAL:
        raise ValueError(
            "Fase 16 homologa bandeira superior em 2 folhas somente para abertura interna."
        )
    if cfg.panel_mode != GR_GLASS_MODE:
        raise ValueError("Fase 16 exige VIDRO INTEIRO.")
    if cfg.hinge_description != GR_HINGE_90:
        raise ValueError("Fase 16 exige DOBRADIÇA 90MM.")
    if cfg.shutter is not None or cfg.shutter_enabled or cfg.screen_enabled:
        raise ValueError("Fase 16 não combina bandeira de 2 folhas com persiana/tela.")
    if cfg.leaf_horizontal_transoms or cfg.leaf_vertical_transoms:
        raise ValueError("Fase 16 exige folhas sem travessas internas.")
    if cfg.structural_reinforcement is not None:
        raise ValueError("Fase 16 não combina reforço estrutural opcional.")
    if not cfg.glass_description:
        raise ValueError("Fase 16 exige vidro informado.")
    v06._glass_and_bead(cfg.glass_description)

    top = float(cfg.top_flag_height_mm)
    if not math.isfinite(top) or top <= 66:
        raise ValueError("Altura da bandeira superior deve gerar vidro positivo.")

    synthetic_height = float(cfg.height_mm) - top + 22.0
    if synthetic_height <= 0:
        raise ValueError("Altura útil da porta ficou inválida com a bandeira.")

    # Reusa exatamente a porta de 2 folhas/vidro já homologada, removendo
    # temporariamente a bandeira. Hs=H-top+22 reproduz GR!J11 => H-top-15.
    v14.calculate_gr(_v14_config(
        cfg,
        height_mm=synthetic_height,
        top_flag_height_mm=0.0,
        bottom_flag_height_mm=0.0,
        screen_enabled=False,
    ))


def _calculate_two_leaf_top_flag(cfg: GrConfiguration) -> CalculationResult:
    _validate_two_leaf_top_flag(cfg)

    width = float(cfg.width_mm)
    height = float(cfg.height_mm)
    top = float(cfg.top_flag_height_mm)
    synthetic_height = height - top + 22.0

    base = v14.calculate_gr(_v14_config(
        cfg,
        height_mm=synthetic_height,
        top_flag_height_mm=0.0,
        bottom_flag_height_mm=0.0,
        screen_enabled=False,
    ))

    bom = []
    for item in base.unit_bom:
        if item.role == "FRAME_HEIGHT":
            bom.append(v15._replace_linear(
                item, length_mm=height + 3.0,
                source_suffix=" / GR!D9/E9 mantém altura total",
            ))
        elif item.role == "INTERNAL_FINISH_HEIGHT":
            bom.append(v15._replace_linear(item, length_mm=height + 140.0))
        elif item.role == "EXTERNAL_FINISH_HEIGHT":
            bom.append(v15._replace_linear(item, length_mm=height + 60.0))
        elif item.role == "FRAME_REINFORCEMENT_HEIGHT":
            bom.append(v15._replace_linear(
                item, length_mm=height - 116.0,
                source_suffix=" / GR!D59 com altura total",
            ))
        elif item.role == "REINFORCEMENT_SCREWS":
            continue
        else:
            bom.append(item)

    boundary_length = width - 68.0
    flag_bead_width = width - 80.0
    flag_bead_height = top - 58.0
    flag_glass_width = flag_bead_width - 8.0
    flag_glass_height = flag_bead_height - 8.0

    for name, value in {
        "boundary_length": boundary_length,
        "flag_bead_width": flag_bead_width,
        "flag_bead_height": flag_bead_height,
        "flag_glass_width": flag_glass_width,
        "flag_glass_height": flag_glass_height,
    }.items():
        if value <= 0 or not math.isfinite(value):
            raise ValueError(f"Geometria inválida da bandeira superior: {name}={value:g} mm.")

    glass, bead_code = v06._glass_and_bead(cfg.glass_description or "")

    bom.extend([
        v06._linear_component(
            "DE6072", "TOP_FLAG_BOUNDARY_TRANSOM", boundary_length, 1.0,
            cfg.quantity, "GR!D19/G19 + PFAB!B18",
            category="PERFIS PRINCIPAIS",
        ),
        v06._linear_component(
            "RAG - DE6072", "TOP_FLAG_BOUNDARY_REINFORCEMENT", boundary_length, 1.0,
            cfg.quantity, "GR!D63/G63 + LISTAPERFIS!A44",
            category="REFORÇOS",
        ),
        v06._linear_component(
            bead_code, "TOP_FLAG_BEAD_HORIZONTAL", flag_bead_width, 2.0,
            cfg.quantity, "GR!27:28 intent + shared Design fixed-panel topology",
        ),
        v06._linear_component(
            bead_code, "TOP_FLAG_BEAD_VERTICAL", flag_bead_height, 2.0,
            cfg.quantity, "GR!27:28 + LEGACY_GR_FLAG_E40_REFERENCE_CORRECTED",
        ),
    ])

    flag_component, raw_panel = v06._glass_component(
        glass, flag_glass_width, flag_glass_height, cfg.quantity
    )
    flag_component = replace(
        flag_component,
        role="TOP_FLAG_GLASS_PANEL",
        source="GR!70 intent + shared Design fixed-panel topology",
    )
    flag_panel = replace(raw_panel, source="TOP_FLAG", position="TOP:R1C1")
    bom.append(flag_component)

    flag_perimeter = 2.0 * (flag_bead_width + flag_bead_height)
    bom.append(v06._seal_component(
        "ACB606", "TOP_FLAG_GLASS_SEAL", flag_perimeter, 1.0,
        cfg.quantity, "RESOLVED_PHYSICAL_2026-09-22 + fixed glazing perimeter",
    ))

    leaf_width_item = next(x for x in bom if x.role == "LEAF_WIDTH")
    leaf_height_item = next(x for x in bom if x.role == "LEAF_HEIGHT")
    frame_width_cut = width + 5.0
    frame_height_cut = height + 3.0
    leaf_piece_qty = leaf_width_item.quantity_per_unit

    # GR!G118:
    # (((E8+E9)/1000)*G8)*4 + (((E10+E11)/1000)*G10)*4
    # + ((E19/1000)*G19)*4. Em porta módulo único: G8=1; em 2 folhas: G10=4.
    reinforcement_screws = 4.0 * (
        (frame_width_cut + frame_height_cut) / 1000.0
        + ((leaf_width_item.length_mm + leaf_height_item.length_mm) / 1000.0)
        * leaf_piece_qty
        + boundary_length / 1000.0
    )
    screw_template = next(
        x for x in base.unit_bom if x.role == "REINFORCEMENT_SCREWS"
    )
    bom.append(replace(
        screw_template,
        quantity_per_unit=reinforcement_screws,
        quantity_order=reinforcement_screws * cfg.quantity,
        cost_per_unit_product=round(reinforcement_screws * screw_template.unit_price, 6),
        source="GR!G118 / G8=1, G10=4, G19=1",
    ))

    geometry = dict(base.geometry)
    geometry.update({
        "frame_height_final_mm": round(height, 6),
        "frame_height_cut_mm": round(height + 3.0, 6),
        "top_flag_height_mm": round(top, 6),
        "top_flag_boundary_transom_length_mm": round(boundary_length, 6),
        "top_flag_bead_width_mm": round(flag_bead_width, 6),
        "top_flag_bead_height_mm": round(flag_bead_height, 6),
        "top_flag_glass_width_mm": round(flag_glass_width, 6),
        "top_flag_glass_height_mm": round(flag_glass_height, 6),
    })

    opening = GridOpening(
        source="TOP_FLAG", row_index=0, column_index=0,
        width_mm=round(flag_bead_width, 6),
        height_mm=round(flag_bead_height, 6),
        quantity=1.0,
    )
    fixed = FixedPanelGeometry(
        position=FixedPanelPosition.TOP,
        width_mm=round(width, 6),
        nominal_height_mm=round(top, 6),
        frame_height_mm=round(top, 6),
        horizontal_transoms=0,
        vertical_transoms=0,
        openings=(opening,),
    )
    boundary = Transom(
        source="TOP_FLAG_BOUNDARY",
        orientation=TransomOrientation.HORIZONTAL,
        material_code="DE6072",
        reinforcement_material_code="RAG - DE6072",
        length_mm=round(boundary_length, 6),
        quantity=1.0,
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
            "LEGACY-GR-FLAG-E40-REFERENCE-CORRECTED",
            "A abertura da bandeira usa a topologia física DE6058+DE6072 já homologada: W-80 por H-58.",
        ),
        EngineeringWarning(
            "GR-TOP-FLAG-TWO-LEAF-SCOPE",
            "Fase 16 homologa bandeira superior simples em porta interna de 2 folhas, sem subdivisão.",
        ),
    ])

    return CalculationResult(
        model_description=base.model_description + " + BANDEIRA SUPERIOR",
        geometry=geometry,
        unit_bom=bom,
        cost_breakdown=breakdown,
        unit_cost=total,
        leaf_openings=list(base.leaf_openings),
        transoms=[*base.transoms, boundary],
        fixed_panels=[*base.fixed_panels, fixed],
        glass_panels=[*base.glass_panels, flag_panel],
        warnings=warnings,
        calculation_version=GR_ENGINE_VERSION,
    )


def calculate_gr(cfg: GrConfiguration) -> CalculationResult:
    """GR v0.16: v0.15 + bandeira superior simples em porta interna 2 folhas."""
    if _is_two_leaf_top_flag(cfg):
        return _calculate_two_leaf_top_flag(cfg)
    return _promote(v15.calculate_gr(cfg))
