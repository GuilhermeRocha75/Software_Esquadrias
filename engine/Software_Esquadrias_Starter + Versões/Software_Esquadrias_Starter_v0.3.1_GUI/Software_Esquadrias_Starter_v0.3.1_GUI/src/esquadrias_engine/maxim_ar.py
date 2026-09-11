from __future__ import annotations

import math

from .catalog import GLASSES, HARDWARE, MATERIALS, STRUCTURAL_REINFORCEMENT_CODES, normalize
from .cr_geometry import make_openings, partition_axis, validate_count
from .models import (
    BomComponent, CalculationResult, EngineeringWarning, FixedPanelGeometry,
    FixedPanelPosition, GlassPanel, GridAxis, GridOpening, MaximArConfiguration,
    MaximArLeafSystem, MaximArModuleMode, MaximArOrientation, Transom,
    TransomOrientation,
)


MAXIM_AR_ENGINE_VERSION = "MX_ENGINE_0.3.0"
MAXIM_AR_SUPPORTED_LEAF_COUNTS = tuple(range(1, 9))
MAXIM_AR_CLOSURE_OPTIONS = ("FECHO 1 PONTO", "MAÇANETA COM CREMONA")
MAXIM_AR_CREMONA_OPTIONS = (
    "CREMONA MAXIM-AR 2 PONTOS COMP. 300mm",
    "CREMONA MAXIM-AR 2 PONTOS COMP. 400mm",
    "CREMONA MAXIM-AR 2 PONTOS COMP. 600mm",
    "CREMONA MAXIM-AR 2 PONTOS COMP. 800mm",
)
MAXIM_AR_INTERNAL_FINISH_OPTIONS = ("GUARNIÇÃO DE 70MM",)
MAXIM_AR_EXTERNAL_FINISH_OPTIONS = ("BARRA CHATA DE 30MM",)

_GROUPS = (
    "PERFIS PRINCIPAIS", "BAGUETES", "ACABAMENTOS", "REFORÇOS",
    "VIDROS", "TELA", "VEDAÇÕES", "ACESSÓRIOS", "FERRAGENS",
)

_SYSTEMS = {
    MaximArLeafSystem.PRIME_WINDOW_42x63: {
        "label": "Prime 42x63", "frame": "PR4263", "leaf": "PR4263",
        "transom": "PR4263", "frame_face": 28.0, "frame_depth": 44.0,
        "leaf_face": 44.0, "transom_face": 28.0, "transom_depth": 14.0,
        "overlap": 6.0, "transom_recess": 6.0,
        "frame_reinforcement": "RAG - PR4263",
        "leaf_reinforcement": "RAG - PR4263",
        "transom_reinforcement": "RAG - PR4263",
    },
    MaximArLeafSystem.DESIGN_WINDOW_60x78: {
        "label": "Design 60x78", "frame": "DE6058", "leaf": "DE6078",
        "transom": "DE6072", "frame_face": 40.0, "frame_depth": 58.0,
        "leaf_face": 60.0, "transom_face": 36.0, "transom_depth": 18.0,
        "overlap": 8.0, "transom_recess": 12.0,
        "frame_reinforcement": "RAG - DE6058",
        "leaf_reinforcement": "RAG - DE6078",
        "transom_reinforcement": "RAG - DE6072",
    },
}


def _linear_component(category, role, material_code, length_mm, quantity_per_unit,
                      order_quantity, source):
    if not math.isfinite(length_mm) or length_mm <= 0:
        raise ValueError(f"Comprimento inválido para {role}: {length_mm:g} mm.")
    if not math.isfinite(quantity_per_unit) or quantity_per_unit <= 0:
        raise ValueError(f"Quantidade inválida para {role}: {quantity_per_unit:g}.")
    material = MATERIALS[material_code]
    cost = length_mm / 1000.0 * quantity_per_unit * material.unit_price
    return BomComponent(
        category=category, role=role, material_code=material.code,
        description=material.description, unit="m", length_mm=round(length_mm, 6),
        width_mm=None, height_mm=None, area_m2=None,
        quantity_per_unit=float(quantity_per_unit),
        quantity_order=float(quantity_per_unit * order_quantity),
        unit_price=material.unit_price, cost_per_unit_product=round(cost, 6),
        source=source,
    )


