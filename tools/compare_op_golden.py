"""Reproducible partial PDF comparison. No private source files are read."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.app.production_schemas import ProductionOrderRequest
from api.app.production_service import build_production_order

FIXTURES = ROOT / "api/tests/fixtures"
COMPANY = "00000000-0000-0000-0000-000000000001"


def compare_case(case: dict, reconstruction: dict) -> dict:
    """Compare every supplied assertion by field, retaining both values.

    Status is input insuficiente when reference-specific configuration is
    missing, even if geometric assertions match under the stated hypothesis.
    Numeric tolerance 1e-6 covers only transcription precision, never counts
    rounded to integers. Supplemental assertions come from the repository spec.
    """
    request = ProductionOrderRequest.model_validate({
        "company_id": COMPANY, "order_id": "ANONYMIZED-PARTIAL-REFERENCE",
        "items": [{"item_id": case["id"], "finish_key": reconstruction["finish_key"],
                   "technical_input": reconstruction["technical_input"]}],
    })
    document = build_production_order(request)
    item = document.items[0]
    rows = []
    roles = {
        "frame_width": {"FRAME_HORIZONTAL", "FRAME_WIDTH"},
        "frame_height": {"FRAME_VERTICAL", "FRAME_HEIGHT"},
        "leaf_width": {"LEAF_HORIZONTAL", "LEAF_WIDTH"},
        "glass": {"GLASS_PANEL"}, "screen": {"SCREEN_MESH"},
        "panel": {"PANEL_FILL"}, "slat": {"SHUTTER_SLAT"},
    }

    def check(section, expected, origin):
        candidates = [line for line in item.lines if line.utilization in roles[section]]
        # Multiple matches are ambiguous; never silently take the first row.
        line = candidates[0] if len(candidates) == 1 else None
        for field, pdf in expected.items():
            actual = getattr(line, field) if line is not None else None
            equal = actual == pdf
            if isinstance(pdf, (float, int)) and isinstance(actual, (float, int)):
                equal = abs(actual - pdf) <= 1e-6
            status = "igual" if equal else ("input insuficiente" if actual is None else "divergente")
            reason = "MATCH" if equal else ("MISSING_TECHNICAL_DATA" if actual is None else "UNEXPLAINED_ENGINE_PDF_DIFFERENCE")
            if section == "slat" and field == "quantity_total" and not equal and actual is not None:
                reason = "EXISTING_ENGINE_PHYSICAL_CORRECTION_CONDITIONAL_ON_SHUTTER_INPUT"
            rows.append({"field": f"{section}.{field}", "pdf": pdf, "engine": actual,
                         "status": status, "reason": reason, "source": case["source"], "origin": origin})

    for section, assertions in case["assertions"].items():
        check(section, assertions, "op_golden_12_partial.json")
    supplemental = {
        "OP-GOLDEN-01": {"screen": {"width_mm": 846, "height_mm": 1294, "quantity_total": 1}},
        "OP-GOLDEN-03": {"panel": {"quantity_total": 12.8357143}},
        "OP-GOLDEN-05": {"frame_height": {"final_length_mm": 1410, "cut_length_mm": 1415, "quantity_total": 2},
                         "slat": {"cut_length_mm": 1346, "quantity_total": 40.25}},
        "OP-GOLDEN-12": {"frame_height": {"final_length_mm": 980, "cut_length_mm": 985, "quantity_total": 2},
                         "slat": {"cut_length_mm": 933, "quantity_total": 59}},
    }
    for section, assertions in supplemental.get(case["id"], {}).items():
        check(section, assertions, "docs/ORDEM_PRODUCAO_V1.md")
    counts = Counter(row["status"] for row in rows)
    status = "input insuficiente" if reconstruction["missing_inputs"] or counts["input insuficiente"] else (
        "divergente" if counts["divergente"] else "igual")
    return {"id": case["id"], "source": case["source"], "family": item.family,
            "status": status, "scope": "PARTIAL_RECONSTRUCTED_INPUT", "engine_version": item.engine_version,
            "assumptions": reconstruction["assumptions"], "missing_inputs": reconstruction["missing_inputs"],
            "technical_input": reconstruction["technical_input"], "fields": rows,
            "validations": [v.model_dump(mode="json") for v in document.validations]}


def build_report() -> dict:
    """Load the 12 anonymized references and return a full audit value report."""
    cases = json.loads((FIXTURES / "op_golden_12_partial.json").read_text(encoding="utf-8"))["cases"]
    inputs = json.loads((FIXTURES / "op_reference_inputs.json").read_text(encoding="utf-8"))["cases"]
    mapping = {case["id"]: case for case in inputs}
    if len(mapping) != len(cases) or set(mapping) != {case["id"] for case in cases}:
        raise ValueError("Reconstruções e referências devem ter os mesmos IDs únicos.")
    results = [compare_case(case, mapping[case["id"]]) for case in cases]
    return {"scope": "PARTIAL_NOT_HOMOLOGATED", "case_counts": dict(Counter(case["status"] for case in results)),
            "field_counts": dict(Counter(row["status"] for case in results for row in case["fields"])),
            "cases": results}


def report_markdown(report: dict) -> str:
    """Render case summary and every PDF/Engine field value, without private data."""
    lines = ["# OP Fase A — comparação parcial reproduzível", "",
             "**Não homologado.** Inputs reconstruídos e hipóteses estão em `op_reference_inputs.json` e no relatório JSON.",
             "A igualdade é restrita aos campos transcritos. Não implica paridade da OP completa.", "",
             f"Casos: `{report['case_counts']}`. Campos: `{report['field_counts']}`.", "",
             "| Caso | Referência | Estado |", "| --- | --- | --- |"]
    for case in report["cases"]:
        lines.append(f"| {case['id']} | {case['source']['filename']} p{case['source']['page']} | {case['status']} |")
    for case in report["cases"]:
        lines += ["", f"## {case['id']} — {case['source']['filename']} p{case['source']['page']}", "",
                  f"Engine: `{case['engine_version']}`. Estado: **{case['status']}**.", ""]
        lines += [f"- {note}" for note in case["assumptions"] + case["missing_inputs"]]
        lines += ["", "| Campo | PDF | Engine | Estado / motivo |", "| --- | --- | --- | --- |"]
        lines += [f"| {r['field']} | {r['pdf']} | {r['engine']} | {r['status']} / {r['reason']} |" for r in case["fields"]]
    return "\n".join(lines) + "\n"


def main() -> None:
    """CLI: --output-dir writes anonymized JSON/Markdown; otherwise stdout summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    report = build_report()
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "op_golden_comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (args.output_dir / "op_golden_comparison.md").write_text(report_markdown(report), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("scope", "case_counts", "field_counts")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
