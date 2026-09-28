from __future__ import annotations

from dataclasses import fields, replace
import math

from . import gr_v06 as v06
from . import gr_v14 as v14
from . import gr_v15 as v15
from . import gr_v17 as v17
from .models import (
    CalculationResult,
    EngineeringWarning,
    FixedPanelGeometry,
    FixedPanelPosition,
    GridOpening,
    Transom,
    TransomOrientation,
)


GR_ENGINE_VERSION = "GR_ENGINE_0.18.0"
GrConfiguration = v17.GrConfiguration

GR_GLASS_MODE = v06.GR_GLASS_MODE
GR_APPLICATION_WINDOW = v06.GR_APPLICATION_WINDOW
GR_LEAF_SYSTEM_WINDOW = v06.GR_LEAF_SYSTEM_WINDOW_EXTERNAL
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


def _is_dual_flag(cfg: GrConfiguration) -> bool:
    return cfg.bottom_flag_height_mm > 0 and cfg.top_flag_height_mm > 0


def _validate_dual_flag(cfg: GrConfiguration) -> None:
    if cfg.application != GR_APPLICATION_WINDOW:
        raise ValueError("Fase 18 homologa bandeiras inferior + superior inicialmente somente em JANELA.")
    if cfg.leaf_count != 1:
        raise ValueError("Fase 18 homologa bandeiras inferior + superior somente em janela de 1 folha.")
    if cfg.leaf_system != GR_LEAF_SYSTEM_WINDOW:
        raise ValueError("Fase 18 exige folha de janela Design 60x78 abertura externa.")
    if cfg.panel_mode != GR_GLASS_MODE:
        raise ValueError("Fase 18 exige VIDRO INTEIRO.")
    if cfg.hinge_description != GR_HINGE_90:
        raise ValueError("Fase 18 homologa inicialmente somente DOBRADIÇA 90MM.")
    if cfg.shutter is not None or cfg.shutter_enabled or cfg.screen_enabled:
        raise ValueError("Fase 18 não combina bandeiras simultâneas com persiana/tela.")
    if cfg.leaf_horizontal_transoms or cfg.leaf_vertical_transoms:
        raise ValueError("Fase 18 exige folha sem travessas internas adicionais.")
    if cfg.structural_reinforcement is not None:
        raise ValueError("Fase 18 não combina reforço estrutural opcional.")
    if not cfg.glass_description:
        raise ValueError("Fase 18 exige vidro informado.")
    v06._glass_and_bead(cfg.glass_description)

    bottom = float(cfg.bottom_flag_height_mm)
    top = float(cfg.top_flag_height_mm)
    if not math.isfinite(bottom) or not math.isfinite(top):
        raise ValueError("Alturas das bandeiras devem ser finitas.")
    if bottom <= 66.0 or top <= 66.0:
        raise ValueError("Cada bandeira deve gerar vidro positivo.")

    synthetic_height = float(cfg.height_mm) - bottom - top + 22.0
    if synthetic_height <= 0:
        raise ValueError("Altura útil da janela ficou inválida com as duas bandeiras.")

    # Janela sem bandeira: H_folha = H - 64.
    # Hs = H - inferior - superior + 22 => H_folha físico =
    # H_total - inferior - superior - 42.
    v14.calculate_gr(_v14_config(
        cfg,
        height_mm=synthetic_height,
        top_flag_height_mm=0.0,
        bottom_flag_height_mm=0.0,
        screen_enabled=False,
    ))


def _flag_geometry(width: float, height: float) -> tuple[float, float, float, float, float]:
    boundary_length = width - 68.0
    bead_width = width - 80.0
    bead_height = height - 58.0
    glass_width = bead_width - 8.0
    glass_height = bead_height - 8.0
    for name, value in {
        "boundary_length": boundary_length,
        "bead_width": bead_width,
        "bead_height": bead_height,
        "glass_width": glass_width,
        "glass_height": glass_height,
    }.items():
        if value <= 0 or not math.isfinite(value):
            raise ValueError(f"Geometria inválida da bandeira: {name}={value:g} mm.")
    return boundary_length, bead_width, bead_height, glass_width, glass_height


