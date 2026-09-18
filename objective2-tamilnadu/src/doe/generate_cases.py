"""
src/doe/generate_cases.py
============================
Phase 5 / D2.4 — reduced design-of-experiments sampling plan
(O2_Unified_PerState_Execution_Framework.md, "Phase 5 - Reduced DOE").

Produces a list of CASE SPECS (not yet simulated) — one dict per row:
    case_id, regime_id (cluster_id), pcm_id (name or None for the no-PCM
    baseline), capsule_diameter_m, n_capsule, flow_rate_kg_s,
    capsule_arrangement, sampling_method, seed.

src/doe/run_batch.py consumes this list and actually calls the Phase 3
simulator; this module only decides WHAT to simulate, never runs physics.

ARRANGEMENT STRATIFICATION (2026-09-17, adapted from
"a Rajasthan-pilot change plan (source removed from this project after adaptation, see docs_objective2/tamilnadu_phase_docs/)" for Tamil Nadu):
now that capsule arrangement is a searched variable (Phase 1-4), every
regime x PCM pair samples all three arrangements in roughly even numbers,
or Phase 6's surrogate would see "staggered" far more often than "radial"
and any arrangement comparison it makes would not be trustworthy.

Sampling plan per regime x shortlisted-PCM pair (per arrangement):
  - Latin Hypercube (scipy.stats.qmc) over (capsule_diameter_m,
    flow_rate_kg_s, capsule_count-as-continuous-then-rounded) —
    N_LHS_PER_PAIR_PER_ARRANGEMENT draws, one independent LHS realization
    per arrangement (distinct seed offset), not the same points relabeled.
  - Boundary cases: the REDUCED 4-corner set (dmin/dmax x fmin/fmax at
    mid-count) repeated once per arrangement -- chosen over the full
    6-corner x 3 set to keep the total case count in the framework's
    150-350 target band (see generate_all_cases docstring for the exact
    count decision); nmin/nmax boundary coverage is still obtained
    incidentally from Phase 2's own per-arrangement max-reachable-fraction
    sweep (docs_objective2 doc 02/17), not silently dropped.
  - One no-PCM baseline case per regime (pcm_id=None, arrangement="staggered"
    -- explicit, not an implicit default: a no-PCM design still runs through
    Phase 2's packing/passage check on its dummy geometry, so arrangement is
    a real field here too, just fixed to one value since it isn't the
    subject of this baseline).

Target total ~150-300 cases per state (framework doc §Phase 5), stated
sampling method and count are printed and returned in the manifest dict.
"""

import zlib
from dataclasses import dataclass, asdict

import numpy as np
from scipy.stats import qmc

from src.io_utils import load_state_config, load_design_bounds

RANDOM_SEED = 20260905   # fixed, documented seed for reproducibility
ARRANGEMENTS = ["single-layer", "staggered", "radial"]


def _stable_hash(text: str) -> int:
    """Deterministic, process-independent string hash for seed derivation.
    Python's built-in hash() is randomized per-process for strings (a
    security feature, PYTHONHASHSEED) -- using it here silently broke the
    "fixed seed" reproducibility claim (different PCM-name seeds, hence
    slightly different LHS draws, on every fresh process). crc32 is stable
    across processes, machines and Python versions."""
    return zlib.crc32(text.encode("utf-8"))


@dataclass
class CaseSpec:
    case_id: str
    regime_id: int
    pcm_id: object          # str or None (no-PCM baseline)
    capsule_diameter_m: float
    n_capsule: int
    flow_rate_kg_s: float
    capsule_arrangement: str
    sampling_method: str
    seed: int


def _lhs_cases(regime_id, pcm_id, n_samples, bounds, seed, prefix, arrangement):
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
            case_id=f"{prefix}_{arrangement}_lhs_{i:03d}",
            regime_id=regime_id, pcm_id=pcm_id,
            capsule_diameter_m=float(diam[i]), n_capsule=int(count[i]),
            flow_rate_kg_s=float(flow[i]), capsule_arrangement=arrangement,
            sampling_method="lhs", seed=seed,
        ))
    return cases


