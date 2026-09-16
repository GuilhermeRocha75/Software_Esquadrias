"""Inventário sanitizado das fontes GR; não imprime nomes ou textos de clientes.

Uso: python tools/audit_gr_sources.py WORKBOOK.xlsm HISTORY_DIR
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

from pypdf import PdfReader

from audit_maxim_ar_phase3a import (
    orcs_rows,
    row_number,
    shared_strings,
    sheet_cells,
    sheet_targets,
    sha256,
)
from zipfile import ZipFile

OFFICIAL_SHA = "96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160"
GR_PATTERN = re.compile(r"(?<![A-Z])GR(?![A-Z])")
HISTORICAL_PATTERN = re.compile(r"\b(?:DE\s+GIRO|ABERTURA\s+INTERNA|ABERTURA\s+EXTERNA|OSCILO.GIRO)\b", re.I)
DIMENSIONS_PATTERN = re.compile(r"\b\d{3,4}\s*mm\s+\d{3,4}\s*mm\b", re.I)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook", type=Path)
    parser.add_argument("history", type=Path)
    args = parser.parse_args()
    digest = sha256(args.workbook)
    if digest != OFFICIAL_SHA:
        raise SystemExit("ERRO: SHA-256 do XLSM não corresponde à fonte oficial")

    with ZipFile(args.workbook) as archive:
        targets = sheet_targets(archive)
        strings = shared_strings(archive)
        gr_counts = {}
        gr_int_formula_count = 0
        for sheet, target in targets.items():
            count = 0
            for coordinate, value, formula in sheet_cells(archive, target, strings):
                count += bool(GR_PATTERN.search(value.upper()))
                if sheet == "GR_INT" and formula:
                    gr_int_formula_count += 1
            gr_counts[sheet] = count
        rows = orcs_rows(archive, targets["ORCS"], strings)
        gr_rows = [(row, values) for row, values in rows.items() if values.get("X") == "GR"]

    pdfs = list(args.history.rglob("*.pdf"))
    pdf_hits = 0
    pdf_errors = 0
    examples = []
    for pdf in pdfs:
        try:
            body = "\n".join(page.extract_text() or "" for page in PdfReader(pdf).pages)
        except Exception:
            pdf_errors += 1
            continue
        matches = HISTORICAL_PATTERN.findall(body)
        if matches:
            pdf_hits += 1
            if len(examples) < 12:
                examples.append({
                    "anonymous_case": pdf_hits,
                    "technical_terms": sorted(set(term.upper() for term in matches)),
                    "dimensions": DIMENSIONS_PATTERN.findall(body)[:5],
                })

    result = {
        "official_xlsm_sha256": digest,
        "gr_occurrences_by_sheet": {key: value for key, value in gr_counts.items() if value},
        "gr_int_formula_count": gr_int_formula_count,
        "orcs_gr_rows": len(gr_rows),
        "orcs_leaf_systems": Counter(values.get("H", "") for _, values in gr_rows),
        "orcs_leaf_counts": Counter(values.get("G", "") for _, values in gr_rows),
        "orcs_applications": Counter(values.get("I", "") for _, values in gr_rows),
        "orcs_panel_modes": Counter(values.get("R", "") for _, values in gr_rows),
        "orcs_screen_modes": Counter(values.get("O", "") for _, values in gr_rows),
        "orcs_flagged_rows": sum(
            values.get("AA", "0") not in ("", "0") or values.get("AB", "0") not in ("", "0")
            for _, values in gr_rows
        ),
        "history_pdf_count": len(pdfs),
        "history_pdf_matches": pdf_hits,
        "history_pdf_parse_errors": pdf_errors,
        "history_anonymous_examples": examples,
        "privacy": "Nenhum nome, contato, endereco, codigo de cliente ou caminho individual de PDF emitido.",
    }
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
