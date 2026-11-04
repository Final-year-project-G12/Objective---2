"""
scripts/tn_lever_sweep.py
============================
Which lever actually decides whether the PCM tank beats the water-only
tank in Tamil Nadu, measured with her simulator and her paired baseline.

This is a DIAGNOSTIC, not a selection: it sweeps one lever at a time
around a reference design so the size of each effect is visible before the
DOE/NSGA-II spend hours searching. Nothing here chooses a design.

Levers swept:
  fraction   PCM volume fraction, 0.02 -> 0.30 (her searched range)
  R_in       capsule inner radius, 10 -> 40 mm (her searched range)
  flow       collector-loop flow, 0.010 -> 0.050 kg/s
  pcm        each PCM in Objective 1's shortlist for that regime

Objective 2 does NOT choose the material. Only Objective 1's shortlisted
PCMs are ever simulated here -- there is no off-shortlist arm. An earlier
revision of this script swept the whole PCM database and reported the
off-list results "separately"; that arm is deleted, because a number that
exists invites being quoted, and quoting it would be Objective 2 re-deriving
Objective 1's deliverable.

Run:  python scripts/tn_lever_sweep.py [n_workers]
"""

import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import STATE   # noqa: E402

REF = dict(r_in_m=0.020, fraction=0.15, flow=0.030, arrangement="staggered")
YEAR = 2016
FRACTIONS = [0.02, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30]
R_INS = [0.010, 0.015, 0.020, 0.028, 0.034, 0.040]
FLOWS = [0.010, 0.015, 0.020, 0.030, 0.040, 0.050]


def _one(job):
    cid, pcm, r_in, frac, flow, arr, lever = job
    from src.optimize.evaluate import evaluate_design
    try:
        res = evaluate_design(cid, pcm, r_in, frac, flow, arr,
                              purpose="explore", years=[YEAR])
        py = (res.get("per_year") or [{}])[0]
        return {"regime": cid, "pcm": pcm, "lever": lever, "R_in_m": r_in,
                "fraction": frac, "flow": flow, "arrangement": arr,
                "N": res.get("N"), "valid": res.get("valid"),
                "reason": res.get("reason", ""),
                "g_window": py.get("g_window"), "g_annual": py.get("g_annual"),
                "g_useful": py.get("g_useful"), "d_overheat": py.get("d_overheat"),
                "t_pcm_max": py.get("t_pcm_max")}
    except Exception as e:
        return {"regime": cid, "pcm": pcm, "lever": lever, "R_in_m": r_in,
                "fraction": frac, "flow": flow, "arrangement": arr,
                "valid": False, "reason": f"{type(e).__name__}: {e}"[:120]}


def build_jobs():
    from src.io_utils import get_regime
    jobs = []
    for cid in (0, 1, 2):
        rank1 = get_regime(STATE, cid)["pcm_shortlist"][0]
        for f in FRACTIONS:
            jobs.append((cid, rank1, REF["r_in_m"], f, REF["flow"], REF["arrangement"], "fraction"))
        for r in R_INS:
            jobs.append((cid, rank1, r, REF["fraction"], REF["flow"], REF["arrangement"], "R_in"))
        for q in FLOWS:
            jobs.append((cid, rank1, REF["r_in_m"], REF["fraction"], q, REF["arrangement"], "flow"))
        for pcm in get_regime(STATE, cid)["pcm_shortlist"]:
            jobs.append((cid, pcm, REF["r_in_m"], REF["fraction"], REF["flow"], REF["arrangement"], "pcm_shortlist"))
    return jobs


def main():
    n_workers = int(sys.argv[1]) if len(sys.argv) > 1 else max(1, (os.cpu_count() or 2) - 3)
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        os.environ.setdefault(var, "1")
    jobs = build_jobs()
    print(f"{len(jobs)} evaluations, {n_workers} workers, year {YEAR}", flush=True)
    t0 = time.time()
    rows = []
    with ProcessPoolExecutor(max_workers=n_workers) as ex:
        for i, row in enumerate(ex.map(_one, jobs), 1):
            rows.append(row)
            if i % 20 == 0:
                print(f"  {i}/{len(jobs)}  {(time.time()-t0)/60:.1f} min", flush=True)

    df = pd.DataFrame(rows)
    out = ROOT / "results" / "tn_lever_sweep.csv"
    df.to_csv(out, index=False)
    ok = df[df["valid"] == True]   # noqa: E712

    pd.set_option("display.width", 200)
    for lever in ("fraction", "R_in", "flow"):
        sub = ok[ok["lever"] == lever]
        if sub.empty:
            continue
        print(f"\n=== {lever} ===")
        piv = sub.pivot_table(index=lever if lever != "R_in" else "R_in_m",
                              columns="regime", values="g_window")
        print(piv.round(2).to_string())

    sub = ok[ok["lever"] == "pcm_shortlist"]
    if not sub.empty:
        print("\n=== pcm_shortlist (g_window by PCM) ===")
        from src.io_utils import get_pcm_properties
        sub = sub.copy()
        sub["Tm_C"] = [get_pcm_properties(STATE, p)["Tm_C"] for p in sub["pcm"]]
        print(sub.pivot_table(index=["pcm", "Tm_C"], columns="regime",
                              values="g_window").round(2).to_string())

    print(f"\nbest g_window per regime, any lever:")
    print(ok.loc[ok.groupby("regime")["g_window"].idxmax()][
        ["regime", "pcm", "lever", "R_in_m", "fraction", "flow", "N", "g_window",
         "t_pcm_max"]].round(4).to_string(index=False))
    print(f"\nwrote {out}   ({(time.time()-t0)/60:.1f} min)")


if __name__ == "__main__":
    main()
