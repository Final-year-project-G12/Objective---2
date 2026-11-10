"""
src/optimize/active_learning.py
==================================
The active-learning loop from her report's G8/S4: run NSGA-II on the
surrogate, simulate a small batch of the designs the surrogate is least
sure about, refit, repeat until the hypervolume stops moving.

STOPPING RULE (hers): "stop when HV moves < 1% for 2 rounds".

ACQUISITION -- WHERE OURS DIFFERS, AND WHY. Her loop picks designs by
COMMITTEE DISAGREEMENT across the three surrogates. We measured that
signal and it is badly calibrated: the NN ensemble's +/-2 sigma interval
covered only 32.8% of held-out truths where 95% is correct, i.e.
overconfident by about 3x (validate_surrogates.py). Driving sampling with
an uncertainty that wrong sends the batches to the wrong places.

The Gaussian process's posterior standard deviation covered 96.9% on the
same test, so that is what is used here instead -- the exact closed-form
posterior of the model that actually won the bake-off. Committee spread is
still COMPUTED and recorded alongside it, so the comparison stays visible
rather than being asserted away.

Batch selection is uncertainty-weighted but spread out: picking the top-k
by sigma alone collapses onto one neighbourhood, because high-uncertainty
regions are contiguous. Candidates are taken from the current Pareto front
and greedily chosen to maximise sigma while staying at least a minimum
normalised distance from already-chosen points -- the standard
diversity-constrained batch rule.

THE BOX-VERTEX STEP (her declared fix, G8 "box-vertex step"): her report
records that the loop initially converged to a front that missed the box
corners, and the fix was to simulate every box vertex before the final
rounds. That is done here too, as a first mandatory round: all 2^3 = 8
corners of (volume fraction, diameter, flow) per group. Corners that are
geometrically invalid are recorded as invalid, not silently skipped.
"""

from dataclasses import dataclass, field
from itertools import product

import numpy as np
import pandas as pd

from src.design.volume_fraction import design_from_fraction, achieved_fraction
from src.io_utils import load_design_bounds, load_system_config
from src.optimize.nsga2_search import search_group, SEARCH_VARS
from src.parallel.runner import SimTask, run_tasks_parallel
from src.surrogate.fit_per_pair import (FEATURES, ALL_TARGETS, fit_group,
                                        aggregate_over_years)

HV_TOL = 0.01          # "HV moves < 1%"
HV_PATIENCE = 2        # "... for 2 rounds"
BATCH_SIZE = 10        # her "10 designs/round"
MIN_BATCH_SEPARATION = 0.12   # normalised design-space distance within a batch


def _bounds_arrays():
    b = load_design_bounds()
    lo = np.array([b["pcm_volume_fraction"]["min"], b["capsule_diameter_m"]["min"],
                   b["flow_rate_kg_s"]["min"]], dtype=float)
    hi = np.array([b["pcm_volume_fraction"]["max"], b["capsule_diameter_m"]["max"],
                   b["flow_rate_kg_s"]["max"]], dtype=float)
    return lo, hi


def box_vertices() -> np.ndarray:
    """All 2^3 corners of the search box (the box-vertex step)."""
    lo, hi = _bounds_arrays()
    return np.array([[lo[0] if a else hi[0], lo[1] if b else hi[1], lo[2] if c else hi[2]]
                     for a, b, c in product([True, False], repeat=3)], dtype=float)


def _normalised(X):
    lo, hi = _bounds_arrays()
    return (np.asarray(X, dtype=float) - lo) / np.maximum(hi - lo, 1e-12)


def select_batch(candidates, sigma, k: int = BATCH_SIZE,
                  min_sep: float = MIN_BATCH_SEPARATION,
                  already=None) -> np.ndarray:
    """Greedy max-sigma selection with a diversity floor. Returns row
    indices into `candidates`."""
    candidates = np.atleast_2d(np.asarray(candidates, dtype=float))
    sigma = np.asarray(sigma, dtype=float)
    Cn = _normalised(candidates)
    chosen_pts = [] if already is None else list(_normalised(already))
    order = np.argsort(-np.nan_to_num(sigma, nan=-np.inf))
    picked = []
    for idx in order:
        if len(picked) >= k:
            break
        p = Cn[idx]
        if all(np.linalg.norm(p - q) >= min_sep for q in chosen_pts):
            picked.append(int(idx))
            chosen_pts.append(p)
    # If the diversity floor starved the batch, top up with the next-highest
    # sigma regardless of separation rather than returning a short batch.
    for idx in order:
        if len(picked) >= k:
            break
        if int(idx) not in picked:
            picked.append(int(idx))
    return np.array(picked, dtype=int)


