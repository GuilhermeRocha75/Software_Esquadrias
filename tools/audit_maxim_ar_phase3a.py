"""Auditoria reproduzivel e sanitizada do legado Maxim-Ar (Fase 3A).

Le um XLSM/XLSX diretamente como OpenXML, sem abrir ou modificar o arquivo.
A saida JSON contem somente estatisticas, formulas, catalogo e identificadores
tecnicos de linha ORCS; campos de cliente, nome, item e local nunca sao emitidos.

Uso:
    python tools/audit_maxim_ar_phase3a.py arquivo.xlsm
    python tools/audit_maxim_ar_phase3a.py arquivo.xlsm --compare snapshot.tmp
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile
import zlib
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"x": MAIN_NS, "r": OFFICE_REL_NS}
CELL_RE = re.compile(r"^([A-Z]+)([1-9][0-9]*)$")
NUMBER_RE = re.compile(r"[-+]?\d+(?:[.,]\d+)?")

SEARCH_TERMS = (
    "AC0708",
    "ACB606",
    "AC0002",
    "AC0312",
    "ALUM10238",
    "ALUM15338",
    "BORRACHA",
    "VEDA",
    "CALCO",
    "CALÇO",
    "TRAVESSA",
)

# ORCS tem um contrato comum entre familias. Em MX, R e U sao campos
# reaproveitados: reforco estrutural e modo de modulo, respectivamente.
TECHNICAL_COLUMNS = {
    "D": "width_mm",
    "E": "height_mm",
    "F": "order_quantity",
    "G": "leaves",
    "H": "system",
    "I": "orientation",
    "K": "glass",
    "O": "screen",
    "P": "closing",
    "Q": "cremona",
    "R": "structural_reinforcement",
    "U": "module_mode",
    "V": "cota_a",
    "W": "cota_b",
    "Y": "cota_d",
    "Z": "cota_e",
    "AA": "lower_flag_height_mm",
    "AB": "upper_flag_height_mm",
    "AC": "cota_i",
    "AE": "cota_k",
    "AF": "leaf_horizontal_transoms",
    "AG": "leaf_vertical_transoms",
    "AH": "lower_vertical_transoms",
    "AI": "lower_horizontal_transoms",
    "AJ": "upper_vertical_transoms",
    "AK": "upper_horizontal_transoms",
    "AO": "stored_cost",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def column_label(coordinate: str) -> str:
    match = CELL_RE.match(coordinate)
    if match is None:
        raise ValueError(f"Coordenada invalida: {coordinate}")
    return match.group(1)


def row_number(coordinate: str) -> int:
    match = CELL_RE.match(coordinate)
    if match is None:
        raise ValueError(f"Coordenada invalida: {coordinate}")
    return int(match.group(2))


def shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return [
        "".join(node.text or "" for node in item.findall(".//x:t", NS))
        for item in root.findall("x:si", NS)
    ]


def sheet_targets(archive: zipfile.ZipFile) -> dict[str, str]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in relationships.findall(f"{{{REL_NS}}}Relationship")
    }
    result: dict[str, str] = {}
    for sheet in workbook.findall("x:sheets/x:sheet", NS):
        relationship_id = sheet.attrib[f"{{{OFFICE_REL_NS}}}id"]
        target = targets[relationship_id].lstrip("/")
        if not target.startswith("xl/"):
            target = str(PurePosixPath("xl") / target)
        result[sheet.attrib["name"]] = target
    return result


def cell_value(cell: ET.Element, strings: list[str]) -> str:
    cell_type = cell.attrib.get("t", "")
    value = cell.find("x:v", NS)
    raw = value.text if value is not None and value.text is not None else ""
    if cell_type == "s" and raw:
        return strings[int(raw)]
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//x:is//x:t", NS))
    if cell_type == "b":
        return "TRUE" if raw == "1" else "FALSE"
    return raw


def sheet_cells(
    archive: zipfile.ZipFile, target: str, strings: list[str]
) -> Iterable[tuple[str, str, str]]:
    root = ET.fromstring(archive.read(target))
    for cell in root.findall(".//x:sheetData/x:row/x:c", NS):
        coordinate = cell.attrib["r"]
        formula_node = cell.find("x:f", NS)
        formula = formula_node.text or "" if formula_node is not None else ""
        yield coordinate, cell_value(cell, strings), formula


def numeric(value: str) -> float:
    if not value:
        return 0.0
    try:
        return float(value.replace(",", "."))
    except ValueError:
        match = NUMBER_RE.search(value)
        return float(match.group(0).replace(",", ".")) if match else 0.0


def normalized_text(value: str) -> str:
    return " ".join(value.upper().strip().split())


def is_nonzero(value: str) -> bool:
    return bool(value.strip()) and numeric(value) != 0


def orcs_rows(
    archive: zipfile.ZipFile, target: str, strings: list[str]
) -> dict[int, dict[str, str]]:
    rows: dict[int, dict[str, str]] = {}
    for coordinate, value, _formula in sheet_cells(archive, target, strings):
        row = row_number(coordinate)
        if row == 1:
            continue
        column = column_label(coordinate)
        if column == "X" or column in TECHNICAL_COLUMNS:
            rows.setdefault(row, {})[column] = value
    return rows


def count(counter: Counter[str], key: str) -> None:
    counter[key] += 1


def analyze_orcs(rows: dict[int, dict[str, str]]) -> dict[str, Any]:
    mx = [(row_id, row) for row_id, row in rows.items() if normalized_text(row.get("X", "")) == "MX"]
    leaves: Counter[str] = Counter()
    systems: Counter[str] = Counter()
    orientations: Counter[str] = Counter()
    combinations: Counter[str] = Counter()
    flag_names = (
        "af_nonzero",
        "ag_nonzero",
        "lower_flag",
        "upper_flag",
        "any_flag",
        "multiple_leaves",
        "screen",
        "separate_modules",
        "structural_reinforcement",
        "lower_vertical_transom",
        "lower_horizontal_transom",
        "upper_vertical_transom",
        "upper_horizontal_transom",
        "complex_flags",
        "separate_with_transoms",
    )
    flags = Counter({name: 0 for name in flag_names})
    relevant_ids: dict[str, list[int]] = {
        "af_nonzero": [],
        "ag_nonzero": [],
        "complex_flags": [],
        "separate_with_transoms": [],
        "structural_reinforcement": [],
    }
    technical_cases: list[dict[str, Any]] = []

    for row_id, row in mx:
        leaf_count = int(numeric(row.get("G", "")))
        leaves[str(leaf_count)] += 1
        system = "DESIGN" if "DESIGN" in normalized_text(row.get("H", "")) else (
            "PRIME" if "PRIME" in normalized_text(row.get("H", "")) else "OTHER_OR_BLANK"
        )
        systems[system] += 1
        orientation = normalized_text(row.get("I", "")) or "BLANK"
        orientations[orientation] += 1

        af = is_nonzero(row.get("AF", ""))
        ag = is_nonzero(row.get("AG", ""))
        lower = is_nonzero(row.get("AA", ""))
        upper = is_nonzero(row.get("AB", ""))
        lower_v = is_nonzero(row.get("AH", ""))
        lower_h = is_nonzero(row.get("AI", ""))
        upper_v = is_nonzero(row.get("AJ", ""))
        upper_h = is_nonzero(row.get("AK", ""))
        any_flag = lower or upper
        any_flag_transom = lower_v or lower_h or upper_v or upper_h
        multiple = leaf_count > 1
        screen = "SEM TELA" not in normalized_text(row.get("O", "")) and bool(row.get("O", "").strip())
        separate = "SEPARAD" in normalized_text(row.get("U", ""))
        reinforcement_text = normalized_text(row.get("R", ""))
        reinforced = bool(reinforcement_text) and "SEM REFOR" not in reinforcement_text
        complex_flag = any_flag and (multiple or any_flag_transom)
        separate_transom = separate and any_flag_transom

        for key, enabled in {
            "af_nonzero": af,
            "ag_nonzero": ag,
            "lower_flag": lower,
            "upper_flag": upper,
            "any_flag": any_flag,
            "multiple_leaves": multiple,
            "screen": screen,
            "separate_modules": separate,
            "structural_reinforcement": reinforced,
            "lower_vertical_transom": lower_v,
            "lower_horizontal_transom": lower_h,
            "upper_vertical_transom": upper_v,
            "upper_horizontal_transom": upper_h,
            "complex_flags": complex_flag,
            "separate_with_transoms": separate_transom,
        }.items():
            if enabled:
                flags[key] += 1

        if af:
            relevant_ids["af_nonzero"].append(row_id)
        if ag:
            relevant_ids["ag_nonzero"].append(row_id)
        if complex_flag:
            relevant_ids["complex_flags"].append(row_id)
        if separate_transom:
            relevant_ids["separate_with_transoms"].append(row_id)
        if reinforced:
            relevant_ids["structural_reinforcement"].append(row_id)

        combination = "+".join(
            key
            for key, enabled in (
                ("AF", af),
                ("AG", ag),
                ("FLAG", any_flag),
                ("MULTI", multiple),
                ("SCREEN", screen),
                ("SEPARATE", separate),
                ("REINFORCED", reinforced),
                ("FLAG_TRANSOM", any_flag_transom),
            )
            if enabled
        ) or "BASE"
        count(combinations, combination)

        # Emitir somente casos pertinentes aos bloqueadores, jamais identificacao comercial.
        if af or ag or complex_flag or separate_transom or reinforced:
            case: dict[str, Any] = {"orcs_row": row_id}
            for column, label in TECHNICAL_COLUMNS.items():
                value = row.get(column, "")
                if value != "":
                    case[label] = value
            technical_cases.append(case)

    return {
        "total_mx": len(mx),
        "leaves": dict(sorted(leaves.items(), key=lambda item: int(item[0]))),
        "systems": dict(sorted(systems.items())),
        "orientations": dict(sorted(orientations.items())),
        "feature_counts": dict(sorted(flags.items())),
        "feature_combinations": dict(sorted(combinations.items())),
        "relevant_row_ids": relevant_ids,
        "technical_cases": technical_cases,
        "privacy": "Campos A/B/C/J/AM/AN e demais identificadores comerciais foram excluidos.",
    }


def defined_names(archive: zipfile.ZipFile) -> dict[str, Any]:
    root = ET.fromstring(archive.read("xl/workbook.xml"))
    result = []
    for item in root.findall("x:definedNames/x:definedName", NS):
        result.append({"name": item.attrib.get("name", ""), "refers_to": item.text or ""})
    relevant_names = {"LISTAP", "LISTAC", "LISTAD", "LISTAF", "LISTAF2", "LISTAV", "PAFAB"}
    relevant = [
        item
        for item in result
        if item["name"].upper() in relevant_names
        or "MX!" in item["refers_to"].upper()
        or any(term in item["refers_to"].upper() for term in SEARCH_TERMS)
    ]
    return {
        "total_definitions": len(result),
        "unique_names": len({item["name"] for item in result}),
        "relevant_to_technical_lookup": relevant,
        "finding": "Nenhum nome definido especifico cria regra adicional para os seis bloqueadores.",
    }


def formula_and_catalog_evidence(
    archive: zipfile.ZipFile, targets: dict[str, str], strings: list[str]
) -> tuple[dict[str, str], list[dict[str, str]], list[dict[str, str]]]:
    formula_hashes: dict[str, str] = {}
    formula_hits: list[dict[str, str]] = []
    catalog_hits: list[dict[str, str]] = []
    for sheet, target in targets.items():
        formulas: list[str] = []
        for coordinate, value, formula in sheet_cells(archive, target, strings):
            if formula:
                formulas.append(f"{coordinate}={formula}")
                upper_formula = formula.upper()
                if any(term in upper_formula for term in SEARCH_TERMS):
                    formula_hits.append({"sheet": sheet, "cell": coordinate, "formula": formula})
            if sheet in {"LISTAPERFIS", "LISTAFERRA", "LISTADIV", "PFAB"}:
                upper_value = normalized_text(value)
                if any(term in upper_value for term in SEARCH_TERMS):
                    catalog_hits.append({"sheet": sheet, "cell": coordinate, "value": value})
        formula_hashes[sheet] = hashlib.sha256("\n".join(formulas).encode("utf-8")).hexdigest()
    return formula_hashes, formula_hits, catalog_hits


def inspect_workbook(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "file_name": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
    }
    with path.open("rb") as stream:
        result["signature_hex"] = stream.read(8).hex().upper()
    try:
        with zipfile.ZipFile(path) as archive:
            bad_entry = archive.testzip()
            targets = sheet_targets(archive)
            strings = shared_strings(archive)
            formula_hashes, formula_hits, catalog_hits = formula_and_catalog_evidence(
                archive, targets, strings
            )
            result.update(
                {
                    "format": "ZIP/OpenXML",
                    "zip_entries": len(archive.namelist()),
                    "zip_integrity": "OK" if bad_entry is None else f"BAD:{bad_entry}",
                    "sheets": list(targets),
                    "formula_hashes": formula_hashes,
                    "defined_names": defined_names(archive),
                    "formula_evidence": formula_hits,
                    "catalog_evidence": catalog_hits,
                }
            )
            if "ORCS" in targets:
                result["orcs"] = analyze_orcs(orcs_rows(archive, targets["ORCS"], strings))
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as error:
        result.update(
            {
                "format": "NOT_A_COMPLETE_OPENXML_PACKAGE",
                "error": str(error),
                "recoverable_local_headers": scan_local_zip_headers(path),
            }
        )
    return result


def scan_local_zip_headers(path: Path) -> dict[str, Any]:
    """Inventaria cabecalhos ZIP locais mesmo sem diretorio central.

    Nao extrai nem grava conteudo. A varredura serve apenas para distinguir um
    fragmento OpenXML de um arquivo aleatorio ou lock file.
    """

    data = path.read_bytes()
    signature = b"PK\x03\x04"
    offsets = [match.start() for match in re.finditer(re.escape(signature), data)]
    names: list[str] = []
    valid_headers = 0
    recovered_entries: dict[str, bytes] = {}
    for offset in offsets:
        if offset + 30 > len(data):
            continue
        try:
            fields = struct.unpack_from("<IHHHHHIIIHH", data, offset)
        except struct.error:
            continue
        compression_method = fields[3]
        compressed_size = fields[7]
        uncompressed_size = fields[8]
        name_length, extra_length = fields[-2:]
        name_start = offset + 30
        name_end = name_start + name_length
        if name_end + extra_length > len(data):
            continue
        raw_name = data[name_start:name_end]
        try:
            name = raw_name.decode("utf-8")
        except UnicodeDecodeError:
            try:
                name = raw_name.decode("cp437")
            except UnicodeDecodeError:
                continue
        if not name or any(ord(character) < 32 for character in name):
            continue
        valid_headers += 1
        if len(names) < 200:
            names.append(name)
        payload_start = name_end + extra_length
        payload_end = payload_start + compressed_size
        if payload_end <= len(data):
            payload = data[payload_start:payload_end]
            try:
                if compression_method == 0:
                    recovered = payload
                elif compression_method == 8:
                    recovered = zlib.decompress(payload, -15)
                else:
                    continue
            except zlib.error:
                continue
            if len(recovered) == uncompressed_size:
                recovered_entries[name] = recovered
    recovered_xml = []
    for name, payload in recovered_entries.items():
        if name.endswith((".xml", ".rels")):
            try:
                ET.fromstring(payload)
            except ET.ParseError:
                continue
            recovered_xml.append(name)

    recovered_sheet_names: list[str] = []
    recovered_technical_sheets: list[str] = []
    recovered_formula_hashes: dict[str, str] = {}
    recovered_mx_formula_evidence: list[dict[str, str]] = []
    try:
        workbook = ET.fromstring(recovered_entries["xl/workbook.xml"])
        relationships = ET.fromstring(recovered_entries["xl/_rels/workbook.xml.rels"])
        rel_targets = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in relationships.findall(f"{{{REL_NS}}}Relationship")
        }
        for sheet in workbook.findall("x:sheets/x:sheet", NS):
            sheet_name = sheet.attrib["name"]
            recovered_sheet_names.append(sheet_name)
            relationship_id = sheet.attrib[f"{{{OFFICE_REL_NS}}}id"]
            target = rel_targets[relationship_id].lstrip("/")
            if not target.startswith("xl/"):
                target = str(PurePosixPath("xl") / target)
            if target in recovered_entries and sheet_name in {"MX", "ORCS", "LISTAPERFIS", "LISTAFERRA", "PFAB"}:
                recovered_technical_sheets.append(sheet_name)
                sheet_root = ET.fromstring(recovered_entries[target])
                formulas = []
                for cell in sheet_root.findall(".//x:sheetData/x:row/x:c", NS):
                    formula_node = cell.find("x:f", NS)
                    if formula_node is not None:
                        formulas.append(f"{cell.attrib['r']}={formula_node.text or ''}")
                        coordinate = cell.attrib["r"]
                        formula_row = row_number(coordinate)
                        if sheet_name == "MX" and (
                            10 <= formula_row <= 32
                            or 59 <= formula_row <= 72
                            or formula_row in {56, 80}
                        ):
                            recovered_mx_formula_evidence.append(
                                {"cell": coordinate, "formula": formula_node.text or ""}
                            )
                recovered_formula_hashes[sheet_name] = hashlib.sha256(
                    "\n".join(formulas).encode("utf-8")
                ).hexdigest()
    except (KeyError, ET.ParseError):
        pass
    last_nonzero = max((index for index, byte in enumerate(data) if byte), default=-1)
    return {
        "local_header_signatures": len(offsets),
        "plausible_headers": valid_headers,
        "entry_names": names,
        "entries_decompressed_in_memory": len(recovered_entries),
        "parseable_xml_entries": len(recovered_xml),
        "workbook_sheet_names": recovered_sheet_names,
        "recovered_technical_sheets": recovered_technical_sheets,
        "recovered_formula_hashes": recovered_formula_hashes,
        "recovered_mx_formula_evidence": recovered_mx_formula_evidence,
        "has_content_types": "[Content_Types].xml" in names,
        "has_workbook_xml": "xl/workbook.xml" in names,
        "has_orcs_candidate": any(name.startswith("xl/worksheets/") for name in names),
        "end_of_central_directory_present": data.rfind(b"PK\x05\x06") >= 0,
        "zero_byte_ratio": round(data.count(0) / len(data), 6) if data else 1.0,
        "last_nonzero_offset": last_nonzero,
    }


def comparison(primary: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    common_sheets = sorted(set(primary.get("sheets", [])) & set(candidate.get("sheets", [])))
    formula_equal = {
        sheet: primary.get("formula_hashes", {}).get(sheet)
        == candidate.get("formula_hashes", {}).get(sheet)
        for sheet in common_sheets
    }
    return {
        "same_sha256": primary["sha256"] == candidate["sha256"],
        "same_sheet_list": primary.get("sheets") == candidate.get("sheets"),
        "formula_hash_equal_by_sheet": formula_equal,
        "mx_formula_hash_equal": formula_equal.get("MX"),
        "orcs_total_mx": {
            "primary": primary.get("orcs", {}).get("total_mx"),
            "candidate": candidate.get("orcs", {}).get("total_mx"),
        },
        "orcs_feature_counts_equal": primary.get("orcs", {}).get("feature_counts")
        == candidate.get("orcs", {}).get("feature_counts"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--compare", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    report: dict[str, Any] = {"primary": inspect_workbook(args.workbook)}
    if args.compare:
        report["comparison_candidate"] = inspect_workbook(args.compare)
        report["comparison"] = comparison(report["primary"], report["comparison_candidate"])
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    print()


if __name__ == "__main__":
    main()
