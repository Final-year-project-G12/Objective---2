"""
ansys/criteria_common/run_all_fluent.py
=======================================
Runs the whole-tank discharge in ANSYS Fluent for every criteria folder, ONE AT A TIME
(the Student licence allows a single Fluent session), saving each terminal output to
<folder>/fluent_terminal.log.  Then draws the cross-criteria comparison plot.

BEFORE YOU RUN: close every open Fluent window (the licence is exclusive).
    python ansys/criteria_common/run_all_fluent.py [--hours 2] [--only criteria_3_ok_not_optimal]
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

ANSYS = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=None)
    ap.add_argument("--only", default=None)
    ap.add_argument("--print-every", type=float, default=10.0)
    ap.add_argument("--frame-every", type=float, default=5.0)
    a = ap.parse_args()
    folders = sorted(p for p in ANSYS.glob("criteria_[0-9]_*") if (p / "fluent_tank_discharge_criteria.py").exists())
    if a.only:
        folders = [p for p in folders if p.name == a.only]
    for f in folders:
        cmd = [sys.executable, "fluent_tank_discharge_criteria.py", "--print-every", str(a.print_every),
               "--frame-every", str(a.frame_every)]
        if a.hours:
            cmd += ["--hours", str(a.hours)]
        t0 = time.time()
        print(f"\n##### {f.name}: {' '.join(cmd)}", flush=True)
        with open(f / "fluent_terminal.log", "w", encoding="utf-8") as log:
            rc = subprocess.run(cmd, cwd=f, stdout=log, stderr=subprocess.STDOUT).returncode
        print(f"##### {f.name}: exit {rc} in {time.time()-t0:.0f}s", flush=True)
    subprocess.run([sys.executable, str(Path(__file__).with_name("plot_comparison.py"))])


if __name__ == "__main__":
    main()
