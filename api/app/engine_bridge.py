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
    StructuralReinforcement,
    build_order_purchase_plan,
    calculate_sliding,
    GLASSES,
    CLOSURE_OPTIONS,
    CREMONA_OPTIONS,
    ROLLER_OPTIONS,
    FINISH_OPTIONS,
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
    "StructuralReinforcement",
    "calculate_sliding",
    "build_order_purchase_plan",
    "GLASSES",
    "CLOSURE_OPTIONS",
    "CREMONA_OPTIONS",
    "ROLLER_OPTIONS",
    "FINISH_OPTIONS",
    "PARAMETERS",
]
