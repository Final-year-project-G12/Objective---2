"""
run_all_tamilnadu.py
=============================================================================
Runs every Objective 2 stage for Tamil Nadu, in the correct dependency
order, in one invocation — via `subprocess`, exactly as if you'd typed
each command from README.md / pipeline.py's own docstring yourself in
sequence (no shared Python process between stages).

Mirrors the style of Objective 1's own `run_all_tamilnadu.py`
(era5-tamilnadu/run_all_tamilnadu.py): a required, stop-on-first-failure
BUILD chain, followed by a required, stop-on-first-failure PIPELINE
chain (each pipeline stage invoked as `python pipeline.py --state
tamilnadu --stage <stage>`), skipping only the interactive `simulate`
demo stage (see below).

ORDER AND WHY:
  BUILD (from README.md, "in this order"):
  1. build_input_package.py   — freezes/hashes Obj1 outputs into
                                 data/objective1/ (requires OBJ1_ROOT in
                                 config.py to point at era5-tamilnadu)
  2. build_regime_weather.py  — per-cluster medoid weather -> data/weather/
  3. build_demand_profile.py  — canonical 300 L/day draw -> data/demand/

  PIPELINE (from pipeline.py's own docstring, Phases 2-8):
  4. geometry      — Phase 2 self-test (state-agnostic, but --state is
                      still required by argparse)
  5. verify        — Phase 4 gates 1-5 (reads the BUILD outputs above)
  6. doe           — Phase 5 DOE batch + train/hold-out split
  7. surrogate     — Phase 6 surrogate training + hold-out evaluation
  8. multifidelity — Phase 6b multi-fidelity augmentation
  9. optimize      — Phase 7 optimization + simulator confirmation
  10. plots        — Phase 2-7 justification plots
  11. robustness   — Phase 8a Monte Carlo robustness analysis
  12. handoff      — Phase 8b recommendation cards + Objective 3 contract

NOT RUN, AND WHY (excluded entirely):
  `simulate` — this is a single-case, hand-parameterized demo/debugging
  stage (`--cluster`, `--pcm`, `--diameter`, `--count`, `--flow`), not a
  step every full run needs; `doe` already runs many such cases in
  batch. Run it yourself, separately, whenever you want to inspect one
  specific design by hand.

HOW TO RUN:
  python run_all_tamilnadu.py                  # everything, in order
  python run_all_tamilnadu.py --dry-run         # print the order, run nothing
  python run_all_tamilnadu.py --from doe        # resume starting at a given
                                                 # stage/script (skips
                                                 # everything before it)
  python run_all_tamilnadu.py --skip-build      # pipeline stages only —
                                                 # use once data/objective1,
                                                 # data/weather, data/demand
                                                 # are already built and you
                                                 # just want Phases 2-8 again
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATE = "tamilnadu"

# Required, sequential, stop-on-failure. Each entry is either a bare
# script name (run as `python <name>`) or a pipeline stage name (run as
# `python pipeline.py --state tamilnadu --stage <name>`).
BUILD_SCRIPTS = [
    "build_input_package.py",
    "build_regime_weather.py",
    "build_demand_profile.py",
]

PIPELINE_STAGES = [
    "geometry",
    "verify",
    "doe",
    "surrogate",
    "multifidelity",
    "optimize",
    "plots",
    "robustness",
    "handoff",
]


def run_command(label, args, stop_on_failure):
    print("\n" + "=" * 68)
    print(f"  RUNNING: {label}")
    print("=" * 68)
    t0 = time.time()
    result = subprocess.run(args, cwd=str(BASE_DIR))
    elapsed = time.time() - t0

    if result.returncode == 0:
        print(f"\n  [OK] {label} finished in {elapsed:.1f}s")
        return "ok", elapsed

    print(f"\n  [FAILED] {label} exited with code {result.returncode} after {elapsed:.1f}s")
    if stop_on_failure:
        print(f"\n  Stopping — every stage after {label} reads its output, "
              f"so continuing would run against stale/missing data.")
    return "failed", elapsed


def run_build_script(name):
    path = BASE_DIR / name
    if not path.exists():
        print(f"  [SKIP] {name} — file not found at {path}")
        return "skipped", 0.0
    return run_command(name, [sys.executable, str(path)], stop_on_failure=True)


def run_pipeline_stage(stage):
    return run_command(
        f"pipeline.py --state {STATE} --stage {stage}",
        [sys.executable, str(BASE_DIR / "pipeline.py"), "--state", STATE, "--stage", stage],
        stop_on_failure=True,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Run the full Objective 2 Tamil Nadu chain end-to-end, in order."
    )
    parser.add_argument("--dry-run", action="store_true",
                         help="Print the resolved run order and exit without running anything.")
    parser.add_argument("--skip-build", action="store_true",
                         help="Skip build_input_package.py / build_regime_weather.py / "
                              "build_demand_profile.py and go straight to the pipeline.py stages.")
    parser.add_argument("--from", dest="from_step", default=None,
                         help="Resume starting at this build script or pipeline stage name "
                              "(e.g. --from doe), skipping everything before it. "
                              "A leading './' or '.\\' is tolerated on script names.")
    args = parser.parse_args()

    all_steps = list(BUILD_SCRIPTS) + list(PIPELINE_STAGES)
    build = list(BUILD_SCRIPTS)
    stages = list(PIPELINE_STAGES)

    if args.skip_build:
        build = []

    if args.from_step:
        from_name = Path(args.from_step).name
        if from_name not in all_steps:
            print(f"ERROR: --from {args.from_step!r} is not one of: {all_steps}")
            sys.exit(2)
        if from_name in build:
            build = build[build.index(from_name):]
        else:
            build = []
            stages = stages[stages.index(from_name):]

    print("=" * 68)
    print(f"  OBJECTIVE 2 — {STATE.upper()} — RUN ORDER")
    print("=" * 68)
    if build:
        print("\n  BUILD (required, stop-on-first-failure):")
        for s in build:
            print(f"    {s}")
    else:
        print("\n  BUILD: skipped (--skip-build or --from started inside PIPELINE)")
    print("\n  PIPELINE (required, stop-on-first-failure; `pipeline.py --state "
          f"{STATE} --stage <name>`):")
    for s in stages:
        print(f"    {s}")
    print("\n  NOT RUN (excluded — see docstring): simulate "
          "(single-case hand-parameterized demo, run it yourself when needed)")

    if args.dry_run:
        print("\n--dry-run: exiting without running anything.")
        return

    t_start = time.time()
    log = []

    for name in build:
        status, elapsed = run_build_script(name)
        log.append((name, status, elapsed))
        if status == "failed":
            print_summary(log, time.time() - t_start)
            sys.exit(1)

    for stage in stages:
        status, elapsed = run_pipeline_stage(stage)
        log.append((f"pipeline.py --stage {stage}", status, elapsed))
        if status == "failed":
            print_summary(log, time.time() - t_start)
            sys.exit(1)

    print_summary(log, time.time() - t_start)


def print_summary(log, total_elapsed):
    print("\n" + "=" * 68)
    print("  SUMMARY")
    print("=" * 68)
    for name, status, elapsed in log:
        tag = {"ok": "OK    ", "failed": "FAILED", "skipped": "SKIP  "}[status]
        print(f"  [{tag}] {name:45s} {elapsed:7.1f}s")
    print(f"\n  Total wall-clock time: {total_elapsed:.1f}s")
    n_failed = sum(1 for _, s, _ in log if s == "failed")
    if n_failed:
        print(f"  {n_failed} stage(s) FAILED — see the log above for the first failure's output.")
    else:
        print("  All stages completed (or were intentionally skipped).")
    print("=" * 68)


if __name__ == "__main__":
    main()