def _calculate_dual_flag(cfg: GrConfiguration) -> CalculationResult:
    _validate_dual_flag(cfg)

    width = float(cfg.width_mm)
    height = float(cfg.height_mm)
    bottom = float(cfg.bottom_flag_height_mm)
    top = float(cfg.top_flag_height_mm)
    synthetic_height = height - bottom - top + 22.0

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

    (
        bottom_boundary,
        bottom_bead_width,
        bottom_bead_height,
        bottom_glass_width,
        bottom_glass_height,
    ) = _flag_geometry(width, bottom)
    (
        top_boundary,
        top_bead_width,
        top_bead_height,
        top_glass_width,
        top_glass_height,
    ) = _flag_geometry(width, top)

    glass, bead_code = v06._glass_and_bead(cfg.glass_description or "")

    for prefix, boundary, bead_width, bead_height in (
        ("BOTTOM", bottom_boundary, bottom_bead_width, bottom_bead_height),
        ("TOP", top_boundary, top_bead_width, top_bead_height),
    ):
        bom.extend([
            v06._linear_component(
                "DE6072", f"{prefix}_FLAG_BOUNDARY_TRANSOM", boundary, 1.0,
                cfg.quantity, "GR!D19/G19 / J19+K19",
                category="PERFIS PRINCIPAIS",
            ),
            v06._linear_component(
                "RAG - DE6072", f"{prefix}_FLAG_BOUNDARY_REINFORCEMENT", boundary, 1.0,
                cfg.quantity, "GR!D63/G63 + LISTAPERFIS!A44",
                category="REFORÇOS",
            ),
            v06._linear_component(
                bead_code, f"{prefix}_FLAG_BEAD_HORIZONTAL", bead_width, 2.0,
                cfg.quantity, "GR!25:28 intent + shared Design fixed-panel topology",
            ),
            v06._linear_component(
                bead_code, f"{prefix}_FLAG_BEAD_VERTICAL", bead_height, 2.0,
                cfg.quantity, "GR!25:28 + LEGACY_GR_FLAG_E40_REFERENCE_CORRECTED",
            ),
        ])

    bottom_component, bottom_raw_panel = v06._glass_component(
        glass, bottom_glass_width, bottom_glass_height, cfg.quantity
    )
    bottom_component = replace(
        bottom_component,
        role="BOTTOM_FLAG_GLASS_PANEL",
        source="GR!69 intent + shared Design fixed-panel topology",
    )
    bottom_panel = replace(
        bottom_raw_panel,
        source="BOTTOM_FLAG",
        position="BOTTOM:R1C1",
    )
    bom.append(bottom_component)

    top_component, top_raw_panel = v06._glass_component(
        glass, top_glass_width, top_glass_height, cfg.quantity
    )
    top_component = replace(
        top_component,
        role="TOP_FLAG_GLASS_PANEL",
        source="GR!70 intent + shared Design fixed-panel topology",
    )
    top_panel = replace(
        top_raw_panel,
        source="TOP_FLAG",
        position="TOP:R1C1",
    )
    bom.append(top_component)

    bom.extend([
        v06._seal_component(
            "ACB606", "BOTTOM_FLAG_GLASS_SEAL",
            2.0 * (bottom_bead_width + bottom_bead_height),
            1.0, cfg.quantity,
            "RESOLVED_PHYSICAL_2026-09-22 + fixed glazing perimeter",
        ),
        v06._seal_component(
            "ACB606", "TOP_FLAG_GLASS_SEAL",
            2.0 * (top_bead_width + top_bead_height),
            1.0, cfg.quantity,
            "RESOLVED_PHYSICAL_2026-09-22 + fixed glazing perimeter",
        ),
    ])

    leaf_width_item = next(x for x in bom if x.role == "LEAF_WIDTH")
    leaf_height_item = next(x for x in bom if x.role == "LEAF_HEIGHT")
    frame_width_cut = width + 5.0
    frame_height_cut = height + 5.0

    # GR!G118 / módulo único / janela 1 folha:
    # G8=2, G10=2, G19=J19+K19=2.
    reinforcement_screws = 4.0 * (
        ((frame_width_cut + frame_height_cut) / 1000.0) * 2.0
        + ((leaf_width_item.length_mm + leaf_height_item.length_mm) / 1000.0)
        * leaf_width_item.quantity_per_unit
        + ((bottom_boundary + top_boundary) / 1000.0)
    )
    screw_template = next(
        x for x in base.unit_bom if x.role == "REINFORCEMENT_SCREWS"
    )
    bom.append(replace(
        screw_template,
        quantity_per_unit=reinforcement_screws,
        quantity_order=reinforcement_screws * cfg.quantity,
        cost_per_unit_product=round(reinforcement_screws * screw_template.unit_price, 6),
        source="GR!G118 / janela: G8=2, G10=2, G19=2",
    ))

    geometry = dict(base.geometry)
    geometry.update({
        "frame_height_final_mm": round(height, 6),
        "frame_height_cut_mm": round(height + 5.0, 6),
        "bottom_flag_height_mm": round(bottom, 6),
        "top_flag_height_mm": round(top, 6),
        "bottom_flag_boundary_transom_length_mm": round(bottom_boundary, 6),
        "top_flag_boundary_transom_length_mm": round(top_boundary, 6),
        "bottom_flag_bead_width_mm": round(bottom_bead_width, 6),
        "bottom_flag_bead_height_mm": round(bottom_bead_height, 6),
        "top_flag_bead_width_mm": round(top_bead_width, 6),
        "top_flag_bead_height_mm": round(top_bead_height, 6),
        "bottom_flag_glass_width_mm": round(bottom_glass_width, 6),
        "bottom_flag_glass_height_mm": round(bottom_glass_height, 6),
        "top_flag_glass_width_mm": round(top_glass_width, 6),
        "top_flag_glass_height_mm": round(top_glass_height, 6),
        "flag_boundary_transom_count": 2.0,
    })

    bottom_opening = GridOpening(
        source="BOTTOM_FLAG",
        row_index=0,
        column_index=0,
        width_mm=round(bottom_bead_width, 6),
        height_mm=round(bottom_bead_height, 6),
        quantity=1.0,
    )
    top_opening = GridOpening(
        source="TOP_FLAG",
        row_index=0,
        column_index=0,
        width_mm=round(top_bead_width, 6),
        height_mm=round(top_bead_height, 6),
        quantity=1.0,
    )
    bottom_fixed = FixedPanelGeometry(
        position=FixedPanelPosition.BOTTOM,
        width_mm=round(width, 6),
        nominal_height_mm=round(bottom, 6),
        frame_height_mm=round(bottom, 6),
        horizontal_transoms=0,
        vertical_transoms=0,
        openings=(bottom_opening,),
    )
    top_fixed = FixedPanelGeometry(
        position=FixedPanelPosition.TOP,
        width_mm=round(width, 6),
        nominal_height_mm=round(top, 6),
        frame_height_mm=round(top, 6),
        horizontal_transoms=0,
        vertical_transoms=0,
        openings=(top_opening,),
    )
    bottom_transom = Transom(
        source="BOTTOM_FLAG_BOUNDARY",
        orientation=TransomOrientation.HORIZONTAL,
        material_code="DE6072",
        reinforcement_material_code="RAG - DE6072",
        length_mm=round(bottom_boundary, 6),
        quantity=1.0,
    )
    top_transom = Transom(
        source="TOP_FLAG_BOUNDARY",
        orientation=TransomOrientation.HORIZONTAL,
        material_code="DE6072",
        reinforcement_material_code="RAG - DE6072",
        length_mm=round(top_boundary, 6),
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
            "LEGACY-GR-DUAL-FLAG-HEIGHT-DOUBLE-SUBTRACTION-CORRECTED",
            "GR!D9 e GR!K11 voltam a subtrair AA2+AB2 no caminho legado. A v0.18 compõe fisicamente as duas bandeiras: H_folha = H_total - H_inferior - H_superior - 42.",
        ),
        EngineeringWarning(
            "LEGACY-GR-FLAG-E40-REFERENCE-CORRECTED",
            "GR!26/28 referencia LISTAPERFIS!E40 vazio. Ambos os fixos usam a topologia Design homologada: W-80 por H-58.",
        ),
        EngineeringWarning(
            "GR-DUAL-FLAG-SIMPLE-SCOPE",
            "Fase 18 homologa bandeiras inferior e superior simples simultâneas em janela GR 1 folha, sem subdivisões, tela ou persiana.",
        ),
    ])

    return CalculationResult(
        model_description=base.model_description + " + BANDEIRA INFERIOR E SUPERIOR",
        geometry=geometry,
        unit_bom=bom,
        cost_breakdown=breakdown,
        unit_cost=total,
        leaf_openings=list(base.leaf_openings),
        transoms=[*base.transoms, bottom_transom, top_transom],
        fixed_panels=[*base.fixed_panels, bottom_fixed, top_fixed],
        glass_panels=[*base.glass_panels, bottom_panel, top_panel],
        warnings=warnings,
        calculation_version=GR_ENGINE_VERSION,
    )


def calculate_gr(cfg: GrConfiguration) -> CalculationResult:
    """GR v0.18: v0.17 + bandeiras inferior e superior simultâneas."""
    if _is_dual_flag(cfg):
        return _calculate_dual_flag(cfg)
    return _promote(v17.calculate_gr(cfg))
