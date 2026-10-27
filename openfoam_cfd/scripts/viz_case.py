#!/usr/bin/env python3
"""
viz_case.py -- run ONE capsule case and keep every 30 s of fields for ParaView.

  python viz_case.py --name rt44_d060 --pcm RT44HC --d 0.06 --mdot 0.03 --dT 15 --t-end-h 1.2

Output: ../cases_viz/<name>/<name>.foam   <- open this file in ParaView (Windows)
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import make_case as mc  # noqa: E402


def wsl(p):
    p = os.path.abspath(p).replace("\\", "/")
    return f"/mnt/{p[0].lower()}{p[2:]}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--pcm", default="RT44HC")
    ap.add_argument("--d", type=float, default=0.06)
    ap.add_argument("--mdot", type=float, default=0.03)
    ap.add_argument("--dT", type=float, default=15.0)
    ap.add_argument("--t-end-h", type=float, default=1.2)
    ap.add_argument("--cell-size", type=float, default=None)
    a = ap.parse_args()
    out = os.path.join(ROOT, "cases_viz", a.name)
    os.makedirs(out, exist_ok=True)
    mc.build_case(out, a.pcm, a.d, a.mdot, a.dT, t_end_h=a.t_end_h, cell_size_m=a.cell_size, viz=True,
                  sample_every_s=30.0)
    r = subprocess.run(["wsl", "-d", "Ubuntu-24.04", "-e", "bash", wsl(os.path.join(HERE, "viz_run.sh")), wsl(out)],
                       capture_output=True, text=True, errors="replace")
    print("\n".join(l for l in r.stdout.splitlines() if "Failed to translate" not in l))
    if r.returncode == 0:
        print("\nOpen in ParaView:", os.path.join(out, a.name + ".foam"))
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
