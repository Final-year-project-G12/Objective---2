"""
src/surrogate/evaluate.py
============================
Phase 6 / D2.5 — breaks the hold-out error down by regime and by PCM
(framework doc §7.4: "error by state and climate regime ... error by PCM
candidate"). Full ablation (climate-only / no-confidence / regime-ID-only
/ design-only) is explicitly deferred per the reduced 40-hr spec — this
module reports the breakdown that IS in scope.

Reads the models saved by train.py; does not retrain anything.

PORTED FROM objective2-tamilnadu/src/surrogate/evaluate.py — logic
unchanged; only the flat results/phaseN_* I/O paths and the __main__
state fallback differ.
"""

import pickle
import sys

import pandas as pd
from sklearn.metrics import mean_absolute_error

from config import RESULTS_DIR
from src.surrogate.features import build_feature_table, feature_target_split, TARGET_COLS

DESIGN_CASES_PATH = RESULTS_DIR / "phase5_design_cases.parquet"
MODELS_PATH = RESULTS_DIR / "phase6_surrogate_models.pkl"
ERROR_BY_GROUP_PATH = RESULTS_DIR / "phase6_surrogate_error_by_group.csv"


def evaluate_by_group(state: str):
    design_cases = pd.read_parquet(DESIGN_CASES_PATH)
    feat_df = build_feature_table(state, design_cases)
    hold = feat_df[feat_df["split"] == "holdout"].copy()

    with open(MODELS_PATH, "rb") as f:
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
    df.to_csv(ERROR_BY_GROUP_PATH, index=False)
    print(df.to_string(index=False))
    print(f"\nSaved: {ERROR_BY_GROUP_PATH}")
    return df


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "rajasthan"
    evaluate_by_group(state)
