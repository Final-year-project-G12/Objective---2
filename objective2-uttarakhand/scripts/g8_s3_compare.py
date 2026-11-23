"""
scripts/g8_s3_compare.py
===========================
G8 / S3 - surrogate selection on the S2 DOE, per (regime, O1 PCM) pair. Usage: python scripts/g8_s3_compare.py
Two validations, both WITHIN a pair (never pooled across regimes, which is what inflated R^2 before):
  designs : 5-fold cross-validation over designs, target = mean over the 5 explore years
  years   : leave-one-year-out x design folds -- train on designs of 4 years' mean, test on held-out designs'
            gain in the left-out year (generalisation to an unseen weather year)
Reported per (pair, target, family): RMSE, RMSE / (mean year-to-year sd of that target = the repeatability scale),
Spearman rho of predicted vs simulated ranking, and global R^2 (for contrast only; NOT used to choose).
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

YEARS = (2016, 2017, 2018, 2019, 2020)


def metrics(y_true, y_pred, scale):
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    rho = float(spearmanr(y_true, y_pred)[0]) if np.ptp(y_true) > 0 else float("nan")
    ss_res, ss_tot = ((y_true - y_pred) ** 2).sum(), ((y_true - y_true.mean()) ** 2).sum()
    return rmse, rmse / scale if scale > 0 else float("nan"), rho, float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")


def run_pair(df, tag):
    ok = df[(df.status == "ok") & df.valid].reset_index(drop=True)
    X = feature_matrix(ok)
    Ymean = ok[list(TARGETS)].to_numpy(float)
    scale = {t: float(ok[t + "_sd"].mean()) if t + "_sd" in ok else float(ok[[f"{t}_{y}" for y in YEARS]].std(axis=1).mean())
             for t in TARGETS}
    kf = KFold(5, shuffle=True, random_state=7)
    rows = []
    for fam, cls in FAMILIES.items():
        # --- design folds
        pred = np.zeros_like(Ymean)
        for tr, te in kf.split(X):
            pred[te] = cls().fit(X[tr], Ymean[tr]).predict(X[te])
        for j, t in enumerate(TARGETS):
            rmse, rel, rho, r2 = metrics(Ymean[:, j], pred[:, j], scale[t])
            rows.append({"pair": tag, "validation": "designs_5fold", "family": fam, "target": t, "n": len(ok),
                         "rmse": rmse, "rmse_over_year_sd": rel, "spearman": rho, "r2_global": r2})
        # --- leave-one-year-out (unseen weather year, unseen designs): one multi-target fit per (year, fold)
        y_all = {t: np.column_stack([ok[f"{t}_{y}"].to_numpy(float) for y in YEARS]) for t in TARGETS}
        res = {t: [] for t in TARGETS}
        for yi, y in enumerate(YEARS):
            Ytrain = np.column_stack([np.delete(y_all[t], yi, axis=1).mean(axis=1) for t in TARGETS])
            P = np.zeros((len(ok), len(TARGETS)))
            for tr, te in kf.split(X):
                P[te] = cls().fit(X[tr], Ytrain[tr]).predict(X[te])
            for j, t in enumerate(TARGETS):
                res[t].append(metrics(y_all[t][:, yi], P[:, j], scale[t]))
        for t in TARGETS:
            a = np.nanmean(np.array(res[t]), axis=0)
            rows.append({"pair": tag, "validation": "leave_one_year_out", "family": fam, "target": t, "n": len(ok),
                         "rmse": a[0], "rmse_over_year_sd": a[1], "spearman": a[2], "r2_global": a[3]})
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
    files = sorted(glob.glob("results/g8_s2_r*_p*.csv"))
    with ProcessPoolExecutor(max_workers=9) as ex:
        out = [o for o in ex.map(_job, files) if o is not None]
    comp = pd.concat(out)
    comp.to_csv("results/g8_s3_comparison.csv", index=False)
    g = comp.groupby(["pair", "family"]).agg(spearman=("spearman", "mean"), rel_rmse=("rmse_over_year_sd", "mean")).reset_index()
    sel = []
    for pair, h in g.groupby("pair"):
        best = h.spearman.max()
        cand = h[h.spearman >= best - 0.02].sort_values("rel_rmse")
        sel.append({"pair": pair, "chosen": cand.iloc[0].family, **{r.family: r.spearman for r in h.itertuples()}})
    pd.DataFrame(sel).to_csv("results/g8_s3_selection.csv", index=False)
    print(pd.DataFrame(sel).to_string())


if __name__ == "__main__":
    main()
