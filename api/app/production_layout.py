"""Immutable OP presentation blocks for future PDF rendering; no PDF or UI."""
from __future__ import annotations

import hashlib
import json
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from . import engine_bridge
from esquadrias_engine.catalog import MATERIALS
from .production_images import ImageSelector, LayoutImage, ProductionImageStore, finish_identity, model_identity
from .production_ordering import ORDER_VERSION, legacy_anchor
from .production_schemas import OPModel, ProductionOrder, ProductionOrderLine, ProductionOrderRequest
from .production_service import build_production_order, canonical_json


class LayoutItemLabel(OPModel):
    item_id: str = Field(min_length=1)
    label: str = Field(min_length=1, max_length=100)


class ProductionLayoutContext(OPModel):
    """Private header data supplied by caller, always bound to one company."""
    company_id: UUID
    client_code: str | None = Field(default=None, min_length=1, max_length=100)
    client_name: str | None = Field(default=None, min_length=1, max_length=200)
    work_code: str | None = Field(default=None, min_length=1, max_length=100)
    work_name: str | None = Field(default=None, min_length=1, max_length=200)
    item_labels: tuple[LayoutItemLabel, ...] = ()

    @model_validator(mode="after")
    def valid_labels(self):
        if len({i.item_id for i in self.item_labels}) != len(self.item_labels):
            raise ValueError("Rótulo de item duplicado.")
        for text in (self.client_code, self.client_name, self.work_code, self.work_name, *(i.label for i in self.item_labels)):
            if text is not None and (not text.strip() or any(ord(c) < 32 for c in text)):
                raise ValueError("Cabeçalho exige texto não vazio, sem caracteres de controle.")
        return self


class ProductionLayoutRequest(OPModel):
    production_order: ProductionOrderRequest
    context: ProductionLayoutContext


class ProductionItemHeader(OPModel):
    client_code: str | None
    client_name: str | None
    work_code: str | None
    work_name: str | None
    item_id: str
    item_label: str
    width_mm: float
    height_mm: float
    quantity: int


class LayoutFinding(OPModel):
    code: str
    item_id: str
    field: str
    message: str
    engine_position: int | None = None


class ProductionLayoutRow(OPModel):
    """Separate print/source position, with the original technical row intact."""
    print_position: int
    engine_position: int
    legacy_sheet: str
    legacy_row: int | None
    utilization_label: str | None
    technical: ProductionOrderLine
    profile_image: LayoutImage | None = None


class ProductionLayoutBlock(OPModel):
    """Contiguous table segment: grouping never changes global row order."""
    position: int
    kind: Literal["CUTS", "SURFACES", "CONSUMABLES", "ACCESSORIES", "HARDWARE", "SCREWS", "ENGINE_EXTENSION"]
    columns: tuple[str, ...]
    rows: tuple[ProductionLayoutRow, ...]
    repeat_columns_on_continuation: bool = True
    allow_continuation: bool = True


class ProductionItemPagePlan(OPModel):
    """One reference item per A4 portrait page intent; no pagination/truncation yet."""
    item_id: str
    position: int
    page_format: Literal["A4"] = "A4"
    orientation: Literal["PORTRAIT"] = "PORTRAIT"
    regions: tuple[str, ...] = ("MODEL_AND_SECTIONS", "HEADER", "MODEL_DESCRIPTION", "TABLE_BLOCKS", "FINDINGS")
    header_columns: tuple[str, ...] = ("Cód. Cliente", "Nome", "Item", "Largura", "Altura", "Quant.")
    header: ProductionItemHeader
    model_description: str
    finish_key: str | None
    model_key: str
    model_image: LayoutImage
    frame_section: LayoutImage
    leaf_section: LayoutImage | None
    blocks: tuple[ProductionLayoutBlock, ...]
    ordering_status: Literal["SOURCE_ORDER_MAPPED", "PARTIALLY_MAPPED"]
    findings: tuple[LayoutFinding, ...]


class ProductionLayoutDocument(OPModel):
    schema_version: Literal["OP_LAYOUT_B1_0.1.0"] = "OP_LAYOUT_B1_0.1.0"
    company_id: UUID
    order_id: str
    ordering_version: str = ORDER_VERSION
    technical_snapshot_sha256: str
    header_snapshot_json: str
    asset_manifest_sha256: str | None
    pages: tuple[ProductionItemPagePlan, ...]
    layout_sha256: str
    audit_status: Literal["PENDING_B1_AUDIT"] = "PENDING_B1_AUDIT"


