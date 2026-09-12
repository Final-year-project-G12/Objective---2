"""
src/surrogate/train.py
=========================
Phase 6 / D2.5 — one combined tree-based surrogate (Extra Trees), no
ablation, per the framework doc's reduced 40-hr spec:
  "One family: Extra Trees or XGBoost regressors for key outputs (useful
   energy, solar fraction, unmet energy at minimum) + optional feasibility
   classifier if the split is sharp. Compare against a linear-regression
   baseline. Report MAE/RMSE/R2 on hold-out. Ablation deferred."

Trains:
  - ExtraTreesRegressor per performance target (useful_energy_kWh,
    solar_fraction, unmet_energy_kWh, pump_energy_kWh, pcm_mass_kg,
    mean_f_melt), each compared against a plain LinearRegression baseline
    on the SAME train/holdout split (the split column written by
    src/doe/split_cases.py).
  - One ExtraTreesClassifier feasibility model (valid/invalid), trained on
    ALL cases (not just the 80% train rows of the valid subset) since
    infeasible cases are exactly what defines the boundary it needs to
    learn.

BUG-FIX 5 (framework doc): the surrogate is a proposal ranker, not the
final oracle. Nothing here is ever reported as a final performance number
— Phase 7 always re-confirms selected designs with the real simulator.
"""

import json
import pickle
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, ExtraTreesClassifier
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from config import RESULTS_DIR
from src.surrogate.features import build_feature_table, feature_target_split, TARGET_COLS

N_ESTIMATORS = 300
RANDOM_STATE = 20260905


def _fit_eval(model, X_train, y_train, X_hold, y_hold):
    model.fit(X_train, y_train)
    pred = model.predict(X_hold)
    mae = mean_absolute_error(y_hold, pred)
    rmse = mean_squared_error(y_hold, pred) ** 0.5
    r2 = r2_score(y_hold, pred) if len(y_hold) > 1 else float("nan")
    max_err = float(np.max(np.abs(pred - y_hold))) if len(y_hold) else float("nan")
    return model, {"MAE": mae, "RMSE": rmse, "R2": r2, "max_abs_error": max_err, "n_holdout": len(y_hold)}


