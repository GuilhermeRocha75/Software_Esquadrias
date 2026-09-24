from __future__ import annotations

import math

from . import gr_v06 as v06
from . import gr_v10 as v10
from . import gr_v11 as v11
from . import gr_v12 as v12
from .models import CalculationResult, EngineeringWarning, ShutterMode


GR_ENGINE_VERSION = "GR_ENGINE_0.13.0"
GrConfiguration = v12.GrConfiguration

GR_LEAF_SYSTEM_INTERNAL = v06.GR_LEAF_SYSTEM_INTERNAL
GR_LEAF_SYSTEM_EXTERNAL = v06.GR_LEAF_SYSTEM_EXTERNAL
GR_APPLICATION_DOOR = v06.GR_APPLICATION_DOOR


def _promote(result: CalculationResult) -> CalculationResult:
    return CalculationResult(
        model_description=result.model_description,
        geometry=result.geometry,
        unit_bom=result.unit_bom,
        cost_breakdown=result.cost_breakdown,
        unit_cost=result.unit_cost,
        leaf_openings=result.leaf_openings,
        transoms=result.transoms,
        fixed_panels=result.fixed_panels,
        glass_panels=result.glass_panels,
        warnings=result.warnings,
        calculation_version=GR_ENGINE_VERSION,
    )


def _validate_independent_double(cfg: GrConfiguration) -> None:
    shutter = cfg.shutter
    if shutter is None or shutter.mode != ShutterMode.MANUAL_DOUBLE_INDEPENDENT_SHAFTS:
        raise ValueError("Configuração manual de 2 painéis/eixos independentes inválida.")
    if shutter.box_description != v11.GR_SHUTTER_BOX:
        raise ValueError(f"Caixa GR fora do escopo v0.13: {shutter.box_description}")
    if shutter.slat_description != v11.GR_SHUTTER_SLAT:
        raise ValueError(f"Tala GR fora do escopo v0.13: {shutter.slat_description}")
    if cfg.panel_mode != v06.GR_GLASS_MODE:
        raise ValueError(
            "GR_ENGINE_0.13.0 libera 2 painéis independentes somente com VIDRO INTEIRO."
        )
    if cfg.application != GR_APPLICATION_DOOR:
        raise ValueError(
            "GR_ENGINE_0.13.0 homologa 2 painéis independentes inicialmente somente em PORTA."
        )
    if cfg.leaf_count != 2:
        raise ValueError(
            "GR_ENGINE_0.13.0 exige porta GR de 2 folhas para o recorte histórico de 2 painéis independentes."
        )
    if cfg.leaf_system not in (GR_LEAF_SYSTEM_INTERNAL, GR_LEAF_SYSTEM_EXTERNAL):
        raise ValueError(
            "GR_ENGINE_0.13.0 exige folha de porta Design 60x104."
        )

    effective_height = float(cfg.height_mm) - 200.0
    if effective_height <= 0:
        raise ValueError("Altura GR insuficiente para caixa de persiana de 200 mm.")

    v10.calculate_gr(v11._v10_config(
        cfg,
        height_mm=effective_height,
        shutter_enabled=False,
    ))


