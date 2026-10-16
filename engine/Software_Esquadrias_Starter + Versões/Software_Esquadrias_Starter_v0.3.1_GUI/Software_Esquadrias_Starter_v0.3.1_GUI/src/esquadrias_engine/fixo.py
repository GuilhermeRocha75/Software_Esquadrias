"""Migração literal da aba FX. Não depende de Excel em tempo de execução.

AJ2 = travessas verticais, AK2 = horizontais. As horizontais são segmentadas
entre as verticais. Comprimentos de reforço e ausência de parafusos/vedações
seguem o XLSM, sem importar regras de CR/MX/GR.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from .catalog import GLASS_ROWS, MATERIALS, PARAMETERS
from .models import BomComponent, CalculationResult, GlassPanel, GridOpening, Transom, TransomOrientation

FIXO_ENGINE_VERSION = "FX_ENGINE_0.1.0"
FIXO_FINISHES = ("GUARNIÇÃO DE 70MM", "BARRA CHATA DE 30MM")
FIXO_GLASS_OPTIONS = tuple(row for row in GLASS_ROWS if row["thickness_mm"] is not None)


@dataclass(frozen=True)
class FixoConfiguration:
    width_mm: float
    height_mm: float
    quantity: int = 1
    vertical_transoms: int = 0
    horizontal_transoms: int = 0
    glass_description: str = "04mm FLOAT INCOLOR"
    internal_finish: str = "GUARNIÇÃO DE 70MM"
    external_finish: str = "BARRA CHATA DE 30MM"


def _glass(description: str) -> dict:
    # VLOOKUP(FALSE): ignora caixa, mas não corrige espaços/grafias históricos.
    for row in FIXO_GLASS_OPTIONS:
        if description.casefold() == row["description"].casefold():
            return row
    raise ValueError(f"Vidro FX ausente da LISTAVIDROS: {description!r}.")


def _bead_code(thickness: int) -> str:
    # FX!B12 utiliza LEFT(K2,2), inclusive nos limites da seleção.
    for upper, code in ((8, "BA3518"), (12, "BA3218"), (19, "BA2516"),
                        (22, "BA2018"), (26, "BA1816"), (31, "BA1216"),
                        (34, "BA1016"), (35, "BA0716")):
        if thickness < upper:
            return code
    raise ValueError("Espessura de vidro FX fora da fórmula B12 (<35 mm).")


def calculate_fixo(cfg: FixoConfiguration) -> CalculationResult:
    for value, label in ((cfg.width_mm, "Largura"), (cfg.height_mm, "Altura")):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"{label} FX deve ser finita e positiva.")
    for value, minimum, label in ((cfg.quantity, 1, "Quantidade"),
                                  (cfg.vertical_transoms, 0, "Travessas verticais"),
                                  (cfg.horizontal_transoms, 0, "Travessas horizontais")):
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ValueError(f"{label} FX deve ser inteiro >= {minimum}.")
    if cfg.internal_finish not in FIXO_FINISHES or cfg.external_finish not in FIXO_FINISHES:
        raise ValueError("Acabamento FX ausente do catálogo de perfis suportado.")
    if not isinstance(cfg.glass_description, str):
        raise ValueError("Descrição do vidro FX deve ser texto.")
    glass = _glass(cfg.glass_description)
    try:
        thickness = int(cfg.glass_description[:2])
    except ValueError as exc:
        raise ValueError("FX!K4 exige espessura nos dois primeiros caracteres do vidro.") from exc
    bead = _bead_code(thickness)
    width, height = float(cfg.width_mm), float(cfg.height_mm)
    vertical, horizontal = cfg.vertical_transoms, cfg.horizontal_transoms
    columns, rows = vertical + 1, horizontal + 1
    opening_w = (width - 80.0 - vertical * 36.0) / columns
    opening_h = (height - 80.0 - horizontal * 36.0) / rows
    glass_w = opening_w - PARAMETERS["glass_clearance_mm"]
    glass_h = opening_h - PARAMETERS["glass_clearance_mm"]
    # FX!E20/E21 = dimensão externa - 2*58 + 5, inclusive no reforço.
    reinforcement_w = width - 111.0
    reinforcement_h = height - 111.0
    for label, value in (("vão de largura", opening_w), ("vão de altura", opening_h),
                         ("vidro largura", glass_w), ("vidro altura", glass_h),
                         ("reforço largura", reinforcement_w), ("reforço altura", reinforcement_h)):
        if value <= 0:
            raise ValueError(f"Geometria FX inválida: {label} <= 0 mm.")

    bom: list[BomComponent] = []
    def add(code: str, role: str, count: int, length: float | None, row: int, category: str) -> None:
        if count == 0:
            return
        material = MATERIALS[code]
        cost = count * material.unit_price * (length / 1000 if length is not None else 1)
        bom.append(BomComponent(category, role, code, material.description, material.unit,
                                length, None, None, None, float(count), float(count * cfg.quantity),
                                material.unit_price, cost, f"FX!{row}"))

    add("DE6058", "Marco Largura", 2, width + 5, 8, "PERFIS PRINCIPAIS")
    add("DE6058", "Marco Altura", 2, height + 5, 9, "PERFIS PRINCIPAIS")
    add("DE6072", "Trav. Horiz. Largura", horizontal * columns, opening_w, 10, "PERFIS PRINCIPAIS")
    add("DE6072", "Trav. Vert. Altura", vertical, height - 80, 11, "PERFIS PRINCIPAIS")
    add(bead, "Baguete Largura", 2 * columns * rows, opening_w, 12, "BAGUETES")
    add(bead, "Baguete Altura", 2 * rows * columns, opening_h, 13, "BAGUETES")
    finish_codes = {"GUARNIÇÃO DE 70MM": "AC7012", "BARRA CHATA DE 30MM": "AC3004"}
    add(finish_codes[cfg.internal_finish], "Arremate Int. Largura", 2, width + 140, 14, "ACABAMENTOS")
    add(finish_codes[cfg.internal_finish], "Arremate Int. Altura", 2, height + 140, 15, "ACABAMENTOS")
    add(finish_codes[cfg.external_finish], "Arremate Ext. Largura", 2, width + 60, 16, "ACABAMENTOS")
    add(finish_codes[cfg.external_finish], "Arremate Ext. Altura", 2, height + 60, 17, "ACABAMENTOS")
    add("RAG - DE6058", "Ref. Marco Largura", 2, reinforcement_w, 20, "REFORÇOS")
    add("RAG - DE6058", "Ref. Marco Altura", 2, reinforcement_h, 21, "REFORÇOS")
    add("RAG - DE6072", "Ref. Trav. Horiz. Largura", horizontal * columns, opening_w, 22, "REFORÇOS")
    add("RAG - DE6072", "Ref. Trav. Vert. Altura", vertical, height - 80, 23, "REFORÇOS")
    count = columns * rows
    area = glass_w * glass_h / 1_000_000
    glass_cost = area * count * glass["price"]
    bom.append(BomComponent("VIDROS", "Vidros", glass["code"], glass["description"], "m²", None,
                            glass_w, glass_h, area, float(count), float(count * cfg.quantity),
                            glass["price"], glass_cost, "FX!27"))
    add("AC0312", "Calço de vidro", 2 * count, None, 30, "ACESSÓRIOS")
    add("AC0001", "Tapa deságue", 2, None, 31, "ACESSÓRIOS")
    breakdown = {group: sum(item.cost_per_unit_product for item in bom if item.category == group)
                 for group in ("PERFIS PRINCIPAIS", "BAGUETES", "ACABAMENTOS", "REFORÇOS", "VIDROS", "ACESSÓRIOS")}
    total = sum(item.cost_per_unit_product for item in bom)
    breakdown["TOTAL"] = total
    openings = [GridOpening(f"FX:{row}:{col}", row, col, opening_w, opening_h, 1)
                for row in range(rows) for col in range(columns)]
    transoms = []
    if horizontal:
        transoms.append(Transom("FX!10", TransomOrientation.HORIZONTAL, "DE6072", "RAG - DE6072",
                                opening_w, horizontal * columns))
    if vertical:
        transoms.append(Transom("FX!11", TransomOrientation.VERTICAL, "DE6072", "RAG - DE6072",
                                height - 80, vertical))
    return CalculationResult(
        model_description=f"PAINEL FIXO - {vertical}V/{horizontal}H",
        geometry={"width_mm": width, "height_mm": height, "opening_width_mm": opening_w,
                  "opening_height_mm": opening_h, "glass_width_mm": glass_w,
                  "glass_height_mm": glass_h, "glass_quantity": count,
                  "frame_width_cut_mm": width + 5, "frame_height_cut_mm": height + 5},
        unit_bom=bom, cost_breakdown=breakdown, unit_cost=total, leaf_openings=openings, transoms=transoms,
        glass_panels=[GlassPanel("FX!27", "FIXO", glass_w, glass_h, count,
                                glass["code"], glass["description"], area, area * glass["price"], glass_cost)],
        calculation_version=FIXO_ENGINE_VERSION,
    )