def _configured_sealing_component(cfg, role, length_mm, order_quantity, source):
    sealing = cfg.sealing
    cost = length_mm / 1000.0 * sealing.unit_price_per_meter
    return BomComponent(
        category="VEDAÇÕES", role=role,
        material_code=sealing.internal_material_id,
        description=sealing.description, unit="m", length_mm=round(length_mm, 6),
        width_mm=None, height_mm=None, area_m2=None, quantity_per_unit=1.0,
        quantity_order=float(order_quantity), unit_price=sealing.unit_price_per_meter,
        cost_per_unit_product=round(cost, 6),
        source=source,
    )


def _unit_component(role, material, quantity_per_unit, order_quantity, source,
                    category="FERRAGENS"):
    if not math.isfinite(quantity_per_unit) or quantity_per_unit <= 0:
        raise ValueError(f"Quantidade inválida para {role}: {quantity_per_unit:g}.")
    return BomComponent(
        category=category, role=role, material_code=material.code,
        description=material.description, unit="un", length_mm=None,
        width_mm=None, height_mm=None, area_m2=None,
        quantity_per_unit=float(quantity_per_unit),
        quantity_order=float(quantity_per_unit * order_quantity),
        unit_price=material.unit_price,
        cost_per_unit_product=round(quantity_per_unit * material.unit_price, 6),
        source=source,
    )


def _glass_component(glass, opening, order_quantity):
    width = opening.width_mm - 8.0
    height = opening.height_mm - 8.0
    if width <= 0 or height <= 0:
        raise ValueError(
            f"Painel de vidro impossível em {opening.source}: {width:g}x{height:g} mm."
        )
    area = width / 1000.0 * height / 1000.0
    return BomComponent(
        category="VIDROS", role="GLASS_PANEL", material_code=glass.code,
        description=glass.description, unit="m²", length_mm=None,
        width_mm=round(width, 6), height_mm=round(height, 6),
        area_m2=round(area, 6), quantity_per_unit=float(opening.quantity),
        quantity_order=float(opening.quantity * order_quantity),
        unit_price=glass.unit_price,
        cost_per_unit_product=round(area * opening.quantity * glass.unit_price, 6),
        source=f"MX-VID-001 / {opening.source}",
    )


def _screen_component(width, height, order_quantity):
    material = MATERIALS["TL3"]
    price = width / 1000.0 * 110.0 + height / 1000.0 * 110.0 + 110.0
    return BomComponent(
        category="TELA", role="RETRACTABLE_SCREEN_ASSEMBLY",
        material_code=material.code, description=material.description, unit="un",
        length_mm=None, width_mm=round(width, 6), height_mm=round(height, 6),
        area_m2=None, quantity_per_unit=1.0, quantity_order=float(order_quantity),
        unit_price=round(price, 6), cost_per_unit_product=round(price, 6),
        source="MX-TEL-001 / MX!D64:L64 / LISTADIV!C5:C7",
    )


def _glass_and_bead(cfg, *, fixed=False):
    glass = GLASSES.get(normalize(cfg.glass_description))
    if glass is None or glass.code == "0" or glass.thickness_mm is None:
        raise ValueError(f"Vidro não suportado no Maxim-Ar: {cfg.glass_description}")
    thickness = float(glass.thickness_mm)
    system = MaximArLeafSystem.DESIGN_WINDOW_60x78 if fixed else cfg.leaf_system
    ranges = (
        ((8, "BA2516"), (12, "BA2018"), (16, "BA1816"), (17, "BA1216"),
         (24, "BA1016"), (25, "BA0716"))
        if system == MaximArLeafSystem.PRIME_WINDOW_42x63 else
        ((8, "BA3518"), (12, "BA3218"), (19, "BA2516"), (22, "BA2018"),
         (26, "BA1816"), (31, "BA1216"), (34, "BA1016"), (35, "BA0716"))
    )
    bead = next((code for upper, code in ranges if thickness < upper), None)
    if bead is None:
        raise ValueError(
            f"Espessura de vidro {thickness:g} mm sem baguete comprovada para {system.value}."
        )
    return glass, bead


def _hardware_by_description(description):
    material = HARDWARE.get(normalize(description))
    if material is None:
        raise ValueError(f"Ferragem Maxim-Ar não encontrada: {description}")
    return material


