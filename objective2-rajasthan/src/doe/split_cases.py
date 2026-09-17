"""
src/doe/split_cases.py
=========================
Phase 5 / D2.4 — case-level train/hold-out split (framework doc's reduced
spec: "Split by whole case_id into 80/20 train/hold-out"). Since every row
in phase5_design_cases.parquet is already one complete simulation case (not
a timestep), a random 80/20 split over ROWS is automatically leakage-free —
there is no shared design/weather trajectory between rows to leak.

Stratified by (regime_id, pcm_id, arrangement, valid) since 2026-09-17
(arrangement restored as a searched variable, docs/05_PROMPT_PHASE5_DOE.md
step 6) so every regime x PCM x arrangement combination has hold-out
coverage, not just every regime x PCM combination pooled across
arrangements -- and so that INVALID cases also get a holdout share. That last point
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
phase5_design_cases.parquet/.csv in place.

PORTED FROM objective2-tamilnadu/src/doe/split_cases.py — logic unchanged;
only the output path (this repo's flat results/phaseN_* scheme) and the
__main__ state fallback differ.
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

    for (regime_id, pcm_id, arrangement, valid), group in df.groupby(
            ["regime_id", "pcm_id", "arrangement", "valid"]):
        idx = group.index.to_numpy().copy()
        rng.shuffle(idx)
        n_holdout = max(1, int(round(len(idx) * HOLDOUT_FRACTION))) if len(idx) > 1 else 0
        holdout_idx = idx[:n_holdout]
        df.loc[holdout_idx, "split"] = "holdout"

    return df


def run_split(state: str):
    parquet_path = RESULTS_DIR / "phase5_design_cases.parquet"
    df = pd.read_parquet(parquet_path)
    df = add_split_column(df)
    df.to_parquet(parquet_path, index=False)
    df.to_csv(RESULTS_DIR / "phase5_design_cases.csv", index=False)

    counts = df["split"].value_counts()
    print(f"Split written for state={state}:")
    print(counts.to_string())
    n_pairs = df[df["valid"]].groupby(["regime_id", "pcm_id"]).ngroups
    n_pairs_with_holdout = df[df["split"] == "holdout"].groupby(["regime_id", "pcm_id"]).ngroups
    print(f"\nregime x PCM pairs with >=1 holdout case: {n_pairs_with_holdout}/{n_pairs}")

    n_combos = df[df["valid"]].groupby(["regime_id", "pcm_id", "arrangement"]).ngroups
    n_combos_with_holdout = df[df["split"] == "holdout"].groupby(
        ["regime_id", "pcm_id", "arrangement"]).ngroups
    print(f"regime x PCM x arrangement combinations with >=1 holdout case: "
          f"{n_combos_with_holdout}/{n_combos}")

    # Combinations with a valid design at all, but zero holdout coverage —
    # a real gap for Phase 6 (docs/05_PROMPT_PHASE5_DOE.md exit check).
    valid_combos = set(map(tuple, df[df["valid"]][["regime_id", "pcm_id", "arrangement"]]
                            .drop_duplicates().values.tolist()))
    holdout_combos = set(map(tuple, df[df["split"] == "holdout"][["regime_id", "pcm_id", "arrangement"]]
                              .drop_duplicates().values.tolist()))
    missing = sorted(valid_combos - holdout_combos)
    if missing:
        print(f"\nWARNING — {len(missing)} (regime, pcm, arrangement) combinations have a valid "
              f"design but NO holdout row:")
        for combo in missing:
            print(f"  {combo}")
    return df


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "rajasthan"
    run_split(state)
