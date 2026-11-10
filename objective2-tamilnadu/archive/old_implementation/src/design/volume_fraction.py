"""
src/design/volume_fraction.py
================================
Conversion between the SEARCHED variable (pcm_volume_fraction) and the
DERIVED one (n_capsule), per design_bounds_shared.yaml v3.0.

Only the SEARCH SPACE is reparameterized. DesignVector and
check_design()/compute_geometry() are deliberately left exactly as they
were -- they still take an integer capsule count, and all of their
validated overlap / passage / pressure logic is untouched. Samplers call
design_from_fraction() to turn a sampled fraction into the design vector
the rest of the pipeline already understands.

Rounding: n_capsule must be an integer, so a requested fraction is
generally not hit exactly. The ACHIEVED fraction is always recomputed and
reported alongside the requested one (achieved_fraction()), and it is the
achieved value that is recorded in results and fed to surrogates -- never
the requested one, which would introduce a small systematic
misattribution between a design's label and its actual physics.
"""

import math

from src.design.schema import DesignVector
from src.io_utils import load_system_config


def capsule_volume_m3(capsule_diameter_m: float) -> float:
    return math.pi / 6.0 * capsule_diameter_m ** 3


def tank_volume_m3(system_config: dict = None) -> float:
    system_config = system_config or load_system_config()
    return system_config["tank"]["volume_L"] / 1000.0


def n_capsule_for_fraction(pcm_volume_fraction: float, capsule_diameter_m: float,
                            system_config: dict = None) -> int:
    """Capsule count whose total volume is closest to the requested
    fraction of the tank. Floors at 1 (a 'fraction so small it rounds to
    zero capsules' request is a degenerate design, not a plain tank -- the
    plain-tank baseline is requested explicitly with pcm_name=None)."""
    v_cap = capsule_volume_m3(capsule_diameter_m)
    if v_cap <= 0:
        return 1
    return max(1, int(round(pcm_volume_fraction * tank_volume_m3(system_config) / v_cap)))


def achieved_fraction(n_capsule: int, capsule_diameter_m: float,
                       system_config: dict = None) -> float:
    """The fraction a given integer count actually realizes."""
    return n_capsule * capsule_volume_m3(capsule_diameter_m) / tank_volume_m3(system_config)


def design_from_fraction(pcm_volume_fraction: float, capsule_diameter_m: float,
                          flow_rate_kg_s: float, capsule_arrangement: str,
                          system_config: dict = None) -> DesignVector:
    n = n_capsule_for_fraction(pcm_volume_fraction, capsule_diameter_m, system_config)
    return DesignVector(capsule_diameter_m=capsule_diameter_m, n_capsule=n,
                         flow_rate_kg_s=flow_rate_kg_s,
                         capsule_arrangement=capsule_arrangement)
