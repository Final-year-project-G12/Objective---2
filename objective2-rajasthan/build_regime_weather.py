"""
build_regime_weather.py (Rajasthan)
=======================================
2026-09-18 re-sync — Objective 1's Rajasthan clustering has moved on since
`configs/states/rajasthan.yaml` was hand-built: Cluster 1's medoid changed
RJP_0202 -> RJP_0192 and Cluster 2's medoid changed RJP_0055 -> RJP_0083
(Cluster 0's medoid, RJP_0132, is unchanged). This script rebuilds the
per-regime representative weather files for the NEW medoids, adapted from
objective2-tamilnadu/build_regime_weather.py (same idea: one file per
regime from Objective 1's raw NASA POWER JSON cache + daily aggregates,
using the highest-max_membership_prob point in each cluster as its medoid)
but matched to era5-rajasthan's actual column names, which differ from
Tamil Nadu's:
  daily_aggregates_rajasthan.csv: GHI_Wh_m2, GHI_clearsky_Wh_m2, kt_daily,
  T2M_min/max/mean, RH2M_mean, WS10M_mean (Wh, not kWh; T2M not Ta_*_true).

Only GHI_Wm2 and T_amb_C are actually read by the physics simulator
(src/simulation/tank_model.py) — confirmed by grep across src/ before
writing this script — but the full column set is still produced to match
the existing weather_regime_*_hourly/daily.csv schema for consistency
with Cluster 0's untouched files.

Run: python build_regime_weather.py            # rebuilds clusters 1 and 2 only
     python build_regime_weather.py --all       # rebuilds all 3 (re-verifies cluster 0 too)
"""

import argparse
import json
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

from config import OBJ1_RAW_POWER_DIR, WEATHER_DIR

STATE = "rajasthan"
ASSIGN_FILE = OBJ1_RAW_POWER_DIR.parent.parent / "processed" / "cluster_assignments_rajasthan_levelA.csv"
DAILY_FILE = OBJ1_RAW_POWER_DIR.parent.parent / "processed" / "daily_aggregates_rajasthan.csv"
OUT_DIR = WEATHER_DIR
OUT_DIR.mkdir(parents=True, exist_ok=True)

MIN_HOURS_FOR_COMPLETE_YEAR = 8000

# Current (2026-09-18) medoids per era5-rajasthan/outputs/recommendation_cards_rajasthan.md
CURRENT_MEDOIDS = {0: "RJP_0132", 1: "RJP_0192", 2: "RJP_0083"}


def load_point_hourly(point_id):
    frames = {}
    for fp in sorted(OBJ1_RAW_POWER_DIR.glob(f"power_{point_id}_*.json")):
        year = fp.stem.split("_")[-1]
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
        params = data.get("properties", {}).get("parameter", {})
        if not params:
            continue
        idx, cols = None, {}
        for var, series in params.items():
            if idx is None:
                idx = pd.to_datetime(list(series.keys()), format="%Y%m%d%H", utc=True)
            cols[var] = list(series.values())
        df = pd.DataFrame(cols, index=idx).replace(-999, np.nan)
        frames[year] = df
    return frames


def build_hourly_for_cluster(cid, point_id):
    frames = load_point_hourly(point_id)
    if not frames:
        print(f"  [WARN] cluster {cid} (medoid {point_id}): no raw hourly cache found under {OBJ1_RAW_POWER_DIR}")
        return None

    best_year = max(frames, key=lambda y: len(frames[y]))
    if len(frames[best_year]) < MIN_HOURS_FOR_COMPLETE_YEAR:
        print(f"  [NOTE] cluster {cid}: best year {best_year} only has {len(frames[best_year])} hours "
              f"(<{MIN_HOURS_FOR_COMPLETE_YEAR}) — using it anyway.")

    df = frames[best_year].rename(columns={
        "ALLSKY_SFC_SW_DWN": "GHI_Wm2",
        "CLRSKY_SFC_SW_DWN": "GHI_clearsky_Wm2",
        "T2M": "T_amb_C",
        "RH2M": "RH_pct",
        "WS10M": "wind_ms",
    })
    df = df.reset_index().rename(columns={"index": "timestamp_utc"})
    df["WS_ms"] = df["wind_ms"]
    df["local_hour"] = (df["timestamp_utc"].dt.tz_convert("Asia/Kolkata")).dt.hour
    df["local_date"] = (df["timestamp_utc"].dt.tz_convert("Asia/Kolkata")).dt.date.astype(str)
    df["point_id"] = point_id
    df["cluster_id"] = cid
    df["year"] = int(best_year)
    cols = ["timestamp_utc", "GHI_Wm2", "T_amb_C", "RH_pct", "WS_ms", "local_hour", "local_date",
            "point_id", "cluster_id", "year", "wind_ms", "GHI_clearsky_Wm2"]
    return df[cols]


def build_daily_for_cluster(cid, point_id, daily_all):
    sub = daily_all[daily_all["point_id"] == point_id].copy()
    if sub.empty:
        print(f"  [WARN] cluster {cid} (medoid {point_id}): no rows in {DAILY_FILE.name}")
        return None
    sub["cluster_id"] = cid
    sub["GHI_daily_kWh"] = sub["GHI_Wh_m2"] / 1000.0
    sub["GHIcs_daily_kWh"] = sub["GHI_clearsky_Wh_m2"] / 1000.0
    sub["Ta_mean_C"] = sub["T2M_mean"]
    sub["Ta_max_C"] = sub["T2M_max"]
    sub["Ta_min_C"] = sub["T2M_min"]
    sub["DTR_C"] = sub["T2M_max"] - sub["T2M_min"]
    sub["RH_mean_pct"] = sub["RH2M_mean"]
    sub["wind_mean_ms"] = sub["WS10M_mean"]
    return sub


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="rebuild all 3 clusters (default: only 1 and 2, the ones that moved)")
    args = ap.parse_args()

    print("=" * 68)
    print(f"  Build Per-Regime Representative Weather — {STATE} (re-sync 2026-09-18)")
    print("=" * 68)

    targets = CURRENT_MEDOIDS if args.all else {k: v for k, v in CURRENT_MEDOIDS.items() if k != 0}
    daily_all = pd.read_csv(DAILY_FILE) if DAILY_FILE.exists() else None
    if daily_all is None:
        print(f"  [WARN] {DAILY_FILE} not found — daily regime files will be skipped.")

    n_hourly_ok, n_daily_ok = 0, 0
    for cid, point_id in targets.items():
        print(f"\n  Cluster {cid}  (medoid {point_id}) ...")
        hourly = build_hourly_for_cluster(cid, point_id)
        if hourly is not None:
            out = OUT_DIR / f"weather_regime_{STATE}_cluster{cid}_hourly.csv"
            hourly.to_csv(out, index=False)
            print(f"    [OK] hourly -> {out.name}  ({len(hourly):,} rows, year {hourly['year'].iloc[0]})")
            n_hourly_ok += 1

        if daily_all is not None:
            daily = build_daily_for_cluster(cid, point_id, daily_all)
            if daily is not None:
                out = OUT_DIR / f"weather_regime_{STATE}_cluster{cid}_daily.csv"
                daily.to_csv(out, index=False)
                print(f"    [OK] daily  -> {out.name}  ({len(daily):,} rows)")
                n_daily_ok += 1

    print("\n" + "=" * 68)
    print(f"  DONE — hourly files: {n_hourly_ok}/{len(targets)}   daily files: {n_daily_ok}/{len(targets)}")
    print(f"  Output: {OUT_DIR}/")
    print("=" * 68)


if __name__ == "__main__":
    main()
