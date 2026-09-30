from __future__ import annotations

from dataclasses import replace

from . import gr_v06 as v06
from . import gr_v23 as v23
from .models import CalculationResult, EngineeringWarning


GR_ENGINE_VERSION = "GR_ENGINE_0.24.0"
GrConfiguration = v23.GrConfiguration

_pending_real = dict(v23.GR_COVERAGE_AUDIT["pending_real"])
_resolved_independence_count = _pending_real.pop("application_leaf_system_independence")

GR_COVERAGE_AUDIT = {
    **v23.GR_COVERAGE_AUDIT,
    "audit_version": "GR_COVERAGE_AUDIT_0.24.0",
    "resolved_or_prohibited": {
        **v23.GR_COVERAGE_AUDIT["resolved_or_prohibited"],
        "application_leaf_system_independence": {
            "status": "RESOLVED_PHYSICAL",
            "count": _resolved_independence_count,
            "confirmation_date": "2026-09-30",
            "rule": (
                "PORTA/JANELA é classificação comercial independente. "
                "Marco, folha, vidro, baguete e auxiliares são calculados pelo tipo de folha."
            ),
        },
    },
    "pending_real": _pending_real,
    "gate": {
        "historical_coverage_closed": False,
        "purchase_plan_supported": False,
        "main_ready": False,
        "status": "FASE_24_INDEPENDENCIA_APLICACAO_RESOLVIDA_COM_PENDENCIAS",
    },
}


def _physical_application_for_leaf(leaf_system: str) -> str:
    """Aplicação técnica usada apenas para percorrer fórmulas legadas."""
    if leaf_system == v06.GR_LEAF_SYSTEM_WINDOW_EXTERNAL:
        return v06.GR_APPLICATION_WINDOW
    return v06.GR_APPLICATION_DOOR


def _description_with_commercial_application(
    description: str,
    commercial_application: str,
) -> str:
    head, separator, tail = description.partition(" ")
    if head in (v06.GR_APPLICATION_DOOR, v06.GR_APPLICATION_WINDOW):
        return commercial_application + (separator + tail if separator else "")
    return description


def calculate_gr(cfg: GrConfiguration) -> CalculationResult:
    """GR v0.24: aplicação comercial não interfere na configuração física."""
    if cfg.application not in (v06.GR_APPLICATION_DOOR, v06.GR_APPLICATION_WINDOW):
        raise ValueError(f"aplicação fora do escopo do GR_ENGINE_0.24.0: {cfg.application}")

    physical_application = _physical_application_for_leaf(cfg.leaf_system)
    normalized = replace(cfg, application=physical_application)
    result = v23.calculate_gr(normalized)

    warnings = list(result.warnings)
    if cfg.application != physical_application:
        warnings.append(EngineeringWarning(
            "GR-APPLICATION-INDEPENDENT",
            (
                f"Aplicação {cfg.application} mantida como classificação comercial; "
                "geometria, cortes e materiais seguem o tipo de folha selecionado."
            ),
        ))

    return replace(
        result,
        model_description=_description_with_commercial_application(
            result.model_description,
            cfg.application,
        ),
        warnings=warnings,
        calculation_version=GR_ENGINE_VERSION,
    )
