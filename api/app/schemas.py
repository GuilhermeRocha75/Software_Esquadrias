from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class CustomDimensionRequest(BaseModel):
    axis: Literal["COLUMNS", "ROWS"]
    index: int = Field(ge=0)
    clear_span_mm: float = Field(gt=0)


class LeafGridRequest(BaseModel):
    horizontal_transoms: int = Field(default=0, ge=0)
    vertical_transoms: int = Field(default=0, ge=0)
    custom_dimensions: list[CustomDimensionRequest] = Field(default_factory=list)


class FixedPanelRequest(BaseModel):
    height_mm: float = Field(gt=0)
    horizontal_transoms: int = Field(default=0, ge=0)
    vertical_transoms: int = Field(default=0, ge=0)


class StructuralReinforcementRequest(BaseModel):
    material_code: Literal["ALUM10238", "ALUM15338"]


class ShutterRequest(BaseModel):
    mode: Literal[
        "SEM PERSIANA",
        "MANUAL EM PAINEL ÚNICO",
        "MANUAL EM 2 PAINÉIS COM EIXO ÚNICO",
        "MANUAL EM 2 PAINÉIS COM EIXOS INDEPENDENTES",
        "AUTOMATIZADA COM BOTOEIRA EM PAINEL ÚNICO",
        "AUTOMATIZADA COM BOTOEIRA EM 2 PAINÉIS",
        "AUTOMATIZADA COM BOTOEIRA EM 3 PAINÉIS",
        "AUTOMATIZADA COM CONTROLE REMOTO EM PAINEL ÚNICO",
        "AUTOMATIZADA COM CONTROLE REMOTO EM 2 PAINÉIS",
        "AUTOMATIZADA COM CONTROLE REMOTO EM 3 PAINÉIS",
    ]
    box_description: Literal["CAIXA DE 200MM"] = "CAIXA DE 200MM"
    slat_description: Literal["TALA DE PVC 40MM"] = "TALA DE PVC 40MM"


class CRItemRequest(BaseModel):
    width_mm: float = Field(gt=0)
    height_mm: float = Field(gt=0)
    quantity: int = Field(default=1, ge=1)
    leaf_count: Literal[2, 3, 4, 6]
    leaf_system: Literal[
        "PRIME_WINDOW_42x66",
        "PRIME_DOOR_42x88",
        "DESIGN_DOOR_60x111",
    ]
    application: Literal["JANELA", "PORTA"] = "JANELA"
    glass_description: str = "04mm FLOAT INCOLOR"
    closure_mode: str = "MAÇANETA COM CREMONA + FECHO OCULTO"
    cremona_base: str = "CREMONA 1 PONTO"
    roller_description: str = "ROLDANA 30KG"
    internal_finish: str = "SEM ACABAMENTO"
    external_finish: str = "SEM ACABAMENTO"
    screen_enabled: bool = False
    shutter_enabled: bool = False
    shutter: ShutterRequest | None = None
    leaf_grid: LeafGridRequest = Field(default_factory=LeafGridRequest)
    bottom_fixed_panel: FixedPanelRequest | None = None
    top_fixed_panel: FixedPanelRequest | None = None
    structural_reinforcement: StructuralReinforcementRequest | None = None


class PurchasePlanRequest(BaseModel):
    items: list[CRItemRequest] = Field(min_length=1)
    kerf_mm: float = Field(default=0.0, ge=0)
