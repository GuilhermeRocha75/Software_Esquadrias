from __future__ import annotations

from dataclasses import asdict
from fastapi import FastAPI, HTTPException

from .engine_bridge import (
    ApplicationType,
    LeafSystem,
    SlidingConfiguration,
    build_order_purchase_plan,
    calculate_sliding,
)
from .schemas import CRItemRequest, PurchasePlanRequest

app = FastAPI(
    title="Software Esquadrias API",
    version="0.1.0",
    description="API inicial da Plataforma de Gestão e Engenharia para Esquadrias.",
)


def _to_config(item: CRItemRequest) -> SlidingConfiguration:
    return SlidingConfiguration(
        width_mm=item.width_mm,
        height_mm=item.height_mm,
        quantity=item.quantity,
        leaf_count=item.leaf_count,
        leaf_system=LeafSystem(item.leaf_system),
        application=ApplicationType(item.application),
        glass_description=item.glass_description,
        closure_mode=item.closure_mode,
        cremona_base=item.cremona_base,
        roller_description=item.roller_description,
        internal_finish=item.internal_finish,
        external_finish=item.external_finish,
        screen_enabled=item.screen_enabled,
        shutter_enabled=item.shutter_enabled,
    )


def _serialize_result(cfg: SlidingConfiguration, result):
    return {
        "engine_version": result.calculation_version,
        "model_description": result.model_description,
        "quantity": cfg.quantity,
        "geometry": result.geometry,
        "bom": [asdict(component) for component in result.unit_bom],
        "cost_by_group": result.cost_breakdown,
        "unit_technical_cost": result.unit_cost,
        "order_technical_cost": result.unit_cost * cfg.quantity,
        "warnings": [asdict(warning) for warning in result.warnings],
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "api_version": "0.1.0",
        "engine": "CR_ENGINE_0.3.x",
    }


@app.post("/api/v1/engine/cr/calculate")
def calculate_cr(payload: CRItemRequest):
    try:
        cfg = _to_config(payload)
        result = calculate_sliding(cfg)
        return _serialize_result(cfg, result)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/purchase-plans/calculate")
def calculate_purchase_plan(payload: PurchasePlanRequest):
    try:
        order_items = []
        serialized_items = []
        for item in payload.items:
            cfg = _to_config(item)
            result = calculate_sliding(cfg)
            order_items.append((cfg, result))
            serialized_items.append(_serialize_result(cfg, result))

        plan = build_order_purchase_plan(order_items)
        return {
            "items": serialized_items,
            "purchase_plan": {
                "technical_total": plan.technical_total,
                "bar_stock_consumption_cost": plan.bar_stock_consumption_cost,
                "bar_stock_purchase_cost": plan.bar_stock_purchase_cost,
                "exact_nonbar_cost": plan.exact_nonbar_cost,
                "procurement_total_estimate": plan.procurement_total_estimate,
                "purchase_increment_vs_consumption": plan.purchase_increment_vs_consumption,
                "lines": [asdict(line) for line in plan.lines],
                "warnings": [asdict(warning) for warning in plan.warnings],
            },
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
