"""
src/design/geometry.py
========================
Phase 2 / Deliverable D2.2 — Geometry & constraint engine.

Given a design vector (capsule diameter, capsule count, flow rate), returns
volume/area/spacing/pressure-drop and a valid/invalid flag with reason.
Universal code — identical for every state; only the demand/weather/PCM
inputs supplied elsewhere differ per state.

GEOMETRIC MODEL (documented simplification, appropriate for a 40-hr MVP):
  - Tank is a vertical cylinder. Its diameter/height are derived from the
    frozen tank volume assuming height = 2 x diameter (typical domestic SWH
    proportion; see system_config_shared.yaml).
  - Capsules are spheres packed in staggered horizontal layers stacked up
    the tank height. Each layer is a 2D hexagonal ("staggered") packing of
    circles in the tank's circular cross-section — the standard staggered
    arrangement referenced in design_bounds_shared.yaml.
  - Pressure drop uses the Ergun equation for flow through a packed bed of
    spheres (Ergun, 1952) — a standard correlation, not derived from
    scratch, as required by the framework doc [1, Sec 3.2].

REASON CODES (constraints.py maps these to reject/accept):
  overlap           - capsule diameter too large for even one to fit in the
                       tank cross-section at the required spacing.
  volume_exceeded   - N_capsule*V_capsule exceeds the allocated PCM volume
                       fraction bound (design_bounds: 0.10-0.20 of V_tank).
  passage_blocked   - the capsule stack does not fit within the tank height,
                       or the resulting bed void fraction is below the
                       minimum free-flow passage fraction.
  pressure_drop_limit - estimated pressure drop exceeds the system's max
                       pressure limit.
  flow_out_of_range - flow rate outside [flow_min, flow_max] (extra reason
                       code beyond the framework doc's base four, documented
                       here for clarity).

Determinism: pure functions of (design vector, frozen configs) -> same
inputs always produce identical outputs (checked in Phase 2 exit test).
"""

import math

from src.design.schema import DesignVector
from src.io_utils import load_system_config, load_design_bounds

WATER_DENSITY_KG_M3 = 1000.0


# ─────────────────────────────────────────────────────────────────────────
# Sphere primitives
# ─────────────────────────────────────────────────────────────────────────

def sphere_volume_m3(diameter_m: float) -> float:
    r = diameter_m / 2.0
    return (4.0 / 3.0) * math.pi * r ** 3


def sphere_surface_area_m2(diameter_m: float) -> float:
    r = diameter_m / 2.0
    return 4.0 * math.pi * r ** 2


# ─────────────────────────────────────────────────────────────────────────
# Tank envelope (derived once from the frozen tank volume)
# ─────────────────────────────────────────────────────────────────────────

def tank_dimensions_m(system_config: dict):
    """Vertical cylinder: V = (pi/4) D^2 H, H = ratio * D  ->  D = (4V/(pi*ratio))^(1/3)."""
    v_tank_m3 = system_config["tank"]["volume_L"] / 1000.0
    ratio = system_config["tank"]["height_to_diameter_ratio"]
    d_tank = (4.0 * v_tank_m3 / (math.pi * ratio)) ** (1.0 / 3.0)
    h_tank = ratio * d_tank
    cross_section_area_m2 = math.pi / 4.0 * d_tank ** 2
    tank_surface_area_m2 = math.pi * d_tank * h_tank + 2 * cross_section_area_m2  # side + 2 caps
    return {
        "tank_diameter_m": d_tank,
        "tank_height_m": h_tank,
        "tank_volume_m3": v_tank_m3,
        "tank_cross_section_area_m2": cross_section_area_m2,
        "tank_surface_area_m2": tank_surface_area_m2,
    }


# ─────────────────────────────────────────────────────────────────────────
# Staggered (hexagonal) packing in the tank's circular cross-section
# ─────────────────────────────────────────────────────────────────────────

def capsules_per_layer(tank_cross_section_area_m2: float, capsule_diameter_m: float,
                        spacing_min_m: float) -> int:
    """Hexagonal (staggered) packing pitch = diameter + minimum clearance.
    Footprint area per sphere in a hex lattice = (sqrt(3)/2) * pitch^2."""
    pitch = capsule_diameter_m + spacing_min_m
    footprint_area = (math.sqrt(3.0) / 2.0) * pitch ** 2
    if footprint_area <= 0:
        return 0
    return max(0, math.floor(tank_cross_section_area_m2 / footprint_area))


