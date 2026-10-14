"""Oráculo GR que executa as fórmulas do XLSM sem Microsoft Excel.

O arquivo oficial é aberto apenas como ZIP/OpenXML. O avaliador implementa
somente o subconjunto de fórmulas realmente usado pela aba GR e nunca lê nem
emite os campos privados A:C/J da ORCS.

Uso:
    python tools/gr_formula_oracle.py fonte.xlsm --rows 270 11480
    python tools/gr_formula_oracle.py fonte.xlsm --self-check
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any, Iterable
import xml.etree.ElementTree as ET
from zipfile import ZipFile


OFFICIAL_SHA256 = "96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160"
MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"x": MAIN_NS, "r": OFFICE_REL_NS}

TECHNICAL_COLUMNS = tuple(
    [chr(code) for code in range(ord("D"), ord("Z") + 1) if chr(code) != "J"]
    + ["A" + chr(code) for code in range(ord("A"), ord("K") + 1)]
)
OUTPUT_CELLS = (
    "D8", "E8", "G8", "D9", "E9", "G9", "B10", "C10", "D10", "E10", "G10",
    "D11", "E11", "G11", "D12", "G12", "D13", "G13", "D14", "G14", "D15",
    "G15", "D16", "G16", "D17", "G17", "D18", "G18", "D19", "G19", "D58",
    "G58", "D59", "G59", "D60", "G60", "D61", "G61", "D68", "E68", "G68",
    "I68", "G83", "I83", "I56", "I65", "I71", "I74", "I81", "I103", "I120",
    "I122", "AO2",
)
BOM_ROWS = tuple((*range(8, 56), *range(58, 65), *range(68, 71), 73,
                  *range(76, 81), *range(83, 103), *range(104, 120)))


class FormulaError(Exception):
    """Valor de erro de planilha que também pode ser propagado como exceção."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class CellData:
    value: Any
    formula: str | None = None
    formula_base: str | None = None


@dataclass(frozen=True)
class CellRef:
    sheet: str | None
    column: int
    row: int
    absolute_column: bool
    absolute_row: bool


@dataclass(frozen=True)
class RangeValue:
    sheet: str
    start_column: int
    start_row: int
    end_column: int
    end_row: int


@dataclass(frozen=True)
class Token:
    kind: str
    value: str


