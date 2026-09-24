from __future__ import annotations

from dataclasses import asdict
import os
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
    ShutterConfiguration,
    ShutterMode,
    StructuralReinforcement,
    MaximArConfiguration,
    MaximArLeafSystem,
    MaximArOrientation,
    MaximArModuleMode,
    MaximArSealingConfiguration,
    GrConfiguration,
    GR_ENGINE_VERSION,
    build_order_purchase_plan,
    calculate_sliding,
    calculate_maxim_ar,
    calculate_gr,
    GLASSES,
    CLOSURE_OPTIONS,
    CREMONA_OPTIONS,
    ROLLER_OPTIONS,
    FINISH_OPTIONS,
    SHUTTER_MODES,
    SHUTTER_BOX_OPTIONS,
    SHUTTER_SLAT_OPTIONS,
    PARAMETERS,
    MAXIM_AR_ENGINE_VERSION,
    MAXIM_AR_CLOSURE_OPTIONS,
    MAXIM_AR_CREMONA_OPTIONS,
    MAXIM_AR_INTERNAL_FINISH_OPTIONS,
    MAXIM_AR_EXTERNAL_FINISH_OPTIONS,
)
from .schemas import (
    CRItemRequest,
    MaximArItemRequest,
    MaximArPurchasePlanRequest,
    GrItemRequest,
    PurchasePlanRequest,
    UnifiedPurchasePlanRequest,
)

app = FastAPI(
    title="Software Esquadrias API",
    version="0.1.4",
    description="API inicial da Plataforma de Gestão e Engenharia para Esquadrias.",
)


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOWED_ORIGINS")
    if raw is None:
        return ["http://127.0.0.1:5173", "http://localhost:5173"]
    origins = [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]
    if any(origin == "*" or not origin.startswith(("http://", "https://")) for origin in origins):
        raise ValueError("CORS_ALLOWED_ORIGINS deve conter origens HTTP(S) explícitas.")
    return origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
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
        shutter=(
            ShutterConfiguration(
                mode=ShutterMode(item.shutter.mode),
                box_description=item.shutter.box_description,
                slat_description=item.shutter.slat_description,
            )
            if item.shutter is not None else None
        ),
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


def _serialize_result(cfg, result):
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


def _to_maxim_ar_config(item: MaximArItemRequest) -> MaximArConfiguration:
    return MaximArConfiguration(
        width_mm=item.width_mm,
        height_mm=item.height_mm,
        quantity=item.quantity,
        leaf_count=item.leaf_count,
        leaf_system=MaximArLeafSystem(item.leaf_system),
        orientation=MaximArOrientation(item.orientation),
        module_mode=MaximArModuleMode(item.module_mode),
        glass_description=item.glass_description,
        closure_mode=item.closure_mode,
        cremona_description=item.cremona_description,
        internal_finish=item.internal_finish,
        external_finish=item.external_finish,
        screen_enabled=item.screen_enabled,
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
        sealing=MaximArSealingConfiguration(**item.sealing.model_dump()),
    )


def _to_gr_config(item: GrItemRequest) -> GrConfiguration:
    return GrConfiguration(
        width_mm=item.width_mm,
        height_mm=item.height_mm,
        quantity=item.quantity,
        leaf_count=item.leaf_count,
        leaf_system=item.leaf_system,
        application=item.application,
        panel_mode=item.panel_mode,
        glass_description=item.glass_description,
        mixed_split_from_bottom_mm=item.mixed_split_from_bottom_mm,
        module_mode=item.module_mode,
        closure_mode=item.closure_mode,
        cremona_description=item.cremona_description,
        hinge_description=item.hinge_description,
        shutter=(
            ShutterConfiguration(
                mode=ShutterMode(item.shutter.mode),
                box_description=item.shutter.box_description,
                slat_description=item.shutter.slat_description,
            )
            if item.shutter is not None else None
        ),
        internal_finish=item.internal_finish,
        external_finish=item.external_finish,
    )


