from __future__ import annotations

from dataclasses import dataclass
import math

from .models import BomComponent, CalculationResult

GR_ENGINE_VERSION = "GR_ENGINE_0.4.0"
GR_LEAF_SYSTEM_INTERNAL = "FOLHA DE PORTA ABERTURA INTERNA 60X104MM - DESIGN"
GR_LEAF_SYSTEM_EXTERNAL = "FOLHA DE PORTA ABERTURA EXTERNA 60X104MM - DESIGN"
GR_LEAF_SYSTEM_WINDOW_EXTERNAL = "FOLHA DE JANELA ABERTURA EXTERNA 60X78MM - DESIGN"
GR_LEAF_SYSTEMS = (
    GR_LEAF_SYSTEM_INTERNAL,
    GR_LEAF_SYSTEM_EXTERNAL,
    GR_LEAF_SYSTEM_WINDOW_EXTERNAL,
)
GR_APPLICATION_DOOR = "PORTA"
GR_APPLICATION_WINDOW = "JANELA"
GR_PANEL_MODE = "PAINEL COMPLETO"
GR_MODULE_MODE = "MÓDULO ÚNICO"
GR_CLOSURE_MONOPOINT = "MAÇANETA DUPLA COM FECHADURA MONOPONTO E CHAVE"
GR_CLOSURE_MULTIPOINT = "MAÇANETA DUPLA COM FECHADURA MULTIPONTO E CHAVE"
GR_CLOSURE_WINDOW_CREMONA = "MAÇANETA COM CREMONA SEM CHAVE"
GR_DOOR_CLOSURES = (GR_CLOSURE_MONOPOINT, GR_CLOSURE_MULTIPOINT)
GR_CREMONA_WINDOW_800 = "CREMONA 2 PONTOS COMP. 800mm E:15mm"
GR_HINGE = "DOBRADIÇA 90MM"
GR_INTERNAL_FINISH = "GUARNIÇÃO DE 70MM"
GR_EXTERNAL_FINISH = "BARRA CHATA DE 30MM"


@dataclass(frozen=True)
class GrConfiguration:
    width_mm: float
    height_mm: float
    quantity: int = 1
    leaf_count: int = 1
    leaf_system: str = GR_LEAF_SYSTEM_INTERNAL
    application: str = GR_APPLICATION_DOOR
    panel_mode: str = GR_PANEL_MODE
    module_mode: str = GR_MODULE_MODE
    closure_mode: str = GR_CLOSURE_MONOPOINT
    cremona_description: str | None = None
    hinge_description: str = GR_HINGE
    internal_finish: str = GR_INTERNAL_FINISH
    external_finish: str = GR_EXTERNAL_FINISH
    shutter_enabled: bool = False
    screen_enabled: bool = False
    bottom_flag_height_mm: float = 0.0
    top_flag_height_mm: float = 0.0
    leaf_horizontal_transoms: int = 0
    leaf_vertical_transoms: int = 0
    structural_reinforcement: str | None = None


_MATERIALS = {
    "DE6058": ("MARCO ALTO DE ABRIR", 38.45, "PERFIS PRINCIPAIS"),
    "DE60104": ("FOLHA PORTA DE GIRO AB. INT.", 55.40, "PERFIS PRINCIPAIS"),
    "DE60104-E": ("FOLHA PORTA DE GIRO AB. EXT.", 54.87, "PERFIS PRINCIPAIS"),
    "DE6078": ("FOLHA JANELA ABERTURA EXTERNA", 45.44, "PERFIS PRINCIPAIS"),
    "BA2516": ("BAGUETE (Vidro 4/6mm - 12/18mm)", 10.72, "BAGUETES"),
    "DE20150": ("PAINEL FECHAMENTO", 20.27, "PERFIS PRINCIPAIS"),
    "AC7012": ("GUARNIÇÃO DE 70MM", 14.63, "ACABAMENTOS"),
    "AC3004": ("BARRA CHATA DE 30MM", 3.24, "ACABAMENTOS"),
    "RAG - DE6058": ("REFORÇO - MARCO ALTO DE ABRIR", 8.00, "REFORÇOS"),
    "RAG - DE60104": ("REFORÇO - FOLHA PORTA DE GIRO", 25.00, "REFORÇOS"),
    "RAG - DE6078": ("REFORÇO - FOLHA JANELA", 10.00, "REFORÇOS"),
    "AC0312": ("CALCO DE VIDRO 3X12", 0.35, "ACESSÓRIOS"),
    "AC0001": ("TAPA DESAGUE", 1.00, "ACESSÓRIOS"),
    "DOB3": ("DOBRADIÇA 90MM", 51.45, "FERRAGENS"),
    "MAC1": ("MACANETA STANDARD", 11.00, "FERRAGENS"),
    "MAC4": ("MAÇANETA DUPLA (GIRO)", 60.00, "FERRAGENS"),
    "FEC5": ("FECHADURA MULTIPONTO (GIRO)", 100.00, "FERRAGENS"),
    "FEC6": ("FECHADURA MONOPONTO (GIRO)", 55.00, "FERRAGENS"),
    "CRE12": ("CREMONA 2 PONTOS COMP. 800mm E:15mm", 18.30, "FERRAGENS"),
    "CIL1": ("CILINDRO 45X45MM", 80.00, "FERRAGENS"),
    "CON1": ("CONTRA FECHO STANDARD", 5.40, "FERRAGENS"),
    "CON2": ("CONTRA-TESTA", 11.00, "FERRAGENS"),
    "PAR2": ("PARAFUSOS DE REFORÇO", 0.10, "FERRAGENS"),
    "PAR1": ("PARAFUSOS DE FERRAGEM", 0.15, "FERRAGENS"),
}

