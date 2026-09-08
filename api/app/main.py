from __future__ import annotations

from dataclasses import asdict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .engine_bridge import (
    ApplicationType,
    CustomDimension,
    FixedPanelConfiguration,
    GridAxis,
    LeafGrid,
    LeafSystem,
    SlidingConfiguration,
    StructuralReinforcement,
    build_order_purchase_plan,
    calculate_sliding,
    GLASSES,
    CLOSURE_OPTIONS,
    CREMONA_OPTIONS,
    ROLLER_OPTIONS,
    FINISH_OPTIONS,
    PARAMETERS,
)
from .schemas import CRItemRequest, PurchasePlanRequest

app = FastAPI(
    title="Software Esquadrias API",
    version="0.1.3",
    description="API inicial da Plataforma de Gestão e Engenharia para Esquadrias.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        leaf_grid=LeafGrid(
            horizontal_transoms=item.leaf_grid.horizontal_transoms,
            vertical_transoms=item.leaf_grid.vertical_transoms,
            custom_dimensions=tuple(
                CustomDimension(
                    axis=GridAxis(dimension.axis),
                    index=dimension.index,
                    clear_span_mm=dimension.clear_span_mm,
                )
                for dimension in item.leaf_grid.custom_dimensions
            ),
        ),
        bottom_fixed_panel=(
            FixedPanelConfiguration(**item.bottom_fixed_panel.model_dump())
            if item.bottom_fixed_panel is not None else None
        ),
        top_fixed_panel=(
            FixedPanelConfiguration(**item.top_fixed_panel.model_dump())
            if item.top_fixed_panel is not None else None
        ),
        structural_reinforcement=(
            StructuralReinforcement(item.structural_reinforcement.material_code)
            if item.structural_reinforcement is not None else None
        ),
    )


def _serialize_result(cfg: SlidingConfiguration, result):
    return {
        "engine_version": result.calculation_version,
        "model_description": result.model_description,
        "quantity": cfg.quantity,
        "geometry": result.geometry,
        "leaf_openings": [asdict(opening) for opening in result.leaf_openings],
        "transoms": [asdict(transom) for transom in result.transoms],
        "fixed_panels": [asdict(panel) for panel in result.fixed_panels],
        "glass_panels": [asdict(panel) for panel in result.glass_panels],
        "bom": [asdict(component) for component in result.unit_bom],
        "cost_by_group": result.cost_breakdown,
        "unit_technical_cost": result.unit_cost,
        "order_technical_cost": result.unit_cost * cfg.quantity,
        "warnings": [asdict(warning) for warning in result.warnings],
    }


@app.get("/")
def root():
    return {
        "name": "Software Esquadrias API",
        "status": "online",
        "api_version": "0.1.3",
        "documentation": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "api_version": "0.1.3",
        "engine": "CR_ENGINE_0.4.0",
    }


@app.get("/api/v1/engine/cr/options")
def cr_options():
    glasses = sorted(
        [
            {
                "code": glass.code,
                "description": glass.description,
                "price": glass.unit_price,
                "thickness_mm": glass.thickness_mm,
            }
            for glass in GLASSES.values()
        ],
        key=lambda row: (row["thickness_mm"] or 999, row["description"]),
    )
    return {
        "leaf_systems": [
            {"value": "PRIME_WINDOW_42x66", "label": "Prime Janela 42x66"},
            {"value": "PRIME_DOOR_42x88", "label": "Prime Porta 42x88"},
            {"value": "DESIGN_DOOR_60x111", "label": "Design 60x111"},
        ],
        "applications": ["JANELA", "PORTA"],
        "leaf_counts": [2, 3, 4, 6],
        "glasses": glasses,
        "closures": list(CLOSURE_OPTIONS),
        "cremonas": list(CREMONA_OPTIONS),
        "rollers": list(ROLLER_OPTIONS),
        "finishes": list(FINISH_OPTIONS.keys()),
        "screen": {"supported": True},
        "leaf_grid": {
            "supported": True,
            "transom_profiles": {"PRIME": "PR4263", "DESIGN": "DE6072"},
            "custom_dimensions": "clear opening spans indexed from zero",
        },
        "fixed_panels": {
            "positions": ["BOTTOM", "TOP"],
            "frame_profile": "DE6058",
            "transom_profile": "DE6072",
        },
        "structural_reinforcement": {
            "materials": ["ALUM10238", "ALUM15338"],
            "panel_clearance_mm": PARAMETERS[
                "structural_reinforcement_panel_clearance_mm"
            ],
        },
        "shutter": {
            "supported": "partial",
            "box_height_mm": PARAMETERS["shutter_box_height_mm"],
            "geometry_effect": "Quando ativa, a caixa padrão é descontada da altura útil do marco.",
            "pending": "O kit completo/material da persiana ainda será migrado do Excel.",
        },
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

        plan = build_order_purchase_plan(order_items, kerf_mm=payload.kerf_mm)
        return {
            "items": serialized_items,
            "purchase_plan": {
                "technical_total": plan.technical_total,
                "bar_stock_consumption_cost": plan.bar_stock_consumption_cost,
                "bar_stock_purchase_cost": plan.bar_stock_purchase_cost,
                "exact_nonbar_cost": plan.exact_nonbar_cost,
                "procurement_total_estimate": plan.procurement_total_estimate,
                "purchase_increment_vs_consumption": plan.purchase_increment_vs_consumption,
                "kerf_mm": plan.kerf_mm,
                "lines": [asdict(line) for line in plan.lines],
                "warnings": [asdict(warning) for warning in plan.warnings],
            },
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
