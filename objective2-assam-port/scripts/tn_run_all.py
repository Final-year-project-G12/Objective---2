"""
scripts/tn_run_all.py
========================
Runs her whole gate sequence for Tamil Nadu, in dependency order, with
each stage parallelised across the independent work it contains.

Her scripts are used UNMODIFIED. This file only decides the order and
what runs concurrently, so every result is reproducible by running her
command lines by hand. Each stage's shape is taken from its own
`__main__` block:

  no args         -> one process
  <cluster>       -> 3 processes (one per regime)
  <cluster> <rank>-> 9 processes (one per regime x O1-PCM-rank pair)

ORDER MATTERS, and not only for file dependencies: the year roles have to
stay apart. Explore years (2016-2020) feed screening, the DOE, the
surrogates and the search; select years (2021-2023) decide the winner;
the test years (2011-2015) are spent ONCE, behind her atomic lock. g10_test
is therefore last among the result-producing stages and is skipped unless
asked for explicitly.

Usage:
  python scripts/tn_run_all.py --list
  python scripts/tn_run_all.py --from g8_s2_doe --to g9_s4_s5
  python scripts/tn_run_all.py --only g8_s3_compare
  python scripts/tn_run_all.py --all            # everything except g10_test
  python scripts/tn_run_all.py --only g10_test --i-mean-it
"""

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import STATE   # noqa: E402

# (script, shape, note). shape: "once" | "regime" | "pair"
STAGES = [
    ("g2_timestep_convergence",   "custom", "timestep convergence ladder"),
    ("g4_multinode_report",       "once",   "single vs multi-node, plain tank"),
    ("g3_metrics_report",         "once",   "TES metric definitions on real runs"),
    ("g6_phase4_o1",              "once",   "Phase-4 gates on the O1 shortlist"),
    ("g7_flow_baseline_and_packing", "once", "flow baseline + packing check"),
    ("g7_sensitivity",            "regime", "design-variable ranges"),
    ("g8_build_plain_baseline",   "regime", "paired water-only flow grids"),
    ("g8_s1_screening",           "pair",   "Taguchi L9 screening + ANOVA"),
    ("g8_s2_doe",                 "pair",   "128-point scrambled-Sobol DOE"),
    ("g8_s3_compare",             "once",   "surrogate bake-off (5 families)"),
    ("g9_s4_s5",                  "pair",   "NSGA-II + active learning"),
    # "regime", not "pair": g9_s6_grid now loops its own GRID_RANKS (rank 1
    # only by default -- see that script's SCOPE note), so launching it per
    # (regime, rank) would re-run the same work three times.
    ("g9_s6_grid",                "regime", "720-design grid cross-check (rank-1, 1 yr)"),
    ("g9_band",                   "regime", "repeatability band per objective"),
    ("g9_assess",                 "once",   "seed stability, coverage, boundary"),
    # "regime", not "once": g20_gp_bo_comparison.py's usage line is
    # `<cluster_id> [pcm_rank] [n_init] [n_iter] [seed]` -- cluster_id is
    # REQUIRED. Registered as "once" it was launched with no arguments at all
    # and died on IndexError at argv[0] before doing any work.
    ("g20_gp_bo_comparison",      "regime", "GP + Bayesian optimisation track"),
    ("g10_select",                "regime", "S0/S1/S2 funnel + tie-break"),
    ("g11_ablation",              "regime", "one-at-a-time ablations"),
    ("g13_issue4_shield_split",   "regime", "shield split, water vs PCM side"),
    ("g14_issue5_controls",       "regime", "interior-anchor controls"),
    ("g15_issue6_anchor",         "regime", "stack-position sensitivity"),
    ("g16_issue3_serve",          "regime", "evening / night-serve decomposition"),
    ("g17_issue2_widen",          "regime", "widened-bounds diagnostic"),
    ("g18_issue1_compare",        "once",   "box-vertex step ablation"),
    ("g21_sizing_study",          "regime", "tank/collector sizing study"),
    ("g22_sensitivity_extra",     "regime", "extra sensitivity gates"),
    ("g23_chen_benchmark",        "regime", "Chen et al. benchmark reproduction"),
    ("g24_flow_fr_study",         "regime", "flow-dependent F_R (Eldokaishi)"),
    ("g12_registry",              "once",   "results registry"),
    ("g12_results_doc",           "once",   "results document"),
    ("g12_verify_docs",           "once",   "doc/number cross-check"),
    ("g10_test",                  "once",   "ONE-SHOT held-out test (locked)"),
    ("g25_obj3_contract",         "once",   "Objective 3 environment contract (handoff)"),
]
# Stages whose CLI is neither "once", "regime" nor "pair". g2 takes a
# comma-separated dt ladder and an output path, and her report runs it
# twice: 300/150/75 to show 300 s failing, then 150/75/37.5 to show 150 s
# passing. Reproduced exactly.
CUSTOM_JOBS = {
    "g2_timestep_convergence": [
        ["300,150,75", "results/g2_timestep_convergence_300_150_75.csv"],
        ["150,75,37.5", "results/g2_timestep_convergence_150_75_37p5.csv"],
    ],
}

