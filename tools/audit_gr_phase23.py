"""Auditoria sanitizada de cobertura histórica da família GR (Fase 23).

O arquivo oficial é lido diretamente como OpenXML e nunca é modificado. A
saída contém somente contagens, vocabulário técnico e números de linha ORCS;
campos de cliente, item e local não são carregados no relatório.

Uso:
    python tools/audit_gr_phase23.py arquivo.xlsm
    python tools/audit_gr_phase23.py arquivo.xlsm --compare snapshot.json
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any
from zipfile import ZipFile

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

ENGINE_SRC = (
    Path(__file__).resolve().parents[1]
    / "engine"
    / "Software_Esquadrias_Starter + Versões"
    / "Software_Esquadrias_Starter_v0.3.1_GUI"
    / "Software_Esquadrias_Starter_v0.3.1_GUI"
    / "src"
)
sys.path.insert(0, str(ENGINE_SRC))
from esquadrias_engine.catalog import GLASSES  # noqa: E402


OFFICIAL_SHA = "96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160"
AUDIT_VERSION = "GR_COVERAGE_AUDIT_0.23.0"

GR_SYSTEM_INTERNAL = "FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN"
GR_SYSTEM_EXTERNAL = "FOLHA DE PORTA ABERTURA EXTERNA 60X104MM - DESIGN"
GR_SYSTEM_WINDOW = "FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN"
GR_SYSTEMS = {GR_SYSTEM_INTERNAL, GR_SYSTEM_EXTERNAL, GR_SYSTEM_WINDOW}
GR_APPLICATIONS = {"PORTA", "JANELA"}
GR_CLOSURES = {
    "MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE",
    "MAÇANETA DUPLA COM FECHADURA MULTIPONTO E CHAVE",
    "MAÇANETA COM CREMONA SEM CHAVE",
}
GR_HINGES = {"DOBRADIÇA 90MM", "DOBRADIÇA SISTEMA OB"}

GR_GLASS_CATALOG = {normalized_text(glass.description) for glass in GLASSES.values()}

SAFE_COLUMNS = {
    "D", "E", "F", "G", "H", "I", "K", "L", "M", "N", "O", "P", "Q",
    "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "AA", "AB", "AC",
    "AD", "AE", "AF", "AG", "AH", "AI", "AJ", "AK", "AO",
}


def _technical_rows(archive: ZipFile) -> list[tuple[int, dict[str, str]]]:
    targets = sheet_targets(archive)
    strings = shared_strings(archive)
    rows: dict[int, dict[str, str]] = {}
    for coordinate, value, _formula in sheet_cells(archive, targets["ORCS"], strings):
        row = row_number(coordinate)
        column = column_label(coordinate)
        if row > 1 and column in SAFE_COLUMNS:
            rows.setdefault(row, {})[column] = value
    return [
        (row, values)
        for row, values in sorted(rows.items())
        if normalized_text(values.get("X", "")) == "GR"
    ]


def _leaf_count(row: dict[str, str]) -> int:
    return 2 if normalized_text(row.get("G", "")) == "2 FOLHAS" else 1


def _screen(row: dict[str, str]) -> bool:
    return normalized_text(row.get("O", "")) == "COM TELA MOSQUITEIRA"


def _has_flag(row: dict[str, str]) -> bool:
    return is_nonzero(row.get("AA", "")) or is_nonzero(row.get("AB", ""))


def _flag_scope_supported(row: dict[str, str]) -> bool:
    """Reflete estritamente os gates de bandeira da GR_ENGINE_0.22.0."""
    bottom = is_nonzero(row.get("AA", ""))
    top = is_nonzero(row.get("AB", ""))
    lower_v = int(float(row.get("AH", "0") or 0))
    lower_h = int(float(row.get("AI", "0") or 0))
    upper_v = int(float(row.get("AJ", "0") or 0))
    upper_h = int(float(row.get("AK", "0") or 0))
    leaf_count = _leaf_count(row)
    system = normalized_text(row.get("H", ""))
    application = normalized_text(row.get("I", ""))
    panel = normalized_text(row.get("R", "")) or "VIDRO INTEIRO"
    screen = _screen(row)

    if lower_h or upper_h:
        return False
    if upper_v == 1:
        return (
            top and not bottom and lower_v == 0
            and application == "PORTA" and leaf_count == 2
            and system == GR_SYSTEM_INTERNAL and panel == "VIDRO INTEIRO"
            and not screen
        )
    if lower_v == 2:
        return (
            bottom and not top and application == "PORTA" and leaf_count == 1
            and system == GR_SYSTEM_EXTERNAL and panel == "VIDRO INTEIRO"
            and not screen
        )
    if lower_v == 3:
        return (
            bottom and not top and application == "JANELA" and leaf_count == 2
            and system == GR_SYSTEM_WINDOW and panel == "VIDRO INTEIRO"
            and not screen
        )
    if lower_v == 1:
        return (
            bottom and not top and application == "JANELA" and leaf_count == 2
            and system == GR_SYSTEM_WINDOW and panel == "VIDRO INTEIRO" and screen
        )
    if lower_v or upper_v:
        return False
    if bottom and top:
        return (
            application == "JANELA" and leaf_count == 1
            and system == GR_SYSTEM_WINDOW and panel == "VIDRO INTEIRO"
            and not screen
        )
    if bottom:
        return (
            application == "JANELA" and leaf_count == 1
            and system == GR_SYSTEM_WINDOW and panel == "VIDRO INTEIRO"
            and not screen
        )
    if top:
        if application != "PORTA" or screen:
            return False
        if leaf_count == 1:
            return system in {GR_SYSTEM_INTERNAL, GR_SYSTEM_EXTERNAL}
        return system == GR_SYSTEM_INTERNAL and panel == "VIDRO INTEIRO"
    return True


def _counter(rows: list[tuple[int, dict[str, str]]], column: str) -> dict[str, int]:
    values = Counter(normalized_text(row.get(column, "")) for _, row in rows)
    return dict(sorted(values.items(), key=lambda item: (-item[1], item[0])))


def build_report(workbook: Path) -> dict[str, Any]:
    digest = sha256(workbook)
    if digest != OFFICIAL_SHA:
        raise ValueError("SHA-256 do XLSM não corresponde à fonte oficial")

    with ZipFile(workbook) as archive:
        rows = _technical_rows(archive)

    flag_rows = [(row_id, row) for row_id, row in rows if _has_flag(row)]
    flag_pending = [row_id for row_id, row in flag_rows if not _flag_scope_supported(row)]
    application_independence = [
        row_id for row_id, row in rows
        if normalized_text(row.get("I", "")) in GR_APPLICATIONS
        and normalized_text(row.get("H", "")) in GR_SYSTEMS
        and (
            ("PORTA" in normalized_text(row.get("H", "")) and normalized_text(row.get("I", "")) == "JANELA")
            or ("JANELA" in normalized_text(row.get("H", "")) and normalized_text(row.get("I", "")) == "PORTA")
        )
    ]
    special_closures = [
        row_id for row_id, row in rows
        if normalized_text(row.get("P", "")) not in GR_CLOSURES
    ]
    closure_compatibility = [
        row_id for row_id, row in rows
        if (
            normalized_text(row.get("I", "")) == "JANELA"
            and normalized_text(row.get("H", "")) == GR_SYSTEM_WINDOW
            and normalized_text(row.get("P", "")) != "MAÇANETA COM CREMONA SEM CHAVE"
        ) or (
            normalized_text(row.get("I", "")) == "PORTA"
            and normalized_text(row.get("H", "")) in {GR_SYSTEM_INTERNAL, GR_SYSTEM_EXTERNAL}
            and normalized_text(row.get("P", "")) not in {
                "MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE",
                "MAÇANETA DUPLA COM FECHADURA MULTIPONTO E CHAVE",
            }
        )
    ]
    catalog_missing = [
        row_id for row_id, row in rows
        if row.get("K", "").strip()
        and normalized_text(row.get("K", "")) not in GR_GLASS_CATALOG
    ]
    unsupported_hinges = [
        row_id for row_id, row in rows
        if normalized_text(row.get("U", "")) not in GR_HINGES
    ]
    mixed_rows = [row_id for row_id, row in rows if normalized_text(row.get("R", "")) == "SUPERIOR VIDRO/INFERIOR PAINEL"]
    mixed_with_explicit_split = [row_id for row_id, row in rows if row_id in mixed_rows and is_nonzero(row.get("AC", ""))]
    leaf_grid_rows = [
        row_id for row_id, row in rows
        if is_nonzero(row.get("AF", "")) or is_nonzero(row.get("AG", ""))
    ]
    prohibited_leaf_grid = [row_id for row_id in leaf_grid_rows if row_id not in mixed_with_explicit_split]
    separate_modules = sum(
        "SEPARAD" in normalized_text(row.get("Y", "")) for _, row in rows
    )
    structural_reinforcement = sum(
        bool(normalized_text(row.get("Z", "")))
        and "SEM REFOR" not in normalized_text(row.get("Z", ""))
        for _, row in rows
    )
    malformed_rows = sorted({
        row_id for row_id, row in rows
        if normalized_text(row.get("H", "")) not in GR_SYSTEMS
        or normalized_text(row.get("I", "")) not in GR_APPLICATIONS
        or normalized_text(row.get("Y", "")) != "MÓDULO ÚNICO"
        or normalized_text(row.get("Z", "")) != "SEM REFORÇO EXTRUTURAL"
    })

    return {
        "audit_version": AUDIT_VERSION,
        "official_xlsm_sha256": digest,
        "orcs_gr_rows": len(rows),
        "historical_inventory": {
            "leaf_systems": _counter(rows, "H"),
            "applications": _counter(rows, "I"),
            "leaf_counts": _counter(rows, "G"),
            "panel_modes": _counter(rows, "R"),
            "screens": _counter(rows, "O"),
            "shutters": _counter(rows, "L"),
            "hinges": _counter(rows, "U"),
            "module_modes": _counter(rows, "Y"),
            "structural_reinforcement": _counter(rows, "Z"),
            "flag_rows": len(flag_rows),
            "flag_subdivision_rows": sum(
                any(is_nonzero(row.get(column, "")) for column in ("AH", "AI", "AJ", "AK"))
                for _, row in flag_rows
            ),
            "mixed_panel_rows": len(mixed_rows),
            "mixed_panel_explicit_split_rows": len(mixed_with_explicit_split),
        },
        "historically_absent": {
            "separate_modules": separate_modules,
            "structural_reinforcement": structural_reinforcement,
        },
        "resolved_or_prohibited": {
            "leaf_grid_inside_mobile_leaf": {
                "status": "PROHIBITED_PHYSICAL",
                "rows": prohibited_leaf_grid,
                "count": len(prohibited_leaf_grid),
                "note": "AF/AG não pertencem à folha móvel; os três demais registros AF representam a travessa do modo misto já modelada por mixed_split_from_bottom_mm.",
            },
        },
        "pending_real": {
            "application_leaf_system_independence": {
                "count": len(application_independence),
                "rows": application_independence,
            },
            "flag_combinations_outside_v022": {
                "count": len(flag_pending),
                "rows": flag_pending,
            },
            "special_closures": {
                "count": len(special_closures),
                "rows": special_closures,
            },
            "closure_application_compatibility": {
                "count": len(closure_compatibility),
                "rows": closure_compatibility,
            },
            "glass_catalog_missing": {
                "count": len(catalog_missing),
                "rows": catalog_missing,
            },
            "hinge_pernio_or_invalid": {
                "count": len(unsupported_hinges),
                "rows": unsupported_hinges,
            },
        },
        "source_data_review": {
            "count": len(malformed_rows),
            "rows": malformed_rows,
        },
        "gate": {
            "historical_coverage_closed": False,
            "purchase_plan_supported": False,
            "main_ready": False,
            "status": "FASE_23_AUDITADA_COM_PENDENCIAS_REAIS",
        },
        "privacy": "Nenhum nome, contato, endereço, código de cliente, item ou local é emitido.",
    }


def _assert_subset(expected: Any, actual: Any, path: str = "report") -> None:
    """Permite snapshots concisos sem esconder divergências nos campos fixados."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            raise ValueError(f"{path}: esperado objeto")
        for key, value in expected.items():
            if key not in actual:
                raise ValueError(f"{path}.{key}: campo ausente")
            _assert_subset(value, actual[key], f"{path}.{key}")
        return
    if expected != actual:
        raise ValueError(f"{path}: esperado {expected!r}, obtido {actual!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    try:
        report = build_report(args.workbook)
    except ValueError as exc:
        raise SystemExit(f"ERRO: {exc}") from exc
    if args.compare is not None:
        expected = json.loads(args.compare.read_text(encoding="utf-8"))
        try:
            _assert_subset(expected, report)
        except ValueError as exc:
            raise SystemExit(f"ERRO: relatório difere do snapshot esperado: {exc}") from exc
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