def _arm_material(system, leaf_height_mm):
    index = 0 if leaf_height_mm <= 500 else 1 if leaf_height_mm <= 600 else 2 if leaf_height_mm <= 800 else 3 if leaf_height_mm <= 1000 else 4
    box = 14 if system == MaximArLeafSystem.PRIME_WINDOW_42x63 else 16
    return _hardware_by_description(
        f"BRAÇO MAXIM-AR CX {box}mm DT{(10, 12, 16, 20, 24)[index]}"
    )


def _validate_configuration(cfg):
    if not math.isfinite(float(cfg.width_mm)) or not math.isfinite(float(cfg.height_mm)):
        raise ValueError("Largura e altura do Maxim-Ar devem ser finitas.")
    if cfg.width_mm <= 0 or cfg.height_mm <= 0:
        raise ValueError("Largura e altura do Maxim-Ar devem ser positivas.")
    if isinstance(cfg.quantity, bool) or not isinstance(cfg.quantity, int) or cfg.quantity < 1:
        raise ValueError("A quantidade do Maxim-Ar deve ser um inteiro maior ou igual a 1.")
    if isinstance(cfg.leaf_count, bool) or cfg.leaf_count not in MAXIM_AR_SUPPORTED_LEAF_COUNTS:
        raise ValueError("O Maxim-Ar comprovado em ORCS admite de 1 a 8 folhas.")
    if cfg.leaf_grid.horizontal_transoms or cfg.leaf_grid.vertical_transoms:
        raise ValueError(
            "Travessas AF/AG dentro da folha móvel são fisicamente inválidas no Maxim-Ar."
        )
    if cfg.leaf_grid.custom_dimensions:
        raise ValueError("Cotas personalizadas V:AE não possuem uso MX comprovado em ORCS.")
    if normalize(cfg.internal_finish) != normalize(MAXIM_AR_INTERNAL_FINISH_OPTIONS[0]):
        raise ValueError("Acabamento interno não comprovado no Maxim-Ar.")
    if normalize(cfg.external_finish) != normalize(MAXIM_AR_EXTERNAL_FINISH_OPTIONS[0]):
        raise ValueError("Acabamento externo não comprovado no Maxim-Ar.")
    if normalize(cfg.closure_mode) not in {normalize(x) for x in MAXIM_AR_CLOSURE_OPTIONS}:
        raise ValueError(f"Fechamento Maxim-Ar não suportado: {cfg.closure_mode}")
    panels = [p for p in (cfg.bottom_fixed_panel, cfg.top_fixed_panel) if p]
    for panel in panels:
        if not math.isfinite(float(panel.height_mm)) or panel.height_mm <= 0:
            raise ValueError("A altura de cada bandeira deve ser positiva e finita.")
        validate_count(panel.horizontal_transoms, "travessas horizontais da bandeira")
        validate_count(panel.vertical_transoms, "travessas verticais da bandeira")
    if cfg.module_mode == MaximArModuleMode.SEPARATE and not panels:
        raise ValueError("MÓDULOS SEPARADOS exige ao menos uma bandeira.")
    if cfg.module_mode == MaximArModuleMode.SEPARATE and any(
        panel.horizontal_transoms or panel.vertical_transoms for panel in panels
    ):
        raise ValueError(
            "Módulos separados com travessas internas são fisicamente inválidos."
        )
    if sum(panel.height_mm for panel in panels) >= cfg.height_mm:
        raise ValueError("As bandeiras não podem consumir toda a altura do conjunto.")
    if cfg.structural_reinforcement:
        code = cfg.structural_reinforcement.material_code
        if code not in STRUCTURAL_REINFORCEMENT_CODES:
            raise ValueError(f"Reforço estrutural Maxim-Ar não suportado: {code}")
        if cfg.module_mode != MaximArModuleMode.SEPARATE:
            raise ValueError("Reforço estrutural é permitido somente em módulos separados.")
    sealing = cfg.sealing
    if not sealing.internal_material_id.strip() or not sealing.description.strip():
        raise ValueError("A vedação configurável exige identificador interno e descrição.")
    if not math.isfinite(sealing.unit_price_per_meter) or sealing.unit_price_per_meter < 0:
        raise ValueError("O preço por metro da vedação deve ser finito e não negativo.")


