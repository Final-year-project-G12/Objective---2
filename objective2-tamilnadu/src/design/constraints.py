"""
src/design/constraints.py
===========================
Phase 2 / D2.2 — wraps geometry.compute_geometry() with the design-bounds
range checks (capsule diameter, capsule count, derived thickness) so every
generated design gets ONE valid/invalid verdict plus a single reason code,
before any physics is run. This is the gate DOE (Phase 5) will call for
every sampled row; the simulator never needs to see a geometrically
invalid design.

Reason-code precedence (first hit wins, matches the framework doc's list):
  bounds_violation -> overlap -> volume_exceeded -> passage_blocked ->
  pressure_drop_limit -> flow_out_of_range -> (valid)
"""

from src.design.schema import DesignVector
from src.design.geometry import compute_geometry
from src.io_utils import load_system_config, load_design_bounds


def _in_bounds(value, bounds):
    return bounds["min"] - 1e-12 <= value <= bounds["max"] + 1e-12


def check_design(design: DesignVector, system_config: dict = None,
                  design_bounds: dict = None) -> dict:
    system_config = system_config or load_system_config()
    design_bounds = design_bounds or load_design_bounds()

    # ---- 1. raw variable-range checks (before any geometry math) -------
    if design.capsule_shape not in design_bounds["capsule_shape"]:
        return _reject(design, "bounds_violation", f"shape {design.capsule_shape} not in "
                                                      f"{design_bounds['capsule_shape']}")
    allowed_arrangements = design_bounds["capsule_arrangement"]["allowed"]
    if design.capsule_arrangement not in allowed_arrangements:
        return _reject(design, "bounds_violation",
                        f"arrangement {design.capsule_arrangement} not in "
                        f"{allowed_arrangements}")
    if not _in_bounds(design.capsule_diameter_m, design_bounds["capsule_diameter_m"]):
        return _reject(design, "bounds_violation", "capsule_diameter_m out of range")

    count_bounds = design_bounds["capsule_count"]
    if not (count_bounds["min"] <= design.n_capsule <= count_bounds["max"]):
        return _reject(design, "bounds_violation", "n_capsule out of range")
    if design.n_capsule != int(design.n_capsule):
        return _reject(design, "bounds_violation", "n_capsule must be an integer")

    thickness_m = design.capsule_diameter_m / 2.0
    if not _in_bounds(thickness_m, design_bounds["pcm_thickness_m"]):
        return _reject(design, "bounds_violation", "derived pcm_thickness_m out of range")

    # ---- 2. geometry + hydraulics (may itself reject) -------------------
    geom = compute_geometry(design, system_config, design_bounds)
    geom["design"] = design.as_dict()
    geom["notes"] = None
    return geom


def _reject(design: DesignVector, reason: str, note: str) -> dict:
    return {
        "design": design.as_dict(),
        "valid": False,
        "reason": reason,
        "notes": note,
    }


# ─────────────────────────────────────────────────────────────────────────
# Phase 2 exit check — determinism + boundary cases
# ─────────────────────────────────────────────────────────────────────────

