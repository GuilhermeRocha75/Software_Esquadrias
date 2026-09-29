from __future__ import annotations

from dataclasses import fields, replace
import math

from . import gr as legacy
from . import gr_v06 as v06
from . import gr_v14 as v14
from . import gr_v21 as v21
from .models import (
    CalculationResult,
    EngineeringWarning,
    FixedPanelGeometry,
    FixedPanelPosition,
    GridOpening,
    Transom,
    TransomOrientation,
)


GR_ENGINE_VERSION = "GR_ENGINE_0.22.0"
GrConfiguration = v21.GrConfiguration


def _v21_config(cfg: GrConfiguration, **overrides) -> v21.GrConfiguration:
    data = {field.name: getattr(cfg, field.name) for field in fields(v21.GrConfiguration)}
    data.update(overrides)
    return v21.GrConfiguration(**data)


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


def _is_phase22_screen_grid(cfg: GrConfiguration) -> bool:
    return (
        cfg.screen_enabled
        and cfg.bottom_flag_vertical_transoms == 1
        and cfg.bottom_flag_horizontal_transoms == 0
        and cfg.top_flag_vertical_transoms == 0
        and cfg.top_flag_horizontal_transoms == 0
    )


def _validate_phase22(cfg: GrConfiguration) -> None:
    counts = (
        cfg.bottom_flag_vertical_transoms,
        cfg.bottom_flag_horizontal_transoms,
        cfg.top_flag_vertical_transoms,
        cfg.top_flag_horizontal_transoms,
    )
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in counts):
        raise ValueError("Divisões de bandeira GR devem ser inteiros maiores ou iguais a zero.")
    if not _is_phase22_screen_grid(cfg):
        raise ValueError(
            "GR_ENGINE_0.22.0 homologa tela com bandeira somente no recorte AH=1 da Fase 22."
        )
    if cfg.bottom_flag_height_mm <= 0 or cfg.top_flag_height_mm != 0:
        raise ValueError("Fase 22 exige somente bandeira inferior.")
    if cfg.application != v06.GR_APPLICATION_WINDOW:
        raise ValueError("Fase 22 exige aplicação JANELA.")
    if cfg.leaf_count != 2:
        raise ValueError("Fase 22 exige janela de 2 folhas.")
    if cfg.leaf_system != v06.GR_LEAF_SYSTEM_WINDOW_EXTERNAL:
        raise ValueError("Fase 22 exige folha de janela Design 60x78 abertura externa.")
    if cfg.panel_mode != v06.GR_GLASS_MODE:
        raise ValueError("Fase 22 exige VIDRO INTEIRO.")
    if cfg.hinge_description != v06.GR_HINGE:
        raise ValueError("Fase 22 exige DOBRADIÇA 90MM.")
    if cfg.closure_mode != v06.GR_CLOSURE_WINDOW_CREMONA:
        raise ValueError("Fase 22 exige maçaneta com cremona sem chave.")
    if cfg.cremona_description not in (None, v06.GR_CREMONA_WINDOW_800):
        raise ValueError("Fase 22 suporta somente cremona padrão de 800mm E:15mm.")
    if cfg.shutter is not None or cfg.shutter_enabled:
        raise ValueError("Fase 22 não combina a tela/bandeira com persiana.")
    if cfg.leaf_horizontal_transoms or cfg.leaf_vertical_transoms:
        raise ValueError("Fase 22 exige folhas sem travessas internas adicionais.")
    if cfg.structural_reinforcement is not None:
        raise ValueError("Fase 22 não combina reforço estrutural opcional.")
    if not cfg.glass_description:
        raise ValueError("Fase 22 exige vidro informado.")
    v06._glass_and_bead(cfg.glass_description)

    width = float(cfg.width_mm)
    height = float(cfg.height_mm)
    bottom = float(cfg.bottom_flag_height_mm)
    if any(not math.isfinite(value) for value in (width, height, bottom)):
        raise ValueError("Dimensões da Fase 22 devem ser finitas.")
    if width <= 0 or height <= 0 or bottom <= 66.0:
        raise ValueError("Dimensões da Fase 22 devem gerar perfis e vidros positivos.")
    if isinstance(cfg.quantity, bool) or not isinstance(cfg.quantity, int) or cfg.quantity < 1:
        raise ValueError("Quantidade GR deve ser inteiro maior ou igual a 1.")


