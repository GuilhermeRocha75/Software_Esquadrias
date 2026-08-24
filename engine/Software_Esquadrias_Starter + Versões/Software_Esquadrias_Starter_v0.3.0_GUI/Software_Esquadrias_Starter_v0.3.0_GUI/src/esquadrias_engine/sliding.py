from __future__ import annotations

from .models import (
    LeafSystem, ApplicationType, SlidingConfiguration, CalculationResult, BomComponent, EngineeringWarning
)
from .catalog import (
    MATERIALS, PARAMETERS, GLASSES, HARDWARE, FINISH_OPTIONS,
    normalize
)

SUPPORTED_LEAF_COUNTS = {2, 3, 4, 6}


def _linear_component(category: str, role: str, material_code: str, length_mm: float,
                      qty_unit: float, order_qty: int) -> BomComponent:
    material = MATERIALS[material_code]
    length_mm = max(0.0, float(length_mm))
    qty_unit = max(0.0, float(qty_unit))
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
    )


def _unit_component(category: str, role: str, material, qty_unit: float,
                    order_qty: int) -> BomComponent:
    qty_unit = max(0.0, float(qty_unit))
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
    )


def _area_component(category: str, role: str, material, width_mm: float,
                    height_mm: float, qty_unit: float, order_qty: int) -> BomComponent:
    width_mm = max(0.0, float(width_mm))
    height_mm = max(0.0, float(height_mm))
    qty_unit = max(0.0, float(qty_unit))
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
    )


def _validate(cfg: SlidingConfiguration) -> None:
    if cfg.width_mm <= 0 or cfg.height_mm <= 0:
        raise ValueError("Largura e altura devem ser positivas.")
    if cfg.quantity <= 0:
        raise ValueError("Quantidade deve ser inteira e positiva.")
    if cfg.leaf_count not in SUPPORTED_LEAF_COUNTS:
        raise ValueError("Número de folhas suportado: 2, 3, 4 ou 6.")
    if normalize(cfg.glass_description) not in GLASSES:
        raise ValueError(f"Vidro não encontrado no catálogo: {cfg.glass_description}")
    if normalize(cfg.internal_finish) not in {normalize(x) for x in FINISH_OPTIONS}:
        raise ValueError(f"Acabamento interno inválido: {cfg.internal_finish}")
    if normalize(cfg.external_finish) not in {normalize(x) for x in FINISH_OPTIONS}:
        raise ValueError(f"Acabamento externo inválido: {cfg.external_finish}")


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


def calculate_sliding(cfg: SlidingConfiguration) -> CalculationResult:
    """CR Engine 0.3.

    Escopo desta versão:
    - perfis principais, tela simples, baguetes e acabamentos;
    - reforços metálicos básicos;
    - vidro;
    - borrachas/escovas;
    - acessórios básicos;
    - ferragens de correr;
    - composição de custos por categoria.

    Travessas, bandeiras e o kit completo de persiana ainda serão tratados
    em versões posteriores.
    """
    _validate(cfg)
    warnings: list[EngineeringWarning] = []
    p = PARAMETERS

    if cfg.shutter_enabled:
        warnings.append(EngineeringWarning(
            "V0.2-SHUTTER-PARTIAL",
            "A altura útil desconta 200 mm como no Excel, mas o kit de persiana ainda não está no BOM."
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

    # CR!D8/D9. Nesta versão ainda sem bandeira inferior/superior.
    frame_width_final = cfg.width_mm
    frame_height_final = cfg.height_mm - (
        p["shutter_box_height_mm"] if cfg.shutter_enabled else 0.0
    )
    if frame_height_final <= 0:
        raise ValueError("Altura útil ficou inválida após o desconto da persiana.")

    frame_width_cut = frame_width_final + p["weld_allowance_mm"]
    frame_height_cut = frame_height_final + p["weld_allowance_mm"]

    leaf_width_final = _leaf_width(cfg, frame_dim, leaf_dim, warnings)
    leaf_height_final = frame_height_final - (2 * frame_dim - 2 * overlap)
    leaf_width_cut = leaf_width_final + p["weld_allowance_mm"]
    leaf_height_cut = leaf_height_final + p["weld_allowance_mm"]

    frame_qty = _frame_profile_qty(cfg)
    leaf_profile_qty = float(2 * cfg.leaf_count)
    screen_leaf_profile_qty = float(cfg.leaf_count) if cfg.screen_enabled else 0.0

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
        screen_baguette_qty = main_baguette_qty / 2.0
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
            (baguette_width * (main_baguette_qty / 2.0))
            + (baguette_height * (main_baguette_qty / 2.0))
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
    if base_cremona == normalize("CREMONA 1 PONTO"):
        hidden_latch_code = "FEC1"
    elif any(x in base_cremona for x in ("400MM", "600MM", "800MM", "1000MM")):
        hidden_latch_code = "FEC2"
    elif any(x in base_cremona for x in ("1200MM", "1400MM", "1600MM", "1800MM")):
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

    return CalculationResult(
        model_description=description,
        geometry=geometry,
        unit_bom=bom,
        cost_breakdown=breakdown,
        unit_cost=total,
        warnings=warnings,
    )