TOKEN_RE = re.compile(
    r'(?P<SPACE>\s+)|'
    r'(?P<STRING>"(?:[^"]|"")*")|'
    r'(?P<NUMBER>(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?)|'
    r"(?P<CELL>(?:(?:'[^']+'|[A-Za-z_][A-Za-z0-9_.]*)!)?\$?[A-Za-z]{1,3}\$?\d+)|"
    r'(?P<NAME>[A-Za-z_][A-Za-z0-9_.]*)|'
    r'(?P<OP><=|>=|<>|[=<>+\-*/^&:,()])'
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _column_number(label: str) -> int:
    value = 0
    for char in label.upper():
        value = value * 26 + ord(char) - ord("A") + 1
    return value


def _column_label(number: int) -> str:
    result = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result


def _split_coordinate(coordinate: str) -> tuple[int, int]:
    match = re.fullmatch(r"([A-Z]+)([1-9][0-9]*)", coordinate.upper())
    if match is None:
        raise ValueError(f"Coordenada inválida: {coordinate}")
    return _column_number(match.group(1)), int(match.group(2))


def _parse_cell_ref(text: str) -> CellRef:
    sheet = None
    if "!" in text:
        raw_sheet, text = text.rsplit("!", 1)
        sheet = raw_sheet[1:-1].replace("''", "'") if raw_sheet.startswith("'") else raw_sheet
    match = re.fullmatch(r"(\$?)([A-Za-z]{1,3})(\$?)([1-9][0-9]*)", text)
    if match is None:
        raise ValueError(f"Referência inválida: {text}")
    return CellRef(
        sheet=sheet,
        column=_column_number(match.group(2)),
        row=int(match.group(4)),
        absolute_column=bool(match.group(1)),
        absolute_row=bool(match.group(3)),
    )


def _typed_value(cell: ET.Element, strings: list[str]) -> Any:
    cell_type = cell.attrib.get("t", "")
    value_node = cell.find("x:v", NS)
    raw = value_node.text if value_node is not None and value_node.text is not None else ""
    if cell_type == "s":
        return strings[int(raw)] if raw else ""
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//x:is//x:t", NS))
    if cell_type == "b":
        return raw == "1"
    if cell_type == "e":
        return FormulaError(raw or "#VALUE!")
    if cell_type == "str":
        return raw
    if not raw:
        return None
    number = float(raw)
    return int(number) if number.is_integer() else number


def _shared_strings(archive: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return [
        "".join(node.text or "" for node in item.findall(".//x:t", NS))
        for item in root.findall("x:si", NS)
    ]


def _sheet_targets(archive: ZipFile) -> dict[str, str]:
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


def _defined_names(archive: ZipFile) -> dict[str, RangeValue]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    result: dict[str, RangeValue] = {}
    for item in workbook.findall("x:definedNames/x:definedName", NS):
        name = item.attrib.get("name", "").upper()
        text = item.text or ""
        match = re.fullmatch(
            r"(?:'([^']+)'|([^!]+))!\$?([A-Z]+)(?:\$?([1-9][0-9]*))?:\$?([A-Z]+)(?:\$?([1-9][0-9]*))?",
            text,
        )
        if match is None:
            continue
        sheet = match.group(1) or match.group(2)
        result[name] = RangeValue(
            sheet=sheet,
            start_column=_column_number(match.group(3)),
            start_row=int(match.group(4) or 1),
            end_column=_column_number(match.group(5)),
            end_row=int(match.group(6) or 1_048_576),
        )
    return result


def _load_sheet(
    archive: ZipFile,
    target: str,
    strings: list[str],
    *,
    allowed_rows: set[int] | None = None,
    allowed_columns: set[str] | None = None,
) -> dict[str, CellData]:
    root = ET.fromstring(archive.read(target))
    result: dict[str, CellData] = {}
    shared: dict[str, tuple[str, str]] = {}
    pending: list[tuple[str, Any, str]] = []
    for cell in root.findall(".//x:sheetData/x:row/x:c", NS):
        coordinate = cell.attrib["r"].upper()
        column, row = _split_coordinate(coordinate)
        if allowed_rows is not None and row not in allowed_rows:
            continue
        if allowed_columns is not None and _column_label(column) not in allowed_columns:
            continue
        value = _typed_value(cell, strings)
        formula_node = cell.find("x:f", NS)
        if formula_node is None:
            result[coordinate] = CellData(value=value)
            continue
        formula = formula_node.text or ""
        if formula_node.attrib.get("t") == "shared":
            shared_id = formula_node.attrib["si"]
            if formula:
                shared[shared_id] = (coordinate, formula)
                result[coordinate] = CellData(value=value, formula=formula, formula_base=coordinate)
            else:
                pending.append((coordinate, value, shared_id))
        else:
            result[coordinate] = CellData(value=value, formula=formula, formula_base=coordinate)
    for coordinate, value, shared_id in pending:
        if shared_id not in shared:
            raise ValueError(f"Fórmula compartilhada {shared_id} sem origem em {coordinate}")
        base, formula = shared[shared_id]
        result[coordinate] = CellData(value=value, formula=formula, formula_base=base)
    return result


def _tokens(formula: str) -> list[Token]:
    result: list[Token] = []
    position = 0
    while position < len(formula):
        match = TOKEN_RE.match(formula, position)
        if match is None:
            raise ValueError(f"Token de fórmula não suportado em {formula[position:position + 30]!r}")
        position = match.end()
        if match.lastgroup != "SPACE":
            result.append(Token(match.lastgroup or "", match.group()))
    result.append(Token("EOF", ""))
    return result


class FormulaParser:
    def __init__(self, formula: str):
        self.tokens = _tokens(formula)
        self.position = 0

    def parse(self) -> Any:
        expression = self._comparison()
        self._expect("EOF")
        return expression

    def _peek(self, value: str | None = None, kind: str | None = None) -> bool:
        token = self.tokens[self.position]
        return (value is None or token.value == value) and (kind is None or token.kind == kind)

    def _take(self) -> Token:
        token = self.tokens[self.position]
        self.position += 1
        return token

    def _expect(self, value_or_kind: str) -> Token:
        token = self._take()
        if token.value != value_or_kind and token.kind != value_or_kind:
            raise ValueError(f"Esperado {value_or_kind}, encontrado {token.value or token.kind}")
        return token

    def _comparison(self) -> Any:
        node = self._concat()
        if self._peek(kind="OP") and self.tokens[self.position].value in ("=", "<>", "<", ">", "<=", ">="):
            operator = self._take().value
            node = ("binary", operator, node, self._concat())
        return node

    def _concat(self) -> Any:
        node = self._additive()
        while self._peek("&"):
            self._take()
            node = ("binary", "&", node, self._additive())
        return node

    def _additive(self) -> Any:
        node = self._multiplicative()
        while self._peek("+") or self._peek("-"):
            operator = self._take().value
            node = ("binary", operator, node, self._multiplicative())
        return node

    def _multiplicative(self) -> Any:
        node = self._power()
        while self._peek("*") or self._peek("/"):
            operator = self._take().value
            node = ("binary", operator, node, self._power())
        return node

    def _power(self) -> Any:
        node = self._unary()
        if self._peek("^"):
            self._take()
            node = ("binary", "^", node, self._power())
        return node

    def _unary(self) -> Any:
        if self._peek("+") or self._peek("-"):
            return ("unary", self._take().value, self._unary())
        return self._range()

    def _range(self) -> Any:
        node = self._primary()
        if self._peek(":"):
            self._take()
            node = ("range", node, self._primary())
        return node

    def _primary(self) -> Any:
        token = self._take()
        if token.kind == "NUMBER":
            value = float(token.value)
            return ("literal", int(value) if value.is_integer() else value)
        if token.kind == "STRING":
            return ("literal", token.value[1:-1].replace('""', '"'))
        if token.kind == "CELL":
            return ("cell", _parse_cell_ref(token.value))
        if token.kind == "NAME":
            name = token.value.upper()
            if self._peek("("):
                self._take()
                arguments = []
                if not self._peek(")"):
                    while True:
                        arguments.append(self._comparison())
                        if not self._peek(","):
                            break
                        self._take()
                self._expect(")")
                return ("call", name, arguments)
            if name in ("TRUE", "FALSE"):
                return ("literal", name == "TRUE")
            return ("name", name)
        if token.value == "(":
            node = self._comparison()
            self._expect(")")
            return node
        raise ValueError(f"Expressão inesperada: {token.value or token.kind}")


def _number(value: Any) -> float:
    if isinstance(value, FormulaError):
        raise value
    if value is None or value == "":
        return 0.0
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "."))
    except ValueError as exc:
        raise FormulaError("#VALUE!") from exc