def _serialize_purchase_plan(plan):
    return {
        "technical_total": plan.technical_total,
        "bar_stock_consumption_cost": plan.bar_stock_consumption_cost,
        "bar_stock_purchase_cost": plan.bar_stock_purchase_cost,
        "exact_nonbar_cost": plan.exact_nonbar_cost,
        "procurement_total_estimate": plan.procurement_total_estimate,
        "purchase_increment_vs_consumption": plan.purchase_increment_vs_consumption,
        "kerf_mm": plan.kerf_mm,
        "lines": [asdict(line) for line in plan.lines],
        "warnings": [asdict(warning) for warning in plan.warnings],
    }


@app.get("/")
def root():
    return {
        "name": "Software Esquadrias API",
        "status": "online",
        "api_version": "0.1.4",
        "documentation": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "api_version": "0.1.4",
        "engine": "CR_ENGINE_0.5.0",
        "engines": ["CR_ENGINE_0.5.0", MAXIM_AR_ENGINE_VERSION, GR_ENGINE_VERSION],
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
            "supported": True,
            "box_height_mm": PARAMETERS["shutter_box_height_mm"],
            "modes": list(SHUTTER_MODES),
            "boxes": list(SHUTTER_BOX_OPTIONS),
            "slats": list(SHUTTER_SLAT_OPTIONS),
            "geometry_effect": "A caixa de 200 mm é descontada da altura útil do marco.",
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


@app.get("/api/v1/engine/maxim-ar/options")
def maxim_ar_options():
    glasses = []
    for glass in GLASSES.values():
        if glass.code == "0" or glass.thickness_mm is None or glass.thickness_mm > 34:
            continue
        compatible_systems = ["DESIGN_WINDOW_60x78"]
        if glass.thickness_mm <= 24:
            compatible_systems.insert(0, "PRIME_WINDOW_42x63")
        glasses.append({
            "code": glass.code,
            "description": glass.description,
            "price": glass.unit_price,
            "thickness_mm": glass.thickness_mm,
            "compatible_systems": compatible_systems,
        })
    glasses.sort(key=lambda row: (row["thickness_mm"], row["description"]))
    return {
        "engine_version": MAXIM_AR_ENGINE_VERSION,
        "phase": 3,
        "leaf_systems": [
            {"value": "PRIME_WINDOW_42x63", "label": "Prime Janela 42x63"},
            {"value": "DESIGN_WINDOW_60x78", "label": "Design Janela 60x78"},
        ],
        "leaf_counts": list(range(1, 9)),
        "orientations": ["HORIZONTAL", "VERTICAL"],
        "module_modes": ["MÓDULO ÚNICO", "MÓDULOS SEPARADOS"],
        "glasses": glasses,
        "closures": list(MAXIM_AR_CLOSURE_OPTIONS),
        "cremonas": list(MAXIM_AR_CREMONA_OPTIONS),
        "internal_finishes": list(MAXIM_AR_INTERNAL_FINISH_OPTIONS),
        "external_finishes": list(MAXIM_AR_EXTERNAL_FINISH_OPTIONS),
        "screen": {
            "supported": True,
            "material_code": "TL3",
            "pricing": "largura_m * 110 + altura_m * 110 + 110",
        },
        "fixed_panels": {
            "supported": True,
            "positions": ["BOTTOM", "TOP"],
            "constraints": [
                "módulo separado sem travessas",
                "grade integrada (V,H) gera (V+1)*(H+1) vidros",
            ],
        },
        "leaf_grid": {
            "supported": False,
            "reason": "AF/AG fisicamente inválidos por confirmação de fabricação",
        },
        "structural_reinforcement": {
            "supported": True,
            "materials": ["ALUM10238", "ALUM15338"],
            "historical_orcs_cases": 0,
            "constraint": "opcional e somente em módulos separados",
        },
        "sealing": {"configurable": True, "unit": "m", "physical_paths": 3},
        "technical_gate": {
            "approved": True,
            "blockers": [],
        },
        "kerf_mm": PARAMETERS["kerf_mm"],
    }


@app.post("/api/v1/engine/maxim-ar/calculate")
def calculate_maxim_ar_endpoint(payload: MaximArItemRequest):
    try:
        cfg = _to_maxim_ar_config(payload)
        return _serialize_result(cfg, calculate_maxim_ar(cfg))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/v1/engine/gr/options")
def gr_options():
    glasses = sorted(
        [
            {
                "code": glass.code,
                "description": glass.description,
                "price": glass.unit_price,
                "thickness_mm": glass.thickness_mm,
            }
            for glass in GLASSES.values()
            if glass.code != "0" and glass.thickness_mm is not None and glass.thickness_mm < 35
        ],
        key=lambda row: (row["thickness_mm"], row["description"]),
    )
    return {
        "engine_version": GR_ENGINE_VERSION,
        "phase": 13,
        "applications": ["PORTA", "JANELA"],
        "leaf_counts": [1, 2],
        "leaf_count_constraints": {
            "PORTA": [1, 2],
            "JANELA": [1],
        },
        "leaf_systems": [
            {
                "value": "FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN",
                "label": "Porta Design 60x104 — abertura interna",
                "application": "PORTA",
                "leaf_counts": [1, 2],
            },
            {
                "value": "FOLHA DE PORTA ABERTURA EXTERNA 60X104MM - DESIGN",
                "label": "Porta Design 60x104 — abertura externa",
                "application": "PORTA",
                "leaf_counts": [1, 2],
            },
            {
                "value": "FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN",
                "label": "Janela Design 60x78 — abertura externa",
                "application": "JANELA",
                "leaf_counts": [1],
            },
        ],
        "panel_modes": ["PAINEL COMPLETO", "VIDRO INTEIRO", "SUPERIOR VIDRO/INFERIOR PAINEL"],
        "mixed_mode": {
            "supported": True,
            "application": "PORTA",
            "leaf_systems": [
                "FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN",
                "FOLHA DE PORTA ABERTURA EXTERNA 60X104MM - DESIGN",
            ],
            "leaf_counts": [1, 2],
            "hinge_description": "DOBRADIÇA 90MM",
            "closures": [
                "MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE",
                "MAÇANETA DUPLA COM FECHADURA MULTIPONTO E CHAVE",
            ],
            "split_field": "mixed_split_from_bottom_mm",
            "split_measurement": "da extremidade inferior da folha pronta para cima até a travessa horizontal",
            "split_is_flexible": True,
            "transom_profile": "DE6072",
            "transom_reinforcement": "RAG - DE6072",
            "reinforcement_screw_rule": "ceil(comprimento_da_travessa_mm / 400) PAR2 por travessa",
            "reinforcement_screw_rule_status": "RESOLVED_PHYSICAL",
            "historical_cases": 119,
            "explicit_reference_orcs_rows": [270, 285, 3560]
        },
        "glass_mode": {
            "supported": True,
            "applications": ["PORTA", "JANELA"],
            "leaf_counts_by_application": {
                "PORTA": [1, 2],
                "JANELA": [1],
            },
            "leaf_systems": [
                "FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN",
                "FOLHA DE PORTA ABERTURA EXTERNA 60X104MM - DESIGN",
                "FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN",
            ],
            "historical_one_leaf_door_cases": 125,
            "historical_two_leaf_door_cases": 58,
            "two_leaf_reference_orcs_row": 17138,
            "glasses": glasses,
            "window_glass": {
                "supported": True,
                "leaf_counts": [1],
                "hinge_description": "DOBRADIÇA 90MM",
                "closure_mode": "MAÇANETA COM CREMONA SEM CHAVE",
                "cremona_default": "CREMONA 2 PONTOS COMP. 800mm E:15mm",
                "historical_clean_90mm_cases": 12,
                "reference_orcs_rows": [11480, 11558],
                "ob_hinge_supported": True,
                "ob_hinge_description": "DOBRADIÇA SISTEMA OB",
                "ob_cremona_required": True,
                "ob_cremonas": [
                    "CREMONA OSCILO/GIRO COMP. 400mm E:15mm",
                    "CREMONA OSCILO/GIRO COMP. 900mm E:15mm",
                    "CREMONA OSCILO/GIRO COMP. 1100mm E:15mm",
                    "CREMONA OSCILO/GIRO COMP. 1400mm E:15mm",
                    "CREMONA OSCILO/GIRO COMP. 1900mm E:15mm",
                ],
                "ob_auto_selection": False,
                "historical_ob_glass_cases": 48,
                "ob_reference_orcs_row": 4572,
                "ob_evidence_status": "RESOLVED_PHYSICAL",
                "ob_physical_confirmation_date": "2026-09-23",
            },
        },
        "module_modes": ["MÓDULO ÚNICO"],
        "closures": [
            "MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE",
            "MAÇANETA DUPLA COM FECHADURA MULTIPONTO E CHAVE",
            "MAÇANETA COM CREMONA SEM CHAVE",
        ],
        "cremonas": {
            "window_default": "CREMONA 2 PONTOS COMP. 800mm E:15mm",
            "physical_evidence": "padrão informado pela fabricação para mais de 90% das janelas de giro no baseline 90mm",
            "ob_options": [
                "CREMONA OSCILO/GIRO COMP. 400mm E:15mm",
                "CREMONA OSCILO/GIRO COMP. 900mm E:15mm",
                "CREMONA OSCILO/GIRO COMP. 1100mm E:15mm",
                "CREMONA OSCILO/GIRO COMP. 1400mm E:15mm",
                "CREMONA OSCILO/GIRO COMP. 1900mm E:15mm",
            ],
            "ob_selection": "explícita; sem inferência automática de comprimento na Fase 9",
        },
        "hinges": ["DOBRADIÇA 90MM", "DOBRADIÇA SISTEMA OB"],
        "internal_finishes": ["GUARNIÇÃO DE 70MM"],
        "external_finishes": ["BARRA CHATA DE 30MM"],
        "panel_squaring_blocks": {
            "material_code": "AC0312",
            "quantity_per_leaf": 4,
            "status": "RESOLVED_PHYSICAL",
            "purpose": "manter cada folha no esquadro e impedir que ceda, com ou sem vidro",
        },
        "sealing": {
            "status": "LEGACY_BUG_CONFIRMED",
            "physical_evidence_date": "2026-09-22",
            "paths": [
                {
                    "role": "BORRACHA DE VIDRO / LAMBRI",
                    "catalog_code": "ACB606",
                    "catalog_reference": "LISTAPERFIS!A53:C53",
                    "applies_to": "perímetro onde entra vidro ou lambri",
                },
                {
                    "role": "BORRACHA REDONDA — FOLHA",
                    "catalog_code": "AC0002",
                    "catalog_reference": "LISTAPERFIS!A55:C55",
                    "applies_to": "folha por fora",
                },
                {
                    "role": "BORRACHA REDONDA — MARCO",
                    "catalog_code": "AC0002",
                    "catalog_reference": "LISTAPERFIS!A55:C55",
                    "applies_to": "marco por dentro",
                },
            ],
            "legacy_problem": "GR!76:78 zerava todas as vedações por condição de família incorreta; painel completo também omitiria a vedação do lambri.",
        },
        "two_leaf_door": {
            "supported": True,
            "historical_clean_panel_cases": 72,
            "historical_glass_cases": 58,
            "panel_rule_status": "LEGACY_BUG_CONFIRMED",
            "panel_rule": "DE20150 deve ser calculado por folha; o XLSM legado não duplicava as faixas em 2 folhas",
            "passive_leaf_hardware": ["2x FEC7", "2x CON3"],
            "passive_hardware_screws": "incluídos nos kits; não adicionar PAR1",
            "physical_evidence_date": "2026-09-17",
        },
        "screen": {"supported": False},
        "shutter": {
            "supported": True,
            "modes": [
                "MANUAL EM PAINEL ÚNICO",
                "AUTOMATIZADA COM BOTOEIRA EM PAINEL ÚNICO",
                "AUTOMATIZADA COM CONTROLE REMOTO EM PAINEL ÚNICO",
                "MANUAL EM 2 PAINÉIS COM EIXOS INDEPENDENTES"
            ],
            "box_description": "CAIXA DE 200MM",
            "slat_description": "TALA DE PVC 40MM",
            "panel_modes": ["VIDRO INTEIRO"],
            "historical_total_cases": 67,
            "historical_manual_single_cases": 44,
            "historical_remote_single_cases": 10,
            "historical_button_single_cases": 7,
            "historical_manual_double_independent_cases": 6,
            "reference_orcs_rows": [18132, 11111, 11417, 12395, 4109],
            "independent_double": {
                "supported": True,
                "application": "PORTA",
                "leaf_count": 2,
                "panel_count": 2,
                "central_guide": "327204",
                "shaft_quantity": 2,
                "independent_divider": "371127",
                "shared_divider": None,
                "physical_corrections": [
                    "2 eixos físicos, um por painel",
                    "corrige typo INDEPENDNETES do XLSM e não usa divisor compartilhado"
                ]
            },
            "geometry": {
                "box_height_mm": 200,
                "box_length_rule": "largura_total - 15",
                "side_guide_length_rule": "altura_total - 200",
                "slat_width_rule": "largura_total - 74",
                "shaft_length_rule": "largura_total - 40"
            },
            "physical_slats": "ceil(altura_total / 40)",
            "legacy_status": [
                "GR!85:102 referencia auxiliares inexistentes 143:156",
                "GR!I103 omite os acessórios da persiana do subtotal",
                "a v0.11 recupera o kit manual de painel único pela CR homologada com os mesmos códigos",
                "a v0.12 recupera os kits automatizados e corrige botoeira para MOT2 (GR!B98 apontava MOT1)",
                "a v0.13 corrige 2 eixos físicos e divisor independente no modo manual de 2 painéis"
            ]
        },
        "fixed_panels": {"supported": False},
        "leaf_grid": {"supported": False},
        "structural_reinforcement": {"supported": False},
        "purchase_plan": {
            "supported": False,
            "reason": "Fase 13 adiciona persiana manual em 2 painéis com eixos independentes; compra/corte GR ainda requer modelagem definitiva de estoque, barras, painel DE20150 e persiana.",
        },
        "technical_gate": {
            "status": "CANDIDATO_A_AUDITORIA_FASE_13",
            "open_questions": [],
        },
    }


@app.post("/api/v1/engine/gr/calculate")
def calculate_gr_endpoint(payload: GrItemRequest):
    try:
        cfg = _to_gr_config(payload)
        return _serialize_result(cfg, calculate_gr(cfg))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/engine/maxim-ar/purchase-plan")
def calculate_maxim_ar_purchase_plan(payload: MaximArPurchasePlanRequest):
    try:
        order_items = []
        serialized_items = []
        for item in payload.items:
            cfg = _to_maxim_ar_config(item)
            result = calculate_maxim_ar(cfg)
            order_items.append((cfg, result))
            serialized_items.append(_serialize_result(cfg, result))
        plan = build_order_purchase_plan(order_items, kerf_mm=payload.kerf_mm)
        return {
            "items": serialized_items,
            "purchase_plan": _serialize_purchase_plan(plan),
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/purchase-plans/calculate-all")
def calculate_unified_purchase_plan(payload: UnifiedPurchasePlanRequest):
    """Plano FFD único para pedidos mistos CR + Maxim-Ar."""
    try:
        order_items = []
        serialized_items = []
        for item in payload.items:
            if isinstance(item, MaximArItemRequest):
                cfg = _to_maxim_ar_config(item)
                result = calculate_maxim_ar(cfg)
            else:
                cfg = _to_config(item)
                result = calculate_sliding(cfg)
            order_items.append((cfg, result))
            serialized_items.append(_serialize_result(cfg, result))
        plan = build_order_purchase_plan(order_items, kerf_mm=payload.kerf_mm)
        return {
            "items": serialized_items,
            "purchase_plan": _serialize_purchase_plan(plan),
        }
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
            "purchase_plan": _serialize_purchase_plan(plan),
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
