"""Extract whitelisted manufacturing numbers only from the hashed OP PDFs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pypdf import PdfReader
from api.app import engine_bridge
from esquadrias_engine.catalog import MATERIALS, normalize
from tools.audit_op_layout_sources import technical_pdf_rows


def numeric_reference(reference_dir: Path) -> dict:
    """Export source row identifiers and printed decimals; never customer headers."""
    source = json.loads((ROOT / "api/tests/fixtures/op_layout_reference_v1.json").read_text(encoding="utf-8"))["cases"]
    cases, readers = [], {}
    for case in source:
        path = reference_dir / case["source"]["filename"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != case["source_sha256"]:
            raise ValueError("Fonte PDF difere da referência B1.")
        if path.name not in readers:
            readers[path.name] = PdfReader(path)
        text = readers[path.name].pages[case["source"]["page"] - 1].extract_text(extraction_mode="layout")
        allowed = {row["label"] for row in case["rows"]}
        if technical_pdf_rows(text, allowed) != case["rows"]:
            raise ValueError("Sequência técnica difere da evidência B1.")
        rows = []
        started = False
        for line in text.splitlines():
            if "UTILIZACAO" in normalize(line) and "CODIGO" in normalize(line):
                started = True
                continue
            if not started:
                continue
            cells = re.split(r"\s{2,}", line.strip())
            if len(cells) < 3 or not re.fullmatch(r"\d+(?:[.,]\d+)?", cells[-1]) or cells[0] not in allowed:
                continue
            code = cells[-4] if len(cells) >= 6 else cells[-2]
            if not any(r["label"] == cells[0] and r["code"] == code for r in case["rows"]):
                continue
            a, b = (cells[-3], cells[-2]) if len(cells) >= 6 else (None, None)
            if any(v is not None and not re.fullmatch(r"\d+(?:[.,]\d+)?", v) for v in (a, b)):
                raise ValueError("Medida impressa não numérica; revisão privada necessária.")
            kind = "SURFACE" if normalize(cells[0]).startswith(("VIDRO", "TELAS")) else "LINEAR"
            if a is None:
                kind = "CONSUMPTION" if code in MATERIALS and MATERIALS[code].unit == "m" else "UNIT"
            rows.append({"label": cells[0], "code": code, "kind": kind,
                         "measure_1": a, "measure_2": b, "quantity": cells[-1]})
        if [{"label": r["label"], "code": r["code"]} for r in rows] != case["rows"]:
            raise ValueError("Extração numérica não cobre todas as linhas técnicas reconhecidas.")
        cases.append({"id": case["id"], "source": case["source"], "source_sha256": case["source_sha256"], "rows": rows})
    return {"schema_version": 1, "scope": "PRINTED_TECHNICAL_NUMBERS_ONLY_NO_CLIENT_DATA", "cases": cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = numeric_reference(args.reference_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"cases": len(data["cases"]), "technical_rows": sum(len(c["rows"]) for c in data["cases"])}))


if __name__ == "__main__":
    main()
