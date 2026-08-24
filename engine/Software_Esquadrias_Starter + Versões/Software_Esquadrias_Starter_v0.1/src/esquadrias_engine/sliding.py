from .models import LeafSystem, SlidingConfiguration, CalculationResult, BomComponent, EngineeringWarning
from .catalog import MATERIALS, PARAMETERS

SUPPORTED_LEAF_COUNTS = {2, 3, 4, 6}


def _linear_component(role: str, material_code: str, length_mm: float, qty_unit: float, order_qty: int) -> BomComponent:
    material = MATERIALS[material_code]
    cost = (length_mm / 1000.0) * qty_unit * material.unit_price
    return BomComponent(
        role=role,
        material_code=material.code,
        description=material.description,
        unit="m",
        length_mm=round(length_mm, 6),
        quantity_per_unit=qty_unit,
        quantity_order=qty_unit * order_qty,
        unit_price=material.unit_price,
        cost_per_unit_product=round(cost, 6),
    )


def _validate(cfg: SlidingConfiguration) -> None:
    if cfg.width_mm <= 0 or cfg.height_mm <= 0:
        raise ValueError("width_mm e height_mm devem ser positivos")
    if cfg.quantity <= 0:
        raise ValueError("quantity deve ser inteiro positivo")
    if cfg.leaf_count not in SUPPORTED_LEAF_COUNTS:
        raise ValueError("leaf_count suportado nesta família: 2, 3, 4 ou 6")


def _select_frame(cfg: SlidingConfiguration) -> str:
    # RF-CR-009. A v0.1 suporta o recorte sem tela no BOM, mas mantém a seleção legada.
    if cfg.leaf_system == LeafSystem.DESIGN_DOOR_60x111:
        return "DE16652"
    if cfg.leaf_count in {3, 6} or cfg.screen_enabled:
        return "PR13852"
    return "PR8852"


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


def _interlock_qty(cfg: SlidingConfiguration) -> int:
    # RF-CR-023
    if cfg.leaf_count == 2:
        return 3 if cfg.screen_enabled else 2
    if cfg.leaf_count == 3:
        return 4
    if cfg.leaf_count == 4:
        return 6 if cfg.screen_enabled else 4
    if cfg.leaf_count == 6:
        return 12
    raise AssertionError("leaf_count validado anteriormente")


