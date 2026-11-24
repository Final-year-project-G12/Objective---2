"""
scripts/run_o2_pipeline.py
============================
Unattended driver for the common-plant Objective 2 rebuild, levels L5 -> L9 (Tamil Nadu). Stages are idempotent: a stage whose output files exist is skipped.
It does NOT decide anything scientific: thresholds are pre-registered (configs/l5_fidelity_preregistration.json, configs/funnel_frozen.json).
A stage failure stops the chain (nothing downstream runs on missing inputs) and is written to results/pipeline_status.json.
Usage: python scripts/run_o2_pipeline.py [--from STAGE]
Stages: wait_doe, c10_fidelity, c10_summary, c11_surrogates, c14_search, c15_grid_band, c16_freeze, c16_evaluate, c16_select, c17_test
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
STATUS = ROOT / "results" / "pipeline_status.json"
LOG = ROOT / "results" / "logs" / "pipeline.log"
PAIRS = [(c, p) for c in (0, 1, 2) for p in (1, 2, 3)]


def say(msg):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + msg
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def status(stage, state, note=""):
    s = json.loads(STATUS.read_text()) if STATUS.exists() else {}
    s[stage] = {"state": state, "note": note, "time": time.strftime("%Y-%m-%d %H:%M:%S")}
    STATUS.write_text(json.dumps(s, indent=2))


WORKERS = 5          # RAM-limited (about 1.7 GB free of 15.7 GB when measured); the simulator is memory-bound beyond ~4-6 jobs


def run_parallel(stage, cmds, logname, workers=WORKERS):
    """Run the commands with at most `workers` concurrent processes (a pool, not a fixed one-per-regime split)."""
    from concurrent.futures import ThreadPoolExecutor

    def one(ic):
        i, cmd = ic
        with open(ROOT / "results" / "logs" / f"_log_{logname}_{i}.log", "w", encoding="utf-8") as fh:
            return subprocess.run([PY] + cmd, cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT).returncode
    with ThreadPoolExecutor(max_workers=workers) as ex:
        rc = list(ex.map(one, enumerate(cmds)))
    if any(rc):
        status(stage, "FAILED", f"return codes {rc}")
        say(f"{stage} FAILED rc={rc}")
        sys.exit(1)


def doe_done():
    for c, p in PAIRS:
        f = ROOT / f"results/c9_l5_doe_r{c}_p{p}.csv"
        if not f.exists() or len(pd.read_csv(f)) < 128:
            return False
    return True


def stage(name, outputs, fn):
    if outputs and all(list(ROOT.glob(o)) for o in outputs):
        say(f"{name}: outputs exist, skipped")
        status(name, "SKIPPED_DONE")
        return
    say(f"{name}: start")
    status(name, "RUNNING")
    fn()
    status(name, "DONE")
    say(f"{name}: done")


def wait_doe():
    while not doe_done():
        time.sleep(120)


def c10_summary():
    d = pd.concat([pd.read_csv(ROOT / f"results/c10_l5_fidelity_r{c}_p{p}.csv") for c, p in PAIRS])
    rows = []
    for pair, g in d.groupby("pair"):
        rho = float(spearmanr(g.cheap_g_window_mean, g.full_g_window_2017)[0]) if g.cheap_g_window_mean.nunique() > 1 else float("nan")
        mx = float((g.cheap_g_window_mean - g.full_g_window_2017).abs().max())
        rows.append({"pair": pair, "n": len(g), "spearman": rho, "max_abs_diff_kWh": mx, "pass": bool(rho >= 0.8 and mx <= 0.5)})
    s = pd.DataFrame(rows)
    s.to_csv(ROOT / "results/c10_l5_fidelity_summary.csv", index=False)
    ok = int(s["pass"].sum())
    verdict = "cheap screen ACCEPTED for ranking" if ok >= 7 else "cheap screen NOT used for selection: all funnel candidates are re-evaluated at full fidelity"
    (ROOT / "results/c10_l5_fidelity_verdict.txt").write_text(f"{ok} of {len(s)} pairs pass (rule: >=7). {verdict}\n")
    say(f"c10 verdict: {ok}/{len(s)} pairs pass -> {verdict}")


def main():
    start = sys.argv[sys.argv.index("--from") + 1] if "--from" in sys.argv else "wait_doe"
    order = ["wait_doe", "c10_fidelity", "c10_summary", "c11_surrogates", "c14_search", "c15_grid_band", "c16_freeze", "c16_evaluate", "c16_select", "c17_test", "post_o2"]
    go = order.index(start)
    steps = {
        "wait_doe": lambda: stage("wait_doe", [], wait_doe) if not doe_done() else say("wait_doe: DOE complete"),
        "c10_fidelity": lambda: stage("c10_fidelity", [f"results/c10_l5_fidelity_r{c}_p{p}.csv" for c, p in PAIRS],
                                      lambda: run_parallel("c10_fidelity", [["scripts/c10_l5_fidelity_check.py", str(c), str(p)] for c, p in PAIRS], "c10")),
        "c10_summary": lambda: stage("c10_summary", ["results/c10_l5_fidelity_summary.csv"], c10_summary),
        "c11_surrogates": lambda: stage("c11_surrogates", ["results/c11_l5_surrogate_selection.csv"],
                                        lambda: run_parallel("c11_surrogates", [["scripts/c11_l5_surrogates.py"]], "c11")),
        "c14_search": lambda: stage("c14_search", [f"results/c14_l6_front_r{c}_p{p}.csv" for c, p in PAIRS],
                                    lambda: run_parallel("c14_search", [["scripts/c14_l6_search.py", str(c), str(p)] for c, p in PAIRS], "c14")),
        "c15_grid_band": lambda: stage("c15_grid_band", [f"results/c15_l7_band_r{c}_p{p}.csv" for c, p in PAIRS],
                                       lambda: run_parallel("c15_grid_band", [["scripts/c15_l7_grid_band.py", str(c), str(p)] for c, p in PAIRS], "c15")),
        "c16_freeze": lambda: stage("c16_freeze", ["configs/funnel_frozen.json"], lambda: run_parallel("c16_freeze", [["scripts/c16_l7_funnel.py", "freeze"]], "c16f")),
        "c16_evaluate": lambda: stage("c16_evaluate", [f"results/c16_select_eval_r{c}_p{p}.csv" for c, p in PAIRS],
                                      lambda: run_parallel("c16_evaluate", [["scripts/c16_l7_funnel.py", "evaluate", str(c), str(p)] for c, p in PAIRS], "c16e")),
        "c16_select": lambda: stage("c16_select", ["results/c16_funnel_winners.csv"], lambda: run_parallel("c16_select", [["scripts/c16_l7_funnel.py", "select"]], "c16s")),
        "post_o2": lambda: stage("post_o2", [], lambda: run_parallel("post_o2", [["scripts/run_post_o2.py"]], "post", workers=1)),
        "c17_test": lambda: stage("c17_test", ["results/common100L_*/c17_summary.csv"], lambda: run_parallel("c17_test", [["scripts/c17_l9_test_and_contract.py"]], "c17")),
    }
    for name in order[go:]:
        steps[name]()
    say("PIPELINE COMPLETE")
    status("pipeline", "COMPLETE")


if __name__ == "__main__":
    main()
