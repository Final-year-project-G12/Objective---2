"""
ansys/criteria_common/build_criteria_folders.py
===============================================
Creates / refreshes one self-contained folder per criteria under ansys/:

    ansys/criteria_<n>_<name>/
        criteria.json                      the design + 2-D proxy + run settings
        fluent_tank_discharge_criteria.py  copy of fluent_tank_discharge.py driven by criteria.json
        make_system_mesh.py                mesh builder (copy of src/cfd/make_system_mesh.py + n_capsules)
        scenarios.py, run_node_model.py    the node-model side (objective values, funnel verdict, day plot)
        mesh/                              the .msh built for this criteria (created on run)
        figures/, *_discharge_timeseries.csv, node_model_*  outputs

Re-run safely any time:  python ansys/criteria_common/build_criteria_folders.py [--hours 2] [--dt 60]
"""
import argparse
import json
import math
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANSYS = HERE.parent
sys.path.insert(0, str(HERE))
from scenarios import (SCENARIOS, V_TANK_M3, WALL_M, N_OPT_3D, R_SCALE_2D, drawn_count, v_outer, PCM, REGIME)  # noqa: E402


def n3d_for(r_in, fraction):
    v = v_outer(r_in)
    lo = math.ceil(0.02 * V_TANK_M3 / v - 1e-9)
    hi = math.floor(0.30 * V_TANK_M3 / v + 1e-9)
    return int(min(max(round(fraction * V_TANK_M3 / v), lo), hi))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=2.0)
    ap.add_argument("--dt", type=float, default=60.0)
    a = ap.parse_args()
    for sc in SCENARIOS:
        d = sc["design"]
        n3 = n3d_for(d["R_in"], d["fraction"])
        r2 = d["R_in"] * R_SCALE_2D
        small = d["R_in"] < 0.02
        crit = {
            "key": sc["key"], "title": sc["title"], "rule": sc["rule"], "why_not_optimal": sc["why_not_optimal"],
            "regime": REGIME, "pcm": PCM, "design": d, "n_3d": n3,
            "fraction_pct": 100.0 * n3 * v_outer(d["R_in"]) / V_TANK_M3, "frac_of_optimal_N": n3 / N_OPT_3D,
            "proxy": {"drawn_capsules": drawn_count(n3), "r_in_2d_m": r2,
                      "rule": "drawn = round(N_3d*34/104); r_2d = 0.5*R_in_3d  (optimal = 34 capsules / 20 mm)"},
            "mesh": {"nx": 340 if small else 260, "ny": 260 if small else 200},
            "run": {"hours": a.hours, "dt_s": a.dt},
        }
        f = ANSYS / sc["key"]
        f.mkdir(parents=True, exist_ok=True)
        (f / "criteria.json").write_text(json.dumps(crit, indent=1), encoding="utf-8")
        shutil.copy(HERE / "templates" / "fluent_tank_discharge_criteria.py", f / "fluent_tank_discharge_criteria.py")
        shutil.copy(HERE / "make_system_mesh.py", f / "make_system_mesh.py")
        shutil.copy(HERE / "scenarios.py", f / "scenarios.py")
        wrapper = (f'"""Node-model side of THIS criteria ({sc["title"]}): objective values, gates, funnel verdict, '
                   f'one-day time behaviour.\nRun from the project root: python ansys/{sc["key"]}/run_node_model.py\n'
                   f'(re-simulates the optimum too, because every number is reported against it)."""\n'
                   f'import sys\nfrom pathlib import Path\n'
                   f'sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "criteria_common"))\n'
                   f'import run_node_model\nrun_node_model.main(only="{sc["key"]}")\n')
        (f / "run_node_model.py").write_text(wrapper, encoding="utf-8")
        print(f"{sc['key']:36s} N3d={n3:4d} frac={crit['fraction_pct']:5.1f}% drawn={crit['proxy']['drawn_capsules']:3d} "
              f"r2d={r2*1000:.1f}mm mesh={crit['mesh']['nx']}x{crit['mesh']['ny']}")


if __name__ == "__main__":
    main()
