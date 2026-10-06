from __future__ import annotations

from dataclasses import dataclass, fields, replace
import math

from . import gr as legacy
from . import gr_v06 as v06
from . import gr_v07 as v07
from . import gr_v11 as v11
from . import gr_v14 as v14
from . import gr_v24 as v24
from .catalog import GLASSES, HARDWARE, MATERIALS, Glass, normalize
from .models import (
    BomComponent,
    CalculationResult,
    EngineeringWarning,
    FixedPanelGeometry,
    FixedPanelPosition,
    GlassPanel,
    GridOpening,
    ShutterMode,
    Transom,
    TransomOrientation,
)


GR_ENGINE_VERSION = "GR_ENGINE_0.25.0"

GR_HINGE_90 = "DOBRADIÇA 90MM"
GR_HINGE_OB = "DOBRADIÇA SISTEMA OB"
GR_HINGE_PERNIO = "DOBRADIÇA PÊRNIO"
GR_HINGES = (GR_HINGE_90, GR_HINGE_OB, GR_HINGE_PERNIO)

GR_CLOSURE_KEY_CREMONA = "MAÇANETA COM CHAVE E CREMONA"
GR_CLOSURE_CREMONA_ALIAS = "MAÇANETA COM CREMONA"
GR_CLOSURES = (
    v06.GR_CLOSURE_MONOPOINT,
    v06.GR_CLOSURE_MULTIPOINT,
    v06.GR_CLOSURE_WINDOW_CREMONA,
    GR_CLOSURE_KEY_CREMONA,
    GR_CLOSURE_CREMONA_ALIAS,
)

_STANDARD_CREMONA_CODES = {f"CRE{number}" for number in range(1, 17)}
_OB_CREMONA_CODES = {"CRE21", "CRE22", "CRE23", "CRE24"}

# Nomes livres encontrados na ORCS que são variações inequívocas de uma
# linha existente na LISTAVIDROS. Os demais nomes livres exigem preço,
# espessura e código explícitos no orçamento.
_GLASS_ALIASES = {
    normalize("06mm LAMINADO LEITOSO"): "06mm LAMINADO OPACO",
    normalize("08mm LAMINADO REFLETIVO CHAMPANHE"): "08mm LAMINADO REFLETIVO CHAMPANHE -VB",
    normalize("06mm TEMPERADO VERDE"): "06mm TEMPERADO VERDE VB",
    normalize("22mm DUPLO LAMINADO INCOLOR/LAMINADO INCOLOR (6/10/6)"): "22mm DUPLO LAMINADO INCOLOR (6/10/6)",
    normalize("10mm TEMPERADO INCOLOR/LAMINADO INCOLOR (5+5)"): "10mm TEMPERADO/LAMINADO INCOLOR",
}


@dataclass(frozen=True)
class GrConfiguration(v24.GrConfiguration):
    """Contrato final da migração GR.

    Vidros que não existem na LISTAVIDROS permanecem utilizáveis sem inventar
    custo: o orçamento informa código, preço por m² e espessura. O comprimento
    da fechadura de janela é um dado comercial/físico e não altera o preço
    genérico preservado do XLSM.
    """

    custom_glass_code: str | None = None
    custom_glass_unit_price: float | None = None
    custom_glass_thickness_mm: float | None = None
    window_lock_length_mm: float | None = None


GR_COVERAGE_AUDIT = {
    **v24.GR_COVERAGE_AUDIT,
    "audit_version": "GR_COVERAGE_AUDIT_0.25.0",
    "resolved_or_prohibited": {
        **v24.GR_COVERAGE_AUDIT["resolved_or_prohibited"],
        "hardware_matrix": {
            "status": "RESOLVED_XLSM_AND_PHYSICAL",
            "closures_implemented": 5,
            "pernio_historical_rows": 5,
            "pernio_rule": "DOB5 x 3 por folha; PAR1 x 8 por dobradiça",
        },
        "flag_combinations": {
            "status": "RESOLVED_XLSM",
            "historical_pending_rows": 21,
            "rule": "bandeiras integradas simples ou com divisões verticais",
        },
        "uncatalogued_glass": {
            "status": "RESOLVED_CONFIGURABLE_INPUT",
            "historical_rows": 24,
            "rule": "descrição livre exige código, espessura e preço/m²",
        },
    },
    "pending_real": {},
    "manual_review_exceptions": {
        "invalid_source_rows": 11,
        "nonstandard_closures_without_complete_kit": 7,
        "policy": "item manual; não inferir ferragens nem preços ausentes",
    },
    "gate": {
        "historical_coverage_closed": True,
        "purchase_plan_supported": True,
        "main_ready": True,
        "status": "FASE_25_FINAL_CONCLUIDA",
    },
}


def _to_v24(cfg: GrConfiguration, **overrides) -> v24.GrConfiguration:
    data = {field.name: getattr(cfg, field.name) for field in fields(v24.GrConfiguration)}
    data.update(overrides)
    return v24.GrConfiguration(**data)


def _physical_application(cfg: GrConfiguration) -> str:
    if cfg.leaf_system == v06.GR_LEAF_SYSTEM_WINDOW_EXTERNAL:
        return v06.GR_APPLICATION_WINDOW
    return v06.GR_APPLICATION_DOOR


def _commercial_description(description: str, application: str) -> str:
    head, separator, tail = description.partition(" ")
    if head in (v06.GR_APPLICATION_DOOR, v06.GR_APPLICATION_WINDOW):
        return application + (separator + tail if separator else "")
    return description


def _glass_for_configuration(cfg: GrConfiguration) -> tuple[Glass | None, str | None]:
    if not cfg.glass_description:
        return None, None

    direct = GLASSES.get(normalize(cfg.glass_description))
    if direct is not None and direct.code != "0" and direct.thickness_mm is not None:
        return direct, None

    alias_description = _GLASS_ALIASES.get(normalize(cfg.glass_description))
    if alias_description is not None:
        aliased = GLASSES[normalize(alias_description)]
        return Glass(
            aliased.code,
            cfg.glass_description,
            aliased.unit_price,
            aliased.thickness_mm,
        ), "ALIAS"

    values = (
        cfg.custom_glass_code,
        cfg.custom_glass_unit_price,
        cfg.custom_glass_thickness_mm,
    )
    if any(value is not None for value in values) and not all(value is not None for value in values):
        raise ValueError(
            "Vidro personalizado exige custom_glass_code, "
            "custom_glass_unit_price e custom_glass_thickness_mm."
        )
    if not all(value is not None for value in values):
        raise ValueError(
            f"Vidro GR não consta na LISTAVIDROS: {cfg.glass_description}. "
            "Informe código, preço por m² e espessura personalizados."
        )

    code = str(cfg.custom_glass_code or "").strip()
    price = float(cfg.custom_glass_unit_price or 0.0)
    thickness = float(cfg.custom_glass_thickness_mm or 0.0)
    if not code:
        raise ValueError("custom_glass_code deve ser preenchido.")
    if not math.isfinite(price) or price < 0:
        raise ValueError("custom_glass_unit_price deve ser finito e não negativo.")
    if not math.isfinite(thickness) or thickness <= 0 or thickness >= 35:
        raise ValueError("custom_glass_thickness_mm deve ser maior que 0 e menor que 35.")
    return Glass(code, cfg.glass_description, price, thickness), "CUSTOM"


