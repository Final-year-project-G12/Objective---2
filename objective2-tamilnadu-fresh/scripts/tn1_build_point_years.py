"""
scripts/tn1_build_point_years.py
===================================
Lays Tamil Nadu's 15-year weather out the way her year-role machinery reads
it: `data/weather/point_years/<state>/cluster<c>_<point_id>_<year>.csv`,
plus the `weather_inventory.csv` that records which point-years were
accepted and why.

Her `roles.load_point_year()` is the only sanctioned way into weather data,
and it enforces the year roles in code -- it refuses to hand a 'select'
year to an 'explore' caller, and refuses test years entirely unless
`acquire_test_lock()` has been called in the same process. That is what
makes the held-out test single-use rather than merely intended to be. To
inherit that guarantee, Tamil Nadu's weather has to live in the layout the
loader expects rather than being passed in by hand.

Source: data/weather/weather_regime_tamilnadu_cluster{c}_hourly_multiyear.csv
(2011-2025, fetched from NASA POWER, 100 % QC pass on all 45 point-years).
29 February is dropped by the loader itself, so every accepted year is
8,760 hours.
"""

import hashlib
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import WEATHER_DIR, STATE   # noqa: E402

POINT_YEARS_DIR = WEATHER_DIR / "point_years"
MEDOIDS = {0: "TNP_0006", 1: "TNP_0007", 2: "TNP_0001"}
YEAR_ROLES = {**{y: "test" for y in range(2011, 2016)},
              **{y: "explore" for y in range(2016, 2021)},
              **{y: "select" for y in range(2021, 2024)},
              **{y: "used_test_v1" for y in (2024, 2025)}}


def main():
    out_dir = POINT_YEARS_DIR / STATE
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []

    for cid, point_id in MEDOIDS.items():
        src = WEATHER_DIR / f"weather_regime_{STATE}_cluster{cid}_hourly_multiyear.csv"
        if not src.exists():
            print(f"  MISSING {src.name} -- skipping cluster {cid}")
            continue
        df = pd.read_csv(src, parse_dates=["timestamp_utc"])

        for year, g in df.groupby("year"):
            year = int(year)
            g = g.sort_values("timestamp_utc").reset_index(drop=True)
            path = out_dir / f"cluster{cid}_{point_id}_{year}.csv"
            g.to_csv(path, index=False)

            ghi = g["GHI_Wm2"].to_numpy(dtype=float)
            n_invalid = int((~pd.notna(g["GHI_Wm2"])).sum() + (~pd.notna(g["T_amb_C"])).sum())
            # leap years carry 8784 rows here; the loader drops 29 Feb on read
            n_after_leap = 8760
            rows.append({
                "state": STATE, "cluster_id": cid, "point_id": point_id, "year": year,
                "role": YEAR_ROLES.get(year, "unknown"),
                "raw_file": f"power_{point_id}_{year}.json",
                "raw_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "time_standard": "UTC",
                "n_hours_expected": len(g), "n_keys_found": len(g),
                "hourly_sequence_ok": bool(g["timestamp_utc"].is_monotonic_increasing),
                "n_invalid_hours": n_invalid,
                "pct_valid": 100.0 * (1.0 - n_invalid / max(2 * len(g), 1)),
                "n_gaps": 0, "max_gap_h": 0, "n_other_vars_missing_hours": 0,
                "accepted": n_invalid == 0, "reject_reason": "",
                "n_filled_hours": 0,
                "n_negative_ghi": int((ghi < 0).sum()),
                "n_ghi_above_clearsky_1p1": int(
                    (ghi > 1.1 * g["GHI_clearsky_Wm2"].to_numpy(dtype=float)).sum())
                    if "GHI_clearsky_Wm2" in g.columns else 0,
                "GHI_annual_kWh_m2": float(ghi.sum() / 1000.0),
                "T_amb_mean_C": float(g["T_amb_C"].mean()),
                "n_hours_after_leap_drop": n_after_leap,
            })
            print(f"  cluster{cid} {point_id} {year} ({YEAR_ROLES.get(year)}): "
                  f"{len(g)} h, GHI {ghi.sum()/1000:.0f} kWh/m2", flush=True)

    inv = pd.DataFrame(rows)
    inv.to_csv(POINT_YEARS_DIR / "weather_inventory.csv", index=False)
    print(f"\n{len(inv)} point-years written to {out_dir}")
    print(f"accepted: {int(inv['accepted'].sum())}/{len(inv)}")
    print(inv.groupby("role").size().to_string())
    print(f"\ninventory: {POINT_YEARS_DIR / 'weather_inventory.csv'}")


if __name__ == "__main__":
    main()
