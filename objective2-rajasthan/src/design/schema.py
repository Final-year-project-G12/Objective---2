"""
src/design/schema.py
=====================
The design vector Objective 2 searches over (D2.2 input). 40-hr scope:
sphere capsules only (design_bounds_shared.yaml). Arrangement was also
frozen (staggered-only) under that same scope cut but is restored as a
searched variable as of 2026-09-17 — see
docs/00_MASTER_CHANGE_PLAN.md / docs/01_PROMPT_PHASE1_CONFIG.md.

x = [capsule_diameter_m, n_capsule, flow_rate_kg_s, capsule_arrangement]

PCM thickness (conduction distance) and PCM volume fraction are DERIVED,
not independently sampled — see design_bounds_shared.yaml's note on why.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DesignVector:
    capsule_diameter_m: float
    n_capsule: int
    flow_rate_kg_s: float
    capsule_arrangement: str   # one of "single-layer", "staggered", "radial" —
                                # required, no default: every caller (DOE
                                # generator, optimizer search, manual CLI) must
                                # pass this explicitly so a staggered-only
                                # assumption can't silently creep back in.
    capsule_shape: str = "sphere"        # frozen for 40-hr scope

    def as_dict(self):
        return {
            "capsule_diameter_m": self.capsule_diameter_m,
            "n_capsule": self.n_capsule,
            "flow_rate_kg_s": self.flow_rate_kg_s,
            "capsule_shape": self.capsule_shape,
            "capsule_arrangement": self.capsule_arrangement,
        }
