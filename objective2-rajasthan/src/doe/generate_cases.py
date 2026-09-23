"""
src/doe/generate_cases.py
============================
Phase 5 / D2.4 — reduced design-of-experiments sampling plan
(O2_Unified_PerState_Execution_Framework.md, "Phase 5 - Reduced DOE").

Produces a list of CASE SPECS (not yet simulated) — one dict per row:
    case_id, regime_id (cluster_id), pcm_id (name or None for the no-PCM
    baseline), capsule_diameter_m, n_capsule, flow_rate_kg_s, arrangement,
    sampling_method, seed.

src/doe/run_batch.py consumes this list and actually calls the Phase 3
simulator; this module only decides WHAT to simulate, never runs physics.

Sampling plan per regime x shortlisted-PCM pair (arrangement-stratified
since 2026-09-17, docs/05_PROMPT_PHASE5_DOE.md — arrangement was restored
as a searched variable in Phase 1/2 and every arrangement must be
represented in roughly even numbers or Phase 6's surrogate can't compare
them fairly):
  - Latin Hypercube (scipy.stats.qmc) over (capsule_diameter_m,
    flow_rate_kg_s, capsule_count-as-continuous-then-rounded): split into
    3 groups of 4 draws, one group per arrangement, same sampler and same
    fixed seed base (20260905) re-run three times per pair with
    arrangement held fixed within each group.
  - Boundary cases: 4 corners ({min,max} diameter x {min,max} flow) at the
    mid-range capsule count, run once per arrangement (12 per pair). Per
    the framework's 150-350 total-case target band, this drops the
    nmin/nmax corners (kept pre-2026-09-17) to hold the new arrangement-
    stratified total closer to the old order of magnitude — see the case-
    count decision in generate_all_cases()'s docstring below.
  - One no-PCM baseline case per regime (pcm_id=None, arrangement doesn't
    apply to a PCM-less config but the schema field is still required —
    passed explicitly as "staggered", a documented sentinel, not an
    implicit default).

Target total ~150-350 cases per state (framework doc §Phase 5), stated
sampling method and count are printed and returned in the manifest dict.
"""

import zlib
from dataclasses import dataclass, asdict

import numpy as np
from scipy.stats import qmc

from src.io_utils import load_state_config, load_design_bounds

RANDOM_SEED = 20260905   # fixed, documented seed for reproducibility
ARRANGEMENTS = ("single-layer", "staggered", "radial")
BASELINE_ARRANGEMENT_SENTINEL = "staggered"   # no-PCM baseline: arrangement doesn't apply,
                                                # but the schema field is required — documented
                                                # sentinel, not an implicit/accidental default.


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
    arrangement: str
    sampling_method: str
    seed: int