_GROUPS = (
    "PERFIS PRINCIPAIS", "BAGUETES", "ACABAMENTOS", "REFORÇOS",
    "VIDROS", "TELA", "VEDAÇÕES", "ACESSÓRIOS", "FERRAGENS",
)


def _validate(cfg: GrConfiguration) -> None:
    if not math.isfinite(float(cfg.width_mm)) or not math.isfinite(float(cfg.height_mm)):
        raise ValueError("Largura e altura GR devem ser finitas.")
    if cfg.width_mm <= 0 or cfg.height_mm <= 0:
        raise ValueError("Largura e altura GR devem ser positivas.")
    if isinstance(cfg.quantity, bool) or not isinstance(cfg.quantity, int) or cfg.quantity < 1:
        raise ValueError("Quantidade GR deve ser inteiro maior ou igual a 1.")
    if cfg.leaf_count != 1:
        raise ValueError("GR_ENGINE_0.4.0 suporta somente 1 folha.")
    if cfg.leaf_system not in GR_LEAF_SYSTEMS:
        raise ValueError(f"tipo de folha fora do escopo do GR_ENGINE_0.4.0: {cfg.leaf_system}")
    checks = (
        (cfg.panel_mode, GR_PANEL_MODE, "painel"),
        (cfg.module_mode, GR_MODULE_MODE, "módulo"),
        (cfg.hinge_description, GR_HINGE, "dobradiça"),
        (cfg.internal_finish, GR_INTERNAL_FINISH, "acabamento interno"),
        (cfg.external_finish, GR_EXTERNAL_FINISH, "acabamento externo"),
    )
    for actual, expected, label in checks:
        if actual != expected:
            raise ValueError(f"{label} fora do escopo do GR_ENGINE_0.4.0: {actual}")

    is_window = cfg.leaf_system == GR_LEAF_SYSTEM_WINDOW_EXTERNAL
    if is_window:
        if cfg.application != GR_APPLICATION_WINDOW:
            raise ValueError("folha de janela GR 60x78 exige aplicação JANELA.")
        if cfg.closure_mode != GR_CLOSURE_WINDOW_CREMONA:
            raise ValueError("janela GR v0.4 suporta somente maçaneta com cremona sem chave.")
        if cfg.cremona_description not in (None, GR_CREMONA_WINDOW_800):
            raise ValueError(
                "janela GR v0.4 suporta somente CREMONA 2 PONTOS COMP. 800mm E:15mm."
            )
    else:
        if cfg.application != GR_APPLICATION_DOOR:
            raise ValueError("folha de porta GR 60x104 exige aplicação PORTA.")
        if cfg.closure_mode not in GR_DOOR_CLOSURES:
            raise ValueError(f"fechamento fora do escopo do GR_ENGINE_0.4.0: {cfg.closure_mode}")
        if cfg.cremona_description is not None:
            raise ValueError("portas GR v0.4 não usam cremona neste recorte.")

    if cfg.shutter_enabled or cfg.screen_enabled:
        raise ValueError("GR_ENGINE_0.4.0 ainda não suporta persiana ou tela.")
    if cfg.bottom_flag_height_mm or cfg.top_flag_height_mm:
        raise ValueError("GR_ENGINE_0.4.0 ainda não suporta bandeiras.")
    if cfg.leaf_horizontal_transoms or cfg.leaf_vertical_transoms:
        raise ValueError("GR_ENGINE_0.4.0 ainda não suporta travessas na folha.")
    if cfg.structural_reinforcement is not None:
        raise ValueError("GR_ENGINE_0.4.0 ainda não suporta reforço estrutural opcional.")


