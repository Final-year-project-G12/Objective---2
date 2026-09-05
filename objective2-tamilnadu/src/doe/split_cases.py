"""
src/doe/split_cases.py
=========================
Phase 5 / D2.4 — case-level train/hold-out split (framework doc's reduced
spec: "Split by whole case_id into 80/20 train/hold-out"). Since every row
in design_cases.parquet is already one complete simulation case (not a
timestep), a random 80/20 split over ROWS is automatically leakage-free —
there is no shared design/weather trajectory between rows to leak.

Stratified by (regime_id, pcm_id, valid) so every regime x PCM pair has
hold-out coverage, not just the pairs that happened to get more LHS draws
-- and so that INVALID cases also get a holdout share. That last point
matters: the performance regressors only ever train/evaluate on valid
rows (src/surrogate/features.feature_target_split filters on `valid`), so
mixing invalid rows into the same train/holdout column is harmless for
them, but it is required for the feasibility CLASSIFIER (trained on every
row) to have any infeasible examples in its holdout set at all -- without
this, "infeasible-class recall" silently evaluates on zero infeasible
holdout examples, which is worse than not reporting it (framework doc
§17: "Surrogate boundary recall: infeasible cases are not systematically
predicted feasible" -- you cannot check that with an empty holdout).

Adds one column, `split` in {"train","holdout"}, and re-writes
design_cases.parquet/.csv in place.
"""

import sys

import numpy as np
import pandas as pd

from config import RESULTS_DIR

HOLDOUT_FRACTION = 0.20
SPLIT_SEED = 20260905


def add_split_column(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["split"] = "train"
    rng = np.random.default_rng(SPLIT_SEED)

    for (regime_id, pcm_id, valid), group in df.groupby(["regime_id", "pcm_id", "valid"]):
        idx = group.index.to_numpy().copy()
        rng.shuffle(idx)
        n_holdout = max(1, int(round(len(idx) * HOLDOUT_FRACTION))) if len(idx) > 1 else 0
        holdout_idx = idx[:n_holdout]
        df.loc[holdout_idx, "split"] = "holdout"

    return df


def run_split(state: str):
    out_dir = RESULTS_DIR / state
    parquet_path = out_dir / "design_cases.parquet"
    df = pd.read_parquet(parquet_path)
    df = add_split_column(df)
    df.to_parquet(parquet_path, index=False)
    df.to_csv(out_dir / "design_cases.csv", index=False)

    counts = df["split"].value_counts()
    print(f"Split written for state={state}:")
    print(counts.to_string())
    n_pairs = df[df["valid"]].groupby(["regime_id", "pcm_id"]).ngroups
    n_pairs_with_holdout = df[df["split"] == "holdout"].groupby(["regime_id", "pcm_id"]).ngroups
    print(f"\nregime x PCM pairs with >=1 holdout case: {n_pairs_with_holdout}/{n_pairs}")
    return df


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "tamilnadu"
    run_split(state)
