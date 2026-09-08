from __future__ import annotations

import math

from .models import (
    LeafSystem, ApplicationType, SlidingConfiguration, CalculationResult,
    BomComponent, EngineeringWarning, GridAxis, GridOpening, Transom,
    TransomOrientation, FixedPanelPosition, FixedPanelGeometry, GlassPanel,
    ShutterMode,
)
from .catalog import (
    MATERIALS, PARAMETERS, GLASSES, HARDWARE, FINISH_OPTIONS,
    CLOSURE_OPTIONS, CREMONA_OPTIONS, ROLLER_OPTIONS,
    STRUCTURAL_REINFORCEMENT_CODES, SHUTTER_BOX_OPTIONS,
    SHUTTER_SLAT_OPTIONS, normalize
)
from .cr_geometry import make_openings, partition_axis, validate_count

SUPPORTED_LEAF_COUNTS = {2, 3, 4, 6}


def _shutter_mode(cfg: SlidingConfiguration) -> ShutterMode | None:
    if cfg.shutter is None:
        return None
    try:
        return ShutterMode(cfg.shutter.mode)
    except ValueError as exc:
        raise ValueError(f"Modo de persiana inválido: {cfg.shutter.mode}") from exc


def _has_complete_shutter(cfg: SlidingConfiguration) -> bool:
    mode = _shutter_mode(cfg)
    return mode is not None and mode != ShutterMode.NONE


def _has_shutter(cfg: SlidingConfiguration) -> bool:
    mode = _shutter_mode(cfg)
    return cfg.shutter_enabled if mode is None else mode != ShutterMode.NONE


def _screen_frame_count(cfg: SlidingConfiguration) -> int:
    """Quantidade física inteira; CR!G69 mantém fator de área separado."""
    return math.ceil(cfg.leaf_count / 2) if cfg.screen_enabled else 0


def _screen_profile_piece_qty(cfg: SlidingConfiguration) -> float:
    return float(2 * _screen_frame_count(cfg))


def _linear_component(category: str, role: str, material_code: str, length_mm: float,
                      qty_unit: float, order_qty: int,
                      source: str | None = None) -> BomComponent:
    material = MATERIALS[material_code]
    length_mm = float(length_mm)
    qty_unit = float(qty_unit)
    if not math.isfinite(length_mm) or length_mm < 0:
        raise ValueError(f"Comprimento inválido para {role}: {length_mm} mm.")
    if not math.isfinite(qty_unit) or qty_unit < 0:
        raise ValueError(f"Quantidade inválida para {role}: {qty_unit}.")
    cost = (length_mm / 1000.0) * qty_unit * material.unit_price
    return BomComponent(
        category=category,
        role=role,
        material_code=material.code,
        description=material.description,
        unit="m",
        length_mm=round(length_mm, 6),
        width_mm=None,
        height_mm=None,
        area_m2=None,
        quantity_per_unit=qty_unit,
        quantity_order=qty_unit * order_qty,
        unit_price=material.unit_price,
        cost_per_unit_product=round(cost, 6),
        source=source,
    )


def _unit_component(category: str, role: str, material, qty_unit: float,
                    order_qty: int, source: str | None = None) -> BomComponent:
    qty_unit = float(qty_unit)
    if not math.isfinite(qty_unit) or qty_unit < 0:
        raise ValueError(f"Quantidade inválida para {role}: {qty_unit}.")
    cost = qty_unit * material.unit_price
    return BomComponent(
        category=category,
        role=role,
        material_code=material.code,
        description=material.description,
        unit="un",
        length_mm=None,
        width_mm=None,
        height_mm=None,
        area_m2=None,
        quantity_per_unit=qty_unit,
        quantity_order=qty_unit * order_qty,
        unit_price=material.unit_price,
        cost_per_unit_product=round(cost, 6),
        source=source,
    )


def _area_component(category: str, role: str, material, width_mm: float,
                    height_mm: float, qty_unit: float, order_qty: int,
                    source: str | None = None) -> BomComponent:
    width_mm = float(width_mm)
    height_mm = float(height_mm)
    qty_unit = float(qty_unit)
    if (
        not math.isfinite(width_mm) or width_mm <= 0
        or not math.isfinite(height_mm) or height_mm <= 0
    ):
        raise ValueError(f"Dimensões de área inválidas para {role}.")
    if not math.isfinite(qty_unit) or qty_unit < 0:
        raise ValueError(f"Quantidade inválida para {role}: {qty_unit}.")
    area_each = (width_mm / 1000.0) * (height_mm / 1000.0)
    cost = area_each * qty_unit * material.unit_price
    return BomComponent(
        category=category,
        role=role,
        material_code=material.code,
        description=material.description,
        unit="m²",
        length_mm=None,
        width_mm=round(width_mm, 6),
        height_mm=round(height_mm, 6),
        area_m2=round(area_each, 6),
        quantity_per_unit=qty_unit,
        quantity_order=qty_unit * order_qty,
        unit_price=material.unit_price,
        cost_per_unit_product=round(cost, 6),
        source=source,
    )


def _validate(cfg: SlidingConfiguration) -> None:
    if (
        not math.isfinite(float(cfg.width_mm))
        or not math.isfinite(float(cfg.height_mm))
        or cfg.width_mm <= 0
        or cfg.height_mm <= 0
    ):
        raise ValueError("Largura e altura devem ser finitas e positivas.")
    if (
        isinstance(cfg.quantity, bool)
        or not math.isfinite(float(cfg.quantity))
        or float(cfg.quantity) != int(cfg.quantity)
        or cfg.quantity <= 0
    ):
        raise ValueError("Quantidade deve ser inteira e positiva.")
    if cfg.leaf_count not in SUPPORTED_LEAF_COUNTS:
        raise ValueError("Número de folhas suportado: 2, 3, 4 ou 6.")
    if normalize(cfg.glass_description) not in GLASSES:
        raise ValueError(f"Vidro não encontrado no catálogo: {cfg.glass_description}")
    if normalize(cfg.internal_finish) not in {normalize(x) for x in FINISH_OPTIONS}:
        raise ValueError(f"Acabamento interno inválido: {cfg.internal_finish}")
    if normalize(cfg.external_finish) not in {normalize(x) for x in FINISH_OPTIONS}:
        raise ValueError(f"Acabamento externo inválido: {cfg.external_finish}")
    if normalize(cfg.closure_mode) not in {normalize(x) for x in CLOSURE_OPTIONS}:
        raise ValueError(f"Fechamento inválido: {cfg.closure_mode}")
    if normalize(cfg.cremona_base) not in {normalize(x) for x in CREMONA_OPTIONS}:
        raise ValueError(f"Cremona inválida: {cfg.cremona_base}")
    if normalize(cfg.roller_description) not in {normalize(x) for x in ROLLER_OPTIONS}:
        raise ValueError(f"Roldana inválida: {cfg.roller_description}")
    mode = _shutter_mode(cfg)
    if cfg.shutter is not None:
        if cfg.shutter_enabled and mode == ShutterMode.NONE:
            raise ValueError(
                "shutter_enabled não pode ser verdadeiro quando o modo é SEM PERSIANA."
            )
        if normalize(cfg.shutter.box_description) not in {
            normalize(value) for value in SHUTTER_BOX_OPTIONS
        }:
            raise ValueError(f"Caixa de persiana inválida: {cfg.shutter.box_description}")
        if normalize(cfg.shutter.slat_description) not in {
            normalize(value) for value in SHUTTER_SLAT_OPTIONS
        }:
            raise ValueError(f"Tala de persiana inválida: {cfg.shutter.slat_description}")
    validate_count(cfg.leaf_grid.horizontal_transoms, "travessas horizontais das folhas")
    validate_count(cfg.leaf_grid.vertical_transoms, "travessas verticais das folhas")
    for panel_name, panel in (
        ("bandeira inferior", cfg.bottom_fixed_panel),
        ("bandeira superior", cfg.top_fixed_panel),
    ):
        if panel is None:
            continue
        if not math.isfinite(float(panel.height_mm)) or panel.height_mm <= 0:
            raise ValueError(f"Altura da {panel_name} deve ser finita e positiva.")
        validate_count(panel.horizontal_transoms, f"travessas horizontais da {panel_name}")
        validate_count(panel.vertical_transoms, f"travessas verticais da {panel_name}")
    if cfg.structural_reinforcement is not None:
        if cfg.structural_reinforcement.material_code not in STRUCTURAL_REINFORCEMENT_CODES:
            raise ValueError(
                "Reforço estrutural inválido: "
                f"{cfg.structural_reinforcement.material_code}"
            )
        if cfg.bottom_fixed_panel is None and cfg.top_fixed_panel is None:
            raise ValueError("Reforço estrutural exige ao menos uma bandeira.")