def _component(code: str, role: str, quantity: float, order_quantity: int, *,
               length_mm: float | None = None, source: str) -> BomComponent:
    if not math.isfinite(quantity) or quantity <= 0:
        raise ValueError(f"Quantidade inválida para {role}: {quantity:g}.")
    description, unit_price, category = _MATERIALS[code]
    if length_mm is None:
        unit = "un"
        cost = quantity * unit_price
    else:
        if not math.isfinite(length_mm) or length_mm <= 0:
            raise ValueError(f"Comprimento inválido para {role}: {length_mm:g} mm.")
        unit = "m"
        cost = length_mm / 1000.0 * quantity * unit_price
    return BomComponent(
        category=category,
        role=role,
        material_code=code,
        description=description,
        unit=unit,
        length_mm=round(length_mm, 6) if length_mm is not None else None,
        width_mm=None,
        height_mm=None,
        area_m2=None,
        quantity_per_unit=float(quantity),
        quantity_order=float(quantity * order_quantity),
        unit_price=unit_price,
        cost_per_unit_product=round(cost, 6),
        source=source,
    )


def _finalize(model_description: str, geometry: dict[str, float], bom: list[BomComponent]) -> CalculationResult:
    breakdown = {group: 0.0 for group in _GROUPS}
    for item in bom:
        breakdown[item.category] += item.cost_per_unit_product
    for group in breakdown:
        breakdown[group] = round(breakdown[group], 6)
    unit_cost = round(sum(item.cost_per_unit_product for item in bom), 6)
    breakdown["TOTAL"] = unit_cost
    return CalculationResult(
        model_description=model_description,
        geometry=geometry,
        unit_bom=bom,
        cost_breakdown=breakdown,
        unit_cost=unit_cost,
        calculation_version=GR_ENGINE_VERSION,
    )


