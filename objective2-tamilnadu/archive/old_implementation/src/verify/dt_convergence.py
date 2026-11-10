"""
src/verify/dt_convergence.py
===============================
Timestep convergence study (Rajasthan report's G2 equivalent), run on
TAMIL NADU's own model rather than inheriting her conclusion.

Her report finds dt=300 s fails convergence for the 10-node tank and
settles on dt=150 s for production. That is a finding about HER kernel's
numerics, not a transferable constant: Tamil Nadu's tank is 100 L (not
50 L), so node masses, the node Courant number (draw mass per node per
step) and the water/PCM thermal time-constant ratio all differ. This
study measures where OUR model converges.

WHAT CONVERGENCE MEANS HERE (stated before the numbers are looked at, so
the threshold is not fitted to the result):
  * Gate-1 energy residual < 0.5% of collector energy -- this project's
    existing conservation gate, applied unchanged.
  * Richardson-style self-consistency: the annual metrics that decisions
    are made on (useful_energy_kWh, max_water_temp_C, max_pcm_temp_C,
    e_del_45_window_kWh) must change by less than 1% when the timestep is
    HALVED. A dt whose metrics still move more than that under refinement
    is not resolving the physics, whatever its residual says.
The coarsest dt that satisfies both, across all three regimes, is the
production timestep.

Run:  python -m src.verify.dt_convergence
"""

import numpy as np
import pandas as pd

from src.io_utils import load_state_config
from src.parallel.runner import SimTask, run_tasks_parallel
from config import RESULTS_DIR

DT_LADDER_S = [600.0, 300.0, 150.0, 75.0, 37.5, 18.75, 9.375]
METRICS = ["useful_energy_kWh", "max_water_temp_C", "max_pcm_temp_C", "e_del_45_window_kWh"]
RESIDUAL_GATE_PCT = 0.5
REFINEMENT_TOL_PCT = 1.0

# The box MIDPOINT in the v3.0 search space (pcm_volume_fraction
# 0.02-0.30, diameter 0.02-0.08 m, flow 0.01-0.05 kg/s). Not an optimized
# design: a convergence study run at a point chosen for its performance
# would tune the timestep to one corner of the box.
MID_DESIGN = dict(capsule_diameter_m=0.05, pcm_volume_fraction=0.16,
                  flow_rate_kg_s=0.03, arrangement="staggered")


def build_tasks(state: str, n_nodes: int = 10):
    cfg = load_state_config(state)
    tasks = []
    for regime in cfg["regimes"]:
        cid = regime["cluster_id"]
        pcm = regime["pcm_shortlist"][0]
        for dt_s in DT_LADDER_S:
            tasks.append(SimTask(
                task_id=f"c{cid}_dt{dt_s:g}", state=state, cluster_id=cid, pcm_name=pcm,
                model="multinode", n_nodes=n_nodes, timestep_s=dt_s, paired_plain=False,
                **MID_DESIGN))
    return tasks


def analyze(df: pd.DataFrame) -> pd.DataFrame:
    """For each regime, the relative change in each decision metric when dt
    is halved from one ladder rung to the next."""
    invalid = df[~df["valid"]]
    if len(invalid):
        raise RuntimeError(
            f"{len(invalid)}/{len(df)} convergence runs were geometrically rejected "
            f"({invalid['reason'].unique().tolist()}) -- the study design must be valid "
            f"in every regime or the ladder compares different things. Fix MID_DESIGN.")
    df = df.copy()
    df["dt_s"] = df["timestep_s"].astype(float)
    rows = []
    for cid, g in df.groupby("cluster_id"):
        g = g.sort_values("dt_s", ascending=False).reset_index(drop=True)
        for i in range(len(g) - 1):
            coarse, fine = g.loc[i], g.loc[i + 1]
            rec = {"cluster_id": cid, "dt_coarse_s": coarse["dt_s"], "dt_fine_s": fine["dt_s"],
                   "residual_pct_coarse": coarse["residual_pct_of_collector"],
                   "residual_pct_fine": fine["residual_pct_of_collector"]}
            worst = 0.0
            for m in METRICS:
                denom = abs(fine[m]) if abs(fine[m]) > 1e-9 else 1.0
                change = 100.0 * abs(coarse[m] - fine[m]) / denom
                rec[f"d_{m}_pct"] = change
                worst = max(worst, change)
            rec["worst_metric_change_pct"] = worst
            rec["converged_at_coarse"] = bool(worst < REFINEMENT_TOL_PCT
                                              and coarse["residual_pct_of_collector"] < RESIDUAL_GATE_PCT)
            rows.append(rec)
    return pd.DataFrame(rows)


