"""
src/surrogate/fit_per_pair.py
================================
Fits one surrogate per (regime x PCM x arrangement) group per target, by
running the full bake-off from src/surrogate/model_zoo.py on that group's
Sobol DOE rows and keeping the winner.

PER-GROUP, NOT ONE GLOBAL MODEL. Rajasthan's report selects a winner per
regime x PCM pair rather than fitting one model across everything, and the
reason shows up in the data: the response surface's shape depends on which
PCM is in the capsules (its melting point relative to the tank's operating
band) and on the arrangement (which changes void fraction and therefore
both the water-side conductance and the pressure drop). A single global
model has to compromise between those surfaces; a per-group model does
not. The existing global ExtraTrees surrogate (src/surrogate/train.py) is
left untouched -- it is what the current validated Phase 6 output uses.

MULTI-YEAR AVERAGING. The DOE runs each design over several explore years.
A surrogate is fitted to the design's MEAN response across those years,
and the across-year standard deviation is kept per design as a measure of
weather-driven scatter. That scatter is what `rmse_over_sd` is compared
against: a surrogate whose error is already smaller than the year-to-year
spread of the thing it predicts cannot be usefully improved by more
training data, only by more years.

TARGETS. The objectives NSGA-II needs, plus the constraint quantity:
g_window_kWh, g_annual_kWh, d_overheat_h (objectives) and max_pcm_temp_C,
max_water_temp_C (safety constraints). Feasibility itself is NEVER
surrogated -- `check_design()` is exact and cheap, so geometric validity
is always evaluated directly, matching her report's "feasibility is never
learned by a surrogate".
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from src.surrogate.model_zoo import (KrigingGP, QuadraticRSM, NNEnsemble, GBTBaseline,
                                     bake_off, RANDOM_SEED)

FEATURES = ["pcm_volume_fraction", "capsule_diameter_m", "flow_rate_kg_s"]
OBJECTIVE_TARGETS = ["g_window_kWh", "g_annual_kWh", "d_overheat_h"]
CONSTRAINT_TARGETS = ["max_pcm_temp_C", "max_water_temp_C"]
ALL_TARGETS = OBJECTIVE_TARGETS + CONSTRAINT_TARGETS

GROUP_KEYS = ["cluster_id", "pcm_name", "arrangement"]

_FACTORY = {
    "kriging_gp": lambda seed: KrigingGP(seed=seed),
    "quadratic_rsm": lambda seed: QuadraticRSM(),
    "nn_ensemble": lambda seed: NNEnsemble(seed=seed),
    "xgboost_baseline": lambda seed: GBTBaseline(seed=seed),
}


def aggregate_over_years(doe_df: pd.DataFrame) -> pd.DataFrame:
    """One row per design per group: the mean of each target across the
    explore years, plus that target's across-year sd."""
    valid = doe_df[doe_df["valid"]].copy()
    design_keys = GROUP_KEYS + FEATURES
    agg = {t: ["mean", "std", "count"] for t in ALL_TARGETS if t in valid.columns}
    out = valid.groupby(design_keys, dropna=False).agg(agg)
    out.columns = [f"{t}_{how}" for t, how in out.columns]
    return out.reset_index()


@dataclass
class GroupFit:
    cluster_id: int
    pcm_name: str
    arrangement: str
    n_designs: int
    models: dict = field(default_factory=dict)        # target -> fitted surrogate
    winners: dict = field(default_factory=dict)       # target -> winning model name
    scores: list = field(default_factory=list)        # flat rows of every candidate's CV score
    year_sd: dict = field(default_factory=dict)       # target -> mean across-year sd

    def predict(self, X) -> dict:
        return {t: m.predict(X) for t, m in self.models.items()}

    def predict_std(self, X) -> dict:
        out = {}
        for t, m in self.models.items():
            try:
                out[t] = m.predict_std(X)
            except Exception:
                out[t] = np.full(len(np.asarray(X)), np.nan)
        return out