def _calculate_door(cfg: GrConfiguration) -> CalculationResult:
    width = float(cfg.width_mm)
    height = float(cfg.height_mm)
    leaf_code = "DE60104-E" if cfg.leaf_system == GR_LEAF_SYSTEM_EXTERNAL else "DE60104"

    frame_width_final = width
    frame_width_cut = width + 5.0
    frame_height_final = height
    frame_height_cut = height + 3.0
    leaf_width_final = width - 64.0
    leaf_width_cut = leaf_width_final + 5.0
    leaf_height_final = height - 37.0
    leaf_height_cut = leaf_height_final + 5.0

    panel_bead_width = leaf_width_final - 172.0
    panel_bead_height = leaf_height_final - 172.0
    panel_secondary_height = -104.0
    panel_strip_qty = (panel_bead_height + panel_secondary_height) / 140.0

    frame_reinf_width = frame_width_final - 116.0
    frame_reinf_height = frame_height_final - 116.0
    leaf_reinf_width = leaf_width_final - 120.0
    leaf_reinf_height = leaf_height_final - 120.0

    positive = {
        "leaf_width_final_mm": leaf_width_final,
        "leaf_height_final_mm": leaf_height_final,
        "panel_bead_width_mm": panel_bead_width,
        "panel_bead_height_mm": panel_bead_height,
        "panel_strip_quantity": panel_strip_qty,
        "frame_reinforcement_width_mm": frame_reinf_width,
        "frame_reinforcement_height_mm": frame_reinf_height,
        "leaf_reinforcement_width_mm": leaf_reinf_width,
        "leaf_reinforcement_height_mm": leaf_reinf_height,
    }
    invalid = {name: value for name, value in positive.items() if value <= 0 or not math.isfinite(value)}
    if invalid:
        details = ", ".join(f"{k}={v:g}" for k, v in invalid.items())
        raise ValueError(f"Dimensões tecnicamente impossíveis para GR v0.4: {details}")

    bom = [
        _component("DE6058", "FRAME_WIDTH", 1, cfg.quantity, length_mm=frame_width_cut, source="GR!E8/G8"),
        _component("DE6058", "FRAME_HEIGHT", 2, cfg.quantity, length_mm=frame_height_cut, source="GR!E9/G9"),
        _component(leaf_code, "LEAF_WIDTH", 2, cfg.quantity, length_mm=leaf_width_cut, source="GR!B10/E10/G10"),
        _component(leaf_code, "LEAF_HEIGHT", 2, cfg.quantity, length_mm=leaf_height_cut, source="GR!B11/E11/G11"),
        _component("BA2516", "PANEL_BEAD_WIDTH", 2, cfg.quantity, length_mm=panel_bead_width, source="GR!E16/G16"),
        _component("BA2516", "PANEL_BEAD_HEIGHT", 2, cfg.quantity, length_mm=panel_bead_height, source="GR!E17/G17"),
        _component("DE20150", "PANEL_FILL", panel_strip_qty, cfg.quantity, length_mm=panel_bead_width, source="GR!E41/G41"),
        _component("AC7012", "INTERNAL_FINISH_WIDTH", 1, cfg.quantity, length_mm=width + 140.0, source="GR!E43/G43"),
        _component("AC7012", "INTERNAL_FINISH_HEIGHT", 2, cfg.quantity, length_mm=height + 140.0, source="GR!E44/G44"),
        _component("AC3004", "EXTERNAL_FINISH_WIDTH", 1, cfg.quantity, length_mm=width + 60.0, source="GR!E45/G45"),
        _component("AC3004", "EXTERNAL_FINISH_HEIGHT", 2, cfg.quantity, length_mm=height + 60.0, source="GR!E46/G46"),
        _component("RAG - DE6058", "FRAME_REINFORCEMENT_WIDTH", 1, cfg.quantity, length_mm=frame_reinf_width, source="GR!E58/G58"),
        _component("RAG - DE6058", "FRAME_REINFORCEMENT_HEIGHT", 2, cfg.quantity, length_mm=frame_reinf_height, source="GR!E59/G59"),
        _component("RAG - DE60104", "LEAF_REINFORCEMENT_WIDTH", 2, cfg.quantity, length_mm=leaf_reinf_width, source="GR!E60/G60"),
        _component("RAG - DE60104", "LEAF_REINFORCEMENT_HEIGHT", 2, cfg.quantity, length_mm=leaf_reinf_height, source="GR!E61/G61"),
        _component(
            "AC0312", "SQUARING_BLOCK", 4, cfg.quantity,
            source="GR!G83/I83 + RESOLVED_PHYSICAL_2026-09-16",
        ),
        _component("AC0001", "DRAIN_CAP", 1, cfg.quantity, source="GR!G84/I84"),
        _component("DOB3", "HINGE_90MM", 3, cfg.quantity, source="GR!G105/I105"),
        _component("MAC4", "DOUBLE_HANDLE", 1, cfg.quantity, source="GR!G111/I111"),
    ]

    if cfg.closure_mode == GR_CLOSURE_MULTIPOINT:
        bom.extend([
            _component("FEC5", "MULTIPOINT_LOCK", 1, cfg.quantity, source="GR!G112/I112"),
            _component("CIL1", "CYLINDER_45X45", 1, cfg.quantity, source="GR!G113/I113"),
            _component("CON1", "STANDARD_COUNTER_LOCK", 4, cfg.quantity, source="GR!G114/I114"),
            _component("CON2", "STRIKE_PLATE", 1, cfg.quantity, source="GR!G115/I115"),
        ])
        counter_lock_qty = 4.0
    else:
        bom.extend([
            _component("FEC6", "MONOPOINT_LOCK", 1, cfg.quantity, source="GR!G112/I112"),
            _component("CIL1", "CYLINDER_45X45", 1, cfg.quantity, source="GR!G113/I113"),
            _component("CON2", "STRIKE_PLATE", 1, cfg.quantity, source="GR!G115/I115"),
        ])
        counter_lock_qty = 0.0

    reinforcement_screws = 4.0 * (
        (frame_width_cut + frame_height_cut) / 1000.0
        + 2.0 * (leaf_width_cut + leaf_height_cut) / 1000.0
    )
    hardware_screws = 3.0 * 8.0 + (1.0 + 1.0 + counter_lock_qty) * 2.0
    bom.extend([
        _component("PAR2", "REINFORCEMENT_SCREWS", reinforcement_screws, cfg.quantity, source="GR!G118/I118"),
        _component("PAR1", "HARDWARE_SCREWS", hardware_screws, cfg.quantity, source="GR!G119/I119"),
    ])

    geometry = {
        "frame_width_final_mm": round(frame_width_final, 6),
        "frame_width_cut_mm": round(frame_width_cut, 6),
        "frame_height_final_mm": round(frame_height_final, 6),
        "frame_height_cut_mm": round(frame_height_cut, 6),
        "leaf_width_final_mm": round(leaf_width_final, 6),
        "leaf_width_cut_mm": round(leaf_width_cut, 6),
        "leaf_height_final_mm": round(leaf_height_final, 6),
        "leaf_height_cut_mm": round(leaf_height_cut, 6),
        "panel_bead_width_mm": round(panel_bead_width, 6),
        "panel_bead_height_mm": round(panel_bead_height, 6),
        "panel_fill_strip_length_mm": round(panel_bead_width, 6),
        "panel_fill_strip_quantity": round(panel_strip_qty, 6),
        "frame_reinforcement_width_mm": round(frame_reinf_width, 6),
        "frame_reinforcement_height_mm": round(frame_reinf_height, 6),
        "leaf_reinforcement_width_mm": round(leaf_reinf_width, 6),
        "leaf_reinforcement_height_mm": round(leaf_reinf_height, 6),
    }
    return _finalize("PORTA 1 FOLHA DE GIRO COM PAINEL HORIZONTAL", geometry, bom)


