from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_ENGINE_SRC = (
    REPO_ROOT
    / "engine"
    / "Software_Esquadrias_Starter + Versões"
    / "Software_Esquadrias_Starter_v0.3.1_GUI"
    / "Software_Esquadrias_Starter_v0.3.1_GUI"
    / "src"
)

if str(LEGACY_ENGINE_SRC) not in sys.path:
    sys.path.insert(0, str(LEGACY_ENGINE_SRC))

from esquadrias_engine import (  # noqa: E402
    ApplicationType,
    CustomDimension,
    FixedPanelConfiguration,
    GridAxis,
    LeafGrid,
    LeafSystem,
    SlidingConfiguration,
    ShutterConfiguration,
    ShutterMode,
    StructuralReinforcement,
    MaximArConfiguration,
    MaximArLeafSystem,
    build_order_purchase_plan,
    calculate_sliding,
    calculate_maxim_ar,
    GLASSES,
    CLOSURE_OPTIONS,
    CREMONA_OPTIONS,
    ROLLER_OPTIONS,
    FINISH_OPTIONS,
    SHUTTER_MODES,
    SHUTTER_BOX_OPTIONS,
    SHUTTER_SLAT_OPTIONS,
)
from esquadrias_engine.maxim_ar import (  # noqa: E402
    MAXIM_AR_ENGINE_VERSION,
    MAXIM_AR_CLOSURE_OPTIONS,
    MAXIM_AR_CREMONA_OPTIONS,
    MAXIM_AR_INTERNAL_FINISH_OPTIONS,
    MAXIM_AR_EXTERNAL_FINISH_OPTIONS,
)
from esquadrias_engine.catalog import PARAMETERS  # noqa: E402

__all__ = [
    "ApplicationType",
    "CustomDimension",
    "FixedPanelConfiguration",
    "GridAxis",
    "LeafGrid",
    "LeafSystem",
    "SlidingConfiguration",
    "ShutterConfiguration",
    "ShutterMode",
    "StructuralReinforcement",
    "MaximArConfiguration",
    "MaximArLeafSystem",
    "calculate_sliding",
    "calculate_maxim_ar",
    "build_order_purchase_plan",
    "GLASSES",
    "CLOSURE_OPTIONS",
    "CREMONA_OPTIONS",
    "ROLLER_OPTIONS",
    "FINISH_OPTIONS",
    "SHUTTER_MODES",
    "SHUTTER_BOX_OPTIONS",
    "SHUTTER_SLAT_OPTIONS",
    "PARAMETERS",
    "MAXIM_AR_ENGINE_VERSION",
    "MAXIM_AR_CLOSURE_OPTIONS",
    "MAXIM_AR_CREMONA_OPTIONS",
    "MAXIM_AR_INTERNAL_FINISH_OPTIONS",
    "MAXIM_AR_EXTERNAL_FINISH_OPTIONS",
]
