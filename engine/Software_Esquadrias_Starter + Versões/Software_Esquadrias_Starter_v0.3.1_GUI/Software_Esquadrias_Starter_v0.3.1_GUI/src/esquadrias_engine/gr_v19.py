from __future__ import annotations

from dataclasses import dataclass, fields, replace
import math

from . import gr_v06 as v06
from . import gr_v18 as v18
from .models import (
    CalculationResult,
    EngineeringWarning,
    FixedPanelGeometry,
    GridOpening,
    Transom,
    TransomOrientation,
)


GR_ENGINE_VERSION = "GR_ENGINE_0.19.0"


@dataclass(frozen=True)
class GrConfiguration(v18.GrConfiguration):
    """Contrato GR v0.19 com subdivisões explícitas das bandeiras.

    Os quatro campos correspondem diretamente ao histórico ORCS AH:AK.
    A Fase 19 homologa somente top_flag_vertical_transoms=1.
    """

    bottom_flag_vertical_transoms: int = 0
    bottom_flag_horizontal_transoms: int = 0
    top_flag_vertical_transoms: int = 0
    top_flag_horizontal_transoms: int = 0


def _v18_config(cfg: GrConfiguration, **overrides) -> v18.GrConfiguration:
    data = {field.name: getattr(cfg, field.name) for field in fields(v18.GrConfiguration)}
    data.update(overrides)
    return v18.GrConfiguration(**data)


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


def _has_flag_grid(cfg: GrConfiguration) -> bool:
    return any((
        cfg.bottom_flag_vertical_transoms,
        cfg.bottom_flag_horizontal_transoms,
        cfg.top_flag_vertical_transoms,
        cfg.top_flag_horizontal_transoms,
    ))


def _validate_top_vertical_one(cfg: GrConfiguration) -> None:
    counts = (
        cfg.bottom_flag_vertical_transoms,
        cfg.bottom_flag_horizontal_transoms,
        cfg.top_flag_vertical_transoms,
        cfg.top_flag_horizontal_transoms,
    )
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in counts):
        raise ValueError("Divisões de bandeira GR devem ser inteiros maiores ou iguais a zero.")

    if (
        cfg.top_flag_vertical_transoms != 1
        or cfg.top_flag_horizontal_transoms != 0
        or cfg.bottom_flag_vertical_transoms != 0
        or cfg.bottom_flag_horizontal_transoms != 0
    ):
        raise ValueError(
            "GR_ENGINE_0.19.0 homologa somente 1 divisão vertical na bandeira superior."
        )
    if cfg.top_flag_height_mm <= 0 or cfg.bottom_flag_height_mm != 0:
        raise ValueError("Fase 19 exige somente bandeira superior.")
    if cfg.application != v06.GR_APPLICATION_DOOR:
        raise ValueError("Fase 19 exige aplicação PORTA.")
    if cfg.leaf_count != 2:
        raise ValueError("Fase 19 exige porta de 2 folhas.")
    if cfg.leaf_system != v06.GR_LEAF_SYSTEM_INTERNAL:
        raise ValueError("Fase 19 homologa inicialmente porta interna Design 60x104.")
    if cfg.panel_mode != v06.GR_GLASS_MODE:
        raise ValueError("Fase 19 exige VIDRO INTEIRO.")
    if cfg.hinge_description != v06.GR_HINGE:
        raise ValueError("Fase 19 exige DOBRADIÇA 90MM.")
    if cfg.shutter is not None or cfg.shutter_enabled or cfg.screen_enabled:
        raise ValueError("Fase 19 não combina subdivisão da bandeira com persiana/tela.")
    if cfg.leaf_horizontal_transoms or cfg.leaf_vertical_transoms:
        raise ValueError("Fase 19 exige folhas sem travessas internas adicionais.")
    if cfg.structural_reinforcement is not None:
        raise ValueError("Fase 19 não combina reforço estrutural opcional.")
    if not cfg.glass_description:
        raise ValueError("Fase 19 exige vidro informado.")
    v06._glass_and_bead(cfg.glass_description)

    # Reusa integralmente a Fase 16 já homologada e só subdivide o fixo superior.
    v18.calculate_gr(_v18_config(cfg))