def _calculate_window(cfg: GrConfiguration) -> CalculationResult:
    width = float(cfg.width_mm)
    height = float(cfg.height_mm)

    # GR!D8:E11 for JANELA / DE6078 / 1 folha / módulo único.
    frame_width_final = width
    frame_width_cut = width + 5.0
    frame_height_final = height
    frame_height_cut = height + 5.0
    leaf_width_final = width - 64.0
    leaf_width_cut = leaf_width_final + 5.0
    leaf_height_final = height - 64.0
    leaf_height_cut = leaf_height_final + 5.0

    # LISTAPERFIS!D16=60 and D18=18 for DE6078 / DE6072.
    panel_bead_width = leaf_width_final - 120.0
    panel_bead_height = leaf_height_final - 120.0
    panel_secondary_height = -78.0
    panel_strip_qty = (panel_bead_height + panel_secondary_height) / 140.0

    frame_reinf_width = frame_width_final - 80.0
    frame_reinf_height = frame_height_final - 80.0
    leaf_reinf_width = leaf_width_final - 120.0
    leaf_reinf_height = leaf_height_final - 120.0

    positive = {
        "leaf_width_final_mm": leaf_width_final,
        "leaf_height_final_mm": leaf_height_final,
        "panel_bead_width_mm": panel_bead_width,
        "panel_bead_height_mm": panel_bead_height,
        "panel_strip_quantity": panel_strip_qty,
        "frame_reinforcement_width_mm": frame_reinf_width,
        "frame_reinforcement_height_mm": frame_reinf_height,
        "leaf_reinforcement_width_mm": leaf_reinf_width,
        "leaf_reinforcement_height_mm": leaf_reinf_height,
    }
    invalid = {name: value for name, value in positive.items() if value <= 0 or not math.isfinite(value)}
    if invalid:
        details = ", ".join(f"{k}={v:g}" for k, v in invalid.items())
        raise ValueError(f"Dimensões tecnicamente impossíveis para GR v0.4: {details}")

    bom = [
        _component("DE6058", "FRAME_WIDTH", 2, cfg.quantity, length_mm=frame_width_cut, source="GR!E8/G8"),
        _component("DE6058", "FRAME_HEIGHT", 2, cfg.quantity, length_mm=frame_height_cut, source="GR!E9/G9"),
        _component("DE6078", "LEAF_WIDTH", 2, cfg.quantity, length_mm=leaf_width_cut, source="GR!B10/E10/G10"),
        _component("DE6078", "LEAF_HEIGHT", 2, cfg.quantity, length_mm=leaf_height_cut, source="GR!B11/E11/G11"),
        _component("BA2516", "PANEL_BEAD_WIDTH", 2, cfg.quantity, length_mm=panel_bead_width, source="GR!E16/G16"),
        _component("BA2516", "PANEL_BEAD_HEIGHT", 2, cfg.quantity, length_mm=panel_bead_height, source="GR!E17/G17"),
        _component("DE20150", "PANEL_FILL", panel_strip_qty, cfg.quantity, length_mm=panel_bead_width, source="GR!E41/G41"),
        _component("AC7012", "INTERNAL_FINISH_WIDTH", 2, cfg.quantity, length_mm=width + 140.0, source="GR!E43/G43"),
        _component("AC7012", "INTERNAL_FINISH_HEIGHT", 2, cfg.quantity, length_mm=height + 140.0, source="GR!E44/G44"),
        _component("AC3004", "EXTERNAL_FINISH_WIDTH", 2, cfg.quantity, length_mm=width + 60.0, source="GR!E45/G45"),
        _component("AC3004", "EXTERNAL_FINISH_HEIGHT", 2, cfg.quantity, length_mm=height + 60.0, source="GR!E46/G46"),
        _component("RAG - DE6058", "FRAME_REINFORCEMENT_WIDTH", 2, cfg.quantity, length_mm=frame_reinf_width, source="GR!E58/G58"),
        _component("RAG - DE6058", "FRAME_REINFORCEMENT_HEIGHT", 2, cfg.quantity, length_mm=frame_reinf_height, source="GR!E59/G59"),
        _component("RAG - DE6078", "LEAF_REINFORCEMENT_WIDTH", 2, cfg.quantity, length_mm=leaf_reinf_width, source="GR!E60/G60"),
        _component("RAG - DE6078", "LEAF_REINFORCEMENT_HEIGHT", 2, cfg.quantity, length_mm=leaf_reinf_height, source="GR!E61/G61"),
        _component(
            "AC0312", "SQUARING_BLOCK", 4, cfg.quantity,
            source="GR!G83/I83 + RESOLVED_PHYSICAL_2026-09-16",
        ),
        _component("AC0001", "DRAIN_CAP", 2, cfg.quantity, source="GR!G84/I84"),
        _component("DOB3", "HINGE_90MM", 3, cfg.quantity, source="GR!G105/I105"),
        _component("MAC1", "STANDARD_HANDLE", 1, cfg.quantity, source="GR!G111/I111"),
        _component(
            "CRE12", "CREMONA_800_E15", 1, cfg.quantity,
            source="GR!G112/I112 + RESOLVED_PHYSICAL_2026-09-16",
        ),
        _component("CON1", "STANDARD_COUNTER_LOCK", 2, cfg.quantity, source="GR!G114/I114"),
    ]

    reinforcement_screws = 4.0 * (
        2.0 * (frame_width_cut + frame_height_cut) / 1000.0
        + 2.0 * (leaf_width_cut + leaf_height_cut) / 1000.0
    )
    hardware_screws = 3.0 * 8.0 + (1.0 + 1.0 + 2.0) * 2.0
    bom.extend([
        _component("PAR2", "REINFORCEMENT_SCREWS", reinforcement_screws, cfg.quantity, source="GR!G118/I118"),
        _component("PAR1", "HARDWARE_SCREWS", hardware_screws, cfg.quantity, source="GR!G119/I119"),
    ])

    geometry = {
        "frame_width_final_mm": round(frame_width_final, 6),
        "frame_width_cut_mm": round(frame_width_cut, 6),
        "frame_height_final_mm": round(frame_height_final, 6),
        "frame_height_cut_mm": round(frame_height_cut, 6),
        "leaf_width_final_mm": round(leaf_width_final, 6),
        "leaf_width_cut_mm": round(leaf_width_cut, 6),
        "leaf_height_final_mm": round(leaf_height_final, 6),
        "leaf_height_cut_mm": round(leaf_height_cut, 6),
        "panel_bead_width_mm": round(panel_bead_width, 6),
        "panel_bead_height_mm": round(panel_bead_height, 6),
        "panel_fill_strip_length_mm": round(panel_bead_width, 6),
        "panel_fill_strip_quantity": round(panel_strip_qty, 6),
        "frame_reinforcement_width_mm": round(frame_reinf_width, 6),
        "frame_reinforcement_height_mm": round(frame_reinf_height, 6),
        "leaf_reinforcement_width_mm": round(leaf_reinf_width, 6),
        "leaf_reinforcement_height_mm": round(leaf_reinf_height, 6),
    }
    return _finalize("JANELA 1 FOLHA DE GIRO COM PAINEL HORIZONTAL", geometry, bom)


def calculate_gr(cfg: GrConfiguration) -> CalculationResult:
    """Calcula os recortes GR comprovados pelo XLSM oficial e pela fabricação."""
    _validate(cfg)
    if cfg.leaf_system == GR_LEAF_SYSTEM_WINDOW_EXTERNAL:
        return _calculate_window(cfg)
    return _calculate_door(cfg)