def _text(value: Any) -> str:
    if isinstance(value, FormulaError):
        raise value
    if value is None:
        return ""
    if value is True:
        return "TRUE"
    if value is False:
        return "FALSE"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _truth(value: Any) -> bool:
    if isinstance(value, FormulaError):
        raise value
    if value is None or value == "" or value is False:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return bool(value)


def _equal(left: Any, right: Any) -> bool:
    if isinstance(left, FormulaError):
        raise left
    if isinstance(right, FormulaError):
        raise right
    if left is None and isinstance(right, (int, float)):
        left = 0
    if right is None and isinstance(left, (int, float)):
        right = 0
    if left is None:
        left = ""
    if right is None:
        right = ""
    if isinstance(left, str) and isinstance(right, str):
        return left.casefold() == right.casefold()
    return left == right


class GrFormulaOracle:
    """Executa a planilha GR diretamente das fórmulas OpenXML."""

    def __init__(self, workbook_path: Path, *, require_official_hash: bool = True):
        self.workbook_path = workbook_path
        digest = _sha256(workbook_path)
        if require_official_hash and digest != OFFICIAL_SHA256:
            raise ValueError("Workbook is not the official GR parity source.")
        self.sha256 = digest
        with ZipFile(workbook_path) as archive:
            strings = _shared_strings(archive)
            targets = _sheet_targets(archive)
            required = {"GR", "ORCS", "LISTAPERFIS", "LISTAVIDROS", "LISTAFERRA", "LISTADIV", "PFAB"}
            missing = required - targets.keys()
            if missing:
                raise ValueError(f"Abas técnicas ausentes: {sorted(missing)}")
            self.names = _defined_names(archive)
            self.sheets = {
                name: _load_sheet(archive, targets[name], strings)
                for name in required - {"ORCS"}
            }
            # Somente o contrato técnico é carregado; dados de cliente, item e local ficam fora da memória.
            self.sheets["ORCS"] = _load_sheet(
                archive,
                targets["ORCS"],
                strings,
                allowed_columns=set(TECHNICAL_COLUMNS),
            )
        self._base_gr = dict(self.sheets["GR"])
        self._ast_cache: dict[tuple[str, str], Any] = {}
        self._value_cache: dict[tuple[str, str], Any] = {}
        self._active: set[tuple[str, str]] = set()

    def _resolve_ref(self, ref: CellRef, current_sheet: str, current_cell: str, formula_base: str) -> tuple[str, str]:
        current_column, current_row = _split_coordinate(current_cell)
        base_column, base_row = _split_coordinate(formula_base)
        column = ref.column if ref.absolute_column else ref.column + current_column - base_column
        row = ref.row if ref.absolute_row else ref.row + current_row - base_row
        if column < 1 or row < 1:
            raise FormulaError("#REF!")
        return ref.sheet or current_sheet, f"{_column_label(column)}{row}"

    def _range(self, start: tuple[str, str], end: tuple[str, str]) -> RangeValue:
        if start[0] != end[0]:
            raise FormulaError("#REF!")
        start_column, start_row = _split_coordinate(start[1])
        end_column, end_row = _split_coordinate(end[1])
        return RangeValue(start[0], min(start_column, end_column), min(start_row, end_row),
                          max(start_column, end_column), max(start_row, end_row))

    def _range_values(self, value: RangeValue) -> Iterable[list[Any]]:
        sheet = self.sheets[value.sheet]
        populated_rows = [
            _split_coordinate(coordinate)[1]
            for coordinate in sheet
            if value.start_column <= _split_coordinate(coordinate)[0] <= value.end_column
        ]
        last_row = min(value.end_row, max(populated_rows, default=value.start_row) + 1)
        for row in range(value.start_row, last_row + 1):
            yield [
                self.value(value.sheet, f"{_column_label(column)}{row}")
                for column in range(value.start_column, value.end_column + 1)
            ]

    def value(self, sheet: str, coordinate: str) -> Any:
        coordinate = coordinate.upper()
        key = (sheet, coordinate)
        if key in self._value_cache:
            return self._value_cache[key]
        if key in self._active:
            return FormulaError("#CIRC!")
        cell = self.sheets.get(sheet, {}).get(coordinate)
        if cell is None:
            return None
        if not cell.formula:
            return cell.value
        self._active.add(key)
        try:
            ast_key = (cell.formula, cell.formula_base or coordinate)
            ast = self._ast_cache.get(ast_key)
            if ast is None:
                ast = FormulaParser(cell.formula).parse()
                self._ast_cache[ast_key] = ast
            try:
                result = self._evaluate(ast, sheet, coordinate, cell.formula_base or coordinate)
            except FormulaError as error:
                result = error
            self._value_cache[key] = result
            return result
        finally:
            self._active.remove(key)

    def _evaluate(self, node: Any, sheet: str, coordinate: str, formula_base: str) -> Any:
        kind = node[0]
        if kind == "literal":
            return node[1]
        if kind == "cell":
            ref = self._resolve_ref(node[1], sheet, coordinate, formula_base)
            return self.value(*ref)
        if kind == "name":
            if node[1] not in self.names:
                raise FormulaError("#NAME?")
            return self.names[node[1]]
        if kind == "range":
            if node[1][0] != "cell" or node[2][0] != "cell":
                raise FormulaError("#REF!")
            start = self._resolve_ref(node[1][1], sheet, coordinate, formula_base)
            end = self._resolve_ref(node[2][1], sheet, coordinate, formula_base)
            return self._range(start, end)
        if kind == "unary":
            number = _number(self._evaluate(node[2], sheet, coordinate, formula_base))
            return number if node[1] == "+" else -number
        if kind == "binary":
            operator = node[1]
            left = self._evaluate(node[2], sheet, coordinate, formula_base)
            right = self._evaluate(node[3], sheet, coordinate, formula_base)
            if operator == "&":
                return _text(left) + _text(right)
            if operator in ("=", "<>"):
                equal = _equal(left, right)
                return equal if operator == "=" else not equal
            if operator in ("<", ">", "<=", ">="):
                left_number, right_number = _number(left), _number(right)
                return {"<": left_number < right_number, ">": left_number > right_number,
                        "<=": left_number <= right_number, ">=": left_number >= right_number}[operator]
            left_number, right_number = _number(left), _number(right)
            if operator == "+":
                return left_number + right_number
            if operator == "-":
                return left_number - right_number
            if operator == "*":
                return left_number * right_number
            if operator == "/":
                if right_number == 0:
                    raise FormulaError("#DIV/0!")
                return left_number / right_number
            if operator == "^":
                return left_number ** right_number
        if kind == "call":
            name, arguments = node[1], node[2]
            if name == "IF":
                if len(arguments) not in (2, 3):
                    raise FormulaError("#VALUE!")
                branch = arguments[1] if _truth(self._evaluate(arguments[0], sheet, coordinate, formula_base)) else (
                    arguments[2] if len(arguments) == 3 else ("literal", False)
                )
                return self._evaluate(branch, sheet, coordinate, formula_base)
            if name in ("AND", "OR"):
                values = [_truth(self._evaluate(arg, sheet, coordinate, formula_base)) for arg in arguments]
                return all(values) if name == "AND" else any(values)
            if name == "LEFT":
                text = _text(self._evaluate(arguments[0], sheet, coordinate, formula_base))
                count = int(_number(self._evaluate(arguments[1], sheet, coordinate, formula_base))) if len(arguments) > 1 else 1
                return text[:count]
            if name == "SUM":
                total = 0.0
                for argument in arguments:
                    value = self._evaluate(argument, sheet, coordinate, formula_base)
                    if isinstance(value, RangeValue):
                        for row in self._range_values(value):
                            for item in row:
                                if isinstance(item, FormulaError):
                                    raise item
                                if isinstance(item, (int, float)) and not isinstance(item, bool):
                                    total += float(item)
                    else:
                        total += _number(value)
                return total
            if name == "VLOOKUP":
                lookup = self._evaluate(arguments[0], sheet, coordinate, formula_base)
                table = self._evaluate(arguments[1], sheet, coordinate, formula_base)
                index = int(_number(self._evaluate(arguments[2], sheet, coordinate, formula_base)))
                exact = len(arguments) > 3 and not _truth(self._evaluate(arguments[3], sheet, coordinate, formula_base))
                if not isinstance(table, RangeValue) or index < 1:
                    raise FormulaError("#VALUE!")
                candidate = None
                for row in self._range_values(table):
                    if exact and _equal(row[0], lookup):
                        return row[index - 1] if index <= len(row) else FormulaError("#REF!")
                    if not exact and self._lookup_less_equal(row[0], lookup):
                        candidate = row[index - 1] if index <= len(row) else FormulaError("#REF!")
                if candidate is not None:
                    return candidate
                raise FormulaError("#N/A")
            raise FormulaError("#NAME?")
        raise FormulaError("#VALUE!")

    @staticmethod
    def _lookup_less_equal(left: Any, right: Any) -> bool:
        try:
            return _number(left) <= _number(right)
        except FormulaError:
            return _text(left).casefold() <= _text(right).casefold()

    def _reset_gr(self) -> None:
        self.sheets["GR"] = dict(self._base_gr)
        self._value_cache.clear()
        self._active.clear()

    def _technical_row(self, row: int) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for column in TECHNICAL_COLUMNS:
            cell = self.sheets["ORCS"].get(f"{column}{row}")
            values[column] = cell.value if cell else None
        if values["X"] != "GR":
            raise ValueError(f"ORCS row {row} is not GR")
        return values

    def calculate_orcs_row(self, row: int) -> dict[str, Any]:
        values = self._technical_row(row)
        self._reset_gr()
        for column, value in values.items():
            self.sheets["GR"][f"{column}2"] = CellData(value=value)
        self.sheets["GR"]["C2"] = CellData(value=1)
        cells = {address: _json_value(self.value("GR", address)) for address in OUTPUT_CELLS}
        bom = []
        for bom_row in BOM_ROWS:
            quantity = self.value("GR", f"G{bom_row}")
            try:
                numeric_quantity = _number(quantity)
            except FormulaError:
                continue
            if numeric_quantity > 0:
                bom.append([
                    bom_row,
                    _json_value(self.value("GR", f"C{bom_row}")),
                    _json_value(self.value("GR", f"D{bom_row}")),
                    _json_value(self.value("GR", f"E{bom_row}")),
                    numeric_quantity,
                    _json_value(self.value("GR", f"H{bom_row}")),
                    _json_value(self.value("GR", f"I{bom_row}")),
                ])
        return {"orcs_row": row, "cells": cells, "bom": bom}

    def gr_rows(self) -> list[int]:
        result = []
        for coordinate, cell in self.sheets["ORCS"].items():
            column, row = _split_coordinate(coordinate)
            if column == _column_number("X") and cell.value == "GR":
                result.append(row)
        return sorted(result)

    def verify_cached_gr(self) -> dict[str, Any]:
        self._reset_gr()
        checked = 0
        mismatches = []
        for coordinate, cell in sorted(self._base_gr.items()):
            if not cell.formula:
                continue
            actual = self.value("GR", coordinate)
            expected = cell.value
            checked += 1
            if not _same_value(actual, expected):
                mismatches.append({
                    "cell": coordinate,
                    "expected": _json_value(expected),
                    "actual": _json_value(actual),
                })
        return {"checked": checked, "mismatch_count": len(mismatches), "mismatches": mismatches}


