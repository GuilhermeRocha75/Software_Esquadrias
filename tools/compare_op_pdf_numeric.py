"""Compare printed reference numbers to B1 values without engineering formulas."""
from collections import Counter
from decimal import Decimal


def compare_numeric_reference(case: dict, reference: dict, layout) -> dict:
    """Keep originals/Engine values, tolerance differences and unresolved units.

    Reference consumables show order meters; B1 shows mm per product plus run
    counts. This layer reports that representation gap instead of manufacturing
    an aggregate quantity outside the Engine.
    """
    lines = {row.engine_position: row.technical for block in layout.pages[0].blocks for row in block.rows}
    fields, units, used, used_engine = [], [], set(), set()
    for common in case["common_rows"]:
        row = reference["rows"][common["pdf_position"] - 1]
        technical = lines[common["engine_position"]]
        used.add(common["pdf_position"] - 1)
        used_engine.add(common["engine_position"])
        if row["kind"] == "CONSUMPTION":
            units.append({"classification": "UNIT_REPRESENTATION_REVIEW", "label": row["label"], "code": row["code"],
                          "pdf_order_quantity_m": row["quantity"], "engine_length_per_product_mm": technical.cut_length_mm,
                          "engine_run_quantity_total": technical.quantity_total,
                          "engine_position": common["engine_position"], "resolved": False})
            continue
        values = [("quantity_total", row["quantity"], technical.quantity_total)]
        if row["measure_1"] is not None:
            first, second = ("width_mm", "height_mm") if row["kind"] == "SURFACE" else ("final_length_mm", "cut_length_mm")
            values += [(first, row["measure_1"], getattr(technical, first)), (second, row["measure_2"], getattr(technical, second))]
        for field, pdf, engine in values:
            expected = Decimal(pdf.replace(",", "."))
            actual = None if engine is None else Decimal(str(engine))
            if actual == expected:
                status, category = "MATCH", "PRINTED_VALUE_MATCH"
            elif actual is not None and abs(actual - expected) <= Decimal("0.000001"):
                status, category = "PRINTED_PRECISION_DIFFERENCE", "PRINTED_PRECISION_DIFFERENCE"
            else:
                status = "DIVERGENT"
                role = technical.utilization
                if role == "SHUTTER_SLAT" and field == "quantity_total":
                    category = "EXISTING_PHYSICAL_CORRECTION_INPUT_PENDING"
                elif role.startswith("SHUTTER_"):
                    category = "INPUT_SHUTTER_MODE_UNCONFIRMED"
                elif role in {"COUNTER_LATCH", "HARDWARE_SCREWS", "ROLLERS", "CREMONA", "HANDLE_STANDARD", "HIDDEN_LATCH"}:
                    category = "RECONSTRUCTED_HARDWARE_OPTION_UNCONFIRMED"
                else:
                    category = "POSSIBLE_ENGINEERING_OR_LEGACY_VARIANT"
            fields.append({"label": row["label"], "role": technical.utilization, "engine_position": common["engine_position"],
                           "pdf_position": common["pdf_position"], "field": field,
                           "pdf_printed": pdf, "engine": engine, "status": status, "classification": category,
                           "identity_also_differs": row["code"] != technical.code})
    missing = [row for index, row in enumerate(reference["rows"]) if index not in used]
    additions = [{"engine_position": position, "role": line.utilization, "code": line.code,
                  "final_length_mm": line.final_length_mm, "cut_length_mm": line.cut_length_mm,
                  "width_mm": line.width_mm, "height_mm": line.height_mm,
                  "quantity_total": line.quantity_total, "quantity_unit": line.quantity_unit}
                 for position, line in lines.items() if position not in used_engine]
    return {"counts": dict(Counter(field["status"] for field in fields)),
            "differences": [field for field in fields if field["status"] != "MATCH"],
            "unit_representation_reviews": units, "missing_reference_rows": missing,
            "engine_additional_rows": additions, "full_equivalence": False}
