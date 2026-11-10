"""Throughput benchmark for the parallel execution layer.

Reports the two numbers that set the compute budget for every expensive
stage (Sobol DOE, NSGA-II, dense grid, diagnostics), and that make the
comparison against Rajasthan's quoted kernel speed a measured claim:

  * per-case wall time, ONE process -> like-for-like against her
    "1.4-3.1 s/year" (a one-process-per-year figure)
  * pooled throughput               -> what the DOE's elapsed time follows

NOTE the __main__ guard: on Windows, ProcessPoolExecutor spawns fresh
interpreters that IMPORT this file, so anything at module level runs again
in every worker. Without the guard each worker builds its own pool and the
whole thing dies with BrokenProcessPool.

Run:  python benchmark_parallel.py [n_cases]
"""

import sys
import time

import numpy as np

from src.io_utils import load_design_bounds
from src.parallel.runner import SimTask, run_tasks_parallel, run_tasks_serial, warm_jit

STATE = "tamilnadu"
PCM = "n-Hexacosane (C26)"
ARRANGEMENTS = ["single-layer", "staggered", "radial"]


def make_tasks(model, n_nodes, n, paired=False):
    bounds = load_design_bounds()
    rng = np.random.default_rng(20261028)   # same designs for every configuration
    d_lo, d_hi = bounds["capsule_diameter_m"]["min"], bounds["capsule_diameter_m"]["max"]
    f_lo, f_hi = bounds["flow_rate_kg_s"]["min"], bounds["flow_rate_kg_s"]["max"]
    n_lo, n_hi = bounds["capsule_count"]["min"], bounds["capsule_count"]["max"]
    tasks = []
    for i in range(n):
        tasks.append(SimTask(
            task_id=f"{model}{n_nodes}_{i:04d}", state=STATE, cluster_id=i % 3, pcm_name=PCM,
            capsule_diameter_m=float(rng.uniform(d_lo, d_hi)),
            n_capsule=int(rng.integers(n_lo, n_hi + 1)),
            flow_rate_kg_s=float(rng.uniform(f_lo, f_hi)),
            arrangement=ARRANGEMENTS[i % 3],
            model=model, n_nodes=n_nodes, paired_plain=paired,
        ))
    return tasks


def main():
    n_cases = int(sys.argv[1]) if len(sys.argv) > 1 else 240
    n_serial = max(6, n_cases // 20)
    print(f"Benchmark: {n_cases} cases pooled, {n_serial} cases serial\n")
    warm_jit()

    table = []
    for label, model, n_nodes, paired in [
        ("multinode N=10", "multinode", 10, False),
        ("multinode N=10 paired", "multinode", 10, True),
        ("single-node", "single", 1, False),
    ]:
        print(f"=== {label} ===")
        ser = run_tasks_serial(make_tasks(model, n_nodes, n_serial, paired), label=label)
        t0 = time.time()
        par = run_tasks_parallel(make_tasks(model, n_nodes, n_cases, paired), label=label)
        wall_par = time.time() - t0

        years_per_case = 2 if paired else 1
        s_per_year_serial = ser["sim_wall_s"].mean() / years_per_case
        pooled_years_per_h = n_cases * years_per_case / wall_par * 3600
        table.append((label, s_per_year_serial, pooled_years_per_h,
                      int(par["valid"].sum()), len(par)))
        print()

    print("=" * 86)
    print(f"{'configuration':24s} {'s/sim-year (1 proc)':>20s} {'sim-years/hour pooled':>23s} {'valid':>12s}")
    print("-" * 86)
    for label, s_yr, yr_h, nv, nt in table:
        print(f"{label:24s} {s_yr:20.3f} {yr_h:23,.0f} {f'{nv}/{nt}':>12s}")
    print("=" * 86)
    print("\nReference: Rajasthan's report quotes 1.4-3.1 s/year for her 10-node numba\n"
          "kernel in one process (= 1,160-2,570 sim-years/hour if she pooled 1 core).")


if __name__ == "__main__":
    main()
