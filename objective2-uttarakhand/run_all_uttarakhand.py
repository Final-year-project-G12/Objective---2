"""
run_all_uttarakhand.py
========================
Orchestrator for the current Objective 2 chain for Uttarakhand (gates G1-G12). It calls pipeline.py stage by stage and stops at the
first failing stage. Ported 2026-10-28 from objective2-rajasthan/run_all_rajasthan.py (K = 4 regimes, held-out years 2024-2025).
The legacy chain (Tm retargeting, Extra Trees, Monte Carlo robustness, K = 5 regimes) is retired and is in git history only.

Modes
  python run_all_uttarakhand.py                  default: tests, then the cheap REPORTING stages from the saved results
                                               (report -> handoff -> plots). Minutes. Always safe, including after the held-out test.
  python run_all_uttarakhand.py --full           the whole chain from the simulator up (verify ... plots). Many hours.
                                               Refused while results/held_out_test.lock exists, because re-deciding the designs
                                               would make the one held-out run meaningless; add --allow-invalidate to override knowingly.
  python run_all_uttarakhand.py --full --dry-run print every command without running anything
Options: --jobs N (parallel jobs inside a stage, default 3), --include-heldout (with --full; the lock still refuses a second run),
         --skip-tests.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable


def _run(argv, label):
    print("\n" + "#" * 72 + f"\n# {label}\n" + "#" * 72, flush=True)
    rc = subprocess.call(argv, cwd=ROOT)
    if rc != 0:
        print(f"\nFAILED at: {label} (exit {rc}). Stopping.")
        sys.exit(rc)


def main():
    ap = argparse.ArgumentParser(description="Run the current Uttarakhand Objective 2 chain")
    ap.add_argument("--state", default="uttarakhand")
    ap.add_argument("--full", action="store_true", help="run every stage from the simulator up (many hours)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--allow-invalidate", action="store_true")
    ap.add_argument("--include-heldout", action="store_true")
    ap.add_argument("--skip-tests", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    pipe = [PY, "pipeline.py", "--state", a.state, "--jobs", str(a.jobs)]
    if a.dry_run:
        pipe.append("--dry-run")

    if not a.skip_tests and not a.dry_run:
        _run([PY, "-m", "pytest", "-q", "tests"], "unit tests")
    if a.full:
        flags = (["--allow-invalidate"] if a.allow_invalidate else []) + (["--include-heldout"] if a.include_heldout else [])
        _run(pipe + ["--stage", "all"] + flags, "full chain (verify ... plots)")
    else:
        for stage in ("report", "handoff", "plots"):
            _run(pipe + ["--stage", stage], f"stage {stage}")
    _run(pipe + ["--stage", "status"], "status")
    print(f"\nDONE in {(time.time() - t0) / 60:.1f} min.")


if __name__ == "__main__":
    main()
