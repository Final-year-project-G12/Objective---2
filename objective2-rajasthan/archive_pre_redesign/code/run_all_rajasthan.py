"""
run_all_rajasthan.py
========================
Step 6.3 of the 2026-09-20 fix plan ("Objective2 rajasthan fix plan.md") --
a single orchestrator running Phases 0/2 through 8 in order, stopping at
the first gate failure rather than silently continuing on to a later
phase built on a broken one.

NOTE: the fix plan names objective2-tamilnadu/run_all_tamilnadu.py and
build_input_package.py's sha256 manifest as the reference for this step.
Neither file actually exists in this repo's objective2-tamilnadu/ copy as
of 2026-09-20 (checked directly) -- Tamil Nadu has no single orchestrator
script either, only its own pipeline.py's per-stage CLI. This script is
therefore written fresh against Rajasthan's own pipeline.py stage
functions (step 7's flowchart: config+Tm retarget -> geometry -> 5 gates
-> DOE -> surrogate -> search+select -> robustness+contract), not ported
from a file that doesn't exist.

Usage:
  python run_all_rajasthan.py [--skip-retarget] [--mc-draws N]

--skip-retarget: skip src/design/retarget_tm.py's Tm re-targeting step
(step 4). Off by default because retarget_all() rewrites
configs/states/rajasthan.yaml in place -- running it twice in a row would
re-target against an already-re-targeted config. Pass --skip-retarget on
any re-run after the first one in a session.
"""

import argparse
import sys
import time

from src.design.constraints import run_boundary_self_test, report_max_reachable_pcm_fraction
from src.verify.gates import run_all_gates
from src.doe.run_batch import run_batch
from src.doe.split_cases import run_split
from src.surrogate.train import train_surrogate
from src.surrogate.evaluate import evaluate_by_group
from src.optimize.select_deployable import run_phase7
from src.robustness.monte_carlo import run_all as run_robustness, N_DRAWS as N_DRAWS_DEFAULT
from src.handoff.build_recommendation_cards import run as build_recommendation_cards
from src.handoff.build_obj3_contract import run as build_obj3_contract


def _step(name):
    print("\n" + "#" * 72)
    print(f"# {name}")
    print("#" * 72)


def main():
    ap = argparse.ArgumentParser(description="Run the full Rajasthan Objective 2 pipeline, phase by phase")
    ap.add_argument("--state", default="rajasthan")
    ap.add_argument("--skip-retarget", action="store_true",
                     help="skip Phase 0's Tm re-targeting step (see module docstring)")
    ap.add_argument("--mc-draws", type=int, default=N_DRAWS_DEFAULT)
    args = ap.parse_args()
    state = args.state
    t_start = time.time()

    if not args.skip_retarget:
        _step("Phase 0 — Tm re-targeting (step 4, decision D2)")
        from src.design.retarget_tm import retarget_all
        retarget_all(state)

    _step("Phase 2 — geometry & constraint boundary self-test")
    _rows, all_deterministic = run_boundary_self_test()
    report_max_reachable_pcm_fraction()
    if not all_deterministic:
        print("\nFAILED at Phase 2 — boundary self-test is not deterministic. Stopping.")
        sys.exit(1)

    _step(f"Phase 4 — verification gates 1-5, state={state}")
    _gates, go_no_go = run_all_gates(state)
    if go_no_go != "GO":
        print(f"\nFAILED at Phase 4 — gate verdict={go_no_go}. Stopping before DOE (framework doc Phase 0 gate).")
        sys.exit(1)

    _step(f"Phase 5 — DOE generation, batch run, train/hold-out split, state={state}")
    run_batch(state)
    run_split(state)

    _step(f"Phase 6 — surrogate training + hold-out evaluation, state={state}")
    train_surrogate(state)
    evaluate_by_group(state)

    _step(f"Phase 7 — optimization pass + simulator confirmation + selection, state={state}")
    run_phase7(state)

    _step(f"Phase 8a — Monte Carlo robustness, state={state}")
    run_robustness(state, args.mc_draws)

    _step(f"Phase 8b — recommendation cards + Objective 3 contract, state={state}")
    build_recommendation_cards(state)
    build_obj3_contract(state)

    elapsed = time.time() - t_start
    print(f"\nDONE — full pipeline for state={state} completed in {elapsed/60:.1f} min.")


if __name__ == "__main__":
    main()
