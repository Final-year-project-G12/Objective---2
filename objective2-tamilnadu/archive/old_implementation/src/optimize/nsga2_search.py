"""
src/optimize/nsga2_search.py
===============================
Runs NSGA-II (src/optimize/nsga2.py) over a fitted per-group surrogate
(src/surrogate/fit_per_pair.py) to produce a Pareto front of candidate
designs per regime x PCM x arrangement group.

OBJECTIVES (her report's section 3.5 / Table 30 set, minimization form):
    f1 = -g_window_kWh     (primary: extra energy delivered at 45 C in the
                            18:00-09:00 window vs. the paired water-only tank)
    f2 = -g_annual_kWh     (the same gain over the whole year)
    f3 =  d_overheat_h     (shield hours of the PCM tank minus the water-only
                            tank's water-side hours -- fewer is better)

CONSTRAINTS (her "Hard constraints ... PCM peak at most 65 C, water peak at
most 75 C", expressed as a single non-negative violation that NSGA-II's
constrained domination consumes):
    g = max(0, PCM_peak - 65) + max(0, water_peak - 75) + geometry_penalty

WHY THE SEARCH RUNS ON THE SURROGATE AND NOT THE SIMULATOR. A single
NSGA-II run at pop=100 x 100 generations is 20,000 evaluations. Done on the
simulator, paired and averaged over 5 explore years, that is 200,000
simulated years PER GROUP -- about 28 hours per group even at 0.5 s/year,
times 27 groups. Rajasthan's pipeline does not do that either: the
surrogate proposes, and the simulator confirms. The expensive simulator
calls are spent where they buy information -- the Sobol DOE and the
active-learning rounds (src/optimize/active_learning.py) -- and every
design that ends up reported is re-simulated for real.

FEASIBILITY IS NEVER SURROGATED. `check_design()` is exact and cheap, so
geometric validity is evaluated directly for every individual and an
invalid design gets a large constraint violation rather than a predicted
one. This matches her report: "Every design passes an exact geometry check
... before it is simulated; feasibility is never learned by a surrogate."

ARRANGEMENT is not encoded as a continuous variable to be rounded. It is a
genuine categorical with three levels, and each level gets its own
surrogate group and its own NSGA-II run; the arrangement comparison is
then made BETWEEN fronts, which is both cleaner and what makes an
arrangement claim defensible.
"""

from dataclasses import dataclass

import numpy as np

from src.design.constraints import check_design
from src.design.volume_fraction import design_from_fraction, achieved_fraction
from src.io_utils import load_system_config, load_design_bounds
from src.optimize.nsga2 import run_nsga2

SEARCH_VARS = ["pcm_volume_fraction", "capsule_diameter_m", "flow_rate_kg_s"]
PCM_PEAK_LIMIT_C = 65.0
WATER_PEAK_LIMIT_C = 75.0
GEOMETRY_PENALTY = 1.0e3     # dominates any physical violation, so invalid
                              # designs are ordered behind every valid one


@dataclass
class SearchResult:
    cluster_id: int
    pcm_name: str
    arrangement: str
    X: np.ndarray            # front design rows, in SEARCH_VARS order
    F: np.ndarray            # front objective rows (minimization form)
    G: np.ndarray            # front constraint violations
    n_capsule: np.ndarray    # derived integer counts for the front
    achieved_fraction: np.ndarray
    hypervolume_history: list
    n_feasible: int
    n_evaluated: int


def _bounds_arrays(design_bounds=None):
    b = design_bounds or load_design_bounds()
    lo = np.array([b["pcm_volume_fraction"]["min"], b["capsule_diameter_m"]["min"],
                   b["flow_rate_kg_s"]["min"]], dtype=float)
    hi = np.array([b["pcm_volume_fraction"]["max"], b["capsule_diameter_m"]["max"],
                   b["flow_rate_kg_s"]["max"]], dtype=float)
    return lo, hi