def _calculate_independent_double(cfg: GrConfiguration) -> CalculationResult:
    _validate_independent_double(cfg)

    width = float(cfg.width_mm)
    overall_height = float(cfg.height_mm)
    effective_height = overall_height - 200.0

    base = v10.calculate_gr(v11._v10_config(
        cfg,
        height_mm=effective_height,
        shutter_enabled=False,
    ))
    bom = v11._restore_full_height_finishes(
        list(base.unit_bom), overall_height, cfg.quantity
    )

    panel_count = 2.0
    box_length = width - 15.0
    guide_length = overall_height - 200.0
    central_guide_length = guide_length
    slat_width = (
        (width - 2.0 * 32.0 - 30.0) / 2.0
        - 10.0
    )
    shaft_length = width / 2.0 - 40.0
    if min(box_length, guide_length, slat_width, shaft_length) <= 0:
        raise ValueError("Dimensões da persiana GR de 2 painéis ficaram inválidas.")

    legacy_slat_qty = (overall_height / 40.0) * panel_count
    slat_qty = float(math.ceil(overall_height / 40.0) * 2)
    shaft_qty = 2.0

    bom.extend([
        v11._linear_shutter(
            "321040", "SHUTTER_BOX", box_length, 1.0, cfg.quantity,
            "GR!D47/G47",
        ),
        v11._linear_shutter(
            "327201", "SHUTTER_SIDE_GUIDE", guide_length, 2.0, cfg.quantity,
            "GR!D48/G48",
        ),
        v11._linear_shutter(
            "327204", "SHUTTER_CENTRAL_GUIDE", central_guide_length, 1.0,
            cfg.quantity, "GR!D49/G49",
        ),
        v11._linear_shutter(
            "326015_F", "SHUTTER_SLAT", slat_width, slat_qty, cfg.quantity,
            "GR!D50/G50 + PHYSICAL_ROUND_UP inherited from homologated CR shutter",
        ),
        v11._linear_shutter(
            "311712", "SHUTTER_TERMINAL", slat_width, 2.0, cfg.quantity,
            "GR!D51/G51",
        ),
        v11._linear_shutter(
            "375021", "SHUTTER_SHAFT", shaft_length, shaft_qty, cfg.quantity,
            "GR!D52/G52 + LEGACY_INDEPENDENT_SHAFT_QTY_CORRECTED",
        ),
    ])

    accessory_lines = [
        ("370113", "SHUTTER_LATERAL_COVER", 2.0, "GR!86 + CR!G120"),
        ("371513_4", "SHUTTER_PULLEY_PLATE", 2.0, "GR!87 + CR!G121"),
        ("371127", "SHUTTER_INDEPENDENT_SHAFT_DIVIDER", 1.0, "GR!92 + CR!G126"),
        ("375110", "SHUTTER_PULLEY", 2.0, "GR!93 + CR!G127"),
        ("375213", "SHUTTER_END_CAP", 2.0, "GR!94 + CR!G128"),
        ("375234", "SHUTTER_END_CAP_ADAPTER", 2.0, "GR!95 + CR!G129"),
        ("375339", "SHUTTER_RECESSED_WINDER", 2.0, "GR!96 + CR!G130"),
        ("373128", "SHUTTER_GUIDE_INVITATION_PAIR", 1.0, "GR!99 + CR!G133"),
        ("375678", "SHUTTER_FIRST_SLAT_COUPLING", 4.0, "GR!100 + CR!G134"),
        ("375415", "SHUTTER_FRONT_PIN", 2.0, "GR!101 + CR!G135"),
        ("375441", "SHUTTER_OPENING_LIMITER", 4.0, "GR!102 + CR!G136"),
    ]
    for code, role, quantity, source in accessory_lines:
        bom.append(v11._unit_shutter(
            code,
            role,
            quantity,
            cfg.quantity,
            source + " / LEGACY_GR_HELPERS_RECOVERED",
        ))

    groups = (*v06._GROUPS, "PERSIANA")
    breakdown = {
        group: round(
            sum(item.cost_per_unit_product for item in bom if item.category == group),
            6,
        )
        for group in groups
    }
    total = round(sum(item.cost_per_unit_product for item in bom), 6)
    breakdown["TOTAL"] = total

    geometry = dict(base.geometry)
    geometry.update({
        "overall_height_mm": round(overall_height, 6),
        "shutter_box_height_mm": 200.0,
        "shutter_main_opening_height_mm": round(effective_height, 6),
        "shutter_panel_count": 2.0,
        "shutter_box_length_mm": round(box_length, 6),
        "shutter_side_guide_length_mm": round(guide_length, 6),
        "shutter_central_guide_length_mm": round(central_guide_length, 6),
        "shutter_slat_width_mm": round(slat_width, 6),
        "shutter_slat_quantity": slat_qty,
        "shutter_shaft_length_mm": round(shaft_length, 6),
        "shutter_shaft_quantity": shaft_qty,
    })

    warnings = list(base.warnings)
    warnings.extend([
        EngineeringWarning(
            "LEGACY-GR-SHUTTER-HELPERS-RECOVERED",
            "GR!85:102 referencia auxiliares inexistentes; o kit de 2 painéis independentes foi recuperado da CR homologada com os mesmos códigos.",
        ),
        EngineeringWarning(
            "LEGACY-GR-SHUTTER-INDEPENDENT-SHAFT-QTY-CORRECTED",
            "GR corta o eixo em meia largura mas registra uma única peça. A v0.13 usa 2 eixos físicos, um por painel.",
        ),
        EngineeringWarning(
            "LEGACY-GR-SHUTTER-DIVIDER-TYPO-CORRECTED",
            "GR!G91 contém INDEPENDNETES e pode selecionar divisor de eixo único por engano. A v0.13 usa somente o divisor 371127 de eixos independentes.",
        ),
        EngineeringWarning(
            "LEGACY-GR-SHUTTER-SUBTOTAL-CORRECTED",
            "GR!I103 omite os acessórios da persiana; a v0.13 inclui o kit físico completo.",
        ),
    ])
    if slat_qty != legacy_slat_qty:
        warnings.append(EngineeringWarning(
            "LEGACY-GR-SHUTTER-SLAT-FRACTION",
            "O XLSM usa (altura/40)*2 como quantidade fracionária de talas; a Engine arredonda cada painel para cima.",
        ))

    return CalculationResult(
        model_description=base.model_description + " COM PERSIANA MANUAL 2 PAINÉIS EIXOS INDEPENDENTES",
        geometry=geometry,
        unit_bom=bom,
        cost_breakdown=breakdown,
        unit_cost=total,
        leaf_openings=list(base.leaf_openings),
        transoms=list(base.transoms),
        fixed_panels=list(base.fixed_panels),
        glass_panels=list(base.glass_panels),
        warnings=warnings,
        calculation_version=GR_ENGINE_VERSION,
    )


def calculate_gr(cfg: GrConfiguration) -> CalculationResult:
    """GR v0.13: v0.12 + persiana manual 2 painéis/eixos independentes."""
    if (
        cfg.shutter is not None
        and cfg.shutter.mode == ShutterMode.MANUAL_DOUBLE_INDEPENDENT_SHAFTS
    ):
        return _calculate_independent_double(cfg)
    return _promote(v12.calculate_gr(cfg))
