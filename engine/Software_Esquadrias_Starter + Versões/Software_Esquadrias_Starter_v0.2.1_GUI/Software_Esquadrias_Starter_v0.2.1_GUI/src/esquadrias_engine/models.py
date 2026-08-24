from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict

class LeafSystem(str, Enum):
    PRIME_WINDOW_42x66 = "PRIME_WINDOW_42x66"
    PRIME_DOOR_42x88 = "PRIME_DOOR_42x88"
    DESIGN_DOOR_60x111 = "DESIGN_DOOR_60x111"

@dataclass(frozen=True)
class SlidingConfiguration:
    width_mm: float
    height_mm: float
    quantity: int
    leaf_count: int
    leaf_system: LeafSystem

    # Opções comerciais/técnicas que o Excel utiliza para completar a composição.
    glass_description: str = "04mm FLOAT INCOLOR"
    closure_mode: str = "MAÇANETA COM CREMONA + FECHO OCULTO"
    cremona_base: str = "CREMONA 1 PONTO"
    roller_description: str = "ROLDANA 30KG"
    internal_finish: str = "SEM ACABAMENTO"
    external_finish: str = "SEM ACABAMENTO"

    screen_enabled: bool = False
    shutter_enabled: bool = False

@dataclass(frozen=True)
class BomComponent:
    category: str
    role: str
    material_code: str
    description: str
    unit: str

    length_mm: float | None
    width_mm: float | None
    height_mm: float | None
    area_m2: float | None

    quantity_per_unit: float
    quantity_order: float
    unit_price: float
    cost_per_unit_product: float

@dataclass(frozen=True)
class EngineeringWarning:
    code: str
    message: str

@dataclass
class CalculationResult:
    model_description: str
    geometry: Dict[str, float]
    unit_bom: List[BomComponent]
    cost_breakdown: Dict[str, float]
    unit_cost: float
    warnings: List[EngineeringWarning] = field(default_factory=list)
    calculation_version: str = "CR_ENGINE_0.2.0"
