from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Sequence

from .catalog import MATERIALS, BAR_STOCK_CODES, DEFAULT_BAR_LENGTH_MM
from .models import (
    SlidingConfiguration, CalculationResult, CutPiece, BarAllocation,
    PurchaseLine, OrderPurchasePlan, EngineeringWarning
)

_EPS = 1e-7

def _explode_pieces(
    order_items: Sequence[tuple[SlidingConfiguration, CalculationResult]],
) -> dict[str, list[CutPiece]]:
    grouped: dict[str, list[CutPiece]] = defaultdict(list)

    for item_index, (cfg, result) in enumerate(order_items, start=1):
        for comp in result.unit_bom:
            if (
                comp.unit != "m"
                or comp.material_code not in BAR_STOCK_CODES
                or comp.length_mm is None
                or comp.length_mm <= 0
                or comp.quantity_order <= 0
            ):
                continue

            qty_float = float(comp.quantity_order)
            qty = int(round(qty_float))
            if abs(qty_float - qty) > 1e-6:
                raise ValueError(
                    f"Quantidade não inteira para material em barra "
                    f"{comp.material_code}: {qty_float}"
                )

            for _ in range(qty):
                grouped[comp.material_code].append(
                    CutPiece(
                        material_code=comp.material_code,
                        description=comp.description,
                        length_mm=float(comp.length_mm),
                        source_item=item_index,
                        source_role=comp.role,
                    )
                )

    return grouped

def _first_fit_decreasing(
    pieces: Iterable[CutPiece],
    stock_length_mm: float,
) -> list[BarAllocation]:
    """Replica a lógica observada no legado: ordenar cortes do maior para o
    menor e encaixar cada corte na primeira barra com espaço disponível.

    Esse método reproduziu 18/19 quantidades do PED_P no teste real enviado.
    A única divergência encontrada no Excel é DE5013, onde o legado registra
    fisicamente 1 barra para 4 cortes de 1902 mm; são necessárias 2.
    """
    sorted_pieces = sorted(pieces, key=lambda p: p.length_mm, reverse=True)
    bars: list[BarAllocation] = []

    for piece in sorted_pieces:
        if piece.length_mm > stock_length_mm + _EPS:
            raise ValueError(
                f"Corte {piece.material_code} de {piece.length_mm:.1f} mm "
                f"é maior que a barra de {stock_length_mm:.1f} mm."
            )

        placed = False
        for bar in bars:
            if piece.length_mm <= bar.leftover_mm + _EPS:
                bar.pieces.append(piece)
                placed = True
                break

        if not placed:
            bars.append(
                BarAllocation(
                    bar_number=len(bars) + 1,
                    stock_length_mm=stock_length_mm,
                    pieces=[piece],
                )
            )

    return bars

def build_order_purchase_plan(
    order_items: Sequence[tuple[SlidingConfiguration, CalculationResult]],
    stock_length_mm: float = DEFAULT_BAR_LENGTH_MM,
) -> OrderPurchasePlan:
    if not order_items:
        return OrderPurchasePlan(
            lines=[],
            technical_total=0.0,
            bar_stock_consumption_cost=0.0,
            bar_stock_purchase_cost=0.0,
            exact_nonbar_cost=0.0,
            procurement_total_estimate=0.0,
            purchase_increment_vs_consumption=0.0,
            warnings=[],
        )

    grouped = _explode_pieces(order_items)
    lines: list[PurchaseLine] = []
    warnings: list[EngineeringWarning] = []

    for code, pieces in sorted(grouped.items(), key=lambda kv: MATERIALS[kv[0]].description):
        material = MATERIALS[code]
        bars = _first_fit_decreasing(pieces, stock_length_mm)
        consumed = sum(p.length_mm for p in pieces)
        purchased = len(bars) * stock_length_mm
        waste = purchased - consumed
        utilization = (consumed / purchased * 100.0) if purchased else 0.0
        consumption_cost = (consumed / 1000.0) * material.unit_price
        purchase_cost = (purchased / 1000.0) * material.unit_price

        lines.append(
            PurchaseLine(
                material_code=code,
                description=material.description,
                unit_price_per_m=material.unit_price,
                stock_length_mm=stock_length_mm,
                pieces_count=len(pieces),
                consumed_length_mm=round(consumed, 6),
                bars_required=len(bars),
                purchased_length_mm=round(purchased, 6),
                waste_length_mm=round(waste, 6),
                utilization_pct=round(utilization, 6),
                consumption_cost=round(consumption_cost, 6),
                purchase_cost=round(purchase_cost, 6),
                bars=bars,
            )
        )

    technical_total = 0.0
    bar_consumption = 0.0
    exact_nonbar = 0.0

    for cfg, result in order_items:
        technical_total += result.unit_cost * cfg.quantity
        for comp in result.unit_bom:
            order_cost = comp.cost_per_unit_product * cfg.quantity
            if comp.unit == "m" and comp.material_code in BAR_STOCK_CODES:
                bar_consumption += order_cost
            else:
                exact_nonbar += order_cost

    bar_purchase = sum(line.purchase_cost for line in lines)
    procurement_total = bar_purchase + exact_nonbar

    # Inconsistência observada no arquivo real enviado.
    de5013 = next((x for x in lines if x.material_code == "DE5013"), None)
    if de5013 and de5013.pieces_count == 4 and de5013.bars_required == 2:
        warnings.append(
            EngineeringWarning(
                "LEGACY-PEDP-DE5013",
                "No Excel de referência, PED_P registra 1 barra de DE5013 para "
                "4 cortes de 1902 mm. O plano correto exige 2 barras (7608 mm > 5900 mm)."
            )
        )

    return OrderPurchasePlan(
        lines=lines,
        technical_total=round(technical_total, 6),
        bar_stock_consumption_cost=round(bar_consumption, 6),
        bar_stock_purchase_cost=round(bar_purchase, 6),
        exact_nonbar_cost=round(exact_nonbar, 6),
        procurement_total_estimate=round(procurement_total, 6),
        purchase_increment_vs_consumption=round(procurement_total - technical_total, 6),
        warnings=warnings,
    )
