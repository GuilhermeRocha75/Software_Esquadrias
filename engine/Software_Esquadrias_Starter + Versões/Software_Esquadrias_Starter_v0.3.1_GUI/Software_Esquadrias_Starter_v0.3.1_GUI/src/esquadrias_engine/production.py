"""Typed fabrication projection of validated results; no purchase or prices.

Lengths without a proved final/cut relationship remain explicitly unknown.
The projection never changes the supplied calculation or rounds quantities.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from .catalog import BAR_STOCK_CODES
from .models import CalculationResult

PRODUCTION_CONTRACT_VERSION = "OP_TECHNICAL_0.1.0"


@dataclass(frozen=True)
class ProductionIssue:
    """Machine-readable technical finding, optionally tied to a BOM position."""

    code: str
    field: str
    message: str
    position: int | None = None


@dataclass(frozen=True)
class ProductionLine:
    """One source BOM row. Counts use quantity_unit, never material_unit.

    Raw BOM counts are retained separately, notably for CR mesh area factors.
    A null final length means unknown or inapplicable, never zero.
    """

    position: int
    group: str
    utilization: str
    code: str | None
    description: str | None
    material_unit: str | None
    quantity_unit: str
    quantity_per_unit: float
    quantity_total: float
    bom_quantity_per_unit: float
    bom_quantity_total: float
    final_length_mm: float | None
    cut_length_mm: float | None
    width_mm: float | None
    height_mm: float | None
    source: str | None
    measurement_basis: str | None
    splice_status: str | None


@dataclass(frozen=True)
class ProductionItemData:
    """Immutable technical projection; positions/groups follow unit_bom."""

    family: str
    engine_version: str
    contract_version: str
    model_description: str
    lines: tuple[ProductionLine, ...]
    issues: tuple[ProductionIssue, ...]


_GEOMETRY_FINALS = {
    "FRAME_HORIZONTAL": "frame_width_final_mm",
    "FRAME_VERTICAL": "frame_height_final_mm",
    "LEAF_HORIZONTAL": "leaf_width_final_mm",
    "LEAF_VERTICAL": "leaf_height_final_mm",
    "SCREEN_LEAF_HORIZONTAL": "leaf_width_final_mm",
    "SCREEN_LEAF_VERTICAL": "leaf_height_final_mm",
    "FRAME_WIDTH": "frame_width_final_mm",
    "FRAME_HEIGHT": "frame_height_final_mm",
    "LEAF_WIDTH": "leaf_width_final_mm",
    "LEAF_HEIGHT": "leaf_height_final_mm",
    "Marco Largura": "width_mm",
    "Marco Altura": "height_mm",
}

# These calls in the homologated calculators use the same dimension for
# manufacture and cutting (no weld addition). Keep an explicit allowlist:
# an unrecognized future role must produce a gap, not inherit this rule.
_DIRECT_LENGTH_ROLES = {
    "INTERLOCK", "LEAF_COVER", "CENTRAL_CLOSURE", "ALUMINUM_RAIL",
    "DESIGN_Z_PROFILE", "DESIGN_Z_TRIM", "PANEL_FILL", "LOWER_PANEL_FILL",
    "MIXED_HORIZONTAL_TRANSOM", "MIXED_HORIZONTAL_TRANSOM_REINFORCEMENT",
    "UPPER_GLASS_BEAD_WIDTH", "UPPER_GLASS_BEAD_HEIGHT",
    "LOWER_PANEL_BEAD_WIDTH", "LOWER_PANEL_BEAD_HEIGHT",
    "GLAZING_BEAD_HORIZONTAL", "GLAZING_BEAD_VERTICAL",
    "GLAZING_BEAD_HEIGHT", "GLAZING_BEAD_WIDTH",
    "GLASS_BEAD_WIDTH", "GLASS_BEAD_HEIGHT", "PANEL_BEAD_WIDTH", "PANEL_BEAD_HEIGHT",
    "SCREEN_BEAD_HORIZONTAL", "SCREEN_BEAD_VERTICAL",
    "INTERNAL_FINISH_HORIZONTAL", "INTERNAL_FINISH_VERTICAL",
    "EXTERNAL_FINISH_HORIZONTAL", "EXTERNAL_FINISH_VERTICAL",
    "INTERNAL_FINISH_WIDTH", "INTERNAL_FINISH_HEIGHT",
    "EXTERNAL_FINISH_WIDTH", "EXTERNAL_FINISH_HEIGHT",
    "FRAME_REINFORCEMENT_HORIZONTAL", "FRAME_REINFORCEMENT_VERTICAL",
    "LEAF_REINFORCEMENT_HORIZONTAL", "LEAF_REINFORCEMENT_VERTICAL",
    "FRAME_REINFORCEMENT_WIDTH", "FRAME_REINFORCEMENT_HEIGHT",
    "LEAF_REINFORCEMENT_WIDTH", "LEAF_REINFORCEMENT_HEIGHT",
    "STRUCTURAL_REINFORCEMENT", "LEAF_TRANSOM_HORIZONTAL", "LEAF_TRANSOM_VERTICAL",
    "FIXED_PANEL_TRANSOM_HORIZONTAL", "FIXED_PANEL_TRANSOM_VERTICAL",
    "LEAF_TRANSOM_REINFORCEMENT_HORIZONTAL", "LEAF_TRANSOM_REINFORCEMENT_VERTICAL",
    "FIXED_PANEL_TRANSOM_REINFORCEMENT_HORIZONTAL", "FIXED_PANEL_TRANSOM_REINFORCEMENT_VERTICAL",
    "LEAF_SEPARATOR_HORIZONTAL", "LEAF_SEPARATOR_VERTICAL",
    "LEAF_SEPARATOR_TRANSOM_REINFORCEMENT_HORIZONTAL", "LEAF_SEPARATOR_TRANSOM_REINFORCEMENT_VERTICAL",
    "SHUTTER_BOX", "SHUTTER_SIDE_GUIDE", "SHUTTER_CENTRAL_GUIDE",
    "SHUTTER_SLAT", "SHUTTER_TERMINAL", "SHUTTER_SHAFT", "SHUTTER_GUIDE_EXTENDER",
    "Trav. Horiz. Largura", "Trav. Vert. Altura", "Baguete Largura", "Baguete Altura",
    "Arremate Int. Largura", "Arremate Int. Altura", "Arremate Ext. Largura", "Arremate Ext. Altura",
    "Ref. Trav. Horiz. Largura", "Ref. Trav. Vert. Altura",
}
for _prefix in ("TOP", "BOTTOM"):
    _DIRECT_LENGTH_ROLES.update(f"{_prefix}_{suffix}" for suffix in (
        "BEAD_HORIZONTAL", "BEAD_VERTICAL", "FRAME_REINFORCEMENT_HORIZONTAL", "FRAME_REINFORCEMENT_VERTICAL",
        "FIXED_FRAME_REINFORCEMENT_HORIZONTAL", "FIXED_FRAME_REINFORCEMENT_VERTICAL",
        "BOUNDARY_TRANSOM_HORIZONTAL", "FIXED_DIVIDER_HORIZONTAL", "FIXED_DIVIDER_VERTICAL",
        "BOUNDARY_TRANSOM_REINFORCEMENT_HORIZONTAL", "FIXED_DIVIDER_TRANSOM_REINFORCEMENT_HORIZONTAL",
        "FIXED_DIVIDER_TRANSOM_REINFORCEMENT_VERTICAL", "FLAG_BOUNDARY_TRANSOM", "FLAG_BOUNDARY_REINFORCEMENT",
        "FLAG_BEAD_HORIZONTAL", "FLAG_BEAD_VERTICAL", "FLAG_INTERNAL_VERTICAL_TRANSOM", "FLAG_INTERNAL_VERTICAL_REINFORCEMENT",
    ))


def _final_length(component, result):
    """Read existing geometry; do not infer weld allowance from cut length."""
    key = _GEOMETRY_FINALS.get(component.role)
    if key is not None:
        return result.geometry.get(key), f"geometry.{key}"
    if result.calculation_version.startswith("FX_ENGINE_") and component.role in {"Ref. Marco Largura", "Ref. Marco Altura"}:
        # Frozen FX source: E20=D20+5, E21=D21+5. Existing BOM stores E.
        # This adds D representation, without changing a cut/cost formula.
        return component.length_mm - 5.0, "FX!E20/E21 = D20/D21 + 5"
    # CR and separate MX fixed frames already expose their pre-weld size.
    for panel in result.fixed_panels:
        prefix = panel.position.value
        if component.role in {f"{prefix}_FIXED_FRAME_HORIZONTAL", f"{prefix}_FRAME_HORIZONTAL"}:
            return panel.width_mm, f"fixed_panels.{prefix}.width_mm"
        if component.role in {f"{prefix}_FIXED_FRAME_VERTICAL", f"{prefix}_FRAME_VERTICAL"}:
            return panel.frame_height_mm, f"fixed_panels.{prefix}.frame_height_mm"
    if component.role in _DIRECT_LENGTH_ROLES:
        return component.length_mm, "engine.direct_length (no weld addition)"
    # Unknown roles stay available as cuts; no blanket final=cut fallback.
    return None, None


def build_production_item(
    family: str,
    result: CalculationResult,
    *,
    stock_lengths_mm: dict[str, float] | None = None,
) -> ProductionItemData:
    """Project CR/MAXIM_AR/GR/FX without mutating a validated result.

    Optional stock lengths are company/material inputs, used only to flag
    integral oversized pieces. No stock default, optimization or splitting
    is applied. PV/GD and mismatched family/version are rejected.
    """
    prefixes = {"CR": "CR_ENGINE_", "MAXIM_AR": "MX_ENGINE_", "GR": "GR_ENGINE_", "FX": "FX_ENGINE_"}
    if family not in prefixes:
        raise ValueError(f"Família não suportada para OP: {family}; PV/GD não suportadas.")
    if not result.calculation_version.startswith(prefixes[family]):
        raise ValueError("Família da OP incompatível com a versão do resultado.")
    stock = dict(stock_lengths_mm or {})
    if any(not code.strip() or isinstance(value, bool) or not math.isfinite(value) or value <= 0
           for code, value in stock.items()):
        raise ValueError("Comprimento de barra deve ser finito e positivo por material.")
    issues, lines = [], []
    for position, component in enumerate(result.unit_bom, start=1):
        def issue(field, message):
            issues.append(ProductionIssue("MISSING_TECHNICAL_DATA", field, message, position))

        for field, value in (("code", component.material_code), ("description", component.description),
                             ("material_unit", component.unit)):
            if value is None or not str(value).strip() or str(value).strip() == "0":
                issue(field, "Identificação/unidade ausente na saída técnica; linha preservada.")
        for field, value in (("quantity_per_unit", component.quantity_per_unit),
                             ("quantity_total", component.quantity_order),
                             ("cut_length_mm", component.length_mm), ("width_mm", component.width_mm),
                             ("height_mm", component.height_mm)):
            if value is not None and (not math.isfinite(value) or value < 0):
                raise ValueError(f"Saída técnica inválida em {position}.{field}.")
        per_unit, total = component.quantity_per_unit, component.quantity_order
        quantity_unit = "piece" if component.material_code in BAR_STOCK_CODES or component.unit in {"un", "m²"} else "run"
        if not component.unit:
            quantity_unit = "unresolved"
        if component.role in {"PANEL_FILL", "LOWER_PANEL_FILL"}:
            quantity_unit = "unresolved"
            issue("quantity_unit", "Painel fracionário mantido na unidade comercial m; confirmar unidade física de contagem.")
        if component.role == "SCREEN_MESH":
            # CR!G69 is an area factor; physical frame count is independently
            # validated in CR phase 2, including odd leaf counts.
            physical = result.geometry.get("screen_frame_count")
            if physical is not None and component.quantity_per_unit > 0:
                multiplier = component.quantity_order / component.quantity_per_unit
                per_unit, total = physical, physical * multiplier
            else:
                quantity_unit = "consumption_factor"
                issue("quantity_unit", "Tela sem contagem física estruturada.")
        if quantity_unit == "piece" and (not float(per_unit).is_integer() or not float(total).is_integer()):
            issue("quantity_total", "Quantidade física fracionária preservada; confirmar unidade/critério de fabricação.")
        final, basis = _final_length(component, result) if component.length_mm is not None else (None, None)
        if component.length_mm is not None and final is None and quantity_unit != "run":
            issue("final_length_mm", "Relação entre medida final e corte não exposta por esta linha homologada.")
        if final is not None and (not math.isfinite(final) or final <= 0):
            raise ValueError(f"Medida final inválida na posição {position}.")
        splice = None
        if component.material_code in stock and component.length_mm is not None and component.length_mm > stock[component.material_code]:
            splice = "MANUAL_SPLICE_REQUIRED" if family == "FX" else "REQUIRES_ENGINEERING_REVIEW"
            issues.append(ProductionIssue("OVERSIZED_PIECE", "cut_length_mm", "Peça integral preservada; não foram criados segmentos ou posições de emenda.", position))
        lines.append(ProductionLine(
            position, component.category, component.role, component.material_code,
            component.description, component.unit, quantity_unit, per_unit, total,
            component.quantity_per_unit, component.quantity_order, final, component.length_mm,
            component.width_mm, component.height_mm, component.source, basis, splice,
        ))
    return ProductionItemData(family, result.calculation_version, PRODUCTION_CONTRACT_VERSION,
                              result.model_description, tuple(lines), tuple(issues))
