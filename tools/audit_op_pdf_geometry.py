"""Extract only image transforms from the 12 hashed private PDF references."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parents[1]


def reference_geometry(reference_dir: Path) -> dict:
    """No header text/pixels exported: only page IDs, hashes and image boxes."""
    cases = json.loads((ROOT / "api/tests/fixtures/op_layout_reference_v1.json").read_text(encoding="utf-8"))["cases"]
    records = []
    for case in cases:
        path = reference_dir / case["source"]["filename"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != case["source_sha256"]:
            raise ValueError("Fonte PDF difere da referência B1.")
        with pymupdf.open(path) as document:
            page = document[case["source"]["page"] - 1]
            model, profiles = [], []
            for image in page.get_images():
                rects = [[round(value, 4) for value in rect] for rect in page.get_image_rects(image[0])]
                (model if image[2:4] == (300, 300) else profiles).extend(rects)
            records.append({"id": case["id"], "source": case["source"], "source_sha256": case["source_sha256"],
                            "model_boxes_pt": model, "profile_boxes_pt": sorted(profiles, key=lambda box: box[1])})
    box = records[0]["model_boxes_pt"][0]
    return {"version": "OP_PDF_REFERENCE_GEOMETRY_0.1.0", "scope": "PRINT_TRANSFORMS_NOT_ENGINEERING_DIMENSIONS",
            "model_box_top_left_pt": box, "profile_slot_size_pt": [38.04, 20.28],
            "profile_min_row_height_pt": 24, "image_scaling": "LEGACY_SHAPE_STRETCH_PRESERVING_ORIGINAL_BYTES",
            "cases": records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = reference_geometry(args.reference_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"reference_cases": len(data["cases"])}))


if __name__ == "__main__":
    main()
