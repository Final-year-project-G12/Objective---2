"""
src/surrogate/multifidelity.py
==================================
Phase 6b -- multi-fidelity surrogate augmentation. Closes the audit gap:
"Multi-fidelity surrogate modeling not explored" (Lee et al., "Efficient
design optimization using multi-fidelity surrogate modeling for a thermal
battery", arXiv 2026; and the DHW-ANN surrogate paper, Energies 2026 --
both describe a cheap low-fidelity model feeding a high-fidelity
correction layer, the standard additive-correction / co-kriging pattern).

Two-tier structure:
  - LOW FIDELITY:  src/simulation/tank_model.py's fidelity="low" mode --
    exactly one fixed-size sub-step per hour, no melt-band refinement, no
    stiffness-adaptive escalation. Cheap and approximate.
  - HIGH FIDELITY: Phase 3's existing adaptive sub-stepping (fidelity=
    "high", the default everywhere else in this project) -- expensive,
    ground truth.

This module:
  1. Re-runs every Phase 5 DOE case (same case specs, same seeds --
     generate_all_cases() is deterministic) at LOW fidelity, and measures
     the speedup vs. the already-recorded Phase 5 high-fidelity runtime.
  2. Reports how well the free low-fidelity output alone predicts the
     high-fidelity ground truth per target (a low-fidelity-only R2/bias
     check -- this is what justifies using it as a surrogate FEATURE
     rather than noise).
  3. Runs a sample-efficiency experiment: trains the SAME ExtraTrees
     architecture Phase 6 uses, at shrinking high-fidelity training
     fractions (100/75/50/25%), with and without the low-fidelity
     prediction as an extra input feature, always evaluated on Phase 6's
     ORIGINAL fixed hold-out set (the same rows, so results are directly
     comparable to surrogate_metrics.csv). This quantifies how much of
     Phase 6's near-ceiling accuracy survives when far fewer expensive
     high-fidelity simulations are available, if a cheap low-fidelity
     proxy is added -- the actual practical claim multi-fidelity
     modeling makes (and the one the audit specifically asked to see
     demonstrated, not just cited).

Never affects Phase 4/5/7/8's authoritative numbers -- this is an
additional, self-contained analysis, run separately (pipeline.py
`--stage multifidelity`), reading Phase 5's design_cases.parquet
read-only and writing its own new files.
"""

import sys
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from config import RESULTS_DIR
from src.design.schema import DesignVector
from src.simulation.run_case import run_case
from src.doe.generate_cases import generate_all_cases
from src.surrogate.features import build_feature_table, TARGET_COLS, DESIGN_COLS, CLIMATE_COLS, PCM_COLS

N_ESTIMATORS = 300
RANDOM_STATE = 20260905
LF_TARGET_COLS = ["useful_energy_kWh", "solar_fraction", "unmet_energy_kWh", "pump_energy_kWh"]
HF_FRACTIONS = [1.0, 0.75, 0.5, 0.25]


def run_low_fidelity_batch(state: str, n_lhs_per_pair: int = 8):
    """Re-runs every Phase 5 case spec at fidelity='low'. Same case_ids as
    design_cases.parquet (deterministic generation), so the two can be
    joined directly."""
    cases, _ = generate_all_cases(state, n_lhs_per_pair=n_lhs_per_pair)
    print(f"Phase 6b — running {len(cases)} DOE cases at LOW fidelity for state={state} ...")

    rows = []
    t_start = time.time()
    for i, spec in enumerate(cases):
        design = DesignVector(capsule_diameter_m=spec.capsule_diameter_m,
                               n_capsule=spec.n_capsule, flow_rate_kg_s=spec.flow_rate_kg_s)
        t0 = time.time()
        out = run_case(state, spec.regime_id, spec.pcm_id, design, record_hourly=False, fidelity="low")
        runtime_s = time.time() - t0

        row = {"case_id": spec.case_id, "lf_valid": out["valid"], "lf_runtime_s": runtime_s}
        if out["valid"]:
            for t in LF_TARGET_COLS:
                row[f"lf_{t}"] = out["metrics"].get(t)
        rows.append(row)
        if (i + 1) % 50 == 0 or (i + 1) == len(cases):
            print(f"  {i+1}/{len(cases)} low-fidelity cases done ({time.time()-t_start:.1f}s elapsed)")

    df = pd.DataFrame(rows)
    out_dir = RESULTS_DIR / state
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_dir / "design_cases_lowfid.parquet", index=False)
    df.to_csv(out_dir / "design_cases_lowfid.csv", index=False)
    print(f"Saved: {out_dir / 'design_cases_lowfid.parquet'} ({len(df)} rows, "
          f"total low-fidelity runtime {df['lf_runtime_s'].sum():.1f}s)")
    return df


