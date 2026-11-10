"""Import selected original OP images into private content-addressed storage."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from api.app import engine_bridge
from esquadrias_engine.catalog import MATERIALS
from api.app.production_images import ImageSelector, import_legacy_images, model_identity, finish_identity
from api.app.production_schemas import ProductionOrderRequest

OFFICIAL_SHA = "96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160"


def main() -> None:
    """CLI requires explicit company, source, technical bindings and private destination."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--legacy-root", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--company-id", type=UUID, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--include-fixo-reference", action="store_true")
    args = parser.parse_args()
    digest = hashlib.sha256(args.workbook.read_bytes()).hexdigest()
    if digest != OFFICIAL_SHA:
        raise ValueError("Workbook não corresponde à fonte homologada.")
    cases = json.loads(args.inputs.read_text(encoding="utf-8"))["cases"]
    if args.include_fixo_reference:
        cases.append({"id": "FX-OWN-CASE", "finish_key": "BRANCO", "technical_input": {"family": "FX", "width_mm": 1200, "height_mm": 1000}})
    request = ProductionOrderRequest(company_id=args.company_id, order_id="PRIVATE-IMAGE-IMPORT", items=[
        {"item_id": c["id"], "finish_key": c["finish_key"], "technical_input": c["technical_input"]} for c in cases])
    bindings = []
    for item in request.items:
        key, basename = model_identity(item.technical_input.model_dump(mode="json"), item.finish_key)
        if basename is None:
            raise ValueError("Acabamento ausente no vínculo de croqui.")
        bindings.append((ImageSelector(kind="MODEL_SKETCH", model_key=key, finish_key=finish_identity(item.finish_key)), basename))
    profiles = tuple(sorted({p.stem for p in (args.legacy_root / "CROQUIS_PERFIS").iterdir() if p.is_file() and p.suffix.lower() == ".jpg" and p.stem in MATERIALS}))
    manifest, missing = import_legacy_images(args.legacy_root, args.output_root, args.company_id, digest, tuple(bindings), profiles)
    (args.output_root / "manifest.json").write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
    # No source path, customer data or asset bytes are printed/exported publicly.
    print(json.dumps({"entries": len(manifest.entries), "model_bindings": sum(e.selector.kind == "MODEL_SKETCH" for e in manifest.entries),
                      "profile_bindings": sum(e.selector.kind == "PROFILE_SECTION" for e in manifest.entries), "missing_bindings": len(missing)}))
    if missing:
        (args.output_root / "missing-bindings.json").write_text(json.dumps(missing, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