def _bead_for_thickness(thickness_mm: float) -> str:
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
    bead = next((code for upper, code in ranges if thickness_mm < upper), None)
    if bead is None:
        raise ValueError(f"Espessura de vidro {thickness_mm:g} mm sem baguete GR comprovada.")
    return bead


def _canonical_glass_description(cfg: GrConfiguration) -> str | None:
    glass, origin = _glass_for_configuration(cfg)
    if glass is None:
        return None
    if origin == "ALIAS":
        return _GLASS_ALIASES[normalize(cfg.glass_description or "")]
    if origin == "CUSTOM":
        # Serve apenas para atravessar as fórmulas geométricas legadas. O
        # material e a baguete são substituídos pelo contrato personalizado.
        return "04mm FLOAT INCOLOR"
    return glass.description


def _validate_common(cfg: GrConfiguration) -> None:
    dimensions = (float(cfg.width_mm), float(cfg.height_mm))
    if any(not math.isfinite(value) or value <= 0 for value in dimensions):
        raise ValueError("Largura e altura GR devem ser finitas e positivas.")
    if isinstance(cfg.quantity, bool) or not isinstance(cfg.quantity, int) or cfg.quantity < 1:
        raise ValueError("Quantidade GR deve ser inteiro maior ou igual a 1.")
    if cfg.leaf_count not in (1, 2):
        raise ValueError("GR suporta somente 1 ou 2 folhas.")
    if cfg.leaf_system not in v06.GR_LEAF_SYSTEMS:
        raise ValueError(f"Tipo de folha fora do escopo GR: {cfg.leaf_system}")
    if cfg.application not in (v06.GR_APPLICATION_DOOR, v06.GR_APPLICATION_WINDOW):
        raise ValueError(f"Aplicação fora do escopo GR: {cfg.application}")
    if cfg.hinge_description not in GR_HINGES:
        raise ValueError(f"Dobradiça GR não automatizada: {cfg.hinge_description}")
    if cfg.closure_mode not in GR_CLOSURES:
        raise ValueError(
            f"Fechamento GR sem kit completo no XLSM: {cfg.closure_mode}. "
            "Cadastre-o como item manual."
        )
    if (
        cfg.leaf_system == v06.GR_LEAF_SYSTEM_WINDOW_EXTERNAL
        and cfg.closure_mode == GR_CLOSURE_KEY_CREMONA
    ):
        raise ValueError("Folha de janela GR não recebe maçaneta com chave.")
    if cfg.module_mode != v06.GR_MODULE_MODE:
        raise ValueError("GR possui evidência histórica somente para MÓDULO ÚNICO.")
    if cfg.structural_reinforcement is not None:
        raise ValueError("GR não possui casos históricos de reforço estrutural opcional.")
    if cfg.leaf_horizontal_transoms or cfg.leaf_vertical_transoms:
        raise ValueError("Travessas dentro da folha móvel GR são fisicamente proibidas.")

    if (
        cfg.shutter is not None
        and cfg.shutter.mode == ShutterMode.MANUAL_DOUBLE_INDEPENDENT_SHAFTS
        and cfg.leaf_count != 2
    ):
        raise ValueError("Persiana manual em 2 painéis com eixos independentes exige GR de 2 folhas.")

    counts = (
        cfg.bottom_flag_vertical_transoms,
        cfg.bottom_flag_horizontal_transoms,
        cfg.top_flag_vertical_transoms,
        cfg.top_flag_horizontal_transoms,
    )
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in counts):
        raise ValueError("Divisões de bandeira GR devem ser inteiros não negativos.")
    if cfg.bottom_flag_horizontal_transoms or cfg.top_flag_horizontal_transoms:
        raise ValueError(
            "A ORCS oficial não possui bandeira GR com divisão horizontal; "
            "essa topologia continua fora da migração automática."
        )
    if cfg.bottom_flag_vertical_transoms and cfg.bottom_flag_height_mm <= 0:
        raise ValueError("Divisão inferior exige bottom_flag_height_mm positivo.")
    if cfg.top_flag_vertical_transoms and cfg.top_flag_height_mm <= 0:
        raise ValueError("Divisão superior exige top_flag_height_mm positivo.")

    has_glazing = (
        cfg.panel_mode != v06.GR_PANEL_MODE
        or cfg.bottom_flag_height_mm > 0
        or cfg.top_flag_height_mm > 0
    )
    if has_glazing:
        if not cfg.glass_description:
            raise ValueError("Vidro deve ser informado para folha envidraçada ou bandeira.")
        _glass_for_configuration(cfg)

    custom_values = (
        cfg.custom_glass_code,
        cfg.custom_glass_unit_price,
        cfg.custom_glass_thickness_mm,
    )
    if not has_glazing and cfg.glass_description:
        raise ValueError("PAINEL COMPLETO sem bandeira não deve informar glass_description.")
    if not has_glazing and any(value is not None for value in custom_values):
        raise ValueError("Vidro personalizado só deve ser informado quando houver vidro.")

    if cfg.window_lock_length_mm is not None:
        length = float(cfg.window_lock_length_mm)
        if not math.isfinite(length) or length <= 0:
            raise ValueError("window_lock_length_mm deve ser finito e positivo.")
        if (
            cfg.leaf_system != v06.GR_LEAF_SYSTEM_WINDOW_EXTERNAL
            or cfg.closure_mode not in (v06.GR_CLOSURE_MONOPOINT, v06.GR_CLOSURE_MULTIPOINT)
        ):
            raise ValueError(
                "window_lock_length_mm só se aplica à folha de janela com fechadura mono/multiponto."
            )
    elif (
        cfg.leaf_system == v06.GR_LEAF_SYSTEM_WINDOW_EXTERNAL
        and cfg.closure_mode in (v06.GR_CLOSURE_MONOPOINT, v06.GR_CLOSURE_MULTIPOINT)
    ):
        raise ValueError("Folha de janela com fechadura mono/multiponto exige window_lock_length_mm.")


