"""
scripts/g8_s3_compare.py
===========================
G8 / S3 - surrogate selection on the S2 DOE, per (regime, O1 PCM) pair. Usage: python scripts/g8_s3_compare.py
Two validations, both WITHIN a pair (never pooled across regimes):
  designs  : 5-fold cross-validation over designs, target = the cheap-fidelity value (mean over the robust anchors)
  top_half : the same out-of-fold predictions scored only on the better half of the designs by simulated g_window, where ranking
             decides the search (rebuild 2026-11-23: replaces leave-one-year-out, which a one-year cheap DOE cannot support;
             year generalisation is tested by the cheap-vs-full check on the finalists, docs/REBUILD_COMMON100L.md section 3d)
Reported per (pair, target, family): RMSE, RMSE / (spread scale of that target), Spearman rho, and global R^2 (contrast only).
Families: nn_ensemble, xgboost, rsm_quadratic, gp_ard, stacked (plan R10).
Selection rule: highest mean Spearman over targets and validations, ties (within 0.02) broken by lower relative RMSE.
Writes results/g8_s3_comparison.csv and g8_s3_selection.csv.
"""

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.model_selection import KFold

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.optimize.surrogates import FAMILIES, TARGETS, feature_matrix



def metrics(y_true, y_pred, scale):
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    rho = float(spearmanr(y_true, y_pred)[0]) if np.ptp(y_true) > 0 else float("nan")
    ss_res, ss_tot = ((y_true - y_pred) ** 2).sum(), ((y_true - y_true.mean()) ** 2).sum()
    return rmse, rmse / scale if scale > 0 else float("nan"), rho, float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")


def run_pair(df, tag):
    ok = df[(df.status == "ok") & df.valid].reset_index(drop=True)
    X = feature_matrix(ok)
    Y = ok[list(TARGETS)].to_numpy(float)
    scale = {t: float(ok[t].std()) for t in TARGETS}               # one-year DOE: the design-to-design spread is the scale
    top = (ok["g_window"] >= ok["g_window"].median()).to_numpy()
    kf = KFold(5, shuffle=True, random_state=7)
    rows = []
    for fam, cls in FAMILIES.items():
        pred = np.zeros_like(Y)
        for tr, te in kf.split(X):
            pred[te] = cls().fit(X[tr], Y[tr]).predict(X[te])
        for j, t in enumerate(TARGETS):
            for val, mask in (("designs_5fold", np.ones(len(ok), bool)), ("top_half", top)):
                rmse, rel, rho, r2 = metrics(Y[mask, j], pred[mask, j], scale[t])
                rows.append({"pair": tag, "validation": val, "family": fam, "target": t, "n": int(mask.sum()),
                             "rmse": rmse, "rmse_over_spread": rel, "spearman": rho, "r2_global": r2})
        print(tag, fam, "done", flush=True)
    return pd.DataFrame(rows)


def _job(f):
    tag = Path(f).stem.replace("g8_s2_", "")
    df = pd.read_csv(f)
    if (df.status == "ok").sum() < 40:
        return None
    return run_pair(df, tag)


def main():
    from concurrent.futures import ProcessPoolExecutor
    files = sorted(f for f in glob.glob("results/g8_s2_r*_p*.csv") if not f.endswith(".partial.csv"))
    with ProcessPoolExecutor(max_workers=3) as ex:        # memory: never more than 3 (2026-11-14)
        out = [o for o in ex.map(_job, files) if o is not None]
    comp = pd.concat(out)
    comp.to_csv("results/g8_s3_comparison.csv", index=False)
    g = comp.groupby(["pair", "family"]).agg(spearman=("spearman", "mean"), rel_rmse=("rmse_over_spread", "mean")).reset_index()
    sel = []
    for pair, h in g.groupby("pair"):
        best = h.spearman.max()
        cand = h[h.spearman >= best - 0.02].sort_values("rel_rmse")
        sel.append({"pair": pair, "chosen": cand.iloc[0].family, **{r.family: r.spearman for r in h.itertuples()}})
    pd.DataFrame(sel).to_csv("results/g8_s3_selection.csv", index=False)
    print(pd.DataFrame(sel).to_string())


if __name__ == "__main__":
    main()
