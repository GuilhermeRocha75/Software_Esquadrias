import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from esquadrias_engine import LeafSystem, SlidingConfiguration, calculate_sliding

cfg = SlidingConfiguration(
    width_mm=1500,
    height_mm=1200,
    quantity=2,
    leaf_count=2,
    leaf_system=LeafSystem.PRIME_WINDOW_42x66,
)
result = calculate_sliding(cfg)
print(result.model_description)
print(result.geometry)
for item in result.unit_bom:
    print(item)
print("Custo implementado:", result.unit_cost)
print("Alertas:", result.warnings)
