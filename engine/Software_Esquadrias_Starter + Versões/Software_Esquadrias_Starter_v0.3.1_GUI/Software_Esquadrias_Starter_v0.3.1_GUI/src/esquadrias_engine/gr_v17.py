from __future__ import annotations

from dataclasses import fields, replace
import math

from . import gr_v06 as v06
from . import gr_v14 as v14
from . import gr_v15 as v15
from . import gr_v16 as v16
from .models import (
    CalculationResult,
    EngineeringWarning,
    FixedPanelGeometry,
    FixedPanelPosition,
    GridOpening,
    Transom,
    TransomOrientation,
)


GR_ENGINE_VERSION = "GR_ENGINE_0.17.0"
GrConfiguration = v16.GrConfiguration

GR_GLASS_MODE = v06.GR_GLASS_MODE
GR_APPLICATION_WINDOW = v06.GR_APPLICATION_WINDOW
GR_LEAF_SYSTEM_WINDOW = v06.GR_LEAF_SYSTEM_WINDOW_EXTERNAL


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


def _is_simple_bottom_flag(cfg: GrConfiguration) -> bool:
    return cfg.bottom_flag_height_mm > 0 and cfg.top_flag_height_mm == 0


def _validate_simple_bottom_flag(cfg: GrConfiguration) -> None:
    if cfg.application != GR_APPLICATION_WINDOW:
        raise ValueError("Fase 17 homologa bandeira inferior inicialmente somente em JANELA.")
    if cfg.leaf_count != 1:
        raise ValueError("Fase 17 homologa bandeira inferior somente em janela de 1 folha.")
    if cfg.leaf_system != GR_LEAF_SYSTEM_WINDOW:
        raise ValueError("Fase 17 exige folha de janela Design 60x78 abertura externa.")
    if cfg.panel_mode != GR_GLASS_MODE:
        raise ValueError("Fase 17 exige VIDRO INTEIRO.")
    if cfg.shutter is not None or cfg.shutter_enabled or cfg.screen_enabled:
        raise ValueError("Fase 17 ainda não combina bandeira inferior com persiana/tela.")
    if cfg.leaf_horizontal_transoms or cfg.leaf_vertical_transoms:
        raise ValueError("Fase 17 exige folha sem travessas internas adicionais.")
    if cfg.structural_reinforcement is not None:
        raise ValueError("Fase 17 ainda não combina reforço estrutural opcional.")
    if not cfg.glass_description:
        raise ValueError("Fase 17 exige vidro informado.")
    v06._glass_and_bead(cfg.glass_description)

    bottom = float(cfg.bottom_flag_height_mm)
    if not math.isfinite(bottom) or bottom <= 66.0:
        raise ValueError("Altura da bandeira inferior deve gerar vidro positivo.")

    synthetic_height = float(cfg.height_mm) - bottom + 22.0
    if synthetic_height <= 0:
        raise ValueError("Altura útil da janela ficou inválida com a bandeira inferior.")

    # A janela sem bandeira tem H_folha = H - 64.
    # Hs = H - bandeira + 22 reproduz a topologia física com uma face de marco
    # (40 mm), uma travessa DE6072 (18 mm) e dois overlaps de 8 mm:
    # H_folha = H - bandeira - 42.
    v14.calculate_gr(_v14_config(
        cfg,
        height_mm=synthetic_height,
        top_flag_height_mm=0.0,
        bottom_flag_height_mm=0.0,
        screen_enabled=False,
    ))


