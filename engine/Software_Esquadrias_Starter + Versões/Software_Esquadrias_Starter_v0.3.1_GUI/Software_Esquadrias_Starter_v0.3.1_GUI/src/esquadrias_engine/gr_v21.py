from __future__ import annotations

from dataclasses import fields, replace
import math

from . import gr as legacy
from . import gr_v06 as v06
from . import gr_v20 as v20
from .models import (
    CalculationResult,
    EngineeringWarning,
    FixedPanelGeometry,
    FixedPanelPosition,
    GridOpening,
    Transom,
    TransomOrientation,
)


GR_ENGINE_VERSION = "GR_ENGINE_0.21.0"
GrConfiguration = v20.GrConfiguration


def _v20_config(cfg: GrConfiguration) -> v20.GrConfiguration:
    return v20.GrConfiguration(**{
        field.name: getattr(cfg, field.name) for field in fields(v20.GrConfiguration)
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


def _is_phase21_bottom_grid(cfg: GrConfiguration) -> bool:
    return (
        cfg.bottom_flag_vertical_transoms == 3
        and cfg.bottom_flag_horizontal_transoms == 0
        and cfg.top_flag_vertical_transoms == 0
        and cfg.top_flag_horizontal_transoms == 0
    )


def _validate_phase21(cfg: GrConfiguration) -> None:
    counts = (
        cfg.bottom_flag_vertical_transoms,
        cfg.bottom_flag_horizontal_transoms,
        cfg.top_flag_vertical_transoms,
        cfg.top_flag_horizontal_transoms,
    )
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in counts):
        raise ValueError("Divisões de bandeira GR devem ser inteiros maiores ou iguais a zero.")
    if not _is_phase21_bottom_grid(cfg):
        raise ValueError(
            "GR_ENGINE_0.21.0 homologa na bandeira inferior somente 3 divisões verticais no recorte da Fase 21."
        )
    if cfg.bottom_flag_height_mm <= 0 or cfg.top_flag_height_mm != 0:
        raise ValueError("Fase 21 exige somente bandeira inferior.")
    if cfg.application != v06.GR_APPLICATION_WINDOW:
        raise ValueError("Fase 21 exige aplicação JANELA.")
    if cfg.leaf_count != 2:
        raise ValueError("Fase 21 exige janela de 2 folhas.")
    if cfg.leaf_system != v06.GR_LEAF_SYSTEM_WINDOW_EXTERNAL:
        raise ValueError("Fase 21 exige folha de janela Design 60x78 abertura externa.")
    if cfg.panel_mode != v06.GR_GLASS_MODE:
        raise ValueError("Fase 21 exige VIDRO INTEIRO.")
    if cfg.hinge_description != v06.GR_HINGE:
        raise ValueError("Fase 21 exige DOBRADIÇA 90MM.")
    if cfg.closure_mode != v06.GR_CLOSURE_WINDOW_CREMONA:
        raise ValueError("Fase 21 exige maçaneta com cremona sem chave.")
    if cfg.cremona_description not in (None, v06.GR_CREMONA_WINDOW_800):
        raise ValueError("Fase 21 suporta somente cremona padrão de 800mm E:15mm.")
    if cfg.shutter is not None or cfg.shutter_enabled or cfg.screen_enabled:
        raise ValueError("Fase 21 não combina subdivisão da bandeira com persiana/tela.")
    if cfg.leaf_horizontal_transoms or cfg.leaf_vertical_transoms:
        raise ValueError("Fase 21 exige folhas sem travessas internas adicionais.")
    if cfg.structural_reinforcement is not None:
        raise ValueError("Fase 21 não combina reforço estrutural opcional.")
    if not cfg.glass_description:
        raise ValueError("Fase 21 exige vidro informado.")
    v06._glass_and_bead(cfg.glass_description)

    width = float(cfg.width_mm)
    height = float(cfg.height_mm)
    bottom = float(cfg.bottom_flag_height_mm)
    values = (width, height, bottom)
    if any(not math.isfinite(value) for value in values):
        raise ValueError("Dimensões da Fase 21 devem ser finitas.")
    if width <= 0 or height <= 0 or bottom <= 66.0:
        raise ValueError("Dimensões da Fase 21 devem gerar perfis e vidros positivos.")
    if isinstance(cfg.quantity, bool) or not isinstance(cfg.quantity, int) or cfg.quantity < 1:
        raise ValueError("Quantidade GR deve ser inteiro maior ou igual a 1.")


def _calculate_phase21(cfg: GrConfiguration) -> CalculationResult:
    _validate_phase21(cfg)

    width = float(cfg.width_mm)
    height = float(cfg.height_mm)
    bottom = float(cfg.bottom_flag_height_mm)
    leaves = 2
    divider_count = 3
    opening_count = 4

    frame_width_cut = width + 5.0
    frame_height_cut = height + 5.0
    leaf_width_final = width / 2.0 - 42.0
    leaf_width_cut = leaf_width_final + 5.0
    leaf_height_final = height - bottom - 42.0
    leaf_height_cut = leaf_height_final + 5.0
    leaf_bead_width = leaf_width_final - 120.0
    leaf_bead_height = leaf_height_final - 120.0
    leaf_glass_width = leaf_bead_width - 8.0
    leaf_glass_height = leaf_bead_height - 8.0
    frame_reinf_width = width - 80.0
    frame_reinf_height = height - 116.0
    leaf_reinf_width = leaf_width_final - 120.0
    leaf_reinf_height = leaf_height_final - 120.0

    boundary_length = width - 68.0
    divider_face_mm = 36.0
    total_clear_width = width - 80.0
    opening_width = (total_clear_width - divider_count * divider_face_mm) / opening_count
    opening_height = bottom - 58.0
    divider_length = opening_height + 12.0
    flag_glass_width = opening_width - 8.0
    flag_glass_height = opening_height - 8.0

    dimensions = {
        "leaf_width_final": leaf_width_final,
        "leaf_height_final": leaf_height_final,
        "leaf_bead_width": leaf_bead_width,
        "leaf_bead_height": leaf_bead_height,
        "leaf_glass_width": leaf_glass_width,
        "leaf_glass_height": leaf_glass_height,
        "frame_reinf_width": frame_reinf_width,
        "frame_reinf_height": frame_reinf_height,
        "leaf_reinf_width": leaf_reinf_width,
        "leaf_reinf_height": leaf_reinf_height,
        "boundary_length": boundary_length,
        "opening_width": opening_width,
        "opening_height": opening_height,
        "divider_length": divider_length,
        "flag_glass_width": flag_glass_width,
        "flag_glass_height": flag_glass_height,
    }
    invalid = {
        name: value for name, value in dimensions.items()
        if not math.isfinite(value) or value <= 0
    }
    if invalid:
        details = ", ".join(f"{name}={value:g}" for name, value in invalid.items())
        raise ValueError(f"Geometria tecnicamente impossível para GR Fase 21: {details}")

    glass, bead_code = v06._glass_and_bead(cfg.glass_description or "")
    leaf_piece_qty = 2.0 * leaves
    bom = [
        legacy._component("DE6058", "FRAME_WIDTH", 2.0, cfg.quantity, length_mm=frame_width_cut, source="GR!E8/G8"),
        legacy._component("DE6058", "FRAME_HEIGHT", 2.0, cfg.quantity, length_mm=frame_height_cut, source="GR!E9/G9"),
        legacy._component("DE6078", "LEAF_WIDTH", leaf_piece_qty, cfg.quantity, length_mm=leaf_width_cut, source="GR!D10/E10/G10 / G5=2"),
        legacy._component("DE6078", "LEAF_HEIGHT", leaf_piece_qty, cfg.quantity, length_mm=leaf_height_cut, source="GR!J11 + PHYSICAL_BOTTOM_FLAG_HEIGHT_CORRECTION"),
        v06._linear_component(bead_code, "GLASS_BEAD_WIDTH", leaf_bead_width, leaf_piece_qty, cfg.quantity, 'GR!D13/G13 + R2=""'),
        v06._linear_component(bead_code, "GLASS_BEAD_HEIGHT", leaf_bead_height, leaf_piece_qty, cfg.quantity, 'GR!D14/G14 + R2=""'),
        legacy._component("AC7012", "INTERNAL_FINISH_WIDTH", 2.0, cfg.quantity, length_mm=width + 140.0, source="GR!E43/G43"),
        legacy._component("AC7012", "INTERNAL_FINISH_HEIGHT", 2.0, cfg.quantity, length_mm=height + 140.0, source="GR!E44/G44"),
        legacy._component("AC3004", "EXTERNAL_FINISH_WIDTH", 2.0, cfg.quantity, length_mm=width + 60.0, source="GR!E45/G45"),
        legacy._component("AC3004", "EXTERNAL_FINISH_HEIGHT", 2.0, cfg.quantity, length_mm=height + 60.0, source="GR!E46/G46"),
        legacy._component("RAG - DE6058", "FRAME_REINFORCEMENT_WIDTH", 2.0, cfg.quantity, length_mm=frame_reinf_width, source="GR!D58/G58"),
        legacy._component("RAG - DE6058", "FRAME_REINFORCEMENT_HEIGHT", 2.0, cfg.quantity, length_mm=frame_reinf_height, source="GR!D59/G59"),
        legacy._component("RAG - DE6078", "LEAF_REINFORCEMENT_WIDTH", leaf_piece_qty, cfg.quantity, length_mm=leaf_reinf_width, source="GR!D60/G60"),
        legacy._component("RAG - DE6078", "LEAF_REINFORCEMENT_HEIGHT", leaf_piece_qty, cfg.quantity, length_mm=leaf_reinf_height, source="GR!D61/G61"),
        legacy._component("AC0312", "SQUARING_BLOCK", 8.0, cfg.quantity, source="GR!G83/I83 / 4 por folha"),
        legacy._component("AC0001", "DRAIN_CAP", 2.0, cfg.quantity, source="GR!G84/I84"),
        legacy._component("DOB3", "HINGE_90MM", 6.0, cfg.quantity, source="GR!G105/I105 / 3 por folha"),
        legacy._component("MAC1", "STANDARD_HANDLE", 1.0, cfg.quantity, source="GR!G111/I111"),
        legacy._component("CRE12", "CREMONA_800_E15", 1.0, cfg.quantity, source="GR!G112/I112"),
        legacy._component("CON1", "STANDARD_COUNTER_LOCK", 2.0, cfg.quantity, source="GR!G114/I114"),
        legacy._component("CON3", "PASSIVE_LEAF_COUNTER_CLAW", 2.0, cfg.quantity, source="GR!G116/I116 + RESOLVED_PHYSICAL_2026-09-17"),
        legacy._component("FEC7", "PASSIVE_LEAF_CLAW_LOCK", 2.0, cfg.quantity, source="GR!G117/I117 + RESOLVED_PHYSICAL_2026-09-17"),
        v06._linear_component("DE6072", "BOTTOM_FLAG_BOUNDARY_TRANSOM", boundary_length, 1.0, cfg.quantity, "GR!D19/G19 / AA2>0", category="PERFIS PRINCIPAIS"),
        v06._linear_component("RAG - DE6072", "BOTTOM_FLAG_BOUNDARY_REINFORCEMENT", boundary_length, 1.0, cfg.quantity, "GR!D63/G63 + LISTAPERFIS!A44", category="REFORÇOS"),
        v06._linear_component("DE6072", "BOTTOM_FLAG_INTERNAL_VERTICAL_TRANSOM", divider_length, float(divider_count), cfg.quantity, "GR!D22/G22 / AH2=3", category="PERFIS PRINCIPAIS"),
        v06._linear_component("RAG - DE6072", "BOTTOM_FLAG_INTERNAL_VERTICAL_REINFORCEMENT", divider_length, float(divider_count), cfg.quantity, "PHYSICAL_RULE_DE6072_REINFORCEMENT + GR!D22/G22", category="REFORÇOS"),
        v06._linear_component(bead_code, "BOTTOM_FLAG_BEAD_HORIZONTAL", opening_width, float(2 * opening_count), cfg.quantity, "4 vãos x 2 baguetes horizontais / LEGACY_GR_G25_COUNT_CORRECTED"),
        v06._linear_component(bead_code, "BOTTOM_FLAG_BEAD_VERTICAL", opening_height, float(2 * opening_count), cfg.quantity, "4 vãos x 2 baguetes verticais / LEGACY_GR_G26_COUNT_CORRECTED"),
    ]

    leaf_panels = []
    for leaf in range(leaves):
        component, raw_panel = v06._glass_component(
            glass, leaf_glass_width, leaf_glass_height, cfg.quantity
        )
        bom.append(replace(
            component,
            role=f"GLASS_PANEL_{leaf + 1}",
            source="GR!D68:E68/G68 / 1 vidro por folha",
        ))
        leaf_panels.append(replace(
            raw_panel,
            source="LEAF",
            position=f"LEAF:{leaf + 1}",
        ))

    bom.extend(v06._physical_seals(
        cfg,
        bead_width_mm=leaf_bead_width,
        bead_height_mm=leaf_bead_height,
        leaf_width_mm=leaf_width_final,
        leaf_height_mm=leaf_height_final,
    ))

    flag_panels = []
    for column in range(opening_count):
        component, raw_panel = v06._glass_component(
            glass, flag_glass_width, flag_glass_height, cfg.quantity
        )
        bom.append(replace(
            component,
            role=f"BOTTOM_FLAG_GLASS_PANEL_{column + 1}",
            source="GR!69 intent + AH2=3 / LEGACY_GR_FLAG_GRID_GLASS_COUNT_CORRECTED",
        ))
        flag_panels.append(replace(
            raw_panel,
            source="BOTTOM_FLAG",
            position=f"BOTTOM:R1C{column + 1}",
        ))

    total_flag_perimeter = 2.0 * (opening_width + opening_height) * opening_count
    bom.append(v06._seal_component(
        "ACB606", "BOTTOM_FLAG_GLASS_SEAL", total_flag_perimeter, 1.0,
        cfg.quantity, "RESOLVED_PHYSICAL_2026-09-22 + 4 fixed glazing perimeters",
    ))

    base_screws = 4.0 * (
        2.0 * (frame_width_cut + frame_height_cut) / 1000.0
        + leaf_piece_qty * (leaf_width_cut + leaf_height_cut) / 1000.0
        + boundary_length / 1000.0
    )
    divider_screws_each = float(math.ceil(divider_length / 400.0))
    reinforcement_screws = round(
        base_screws + divider_count * divider_screws_each, 6
    )
    hardware_screws = 6.0 * 8.0 + (1.0 + 1.0 + 2.0) * 2.0
    bom.extend([
        legacy._component("PAR2", "REINFORCEMENT_SCREWS", reinforcement_screws, cfg.quantity, source="GR!G118 + PHYSICAL_RULE 3x DE6072 interno: ceil(length/400)"),
        legacy._component("PAR1", "HARDWARE_SCREWS", hardware_screws, cfg.quantity, source="GR!G119/I119 + kits passivos completos"),
    ])

    geometry = {
        "frame_width_final_mm": round(width, 6),
        "frame_width_cut_mm": round(frame_width_cut, 6),
        "frame_height_final_mm": round(height, 6),
        "frame_height_cut_mm": round(frame_height_cut, 6),
        "leaf_width_final_mm": round(leaf_width_final, 6),
        "leaf_width_cut_mm": round(leaf_width_cut, 6),
        "leaf_height_final_mm": round(leaf_height_final, 6),
        "leaf_height_cut_mm": round(leaf_height_cut, 6),
        "glass_bead_width_mm": round(leaf_bead_width, 6),
        "glass_bead_height_mm": round(leaf_bead_height, 6),
        "glass_width_mm": round(leaf_glass_width, 6),
        "glass_height_mm": round(leaf_glass_height, 6),
        "glass_panel_count": 2.0,
        "frame_reinforcement_width_mm": round(frame_reinf_width, 6),
        "frame_reinforcement_height_mm": round(frame_reinf_height, 6),
        "leaf_reinforcement_width_mm": round(leaf_reinf_width, 6),
        "leaf_reinforcement_height_mm": round(leaf_reinf_height, 6),
        "bottom_flag_height_mm": round(bottom, 6),
        "bottom_flag_boundary_transom_length_mm": round(boundary_length, 6),
        "bottom_flag_vertical_transoms": float(divider_count),
        "bottom_flag_horizontal_transoms": 0.0,
        "bottom_flag_opening_count": float(opening_count),
        "bottom_flag_bead_width_mm": round(opening_width, 6),
        "bottom_flag_bead_height_mm": round(opening_height, 6),
        "bottom_flag_glass_width_mm": round(flag_glass_width, 6),
        "bottom_flag_glass_height_mm": round(flag_glass_height, 6),
        "bottom_flag_internal_vertical_transom_length_mm": round(divider_length, 6),
        "bottom_flag_internal_vertical_reinforcement_screws_added": float(divider_count) * divider_screws_each,
        "bottom_flag_glass_panel_count": float(opening_count),
    }

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
    warnings = [
        EngineeringWarning(
            "LEGACY-GR-SEALING-CORRECTED",
            "GR!76:78 zerava as vedações por condição de família incorreta; a Fase 21 mantém os três percursos físicos homologados.",
        ),
        EngineeringWarning(
            "LEGACY-GR-BOTTOM-FLAG-HEIGHT-DOUBLE-SUBTRACTION-CORRECTED",
            "GR!D9/J11 subtrai AA2 duas vezes. A v0.21 usa H_folha = H_total - H_bandeira - 42 para janela.",
        ),
        EngineeringWarning(
            "LEGACY-GR-BOTTOM-FLAG-GRID-BAGUETTE-COUNT-CORRECTED",
            "GR!G25/G26 não representa o perímetro físico completo dos quatro vãos com AH2=3. A v0.21 usa 8 baguetes horizontais e 8 verticais.",
        ),
        EngineeringWarning(
            "LEGACY-GR-BOTTOM-FLAG-GRID-REINFORCEMENT-CORRECTED",
            "GR!G118 omite as travessas verticais internas. A v0.21 inclui 3 RAG-DE6072 e PAR2 a cada 400 mm.",
        ),
        EngineeringWarning(
            "GR-TWO-LEAF-WINDOW-SCOPE",
            "Fase 21 homologa janela externa de 2 folhas somente no recorte ORCS 14179, sem tela ou persiana.",
        ),
    ]

    return CalculationResult(
        model_description="JANELA 2 FOLHAS DE GIRO + BANDEIRA INFERIOR COM 3 DIVISÕES VERTICAIS",
        geometry=geometry,
        unit_bom=bom,
        cost_breakdown=breakdown,
        unit_cost=total,
        leaf_openings=[],
        transoms=[boundary, internal_divider],
        fixed_panels=[fixed],
        glass_panels=[*leaf_panels, *flag_panels],
        warnings=warnings,
        calculation_version=GR_ENGINE_VERSION,
    )


def calculate_gr(cfg: GrConfiguration) -> CalculationResult:
    """GR v0.21: v0.20 + janela 2 folhas/AH=3 do ORCS 14179."""
    if _is_phase21_bottom_grid(cfg):
        return _calculate_phase21(cfg)
    return _promote(v20.calculate_gr(_v20_config(cfg)))
