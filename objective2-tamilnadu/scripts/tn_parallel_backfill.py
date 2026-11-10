"""
scripts/tn_parallel_backfill.py
==================================
Runs the two outstanding verification backfills CONCURRENTLY instead of one at
a time:

  * g9_s6_grid for O1 PCM ranks 2 and 3 (6 jobs) - the dense-grid cross-check
    at the SAME reduced fidelity rank 1 used (720 designs x 1 year), so the
    three ranks stay comparable.
  * g9_s4_s5 warm re-runs for the g18 with/without-vertices diagnostic
    (18 jobs): `novert` = base + 3 more AL rounds with no vertex step;
    `vert` = base + the 24 box vertices + 3 more rounds.

Neither g9_s6_grid nor g9_s4_s5 parallelises internally, so running them
sequentially used 2 of this machine's 12 cores. Every job writes its own output
files, so they are safe to run side by side.

SAFETY
------
* Explore years only. Nothing here touches the held-out years or the lock.
* Idempotent: a job whose output is already complete is skipped, so this can be
  re-run after an interruption.
* An output being written by another process (log touched in the last
  STALE_S seconds) is deferred to the end and waited for, rather than being
  started a second time and corrupting the file.

Usage:
  python scripts/tn_parallel_backfill.py [--workers N] [--dry-run]
"""

import argparse
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
NOVERT = RESULTS / "issue1_novert"
GRID_ROWS = 720          # designs per dense-grid pair
STALE_S = 150            # a log untouched this long is considered finished


def _rows(p: Path) -> int:
    if not p.exists():
        return 0
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return max(0, sum(1 for _ in f) - 1)


def _busy(log: Path) -> bool:
    return log.exists() and (time.time() - log.stat().st_mtime) < STALE_S


def jobs():
    """(key, argv, env_overrides, output_path, log_path, complete_fn)"""
    out = []
    for rank in (2, 3):
        for cid in (0, 1, 2):
            k = f"grid_r{cid}_p{rank}"
            out.append((k,
                        ["scripts/g9_s6_grid.py", str(cid), str(rank)],
                        {},
                        RESULTS / f"g9_s6_grid_r{cid}_p{rank}.csv",
                        RESULTS / f"_log_g9_s6_grid_{cid}_p{rank}.log",
                        lambda p: _rows(p) >= GRID_ROWS))
    for cid in (0, 1, 2):
        for rank in (1, 2, 3):
            out.append((f"novert_r{cid}_p{rank}",
                        ["scripts/g9_s4_s5.py", str(cid), str(rank)],
                        {"G9_WARM": "1", "G9_MAX_ROUNDS": "8",
                         "G9_OUTDIR": "results/issue1_novert"},
                        NOVERT / f"g9_points_r{cid}_p{rank}_ext.csv",
                        NOVERT / f"_log_r{cid}_p{rank}.log",
                        lambda p: p.exists()))
    for cid in (0, 1, 2):
        for rank in (1, 2, 3):
            out.append((f"vert_r{cid}_p{rank}",
                        ["scripts/g9_s4_s5.py", str(cid), str(rank)],
                        {"G9_WARM": "1", "G9_VERTICES": "1", "G9_MAX_ROUNDS": "8"},
                        RESULTS / f"g9_points_r{cid}_p{rank}_ext2.csv",
                        RESULTS / f"_log_g9_vert_r{cid}_p{rank}.log",
                        lambda p: p.exists()))
    return out


def run_one(key, argv, envover, log_path):
    env = dict(os.environ)
    env.update(envover)
    env.setdefault("PYTHONUNBUFFERED", "1")
    # Each job is single-threaded Python; stop BLAS from grabbing every core
    # and thrashing once a dozen of them run side by side.
    for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
              "NUMEXPR_NUM_THREADS"):
        env.setdefault(v, "1")
    t0 = time.time()
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as fh:
        rc = subprocess.call([sys.executable] + argv, cwd=str(ROOT),
                             stdout=fh, stderr=subprocess.STDOUT, env=env)
    return key, rc, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    todo, done, deferred = [], [], []
    for key, argv, envover, outp, logp, is_done in jobs():
        if is_done(outp):
            done.append(key)
        elif _busy(logp):
            deferred.append((key, argv, envover, outp, logp, is_done))
        else:
            todo.append((key, argv, envover, outp, logp))

    print(f"{len(done)} already complete, {len(todo)} to run, "
          f"{len(deferred)} in flight elsewhere (deferred)")
    for k in done:
        print(f"  done     {k}")
    for k, *_ in deferred:
        print(f"  in-flight {k}  (another process is writing it)")
    if a.dry_run:
        return 0

    fails = []
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(run_one, k, argv, env, lp): k
                for k, argv, env, _, lp in todo}
        print(f"running {len(futs)} job(s) on {a.workers} workers")
        for fut in as_completed(futs):
            key, rc, secs = fut.result()
            print(f"  {'ok  ' if rc == 0 else 'FAIL'} {key}  ({secs/60:.1f} min)")
            if rc:
                fails.append(key)

    # Jobs another process was already writing: wait for that process to finish,
    # then run any that did not complete.
    for key, argv, envover, outp, logp, is_done in deferred:
        while _busy(logp):
            time.sleep(20)
        if is_done(outp):
            print(f"  ok   {key}  (finished by the other process)")
            continue
        print(f"  resuming {key}")
        _, rc, secs = run_one(key, argv, envover, logp)
        print(f"  {'ok  ' if rc == 0 else 'FAIL'} {key}  ({secs/60:.1f} min)")
        if rc:
            fails.append(key)

    print(f"\nall backfill jobs finished in {(time.time()-t0)/60:.1f} min; "
          f"{len(fails)} failure(s)" + (": " + ", ".join(fails) if fails else ""))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