def _calculate_top_vertical_one(cfg: GrConfiguration) -> CalculationResult:
    _validate_top_vertical_one(cfg)

    base = v18.calculate_gr(_v18_config(cfg))
    width = float(cfg.width_mm)
    top = float(cfg.top_flag_height_mm)

    total_clear_width = width - 80.0
    divider_face_mm = 36.0  # LISTAPERFIS!E18 / DE6072
    opening_count = 2.0
    opening_width = (total_clear_width - divider_face_mm) / opening_count
    opening_height = top - 58.0
    divider_length = opening_height + 12.0  # GR!D24 = D28 + PFAB!B18
    glass_width = opening_width - 8.0
    glass_height = opening_height - 8.0

    for name, value in {
        "opening_width": opening_width,
        "opening_height": opening_height,
        "divider_length": divider_length,
        "glass_width": glass_width,
        "glass_height": glass_height,
    }.items():
        if not math.isfinite(value) or value <= 0:
            raise ValueError(
                f"Geometria inválida da subdivisão superior: {name}={value:g} mm."
            )

    glass, bead_code = v06._glass_and_bead(cfg.glass_description or "")

    removed_roles = {
        "TOP_FLAG_BEAD_HORIZONTAL",
        "TOP_FLAG_BEAD_VERTICAL",
        "TOP_FLAG_GLASS_PANEL",
        "TOP_FLAG_GLASS_SEAL",
        "REINFORCEMENT_SCREWS",
    }
    bom = [item for item in base.unit_bom if item.role not in removed_roles]

    bom.extend([
        v06._linear_component(
            "DE6072",
            "TOP_FLAG_INTERNAL_VERTICAL_TRANSOM",
            divider_length,
            1.0,
            cfg.quantity,
            "GR!D24/G24 / AJ2=1",
            category="PERFIS PRINCIPAIS",
        ),
        v06._linear_component(
            "RAG - DE6072",
            "TOP_FLAG_INTERNAL_VERTICAL_REINFORCEMENT",
            divider_length,
            1.0,
            cfg.quantity,
            "PHYSICAL_RULE_DE6072_REINFORCEMENT + GR!D24/G24",
            category="REFORÇOS",
        ),
        v06._linear_component(
            bead_code,
            "TOP_FLAG_BEAD_HORIZONTAL",
            opening_width,
            4.0,
            cfg.quantity,
            "2 vãos x 2 baguetes horizontais / LEGACY_GR_G27_COUNT_CORRECTED",
        ),
        v06._linear_component(
            bead_code,
            "TOP_FLAG_BEAD_VERTICAL",
            opening_height,
            4.0,
            cfg.quantity,
            "2 vãos x 2 baguetes verticais / LEGACY_GR_G28_COUNT_CORRECTED",
        ),
    ])

    new_flag_panels = []
    for column in (0, 1):
        component, raw_panel = v06._glass_component(
            glass, glass_width, glass_height, cfg.quantity
        )
        component = replace(
            component,
            role=f"TOP_FLAG_GLASS_PANEL_{column + 1}",
            source=(
                "GR!70 intent + AJ2=1 / "
                "LEGACY_GR_FLAG_GRID_GLASS_COUNT_CORRECTED"
            ),
        )
        bom.append(component)
        new_flag_panels.append(replace(
            raw_panel,
            source="TOP_FLAG",
            position=f"TOP:R1C{column + 1}",
        ))

    total_glazing_perimeter = 2.0 * (opening_width + opening_height) * opening_count
    bom.append(v06._seal_component(
        "ACB606",
        "TOP_FLAG_GLASS_SEAL",
        total_glazing_perimeter,
        1.0,
        cfg.quantity,
        "RESOLVED_PHYSICAL_2026-09-22 + 2 fixed glazing perimeters",
    ))

    base_screws = next(
        item for item in base.unit_bom if item.role == "REINFORCEMENT_SCREWS"
    )
    divider_screws = float(math.ceil(divider_length / 400.0))
    total_screws = base_screws.quantity_per_unit + divider_screws
    bom.append(replace(
        base_screws,
        quantity_per_unit=total_screws,
        quantity_order=total_screws * cfg.quantity,
        cost_per_unit_product=round(total_screws * base_screws.unit_price, 6),
        source=(
            (base_screws.source or "")
            + " + PHYSICAL_RULE internal DE6072: ceil(length/400)"
        ),
    ))

    geometry = dict(base.geometry)
    geometry.update({
        "top_flag_vertical_transoms": 1.0,
        "top_flag_horizontal_transoms": 0.0,
        "top_flag_opening_count": 2.0,
        "top_flag_bead_width_mm": round(opening_width, 6),
        "top_flag_bead_height_mm": round(opening_height, 6),
        "top_flag_glass_width_mm": round(glass_width, 6),
        "top_flag_glass_height_mm": round(glass_height, 6),
        "top_flag_internal_vertical_transom_length_mm": round(divider_length, 6),
        "top_flag_internal_vertical_reinforcement_screws_added": divider_screws,
        "top_flag_glass_panel_count": 2.0,
    })

    openings = tuple(
        GridOpening(
            source="TOP_FLAG",
            row_index=0,
            column_index=column,
            width_mm=round(opening_width, 6),
            height_mm=round(opening_height, 6),
            quantity=1.0,
        )
        for column in (0, 1)
    )
    fixed_panels = []
    for panel in base.fixed_panels:
        if panel.position.value == "TOP":
            fixed_panels.append(FixedPanelGeometry(
                position=panel.position,
                width_mm=panel.width_mm,
                nominal_height_mm=panel.nominal_height_mm,
                frame_height_mm=panel.frame_height_mm,
                horizontal_transoms=0,
                vertical_transoms=1,
                openings=openings,
            ))
        else:
            fixed_panels.append(panel)

    internal_divider = Transom(
        source="TOP_FLAG_INTERNAL",
        orientation=TransomOrientation.VERTICAL,
        material_code="DE6072",
        reinforcement_material_code="RAG - DE6072",
        length_mm=round(divider_length, 6),
        quantity=1.0,
    )

    main_glass_panels = [
        panel for panel in base.glass_panels if panel.source != "TOP_FLAG"
    ]

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
            "LEGACY-GR-TOP-FLAG-GRID-BAGUETTE-COUNT-CORRECTED",
            "GR!G27/G28 não representa o perímetro físico completo dos dois vãos com AJ2=1. A v0.19 usa 4 baguetes horizontais e 4 verticais.",
        ),
        EngineeringWarning(
            "LEGACY-GR-TOP-FLAG-GRID-REINFORCEMENT-CORRECTED",
            "GR!G118 não inclui a travessa vertical interna da bandeira no módulo único. A v0.19 inclui RAG-DE6072 e ceil(comprimento/400) PAR2, conforme regra física já confirmada para reforço de travessa.",
        ),
        EngineeringWarning(
            "GR-TOP-FLAG-VERTICAL-GRID-SCOPE",
            "Fase 19 homologa somente 1 divisão vertical na bandeira superior de porta interna 2 folhas.",
        ),
    ])

    return CalculationResult(
        model_description=base.model_description + " + 1 DIVISÃO VERTICAL NA BANDEIRA",
        geometry=geometry,
        unit_bom=bom,
        cost_breakdown=breakdown,
        unit_cost=total,
        leaf_openings=list(base.leaf_openings),
        transoms=[*base.transoms, internal_divider],
        fixed_panels=fixed_panels,
        glass_panels=[*main_glass_panels, *new_flag_panels],
        warnings=warnings,
        calculation_version=GR_ENGINE_VERSION,
    )


def calculate_gr(cfg: GrConfiguration) -> CalculationResult:
    """GR v0.19: v0.18 + primeira subdivisão interna de bandeira."""
    if _has_flag_grid(cfg):
        return _calculate_top_vertical_one(cfg)
    return _promote(v18.calculate_gr(_v18_config(cfg)))
