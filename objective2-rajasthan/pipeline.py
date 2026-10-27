"""
pipeline.py
=============
Objective 2 entry point for Rajasthan - the current chain (gates G1-G12 of OBJECTIVE2_REDESIGN_PROPOSED_PLAN.md).
The legacy chain (Extra Trees surrogate, 600 random candidates, medoid-plus-noise robustness, retargeted PCM list) is retired;
a copy of the old entry point is kept in the deleted legacy copy and is not wired to anything.

Every stage runs the script that produced the saved results (scripts/g*.py, src/...) with the same arguments, so this file is the
single place that states the order of the chain. Stages that take hours say so below. Output goes to results/.

  verify       G6   Phase-4 verification battery on the repaired simulator with O1's top-3 PCMs            (minutes)
  sensitivity  G7   bounded sensitivity study (explore years 2018-2019), 3 regimes + flow/packing supplement (about 1 h)
  baseline     G8   water-only flow grids for the paired baseline, 3 regimes                               (about 30 min)
  screening    G8   S1 Taguchi L9 screening, 9 (regime, PCM) pairs                                          (about 1 h)
  doe          G8   S2 Sobol DOE (128 points x 5 explore years), 9 pairs, then repair of memory errors     (hours)
  surrogate    G8   S3 surrogate comparison (NN ensemble / XGBoost / quadratic RSM) with within-pair validation
  band         G9   WP6 repeatability band, 3 regimes
  optimize     G9   S4/S5 NSGA-II + active learning for 9 pairs (5 rounds), then the box-vertex step + 3 more rounds
                    (G9_WARM=1 G9_VERTICES=1, files *_ext2), then S6 dense grid and the G9 assessment   (many hours)
  select       G10  final design per regime on the select years 2021-2023
  heldout      G10  the one-shot held-out test on the untouched years 2011-2015 (v3, cap 30 %). REFUSES when results/held_out_test.lock exists.
  ablation     G11  ablations and controls around the chosen design, explore years, 3 regimes
  report       G12  results registry, generated results document, document-reference check
  handoff      G12  Objective 3 environment contract v2
  plots        G12  figures from the saved results (results/plots/)
  simulate          one design, explore/select years, paired against the same-flow water-only tank (quick check, no files written)
  status            which stage outputs exist, and whether the held-out lock is set

`--stage all` runs verify ... handoff, plots in that order and stops at the first failing stage. It never runs `heldout`
unless `--include-heldout` is given (the lock still refuses a second run).

SAFETY. The v1 (cap 20 %) held-out test on 2024-2025 is archived in results/v1_cap20/ and those years are labelled used.
The v3 held-out test runs once (run id in results/held_out_test.lock). The stages that decide the frozen designs
(baseline, screening, doe, surrogate, band, optimize, select) would overwrite them and make that run meaningless, so they refuse
while the lock exists unless `--allow-invalidate` is passed. The reporting stages (report, handoff, plots, status) are always safe.
Re-deriving r0_p1 from scratch follows the general recipe (5 rounds, then vertices); the saved r0_p1 files took one extra step
(an intermediate `_ext` run) first, see docs/03_OPTIMISATION_PIPELINE.md.

USAGE
  python pipeline.py --state rajasthan --stage status
  python pipeline.py --state rajasthan --stage report
  python pipeline.py --state rajasthan --stage plots
  python pipeline.py --state rajasthan --stage handoff
  python pipeline.py --state rajasthan --stage simulate --cluster 0 --pcm-rank 1 --radius-mm 40 --fraction 0.2 --flow 0.025 --arrangement staggered
  python pipeline.py --state rajasthan --stage optimize --dry-run        # print the commands only
  python pipeline.py --state rajasthan --stage all --allow-invalidate --jobs 3
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RD = ROOT / "results"
LOCK = RD / "held_out_test.lock"
PY = sys.executable
REGIMES = (0, 1, 2)
PAIRS = [(c, k) for c in REGIMES for k in (1, 2, 3)]

# stages that change what the frozen designs are; refused while the held-out lock exists
DECIDING = {"baseline", "screening", "doe", "surrogate", "band", "optimize", "select"}
ORDER = ["verify", "sensitivity", "baseline", "screening", "doe", "surrogate", "band", "optimize", "select",
         "ablation", "report", "handoff", "plots"]


def cmd(*args, env=None):
    return {"argv": [PY, *map(str, args)], "env": env or {}}


def commands(stage):
    """Return a list of groups; commands inside a group may run in parallel (--jobs), groups run in order."""
    s = "scripts/"
    if stage == "verify":
        return [[cmd(s + "g6_phase4_o1.py")]]
    if stage == "sensitivity":
        return [[cmd(s + "g7_sensitivity.py", c) for c in REGIMES], [cmd(s + "g7_flow_baseline_and_packing.py")]]
    if stage == "baseline":
        return [[cmd(s + "g8_build_plain_baseline.py", c) for c in REGIMES]]
    if stage == "screening":
        return [[cmd(s + "g8_s1_screening.py", c, k) for c, k in PAIRS]]
    if stage == "doe":
        return [[cmd(s + "g8_s2_doe.py", c, k) for c, k in PAIRS], [cmd(s + "g8_s2_repair.py")]]
    if stage == "surrogate":
        return [[cmd(s + "g8_s3_compare.py")]]
    if stage == "band":
        return [[cmd(s + "g9_band.py", c) for c in REGIMES]]
    if stage == "optimize":
        return [[cmd(s + "g9_s4_s5.py", c, k) for c, k in PAIRS],
                [cmd(s + "g9_s4_s5.py", c, k, env={"G9_WARM": "1", "G9_VERTICES": "1"}) for c, k in PAIRS],
                [cmd(s + "g9_s6_grid.py", c, 1) for c in REGIMES],
                [cmd(s + "g9_assess.py")]]
    if stage == "select":
        return [[cmd(s + "g10_select.py", c) for c in REGIMES]]
    if stage == "heldout":
        return [[cmd(s + "g10_test.py", "--confirm-run-once")]]
    if stage == "ablation":
        return [[cmd(s + "g11_ablation.py", c) for c in REGIMES]]
    if stage == "report":
        return [[cmd(s + "g12_registry.py")], [cmd(s + "g12_results_doc.py")], [cmd(s + "g12_verify_docs.py")]]
    if stage == "handoff":
        return [[cmd("-m", "src.handoff.build_obj3_contract_v2", env={"PYTHONPATH": "."})]]
    if stage == "plots":
        return [[cmd("-m", "src.plots.make_plots_results")], [cmd("-m", "src.plots.make_plots_phases")]]
    raise KeyError(stage)


def run_groups(groups, jobs, dry):
    for group in groups:
        running = []
        for c in group:
            shown = " ".join(f"{k}={v}" for k, v in c["env"].items())
            print("  $", (shown + " " if shown else "") + " ".join(Path(a).name if a == PY else a for a in c["argv"]), flush=True)
            if dry:
                continue
            while len(running) >= jobs:
                running = _reap(running)
            env = {**os.environ, **c["env"]}
            running.append((c, subprocess.Popen(c["argv"], cwd=ROOT, env=env)))
        while running:
            running = _reap(running)


def _reap(running):
    time.sleep(0.5)
    still = []
    for c, p in running:
        rc = p.poll()
        if rc is None:
            still.append((c, p))
        elif rc != 0:
            for _, q in still:
                q.terminate()
            raise SystemExit(f"FAILED (exit {rc}): {' '.join(c['argv'])}")
    return still


def stage_status():
    print("held-out lock:", "SET (" + LOCK.read_text(encoding="utf-8").strip().replace("\n", " ")[:120] + ")" if LOCK.exists() else "not set")
    checks = {
        "verify": "phase4_verification_o1_pcms.txt", "sensitivity": "g7_sensitivity_r0.csv", "baseline": "plain_baseline_select_r0.csv",
        "screening": "g8_s1_r0_p1.csv", "doe": "g8_s2_r0_p1.csv", "surrogate": "g8_s3_selection.csv", "band": "wp6_band.csv",
        "optimize": "g9_grid_check.csv", "select": "g10_selection_r0.json", "heldout": "g10_heldout_results.csv",
        "ablation": "g11_ablation_r0.csv", "report": "results_registry.csv", "handoff": "obj3_environment_contract_rajasthan_v2.json",
        "plots": "plots/fig1_front_vs_grid.png",
    }
    for k, f in checks.items():
        print(f"  {k:12s} {'present' if (RD / f).exists() else 'MISSING':8s} results/{f}")


def stage_simulate(a):
    from src.io_utils import o1_top3
    from src.optimize.evaluate import evaluate_design, flatten
    pcm = o1_top3("rajasthan")[a.cluster][a.pcm_rank - 1]
    res = evaluate_design(a.cluster, pcm, a.radius_mm / 1000.0, a.fraction, a.flow, a.arrangement, purpose=a.purpose)
    print(json.dumps(flatten(res), indent=2, default=str))
    if res.get("per_year"):
        print("per year:", json.dumps([{k: round(v, 3) if isinstance(v, float) else v for k, v in y.items()} for y in res["per_year"]]))


def main():
    ap = argparse.ArgumentParser(description="Objective 2 pipeline - Rajasthan (current chain, G1-G12)")
    ap.add_argument("--state", required=True, help="rajasthan (the rework exists for Rajasthan only)")
    ap.add_argument("--stage", required=True, choices=ORDER + ["heldout", "simulate", "status", "all"])
    ap.add_argument("--dry-run", action="store_true", help="print the commands without running them")
    ap.add_argument("--jobs", type=int, default=3, help="parallel jobs inside a stage (9 parallel jobs ran out of memory once)")
    ap.add_argument("--allow-invalidate", action="store_true",
                    help="allow stages that overwrite the frozen designs even though the held-out lock exists")
    ap.add_argument("--include-heldout", action="store_true", help="with --stage all: also call the held-out stage (the lock refuses a rerun)")
    ap.add_argument("--cluster", type=int, default=0)
    ap.add_argument("--pcm-rank", type=int, default=1, choices=(1, 2, 3))
    ap.add_argument("--radius-mm", type=float, default=40.0)
    ap.add_argument("--fraction", type=float, default=0.20)
    ap.add_argument("--flow", type=float, default=0.025)
    ap.add_argument("--arrangement", default="staggered", choices=["single-layer", "staggered", "radial"])
    ap.add_argument("--purpose", default="explore", choices=["explore", "select"], help="held-out years are not reachable from here")
    a = ap.parse_args()
    if a.state != "rajasthan":
        raise SystemExit("the current chain exists for Rajasthan only; the other states still use their own frozen pipelines")

    if a.stage == "status":
        return stage_status()
    if a.stage == "simulate":
        return stage_simulate(a)

    stages = ORDER + (["heldout"] if a.include_heldout else []) if a.stage == "all" else [a.stage]
    if a.stage == "all" and a.include_heldout:      # keep heldout after select/ablation-independent stages, before reporting
        stages = ORDER[:ORDER.index("ablation")] + ["heldout"] + ORDER[ORDER.index("ablation"):]
    blocked = [s for s in stages if s in DECIDING and LOCK.exists() and not a.allow_invalidate]
    if blocked and not a.dry_run:
        raise SystemExit(f"refusing {blocked}: results/held_out_test.lock exists, so re-deciding the designs would make the held-out "
                         "run meaningless. Pass --allow-invalidate if that is really intended (the held-out years can then no longer be "
                         "treated as untouched).")
    t0 = time.time()
    for s in stages:
        print(f"\n### stage {s}")
        run_groups(commands(s), max(1, a.jobs), a.dry_run)
    print(f"\nDONE {', '.join(stages)} in {(time.time() - t0) / 60:.1f} min" + (" (dry run)" if a.dry_run else ""))


if __name__ == "__main__":
    main()
