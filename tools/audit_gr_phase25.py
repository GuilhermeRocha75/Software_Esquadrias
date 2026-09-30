"""Auditoria sanitizada das ferragens GR (Fase 25).

Lê o XLSM oficial diretamente como OpenXML, sem modificá-lo. A saída contém
somente dados técnicos, contagens e números de linha da ORCS.

Uso:
    python tools/audit_gr_phase25.py arquivo.xlsm
    python tools/audit_gr_phase25.py arquivo.xlsm --output snapshot.json
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
from typing import Any
from zipfile import ZipFile

from audit_gr_phase23 import (
    GR_APPLICATIONS,
    GR_CLOSURES,
    GR_HINGES,
    GR_SYSTEM_EXTERNAL,
    GR_SYSTEM_INTERNAL,
    GR_SYSTEM_WINDOW,
    GR_SYSTEMS,
    _technical_rows,
)
from audit_maxim_ar_phase3a import (
    column_label,
    is_nonzero,
    normalized_text,
    row_number,
    sha256,
    shared_strings,
    sheet_cells,
    sheet_targets,
)


OFFICIAL_SHA = "96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160"
AUDIT_VERSION = "GR_HARDWARE_AUDIT_0.25.0"

MONOPOINT = "MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE"
MULTIPOINT = "MAÇANETA DUPLA COM FECHADURA MULTIPONTO E CHAVE"
WINDOW_CREMONA = "MAÇANETA COM CREMONA SEM CHAVE"
HINGE_90 = "DOBRADIÇA 90MM"
HINGE_OB = "DOBRADIÇA SISTEMA OB"
HINGE_PERNIO = "DOBRADIÇA PÉRNIO"
OB_CREMONAS = {
    "CREMONA OSCILO/GIRO COMP. 400MM E:15MM",
    "CREMONA OSCILO/GIRO COMP. 900MM E:15MM",
    "CREMONA OSCILO/GIRO COMP. 1100MM E:15MM",
    "CREMONA OSCILO/GIRO COMP. 1400MM E:15MM",
    "CREMONA OSCILO/GIRO COMP. 1900MM E:15MM",
}

CLASSIFICATIONS = (
    "ALREADY_SUPPORTED",
    "SUPPORTED_AFTER_APPLICATION_INDEPENDENCE",
    "REQUIRES_ENGINE_IMPLEMENTATION",
    "REQUIRES_PHYSICAL_CONFIRMATION",
    "INVALID_SOURCE_DATA",
)

COMBINATION_COLUMNS = {
    "leaf_system": "H",
    "leaf_count": "G",
    "historical_application": "I",
    "closure": "P",
    "cremona": "Q",
    "hinge": "U",
}


def _counter(rows: list[tuple[int, dict[str, str]]], column: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for line, values in rows:
        grouped[normalized_text(values.get(column, ""))].append(line)
    return [
        {"value": value, "count": len(lines), "orcs_rows": lines}
        for value, lines in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))
    ]


def _panel_mode(row: dict[str, str]) -> str:
    value = normalized_text(row.get("R", ""))
    if not value:
        return "VIDRO INTEIRO"
    if value == "SUPERIOR VIDRO/INFERIOR PAINEL":
        return "MODO MISTO"
    return value


def _flag_mode(row: dict[str, str]) -> str:
    bottom = is_nonzero(row.get("AA", ""))
    top = is_nonzero(row.get("AB", ""))
    if bottom and top:
        return "BANDEIRA INFERIOR E SUPERIOR"
    if bottom:
        return "BANDEIRA INFERIOR"
    if top:
        return "BANDEIRA SUPERIOR"
    return "SEM BANDEIRA"


def _expected_application(leaf_system: str) -> str | None:
    if leaf_system == GR_SYSTEM_WINDOW:
        return "JANELA"
    if leaf_system in {GR_SYSTEM_INTERNAL, GR_SYSTEM_EXTERNAL}:
        return "PORTA"
    return None


def _source_invalid(row: dict[str, str]) -> bool:
    system = normalized_text(row.get("H", ""))
    application = normalized_text(row.get("I", ""))
    leaf_count = normalized_text(row.get("G", ""))
    closure = normalized_text(row.get("P", ""))
    cremona = normalized_text(row.get("Q", ""))
    hinge = normalized_text(row.get("U", ""))
    if system not in GR_SYSTEMS or application not in GR_APPLICATIONS:
        return True
    if leaf_count not in {"1 FOLHA", "2 FOLHAS"}:
        return True
    if not closure or not hinge:
        return True
    # Q é seleção de cremona. Texto de vedação ou cremona associada a um
    # fechamento que não usa cremona é evidência de coluna contaminada.
    if cremona and closure in GR_CLOSURES and (
        cremona not in OB_CREMONAS or closure != WINDOW_CREMONA
    ):
        return True
    return False


def _hardware_supported(row: dict[str, str]) -> bool:
    """Recortes de ferragem já comprovados pela Engine v0.24.

    A aplicação histórica não participa desta decisão; leaf_system é o
    condutor físico, conforme a confirmação da Fase 24.
    """
    system = normalized_text(row.get("H", ""))
    leaf_count = normalized_text(row.get("G", ""))
    closure = normalized_text(row.get("P", ""))
    cremona = normalized_text(row.get("Q", ""))
    hinge = normalized_text(row.get("U", ""))

    if hinge == HINGE_90:
        if system in {GR_SYSTEM_INTERNAL, GR_SYSTEM_EXTERNAL}:
            return closure in {MONOPOINT, MULTIPOINT} and not cremona
        return system == GR_SYSTEM_WINDOW and closure == WINDOW_CREMONA and not cremona

    if hinge == HINGE_OB:
        # v0.9: janela de uma folha, conjunto OB e cremona explicitamente
        # selecionada. Ausência do comprimento não é inferida.
        if system == GR_SYSTEM_WINDOW:
            return (
                leaf_count == "1 FOLHA"
                and closure == WINDOW_CREMONA
                and cremona in OB_CREMONAS
            )
        # O conjunto exato de porta externa monoponto foi comprovado na Fase
        # 20. Outros usos do OB permanecem evidência, não suporte por analogia.
        return (
            system == GR_SYSTEM_EXTERNAL
            and leaf_count == "1 FOLHA"
            and closure == MONOPOINT
            and not cremona
        )
    return False


def _requires_physical_confirmation(row: dict[str, str]) -> bool:
    system = normalized_text(row.get("H", ""))
    leaf_count = normalized_text(row.get("G", ""))
    closure = normalized_text(row.get("P", ""))
    cremona = normalized_text(row.get("Q", ""))
    hinge = normalized_text(row.get("U", ""))

    if hinge not in GR_HINGES:
        return True
    if closure not in GR_CLOSURES:
        return True
    if hinge == HINGE_OB and closure == WINDOW_CREMONA and not cremona:
        return True
    if hinge == HINGE_OB and leaf_count == "2 FOLHAS":
        return True
    # Um conjunto OB de janela com fechadura, ou de porta interna, aparece no
    # histórico, mas não foi fisicamente homologado como conjunto completo.
    if hinge == HINGE_OB and (
        system == GR_SYSTEM_INTERNAL
        or (system == GR_SYSTEM_WINDOW and closure != WINDOW_CREMONA)
    ):
        return True
    return False


def _classify(row: dict[str, str]) -> tuple[str, str]:
    if _source_invalid(row):
        return "INVALID_SOURCE_DATA", "campo técnico ausente, inválido ou contaminado"
    if _requires_physical_confirmation(row):
        return "REQUIRES_PHYSICAL_CONFIRMATION", "conjunto não homologado fisicamente"
    if not _hardware_supported(row):
        return "REQUIRES_ENGINE_IMPLEMENTATION", "combinação histórica fora dos recortes implementados"

    system = normalized_text(row.get("H", ""))
    application = normalized_text(row.get("I", ""))
    if application != _expected_application(system):
        return (
            "SUPPORTED_AFTER_APPLICATION_INDEPENDENCE",
            "ferragem suportada pelo tipo físico de folha; aplicação é apenas histórica",
        )
    return "ALREADY_SUPPORTED", "combinação física já suportada antes da Fase 24"


def _combination_key(row: dict[str, str], classification: str) -> tuple[str, ...]:
    return (
        *(normalized_text(row.get(column, "")) for column in COMBINATION_COLUMNS.values()),
        _panel_mode(row),
        _flag_mode(row),
        normalized_text(row.get("O", "")),
        normalized_text(row.get("L", "")),
        classification,
    )


def _combinations(rows: list[tuple[int, dict[str, str]]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[int]] = defaultdict(list)
    reasons: dict[tuple[str, ...], str] = {}
    for line, row in rows:
        classification, reason = _classify(row)
        key = _combination_key(row, classification)
        grouped[key].append(line)
        reasons[key] = reason

    result = []
    field_names = [
        *COMBINATION_COLUMNS,
        "panel_mode",
        "flag_mode",
        "screen",
        "shutter",
        "classification",
    ]
    for key, lines in sorted(grouped.items()):
        item = dict(zip(field_names, key))
        item.update({"reason": reasons[key], "count": len(lines), "orcs_rows": lines})
        result.append(item)
    return result


def _phase23_sets(rows: list[tuple[int, dict[str, str]]]) -> dict[str, list[int]]:
    closure_compatibility = []
    special = []
    unsupported_hinge = []
    for line, row in rows:
        system = normalized_text(row.get("H", ""))
        application = normalized_text(row.get("I", ""))
        closure = normalized_text(row.get("P", ""))
        hinge = normalized_text(row.get("U", ""))
        if (
            application == "JANELA"
            and system == GR_SYSTEM_WINDOW
            and closure != WINDOW_CREMONA
        ) or (
            application == "PORTA"
            and system in {GR_SYSTEM_INTERNAL, GR_SYSTEM_EXTERNAL}
            and closure not in {MONOPOINT, MULTIPOINT}
        ):
            closure_compatibility.append(line)
        if closure not in GR_CLOSURES:
            special.append(line)
        if hinge not in GR_HINGES:
            unsupported_hinge.append(line)
    return {
        "closure_application_compatibility": closure_compatibility,
        "special_closures": special,
        "hinge_pernio_or_invalid": unsupported_hinge,
    }


def _cell_map(archive: ZipFile, sheet: str) -> dict[str, dict[str, str]]:
    targets = sheet_targets(archive)
    strings = shared_strings(archive)
    return {
        coordinate: {"value": value, "formula": formula}
        for coordinate, value, formula in sheet_cells(archive, targets[sheet], strings)
    }


def _formula_audit(archive: ZipFile) -> dict[str, Any]:
    gr = _cell_map(archive, "GR")
    catalog = _cell_map(archive, "LISTAFERRA")
    catalog_rows = (24, 35, 46, 47, 50, 51, 52, 53, 54, 55, 61, 62, 63, 64, 65, 66, 72, 73)
    catalog_refs = {
        f"LISTAFERRA!A{line}:C{line}": {
            "description": catalog.get(f"A{line}", {}).get("value", ""),
            "material_code": catalog.get(f"B{line}", {}).get("value", ""),
            "unit_price": catalog.get(f"C{line}", {}).get("value", ""),
        }
        for line in catalog_rows
    }
    conditions = {
        105: "U3=1 (OB): DOB6 x folhas; caso contrário: U2 x 3 x folhas",
        106: "U3=1 (OB): DOB7 x folhas; caso contrário zero",
        107: "U3=1 (OB): DOB8 x folhas; caso contrário zero",
        108: "U3=1 (OB): DOB9 x folhas; caso contrário zero",
        109: "U3=1 (OB): DOB10 x folhas; caso contrário zero",
        110: "U3=1 (OB): DOB11 x folhas; caso contrário zero",
        111: "sempre 1; P3=1/2 usa MAC4, P3=3 usa MAC1, demais usam MAC5",
        112: "sempre 1; P3=1 usa FEC5, P3=2 usa FEC6, demais usam Q2",
        113: "P3=1/2: CIL1 x 1; demais zero",
        114: "P3=1: CON1 x 4; P3=2: zero; demais CON1 x 2",
        115: "P3=1/2: CON2 x 1; demais zero",
        116: "duas folhas: CON3 x 2; uma folha: zero",
        117: "duas folhas: FEC7 x 2; uma folha: zero",
        118: "PAR2 conforme comprimentos e quantidades de perfis reforçados",
        119: "PAR1=(G105*8)+(G111+G112+G114)*2",
    }
    references = {
        105: [61], 106: [62], 107: [63], 108: [64], 109: [65], 110: [66],
        111: [51, 24, 53], 112: [50, 52], 113: [54], 114: [35],
        115: [55], 116: [73], 117: [72], 118: [47], 119: [46],
    }
    dependencies = {
        105: ["hinge", "leaf_count"],
        106: ["hinge", "leaf_count"],
        107: ["hinge", "leaf_count"],
        108: ["hinge", "leaf_count"],
        109: ["hinge", "leaf_count"],
        110: ["hinge", "leaf_count"],
        111: ["closure"],
        112: ["closure", "cremona"],
        113: ["closure"],
        114: ["closure"],
        115: ["closure"],
        116: ["leaf_count"],
        117: ["leaf_count"],
        118: [],
        119: ["hinge", "closure", "cremona", "leaf_count"],
    }
    lines = []
    for line in range(105, 120):
        formulas = {
            column: gr.get(f"{column}{line}", {}).get("formula", "")
            for column in ("B", "C", "G", "I")
            if gr.get(f"{column}{line}", {}).get("formula", "")
        }
        lines.append({
            "gr_row": line,
            "label": gr.get(f"A{line}", {}).get("value", ""),
            "activation_and_quantity": conditions[line],
            "dependencies": dependencies[line],
            "catalog_references": [f"LISTAFERRA!A{item}:C{item}" for item in references[line]],
            "material_options": [
                catalog_refs[f"LISTAFERRA!A{item}:C{item}"]
                for item in references[line]
            ],
            "formulas": formulas,
        })
    return {
        "selector_formulas": {
            coordinate: gr.get(coordinate, {}).get("formula", "")
            for coordinate in ("P3", "Q3", "U3")
        },
        "lines_105_119": lines,
        "catalog_references": catalog_refs,
        "par1_rule": {
            "cell": "GR!G119",
            "formula": gr.get("G119", {}).get("formula", ""),
            "interpretation": "8 parafusos por G105 e 2 por unidade de G111, G112 e G114; G106:G110, G113, G115:G117 não entram na fórmula legada.",
        },
    }


def _rows_by_class(rows: list[tuple[int, dict[str, str]]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[int]] = {name: [] for name in CLASSIFICATIONS}
    for line, row in rows:
        grouped[_classify(row)[0]].append(line)
    return {
        name: {"count": len(lines), "orcs_rows": lines}
        for name, lines in grouped.items()
    }


def build_report(workbook: Path) -> dict[str, Any]:
    digest = sha256(workbook)
    if digest != OFFICIAL_SHA:
        raise ValueError("SHA-256 do XLSM não corresponde à fonte oficial")

    with ZipFile(workbook) as archive:
        rows = _technical_rows(archive)
        formula_audit = _formula_audit(archive)

    phase23 = _phase23_sets(rows)
    row_lookup = dict(rows)
    phase23_closure = phase23["closure_application_compatibility"]
    closure_classifications = Counter(_classify(row_lookup[line])[0] for line in phase23_closure)
    independence_resolved = [
        line for line in phase23_closure
        if _classify(row_lookup[line])[0] == "SUPPORTED_AFTER_APPLICATION_INDEPENDENCE"
    ]
    special_rows = [(line, row_lookup[line]) for line in phase23["special_closures"]]
    hinge_rows = [(line, row_lookup[line]) for line in phase23["hinge_pernio_or_invalid"]]
    intersection = sorted(set(phase23["special_closures"]) & set(phase23["hinge_pernio_or_invalid"]))

    classifications = _rows_by_class(rows)
    invalid_rows = classifications["INVALID_SOURCE_DATA"]["orcs_rows"]
    combination_rows = _combinations(rows)
    return {
        "audit_version": AUDIT_VERSION,
        "scope": "AUDITORIA_REPRODUZIVEL_SEM_ALTERACAO_DE_CALCULOS",
        "official_xlsm_sha256": digest,
        "orcs_gr_rows": len(rows),
        "inventory": {
            "closures_column_p": _counter(rows, "P"),
            "cremonas_column_q": _counter(rows, "Q"),
            "hinges_column_u": _counter(rows, "U"),
        },
        "phase23_reproduction": {
            name: {"count": len(lines), "orcs_rows": lines}
            for name, lines in phase23.items()
        },
        "phase24_effect_on_the_66": {
            "resolved_automatically_count": len(independence_resolved),
            "orcs_rows": independence_resolved,
            "explanation": "Os 66 registros usam aplicação histórica coerente com leaf_system; são disjuntos dos 47 casos de independência da Fase 24.",
            "remaining_classifications": dict(sorted(closure_classifications.items())),
        },
        "special_closures": {
            "inventory": _counter(special_rows, "P"),
            "count": len(special_rows),
        },
        "hinge_pernio_or_invalid": {
            "inventory": _counter(hinge_rows, "U"),
            "count": len(hinge_rows),
        },
        "special_closure_and_unsupported_hinge_intersection": {
            "count": len(intersection),
            "orcs_rows": intersection,
        },
        "classification_summary": classifications,
        "classification_total": sum(item["count"] for item in classifications.values()),
        "combinations": combination_rows,
        "separations": {
            "panel_mode": _counter([(line, {"V": _panel_mode(row)}) for line, row in rows], "V"),
            "flag_mode": _counter([(line, {"V": _flag_mode(row)}) for line, row in rows], "V"),
            "screen": _counter(rows, "O"),
            "shutter": _counter(rows, "L"),
        },
        "formula_audit": formula_audit,
        "incomplete_or_invalid": {
            "count": len(invalid_rows),
            "orcs_rows": invalid_rows,
            "criteria": "folha/aplicação/contagem inválida, fechamento/dobradiça ausente ou coluna Q contaminada",
        },
        "classification_policy": {
            "physical_driver": "leaf_system (ORCS H)",
            "historical_only": "application (ORCS I)",
            "no_analogy": True,
            "classes": list(CLASSIFICATIONS),
        },
        "privacy": "Somente valores técnicos, contagens e números de linha ORCS são emitidos; campos privados não são lidos.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = build_report(args.workbook)
    except ValueError as exc:
        raise SystemExit(f"ERRO: {exc}") from exc
    body = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(body, encoding="utf-8")
    else:
        print(body, end="")


if __name__ == "__main__":
    main()