def _select_frame(cfg: SlidingConfiguration) -> str:
    if cfg.leaf_system == LeafSystem.DESIGN_DOOR_60x111:
        return "DE16652"
    if cfg.leaf_count in {3, 6} or cfg.screen_enabled:
        return "PR13852"
    return "PR8852"


def _frame_profile_qty(cfg: SlidingConfiguration) -> float:
    # Compatibilidade com CR!G8.
    if (
        cfg.leaf_system == LeafSystem.PRIME_DOOR_42x88
        and cfg.screen_enabled
        and cfg.leaf_count in {3, 6}
    ):
        return 4.0
    return 2.0


def _select_leaf(cfg: SlidingConfiguration) -> str:
    return {
        LeafSystem.PRIME_WINDOW_42x66: "PR4266",
        LeafSystem.PRIME_DOOR_42x88: "PR4288",
        LeafSystem.DESIGN_DOOR_60x111: "DE60111",
    }[cfg.leaf_system]


def _select_interlock(cfg: SlidingConfiguration) -> str:
    return {
        LeafSystem.PRIME_WINDOW_42x66: "PR4536",
        LeafSystem.PRIME_DOOR_42x88: "PR4550",
        LeafSystem.DESIGN_DOOR_60x111: "DE4109",
    }[cfg.leaf_system]


def _select_frame_reinforcement(frame_code: str) -> str:
    return {
        "PR8852": "RAG - PR8852",
        "PR13852": "RAG - PR13852",
        "DE16652": "RAG - DE16652",
    }[frame_code]


def _select_leaf_reinforcement(leaf_code: str) -> str:
    return {
        "PR4266": "RAG - PR4266",
        "PR4288": "RAG - PR4288",
        "DE60111": "RAG - DE60111",
    }[leaf_code]


def _select_leaf_transom(cfg: SlidingConfiguration) -> tuple[str, str]:
    if cfg.leaf_system == LeafSystem.DESIGN_DOOR_60x111:
        return "DE6072", "RAG - DE6072"
    return "PR4263", "RAG - PR4263"


def _interlock_qty(cfg: SlidingConfiguration) -> int:
    if cfg.leaf_count == 2:
        return 3 if cfg.screen_enabled else 2
    if cfg.leaf_count == 3:
        return 4
    if cfg.leaf_count == 4:
        return 6 if cfg.screen_enabled else 4
    if cfg.leaf_count == 6:
        return 12
    raise AssertionError("leaf_count validado anteriormente")


def _leaf_width(cfg: SlidingConfiguration, frame_dim_mm: float, leaf_dim_mm: float,
                warnings: list[EngineeringWarning]) -> float:
    n = cfg.leaf_count
    p = PARAMETERS

    # Mantém o comportamento legado do CR!D10 para comparação 1:1.
    if cfg.leaf_system == LeafSystem.DESIGN_DOOR_60x111:
        overlap = p["prime_overlap_mm"]
        warnings.append(EngineeringWarning(
            "DT-CR-003",
            "Compatibilidade Excel: largura DESIGN ainda usa o transpasse PRIME (PFAB B3)."
        ))
        if n in {4, 6}:
            if n == 6:
                central = p["prime_central_meeting_mm"]
                warnings.append(EngineeringWarning(
                    "DT-CR-004",
                    "Compatibilidade Excel: 6 folhas DESIGN usa fechamento central PRIME (PFAB B9)."
                ))
            else:
                central = p["design_central_meeting_mm"]
        else:
            central = 0.0
    else:
        overlap = p["prime_overlap_mm"]
        central = p["prime_central_meeting_mm"] if n in {4, 6} else 0.0

    overlap_count = {2: 1, 3: 2, 4: 2, 6: 4}[n]
    return (
        cfg.width_mm - central - 2 * frame_dim_mm
        + 2 * overlap + overlap_count * leaf_dim_mm
    ) / n


def _select_baguette(cfg: SlidingConfiguration, thickness_mm: float | None) -> str:
    if thickness_mm is None:
        raise ValueError("Não foi possível determinar a espessura do vidro.")
    t = float(thickness_mm)

    if cfg.leaf_system in {LeafSystem.PRIME_WINDOW_42x66, LeafSystem.PRIME_DOOR_42x88}:
        if t < 8:
            return "BA2516"
        if t < 12:
            return "BA2018"
        if t < 16:
            return "BA1816"
        if t < 17:
            return "BA1216"
        if t < 24:
            return "BA1016"
        if t < 25:
            return "BA0716"
    else:
        if t < 8:
            return "BA3518"
        if t < 12:
            return "BA3218"
        if t < 19:
            return "BA2516"
        if t < 22:
            return "BA2018"
        if t < 26:
            return "BA1816"
        if t < 31:
            return "BA1216"
        if t < 34:
            return "BA1016"
        if t < 35:
            return "BA0716"

    raise ValueError(
        f"Espessura de vidro {t:g} mm fora das faixas de baguete do módulo CR."
    )


def _select_fixed_panel_baguette(thickness_mm: float | None) -> str:
    if thickness_mm is None:
        raise ValueError("Não foi possível determinar a espessura do vidro.")
    t = float(thickness_mm)
    if t < 8:
        return "BA3518"
    if t < 12:
        return "BA3218"
    if t < 19:
        return "BA2516"
    if t < 22:
        return "BA2018"
    if t < 26:
        return "BA1816"
    if t < 31:
        return "BA1216"
    if t < 34:
        return "BA1016"
    if t < 35:
        return "BA0716"
    raise ValueError(
        f"Espessura de vidro {t:g} mm fora das faixas de bandeira do módulo CR."
    )


def _fixed_panel_geometry(
    cfg: SlidingConfiguration,
    position: FixedPanelPosition,
) -> FixedPanelGeometry | None:
    panel_cfg = (
        cfg.bottom_fixed_panel
        if position == FixedPanelPosition.BOTTOM
        else cfg.top_fixed_panel
    )
    if panel_cfg is None:
        return None

    frame = MATERIALS["DE6058"]
    transom = MATERIALS["DE6072"]
    frame_rebate = float(frame.dim_b_mm or 0.0)
    transom_face = float(transom.dim_b_mm or 0.0)
    clearance = (
        PARAMETERS["structural_reinforcement_panel_clearance_mm"]
        if cfg.structural_reinforcement is not None
        else 0.0
    )
    frame_height = float(panel_cfg.height_mm) - clearance
    if frame_height <= 0:
        raise ValueError(
            f"Altura útil da bandeira {position.value} ficou inválida após "
            "o desconto do reforço estrutural."
        )

    inner_width = float(cfg.width_mm) - 2 * frame_rebate
    inner_height = frame_height - 2 * frame_rebate
    columns = partition_axis(
        inner_width,
        panel_cfg.vertical_transoms,
        transom_face,
        (),
        GridAxis.COLUMNS,
        f"largura da bandeira {position.value}",
    )
    rows = partition_axis(
        inner_height,
        panel_cfg.horizontal_transoms,
        transom_face,
        (),
        GridAxis.ROWS,
        f"altura da bandeira {position.value}",
    )
    source = f"FIXED_PANEL_{position.value}"
    openings = make_openings(source, columns, rows, 1.0)
    return FixedPanelGeometry(
        position=position,
        width_mm=round(float(cfg.width_mm), 6),
        nominal_height_mm=round(float(panel_cfg.height_mm), 6),
        frame_height_mm=round(frame_height, 6),
        horizontal_transoms=panel_cfg.horizontal_transoms,
        vertical_transoms=panel_cfg.vertical_transoms,
        openings=openings,
    )