def _lhs_cases(regime_id, pcm_id, n_samples_per_arrangement, bounds, seed_base, prefix):
    d_bounds = bounds["capsule_diameter_m"]
    f_bounds = bounds["flow_rate_kg_s"]
    n_bounds = bounds["capsule_count"]

    cases = []
    for arr_i, arrangement in enumerate(ARRANGEMENTS):
        # Same LHS sampler, same seed base per arrangement group (arr_i
        # offsets the seed deterministically so the three groups draw
        # different-but-reproducible points, not the same 4 points thrice).
        seed = seed_base + arr_i
        sampler = qmc.LatinHypercube(d=3, seed=seed)
        unit = sampler.random(n=n_samples_per_arrangement)   # shape (n, 3) in [0,1)

        diam = qmc.scale(unit[:, [0]], [d_bounds["min"]], [d_bounds["max"]]).ravel()
        flow = qmc.scale(unit[:, [1]], [f_bounds["min"]], [f_bounds["max"]]).ravel()
        count_cont = qmc.scale(unit[:, [2]], [n_bounds["min"]], [n_bounds["max"]]).ravel()
        count = np.clip(np.round(count_cont), n_bounds["min"], n_bounds["max"]).astype(int)

        for i in range(n_samples_per_arrangement):
            cases.append(CaseSpec(
                case_id=f"{prefix}_lhs_{_arr_slug(arrangement)}_{i:03d}",
                regime_id=regime_id, pcm_id=pcm_id,
                capsule_diameter_m=float(diam[i]), n_capsule=int(count[i]),
                flow_rate_kg_s=float(flow[i]), arrangement=arrangement,
                sampling_method="lhs", seed=seed,
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
    for arrangement in ARRANGEMENTS:
        for d_label, d_val, f_label, f_val in combos:
            cases.append(CaseSpec(
                case_id=f"{prefix}_bnd_{_arr_slug(arrangement)}_{d_label}_{f_label}",
                regime_id=regime_id, pcm_id=pcm_id,
                capsule_diameter_m=float(d_val), n_capsule=mid_count,
                flow_rate_kg_s=float(f_val), arrangement=arrangement,
                sampling_method="boundary", seed=0,
            ))
    return cases


def generate_all_cases(state: str, n_lhs_per_pair: int = 12):
    """Returns (list_of_CaseSpec, manifest_dict).

    n_lhs_per_pair is split evenly across the 3 arrangements (4 each at the
    default of 12) by _lhs_cases(). Boundary cases are the 4
    diameter x flow corners, run once per arrangement (12 per pair) —
    nmin/nmax corners were dropped in the 2026-09-17 arrangement-restore
    change to keep the arrangement-stratified total inside the framework's
    150-350 case-count target band without a 3x case-count blowup:
    9 pairs x (12 LHS + 12 boundary) + 3 baseline = 219 cases (up from the
    pre-restore 165; the alternative — keeping all 6 boundary corners per
    arrangement — would have given 9x(12+18)+3=273, still in-band but a
    larger jump). This decision is stated here, not silently applied."""
    cfg = load_state_config(state)
    bounds = load_design_bounds()

    all_cases = []
    n_pairs = 0
    for regime in cfg["regimes"]:
        cid = regime["cluster_id"]

        # one no-PCM baseline per regime — arrangement doesn't apply, but
        # the schema field is required, so pass the documented sentinel.
        all_cases.append(CaseSpec(
            case_id=f"c{cid}_baseline_noPCM", regime_id=cid, pcm_id=None,
            capsule_diameter_m=bounds["capsule_diameter_m"]["max"],
            n_capsule=bounds["capsule_count"]["min"],
            flow_rate_kg_s=(bounds["flow_rate_kg_s"]["min"] + bounds["flow_rate_kg_s"]["max"]) / 2,
            arrangement=BASELINE_ARRANGEMENT_SENTINEL,
            sampling_method="baseline", seed=0,
        ))

        for pcm_id in regime["pcm_shortlist"]:
            n_pairs += 1
            prefix = f"c{cid}_{_slug(pcm_id)}"
            seed = RANDOM_SEED + cid * 1000 + _stable_hash(pcm_id) % 1000
            n_lhs_per_arrangement = max(1, n_lhs_per_pair // len(ARRANGEMENTS))
            all_cases += _lhs_cases(cid, pcm_id, n_lhs_per_arrangement, bounds, seed, prefix)
            all_cases += _boundary_cases(cid, pcm_id, bounds, prefix)

    manifest = {
        "state": state, "random_seed_base": RANDOM_SEED,
        "n_regime_pcm_pairs": n_pairs, "n_lhs_per_pair": n_lhs_per_pair,
        "n_boundary_per_pair": 4 * len(ARRANGEMENTS), "n_baseline_cases": len(cfg["regimes"]),
        "n_total_cases": len(all_cases),
        "design_bounds_version": bounds.get("version"),
        "arrangements": list(ARRANGEMENTS),
        "case_count_decision": ("2026-09-17: dropped nmin/nmax boundary corners per arrangement "
                                 "(4 corners x 3 arrangements = 12/pair, not 6x3=18/pair) to keep "
                                 "the arrangement-stratified total (219) inside the 150-350 target "
                                 "band without a full 3x blowup from the pre-restore 165 total; see "
                                 "docs/05_PROMPT_PHASE5_DOE.md step 4."),
    }
    return all_cases, manifest


def _slug(name):
    return "".join(c if c.isalnum() else "_" for c in str(name))[:24]


def _arr_slug(arrangement):
    return arrangement.replace("-", "")


if __name__ == "__main__":
    import sys
    state = sys.argv[1] if len(sys.argv) > 1 else "rajasthan"
    cases, manifest = generate_all_cases(state)
    print(f"Generated {manifest['n_total_cases']} cases for state={state}:")
    print(f"  {manifest['n_regime_pcm_pairs']} regime x PCM pairs, "
          f"{manifest['n_lhs_per_pair']} LHS + {manifest['n_boundary_per_pair']} boundary cases each, "
          f"+ {manifest['n_baseline_cases']} no-PCM baselines")
    print(f"  seed base = {manifest['random_seed_base']}")
    print(f"  case count decision: {manifest['case_count_decision']}")
