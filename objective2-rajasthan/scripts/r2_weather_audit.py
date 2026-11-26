"""
scripts/r2_weather_audit.py  -  rebuild level L2: weather-only representativeness audit (plan section 7.3) and the input manifest
=================================================================================================================================
WEATHER ONLY: no simulation, no plant outcome is computed, so looking at the 2006-2010 test years here does not touch the test.
Per regime medoid and year: annual GHI, monsoon (Jun-Sep) and winter (Dec-Feb) GHI, the 10th percentile of daily GHI (lower tail),
the longest run of cloudy days (daily clearness GHI/GHI_clear < 0.4), mean ambient temperature and data completeness.
Each year is compared with the 2016-2025 distribution of the same regime (z-score), and each role group with the rest.

Writes results/l2_weather_audit_years.csv, results/l2_weather_audit_roles.csv and results/l2_input_manifest.json
(SHA-256 of the configs, demand profile, O1 manifest, weather inventory and every point-year file, plus the code commit).
The plan's rule: keep the split as specified unless this audit shows a data-quality defect; never swap years after seeing
simulator outcomes.
Usage: python scripts/r2_weather_audit.py
"""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.weather import roles                       # noqa: E402

OUT = ROOT / "results"
CLOUDY_KT = 0.4


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def longest_run(mask):
    best = cur = 0
    for m in mask:
        cur = cur + 1 if m else 0
        best = max(best, cur)
    return best


def year_row(r):
    d = pd.read_csv(roles.point_year_path("rajasthan", r.cluster_id, r.point_id, r.year))
    d = d[~d.local_date.str.endswith("-02-29")]
    day = d.groupby("local_date").agg(ghi=("GHI_Wm2", "sum"), clr=("GHI_clearsky_Wm2", "sum"))
    day["kt"] = day.ghi / day.clr.where(day.clr > 0)
    m = pd.to_datetime(day.index).month
    return {"regime": r.cluster_id, "point_id": r.point_id, "year": r.year, "role": r.role,
            "ghi_annual_kWh_m2": d.GHI_Wm2.sum() / 1000, "ghi_monsoon_kWh_m2": day.ghi[(m >= 6) & (m <= 9)].sum() / 1000,
            "ghi_winter_kWh_m2": day.ghi[(m == 12) | (m <= 2)].sum() / 1000,
            "ghi_daily_p10_kWh_m2": float(np.percentile(day.ghi / 1000, 10)),
            "longest_cloudy_run_days": longest_run((day.kt < CLOUDY_KT).to_numpy()),
            "t_amb_mean_C": d.T_amb_C.mean(), "pct_valid": r.pct_valid, "n_filled_hours": getattr(r, "n_filled_hours", 0)}


def main():
    inv = pd.read_csv(roles.INVENTORY_PATH)
    yrs = pd.DataFrame([year_row(r) for r in inv.itertuples()])
    metrics = ["ghi_annual_kWh_m2", "ghi_monsoon_kWh_m2", "ghi_winter_kWh_m2", "ghi_daily_p10_kWh_m2", "longest_cloudy_run_days", "t_amb_mean_C"]
    for m in metrics:
        ref = yrs[yrs.year >= 2016].groupby("regime")[m].agg(["mean", "std"])
        yrs[f"z_{m}"] = (yrs[m] - yrs.regime.map(ref["mean"])) / yrs.regime.map(ref["std"])
    yrs.to_csv(OUT / "l2_weather_audit_years.csv", index=False)
    roles_tab = yrs.groupby(["regime", "role"])[metrics].mean().reset_index()
    roles_tab.to_csv(OUT / "l2_weather_audit_roles.csv", index=False)
    print(roles_tab.round(1).to_string(index=False))
    flag = yrs[(yrs.year < 2016) & (yrs[[f"z_{m}" for m in metrics]].abs() > 2.5).any(axis=1)]
    print("\n2006-2010 point-years with any |z| > 2.5 against 2016-2025:", len(flag))
    if len(flag):
        print(flag[["regime", "year"] + [f"z_{m}" for m in metrics]].round(2).to_string(index=False))

    files = {p: sha(ROOT / p) for p in ["configs/system_config_shared.yaml", "configs/design_space.yaml", "configs/states/rajasthan.yaml",
                                         "configs/cfd_closure_v1.yaml", "data/demand/demand_profile_rajasthan.csv",
                                         "results/o1_manifest_rajasthan.json", "data/weather/point_years/weather_inventory.csv"]}
    files.update({str(roles.point_year_path("rajasthan", r.cluster_id, r.point_id, r.year).relative_to(ROOT)).replace("\\", "/"):
                  sha(roles.point_year_path("rajasthan", r.cluster_id, r.point_id, r.year)) for r in inv.itertuples()})
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    man = {"level": "L2 input/config freeze (plan gate G0)", "generated_utc": datetime.now(timezone.utc).isoformat(),
           "code_commit_at_generation": commit, "plant_hash": roles.plant_hash(), "test_lock_path": str(roles.test_lock_path().relative_to(ROOT)),
           "year_roles": {str(y): r for y, r in sorted(roles.YEAR_ROLES.items())}, "files_sha256": files}
    (OUT / "l2_input_manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    print("\nplant hash", man["plant_hash"], "| files hashed:", len(files))


if __name__ == "__main__":
    main()
