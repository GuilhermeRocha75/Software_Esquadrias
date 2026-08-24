import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import (
    LeafSystem, ApplicationType, SlidingConfiguration,
    calculate_sliding, build_order_purchase_plan
)

configs = [
    SlidingConfiguration(
        width_mm=3500, height_mm=2000, quantity=1, leaf_count=2,
        leaf_system=LeafSystem.PRIME_WINDOW_42x66,
        application=ApplicationType.WINDOW,
        glass_description="04mm FLOAT INCOLOR",
        closure_mode="MAÇANETA COM CREMONA + FECHO OCULTO",
        cremona_base="CREMONA 1 PONTO",
        roller_description="ROLDANA 30KG",
        internal_finish="GUARNIÇÃO DE 70MM",
        external_finish="BARRA CHATA DE 30MM",
    ),
    SlidingConfiguration(
        width_mm=2000, height_mm=2000, quantity=1, leaf_count=2,
        leaf_system=LeafSystem.DESIGN_DOOR_60x111,
        application=ApplicationType.WINDOW,
        glass_description="04mm FLOAT INCOLOR",
        closure_mode="MAÇANETA COM CREMONA + FECHO OCULTO",
        cremona_base="CREMONA 1 PONTO",
        roller_description="ROLDANA 30KG",
        internal_finish="GUARNIÇÃO DE 70MM",
        external_finish="BARRA CHATA DE 30MM",
    ),
    SlidingConfiguration(
        width_mm=1500, height_mm=3000, quantity=1, leaf_count=2,
        leaf_system=LeafSystem.PRIME_WINDOW_42x66,
        application=ApplicationType.WINDOW,
        glass_description="05mm FLOAT FUMÊ",
        closure_mode="MAÇANETA COM CREMONA",
        cremona_base="CREMONA 1 PONTO",
        roller_description="ROLDANA 50KG",
        internal_finish="GUARNIÇÃO DE 70MM",
        external_finish="BARRA CHATA DE 30MM",
    ),
    SlidingConfiguration(
        width_mm=2000, height_mm=2000, quantity=1, leaf_count=2,
        leaf_system=LeafSystem.DESIGN_DOOR_60x111,
        application=ApplicationType.WINDOW,
        glass_description="04mm FLOAT INCOLOR",
        closure_mode="MAÇANETA COM CREMONA + FECHO OCULTO",
        cremona_base="CREMONA 1 PONTO",
        roller_description="ROLDANA 30KG",
        internal_finish="GUARNIÇÃO DE 70MM",
        external_finish="BARRA CHATA DE 30MM",
    ),
]

order = [(cfg, calculate_sliding(cfg)) for cfg in configs]
plan = build_order_purchase_plan(order)

print("Custos técnicos dos itens:")
for i, (cfg, result) in enumerate(order, 1):
    print(i, cfg.width_mm, "x", cfg.height_mm, "=>", round(result.unit_cost * cfg.quantity, 5))

print("\nCompra de barras:")
for line in plan.lines:
    print(
        line.material_code,
        "cortes=", line.pieces_count,
        "barras=", line.bars_required,
        "consumo_m=", round(line.consumed_length_mm/1000, 3),
        "compra_R$=", round(line.purchase_cost, 3),
    )

print("\nTOTAL consumo técnico:", plan.technical_total)
print("TOTAL compra de barras:", plan.bar_stock_purchase_cost)
print("TOTAL compra estimada:", plan.procurement_total_estimate)
print("Alertas:", [w.code for w in plan.warnings])