def _calculate_phase22(cfg: GrConfiguration) -> CalculationResult:
    _validate_phase22(cfg)

    # A base estrutural de janela de duas folhas foi homologada na Fase 21.
    # AH=3 é usado somente para obtê-la; toda a grade fixa é substituída abaixo.
    base = v21._calculate_phase21(_v21_config(
        cfg,
        screen_enabled=False,
        bottom_flag_vertical_transoms=3,
    ))

    width = float(cfg.width_mm)
    height = float(cfg.height_mm)
    bottom = float(cfg.bottom_flag_height_mm)
    divider_count = 1
    opening_count = 2
    opening_width = (width - 80.0 - divider_count * 36.0) / opening_count
    opening_height = bottom - 58.0
    divider_length = opening_height + 12.0
    glass_width = opening_width - 8.0
    glass_height = opening_height - 8.0
    boundary_length = width - 68.0

    for name, value in {
        "opening_width": opening_width,
        "opening_height": opening_height,
        "divider_length": divider_length,
        "glass_width": glass_width,
        "glass_height": glass_height,
    }.items():
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"Geometria inválida da subdivisão inferior: {name}={value:g} mm.")

    glass, bead_code = v06._glass_and_bead(cfg.glass_description or "")
    removed_roles = {
        "BOTTOM_FLAG_INTERNAL_VERTICAL_TRANSOM",
        "BOTTOM_FLAG_INTERNAL_VERTICAL_REINFORCEMENT",
        "BOTTOM_FLAG_BEAD_HORIZONTAL",
        "BOTTOM_FLAG_BEAD_VERTICAL",
        "BOTTOM_FLAG_GLASS_PANEL_1",
        "BOTTOM_FLAG_GLASS_PANEL_2",
        "BOTTOM_FLAG_GLASS_PANEL_3",
        "BOTTOM_FLAG_GLASS_PANEL_4",
        "BOTTOM_FLAG_GLASS_SEAL",
        "REINFORCEMENT_SCREWS",
    }
    bom = [item for item in base.unit_bom if item.role not in removed_roles]
    bom.extend([
        v06._linear_component(
            "DE6072", "BOTTOM_FLAG_INTERNAL_VERTICAL_TRANSOM", divider_length,
            1.0, cfg.quantity, "GR!D22/G22 / AH2=1", category="PERFIS PRINCIPAIS",
        ),
        v06._linear_component(
            "RAG - DE6072", "BOTTOM_FLAG_INTERNAL_VERTICAL_REINFORCEMENT",
            divider_length, 1.0, cfg.quantity,
            "PHYSICAL_RULE_DE6072_REINFORCEMENT + GR!D22/G22", category="REFORÇOS",
        ),
        v06._linear_component(
            bead_code, "BOTTOM_FLAG_BEAD_HORIZONTAL", opening_width,
            float(2 * opening_count), cfg.quantity,
            "2 vãos x 2 baguetes horizontais / LEGACY_GR_G25_COUNT_CORRECTED",
        ),
        v06._linear_component(
            bead_code, "BOTTOM_FLAG_BEAD_VERTICAL", opening_height,
            float(2 * opening_count), cfg.quantity,
            "2 vãos x 2 baguetes verticais / LEGACY_GR_G26_COUNT_CORRECTED",
        ),
    ])

    flag_panels = []
    for column in range(opening_count):
        component, raw_panel = v06._glass_component(
            glass, glass_width, glass_height, cfg.quantity
        )
        bom.append(replace(
            component,
            role=f"BOTTOM_FLAG_GLASS_PANEL_{column + 1}",
            source="GR!69 intent + AH2=1 / LEGACY_GR_FLAG_GRID_GLASS_COUNT_CORRECTED",
        ))
        flag_panels.append(replace(
            raw_panel,
            source="BOTTOM_FLAG",
            position=f"BOTTOM:R1C{column + 1}",
        ))

    total_flag_perimeter = 2.0 * (opening_width + opening_height) * opening_count
    bom.append(v06._seal_component(
        "ACB606", "BOTTOM_FLAG_GLASS_SEAL", total_flag_perimeter, 1.0,
        cfg.quantity, "RESOLVED_PHYSICAL_2026-09-22 + 2 fixed glazing perimeters",
    ))

    frame_width_cut = width + 5.0
    frame_height_cut = height + 5.0
    leaf_width_item = next(item for item in bom if item.role == "LEAF_WIDTH")
    leaf_height_item = next(item for item in bom if item.role == "LEAF_HEIGHT")
    base_screws = 4.0 * (
        2.0 * (frame_width_cut + frame_height_cut) / 1000.0
        + leaf_width_item.quantity_per_unit
        * (leaf_width_item.length_mm + leaf_height_item.length_mm) / 1000.0
        + boundary_length / 1000.0
    )
    divider_screws = float(math.ceil(divider_length / 400.0))
    reinforcement_screws = round(base_screws + divider_screws, 6)
    bom.append(legacy._component(
        "PAR2", "REINFORCEMENT_SCREWS", reinforcement_screws, cfg.quantity,
        source="GR!G118 + PHYSICAL_RULE 1x DE6072 interno: ceil(length/400)",
    ))

    screen = v14._screen_component(width, height, cfg.quantity)
    bom.append(screen)

    geometry = dict(base.geometry)
    geometry.update({
        "bottom_flag_vertical_transoms": 1.0,
        "bottom_flag_opening_count": 2.0,
        "bottom_flag_bead_width_mm": round(opening_width, 6),
        "bottom_flag_bead_height_mm": round(opening_height, 6),
        "bottom_flag_glass_width_mm": round(glass_width, 6),
        "bottom_flag_glass_height_mm": round(glass_height, 6),
        "bottom_flag_internal_vertical_transom_length_mm": round(divider_length, 6),
        "bottom_flag_internal_vertical_reinforcement_screws_added": divider_screws,
        "bottom_flag_glass_panel_count": 2.0,
        "screen_width_mm": round(width, 6),
        "screen_height_mm": round(height, 6),
        "screen_panel_count": 1.0,
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
        vertical_transoms=1,
        openings=openings,
    )
    boundary = next(item for item in base.transoms if item.source == "BOTTOM_FLAG_BOUNDARY")
    internal_divider = Transom(
        source="BOTTOM_FLAG_INTERNAL",
        orientation=TransomOrientation.VERTICAL,
        material_code="DE6072",
        reinforcement_material_code="RAG - DE6072",
        length_mm=round(divider_length, 6),
        quantity=1.0,
    )
    leaf_panels = [panel for panel in base.glass_panels if panel.source != "BOTTOM_FLAG"]

    breakdown = {
        group: round(
            sum(item.cost_per_unit_product for item in bom if item.category == group),
            6,
        )
        for group in v06._GROUPS
    }
    total = round(sum(item.cost_per_unit_product for item in bom), 6)
    breakdown["TOTAL"] = total
    warnings = [
        warning for warning in base.warnings
        if warning.code in {
            "LEGACY-GR-SEALING-CORRECTED",
            "LEGACY-GR-BOTTOM-FLAG-HEIGHT-DOUBLE-SUBTRACTION-CORRECTED",
        }
    ]
    warnings.extend([
        EngineeringWarning(
            "LEGACY-GR-BOTTOM-FLAG-GRID-BAGUETTE-COUNT-CORRECTED",
            "A v0.22 usa o perímetro físico completo dos dois vãos com AH2=1: 4 baguetes horizontais e 4 verticais.",
        ),
        EngineeringWarning(
            "LEGACY-GR-BOTTOM-FLAG-GRID-REINFORCEMENT-CORRECTED",
            "GR!G118 omite a travessa vertical interna. A v0.22 inclui RAG-DE6072 e PAR2 a cada 400 mm.",
        ),
        EngineeringWarning(
            "LEGACY-GR-SCREEN-REFERENCE-CORRECTED",
            "GR!D73/E73 referencia células vazias. A v0.22 mantém a fórmula TL3 homologada na Fase 14 com largura e altura reais do marco.",
        ),
        EngineeringWarning(
            "GR-SCREEN-BOTTOM-FLAG-SCOPE",
            "Fase 22 homologa tela com bandeira somente na janela externa de 2 folhas do ORCS 16527, com AH=1.",
        ),
    ])

    return CalculationResult(
        model_description=(
            "JANELA 2 FOLHAS DE GIRO + BANDEIRA INFERIOR COM 1 DIVISÃO VERTICAL "
            "+ TELA MOSQUITEIRA"
        ),
        geometry=geometry,
        unit_bom=bom,
        cost_breakdown=breakdown,
        unit_cost=total,
        leaf_openings=list(base.leaf_openings),
        transoms=[boundary, internal_divider],
        fixed_panels=[fixed],
        glass_panels=[*leaf_panels, *flag_panels],
        warnings=warnings,
        calculation_version=GR_ENGINE_VERSION,
    )


def calculate_gr(cfg: GrConfiguration) -> CalculationResult:
    """GR v0.22: v0.21 + tela/AH=1 da janela ORCS 16527."""
    if _is_phase22_screen_grid(cfg):
        return _calculate_phase22(cfg)
    return _promote(v21.calculate_gr(_v21_config(cfg)))
