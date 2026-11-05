"""Read private OP sources; export only whitelisted technical ordering evidence.

Never exports headers, customer values, raw PDF text, VBA or absolute paths.
The source workbook must match the homologated SHA. No macros are executed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from audit_maxim_ar_phase3a import shared_strings, sheet_targets, sheet_cells
from api.app import engine_bridge
from api.app.production_images import model_identity
from esquadrias_engine.catalog import MATERIALS, HARDWARE, GLASSES, normalize

OFFICIAL_SHA = "96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160"
FAMILIES = {"CR": "CR", "MAXIM_AR": "MX", "GR": "GR", "FX": "FX"}


def workbook_order(workbook: Path) -> dict:
    """Read A8:A200 labels only; customer/cache/input cells are excluded."""
    if hashlib.sha256(workbook.read_bytes()).hexdigest() != OFFICIAL_SHA:
        raise ValueError("Workbook não corresponde ao SHA homologado.")
    families = {}
    with ZipFile(workbook) as archive:
        targets, strings = sheet_targets(archive), shared_strings(archive)
        for family, sheet in FAMILIES.items():
            rows = []
            for coordinate, value, _ in sheet_cells(archive, targets[sheet], strings):
                match = re.fullmatch(r"A(\d+)", coordinate)
                if match and 8 <= int(match[1]) <= 200 and value.strip():
                    # Label is fixed technical vocabulary, not a calculated input.
                    rows.append({"row": int(match[1]), "label": value.strip()})
            families[family] = {"sheet": sheet, "rows": rows}
    return {"schema_version": 1, "source_workbook_sha256": OFFICIAL_SHA, "families": families}


def technical_pdf_rows(text: str, allowed_labels: set[str]) -> list[dict]:
    """Extract ordered utilization/code only, after the technical table header.

    Unknown lines fail closed: excluded from public evidence, never exported as
    raw text. No descriptions, numeric values, file paths or customer headers.
    """
    labels = {normalize(label) for label in allowed_labels}
    labels.add(normalize("CONTRA-TESTA"))
    known_codes = set(MATERIALS) | {v.code for v in HARDWARE.values()} | {v.code for v in GLASSES.values()} | {"0"}
    lines = text.splitlines()
    start = next((n for n, line in enumerate(lines) if "UTILIZACAO" in normalize(line) and "CODIGO" in normalize(line)), None)
    if start is None:
        raise ValueError("Cabeçalho técnico não localizado.")
    rows = []
    for line in lines[start + 1:]:
        cells = re.split(r"\s{2,}", line.strip())
        if len(cells) < 3 or not re.fullmatch(r"\d+(?:[.,]\d+)?", cells[-1]):
            continue
        label = cells[0]
        if normalize(label) not in labels:
            continue
        code = cells[-4] if len(cells) >= 6 else cells[-2]
        if code not in known_codes:
            continue
        rows.append({"label": label, "code": code})
    if not rows:
        raise ValueError("Nenhuma linha técnica reconhecida.")
    return rows


def reference_order(pdf_dir: Path, order: dict) -> dict:
    """Export 12 page orders and technical sketch basenames; no private headers."""
    from pypdf import PdfReader
    cases = json.loads((ROOT / "api/tests/fixtures/op_golden_12_partial.json").read_text(encoding="utf-8"))["cases"]
    inputs = {c["id"]: c for c in json.loads((ROOT / "api/tests/fixtures/op_reference_inputs.json").read_text(encoding="utf-8"))["cases"]}
    readers, result = {}, []
    for case in cases:
        filename = case["source"]["filename"]
        if filename not in readers:
            readers[filename] = PdfReader(pdf_dir / filename)
        page = readers[filename].pages[case["source"]["page"] - 1]
        text = page.extract_text(extraction_mode="layout")
        family = "MAXIM_AR" if case["family"] == "MX" else case["family"]
        names = re.findall(r"Croquis\\([^\r\n]+?\.jpg)", text, re.I)
        _, expected_name = model_identity(inputs[case["id"]]["technical_input"], inputs[case["id"]]["finish_key"])
        if len(names) != 1 or names[0] != expected_name or any(c in names[0] for c in "\\/:"):
            raise ValueError("Descritor de croqui não reconhecido; revisar fonte privada.")
        result.append({"id": case["id"], "family": family, "source": case["source"],
                       "source_sha256": hashlib.sha256((pdf_dir / filename).read_bytes()).hexdigest(),
                       "model_basename": names[0],
                       "page_size_pt": [float(page.mediabox.width), float(page.mediabox.height)],
                       "rows": technical_pdf_rows(text, {r["label"] for r in order["families"][family]["rows"]})})
    return {"schema_version": 1, "scope": "ORDER_ONLY_NOT_FULL_PARITY", "cases": result}


def main() -> None:
    """CLI: --workbook --pdf-dir --order-output --reference-output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--pdf-dir", type=Path, required=True)
    parser.add_argument("--order-output", type=Path, required=True)
    parser.add_argument("--reference-output", type=Path, required=True)
    args = parser.parse_args()
    order = workbook_order(args.workbook)
    reference = reference_order(args.pdf_dir, order)
    for path, data in ((args.order_output, order), (args.reference_output, reference)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"families": len(order["families"]), "pages": len(reference["cases"]),
                      "technical_rows": sum(len(c["rows"]) for c in reference["cases"])}))


if __name__ == "__main__":
    main()