def _fixed_panel_geometry(cfg, position, props):
    panel_cfg = cfg.bottom_fixed_panel if position == FixedPanelPosition.BOTTOM else cfg.top_fixed_panel
    if panel_cfg is None:
        return None
    separate = cfg.module_mode == MaximArModuleMode.SEPARATE
    clearance = 50.0 if separate and cfg.structural_reinforcement and cfg.structural_reinforcement.material_code == "ALUM10238" else 0.0
    frame_height = float(panel_cfg.height_mm) - clearance
    frame_face = float(props["frame_face"])
    transom_face = float(props["transom_face"])
    transom_depth = float(props["transom_depth"])
    # Em módulos separados, MX!D24/D30 retira também o rebaixo PFAB!B18.
    # Esse detalhe é comprovado nos casos ORCS de uma folha (por exemplo 990).
    inner_width = float(cfg.width_mm) - 2 * frame_face - (float(props["transom_recess"]) if separate else 0.0)
    inner_height = frame_height - 2 * frame_face if separate else frame_height - frame_face - transom_depth
    widths = partition_axis(inner_width, panel_cfg.vertical_transoms, transom_face, (), GridAxis.COLUMNS, f"largura da bandeira {position.value}")
    heights = partition_axis(inner_height, panel_cfg.horizontal_transoms, transom_face, (), GridAxis.ROWS, f"altura da bandeira {position.value}")
    return FixedPanelGeometry(
        position=position, width_mm=float(cfg.width_mm),
        nominal_height_mm=float(panel_cfg.height_mm), frame_height_mm=frame_height,
        horizontal_transoms=panel_cfg.horizontal_transoms,
        vertical_transoms=panel_cfg.vertical_transoms,
        openings=make_openings(position.value, widths, heights, 1.0),
    )


def _glass_panel(component, opening, glass):
    return GlassPanel(
        source=opening.source,
        position=f"R{opening.row_index + 1}C{opening.column_index + 1}",
        width_mm=component.width_mm or 0.0, height_mm=component.height_mm or 0.0,
        quantity=opening.quantity, material_code=glass.code,
        material_description=glass.description, area_m2=component.area_m2 or 0.0,
        unit_cost=glass.unit_price, total_cost=component.cost_per_unit_product,
    )


