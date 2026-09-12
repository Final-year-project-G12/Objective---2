"""
src/design/schema.py
=====================
The design vector Objective 2 searches over (D2.2 input). 40-hr scope:
sphere capsules, staggered arrangement only (design_bounds_shared.yaml).

x = [capsule_diameter_m, n_capsule, flow_rate_kg_s]

PCM thickness (conduction distance) and PCM volume fraction are DERIVED,
not independently sampled — see design_bounds_shared.yaml's note on why.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DesignVector:
    capsule_diameter_m: float
    n_capsule: int
    flow_rate_kg_s: float
    capsule_shape: str = "sphere"        # frozen for 40-hr scope
    capsule_arrangement: str = "staggered"  # frozen for 40-hr scope

    def as_dict(self):
        return {
            "capsule_diameter_m": self.capsule_diameter_m,
            "n_capsule": self.n_capsule,
            "flow_rate_kg_s": self.flow_rate_kg_s,
            "capsule_shape": self.capsule_shape,
            "capsule_arrangement": self.capsule_arrangement,
        }