def _unit_component(
    description: str,
    role: str,
    quantity: float,
    order_quantity: int,
    source: str,
    *,
    description_override: str | None = None,
) -> BomComponent:
    material = HARDWARE.get(normalize(description))
    if material is None:
        raise ValueError(f"Ferragem não cadastrada na LISTAFERRA: {description}")
    if not math.isfinite(quantity) or quantity <= 0:
        raise ValueError(f"Quantidade inválida para {role}: {quantity:g}")
    return BomComponent(
        category="FERRAGENS",
        role=role,
        material_code=material.code,
        description=description_override or material.description,
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


def _finalize(
    base: CalculationResult,
    bom: list[BomComponent],
    *,
    geometry: dict[str, float] | None = None,
    model_description: str | None = None,
    leaf_openings=None,
    transoms=None,
    fixed_panels=None,
    glass_panels=None,
    warnings=None,
) -> CalculationResult:
    groups = set(base.cost_breakdown) | {item.category for item in bom}
    groups.discard("TOTAL")
    breakdown = {
        group: round(sum(item.cost_per_unit_product for item in bom if item.category == group), 6)
        for group in sorted(groups)
    }
    total = round(sum(item.cost_per_unit_product for item in bom), 6)
    breakdown["TOTAL"] = total
    return CalculationResult(
        model_description=model_description or base.model_description,
        geometry=dict(base.geometry) if geometry is None else geometry,
        unit_bom=bom,
        cost_breakdown=breakdown,
        unit_cost=total,
        leaf_openings=list(base.leaf_openings) if leaf_openings is None else list(leaf_openings),
        transoms=list(base.transoms) if transoms is None else list(transoms),
        fixed_panels=list(base.fixed_panels) if fixed_panels is None else list(fixed_panels),
        glass_panels=list(base.glass_panels) if glass_panels is None else list(glass_panels),
        warnings=list(base.warnings) if warnings is None else list(warnings),
        calculation_version=GR_ENGINE_VERSION,
    )


def _canonical_hardware_overrides(cfg: GrConfiguration) -> dict:
    if cfg.leaf_system == v06.GR_LEAF_SYSTEM_WINDOW_EXTERNAL:
        return {
            "application": v06.GR_APPLICATION_WINDOW,
            "closure_mode": v06.GR_CLOSURE_WINDOW_CREMONA,
            "cremona_description": v06.GR_CREMONA_WINDOW_800,
            "hinge_description": GR_HINGE_90,
        }
    return {
        "application": v06.GR_APPLICATION_DOOR,
        "closure_mode": v06.GR_CLOSURE_MONOPOINT,
        "cremona_description": None,
        "hinge_description": GR_HINGE_90,
    }


def _call_v24(cfg: GrConfiguration, *, canonical_hardware: bool) -> CalculationResult:
    overrides = {
        "glass_description": _canonical_glass_description(cfg),
    }
    if canonical_hardware:
        overrides.update(_canonical_hardware_overrides(cfg))
    return v24.calculate_gr(_to_v24(cfg, **overrides))


def _calculate_window_two_leaf_plain(cfg: GrConfiguration) -> CalculationResult:
    if cfg.panel_mode not in (v06.GR_PANEL_MODE, v06.GR_GLASS_MODE):
        raise ValueError("Janela GR de 2 folhas não possui modo misto no histórico ORCS.")
    width = float(cfg.width_mm)
    height = float(cfg.height_mm)
    leaves = 2
    leaf_pieces = 4.0
    frame_width_cut = width + 5.0
    frame_height_cut = height + 5.0
    leaf_width = width / 2.0 - 42.0
    leaf_height = height - 64.0
    leaf_width_cut = leaf_width + 5.0
    leaf_height_cut = leaf_height + 5.0
    bead_width = leaf_width - 120.0
    bead_height = leaf_height - 120.0
    frame_reinf_width = width - 80.0
    frame_reinf_height = height - 80.0
    leaf_reinf_width = leaf_width - 120.0
    leaf_reinf_height = leaf_height - 120.0
    values = {
        "leaf_width": leaf_width,
        "leaf_height": leaf_height,
        "bead_width": bead_width,
        "bead_height": bead_height,
        "frame_reinf_width": frame_reinf_width,
        "frame_reinf_height": frame_reinf_height,
        "leaf_reinf_width": leaf_reinf_width,
        "leaf_reinf_height": leaf_reinf_height,
    }
    invalid = {name: value for name, value in values.items() if not math.isfinite(value) or value <= 0}
    if invalid:
        detail = ", ".join(f"{name}={value:g}" for name, value in invalid.items())
        raise ValueError(f"Geometria tecnicamente impossível para janela GR 2 folhas: {detail}")

    bom = [
        legacy._component("DE6058", "FRAME_WIDTH", 2, cfg.quantity, length_mm=frame_width_cut, source="GR!E8/G8"),
        legacy._component("DE6058", "FRAME_HEIGHT", 2, cfg.quantity, length_mm=frame_height_cut, source="GR!E9/G9"),
        legacy._component("DE6078", "LEAF_WIDTH", leaf_pieces, cfg.quantity, length_mm=leaf_width_cut, source="GR!D10/E10/G10 / G5=2"),
        legacy._component("DE6078", "LEAF_HEIGHT", leaf_pieces, cfg.quantity, length_mm=leaf_height_cut, source="GR!D11/E11/G11 / G5=2"),
        legacy._component("AC7012", "INTERNAL_FINISH_WIDTH", 2, cfg.quantity, length_mm=width + 140.0, source="GR!E43/G43"),
        legacy._component("AC7012", "INTERNAL_FINISH_HEIGHT", 2, cfg.quantity, length_mm=height + 140.0, source="GR!E44/G44"),
        legacy._component("AC3004", "EXTERNAL_FINISH_WIDTH", 2, cfg.quantity, length_mm=width + 60.0, source="GR!E45/G45"),
        legacy._component("AC3004", "EXTERNAL_FINISH_HEIGHT", 2, cfg.quantity, length_mm=height + 60.0, source="GR!E46/G46"),
        legacy._component("RAG - DE6058", "FRAME_REINFORCEMENT_WIDTH", 2, cfg.quantity, length_mm=frame_reinf_width, source="GR!D58/G58"),
        legacy._component("RAG - DE6058", "FRAME_REINFORCEMENT_HEIGHT", 2, cfg.quantity, length_mm=frame_reinf_height, source="GR!D59/G59"),
        legacy._component("RAG - DE6078", "LEAF_REINFORCEMENT_WIDTH", leaf_pieces, cfg.quantity, length_mm=leaf_reinf_width, source="GR!D60/G60"),
        legacy._component("RAG - DE6078", "LEAF_REINFORCEMENT_HEIGHT", leaf_pieces, cfg.quantity, length_mm=leaf_reinf_height, source="GR!D61/G61"),
        legacy._component("AC0312", "SQUARING_BLOCK", 8, cfg.quantity, source="GR!G83/I83 / 4 por folha"),
        legacy._component("AC0001", "DRAIN_CAP", 2, cfg.quantity, source="GR!G84/I84"),
    ]

    glass_panels: list[GlassPanel] = []
    if cfg.panel_mode == v06.GR_PANEL_MODE:
        strip_qty = ((bead_height - 78.0) / 140.0) * leaves
        if strip_qty <= 0:
            raise ValueError("Altura insuficiente para painel DE20150 na janela GR 2 folhas.")
        bom.extend([
            legacy._component("BA2516", "PANEL_BEAD_WIDTH", leaf_pieces, cfg.quantity, length_mm=bead_width, source="GR!E16/G16"),
            legacy._component("BA2516", "PANEL_BEAD_HEIGHT", leaf_pieces, cfg.quantity, length_mm=bead_height, source="GR!E17/G17"),
            legacy._component("DE20150", "PANEL_FILL", strip_qty, cfg.quantity, length_mm=bead_width, source="GR!E41/G41 + painel por folha"),
        ])
        model = "JANELA 2 FOLHAS DE GIRO COM PAINEL HORIZONTAL"
    else:
        glass = GLASSES[normalize(_canonical_glass_description(cfg) or "")]
        _unused, bead_code = v06._glass_and_bead(glass.description)
        bom.extend([
            v06._linear_component(bead_code, "GLASS_BEAD_WIDTH", bead_width, leaf_pieces, cfg.quantity, 'GR!D13/G13 / R2=""'),
            v06._linear_component(bead_code, "GLASS_BEAD_HEIGHT", bead_height, leaf_pieces, cfg.quantity, 'GR!D14/G14 / R2=""'),
        ])
        component, panel = v07._glass_component_multi(
            glass, bead_width - 8.0, bead_height - 8.0, leaves, cfg.quantity
        )
        bom.append(component)
        glass_panels.append(panel)
        model = "JANELA 2 FOLHAS DE GIRO"

    bom.extend(v06._physical_seals(
        cfg,
        bead_width_mm=bead_width,
        bead_height_mm=bead_height,
        leaf_width_mm=leaf_width,
        leaf_height_mm=leaf_height,
    ))
    reinforcement_screws = 4.0 * (
        2.0 * (frame_width_cut + frame_height_cut) / 1000.0
        + leaf_pieces * (leaf_width_cut + leaf_height_cut) / 1000.0
    )
    bom.append(legacy._component(
        "PAR2", "REINFORCEMENT_SCREWS", reinforcement_screws, cfg.quantity,
        source="GR!G118 / janela 2 folhas",
    ))

    geometry = {
        "frame_width_final_mm": round(width, 6),
        "frame_width_cut_mm": round(frame_width_cut, 6),
        "frame_height_final_mm": round(height, 6),
        "frame_height_cut_mm": round(frame_height_cut, 6),
        "leaf_width_final_mm": round(leaf_width, 6),
        "leaf_width_cut_mm": round(leaf_width_cut, 6),
        "leaf_height_final_mm": round(leaf_height, 6),
        "leaf_height_cut_mm": round(leaf_height_cut, 6),
        "frame_reinforcement_width_mm": round(frame_reinf_width, 6),
        "frame_reinforcement_height_mm": round(frame_reinf_height, 6),
        "leaf_reinforcement_width_mm": round(leaf_reinf_width, 6),
        "leaf_reinforcement_height_mm": round(leaf_reinf_height, 6),
    }
    if cfg.panel_mode == v06.GR_PANEL_MODE:
        geometry.update({
            "panel_bead_width_mm": round(bead_width, 6),
            "panel_bead_height_mm": round(bead_height, 6),
            "panel_fill_strip_length_mm": round(bead_width, 6),
            "panel_fill_strip_quantity": round(strip_qty, 6),
        })
    else:
        geometry.update({
            "glass_bead_width_mm": round(bead_width, 6),
            "glass_bead_height_mm": round(bead_height, 6),
            "glass_width_mm": round(bead_width - 8.0, 6),
            "glass_height_mm": round(bead_height - 8.0, 6),
            "glass_panel_count": 2.0,
        })

    seed = CalculationResult(
        model_description=model,
        geometry=geometry,
        unit_bom=bom,
        cost_breakdown={},
        unit_cost=0.0,
        glass_panels=glass_panels,
        warnings=[EngineeringWarning(
            "GR-TWO-LEAF-WINDOW-GENERALIZED",
            "A Fase 25 generaliza a fórmula G5=2 do XLSM para janela de duas folhas.",
        )],
        calculation_version=GR_ENGINE_VERSION,
    )
    return _finalize(seed, bom)


def _calculate_plain(cfg: GrConfiguration) -> CalculationResult:
    if cfg.leaf_system == v06.GR_LEAF_SYSTEM_WINDOW_EXTERNAL and cfg.leaf_count == 2:
        return _calculate_window_two_leaf_plain(cfg)
    try:
        return _call_v24(cfg, canonical_hardware=False)
    except ValueError:
        return _call_v24(cfg, canonical_hardware=True)


def _replace_linear(item: BomComponent, length_mm: float, source_suffix: str = "") -> BomComponent:
    cost = length_mm / 1000.0 * item.quantity_per_unit * item.unit_price
    return replace(
        item,
        length_mm=round(length_mm, 6),
        cost_per_unit_product=round(cost, 6),
        source=(item.source or "") + source_suffix,
    )


def _append_flag(
    cfg: GrConfiguration,
    position: FixedPanelPosition,
    height_mm: float,
    vertical_transoms: int,
    glass: Glass,
    bead_code: str,
) -> tuple[list[BomComponent], FixedPanelGeometry, list[Transom], list[GlassPanel], dict[str, float], float]:
    prefix = "BOTTOM" if position == FixedPanelPosition.BOTTOM else "TOP"
    source = "BOTTOM_FLAG" if position == FixedPanelPosition.BOTTOM else "TOP_FLAG"
    opening_count = vertical_transoms + 1
    boundary_length = float(cfg.width_mm) - 68.0
    opening_width = (
        float(cfg.width_mm) - 80.0 - vertical_transoms * 36.0
    ) / opening_count
    opening_height = float(height_mm) - 58.0
    glass_width = opening_width - 8.0
    glass_height = opening_height - 8.0
    divider_length = opening_height + 12.0
    values = {
        "boundary_length": boundary_length,
        "opening_width": opening_width,
        "opening_height": opening_height,
        "glass_width": glass_width,
        "glass_height": glass_height,
    }
    invalid = {name: value for name, value in values.items() if not math.isfinite(value) or value <= 0}
    if invalid:
        detail = ", ".join(f"{name}={value:g}" for name, value in invalid.items())
        raise ValueError(f"Geometria inválida da bandeira {prefix.lower()}: {detail}")

    bom = [
        v06._linear_component(
            "DE6072", f"{prefix}_FLAG_BOUNDARY_TRANSOM", boundary_length, 1.0,
            cfg.quantity, "GR!D19/G19", category="PERFIS PRINCIPAIS",
        ),
        v06._linear_component(
            "RAG - DE6072", f"{prefix}_FLAG_BOUNDARY_REINFORCEMENT", boundary_length, 1.0,
            cfg.quantity, "GR!D63/G63 + LISTAPERFIS!A44", category="REFORÇOS",
        ),
        v06._linear_component(
            bead_code, f"{prefix}_FLAG_BEAD_HORIZONTAL", opening_width,
            float(2 * opening_count), cfg.quantity,
            f"GR!25:28 / {opening_count} vão(s) x 2 baguetes",
        ),
        v06._linear_component(
            bead_code, f"{prefix}_FLAG_BEAD_VERTICAL", opening_height,
            float(2 * opening_count), cfg.quantity,
            f"GR!25:28 / {opening_count} vão(s) x 2 baguetes",
        ),
    ]
    transoms = [Transom(
        source=f"{source}_BOUNDARY",
        orientation=TransomOrientation.HORIZONTAL,
        material_code="DE6072",
        reinforcement_material_code="RAG - DE6072",
        length_mm=round(boundary_length, 6),
        quantity=1.0,
    )]
    divider_screws = 0.0
    if vertical_transoms:
        bom.extend([
            v06._linear_component(
                "DE6072", f"{prefix}_FLAG_INTERNAL_VERTICAL_TRANSOM", divider_length,
                float(vertical_transoms), cfg.quantity,
                f"GR!D22:D24 / {vertical_transoms} divisão(ões)", category="PERFIS PRINCIPAIS",
            ),
            v06._linear_component(
                "RAG - DE6072", f"{prefix}_FLAG_INTERNAL_VERTICAL_REINFORCEMENT", divider_length,
                float(vertical_transoms), cfg.quantity,
                "PHYSICAL_RULE_DE6072_REINFORCEMENT", category="REFORÇOS",
            ),
        ])
        transoms.append(Transom(
            source=f"{source}_INTERNAL",
            orientation=TransomOrientation.VERTICAL,
            material_code="DE6072",
            reinforcement_material_code="RAG - DE6072",
            length_mm=round(divider_length, 6),
            quantity=float(vertical_transoms),
        ))
        divider_screws = float(vertical_transoms * math.ceil(divider_length / 400.0))

    openings = []
    panels = []
    for column in range(opening_count):
        component, raw_panel = v06._glass_component(
            glass, glass_width, glass_height, cfg.quantity
        )
        bom.append(replace(
            component,
            role=f"{prefix}_FLAG_GLASS_PANEL_{column + 1}",
            source=f"GR!68:70 / {source} R1C{column + 1}",
        ))
        panels.append(replace(
            raw_panel,
            source=source,
            position=f"{prefix}:R1C{column + 1}",
        ))
        openings.append(GridOpening(
            source=source,
            row_index=0,
            column_index=column,
            width_mm=round(opening_width, 6),
            height_mm=round(opening_height, 6),
            quantity=1.0,
        ))

    perimeter = 2.0 * (opening_width + opening_height) * opening_count
    bom.append(v06._seal_component(
        "ACB606", f"{prefix}_FLAG_GLASS_SEAL", perimeter, 1.0,
        cfg.quantity, "RESOLVED_PHYSICAL_2026-09-22 + perímetros dos vãos fixos",
    ))
    fixed = FixedPanelGeometry(
        position=position,
        width_mm=round(float(cfg.width_mm), 6),
        nominal_height_mm=round(float(height_mm), 6),
        frame_height_mm=round(float(height_mm), 6),
        horizontal_transoms=0,
        vertical_transoms=vertical_transoms,
        openings=tuple(openings),
    )
    geometry = {
        f"{prefix.lower()}_flag_height_mm": round(float(height_mm), 6),
        f"{prefix.lower()}_flag_boundary_transom_length_mm": round(boundary_length, 6),
        f"{prefix.lower()}_flag_vertical_transoms": float(vertical_transoms),
        f"{prefix.lower()}_flag_horizontal_transoms": 0.0,
        f"{prefix.lower()}_flag_opening_count": float(opening_count),
        f"{prefix.lower()}_flag_bead_width_mm": round(opening_width, 6),
        f"{prefix.lower()}_flag_bead_height_mm": round(opening_height, 6),
        f"{prefix.lower()}_flag_glass_width_mm": round(glass_width, 6),
        f"{prefix.lower()}_flag_glass_height_mm": round(glass_height, 6),
        f"{prefix.lower()}_flag_glass_panel_count": float(opening_count),
    }
    if vertical_transoms:
        geometry[f"{prefix.lower()}_flag_internal_vertical_transom_length_mm"] = round(divider_length, 6)
        geometry[f"{prefix.lower()}_flag_internal_vertical_reinforcement_screws_added"] = divider_screws
    return bom, fixed, transoms, panels, geometry, divider_screws


def _calculate_generic_flags(cfg: GrConfiguration) -> CalculationResult:
    bottom = float(cfg.bottom_flag_height_mm)
    top = float(cfg.top_flag_height_mm)
    shutter_height = 200.0 if cfg.shutter is not None else 0.0
    effective_height = float(cfg.height_mm) - shutter_height
    synthetic_height = effective_height - bottom - top + 22.0
    if synthetic_height <= 0:
        raise ValueError("Altura útil da folha ficou inválida com bandeira/persiana.")

    base_cfg = replace(
        cfg,
        height_mm=synthetic_height,
        bottom_flag_height_mm=0.0,
        top_flag_height_mm=0.0,
        bottom_flag_vertical_transoms=0,
        bottom_flag_horizontal_transoms=0,
        top_flag_vertical_transoms=0,
        top_flag_horizontal_transoms=0,
        screen_enabled=False,
        shutter=None,
        shutter_enabled=False,
    )
    if cfg.panel_mode == v06.GR_PANEL_MODE:
        base_cfg = replace(
            base_cfg,
            glass_description=None,
            custom_glass_code=None,
            custom_glass_unit_price=None,
            custom_glass_thickness_mm=None,
        )
    base = _calculate_plain(base_cfg)
    original_screws = next(
        (item for item in base.unit_bom if item.role == "REINFORCEMENT_SCREWS"),
        None,
    )
    if original_screws is None:
        raise ValueError("Base GR sem PAR2 para receber bandeira.")

    physical_window = cfg.leaf_system == v06.GR_LEAF_SYSTEM_WINDOW_EXTERNAL
    frame_cut_extra = 5.0 if physical_window else 3.0
    frame_multiplier = 2.0 if physical_window else 1.0
    bom = []
    for item in base.unit_bom:
        if item.role == "FRAME_HEIGHT":
            bom.append(_replace_linear(item, effective_height + frame_cut_extra, " / altura externa do módulo integrado"))
        elif item.role == "INTERNAL_FINISH_HEIGHT":
            bom.append(_replace_linear(item, effective_height + 140.0))
        elif item.role == "EXTERNAL_FINISH_HEIGHT":
            bom.append(_replace_linear(item, effective_height + 60.0))
        elif item.role == "FRAME_REINFORCEMENT_HEIGHT":
            bom.append(_replace_linear(item, effective_height - 116.0, " / GR!D59 com altura integrada"))
        elif item.role != "REINFORCEMENT_SCREWS":
            bom.append(item)

    glass = GLASSES[normalize(_canonical_glass_description(cfg) or "")]
    _unused, bead_code = v06._glass_and_bead(glass.description)
    fixed_panels = list(base.fixed_panels)
    transoms = list(base.transoms)
    glass_panels = list(base.glass_panels)
    geometry = dict(base.geometry)
    geometry.update({
        "frame_height_final_mm": round(effective_height, 6),
        "frame_height_cut_mm": round(effective_height + frame_cut_extra, 6),
    })
    divider_screws = 0.0
    boundary_total = 0.0

    if bottom > 0:
        addition = _append_flag(
            cfg, FixedPanelPosition.BOTTOM, bottom,
            cfg.bottom_flag_vertical_transoms, glass, bead_code,
        )
        flag_bom, fixed, flag_transoms, panels, flag_geometry, screws = addition
        bom.extend(flag_bom)
        fixed_panels.append(fixed)
        transoms.extend(flag_transoms)
        glass_panels.extend(panels)
        geometry.update(flag_geometry)
        divider_screws += screws
        boundary_total += float(cfg.width_mm) - 68.0
    if top > 0:
        addition = _append_flag(
            cfg, FixedPanelPosition.TOP, top,
            cfg.top_flag_vertical_transoms, glass, bead_code,
        )
        flag_bom, fixed, flag_transoms, panels, flag_geometry, screws = addition
        bom.extend(flag_bom)
        fixed_panels.append(fixed)
        transoms.extend(flag_transoms)
        glass_panels.extend(panels)
        geometry.update(flag_geometry)
        divider_screws += screws
        boundary_total += float(cfg.width_mm) - 68.0

    frame_delta = effective_height - synthetic_height
    reinforcement_screws = (
        original_screws.quantity_per_unit
        + 4.0 * frame_multiplier * frame_delta / 1000.0
        + 4.0 * boundary_total / 1000.0
        + divider_screws
    )
    bom.append(replace(
        original_screws,
        quantity_per_unit=round(reinforcement_screws, 6),
        quantity_order=round(reinforcement_screws * cfg.quantity, 6),
        cost_per_unit_product=round(reinforcement_screws * original_screws.unit_price, 6),
        source="GR!G118 + travessas/reforços de bandeira integrados",
    ))

    warnings = [
        warning for warning in base.warnings
        if warning.code != "GR-OB-DOOR-HARDWARE-SCOPE"
    ]
    warnings.extend([
        EngineeringWarning(
            "LEGACY-GR-FLAG-E40-REFERENCE-CORRECTED",
            "GR!26/28 referencia uma dimensão vazia; a Fase 25 usa a topologia DE6058+DE6072 comprovada: vão W-80 por H-58.",
        ),
        EngineeringWarning(
            "GR-FLAG-MATRIX-GENERALIZED",
            "Bandeiras simples e com divisões verticais seguem diretamente AA/AB/AH/AJ do XLSM e um vidro por vão.",
        ),
    ])
    suffixes = []
    if bottom > 0:
        suffixes.append("BANDEIRA INFERIOR")
    if top > 0:
        suffixes.append("BANDEIRA SUPERIOR")
    result = _finalize(
        base,
        bom,
        geometry=geometry,
        model_description=base.model_description + " + " + " E ".join(suffixes),
        transoms=transoms,
        fixed_panels=fixed_panels,
        glass_panels=glass_panels,
        warnings=warnings,
    )
    if cfg.screen_enabled:
        screen = v14._screen_component(float(cfg.width_mm), effective_height, cfg.quantity)
        geometry = dict(result.geometry)
        geometry.update({
            "screen_width_mm": round(float(cfg.width_mm), 6),
            "screen_height_mm": round(effective_height, 6),
            "screen_panel_count": 1.0,
        })
        warnings = [*result.warnings, EngineeringWarning(
            "LEGACY-GR-SCREEN-REFERENCE-CORRECTED",
            "A tela TL3 usa largura e altura reais do marco abaixo da caixa de persiana, quando houver.",
        )]
        result = _finalize(
            result,
            [*result.unit_bom, screen],
            geometry=geometry,
            model_description=result.model_description + " + TELA MOSQUITEIRA",
            warnings=warnings,
        )
    return result


def _append_generic_shutter(base: CalculationResult, cfg: GrConfiguration) -> CalculationResult:
    shutter = cfg.shutter
    if shutter is None:
        return base
    supported = {
        ShutterMode.MANUAL_SINGLE,
        ShutterMode.BUTTON_SINGLE,
        ShutterMode.REMOTE_SINGLE,
        ShutterMode.MANUAL_DOUBLE_INDEPENDENT_SHAFTS,
    }
    if shutter.mode not in supported:
        raise ValueError(f"Modo de persiana GR não comprovado na ORCS: {shutter.mode.value}")
    if shutter.box_description != v11.GR_SHUTTER_BOX or shutter.slat_description != v11.GR_SHUTTER_SLAT:
        raise ValueError("GR suporta caixa de 200mm e tala de PVC 40mm.")
    if cfg.panel_mode != v06.GR_GLASS_MODE:
        raise ValueError("Persiana GR possui evidência histórica somente com VIDRO INTEIRO.")

    width = float(cfg.width_mm)
    overall_height = float(cfg.height_mm)
    effective_height = overall_height - 200.0
    if effective_height <= 0:
        raise ValueError("Altura GR insuficiente para caixa de persiana de 200mm.")
    bom = v11._restore_full_height_finishes(list(base.unit_bom), overall_height, cfg.quantity)
    box_length = width - 15.0
    guide_length = effective_height
    double = shutter.mode == ShutterMode.MANUAL_DOUBLE_INDEPENDENT_SHAFTS
    if double:
        panel_count = 2.0
        slat_width = (width - 2.0 * 32.0 - 30.0) / 2.0 - 10.0
        shaft_length = width / 2.0 - 40.0
        slat_qty = float(math.ceil(overall_height / 40.0) * 2)
        shaft_qty = 2.0
    else:
        panel_count = 1.0
        slat_width = width - 2.0 * 32.0 - 10.0
        shaft_length = width - 40.0
        slat_qty = float(math.ceil(overall_height / 40.0))
        shaft_qty = 1.0
    if min(box_length, guide_length, slat_width, shaft_length) <= 0:
        raise ValueError("Dimensões da persiana GR ficaram inválidas.")

    bom.extend([
        v11._linear_shutter("321040", "SHUTTER_BOX", box_length, 1.0, cfg.quantity, "GR!D47/G47"),
        v11._linear_shutter("327201", "SHUTTER_SIDE_GUIDE", guide_length, 2.0, cfg.quantity, "GR!D48/G48"),
    ])
    if double:
        bom.append(v11._linear_shutter("327204", "SHUTTER_CENTRAL_GUIDE", guide_length, 1.0, cfg.quantity, "GR!D49/G49"))
    bom.extend([
        v11._linear_shutter("326015_F", "SHUTTER_SLAT", slat_width, slat_qty, cfg.quantity, "GR!D50/G50 + PHYSICAL_ROUND_UP"),
        v11._linear_shutter("311712", "SHUTTER_TERMINAL", slat_width, panel_count, cfg.quantity, "GR!D51/G51"),
        v11._linear_shutter("375021", "SHUTTER_SHAFT", shaft_length, shaft_qty, cfg.quantity, "GR!D52/G52"),
    ])

    if double:
        accessories = [
            ("370113", "SHUTTER_LATERAL_COVER", 2.0),
            ("371513_4", "SHUTTER_PULLEY_PLATE", 2.0),
            ("371127", "SHUTTER_INDEPENDENT_SHAFT_DIVIDER", 1.0),
            ("375110", "SHUTTER_PULLEY", 2.0),
            ("375213", "SHUTTER_END_CAP", 2.0),
            ("375234", "SHUTTER_END_CAP_ADAPTER", 2.0),
            ("375339", "SHUTTER_RECESSED_WINDER", 2.0),
            ("373128", "SHUTTER_GUIDE_INVITATION_PAIR", 1.0),
            ("375678", "SHUTTER_FIRST_SLAT_COUPLING", 4.0),
            ("375415", "SHUTTER_FRONT_PIN", 2.0),
            ("375441", "SHUTTER_OPENING_LIMITER", 4.0),
        ]
        suffix = " COM PERSIANA MANUAL 2 PAINÉIS EIXOS INDEPENDENTES"
    elif shutter.mode == ShutterMode.MANUAL_SINGLE:
        accessories = [
            ("370113", "SHUTTER_LATERAL_COVER", 2.0),
            ("371513_4", "SHUTTER_PULLEY_PLATE", 1.0),
            ("371513_2", "SHUTTER_END_PLATE", 1.0),
            ("375110", "SHUTTER_PULLEY", 1.0),
            ("375213", "SHUTTER_END_CAP", 1.0),
            ("375234", "SHUTTER_END_CAP_ADAPTER", 1.0),
            ("375339", "SHUTTER_RECESSED_WINDER", 1.0),
            ("373128", "SHUTTER_GUIDE_INVITATION_PAIR", 1.0),
            ("375678", "SHUTTER_FIRST_SLAT_COUPLING", 2.0),
            ("375415", "SHUTTER_FRONT_PIN", 1.0),
            ("375441", "SHUTTER_OPENING_LIMITER", 2.0),
        ]
        suffix = " COM PERSIANA"
    else:
        motor = "MOT1" if shutter.mode == ShutterMode.REMOTE_SINGLE else "MOT2"
        accessories = [
            ("370113", "SHUTTER_LATERAL_COVER", 1.0),
            ("371513_2", "SHUTTER_END_PLATE", 1.0),
            ("370141", "SHUTTER_MOTOR_COVER", 1.0),
            ("371553", "SHUTTER_MOTOR_PLATE", 1.0),
            ("375213", "SHUTTER_END_CAP", 1.0),
            ("375234", "SHUTTER_END_CAP_ADAPTER", 1.0),
            (motor, "SHUTTER_MOTOR", 1.0),
            ("373128", "SHUTTER_GUIDE_INVITATION_PAIR", 1.0),
            ("375678", "SHUTTER_FIRST_SLAT_COUPLING", 2.0),
            ("375441", "SHUTTER_OPENING_LIMITER", 2.0),
        ]
        suffix = " COM PERSIANA AUTOMATIZADA " + (
            "CONTROLE REMOTO" if shutter.mode == ShutterMode.REMOTE_SINGLE else "BOTOEIRA"
        )
    for code, role, quantity in accessories:
        bom.append(v11._unit_shutter(code, role, quantity, cfg.quantity, "GR!85:102 + CR homologada"))

    geometry = dict(base.geometry)
    geometry.update({
        "overall_height_mm": round(overall_height, 6),
        "shutter_box_height_mm": 200.0,
        "shutter_main_opening_height_mm": round(effective_height, 6),
        "shutter_panel_count": panel_count,
        "shutter_box_length_mm": round(box_length, 6),
        "shutter_side_guide_length_mm": round(guide_length, 6),
        "shutter_slat_width_mm": round(slat_width, 6),
        "shutter_slat_quantity": slat_qty,
        "shutter_shaft_length_mm": round(shaft_length, 6),
        "shutter_shaft_quantity": shaft_qty,
    })
    warnings = [*base.warnings, EngineeringWarning(
        "LEGACY-GR-SHUTTER-HELPERS-RECOVERED",
        "O kit de persiana usa os mesmos códigos físicos homologados na CR; a Fase 25 o combina com toda a matriz GR válida.",
    )]
    return _finalize(
        base,
        bom,
        geometry=geometry,
        model_description=base.model_description + suffix,
        warnings=warnings,
    )


def _selected_cremona(cfg: GrConfiguration) -> tuple[str, bool]:
    description = cfg.cremona_description
    used_default = False
    if not description:
        if cfg.hinge_description == GR_HINGE_OB:
            raise ValueError("Dobradiça Sistema OB com cremona exige seleção explícita do comprimento.")
        description = v06.GR_CREMONA_WINDOW_800
        used_default = True
    material = HARDWARE.get(normalize(description))
    if material is None:
        raise ValueError(f"Cremona não cadastrada na LISTAFERRA: {description}")
    allowed = _OB_CREMONA_CODES if cfg.hinge_description == GR_HINGE_OB else _STANDARD_CREMONA_CODES
    if material.code not in allowed:
        family = "Oscilo/Giro" if cfg.hinge_description == GR_HINGE_OB else "standard 7,5/15mm"
        raise ValueError(f"A dobradiça selecionada exige cremona {family}.")
    return description, used_default


def _replace_hardware(base: CalculationResult, cfg: GrConfiguration) -> CalculationResult:
    bom = [
        item for item in base.unit_bom
        if item.category != "FERRAGENS" or item.role == "REINFORCEMENT_SCREWS"
    ]
    warnings = [
        warning for warning in base.warnings
        if warning.code != "GR-OB-DOOR-HARDWARE-SCOPE"
    ]
    leaves = cfg.leaf_count

    if cfg.hinge_description == GR_HINGE_OB:
        ob_components = (
            ("FALSO COMPASSO", "OB_FALSE_STAY"),
            ("CORPO DA DOBRADIÇA", "OB_HINGE_BODY"),
            ("CORPO E PINO DOBRADIÇA SUPERIOR", "OB_UPPER_HINGE_PIN"),
            ("DOBRADIÇA INFERIOR ", "OB_LOWER_HINGE"),
            ("SUPORTE DA DOBRADIÇA INFERIOR", "OB_LOWER_HINGE_SUPPORT"),
            ("CONJUNTO  CAPAS DOBRADIÇA OSCILO", "OB_HINGE_COVERS"),
        )
        for description, role in ob_components:
            bom.append(_unit_component(description, role, leaves, cfg.quantity, "GR!105:110 / U3=1"))
        primary_hinge_qty = float(leaves)
    elif cfg.hinge_description == GR_HINGE_PERNIO:
        primary_hinge_qty = float(3 * leaves)
        bom.append(_unit_component(
            "DOBRADIÇA PÊRNIO", "HINGE_PERNIO", primary_hinge_qty,
            cfg.quantity, "GR!G105/I105 + confirmação Fase 25",
        ))
        warnings.append(EngineeringWarning(
            "GR-PERNIO-LOW-HISTORICAL-FREQUENCY",
            "DOBRADIÇA PÊRNIO é opção válida e pouco frequente: 3 unidades por folha, 8 PAR1 por unidade.",
        ))
    else:
        primary_hinge_qty = float(3 * leaves)
        bom.append(_unit_component(
            "DOBRADIÇA 90MM", "HINGE_90MM", primary_hinge_qty,
            cfg.quantity, "GR!G105/I105",
        ))

    handle_qty = 1.0
    closure_qty = 1.0
    counter_qty = 0.0
    physical_window = cfg.leaf_system == v06.GR_LEAF_SYSTEM_WINDOW_EXTERNAL
    lock_description_override = None
    if physical_window and cfg.window_lock_length_mm is not None:
        lock_description_override = f"{{description}} — COMP. {float(cfg.window_lock_length_mm):g}MM"

    if cfg.closure_mode in (v06.GR_CLOSURE_MONOPOINT, v06.GR_CLOSURE_MULTIPOINT):
        bom.append(_unit_component("MAÇANETA DUPLA (GIRO)", "DOUBLE_HANDLE", 1, cfg.quantity, "GR!G111/I111"))
        if cfg.closure_mode == v06.GR_CLOSURE_MULTIPOINT:
            lock_description = "FECHADURA MULTIPONTO (GIRO)"
            role = "WINDOW_MULTIPOINT_LOCK" if physical_window else "MULTIPOINT_LOCK"
            counter_qty = 4.0
        else:
            lock_description = "FECHADURA MONOPONTO (GIRO)"
            role = "WINDOW_MONOPOINT_LOCK" if physical_window else "MONOPOINT_LOCK"
        override = None
        if lock_description_override:
            override = lock_description_override.format(description=lock_description)
        bom.append(_unit_component(
            lock_description, role, 1, cfg.quantity, "GR!G112/I112",
            description_override=override,
        ))
        if not physical_window:
            bom.append(_unit_component("CILINDRO 45X45MM", "CYLINDER_45X45", 1, cfg.quantity, "GR!G113/I113"))
        else:
            warnings.append(EngineeringWarning(
                "GR-WINDOW-LOCK-NO-CYLINDER",
                "Folha de janela usa fechadura sem chave/cilindro; o comprimento é selecionado no orçamento.",
            ))
        if counter_qty:
            bom.append(_unit_component("CONTRA FECHO STANDARD", "STANDARD_COUNTER_LOCK", counter_qty, cfg.quantity, "GR!G114/I114"))
        bom.append(_unit_component("CONTRA-TESTA ", "STRIKE_PLATE", 1, cfg.quantity, "GR!G115/I115"))
    else:
        cremona, used_default = _selected_cremona(cfg)
        keyed = cfg.closure_mode == GR_CLOSURE_KEY_CREMONA
        handle = "MAÇANETA COM CHAVE" if keyed else "MACANETA STANDARD"
        role = "KEYED_HANDLE" if keyed else "STANDARD_HANDLE"
        bom.append(_unit_component(handle, role, 1, cfg.quantity, "GR!G111/I111"))
        bom.append(_unit_component(cremona, "CREMONA", 1, cfg.quantity, "GR!G112/I112 / seleção do orçamento"))
        counter_qty = 2.0
        bom.append(_unit_component("CONTRA FECHO STANDARD", "STANDARD_COUNTER_LOCK", counter_qty, cfg.quantity, "GR!G114/I114"))
        if cfg.closure_mode == GR_CLOSURE_CREMONA_ALIAS:
            warnings.append(EngineeringWarning(
                "GR-CLOSURE-CREMONA-ALIAS-NORMALIZED",
                "O texto histórico MAÇANETA COM CREMONA foi normalizado para o conjunto sem chave.",
            ))
        if used_default:
            warnings.append(EngineeringWarning(
                "GR-CREMONA-LEGACY-DEFAULT",
                "Cremona não informada: CRE12 de 800mm foi mantida apenas por compatibilidade; novos orçamentos devem selecionar a peça.",
            ))

    if leaves == 2:
        bom.extend([
            _unit_component("CONTRA FECHO UNHA", "PASSIVE_LEAF_COUNTER_CLAW", 2, cfg.quantity, "GR!G116/I116"),
            _unit_component("FECHO UNHA", "PASSIVE_LEAF_CLAW_LOCK", 2, cfg.quantity, "GR!G117/I117"),
        ])

    hardware_screws = primary_hinge_qty * 8.0 + (handle_qty + closure_qty + counter_qty) * 2.0
    bom.append(_unit_component(
        "PARAFUSOS DE FERRAGEM", "HARDWARE_SCREWS", hardware_screws,
        cfg.quantity, "GR!G119=(G105*8)+(G111+G112+G114)*2",
    ))
    if cfg.hinge_description == GR_HINGE_OB:
        warnings.append(EngineeringWarning(
            "GR-OB-DOOR-HARDWARE-SCOPE",
            f"Conjunto Sistema OB calculado por GR!105:110; GR!G119 resulta em {hardware_screws:g} PAR1 para este fechamento.",
        ))
    return _finalize(base, bom, warnings=warnings)


def _apply_glass_contract(base: CalculationResult, cfg: GrConfiguration) -> CalculationResult:
    glass, origin = _glass_for_configuration(cfg)
    if glass is None or origin is None:
        return base
    bead_code = _bead_for_thickness(float(glass.thickness_mm or 0.0))
    bead = MATERIALS[bead_code]
    bom = []
    for item in base.unit_bom:
        if item.category == "VIDROS":
            area = float(item.area_m2 or 0.0)
            cost = area * item.quantity_per_unit * glass.unit_price
            bom.append(replace(
                item,
                material_code=glass.code,
                description=glass.description,
                unit_price=glass.unit_price,
                cost_per_unit_product=round(cost, 6),
                source=(item.source or "") + " / FASE25_GLASS_CONTRACT",
            ))
        elif item.category == "BAGUETES" and (
            "GLASS_BEAD" in item.role or "FLAG_BEAD" in item.role
        ):
            cost = float(item.length_mm or 0.0) / 1000.0 * item.quantity_per_unit * bead.unit_price
            bom.append(replace(
                item,
                material_code=bead.code,
                description=bead.description,
                unit_price=bead.unit_price,
                cost_per_unit_product=round(cost, 6),
                source=(item.source or "") + " / baguete pela espessura da Fase 25",
            ))
        else:
            bom.append(item)
    panels = [replace(
        panel,
        material_code=glass.code,
        material_description=glass.description,
        unit_cost=glass.unit_price,
        total_cost=round(panel.area_m2 * panel.quantity * glass.unit_price, 6),
    ) for panel in base.glass_panels]
    warning = EngineeringWarning(
        "GR-GLASS-CATALOG-ALIAS" if origin == "ALIAS" else "GR-CUSTOM-GLASS-PRICED",
        (
            "Descrição histórica associada a uma linha equivalente da LISTAVIDROS."
            if origin == "ALIAS"
            else "Vidro ausente da LISTAVIDROS calculado com código, espessura e preço informados no orçamento."
        ),
    )
    return _finalize(base, bom, glass_panels=panels, warnings=[*base.warnings, warning])


def calculate_gr(cfg: GrConfiguration) -> CalculationResult:
    """Fase 25 final: cobertura GR consolidada e pronta para plano de compra."""
    _validate_common(cfg)
    has_flags = bool(cfg.bottom_flag_height_mm or cfg.top_flag_height_mm)

    if has_flags:
        try:
            result = _call_v24(cfg, canonical_hardware=False)
        except ValueError:
            result = _calculate_generic_flags(cfg)
    elif cfg.shutter is not None and (
        cfg.leaf_system == v06.GR_LEAF_SYSTEM_WINDOW_EXTERNAL and cfg.leaf_count == 2
    ):
        effective = replace(cfg, height_mm=float(cfg.height_mm) - 200.0, shutter=None, screen_enabled=False)
        result = _calculate_plain(effective)
        if cfg.screen_enabled:
            screen = v14._screen_component(float(cfg.width_mm), float(cfg.height_mm) - 200.0, cfg.quantity)
            result = _finalize(result, [*result.unit_bom, screen], model_description=result.model_description + " + TELA MOSQUITEIRA")
        result = _append_generic_shutter(result, cfg)
    else:
        result = _calculate_plain(cfg)
        if cfg.screen_enabled and not any(item.category == "TELA" for item in result.unit_bom):
            screen = v14._screen_component(float(cfg.width_mm), float(result.geometry["frame_height_final_mm"]), cfg.quantity)
            result = _finalize(result, [*result.unit_bom, screen], model_description=result.model_description + " + TELA MOSQUITEIRA")

    if cfg.shutter is not None and has_flags and not any(item.category == "PERSIANA" for item in result.unit_bom):
        result = _append_generic_shutter(result, cfg)

    result = _replace_hardware(result, cfg)
    result = _apply_glass_contract(result, cfg)

    warnings = list(result.warnings)
    physical_application = _physical_application(cfg)
    if cfg.application != physical_application and not any(
        warning.code == "GR-APPLICATION-INDEPENDENT" for warning in warnings
    ):
        warnings.append(EngineeringWarning(
            "GR-APPLICATION-INDEPENDENT",
            "PORTA/JANELA é classificação comercial; geometria e materiais seguem o tipo físico da folha.",
        ))
    return replace(
        result,
        model_description=_commercial_description(result.model_description, cfg.application),
        warnings=warnings,
        calculation_version=GR_ENGINE_VERSION,
    )