def _calculate_simple_bottom_flag(cfg: GrConfiguration) -> CalculationResult:
    _validate_simple_bottom_flag(cfg)

    width = float(cfg.width_mm)
    height = float(cfg.height_mm)
    bottom = float(cfg.bottom_flag_height_mm)
    synthetic_height = height - bottom + 22.0

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
                item,
                length_mm=height + 5.0,
                source_suffix=" / GR!E9 janela mantém altura externa total",
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

    boundary_length = width - 68.0
    flag_bead_width = width - 80.0
    flag_bead_height = bottom - 58.0
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
            raise ValueError(f"Geometria inválida da bandeira inferior: {name}={value:g} mm.")

    glass, bead_code = v06._glass_and_bead(cfg.glass_description or "")

    bom.extend([
        v06._linear_component(
            "DE6072", "BOTTOM_FLAG_BOUNDARY_TRANSOM", boundary_length, 1.0,
            cfg.quantity, "GR!D19/G19 / AA2>0",
            category="PERFIS PRINCIPAIS",
        ),
        v06._linear_component(
            "RAG - DE6072", "BOTTOM_FLAG_BOUNDARY_REINFORCEMENT", boundary_length, 1.0,
            cfg.quantity, "GR!D63/G63 + LISTAPERFIS!A44",
            category="REFORÇOS",
        ),
        v06._linear_component(
            bead_code, "BOTTOM_FLAG_BEAD_HORIZONTAL", flag_bead_width, 2.0,
            cfg.quantity, "GR!25:26 intent + shared Design fixed-panel topology",
        ),
        v06._linear_component(
            bead_code, "BOTTOM_FLAG_BEAD_VERTICAL", flag_bead_height, 2.0,
            cfg.quantity, "GR!25:26 + LEGACY_GR_FLAG_E40_REFERENCE_CORRECTED",
        ),
    ])

    flag_component, raw_panel = v06._glass_component(
        glass, flag_glass_width, flag_glass_height, cfg.quantity
    )
    flag_component = replace(
        flag_component,
        role="BOTTOM_FLAG_GLASS_PANEL",
        source="GR!68:70 intent + shared Design fixed-panel topology",
    )
    flag_panel = replace(
        raw_panel,
        source="BOTTOM_FLAG",
        position="BOTTOM:R1C1",
    )
    bom.append(flag_component)

    flag_perimeter = 2.0 * (flag_bead_width + flag_bead_height)
    bom.append(v06._seal_component(
        "ACB606", "BOTTOM_FLAG_GLASS_SEAL", flag_perimeter, 1.0,
        cfg.quantity, "RESOLVED_PHYSICAL_2026-09-22 + fixed glazing perimeter",
    ))

    leaf_width_item = next(x for x in bom if x.role == "LEAF_WIDTH")
    leaf_height_item = next(x for x in bom if x.role == "LEAF_HEIGHT")
    frame_width_cut = width + 5.0
    frame_height_cut = height + 5.0

    # GR!G118 no recorte de janela 1 folha, módulo único:
    # G8=2, G10=2 e G19=1.
    reinforcement_screws = 4.0 * (
        ((frame_width_cut + frame_height_cut) / 1000.0) * 2.0
        + ((leaf_width_item.length_mm + leaf_height_item.length_mm) / 1000.0)
        * leaf_width_item.quantity_per_unit
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
        source="GR!G118 / janela: G8=2, G10=2, G19=1",
    ))

    geometry = dict(base.geometry)
    geometry.update({
        "frame_height_final_mm": round(height, 6),
        "frame_height_cut_mm": round(height + 5.0, 6),
        "bottom_flag_height_mm": round(bottom, 6),
        "bottom_flag_boundary_transom_length_mm": round(boundary_length, 6),
        "bottom_flag_bead_width_mm": round(flag_bead_width, 6),
        "bottom_flag_bead_height_mm": round(flag_bead_height, 6),
        "bottom_flag_glass_width_mm": round(flag_glass_width, 6),
        "bottom_flag_glass_height_mm": round(flag_glass_height, 6),
    })

    opening = GridOpening(
        source="BOTTOM_FLAG",
        row_index=0,
        column_index=0,
        width_mm=round(flag_bead_width, 6),
        height_mm=round(flag_bead_height, 6),
        quantity=1.0,
    )
    fixed = FixedPanelGeometry(
        position=FixedPanelPosition.BOTTOM,
        width_mm=round(width, 6),
        nominal_height_mm=round(bottom, 6),
        frame_height_mm=round(bottom, 6),
        horizontal_transoms=0,
        vertical_transoms=0,
        openings=(opening,),
    )
    boundary = Transom(
        source="BOTTOM_FLAG_BOUNDARY",
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
            "LEGACY-GR-BOTTOM-FLAG-HEIGHT-DOUBLE-SUBTRACTION-CORRECTED",
            "GR!D9 e GR!J11 subtraem AA2 duas vezes no caminho legado. A v0.17 usa a topologia física DE6058+DE6072: H_folha = H_total - H_bandeira - 42.",
        ),
        EngineeringWarning(
            "LEGACY-GR-FLAG-E40-REFERENCE-CORRECTED",
            "GR!26 referencia LISTAPERFIS!E40 vazio. A abertura fixa usa a topologia Design já homologada: W-80 por H-58.",
        ),
        EngineeringWarning(
            "GR-BOTTOM-FLAG-SIMPLE-SCOPE",
            "Fase 17 homologa bandeira inferior simples em janela GR 1 folha, sem subdivisões, tela ou persiana.",
        ),
    ])

    return CalculationResult(
        model_description=base.model_description + " + BANDEIRA INFERIOR",
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
    """GR v0.17: v0.16 + bandeira inferior simples em janela 1 folha."""
    if _is_simple_bottom_flag(cfg):
        return _calculate_simple_bottom_flag(cfg)
    return _promote(v16.calculate_gr(cfg))
