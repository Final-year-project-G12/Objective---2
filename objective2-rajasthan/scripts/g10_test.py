"""
scripts/g10_test.py
======================
G10 / S8 - the HELD-OUT test (v3: untouched years 2011-2015), run exactly ONCE. The v1 test on 2024-2025 is archived (results/v1_cap20/). Usage: python scripts/g10_test.py --confirm-run-once

What is run: the frozen designs from the three selection logs (results/g10_selection_r{0,1,2}.json): per regime the
chosen design plus the best-g_window design of every other O1 PCM, each next to its water-only twin at the SAME flow
(exact plain runs; no flow-grid baseline is built for the test years). Both test years, every metric, nothing dropped.
Enforcement: the selection fingerprints are verified against the files on disk, then roles.acquire_test_lock() creates
results/held_out_test.lock atomically. A second run refuses with HeldOutLockError. The lock is the first thing
this script does after verification; if the run crashes afterwards the lock stays and the incident must be logged in
docs/PROGRESS.md (it is never deleted to retry silently).
"""

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.optimize.evaluate import evaluate_night
from src.weather import roles

OUT = Path("results")


def frozen_designs():
    designs, prints = [], []
    for cid in range(3):
        log = json.loads((OUT / f"g10_selection_r{cid}.json").read_text())
        cand = pd.read_csv(OUT / f"g10_selection_candidates_r{cid}.csv")
        body = json.dumps({k: v for k, v in log.items() if k != "fingerprint_sha256"}, sort_keys=True, default=str)
        recomputed = hashlib.sha256((body + cand.round(9).to_csv()).encode()).hexdigest()
        if recomputed != log["fingerprint_sha256"]:
            raise RuntimeError(f"selection log r{cid} was modified after it was written (fingerprint mismatch)")
        prints.append(log["fingerprint_sha256"])
        if "chosen" not in log:
            continue
        chosen = log["chosen"]
        entries = [("chosen", chosen)] + [("best_of_pcm", a) for a in log["alternatives_best_per_pcm"]
                                          if a["pcm"] != chosen["pcm"]]
        for role, d in entries:
            designs.append({"regime": cid, "role": role, **{k: d[k] for k in ("pcm", "R_in_m", "fraction", "N", "flow", "arrangement")}})
    return designs, hashlib.sha256("".join(prints).encode()).hexdigest()


def main():
    if "--confirm-run-once" not in sys.argv:
        sys.exit("refusing to run: pass --confirm-run-once (this evaluation may only ever be run one time)")
    designs, fingerprint = frozen_designs()
    run_id = "heldout_" + fingerprint[:12]
    roles.acquire_test_lock(run_id, fingerprint)                  # raises HeldOutLockError if already used
    from src.optimize.evaluate import evaluate_night as night
    rows = []
    for d in designs:
        for r in night(d["regime"], d["pcm"], d["R_in_m"], d["fraction"], d["flow"], d["arrangement"], "test", stride=5):
            rows.append({**d, **r, "run_id": run_id})
        print("test", d["regime"], d["role"], d["pcm"], flush=True)
        pd.DataFrame(rows).to_csv(OUT / "g10_heldout_results.csv", index=False)
    pd.DataFrame(rows).to_csv(OUT / "g10_heldout_results.csv", index=False)
    print("held-out test complete", run_id, len(rows), "rows")


if __name__ == "__main__":
    main()