def _glass_panel(opening: GridOpening, glass, clearance_mm: float) -> GlassPanel:
    width = float(opening.width_mm) - clearance_mm
    height = float(opening.height_mm) - clearance_mm
    if width <= 0 or height <= 0:
        raise ValueError(
            f"Dimensões de vidro ficaram inválidas em {opening.source} "
            f"[{opening.row_index},{opening.column_index}]."
        )
    area = width / 1000.0 * height / 1000.0
    unit_cost = area * glass.unit_price
    return GlassPanel(
        source=opening.source,
        position=f"R{opening.row_index + 1}C{opening.column_index + 1}",
        width_mm=round(width, 6),
        height_mm=round(height, 6),
        quantity=opening.quantity,
        material_code=glass.code,
        material_description=glass.description,
        area_m2=round(area, 6),
        unit_cost=round(unit_cost, 6),
        total_cost=round(unit_cost * opening.quantity, 6),
    )


def _hardware_lookup(description: str, warnings: list[EngineeringWarning]):
    key = normalize(description)
    material = HARDWARE.get(key)
    if material is None:
        warnings.append(EngineeringWarning(
            "HW-NOT-FOUND",
            f"Ferragem não encontrada no catálogo do Excel: {description}"
        ))
    return material


def _finish_code(description: str) -> str | None:
    key = normalize(description)
    for label, code in FINISH_OPTIONS.items():
        if normalize(label) == key:
            return code
    return None


def _add_finish(bom: list[BomComponent], cfg: SlidingConfiguration,
                description: str, side: str, extra_mm: float) -> None:
    code = _finish_code(description)
    if code is None:
        return
    # CR!G49/G51: a quantidade depende de I2 (Aplicação), não do tipo da folha.
    # Isso é importante porque o Excel permite, por exemplo, folha DESIGN com aplicação JANELA.
    width_qty = 1.0 if cfg.application == ApplicationType.DOOR else 2.0
    bom.append(_linear_component(
        "ACABAMENTOS", f"{side}_FINISH_HORIZONTAL", code,
        cfg.width_mm + extra_mm, width_qty, cfg.quantity
    ))
    bom.append(_linear_component(
        "ACABAMENTOS", f"{side}_FINISH_VERTICAL", code,
        cfg.height_mm + extra_mm, 2.0, cfg.quantity
    ))


def _add_shutter(
    bom: list[BomComponent],
    cfg: SlidingConfiguration,
    warnings: list[EngineeringWarning],
) -> None:
    """Migra CR!54:60 e CR!120:136 com rastreabilidade por célula."""
    if not _has_complete_shutter(cfg):
        return

    mode = _shutter_mode(cfg)
    assert mode is not None and mode != ShutterMode.NONE
    p = PARAMETERS
    panel_count = {
        ShutterMode.MANUAL_SINGLE: 1,
        ShutterMode.MANUAL_DOUBLE_SHARED_SHAFT: 2,
        ShutterMode.MANUAL_DOUBLE_INDEPENDENT_SHAFTS: 2,
        ShutterMode.BUTTON_SINGLE: 1,
        ShutterMode.BUTTON_DOUBLE: 2,
        ShutterMode.BUTTON_TRIPLE: 3,
        ShutterMode.REMOTE_SINGLE: 1,
        ShutterMode.REMOTE_DOUBLE: 2,
        ShutterMode.REMOTE_TRIPLE: 3,
    }[mode]
    manual = mode in {
        ShutterMode.MANUAL_SINGLE,
        ShutterMode.MANUAL_DOUBLE_SHARED_SHAFT,
        ShutterMode.MANUAL_DOUBLE_INDEPENDENT_SHAFTS,
    }
    independent = mode == ShutterMode.MANUAL_DOUBLE_INDEPENDENT_SHAFTS
    button = mode in {
        ShutterMode.BUTTON_SINGLE,
        ShutterMode.BUTTON_DOUBLE,
        ShutterMode.BUTTON_TRIPLE,
    }
    remote = mode in {
        ShutterMode.REMOTE_SINGLE,
        ShutterMode.REMOTE_DOUBLE,
        ShutterMode.REMOTE_TRIPLE,
    }

    box_length = cfg.width_mm - p["shutter_box_end_clearance_mm"]
    guide_length = cfg.height_mm - p["shutter_box_height_mm"]
    slat_width = (
        (
            cfg.width_mm
            - 2 * p["shutter_side_guide_width_mm"]
            - (panel_count - 1) * p["shutter_central_guide_width_mm"]
        )
        / panel_count
        - p["shutter_slat_clearance_mm"]
    )
    if min(box_length, guide_length, slat_width) <= 0:
        raise ValueError("Dimensões da persiana ficaram inválidas.")

    # O XLSM usa (altura/40)*painéis, inclusive fracionário. Cada tala é uma
    # peça física de barra; a Engine arredonda para cima para cobrir a altura.
    slat_qty = float(math.ceil(cfg.height_mm / p["shutter_slat_height_mm"]) * panel_count)
    shaft_length = (
        cfg.width_mm / 2.0 - p["shutter_shaft_clearance_mm"]
        if independent
        else cfg.width_mm - p["shutter_shaft_clearance_mm"]
    )
    if shaft_length <= 0:
        raise ValueError("Comprimento do eixo da persiana ficou inválido.")
    # No modo de eixos independentes o XLSM corta meia largura, mas registra
    # apenas 1 peça. Dois eixos são fisicamente exigidos e chegam ao FFD.
    shaft_qty = 2.0 if independent else 1.0

    bom.extend([
        _linear_component("PERSIANA", "SHUTTER_BOX", "321040", box_length, 1, cfg.quantity, "CR!D54/G54"),
        _linear_component("PERSIANA", "SHUTTER_SIDE_GUIDE", "327201", guide_length, 2, cfg.quantity, "CR!D55/G55"),
        _linear_component("PERSIANA", "SHUTTER_SLAT", "326015_F", slat_width, slat_qty, cfg.quantity, "CR!D57/G57"),
        _linear_component("PERSIANA", "SHUTTER_TERMINAL", "311712", slat_width, panel_count, cfg.quantity, "CR!D58/G58"),
        _linear_component("PERSIANA", "SHUTTER_SHAFT", "375021", shaft_length, shaft_qty, cfg.quantity, "CR!D59/G59"),
        _linear_component("PERSIANA", "SHUTTER_GUIDE_EXTENDER", "327019", guide_length, 2, cfg.quantity, "CR!D60/G60"),
    ])
    if panel_count > 1:
        bom.append(_linear_component(
            "PERSIANA", "SHUTTER_CENTRAL_GUIDE", "327204",
            guide_length, panel_count - 1, cfg.quantity, "CR!D56/G56",
        ))

    motor_cover_qty = 0.0 if manual else 1.0
    pulley_plate_qty = 2.0 if independent else (1.0 if manual else 0.0)
    end_plate_qty = 0.0 if independent else 1.0
    independent_divider_qty = 1.0 if independent else 0.0
    shared_divider_qty = 0.0 if panel_count == 1 or independent else float(panel_count - 1)
    pulley_qty = pulley_plate_qty
    end_cap_qty = end_plate_qty + 2.0 * independent_divider_qty
    unit_lines = [
        ("SHUTTER_LATERAL_COVER", "370113", 2.0 if manual else 1.0, "CR!G120"),
        ("SHUTTER_PULLEY_PLATE", "371513_4", pulley_plate_qty, "CR!G121"),
        ("SHUTTER_END_PLATE", "371513_2", end_plate_qty, "CR!G122"),
        ("SHUTTER_MOTOR_COVER", "370141", motor_cover_qty, "CR!G123"),
        ("SHUTTER_MOTOR_PLATE", "371553", motor_cover_qty, "CR!G124"),
        ("SHUTTER_SHARED_SHAFT_DIVIDER", "371143", shared_divider_qty, "CR!G125"),
        ("SHUTTER_INDEPENDENT_SHAFT_DIVIDER", "371127", independent_divider_qty, "CR!G126"),
        ("SHUTTER_PULLEY", "375110", pulley_qty, "CR!G127"),
        ("SHUTTER_END_CAP", "375213", end_cap_qty, "CR!G128"),
        ("SHUTTER_END_CAP_ADAPTER", "375234", end_cap_qty, "CR!G129"),
        ("SHUTTER_RECESSED_WINDER", "375339", pulley_qty, "CR!G130"),
        ("SHUTTER_REMOTE_MOTOR", "MOT1", 1.0 if remote else 0.0, "CR!G131"),
        ("SHUTTER_BUTTON_MOTOR", "MOT2", 1.0 if button else 0.0, "CR!G132"),
        ("SHUTTER_GUIDE_INVITATION_PAIR", "373128", 1.0, "CR!G133"),
        ("SHUTTER_FIRST_SLAT_COUPLING", "375678", 2.0 * panel_count, "CR!G134"),
        ("SHUTTER_FRONT_PIN", "375415", pulley_qty, "CR!G135"),
        ("SHUTTER_OPENING_LIMITER", "375441", 2.0 * panel_count, "CR!G136"),
    ]
    for role, code, quantity, source in unit_lines:
        if quantity > 0:
            bom.append(_unit_component(
                "PERSIANA", role, MATERIALS[code], quantity, cfg.quantity, source
            ))

    if independent:
        warnings.append(EngineeringWarning(
            "LEGACY-SHUTTER-INDEPENDENT-SHAFT",
            "O Excel corta meia largura, mas registra 1 eixo e seleciona também o "
            "divisor de eixo único por erro de digitação. A Engine usa 2 eixos e "
            "somente o divisor de eixos independentes.",
        ))
    if slat_qty != (cfg.height_mm / p["shutter_slat_height_mm"]) * panel_count:
        warnings.append(EngineeringWarning(
            "LEGACY-SHUTTER-SLAT-FRACTION",
            "A quantidade física de talas foi arredondada para cima; o Excel "
            "mantém altura/40 como quantidade fracionária.",
        ))


