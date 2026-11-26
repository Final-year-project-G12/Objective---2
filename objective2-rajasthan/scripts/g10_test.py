"""
scripts/g10_test.py
======================
Common-plant rebuild, plan O2-14 / O2-15: the ONE-SHOT confirmatory test on 2006-2010, then the report-only years 2022-2025.
Usage: python scripts/g10_test.py --confirm-run-once            (test; refuses if the lock for this plant already exists)
       python scripts/g10_test.py --report-years                (2022-2025; only after the test lock exists)

Frozen designs: from results/g10_selection_r{0..3}.json (fingerprints re-verified against the files): per regime the pick plus the
best g_window design of every other O1 PCM. Each is evaluated at the FULL fidelity (37.5 s) on every year of the role at every
robust anchor, paired with its exact water-only twin, and reported per year and anchor (no year dropped):
  * primary: paired g_window, g_annual, d_overheat at 45 C; peaks; residual;
  * secondary (Rajasthan, plan R2): the same at 50 C (delivery.target_temp_C overridden for the design AND its twin; not pooled);
  * hygiene (plan R9): share of days with the top layer >= 60 C for >= 1 h and the longest gap, for the PCM tank and the water-only tank;
  * night hold/serve scenarios at 37.5 s, centre anchor (stride 5).
The parent process creates the lock (roles.acquire_test_lock) and hands the run id to at most 3 worker processes, which may only JOIN
that run (roles.join_test_lock); a second test run refuses with HeldOutLockError. If the run crashes after the lock, the lock stays
and the incident is logged in docs/PROGRESS.md (never deleted to retry silently).
Writes results/o2_test_2006_2010.csv and o2_test_night.csv, or results/o2_report_2022_2025.csv and o2_report_night.csv.
"""

import hashlib
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.weather import roles                       # noqa: E402
from src.weather.inventory import REGIMES          # noqa: E402

OUT = ROOT / "results"


def frozen_designs():
    designs, prints = [], []
    for cid in REGIMES:
        log = json.loads((OUT / f"g10_selection_r{cid}.json").read_text())
        cand = pd.read_csv(OUT / f"g10_selection_candidates_r{cid}.csv")
        body = json.dumps({k: v for k, v in log.items() if k != "fingerprint_sha256"}, sort_keys=True, default=str)
        if hashlib.sha256((body + cand.round(9).to_csv()).encode()).hexdigest() != log["fingerprint_sha256"]:
            raise RuntimeError(f"selection log r{cid} was modified after it was written (fingerprint mismatch)")
        prints.append(log["fingerprint_sha256"])
        if "chosen" not in log:
            continue
        chosen = log["chosen"]
        entries = [("chosen", chosen)] + [("best_of_pcm", a) for a in log["alternatives_best_per_pcm"] if a["pcm"] != chosen["pcm"]]
        for role, d in entries:
            designs.append({"regime": cid, "role": role, "recommendation": log.get("recommendation", ""),
                            **{k: d[k] for k in ("pcm", "R_in_m", "fraction", "N", "flow", "arrangement")}})
    return designs, hashlib.sha256("".join(prints).encode()).hexdigest()


def plain_hygiene(cid, year, purpose, dt):
    from src.design.box import hygiene
    from src.design.space import geometry_bounds, to_design
    from src.optimize.evaluate import _weather
    from src.simulation.run_case import run_case
    r = run_case("rajasthan", cid, None, to_design(0.02, 0.05, 0.03, "staggered"), design_bounds=geometry_bounds(),
                 weather=_weather(cid, year, purpose), tank_model="multinode", n_nodes=10, record_hourly=True,
                 system_config_overrides={"solver": {"timestep_s": dt}})
    return hygiene(r["hourly"])


def work(args):
    d, purpose, run_id = args
    if purpose == "test":
        roles.join_test_lock(run_id)
    from src.design.box import full_dt
    from src.io_utils import load_system_config
    from src.optimize.evaluate import evaluate_design, evaluate_night
    sec = float(load_system_config()["delivery"]["secondary_report_temp_C"])
    a = evaluate_design(d["regime"], d["pcm"], d["R_in_m"], d["fraction"], d["flow"], d["arrangement"], purpose=purpose,
                        fidelity="full", record_hygiene=True)
    b = evaluate_design(d["regime"], d["pcm"], d["R_in_m"], d["fraction"], d["flow"], d["arrangement"], purpose=purpose,
                        fidelity="full", system_config_overrides={"delivery": {"target_temp_C": sec}})
    sec_rows = {(r["year"], r["anchor"]): r for r in b["per_year"]}
    rows = []
    for r in a["per_year"]:
        s = sec_rows[(r["year"], r["anchor"])]
        rows.append({**d, **r, "g_window_50C": s["g_window"], "g_annual_50C": s["g_annual"], "run_id": run_id})
    night = [{**d, **n, "run_id": run_id} for n in
             evaluate_night(d["regime"], d["pcm"], d["R_in_m"], d["fraction"], d["flow"], d["arrangement"], purpose, stride=5,
                            dt=full_dt(), anchor="center")]
    return rows, night


def main():
    report = "--report-years" in sys.argv
    if not report and "--confirm-run-once" not in sys.argv:
        sys.exit("refusing to run: pass --confirm-run-once (the 2006-2010 test may only ever be run one time) or --report-years")
    designs, fingerprint = frozen_designs()
    if report:
        if not roles.test_lock_path().exists():
            sys.exit("report-only years come after the test: no test lock yet")
        purpose, run_id = "report", json.loads(roles.test_lock_path().read_text())["run_id"] + "_report"
        out, out_n = OUT / "o2_report_2022_2025.csv", OUT / "o2_report_night.csv"
    else:
        purpose, run_id = "test", "o2test_" + fingerprint[:12]
        roles.acquire_test_lock(run_id, fingerprint)          # raises HeldOutLockError if this plant's test was already run
        out, out_n = OUT / "o2_test_2006_2010.csv", OUT / "o2_test_night.csv"
    rows, night = [], []
    with ProcessPoolExecutor(max_workers=3) as ex:
        for r, n in ex.map(work, [(d, purpose, run_id) for d in designs]):
            rows += r
            night += n
            print(purpose, r[0]["regime"], r[0]["role"], r[0]["pcm"], flush=True)
            pd.DataFrame(rows).to_csv(out, index=False)
            pd.DataFrame(night).to_csv(out_n, index=False)
    if purpose == "test":
        roles.join_test_lock(run_id)
    from src.design.box import full_dt
    hyg = [{"regime": cid, "year": y, **plain_hygiene(cid, y, purpose, full_dt())} for cid in REGIMES for y in roles.years_for(purpose)]
    pd.DataFrame(hyg).to_csv(out.with_name(out.stem + "_plain_hygiene.csv"), index=False)
    print(purpose, "complete", run_id, len(rows), "rows")


if __name__ == "__main__":
    main()
