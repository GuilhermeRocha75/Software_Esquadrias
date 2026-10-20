"""Compara toda a ORCS FX com fórmulas originais. Sem Office e sem gravar no XLSM.

python tools/compare_fixo_formula_engine.py fonte.xlsm --output relatorio.json
--fixtures DIRECTORY gera evidências técnicas para regressão sem o arquivo privado.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
import json
import math
from pathlib import Path
import sys

from fixo_formula_oracle import FixoFormulaOracle, FormulaError
ENGINE_ROOT = (Path(__file__).resolve().parents[1] / "engine/Software_Esquadrias_Starter + Versões"
               / "Software_Esquadrias_Starter_v0.3.1_GUI/Software_Esquadrias_Starter_v0.3.1_GUI")

sys.path.insert(0, str(ENGINE_ROOT / "src"))
from esquadrias_engine.fixo import FixoConfiguration, calculate_fixo  # noqa: E402


def configuration(inputs):
    def number(column):
        value = inputs.get(column)
        return float(str(value).replace(",", ".")) if value not in (None, "") else 0.0
    def integer(column):
        value = number(column)
        if not math.isfinite(value) or not value.is_integer():
            raise ValueError(f"ORCS {column} exige inteiro.")
        return int(value)
    return FixoConfiguration(width_mm=number("D"), height_mm=number("E"), quantity=integer("F"),
                             glass_description=inputs.get("K"), internal_finish=inputs.get("S"),
                             external_finish=inputs.get("T"), vertical_transoms=integer("AJ"),
                             horizontal_transoms=integer("AK"))


def compare(oracle, cfg):
    result = calculate_fixo(cfg)
    actual = {item.source: item for item in result.unit_bom}
    expected = oracle.bom()
    differences = []
    def check(label, expected_value, actual_value):
        if isinstance(expected_value, (int, float)) and isinstance(actual_value, (int, float)):
            equal = math.isclose(expected_value, actual_value, abs_tol=1e-7, rel_tol=1e-10)
        else:
            equal = expected_value == actual_value
        if not equal:
            differences.append({"field": label, "excel": expected_value, "engine": actual_value})
    check("BOM sources", sorted(item["source"] for item in expected), sorted(actual))
    for item in expected:
        component = actual.get(item["source"])
        if component is None:
            continue
        for col, field in (("C", "material_code"), ("F", "quantity_order"), ("G", "quantity_per_unit"),
                           ("H", "unit_price"), ("I", "cost_per_unit_product")):
            check(f"{item['source']}:{col}", item[col], getattr(component, field))
        if component.length_mm is not None:
            check(f"{item['source']}:E", item["E"], component.length_mm)
        if component.unit == "m²":
            check("FX!D27", item["D"], component.width_mm)
            check("FX!E27", item["E"], component.height_mm)
    groups = result.cost_breakdown
    for cell, total in (("I18", groups["PERFIS PRINCIPAIS"] + groups["BAGUETES"] + groups["ACABAMENTOS"]),
                        ("I24", groups["REFORÇOS"]), ("I28", groups["VIDROS"]),
                        ("I32", groups["ACESSÓRIOS"]), ("I34", result.unit_cost), ("AO2", result.unit_cost)):
        check(f"FX!{cell}", oracle.value("FX", cell), total)
    return differences


def source_input_issues(oracle, inputs):
    """Classifica origem sem usar validações da Engine como evidência."""
    issues = []
    for column in ("D", "E", "F", "AJ", "AK"):
        raw = inputs.get(column)
        try:
            number = float(str(raw).replace(",", ".")) if raw not in (None, "") else 0.0
        except (TypeError, ValueError):
            issues.append(f"{column}: valor não numérico")
            continue
        if not math.isfinite(number) or number < (1 if column in ("D", "E", "F") else 0):
            issues.append(f"{column}: valor inválido {number}")
        if column in ("F", "AJ", "AK") and not number.is_integer():
            issues.append(f"{column}: quantidade fracionária")
    for cell in ("E20", "E21", "D27", "E27"):
        value = oracle.value("FX", cell)
        if isinstance(value, (int, float)) and value <= 0:
            issues.append(f"FX!{cell} <= 0 mm")
    return issues


def audit(oracle):
    statuses = Counter()
    cases, golden, combinations = [], [], set()
    max_delta = 0.0
    for row in oracle.fx_rows():
        inputs = oracle.technical_inputs(row)
        oracle.set_inputs(inputs)
        total = oracle.value("FX", "I34")
        record = {"orcs_row": row}
        if isinstance(total, FormulaError):
            record.update(status="SOURCE_FORMULA_ERROR", error=total.code)
            try:
                calculate_fixo(configuration(inputs))
            except (ValueError, TypeError) as exc:
                record["engine_rejection"] = str(exc)
            else:
                record["status"] = "UNEXPECTED_ENGINE_ACCEPTANCE"
        else:
            source_issues = source_input_issues(oracle, inputs)
            if source_issues:
                record.update(status="INVALID_SOURCE_GEOMETRY_OR_INPUT", reasons=source_issues, formula_total=total)
                try:
                    calculate_fixo(configuration(inputs))
                except (ValueError, TypeError):
                    pass
                else:
                    record["status"] = "UNEXPECTED_ENGINE_ACCEPTANCE"
            else:
                try:
                    cfg = configuration(inputs)
                    differences = compare(oracle, cfg)
                except (ValueError, TypeError) as exc:
                    record.update(status="UNEXPECTED_ENGINE_REJECTION", reason=str(exc), formula_total=total)
                else:
                    record.update(status="PARITY_MISMATCH" if differences else "PARITY_OK", formula_total=total,
                                  differences=differences)
                    calculated = calculate_fixo(cfg).unit_cost
                    max_delta = max(max_delta, abs(total - calculated))
                    key = (cfg.vertical_transoms, cfg.horizontal_transoms, cfg.glass_description[:2])
                    if key not in combinations:
                        combinations.add(key)
                        golden.append({"orcs_row": row, "inputs": inputs, "configuration": asdict(cfg),
                                       "expected_bom": oracle.bom(), "expected_total": total})
        if record["status"] != "PARITY_OK":
            record["inputs"] = inputs
        statuses[record["status"]] += 1
        cases.append(record)
    return {"source_sha256": oracle.sha256, "rows_evaluated": len(cases), "counts": dict(statuses),
            "max_total_absolute_delta": max_delta, "representative_cases": len(golden),
            "cached_formula_check": oracle.verify_cached_fx(),
            "gate": {"main_ready": False, "status": "PENDING_HOMOLOGATION",
                     "reason": "Homologar interface e revisar exceções de origem antes do merge."},
            "cases": cases}, golden


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path)
    args = parser.parse_args()
    oracle = FixoFormulaOracle(args.workbook)
    report, golden = audit(oracle)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.fixtures:
        args.fixtures.mkdir(parents=True, exist_ok=True)
        oracle.set_inputs({})
        for filename, data in (("fixo_formula_snapshot_v0_1.json", oracle.snapshot()),
                               ("fixo_golden_v0_1.json", {"source_sha256": oracle.sha256, "cases": golden})):
            (args.fixtures / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("rows_evaluated", "counts", "max_total_absolute_delta", "representative_cases", "cached_formula_check")}, ensure_ascii=False))
    return int(any(report["counts"].get(key, 0) for key in ("PARITY_MISMATCH", "UNEXPECTED_ENGINE_ACCEPTANCE", "UNEXPECTED_ENGINE_REJECTION"))
               or report["cached_formula_check"]["mismatch_count"] > 0)


if __name__ == "__main__":
    raise SystemExit(main())
