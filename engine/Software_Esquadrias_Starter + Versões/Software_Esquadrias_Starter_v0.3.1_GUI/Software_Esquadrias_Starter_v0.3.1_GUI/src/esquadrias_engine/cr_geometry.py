from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

from .models import CustomDimension, GridAxis, GridOpening


_EPS = 1e-7


def validate_count(value: int, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} deve ser inteiro maior ou igual a zero.")


def partition_axis(
    inner_span_mm: float,
    transom_count: int,
    transom_face_mm: float,
    custom_dimensions: Iterable[CustomDimension],
    axis: GridAxis,
    label: str,
) -> tuple[float, ...]:
    """Return the clear openings on one axis of a rectangular grid.

    Custom dimensions are clear opening sizes. Any unspecified openings share
    the remaining span. This is intentionally independent from the legacy
    workbook's positional helper cells and their known negative-dimension bug.
    """

    validate_count(transom_count, f"Quantidade de travessas ({label})")
    if not math.isfinite(float(inner_span_mm)) or inner_span_mm <= 0:
        raise ValueError(f"Vão interno de {label} deve ser finito e positivo.")
    if not math.isfinite(float(transom_face_mm)) or transom_face_mm <= 0:
        raise ValueError(f"Face da travessa de {label} deve ser finita e positiva.")

    opening_count = transom_count + 1
    available = float(inner_span_mm) - transom_count * float(transom_face_mm)
    if available <= 0:
        raise ValueError(
            f"Travessas excedem o vão disponível de {label}: {available:.3f} mm."
        )

    specified: dict[int, float] = {}
    for dimension in custom_dimensions:
        dimension_axis = GridAxis(dimension.axis)
        if dimension_axis != axis:
            continue
        if isinstance(dimension.index, bool) or not isinstance(dimension.index, int):
            raise ValueError("Índice de cota manual deve ser inteiro.")
        if not 0 <= dimension.index < opening_count:
            raise ValueError(
                f"Índice {dimension.index} fora da grade de {label} "
                f"({opening_count} vãos)."
            )
        if dimension.index in specified:
            raise ValueError(
                f"Cota manual duplicada para {label}, vão {dimension.index}."
            )
        value = float(dimension.clear_span_mm)
        if not math.isfinite(value) or value <= 0:
            raise ValueError("Cota manual deve ser finita e positiva.")
        specified[dimension.index] = value

    unspecified_count = opening_count - len(specified)
    remaining = available - sum(specified.values())
    if unspecified_count == 0:
        if abs(remaining) > _EPS:
            raise ValueError(
                f"Cotas manuais de {label} devem totalizar {available:.3f} mm."
            )
        default = 0.0
    else:
        default = remaining / unspecified_count
        if default <= 0:
            raise ValueError(
                f"Cotas manuais não deixam vão positivo em {label}."
            )

    spans = tuple(specified.get(index, default) for index in range(opening_count))
    if any(not math.isfinite(value) or value <= 0 for value in spans):
        raise ValueError(f"A grade gerou dimensão inválida em {label}.")
    return spans


def make_openings(
    source: str,
    column_widths_mm: Sequence[float],
    row_heights_mm: Sequence[float],
    quantity: float,
) -> tuple[GridOpening, ...]:
    if not math.isfinite(float(quantity)) or quantity <= 0:
        raise ValueError("Quantidade de vãos deve ser finita e positiva.")
    return tuple(
        GridOpening(
            source=source,
            row_index=row_index,
            column_index=column_index,
            width_mm=round(float(width), 6),
            height_mm=round(float(height), 6),
            quantity=float(quantity),
        )
        for row_index, height in enumerate(row_heights_mm)
        for column_index, width in enumerate(column_widths_mm)
    )
