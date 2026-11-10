"""
src/weather/fetch_multiyear_weather.py
=========================================
Tamil Nadu currently has only ONE weather year (2016) per regime medoid
(data/weather/weather_regime_tamilnadu_cluster{0,1,2}_hourly.csv). Porting
Rajasthan's methodology (explore/select/test year roles, a held-out lock
test) needs multiple independent years -- so this fetches 2011-2025 (15
years) for Tamil Nadu's own 3 regime medoid points, from the SAME source
already used for Objective 1 (NASA POWER, public, no API key -- see
tamilnadu_pipeline/01b_download_nasapower.py, which this mirrors but only
for the 3 medoid points instead of the full 133-point population grid).

Medoid points (from tamilnadu_pipeline/data/processed/population_grid_points.csv):
  cluster 0 -> TNP_0006  lat 10.875  lon 78.625
  cluster 1 -> TNP_0007  lat 10.875  lon 76.875
  cluster 2 -> TNP_0001  lat 13.125  lon 80.125

Writes, per regime:
  data/weather/raw_nasapower_multiyear/power_{point_id}_{year}.json  (cache)
  data/weather/weather_regime_tamilnadu_cluster{N}_hourly_multiyear.csv
    columns match the existing single-year files
    (timestamp_utc, GHI_Wm2, GHI_clearsky_Wm2, T_amb_C, RH_pct, wind_ms,
     point_id, cluster_id, year) PLUS a new `year_role` column.

Does NOT touch or overwrite the existing single-year files -- those stay
exactly as they are and keep being what the currently-validated pipeline
reads; this is new, additive data for the new NSGA-II/active-learning/
held-out-test chain only.

HOW TO RUN:
  python -m src.weather.fetch_multiyear_weather
"""

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from config import BASE_DIR

RAW_DIR = BASE_DIR / "data" / "weather" / "raw_nasapower_multiyear"
OUT_DIR = BASE_DIR / "data" / "weather"
RAW_DIR.mkdir(parents=True, exist_ok=True)

POWER_BASE = "https://power.larc.nasa.gov/api/temporal/hourly/point"
POWER_PARAMETERS = "ALLSKY_SFC_SW_DWN,CLRSKY_SFC_SW_DWN,T2M,RH2M,WS10M"
POWER_COMMUNITY = "RE"

YEARS = list(range(2011, 2026))   # 2011-2025, matches Rajasthan's 15-year inventory

MEDOIDS = {
    0: {"point_id": "TNP_0006", "lat": 10.875, "lon": 78.625},
    1: {"point_id": "TNP_0007", "lat": 10.875, "lon": 76.875},
    2: {"point_id": "TNP_0001", "lat": 13.125, "lon": 80.125},
}

# Year roles, identical scheme to Rajasthan's report (docs section 4.2):
#   explore: screening / DOE / surrogate training / active learning / dense grid / ablations
#   select:  choosing the final design
#   test:    one-shot held-out evaluation, untouched until the lock is created
#   extra:   available but not assigned a role (kept for future use)
YEAR_ROLES = {}
for y in range(2016, 2021):
    YEAR_ROLES[y] = "explore"
for y in (2021, 2022, 2023):
    YEAR_ROLES[y] = "select"
for y in range(2011, 2016):
    YEAR_ROLES[y] = "test"
for y in (2024, 2025):
    YEAR_ROLES[y] = "extra"

MAX_RETRIES = 3
RETRY_WAIT = 15
REQUEST_SLEEP = 1.0
REQUEST_TIMEOUT = 90


