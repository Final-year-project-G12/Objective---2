"""
src/doe/generate_cases.py
============================
Phase 5 / D2.4 — reduced design-of-experiments sampling plan
(O2_Unified_PerState_Execution_Framework.md, "Phase 5 - Reduced DOE").

Produces a list of CASE SPECS (not yet simulated) — one dict per row:
    case_id, regime_id (cluster_id), pcm_id (name or None for the no-PCM
    baseline), capsule_diameter_m, n_capsule, flow_rate_kg_s,
    sampling_method, seed.

src/doe/run_batch.py consumes this list and actually calls the Phase 3
simulator; this module only decides WHAT to simulate, never runs physics.

Sampling plan per regime x shortlisted-PCM pair:
  - Latin Hypercube (scipy.stats.qmc) over (capsule_diameter_m,
    flow_rate_kg_s, capsule_count-as-continuous-then-rounded) — the
    framework doc's "explicit enumeration for small integer sets" is
    approximated here by rounding the LHS draw to the nearest integer
    capsule count rather than enumerating a separate integer grid; with
    only 17 allowed integer values (8-24) this still gives reasonable
    coverage while keeping every LHS point jointly space-filling across
    all three variables at once (documented compromise, not a plain
    enumeration).
  - Boundary cases: every combination of {min,max} diameter x {min,max}
    flow, at the mid-range capsule count.
  - One no-PCM baseline case per regime (pcm_id=None).

Target total ~150-300 cases per state (framework doc §Phase 5), stated
sampling method and count are printed and returned in the manifest dict.
"""

from dataclasses import dataclass, asdict

import numpy as np
from scipy.stats import qmc

from src.io_utils import load_state_config, load_design_bounds

RANDOM_SEED = 20260905   # fixed, documented seed for reproducibility


@dataclass
class CaseSpec:
    case_id: str
    regime_id: int
    pcm_id: object          # str or None (no-PCM baseline)
    capsule_diameter_m: float
    n_capsule: int
    flow_rate_kg_s: float
    sampling_method: str
    seed: int


def _lhs_cases(regime_id, pcm_id, n_samples, bounds, seed, prefix):
    d_bounds = bounds["capsule_diameter_m"]
    f_bounds = bounds["flow_rate_kg_s"]
    n_bounds = bounds["capsule_count"]

    sampler = qmc.LatinHypercube(d=3, seed=seed)
    unit = sampler.random(n=n_samples)   # shape (n_samples, 3) in [0,1)

    diam = qmc.scale(unit[:, [0]], [d_bounds["min"]], [d_bounds["max"]]).ravel()
    flow = qmc.scale(unit[:, [1]], [f_bounds["min"]], [f_bounds["max"]]).ravel()
    count_cont = qmc.scale(unit[:, [2]], [n_bounds["min"]], [n_bounds["max"]]).ravel()
    count = np.clip(np.round(count_cont), n_bounds["min"], n_bounds["max"]).astype(int)

    cases = []
    for i in range(n_samples):
        cases.append(CaseSpec(
            case_id=f"{prefix}_lhs_{i:03d}",
            regime_id=regime_id, pcm_id=pcm_id,
            capsule_diameter_m=float(diam[i]), n_capsule=int(count[i]),
            flow_rate_kg_s=float(flow[i]), sampling_method="lhs", seed=seed,
        ))
    return cases


def _boundary_cases(regime_id, pcm_id, bounds, prefix):
    d_bounds = bounds["capsule_diameter_m"]
    f_bounds = bounds["flow_rate_kg_s"]
    n_bounds = bounds["capsule_count"]
    mid_count = int(round((n_bounds["min"] + n_bounds["max"]) / 2))

    combos = []
    for d_label, d_val in [("dmin", d_bounds["min"]), ("dmax", d_bounds["max"])]:
        for f_label, f_val in [("fmin", f_bounds["min"]), ("fmax", f_bounds["max"])]:
            combos.append((d_label, d_val, f_label, f_val))

    cases = []
    for i, (d_label, d_val, f_label, f_val) in enumerate(combos):
        cases.append(CaseSpec(
            case_id=f"{prefix}_bnd_{d_label}_{f_label}",
            regime_id=regime_id, pcm_id=pcm_id,
            capsule_diameter_m=float(d_val), n_capsule=mid_count,
            flow_rate_kg_s=float(f_val), sampling_method="boundary", seed=0,
        ))
    # min/max count at mid diameter/flow, so the count bound is also probed
    mid_d = (d_bounds["min"] + d_bounds["max"]) / 2
    mid_f = (f_bounds["min"] + f_bounds["max"]) / 2
    for label, n_val in [("nmin", n_bounds["min"]), ("nmax", n_bounds["max"])]:
        cases.append(CaseSpec(
            case_id=f"{prefix}_bnd_{label}",
            regime_id=regime_id, pcm_id=pcm_id,
            capsule_diameter_m=float(mid_d), n_capsule=int(n_val),
            flow_rate_kg_s=float(mid_f), sampling_method="boundary", seed=0,
        ))
    return cases


def generate_all_cases(state: str, n_lhs_per_pair: int = 8):
    """Returns (list_of_CaseSpec, manifest_dict)."""
    cfg = load_state_config(state)
    bounds = load_design_bounds()

    all_cases = []
    n_pairs = 0
    for regime in cfg["regimes"]:
        cid = regime["cluster_id"]

        # one no-PCM baseline per regime
        all_cases.append(CaseSpec(
            case_id=f"c{cid}_baseline_noPCM", regime_id=cid, pcm_id=None,
            capsule_diameter_m=bounds["capsule_diameter_m"]["max"],
            n_capsule=bounds["capsule_count"]["min"],
            flow_rate_kg_s=(bounds["flow_rate_kg_s"]["min"] + bounds["flow_rate_kg_s"]["max"]) / 2,
            sampling_method="baseline", seed=0,
        ))

        for pcm_id in regime["pcm_shortlist"]:
            n_pairs += 1
            prefix = f"c{cid}_{_slug(pcm_id)}"
            seed = RANDOM_SEED + cid * 1000 + hash(pcm_id) % 1000
            all_cases += _lhs_cases(cid, pcm_id, n_lhs_per_pair, bounds, seed, prefix)
            all_cases += _boundary_cases(cid, pcm_id, bounds, prefix)

    manifest = {
        "state": state, "random_seed_base": RANDOM_SEED,
        "n_regime_pcm_pairs": n_pairs, "n_lhs_per_pair": n_lhs_per_pair,
        "n_boundary_per_pair": 6, "n_baseline_cases": len(cfg["regimes"]),
        "n_total_cases": len(all_cases),
        "design_bounds_version": bounds.get("version"),
    }
    return all_cases, manifest


def _slug(name):
    return "".join(c if c.isalnum() else "_" for c in str(name))[:24]


if __name__ == "__main__":
    import sys
    state = sys.argv[1] if len(sys.argv) > 1 else "tamilnadu"
    cases, manifest = generate_all_cases(state)
    print(f"Generated {manifest['n_total_cases']} cases for state={state}:")
    print(f"  {manifest['n_regime_pcm_pairs']} regime x PCM pairs, "
          f"{manifest['n_lhs_per_pair']} LHS + 6 boundary cases each, "
          f"+ {manifest['n_baseline_cases']} no-PCM baselines")
    print(f"  seed base = {manifest['random_seed_base']}")
