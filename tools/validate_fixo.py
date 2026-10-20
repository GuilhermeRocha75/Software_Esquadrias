"""Validação FX ampliada: fonte real, matriz de entradas e exceções históricas.

python tools/validate_fixo.py fonte.xlsm --output relatorio.json
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
from itertools import product
import json
from pathlib import Path

from compare_fixo_formula_engine import (
    FixoConfiguration, calculate_fixo, compare, audit, source_input_issues, configuration,
)
from fixo_formula_oracle import FixoFormulaOracle
from esquadrias_engine.fixo import FIXO_ENGINE_VERSION, FIXO_GLASS_OPTIONS
from esquadrias_engine import build_order_purchase_plan
from esquadrias_engine.models import ManualSpliceAllocation
import math


def inputs_for(cfg):
    return {"D": cfg.width_mm, "E": cfg.height_mm, "F": cfg.quantity,
            "K": cfg.glass_description, "S": cfg.internal_finish, "T": cfg.external_finish,
            "AJ": cfg.vertical_transoms, "AK": cfg.horizontal_transoms}


def audit_purchase(oracle, historical):
    failures, manual_rows, passed = [], [], 0
    max_length = 0.0
    for record in historical["cases"]:
        if record["status"] != "PARITY_OK":
            continue
        row = record["orcs_row"]
        cfg = configuration(oracle.technical_inputs(row))
        result = calculate_fixo(cfg)
        try:
            plan = build_order_purchase_plan([(cfg, result)])
            assert math.isclose(plan.technical_total, result.unit_cost * cfg.quantity, abs_tol=1e-6)
            manual = []
            for line in plan.lines:
                actual = [p.length_mm for bar in line.bars for p in bar.pieces]
                expected = [comp.length_mm for comp in result.unit_bom
                            if comp.material_code == line.material_code
                            for _ in range(int(comp.quantity_order))]
                assert sorted(actual) == sorted(expected), line.material_code
                assert line.purchased_length_mm >= line.consumed_length_mm + line.kerf_loss_mm - 1e-6
                assert line.bars_required == sum(getattr(bar, "stock_bars_required", 1) for bar in line.bars)
                for bar in line.bars:
                    if isinstance(bar, ManualSpliceAllocation):
                        assert len(bar.pieces) == 1
                        assert bar.stock_bars_required == math.ceil(bar.used_mm / line.stock_length_mm)
                        manual.append(bar.pieces[0].length_mm)
                    assert bar.leftover_mm >= -1e-6
            if manual:
                manual_rows.append(row)
                max_length = max(max_length, *manual)
            passed += 1
        except (ValueError, AssertionError) as exc:
            failures.append({"orcs_row": row, "error": str(exc)})
    return {"historical_valid_passed": passed, "manual_splice_row_count": len(manual_rows),
            "manual_splice_rows": manual_rows, "maximum_integral_piece_mm": max_length,
            "policy": "KEEP_INTEGRAL_PIECE_MANUAL_FACTORY_SPLICE",
            "purchase_estimate": "Reserve whole stock bars per oversize piece; no assumed segment lengths, extra splice allowance or reuse between reserves.",
            "failures": failures}


def validate(oracle):
    historical, _ = audit(oracle)
    failures, totals = [], Counter()
    max_delta = 0.0

    def case(cfg, group):
        nonlocal max_delta
        inputs = inputs_for(cfg)
        oracle.set_inputs(inputs)
        invalid = source_input_issues(oracle, inputs)
        try:
            result = calculate_fixo(cfg)
        except ValueError as exc:
            if invalid:
                totals[f"{group}:source_invalid_rejected"] += 1
            else:
                failures.append({"configuration": asdict(cfg), "unexpected_rejection": str(exc)})
        else:
            if invalid:
                failures.append({"configuration": asdict(cfg), "unexpected_acceptance": invalid})
                return
            differences = compare(oracle, cfg)
            if differences:
                failures.append({"configuration": asdict(cfg), "differences": differences})
            else:
                totals[f"{group}:parity_ok"] += 1
            max_delta = max(max_delta, abs(result.unit_cost - oracle.value("FX", "I34")))

    # Todos os vidros com toda a grade de contagens observadas: V=0..7, H=0..4.
    for glass, vertical, horizontal in product(FIXO_GLASS_OPTIONS, range(8), range(5)):
        case(FixoConfiguration(4400, 3200, 2, vertical, horizontal, glass["description"]), "catalog_grid")
    # Dimensões não quadradas/fracionárias, fronteira de reforço, acabamentos e quantidades.
    finishes = ("GUARNIÇÃO DE 70MM", "BARRA CHATA DE 30MM")
    for dimensions, grid, internal, external, quantity, glass in product(
        ((1200, 1000), (1560.25, 2200.75), (2000, 2200), (112.001, 112.001)),
        ((0, 0), (2, 0), (0, 2), (2, 3)), finishes, finishes, (1, 2, 7),
        ("04mm FLOAT INCOLOR", "08mm TEMPERADO INCOLOR"),
    ):
        case(FixoConfiguration(*dimensions, quantity, *grid, glass, internal, external), "dimensions_finishes_quantity")

    exceptions = [record for record in historical["cases"] if record["status"] != "PARITY_OK"]
    glass_exceptions = {}
    for record in exceptions:
        if record.get("error") == "#N/A":
            description = record["inputs"]["K"]
            glass_exceptions.setdefault(description, []).append(record["orcs_row"])
    manual = []
    configurations = (
        ("SIMPLES", FixoConfiguration(1200, 1000)),
        ("GRADE_2V_3H_Q2", FixoConfiguration(2000, 2200, 2, 2, 3, "08mm TEMPERADO INCOLOR")),
        ("HISTORICO_14_Q3", FixoConfiguration(1560, 2200, 3, 0, 0, "06mm FLOAT INCOLOR")),
        ("VIDRO_DUPLO", FixoConfiguration(3400, 1800, 1, 3, 1, "20mm DUPLO FLOAT INCOLOR (4/10/6)")),
    )
    for name, cfg in configurations:
        oracle.set_inputs(inputs_for(cfg))
        manual.append({"name": name, "configuration": asdict(cfg), "expected": {
            "glass_width_mm": oracle.value("FX", "D27"),
            "glass_height_mm": oracle.value("FX", "E27"),
            "glass_quantity_per_product": oracle.value("FX", "G27"),
            "glass_quantity_order": oracle.value("FX", "F27"),
            "unit_technical_cost": oracle.value("FX", "I34"),
            "order_technical_cost": oracle.value("FX", "I34") * cfg.quantity,
        }})
    historical_failed = any(historical["counts"].get(key, 0) for key in (
        "PARITY_MISMATCH", "UNEXPECTED_ENGINE_ACCEPTANCE", "UNEXPECTED_ENGINE_REJECTION"))
    purchase = audit_purchase(oracle, historical)
    passed = not purchase["failures"] and not failures and not historical_failed and historical["cached_formula_check"]["mismatch_count"] == 0
    return {
        "validation_version": "FX_VALIDATION_1.0", "engine_version": FIXO_ENGINE_VERSION,
        "source_sha256": oracle.sha256, "technical_validation_passed": passed,
        "historical_counts": historical["counts"], "historical_rows": historical["rows_evaluated"],
        "cached_formula_check": historical["cached_formula_check"],
        "expanded_matrix": {"counts": dict(totals), "total": sum(totals.values()) + len(failures),
                            "glass_catalog_count": len(FIXO_GLASS_OPTIONS),
                            "max_total_absolute_delta": max_delta, "failures": failures},
        "source_exceptions": {"total": len(exceptions),
                              "missing_catalog_descriptions": glass_exceptions,
                              "missing_glass_rows": [r["orcs_row"] for r in exceptions if r.get("error") == "#VALUE!"],
                              "invalid_geometry_rows": [r["orcs_row"] for r in exceptions if r["status"] == "INVALID_SOURCE_GEOMETRY_OR_INPUT"],
                              "policy": "REJECT_WITHOUT_PRICE_OR_GLASS_SUBSTITUTION"},
        "manual_cases": manual,
        "purchase_validation": purchase,
        "gate": {"main_ready": False, "status": "PENDING_HOMOLOGATION",
                 "remaining": "Aceite funcional e da rejeição dos 74 registros inválidos da fonte."},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = validate(FixoFormulaOracle(args.workbook))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["technical_validation_passed"], "historical": report["historical_counts"],
                      "expanded_matrix": report["expanded_matrix"]}, ensure_ascii=False))
    return int(not report["technical_validation_passed"])


if __name__ == "__main__":
    raise SystemExit(main())
