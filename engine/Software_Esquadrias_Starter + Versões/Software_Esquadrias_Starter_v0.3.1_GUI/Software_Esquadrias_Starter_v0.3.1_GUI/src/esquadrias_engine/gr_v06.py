from __future__ import annotations

from dataclasses import dataclass, fields
import math

from . import gr as legacy
from .catalog import GLASSES, MATERIALS, normalize
from .models import BomComponent, CalculationResult, EngineeringWarning, GlassPanel


GR_ENGINE_VERSION = "GR_ENGINE_0.6.0"
GR_PANEL_MODE = legacy.GR_PANEL_MODE
GR_GLASS_MODE = "VIDRO INTEIRO"

# Reexporta os contratos já comprovados na v0.5.
GR_LEAF_SYSTEM_INTERNAL = legacy.GR_LEAF_SYSTEM_INTERNAL
GR_LEAF_SYSTEM_EXTERNAL = legacy.GR_LEAF_SYSTEM_EXTERNAL
GR_LEAF_SYSTEM_WINDOW_EXTERNAL = legacy.GR_LEAF_SYSTEM_WINDOW_EXTERNAL
GR_LEAF_SYSTEMS = legacy.GR_LEAF_SYSTEMS
GR_APPLICATION_DOOR = legacy.GR_APPLICATION_DOOR
GR_APPLICATION_WINDOW = legacy.GR_APPLICATION_WINDOW
GR_MODULE_MODE = legacy.GR_MODULE_MODE
GR_CLOSURE_MONOPOINT = legacy.GR_CLOSURE_MONOPOINT
GR_CLOSURE_MULTIPOINT = legacy.GR_CLOSURE_MULTIPOINT
GR_CLOSURE_WINDOW_CREMONA = legacy.GR_CLOSURE_WINDOW_CREMONA
GR_DOOR_CLOSURES = legacy.GR_DOOR_CLOSURES
GR_CREMONA_WINDOW_800 = legacy.GR_CREMONA_WINDOW_800
GR_HINGE = legacy.GR_HINGE
GR_INTERNAL_FINISH = legacy.GR_INTERNAL_FINISH
GR_EXTERNAL_FINISH = legacy.GR_EXTERNAL_FINISH


@dataclass(frozen=True)
class GrConfiguration(legacy.GrConfiguration):
    """Contrato GR v0.6.

    ``panel_mode=VIDRO INTEIRO`` representa o legado ``GR!R2=""`` de forma
    explícita para API. Painel completo continua sendo o default compatível.
    """

    glass_description: str | None = None


_GROUPS = (
    "PERFIS PRINCIPAIS", "BAGUETES", "ACABAMENTOS", "REFORÇOS",
    "VIDROS", "TELA", "VEDAÇÕES", "ACESSÓRIOS", "FERRAGENS",
)

# O XLSM já aponta as três linhas de vedação GR para A53/A55, porém uma condição
# copiada de PR4263 zera tudo. A fabricação confirmou em 2026-09-22 os papéis
# físicos: A53 é usado como borracha de vidro/lambri; A55 é a borracha redonda
# aplicada no marco por dentro e na folha por fora.
_SEALS = {
    "ACB606": ("BORRACHA DE VIDRO / LAMBRI", 1.80),
    "AC0002": ("BORRACHA REDONDA", 1.60),
}


def _legacy_config(cfg: GrConfiguration) -> legacy.GrConfiguration:
    data = {field.name: getattr(cfg, field.name) for field in fields(legacy.GrConfiguration)}
    if cfg.panel_mode == GR_GLASS_MODE:
        data["panel_mode"] = legacy.GR_PANEL_MODE
    return legacy.GrConfiguration(**data)


def _glass_and_bead(description: str):
    glass = GLASSES.get(normalize(description))
    if glass is None or glass.code == "0" or glass.thickness_mm is None:
        raise ValueError(f"Vidro GR não suportado: {description}")
    thickness = float(glass.thickness_mm)
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
    bead = next((code for upper, code in ranges if thickness < upper), None)
    if bead is None:
        raise ValueError(f"Espessura de vidro {thickness:g} mm sem baguete GR comprovada.")
    return glass, bead


