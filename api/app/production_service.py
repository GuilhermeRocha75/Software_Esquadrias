"""Stateless OP construction. Technical formulas remain in esquadrias_engine."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json

from . import engine_bridge  # establishes the active Engine import path
from esquadrias_engine.catalog import MATERIALS
from esquadrias_engine.production import build_production_item

from .configurations import _to_config, _to_maxim_ar_config, _to_gr_config, _to_fixo_config
from .production_assets import ProductionAssetIndex
from .production_schemas import (
    ProductionOrderRequest, ProductionOrder, ProductionOrderItem,
    ProductionOrderLine, ProductionValidation, ProductionAssetReference,
)


def canonical_json(value: object) -> str:
    """Stable UTF-8 JSON representation; rejects NaN and infinity."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _assets(item, lines, index, validations):
    references = []

    def add(kind, key, technical_missing=False):
        asset = index.find(key) if not technical_missing else None
        status = "MISSING_TECHNICAL_DATA" if technical_missing else ("AVAILABLE" if asset else "MISSING_ASSET")
        references.append(ProductionAssetReference(
            kind=kind, key=key, status=status,
            relative_path=asset.relative_path if asset else None,
            sha256=asset.sha256 if asset else None,
        ))
        if status != "AVAILABLE":
            validations.append(ProductionValidation(
                code=status, severity="error" if technical_missing else "warning",
                item_id=item.item_id, field=f"assets.{kind}.{key}",
                message="Descritor/código/cor ausente ou não validado." if technical_missing else "Arquivo não registrado no índice desta empresa.",
            ))

    finish = item.finish_key
    snapshot = canonical_json(item.technical_input.model_dump(mode="json"))
    # Complete technical descriptor avoids selecting a sketch solely by family.
    descriptor = hashlib.sha256(snapshot.encode("utf-8")).hexdigest()
    add("MODEL_SKETCH", f"model/{item.technical_input.family}/{descriptor}/{finish or 'UNSPECIFIED'}", not finish)
    for line in lines:
        if line.cut_length_mm is None or line.material_unit != "m" or line.group == "VEDAÇÕES":
            continue
        # A code with no catalogue entry is missing technical identification,
        # whereas a known profile without an image is only a missing asset.
        invalid = not line.code or line.code not in MATERIALS
        kind = "FRAME_SECTION" if line.utilization in {"FRAME_HORIZONTAL", "FRAME_WIDTH", "Marco Largura"} else (
            "LEAF_SECTION" if line.utilization in {"LEAF_HORIZONTAL", "LEAF_WIDTH"} else "PROFILE_SECTION")
        key = f"profile/{line.code or 'UNSPECIFIED'}/{finish or 'UNSPECIFIED'}"
        if not any(ref.kind == kind and ref.key == key for ref in references):
            add(kind, key, invalid or not finish)
    return tuple(references)


def build_production_order(
    request: ProductionOrderRequest,
    *,
    asset_index: ProductionAssetIndex | None = None,
) -> ProductionOrder:
    """Calculate a mixed OP, snapshot effective inputs and collect all gaps.

    Asset metadata is server supplied and company scoped. No persistence,
    authorization, PDF, pricing, purchase planning or formula correction occurs.
    ValueError means invalid technical input, foreign index or invalid output.
    """
    # Revalidate mutable input containers at the service boundary.
    request = ProductionOrderRequest.model_validate(request.model_dump(mode="json"))
    index = asset_index or ProductionAssetIndex(request.company_id)
    if index.company_id != request.company_id:
        raise ValueError("Índice de assets pertence a outra empresa.")
    dispatch = {
        "CR": (_to_config, engine_bridge.calculate_sliding),
        "MAXIM_AR": (_to_maxim_ar_config, engine_bridge.calculate_maxim_ar),
        "GR": (_to_gr_config, engine_bridge.calculate_gr),
        "FX": (_to_fixo_config, engine_bridge.calculate_fixo),
    }
    items, validations = [], []
    for position, item in enumerate(request.items, start=1):
        convert, calculate = dispatch[item.technical_input.family]
        cfg = convert(item.technical_input)
        try:
            result = calculate(cfg)
            technical = build_production_item(item.technical_input.family, result, stock_lengths_mm=request.stock_lengths_mm)
        except ValueError as exc:
            raise ValueError(f"Item {item.item_id}: {exc}") from exc
        lines = tuple(ProductionOrderLine(**asdict(line)) for line in technical.lines)
        for issue in technical.issues:
            validations.append(ProductionValidation(
                **asdict(issue), severity="error" if issue.code == "MISSING_TECHNICAL_DATA" else "warning",
                item_id=item.item_id,
            ))
        for warning in result.warnings:
            validations.append(ProductionValidation(
                code="ENGINE_WARNING", severity="warning", item_id=item.item_id,
                field=f"engine.{warning.code}", message=warning.message,
            ))
        validations.append(ProductionValidation(
            code="LEGACY_LAYOUT_UNVERIFIED", severity="warning", item_id=item.item_id,
            field="lines.position", message="Ordem/grupos da Engine preservados; conferir sequência impressa POP/OP com fonte privada.",
        ))
        assets = _assets(item, lines, index, validations)
        items.append(ProductionOrderItem(
            item_id=item.item_id, position=position, family=technical.family, finish_key=item.finish_key,
            input_snapshot_json=canonical_json(item.technical_input.model_dump(mode="json")),
            engine_version=technical.engine_version, technical_contract_version=technical.contract_version,
            model_description=technical.model_description, lines=lines, assets=assets,
        ))
    document = ProductionOrder(
        company_id=request.company_id, order_id=request.order_id,
        request_snapshot_json=canonical_json(request.model_dump(mode="json")), snapshot_sha256="",
        items=tuple(items), validations=tuple(validations),
        technical_data_complete=not any(v.code == "MISSING_TECHNICAL_DATA" for v in validations),
        assets_complete=all(asset.status == "AVAILABLE" for item in items for asset in item.assets),
    )
    digest = hashlib.sha256(canonical_json(document.model_dump(mode="json", exclude={"snapshot_sha256"})).encode("utf-8")).hexdigest()
    return document.model_copy(update={"snapshot_sha256": digest})
