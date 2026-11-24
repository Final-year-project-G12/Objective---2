"""
scripts/run_post_o2.py
========================
Runs AFTER the Objective 2 pipeline (scripts/run_o2_pipeline.py) has produced the funnel winners and the one-shot test:
  1. L4 re-runs at 175 L/day (one-at-a-time sensitivity c7 and Taguchi L9 c8), pooled.
  2. L8  ANSYS Fluent cross-check: regenerate the seven criteria around the new optimum, node-model numbers, Fluent discharge (one at a time: Student licence).
  3. M1  MATLAB checkpoint: simulator export (c20) and MATLAB figures/animations (matlab_m1/m1_main.m).
  4. Docs: results document, README status, legacy banners, Word report, plan documents (c21, c22).
Every sub-stage is isolated: a failure is logged in results/post_o2_status.json and the next sub-stage still runs (Fluent in particular needs the licence free).
Usage: python scripts/run_post_o2.py
"""
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
ST = ROOT / "results" / "post_o2_status.json"
LOG = ROOT / "results" / "logs" / "post_o2.log"
PAIRS = [(c, p) for c in (0, 1, 2) for p in (1, 2, 3)]


def say(m):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + m
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def mark(stage, state, note=""):
    s = json.loads(ST.read_text()) if ST.exists() else {}
    s[stage] = {"state": state, "note": note, "time": time.strftime("%Y-%m-%d %H:%M:%S")}
    ST.write_text(json.dumps(s, indent=2))


def run(cmd, log, cwd=ROOT, timeout=None):
    with open(ROOT / "results" / "logs" / log, "w", encoding="utf-8") as fh:
        return subprocess.run(cmd, cwd=cwd, stdout=fh, stderr=subprocess.STDOUT, timeout=timeout).returncode


def step(name, fn, skip_if=None):
    if skip_if and all(list(ROOT.glob(g)) for g in skip_if):
        say(f"{name}: outputs exist, skipped")
        mark(name, "SKIPPED_DONE")
        return
    say(f"{name}: start")
    mark(name, "RUNNING")
    try:
        rc = fn()
        mark(name, "DONE" if not rc else "FAILED", f"rc={rc}")
        say(f"{name}: {'done' if not rc else 'FAILED rc=' + str(rc)}")
    except Exception as e:                                         # noqa: BLE001
        mark(name, "FAILED", repr(e)[:200])
        say(f"{name}: FAILED {e!r}")


def pool(cmds, tag, workers=5):
    def one(ic):
        i, c = ic
        return run([PY] + c, f"_log_{tag}_{i}.log")
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return max(list(ex.map(one, enumerate(cmds))) or [0])


def main():
    step("l4_sensitivity_175", lambda: pool([["scripts/c7_l4_sensitivity.py", str(c)] for c in (0, 1, 2)], "c7"), ["results/c7_l4_sensitivity_r0.csv"])
    step("l4_taguchi_175", lambda: pool([["scripts/c8_l4_taguchi.py", str(c), str(p)] for c, p in PAIRS], "c8"), ["results/c8_l4_taguchi_r0_p1.csv"])
    step("l8_regen_scenarios", lambda: run([PY, "ansys/criteria_common/regen_scenarios.py"], "_log_l8_regen.log"))
    step("l8_build_folders", lambda: run([PY, "ansys/criteria_common/build_criteria_folders.py", "--hours", "1.0", "--dt", "60"], "_log_l8_build.log"))
    step("l8_node_model", lambda: run([PY, "ansys/criteria_common/run_node_model.py"], "_log_l8_node.log"))
    step("l8_fluent", lambda: run([PY, "ansys/criteria_common/run_all_fluent.py", "--hours", "1.0"], "_log_l8_fluent.log", timeout=4 * 3600))
    step("m1_export", lambda: run([PY, "scripts/c20_m1_export.py"], "_log_m1_export.log"))
    step("m1_matlab", lambda: run(["matlab", "-batch", "run('matlab_m1/m1_main.m')"], "_log_m1_matlab.log", timeout=3 * 3600))
    step("docs_results", lambda: run([PY, "scripts/c21_build_docs.py"], "_log_docs.log"))
    step("docs_plan", lambda: run([PY, "scripts/c22_update_plan_docs.py"], "_log_docs_plan.log"))
    say("POST-O2 COMPLETE")
    mark("post_o2", "COMPLETE")


if __name__ == "__main__":
    main()
