from __future__ import annotations

from dataclasses import fields

from . import gr as legacy
from . import gr_v06 as v06
from .models import BomComponent, CalculationResult, GlassPanel


GR_ENGINE_VERSION = "GR_ENGINE_0.7.0"
GrConfiguration = v06.GrConfiguration

GR_PANEL_MODE = v06.GR_PANEL_MODE
GR_GLASS_MODE = v06.GR_GLASS_MODE
GR_LEAF_SYSTEM_INTERNAL = v06.GR_LEAF_SYSTEM_INTERNAL
GR_LEAF_SYSTEM_EXTERNAL = v06.GR_LEAF_SYSTEM_EXTERNAL
GR_LEAF_SYSTEM_WINDOW_EXTERNAL = v06.GR_LEAF_SYSTEM_WINDOW_EXTERNAL
GR_APPLICATION_DOOR = v06.GR_APPLICATION_DOOR
GR_APPLICATION_WINDOW = v06.GR_APPLICATION_WINDOW


def _legacy_config(cfg: GrConfiguration) -> legacy.GrConfiguration:
    data = {field.name: getattr(cfg, field.name) for field in fields(legacy.GrConfiguration)}
    if cfg.panel_mode == GR_GLASS_MODE:
        data["panel_mode"] = legacy.GR_PANEL_MODE
    return legacy.GrConfiguration(**data)


def _validate(cfg: GrConfiguration) -> None:
    if cfg.panel_mode != GR_GLASS_MODE:
        v06._validate(cfg)
        return

    # Reusa todos os gates estruturais e de ferragens já comprovados pela v0.5,
    # normalizando apenas o preenchimento para permitir calcular a geometria-base.
    legacy._validate(_legacy_config(cfg))

    if cfg.application != GR_APPLICATION_DOOR:
        raise ValueError("GR_ENGINE_0.7.0 libera vidro inteiro somente para PORTA.")
    if cfg.leaf_count not in (1, 2):
        raise ValueError("GR_ENGINE_0.7.0 libera vidro inteiro para porta de 1 ou 2 folhas.")
    if cfg.leaf_system not in (GR_LEAF_SYSTEM_INTERNAL, GR_LEAF_SYSTEM_EXTERNAL):
        raise ValueError("VIDRO INTEIRO v0.7 exige folha de porta Design 60x104.")
    if not cfg.glass_description:
        raise ValueError("VIDRO INTEIRO exige glass_description.")
    v06._glass_and_bead(cfg.glass_description)


def _glass_component_multi(glass, width_mm: float, height_mm: float,
                           leaves: int, order_quantity: int) -> tuple[BomComponent, GlassPanel]:
    if width_mm <= 0 or height_mm <= 0:
        raise ValueError(f"Vidro GR tecnicamente impossível: {width_mm:g}x{height_mm:g} mm.")
    area = width_mm / 1000.0 * height_mm / 1000.0
    total_cost = area * leaves * glass.unit_price
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
        quantity_per_unit=float(leaves),
        quantity_order=float(leaves * order_quantity),
        unit_price=glass.unit_price,
        cost_per_unit_product=round(total_cost, 6),
        source="GR!B68:I68 / GR!G68=G13/2 / RESOLVED_EXCEL",
    )
    panel = GlassPanel(
        source="GR!D68:E68/G68",
        position="R1C1",
        width_mm=round(width_mm, 6),
        height_mm=round(height_mm, 6),
        quantity=float(leaves),
        material_code=glass.code,
        material_description=glass.description,
        area_m2=round(area, 6),
        unit_cost=glass.unit_price,
        total_cost=round(total_cost, 6),
    )
    return component, panel


def _calculate_glass(cfg: GrConfiguration) -> CalculationResult:
    leaves = cfg.leaf_count
    base = legacy.calculate_gr(_legacy_config(cfg))
    bead_width = base.geometry["panel_bead_width_mm"]
    bead_height = base.geometry["panel_bead_height_mm"]
    glass, bead_code = v06._glass_and_bead(cfg.glass_description or "")

    bom = [
        item for item in base.unit_bom
        if item.role not in {"PANEL_BEAD_WIDTH", "PANEL_BEAD_HEIGHT", "PANEL_FILL"}
    ]
    bead_piece_qty = 2 * leaves
    bom.extend([
        v06._linear_component(
            bead_code, "GLASS_BEAD_WIDTH", bead_width, bead_piece_qty,
            cfg.quantity, "GR!B13:E13/G13 / R2=\"\"",
        ),
        v06._linear_component(
            bead_code, "GLASS_BEAD_HEIGHT", bead_height, bead_piece_qty,
            cfg.quantity, "GR!B14:E14/G14 / R2=\"\"",
        ),
    ])
    glass_component, glass_panel = _glass_component_multi(
        glass, bead_width - 8.0, bead_height - 8.0, leaves, cfg.quantity
    )
    bom.append(glass_component)
    bom.extend(v06._physical_seals(
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
    geometry["glass_panel_count"] = float(leaves)

    model = base.model_description.replace(" COM PAINEL HORIZONTAL", "")
    result = v06._finalize(
        base,
        bom,
        model_description=model,
        geometry=geometry,
        glass_panels=[glass_panel],
    )
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


def _promote_panel_result(result: CalculationResult) -> CalculationResult:
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


def calculate_gr(cfg: GrConfiguration) -> CalculationResult:
    """GR v0.7: v0.6 física + portas de 2 folhas com vidro inteiro."""
    _validate(cfg)
    if cfg.panel_mode == GR_GLASS_MODE:
        return _calculate_glass(cfg)
    return _promote_panel_result(v06.calculate_gr(cfg))