def benchmark_fidelity_runtime(state: str, n_lhs_per_pair: int = 8, seed: int = 20260907) -> pd.DataFrame:
    """Fair, contemporaneous speedup measurement. compute_speedup_and_accuracy
    originally compared a freshly-timed low-fidelity pass against the
    high-fidelity runtime_s column already sitting in design_cases.parquet
    -- timed whenever Phase 5 originally ran, on a different machine
    state/moment. That produced a nonsensical "0.27x speedup" (low
    fidelity slower), which is a measurement artifact, not a real result
    (low fidelity does strictly less work per sub-step, so it cannot be
    slower for the same case). This function re-times BOTH fidelities for
    every case in the SAME process, back-to-back, with the run order
    randomized per case (not all-high-then-all-low) so any system drift
    over the run (thermal throttling, background load) cannot
    systematically favor either fidelity."""
    cases, _ = generate_all_cases(state, n_lhs_per_pair=n_lhs_per_pair)
    rng = np.random.default_rng(seed)
    print(f"Phase 6b — fair runtime benchmark: {len(cases)} cases, both fidelities, randomized order ...")

    rows = []
    t_start = time.time()
    for i, spec in enumerate(cases):
        design = DesignVector(capsule_diameter_m=spec.capsule_diameter_m,
                               n_capsule=spec.n_capsule, flow_rate_kg_s=spec.flow_rate_kg_s)
        order = ["high", "low"] if rng.random() < 0.5 else ["low", "high"]
        timings = {}
        for fidelity in order:
            t0 = time.time()
            out = run_case(state, spec.regime_id, spec.pcm_id, design, record_hourly=False, fidelity=fidelity)
            timings[fidelity] = time.time() - t0
            timings[f"{fidelity}_valid"] = out["valid"]
        rows.append({"case_id": spec.case_id, "order": "-".join(order),
                      "hf_runtime_s_fresh": timings["high"], "lf_runtime_s_fresh": timings["low"],
                      "hf_valid_fresh": timings["high_valid"], "lf_valid_fresh": timings["low_valid"]})
        if (i + 1) % 50 == 0 or (i + 1) == len(cases):
            print(f"  {i+1}/{len(cases)} benchmark cases done ({time.time()-t_start:.1f}s elapsed)")

    df = pd.DataFrame(rows)
    out_dir = RESULTS_DIR / state
    df.to_csv(out_dir / "multifidelity_runtime_benchmark.csv", index=False)
    hf_total, lf_total = df["hf_runtime_s_fresh"].sum(), df["lf_runtime_s_fresh"].sum()
    print(f"Fresh, order-randomized totals -- high-fidelity: {hf_total:.1f}s  low-fidelity: {lf_total:.1f}s  "
          f"speedup: {hf_total/lf_total:.2f}x")
    print(f"Saved: {out_dir / 'multifidelity_runtime_benchmark.csv'}")
    return df


def _joined(state: str):
    out_dir = RESULTS_DIR / state
    hf = pd.read_parquet(out_dir / "design_cases.parquet")
    lf = pd.read_parquet(out_dir / "design_cases_lowfid.parquet")
    return hf.merge(lf, on="case_id", how="inner")


def compute_speedup_and_accuracy(state: str, runtime_benchmark: pd.DataFrame) -> dict:
    joined = _joined(state)
    both_valid = joined[joined["valid"] & joined["lf_valid"]]

    bench_valid = runtime_benchmark[runtime_benchmark["hf_valid_fresh"] & runtime_benchmark["lf_valid_fresh"]]
    hf_runtime = bench_valid["hf_runtime_s_fresh"].sum()
    lf_runtime = bench_valid["lf_runtime_s_fresh"].sum()
    speedup = hf_runtime / lf_runtime if lf_runtime > 0 else float("nan")

    accuracy_rows = []
    for t in LF_TARGET_COLS:
        y_hf = both_valid[t]
        y_lf = both_valid[f"lf_{t}"]
        r2 = r2_score(y_hf, y_lf)
        mae = mean_absolute_error(y_hf, y_lf)
        bias_pct = float(((y_lf - y_hf) / y_hf.replace(0, np.nan)).mean() * 100)
        accuracy_rows.append({"target": t, "low_fidelity_only_R2": r2, "low_fidelity_only_MAE": mae,
                               "low_fidelity_only_mean_bias_pct": bias_pct, "n_cases": len(both_valid)})

    report = {
        "n_cases_total": len(joined), "n_cases_both_valid": len(both_valid),
        "n_cases_in_runtime_benchmark": len(bench_valid),
        "high_fidelity_total_runtime_s": float(hf_runtime), "low_fidelity_total_runtime_s": float(lf_runtime),
        "speedup_x": float(speedup),
        "runtime_benchmark_note": "hf/lf runtimes above are from a fresh, order-randomized, "
                                   "same-process re-timing of both fidelities (benchmark_fidelity_runtime()), "
                                   "NOT from design_cases.parquet's stale runtime_s column -- an initial "
                                   "version of this comparison mixed a fresh low-fidelity timing against an "
                                   "old high-fidelity timing recorded in a separate process days earlier and "
                                   "produced a nonsensical >1x slowdown for low fidelity; this is the corrected "
                                   "measurement.",
        "low_fidelity_accuracy_by_target": accuracy_rows,
    }
    print(f"\nHigh-fidelity total runtime: {hf_runtime:.1f}s  |  Low-fidelity total runtime: {lf_runtime:.1f}s"
          f"  |  Speedup: {speedup:.2f}x")
    for r in accuracy_rows:
        print(f"  low-fidelity-only vs. high-fidelity ground truth — {r['target']:20s} "
              f"R2={r['low_fidelity_only_R2']:.3f}  mean bias={r['low_fidelity_only_mean_bias_pct']:+.1f}%")
    return report