def calculate_maxim_ar(cfg):
    """Calcula o recorte MX comprovado e bloqueia ramos legados não físicos."""
    _validate_configuration(cfg)
    props = _SYSTEMS[cfg.leaf_system]
    glass, bead_code = _glass_and_bead(cfg)
    _, fixed_bead_code = _glass_and_bead(cfg, fixed=True)
    width, height, count = float(cfg.width_mm), float(cfg.height_mm), cfg.leaf_count
    frame_face, frame_depth = float(props["frame_face"]), float(props["frame_depth"])
    leaf_face = float(props["leaf_face"])
    transom_face, transom_depth = float(props["transom_face"]), float(props["transom_depth"])
    overlap, recess = float(props["overlap"]), float(props["transom_recess"])
    bottom_height = cfg.bottom_fixed_panel.height_mm if cfg.bottom_fixed_panel else 0.0
    top_height = cfg.top_fixed_panel.height_mm if cfg.top_fixed_panel else 0.0
    separate = cfg.module_mode == MaximArModuleMode.SEPARATE
    frame_height = height - bottom_height - top_height if separate else height

    if cfg.orientation == MaximArOrientation.HORIZONTAL:
        leaf_width = (width - 2 * frame_face - (count - 1) * transom_face) / count + 2 * overlap
        if separate or not (bottom_height or top_height):
            leaf_height = frame_height - 2 * frame_face + 2 * overlap
        elif bottom_height and top_height:
            leaf_height = frame_height - bottom_height - top_height - 2 * transom_depth + 2 * overlap
        else:
            leaf_height = frame_height - bottom_height - top_height - frame_face - transom_depth + 2 * overlap
    else:
        leaf_width = width - 2 * frame_face + 2 * overlap
        leaf_height = (frame_height - 2 * frame_face - (count - 1) * transom_face) / count + 2 * overlap

    bead_width, bead_height = leaf_width - 2 * leaf_face, leaf_height - 2 * leaf_face
    dimensions = {
        "main_frame_height_mm": frame_height, "leaf_width_final_mm": leaf_width,
        "leaf_height_final_mm": leaf_height, "baguette_width_mm": bead_width,
        "baguette_height_mm": bead_height, "glass_width_mm": bead_width - 8,
        "glass_height_mm": bead_height - 8,
        "frame_reinforcement_width_mm": width - 2 * frame_depth,
        "frame_reinforcement_height_mm": frame_height - 2 * frame_depth,
    }
    invalid = [(name, value) for name, value in dimensions.items() if value <= 0]
    if invalid:
        name, value = invalid[0]
        raise ValueError(f"Dimensão tecnicamente impossível para Maxim-Ar: {name}={value:g} mm.")

    quantity, weld = cfg.quantity, 5.0
    frame_code, leaf_code = str(props["frame"]), str(props["leaf"])
    transom_code = str(props["transom"])
    frame_reinforcement = str(props["frame_reinforcement"])
    leaf_reinforcement = str(props["leaf_reinforcement"])
    transom_reinforcement = str(props["transom_reinforcement"])
    frame_width_cut, frame_height_cut = width + weld, frame_height + weld
    leaf_width_cut, leaf_height_cut = leaf_width + weld, leaf_height + weld
    bom = [
        _linear_component("PERFIS PRINCIPAIS", "FRAME_HORIZONTAL", frame_code, frame_width_cut, 2, quantity, "MX-GEO-001 / MX!E8:G8"),
        _linear_component("PERFIS PRINCIPAIS", "FRAME_VERTICAL", frame_code, frame_height_cut, 2, quantity, "MX-GEO-001 / MX!E9:G9"),
        _linear_component("PERFIS PRINCIPAIS", "LEAF_HORIZONTAL", leaf_code, leaf_width_cut, 2 * count, quantity, "MX-GEO-002 / MX!E10:G10"),
        _linear_component("PERFIS PRINCIPAIS", "LEAF_VERTICAL", leaf_code, leaf_height_cut, 2 * count, quantity, "MX-GEO-002 / MX!E11:G11"),
    ]
    transoms = []
    if count > 1:
        if cfg.orientation == MaximArOrientation.HORIZONTAL:
            orientation, length, source = TransomOrientation.VERTICAL, frame_height - 2 * frame_face + recess, "MX-GEO-004 / MX!D15:G15"
        else:
            orientation, length, source = TransomOrientation.HORIZONTAL, width - 2 * frame_face + recess, "MX-GEO-004 / MX!D14:G14"
        transoms.append(Transom("LEAF_SEPARATOR", orientation, transom_code, transom_reinforcement, round(length, 6), float(count - 1)))
        bom.append(_linear_component("PERFIS PRINCIPAIS", f"LEAF_SEPARATOR_{orientation.value}", transom_code, length, count - 1, quantity, source))

    leaf_opening = GridOpening("LEAF", 0, 0, round(bead_width, 6), round(bead_height, 6), float(count))
    leaf_openings = [leaf_opening]
    bom.extend([
        _linear_component("BAGUETES", "GLAZING_BEAD_HORIZONTAL", bead_code, bead_width, 2 * count, quantity, "MX-GEO-003 / MX!D12:G12"),
        _linear_component("BAGUETES", "GLAZING_BEAD_VERTICAL", bead_code, bead_height, 2 * count, quantity, "MX-GEO-003 / MX!D13:G13"),
    ])
    fixed_panels = [p for p in (
        _fixed_panel_geometry(cfg, FixedPanelPosition.BOTTOM, props),
        _fixed_panel_geometry(cfg, FixedPanelPosition.TOP, props),
    ) if p]
    fixed_openings = [opening for panel in fixed_panels for opening in panel.openings]
    for panel in fixed_panels:
        prefix = panel.position.value
        if separate:
            base_row = 20 if prefix == "BOTTOM" else 26
            bom.extend([
                _linear_component("PERFIS PRINCIPAIS", f"{prefix}_FRAME_HORIZONTAL", frame_code, width + weld, 2, quantity, f"MX!E{base_row}:G{base_row}"),
                _linear_component("PERFIS PRINCIPAIS", f"{prefix}_FRAME_VERTICAL", frame_code, panel.frame_height_mm + weld, 2, quantity, f"MX!E{base_row + 1}:G{base_row + 1}"),
            ])
        else:
            panel_cfg = cfg.bottom_fixed_panel if panel.position == FixedPanelPosition.BOTTOM else cfg.top_fixed_panel
            inner_width = sum(o.width_mm for o in panel.openings if o.row_index == 0) + panel_cfg.vertical_transoms * transom_face
            inner_height = sum(o.height_mm for o in panel.openings if o.column_index == 0) + panel_cfg.horizontal_transoms * transom_face
            boundary_length = inner_width + recess
            boundary = Transom(f"{prefix}_BOUNDARY", TransomOrientation.HORIZONTAL, transom_code, transom_reinforcement, round(boundary_length, 6), 1.0)
            transoms.append(boundary)
            bom.append(_linear_component("PERFIS PRINCIPAIS", f"{prefix}_BOUNDARY_TRANSOM_HORIZONTAL", transom_code, boundary_length, 1, quantity, "MX-GEO-005 / MX!D14:G14"))
            if panel_cfg.horizontal_transoms:
                divider = Transom(f"{prefix}_FIXED_DIVIDER", TransomOrientation.HORIZONTAL, transom_code, transom_reinforcement, round(boundary_length, 6), float(panel_cfg.horizontal_transoms))
                transoms.append(divider)
                bom.append(_linear_component("PERFIS PRINCIPAIS", f"{prefix}_FIXED_DIVIDER_HORIZONTAL", transom_code, boundary_length, panel_cfg.horizontal_transoms, quantity, "MX-GEO-006 / RESOLVED_PHYSICAL_TOPOLOGY"))
            if panel_cfg.vertical_transoms:
                vertical_length = inner_height + recess
                divider = Transom(f"{prefix}_FIXED_DIVIDER", TransomOrientation.VERTICAL, transom_code, transom_reinforcement, round(vertical_length, 6), float(panel_cfg.vertical_transoms))
                transoms.append(divider)
                bom.append(_linear_component("PERFIS PRINCIPAIS", f"{prefix}_FIXED_DIVIDER_VERTICAL", transom_code, vertical_length, panel_cfg.vertical_transoms, quantity, "MX-GEO-006 / RESOLVED_PHYSICAL_TOPOLOGY"))
        for opening in panel.openings:
            position = f"{prefix}:R{opening.row_index + 1}C{opening.column_index + 1}"
            bom.extend([
                _linear_component("BAGUETES", f"{prefix}_BEAD_HORIZONTAL", fixed_bead_code, opening.width_mm, 2 * opening.quantity, quantity, position),
                _linear_component("BAGUETES", f"{prefix}_BEAD_VERTICAL", fixed_bead_code, opening.height_mm, 2 * opening.quantity, quantity, position),
            ])

    bom.extend([
        _linear_component("ACABAMENTOS", "INTERNAL_FINISH_HORIZONTAL", "AC7012", width + 140, 2, quantity, "MX-ACA-001 / MX!D33:G33"),
        _linear_component("ACABAMENTOS", "INTERNAL_FINISH_VERTICAL", "AC7012", height + 140, 2, quantity, "MX-ACA-001 / MX!D34:G34"),
        _linear_component("ACABAMENTOS", "EXTERNAL_FINISH_HORIZONTAL", "AC3004", width + 60, 2, quantity, "MX-ACA-002 / MX!D35:G35"),
        _linear_component("ACABAMENTOS", "EXTERNAL_FINISH_VERTICAL", "AC3004", height + 60, 2, quantity, "MX-ACA-002 / MX!D36:G36"),
        _linear_component("REFORÇOS", "FRAME_REINFORCEMENT_HORIZONTAL", frame_reinforcement, width - 2 * frame_depth, 2, quantity, "MX-REF-001 / MX!D42:G42"),
        _linear_component("REFORÇOS", "FRAME_REINFORCEMENT_VERTICAL", frame_reinforcement, frame_height - 2 * frame_depth, 2, quantity, "MX-REF-001 / MX!D43:G43"),
        _linear_component("REFORÇOS", "LEAF_REINFORCEMENT_HORIZONTAL", leaf_reinforcement, bead_width, 2 * count, quantity, "MX-REF-002 / MX!D44:G44"),
        _linear_component("REFORÇOS", "LEAF_REINFORCEMENT_VERTICAL", leaf_reinforcement, bead_height, 2 * count, quantity, "MX-REF-002 / MX!D45:G45"),
    ])
    for transom in transoms:
        bom.append(_linear_component("REFORÇOS", f"{transom.source}_TRANSOM_REINFORCEMENT_{transom.orientation.value}", transom.reinforcement_material_code, transom.length_mm, transom.quantity, quantity, transom.source))
    if separate:
        for panel in fixed_panels:
            prefix = panel.position.value
            bom.extend([
                _linear_component("REFORÇOS", f"{prefix}_FRAME_REINFORCEMENT_HORIZONTAL", frame_reinforcement, width - 2 * frame_depth, 2, quantity, "MX-REF-003 / MX!I48:I55"),
                _linear_component("REFORÇOS", f"{prefix}_FRAME_REINFORCEMENT_VERTICAL", frame_reinforcement, panel.frame_height_mm - 2 * frame_depth, 2, quantity, "MX-REF-003 / MX!I48:I55"),
            ])
    if cfg.structural_reinforcement:
        bom.append(_linear_component("REFORÇOS", "STRUCTURAL_REINFORCEMENT", cfg.structural_reinforcement.material_code, width, len(fixed_panels), quantity, "MX-REF-004 / MX!D32:G32"))

    all_openings = [*leaf_openings, *fixed_openings]
    glass_components = [_glass_component(glass, opening, quantity) for opening in all_openings]
    bom.extend(glass_components)
    if cfg.screen_enabled:
        bom.append(_screen_component(width, frame_height, quantity))

    glass_sealing_length = sum(2 * (o.width_mm + o.height_mm) * o.quantity for o in all_openings)
    leaf_perimeter = 2 * count * (leaf_width + leaf_height)
    bom.extend([
        _configured_sealing_component(cfg, "GLASS_SEATING_SEAL", glass_sealing_length, quantity, "MX-VED-001 / RESOLVED_PHYSICAL"),
        _configured_sealing_component(cfg, "LEAF_EXTERNAL_SEAL", leaf_perimeter, quantity, "MX-VED-002 / RESOLVED_PHYSICAL"),
        _configured_sealing_component(cfg, "FRAME_CONTACT_SEAL", leaf_perimeter, quantity, "MX-VED-003 / RESOLVED_PHYSICAL"),
    ])
    warnings = []
    if cfg.sealing.unit_price_per_meter == 0:
        warnings.append(EngineeringWarning("MX-SEALING-PRICE-NOT-CONFIGURED", "A vedação física foi calculada, mas o preço configurado é zero."))
    if cfg.orientation == MaximArOrientation.VERTICAL and cfg.leaf_system == MaximArLeafSystem.PRIME_WINDOW_42x63:
        warnings.append(EngineeringWarning("LEGACY-MX-PRIME-VERTICAL-DESIGN-OVERLAP-CORRECTED", "MX!D10 usa PFAB!B17=8 mm; a Engine usa o transpasse PRIME PFAB!B5=6 mm, com delta intencional contra o Excel."))
    if separate:
        warnings.extend([
            EngineeringWarning("LEGACY-MX-SEPARATE-REINFORCEMENT-SUBTOTAL-CORRECTED", "MX!I56 soma apenas I42:I47 e omite os reforços físicos I48:I55; a Engine os inclui."),
            EngineeringWarning("LEGACY-MX-SEPARATE-SCREWS-CORRECTED", "MX!G80 ignora os quadros separados; a Engine aplica a mesma taxa comprovada de 4 parafusos/m."),
        ])
    if cfg.structural_reinforcement:
        warnings.append(EngineeringWarning("MX-STRUCTURAL-REINFORCEMENT-NO-HISTORICAL-ORCS", "A fórmula MX!D32:G32 e o catálogo comprovam o item, mas ORCS não contém nenhum caso MX preenchido com reforço estrutural."))

    bom.extend([
        _unit_component("GLAZING_BLOCK", MATERIALS["AC0312"], 4 * sum(o.quantity for o in all_openings), quantity, "MX-ACE-001 / RESOLVED_PHYSICAL", "ACESSÓRIOS"),
        _unit_component("DRAIN_CAP", MATERIALS["AC0001"], 2, quantity, "MX-ACE-002 / MX!G73:I73", "ACESSÓRIOS"),
    ])
    bom.append(_unit_component("MAXIM_AR_ARM", _arm_material(cfg.leaf_system, leaf_height), count, quantity, "MX-FER-001 / MX!B76:I76"))
    if normalize(cfg.closure_mode) == normalize("FECHO 1 PONTO"):
        if cfg.cremona_description:
            raise ValueError("FECHO 1 PONTO não utiliza cremona no XLSM.")
        bom.append(_unit_component("MAXIM_AR_LATCH", _hardware_by_description("FECHO MAXIM-AR 1 PONTO"), count, quantity, "MX-FER-002 / MX!B77:I77"))
        hardware_screws = 10.0 * count
    else:
        if cfg.cremona_description is None or normalize(cfg.cremona_description) not in {normalize(x) for x in MAXIM_AR_CREMONA_OPTIONS}:
            raise ValueError("MAÇANETA COM CREMONA exige uma cremona Maxim-Ar exata.")
        bom.extend([
            _unit_component("MAXIM_AR_HANDLE", _hardware_by_description("MAÇANETA ESTREITA MAXIM-AR"), count, quantity, "MX-FER-003 / MX!B77:I77"),
            _unit_component("CREMONA", _hardware_by_description(cfg.cremona_description), count, quantity, "MX-FER-004 / MX!B78:I78"),
            _unit_component("COUNTER_LATCH", _hardware_by_description("CONTRA FECHO STANDARD"), 2 * count, quantity, "MX-FER-005 / MX!B79:I79"),
        ])
        hardware_screws = 16.0 * count
    principal_length_m = sum((item.length_mm or 0) / 1000 * item.quantity_per_unit for item in bom if item.category == "PERFIS PRINCIPAIS")
    bom.extend([
        _unit_component("REINFORCEMENT_SCREWS", MATERIALS["PAR2"], principal_length_m * 4, quantity, "MX-FER-006 / MX!G80:I80"),
        _unit_component("HARDWARE_SCREWS", MATERIALS["PAR1"], hardware_screws, quantity, "MX-FER-007 / MX!G81:I81"),
    ])
    breakdown = {
        group: round(sum(x.cost_per_unit_product for x in bom if x.category == group), 6)
        for group in _GROUPS if group != "TELA" or cfg.screen_enabled
    }
    total = round(sum(breakdown.values()), 6)
    breakdown["TOTAL"] = total
    glass_panels = [_glass_panel(component, opening, glass) for component, opening in zip(glass_components, all_openings)]
    geometry = {
        "frame_width_final_mm": round(width, 6), "frame_height_final_mm": round(frame_height, 6),
        "frame_width_cut_mm": round(frame_width_cut, 6), "frame_height_cut_mm": round(frame_height_cut, 6),
        "leaf_width_final_mm": round(leaf_width, 6), "leaf_height_final_mm": round(leaf_height, 6),
        "leaf_width_cut_mm": round(leaf_width_cut, 6), "leaf_height_cut_mm": round(leaf_height_cut, 6),
        "baguette_width_mm": round(bead_width, 6), "baguette_height_mm": round(bead_height, 6),
        "glass_width_mm": round(bead_width - 8, 6), "glass_height_mm": round(bead_height - 8, 6),
    }
    if count != 1 or fixed_panels or cfg.screen_enabled:
        geometry.update({
            "leaf_count": float(count), "leaf_glass_panel_count": float(count),
            "total_glass_panel_count": float(sum(o.quantity for o in all_openings)),
        })
    if fixed_panels:
        geometry["fixed_glass_panel_count"] = float(sum(o.quantity for o in fixed_openings))
    if cfg.screen_enabled:
        geometry["screen_panel_count"] = 1.0
    if cfg.bottom_fixed_panel:
        geometry["bottom_fixed_panel_height_mm"] = round(cfg.bottom_fixed_panel.height_mm, 6)
    if cfg.top_fixed_panel:
        geometry["top_fixed_panel_height_mm"] = round(cfg.top_fixed_panel.height_mm, 6)
    return CalculationResult(
        model_description=f"JANELA {count} {'FOLHA' if count == 1 else 'FOLHAS'} MAXIM-AR ({props['label']}, {cfg.orientation.value})",
        geometry=geometry, unit_bom=bom, cost_breakdown=breakdown, unit_cost=total,
        leaf_openings=leaf_openings, transoms=transoms, fixed_panels=fixed_panels,
        glass_panels=glass_panels, warnings=warnings,
        calculation_version=MAXIM_AR_ENGINE_VERSION,
    )