def _calculate_sliding_base(cfg: SlidingConfiguration) -> CalculationResult:
    """CR Engine 0.5.

    Escopo desta versão:
    - perfis principais, tela simples, baguetes e acabamentos;
    - reforços metálicos básicos;
    - vidro;
    - borrachas/escovas;
    - acessórios básicos;
    - ferragens de correr;
    - composição de custos por categoria e kit completo de persiana.

    Esta função mantém o núcleo simples previamente homologado. A composição
    dinâmica de travessas, bandeiras e painéis de vidro é aplicada pelo
    ``calculate_sliding`` público.
    """
    _validate(cfg)
    warnings: list[EngineeringWarning] = []
    p = PARAMETERS

    if cfg.shutter_enabled and cfg.shutter is None:
        warnings.append(EngineeringWarning(
            "V0.2-SHUTTER-PARTIAL",
            "Entrada legada shutter_enabled: a altura útil mantém o desconto "
            "de 200 mm sem inferir um modo de acionamento. Envie shutter para o kit completo."
        ))

    frame_code = _select_frame(cfg)
    leaf_code = _select_leaf(cfg)
    interlock_code = _select_interlock(cfg)
    frame = MATERIALS[frame_code]
    leaf = MATERIALS[leaf_code]

    frame_dim = float(frame.dim_a_mm or 0.0)
    leaf_dim = float(leaf.dim_a_mm or 0.0)
    glazing_rebate = float(leaf.dim_b_mm or 0.0)
    overlap = (
        p["design_overlap_mm"]
        if cfg.leaf_system == LeafSystem.DESIGN_DOOR_60x111
        else p["prime_overlap_mm"]
    )

    # CR!D8/D9: o marco principal perde bandeiras e reserva da persiana.
    frame_width_final = cfg.width_mm
    bottom_height = (
        float(cfg.bottom_fixed_panel.height_mm)
        if cfg.bottom_fixed_panel is not None else 0.0
    )
    top_height = (
        float(cfg.top_fixed_panel.height_mm)
        if cfg.top_fixed_panel is not None else 0.0
    )
    frame_height_final = (
        cfg.height_mm
        - bottom_height
        - top_height
        - (p["shutter_box_height_mm"] if _has_shutter(cfg) else 0.0)
    )
    if frame_height_final <= 0:
        raise ValueError(
            "Altura útil do marco principal ficou inválida após os descontos "
            "de bandeiras/persiana."
        )

    frame_width_cut = frame_width_final + p["weld_allowance_mm"]
    frame_height_cut = frame_height_final + p["weld_allowance_mm"]

    leaf_width_final = _leaf_width(cfg, frame_dim, leaf_dim, warnings)
    leaf_height_final = frame_height_final - (2 * frame_dim - 2 * overlap)
    leaf_width_cut = leaf_width_final + p["weld_allowance_mm"]
    leaf_height_cut = leaf_height_final + p["weld_allowance_mm"]

    # Falha cedo com a mensagem técnica correta, antes de criar reforços/BOM.
    if (
        leaf_width_final - 2 * glazing_rebate - p["glass_clearance_mm"] <= 0
        or leaf_height_final - 2 * glazing_rebate - p["glass_clearance_mm"] <= 0
    ):
        raise ValueError("Dimensões de vidro ficaram inválidas.")

    frame_qty = _frame_profile_qty(cfg)
    leaf_profile_qty = float(2 * cfg.leaf_count)
    screen_leaf_profile_qty = _screen_profile_piece_qty(cfg)

    bom: list[BomComponent] = []

    # PERFIS PRINCIPAIS
    bom.extend([
        _linear_component("PERFIS PRINCIPAIS", "FRAME_HORIZONTAL", frame_code,
                          frame_width_cut, frame_qty, cfg.quantity),
        _linear_component("PERFIS PRINCIPAIS", "FRAME_VERTICAL", frame_code,
                          frame_height_cut, frame_qty, cfg.quantity),
        _linear_component("PERFIS PRINCIPAIS", "LEAF_HORIZONTAL", leaf_code,
                          leaf_width_cut, leaf_profile_qty, cfg.quantity),
        _linear_component("PERFIS PRINCIPAIS", "LEAF_VERTICAL", leaf_code,
                          leaf_height_cut, leaf_profile_qty, cfg.quantity),
    ])

    if cfg.screen_enabled:
        # CR!12/13: folha adicional da tela usa o mesmo perfil de folha.
        bom.extend([
            _linear_component("TELA", "SCREEN_LEAF_HORIZONTAL", leaf_code,
                              leaf_width_cut, screen_leaf_profile_qty, cfg.quantity),
            _linear_component("TELA", "SCREEN_LEAF_VERTICAL", leaf_code,
                              leaf_height_cut, screen_leaf_profile_qty, cfg.quantity),
        ])

    interlock_length = leaf_height_final - p["interlock_clearance_mm"]
    iq = float(_interlock_qty(cfg))
    bom.append(_linear_component(
        "PERFIS PRINCIPAIS", "INTERLOCK", interlock_code,
        interlock_length, iq, cfg.quantity
    ))

    if cfg.leaf_system == LeafSystem.DESIGN_DOOR_60x111:
        bom.append(_linear_component(
            "PERFIS PRINCIPAIS", "LEAF_COVER", "DE5013",
            interlock_length, iq, cfg.quantity
        ))

    if cfg.leaf_count in {4, 6}:
        bom.append(_linear_component(
            "PERFIS PRINCIPAIS", "CENTRAL_CLOSURE", "AC4222",
            leaf_height_final, 1.0, cfg.quantity
        ))

    rail_code = "AL19" if frame_code == "DE16652" else "AL16"
    rail_length = cfg.width_mm - 2 * 52.0
    rail_qty = 2.0 if frame_code == "PR8852" else 3.0
    bom.append(_linear_component(
        "PERFIS PRINCIPAIS", "ALUMINUM_RAIL", rail_code,
        rail_length, rail_qty, cfg.quantity
    ))

    if frame_code == "DE16652":
        # CR!35/36.
        bom.append(_linear_component(
            "PERFIS PRINCIPAIS", "DESIGN_Z_PROFILE", "AL18",
            cfg.width_mm, 1.0, cfg.quantity
        ))
        bom.append(_linear_component(
            "PERFIS PRINCIPAIS", "DESIGN_Z_TRIM", "AL17",
            cfg.width_mm, 1.0, cfg.quantity
        ))

    # BAGUETES
    glass = GLASSES[normalize(cfg.glass_description)]
    baguette_code = _select_baguette(cfg, glass.thickness_mm)
    baguette_width = leaf_width_final - 2 * glazing_rebate
    baguette_height = leaf_height_final - 2 * glazing_rebate
    if baguette_width <= 0 or baguette_height <= 0:
        raise ValueError("Dimensões de baguete ficaram inválidas.")

    main_baguette_qty = leaf_profile_qty
    bom.extend([
        _linear_component("BAGUETES", "GLAZING_BEAD_HORIZONTAL", baguette_code,
                          baguette_width, main_baguette_qty, cfg.quantity),
        _linear_component("BAGUETES", "GLAZING_BEAD_VERTICAL", baguette_code,
                          baguette_height, main_baguette_qty, cfg.quantity),
    ])

    if cfg.screen_enabled:
        screen_baguette_qty = screen_leaf_profile_qty
        bom.extend([
            _linear_component("TELA", "SCREEN_BEAD_HORIZONTAL", "BA3218",
                              baguette_width, screen_baguette_qty, cfg.quantity),
            _linear_component("TELA", "SCREEN_BEAD_VERTICAL", "BA3218",
                              baguette_height, screen_baguette_qty, cfg.quantity),
        ])

    # ACABAMENTOS
    _add_finish(
        bom, cfg, cfg.internal_finish, "INTERNAL",
        p["internal_finish_extra_mm"]
    )
    _add_finish(
        bom, cfg, cfg.external_finish, "EXTERNAL",
        p["external_finish_extra_mm"]
    )

    # REFORÇOS
    frame_reinf = _select_frame_reinforcement(frame_code)
    leaf_reinf = _select_leaf_reinforcement(leaf_code)
    frame_reinf_width = frame_width_final - 2 * frame_dim
    frame_reinf_height = frame_height_final - 2 * frame_dim
    leaf_reinf_width = leaf_width_final - 2 * frame_dim
    leaf_reinf_height = leaf_height_final - 2 * frame_dim
    reinforced_leaf_piece_qty = leaf_profile_qty + screen_leaf_profile_qty

    bom.extend([
        _linear_component("REFORÇOS", "FRAME_REINFORCEMENT_HORIZONTAL", frame_reinf,
                          frame_reinf_width, frame_qty, cfg.quantity),
        _linear_component("REFORÇOS", "FRAME_REINFORCEMENT_VERTICAL", frame_reinf,
                          frame_reinf_height, frame_qty, cfg.quantity),
        _linear_component("REFORÇOS", "LEAF_REINFORCEMENT_HORIZONTAL", leaf_reinf,
                          leaf_reinf_width, reinforced_leaf_piece_qty, cfg.quantity),
        _linear_component("REFORÇOS", "LEAF_REINFORCEMENT_VERTICAL", leaf_reinf,
                          leaf_reinf_height, reinforced_leaf_piece_qty, cfg.quantity),
    ])

    # VIDRO
    glass_width = baguette_width - p["glass_clearance_mm"]
    glass_height = baguette_height - p["glass_clearance_mm"]
    if glass_width <= 0 or glass_height <= 0:
        raise ValueError("Dimensões de vidro ficaram inválidas.")
    glass_qty = main_baguette_qty / 2.0
    bom.append(_area_component(
        "VIDROS", "GLASS_PANEL", glass,
        glass_width, glass_height, glass_qty, cfg.quantity
    ))

    # TELA
    if cfg.screen_enabled:
        screen_qty = glass_qty / 2.0
        screen_mat = MATERIALS["TL1"]
        bom.append(_area_component(
            "TELA", "SCREEN_MESH", screen_mat,
            glass_width, glass_height, screen_qty, cfg.quantity
        ))

        screen_rubber_length_m = (
            2.0 * (baguette_width + baguette_height) * _screen_frame_count(cfg)
        ) / 1000.0
        bom.append(_linear_component(
            "VEDAÇÕES", "SCREEN_RUBBER", "TL2",
            screen_rubber_length_m * 1000.0, 1.0, cfg.quantity
        ))

    # BORRACHAS / ESCOVAS
    rubber_code = (
        "AC0708" if frame_code == "DE16652" else "ACB606"
    )
    brush_code = (
        "AC0710" if frame_code == "DE16652" else "ACE606"
    )

    rubber_length_mm = (
        baguette_width * main_baguette_qty
        + baguette_height * main_baguette_qty
    )
    bom.append(_linear_component(
        "VEDAÇÕES", "LEAF_RUBBER", rubber_code,
        rubber_length_mm, 1.0, cfg.quantity
    ))

    brush_length_mm = (
        leaf_width_cut * leaf_profile_qty * 2
        + leaf_height_cut * leaf_profile_qty * 2
        + leaf_width_cut * screen_leaf_profile_qty * 2
        + leaf_height_cut * screen_leaf_profile_qty * 2
    )
    bom.append(_linear_component(
        "VEDAÇÕES", "LEAF_BRUSH", brush_code,
        brush_length_mm, 1.0, cfg.quantity
    ))

    # ACESSÓRIOS
    wind_code = "AC0009" if frame_code == "DE16652" else "AC0012"
    wind_qty = (leaf_profile_qty - 2.0) + screen_leaf_profile_qty
    bom.append(_unit_component(
        "ACESSÓRIOS", "WIND_STOP", MATERIALS[wind_code],
        wind_qty, cfg.quantity
    ))

    glazing_block_qty = glass_qty * 2.0
    bom.append(_unit_component(
        "ACESSÓRIOS", "GLAZING_BLOCK", MATERIALS["AC0312"],
        glazing_block_qty, cfg.quantity
    ))

    drain_qty = frame_qty
    bom.append(_unit_component(
        "ACESSÓRIOS", "DRAIN_CAP", MATERIALS["AC0001"],
        drain_qty, cfg.quantity
    ))

    limiter_qty = leaf_profile_qty + screen_leaf_profile_qty
    bom.append(_unit_component(
        "ACESSÓRIOS", "OPENING_LIMITER", MATERIALS["375441"],
        limiter_qty, cfg.quantity
    ))

    # FERRAGENS
    closure = normalize(cfg.closure_mode)
    if closure == normalize("MAÇANETA COM CREMONA + FECHO OCULTO"):
        closure_code = 1
    elif closure == normalize("MAÇANETA COM CREMONA + MAÇANETA OCULTA COM CREMONA"):
        closure_code = 2
    elif closure == normalize("MAÇANETA COM CREMONA"):
        closure_code = 3
    else:
        raise ValueError(f"Fechamento não reconhecido: {cfg.closure_mode}")

    edge = "E:7,5mm" if cfg.leaf_system == LeafSystem.PRIME_WINDOW_42x66 else "E:15mm"
    cremona_desc = f"{cfg.cremona_base} {edge}"
    cremona = _hardware_lookup(cremona_desc, warnings)
    cremona_qty = 1.0 if closure_code == 1 else (2.0 if cfg.leaf_count < 4 else 3.0)
    if cremona is not None:
        bom.append(_unit_component(
            "FERRAGENS", "CREMONA", cremona, cremona_qty, cfg.quantity
        ))

    handle_qty = (2.0 if cfg.leaf_count < 4 else 3.0) if closure_code == 3 else 1.0
    bom.append(_unit_component(
        "FERRAGENS", "HANDLE_STANDARD", MATERIALS["MAC1"],
        handle_qty, cfg.quantity
    ))

    hidden_handle_qty = (
        (1.0 if cfg.leaf_count < 4 else 2.0) if closure_code == 2 else 0.0
    )
    if hidden_handle_qty:
        bom.append(_unit_component(
            "FERRAGENS", "HANDLE_HIDDEN", MATERIALS["MAC2"],
            hidden_handle_qty, cfg.quantity
        ))

    base_cremona = normalize(cfg.cremona_base)
    hidden_latch_code = None
    short_hidden_latches = {
        normalize(f"CREMONA 2 PONTOS COMP. {length}MM")
        for length in (400, 600, 800, 1000)
    }
    long_hidden_latches = {
        normalize(f"CREMONA 2 PONTOS COMP. {length}MM")
        for length in (1200, 1400, 1600, 1800)
    }
    if base_cremona == normalize("CREMONA 1 PONTO"):
        hidden_latch_code = "FEC1"
    elif base_cremona in short_hidden_latches:
        hidden_latch_code = "FEC2"
    elif base_cremona in long_hidden_latches:
        hidden_latch_code = "FEC3"

    hidden_latch_qty = (
        (1.0 if cfg.leaf_count < 4 else 2.0) if closure_code == 1 else 0.0
    )
    if hidden_latch_code and hidden_latch_qty:
        bom.append(_unit_component(
            "FERRAGENS", "HIDDEN_LATCH", MATERIALS[hidden_latch_code],
            hidden_latch_qty, cfg.quantity
        ))

    roller = _hardware_lookup(cfg.roller_description, warnings)
    roller_qty = leaf_profile_qty + screen_leaf_profile_qty
    if roller is not None:
        bom.append(_unit_component(
            "FERRAGENS", "ROLLERS", roller, roller_qty, cfg.quantity
        ))

    if base_cremona == normalize("CREMONA 1 PONTO"):
        counter_latch_qty = 2.0 if cfg.leaf_count < 4 else 3.0
    else:
        counter_latch_qty = 4.0 if cfg.leaf_count < 4 else 6.0
    bom.append(_unit_component(
        "FERRAGENS", "COUNTER_LATCH", MATERIALS["CON1"],
        counter_latch_qty, cfg.quantity
    ))

    # CR!G145. Sem bandeiras, as parcelas D37:D44 são zero.
    screw_reinf_qty = (
        (((frame_width_cut + frame_height_cut) / 1000.0) * frame_qty) * 4.0
        + (((leaf_width_cut + leaf_height_cut) / 1000.0)
           * (leaf_profile_qty + screen_leaf_profile_qty)) * 4.0
    )
    bom.append(_unit_component(
        "FERRAGENS", "REINFORCEMENT_SCREWS", MATERIALS["PAR2"],
        screw_reinf_qty, cfg.quantity
    ))

    screw_hw_qty = (roller_qty + hidden_latch_qty + cremona_qty) * 3.0
    bom.append(_unit_component(
        "FERRAGENS", "HARDWARE_SCREWS", MATERIALS["PAR1"],
        screw_hw_qty, cfg.quantity
    ))

    _add_shutter(bom, cfg, warnings)

    # Remove linhas de quantidade zero para tornar a BOM mais legível.
    bom = [x for x in bom if x.quantity_per_unit > 0 and x.cost_per_unit_product >= 0]

    breakdown: dict[str, float] = {}
    for component in bom:
        breakdown[component.category] = round(
            breakdown.get(component.category, 0.0) + component.cost_per_unit_product, 6
        )
    total = round(sum(x.cost_per_unit_product for x in bom), 6)
    breakdown["TOTAL"] = total

    description = f"{cfg.leaf_count} FOLHAS DE CORRER - {cfg.leaf_system.value}"
    geometry = {
        "frame_width_final_mm": round(frame_width_final, 6),
        "frame_height_final_mm": round(frame_height_final, 6),
        "frame_width_cut_mm": round(frame_width_cut, 6),
        "frame_height_cut_mm": round(frame_height_cut, 6),
        "leaf_width_final_mm": round(leaf_width_final, 6),
        "leaf_height_final_mm": round(leaf_height_final, 6),
        "leaf_width_cut_mm": round(leaf_width_cut, 6),
        "leaf_height_cut_mm": round(leaf_height_cut, 6),
        "baguette_width_mm": round(baguette_width, 6),
        "baguette_height_mm": round(baguette_height, 6),
        "glass_width_mm": round(glass_width, 6),
        "glass_height_mm": round(glass_height, 6),
    }
    if cfg.screen_enabled:
        geometry.update({
            "screen_panel_count": float(_screen_frame_count(cfg)),
            "screen_frame_count": float(_screen_frame_count(cfg)),
            "screen_mesh_area_m2": round(
                glass_width / 1000.0 * glass_height / 1000.0 * screen_qty,
                6,
            ),
        })
        if cfg.leaf_count == 3:
            warnings.append(EngineeringWarning(
                "LEGACY-SCREEN-3-LEAF-FRACTION",
                "CR!G69 usa 3/2 como fator de área da TL1. A Engine preserva "
                "esse consumo de malha, mas usa 2 quadros físicos inteiros.",
            ))

    return CalculationResult(
        model_description=description,
        geometry=geometry,
        unit_bom=bom,
        cost_breakdown=breakdown,
        unit_cost=total,
        warnings=warnings,
    )


