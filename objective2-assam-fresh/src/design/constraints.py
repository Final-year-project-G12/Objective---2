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
    crashes; determinism (same vector twice -> identical output)."""
    system_config = load_system_config()
    bounds = load_design_bounds()
    d_bounds = bounds["capsule_diameter_m"]
    n_bounds = bounds["capsule_count"]
    f_bounds = bounds["flow_rate_kg_s"]

    cases = [
        ("min_diameter_min_count", DesignVector(d_bounds["min"], n_bounds["min"], f_bounds["min"])),
        ("max_diameter_max_count", DesignVector(d_bounds["max"], n_bounds["max"], f_bounds["max"])),
        ("min_diameter_max_count", DesignVector(d_bounds["min"], n_bounds["max"], f_bounds["max"])),
        ("max_diameter_min_count", DesignVector(d_bounds["max"], n_bounds["min"], f_bounds["min"])),
        ("mid_case", DesignVector(0.05, 14, 0.030)),
        ("flow_below_min", DesignVector(0.05, 14, f_bounds["min"] - 0.005)),
        ("flow_above_max", DesignVector(0.05, 14, f_bounds["max"] + 0.005)),
        ("oversized_diameter_for_tank", DesignVector(0.30, 14, 0.030)),
    ]

    rows = []
    for name, design in cases:
        r1 = check_design(design, system_config, bounds)
        r2 = check_design(design, system_config, bounds)
        deterministic = (r1["valid"] == r2["valid"] and r1["reason"] == r2["reason"])
        rows.append((name, r1["valid"], r1["reason"], deterministic))
        if verbose:
            print(f"  {name:28s} valid={r1['valid']!s:5s} reason={str(r1['reason']):20s} "
                  f"deterministic={deterministic}")

    all_deterministic = all(r[3] for r in rows)
    if verbose:
        print(f"\n  All boundary cases deterministic: {all_deterministic}")
    return rows, all_deterministic


if __name__ == "__main__":
    print("=" * 68)
    print("  Phase 2 exit check — geometry & constraint boundary cases")
    print("=" * 68)
    run_boundary_self_test()
