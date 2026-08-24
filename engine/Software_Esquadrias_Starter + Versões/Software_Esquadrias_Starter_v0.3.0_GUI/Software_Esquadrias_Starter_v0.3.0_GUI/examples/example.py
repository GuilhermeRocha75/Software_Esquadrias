import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from esquadrias_engine import LeafSystem, SlidingConfiguration, calculate_sliding

cfg = SlidingConfiguration(
    width_mm=2000,
    height_mm=2000,
    quantity=1,
    leaf_count=2,
    leaf_system=LeafSystem.PRIME_DOOR_42x88,
    glass_description="04mm FLOAT INCOLOR",
    closure_mode="MAÇANETA COM CREMONA + FECHO OCULTO",
    cremona_base="CREMONA 1 PONTO",
    roller_description="ROLDANA 30KG",
    internal_finish="GUARNIÇÃO DE 70MM",
    external_finish="BARRA CHATA DE 30MM",
)

result = calculate_sliding(cfg)

print(result.model_description)
print(result.geometry)
print("\nCUSTOS POR GRUPO")
for group, value in result.cost_breakdown.items():
    print(f"{group}: R$ {value:.2f}")

print("\nBOM")
for component in result.unit_bom:
    print(component)

print(f"\nCusto total da Engine: R$ {result.unit_cost:.2f}")
print("Alertas:", result.warnings)