def _boundary_cases(regime_id, pcm_id, bounds, prefix, arrangement):
    """Reduced 4-corner set (dmin/dmax x fmin/fmax at mid-count) — see
    module docstring for why nmin/nmax boundary cases are not repeated
    here (kept as a single arrangement-agnostic check would have diluted
    the LHS budget; Phase 2's own per-arrangement max-reachable-fraction
    sweep already probes the count boundary per arrangement directly)."""
    d_bounds = bounds["capsule_diameter_m"]
    f_bounds = bounds["flow_rate_kg_s"]
    n_bounds = bounds["capsule_count"]
    mid_count = int(round((n_bounds["min"] + n_bounds["max"]) / 2))

    combos = []
    for d_label, d_val in [("dmin", d_bounds["min"]), ("dmax", d_bounds["max"])]:
        for f_label, f_val in [("fmin", f_bounds["min"]), ("fmax", f_bounds["max"])]:
            combos.append((d_label, d_val, f_label, f_val))

    cases = []
    for d_label, d_val, f_label, f_val in combos:
        cases.append(CaseSpec(
            case_id=f"{prefix}_{arrangement}_bnd_{d_label}_{f_label}",
            regime_id=regime_id, pcm_id=pcm_id,
            capsule_diameter_m=float(d_val), n_capsule=mid_count,
            flow_rate_kg_s=float(f_val), capsule_arrangement=arrangement,
            sampling_method="boundary", seed=0,
        ))
    return cases


def generate_all_cases(state: str, n_lhs_per_pair_per_arrangement: int = 4):
    """Returns (list_of_CaseSpec, manifest_dict).

    Case-count decision (documented, not silently picked -- adapted from
    "a Rajasthan-pilot change plan (source removed from this project after adaptation, see docs_objective2/tamilnadu_phase_docs/)" step 4): the
    REDUCED 4-boundary-corner variant is used (not the full 6-corner set),
    so with 9 regime x PCM pairs, 4 LHS draws x 3 arrangements = 12 LHS,
    and 4 boundary corners x 3 arrangements = 12 boundary per pair:
        9 x (12 + 12) + 3 baseline = 219 cases
    -- inside the framework's 150-350 target band, and keeps DOE runtime
    to a few minutes rather than the ~9 minutes the full 6-corner variant
    (273 cases) would take."""
    cfg = load_state_config(state)
    bounds = load_design_bounds()
    arrangements = bounds["capsule_arrangement"]["allowed"]

    all_cases = []
    n_pairs = 0
    for regime in cfg["regimes"]:
        cid = regime["cluster_id"]

        # one no-PCM baseline per regime — arrangement explicitly fixed to
        # "staggered" (documented choice, not an implicit default: see
        # module docstring).
        all_cases.append(CaseSpec(
            case_id=f"c{cid}_baseline_noPCM", regime_id=cid, pcm_id=None,
            capsule_diameter_m=bounds["capsule_diameter_m"]["max"],
            n_capsule=bounds["capsule_count"]["min"],
            flow_rate_kg_s=(bounds["flow_rate_kg_s"]["min"] + bounds["flow_rate_kg_s"]["max"]) / 2,
            capsule_arrangement="staggered",
            sampling_method="baseline", seed=0,
        ))

        for pcm_id in regime["pcm_shortlist"]:
            n_pairs += 1
            prefix = f"c{cid}_{_slug(pcm_id)}"
            base_seed = RANDOM_SEED + cid * 1000 + _stable_hash(pcm_id) % 1000
            for arr_idx, arrangement in enumerate(arrangements):
                seed = base_seed + arr_idx   # distinct LHS realization per arrangement
                all_cases += _lhs_cases(cid, pcm_id, n_lhs_per_pair_per_arrangement, bounds,
                                         seed, prefix, arrangement)
                all_cases += _boundary_cases(cid, pcm_id, bounds, prefix, arrangement)

    manifest = {
        "state": state, "random_seed_base": RANDOM_SEED,
        "n_regime_pcm_pairs": n_pairs,
        "n_lhs_per_pair_per_arrangement": n_lhs_per_pair_per_arrangement,
        "n_boundary_per_pair_per_arrangement": 4,
        "arrangements": arrangements,
        "n_baseline_cases": len(cfg["regimes"]),
        "n_total_cases": len(all_cases),
        "design_bounds_version": bounds.get("version"),
        "case_count_decision": "reduced 4-corner boundary set x 3 arrangements "
                                 "(not the full 6-corner set) -- see generate_all_cases docstring",
    }
    return all_cases, manifest


def _slug(name):
    return "".join(c if c.isalnum() else "_" for c in str(name))[:24]


if __name__ == "__main__":
    import sys
    state = sys.argv[1] if len(sys.argv) > 1 else "tamilnadu"
    cases, manifest = generate_all_cases(state)
    print(f"Generated {manifest['n_total_cases']} cases for state={state}:")
    print(f"  {manifest['n_regime_pcm_pairs']} regime x PCM pairs x {len(manifest['arrangements'])} arrangements, "
          f"{manifest['n_lhs_per_pair_per_arrangement']} LHS + "
          f"{manifest['n_boundary_per_pair_per_arrangement']} boundary cases each, "
          f"+ {manifest['n_baseline_cases']} no-PCM baselines")
    print(f"  seed base = {manifest['random_seed_base']}")
