from __future__ import annotations

from dataclasses import fields
import math

from . import gr_v13 as v13
from .catalog import MATERIALS
from .models import BomComponent, CalculationResult, EngineeringWarning


GR_ENGINE_VERSION = "GR_ENGINE_0.14.0"
GrConfiguration = v13.GrConfiguration


def _v13_config(cfg: GrConfiguration, **overrides) -> v13.GrConfiguration:
    data = {field.name: getattr(cfg, field.name) for field in fields(v13.GrConfiguration)}
    data.update(overrides)
    return v13.GrConfiguration(**data)


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


def _screen_component(width_mm: float, height_mm: float, order_quantity: int) -> BomComponent:
    if (
        not math.isfinite(width_mm)
        or not math.isfinite(height_mm)
        or width_mm <= 0
        or height_mm <= 0
    ):
        raise ValueError(
            f"Dimensões inválidas para tela GR: {width_mm:g}x{height_mm:g} mm."
        )

    # GR!73 pretende usar a tabela LISTADIV!C5:C7 (110/110/110), mas
    # referencia D4/E5, células vazias. MX!64 usa o mesmo TL3 e a mesma tabela
    # com a referência correta ao marco: largura/1000 e altura/1000.
    price = width_mm / 1000.0 * 110.0 + height_mm / 1000.0 * 110.0 + 110.0
    material = MATERIALS["TL3"]
    return BomComponent(
        category="TELA",
        role="RETRACTABLE_SCREEN_ASSEMBLY",
        material_code=material.code,
        description=material.description,
        unit="un",
        length_mm=None,
        width_mm=round(width_mm, 6),
        height_mm=round(height_mm, 6),
        area_m2=None,
        quantity_per_unit=1.0,
        quantity_order=float(order_quantity),
        unit_price=round(price, 6),
        cost_per_unit_product=round(price, 6),
        source=(
            "GR!D73:L73 + LEGACY_GR_SCREEN_REFERENCE_CORRECTED "
            "+ MX!D64:L64 / LISTADIV!C5:C7"
        ),
    )


def _calculate_with_screen(cfg: GrConfiguration) -> CalculationResult:
    base = v13.calculate_gr(_v13_config(cfg, screen_enabled=False))

    width = float(base.geometry["frame_width_final_mm"])
    height = float(base.geometry["frame_height_final_mm"])
    screen = _screen_component(width, height, cfg.quantity)
    bom = [*base.unit_bom, screen]

    breakdown = dict(base.cost_breakdown)
    breakdown["TELA"] = round(
        sum(item.cost_per_unit_product for item in bom if item.category == "TELA"),
        6,
    )
    total = round(sum(item.cost_per_unit_product for item in bom), 6)
    breakdown["TOTAL"] = total

    geometry = dict(base.geometry)
    geometry.update({
        "screen_width_mm": round(width, 6),
        "screen_height_mm": round(height, 6),
        "screen_panel_count": 1.0,
    })

    warnings = list(base.warnings)
    warnings.append(EngineeringWarning(
        "LEGACY-GR-SCREEN-REFERENCE-CORRECTED",
        "GR!D73/E73 referencia D4/D5 vazias. A v0.14 recupera a mesma fórmula TL3 homologada em MX, usando largura e altura reais do marco GR.",
    ))

    return CalculationResult(
        model_description=base.model_description + " + TELA MOSQUITEIRA",
        geometry=geometry,
        unit_bom=bom,
        cost_breakdown=breakdown,
        unit_cost=total,
        leaf_openings=list(base.leaf_openings),
        transoms=list(base.transoms),
        fixed_panels=list(base.fixed_panels),
        glass_panels=list(base.glass_panels),
        warnings=warnings,
        calculation_version=GR_ENGINE_VERSION,
    )


def calculate_gr(cfg: GrConfiguration) -> CalculationResult:
    """GR v0.14: v0.13 + tela mosquiteira recolhível TL3."""
    if cfg.screen_enabled:
        return _calculate_with_screen(cfg)
    return _promote(v13.calculate_gr(cfg))
