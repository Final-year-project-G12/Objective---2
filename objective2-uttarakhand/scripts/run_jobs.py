"""
scripts/run_jobs.py  -  rebuild job runner: at most N simulator jobs at a time (plan 14.2; this PC ran out of memory at 8, 2026-11-14)
=====================================================================================================================================
Reads a job file (one job per line: "<output path relative to the Uttarakhand root> <script> <args...>"), skips a job whose output
already exists (so an interrupted stage resumes), runs the rest with at most --workers in parallel, logs each job's stdout/stderr to
logs/<script>_<args>.log and appends "time rc seconds job" lines to logs/done.txt. Exit code 1 if any job failed.
Usage: python scripts/run_jobs.py <jobfile> [--workers 3]
"""
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "logs"


def run(line):
    out, *cmd = line.split()
    if (ROOT / out).exists():
        print("skip", line, flush=True)
        return 0
    tag = "_".join(Path(c).stem for c in cmd)
    LOG.mkdir(exist_ok=True)
    t0 = time.time()
    env = {**os.environ, "PYTHONPATH": str(ROOT), "PYTHONIOENCODING": "utf-8"}
    with open(LOG / f"{tag}.log", "w", encoding="utf-8") as fh:
        rc = subprocess.call([sys.executable, *cmd], cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT, env=env)
    msg = f"{time.strftime('%Y-%m-%d %H:%M:%S')} rc={rc} {time.time() - t0:7.0f}s {' '.join(cmd)}"
    with open(LOG / "done.txt", "a", encoding="utf-8") as fh:
        fh.write(msg + "\n")
    print(msg, flush=True)
    return rc


def main():
    jobfile = Path(sys.argv[1])
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 3
    jobs = [ln.strip() for ln in jobfile.read_text().splitlines() if ln.strip() and not ln.startswith("#")]
    print(f"{len(jobs)} jobs, {workers} workers", flush=True)
    with ThreadPoolExecutor(workers) as ex:
        rcs = list(ex.map(run, jobs))
    print(f"finished: {sum(1 for r in rcs if r)} failed", flush=True)
    return 1 if any(rcs) else 0


if __name__ == "__main__":
    sys.exit(main())
