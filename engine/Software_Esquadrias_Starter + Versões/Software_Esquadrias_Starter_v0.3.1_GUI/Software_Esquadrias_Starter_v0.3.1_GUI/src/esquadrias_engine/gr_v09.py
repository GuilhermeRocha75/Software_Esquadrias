from __future__ import annotations

from dataclasses import replace
import math

from . import gr as legacy
from . import gr_v06 as v06
from . import gr_v08 as v08
from .models import BomComponent, CalculationResult, EngineeringWarning


GR_ENGINE_VERSION = "GR_ENGINE_0.9.0"
GrConfiguration = v08.GrConfiguration

GR_GLASS_MODE = v08.GR_GLASS_MODE
GR_LEAF_SYSTEM_WINDOW_EXTERNAL = v08.GR_LEAF_SYSTEM_WINDOW_EXTERNAL
GR_APPLICATION_WINDOW = v08.GR_APPLICATION_WINDOW
GR_CLOSURE_WINDOW_CREMONA = v08.GR_CLOSURE_WINDOW_CREMONA
GR_HINGE_90 = v08.GR_HINGE
GR_HINGE_OB = "DOBRADIÇA SISTEMA OB"

GR_OB_CREMONAS = (
    "CREMONA OSCILO/GIRO COMP. 400mm E:15mm",
    "CREMONA OSCILO/GIRO COMP. 900mm E:15mm",
    "CREMONA OSCILO/GIRO COMP. 1100mm E:15mm",
    "CREMONA OSCILO/GIRO COMP. 1400mm E:15mm",
    "CREMONA OSCILO/GIRO COMP. 1900mm E:15mm",
)

_OB_HINGE_COMPONENTS = (
    ("DOB6", "FALSO COMPASSO", 18.00, "OB_FALSE_COMPASS", "GR!B105/G105 + LISTAFERRA!A61:C61"),
    ("DOB7", "CORPO DA DOBRADIÇA", 3.14, "OB_HINGE_BODY", "GR!B106/G106 + LISTAFERRA!A62:C62"),
    ("DOB8", "CORPO E PINO DOBRADIÇA SUPERIOR", 10.00, "OB_UPPER_HINGE_BODY_PIN", "GR!B107/G107 + LISTAFERRA!A63:C63"),
    ("DOB9", "DOBRADIÇA INFERIOR", 10.00, "OB_LOWER_HINGE", "GR!B108/G108 + LISTAFERRA!A64:C64"),
    ("DOB10", "SUPORTE DA DOBRADIÇA INFERIOR", 30.00, "OB_LOWER_HINGE_SUPPORT", "GR!B109/G109 + LISTAFERRA!A65:C65"),
    ("DOB11", "CONJUNTO CAPAS DOBRADIÇA OSCILO", 1.45, "OB_HINGE_COVERS", "GR!B110/G110 + LISTAFERRA!A66:C66"),
)

_OB_CREMONA_MATERIALS = {
    "CREMONA OSCILO/GIRO COMP. 400mm E:15mm": ("CRE21", 15.00),
    "CREMONA OSCILO/GIRO COMP. 900mm E:15mm": ("CRE22", 17.00),
    "CREMONA OSCILO/GIRO COMP. 1100mm E:15mm": ("CRE23", 18.00),
    # O XLSM usa o mesmo código CRE24 para 1400 e 1900 mm, com preços distintos.
    "CREMONA OSCILO/GIRO COMP. 1400mm E:15mm": ("CRE24", 20.68),
    "CREMONA OSCILO/GIRO COMP. 1900mm E:15mm": ("CRE24", 25.52),
}


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


def _is_ob_window_glass(cfg: GrConfiguration) -> bool:
    return (
        cfg.hinge_description == GR_HINGE_OB
        and cfg.panel_mode == GR_GLASS_MODE
        and cfg.leaf_system == GR_LEAF_SYSTEM_WINDOW_EXTERNAL
    )


def _normalized_90mm_cfg(cfg: GrConfiguration) -> GrConfiguration:
    # Reusa somente a geometria/BOM não-OB já homologados pela v0.8.
    # A ferragem de 90 mm, a cremona CRE12 e seus parafusos são removidos
    # integralmente antes de aplicar o conjunto OB provado em GR!105:110.
    return replace(
        cfg,
        hinge_description=GR_HINGE_90,
        cremona_description=legacy.GR_CREMONA_WINDOW_800,
    )