def make_evaluator(group_fit, arrangement: str, system_config=None, design_bounds=None):
    """Returns evaluate_fn(X) -> (F, G) for run_nsga2.

    Evaluated for the WHOLE population in one call, which is what lets the
    surrogate predictions be vectorized (and what would let a simulator
    backend be fanned out across processes instead).
    """
    system_config = system_config or load_system_config()
    design_bounds = design_bounds or load_design_bounds()

    def evaluate_fn(X):
        X = np.atleast_2d(np.asarray(X, dtype=float))
        n = len(X)

        preds = group_fit.predict(X)
        g_window = preds.get("g_window_kWh", np.zeros(n))
        g_annual = preds.get("g_annual_kWh", np.zeros(n))
        d_over = preds.get("d_overheat_h", np.zeros(n))
        pcm_peak = preds.get("max_pcm_temp_C", np.zeros(n))
        water_peak = preds.get("max_water_temp_C", np.zeros(n))

        F = np.stack([-g_window, -g_annual, d_over], axis=1)

        viol = (np.clip(pcm_peak - PCM_PEAK_LIMIT_C, 0.0, None)
                + np.clip(water_peak - WATER_PEAK_LIMIT_C, 0.0, None))

        # Exact geometry check per individual -- never surrogated.
        for i in range(n):
            frac, diam, flow = X[i, 0], X[i, 1], X[i, 2]
            design = design_from_fraction(frac, diam, flow, arrangement, system_config)
            geom = check_design(design, system_config, design_bounds)
            if not geom["valid"]:
                viol[i] += GEOMETRY_PENALTY

        return F, viol

    return evaluate_fn


def search_group(group_fit, pop_size: int = 100, n_gen: int = 100, seed: int = 0,
                  system_config=None, design_bounds=None,
                  ref_point=None) -> SearchResult:
    system_config = system_config or load_system_config()
    design_bounds = design_bounds or load_design_bounds()
    lo, hi = _bounds_arrays(design_bounds)

    evaluate_fn = make_evaluator(group_fit, group_fit.arrangement,
                                 system_config, design_bounds)
    res = run_nsga2(evaluate_fn, lo, hi, pop_size=pop_size, n_gen=n_gen, seed=seed,
                    ref_point=ref_point, track_hypervolume=ref_point is not None)

    front = res.fronts[0]
    Xf, Ff, Gf = res.X[front], res.F[front], res.G[front]
    counts = np.array([
        design_from_fraction(x[0], x[1], x[2], group_fit.arrangement, system_config).n_capsule
        for x in Xf], dtype=int)
    fracs = np.array([achieved_fraction(c, x[1], system_config)
                      for c, x in zip(counts, Xf)], dtype=float)

    return SearchResult(
        cluster_id=group_fit.cluster_id, pcm_name=group_fit.pcm_name,
        arrangement=group_fit.arrangement, X=Xf, F=Ff, G=Gf,
        n_capsule=counts, achieved_fraction=fracs,
        hypervolume_history=res.history_hypervolume,
        n_feasible=int(np.sum(res.G <= 0)), n_evaluated=len(res.X),
    )


def front_to_frame(result: SearchResult):
    import pandas as pd
    return pd.DataFrame({
        "cluster_id": result.cluster_id,
        "pcm_name": result.pcm_name,
        "arrangement": result.arrangement,
        "pcm_volume_fraction_requested": result.X[:, 0],
        "pcm_volume_fraction": result.achieved_fraction,
        "capsule_diameter_m": result.X[:, 1],
        "flow_rate_kg_s": result.X[:, 2],
        "n_capsule": result.n_capsule,
        # back to natural sign/orientation for reading
        "g_window_kWh_pred": -result.F[:, 0],
        "g_annual_kWh_pred": -result.F[:, 1],
        "d_overheat_h_pred": result.F[:, 2],
        "constraint_violation": result.G,
    })