def train_surrogate(state: str):
    out_dir = RESULTS_DIR / state
    design_cases = pd.read_parquet(out_dir / "design_cases.parquet")
    feat_df = build_feature_table(state, design_cases)

    train_mask = feat_df["split"] == "train"
    hold_mask = feat_df["split"] == "holdout"

    X_train, y_train_dict, _, feature_cols = feature_target_split(feat_df[train_mask], only_valid=True)
    X_hold, y_hold_dict, _, _ = feature_target_split(feat_df[hold_mask], only_valid=True)

    print(f"Surrogate training set: {len(X_train)} rows, hold-out: {len(X_hold)} rows, "
          f"{len(feature_cols)} features")

    models = {}
    metrics_rows = []
    for target in TARGET_COLS:
        if target not in y_train_dict or target not in y_hold_dict:
            continue
        y_train, y_hold = y_train_dict[target], y_hold_dict[target]

        et = ExtraTreesRegressor(n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE, n_jobs=-1)
        et, et_metrics = _fit_eval(et, X_train, y_train, X_hold, y_hold)

        lr = LinearRegression()
        lr, lr_metrics = _fit_eval(lr, X_train, y_train, X_hold, y_hold)

        models[target] = et
        metrics_rows.append({"target": target, "model": "ExtraTrees", **et_metrics})
        metrics_rows.append({"target": target, "model": "LinearRegression", **lr_metrics})
        beats_linear = et_metrics["RMSE"] <= lr_metrics["RMSE"]
        print(f"  {target:22s} ExtraTrees RMSE={et_metrics['RMSE']:.4g} R2={et_metrics['R2']:.3f}  |  "
              f"Linear RMSE={lr_metrics['RMSE']:.4g} R2={lr_metrics['R2']:.3f}  "
              f"{'[tree beats linear]' if beats_linear else '[WARNING: linear as good or better]'}")

    # --- feasibility classifier: trained on ALL cases (valid label) -----
    X_all, _, feas_y_all, feas_feature_cols = feature_target_split(feat_df, only_valid=False)

    # BUG FIX (found on Uttarakhand's real run, applies to every state):
    # constraints.py's _reject() returns only {design, valid, reason, notes}
    # for bounds_violation cases -- none of the 8 geom_* geometry/hydraulics
    # fields are computed for a design that's already out of bounds, since
    # they're not meaningfully definable there. That leaves NaN in every
    # geom_* column for 100% of rejected rows, and ExtraTreesClassifier
    # (unlike some sklearn estimators) refuses to fit on NaN at all.
    # Fix: (1) add an explicit "was geometry ever computed" flag -- this is
    # itself a legitimate, informative feature for a feasibility classifier,
    # not a workaround being hidden; (2) median-impute the NaN geom_*
    # values using ONLY the valid rows' medians, so the imputed value is a
    # physically plausible in-range number, not an arbitrary 0.
    geom_cols_with_nan = [c for c in feas_feature_cols if X_all[c].isna().any()]
    if geom_cols_with_nan:
        valid_medians = X_all.loc[feat_df["valid"], geom_cols_with_nan].median()
        X_all["geometry_was_computed"] = (~X_all[geom_cols_with_nan[0]].isna()).astype(int)
        X_all[geom_cols_with_nan] = X_all[geom_cols_with_nan].fillna(valid_medians)
        feas_feature_cols = feas_feature_cols + ["geometry_was_computed"]
        print(f"  [NOTE] {len(geom_cols_with_nan)} geometry feature(s) were NaN for all "
              f"{(~feat_df['valid']).sum()} bounds_violation-rejected rows (never computed, "
              f"not missing data) -- median-imputed from valid rows + added an explicit "
              f"'geometry_was_computed' flag feature so the classifier isn't fed silent NaN.")

    all_train_mask = (feat_df["split"] != "holdout")   # everything not held out (train + excluded_invalid)
    clf = ExtraTreesClassifier(n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE, n_jobs=-1)
    clf.fit(X_all[feas_feature_cols][all_train_mask], feas_y_all[all_train_mask])

    hold_all_mask = feat_df["split"] == "holdout"
    if hold_all_mask.sum():
        feas_pred = clf.predict(X_all[feas_feature_cols][hold_all_mask])
        feas_true = feas_y_all[hold_all_mask]
        # recall for the infeasible class matters most (framework doc §7.2/§17:
        # "Surrogate boundary recall: infeasible cases are not systematically
        # predicted feasible")
        infeasible_mask = feas_true == 0
        recall_infeasible = (float((feas_pred[infeasible_mask] == 0).mean())
                              if infeasible_mask.sum() else float("nan"))
        acc = float((feas_pred == feas_true).mean())
        print(f"  feasibility classifier: holdout accuracy={acc:.3f}, "
              f"infeasible-class recall={recall_infeasible:.3f} (n_infeasible_holdout={int(infeasible_mask.sum())})")
        metrics_rows.append({"target": "feasibility", "model": "ExtraTreesClassifier",
                              "accuracy": acc, "infeasible_recall": recall_infeasible,
                              "n_holdout": int(hold_all_mask.sum())})
    models["feasibility"] = clf

    metrics_df = pd.DataFrame(metrics_rows)
    metrics_df.to_csv(out_dir / "surrogate_metrics.csv", index=False)

    surrogate_dir = out_dir / "surrogate"
    surrogate_dir.mkdir(parents=True, exist_ok=True)
    with open(surrogate_dir / "models.pkl", "wb") as f:
        pickle.dump({"models": models, "feature_cols": feature_cols,
                     "feasibility_feature_cols": feas_feature_cols}, f)
    with open(surrogate_dir / "feature_cols.json", "w") as f:
        json.dump(feature_cols, f, indent=2)
    with open(surrogate_dir / "feasibility_feature_cols.json", "w") as f:
        json.dump(feas_feature_cols, f, indent=2)

    print(f"\nSaved: {out_dir / 'surrogate_metrics.csv'}")
    print(f"Saved: {surrogate_dir / 'models.pkl'}")
    return models, feature_cols, metrics_df


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "uttarakhand"
    train_surrogate(state)