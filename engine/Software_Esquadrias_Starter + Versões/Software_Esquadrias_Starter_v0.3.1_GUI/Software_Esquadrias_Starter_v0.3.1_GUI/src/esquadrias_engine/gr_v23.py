from __future__ import annotations

from dataclasses import replace

from . import gr_v22 as v22
from .models import CalculationResult


GR_ENGINE_VERSION = "GR_ENGINE_0.23.0"
GrConfiguration = v22.GrConfiguration

# Contrato técnico da auditoria ORCS. A API apenas publica este estado; a
# classificação de engenharia continua pertencendo à Engine.
GR_COVERAGE_AUDIT = {
    "audit_version": "GR_COVERAGE_AUDIT_0.23.0",
    "source": {
        "orcs_gr_rows": 1684,
        "official_xlsm_sha256": "96514d7818bcbbc1db86f94f86d8ed0239675e9f8d3a6b64df651f30fd90c160",
    },
    "historically_absent": {
        "separate_modules": 0,
        "structural_reinforcement": 0,
    },
    "resolved_or_prohibited": {
        "leaf_grid_inside_mobile_leaf": {
            "status": "PROHIBITED_PHYSICAL",
            "count": 1,
            "reference_orcs_rows": [9155],
        },
    },
    "pending_real": {
        "application_leaf_system_independence": 47,
        "flag_combinations_outside_v022": 21,
        "closure_application_compatibility": 66,
        "special_closures": 18,
        "glass_catalog_missing": 24,
        "hinge_pernio_or_invalid": 5,
    },
    "source_data_review": {
        "count": 2,
        "reference_orcs_rows": [543, 914],
    },
    "gate": {
        "historical_coverage_closed": False,
        "purchase_plan_supported": False,
        "main_ready": False,
        "status": "FASE_23_AUDITADA_COM_PENDENCIAS_REAIS",
    },
}


def calculate_gr(cfg: GrConfiguration) -> CalculationResult:
    """GR v0.23: preserva v0.22 e publica o gate de cobertura histórica."""
    return replace(v22.calculate_gr(cfg), calculation_version=GR_ENGINE_VERSION)
