"""
src/design/schema.py
=====================
The design vector Objective 2 searches over (D2.2 input).

x = [capsule_diameter_m, n_capsule, flow_rate_kg_s, capsule_arrangement]

Capsule shape stays frozen to sphere (never named in the objective
statement). Capsule arrangement was previously ALSO frozen (staggered
only, a "40-hr scope cut") but that contradicted the objective statement,
which names "capsule arrangement" as one of the four things Objective 2
must determine. Restored 2026-09-17 as a required, explicitly-passed
categorical field -- see design_bounds_shared.yaml and
docs_objective2/17_ARRANGEMENT_RESTORATION.md (adapted from
"a Rajasthan-pilot change plan (source removed from this project after adaptation, see docs_objective2/tamilnadu_phase_docs/)" for Tamil
Nadu). `capsule_arrangement` intentionally has NO default here: every
caller (DOE generator, optimizer search, CLI) must now pass it explicitly,
so an implicit staggered-only assumption can never silently creep back in
downstream. A call site that doesn't pass it is a bug to fix at that call
site, not something to paper over with a dataclass default.

PCM thickness (conduction distance) and PCM volume fraction are DERIVED,
not independently sampled — see design_bounds_shared.yaml's note on why.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DesignVector:
    capsule_diameter_m: float
    n_capsule: int
    flow_rate_kg_s: float
    capsule_arrangement: str            # "single-layer" | "staggered" | "radial" -- required, no default
    capsule_shape: str = "sphere"        # frozen: never named in the objective statement

    def as_dict(self):
        return {
            "capsule_diameter_m": self.capsule_diameter_m,
            "n_capsule": self.n_capsule,
            "flow_rate_kg_s": self.flow_rate_kg_s,
            "capsule_shape": self.capsule_shape,
            "capsule_arrangement": self.capsule_arrangement,
        }