def _validate(cfg: GrConfiguration) -> None:
    if cfg.panel_mode not in (GR_PANEL_MODE, GR_GLASS_MODE):
        raise ValueError(f"painel fora do escopo do GR_ENGINE_0.6.0: {cfg.panel_mode}")

    # Reutiliza todos os gates já auditados da v0.5, normalizando apenas o
    # modo VIDRO INTEIRO para o R2 vazio do legado.
    legacy._validate(_legacy_config(cfg))

    if cfg.panel_mode == GR_PANEL_MODE:
        if cfg.glass_description not in (None, ""):
            raise ValueError("PAINEL COMPLETO não deve informar glass_description.")
        return

    if cfg.application != GR_APPLICATION_DOOR:
        raise ValueError("GR_ENGINE_0.6.0 libera vidro inteiro somente para PORTA.")
    if cfg.leaf_count != 1:
        raise ValueError("GR_ENGINE_0.6.0 libera vidro inteiro somente em porta de 1 folha.")
    if cfg.leaf_system not in (GR_LEAF_SYSTEM_INTERNAL, GR_LEAF_SYSTEM_EXTERNAL):
        raise ValueError("VIDRO INTEIRO v0.6 exige folha de porta Design 60x104.")
    if not cfg.glass_description:
        raise ValueError("VIDRO INTEIRO exige glass_description.")
    _glass_and_bead(cfg.glass_description)


def _linear_component(code: str, role: str, length_mm: float, quantity: float,
                      order_quantity: int, source: str, *, description: str | None = None,
                      category: str | None = None, unit_price: float | None = None) -> BomComponent:
    if not math.isfinite(length_mm) or length_mm <= 0:
        raise ValueError(f"Comprimento inválido para {role}: {length_mm:g} mm.")
    if not math.isfinite(quantity) or quantity <= 0:
        raise ValueError(f"Quantidade inválida para {role}: {quantity:g}.")
    material = MATERIALS.get(code)
    if material is not None:
        resolved_description = description or material.description
        resolved_price = material.unit_price if unit_price is None else unit_price
    else:
        resolved_description = description or code
        if unit_price is None:
            raise ValueError(f"Preço não configurado para {code}.")
        resolved_price = unit_price
    resolved_category = category or "BAGUETES"
    cost = length_mm / 1000.0 * quantity * resolved_price
    return BomComponent(
        category=resolved_category,
        role=role,
        material_code=code,
        description=resolved_description,
        unit="m",
        length_mm=round(length_mm, 6),
        width_mm=None,
        height_mm=None,
        area_m2=None,
        quantity_per_unit=float(quantity),
        quantity_order=float(quantity * order_quantity),
        unit_price=resolved_price,
        cost_per_unit_product=round(cost, 6),
        source=source,
    )


def _seal_component(code: str, role: str, length_mm: float, quantity: float,
                    order_quantity: int, source: str) -> BomComponent:
    description, price = _SEALS[code]
    return _linear_component(
        code, role, length_mm, quantity, order_quantity, source,
        description=description, category="VEDAÇÕES", unit_price=price,
    )


def _glass_component(glass, width_mm: float, height_mm: float,
                     order_quantity: int) -> tuple[BomComponent, GlassPanel]:
    if width_mm <= 0 or height_mm <= 0:
        raise ValueError(f"Vidro GR tecnicamente impossível: {width_mm:g}x{height_mm:g} mm.")
    area = width_mm / 1000.0 * height_mm / 1000.0
    cost = area * glass.unit_price
    component = BomComponent(
        category="VIDROS",
        role="GLASS_PANEL",
        material_code=glass.code,
        description=glass.description,
        unit="m²",
        length_mm=None,
        width_mm=round(width_mm, 6),
        height_mm=round(height_mm, 6),
        area_m2=round(area, 6),
        quantity_per_unit=1.0,
        quantity_order=float(order_quantity),
        unit_price=glass.unit_price,
        cost_per_unit_product=round(cost, 6),
        source="GR!B68:I68 / GR!D68=D13-PFAB!B12 / GR!E68=D14-PFAB!B12",
    )
    panel = GlassPanel(
        source="GR!D68:E68",
        position="R1C1",
        width_mm=round(width_mm, 6),
        height_mm=round(height_mm, 6),
        quantity=1.0,
        material_code=glass.code,
        material_description=glass.description,
        area_m2=round(area, 6),
        unit_cost=glass.unit_price,
        total_cost=round(cost, 6),
    )
    return component, panel


def _physical_seals(cfg: GrConfiguration, *, bead_width_mm: float,
                    bead_height_mm: float, leaf_width_mm: float,
                    leaf_height_mm: float) -> list[BomComponent]:
    leaves = cfg.leaf_count
    glazing_perimeter = 2.0 * (bead_width_mm + bead_height_mm)
    leaf_perimeter = 2.0 * (leaf_width_mm + leaf_height_mm)
    source = (
        "GR!76:78 + LEGACY_BUG_CONFIRMED_2026-09-22 "
        "+ RESOLVED_PHYSICAL_2026-09-22"
    )
    return [
        _seal_component(
            "ACB606", "GLASS_OR_LAMBRI_SEAL", glazing_perimeter, leaves,
            cfg.quantity, source + " / borracha de vidro também no lambri",
        ),
        _seal_component(
            "AC0002", "ROUND_SEAL_LEAF", leaf_perimeter, leaves,
            cfg.quantity, source + " / folha por fora",
        ),
        _seal_component(
            "AC0002", "ROUND_SEAL_FRAME", leaf_perimeter, leaves,
            cfg.quantity, source + " / marco por dentro",
        ),
    ]


