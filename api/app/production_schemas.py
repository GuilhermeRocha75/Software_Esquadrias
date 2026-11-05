"""OP v1 input/output contracts. All public models are documented in docs/OP_FASE_A.md."""
from __future__ import annotations

import math
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .schemas import (
    CRItemRequest, MaximArItemRequest, GrItemRequest, FixoItemRequest,
    CustomDimensionRequest, LeafGridRequest, FixedPanelRequest,
    StructuralReinforcementRequest, MaximArSealingRequest, ShutterRequest,
)


class OPModel(BaseModel):
    """Closed, frozen transport model; no unknown fields or nonfinite numbers."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class OPCustomDimension(CustomDimensionRequest, OPModel):
    pass


class OPLeafGrid(LeafGridRequest, OPModel):
    custom_dimensions: list[OPCustomDimension] = Field(default_factory=list)


class OPFixedPanel(FixedPanelRequest, OPModel):
    pass


class OPReinforcement(StructuralReinforcementRequest, OPModel):
    pass


class OPSealing(MaximArSealingRequest, OPModel):
    pass


class OPShutter(ShutterRequest, OPModel):
    pass


class OPCRInput(CRItemRequest, OPModel):
    quantity: int = Field(default=1, ge=1, strict=True)
    leaf_grid: OPLeafGrid = Field(default_factory=OPLeafGrid)
    bottom_fixed_panel: OPFixedPanel | None = None
    top_fixed_panel: OPFixedPanel | None = None
    structural_reinforcement: OPReinforcement | None = None
    shutter: OPShutter | None = None


class OPMaximArInput(MaximArItemRequest, OPModel):
    quantity: int = Field(default=1, ge=1, strict=True)
    leaf_grid: OPLeafGrid = Field(default_factory=OPLeafGrid)
    bottom_fixed_panel: OPFixedPanel | None = None
    top_fixed_panel: OPFixedPanel | None = None
    structural_reinforcement: OPReinforcement | None = None
    sealing: OPSealing = Field(default_factory=OPSealing)


class OPGrInput(GrItemRequest, OPModel):
    quantity: int = Field(default=1, ge=1, strict=True)
    shutter: OPShutter | None = None


class OPFixoInput(FixoItemRequest, OPModel):
    pass


TechnicalInput = Annotated[OPCRInput | OPMaximArInput | OPGrInput | OPFixoInput, Field(discriminator="family")]


class ProductionOrderItemRequest(OPModel):
    """Stable item identity, optional finish asset key and explicit family input."""

    item_id: str = Field(min_length=1, max_length=100, pattern=r"^\S(?:.*\S)?$")
    finish_key: str | None = Field(default=None, min_length=1, max_length=100, pattern=r"^\S(?:.*\S)?$")
    technical_input: TechnicalInput

    @field_validator("technical_input", mode="before")
    @classmethod
    def validate_numbers(cls, value):
        def walk(node, key=""):
            if isinstance(node, BaseModel):
                node = node.model_dump()
            if isinstance(node, dict):
                for name, child in node.items():
                    walk(child, name)
            elif isinstance(node, (list, tuple)):
                for child in node:
                    walk(child, key)
            elif isinstance(node, bool) and key not in {"screen_enabled", "shutter_enabled"}:
                raise ValueError(f"Booleano não permitido em {key}.")
            elif isinstance(node, float) and not math.isfinite(node):
                raise ValueError(f"Número não finito em {key}.")
        walk(value)
        return value


class ProductionOrderRequest(OPModel):
    """Stateless preview request; company identity is context, not authorization."""

    company_id: UUID
    order_id: str = Field(min_length=1, max_length=100, pattern=r"^\S(?:.*\S)?$")
    items: tuple[ProductionOrderItemRequest, ...] = Field(min_length=1)
    stock_lengths_mm: dict[str, float] = Field(default_factory=dict)

    @field_validator("stock_lengths_mm", mode="before")
    @classmethod
    def stock_has_no_booleans(cls, value):
        if isinstance(value, dict) and any(isinstance(length, bool) for length in value.values()):
            raise ValueError("Comprimento de barra não aceita booleanos.")
        return value

    @model_validator(mode="after")
    def unique_items_and_stock(self):
        ids = [item.item_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("item_id deve ser único dentro da OP.")
        if any(not code.strip() or value <= 0 for code, value in self.stock_lengths_mm.items()):
            raise ValueError("Comprimento de barra deve ser positivo por material.")
        return self


class ProductionValidation(OPModel):
    """Actionable error/warning with item, field and optional source row."""

    code: Literal["MISSING_ASSET", "MISSING_TECHNICAL_DATA", "OVERSIZED_PIECE", "ENGINE_WARNING", "LEGACY_LAYOUT_UNVERIFIED"]
    severity: Literal["error", "warning"]
    item_id: str
    field: str
    message: str
    position: int | None = None


class ProductionAssetReference(OPModel):
    """Logical asset request, with a safe relative path only after validation."""

    kind: Literal["MODEL_SKETCH", "FRAME_SECTION", "LEAF_SECTION", "PROFILE_SECTION"]
    key: str
    status: Literal["AVAILABLE", "MISSING_ASSET", "MISSING_TECHNICAL_DATA"]
    relative_path: str | None = None
    sha256: str | None = None


class ProductionOrderLine(OPModel):
    """One Engine row with separate fabrication count and commercial unit."""

    position: int = Field(ge=1)
    group: str
    utilization: str
    code: str | None
    description: str | None
    material_unit: str | None
    quantity_unit: Literal["piece", "run", "consumption_factor", "unresolved"]
    quantity_per_unit: float = Field(ge=0)
    quantity_total: float = Field(ge=0)
    bom_quantity_per_unit: float = Field(ge=0)
    bom_quantity_total: float = Field(ge=0)
    final_length_mm: float | None = Field(default=None, gt=0)
    cut_length_mm: float | None = Field(default=None, ge=0)
    width_mm: float | None = Field(default=None, ge=0)
    height_mm: float | None = Field(default=None, ge=0)
    source: str | None
    measurement_basis: str | None
    splice_status: Literal["MANUAL_SPLICE_REQUIRED", "REQUIRES_ENGINEERING_REVIEW"] | None


class ProductionOrderItem(OPModel):
    """Snapshot JSON contains every effective technical input, including defaults."""

    item_id: str
    position: int
    family: Literal["CR", "MAXIM_AR", "GR", "FX"]
    finish_key: str | None
    input_snapshot_json: str
    engine_version: str
    technical_contract_version: str
    model_description: str
    lines: tuple[ProductionOrderLine, ...]
    assets: tuple[ProductionAssetReference, ...]


class ProductionOrder(OPModel):
    """Immutable values for future rendering, without commercial/purchase data."""

    schema_version: Literal["OP_0.1.0"] = "OP_0.1.0"
    company_id: UUID
    order_id: str
    request_snapshot_json: str
    snapshot_sha256: str
    items: tuple[ProductionOrderItem, ...]
    validations: tuple[ProductionValidation, ...]
    technical_data_complete: bool
    assets_complete: bool
    audit_status: Literal["PENDING_INDEPENDENT_AUDIT"] = "PENDING_INDEPENDENT_AUDIT"
