"""
run_all_uttarakhand.py
========================
Orchestrator for the Uttarakhand Objective 2 COMMON-PLANT REBUILD (docs/REBUILD_COMMON100L.md). It calls pipeline.py stage by stage
and stops at the first failing stage.

Modes
  python run_all_uttarakhand.py                  tests, then the safe REPORTING stages from the saved results
                                               (handoff -> figures -> manifest; + m1 when --matlab is given). Minutes.
  python run_all_uttarakhand.py --full           the whole chain (o1 ... manifest). Many hours. Refused while the 2006-2010 test lock
                                               exists (re-deciding the design would void the one-shot test); --allow-invalidate overrides.
  python run_all_uttarakhand.py --full --dry-run print every command without running anything
Options: --jobs N (default 3), --include-test (with --full; the lock still refuses a second run), --matlab PATH, --skip-tests.
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
    ap.add_argument("--include-test", action="store_true")
    ap.add_argument("--matlab", default=None)
    ap.add_argument("--skip-tests", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    pipe = [PY, "pipeline.py", "--state", a.state, "--jobs", str(a.jobs)]
    if a.dry_run:
        pipe.append("--dry-run")

    if not a.skip_tests and not a.dry_run:
        _run([PY, "-m", "pytest", "-q", "tests"], "unit tests")
    if a.full:
        flags = (["--allow-invalidate"] if a.allow_invalidate else []) + (["--include-test"] if a.include_test else []) +                 (["--matlab", a.matlab] if a.matlab else [])
        _run(pipe + ["--stage", "all"] + flags, "full chain (o1 ... manifest)")
    else:
        for stage in ("handoff", "figures") + (("m1",) if a.matlab else ()) + ("manifest",):
            _run(pipe + ["--stage", stage] + (["--matlab", a.matlab] if stage == "m1" else []), f"stage {stage}")
    _run(pipe + ["--stage", "status"], "status")
    print(f"\nDONE in {(time.time() - t0) / 60:.1f} min.")


if __name__ == "__main__":
    main()