_CUT_COLUMNS = ("Utilização", "Imagem do perfil", "Descrição", "Código", "Med. Final (mm)", "Med. Corte (mm)", "Quant.", "Unidade da quantidade")
_SURFACE_COLUMNS = ("Utilização", "Descrição", "Código", "Largura (mm)", "Altura (mm)", "Quant.", "Unidade da quantidade")
_UNIT_COLUMNS = ("Utilização", "Descrição", "Código", "Quant.", "Unidade da quantidade")
_FRAME_ROLES = {"FRAME_HORIZONTAL", "FRAME_WIDTH", "Marco Largura"}
_LEAF_ROLES = {"LEAF_HORIZONTAL", "LEAF_WIDTH"}
_PICTURE_ROLES = _FRAME_ROLES | _LEAF_ROLES | {"FRAME_VERTICAL", "FRAME_HEIGHT", "Marco Altura", "LEAF_VERTICAL", "LEAF_HEIGHT"}


def build_production_layout(
    document: ProductionOrder, context: ProductionLayoutContext,
    *, image_store: ProductionImageStore | None = None,
) -> ProductionLayoutDocument:
    """Build presentation from a saved OP without calling any calculator.

    Existing unknown/extra rows remain visible. Source anchors reorder only
    known rows; unmapped additions are explicit final extension blocks.
    """
    digest = hashlib.sha256(canonical_json(document.model_dump(mode="json", exclude={"snapshot_sha256"})).encode("utf-8")).hexdigest()
    if digest != document.snapshot_sha256:
        raise ValueError("Snapshot técnico foi alterado; hash inválido.")
    if context.company_id != document.company_id or image_store and image_store.manifest.company_id != document.company_id:
        raise ValueError("Contexto/manifest de outra empresa.")
    if {label.item_id for label in context.item_labels} - {item.item_id for item in document.items}:
        raise ValueError("Rótulo de cabeçalho referencia item inexistente.")
    pages = []
    for item in document.items:
        inputs = json.loads(item.input_snapshot_json)
        finish = finish_identity(item.finish_key)
        model_key, _ = model_identity(inputs, finish)
        findings = []

        def finding(code, field, message, position=None):
            findings.append(LayoutFinding(code=code, item_id=item.item_id, field=field, message=message, engine_position=position))

        def image(kind, code=None, position=None):
            if not finish or kind == "PROFILE_SECTION" and (not code or code == "0" or code not in MATERIALS or MATERIALS[code].unit != "m"):
                resolved = LayoutImage(selector=None, status="MISSING_TECHNICAL_DATA")
            else:
                selector = ImageSelector(kind=kind, model_key=model_key if kind == "MODEL_SKETCH" else None,
                                         code=code, finish_key=finish)
                resolved = image_store.resolve(selector, document.company_id) if image_store else LayoutImage(selector=selector, status="MISSING_ASSET")
            if resolved.status != "VERIFIED":
                finding(resolved.status, "images", "Imagem técnica ausente ou não verificada; nenhum substituto foi aplicado.", position)
            return resolved

        model_image = image("MODEL_SKETCH")
        frame = next((line for line in item.lines if line.utilization in _FRAME_ROLES), None)
        leaf = next((line for line in item.lines if line.utilization in _LEAF_ROLES), None)
        frame_section = image("PROFILE_SECTION", frame.code if frame else None)
        leaf_section = image("PROFILE_SECTION", leaf.code if leaf else None) if item.family != "FX" else None
        ordered = [(line, *legacy_anchor(item.family, line, inputs)) for line in item.lines]
        ordered.sort(key=lambda record: (record[2] is None, record[2] or 0, record[0].position))
        grid_review = item.family != "FX" and any(inputs.get("leaf_grid", {}).get(axis, 0) for axis in ("vertical_transoms", "horizontal_transoms"))
        if grid_review:
            finding("DYNAMIC_LAYOUT_REVIEW", "ordering", "Grades preservadas integralmente por âncora; conferir rótulos A/B/C e subdivisões com OP própria.")
        blocks = []
        for position, (line, sheet, row, label) in enumerate(ordered, 1):
            if row is None:
                kind = "ENGINE_EXTENSION"
                finding("UNMAPPED_LEGACY_ROW", "ordering", "Linha adicional preservada; posição POP/OP precisa de comprovação.", line.position)
            elif line.width_mm is not None and line.height_mm is not None:
                kind = "SURFACES"
            elif line.quantity_unit == "run":
                kind = "CONSUMABLES"
            elif line.cut_length_mm is not None:
                kind = "CUTS"
            elif "SCREW" in line.utilization:
                kind = "SCREWS"
            elif line.group == "FERRAGENS":
                kind = "HARDWARE"
            else:
                kind = "ACCESSORIES"
            if line.quantity_unit == "unresolved" or line.quantity_unit == "piece" and not line.quantity_total.is_integer():
                finding("FRACTIONAL_UNIT_REVIEW", "quantity", "Unidade/quantidade física exige confirmação; valor original preservado.", line.position)
            if line.quantity_unit == "run":
                finding("CONSUMPTION_PRESENTATION_REVIEW", "quantity", "Consumo agregado em comprimento/conjuntos; não tratar como peças físicas.", line.position)
            layout_row = ProductionLayoutRow(print_position=position, engine_position=line.position,
                                            legacy_sheet=sheet, legacy_row=row, utilization_label=label,
                                            technical=line, profile_image=image("PROFILE_SECTION", line.code, line.position) if line.utilization in _PICTURE_ROLES else None)
            columns = _CUT_COLUMNS if kind in {"CUTS", "ENGINE_EXTENSION"} else _SURFACE_COLUMNS if kind == "SURFACES" else (
                _UNIT_COLUMNS + ("Comprimento agregado (mm)",) if kind == "CONSUMABLES" else _UNIT_COLUMNS)
            if blocks and blocks[-1].kind == kind:
                blocks[-1] = blocks[-1].model_copy(update={"rows": blocks[-1].rows + (layout_row,)})
            else:
                blocks.append(ProductionLayoutBlock(position=len(blocks) + 1, kind=kind, columns=columns, rows=(layout_row,)))
        for validation in document.validations:
            # B1 resolves its own stable image identities instead of Phase A's
            # all-input hash keys. All non-image technical findings are retained.
            if validation.item_id == item.item_id and validation.code != "MISSING_ASSET" and not validation.field.startswith("assets.") and validation.code != "LEGACY_LAYOUT_UNVERIFIED":
                finding(validation.code, validation.field, validation.message, validation.position)
        for field in ("client_code", "client_name", "work_name"):
            if getattr(context, field) is None:
                finding("MISSING_HEADER_DATA", f"header.{field}", "Dado privado de cabeçalho não fornecido.")
        header = ProductionItemHeader(**context.model_dump(exclude={"company_id", "item_labels"}),
                                      item_id=item.item_id, item_label=next((v.label for v in context.item_labels if v.item_id == item.item_id), item.item_id),
                                      width_mm=inputs["width_mm"], height_mm=inputs["height_mm"], quantity=inputs["quantity"])
        pages.append(ProductionItemPagePlan(item_id=item.item_id, position=item.position, header=header,
                     model_description=item.model_description, finish_key=finish, model_key=model_key,
                     model_image=model_image, frame_section=frame_section, leaf_section=leaf_section, blocks=tuple(blocks),
                     ordering_status="PARTIALLY_MAPPED" if grid_review or any(record[2] is None for record in ordered) else "SOURCE_ORDER_MAPPED", findings=tuple(findings)))
    manifest_digest = None if image_store is None else hashlib.sha256(canonical_json(image_store.manifest.model_dump(mode="json")).encode("utf-8")).hexdigest()
    result = ProductionLayoutDocument(company_id=document.company_id, order_id=document.order_id,
              technical_snapshot_sha256=document.snapshot_sha256, header_snapshot_json=canonical_json(context.model_dump(mode="json")),
              asset_manifest_sha256=manifest_digest, pages=tuple(pages), layout_sha256="")
    digest = hashlib.sha256(canonical_json(result.model_dump(mode="json", exclude={"layout_sha256"})).encode("utf-8")).hexdigest()
    return result.model_copy(update={"layout_sha256": digest})


def prepare_production_layout(request: ProductionLayoutRequest, *, image_store: ProductionImageStore | None = None) -> ProductionLayoutDocument:
    """Calculate via the existing OP service, then build immutable layout blocks."""
    if request.context.company_id != request.production_order.company_id or image_store and image_store.manifest.company_id != request.production_order.company_id:
        raise ValueError("Contexto/manifest de outra empresa.")
    return build_production_layout(build_production_order(request.production_order), request.context, image_store=image_store)