def _augmented_feature_table(state: str):
    joined = _joined(state)
    feat_df = build_feature_table(state, joined)
    lf_cols = [f"lf_{t}" for t in LF_TARGET_COLS]
    feat_df[lf_cols] = feat_df[lf_cols].fillna(0.0)
    return feat_df, lf_cols


def run_sample_efficiency_experiment(state: str) -> pd.DataFrame:
    feat_df, lf_cols = _augmented_feature_table(state)
    base_feature_cols = [c for c in DESIGN_COLS if c in feat_df.columns]
    base_feature_cols += [c for c in CLIMATE_COLS if c in feat_df.columns]
    base_feature_cols += [c for c in PCM_COLS if c in feat_df.columns]
    base_feature_cols += ["is_no_pcm", "top3_inclusion_probability"]
    base_feature_cols = list(dict.fromkeys(base_feature_cols))

    valid = feat_df[feat_df["valid"] & feat_df["lf_valid"]]
    train_all = valid[valid["split"] == "train"]
    hold = valid[valid["split"] == "holdout"]
    print(f"\nSample-efficiency experiment: {len(train_all)} candidate train rows, "
          f"{len(hold)} fixed hold-out rows (same hold-out as Phase 6)")

    rows = []
    for frac in HF_FRACTIONS:
        rng = np.random.default_rng(RANDOM_STATE + int(frac * 1000))
        idx = train_all.index.to_numpy().copy()
        rng.shuffle(idx)
        n_take = max(5, int(round(len(idx) * frac)))
        train_sub = train_all.loc[idx[:n_take]]

        for target in LF_TARGET_COLS:
            if target not in train_sub.columns:
                continue
            X_hold = hold[base_feature_cols]
            X_hold_mf = hold[base_feature_cols + lf_cols]
            y_hold = hold[target]

            baseline = ExtraTreesRegressor(n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE, n_jobs=-1)
            baseline.fit(train_sub[base_feature_cols], train_sub[target])
            pred_b = baseline.predict(X_hold)

            mf = ExtraTreesRegressor(n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE, n_jobs=-1)
            mf.fit(train_sub[base_feature_cols + lf_cols], train_sub[target])
            pred_mf = mf.predict(X_hold_mf)

            for model_name, pred in [("high_fidelity_only", pred_b), ("multi_fidelity_augmented", pred_mf)]:
                rows.append({
                    "target": target, "hf_training_fraction": frac, "n_train": n_take,
                    "model": model_name,
                    "R2": r2_score(y_hold, pred), "RMSE": mean_squared_error(y_hold, pred) ** 0.5,
                    "MAE": mean_absolute_error(y_hold, pred),
                })

    report_df = pd.DataFrame(rows)
    print(report_df.pivot_table(index=["target", "hf_training_fraction"], columns="model",
                                 values="R2").to_string())
    return report_df


def run(state: str, force_lowfid_rerun: bool = False):
    lowfid_path = RESULTS_DIR / state / "design_cases_lowfid.parquet"
    if force_lowfid_rerun or not lowfid_path.exists():
        run_low_fidelity_batch(state)
    else:
        print(f"Reusing existing {lowfid_path} (pass force_lowfid_rerun=True to regenerate)")
    runtime_benchmark = benchmark_fidelity_runtime(state)
    speedup_report = compute_speedup_and_accuracy(state, runtime_benchmark)
    efficiency_df = run_sample_efficiency_experiment(state)

    out_dir = RESULTS_DIR / state
    efficiency_df.to_csv(out_dir / "multifidelity_sample_efficiency.csv", index=False)

    import json
    with open(out_dir / "multifidelity_speedup_report.json", "w", encoding="utf-8") as f:
        json.dump(speedup_report, f, indent=2, default=str)

    print(f"\nSaved: {out_dir / 'multifidelity_sample_efficiency.csv'}")
    print(f"Saved: {out_dir / 'multifidelity_speedup_report.json'}")
    return speedup_report, efficiency_df


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "tamilnadu"
    run(state)