LOCKED = {"g10_test"}
NAMES = [s[0] for s in STAGES]


def jobs_for(shape, name=None):
    if shape == "custom":
        return CUSTOM_JOBS[name]
    if shape == "once":
        return [[]]
    if shape == "regime":
        return [[str(c)] for c in range(3)]
    return [[str(c), str(r)] for c in range(3) for r in range(1, 4)]


def run_stage(name, shape, max_par, dry=False):
    script = ROOT / "scripts" / f"{name}.py"
    if not script.exists():
        print(f"  SKIP {name}: no such script")
        return True
    jobs = jobs_for(shape, name)
    par = min(len(jobs), max_par)
    print(f"\n=== {name} ({shape}, {len(jobs)} job(s), {par} at a time) ===", flush=True)
    if dry:
        for j in jobs:
            print(f"    python scripts/{name}.py {' '.join(j)}")
        return True

    env = dict(os.environ)
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                "NUMEXPR_NUM_THREADS"):
        env.setdefault(var, "1")

    t0 = time.time()
    queued, running, failed = list(jobs), [], []
    while queued or running:
        while queued and len(running) < par:
            job = queued.pop(0)
            # args can contain paths/commas (g2), so the log name is a
            # sanitised, length-capped version of them
            tag = re.sub(r"[^A-Za-z0-9._-]+", "_", "_".join(job)) or "all"
            tag = tag[:60].strip("_")
            log = ROOT / "results" / f"_log_{name}_{tag}.log"
            fh = open(log, "w", encoding="utf-8")
            p = subprocess.Popen([sys.executable, str(script)] + job, cwd=str(ROOT),
                                 stdout=fh, stderr=subprocess.STDOUT, env=env)
            running.append((p, tag, fh, log, time.time()))
            print(f"    start {tag}", flush=True)
        time.sleep(5)
        still = []
        for p, tag, fh, log, started in running:
            if p.poll() is None:
                still.append((p, tag, fh, log, started))
            else:
                fh.close()
                el = (time.time() - started) / 60
                if p.returncode == 0:
                    print(f"    ok    {tag}  ({el:.1f} min)", flush=True)
                else:
                    failed.append((tag, log))
                    print(f"    FAIL  {tag}  rc={p.returncode}  ({el:.1f} min)", flush=True)
        running = still

    print(f"--- {name} finished in {(time.time()-t0)/60:.1f} min, "
          f"{len(failed)} failure(s)")
    for tag, log in failed:
        try:
            tail = log.read_text(encoding="utf-8", errors="ignore").strip().splitlines()[-8:]
            print(f"    [{tag}] " + "\n            ".join(tail))
        except Exception:
            pass
    return not failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--from", dest="start", default=None)
    ap.add_argument("--to", dest="end", default=None)
    # os.cpu_count() reports LOGICAL processors, which badly overcommits a
    # hybrid mobile CPU: on the i7-1255U this runs on (2 P-cores + 8 E-cores,
    # 12 logical) nine concurrent jobs delivered 0.26 sim-years/s in aggregate
    # against 0.21 from a SINGLE job -- 9x the processes for 1.2x the work,
    # because most of them land on E-cores and the box has ~1.4 GB free RAM.
    # Default to the physical P-core-ish count instead; pass --workers to override.
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--i-mean-it", action="store_true",
                    help="required to run the one-shot held-out test")
    ap.add_argument("--keep-going", action="store_true",
                    help="continue to later stages even if one fails")
    args = ap.parse_args()

    if args.list:
        print(f"state = {STATE}\n")
        for i, (n, shape, note) in enumerate(STAGES):
            mark = "  [LOCKED]" if n in LOCKED else ""
            print(f"  {i:2d}  {n:30s} {shape:7s} {note}{mark}")
        return 0

    if args.only:
        chosen = [s for s in STAGES if s[0] in args.only]
        unknown = set(args.only) - set(NAMES)
        if unknown:
            sys.exit(f"unknown stage(s): {sorted(unknown)}")
    elif args.all or args.start or args.end:
        i0 = NAMES.index(args.start) if args.start else 0
        i1 = NAMES.index(args.end) + 1 if args.end else len(STAGES)
        chosen = STAGES[i0:i1]
    else:
        sys.exit("pick --list, --all, --only, or --from/--to")

    skipped = [s for s in chosen if s[0] in LOCKED and not args.i_mean_it]
    chosen = [s for s in chosen if s not in skipped]
    for n, _, _ in skipped:
        print(f"skipping {n}: one-shot held-out test, pass --i-mean-it to run it")

    print(f"running {len(chosen)} stage(s), up to {args.workers} processes each")
    t0 = time.time()
    for name, shape, _note in chosen:
        ok = run_stage(name, shape, args.workers, dry=args.dry_run)
        if not ok and not args.keep_going:
            print(f"\nstopping at {name} (pass --keep-going to continue past failures)")
            return 1
    print(f"\nall requested stages done in {(time.time()-t0)/60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
