from __future__ import annotations

from dataclasses import dataclass, fields, replace
import math

from . import gr as legacy
from . import gr_v06 as v06
from . import gr_v07 as v07
from . import gr_v09 as v09
from .models import (
    BomComponent,
    CalculationResult,
    EngineeringWarning,
    Transom,
    TransomOrientation,
)


GR_ENGINE_VERSION = "GR_ENGINE_0.10.0"
GR_MIXED_MODE = "SUPERIOR VIDRO/INFERIOR PAINEL"

GR_LEAF_SYSTEM_INTERNAL = v06.GR_LEAF_SYSTEM_INTERNAL
GR_LEAF_SYSTEM_EXTERNAL = v06.GR_LEAF_SYSTEM_EXTERNAL
GR_APPLICATION_DOOR = v06.GR_APPLICATION_DOOR
GR_HINGE_90 = v09.GR_HINGE_90


@dataclass(frozen=True)
class GrConfiguration(v09.GrConfiguration):
    """Contrato GR v0.10.

    mixed_split_from_bottom_mm é a distância medida da extremidade inferior
    da folha pronta para cima até a divisão horizontal DE6072.
    """

    mixed_split_from_bottom_mm: float | None = None


def _v09_config(cfg: GrConfiguration, **overrides) -> v09.GrConfiguration:
    data = {field.name: getattr(cfg, field.name) for field in fields(v09.GrConfiguration)}
    data.update(overrides)
    return v09.GrConfiguration(**data)


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


def _is_mixed(cfg: GrConfiguration) -> bool:
    return cfg.panel_mode == GR_MIXED_MODE


def _base_panel_cfg(cfg: GrConfiguration) -> v09.GrConfiguration:
    return _v09_config(
        cfg,
        panel_mode=v06.GR_PANEL_MODE,
        glass_description=None,
    )


def _validate_mixed(cfg: GrConfiguration) -> None:
    base_cfg = _base_panel_cfg(cfg)
    v09.calculate_gr(base_cfg)

    if cfg.application != GR_APPLICATION_DOOR:
        raise ValueError("SUPERIOR VIDRO/INFERIOR PAINEL v0.10 exige aplicação PORTA.")
    if cfg.leaf_system not in (GR_LEAF_SYSTEM_INTERNAL, GR_LEAF_SYSTEM_EXTERNAL):
        raise ValueError("modo misto v0.10 exige folha de porta Design 60x104.")
    if cfg.leaf_count not in (1, 2):
        raise ValueError("modo misto v0.10 suporta somente porta de 1 ou 2 folhas.")
    if cfg.hinge_description != GR_HINGE_90:
        raise ValueError("modo misto v0.10 está homologado somente com DOBRADIÇA 90MM.")
    if not cfg.glass_description:
        raise ValueError("modo misto exige glass_description para o vidro superior.")
    v06._glass_and_bead(cfg.glass_description)

    split = cfg.mixed_split_from_bottom_mm
    if split is None or not math.isfinite(float(split)) or split <= 0:
        raise ValueError(
            "modo misto exige mixed_split_from_bottom_mm positivo, medido da base da folha pronta para cima."
        )


def _mixed_geometry(cfg: GrConfiguration, base: CalculationResult) -> dict[str, float]:
    split = float(cfg.mixed_split_from_bottom_mm or 0.0)
    leaf_width = base.geometry["leaf_width_final_mm"]
    leaf_height = base.geometry["leaf_height_final_mm"]

    bead_width = leaf_width - 172.0
    upper_glass_bead_height = leaf_height - split - 122.0
    lower_panel_bead_height = split - 122.0
    transom_length = leaf_width - 160.0
    glass_width = bead_width - 8.0
    glass_height = upper_glass_bead_height - 8.0
    panel_strip_qty_per_leaf = lower_panel_bead_height / 140.0

    values = {
        "mixed_split_from_bottom_mm": split,
        "mixed_common_bead_width_mm": bead_width,
        "upper_glass_bead_height_mm": upper_glass_bead_height,
        "lower_panel_bead_height_mm": lower_panel_bead_height,
        "horizontal_transom_length_mm": transom_length,
        "glass_width_mm": glass_width,
        "glass_height_mm": glass_height,
        "panel_fill_strip_length_mm": bead_width,
        "panel_fill_strip_quantity_per_leaf": panel_strip_qty_per_leaf,
    }
    invalid = {
        name: value
        for name, value in values.items()
        if name != "mixed_split_from_bottom_mm" and (value <= 0 or not math.isfinite(value))
    }
    if invalid:
        details = ", ".join(f"{key}={value:g}" for key, value in invalid.items())
        raise ValueError(f"Cota I/divisão tecnicamente impossível para GR v0.10: {details}")

    values["panel_fill_strip_quantity"] = panel_strip_qty_per_leaf * cfg.leaf_count
    values["glass_panel_count"] = float(cfg.leaf_count)
    values["transom_count"] = float(cfg.leaf_count)
    return {key: round(value, 6) for key, value in values.items()}


