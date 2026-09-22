from __future__ import annotations

from . import gr as legacy
from . import gr_v06 as v06
from . import gr_v07 as v07
from .models import CalculationResult


GR_ENGINE_VERSION = "GR_ENGINE_0.8.0"
GrConfiguration = v07.GrConfiguration

GR_PANEL_MODE = v07.GR_PANEL_MODE
GR_GLASS_MODE = v07.GR_GLASS_MODE
GR_LEAF_SYSTEM_WINDOW_EXTERNAL = v07.GR_LEAF_SYSTEM_WINDOW_EXTERNAL
GR_APPLICATION_WINDOW = v07.GR_APPLICATION_WINDOW
GR_CLOSURE_WINDOW_CREMONA = legacy.GR_CLOSURE_WINDOW_CREMONA
GR_CREMONA_WINDOW_800 = legacy.GR_CREMONA_WINDOW_800
GR_HINGE = legacy.GR_HINGE


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


def _is_window_glass(cfg: GrConfiguration) -> bool:
    return (
        cfg.panel_mode == GR_GLASS_MODE
        and cfg.leaf_system == GR_LEAF_SYSTEM_WINDOW_EXTERNAL
    )


def _validate_window_glass(cfg: GrConfiguration) -> None:
    # Normaliza VIDRO INTEIRO para o recorte estrutural de painel apenas para
    # reaproveitar os gates de geometria/ferragens já homologados da v0.5.
    legacy._validate(v07._legacy_config(cfg))
    if cfg.application != GR_APPLICATION_WINDOW:
        raise ValueError("janela GR Design 60x78 com vidro exige aplicação JANELA.")
    if cfg.leaf_count != 1:
        raise ValueError("GR_ENGINE_0.8.0 libera vidro em janela somente com 1 folha.")
    if cfg.hinge_description != GR_HINGE:
        raise ValueError("GR_ENGINE_0.8.0 libera vidro em janela somente com DOBRADIÇA 90MM.")
    if cfg.closure_mode != GR_CLOSURE_WINDOW_CREMONA:
        raise ValueError("janela GR com vidro v0.8 exige MAÇANETA COM CREMONA SEM CHAVE.")
    if cfg.cremona_description not in (None, GR_CREMONA_WINDOW_800):
        raise ValueError("janela GR com vidro v0.8 suporta somente cremona padrão de 800mm E:15mm.")
    if not cfg.glass_description:
        raise ValueError("VIDRO INTEIRO exige glass_description.")
    v06._glass_and_bead(cfg.glass_description)


def _calculate_window_glass(cfg: GrConfiguration) -> CalculationResult:
    # A geometria de marco/folha/reforço e o conjunto 90mm + cremona 800 já
    # foram homologados no baseline de janela com painel. A Fase 8 troca apenas
    # o preenchimento/baguete e acrescenta o vidro, preservando as 3 vedações
    # físicas confirmadas em 2026-09-22.
    base = legacy.calculate_gr(v07._legacy_config(cfg))
    bead_width = base.geometry["panel_bead_width_mm"]
    bead_height = base.geometry["panel_bead_height_mm"]
    glass, bead_code = v06._glass_and_bead(cfg.glass_description or "")

    bom = [
        item for item in base.unit_bom
        if item.role not in {"PANEL_BEAD_WIDTH", "PANEL_BEAD_HEIGHT", "PANEL_FILL"}
    ]
    bom.extend([
        v06._linear_component(
            bead_code,
            "GLASS_BEAD_WIDTH",
            bead_width,
            2,
            cfg.quantity,
            'GR!B13:E13/G13 + GR!R2="" (VIDRO INTEIRO)',
        ),
        v06._linear_component(
            bead_code,
            "GLASS_BEAD_HEIGHT",
            bead_height,
            2,
            cfg.quantity,
            'GR!B14:E14/G14 + GR!R2="" (VIDRO INTEIRO)',
        ),
    ])
    glass_component, glass_panel = v06._glass_component(
        glass,
        bead_width - 8.0,
        bead_height - 8.0,
        cfg.quantity,
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
    geometry["glass_panel_count"] = 1.0

    result = v06._finalize(
        base,
        bom,
        model_description="JANELA 1 FOLHA DE GIRO",
        geometry=geometry,
        glass_panels=[glass_panel],
    )
    return _promote(result)


def calculate_gr(cfg: GrConfiguration) -> CalculationResult:
    """GR v0.8: v0.7 + janela 60x78 com vidro e dobradiça 90mm."""
    if _is_window_glass(cfg):
        _validate_window_glass(cfg)
        return _calculate_window_glass(cfg)
    return _promote(v07.calculate_gr(cfg))
