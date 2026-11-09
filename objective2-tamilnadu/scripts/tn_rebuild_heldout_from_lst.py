"""
scripts/tn_rebuild_heldout_from_lst.py
======================================
Rebuilds the held-out years 2011-2015 from the LST-stamped raw NASA POWER
files, and refuses to write anything that disagrees with solar geometry.

WHY THESE YEARS WERE BLOCKED, AND WHY THEY NEED NOT BE
------------------------------------------------------
On 2026-10-29 the per-point-year cache was found to carry a +5 h solar shift
and every point-year was rebuilt from raw. 2011-2015 could not be: the only
raw files then in hand (data/objective1/raw_weather/) cover 2016-2025. Those
five years were quarantined and the one-shot held-out test was declared
blocked by construction.

A second raw set was later found in the retired tree, now promoted to
data/weather/raw_nasapower_LST/. It covers 2011-2025 for all three medoids --
and its header reads:

    "time_standard": "LST"

Local Solar Time, not UTC. THAT IS THE ORIGIN OF THE ORIGINAL BUG: this set
was read as though its keys were UTC, which at ~80 E is wrong by about five
hours. The defect was never in the pipeline's arithmetic; it was in treating
LST keys as UTC keys.

THE OFFSET IS MEASURED, NOT ASSUMED
-----------------------------------
2016-2025 exist in BOTH sets -- LST here and UTC in data/objective1/raw_weather
-- so the offset is determined by overlapping the two rather than by computing
longitude/15 and hoping:

    shift -6h  corr 0.94312
    shift -5h  corr 1.00000      <- exact
    shift -4h  corr 0.94312

A correlation of exactly 1.0 means the two series are the same data, displaced
by precisely five whole hours. So UTC = LST - 5 h.

That offset is re-measured at run time for every point from its own overlap
years, and a point whose measured offset is not a clean whole-hour match is
refused rather than converted on a guess.

Run:  python scripts/tn_rebuild_heldout_from_lst.py [--dry-run]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.tn0_add_local_hour import add_local_columns      # noqa: E402
from config import WEATHER_DIR, STATE                         # noqa: E402

LST_DIR = REPO_ROOT / "data" / "weather" / "raw_nasapower_LST"
UTC_DIR = REPO_ROOT / "data" / "objective1" / "raw_weather"
SUNTIMES = REPO_ROOT / "data" / "objective1" / "suntimes.csv"
POINT_YEARS_DIR = WEATHER_DIR / "point_years" / STATE

MEDOIDS = {0: "TNP_0006", 1: "TNP_0007", 2: "TNP_0001"}
HELD_OUT_YEARS = list(range(2011, 2016))
OVERLAP_YEARS = list(range(2016, 2026))

PARAM_MAP = {"ALLSKY_SFC_SW_DWN": "GHI_Wm2", "CLRSKY_SFC_SW_DWN": "GHI_clearsky_Wm2",
             "T2M": "T_amb_C", "RH2M": "RH_pct", "WS10M": "wind_ms"}
FILL = -999.0
COLUMNS = ["timestamp_utc", "GHI_Wm2", "GHI_clearsky_Wm2", "T_amb_C", "RH_pct",
           "wind_ms", "point_id", "cluster_id", "year", "local_hour", "local_date", "WS_ms"]


def _series(path: Path, param="CLRSKY_SFC_SW_DWN"):
    doc = json.load(open(path, encoding="utf-8"))
    p = doc["properties"]["parameter"][param]
    keys = sorted(p)
    return doc, keys, np.array([p[k] for k in keys], dtype=float)


def measure_offset_hours(point_id: str) -> int:
    """Hours to shift the LST series so it lines up with the UTC series.

    Measured on every year present in both sets. A point is only accepted if
    every overlap year agrees on the same whole-hour shift AND that shift
    reproduces the UTC series essentially exactly.
    """
    votes, corrs = [], []
    for year in OVERLAP_YEARS:
        lp, up = LST_DIR / f"power_{point_id}_{year}.json", UTC_DIR / f"power_{point_id}_{year}.json"
        if not (lp.exists() and up.exists()):
            continue
        _, _, a = _series(lp)
        _, _, b = _series(up)
        n = min(len(a), len(b))
        a, b = a[:n], b[:n]
        best = max(range(-12, 13), key=lambda s: np.corrcoef(np.roll(a, s), b)[0, 1])
        votes.append(best)
        corrs.append(float(np.corrcoef(np.roll(a, best), b)[0, 1]))
    if not votes:
        raise SystemExit(f"{point_id}: no overlapping years, cannot measure the LST offset")
    if len(set(votes)) != 1:
        raise SystemExit(f"{point_id}: overlap years disagree on the offset {sorted(set(votes))} -- "
                         "refusing to convert on a guess")
    if min(corrs) < 0.9999:
        raise SystemExit(f"{point_id}: best-shift correlation only {min(corrs):.5f}; "
                         "the two sources are not the same data, refusing to convert")
    print(f"  {point_id}: LST->UTC shift {votes[0]:+d} h "
          f"(agreed across {len(votes)} overlap years, min corr {min(corrs):.5f})")
    return votes[0]


def _one_file_as_utc(point_id: str, year: int, shift_h: int) -> pd.DataFrame:
    """One LST file, re-stamped onto true UTC (no year filtering)."""
    doc = json.load(open(LST_DIR / f"power_{point_id}_{year}.json", encoding="utf-8"))
    std = doc.get("header", {}).get("time_standard")
    if std != "LST":
        raise SystemExit(f"power_{point_id}_{year}.json: time_standard is {std!r}, expected 'LST'")
    param = doc["properties"]["parameter"]
    missing = set(PARAM_MAP) - set(param)
    if missing:
        raise SystemExit(f"power_{point_id}_{year}.json: missing {sorted(missing)}")

    keys = sorted(param["ALLSKY_SFC_SW_DWN"])
    # The keys are LOCAL SOLAR time. np.roll(values, shift) is what the offset
    # was measured with, so the equivalent on timestamps is to move the clock
    # by shift: a value stamped 11:00 LST belongs at 06:00 UTC for shift=-5.
    stamps = pd.to_datetime(keys, format="%Y%m%d%H", utc=True) + pd.Timedelta(hours=shift_h)
    df = pd.DataFrame({"timestamp_utc": stamps})
    for src, dst in PARAM_MAP.items():
        v = pd.Series([param[src][k] for k in keys], dtype=float)
        df[dst] = v.mask(v <= FILL + 1.0)
    return df


def read_lst_as_utc(point_id: str, year: int, shift_h: int) -> pd.DataFrame:
    """A COMPLETE UTC year, stitched across the LST file boundary.

    Shifting by -5 h moves every stamp back, so one LST file does not cover one
    UTC year: its first 5 hours fall into the previous UTC year, and the last 5
    hours of this UTC year sit at the START of the NEXT LST file. Taking a
    single file and filtering to `year` therefore yields 8755 rows, not 8760 --
    five hours missing at 31 December, every year.

    That shortfall is silent and would have propagated into the held-out
    evaluation, so the next year's file is read and its leading hours are
    appended. The result is asserted to be exactly 8760 (8784 in a leap year)
    with no duplicate or missing hour.
    """
    df = _one_file_as_utc(point_id, year, shift_h)
    nxt = LST_DIR / f"power_{point_id}_{year + 1}.json"
    if nxt.exists():
        df = pd.concat([df, _one_file_as_utc(point_id, year + 1, shift_h)], ignore_index=True)

    df = df[df["timestamp_utc"].dt.year == year].sort_values("timestamp_utc")
    df = df.drop_duplicates("timestamp_utc").reset_index(drop=True)

    expected = 8784 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 8760
    if len(df) != expected:
        raise SystemExit(
            f"{point_id} {year}: stitched to {len(df)} hours, expected {expected}. "
            f"The LST file for {year + 1} is needed to complete this UTC year "
            f"({'present' if nxt.exists() else 'MISSING'}).")
    step = df["timestamp_utc"].diff().dropna()
    if not step.eq(pd.Timedelta(hours=1)).all():
        raise SystemExit(f"{point_id} {year}: stitched series is not strictly hourly")

    df["WS_ms"] = df["wind_ms"]
    df["point_id"] = point_id
    df["year"] = year
    return df


def verify_against_ephemeris(df: pd.DataFrame, point_id: str, year: int) -> None:
    """The same gate the 2016-2025 rebuild had to pass."""
    if not SUNTIMES.exists():
        raise SystemExit("suntimes.csv missing -- refusing to write unverifiable held-out weather")
    st = pd.read_csv(SUNTIMES, parse_dates=["time_utc"])
    if st["time_utc"].dt.tz is None:
        st["time_utc"] = st["time_utc"].dt.tz_localize("UTC")
    st = st[st.point_id == point_id]
    if st.empty:
        raise SystemExit(f"no suntimes rows for {point_id} -- cannot verify")

    sun = st.pivot_table(index="date", columns="event", values="time_utc", aggfunc="first")
    if not {"sunrise", "sunset"} <= set(sun.columns):
        raise SystemExit("suntimes lacks sunrise/sunset")
    sun.index = pd.to_datetime(sun.index)

    # suntimes.csv covers 2016-2025 only, and these are the 2011-2015 years, so
    # no date matches directly. Sunrise and sunset are fixed by latitude and
    # day-of-year; across a 15-year span the same calendar day moves by a
    # minute or two, against the 90-minute tolerance used below. So the
    # reference is taken by MONTH-DAY, averaged over the covered years, which
    # is the same astronomy with the year stripped out.
    ref = sun.copy()
    ref["md"] = ref.index.strftime("%m-%d")
    # times -> seconds since midnight UTC so they can be averaged, then back
    for ev in ("sunrise", "sunset"):
        ref[ev + "_s"] = (ref[ev] - ref[ev].dt.normalize()).dt.total_seconds()
    by_md = ref.groupby("md")[["sunrise_s", "sunset_s"]].mean()

    d = df.dropna(subset=["GHI_clearsky_Wm2"]).copy()
    d["utc_date"] = d["timestamp_utc"].dt.date
    lit = d[d["GHI_clearsky_Wm2"] > 1.0]
    slack = pd.Timedelta(hours=1, minutes=30)
    checked = bad = 0
    worst = None
    for day, grp in lit.groupby("utc_date"):
        md = f"{day.month:02d}-{day.day:02d}"
        if md not in by_md.index:
            continue
        base = pd.Timestamp(day, tz="UTC")
        sr = base + pd.Timedelta(seconds=float(by_md.loc[md, "sunrise_s"]))
        ss = base + pd.Timedelta(seconds=float(by_md.loc[md, "sunset_s"]))
        if pd.isna(sr) or pd.isna(ss):
            continue
        checked += 1
        lo = grp["timestamp_utc"].min()
        hi = grp["timestamp_utc"].max() + pd.Timedelta(hours=1)
        off = max((sr - lo), (hi - ss), pd.Timedelta(0))
        if off > slack:
            bad += 1
            if worst is None or off > worst[1]:
                worst = (day, off)
    if not checked:
        raise SystemExit(f"{point_id} {year}: no days could be checked against suntimes")
    if bad:
        day, off = worst
        raise SystemExit(
            f"GEOMETRY CHECK FAILED for {point_id} {year}: {bad}/{checked} days do not bracket "
            f"sunrise/sunset (worst {day}, off by {off}). NOT written.")
    print(f"    {year}: geometry OK ({checked} days bracket sunrise/sunset within 90 min)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    POINT_YEARS_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for cid, point_id in MEDOIDS.items():
        print(f"\n=== cluster {cid} ({point_id}) ===")
        shift = measure_offset_hours(point_id)
        for year in HELD_OUT_YEARS:
            if not (LST_DIR / f"power_{point_id}_{year}.json").exists():
                print(f"    {year}: no LST file -- skipped")
                continue
            df = read_lst_as_utc(point_id, year, shift)
            df["cluster_id"] = cid
            df = add_local_columns(df)
            verify_against_ephemeris(df, point_id, year)
            df["year_role"] = "test"
            cols = COLUMNS[:9] + ["year_role"] + COLUMNS[9:]
            out = POINT_YEARS_DIR / f"cluster{cid}_{point_id}_{year}.csv"
            if not args.dry_run:
                df[cols].to_csv(out, index=False)
            written += 1
    print(f"\n{'DRY RUN -- nothing written.' if args.dry_run else f'wrote {written} held-out point-years.'}")


if __name__ == "__main__":
    main()
