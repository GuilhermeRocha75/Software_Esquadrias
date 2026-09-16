"""Inventaria evidencias tecnicas de um RAR historico ja extraido.

O script nao emite nomes de arquivos PDF, clientes, enderecos, contatos,
locais ou valores comerciais. PDFs recebem um ID anonimo derivado do SHA-256.

Dependencia para leitura de PDF:
    python -m pip install pypdf

Uso:
    python tools/audit_maxim_ar_historical_archive.py <diretorio-extraido> --pretty
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from pypdf import PdfReader
except ImportError as error:  # pragma: no cover - depende do ambiente de auditoria
    raise SystemExit("Instale a dependencia de auditoria: python -m pip install pypdf") from error

try:
    from audit_maxim_ar_phase3a import inspect_workbook
except ModuleNotFoundError:  # permite importar como tools.audit_...
    from tools.audit_maxim_ar_phase3a import inspect_workbook


DIMENSIONS_RE = re.compile(
    r"(?P<width>\d+(?:[.,]\d+)?)\s*mm\s+"
    r"(?P<height>\d+(?:[.,]\d+)?)\s*mm\s+"
    r"(?P<quantity>\d+(?:[.,]\d+)?)\s*(?:pc|un|p[cç]s?)\b",
    re.IGNORECASE,
)
FLAG_CODE_RE = re.compile(r"BANDEIRA\s+(INFERIOR|SUPERIOR)\s*\((\d)(\d)\)")
MATERIAL_TERMS = (
    "ALUM10238",
    "ALUM15338",
    "AC0708",
    "AC0002",
    "ACB606",
    "AC0312",
)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(ascii_text.upper().split())


def is_maxim_ar(value: str) -> bool:
    return re.search(r"\bMAXI(?:M)?\s*-?\s*AR\b", value) is not None


def technical_description(line: str) -> str | None:
    clean = " ".join(line.split())
    upper = normalized(clean)
    if not is_maxim_ar(upper):
        return None
    if upper.startswith("ITEM "):
        return None
    upper = re.sub(
        r"^.*\.(?:JPG|JPEG|PNG)(?=JANELA|PORTA|CONJUNTO)", "", upper
    )
    starts = [upper.find(word) for word in ("JANELA", "PORTA", "CONJUNTO") if word in upper]
    if not starts:
        return None
    # A normalizacao tambem garante que o texto emitido nao carregue prefixos
    # de campos comerciais do PDF.
    return upper[min(starts) :]


def features(description: str) -> dict[str, Any]:
    leaf_match = re.search(r"\b([1-8])\s+FOLHAS?\b", description)
    codes = [
        {
            "position": match.group(1),
            "vertical_transoms": int(match.group(2)),
            "horizontal_transoms": int(match.group(3)),
        }
        for match in FLAG_CODE_RE.finditer(description)
    ]
    return {
        "leaves": int(leaf_match.group(1)) if leaf_match else None,
        "screen": "TELA" in description,
        "lower_flag": "BANDEIRA INFERIOR" in description,
        "upper_flag": "BANDEIRA SUPERIOR" in description or "BANDEIRAS" in description,
        "multiple_leaves": bool(leaf_match and int(leaf_match.group(1)) > 1),
        "explicit_flag_grid_codes": codes,
        "separate_module_wording": "MODULO" in description,
        "external_muntin": "PINAZIO" in description,
    }


def analyze_pdfs(root: Path) -> dict[str, Any]:
    pdfs = sorted(root.rglob("*.pdf"))
    pages = 0
    text_pages = 0
    errors = Counter()
    relevant_documents: set[str] = set()
    unique_document_hashes: set[str] = set()
    material_hits = Counter({term: 0 for term in MATERIAL_TERMS})
    items: list[dict[str, Any]] = []
    description_counts = Counter()

    for path in pdfs:
        full_hash = file_sha256(path)
        document_id = f"PDF-{full_hash[:12].upper()}"
        unique_document_hashes.add(full_hash)
        try:
            reader = PdfReader(path)
            page_texts = []
            for page in reader.pages:
                pages += 1
                text = page.extract_text() or ""
                if text.strip():
                    text_pages += 1
                page_texts.append(text)
        except Exception as error:  # pragma: no cover - depende do corpus
            errors[type(error).__name__] += 1
            continue

        text = "\n".join(page_texts)
        upper_text = normalized(text)
        for term in MATERIAL_TERMS:
            material_hits[term] += upper_text.count(term)

        lines = text.splitlines()
        item_ordinal = 0
        for index, line in enumerate(lines):
            description = technical_description(line)
            if description is None:
                continue
            item_ordinal += 1
            relevant_documents.add(document_id)
            description_counts[description] += 1
            dimension_match = None
            for candidate in lines[index + 1 : index + 10]:
                dimension_match = DIMENSIONS_RE.search(normalized(candidate))
                if dimension_match:
                    break
            item: dict[str, Any] = {
                "document_id": document_id,
                "technical_item": item_ordinal,
                "description": description,
                **features(description),
            }
            if dimension_match:
                item.update(
                    {
                        "width_mm": dimension_match.group("width").replace(",", "."),
                        "height_mm": dimension_match.group("height").replace(",", "."),
                        "quantity": dimension_match.group("quantity").replace(",", "."),
                    }
                )
            items.append(item)

    feature_counts = Counter()
    leaf_counts = Counter()
    grid_codes = Counter()
    for item in items:
        if item["leaves"] is not None:
            leaf_counts[str(item["leaves"])] += 1
        for key in (
            "screen",
            "lower_flag",
            "upper_flag",
            "multiple_leaves",
            "separate_module_wording",
            "external_muntin",
        ):
            if item[key]:
                feature_counts[key] += 1
        for code in item["explicit_flag_grid_codes"]:
            grid_codes[
                f"{code['position']}:{code['vertical_transoms']}{code['horizontal_transoms']}"
            ] += 1

    return {
        "documents": len(pdfs),
        "unique_document_hashes": len(unique_document_hashes),
        "pages": pages,
        "pages_with_text": text_pages,
        "read_errors": dict(errors),
        "documents_with_maxim_ar": len(relevant_documents),
        "maxim_ar_item_occurrences": len(items),
        "unique_maxim_ar_descriptions": len(description_counts),
        "feature_counts": dict(sorted(feature_counts.items())),
        "leaf_counts": dict(sorted(leaf_counts.items())),
        "flag_grid_codes": dict(sorted(grid_codes.items())),
        "material_code_occurrences": dict(material_hits),
        "technical_items": items,
        "privacy": "Somente descricao, dimensoes e opcoes tecnicas; identificador PDF por hash.",
    }


def analyze_croquis(root: Path) -> dict[str, Any]:
    image_extensions = {".jpg", ".jpeg", ".png", ".jfif", ".webp"}
    images = [path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in image_extensions]
    maxim = []
    content_hashes = set()
    descriptions = Counter()
    grid_codes = Counter()
    feature_counts = Counter()
    for path in images:
        name = normalized(path.stem)
        if not is_maxim_ar(name):
            continue
        maxim.append(path)
        content_hashes.add(file_sha256(path))
        descriptions[name] += 1
        item_features = features(name)
        for key, value in item_features.items():
            if key not in {"explicit_flag_grid_codes", "leaves"} and value:
                feature_counts[key] += 1
        for code in item_features["explicit_flag_grid_codes"]:
            grid_codes[
                f"{code['position']}:{code['vertical_transoms']}{code['horizontal_transoms']}"
            ] += 1
    return {
        "images": len(images),
        "maxim_ar_images": len(maxim),
        "distinct_maxim_ar_image_hashes": len(content_hashes),
        "unique_technical_names": len(descriptions),
        "feature_counts": dict(sorted(feature_counts.items())),
        "flag_grid_codes": dict(sorted(grid_codes.items())),
    }


def analyze_historical_workbooks(root: Path) -> list[dict[str, Any]]:
    workbooks = []
    for path in sorted(root.rglob("*.xlsm")):
        size = path.stat().st_size
        digest = file_sha256(path)
        if size < 1024:
            workbooks.append(
                {
                    "snapshot_id": digest[:12].upper(),
                    "sha256": digest.upper(),
                    "size_bytes": size,
                    "classification": "owner_lock_not_workbook",
                }
            )
            continue
        audit = inspect_workbook(path)
        orcs = audit.get("orcs", {})
        workbooks.append(
            {
                "snapshot_id": digest[:12].upper(),
                "sha256": digest.upper(),
                "size_bytes": size,
                "classification": "historical_snapshot",
                "sheet_count": len(audit.get("sheets", [])),
                "mx_formula_hash": audit.get("formula_hashes", {}).get("MX"),
                "orcs": {
                    key: orcs.get(key)
                    for key in (
                        "total_mx",
                        "leaves",
                        "systems",
                        "orientations",
                        "feature_counts",
                        "feature_combinations",
                        "relevant_row_ids",
                        "privacy",
                    )
                },
            }
        )
    return workbooks


def inventory(root: Path) -> dict[str, Any]:
    files = [path for path in root.rglob("*") if path.is_file()]
    extensions = Counter(path.suffix.lower() or "[no_extension]" for path in files)
    return {
        "files": len(files),
        "bytes": sum(path.stat().st_size for path in files),
        "extensions": dict(sorted(extensions.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("extracted_directory", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    root = args.extracted_directory.resolve()
    if not root.is_dir():
        raise SystemExit(f"Diretorio nao encontrado: {root}")
    report = {
        "inventory": inventory(root),
        "pdfs": analyze_pdfs(root),
        "croquis": analyze_croquis(root),
        "historical_workbooks": analyze_historical_workbooks(root),
    }
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    print()


if __name__ == "__main__":
    main()