def _tasks_for(X, cluster_id, pcm_name, arrangement, state, years,
                n_nodes, timestep_s, tag):
    sysconf = load_system_config()
    tasks = []
    for i, x in enumerate(X):
        for y in years:
            tasks.append(SimTask(
                task_id=f"{tag}_{i:03d}_y{y}", state=state, cluster_id=cluster_id,
                pcm_name=pcm_name, capsule_diameter_m=float(x[1]),
                pcm_volume_fraction=float(x[0]), flow_rate_kg_s=float(x[2]),
                arrangement=arrangement, model="multinode", n_nodes=n_nodes,
                timestep_s=timestep_s, year=y, paired_plain=True))
    return tasks


@dataclass
class ActiveLearningResult:
    cluster_id: int
    pcm_name: str
    arrangement: str
    rounds: list = field(default_factory=list)      # per-round diagnostics
    doe_rows: pd.DataFrame = None                    # every simulated row, DOE + all batches
    final_fit: object = None
    final_front: pd.DataFrame = None
    stopped_because: str = ""


def run_active_learning(group_doe_rows: pd.DataFrame, cluster_id, pcm_name, arrangement,
                         state: str = "tamilnadu", years=(2016,), n_nodes: int = 10,
                         timestep_s: float = 150.0, max_rounds: int = 8,
                         pop_size: int = 100, n_gen: int = 60, seed: int = 0,
                         ref_point=None, batch_size: int = BATCH_SIZE,
                         verbose: bool = True) -> ActiveLearningResult:
    rows = group_doe_rows.copy()
    res = ActiveLearningResult(cluster_id=cluster_id, pcm_name=pcm_name,
                                arrangement=arrangement)
    hv_hist = []
    n_quiet = 0

    for rnd in range(max_rounds + 1):
        agg = aggregate_over_years(rows)
        fit = fit_group(agg, cluster_id, pcm_name, arrangement)
        if not fit.models:
            res.stopped_because = "not enough valid designs to fit a surrogate"
            break

        search = search_group(fit, pop_size=pop_size, n_gen=n_gen, seed=seed,
                              ref_point=ref_point)
        hv = (search.hypervolume_history[-1]
              if search.hypervolume_history else float("nan"))
        hv_hist.append(hv)

        rel_move = float("inf")
        if len(hv_hist) >= 2 and np.isfinite(hv_hist[-2]) and hv_hist[-2] > 0:
            rel_move = abs(hv_hist[-1] - hv_hist[-2]) / hv_hist[-2]
            n_quiet = n_quiet + 1 if rel_move < HV_TOL else 0

        res.rounds.append({
            "round": rnd, "n_designs": fit.n_designs, "hypervolume": hv,
            "hv_rel_move": rel_move, "n_quiet_rounds": n_quiet,
            "front_size": len(search.X), "n_feasible": search.n_feasible,
            "winners": dict(fit.winners),
        })
        if verbose:
            print(f"    round {rnd}: n={fit.n_designs:4d} front={len(search.X):3d} "
                  f"HV={hv:.4g} move={rel_move if np.isfinite(rel_move) else float('nan'):.4f} "
                  f"quiet={n_quiet}", flush=True)

        if n_quiet >= HV_PATIENCE:
            res.stopped_because = f"hypervolume moved <{HV_TOL:.0%} for {HV_PATIENCE} rounds"
            res.final_fit, res.final_front = fit, search
            break
        if rnd == max_rounds:
            res.stopped_because = f"hit max_rounds={max_rounds}"
            res.final_fit, res.final_front = fit, search
            break

        # ---- pick the next batch -------------------------------------
        if rnd == 0:
            # Box-vertex step first, before any uncertainty-driven sampling.
            X_next, tag = box_vertices(), f"vertex_c{cluster_id}"
        else:
            cand = search.X
            sig = fit.predict_std(cand).get("g_window_kWh")
            if sig is None or not np.isfinite(sig).any():
                sig = np.ones(len(cand))
            idx = select_batch(cand, sig, k=batch_size,
                               already=rows[FEATURES].to_numpy(dtype=float))
            X_next, tag = cand[idx], f"al{rnd}_c{cluster_id}"

        tasks = _tasks_for(X_next, cluster_id, pcm_name, arrangement, state, years,
                           n_nodes, timestep_s, tag)
        new_rows = run_tasks_parallel(tasks, chunksize=2, label=f"AL r{rnd}")
        rows = pd.concat([rows, new_rows], ignore_index=True)

    res.doe_rows = rows
    return res
