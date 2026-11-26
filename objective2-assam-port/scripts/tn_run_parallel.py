"""
scripts/tn_run_parallel.py
=============================
Runs her per-(regime, PCM-rank) gate scripts across processes instead of
one after another.

Her scripts are written as `python scripts/g8_s2_doe.py <cluster> <rank>`
-- one serial sweep per pair, with CSV checkpointing every 16 designs. The
nine pairs are completely independent, so running them nine-up turns a
~7-hour serial DOE into roughly the time of its slowest pair.

Nothing inside her scripts is modified. This launcher only decides WHICH
of them run at once, so the algorithms, seeds and outputs stay exactly
hers; a result produced here is reproducible by running her command line
directly.

Thread pinning matters: each worker imports numpy, and 9 processes each
starting a 12-thread BLAS pool would oversubscribe 12 cores by 9x. One
BLAS thread per worker is set before the children start.

Usage:
  python scripts/tn_run_parallel.py g8_s2_doe              # all 9 pairs
  python scripts/tn_run_parallel.py g8_s2_doe --pairs 0:1 1:1
  python scripts/tn_run_parallel.py g8_build_plain_baseline --regimes
  python scripts/tn_run_parallel.py g9_s4_s5 --workers 5
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import STATE   # noqa: E402

N_REGIMES = 3
N_RANKS = 3


def pair_args(spec):
    out = []
    for s in spec:
        c, r = s.split(":")
        out.append((int(c), int(r)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script", help="her script name, with or without .py")
    ap.add_argument("--pairs", nargs="*", default=None,
                    help="explicit cluster:rank pairs, e.g. 0:1 1:2")
    ap.add_argument("--regimes", action="store_true",
                    help="the script takes only a cluster id, not a rank")
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--extra", nargs="*", default=[],
                    help="extra args appended to every invocation")
    args = ap.parse_args()

    name = args.script if args.script.endswith(".py") else args.script + ".py"
    script = ROOT / "scripts" / name
    if not script.exists():
        sys.exit(f"no such script: {script}")

    if args.regimes:
        jobs = [[str(c)] for c in range(N_REGIMES)]
    elif args.pairs:
        jobs = [[str(c), str(r)] for c, r in pair_args(args.pairs)]
    else:
        jobs = [[str(c), str(r)] for c in range(N_REGIMES)
                for r in range(1, N_RANKS + 1)]
    jobs = [j + list(args.extra) for j in jobs]

    env = dict(os.environ)
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                "NUMEXPR_NUM_THREADS"):
        env.setdefault(var, "1")

    max_par = args.workers or min(len(jobs), max(1, (os.cpu_count() or 2) - 1))
    log_dir = ROOT / "results"
    log_dir.mkdir(parents=True, exist_ok=True)

    print(f"{name}: {len(jobs)} jobs, {max_par} at a time, state={STATE}")
    t0 = time.time()
    running, queued, done = [], list(jobs), []

    while queued or running:
        while queued and len(running) < max_par:
            job = queued.pop(0)
            tag = "_".join(job)
            log = log_dir / f"_log_{name.replace('.py','')}_{tag}.log"
            fh = open(log, "w", encoding="utf-8")
            p = subprocess.Popen([sys.executable, str(script)] + job,
                                 cwd=str(ROOT), stdout=fh, stderr=subprocess.STDOUT,
                                 env=env)
            running.append((p, job, fh, log, time.time()))
            print(f"  start {tag}  -> {log.name}", flush=True)

        time.sleep(5)
        still = []
        for p, job, fh, log, started in running:
            if p.poll() is None:
                still.append((p, job, fh, log, started))
            else:
                fh.close()
                tag = "_".join(job)
                el = (time.time() - started) / 60
                status = "ok" if p.returncode == 0 else f"FAILED rc={p.returncode}"
                print(f"  done  {tag}  {status}  ({el:.1f} min)", flush=True)
                done.append((tag, p.returncode, log))
        running = still

    el = (time.time() - t0) / 60
    bad = [d for d in done if d[1] != 0]
    print(f"\n{len(done)} jobs in {el:.1f} min; {len(bad)} failed")
    for tag, rc, log in bad:
        print(f"  {tag}: rc={rc} -- see {log}")
        try:
            tail = log.read_text(encoding="utf-8", errors="ignore").strip().splitlines()[-6:]
            for line in tail:
                print(f"      {line}")
        except Exception:
            pass
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