_DYNAMIC_ROLES = {
    "GLAZING_BEAD_HORIZONTAL",
    "GLAZING_BEAD_VERTICAL",
    "SCREEN_BEAD_HORIZONTAL",
    "SCREEN_BEAD_VERTICAL",
    "GLASS_PANEL",
    "SCREEN_MESH",
    "SCREEN_RUBBER",
    "LEAF_RUBBER",
    "GLAZING_BLOCK",
    "DRAIN_CAP",
    "REINFORCEMENT_SCREWS",
}


def _append_opening_baguettes(
    bom: list[BomComponent],
    openings: tuple[GridOpening, ...],
    baguette_code: str,
    order_qty: int,
    role_prefix: str,
) -> None:
    for opening in openings:
        source = (
            f"{opening.source}:R{opening.row_index + 1}"
            f"C{opening.column_index + 1}"
        )
        bom.append(_linear_component(
            "BAGUETES",
            f"{role_prefix}_BEAD_HORIZONTAL",
            baguette_code,
            opening.width_mm,
            2.0 * opening.quantity,
            order_qty,
            source,
        ))
        bom.append(_linear_component(
            "BAGUETES",
            f"{role_prefix}_BEAD_VERTICAL",
            baguette_code,
            opening.height_mm,
            2.0 * opening.quantity,
            order_qty,
            source,
        ))