def fit_group(group_df: pd.DataFrame, cluster_id, pcm_name, arrangement,
               n_splits: int = 5, seed: int = RANDOM_SEED,
               targets=ALL_TARGETS) -> GroupFit:
    X = group_df[FEATURES].to_numpy(dtype=float)
    fit = GroupFit(cluster_id=cluster_id, pcm_name=pcm_name, arrangement=arrangement,
                    n_designs=len(group_df))

    for target in targets:
        col = f"{target}_mean"
        if col not in group_df.columns:
            continue
        y = group_df[col].to_numpy(dtype=float)
        keep = np.isfinite(y)
        if keep.sum() < max(8, n_splits):
            continue   # too few designs in this group to cross-validate honestly

        winner, scores = bake_off(X[keep], y[keep], n_splits=n_splits, seed=seed)
        fit.winners[target] = winner
        fit.models[target] = _FACTORY[winner](seed).fit(X[keep], y[keep])

        sd_col = f"{target}_std"
        fit.year_sd[target] = (float(np.nanmean(group_df[sd_col].to_numpy(dtype=float)))
                               if sd_col in group_df.columns else float("nan"))
        for s in scores:
            fit.scores.append({
                "cluster_id": cluster_id, "pcm_name": pcm_name, "arrangement": arrangement,
                "target": target, "model": s.model, "spearman": s.spearman,
                "rmse": s.rmse, "rmse_over_sd": s.rmse_over_sd, "r2": s.r2,
                "std_calibration": s.std_calibration, "fit_seconds": s.fit_seconds,
                "is_winner": s.model == winner,
                "year_sd": fit.year_sd[target],
                "rmse_over_year_sd": (s.rmse / fit.year_sd[target]
                                      if fit.year_sd.get(target, 0) else float("nan")),
            })
    return fit


def _fit_one(payload):
    """Worker entry point for parallel group fitting. Takes/returns plain
    data so it pickles cheaply; the fitted models are rebuilt in the
    parent from the winner name, because a fitted GP pickles to several MB
    and 27 of them crossing the process boundary costs more than refitting
    the winner once."""
    g, cid, pcm, arr, n_splits, seed, targets = payload
    fit = fit_group(g, cid, pcm, arr, n_splits=n_splits, seed=seed, targets=targets)
    return (cid, pcm, arr), fit.winners, fit.scores, fit.year_sd, fit.n_designs


def fit_all_groups(doe_df: pd.DataFrame, n_splits: int = 5, seed: int = RANDOM_SEED,
                    targets=ALL_TARGETS, verbose: bool = True, n_workers: int = None):
    """Fits every group. Groups are independent, so they are fanned out
    across processes -- the bake-off is the expensive part (a GP 5-fold CV
    is ~9 s and an NN-ensemble CV ~24 s, times 5 targets times 27 groups,
    which is over an hour serially)."""
    import os
    from concurrent.futures import ProcessPoolExecutor

    agg = aggregate_over_years(doe_df)
    groups = list(agg.groupby(GROUP_KEYS, dropna=False))
    payloads = [(g, cid, pcm, arr, n_splits, seed, targets)
                for (cid, pcm, arr), g in groups]

    n_workers = n_workers or max(1, (os.cpu_count() or 2) - 1)
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ.setdefault(var, "1")   # one BLAS thread per worker, not 12

    fits, score_rows = {}, []
    with ProcessPoolExecutor(max_workers=min(n_workers, len(payloads))) as pool:
        for key, winners, scores, year_sd, n_designs in pool.map(_fit_one, payloads):
            cid, pcm, arr = key
            score_rows.extend(scores)
            # Refit the winner only, in-process, so the caller gets usable
            # models without shipping fitted estimators between processes.
            g = agg[(agg["cluster_id"] == cid) & (agg["pcm_name"] == pcm)
                    & (agg["arrangement"] == arr)]
            X = g[FEATURES].to_numpy(dtype=float)
            fit = GroupFit(cluster_id=cid, pcm_name=pcm, arrangement=arr,
                            n_designs=n_designs, winners=dict(winners),
                            scores=scores, year_sd=dict(year_sd))
            for target, model_name in winners.items():
                y = g[f"{target}_mean"].to_numpy(dtype=float)
                keep = np.isfinite(y)
                fit.models[target] = _FACTORY[model_name](seed).fit(X[keep], y[keep])
            fits[key] = fit
            if verbose:
                won = ", ".join(f"{t}:{m}" for t, m in winners.items())
                print(f"  c{cid} {pcm:22s} {arr:13s} n={n_designs:4d}  {won}", flush=True)

    return fits, pd.DataFrame(score_rows)