def _leaf_width(cfg: SlidingConfiguration, frame_dim_mm: float, leaf_dim_mm: float, warnings: list[EngineeringWarning]) -> float:
    n = cfg.leaf_count
    p = PARAMETERS

    # Modo de compatibilidade com D10 do Excel. As referências suspeitas são sinalizadas.
    if cfg.leaf_system == LeafSystem.DESIGN_DOOR_60x111:
        overlap = p["prime_overlap_mm"]  # legado: D10 usa PFAB B3 em vez de B4
        warnings.append(EngineeringWarning(
            "DT-CR-003",
            "Compatibilidade Excel: largura da folha DESIGN usa o transpasse PRIME (PFAB B3). Validar antes da v1.0."
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
    return (cfg.width_mm - central - 2*frame_dim_mm + 2*overlap + overlap_count*leaf_dim_mm) / n


def calculate_sliding(cfg: SlidingConfiguration) -> CalculationResult:
    """Primeiro recorte executável do motor CR.

    Escopo v0.1:
      - marco principal
      - folhas
      - interlock
      - fechamento central 4/6 folhas
      - trilho de alumínio
      - tapa-folha DESIGN
      - custo linear desses componentes

    Ainda NÃO calcula tela, vidro, baguete, persiana, bandeiras, travessas, reforços,
    vedações e ferragens completas. Esses itens entram nas versões v0.2/v0.3.
    """
    _validate(cfg)
    warnings: list[EngineeringWarning] = []
    if cfg.screen_enabled:
        warnings.append(EngineeringWarning(
            "V0.1-SCREEN-PARTIAL",
            "A seleção do marco/interlock considera tela, mas o BOM específico da tela ainda não é calculado."
        ))
    if cfg.shutter_enabled:
        warnings.append(EngineeringWarning(
            "V0.1-SHUTTER-NOT-IMPLEMENTED",
            "Persiana ainda não faz parte do BOM v0.1; altura útil permanece sem o desconto de 200 mm."
        ))

    frame_code = _select_frame(cfg)
    leaf_code = _select_leaf(cfg)
    interlock_code = _select_interlock(cfg)
    frame = MATERIALS[frame_code]
    leaf = MATERIALS[leaf_code]

    frame_dim = float(frame.dim_a_mm or 0)
    leaf_dim = float(leaf.dim_a_mm or 0)
    overlap = PARAMETERS["design_overlap_mm"] if cfg.leaf_system == LeafSystem.DESIGN_DOOR_60x111 else PARAMETERS["prime_overlap_mm"]

    frame_width_final = cfg.width_mm
    frame_height_final = cfg.height_mm
    frame_width_cut = frame_width_final + PARAMETERS["weld_allowance_mm"]
    frame_height_cut = frame_height_final + PARAMETERS["weld_allowance_mm"]

    leaf_width_final = _leaf_width(cfg, frame_dim, leaf_dim, warnings)
    leaf_height_final = frame_height_final - (2*frame_dim - 2*overlap)
    leaf_width_cut = leaf_width_final + PARAMETERS["weld_allowance_mm"]
    leaf_height_cut = leaf_height_final + PARAMETERS["weld_allowance_mm"]

    frame_qty = 2.0
    leaf_profile_qty = float(2 * cfg.leaf_count)  # G10/G11

    bom = [
        _linear_component("FRAME_HORIZONTAL", frame_code, frame_width_cut, frame_qty, cfg.quantity),
        _linear_component("FRAME_VERTICAL", frame_code, frame_height_cut, frame_qty, cfg.quantity),
        _linear_component("LEAF_HORIZONTAL", leaf_code, leaf_width_cut, leaf_profile_qty, cfg.quantity),
        _linear_component("LEAF_VERTICAL", leaf_code, leaf_height_cut, leaf_profile_qty, cfg.quantity),
    ]

    # Interlock: D32 = D11 - 10; G32 conforme topologia.
    interlock_length = leaf_height_final - PARAMETERS["interlock_clearance_mm"]
    iq = float(_interlock_qty(cfg))
    bom.append(_linear_component("INTERLOCK", interlock_code, interlock_length, iq, cfg.quantity))

    # DESIGN adiciona tapa-folha com mesmo comprimento/quantidade do interlock.
    if cfg.leaf_system == LeafSystem.DESIGN_DOOR_60x111:
        bom.append(_linear_component("LEAF_COVER", "DE5013", interlock_length, iq, cfg.quantity))

    # Fechamento central (AC4222): 4/6 folhas, uma peça linear com altura da folha.
    if cfg.leaf_count in {4, 6}:
        bom.append(_linear_component("CENTRAL_CLOSURE", "AC4222", leaf_height_final, 1.0, cfg.quantity))

    # Trilho de alumínio: D34 = largura - 2*52; 2 trilhos no marco PR8852, senão 3.
    rail_code = "AL19" if frame_code == "DE16652" else "AL16"
    rail_length = cfg.width_mm - 2*52.0
    rail_qty = 2.0 if frame_code == "PR8852" else 3.0
    bom.append(_linear_component("ALUMINUM_RAIL", rail_code, rail_length, rail_qty, cfg.quantity))

    profiles_cost = round(sum(x.cost_per_unit_product for x in bom), 6)
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
    }
    return CalculationResult(
        model_description=description,
        geometry=geometry,
        unit_bom=bom,
        cost_breakdown={"profiles_basic": profiles_cost, "total_implemented": profiles_cost},
        unit_cost=profiles_cost,
        warnings=warnings,
    )