def _leaf_transoms(
    cfg: SlidingConfiguration,
    column_widths: tuple[float, ...],
    full_inner_height: float,
    material_code: str,
    reinforcement_code: str,
) -> list[Transom]:
    transoms: list[Transom] = []
    for column_index, width in enumerate(column_widths):
        if cfg.leaf_grid.horizontal_transoms:
            transoms.append(Transom(
                source=f"LEAF:C{column_index + 1}",
                orientation=TransomOrientation.HORIZONTAL,
                material_code=material_code,
                reinforcement_material_code=reinforcement_code,
                length_mm=round(float(width), 6),
                quantity=float(
                    cfg.leaf_grid.horizontal_transoms * cfg.leaf_count
                ),
            ))
    for transom_index in range(cfg.leaf_grid.vertical_transoms):
        transoms.append(Transom(
            source=f"LEAF:V{transom_index + 1}",
            orientation=TransomOrientation.VERTICAL,
            material_code=material_code,
            reinforcement_material_code=reinforcement_code,
            length_mm=round(float(full_inner_height), 6),
            quantity=float(cfg.leaf_count),
        ))
    return transoms


def _fixed_panel_transoms(panel: FixedPanelGeometry) -> list[Transom]:
    widths = tuple(
        opening.width_mm
        for opening in panel.openings
        if opening.row_index == 0
    )
    full_inner_height = panel.frame_height_mm - 2 * float(
        MATERIALS["DE6058"].dim_b_mm or 0.0
    )
    transoms: list[Transom] = []
    for column_index, width in enumerate(widths):
        if panel.horizontal_transoms:
            transoms.append(Transom(
                source=f"{panel.position.value}:C{column_index + 1}",
                orientation=TransomOrientation.HORIZONTAL,
                material_code="DE6072",
                reinforcement_material_code="RAG - DE6072",
                length_mm=round(float(width), 6),
                quantity=float(panel.horizontal_transoms),
            ))
    for transom_index in range(panel.vertical_transoms):
        transoms.append(Transom(
            source=f"{panel.position.value}:V{transom_index + 1}",
            orientation=TransomOrientation.VERTICAL,
            material_code="DE6072",
            reinforcement_material_code="RAG - DE6072",
            length_mm=round(float(full_inner_height), 6),
            quantity=1.0,
        ))
    return transoms


