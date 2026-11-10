"""
src/simulation/capsule_mass.py
=================================
Derived per-capsule quantities that distinguish the OUTER shell from the
PCM actually inside it. Ports two repairs from Manvitha's Rajasthan report
(her G2 and decision D3), which Tamil Nadu did not have:

  G2  "PCM mass from inner sphere (D - 2 t_wall); wall heat capacity
       carried in the PCM node."  Her measured effect: "Older
       outer-volume mass overstated PCM by 11.5 / 5.9 %."
  D3  "PCM conduction path uses inner radius and inner area
       (thickness = inner radius)."

WHY IT MATTERS. A capsule of outer diameter D with an 0.8 mm aluminium
wall does not contain D-worth of PCM. Using the outer volume for mass
inflates both the sensible and the latent capacity of the store -- and the
latent term is the entire point of the design, so the error flows straight
into g_window. It also mis-states the conduction path: heat entering the
capsule travels from the inner wall surface inward, over the inner radius,
not the outer one.

The aluminium shell is not thermally inert either: it has real heat
capacity sitting between the water and the PCM. Rather than adding a third
node, its capacity is folded into the PCM node, exactly as her report
describes ("wall heat capacity carried in the PCM node"). The mechanism
used here is an AUGMENTED SPECIFIC HEAT: per kilogram of PCM,

    cp_aug = cp_pcm + (m_wall * cp_wall) / m_pcm

applied to both the solid and the liquid branch, with the latent heat per
kilogram of PCM left untouched (the shell does not melt). Because
`capsule_enthalpy`'s h(T) is built from cp_solid/cp_liquid/latent, feeding
it the augmented cp makes every downstream quantity consistent
automatically -- h_s, the melt band, and the inversion of h back to
(T, f_melt) -- and `m_pcm * h` then totals the PCM *and* shell energy, so
the Gate-1 energy balance still closes without a separate wall term.

Aluminium density and specific heat are HANDBOOK values, not measured
here and (as her report also notes) not present in the frozen config;
they are read from config if present and otherwise default to the
standard values below.
"""

import math
from dataclasses import dataclass, replace

from src.simulation.capsule_enthalpy import PCMThermalProps

AL_DENSITY_KG_M3 = 2700.0      # handbook, aluminium
AL_CP_J_KGK = 900.0            # handbook, aluminium


@dataclass(frozen=True)
class CapsuleMassBreakdown:
    outer_diameter_m: float
    inner_diameter_m: float
    wall_thickness_m: float
    outer_volume_m3: float
    inner_volume_m3: float
    wall_volume_m3: float
    inner_area_m2: float
    outer_area_m2: float
    m_pcm_total_kg: float
    m_wall_total_kg: float
    cp_augment_J_kgK: float     # (m_wall * cp_wall) / m_pcm, per kg of PCM


def capsule_breakdown(n_capsule: int, outer_diameter_m: float, pcm_density_kg_m3: float,
                       system_config: dict) -> CapsuleMassBreakdown:
    integ = system_config["pcm_integration"]
    t = float(integ["capsule_wall_thickness_m"])
    rho_wall = float(integ.get("capsule_wall_density_kg_m3", AL_DENSITY_KG_M3))
    cp_wall = float(integ.get("capsule_wall_cp_J_kgK", AL_CP_J_KGK))

    d_in = max(outer_diameter_m - 2.0 * t, 1e-9)
    v_out = math.pi / 6.0 * outer_diameter_m ** 3
    v_in = math.pi / 6.0 * d_in ** 3
    v_wall = max(v_out - v_in, 0.0)

    m_pcm = n_capsule * v_in * pcm_density_kg_m3
    m_wall = n_capsule * v_wall * rho_wall
    cp_aug = (m_wall * cp_wall / m_pcm) if m_pcm > 0 else 0.0

    return CapsuleMassBreakdown(
        outer_diameter_m=outer_diameter_m, inner_diameter_m=d_in, wall_thickness_m=t,
        outer_volume_m3=v_out, inner_volume_m3=v_in, wall_volume_m3=v_wall,
        inner_area_m2=math.pi * d_in ** 2, outer_area_m2=math.pi * outer_diameter_m ** 2,
        m_pcm_total_kg=m_pcm, m_wall_total_kg=m_wall, cp_augment_J_kgK=cp_aug,
    )


def props_with_wall_capacity(pcm_props: PCMThermalProps,
                              breakdown: CapsuleMassBreakdown) -> PCMThermalProps:
    """PCM properties with the shell's heat capacity folded in (G2).
    Latent heat is deliberately NOT scaled -- aluminium does not melt."""
    if breakdown.cp_augment_J_kgK <= 0:
        return pcm_props
    return replace(
        pcm_props,
        cp_solid_J_kgK=pcm_props.cp_solid_J_kgK + breakdown.cp_augment_J_kgK,
        cp_liquid_J_kgK=pcm_props.cp_liquid_J_kgK + breakdown.cp_augment_J_kgK,
    )


def pcm_side_resistance(breakdown: CapsuleMassBreakdown, k_eff_W_mK: float) -> float:
    """Internal PCM conduction resistance on the INNER radius and INNER
    area (D3), replacing the outer-geometry version. Same lumped
    r/(5 k A) sphere approximation as before -- only the geometry it is
    evaluated on changes."""
    if k_eff_W_mK <= 0 or breakdown.inner_area_m2 <= 0:
        return float("inf")
    return (breakdown.inner_diameter_m / 2.0) / (5.0 * k_eff_W_mK * breakdown.inner_area_m2)
