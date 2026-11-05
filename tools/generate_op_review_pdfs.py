"""Private B2 review PDFs and sanitized technical divergence evidence.

No original PDF, client header, imported bitmap or manifest is published.
The public report contains only reference IDs, technical differences and checks.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pypdf import PdfReader, PdfWriter
import pymupdf
from api.app.production_images import ProductionImageManifest, ProductionImageStore
from api.app.production_layout import ProductionLayoutRequest, ProductionLayoutContext, prepare_production_layout
from api.app.production_schemas import ProductionOrderRequest
from api.app.production_pdf import render_production_pdf, pdf_model_headings, PdfReviewNote, pdf_number
from tools.compare_op_layout import build_report as layout_report
from tools.compare_op_golden import compare_case
from tools.inspect_op_pdf import inspect_pdf
from tools.compare_op_pdf_numeric import compare_numeric_reference

COMPANY = "00000000-0000-0000-0000-000000000001"


def classify_b1_differences(case: dict) -> list[dict]:
    """Classify explanations conservatively; unresolved engineering is not exonerated."""
    findings = []
    for row in case["reference_rows_without_engine_match"]:
        category = "INCOMPLETE_RECONSTRUCTED_INPUT" if row["label"].startswith("Arremate") else (
            "INPUT_SHUTTER_MODE_UNCONFIRMED" if "Divisor" in row["label"] else "POSSIBLE_ENGINEERING_OR_LEGACY_VARIANT")
        findings.append({"kind": "REFERENCE_ROW_ABSENT", "classification": category, **row})
    for row in case["engine_additions"]:
        category = "INPUT_SHUTTER_MODE_UNCONFIRMED" if row["role"].startswith("SHUTTER_") else "EXISTING_ENGINE_RULE_NOT_SHOWN_IN_REFERENCE"
        findings.append({"kind": "ENGINE_ADDITIONAL_ROW", "classification": category, **row})
    for row in case["code_differences"]:
        category = "LEGACY_IDENTIFICATION_ANOMALY" if row["pdf_code"] == "0" else "RECONSTRUCTED_OPTION_UNCONFIRMED"
        findings.append({"kind": "CODE_DIFFERENCE", "classification": category, **row})
    return findings


def reference_request(case: dict, number: int) -> ProductionLayoutRequest:
    """Anonymous technical reconstruction; never imports real client/work headers."""
    order = ProductionOrderRequest(company_id=COMPANY, order_id="CONFERENCIA-B2", items=[{
        "item_id": case["id"], "finish_key": case["finish_key"], "technical_input": case["technical_input"]}])
    context = ProductionLayoutContext(company_id=COMPANY, client_code="ANON",
        client_name="CLIENTE ANONIMIZADO", work_code="REF-B2", work_name="OBRA DE CONFERÊNCIA",
        item_labels=[{"item_id": case["id"], "label": f"{number:02d}"}])
    return ProductionLayoutRequest(production_order=order, context=context)


def _notes(case, differences, golden, numeric):
    source = f"{case['source']['filename']}, página {case['source']['page']}"
    notes = [PdfReviewNote(item_id=case["id"], classification="REFERÊNCIA PARCIAL",
                          message=f"{source}. Inputs reconstruídos; não se demonstrou equivalência técnica integral.")]
    for difference in differences:
        if difference["kind"] == "REFERENCE_ROW_ABSENT":
            text = f"Linha do PDF não presente na Engine: {difference['label']} / {difference['code']}."
            source_row = next((row for row in numeric["missing_reference_rows"] if row["label"] == difference["label"] and row["code"] == difference["code"]), None)
            if source_row:
                text += f" Quantidade impressa: {source_row['quantity']}."
                if source_row["measure_1"] is not None:
                    text += f" Medidas impressas: {source_row['measure_1']} / {source_row['measure_2']} mm."
        elif difference["kind"] == "ENGINE_ADDITIONAL_ROW":
            text = f"Linha adicional da Engine, posição {difference['engine_position']}: {difference['role']}."
        else:
            text = f"{difference['utilization']}: código PDF {difference['pdf_code']} / Engine {difference['engine_code']}."
        notes.append(PdfReviewNote(item_id=case["id"], classification=difference["classification"], message=text))
    for field in golden["fields"]:
        if field["status"] != "igual":
            notes.append(PdfReviewNote(item_id=case["id"], classification=field["reason"],
                         message=f"{field['field']}: PDF {field['pdf']} / Engine {field['engine']}. Não alterado pelo PDF."))
    for field in numeric["differences"]:
        notes.append(PdfReviewNote(item_id=case["id"], classification=field["classification"],
                      message=f"{field['label']} / {field['field']}: PDF {field['pdf_printed']} / Engine {pdf_number(field['engine'])}. Causa não homologada; não corrigida pela apresentação."))
    if numeric["unit_representation_reviews"]:
        notes.append(PdfReviewNote(item_id=case["id"], classification="UNIT_REPRESENTATION_REVIEW",
                     message="O PDF legado mostra consumíveis em metros totais do pedido. A B1 fornece mm por esquadria e contagem de conjuntos. Mantidas as duas grandezas explícitas, sem criar cálculo técnico de consumo na apresentação."))
    return tuple(notes)


def private_output_dir(path: Path) -> Path:
    """Reject repository destinations outside ignored .private; external roots allowed."""
    path = path.resolve()
    if path.is_relative_to(ROOT) and not path.is_relative_to(ROOT / ".private"):
        raise ValueError("PDFs/imagens de conferência no repositório exigem destino .private.")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _private_visual_pair(reference_path, reference_page, generated, output):
    """Rasterize side by side; redact original customer/path text in memory only."""
    from PIL import Image
    with pymupdf.open(reference_path) as source, pymupdf.open(stream=generated, filetype="pdf") as target:
        page = source[reference_page - 1]
        # Original references share the customer line around y=143pt. Use text
        # boxes rather than copying any customer strings into an audit report.
        for block in page.get_text("dict")["blocks"]:
            if block["type"] != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"]
                    if "Users" in text or ":\\" in text or ("Croquis" in text and ".jpg" in text):
                        page.add_redact_annot(pymupdf.Rect(span["bbox"]), fill=(1, 1, 1))
        page.add_redact_annot(pymupdf.Rect(18, 141, 352, 158), fill=(1, 1, 1))
        page.apply_redactions(images=0, graphics=0)
        left = page.get_pixmap(matrix=pymupdf.Matrix(1.2, 1.2), alpha=False)
        right = target[0].get_pixmap(matrix=pymupdf.Matrix(1.2, 1.2), alpha=False)
        a = Image.frombytes("RGB", (left.width, left.height), left.samples)
        b = Image.frombytes("RGB", (right.width, right.height), right.samples)
        pair = Image.new("RGB", (a.width + b.width + 12, max(a.height, b.height)), "white")
        pair.paste(a, (0, 0))
        pair.paste(b, (a.width + 12, 0))
        pair.save(output)


def generate_review_set(output_dir: Path, *, image_store=None, reference_dir: Path | None = None) -> dict:
    """Generate 12 reference PDFs plus FX; verify actual PDF cells/images/pages.

    Comparison files are private. Returned report excludes original headers and
    binary assets, and is suitable for public technical audit after review.
    """
    output = private_output_dir(output_dir)
    (output / "audits").mkdir(exist_ok=True)
    (output / "visual").mkdir(exist_ok=True)
    fixtures = ROOT / "api/tests/fixtures"
    inputs = json.loads((fixtures / "op_reference_inputs.json").read_text(encoding="utf-8"))["cases"]
    inputs_by_id = {case["id"]: case for case in inputs}
    golden = json.loads((fixtures / "op_golden_12_partial.json").read_text(encoding="utf-8"))["cases"]
    golden_by_id = {case["id"]: case for case in golden}
    b1 = layout_report(image_store)
    source_evidence = {case["id"]: case for case in json.loads((fixtures / "op_layout_reference_v1.json").read_text(encoding="utf-8"))["cases"]}
    numeric_evidence = {case["id"]: case for case in json.loads((fixtures / "op_pdf_numeric_reference_v1.json").read_text(encoding="utf-8"))["cases"]}
    all_images = None if image_store is None else {entry.sha256: image_store.read_verified(entry) for entry in image_store.manifest.entries}
    records, pdfs = [], []
    for number, case in enumerate(b1["cases"], 1):
        input_case = inputs_by_id[case["id"]]
        request = reference_request(input_case, number)
        layout = prepare_production_layout(request, image_store=image_store)
        differences = classify_b1_differences(case)
        comparison = compare_case(golden_by_id[case["id"]], input_case)
        numeric = compare_numeric_reference(case, numeric_evidence[case["id"]], layout)
        result = render_production_pdf(layout, image_store=image_store,
                  model_headings=pdf_model_headings(request), review_notes=_notes(case, differences, comparison, numeric))
        checks = inspect_pdf(result.content, result.audit, expected_images=all_images)
        if not checks["integrity_valid"]:
            raise ValueError(f"Integridade do PDF {case['id']}: {checks['errors']}")
        filename = case["id"] + ".pdf"
        (output / filename).write_bytes(result.content)
        (output / "audits" / (case["id"] + ".json")).write_text(result.audit.model_dump_json(indent=2) + "\n", encoding="utf-8")
        visual = "REFERENCE_NOT_AVAILABLE"
        if reference_dir is not None and (reference_dir / case["source"]["filename"]).is_file():
            original = reference_dir / case["source"]["filename"]
            if hashlib.sha256(original.read_bytes()).hexdigest() != source_evidence[case["id"]]["source_sha256"]:
                raise ValueError("PDF original difere do SHA da referência B1.")
            _private_visual_pair(original, case["source"]["page"], result.content, output / "visual" / (case["id"] + ".png"))
            visual = "PAIR_GENERATED_FOR_VISUAL_AUDIT"
        pdfs.append(result.content)
        records.append({"id": case["id"], "family": input_case["technical_input"]["family"], "source": case["source"],
            "pdf_filename": filename, "pdf_sha256": result.audit.pdf_sha256, "checks": checks,
            "comparison_status": "NOT_EQUIVALENT_PENDING_TECHNICAL_AND_VISUAL_AUDIT",
            "reference_pages": 1, "visual_status": visual,
            "differences": differences, "numeric_reference_comparison": numeric,
            "golden_numeric_differences": [f for f in comparison["fields"] if f["status"] != "igual"],
            "missing_inputs": input_case["missing_inputs"],
            "presentation_differences": ["REVIEW_MARK_AND_FINDINGS_ANNEX", "EXPLICIT_UNITS_AND_CONSUMPTION", "TEMPLATE_FONT_SPACING_AND_SECTION_HEADERS", "CUSTOMER_HEADERS_ANONYMIZED"],
            "fabrication_allowed": False})
    fx = {"id": "FX-PROPRIO", "finish_key": "BRANCO", "technical_input": {"family": "FX", "width_mm": 1200, "height_mm": 1000}}
    request = reference_request(fx, 13)
    result = render_production_pdf(prepare_production_layout(request, image_store=image_store), image_store=image_store,
                                  model_headings=pdf_model_headings(request), review_notes=(PdfReviewNote(item_id=fx["id"], classification="SEM PDF ORIGINAL FX", message="Caso próprio. Não demonstra paridade com OP real de fábrica."),))
    checks = inspect_pdf(result.content, result.audit, expected_images=all_images)
    if not checks["integrity_valid"]:
        raise ValueError("Integridade do PDF FX inválida.")
    (output / "FX-PROPRIO.pdf").write_bytes(result.content)
    (output / "audits/FX-PROPRIO.json").write_text(result.audit.model_dump_json(indent=2) + "\n", encoding="utf-8")
    writer = PdfWriter()
    for content in pdfs:
        writer.append(PdfReader(BytesIO(content)))
    writer.add_metadata({"/Title": "OP — 12 casos de conferência B2", "/Author": "Software Esquadrias"})
    with (output / "OP-REFERENCIAS-12.pdf").open("wb") as handle:
        writer.write(handle)
    with ZipFile(output / "OP-B2-CONFERENCIA.zip", "w", ZIP_DEFLATED) as bundle:
        for filename in [r["pdf_filename"] for r in records] + ["FX-PROPRIO.pdf", "OP-REFERENCIAS-12.pdf"]:
            bundle.write(output / filename, filename)
    report = {"scope": "B2_REVIEW_NOT_HOMOLOGATED_NOT_FOR_MANUFACTURING", "cases": records,
       "fx_own_case": {"id": fx["id"], "family": "FX", "pdf_filename": "FX-PROPRIO.pdf", "checks": checks, "reference": None},
       "reference_cases": 12, "reference_rows_preserved": sum(r["checks"]["rows"] for r in records),
       "b1_difference_counts": dict(Counter(d["kind"] for r in records for d in r["differences"])),
       "classification_counts": dict(Counter(d["classification"] for r in records for d in r["differences"])),
       "numeric_comparison_counts": dict(sum((Counter(r["numeric_reference_comparison"]["counts"]) for r in records), Counter())),
       "numeric_difference_classifications": dict(Counter(d["classification"] for r in records for d in r["numeric_reference_comparison"]["differences"])),
       "reference_pdf_pages_generated": sum(r["checks"]["pages"] for r in records),
       "private_assets_available": image_store is not None, "manufacturing_allowed": False}
    (output / "pdf-review-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--reference-dir", type=Path)
    parser.add_argument("--public-report", type=Path)
    args = parser.parse_args()
    store = None if args.manifest is None else ProductionImageStore(args.manifest.parent,
                 ProductionImageManifest.model_validate_json(args.manifest.read_text(encoding="utf-8")))
    report = generate_review_set(args.output_dir, image_store=store, reference_dir=args.reference_dir)
    if args.public_report:
        args.public_report.parent.mkdir(parents=True, exist_ok=True)
        args.public_report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("reference_cases", "reference_rows_preserved", "b1_difference_counts", "reference_pdf_pages_generated", "private_assets_available", "manufacturing_allowed")}))


if __name__ == "__main__":
    main()
