"""Compare OP presentation ordering against anonymized PDF row evidence."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from api.app.production_images import ProductionImageManifest, ProductionImageStore, model_identity
from api.app.production_layout import ProductionLayoutContext, build_production_layout
from api.app.production_schemas import ProductionOrderRequest
from api.app.production_service import build_production_order
from esquadrias_engine.catalog import normalize

COMPANY = UUID("00000000-0000-0000-0000-000000000001")


def compare_layout_case(reference: dict, reconstruction: dict, image_store=None) -> dict:
    """Compare relative order of common rows; enumerate additions/absences/codes.

    A match does not assert full BOM parity. Unknown reference inputs are not
    filled to force a match. No customer headers are copied to this report.
    """
    request = ProductionOrderRequest(company_id=COMPANY, order_id="ANON-LAYOUT", items=[{
        "item_id": reference["id"], "finish_key": reconstruction["finish_key"],
        "technical_input": reconstruction["technical_input"]}])
    technical = build_production_order(request)
    page = build_production_layout(technical, ProductionLayoutContext(company_id=COMPANY), image_store=image_store).pages[0]
    rows = [r for b in page.blocks for r in b.rows]
    used, matched, additions, code_differences = set(), [], [], []
    for row in rows:
        candidates = [(n, r) for n, r in enumerate(reference["rows"]) if n not in used
                      and row.utilization_label is not None and normalize(row.utilization_label) == normalize(r["label"])]
        if not candidates and row.utilization_label is None:
            candidates = [(n, r) for n, r in enumerate(reference["rows"]) if n not in used and r["code"] == row.technical.code]
        if len(candidates) == 1:
            n, expected = candidates[0]
            used.add(n)
            matched.append({"pdf_position": n + 1, "print_position": row.print_position,
                            "engine_position": row.engine_position, "legacy_row": row.legacy_row,
                            "utilization": expected["label"]})
            if expected["code"] != row.technical.code:
                code_differences.append({"utilization": expected["label"], "pdf_code": expected["code"],
                                         "engine_code": row.technical.code, "reason": "INPUT_OR_EXISTING_TECHNICAL_DIFFERENCE_NOT_CORRECTED"})
        else:
            additions.append({"engine_position": row.engine_position, "role": row.technical.utilization,
                              "legacy_row": row.legacy_row, "reason": "ENGINE_ROW_NOT_IN_REFERENCE_OR_AMBIGUOUS"})
    positions = [r["pdf_position"] for r in matched]
    _, basename = model_identity(json.loads(technical.items[0].input_snapshot_json), reconstruction["finish_key"])
    return {"id": reference["id"], "source": reference["source"], "ordering_status": page.ordering_status,
            "relative_order": "MATCH" if positions == sorted(positions) else "DIVERGENT",
            "model_basename_matches": basename == reference["model_basename"],
            "images": {"model": page.model_image.status, "frame": page.frame_section.status,
                       "leaf": page.leaf_section.status if page.leaf_section else "NOT_APPLICABLE"},
            "engine_row_count": len(technical.items[0].lines), "presentation_row_count": len(rows),
            "common_rows": matched, "engine_additions": additions,
            "reference_rows_without_engine_match": [r for n, r in enumerate(reference["rows"]) if n not in used],
            "code_differences": code_differences, "missing_inputs": reconstruction["missing_inputs"],
            "scope": "RELATIVE_ORDER_ONLY_NOT_FULL_TECHNICAL_OR_VISUAL_PARITY"}


def build_report(image_store=None) -> dict:
    """Build the 12 sanitized reference comparisons; optional private image check."""
    fixtures = ROOT / "api/tests/fixtures"
    references = json.loads((fixtures / "op_layout_reference_v1.json").read_text(encoding="utf-8"))["cases"]
    inputs = {c["id"]: c for c in json.loads((fixtures / "op_reference_inputs.json").read_text(encoding="utf-8"))["cases"]}
    cases = [compare_layout_case(c, inputs[c["id"]], image_store) for c in references]
    return {"scope": "B1_PRESENTATION_NOT_HOMOLOGATED", "cases": cases,
            "relative_order_counts": dict(Counter(c["relative_order"] for c in cases)),
            "model_identity_matches": sum(c["model_basename_matches"] for c in cases),
            "engine_rows": sum(c["engine_row_count"] for c in cases),
            "presentation_rows": sum(c["presentation_row_count"] for c in cases)}


def main() -> None:
    """CLI: --output JSON report; optional --manifest verifies actual private images."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    store = None if args.manifest is None else ProductionImageStore(args.manifest.parent,
                 ProductionImageManifest.model_validate_json(args.manifest.read_text(encoding="utf-8")))
    report = build_report(store)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}))


if __name__ == "__main__":
    main()
