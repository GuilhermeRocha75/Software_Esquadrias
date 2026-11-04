"""Oráculo FX: avalia as fórmulas OpenXML, separado da implementação técnica.

Reutiliza somente o interpretador de fórmulas do GR. Não importa a Engine.
O snapshot contém apenas fórmulas FX e catálogos técnicos, nunca clientes.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from zipfile import ZipFile

from gr_formula_oracle import (
    CellData, FormulaError, GrFormulaOracle, OFFICIAL_SHA256, RangeValue,
    TECHNICAL_COLUMNS, _defined_names, _json_value, _load_sheet, _same_value,
    _sha256, _shared_strings, _sheet_targets, _split_coordinate,
)

FX_INPUT_COLUMNS = ("D", "E", "F", "K", "S", "T", "AJ", "AK")
FX_BOM_ROWS = (*range(8, 18), *range(20, 24), 27, 30, 31)


class FixoFormulaOracle(GrFormulaOracle):
    def __init__(self, workbook_path: Path):
        self.sha256 = _sha256(workbook_path)
        if self.sha256 != OFFICIAL_SHA256:
            raise ValueError("A planilha não corresponde à fonte oficial de paridade FX.")
        with ZipFile(workbook_path) as archive:
            targets, strings = _sheet_targets(archive), _shared_strings(archive)
            names = _defined_names(archive)
            self.names = {name: names[name] for name in ("LISTAP", "LISTAV")}
            self.sheets = {name: _load_sheet(archive, targets[name], strings)
                           for name in ("FX", "LISTAPERFIS", "LISTAVIDROS")}
            # Somente A:C dos catálogos e as dimensões 18/19 pertencem à FX.
            self.sheets["LISTAPERFIS"] = {
                c: v for c, v in self.sheets["LISTAPERFIS"].items()
                if _split_coordinate(c)[0] <= 3 or c in ("D19", "E19", "E18")}
            self.sheets["LISTAVIDROS"] = {
                c: v for c, v in self.sheets["LISTAVIDROS"].items() if _split_coordinate(c)[0] <= 3}
            self.sheets["PFAB"] = _load_sheet(archive, targets["PFAB"], strings,
                                            allowed_rows={12, 14, 15}, allowed_columns={"B"})
            self.sheets["FX"] = {c: v for c, v in self.sheets["FX"].items()
                                  if _split_coordinate(c)[1] >= 3 or c in ("AN2", "AO2")}
            self.sheets["ORCS"] = _load_sheet(archive, targets["ORCS"], strings,
                                             allowed_columns=set(TECHNICAL_COLUMNS))
        self._initialize()

    def _initialize(self):
        self._base_fx = dict(self.sheets["FX"])
        self._ast_cache = {}
        self._value_cache = {}
        self._active = set()
        self._table_cache = {}

    def _range_values(self, value):
        # Os únicos intervalos de lookup são catálogos imutáveis nesta execução.
        if value.sheet == "FX":
            return super()._range_values(value)
        if value not in self._table_cache:
            self._table_cache[value] = list(super()._range_values(value))
        return iter(self._table_cache[value])

    def value(self, sheet, coordinate):
        result = super().value(sheet, coordinate)
        cell = self.sheets.get(sheet, {}).get(coordinate.upper())
        # Referência direta a uma célula vazia retorna zero no Excel. A célula
        # vazia em si continua None para LEFT/SUM distinguirem seu contexto.
        if result is None and cell is not None and cell.formula:
            self._value_cache[(sheet, coordinate.upper())] = 0
            return 0
        return result

    def _evaluate(self, node, sheet, coordinate, formula_base):
        if node[0] == "binary" and node[1] in ("+", "-", "*", "/", "^", "<", ">", "<=", ">="):
            left = self._evaluate(node[2], sheet, coordinate, formula_base)
            right = self._evaluate(node[3], sheet, coordinate, formula_base)
            # FX!K3 pode produzir texto vazio; K4=""*1 é #VALUE!, não zero.
            if left == "" or right == "":
                raise FormulaError("#VALUE!")
        return super()._evaluate(node, sheet, coordinate, formula_base)

    def fx_rows(self):
        return sorted(int(c[1:]) for c, v in self.sheets["ORCS"].items()
                      if c.startswith("X") and v.value == "FX")

    def technical_inputs(self, row):
        if self.sheets["ORCS"].get(f"X{row}", CellData(None)).value != "FX":
            raise ValueError(f"Linha ORCS {row} não é FX.")
        return {col: self.sheets["ORCS"].get(f"{col}{row}", CellData(None)).value
                for col in FX_INPUT_COLUMNS}

    def set_inputs(self, inputs):
        if set(inputs) - set(FX_INPUT_COLUMNS):
            raise ValueError("Entrada fora do contrato técnico FX.")
        self.sheets["FX"] = dict(self._base_fx)
        self.sheets["FX"].update({f"{col}2": CellData(value) for col, value in inputs.items()})
        self._value_cache = {key: value for key, value in self._value_cache.items() if key[0] != "FX"}
        self._active.clear()

    def bom(self):
        result = []
        for row in FX_BOM_ROWS:
            count = self.value("FX", f"G{row}")
            if isinstance(count, (int, float)) and count > 0:
                result.append({"source": f"FX!{row}", **{
                    col: _json_value(self.value("FX", f"{col}{row}"))
                    for col in ("C", "D", "E", "F", "G", "H", "I")}})
                # LISTAP armazena parte dos preços como texto com vírgula.
                price = result[-1]["H"]
                if isinstance(price, str) and not price.startswith("#"):
                    result[-1]["H"] = float(price.replace(",", "."))
                if isinstance(result[-1]["C"], (int, float)):
                    result[-1]["C"] = str(result[-1]["C"])
        return result

    def verify_cached_fx(self):
        self.set_inputs({})
        differences = []
        checked = 0
        for address, cell in self._base_fx.items():
            if cell.formula:
                checked += 1
                actual = self.value("FX", address)
                if not _same_value(actual, cell.value):
                    differences.append({"cell": address, "cached": _json_value(cell.value),
                                        "calculated": _json_value(actual)})
        return {"checked": checked, "mismatch_count": len(differences), "mismatches": differences}

    def snapshot(self):
        return {"source_sha256": self.sha256,
                "names": {name: asdict(value) for name, value in self.names.items()},
                "sheets": {name: {c: {"value": _json_value(v.value), "formula": v.formula,
                                       "formula_base": v.formula_base} for c, v in cells.items()}
                           for name, cells in self.sheets.items() if name != "ORCS"}}

    @classmethod
    def from_snapshot(cls, snapshot):
        oracle = object.__new__(cls)
        oracle.sha256 = snapshot["source_sha256"]
        oracle.names = {name: RangeValue(**value) for name, value in snapshot["names"].items()}
        def cell(value):
            raw = value["value"]
            if isinstance(raw, str) and raw.startswith("#"):
                raw = FormulaError(raw)
            return CellData(raw, value["formula"], value["formula_base"])
        oracle.sheets = {name: {c: cell(value) for c, value in cells.items()}
                         for name, cells in snapshot["sheets"].items()}
        oracle._initialize()
        return oracle
