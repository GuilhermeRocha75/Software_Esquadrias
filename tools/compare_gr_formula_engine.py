"""Compara as fórmulas GR do XLSM com a Engine 0.25 sem Microsoft Excel.

As diferenças aceitas são explícitas e congeladas por caso. Uma mudança no
resultado legado ou no resultado físico da Engine faz o comando falhar.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any

from gr_formula_oracle import GrFormulaOracle


REPOSITORY = Path(__file__).resolve().parents[1]
ENGINE_ROOT = (
    REPOSITORY
    / "engine/Software_Esquadrias_Starter + Versões"
    / "Software_Esquadrias_Starter_v0.3.1_GUI"
    / "Software_Esquadrias_Starter_v0.3.1_GUI"
)
sys.path.insert(0, str(ENGINE_ROOT / "src"))

from esquadrias_engine import (  # noqa: E402
    GrConfiguration,
    ShutterConfiguration,
    ShutterMode,
    calculate_gr,
)
from esquadrias_engine.gr_v06 import GR_CREMONA_WINDOW_800  # noqa: E402


CANONICAL_CASES = {
    270: {
        "formula_total": 1343.086267714286,
        "engine_total": 1368.725685,
        "corrections": [
            "vedações físicas ausentes no total legado",
            "geometria e consumo físico do modo misto",
            "parafusos de reforço da travessa",
            "AF histórico incompatível normalizado para folha sem travessa",
        ],
    },
    11480: {
        "formula_total": 1165.39716,
        "engine_total": 1214.70516,
        "corrections": [
            "cremona histórica vazia normalizada para CRE12",
            "vedações físicas da folha de janela",
            "comprimento físico do reforço do marco",
        ],
    },
    14891: {
        "formula_total": 1697.59975,
        "engine_total": 1863.30363,
        "corrections": [
            "geometria física do vidro e das baguetes da bandeira superior",
            "vedações físicas ausentes no total legado",
        ],
    },
    15295: {
        "formula_total": 3791.31241,
        "engine_total": 5594.46035,
        "corrections": [
            "dois vãos físicos de vidro na bandeira superior",
            "baguetes e reforço da divisão vertical",
            "parafusos do reforço da travessa",
            "vedações físicas ausentes no total legado",
        ],
    },
    16527: {
        "formula_total": 3767.69169,
        "engine_total": 4991.80917,
        "corrections": [
            "acessórios completos e quantidade física de talas da persiana",
            "geometria física de vidros e baguetes",
            "tela retrátil calculada pelo quadro completo",
            "cremona histórica vazia normalizada para CRE12",
            "vedações e reforço da divisão da bandeira inferior",
        ],
    },
    18132: {
        "formula_total": 1810.46189,
        "engine_total": 2049.99025,
        "corrections": [
            "acessórios completos e quantidade física de talas da persiana",
            "vedações físicas ausentes no total legado",
        ],
    },
    18545: {
        "formula_total": 1418.5308554285714,
        "engine_total": 1445.782455,
        "corrections": ["vedações físicas ausentes no total legado"],
    },
}


def _number(values: dict[str, Any], column: str) -> float:
    value = values.get(column)
    if value in (None, ""):
        return 0.0
    return float(str(value).replace(",", "."))


def configuration_from_orcs(values: dict[str, Any]) -> tuple[GrConfiguration, list[str]]:
    normalizations: list[str] = []
    panel_mode = values.get("R") or "VIDRO INTEIRO"
    leaf_horizontal = int(_number(values, "AF"))
    leaf_vertical = int(_number(values, "AG"))
    if panel_mode == "SUPERIOR VIDRO/INFERIOR PAINEL" and (leaf_horizontal or leaf_vertical):
        leaf_horizontal = 0
        leaf_vertical = 0
        normalizations.append("AF/AG históricos ignorados no modo misto")

    glass_description = values.get("K")
    if panel_mode == "PAINEL COMPLETO" and glass_description:
        glass_description = None
        normalizations.append("vidro residual ignorado no modo painel completo")

    shutter = None
    shutter_mode = values.get("L")
    if shutter_mode and shutter_mode != ShutterMode.NONE.value:
        shutter = ShutterConfiguration(
            mode=ShutterMode(shutter_mode),
            box_description=values.get("M") or "CAIXA DE 200MM",
            slat_description=values.get("N") or "TALA DE PVC 40MM",
        )

    cremona = values.get("Q")
    is_window = values.get("H") == "FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN"
    if is_window and values.get("P") == "MAÇANETA COM CREMONA SEM CHAVE" and not cremona:
        cremona = GR_CREMONA_WINDOW_800
        normalizations.append("cremona histórica vazia substituída por CRE12")

    reinforcement = values.get("Z")
    if not reinforcement or reinforcement == "SEM REFORÇO EXTRUTURAL":
        reinforcement = None

    hinge = values.get("U")
    if hinge == "DOBRADIÇA PÉRNIO":
        hinge = "DOBRADIÇA PÊRNIO"
        normalizations.append("grafia histórica PÉRNIO normalizada para PÊRNIO")

    configuration = GrConfiguration(
        width_mm=_number(values, "D"),
        height_mm=_number(values, "E"),
        quantity=int(_number(values, "F")),
        leaf_count=int(str(values.get("G") or "1").split()[0]),
        leaf_system=values.get("H"),
        application=values.get("I"),
        panel_mode=panel_mode,
        module_mode=values.get("Y") or "MÓDULO ÚNICO",
        closure_mode=values.get("P"),
        cremona_description=cremona,
        hinge_description=hinge,
        internal_finish=values.get("S") or "GUARNIÇÃO DE 70MM",
        external_finish=values.get("T") or "BARRA CHATA DE 30MM",
        screen_enabled=values.get("O") == "COM TELA MOSQUITEIRA",
        bottom_flag_height_mm=_number(values, "AA"),
        top_flag_height_mm=_number(values, "AB"),
        leaf_horizontal_transoms=leaf_horizontal,
        leaf_vertical_transoms=leaf_vertical,
        structural_reinforcement=reinforcement,
        glass_description=glass_description,
        mixed_split_from_bottom_mm=_number(values, "AC") or None,
        shutter=shutter,
        bottom_flag_vertical_transoms=int(_number(values, "AH")),
        bottom_flag_horizontal_transoms=int(_number(values, "AI")),
        top_flag_vertical_transoms=int(_number(values, "AJ")),
        top_flag_horizontal_transoms=int(_number(values, "AK")),
    )
    return configuration, normalizations


def compare_case(oracle: GrFormulaOracle, row: int) -> dict[str, Any]:
    if row not in CANONICAL_CASES:
        raise ValueError(f"ORCS {row} não possui delta técnico homologado")
    expected = CANONICAL_CASES[row]
    formula_case = oracle.calculate_orcs_row(row)
    formula_total = formula_case["cells"]["AO2"]
    if not isinstance(formula_total, (int, float)):
        raise ValueError(f"ORCS {row}: fórmula AO2 retornou {formula_total}")
    configuration, normalizations = configuration_from_orcs(oracle._technical_row(row))
    engine_result = calculate_gr(configuration)
    engine_total = engine_result.unit_cost
    formula_ok = math.isclose(formula_total, expected["formula_total"], rel_tol=0, abs_tol=1e-6)
    engine_ok = math.isclose(engine_total, expected["engine_total"], rel_tol=0, abs_tol=1e-6)
    status = "DOCUMENTED_CORRECTION" if formula_ok and engine_ok else "FAIL"
    if math.isclose(formula_total, engine_total, rel_tol=0, abs_tol=1e-6):
        status = "EXACT_MATCH" if formula_ok and engine_ok else "FAIL"
    return {
        "orcs_row": row,
        "status": status,
        "xlsm_formula_total": round(float(formula_total), 6),
        "engine_total": round(float(engine_total), 6),
        "delta_engine_minus_xlsm": round(float(engine_total - formula_total), 6),
        "formula_baseline_ok": formula_ok,
        "engine_baseline_ok": engine_ok,
        "normalizations": normalizations,
        "documented_corrections": expected["corrections"],
    }


def compare(workbook: Path, rows: list[int]) -> dict[str, Any]:
    oracle = GrFormulaOracle(workbook)
    cases = [compare_case(oracle, row) for row in rows]
    return {
        "source_sha256": oracle.sha256,
        "engine_version": "GR_ENGINE_0.25.0",
        "policy": "igualdade literal ou diferença física previamente documentada e congelada",
        "passed": all(case["status"] != "FAIL" for case in cases),
        "summary": {
            "total": len(cases),
            "exact_matches": sum(case["status"] == "EXACT_MATCH" for case in cases),
            "documented_corrections": sum(case["status"] == "DOCUMENTED_CORRECTION" for case in cases),
            "failures": sum(case["status"] == "FAIL" for case in cases),
        },
        "cases": cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--rows", nargs="+", type=int, default=list(CANONICAL_CASES))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = compare(args.workbook, args.rows)
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(serialized, encoding="utf-8")
    else:
        sys.stdout.write(serialized)
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
