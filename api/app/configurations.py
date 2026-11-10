"""Shared request-to-Engine conversion; contains no engineering calculations."""
from __future__ import annotations

from .engine_bridge import (
    ApplicationType, CustomDimension, FixedPanelConfiguration, GridAxis,
    LeafGrid, LeafSystem, SlidingConfiguration, ShutterConfiguration, ShutterMode,
    StructuralReinforcement, MaximArConfiguration, MaximArLeafSystem,
    MaximArOrientation, MaximArModuleMode, MaximArSealingConfiguration,
    GrConfiguration, FixoConfiguration,
)
from .schemas import CRItemRequest, MaximArItemRequest, GrItemRequest, FixoItemRequest


def _to_config(item: CRItemRequest) -> SlidingConfiguration:
    return SlidingConfiguration(
        width_mm=item.width_mm,
        height_mm=item.height_mm,
        quantity=item.quantity,
        leaf_count=item.leaf_count,
        leaf_system=LeafSystem(item.leaf_system),
        application=ApplicationType(item.application),
        glass_description=item.glass_description,
        closure_mode=item.closure_mode,
        cremona_base=item.cremona_base,
        roller_description=item.roller_description,
        internal_finish=item.internal_finish,
        external_finish=item.external_finish,
        screen_enabled=item.screen_enabled,
        shutter_enabled=item.shutter_enabled,
        shutter=(
            ShutterConfiguration(
                mode=ShutterMode(item.shutter.mode),
                box_description=item.shutter.box_description,
                slat_description=item.shutter.slat_description,
            )
            if item.shutter is not None else None
        ),
        leaf_grid=LeafGrid(
            horizontal_transoms=item.leaf_grid.horizontal_transoms,
            vertical_transoms=item.leaf_grid.vertical_transoms,
            custom_dimensions=tuple(
                CustomDimension(
                    axis=GridAxis(dimension.axis),
                    index=dimension.index,
                    clear_span_mm=dimension.clear_span_mm,
                )
                for dimension in item.leaf_grid.custom_dimensions
            ),
        ),
        bottom_fixed_panel=(
            FixedPanelConfiguration(**item.bottom_fixed_panel.model_dump())
            if item.bottom_fixed_panel is not None else None
        ),
        top_fixed_panel=(
            FixedPanelConfiguration(**item.top_fixed_panel.model_dump())
            if item.top_fixed_panel is not None else None
        ),
        structural_reinforcement=(
            StructuralReinforcement(item.structural_reinforcement.material_code)
            if item.structural_reinforcement is not None else None
        ),
    )


def _to_maxim_ar_config(item: MaximArItemRequest) -> MaximArConfiguration:
    return MaximArConfiguration(
        width_mm=item.width_mm,
        height_mm=item.height_mm,
        quantity=item.quantity,
        leaf_count=item.leaf_count,
        leaf_system=MaximArLeafSystem(item.leaf_system),
        orientation=MaximArOrientation(item.orientation),
        module_mode=MaximArModuleMode(item.module_mode),
        glass_description=item.glass_description,
        closure_mode=item.closure_mode,
        cremona_description=item.cremona_description,
        internal_finish=item.internal_finish,
        external_finish=item.external_finish,
        screen_enabled=item.screen_enabled,
        leaf_grid=LeafGrid(
            horizontal_transoms=item.leaf_grid.horizontal_transoms,
            vertical_transoms=item.leaf_grid.vertical_transoms,
            custom_dimensions=tuple(
                CustomDimension(
                    axis=GridAxis(dimension.axis),
                    index=dimension.index,
                    clear_span_mm=dimension.clear_span_mm,
                )
                for dimension in item.leaf_grid.custom_dimensions
            ),
        ),
        bottom_fixed_panel=(
            FixedPanelConfiguration(**item.bottom_fixed_panel.model_dump())
            if item.bottom_fixed_panel is not None else None
        ),
        top_fixed_panel=(
            FixedPanelConfiguration(**item.top_fixed_panel.model_dump())
            if item.top_fixed_panel is not None else None
        ),
        structural_reinforcement=(
            StructuralReinforcement(item.structural_reinforcement.material_code)
            if item.structural_reinforcement is not None else None
        ),
        sealing=MaximArSealingConfiguration(**item.sealing.model_dump()),
    )


def _to_gr_config(item: GrItemRequest) -> GrConfiguration:
    return GrConfiguration(
        width_mm=item.width_mm,
        height_mm=item.height_mm,
        quantity=item.quantity,
        leaf_count=item.leaf_count,
        leaf_system=item.leaf_system,
        application=item.application,
        panel_mode=item.panel_mode,
        glass_description=item.glass_description,
        custom_glass_code=item.custom_glass_code,
        custom_glass_unit_price=item.custom_glass_unit_price,
        custom_glass_thickness_mm=item.custom_glass_thickness_mm,
        mixed_split_from_bottom_mm=item.mixed_split_from_bottom_mm,
        module_mode=item.module_mode,
        closure_mode=item.closure_mode,
        cremona_description=item.cremona_description,
        hinge_description=item.hinge_description,
        window_lock_length_mm=item.window_lock_length_mm,
        shutter=(
            ShutterConfiguration(
                mode=ShutterMode(item.shutter.mode),
                box_description=item.shutter.box_description,
                slat_description=item.shutter.slat_description,
            )
            if item.shutter is not None else None
        ),
        screen_enabled=item.screen_enabled,
        top_flag_height_mm=item.top_flag_height_mm,
        bottom_flag_height_mm=item.bottom_flag_height_mm,
        bottom_flag_vertical_transoms=item.bottom_flag_vertical_transoms,
        bottom_flag_horizontal_transoms=item.bottom_flag_horizontal_transoms,
        top_flag_vertical_transoms=item.top_flag_vertical_transoms,
        top_flag_horizontal_transoms=item.top_flag_horizontal_transoms,
        internal_finish=item.internal_finish,
        external_finish=item.external_finish,
    )


def _to_fixo_config(item: FixoItemRequest) -> FixoConfiguration:
    return FixoConfiguration(**item.model_dump(exclude={"family"}))
