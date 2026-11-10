"""Presentation row anchors from the homologated sheet and OP1.OP_1.

This module changes display order only. It never changes or drops an Engine row.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

ORDER_VERSION = "OP_LEGACY_ORDER_0.1.0"
_SOURCE = json.loads((Path(__file__).parent / "data/op_legacy_order_v1.json").read_text(encoding="utf-8"))

_CR = {
    "FRAME_HORIZONTAL": 8, "FRAME_VERTICAL": 9, "LEAF_HORIZONTAL": 10, "LEAF_VERTICAL": 11,
    "SCREEN_LEAF_HORIZONTAL": 12, "SCREEN_LEAF_VERTICAL": 13,
    "GLAZING_BEAD_HORIZONTAL": 14, "GLAZING_BEAD_VERTICAL": 17,
    "SCREEN_BEAD_HORIZONTAL": 20, "SCREEN_BEAD_VERTICAL": 23,
    "LEAF_TRANSOM_HORIZONTAL": 26, "LEAF_TRANSOM_VERTICAL": 29,
    "CENTRAL_CLOSURE": 30, "INTERLOCK": 32, "LEAF_COVER": 33, "ALUMINUM_RAIL": 34,
    "DESIGN_Z_PROFILE": 35, "DESIGN_Z_TRIM": 36,
    "BOTTOM_FIXED_FRAME_HORIZONTAL": 37, "BOTTOM_FIXED_FRAME_VERTICAL": 38,
    "BOTTOM_BEAD_HORIZONTAL": 41, "BOTTOM_BEAD_VERTICAL": 42,
    "TOP_FIXED_FRAME_HORIZONTAL": 43, "TOP_FIXED_FRAME_VERTICAL": 44,
    "TOP_BEAD_HORIZONTAL": 47, "TOP_BEAD_VERTICAL": 48,
    "INTERNAL_FINISH_HORIZONTAL": 49, "INTERNAL_FINISH_VERTICAL": 50,
    "EXTERNAL_FINISH_HORIZONTAL": 51, "EXTERNAL_FINISH_VERTICAL": 52,
    "STRUCTURAL_REINFORCEMENT": 53,
    "FRAME_REINFORCEMENT_HORIZONTAL": 65, "FRAME_REINFORCEMENT_VERTICAL": 66,
    "LEAF_REINFORCEMENT_HORIZONTAL": 67, "LEAF_REINFORCEMENT_VERTICAL": 68,
    "LEAF_TRANSOM_REINFORCEMENT_HORIZONTAL": 69, "LEAF_TRANSOM_REINFORCEMENT_VERTICAL": 72,
    "BOTTOM_FIXED_FRAME_REINFORCEMENT_HORIZONTAL": 73, "BOTTOM_FIXED_FRAME_REINFORCEMENT_VERTICAL": 74,
    "TOP_FIXED_FRAME_REINFORCEMENT_HORIZONTAL": 77, "TOP_FIXED_FRAME_REINFORCEMENT_VERTICAL": 78,
    "GLASS_PANEL": 84, "SCREEN_MESH": 97, "LEAF_RUBBER": 108, "SCREEN_RUBBER": 109,
    "LEAF_BRUSH": 110, "WIND_STOP": 116, "GLAZING_BLOCK": 117, "DRAIN_CAP": 118,
    "OPENING_LIMITER": 119, "CREMONA": 139, "HANDLE_STANDARD": 140,
    "HANDLE_HIDDEN": 141, "HIDDEN_LATCH": 142, "ROLLERS": 143,
    "COUNTER_LATCH": 144, "REINFORCEMENT_SCREWS": 145, "HARDWARE_SCREWS": 146,
}
_MX = {
    "FRAME_HORIZONTAL": 8, "FRAME_VERTICAL": 9, "LEAF_HORIZONTAL": 10, "LEAF_VERTICAL": 11,
    "GLAZING_BEAD_HORIZONTAL": 12, "GLAZING_BEAD_VERTICAL": 13,
    "LEAF_SEPARATOR_HORIZONTAL": 14, "LEAF_SEPARATOR_VERTICAL": 15,
    "STRUCTURAL_REINFORCEMENT": 32, "INTERNAL_FINISH_HORIZONTAL": 33, "INTERNAL_FINISH_VERTICAL": 34,
    "EXTERNAL_FINISH_HORIZONTAL": 35, "EXTERNAL_FINISH_VERTICAL": 36,
    "FRAME_REINFORCEMENT_HORIZONTAL": 42, "FRAME_REINFORCEMENT_VERTICAL": 43,
    "LEAF_REINFORCEMENT_HORIZONTAL": 44, "LEAF_REINFORCEMENT_VERTICAL": 45,
    "LEAF_SEPARATOR_TRANSOM_REINFORCEMENT_HORIZONTAL": 46, "LEAF_SEPARATOR_TRANSOM_REINFORCEMENT_VERTICAL": 47,
    "GLASS_PANEL": 59, "RETRACTABLE_SCREEN_ASSEMBLY": 64,
    "GLASS_SEATING_SEAL": 67, "LEAF_EXTERNAL_SEAL": 68, "FRAME_CONTACT_SEAL": 69,
    "GLAZING_BLOCK": 72, "DRAIN_CAP": 73, "MAXIM_AR_ARM": 76, "MAXIM_AR_LATCH": 77,
    "HANDLE_STANDARD": 77, "CREMONA": 78, "COUNTER_LATCH": 79,
    "REINFORCEMENT_SCREWS": 80, "HARDWARE_SCREWS": 81,
}
_GR = {
    "FRAME_WIDTH": 8, "FRAME_HEIGHT": 9, "LEAF_WIDTH": 10, "LEAF_HEIGHT": 11,
    "MIXED_HORIZONTAL_TRANSOM": 12, "GLASS_BEAD_WIDTH": 13, "GLASS_BEAD_HEIGHT": 14,
    "UPPER_GLASS_BEAD_WIDTH": 13, "UPPER_GLASS_BEAD_HEIGHT": 14,
    "PANEL_BEAD_WIDTH": 16, "PANEL_BEAD_HEIGHT": 17,
    "LOWER_PANEL_BEAD_WIDTH": 16, "LOWER_PANEL_BEAD_HEIGHT": 18,
    "PANEL_FILL": 41, "LOWER_PANEL_FILL": 41, "STRUCTURAL_REINFORCEMENT": 42,
    "INTERNAL_FINISH_WIDTH": 43, "INTERNAL_FINISH_HEIGHT": 44,
    "EXTERNAL_FINISH_WIDTH": 45, "EXTERNAL_FINISH_HEIGHT": 46,
    "FRAME_REINFORCEMENT_WIDTH": 58, "FRAME_REINFORCEMENT_HEIGHT": 59,
    "LEAF_REINFORCEMENT_WIDTH": 60, "LEAF_REINFORCEMENT_HEIGHT": 61,
    "MIXED_HORIZONTAL_TRANSOM_REINFORCEMENT": 62,
    "GLASS_PANEL": 68, "RETRACTABLE_SCREEN_ASSEMBLY": 73,
    "GLASS_OR_LAMBRI_SEAL": 76, "UPPER_GLASS_SEAL": 76, "LOWER_LAMBRI_SEAL": 76,
    "ROUND_SEAL_LEAF": 77, "ROUND_SEAL_FRAME": 78,
    "SQUARING_BLOCK": 83, "GLAZING_BLOCK": 83, "DRAIN_CAP": 84,
    "HINGE_90MM": 105, "DOUBLE_HANDLE": 111, "HANDLE_STANDARD": 111,
    "MONOPOINT_LOCK": 112, "MULTIPOINT_LOCK": 112, "CREMONA": 112,
    "CYLINDER_45X45": 113, "COUNTER_LATCH": 114, "STRIKE_PLATE": 115,
    "REINFORCEMENT_SCREWS": 118, "HARDWARE_SCREWS": 119,
}
_SHUTTER = ["SHUTTER_BOX", "SHUTTER_SIDE_GUIDE", "SHUTTER_CENTRAL_GUIDE", "SHUTTER_SLAT", "SHUTTER_TERMINAL", "SHUTTER_SHAFT", "SHUTTER_GUIDE_EXTENDER"]
_SHUTTER_UNITS = ["SHUTTER_LATERAL_COVER", "SHUTTER_PULLEY_PLATE", "SHUTTER_END_PLATE", "SHUTTER_MOTOR_COVER", "SHUTTER_MOTOR_PLATE", "SHUTTER_SHARED_SHAFT_DIVIDER", "SHUTTER_INDEPENDENT_SHAFT_DIVIDER", "SHUTTER_PULLEY", "SHUTTER_END_CAP", "SHUTTER_END_CAP_ADAPTER", "SHUTTER_RECESSED_WINDER", "SHUTTER_REMOTE_MOTOR", "SHUTTER_BUTTON_MOTOR", "SHUTTER_GUIDE_INVITATION_PAIR", "SHUTTER_FIRST_SLAT_COUPLING", "SHUTTER_FRONT_PIN", "SHUTTER_OPENING_LIMITER"]
_CR.update({role: 54 + n for n, role in enumerate(_SHUTTER)})
_CR.update({role: 120 + n for n, role in enumerate(_SHUTTER_UNITS)})
_GR.update({role: 47 + n for n, role in enumerate(_SHUTTER[:6])})
_GR.update({role: 86 + n for n, role in enumerate(_SHUTTER_UNITS)})


def legacy_anchor(family: str, line, inputs: dict) -> tuple[str, int | None, str | None]:
    """Return source sheet/row/label; unknown rows remain explicit extensions.

    Repeated grid rows share an anchor and retain Engine order. No cap on grid
    rows or the legacy 80-row print buffer is imposed.
    """
    source = _SOURCE["families"][family]
    sheet, role = source["sheet"], line.utilization
    row = {"CR": _CR, "MAXIM_AR": _MX, "GR": _GR}.get(family, {}).get(role)
    if family == "CR" and role in {"FIXED_PANEL_TRANSOM_HORIZONTAL", "FIXED_PANEL_TRANSOM_VERTICAL", "FIXED_PANEL_TRANSOM_REINFORCEMENT_HORIZONTAL", "FIXED_PANEL_TRANSOM_REINFORCEMENT_VERTICAL"}:
        top = bool(line.source and line.source.startswith("TOP"))
        vertical = role.endswith("VERTICAL")
        row = (79 if top else 75) if "REINFORCEMENT" in role else (45 if top else 39)
        row += int(vertical)
    if role in {"GLASS_PANEL", "GLASS_PANEL_1"} and line.source:
        if "BOTTOM" in line.source:
            row = {"CR": 93, "MAXIM_AR": 60, "GR": 69}.get(family, row)
        elif "TOP" in line.source:
            row = {"CR": 94, "MAXIM_AR": 61, "GR": 70}.get(family, row)
    if family == "MAXIM_AR":
        separate = inputs.get("module_mode") == "MÓDULOS SEPARADOS"
        for prefix, base, reinforcement in (("BOTTOM", 20, 48), ("TOP", 26, 52)):
            mapping = {f"{prefix}_FRAME_HORIZONTAL": base, f"{prefix}_FRAME_VERTICAL": base + 1,
                       f"{prefix}_FRAME_REINFORCEMENT_HORIZONTAL": reinforcement,
                       f"{prefix}_FRAME_REINFORCEMENT_VERTICAL": reinforcement + 1,
                       f"{prefix}_BEAD_HORIZONTAL": base + 4 if separate else (16 if prefix == "BOTTOM" else 18),
                       f"{prefix}_BEAD_VERTICAL": base + 5 if separate else (17 if prefix == "BOTTOM" else 19)}
            if role in mapping:
                row = mapping[role]
    if row is None and line.source:
        match = re.search(r"(?:^| / )" + re.escape(sheet) + r"!\$?[A-Z]*\$?(\d+)", line.source)
        if match and 8 <= int(match[1]) <= 200:
            row = int(match[1])
    label = next((r["label"] for r in source["rows"] if r["row"] == row), None)
    return sheet, row, label
