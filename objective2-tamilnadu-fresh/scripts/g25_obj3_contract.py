"""
scripts/g25_obj3_contract.py
===============================
G25 - Objective 3 handoff. Builds the Tamil Nadu environment contract from the
CURRENT Objective 2 results and writes
results/obj3_environment_contract_tamilnadu_v3.json.

This is the LAST stage of the pipeline: it must run after g10_select and
g10_test, because it reads their outputs (g10_selection_r*.json,
g10_heldout_results.csv, held_out_test.lock) plus wp6_band.csv.

The generator lives in src/handoff/build_obj3_contract_tamilnadu.py; this is a
thin wrapper so the stage follows scripts/tn_run_all.py's "scripts/<name>.py"
convention.

Usage: python scripts/g25_obj3_contract.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.handoff.build_obj3_contract_tamilnadu import build  # noqa: E402

REQUIRED = [
    "results/g10_selection_r0.json",
    "results/g10_selection_r1.json",
    "results/g10_selection_r2.json",
    "results/g10_heldout_results.csv",
    "results/held_out_test.lock",
    "results/wp6_band.csv",
]


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    missing = [r for r in REQUIRED if not (root / r).exists()]
    if missing:
        print("CANNOT BUILD THE OBJECTIVE 3 CONTRACT - these inputs are missing:")
        for m in missing:
            print(f"  {m}")
        print("\nRun g10_select (and g10_test for the held-out block) first.")
        return 1
    out = build()
    print(f"written {out}  ({out.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
