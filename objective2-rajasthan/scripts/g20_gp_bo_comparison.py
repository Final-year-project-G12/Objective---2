"""
scripts/g20_gp_bo_comparison.py
==================================
Plan option C (WP5, comparison only): Gaussian-process Bayesian optimisation of the single objective g_window for the rank-1 O1 PCM of a regime,
on the explore years 2016-2020, using the real simulator (src/optimize/evaluate.evaluate_design). It is a COMPARISON for the NSGA-II chain, not a
replacement: the NSGA-II / dense-grid designs are not changed and no select or test year is touched.

Method: scrambled-Sobol start (n_init), then n_iter rounds of expected improvement on a Matern-5/2 GP (scikit-learn) over
x = (R_in, PCM fraction, flow, arrangement index); each round picks the best of a random pool of 4000 points. Infeasible designs
(geometry rejected, or PCM peak above 65 C / water peak above 75 C) are recorded and given the worst feasible value seen so far minus a penalty, so the GP
learns to avoid them. The arrangement is one integer dimension (0 single-layer, 1 staggered, 2 radial), a simplification noted in the output.

Output: results/g20_gpbo_r<c>_p<rank>.csv (every evaluated design) and a printed comparison with the NSGA-II chosen design's explore-year value
(results/g10_selection_r<c>.json, key explore_g_window).

Usage: python scripts/g20_gp_bo_comparison.py <cluster_id> [pcm_rank=1] [n_init=20] [n_iter=40] [seed=20261028]
"""

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, qmc
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.design.space import load_space
from src.io_utils import get_regime
from src.optimize.evaluate import evaluate_design

OUT = Path("results")
ARR = ["single-layer", "staggered", "radial"]
SP = load_space()["variables"]
LO = np.array([SP["inner_radius_m"]["min"], SP["pcm_volume_fraction"]["min"], SP["flow_rate_kg_s"]["min"], 0.0])
HI = np.array([SP["inner_radius_m"]["max"], SP["pcm_volume_fraction"]["max"], SP["flow_rate_kg_s"]["max"], 3.0 - 1e-9])


def decode(u):
    x = LO + np.asarray(u) * (HI - LO)
    return float(x[0]), float(x[1]), float(x[2]), ARR[int(x[3])]


def run(cid, pcm, u):
    r, f, q, a = decode(u)
    res = evaluate_design(cid, pcm, r, f, q, a, purpose="explore")
    ok = bool(res.get("valid")) and bool(res.get("feasible"))
    return {"R_in_m": r, "fraction_req": f, "flow": q, "arrangement": a, "N": res.get("N"), "valid": res.get("valid"),
            "feasible": ok, "g_window": res.get("g_window") if ok else np.nan, "g_annual": res.get("g_annual"),
            "d_overheat": res.get("d_overheat"), "t_pcm_max": res.get("t_pcm_max")}


def expected_improvement(mu, sd, best):
    sd = np.maximum(sd, 1e-9)
    z = (mu - best) / sd
    return (mu - best) * norm.cdf(z) + sd * norm.pdf(z)


def main(cid, rank=1, n_init=20, n_iter=40, seed=20261028):
    pcm = get_regime("rajasthan", cid)["pcm_shortlist"][rank - 1]
    rng = np.random.default_rng(seed)
    U = qmc.Sobol(d=4, scramble=True, seed=seed).random(n_init)
    rows = [run(cid, pcm, u) for u in U]
    for i, r in enumerate(rows):
        print(f"init {i:3d} feasible={r['feasible']} g_window={r['g_window']}", flush=True)
    kernel = ConstantKernel(1.0) * Matern(length_scale=np.ones(4) * 0.5, nu=2.5) + WhiteKernel(1e-3)
    for it in range(n_iter):
        feas = [r["g_window"] for r in rows if r["feasible"]]
        worst = min(feas) if feas else 0.0
        y = np.array([r["g_window"] if r["feasible"] else worst - 20.0 for r in rows])
        ym, ys = y.mean(), max(y.std(), 1e-6)
        gp = GaussianProcessRegressor(kernel=kernel, normalize_y=False, n_restarts_optimizer=2, random_state=seed)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            gp.fit(U, (y - ym) / ys)
        pool = rng.random((4000, 4))
        mu, sd = gp.predict(pool, return_std=True)
        best = ((max(feas) if feas else worst) - ym) / ys
        u = pool[int(np.argmax(expected_improvement(mu, sd, best)))]
        U = np.vstack([U, u])
        rows.append(run(cid, pcm, u))
        print(f"iter {it:3d} feasible={rows[-1]['feasible']} g_window={rows[-1]['g_window']} best={np.nanmax([r['g_window'] for r in rows])}", flush=True)
        pd.DataFrame(rows).to_csv(OUT / f"g20_gpbo_r{cid}_p{rank}.csv", index=False)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / f"g20_gpbo_r{cid}_p{rank}.csv", index=False)
    b = df.loc[df.g_window.idxmax()]
    sel = json.load(open(OUT / f"g10_selection_r{cid}.json", encoding="utf-8"))["chosen"]
    print(f"\nregime {cid} / {pcm}: {len(df)} simulator designs ({n_init} Sobol + {n_iter} GP rounds)")
    print(f"  GP-BO best explore g_window = {b.g_window:.1f} kWh  (R {b.R_in_m*1000:.1f} mm, fraction {b.fraction_req:.3f}, flow {b.flow:.4f}, {b.arrangement})")
    print(f"  NSGA-II chosen design, explore years = {sel['explore_g_window']:.1f} kWh  (PCM {sel['pcm']})")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(int(a[0]), *(int(x) for x in a[1:4]), *( [int(a[4])] if len(a) > 4 else []))
