#!/usr/bin/env python3
"""Generate and run several cases in WSL (OpenFOAM v2406), a few in parallel, then print the wall time of each.
usage: python scripts/run_batch.py [--jobs 4] [--mesh-only] -- <make_capsule_case args for case 1> -- <args for case 2> ...
Example: python scripts/run_batch.py --jobs 3 -- --design r0 --scenario charge_70 --cells 20 -- --design r0 --scenario charge_70 --cells 40
Each case is run by scripts/run_wsl.sh on the Linux filesystem and copied back into cases/."""
import argparse, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def wslpath(p):
    d, rest = os.path.splitdrive(os.path.abspath(p))
    return "/mnt/" + d[0].lower() + rest.replace("\\", "/")


def one(args, mesh_only):
    out = subprocess.run([sys.executable, "-I", os.path.join(HERE, "make_capsule_case.py")] + args, capture_output=True, text=True)
    if out.returncode:
        return args, "GENERATOR FAILED: " + out.stdout + out.stderr, 0
    case = os.path.join(ROOT, "cases", os.path.basename(out.stdout.strip().splitlines()[-1]))
    t0 = time.time()
    env = dict(os.environ, WSLENV="MESH_ONLY", MESH_ONLY="1" if mesh_only else "")
    subprocess.run(["wsl", "-d", "Ubuntu-24.04", "--", "bash", wslpath(os.path.join(HERE, "run_wsl.sh")), wslpath(case)],
                   capture_output=True, env=dict(env, MSYS_NO_PATHCONV="1"))
    return args, case, time.time() - t0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--mesh-only", action="store_true")
    argv = sys.argv[1:]
    i = argv.index("--") if "--" in argv else len(argv)
    opt = ap.parse_args(argv[:i])
    groups, cur = [], []
    for t in argv[i + 1:]:
        if t == "--":
            groups.append(cur); cur = []
        else:
            cur.append(t)
    groups.append(cur)
    with ThreadPoolExecutor(opt.jobs) as ex:
        for args, case, dt in ex.map(lambda g: one(g, opt.mesh_only), [g for g in groups if g]):
            print(f"{dt:8.0f} s  {case}", flush=True)
