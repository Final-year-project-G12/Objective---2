"""
build_regime_weather.py
===========================
Fills the gap: Objective 1 (as built) produces weather PER POINT (raw
hourly NASA POWER JSON, daily aggregates) but never a per-CLUSTER
representative weather file. The Obj2 simulator/DOE wants one file per
regime, not per point — this script builds that.

For each cluster it uses the MEDOID point (highest GMM membership
probability, from cluster_assignments_*.csv) as the regime's
representative location — same choice 10_physics_validation.py already
makes internally; this script just saves the result as a reusable file
instead of rebuilding it inside every downstream script.

OUTPUTS (per cluster k):
  data/objective1/weather/weather_regime_{STATE}_cluster{k}_hourly.csv
      Real (not synthetic) hourly series for the medoid's most-complete
      year, from the raw NASA POWER cache copied by build_input_package.py.
      Columns: timestamp_utc, GHI_Wm2, GHI_clearsky_Wm2, T_amb_C, RH_pct,
      wind_ms, point_id, cluster_id, year.

  data/objective1/weather/weather_regime_{STATE}_cluster{k}_daily.csv
      Multi-year (all years on disk) daily-resolution series for the
      medoid, from daily_aggregates_{STATE}.csv. Better than the hourly
      file for DOE runs that need several years/seasons cheaply.
      Columns: date, GHI_daily_kWh, GHIcs_daily_kWh, kt_daily, Ta_mean_C,
      Ta_max_C, Ta_min_C, DTR_C, RH_mean_pct, wind_mean_ms, point_id,
      cluster_id.

HOW TO RUN (after build_input_package.py):
  python build_regime_weather.py
"""

import json
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

from config import OBJ1_FROZEN_DIR, OBJ1_FROZEN_WEATHER_DIR, DATA_DIR

# ── Edit this if you're running the pipeline for a different state ────────
STATE = "tamilnadu"

ASSIGN_FILE = OBJ1_FROZEN_DIR / f"cluster_assignments_{STATE}.csv"
DAILY_FILE = OBJ1_FROZEN_DIR / f"daily_aggregates_{STATE}.csv"
OUT_DIR = DATA_DIR / "weather"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MIN_HOURS_FOR_COMPLETE_YEAR = 8000   # out of ~8760 — picks the best-covered year


def load_medoids():
    assign = pd.read_csv(ASSIGN_FILE)
    idx = assign.groupby("cluster_id")["max_membership_prob"].idxmax()
    return assign.loc[idx, ["cluster_id", "point_id"]].reset_index(drop=True)


def load_point_hourly(point_id):
    """Concatenate every cached year's raw NASA POWER JSON for one point."""
    frames = {}
    for fp in sorted(OBJ1_FROZEN_WEATHER_DIR.glob(f"power_{point_id}_*.json")):
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
        print(f"  [WARN] cluster {cid} (medoid {point_id}): no raw hourly cache found "
              f"under {OBJ1_FROZEN_WEATHER_DIR} — did build_input_package.py run "
              f"successfully for this medoid?")
        return None

    best_year = max(frames, key=lambda y: len(frames[y]))
    if len(frames[best_year]) < MIN_HOURS_FOR_COMPLETE_YEAR:
        print(f"  [NOTE] cluster {cid}: best year {best_year} only has "
              f"{len(frames[best_year])} hours (<{MIN_HOURS_FOR_COMPLETE_YEAR}) — using it "
              f"anyway, flag as partial-year in your methodology if you rely on this file.")

    df = frames[best_year].rename(columns={
        "ALLSKY_SFC_SW_DWN": "GHI_Wm2",
        "CLRSKY_SFC_SW_DWN": "GHI_clearsky_Wm2",
        "T2M": "T_amb_C",
        "RH2M": "RH_pct",
        "WS10M": "wind_ms",
    })
    df = df.reset_index().rename(columns={"index": "timestamp_utc"})
    df["point_id"] = point_id
    df["cluster_id"] = cid
    df["year"] = int(best_year)
    return df


def build_daily_for_cluster(cid, point_id, daily_all):
    sub = daily_all[daily_all["point_id"] == point_id].copy()
    if sub.empty:
        print(f"  [WARN] cluster {cid} (medoid {point_id}): no rows in {DAILY_FILE.name}")
        return None
    rename = {
        "GHI_daily_kWh": "GHI_daily_kWh", "GHIcs_daily_kWh": "GHIcs_daily_kWh",
        "kt_daily": "kt_daily", "Ta_mean_true": "Ta_mean_C",
        "Ta_max_true": "Ta_max_C", "Ta_min_true": "Ta_min_C",
        "DTR_true": "DTR_C", "RH_mean_true": "RH_mean_pct",
        "wind_mean_true": "wind_mean_ms",
    }
    sub = sub.rename(columns={k: v for k, v in rename.items() if k in sub.columns})
    sub["cluster_id"] = cid
    return sub


def main():
    print("=" * 68)
    print(f"  Build Per-Regime Representative Weather — {STATE}")
    print("=" * 68)

    if not ASSIGN_FILE.exists():
        print(f"\n  ERROR: {ASSIGN_FILE} not found — run build_input_package.py first.")
        return

    medoids = load_medoids()
    print(f"\n  Clusters: {len(medoids)}")

    daily_all = pd.read_csv(DAILY_FILE, parse_dates=["date"]) if DAILY_FILE.exists() else None
    if daily_all is None:
        print(f"  [WARN] {DAILY_FILE} not found — daily regime files will be skipped.")

    n_hourly_ok, n_daily_ok = 0, 0
    for row in medoids.itertuples(index=False):
        cid, point_id = row.cluster_id, row.point_id
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
                print(f"    [OK] daily  -> {out.name}  ({len(daily):,} rows, "
                      f"{pd.to_datetime(daily['date']).dt.year.nunique()} years)")
                n_daily_ok += 1

    print("\n" + "=" * 68)
    print(f"  DONE — hourly files: {n_hourly_ok}/{len(medoids)}   "
          f"daily files: {n_daily_ok}/{len(medoids)}")
    print(f"  Output: {OUT_DIR}/")
    print("=" * 68)


if __name__ == "__main__":
    main()
