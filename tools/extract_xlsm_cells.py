"""Read selected cells/formulas from an XLSM without Excel dependencies.

Usage:
    python tools/extract_xlsm_cells.py workbook.xlsm CR A1:AK149
"""

from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"x": MAIN_NS, "r": OFFICE_REL_NS}
CELL_RE = re.compile(r"^([A-Z]+)([1-9][0-9]*)$")


def column_number(label: str) -> int:
    number = 0
    for char in label:
        number = number * 26 + ord(char) - ord("A") + 1
    return number


def parse_coordinate(coordinate: str) -> tuple[int, int]:
    match = CELL_RE.fullmatch(coordinate.upper())
    if match is None:
        raise ValueError(f"Invalid cell coordinate: {coordinate}")
    return column_number(match.group(1)), int(match.group(2))


@dataclass(frozen=True)
class CellRange:
    min_column: int
    min_row: int
    max_column: int
    max_row: int

    @classmethod
    def parse(cls, value: str) -> "CellRange":
        first, separator, last = value.partition(":")
        if not separator:
            last = first
        first_column, first_row = parse_coordinate(first)
        last_column, last_row = parse_coordinate(last)
        return cls(
            min(first_column, last_column),
            min(first_row, last_row),
            max(first_column, last_column),
            max(first_row, last_row),
        )

    def contains(self, coordinate: str) -> bool:
        column, row = parse_coordinate(coordinate)
        return (
            self.min_column <= column <= self.max_column
            and self.min_row <= row <= self.max_row
        )


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
        target = PurePosixPath("xl") / targets[relationship_id]
        result[sheet.attrib["name"]] = str(target)
    return result


def extract_cells(
    archive: zipfile.ZipFile,
    target: str,
    selection: CellRange,
    strings: list[str],
) -> list[tuple[str, str, str, str, str]]:
    root = ET.fromstring(archive.read(target))
    rows: list[tuple[str, str, str, str, str]] = []
    for cell in root.findall(".//x:sheetData/x:row/x:c", NS):
        coordinate = cell.attrib["r"]
        if not selection.contains(coordinate):
            continue
        value_node = cell.find("x:v", NS)
        formula_node = cell.find("x:f", NS)
        raw_value = value_node.text if value_node is not None and value_node.text else ""
        cell_type = cell.attrib.get("t", "")
        displayed = raw_value
        if cell_type == "s" and raw_value:
            displayed = strings[int(raw_value)]
        elif cell_type == "inlineStr":
            displayed = "".join(
                node.text or "" for node in cell.findall(".//x:is//x:t", NS)
            )
        formula = formula_node.text or "" if formula_node is not None else ""
        formula_metadata = ""
        if formula_node is not None and formula_node.attrib:
            formula_metadata = ",".join(
                f"{key}={value}" for key, value in sorted(formula_node.attrib.items())
            )
        rows.append((coordinate, cell_type, displayed, formula, formula_metadata))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook")
    parser.add_argument("sheet")
    parser.add_argument("cell_range")
    parser.add_argument("--formulas-only", action="store_true")
    args = parser.parse_args()

    selection = CellRange.parse(args.cell_range)
    with zipfile.ZipFile(args.workbook) as archive:
        targets = sheet_targets(archive)
        if args.sheet not in targets:
            raise SystemExit(f"Sheet not found: {args.sheet}")
        strings = shared_strings(archive)
        rows = extract_cells(archive, targets[args.sheet], selection, strings)

    print("cell\ttype\tvalue\tformula\tformula_metadata")
    for row in rows:
        if args.formulas_only and not row[3]:
            continue
        print("\t".join(value.replace("\t", " ").replace("\n", " ") for value in row))


if __name__ == "__main__":
    main()
