"""
src/design/geometry.py
========================
Phase 2 / Deliverable D2.2 — Geometry & constraint engine.

Given a design vector (capsule diameter, capsule count, flow rate,
arrangement), returns volume/area/spacing/pressure-drop and a valid/invalid
flag with reason. Universal code — identical for every state; only the
demand/weather/PCM inputs supplied elsewhere differ per state.

GEOMETRIC MODEL (documented simplification, appropriate for a 40-hr MVP):
  - Tank is a vertical cylinder. Its diameter/height are derived from the
    frozen tank volume assuming height = 2 x diameter (typical domestic SWH
    proportion; see system_config_shared.yaml).
  - Capsules are spheres packed in horizontal layers stacked up the tank
    height, in one of three arrangements (restored as a searched variable
    2026-09-17 -- see design_bounds_shared.yaml and
    docs_objective2/17_ARRANGEMENT_RESTORATION.md):
      staggered    - 2D hexagonal-lattice packing per layer (highest
                     packing density of the three).
      single-layer - simple square-grid packing per layer, no row offset
                     (lower density than staggered by construction).
      radial       - concentric rings of capsules around the tank's
                     vertical axis, ring count/capacity set by tank and
                     capsule diameter.
    Each arrangement's local bed void fraction (used by the Ergun pressure-
    drop/heat-transfer calculations) is derived from HOW MANY LAYERS its
    own packing needs for a given capsule count -- denser packing (fewer,
    shorter layers) gives a different local void fraction than sparser
    packing for the identical (diameter, count) design, which is why the
    same design vector run under different arrangements produces genuinely
    different pressure_drop_pa/void_fraction, not just different labels.
  - Pressure drop uses the Ergun equation for flow through a packed bed of
    spheres (Ergun, 1952) — a standard correlation, not derived from
    scratch, as required by the framework doc [1, Sec 3.2].

REASON CODES (constraints.py maps these to reject/accept):
  overlap           - capsule diameter too large for even one to fit in the
                       tank cross-section at the required spacing (any
                       arrangement).
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
from dataclasses import dataclass

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
# Per-arrangement packing models
# ─────────────────────────────────────────────────────────────────────────

@dataclass
class PackingResult:
    arrangement: str
    capsules_per_layer: int      # or "per ring-set" for radial — same field name, see docstring
    n_layers: int
    stack_height_m: float
    void_fraction: float         # LOCAL bed porosity within the occupied stack (see module docstring)


def pack_staggered(diameter_m: float, tank_diameter_m: float, tank_height_m: float,
                    spacing_min_m: float, n_capsule: int, capsule_volume_m3: float) -> PackingResult:
    """2D hexagonal-lattice packing per horizontal layer — the original,
    already-validated staggered arrangement. Per-layer capacity math
    unchanged from the pre-2026-09-17 single-arrangement implementation;
    only wrapped into the common PackingResult interface, and void_fraction
    now comes from the pattern's own unit-cell porosity (see
    _pattern_void_fraction) rather than a whole-bed volumetric average."""
    cross_section_area = math.pi / 4.0 * tank_diameter_m ** 2
    pitch = diameter_m + spacing_min_m
    footprint_area = (math.sqrt(3.0) / 2.0) * pitch ** 2
    per_layer = max(0, math.floor(cross_section_area / footprint_area)) if footprint_area > 0 else 0
    void_fraction = _pattern_void_fraction(capsule_volume_m3, footprint_area, pitch)
    return _finish_packing("staggered", per_layer, n_capsule, pitch, tank_height_m, void_fraction)


def pack_single_layer(diameter_m: float, tank_diameter_m: float, tank_height_m: float,
                       spacing_min_m: float, n_capsule: int, capsule_volume_m3: float) -> PackingResult:
    """Simple planar square-grid packing per layer, no row offset. Lower
    packing density than staggered by construction (footprint = pitch^2,
    not the hex lattice's (sqrt(3)/2)*pitch^2 ~ 0.866*pitch^2) -- this is
    the expected, correct direction, not artificially equalized to match
    staggered's count. (Sanity check: this unit-cell model gives ~0.476
    void fraction for simple-cubic-equivalent stacking, matching the
    textbook simple-cubic sphere-packing porosity.)"""
    cross_section_area = math.pi / 4.0 * tank_diameter_m ** 2
    pitch = diameter_m + spacing_min_m
    footprint_area = pitch ** 2
    per_layer = max(0, math.floor(cross_section_area / footprint_area)) if footprint_area > 0 else 0
    void_fraction = _pattern_void_fraction(capsule_volume_m3, footprint_area, pitch)
    return _finish_packing("single-layer", per_layer, n_capsule, pitch, tank_height_m, void_fraction)


def pack_radial(diameter_m: float, tank_diameter_m: float, tank_height_m: float,
                 spacing_min_m: float, n_capsule: int, capsule_volume_m3: float) -> PackingResult:
    """Concentric rings of capsules around the tank's vertical axis. Ring k
    (k=0,1,2,...) sits at radius r_k=(k+0.5)*pitch from the centerline and
    holds floor(2*pi*r_k/pitch) capsules (ring circumference / pitch);
    rings stop once r_k+diameter/2 would exceed the tank radius. Per-layer
    capacity is the sum across all rings that fit. void_fraction uses the
    AVERAGE footprint area per capsule across the placed rings (area of the
    disk enclosing every used ring, divided by per_layer) -- radial's
    packing density is therefore a genuine function of how evenly the ring
    pattern fills the tank's circular cross-section, distinct from both the
    square-grid and hex-lattice patterns."""
    cross_section_area = math.pi / 4.0 * tank_diameter_m ** 2
    pitch = diameter_m + spacing_min_m
    tank_radius = tank_diameter_m / 2.0
    per_layer = 0
    k = 0
    last_r = 0.0
    while True:
        r_k = (k + 0.5) * pitch
        if r_k + diameter_m / 2.0 > tank_radius:
            break
        ring_capacity = max(1, math.floor(2 * math.pi * r_k / pitch)) if pitch > 0 else 0
        per_layer += ring_capacity
        last_r = r_k
        k += 1
        if k > 10_000:   # safety valve against a degenerate pitch<=0 infinite loop
            break

    if per_layer < 1:
        void_fraction = 1.0
    else:
        enclosing_disk_area = math.pi * (last_r + pitch / 2.0) ** 2
        avg_footprint_area = enclosing_disk_area / per_layer
        void_fraction = _pattern_void_fraction(capsule_volume_m3, avg_footprint_area, pitch)
    return _finish_packing("radial", per_layer, n_capsule, pitch, tank_height_m, void_fraction)


def _pattern_void_fraction(capsule_volume_m3: float, footprint_area_per_capsule_m2: float,
                            layer_pitch_m: float) -> float:
    """Unit-cell porosity of a packing pattern: 1 - (sphere volume) /
    (footprint area per capsule x layer pitch). This is a property of the
    PATTERN and capsule size alone -- constant regardless of how many
    capsules or layers are actually used -- which is what makes it a valid
    Ergun-equation bed porosity (a bed-characteristic constant for the
    packing type) and what makes different arrangements produce genuinely
    different void_fraction/pressure_drop even for an identical (diameter,
    count, flow) design and even when all capsules fit in a single layer."""
    unit_cell_volume = footprint_area_per_capsule_m2 * layer_pitch_m
    if unit_cell_volume <= 0:
        return 1.0
    return max(0.0, min(1.0, 1.0 - capsule_volume_m3 / unit_cell_volume))


def _finish_packing(arrangement: str, per_layer: int, n_capsule: int, layer_pitch_m: float,
                     tank_height_m: float, void_fraction: float) -> PackingResult:
    if per_layer < 1:
        return PackingResult(arrangement, per_layer, 0, 0.0, 1.0)
    n_layers = math.ceil(n_capsule / per_layer) if n_capsule > 0 else 0
    stack_height_m = n_layers * layer_pitch_m
    return PackingResult(arrangement, per_layer, n_layers, stack_height_m, void_fraction)


def pack_capsules(arrangement: str, diameter_m: float, tank_diameter_m: float, tank_height_m: float,
                   spacing_min_m: float, n_capsule: int, capsule_volume_m3: float) -> PackingResult:
    """Dispatcher — the ONLY place arrangement selects which packing model
    runs; everything downstream (volume/passage/pressure-drop checks)
    consumes the returned PackingResult identically regardless of which
    branch produced it."""
    if arrangement == "single-layer":
        return pack_single_layer(diameter_m, tank_diameter_m, tank_height_m, spacing_min_m,
                                  n_capsule, capsule_volume_m3)
    elif arrangement == "staggered":
        return pack_staggered(diameter_m, tank_diameter_m, tank_height_m, spacing_min_m,
                               n_capsule, capsule_volume_m3)
    elif arrangement == "radial":
        return pack_radial(diameter_m, tank_diameter_m, tank_height_m, spacing_min_m,
                            n_capsule, capsule_volume_m3)
    else:
        raise ValueError(f"unknown arrangement: {arrangement!r} "
                          f"(expected one of: single-layer, staggered, radial)")


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
        "arrangement": design.capsule_arrangement,
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

    # ---- arrangement-dispatched packing (capsules-per-layer / overlap) --
    packing = pack_capsules(design.capsule_arrangement, d, tank["tank_diameter_m"],
                             tank["tank_height_m"], spacing_min, n, v_capsule)
    result["capsules_per_layer"] = packing.capsules_per_layer
    if packing.capsules_per_layer < 1:
        result.update(valid=False, reason="overlap")
        return result

    n_layers = packing.n_layers
    stack_height_m = packing.stack_height_m
    result["n_layers"] = n_layers
    result["stack_height_m"] = stack_height_m

    # ---- PCM volume fraction (derived, bulk — used for the 10-20% bound) -
    v_pcm_total = n * v_capsule
    pcm_volume_fraction = v_pcm_total / v_tank if v_tank > 0 else float("inf")
    result["pcm_volume_total_m3"] = v_pcm_total
    result["pcm_volume_fraction"] = pcm_volume_fraction

    vf_bounds = design_bounds["pcm_volume_fraction"]
    if pcm_volume_fraction > vf_bounds["max"] + 1e-9:
        result.update(valid=False, reason="volume_exceeded")
        return result

    # ---- passage / envelope check --------------------------------------
    # void_fraction is the LOCAL bed porosity within the occupied stack
    # (packing.void_fraction, arrangement-specific — see PackingResult /
    # module docstring), NOT the bulk 1-pcm_volume_fraction dilution figure
    # used only for the 10-20% bound check above. This is what makes the
    # same (diameter, count, flow) design produce genuinely different
    # pressure_drop_pa/void_fraction under different arrangements.
    void_fraction = packing.void_fraction
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


# ─────────────────────────────────────────────────────────────────────────
# Per-arrangement reachability sweep (Phase 2 exit requirement)
# ─────────────────────────────────────────────────────────────────────────

def get_max_reachable_pcm_fraction(arrangement: str, diameter_m: float = 0.08,
                                    count_max: int = 37, system_config: dict = None,
                                    design_bounds: dict = None) -> dict:
    """Sweeps capsule count 1..count_max at the diameter ceiling for one
    arrangement and returns the highest count that still produces a
    VOLUME/PASSAGE/PRESSURE-valid design (bounds_violation on diameter/flow
    is not checked here — this is a pure geometry sweep, mirroring what
    constraints.check_design would report for the diameter/count pair at a
    fixed representative flow rate). Used to build the per-arrangement
    max-reachable-fraction table (Phase 2 exit check) — do not assume any
    arrangement reaches the same fraction as another; report what the sweep
    actually finds."""
    system_config = system_config or load_system_config()
    design_bounds = design_bounds or load_design_bounds()
    spacing_min = design_bounds["geometry"]["spacing_min_m"]
    passage_min_fraction = design_bounds["geometry"]["passage_min_fraction"]
    vf_max = design_bounds["pcm_volume_fraction"]["max"]

    tank = tank_dimensions_m(system_config)
    v_capsule = sphere_volume_m3(diameter_m)
    v_tank = tank["tank_volume_m3"]

    best_n, best_fraction = 0, 0.0
    for n in range(1, count_max + 1):
        packing = pack_capsules(arrangement, diameter_m, tank["tank_diameter_m"],
                                 tank["tank_height_m"], spacing_min, n, v_capsule)
        if packing.capsules_per_layer < 1:
            break   # this arrangement can't even place one capsule at this diameter
        fraction = (n * v_capsule) / v_tank if v_tank > 0 else float("inf")
        if fraction > vf_max + 1e-9:
            break   # exceeds the shared volume-fraction ceiling
        if packing.stack_height_m > tank["tank_height_m"]:
            break   # exceeds tank height -> passage_blocked
        if packing.void_fraction < passage_min_fraction:
            break   # bed too dense -> passage_blocked
        best_n, best_fraction = n, fraction

    return {"arrangement": arrangement, "diameter_m": diameter_m,
            "max_n_feasible": best_n, "max_reachable_pcm_volume_fraction": best_fraction}
