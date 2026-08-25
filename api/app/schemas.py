from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


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


class PurchasePlanRequest(BaseModel):
    items: list[CRItemRequest] = Field(min_length=1)