def richardson(df: pd.DataFrame) -> pd.DataFrame:
    """Observed order of convergence and the extrapolated dt->0 limit.

    For three successive rungs at refinement ratio r=2 with values
    f_coarse, f_mid, f_fine, the observed order is
        p = log|(f_coarse - f_mid) / (f_mid - f_fine)| / log 2
    and the extrapolated limit is
        f_exact ~= f_fine + (f_fine - f_mid) / (2^p - 1).
    Backward Euler is formally first-order in time (p=1), so a fitted p
    near 1 is confirmation the ladder is in the asymptotic range and the
    extrapolation is meaningful; a p that wanders (or a sign flip in the
    differences) means the response is NOT smooth in dt for that metric,
    and its extrapolated limit must not be trusted. Reported either way,
    because knowing which metrics behave is the point.
    """
    df = df.copy()
    df["dt_s"] = df["timestep_s"].astype(float)
    rows = []
    for cid in sorted(df["cluster_id"].unique()):
      for metric in METRICS:
        g = df[df["cluster_id"] == cid].sort_values("dt_s", ascending=False)
        vals = g[metric].to_numpy(dtype=float)
        dts = g["dt_s"].to_numpy(dtype=float)
        if len(vals) < 3:
            continue
        # use the three FINEST rungs -- the asymptotic range, if there is one
        f_c, f_m, f_f = vals[-3], vals[-2], vals[-1]
        d1, d2 = f_c - f_m, f_m - f_f
        smooth = (abs(d2) > 1e-12) and (d1 * d2 > 0)
        p = float(np.log(abs(d1 / d2)) / np.log(2.0)) if smooth else float("nan")
        f_exact = float(f_f + (f_f - f_m) / (2.0 ** p - 1.0)) if smooth and p > 0.05 else float("nan")
        rec = {"cluster_id": cid, "metric": metric, "observed_order_p": p,
               "monotone_in_dt": smooth, "extrapolated_limit": f_exact,
               "value_at_finest": f_f, "dt_finest_s": dts[-1]}
        if f_exact == f_exact and abs(f_exact) > 1e-12:
            for dt_v, v in zip(dts, vals):
                rec[f"err_pct_at_dt{dt_v:g}"] = 100.0 * abs(v - f_exact) / abs(f_exact)
        rows.append(rec)
    return pd.DataFrame(rows)


def main(state: str = "tamilnadu"):
    tasks = build_tasks(state)
    print(f"dt convergence study: {len(tasks)} runs "
          f"({len(DT_LADDER_S)} timesteps x 3 regimes, 10-node model)")
    df = run_tasks_parallel(tasks, progress_every=3, label="dt-conv")

    out_dir = RESULTS_DIR / state
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "dt_convergence_runs.csv", index=False)

    summary = analyze(df)
    summary.to_csv(out_dir / "dt_convergence_summary.csv", index=False)

    print("\n--- per-rung refinement sensitivity (coarse vs. half-step) ---")
    print(summary[["cluster_id", "dt_coarse_s", "dt_fine_s", "residual_pct_coarse",
                   "worst_metric_change_pct", "converged_at_coarse"]].to_string(index=False))

    rich = richardson(df)
    rich.to_csv(out_dir / "dt_convergence_richardson.csv", index=False)
    print("\n--- observed order of convergence + Richardson-extrapolated dt->0 limit ---")
    print("(p is fitted from three successive halvings; the error column is each dt's\n"
          " distance from the extrapolated limit, which is the quantity that matters)")
    print(rich.to_string(index=False))

    # The production dt is the COARSEST rung that converges in every regime.
    ok_by_dt = summary.groupby("dt_coarse_s")["converged_at_coarse"].all()
    converged = [dt for dt, ok in ok_by_dt.items() if ok]
    chosen = max(converged) if converged else min(DT_LADDER_S)
    print(f"\nRungs converged in ALL regimes: {sorted(converged, reverse=True)}")
    print(f"PRODUCTION TIMESTEP -> dt = {chosen:.0f} s"
          + ("" if converged else "  (no rung converged; using the finest ladder step)"))
    print(f"\nwrote {out_dir / 'dt_convergence_runs.csv'}")
    print(f"wrote {out_dir / 'dt_convergence_summary.csv'}")
    return chosen


if __name__ == "__main__":
    main()
