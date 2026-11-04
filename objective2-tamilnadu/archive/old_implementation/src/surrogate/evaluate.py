"""
src/surrogate/evaluate.py
============================
Phase 6 / D2.5 — breaks the hold-out error down by regime, PCM, and
(2026-09-17) arrangement (framework doc §7.4: "error by state and climate
regime ... error by PCM candidate"; arrangement breakdown adapted from
"a Rajasthan-pilot change plan (source removed from this project after adaptation, see docs_objective2/tamilnadu_phase_docs/)"). Full
ablation (climate-only / no-confidence / regime-ID-only / design-only) is
explicitly deferred per the reduced 40-hr spec — this module reports the
breakdown that IS in scope, plus a dedicated arrangement feature-importance
diagnostic (required now that arrangement is a searched variable).

Reads the models saved by train.py; does not retrain anything.
"""

import pickle
import sys

import pandas as pd
from sklearn.metrics import mean_absolute_error

from config import RESULTS_DIR
from src.surrogate.features import build_feature_table, feature_target_split, TARGET_COLS, ARRANGEMENT_COLS


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
        # 2026-09-17: arrangement breakdown (this will produce roughly 3x
        # more rows than the pre-arrangement file — expected).
        for arrangement, idx in hold_valid.groupby("arrangement").groups.items():
            idx = [i for i in idx if i in y_true.index]
            if not idx:
                continue
            rows.append({"target": target, "group_type": "arrangement", "group": arrangement,
                         "MAE": mean_absolute_error(y_true.loc[idx], pred_s.loc[idx]), "n": len(idx)})
        # regime x pcm x arrangement (finest breakdown DOE/split now supports)
        for (regime_id, pcm_id, arrangement), idx in hold_valid.groupby(
                ["regime_id", "pcm_id", "arrangement"]).groups.items():
            idx = [i for i in idx if i in y_true.index]
            if not idx:
                continue
            rows.append({"target": target, "group_type": "regime_pcm_arrangement",
                         "group": f"{regime_id}/{pcm_id}/{arrangement}",
                         "MAE": mean_absolute_error(y_true.loc[idx], pred_s.loc[idx]), "n": len(idx)})

    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "surrogate_error_by_group.csv", index=False)
    print(df[df["group_type"].isin(["regime", "pcm", "arrangement"])].to_string(index=False))
    print(f"\nSaved: {out_dir / 'surrogate_error_by_group.csv'}  "
          f"({len(df)} rows, including the finer regime x pcm x arrangement breakdown)")

    report_arrangement_importance(models, feature_cols)
    return df


def report_arrangement_importance(models: dict, feature_cols: list):
    """Required diagnostic (2026-09-17): feature importance specifically
    for the 3 arrangement one-hot columns, combined and individually, for
    every regression target. Reported honestly whichever way it comes out
    — a near-zero combined importance means "arrangement had minimal
    effect on this target in this design-space region," not that
    something is broken."""
    print("\n" + "=" * 72)
    print("Arrangement feature importance (2026-09-17)")
    print("=" * 72)
    arr_idx = {col: feature_cols.index(col) for col in ARRANGEMENT_COLS if col in feature_cols}
    if not arr_idx:
        print("  Arrangement columns not found in feature_cols -- was the surrogate "
              "trained before this diagnostic was added? Re-run --stage surrogate.")
        return

    for target, model in models.items():
        if target == "feasibility" or not hasattr(model, "feature_importances_"):
            continue
        importances = model.feature_importances_
        per_arr = {col: float(importances[idx]) for col, idx in arr_idx.items()}
        combined = sum(per_arr.values())
        detail = ", ".join(f"{col}={val:.4f}" for col, val in per_arr.items())
        finding = ("minimal effect on this target in this design-space region"
                   if combined < 0.01 else "a meaningful contributor for this target")
        print(f"  {target:22s} {detail}, combined={combined:.4f}  -> arrangement had {finding}")


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "tamilnadu"
    evaluate_by_group(state)
