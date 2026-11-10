"""
src/doe/run_sobol_doe.py
===========================
Executes the Sobol DOE (src/doe/sobol_doe.py) against the real simulator,
in parallel, over the EXPLORE years only.

This is the first genuinely expensive stage of the ported pipeline, so
everything about it is built around the parallel layer
(src/parallel/runner.py): one SimTask per (case x explore year), each
carrying only ids and numbers, fanned out across worker processes that
each parse the weather/demand/PCM/config inputs at most once.

YEAR DISCIPLINE (her G5/G6 year-role methodology): the DOE and everything
downstream of it sees EXPLORE years only (2016-2020). The select years
(2021-2023) are reserved for the selection funnel's hard constraints, and
the test years (2011-2015) are locked behind a one-shot held-out test.
Reading a select or test year here would leak it, so this module refuses
to build a task for one rather than trusting the caller.

Each case is run PAIRED (`paired_plain=True`): the same design with zero
capsules, same flow/weather/demand, is simulated in the same worker so
g_window / g_annual / d_overheat are differences against a baseline run
under identical conditions rather than against a separately-configured
run.

Run:  python -m src.doe.run_sobol_doe                 (all 5 explore years)
      python -m src.doe.run_sobol_doe --years 1       (1 year, quick pass)
      python -m src.doe.run_sobol_doe --points 32     (smaller Sobol set)
"""

import argparse
import time

import pandas as pd

from config import RESULTS_DIR
from src.doe.sobol_doe import generate_sobol_cases, SOBOL_SEED
from src.parallel.runner import SimTask, run_tasks_parallel
from src.weather.fetch_multiyear_weather import YEAR_ROLES

EXPLORE_YEARS = sorted(y for y, role in YEAR_ROLES.items() if role == "explore")


def build_tasks(state: str, n_points: int, years, n_nodes: int = 10,
                 timestep_s: float = None):
    for y in years:
        role = YEAR_ROLES.get(y)
        if role != "explore":
            raise ValueError(
                f"year {y} has role {role!r}, not 'explore'. The DOE must not see "
                f"select (2021-2023) or test (2011-2015) years -- that would leak "
                f"the data the selection funnel and the held-out test depend on.")

    cases, manifest = generate_sobol_cases(state, n_points=n_points)
    tasks = []
    for c in cases:
        for y in years:
            tasks.append(SimTask(
                task_id=f"{c.case_id}_y{y}", state=state, cluster_id=c.regime_id,
                pcm_name=c.pcm_id,
                capsule_diameter_m=c.capsule_diameter_m,
                pcm_volume_fraction=c.pcm_volume_fraction,
                flow_rate_kg_s=c.flow_rate_kg_s,
                arrangement=c.capsule_arrangement,
                model="multinode", n_nodes=n_nodes, timestep_s=timestep_s,
                year=y, paired_plain=True))
    manifest["explore_years"] = list(years)
    manifest["n_tasks"] = len(tasks)
    manifest["n_nodes"] = n_nodes
    manifest["timestep_s"] = timestep_s
    return tasks, manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="tamilnadu")
    ap.add_argument("--points", type=int, default=128, help="Sobol points per pair per arrangement")
    ap.add_argument("--years", type=int, default=len(EXPLORE_YEARS),
                    help="how many explore years to use (from the start of the explore block)")
    ap.add_argument("--nodes", type=int, default=10)
    ap.add_argument("--dt", type=float, default=None, help="solver timestep override, seconds")
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    years = EXPLORE_YEARS[:args.years]
    tasks, manifest = build_tasks(args.state, args.points, years, args.nodes, args.dt)

    sim_years = 2 * len(tasks)   # paired: each task runs the PCM tank and its water-only twin
    print(f"Sobol DOE: {manifest['n_total_cases']} cases x {len(years)} explore years "
          f"= {len(tasks)} tasks ({sim_years:,} simulated years, paired)")
    print(f"  seed={SOBOL_SEED}  bounds={manifest['design_bounds_version']}  "
          f"N={args.nodes}  dt={args.dt or 'config default'}  years={years}")

    t0 = time.time()
    df = run_tasks_parallel(tasks, n_workers=args.workers, chunksize=4,
                            progress_every=max(1, len(tasks) // 40), label="sobol-doe")
    elapsed = time.time() - t0

    out_dir = RESULTS_DIR / args.state
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / (args.out or "sobol_doe_results.csv")
    df.to_csv(out, index=False)

    n_valid = int(df["valid"].sum())
    print(f"\n{n_valid}/{len(df)} geometrically valid ({100*n_valid/len(df):.1f}%)")
    if n_valid:
        ok = df[df["valid"]]
        print(f"g_window kWh      : min {ok['g_window_kWh'].min():+8.2f}  "
              f"median {ok['g_window_kWh'].median():+8.2f}  max {ok['g_window_kWh'].max():+8.2f}")
        print(f"max PCM temp C    : max {ok['max_pcm_temp_C'].max():.2f}  (limit 65)")
        print(f"max water temp C  : max {ok['max_water_temp_C'].max():.2f}  (limit 75)")
        print(f"residual %        : max {ok['residual_pct_of_collector'].max():.4f}  (gate 0.5)")
        n_feasible = int(((ok["max_pcm_temp_C"] <= 65.0) & (ok["max_water_temp_C"] <= 75.0)).sum())
        print(f"feasible on safety: {n_feasible}/{n_valid}")
    if (~df["valid"]).any():
        print("\nrejection reasons:")
        print(df[~df["valid"]]["reason"].value_counts().to_string())

    print(f"\nwrote {out}")
    print(f"wall time {elapsed/60:.2f} min for {sim_years:,} simulated years "
          f"({3600*sim_years/elapsed:,.0f} sim-years/hour)")


if __name__ == "__main__":
    main()
