"""
scripts/tn_rebuild_weather_from_raw.py
=========================================
Rebuilds the multiyear regime weather files and the per-point-year caches
DIRECTLY from the raw NASA POWER JSONs, and refuses to write anything that
disagrees with independently computed sunrise/sunset times.

WHY THIS EXISTS
---------------
`weather_regime_tamilnadu_cluster{0,1,2}_hourly_multiyear.csv` -- and
therefore all 45 files under data/weather/point_years/tamilnadu/ that were
sliced out of it -- carried the solar columns SHIFTED +5 HOURS against their
own `timestamp_utc`. Every Objective-2 result computed through
`roles.load_point_year` inherited that shift.

The evidence, for TNP_0001 on 2016-06-15 (sunrise 00:13 UTC per
data/objective1/suntimes.csv):

    raw POWER JSON       clearsky 00:00..12:00 UTC, peak 06:00   <- truth
    legacy single-year   clearsky 00:00..12:00 UTC, peak 06:00   <- correct
    multiyear + caches   clearsky 05:00..17:00 UTC, peak 11:00   <- +5 h

A +5 h error is IST (+05:30) truncated to whole hours, so the series was
written against local-clock stamps while being labelled UTC. The raw JSON is
explicit -- `header.time_standard == "UTC"` -- and its own values put solar
noon at 06:00 UTC = 11:30 IST, which is right for Tamil Nadu (~78 E; the IST
meridian is 82.5 E, so local solar noon runs ~12:18 IST).

Consequence of the bug: collector gain peaked at ~16:30 local instead of
~11:30, i.e. four to five hours closer to the 19:00 demand peak than reality.
That biases the evening-window objective -- the study's primary objective --
in favour of PCM, so the shift could not be left in place and corrected for
later.

WHAT IT REBUILDS
----------------
Raw JSONs exist for 2016-2025, which covers every year the pipeline uses:
explore 2016-2020, select 2021-2023, used_test_v1 2024-2025. The held-out
test years 2011-2015 have no raw JSON here, so they are NOT rebuilt and are
dropped from the multiyear file; g10_test cannot run until they are fetched.
That is deliberate -- a locked one-shot test must not be spent on weather
this script cannot verify.

Run:  python scripts/tn_rebuild_weather_from_raw.py [--dry-run]
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.tn0_add_local_hour import add_local_columns   # noqa: E402
from config import WEATHER_DIR, STATE                      # noqa: E402

# REPO_ROOT, not REPO_ROOT.parent: until the 2026-10-30 restructure this file
# lived in rajmethod/scripts/ and reached up into the parent project for the
# raw inputs. The pipeline is now the project root and carries its own
# data/objective1/ (all 60 raw POWER JSONs), so reaching out would escape the
# project entirely.
RAW_DIR = REPO_ROOT / "data" / "objective1" / "raw_weather"
SUNTIMES = REPO_ROOT / "data" / "objective1" / "suntimes.csv"
POINT_YEARS_DIR = WEATHER_DIR / "point_years" / STATE

MEDOIDS = {0: "TNP_0006", 1: "TNP_0007", 2: "TNP_0001"}
YEARS = list(range(2016, 2026))
YEAR_ROLES = {**{y: "test" for y in range(2011, 2016)},
              **{y: "explore" for y in range(2016, 2021)},
              **{y: "select" for y in range(2021, 2024)},
              **{y: "used_test_v1" for y in (2024, 2025)}}

# POWER parameter -> our column name. WS_ms duplicates wind_ms because the
# existing schema carries both and the simulator reads WS_ms.
PARAM_MAP = {"ALLSKY_SFC_SW_DWN": "GHI_Wm2", "CLRSKY_SFC_SW_DWN": "GHI_clearsky_Wm2",
             "T2M": "T_amb_C", "RH2M": "RH_pct", "WS10M": "wind_ms"}
FILL = -999.0

COLUMNS = ["timestamp_utc", "GHI_Wm2", "GHI_clearsky_Wm2", "T_amb_C", "RH_pct",
           "wind_ms", "point_id", "cluster_id", "year", "local_hour", "local_date", "WS_ms"]


def read_raw(point_id: str, year: int) -> pd.DataFrame:
    """One point-year straight out of the POWER JSON, on UTC stamps."""
    path = RAW_DIR / f"power_{point_id}_{year}.json"
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)

    std = doc.get("header", {}).get("time_standard")
    if std != "UTC":
        raise SystemExit(f"{path.name}: time_standard is {std!r}, not 'UTC' -- "
                         "the key-to-UTC assumption below would be wrong")

    param = doc["properties"]["parameter"]
    missing = set(PARAM_MAP) - set(param)
    if missing:
        raise SystemExit(f"{path.name}: missing parameters {sorted(missing)}")

    # Keys are YYYYMMDDHH in the declared time standard (UTC). Parsed as UTC,
    # with NO offset applied -- applying one is exactly the bug being fixed.
    keys = sorted(param["ALLSKY_SFC_SW_DWN"])
    df = pd.DataFrame({"timestamp_utc": pd.to_datetime(keys, format="%Y%m%d%H", utc=True)})
    for src, dst in PARAM_MAP.items():
        v = pd.Series([param[src][k] for k in keys], dtype=float)
        df[dst] = v.mask(v <= FILL + 1.0)        # POWER fills with -999
    df["WS_ms"] = df["wind_ms"]
    df["point_id"] = point_id
    df["year"] = year
    return df


def verify_against_ephemeris(df: pd.DataFrame, point_id: str, year: int) -> None:
    """Refuse the rebuild unless clearsky daylight brackets true sunrise/sunset.

    This is the check the original build lacked. Clearsky irradiance is pure
    solar geometry, so it must be zero before sunrise and after sunset on
    every day -- a property no amount of weather can change, and one that a
    whole-hour timestamp shift breaks immediately.
    """
    if not SUNTIMES.exists():
        print(f"    (no suntimes.csv -- geometry check skipped for {point_id} {year})")
        return
    st = pd.read_csv(SUNTIMES, parse_dates=["time_utc"])
    # suntimes.csv stores naive stamps that are already UTC (column name and
    # the 01:01 sunrise for Chennai in January both say so); label them so.
    if st["time_utc"].dt.tz is None:
        st["time_utc"] = st["time_utc"].dt.tz_localize("UTC")
    st = st[st.point_id == point_id]
    if st.empty:
        print(f"    (no suntimes rows for {point_id} -- check skipped)")
        return

    sun = st.pivot_table(index="date", columns="event", values="time_utc", aggfunc="first")
    if not {"sunrise", "sunset"} <= set(sun.columns):
        print(f"    (suntimes lacks sunrise/sunset for {point_id} -- check skipped)")
        return
    sun.index = pd.to_datetime(sun.index).date

    d = df.dropna(subset=["GHI_clearsky_Wm2"]).copy()
    d["utc_date"] = d["timestamp_utc"].dt.date
    lit = d[d["GHI_clearsky_Wm2"] > 1.0]

    checked = bad = 0
    worst = None
    for day, grp in lit.groupby("utc_date"):
        if day not in sun.index:
            continue
        sr, ss = sun.loc[day, "sunrise"], sun.loc[day, "sunset"]
        if pd.isna(sr) or pd.isna(ss):
            continue
        checked += 1
        # hour-beginning stamps: an hour is lit if it overlaps [sunrise, sunset]
        lo = grp["timestamp_utc"].min()
        hi = grp["timestamp_utc"].max() + pd.Timedelta(hours=1)
        slack = pd.Timedelta(hours=1, minutes=30)
        off = max((sr - lo), (hi - ss), pd.Timedelta(0))
        if off > slack:
            bad += 1
            if worst is None or off > worst[1]:
                worst = (day, off)
    if checked and bad:
        day, off = worst
        raise SystemExit(
            f"GEOMETRY CHECK FAILED for {point_id} {year}: on {bad}/{checked} days the "
            f"clearsky window does not bracket true sunrise/sunset (worst {day}, "
            f"off by {off}). The rebuild was NOT written.")
    print(f"    geometry OK ({checked} days bracket sunrise/sunset within 90 min)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    POINT_YEARS_DIR.mkdir(parents=True, exist_ok=True)
    for cid, point_id in MEDOIDS.items():
        print(f"\n=== cluster {cid}  ({point_id}) ===")
        frames = []
        for year in YEARS:
            if not (RAW_DIR / f"power_{point_id}_{year}.json").exists():
                print(f"  {year}: no raw JSON -- skipped")
                continue
            df = read_raw(point_id, year)
            df["cluster_id"] = cid
            df = add_local_columns(df)
            print(f"  {year}: {len(df)} rows, "
                  f"clearsky peak at UTC hour "
                  f"{int(df.groupby(df.timestamp_utc.dt.hour).GHI_clearsky_Wm2.mean().idxmax())}")
            verify_against_ephemeris(df, point_id, year)

            py = df.copy()
            py["year_role"] = YEAR_ROLES.get(year, "unknown")
            cols = COLUMNS[:9] + ["year_role"] + COLUMNS[9:]
            out = POINT_YEARS_DIR / f"cluster{cid}_{point_id}_{year}.csv"
            if not args.dry_run:
                py[cols].to_csv(out, index=False)
            frames.append(df[COLUMNS])

        if frames:
            multi = pd.concat(frames, ignore_index=True).sort_values("timestamp_utc")
            dst = WEATHER_DIR / f"weather_regime_{STATE}_cluster{cid}_hourly_multiyear.csv"
            if not args.dry_run:
                multi.to_csv(dst, index=False)
            print(f"  -> {dst.name}: {len(multi)} rows, "
                  f"{multi.year.min()}-{multi.year.max()}")

    print("\nDRY RUN -- nothing written." if args.dry_run else "\nrebuilt.")


if __name__ == "__main__":
    main()