def run_boundary_self_test(verbose: bool = True):
    """Runs the Phase 2 exit check: the 8 boundary cases (min/max
    thickness, min/max count, flow limits, an oversized capsule) once per
    arrangement (24 total, restored 2026-09-17 -- was 8 when arrangement
    was frozen to staggered-only), each checked for determinism (same
    vector twice -> identical output), PLUS a cross-arrangement sanity
    case: the identical (diameter, count, flow) triple run under all three
    arrangements must NOT produce identical void_fraction/pressure_drop_pa
    -- if it does, the dispatcher isn't actually branching, and that is a
    test failure, not a pass (adapted from
    "a Rajasthan-pilot change plan (source removed from this project after adaptation, see docs_objective2/tamilnadu_phase_docs/)" for
    Tamil Nadu)."""
    system_config = load_system_config()
    bounds = load_design_bounds()
    d_bounds = bounds["capsule_diameter_m"]
    n_bounds = bounds["capsule_count"]
    f_bounds = bounds["flow_rate_kg_s"]
    arrangements = bounds["capsule_arrangement"]["allowed"]

    base_cases = [
        ("min_diameter_min_count", d_bounds["min"], n_bounds["min"], f_bounds["min"]),
        ("max_diameter_max_count", d_bounds["max"], n_bounds["max"], f_bounds["max"]),
        ("min_diameter_max_count", d_bounds["min"], n_bounds["max"], f_bounds["max"]),
        ("max_diameter_min_count", d_bounds["max"], n_bounds["min"], f_bounds["min"]),
        ("mid_case", 0.05, 14, 0.030),
        ("flow_below_min", 0.05, 14, f_bounds["min"] - 0.005),
        ("flow_above_max", 0.05, 14, f_bounds["max"] + 0.005),
        ("oversized_diameter_for_tank", 0.30, 14, 0.030),
    ]

    rows = []
    for arrangement in arrangements:
        if verbose:
            print(f"\n  -- arrangement: {arrangement} --")
        for name, d, n, f in base_cases:
            design = DesignVector(d, n, f, capsule_arrangement=arrangement)
            r1 = check_design(design, system_config, bounds)
            r2 = check_design(design, system_config, bounds)
            deterministic = (r1["valid"] == r2["valid"] and r1["reason"] == r2["reason"])
            rows.append((f"{arrangement}/{name}", r1["valid"], r1["reason"], deterministic))
            if verbose:
                print(f"    {name:28s} valid={r1['valid']!s:5s} reason={str(r1['reason']):20s} "
                      f"deterministic={deterministic}")

    all_deterministic = all(r[3] for r in rows)
    if verbose:
        print(f"\n  All {len(rows)} boundary cases deterministic: {all_deterministic}")

    # ---- cross-arrangement sanity check ---------------------------------
    sanity_design_by_arr = {a: DesignVector(0.05, 20, 0.030, capsule_arrangement=a) for a in arrangements}
    sanity_results = {a: check_design(d, system_config, bounds) for a, d in sanity_design_by_arr.items()}
    void_fracs = {a: r.get("void_fraction") for a, r in sanity_results.items() if r["valid"]}
    pressure_drops = {a: r.get("pressure_drop_pa") for a, r in sanity_results.items() if r["valid"]}
    arrangements_actually_differ = len(set(void_fracs.values())) > 1 or len(set(pressure_drops.values())) > 1
    if verbose:
        print(f"\n  Cross-arrangement sanity check (same 0.05m/20-capsule/0.030kg-s design):")
        for a in arrangements:
            r = sanity_results[a]
            print(f"    {a:12s} valid={r['valid']!s:5s} void_fraction={r.get('void_fraction')} "
                  f"pressure_drop_pa={r.get('pressure_drop_pa')}")
        print(f"  Arrangements produce genuinely different geometry: {arrangements_actually_differ}"
              f"  {'(PASS — dispatcher is branching)' if arrangements_actually_differ else '(FAIL — dispatcher NOT branching!)'}")

    return rows, all_deterministic, arrangements_actually_differ


def report_max_reachable_fraction_table(verbose: bool = True):
    """Phase 2 exit requirement: max-reachable PCM-volume-fraction per
    arrangement at the diameter ceiling, up to the shared capsule_count
    ceiling. Does NOT assume any arrangement matches another's number --
    report whatever the sweep finds, including asymmetry between
    arrangements (that asymmetry is itself a finding for Phase 6/7 to
    pick up on later, not something to equalize here)."""
    from src.design.geometry import get_max_reachable_pcm_fraction
    bounds = load_design_bounds()
    arrangements = bounds["capsule_arrangement"]["allowed"]
    count_max = bounds["capsule_count"]["max"]
    diameter = bounds["capsule_diameter_m"]["max"]

    rows = [get_max_reachable_pcm_fraction(a, diameter_m=diameter, count_max=count_max) for a in arrangements]
    if verbose:
        print(f"\n  Max-reachable PCM-volume-fraction table (diameter={diameter} m, count_max={count_max}):")
        print(f"  {'Arrangement':<14}{'Max N feasible':<18}{'Max reachable PCM vol %':<26}")
        for r in rows:
            print(f"  {r['arrangement']:<14}{r['max_n_feasible']:<18}"
                  f"{r['max_reachable_pcm_volume_fraction']*100:<26.2f}")
    return rows


if __name__ == "__main__":
    print("=" * 68)
    print("  Phase 2 exit check — geometry & constraint boundary cases")
    print("  (arrangement restored 2026-09-17 — 24-case table + cross-arrangement")
    print("   sanity check + max-reachable-fraction table)")
    print("=" * 68)
    run_boundary_self_test()
    report_max_reachable_fraction_table()
