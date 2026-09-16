"""Serialization shared by the frozen golden checks; does not calculate expectations."""
from dataclasses import asdict
import json
from esquadrias_engine import (
    FixedPanelConfiguration, MaximArConfiguration, MaximArLeafSystem,
    MaximArModuleMode, MaximArOrientation, MaximArSealingConfiguration,
    StructuralReinforcement,
)


def configuration_from_json(values):
    values = dict(values)
    for field, enum in (("leaf_system", MaximArLeafSystem),
                        ("module_mode", MaximArModuleMode),
                        ("orientation", MaximArOrientation)):
        values[field] = enum(values[field])
    for field in ("bottom_fixed_panel", "top_fixed_panel"):
        if values.get(field):
            values[field] = FixedPanelConfiguration(**values[field])
    if values.get("structural_reinforcement"):
        values["structural_reinforcement"] = StructuralReinforcement(**values["structural_reinforcement"])
    values["sealing"] = MaximArSealingConfiguration(**values["sealing"])
    return MaximArConfiguration(**values)


def snapshot(result, plan):
    value = {
        "geometry": result.geometry,
        "leaf_openings": [asdict(x) for x in result.leaf_openings],
        "fixed_panels": [asdict(x) for x in result.fixed_panels],
        "glass_panels": [asdict(x) for x in result.glass_panels],
        "transoms": [asdict(x) for x in result.transoms],
        "bom": [list(asdict(x).values()) for x in result.unit_bom],
        "cost_by_group": result.cost_breakdown,
        "unit_cost": result.unit_cost,
        "warnings": [asdict(x) for x in result.warnings],
        "purchase": {
            **{k: v for k, v in asdict(plan).items() if k != "lines"},
            "lines": [{
                **{k: v for k, v in asdict(line).items() if k != "bars"},
                "bars": [{
                    "bar_number": bar.bar_number,
                    "stock_length_mm": bar.stock_length_mm,
                    "kerf_mm": bar.kerf_mm,
                    "leftover_mm": round(bar.leftover_mm, 6),
                    "pieces": [[p.length_mm, p.source_item, p.source_role, p.source_position]
                               for p in bar.pieces],
                } for bar in line.bars],
            } for line in plan.lines],
        },
    }
    # JSON is the frozen contract; normalize tuples and enum string subclasses.
    return json.loads(json.dumps(value, ensure_ascii=False))
