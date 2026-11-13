"""
RUN_LIVE_MENU.py - one command for the demo:   python ansys/RUN_LIVE_MENU.py
Pick a criteria (0-6) and it opens ANSYS Fluent LIVE for it (window + redrawing contour + terminal table).
Close any other Fluent window first. Optional: python ansys/RUN_LIVE_MENU.py 3 --hours 0.5
"""
import subprocess
import sys
from pathlib import Path

A = Path(__file__).resolve().parent
dirs = sorted(p for p in A.glob("criteria_[0-9]_*"))
args = sys.argv[1:]
hours = []
if "--hours" in args:
    i = args.index("--hours"); hours = ["--hours", args[i + 1]]; args = args[:i] + args[i + 2:]
if args:
    pick = int(args[0])
else:
    for p in dirs:
        print(f"  {p.name.split('_')[1]}  {p.name}")
    pick = int(input("criteria number to run live: "))
d = next(p for p in dirs if p.name.split("_")[1] == str(pick))
subprocess.run([sys.executable, "fluent_tank_discharge_criteria.py", "--live", *hours], cwd=d)