def calculate_sliding(cfg: SlidingConfiguration) -> CalculationResult:
    """Calculate a CR assembly with dynamic leaf and fixed-panel geometry."""

    result = _calculate_sliding_base(cfg)
    p = PARAMETERS
    glass = GLASSES[normalize(cfg.glass_description)]

    is_validated_simple_case = (
        cfg.leaf_grid.horizontal_transoms == 0
        and cfg.leaf_grid.vertical_transoms == 0
        and not cfg.leaf_grid.custom_dimensions
        and cfg.bottom_fixed_panel is None
        and cfg.top_fixed_panel is None
        and cfg.structural_reinforcement is None
    )
    if is_validated_simple_case:
        opening = GridOpening(
            source="LEAF",
            row_index=0,
            column_index=0,
            width_mm=result.geometry["baguette_width_mm"],
            height_mm=result.geometry["baguette_height_mm"],
            quantity=float(cfg.leaf_count),
        )
        panel = _glass_panel(opening, glass, p["glass_clearance_mm"])
        result.geometry.update({
            "leaf_grid_columns": 1.0,
            "leaf_grid_rows": 1.0,
            "leaf_glass_panel_count": float(cfg.leaf_count),
            "total_glass_panel_count": float(cfg.leaf_count),
        })
        result.leaf_openings = [opening]
        result.glass_panels = [panel]
        return result

    leaf_code = _select_leaf(cfg)
    leaf = MATERIALS[leaf_code]
    leaf_rebate = float(leaf.dim_b_mm or 0.0)
    leaf_inner_width = float(result.geometry["leaf_width_final_mm"]) - 2 * leaf_rebate
    leaf_inner_height = float(result.geometry["leaf_height_final_mm"]) - 2 * leaf_rebate
    transom_code, transom_reinforcement_code = _select_leaf_transom(cfg)
    transom_face = float(MATERIALS[transom_code].dim_b_mm or 0.0)

    column_widths = partition_axis(
        leaf_inner_width,
        cfg.leaf_grid.vertical_transoms,
        transom_face,
        cfg.leaf_grid.custom_dimensions,
        GridAxis.COLUMNS,
        "largura das folhas",
    )
    row_heights = partition_axis(
        leaf_inner_height,
        cfg.leaf_grid.horizontal_transoms,
        transom_face,
        cfg.leaf_grid.custom_dimensions,
        GridAxis.ROWS,
        "altura das folhas",
    )
    leaf_openings = make_openings(
        "LEAF",
        column_widths,
        row_heights,
        float(cfg.leaf_count),
    )

    fixed_panels = [
        panel
        for panel in (
            _fixed_panel_geometry(cfg, FixedPanelPosition.BOTTOM),
            _fixed_panel_geometry(cfg, FixedPanelPosition.TOP),
        )
        if panel is not None
    ]
    fixed_openings = tuple(
        opening
        for panel in fixed_panels
        for opening in panel.openings
    )

    transoms = _leaf_transoms(
        cfg,
        column_widths,
        leaf_inner_height,
        transom_code,
        transom_reinforcement_code,
    )
    for panel in fixed_panels:
        transoms.extend(_fixed_panel_transoms(panel))

    bom = [component for component in result.unit_bom if component.role not in _DYNAMIC_ROLES]
    leaf_baguette_code = _select_baguette(cfg, glass.thickness_mm)
    _append_opening_baguettes(
        bom,
        leaf_openings,
        leaf_baguette_code,
        cfg.quantity,
        "GLAZING",
    )

    if cfg.screen_enabled:
        screen_bead_qty = _screen_profile_piece_qty(cfg)
        for opening in leaf_openings:
            source = (
                f"SCREEN:R{opening.row_index + 1}"
                f"C{opening.column_index + 1}"
            )
            bom.append(_linear_component(
                "TELA", "SCREEN_BEAD_HORIZONTAL", "BA3218",
                opening.width_mm, screen_bead_qty, cfg.quantity, source,
            ))
            bom.append(_linear_component(
                "TELA", "SCREEN_BEAD_VERTICAL", "BA3218",
                opening.height_mm, screen_bead_qty, cfg.quantity, source,
            ))

    fixed_baguette_code = _select_fixed_panel_baguette(glass.thickness_mm)
    for panel in fixed_panels:
        prefix = f"{panel.position.value}_FIXED_GLAZING"
        _append_opening_baguettes(
            bom, panel.openings, fixed_baguette_code, cfg.quantity, prefix
        )

        frame_height_reinforcement = panel.frame_height_mm - 2 * float(
            MATERIALS["DE6058"].dim_a_mm or 0.0
        )
        frame_width_reinforcement = panel.width_mm - 2 * float(
            MATERIALS["DE6058"].dim_a_mm or 0.0
        )
        if frame_height_reinforcement <= 0 or frame_width_reinforcement <= 0:
            raise ValueError(
                f"Bandeira {panel.position.value} não comporta o reforço do marco."
            )
        bom.extend([
            _linear_component(
                "PERFIS PRINCIPAIS",
                f"{panel.position.value}_FIXED_FRAME_HORIZONTAL",
                "DE6058",
                panel.width_mm + p["weld_allowance_mm"],
                2.0,
                cfg.quantity,
                panel.position.value,
            ),
            _linear_component(
                "PERFIS PRINCIPAIS",
                f"{panel.position.value}_FIXED_FRAME_VERTICAL",
                "DE6058",
                panel.frame_height_mm + p["weld_allowance_mm"],
                2.0,
                cfg.quantity,
                panel.position.value,
            ),
            _linear_component(
                "REFORÇOS",
                f"{panel.position.value}_FIXED_FRAME_REINFORCEMENT_HORIZONTAL",
                "RAG - DE6058",
                frame_width_reinforcement,
                2.0,
                cfg.quantity,
                panel.position.value,
            ),
            _linear_component(
                "REFORÇOS",
                f"{panel.position.value}_FIXED_FRAME_REINFORCEMENT_VERTICAL",
                "RAG - DE6058",
                frame_height_reinforcement,
                2.0,
                cfg.quantity,
                panel.position.value,
            ),
        ])

    for transom in transoms:
        role_scope = "LEAF" if transom.source.startswith("LEAF") else "FIXED_PANEL"
        bom.append(_linear_component(
            "PERFIS PRINCIPAIS",
            f"{role_scope}_TRANSOM_{transom.orientation.value}",
            transom.material_code,
            transom.length_mm,
            transom.quantity,
            cfg.quantity,
            transom.source,
        ))
        bom.append(_linear_component(
            "REFORÇOS",
            f"{role_scope}_TRANSOM_REINFORCEMENT_{transom.orientation.value}",
            transom.reinforcement_material_code,
            transom.length_mm,
            transom.quantity,
            cfg.quantity,
            transom.source,
        ))

    if cfg.structural_reinforcement is not None and fixed_panels:
        bom.append(_linear_component(
            "REFORÇOS",
            "STRUCTURAL_REINFORCEMENT",
            cfg.structural_reinforcement.material_code,
            cfg.width_mm,
            float(len(fixed_panels)),
            cfg.quantity,
            "FIXED_PANELS",
        ))

    glass_panels = [
        _glass_panel(opening, glass, p["glass_clearance_mm"])
        for opening in (*leaf_openings, *fixed_openings)
    ]
    for panel in glass_panels:
        bom.append(_area_component(
            "VIDROS",
            "GLASS_PANEL",
            glass,
            panel.width_mm,
            panel.height_mm,
            panel.quantity,
            cfg.quantity,
            f"{panel.source}:{panel.position}",
        ))

    if cfg.screen_enabled:
        screen_material = MATERIALS["TL1"]
        for panel in glass_panels:
            if panel.source != "LEAF":
                continue
            bom.append(_area_component(
                "TELA",
                "SCREEN_MESH",
                screen_material,
                panel.width_mm,
                panel.height_mm,
                panel.quantity / 2.0,
                cfg.quantity,
                f"SCREEN:{panel.position}",
            ))

    frame_code = _select_frame(cfg)
    rubber_code = "AC0708" if frame_code == "DE16652" else "ACB606"
    leaf_rubber_length = sum(
        2.0 * (opening.width_mm + opening.height_mm) * opening.quantity
        for opening in leaf_openings
    )
    bom.append(_linear_component(
        "VEDAÇÕES", "LEAF_RUBBER", rubber_code,
        leaf_rubber_length, 1.0, cfg.quantity, "LEAF_GRID",
    ))
    if fixed_openings:
        fixed_rubber_length = sum(
            2.0 * (opening.width_mm + opening.height_mm) * opening.quantity
            for opening in fixed_openings
        )
        bom.append(_linear_component(
            "VEDAÇÕES", "FIXED_PANEL_RUBBER", "AC0708",
            fixed_rubber_length, 1.0, cfg.quantity, "FIXED_PANELS",
        ))
    if cfg.screen_enabled:
        screen_rubber_length = sum(
            2.0 * (opening.width_mm + opening.height_mm) * _screen_frame_count(cfg)
            for opening in leaf_openings
        )
        bom.append(_linear_component(
            "VEDAÇÕES", "SCREEN_RUBBER", "TL2",
            screen_rubber_length, 1.0, cfg.quantity, "SCREEN_GRID",
        ))

    total_glass_panel_count = sum(panel.quantity for panel in glass_panels)
    bom.append(_unit_component(
        "ACESSÓRIOS", "GLAZING_BLOCK", MATERIALS["AC0312"],
        total_glass_panel_count * 2.0, cfg.quantity, "ALL_GLASS_PANELS",
    ))
    bom.append(_unit_component(
        "ACESSÓRIOS", "DRAIN_CAP", MATERIALS["AC0001"],
        _frame_profile_qty(cfg) + 2.0 * len(fixed_panels),
        cfg.quantity,
        "MAIN_AND_FIXED_FRAMES",
    ))

    frame_qty = _frame_profile_qty(cfg)
    leaf_profile_qty = float(2 * cfg.leaf_count)
    screen_leaf_profile_qty = _screen_profile_piece_qty(cfg)
    fastener_rate = p["reinforcement_fastener_rate_per_meter"]
    screw_reinforcement_qty = (
        (
            (result.geometry["frame_width_cut_mm"] + result.geometry["frame_height_cut_mm"])
            / 1000.0 * frame_qty
        ) * fastener_rate
        + (
            (result.geometry["leaf_width_cut_mm"] + result.geometry["leaf_height_cut_mm"])
            / 1000.0 * (leaf_profile_qty + screen_leaf_profile_qty)
        ) * fastener_rate
        + sum(
            ((panel.width_mm + panel.frame_height_mm) / 1000.0 * 2.0)
            * fastener_rate
            for panel in fixed_panels
        )
    )
    bom.append(_unit_component(
        "FERRAGENS", "REINFORCEMENT_SCREWS", MATERIALS["PAR2"],
        screw_reinforcement_qty, cfg.quantity, "REINFORCED_FRAMES_AND_LEAVES",
    ))

    bom = [
        component
        for component in bom
        if component.quantity_per_unit > 0 and component.cost_per_unit_product >= 0
    ]
    breakdown: dict[str, float] = {}
    for component in bom:
        breakdown[component.category] = round(
            breakdown.get(component.category, 0.0)
            + component.cost_per_unit_product,
            6,
        )
    total = round(sum(component.cost_per_unit_product for component in bom), 6)
    breakdown["TOTAL"] = total

    first_leaf_opening = leaf_openings[0]
    first_glass = next(panel for panel in glass_panels if panel.source == "LEAF")
    result.geometry.update({
        "baguette_width_mm": first_leaf_opening.width_mm,
        "baguette_height_mm": first_leaf_opening.height_mm,
        "glass_width_mm": first_glass.width_mm,
        "glass_height_mm": first_glass.height_mm,
        "leaf_grid_columns": float(len(column_widths)),
        "leaf_grid_rows": float(len(row_heights)),
        "leaf_glass_panel_count": round(
            sum(opening.quantity for opening in leaf_openings), 6
        ),
        "fixed_glass_panel_count": round(
            sum(opening.quantity for opening in fixed_openings), 6
        ),
        "total_glass_panel_count": round(total_glass_panel_count, 6),
    })
    if cfg.screen_enabled:
        result.geometry.update({
            "screen_panel_count": float(_screen_frame_count(cfg)),
            "screen_frame_count": float(_screen_frame_count(cfg)),
            "screen_mesh_area_m2": round(sum(
                panel.area_m2 * panel.quantity / 2.0
                for panel in glass_panels
                if panel.source == "LEAF"
            ), 6),
        })
    if cfg.bottom_fixed_panel is not None:
        result.geometry["bottom_fixed_panel_height_mm"] = round(
            cfg.bottom_fixed_panel.height_mm, 6
        )
    if cfg.top_fixed_panel is not None:
        result.geometry["top_fixed_panel_height_mm"] = round(
            cfg.top_fixed_panel.height_mm, 6
        )
    result.unit_bom = bom
    result.cost_breakdown = breakdown
    result.unit_cost = total
    result.leaf_openings = list(leaf_openings)
    result.transoms = transoms
    result.fixed_panels = fixed_panels
    result.glass_panels = glass_panels
    return result
