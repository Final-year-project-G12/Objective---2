"""
scripts/c11_l5_surrogates.py   (level L5, step O2-9)
======================================================
Surrogate bake-off on the NEW labelled DOE (c9), per (regime, O1 PCM) pair - no old winner is carried over. Families: RSM quadratic, XGBoost,
NN ensemble, GP-ARD, stacked. Inputs: R_in [mm], PCM fraction, one-hot arrangement (flow is frozen, anchor is inside the targets).
Targets: g_window_mean (robust ranking value), g_window_worst, d_overheat_mean, t_pcm_max_mean. 5-fold CV over designs, within the pair.
Reported: RMSE, RMSE / spread of the target, Spearman (rank agreement, the selection criterion), R^2 for contrast only.
Selection: highest mean Spearman, ties within 0.02 broken by lower relative RMSE. Surrogates only PROPOSE; the simulator makes every number.
Usage: python scripts/c11_l5_surrogates.py  -> results/c11_l5_surrogate_comparison.csv, c11_l5_surrogate_selection.csv
"""
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.model_selection import KFold

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.optimize.surrogates import FAMILIES, ARR           # noqa: E402

TARGETS = ("g_window_mean", "g_window_worst", "d_overheat_mean", "t_pcm_max_mean")


def feats(df):
    return np.column_stack([df.R_in_m * 1000.0, df.fraction] + [(df.arrangement == a).astype(float) for a in ARR])


def run_pair(f):
    tag = Path(f).stem.replace("c9_l5_doe_", "")
    df = pd.read_csv(f)
    ok = df[df.valid.astype(str) == "True"].reset_index(drop=True)
    X, Y = feats(ok), ok[list(TARGETS)].to_numpy(float)
    spread = Y.std(axis=0)
    rows = []
    for fam, cls in FAMILIES.items():
        pred = np.zeros_like(Y)
        for tr, te in KFold(5, shuffle=True, random_state=7).split(X):
            pred[te] = cls().fit(X[tr], Y[tr]).predict(X[te])
        for j, t in enumerate(TARGETS):
            rmse = float(np.sqrt(np.mean((Y[:, j] - pred[:, j]) ** 2)))
            ss = ((Y[:, j] - Y[:, j].mean()) ** 2).sum()
            rows.append({"pair": tag, "family": fam, "target": t, "n": len(ok), "rmse": rmse, "rmse_over_spread": rmse / spread[j] if spread[j] > 0 else np.nan,
                         "spearman": float(spearmanr(Y[:, j], pred[:, j])[0]), "r2_global": float(1 - ((Y[:, j] - pred[:, j]) ** 2).sum() / ss) if ss > 0 else np.nan})
        print(tag, fam, "done", flush=True)
    return pd.DataFrame(rows)


def main():
    from concurrent.futures import ProcessPoolExecutor
    files = sorted(glob.glob("results/c9_l5_doe_r*_p*.csv"))
    with ProcessPoolExecutor(max_workers=3) as ex:
        comp = pd.concat(list(ex.map(run_pair, files)))
    comp.to_csv("results/c11_l5_surrogate_comparison.csv", index=False)
    g = comp.groupby(["pair", "family"]).agg(spearman=("spearman", "mean"), rel=("rmse_over_spread", "mean")).reset_index()
    sel = []
    for pair, h in g.groupby("pair"):
        cand = h[h.spearman >= h.spearman.max() - 0.02].sort_values("rel")
        sel.append({"pair": pair, "chosen": cand.iloc[0].family, **{r.family: round(r.spearman, 3) for r in h.itertuples()}})
    s = pd.DataFrame(sel)
    s.to_csv("results/c11_l5_surrogate_selection.csv", index=False)
    print(s.to_string())


if __name__ == "__main__":
    main()