def _finalize(base: CalculationResult, bom: list[BomComponent], *,
              model_description: str | None = None,
              geometry: dict[str, float] | None = None,
              glass_panels: list[GlassPanel] | None = None) -> CalculationResult:
    breakdown = {
        group: round(sum(item.cost_per_unit_product for item in bom if item.category == group), 6)
        for group in _GROUPS
    }
    total = round(sum(item.cost_per_unit_product for item in bom), 6)
    breakdown["TOTAL"] = total
    warnings = list(base.warnings)
    warnings.append(EngineeringWarning(
        "LEGACY-GR-SEALING-CORRECTED",
        "GR!76:78 zerava as vedações por condição de família incorreta; fabricação confirmou borracha de vidro/lambri e borracha redonda em folha e marco.",
    ))
    return CalculationResult(
        model_description=model_description or base.model_description,
        geometry=geometry or dict(base.geometry),
        unit_bom=bom,
        cost_breakdown=breakdown,
        unit_cost=total,
        leaf_openings=list(base.leaf_openings),
        transoms=list(base.transoms),
        fixed_panels=list(base.fixed_panels),
        glass_panels=list(base.glass_panels) if glass_panels is None else glass_panels,
        warnings=warnings,
        calculation_version=GR_ENGINE_VERSION,
    )


def _calculate_panel(cfg: GrConfiguration) -> CalculationResult:
    base = legacy.calculate_gr(_legacy_config(cfg))
    bead_width = base.geometry["panel_bead_width_mm"]
    bead_height = base.geometry["panel_bead_height_mm"]
    seals = _physical_seals(
        cfg,
        bead_width_mm=bead_width,
        bead_height_mm=bead_height,
        leaf_width_mm=base.geometry["leaf_width_final_mm"],
        leaf_height_mm=base.geometry["leaf_height_final_mm"],
    )
    return _finalize(base, [*base.unit_bom, *seals])


def _calculate_glass(cfg: GrConfiguration) -> CalculationResult:
    # A geometria estrutural é idêntica ao recorte de painel completo sem
    # travessas; somente baguete/preenchimento mudam. Isso preserva as regras
    # de marco, folha, reforços, acabamentos, calços e ferragens já auditadas.
    base = legacy.calculate_gr(_legacy_config(cfg))
    bead_width = base.geometry["panel_bead_width_mm"]
    bead_height = base.geometry["panel_bead_height_mm"]
    glass, bead_code = _glass_and_bead(cfg.glass_description or "")

    bom = [
        item for item in base.unit_bom
        if item.role not in {"PANEL_BEAD_WIDTH", "PANEL_BEAD_HEIGHT", "PANEL_FILL"}
    ]
    bom.extend([
        _linear_component(
            bead_code, "GLASS_BEAD_WIDTH", bead_width, 2, cfg.quantity,
            "GR!B13:E13/G13 + GR!R2=\"\" (VIDRO INTEIRO)",
        ),
        _linear_component(
            bead_code, "GLASS_BEAD_HEIGHT", bead_height, 2, cfg.quantity,
            "GR!B14:E14/G14 + GR!R2=\"\" (VIDRO INTEIRO)",
        ),
    ])
    glass_component, glass_panel = _glass_component(
        glass, bead_width - 8.0, bead_height - 8.0, cfg.quantity
    )
    bom.append(glass_component)
    bom.extend(_physical_seals(
        cfg,
        bead_width_mm=bead_width,
        bead_height_mm=bead_height,
        leaf_width_mm=base.geometry["leaf_width_final_mm"],
        leaf_height_mm=base.geometry["leaf_height_final_mm"],
    ))

    geometry = dict(base.geometry)
    geometry["glass_bead_width_mm"] = geometry.pop("panel_bead_width_mm")
    geometry["glass_bead_height_mm"] = geometry.pop("panel_bead_height_mm")
    geometry.pop("panel_fill_strip_length_mm", None)
    geometry.pop("panel_fill_strip_quantity", None)
    geometry["glass_width_mm"] = round(bead_width - 8.0, 6)
    geometry["glass_height_mm"] = round(bead_height - 8.0, 6)

    return _finalize(
        base,
        bom,
        model_description=base.model_description.replace(" COM PAINEL HORIZONTAL", ""),
        geometry=geometry,
        glass_panels=[glass_panel],
    )


def calculate_gr(cfg: GrConfiguration) -> CalculationResult:
    """Calcula GR v0.6 com vedações físicas e primeiro recorte de vidro."""
    _validate(cfg)
    if cfg.panel_mode == GR_GLASS_MODE:
        return _calculate_glass(cfg)
    return _calculate_panel(cfg)
