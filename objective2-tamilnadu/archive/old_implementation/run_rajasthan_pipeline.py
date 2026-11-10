"""
run_rajasthan_pipeline.py
============================
End-to-end runner for the ported Rajasthan methodology, Tamil Nadu.

Stage order matters and is enforced: each stage consumes the previous
stage's file, and the year roles are kept apart (explore -> search,
select -> feasibility, test -> one-shot held-out).

  1  surrogate   per-group bake-off on the Sobol DOE (explore years)
  2  search      NSGA-II on the winning surrogate, per group
  3  active      active learning w/ box-vertex step, until HV settles
  4  confirm     every front candidate RE-SIMULATED on the select years
  5  band        repeatability band, measured not assumed
  6  select      S0 -> S1 -> S2 funnel + tie-break -> chosen design
  7  heldout     one-shot locked test on the test years
  8  diagnostics G11, G13-G18
  9  registry    every citable number, with its source file

Run one stage:   python run_rajasthan_pipeline.py --stage surrogate
Run everything:  python run_rajasthan_pipeline.py --stage all

Every stage writes to results/<state>/ and is idempotent except `heldout`,
which is single-use by design (see src/verify/held_out_lock.py).
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from config import RESULTS_DIR
from src.io_utils import load_state_config
from src.weather.fetch_multiyear_weather import YEAR_ROLES

EXPLORE_YEARS = sorted(y for y, r in YEAR_ROLES.items() if r == "explore")
SELECT_YEARS = sorted(y for y, r in YEAR_ROLES.items() if r == "select")
TEST_YEARS = sorted(y for y, r in YEAR_ROLES.items() if r == "test")

PRODUCTION_DT_S = 150.0     # from src/verify/dt_convergence.py -- matches her 150 s
N_NODES = 10


def _out(state):
    d = RESULTS_DIR / state
    d.mkdir(parents=True, exist_ok=True)
    return d


def _need(path: Path, stage_hint: str):
    if not path.exists():
        sys.exit(f"missing {path.name} -- run `--stage {stage_hint}` first")
    return pd.read_csv(path)


# ---------------------------------------------------------------- stages

def stage_surrogate(state, args):
    from src.surrogate.fit_per_pair import fit_all_groups
    doe = _need(_out(state) / "sobol_doe_results.csv", "the Sobol DOE (src.doe.run_sobol_doe)")
    print(f"fitting per-group surrogates on {len(doe)} DOE rows "
          f"({int(doe['valid'].sum())} valid)")
    fits, scores = fit_all_groups(doe)
    scores.to_csv(_out(state) / "surrogate_bakeoff.csv", index=False)

    win = scores[scores["is_winner"]]
    print("\nwinners by target:")
    print(win.groupby(["target", "model"]).size().to_string())
    print("\nmean rmse/sd by model (lower is better):")
    print(scores.groupby("model")["rmse_over_sd"].mean().sort_values().to_string())
    print(f"\nwrote {_out(state) / 'surrogate_bakeoff.csv'}")
    return fits


def stage_search(state, args, fits=None):
    from src.surrogate.fit_per_pair import fit_all_groups
    from src.optimize.nsga2_search import search_group, front_to_frame
    if fits is None:
        doe = _need(_out(state) / "sobol_doe_results.csv", "surrogate")
        fits, _ = fit_all_groups(doe, verbose=False)

    frames = []
    for key, fit in fits.items():
        if not fit.models:
            continue
        res = search_group(fit, pop_size=args.pop, n_gen=args.gen, seed=args.seed)
        frames.append(front_to_frame(res))
        print(f"  c{fit.cluster_id} {fit.pcm_name:22s} {fit.arrangement:13s} "
              f"front={len(res.X):3d} feasible={res.n_feasible}/{res.n_evaluated}",
              flush=True)
    fronts = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    fronts.to_csv(_out(state) / "nsga2_fronts.csv", index=False)
    print(f"\n{len(fronts)} front points across {len(frames)} groups")
    print(f"wrote {_out(state) / 'nsga2_fronts.csv'}")
    return fronts


def stage_active(state, args):
    from src.optimize.active_learning import run_active_learning
    doe = _need(_out(state) / "sobol_doe_results.csv", "the Sobol DOE")
    rounds, all_rows = [], []
    groups = list(doe.groupby(["cluster_id", "pcm_name", "arrangement"], dropna=False))
    print(f"active learning over {len(groups)} groups "
          f"(max {args.rounds} rounds, batch {args.batch})")
    for (cid, pcm, arr), g in groups:
        print(f"  c{cid} {pcm} {arr}", flush=True)
        r = run_active_learning(g, cid, pcm, arr, state=state,
                                years=tuple(EXPLORE_YEARS[:1]), n_nodes=N_NODES,
                                timestep_s=PRODUCTION_DT_S, max_rounds=args.rounds,
                                pop_size=args.pop, n_gen=args.gen, seed=args.seed,
                                batch_size=args.batch)
        for rec in r.rounds:
            rec.update({"cluster_id": cid, "pcm_name": pcm, "arrangement": arr,
                        "stopped_because": r.stopped_because})
            rounds.append(rec)
        if r.doe_rows is not None:
            all_rows.append(r.doe_rows)
    pd.DataFrame(rounds).to_csv(_out(state) / "active_learning_rounds.csv", index=False)
    if all_rows:
        pd.concat(all_rows, ignore_index=True).to_csv(
            _out(state) / "active_learning_simulated.csv", index=False)
    print(f"wrote {_out(state) / 'active_learning_rounds.csv'}")


def stage_confirm(state, args):
    """Re-simulate every front candidate on the SELECT years, for real."""
    from src.parallel.runner import SimTask, run_tasks_parallel
    fronts = _need(_out(state) / "nsga2_fronts.csv", "search")
    top = (fronts.sort_values("g_window_kWh_pred", ascending=False)
                 .groupby(["cluster_id", "pcm_name", "arrangement"], dropna=False)
                 .head(args.top_n).reset_index(drop=True))
    tasks = []
    for i, d in top.iterrows():
        for y in SELECT_YEARS:
            tasks.append(SimTask(
                task_id=f"confirm_{i:04d}_y{y}", state=state,
                cluster_id=int(d["cluster_id"]), pcm_name=d["pcm_name"],
                capsule_diameter_m=float(d["capsule_diameter_m"]),
                n_capsule=int(d["n_capsule"]),
                flow_rate_kg_s=float(d["flow_rate_kg_s"]),
                arrangement=d["arrangement"], model="multinode", n_nodes=N_NODES,
                timestep_s=PRODUCTION_DT_S, year=y, paired_plain=True))
    print(f"confirming {len(top)} candidates x {len(SELECT_YEARS)} select years "
          f"= {len(tasks)} runs")
    df = run_tasks_parallel(tasks, chunksize=2,
                            progress_every=max(1, len(tasks) // 20), label="confirm")
    df.to_csv(_out(state) / "confirmed_select_years.csv", index=False)
    print(f"wrote {_out(state) / 'confirmed_select_years.csv'}")
    return df


def stage_band(state, args):
    from src.verify.repeatability import measure_band
    conf = _need(_out(state) / "confirmed_select_years.csv", "confirm")
    ok = conf[conf["valid"]]
    best = (ok.groupby(["cluster_id", "pcm_name", "arrangement", "n_capsule",
                        "capsule_diameter_m", "flow_rate_kg_s"], dropna=False)
              ["g_window_kWh"].mean().reset_index()
              .sort_values("g_window_kWh", ascending=False)
              .groupby("cluster_id").head(1))
    print(f"measuring the repeatability band on {len(best)} designs")
    band, runs = measure_band(best, state, SELECT_YEARS, base_dt=PRODUCTION_DT_S,
                              base_nodes=N_NODES)
    band.to_csv(_out(state) / "repeatability_band.csv", index=False)
    runs.to_csv(_out(state) / "repeatability_runs.csv", index=False)
    print(f"wrote {_out(state) / 'repeatability_band.csv'}")
    return band


def stage_select(state, args):
    from src.optimize.selection_funnel import select_per_regime
    conf = _need(_out(state) / "confirmed_select_years.csv", "confirm")
    band_df = _need(_out(state) / "repeatability_band.csv", "band")
    bands = dict(zip(band_df["cluster_id"], band_df["band_kWh"]))
    chosen, audit = select_per_regime(conf, bands)
    chosen.to_csv(_out(state) / "deployable_design_per_regime.csv", index=False)
    audit.to_csv(_out(state) / "selection_funnel_audit.csv", index=False)
    print("\nfunnel:")
    print(audit.to_string(index=False))
    print("\nchosen per regime:")
    cols = [c for c in ["cluster_id", "pcm_name", "arrangement", "n_capsule",
                        "capsule_diameter_m", "flow_rate_kg_s", "g_window_kWh",
                        "pcm_mass_kg", "max_pcm_temp_C", "n_indistinguishable"]
            if c in chosen.columns]
    print(chosen[cols].to_string(index=False))
    print(f"\nwrote {_out(state) / 'deployable_design_per_regime.csv'}")
    return chosen


def stage_heldout(state, args):
    from src.verify.held_out_lock import run_held_out_test, HeldOutLockError
    chosen = _need(_out(state) / "deployable_design_per_regime.csv", "select")
    try:
        df, rec = run_held_out_test(chosen, state=state, years=tuple(TEST_YEARS),
                                     n_nodes=N_NODES, timestep_s=PRODUCTION_DT_S)
    except HeldOutLockError as e:
        print(f"HELD-OUT LOCK: {e}")
        return None
    ok = df[df["valid"]]
    print(f"\nrun_id {rec['run_id']}  years {TEST_YEARS}")
    print(ok.groupby("cluster_id")[["g_window_kWh", "max_pcm_temp_C",
                                     "max_water_temp_C"]].agg(["mean", "min", "max"]).to_string())
    return df


def stage_diagnostics(state, args):
    from src.verify import diagnostics as dg
    chosen = _need(_out(state) / "deployable_design_per_regime.csv", "select")
    years = tuple(SELECT_YEARS[:1])
    kw = dict(n_nodes=N_NODES, dt=PRODUCTION_DT_S)
    for name, fn in [
        ("g13_shield_split", dg.g13_shield_split),
        ("g14_g16_stack_position", dg.g14_g16_stack_position),
        ("g11_one_at_a_time", dg.g11_one_at_a_time),
        ("g17_widened_bounds", dg.g17_widened_bounds),
        ("g15_serve_decomposition", dg.g15_serve_decomposition),
    ]:
        print(f"\n--- {name} ---", flush=True)
        try:
            df = fn(chosen, state, years, **kw)
            df.to_csv(_out(state) / f"{name}.csv", index=False)
            print(f"wrote {name}.csv ({len(df)} rows)")
        except Exception as e:
            print(f"{name} FAILED: {type(e).__name__}: {e}")


def stage_registry(state, args):
    from src.verify.results_registry import main as build
    return build(state)


STAGES = {
    "surrogate": stage_surrogate, "search": stage_search, "active": stage_active,
    "confirm": stage_confirm, "band": stage_band, "select": stage_select,
    "heldout": stage_heldout, "diagnostics": stage_diagnostics,
    "registry": stage_registry,
}
ALL_ORDER = ["surrogate", "search", "confirm", "band", "select",
             "heldout", "diagnostics", "registry"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="tamilnadu")
    ap.add_argument("--stage", required=True,
                    choices=list(STAGES) + ["all"])
    ap.add_argument("--pop", type=int, default=100)
    ap.add_argument("--gen", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--rounds", type=int, default=6)
    ap.add_argument("--batch", type=int, default=10)
    ap.add_argument("--top-n", type=int, default=12,
                    help="front candidates per group carried into confirmation")
    args = ap.parse_args()

    order = ALL_ORDER if args.stage == "all" else [args.stage]
    for st in order:
        print(f"\n{'='*70}\n== {st}\n{'='*70}", flush=True)
        t0 = time.time()
        STAGES[st](args.state, args)
        print(f"-- {st} done in {(time.time()-t0)/60:.2f} min", flush=True)


if __name__ == "__main__":
    main()