def compute_geometry(design: DesignVector, system_config: dict = None,
                      design_bounds: dict = None) -> dict:
    """Deterministic geometry + hydraulics for one design vector.
    Returns a dict always containing `valid` (bool) and `reason` (str or None).
    """
    system_config = system_config or load_system_config()
    design_bounds = design_bounds or load_design_bounds()

    d = design.capsule_diameter_m
    n = design.n_capsule
    mdot = design.flow_rate_kg_s

    tank = tank_dimensions_m(system_config)
    v_tank = tank["tank_volume_m3"]

    v_capsule = sphere_volume_m3(d)
    a_capsule = sphere_surface_area_m2(d)
    thickness_m = d / 2.0   # max PCM conduction distance for a sphere = radius

    spacing_min = design_bounds["geometry"]["spacing_min_m"]
    passage_min_fraction = design_bounds["geometry"]["passage_min_fraction"]

    result = {
        "capsule_diameter_m": d,
        "n_capsule": n,
        "flow_rate_kg_s": mdot,
        "pcm_thickness_m": thickness_m,
        "capsule_volume_m3": v_capsule,
        "capsule_surface_area_m2": a_capsule,
        **tank,
        "valid": True,
        "reason": None,
    }

    # ---- flow range check --------------------------------------------
    flow_bounds = design_bounds["flow_rate_kg_s"]
    if not (flow_bounds["min"] - 1e-12 <= mdot <= flow_bounds["max"] + 1e-12):
        result.update(valid=False, reason="flow_out_of_range")
        return result

    # ---- capsule-per-layer / overlap check -----------------------------
    per_layer = capsules_per_layer(tank["tank_cross_section_area_m2"], d, spacing_min)
    result["capsules_per_layer"] = per_layer
    if per_layer < 1:
        result.update(valid=False, reason="overlap")
        return result

    n_layers = math.ceil(n / per_layer) if n > 0 else 0
    layer_pitch_m = d + spacing_min
    stack_height_m = n_layers * layer_pitch_m
    result["n_layers"] = n_layers
    result["stack_height_m"] = stack_height_m

    # ---- PCM volume fraction (derived) ---------------------------------
    v_pcm_total = n * v_capsule
    pcm_mass_kg_solid_basis = None  # filled by caller with PCM density (material-dependent)
    pcm_volume_fraction = v_pcm_total / v_tank if v_tank > 0 else float("inf")
    result["pcm_volume_total_m3"] = v_pcm_total
    result["pcm_volume_fraction"] = pcm_volume_fraction

    vf_bounds = design_bounds["pcm_volume_fraction"]
    if pcm_volume_fraction > vf_bounds["max"] + 1e-9:
        result.update(valid=False, reason="volume_exceeded")
        return result

    # ---- passage / envelope check --------------------------------------
    void_fraction = 1.0 - pcm_volume_fraction   # bed porosity approximation
    result["void_fraction"] = void_fraction
    if stack_height_m > tank["tank_height_m"]:
        result.update(valid=False, reason="passage_blocked")
        return result
    if void_fraction < passage_min_fraction:
        result.update(valid=False, reason="passage_blocked")
        return result
    if pcm_volume_fraction < vf_bounds["min"] - 1e-9:
        # Below the documented 10% floor — not a hard geometric failure, but
        # flagged so DOE/optimize can treat it as "below the tested range".
        result["below_min_pcm_fraction"] = True
    else:
        result["below_min_pcm_fraction"] = False

    # ---- hydraulics: Ergun equation over the packed capsule bed --------
    hydraulics = compute_hydraulics(
        mdot_kg_s=mdot,
        capsule_diameter_m=d,
        void_fraction=void_fraction,
        cross_section_area_m2=tank["tank_cross_section_area_m2"],
        bed_length_m=stack_height_m if stack_height_m > 0 else tank["tank_height_m"],
        system_config=system_config,
    )
    result.update(hydraulics)

    max_pressure_pa = system_config["safety"]["max_pressure_bar"] * 1e5
    if result["pressure_drop_pa"] > max_pressure_pa:
        result.update(valid=False, reason="pressure_drop_limit")
        return result

    return result


# ─────────────────────────────────────────────────────────────────────────
# Hydraulics — Ergun equation (packed bed of spheres) + pump power
# ─────────────────────────────────────────────────────────────────────────

def compute_hydraulics(mdot_kg_s: float, capsule_diameter_m: float, void_fraction: float,
                        cross_section_area_m2: float, bed_length_m: float,
                        system_config: dict) -> dict:
    rho = system_config["water"]["density_kg_m3"]
    mu = _water_dynamic_viscosity_pa_s()

    eps = min(max(void_fraction, 1e-3), 0.999)
    dp = capsule_diameter_m
    volumetric_flow_m3_s = mdot_kg_s / rho
    superficial_velocity_m_s = volumetric_flow_m3_s / cross_section_area_m2 if cross_section_area_m2 > 0 else 0.0

    re_particle = rho * superficial_velocity_m_s * dp / mu if mu > 0 else 0.0

    # Ergun (1952): dP/L = 150*(1-eps)^2/eps^3 * mu*u/dp^2 + 1.75*(1-eps)/eps^3 * rho*u^2/dp
    viscous_term = 150.0 * (1 - eps) ** 2 / eps ** 3 * mu * superficial_velocity_m_s / dp ** 2
    inertial_term = 1.75 * (1 - eps) / eps ** 3 * rho * superficial_velocity_m_s ** 2 / dp
    dp_dl_pa_per_m = viscous_term + inertial_term
    pressure_drop_pa = dp_dl_pa_per_m * bed_length_m

    hydraulic_diameter_m = (2.0 / 3.0) * dp * eps / (1 - eps) if eps < 1.0 else dp

    eta_pump = system_config["pump"]["efficiency"]
    pump_power_w = pressure_drop_pa * volumetric_flow_m3_s / eta_pump if eta_pump > 0 else 0.0

    return {
        "void_fraction_used_for_hydraulics": eps,
        "superficial_velocity_m_s": superficial_velocity_m_s,
        "reynolds_number_particle": re_particle,
        "hydraulic_diameter_m": hydraulic_diameter_m,
        "pressure_drop_pa": pressure_drop_pa,
        "pump_power_w": pump_power_w,
    }


def _water_dynamic_viscosity_pa_s(t_c: float = 40.0) -> float:
    """Simple correlation for water dynamic viscosity (Pa.s) near typical
    operating temperature; adequate for a design-space pressure-drop estimate
    (documented simplification — not a full property library)."""
    # Vogel-like fit, valid ~0-100 C, matches tabulated water viscosity to
    # within a few percent in the 20-60 C range used by this project.
    a, b, c = 2.414e-5, 247.8, 140.0
    t_k = t_c + 273.15
    return a * 10 ** (b / (t_k - c))