def _fetch_point_year(point_id, lat, lon, year):
    cache_path = RAW_DIR / f"power_{point_id}_{year}.json"
    if cache_path.exists():
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    params = {
        "parameters": POWER_PARAMETERS, "community": POWER_COMMUNITY,
        "longitude": lon, "latitude": lat,
        "start": f"{year}0101", "end": f"{year}1231",
        "format": "JSON",
    }
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(POWER_BASE, params=params, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                data = r.json()
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(data, f)
                time.sleep(REQUEST_SLEEP)
                return data
            print(f"    [warn] {point_id} {year}: HTTP {r.status_code}, attempt {attempt}/{MAX_RETRIES}")
        except requests.RequestException as e:
            print(f"    [warn] {point_id} {year}: {e}, attempt {attempt}/{MAX_RETRIES}")
        time.sleep(RETRY_WAIT)
    raise RuntimeError(f"Failed to fetch {point_id} {year} after {MAX_RETRIES} attempts")


def _json_to_hourly_df(data, point_id, cluster_id, year):
    params = data["properties"]["parameter"]
    ghi = params["ALLSKY_SFC_SW_DWN"]
    ghi_cs = params["CLRSKY_SFC_SW_DWN"]
    t2m = params["T2M"]
    rh2m = params["RH2M"]
    ws10m = params["WS10M"]

    timestamps = sorted(ghi.keys())   # "YYYYMMDDHH" strings
    rows = []
    for ts in timestamps:
        dt = pd.Timestamp(year=int(ts[0:4]), month=int(ts[4:6]), day=int(ts[6:8]),
                           hour=int(ts[8:10]), tz="UTC")
        rows.append({
            "timestamp_utc": dt,
            "GHI_Wm2": ghi.get(ts, -999.0),
            "GHI_clearsky_Wm2": ghi_cs.get(ts, -999.0),
            "T_amb_C": t2m.get(ts, -999.0),
            "RH_pct": rh2m.get(ts, -999.0),
            "wind_ms": ws10m.get(ts, -999.0),
            "point_id": point_id, "cluster_id": cluster_id, "year": year,
        })
    df = pd.DataFrame(rows)

    # NASA POWER fill value is -999; validate + interpolate short gaps.
    value_cols = ["GHI_Wm2", "GHI_clearsky_Wm2", "T_amb_C", "RH_pct", "wind_ms"]
    df[value_cols] = df[value_cols].mask(df[value_cols] <= -990, np.nan)
    n_missing = int(df[value_cols].isna().any(axis=1).sum())
    n_total = len(df)
    pct_valid = 100.0 * (1 - n_missing / n_total) if n_total else 0.0
    df[value_cols] = df[value_cols].interpolate(limit=3, limit_direction="both")

    # Drop 29 February so every year is exactly 8760 h (matches Rajasthan's
    # io_utils.drop_leap_day and the project's existing convention).
    df = df[~((df["timestamp_utc"].dt.month == 2) & (df["timestamp_utc"].dt.day == 29))].reset_index(drop=True)

    return df, pct_valid, n_missing


def main():
    qc_rows = []
    for cluster_id, medoid in MEDOIDS.items():
        point_id, lat, lon = medoid["point_id"], medoid["lat"], medoid["lon"]
        print(f"\n=== cluster {cluster_id} ({point_id}, {lat}, {lon}) ===")
        year_frames = []
        for year in YEARS:
            print(f"  fetching {point_id} {year}...", end=" ")
            data = _fetch_point_year(point_id, lat, lon, year)
            df, pct_valid, n_missing = _json_to_hourly_df(data, point_id, cluster_id, year)
            df["year_role"] = YEAR_ROLES[year]
            year_frames.append(df)
            status = "OK" if pct_valid >= 98.0 else "FAILED QC"
            print(f"{status} ({pct_valid:.2f}% valid, {n_missing} interpolated/filled)")
            qc_rows.append({"cluster_id": cluster_id, "point_id": point_id, "year": year,
                             "pct_valid": round(pct_valid, 3), "n_missing_hours": n_missing,
                             "year_role": YEAR_ROLES[year], "accepted": pct_valid >= 98.0})

        combined = pd.concat(year_frames, ignore_index=True).sort_values("timestamp_utc").reset_index(drop=True)
        out_path = OUT_DIR / f"weather_regime_tamilnadu_cluster{cluster_id}_hourly_multiyear.csv"
        combined.to_csv(out_path, index=False)
        print(f"  [OK] wrote {out_path} ({len(combined)} rows, {combined['year'].nunique()} years)")

    qc_df = pd.DataFrame(qc_rows)
    qc_path = OUT_DIR / "multiyear_weather_qc.csv"
    qc_df.to_csv(qc_path, index=False)
    print(f"\n[OK] wrote {qc_path}")
    print(qc_df.groupby("accepted").size())
    n_rejected = int((~qc_df["accepted"]).sum())
    if n_rejected:
        print(f"\n[WARN] {n_rejected} point-years failed the 98% valid-hours QC gate -- see {qc_path}")
    else:
        print(f"\nAll {len(qc_df)} point-years passed QC (>=98% valid hours).")


if __name__ == "__main__":
    main()
