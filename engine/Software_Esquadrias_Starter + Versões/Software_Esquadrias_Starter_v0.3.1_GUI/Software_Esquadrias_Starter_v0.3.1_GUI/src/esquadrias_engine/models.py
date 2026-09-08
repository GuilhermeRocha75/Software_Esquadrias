from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict

class LeafSystem(str, Enum):
    PRIME_WINDOW_42x66 = "PRIME_WINDOW_42x66"
    PRIME_DOOR_42x88 = "PRIME_DOOR_42x88"
    DESIGN_DOOR_60x111 = "DESIGN_DOOR_60x111"

class ApplicationType(str, Enum):
    WINDOW = "JANELA"
    DOOR = "PORTA"


class GridAxis(str, Enum):
    COLUMNS = "COLUMNS"
    ROWS = "ROWS"


class TransomOrientation(str, Enum):
    HORIZONTAL = "HORIZONTAL"
    VERTICAL = "VERTICAL"


class FixedPanelPosition(str, Enum):
    BOTTOM = "BOTTOM"
    TOP = "TOP"


@dataclass(frozen=True)
class CustomDimension:
    """Clear size of one opening in a grid axis.

    ``index`` is zero-based. Openings without a custom value share the
    remaining clear span equally. This replaces the ambiguous A..K helper
    cells from the legacy workbook with an explicit geometric contract.
    """

    axis: GridAxis
    index: int
    clear_span_mm: float


@dataclass(frozen=True)
class LeafGrid:
    horizontal_transoms: int = 0
    vertical_transoms: int = 0
    custom_dimensions: tuple[CustomDimension, ...] = ()


@dataclass(frozen=True)
class FixedPanelConfiguration:
    height_mm: float
    horizontal_transoms: int = 0
    vertical_transoms: int = 0


@dataclass(frozen=True)
class StructuralReinforcement:
    material_code: str

@dataclass(frozen=True)
class SlidingConfiguration:
    width_mm: float
    height_mm: float
    quantity: int
    leaf_count: int
    leaf_system: LeafSystem

    # No Excel, aplicação e tipo de folha são independentes.
    application: ApplicationType = ApplicationType.WINDOW

    glass_description: str = "04mm FLOAT INCOLOR"
    closure_mode: str = "MAÇANETA COM CREMONA + FECHO OCULTO"
    cremona_base: str = "CREMONA 1 PONTO"
    roller_description: str = "ROLDANA 30KG"
    internal_finish: str = "SEM ACABAMENTO"
    external_finish: str = "SEM ACABAMENTO"

    screen_enabled: bool = False
    shutter_enabled: bool = False

    leaf_grid: LeafGrid = field(default_factory=LeafGrid)
    bottom_fixed_panel: FixedPanelConfiguration | None = None
    top_fixed_panel: FixedPanelConfiguration | None = None
    structural_reinforcement: StructuralReinforcement | None = None


@dataclass(frozen=True)
class GridOpening:
    source: str
    row_index: int
    column_index: int
    width_mm: float
    height_mm: float
    quantity: float


@dataclass(frozen=True)
class Transom:
    source: str
    orientation: TransomOrientation
    material_code: str
    reinforcement_material_code: str
    length_mm: float
    quantity: float


@dataclass(frozen=True)
class FixedPanelGeometry:
    position: FixedPanelPosition
    width_mm: float
    nominal_height_mm: float
    frame_height_mm: float
    horizontal_transoms: int
    vertical_transoms: int
    openings: tuple[GridOpening, ...]


@dataclass(frozen=True)
class GlassPanel:
    source: str
    position: str
    width_mm: float
    height_mm: float
    quantity: float
    material_code: str
    material_description: str
    area_m2: float
    unit_cost: float
    total_cost: float

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
    source: str | None = None

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
    leaf_openings: List[GridOpening] = field(default_factory=list)
    transoms: List[Transom] = field(default_factory=list)
    fixed_panels: List[FixedPanelGeometry] = field(default_factory=list)
    glass_panels: List[GlassPanel] = field(default_factory=list)
    warnings: List[EngineeringWarning] = field(default_factory=list)
    calculation_version: str = "CR_ENGINE_0.4.0"

@dataclass(frozen=True)
class CutPiece:
    material_code: str
    description: str
    length_mm: float
    source_item: int
    source_role: str
    source_position: str | None = None

@dataclass
class BarAllocation:
    bar_number: int
    stock_length_mm: float
    pieces: List[CutPiece] = field(default_factory=list)
    kerf_mm: float = 0.0

    @property
    def used_mm(self) -> float:
        return sum(p.length_mm for p in self.pieces) + self.kerf_mm * len(self.pieces)

    @property
    def leftover_mm(self) -> float:
        return self.stock_length_mm - self.used_mm

@dataclass
class PurchaseLine:
    material_code: str
    description: str
    unit_price_per_m: float
    stock_length_mm: float
    pieces_count: int
    consumed_length_mm: float
    bars_required: int
    purchased_length_mm: float
    waste_length_mm: float
    utilization_pct: float
    consumption_cost: float
    purchase_cost: float
    kerf_mm: float = 0.0
    kerf_loss_mm: float = 0.0
    bars: List[BarAllocation] = field(default_factory=list)

@dataclass
class OrderPurchasePlan:
    lines: List[PurchaseLine]
    technical_total: float
    bar_stock_consumption_cost: float
    bar_stock_purchase_cost: float
    exact_nonbar_cost: float
    procurement_total_estimate: float
    purchase_increment_vs_consumption: float
    kerf_mm: float = 0.0
    warnings: List[EngineeringWarning] = field(default_factory=list)