def _replace_reinforcement_screws(
    bom: list[BomComponent],
    *,
    transom_length_mm: float,
    leaves: int,
    order_quantity: int,
) -> tuple[list[BomComponent], float]:
    original = next(item for item in bom if item.role == "REINFORCEMENT_SCREWS")
    per_transom = max(1, math.ceil(transom_length_mm / 400.0))
    added = float(per_transom * leaves)
    corrected_qty = original.quantity_per_unit + added
    corrected = replace(
        original,
        quantity_per_unit=corrected_qty,
        quantity_order=corrected_qty * order_quantity,
        cost_per_unit_product=round(corrected_qty * original.unit_price, 6),
        source=(
            "GR!G118 + LEGACY_BUG_CONFIRMED_2026-09-24 + "
            "RESOLVED_PHYSICAL_2026-09-24 / RAG-DE6072: "
            "ceil(comprimento/400mm) PAR2 por travessa"
        ),
    )
    return [
        corrected if item.role == "REINFORCEMENT_SCREWS" else item
        for item in bom
    ], added


def _calculate_mixed(cfg: GrConfiguration) -> CalculationResult:
    _validate_mixed(cfg)
    base = v09.calculate_gr(_base_panel_cfg(cfg))
    geom = _mixed_geometry(cfg, base)
    leaves = cfg.leaf_count
    bead_width = geom["mixed_common_bead_width_mm"]
    upper_h = geom["upper_glass_bead_height_mm"]
    lower_h = geom["lower_panel_bead_height_mm"]
    transom_length = geom["horizontal_transom_length_mm"]

    glass, glass_bead_code = v06._glass_and_bead(cfg.glass_description or "")

    bom = [
        item for item in base.unit_bom
        if item.role not in {"PANEL_BEAD_WIDTH", "PANEL_BEAD_HEIGHT", "PANEL_FILL"}
        and item.category != "VEDAÇÕES"
    ]

    piece_qty = 2 * leaves
    bom.extend([
        v06._linear_component(
            "DE6072", "MIXED_HORIZONTAL_TRANSOM", transom_length, leaves,
            cfg.quantity, "GR!E12/G12 / AF2=1",
            category="PERFIS PRINCIPAIS",
        ),
        v06._linear_component(
            "RAG - DE6072", "MIXED_HORIZONTAL_TRANSOM_REINFORCEMENT",
            transom_length, leaves, cfg.quantity,
            "GR!E62/G62 / RESOLVED_PHYSICAL_2026-09-24",
            category="REFORÇOS",
        ),
        v06._linear_component(
            glass_bead_code, "UPPER_GLASS_BEAD_WIDTH", bead_width, piece_qty,
            cfg.quantity, "GR!E13/G13 / SUPERIOR VIDRO",
        ),
        v06._linear_component(
            glass_bead_code, "UPPER_GLASS_BEAD_HEIGHT", upper_h, piece_qty,
            cfg.quantity, "GR!E14/G14 / K14 / SUPERIOR VIDRO",
        ),
        v06._linear_component(
            "BA2516", "LOWER_PANEL_BEAD_WIDTH", bead_width, piece_qty,
            cfg.quantity, "GR!E16/G16 / INFERIOR PAINEL",
        ),
        v06._linear_component(
            "BA2516", "LOWER_PANEL_BEAD_HEIGHT", lower_h, piece_qty,
            cfg.quantity, "GR!E18/G18 / INFERIOR PAINEL",
        ),
        v06._linear_component(
            "DE20150", "LOWER_PANEL_FILL", bead_width,
            geom["panel_fill_strip_quantity"], cfg.quantity,
            "GR!E41/G41 + RESOLVED_PHYSICAL panel por folha",
            description=legacy._MATERIALS["DE20150"][0],
            category="PERFIS PRINCIPAIS",
            unit_price=legacy._MATERIALS["DE20150"][1],
        ),
    ])

    glass_component, glass_panel = v07._glass_component_multi(
        glass,
        geom["glass_width_mm"],
        geom["glass_height_mm"],
        leaves,
        cfg.quantity,
    )
    bom.append(glass_component)

    glass_perimeter = 2.0 * (bead_width + upper_h)
    panel_perimeter = 2.0 * (bead_width + lower_h)
    leaf_perimeter = 2.0 * (
        base.geometry["leaf_width_final_mm"] + base.geometry["leaf_height_final_mm"]
    )
    seal_source = "RESOLVED_PHYSICAL_2026-09-22 + MIXED_MODE_2026-09-24"
    bom.extend([
        v06._seal_component(
            "ACB606", "UPPER_GLASS_SEAL", glass_perimeter, leaves,
            cfg.quantity, seal_source + " / vidro superior",
        ),
        v06._seal_component(
            "ACB606", "LOWER_LAMBRI_SEAL", panel_perimeter, leaves,
            cfg.quantity, seal_source + " / painel inferior",
        ),
        v06._seal_component(
            "AC0002", "ROUND_SEAL_LEAF", leaf_perimeter, leaves,
            cfg.quantity, seal_source + " / folha por fora",
        ),
        v06._seal_component(
            "AC0002", "ROUND_SEAL_FRAME", leaf_perimeter, leaves,
            cfg.quantity, seal_source + " / marco por dentro",
        ),
    ])

    bom, added_par2 = _replace_reinforcement_screws(
        bom,
        transom_length_mm=transom_length,
        leaves=leaves,
        order_quantity=cfg.quantity,
    )

    geometry = dict(base.geometry)
    geometry.pop("panel_bead_width_mm", None)
    geometry.pop("panel_bead_height_mm", None)
    geometry.pop("panel_fill_strip_length_mm", None)
    geometry.pop("panel_fill_strip_quantity", None)
    geometry.update(geom)
    geometry["transom_reinforcement_screws_added"] = round(added_par2, 6)

    breakdown = {
        group: round(
            sum(item.cost_per_unit_product for item in bom if item.category == group),
            6,
        )
        for group in v06._GROUPS
    }
    total = round(sum(item.cost_per_unit_product for item in bom), 6)
    breakdown["TOTAL"] = total

    warnings = list(base.warnings)
    warnings.extend([
        EngineeringWarning(
            "GR-MIXED-SPLIT-FROM-BOTTOM",
            "A divisão horizontal é medida da extremidade inferior da folha pronta para cima e é informada livremente no orçamento.",
        ),
        EngineeringWarning(
            "LEGACY-GR-TRANSOM-REINFORCEMENT-SCREWS-CORRECTED",
            "GR!G118 omitia os parafusos do reforço RAG-DE6072; fabricação confirmou aproximadamente 1 PAR2 a cada 400 mm de travessa.",
        ),
    ])

    transom = Transom(
        source="GR!E12/G12 + RESOLVED_PHYSICAL_2026-09-24",
        orientation=TransomOrientation.HORIZONTAL,
        material_code="DE6072",
        reinforcement_material_code="RAG - DE6072",
        length_mm=round(transom_length, 6),
        quantity=float(leaves),
    )

    model = (
        f"PORTA {leaves} {'FOLHA' if leaves == 1 else 'FOLHAS'} DE GIRO "
        "SUPERIOR VIDRO / INFERIOR PAINEL"
    )
    return CalculationResult(
        model_description=model,
        geometry=geometry,
        unit_bom=bom,
        cost_breakdown=breakdown,
        unit_cost=total,
        leaf_openings=list(base.leaf_openings),
        transoms=[transom],
        fixed_panels=list(base.fixed_panels),
        glass_panels=[glass_panel],
        warnings=warnings,
        calculation_version=GR_ENGINE_VERSION,
    )


def calculate_gr(cfg: GrConfiguration) -> CalculationResult:
    """GR v0.10: v0.9 + porta com vidro superior/painel inferior flexível."""
    if _is_mixed(cfg):
        return _calculate_mixed(cfg)

    if cfg.mixed_split_from_bottom_mm is not None:
        raise ValueError(
            "mixed_split_from_bottom_mm só deve ser informado em SUPERIOR VIDRO/INFERIOR PAINEL."
        )
    return _promote(v09.calculate_gr(_v09_config(cfg)))
