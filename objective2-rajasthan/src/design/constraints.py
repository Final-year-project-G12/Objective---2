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
    if design.capsule_arrangement not in design_bounds["capsule_arrangement"]:
        return _reject(design, "bounds_violation",
                        f"arrangement {design.capsule_arrangement} not in "
                        f"{design_bounds['capsule_arrangement']}")
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
    """Runs the framework doc's Phase 2 exit check: boundary cases (min/max
    thickness, min/max count) each return a clean valid/invalid + reason, no
    crashes; determinism (same vector twice -> identical output).

    Restored 2026-09-17 (docs/02_PROMPT_PHASE2_GEOMETRY.md): the original 8
    boundary cases now run once per arrangement (24 total, not 8), plus one
    new cross-arrangement sanity case confirming the packing dispatcher
    actually branches (same diameter/count/flow must NOT produce identical
    void_fraction/pressure_drop_pa across all three arrangements)."""
    system_config = load_system_config()
    bounds = load_design_bounds()
    d_bounds = bounds["capsule_diameter_m"]
    n_bounds = bounds["capsule_count"]
    f_bounds = bounds["flow_rate_kg_s"]
    arrangements = bounds["capsule_arrangement"]

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
        for name, d, n, f in base_cases:
            design = DesignVector(d, n, f, capsule_arrangement=arrangement)
            r1 = check_design(design, system_config, bounds)
            r2 = check_design(design, system_config, bounds)
            deterministic = (r1["valid"] == r2["valid"] and r1["reason"] == r2["reason"])
            full_name = f"{name} [{arrangement}]"
            rows.append((full_name, r1["valid"], r1["reason"], deterministic))
            if verbose:
                print(f"  {full_name:42s} valid={r1['valid']!s:5s} reason={str(r1['reason']):20s} "
                      f"deterministic={deterministic}")

    all_deterministic = all(r[3] for r in rows)
    if verbose:
        print(f"\n  All {len(rows)} boundary cases deterministic: {all_deterministic}")

    # ---- cross-arrangement sanity: dispatcher must actually branch --------
    sanity_design_by_arr = {a: DesignVector(0.05, 14, 0.030, capsule_arrangement=a) for a in arrangements}
    sanity_results = {a: check_design(d, system_config, bounds) for a, d in sanity_design_by_arr.items()}
    void_fractions = {a: r.get("void_fraction") for a, r in sanity_results.items()}
    pressure_drops = {a: r.get("pressure_drop_pa") for a, r in sanity_results.items()}
    dispatcher_branches = (len(set(void_fractions.values())) > 1 or len(set(pressure_drops.values())) > 1)
    if verbose:
        print("\n  Cross-arrangement sanity (same d=0.05, n=14, flow=0.030):")
        for a in arrangements:
            print(f"    {a:14s} void_fraction={void_fractions[a]!s:22s} pressure_drop_pa={pressure_drops[a]}")
        print(f"  Dispatcher genuinely branches (values differ across arrangements): {dispatcher_branches}")

    all_pass = all_deterministic and dispatcher_branches
    return rows, all_pass


def report_max_reachable_pcm_fraction(verbose: bool = True):
    """Phase 2 exit check: per-arrangement max-reachable-fraction table
    (docs/02_PROMPT_PHASE2_GEOMETRY.md step 8)."""
    from src.design.geometry import get_max_reachable_pcm_fraction

    bounds = load_design_bounds()
    arrangements = bounds["capsule_arrangement"]
    count_max = bounds["capsule_count"]["max"]
    rows = [get_max_reachable_pcm_fraction(a, diameter_m=0.08, count_max=count_max) for a in arrangements]
    if verbose:
        print(f"\n  Max-reachable-fraction table (diameter=0.08 m, count ceiling={count_max}):")
        print(f"  {'arrangement':14s} {'max_n_feasible':16s} {'max_reachable_pcm_fraction':28s}")
        for row in rows:
            print(f"  {row['arrangement']:14s} {row['max_n_feasible']:<16d} "
                  f"{row['max_reachable_pcm_fraction']:.4f}")
    return rows


if __name__ == "__main__":
    print("=" * 68)
    print("  Phase 2 exit check — geometry & constraint boundary cases")
    print("=" * 68)
    run_boundary_self_test()
    report_max_reachable_pcm_fraction()