def _validate_ob_window_glass(cfg: GrConfiguration) -> None:
    v08._validate_window_glass(_normalized_90mm_cfg(cfg))
    if cfg.application != GR_APPLICATION_WINDOW:
        raise ValueError("Sistema OB GR exige aplicação JANELA.")
    if cfg.leaf_count != 1:
        raise ValueError("GR_ENGINE_0.9.0 libera Sistema OB somente em janela de 1 folha.")
    if cfg.closure_mode != GR_CLOSURE_WINDOW_CREMONA:
        raise ValueError("Sistema OB GR exige MAÇANETA COM CREMONA SEM CHAVE.")
    if cfg.cremona_description not in GR_OB_CREMONAS:
        raise ValueError(
            "Sistema OB exige seleção explícita de uma CREMONA OSCILO/GIRO "
            "(400/900/1100/1400/1900 mm, E:15mm)."
        )
    if not cfg.glass_description:
        raise ValueError("Sistema OB v0.9 exige VIDRO INTEIRO com glass_description.")
    v06._glass_and_bead(cfg.glass_description)


def _unit_component(code: str, description: str, price: float, role: str,
                    quantity: float, order_quantity: int, source: str) -> BomComponent:
    if not math.isfinite(quantity) or quantity <= 0:
        raise ValueError(f"Quantidade inválida para {role}: {quantity:g}.")
    return BomComponent(
        category="FERRAGENS",
        role=role,
        material_code=code,
        description=description,
        unit="un",
        length_mm=None,
        width_mm=None,
        height_mm=None,
        area_m2=None,
        quantity_per_unit=float(quantity),
        quantity_order=float(quantity * order_quantity),
        unit_price=price,
        cost_per_unit_product=round(quantity * price, 6),
        source=source,
    )


def _finalize_ob(base: CalculationResult, bom: list[BomComponent]) -> CalculationResult:
    breakdown = {
        group: round(sum(item.cost_per_unit_product for item in bom if item.category == group), 6)
        for group in v06._GROUPS
    }
    total = round(sum(item.cost_per_unit_product for item in bom), 6)
    breakdown["TOTAL"] = total
    warnings = list(base.warnings)
    warnings.append(EngineeringWarning(
        "GR-OB-CREMONA-EXPLICIT",
        "Sistema OB usa GR!Q2 como seleção explícita da cremona; a v0.9 não infere comprimento automaticamente.",
    ))
    return CalculationResult(
        model_description=base.model_description,
        geometry=dict(base.geometry),
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


def _calculate_ob_window_glass(cfg: GrConfiguration) -> CalculationResult:
    base = v08.calculate_gr(_normalized_90mm_cfg(cfg))

    # Substitui integralmente o conjunto 90 mm + cremona padrão + parafusos
    # pelo conjunto OB do XLSM. MAC1 e 2x CON1 permanecem, conforme GR!111/114.
    bom = [
        item
        for item in base.unit_bom
        if item.role not in {"HINGE_90MM", "CREMONA_800_E15", "HARDWARE_SCREWS"}
    ]

    for code, description, price, role, source in _OB_HINGE_COMPONENTS:
        bom.append(_unit_component(
            code, description, price, role, 1.0, cfg.quantity, source
        ))

    cremona_description = cfg.cremona_description or ""
    cremona_code, cremona_price = _OB_CREMONA_MATERIALS[cremona_description]
    bom.append(_unit_component(
        cremona_code,
        cremona_description,
        cremona_price,
        "OB_CREMONA",
        1.0,
        cfg.quantity,
        "GR!B112=Q2/G112 + LISTAFERRA!A67:C71",
    ))

    # GR!G119 = (G105*8) + (G111+G112+G114)*2.
    # No OB: G105=1, G111=1, G112=1, G114=2 => 16 parafusos.
    bom.append(_unit_component(
        "PAR1",
        "PARAFUSOS DE FERRAGEM",
        0.15,
        "HARDWARE_SCREWS",
        16.0,
        cfg.quantity,
        "GR!G119 / U3=1 => (1*8)+(1+1+2)*2 = 16",
    ))

    return _finalize_ob(base, bom)


def calculate_gr(cfg: GrConfiguration) -> CalculationResult:
    """GR v0.9: v0.8 + janela 60x78 com vidro e Sistema OB explícito."""
    if _is_ob_window_glass(cfg):
        _validate_ob_window_glass(cfg)
        return _calculate_ob_window_glass(cfg)
    return _promote(v08.calculate_gr(cfg))
