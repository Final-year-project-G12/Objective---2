"""
src/surrogate/evaluate.py
============================
Phase 6 / D2.5 — breaks the hold-out error down by regime and by PCM
(framework doc §7.4: "error by state and climate regime ... error by PCM
candidate"). Full ablation (climate-only / no-confidence / regime-ID-only
/ design-only) is explicitly deferred per the reduced 40-hr spec — this
module reports the breakdown that IS in scope.

Reads the models saved by train.py; does not retrain anything.
"""

import pickle
import sys

import pandas as pd
from sklearn.metrics import mean_absolute_error

from config import RESULTS_DIR
from src.surrogate.features import build_feature_table, feature_target_split, TARGET_COLS


def evaluate_by_group(state: str):
    out_dir = RESULTS_DIR / state
    design_cases = pd.read_parquet(out_dir / "design_cases.parquet")
    feat_df = build_feature_table(state, design_cases)
    hold = feat_df[feat_df["split"] == "holdout"].copy()

    with open(out_dir / "surrogate" / "models.pkl", "rb") as f:
        saved = pickle.load(f)
    models, feature_cols = saved["models"], saved["feature_cols"]

    X_hold, y_hold_dict, _, _ = feature_target_split(hold, only_valid=True)
    hold_valid = hold[hold["valid"]].reset_index(drop=True)

    rows = []
    for target in TARGET_COLS:
        if target not in models or target not in y_hold_dict:
            continue
        pred = models[target].predict(X_hold)
        y_true = y_hold_dict[target].reset_index(drop=True)
        pred_s = pd.Series(pred, index=y_true.index)

        for regime_id, idx in hold_valid.groupby("regime_id").groups.items():
            idx = [i for i in idx if i in y_true.index]
            if not idx:
                continue
            rows.append({"target": target, "group_type": "regime", "group": regime_id,
                         "MAE": mean_absolute_error(y_true.loc[idx], pred_s.loc[idx]), "n": len(idx)})
        for pcm_id, idx in hold_valid.groupby("pcm_id").groups.items():
            idx = [i for i in idx if i in y_true.index]
            if not idx:
                continue
            rows.append({"target": target, "group_type": "pcm", "group": pcm_id,
                         "MAE": mean_absolute_error(y_true.loc[idx], pred_s.loc[idx]), "n": len(idx)})

    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "surrogate_error_by_group.csv", index=False)
    print(df.to_string(index=False))
    print(f"\nSaved: {out_dir / 'surrogate_error_by_group.csv'}")
    return df


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "tamilnadu"
    evaluate_by_group(state)