def _same_value(actual: Any, expected: Any) -> bool:
    if isinstance(actual, FormulaError) or isinstance(expected, FormulaError):
        return isinstance(actual, FormulaError) and isinstance(expected, FormulaError) and actual.code == expected.code
    if actual is None and expected in (None, ""):
        return True
    if expected is None and actual in (None, ""):
        return True
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return math.isclose(float(actual), float(expected), rel_tol=1e-10, abs_tol=1e-8)
    return actual == expected


def _json_value(value: Any) -> Any:
    if isinstance(value, FormulaError):
        return value.code
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _case_summary(cases: list[dict[str, Any]], source_sha256: str) -> dict[str, Any]:
    errors: dict[str, list[int]] = {}
    numeric_rows = 0
    for case in cases:
        total = case["cells"]["AO2"]
        if isinstance(total, (int, float)) and not isinstance(total, bool):
            numeric_rows += 1
        else:
            errors.setdefault(str(total), []).append(case["orcs_row"])
    return {
        "source_sha256": source_sha256,
        "rows_evaluated": len(cases),
        "numeric_total_rows": numeric_rows,
        "formula_error_rows": sum(len(rows) for rows in errors.values()),
        "errors": {
            code: {"count": len(rows), "orcs_rows": rows}
            for code, rows in sorted(errors.items())
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--rows", nargs="+", type=int)
    parser.add_argument("--all-gr-rows", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-other-hash", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not (args.rows or args.all_gr_rows or args.self_check):
        parser.error("informe --rows, --all-gr-rows ou --self-check")

    oracle = GrFormulaOracle(args.workbook, require_official_hash=not args.allow_other_hash)
    if args.self_check and not (args.rows or args.all_gr_rows):
        payload: Any = oracle.verify_cached_gr()
    else:
        rows = oracle.gr_rows() if args.all_gr_rows else args.rows or []
        cases = [oracle.calculate_orcs_row(row) for row in rows]
        payload = _case_summary(cases, oracle.sha256) if args.summary else cases
        if args.self_check:
            payload = {"self_check": oracle.verify_cached_gr(), "cases": payload}
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        args.output.write_text(serialized + "\n", encoding="utf-8")
    else:
        sys.stdout.write(serialized + "\n")


if __name__ == "__main__":
    main()
