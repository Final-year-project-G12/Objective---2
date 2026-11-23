"""
pipeline.py
=============
Objective 2 entry point for Uttarakhand - the COMMON-PLANT REBUILD (Unified O2+O3 Rebuild Plan, Revision 13; adopted 2026-11-22;
decision record and results: docs/REBUILD_COMMON100L.md). 100 L / 2.0 m2 / 100 L/day, 45 C primary + 50 C secondary, flow fixed at
0.030 kg/s, PCM fraction 2-40 %, robust bottom/centre/top anchor, year roles 2016-19 explore / 2020-21 select / 2022-25 report-only /
2006-10 one-shot test. The legacy 50 L chain is archived in results_legacy_50L_v3/ (its scripts are in git history before c18945a).

Every stage runs the script that produced the saved results, so this file states the order of the chain (plan levels L0-L9 + M1).
  o1           L1   O1 manifest (Option B): scripts/r1_o1_manifest.py
  weather      L2   2006-2010 fetch, inventory, member-point weather, weather-only audit + input manifest
  verify       L3   simulator verification on the 100 L plant (dt halving, nodes, closure, IS 12976 standing loss), 4 regimes
  baseline     L4   exact water-only runs at the fixed flow (explore + select, 150 s and 37.5 s), 4 regimes
  screening    L4   Taguchi L9, 12 (regime, PCM) pairs, explore years, three anchors
  doe          L5   Sobol DOE (128 points, cheap fidelity, three anchors), 12 pairs, then repair of memory errors
  surrogate    L5   five surrogate families per pair (nn_ensemble, xgboost, rsm_quadratic, gp_ard, stacked)
  optimize     L6   NSGA-II + committee active learning with the box vertices, 12 pairs
  grid         L7   720-run dense grid, rank-1 PCM, 4 regimes
  band         L7   repeatability band (recipe frozen in docs/REBUILD_COMMON100L.md section 5), 4 regimes
  assess       L7   grid check, seed stability, AL summary, boundary check, band table
  select       L7   frozen funnel on 2020-2021 at full fidelity (section 3e), 4 regimes
  test         L9   the ONE-SHOT 2006-2010 test. Refuses if this plant's lock already exists (results/locks/o2_test_<hash>.lock)
  report       L9   report-only years 2022-2025 (only after the test lock)
  handoff      L9   Objective 3 contract on the common plant
  m1                MATLAB checkpoint M1 (export from the kernel, then matlab/m1_checkpoint.m; needs MATLAB on PATH or --matlab)
  figures           rebuild figures (results/plots_common100L/)
  supplementary     post-result studies (sensitivities, auxiliary heater, plant cases, bound diagnostic), never for selection
  manifest          SHA-256 of every output file (plan R20)
  simulate          one design at the cheap fidelity (quick check, no files written)
  status            which stage outputs exist and whether the test lock is set

`--stage all` runs o1 ... handoff, m1, figures, supplementary, manifest and stops at the first failing stage; it never runs `test` unless
`--include-test` is given. SAFETY: once the test lock exists the stages that decide the frozen design (baseline ... select) refuse,
unless `--allow-invalidate` is passed knowingly.

USAGE
  python pipeline.py --state uttarakhand --stage status
  python pipeline.py --state uttarakhand --stage handoff
  python pipeline.py --state uttarakhand --stage optimize --dry-run
  python pipeline.py --state uttarakhand --stage simulate --cluster 1 --pcm-rank 1 --radius-mm 30 --fraction 0.1 --arrangement staggered
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
PY = sys.executable
REGIMES = (0, 1, 2, 3)
PAIRS = [(c, k) for c in REGIMES for k in (1, 2, 3)]
DECIDING = {"baseline", "screening", "doe", "surrogate", "optimize", "grid", "band", "assess", "select"}
ORDER = ["o1", "weather", "verify", "baseline", "screening", "doe", "surrogate", "optimize", "grid", "band", "assess", "select",
         "report", "handoff", "m1", "figures", "supplementary", "manifest"]
ENV = {"PYTHONPATH": str(ROOT), "PYTHONIOENCODING": "utf-8"}


def lock_path():
    sys.path.insert(0, str(ROOT))
    from src.weather import roles
    return roles.test_lock_path()


def cmd(*args, env=None):
    return {"argv": [PY, *map(str, args)], "env": {**ENV, **(env or {})}}


def commands(stage, matlab="matlab"):
    """A list of groups; commands inside a group may run in parallel (--jobs), groups run in order."""
    s = "scripts/"
    if stage == "o1":
        return [[cmd(s + "r1_o1_manifest.py")]]
    if stage == "weather":
        return [[cmd(s + "r2_fetch_test_weather.py")], [cmd("-c", "from src.weather.inventory import build_inventory; build_inventory()")],
                [cmd(s + "r7_member_weather.py")], [cmd(s + "r2_weather_audit.py")]]
    if stage == "verify":
        return [[cmd(s + "r3_verification.py", c) for c in REGIMES]]
    if stage == "baseline":
        return [[cmd(s + "g8_build_plain_baseline.py", c) for c in REGIMES]]
    if stage == "screening":
        return [[cmd(s + "g8_s1_screening.py", c, k) for c, k in PAIRS]]
    if stage == "doe":
        return [[cmd(s + "g8_s2_doe.py", c, k) for c, k in PAIRS], [cmd(s + "g8_s2_repair.py")]]
    if stage == "surrogate":
        return [[cmd(s + "g8_s3_compare.py")]]
    if stage == "optimize":
        return [[cmd(s + "g9_s4_s5.py", c, k) for c, k in PAIRS]]
    if stage == "grid":
        return [[cmd(s + "g9_s6_grid.py", c, 1) for c in REGIMES]]
    if stage == "band":
        return [[cmd(s + "g9_band.py", c) for c in REGIMES]]
    if stage == "assess":
        return [[cmd(s + "g9_assess.py")]]
    if stage == "select":
        return [[cmd(s + "g10_select.py", c) for c in REGIMES]]
    if stage == "test":
        return [[cmd(s + "g10_test.py", "--confirm-run-once")]]
    if stage == "report":
        return [[cmd(s + "g10_test.py", "--report-years")]]
    if stage == "handoff":
        return [[cmd("-m", "src.handoff.build_obj3_contract_common100L")]]
    if stage == "m1":
        return [[cmd(s + "m1_export.py")],
                [{"argv": [matlab, "-batch", f"addpath('{ROOT / 'matlab'}'); m1_checkpoint('{ROOT}')"], "env": {}}]]
    if stage == "figures":
        return [[cmd(s + "r9_rebuild_figures.py")]]
    if stage == "supplementary":
        return [[cmd(s + "r10_supplementary.py", "sens", c) for c in REGIMES] +
                [cmd(s + "r10_supplementary.py", "cases", n) for n in ("d70", "d150", "legacy", "t150")] +
                [cmd(s + "r10_supplementary.py", "aux", c) for c in REGIMES] + [cmd(s + "r10_supplementary.py", "boundary")]]
    if stage == "manifest":
        return [[cmd(s + "r11_output_manifest.py")]]
    raise KeyError(stage)


def run_groups(groups, jobs, dry):
    for group in groups:
        running = []
        for c in group:
            print("  $", " ".join(Path(a).name if a == PY else a for a in c["argv"]), flush=True)
            if dry:
                continue
            while len(running) >= jobs:
                running = _reap(running)
            running.append((c, subprocess.Popen(c["argv"], cwd=ROOT, env={**os.environ, **c["env"]})))
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
    lk = lock_path()
    print("O2 test lock:", "SET " + json.loads(lk.read_text())["run_id"] if lk.exists() else "not set", f"({lk.name})")
    checks = {"o1": "o1_manifest_uttarakhand.json", "weather": "l2_input_manifest.json", "verify": "l3_timestep.csv",
              "baseline": "plain_baseline_select_dt37p5_r0.csv", "screening": "g8_s1_r0_p1.csv", "doe": "g8_s2_r0_p1.csv",
              "surrogate": "g8_s3_selection.csv", "optimize": "g9_points_r0_p1.csv", "grid": "g9_s6_grid_r0_p1.csv",
              "band": "g9_band_r0.csv", "assess": "wp6_band.csv", "select": "g10_selection_r0.json", "test": "o2_test_2006_2010.csv",
              "report": "o2_report_2022_2025.csv", "handoff": "obj3_environment_contract_uttarakhand_common100L.json",
              "m1": "m1_matlab/m1_gate.txt", "figures": "plots_common100L/rb1_pareto_fronts.png",
              "supplementary": "supp_boundary_below_2pct.csv", "manifest": "o2_output_manifest.json"}
    for k, f in checks.items():
        print(f"  {k:14s} {'present' if (RD / f).exists() else 'MISSING':8s} results/{f}")


def stage_simulate(a):
    sys.path.insert(0, str(ROOT))
    from src.design.box import flow_fixed
    from src.io_utils import get_regime
    from src.optimize.evaluate import evaluate_design, flatten
    pcm = get_regime("uttarakhand", a.cluster)["pcm_shortlist"][a.pcm_rank - 1]
    res = evaluate_design(a.cluster, pcm, a.radius_mm / 1000.0, a.fraction, flow_fixed(), a.arrangement, purpose="explore", fidelity="cheap")
    print(json.dumps(flatten(res), indent=2, default=str))


def main():
    ap = argparse.ArgumentParser(description="Objective 2 pipeline - Uttarakhand common-plant rebuild")
    ap.add_argument("--state", required=True, help="uttarakhand")
    ap.add_argument("--stage", required=True, choices=ORDER + ["test", "simulate", "status", "all"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--jobs", type=int, default=3, help="parallel jobs inside a stage (this PC ran out of memory at 8)")
    ap.add_argument("--allow-invalidate", action="store_true", help="allow re-deciding the design although the test lock exists")
    ap.add_argument("--include-test", action="store_true", help="with --stage all: also run the one-shot test (the lock refuses a rerun)")
    ap.add_argument("--matlab", default="matlab", help="MATLAB executable for the m1 stage (e.g. D:\\bin\\matlab.exe)")
    ap.add_argument("--cluster", type=int, default=0)
    ap.add_argument("--pcm-rank", type=int, default=1, choices=(1, 2, 3))
    ap.add_argument("--radius-mm", type=float, default=30.0)
    ap.add_argument("--fraction", type=float, default=0.10)
    ap.add_argument("--arrangement", default="staggered", choices=["single-layer", "staggered", "radial"])
    a = ap.parse_args()
    if a.state != "uttarakhand":
        raise SystemExit("this pipeline is the Uttarakhand rebuild")
    if a.stage == "status":
        return stage_status()
    if a.stage == "simulate":
        return stage_simulate(a)
    stages = [a.stage]
    if a.stage == "all":
        stages = ORDER[:ORDER.index("report")] + (["test"] if a.include_test else []) + ORDER[ORDER.index("report"):]
    blocked = [s for s in stages if s in DECIDING and lock_path().exists() and not a.allow_invalidate]
    if blocked and not a.dry_run:
        raise SystemExit(f"refusing {blocked}: the 2006-2010 test lock exists, so re-deciding the design would make the one-shot test "
                         "meaningless. Pass --allow-invalidate only if that is really intended.")
    t0 = time.time()
    for s in stages:
        print(f"\n### stage {s}")
        run_groups(commands(s, a.matlab), max(1, a.jobs), a.dry_run)
    print(f"\nDONE {', '.join(stages)} in {(time.time() - t0) / 60:.1f} min" + (" (dry run)" if a.dry_run else ""))


if __name__ == "__main__":
    main()
