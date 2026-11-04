"""
scripts/tn0_add_local_hour.py
================================
Adds the `local_hour` / `local_date` columns Manvitha's simulator requires
to Tamil Nadu's weather files, and splits the 15-year multi-year files into
the per-year files her year-role machinery expects.

WHY THIS SCRIPT EXISTS. Her `_demand_hour_of_day()` refuses a weather frame
that has `timestamp_utc` but no `local_hour`:

    raise ValueError("weather frame has timestamp_utc but no local_hour; "
                     "refusing to index the local-time demand profile by UTC hour")

That refusal is the G1 fix made structural. The demand profile is defined on
local clock hours (07:00 / 19:00 peaks), so indexing it by UTC put the
evening draw at about 00:30 local -- she measured that error at 30.7 / 34.9 /
32.4 % of plain-tank annual useful energy. Rather than let a caller fall back
to UTC, the data has to carry the local hour explicitly. Her Rajasthan files
do; Tamil Nadu's did not.

IST is UTC+05:30, so local_hour = floor(utc_hour + 5.5) -- FLOOR, not round.
Every UTC hour maps to a half-hour local value (00:00 UTC -> 05:30 IST), and
rounding sends 5.5 to 6 and 6.5 to 6 (both numpy and Python round halves to
even), which collapses the 24 local hours onto 12 buckets and silently drops
half the demand curve.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import WEATHER_DIR, STATE   # noqa: E402

IST_OFFSET = pd.Timedelta(hours=5, minutes=30)


def add_local_columns(df: pd.DataFrame) -> pd.DataFrame:
    ts = pd.to_datetime(df["timestamp_utc"], utc=True)
    local = ts + IST_OFFSET
    out = df.copy()
    out["local_hour"] = local.dt.hour.astype(int)      # floor by construction
    out["local_date"] = local.dt.date.astype(str)
    if "wind_ms" not in out.columns and "WS_ms" in out.columns:
        out["wind_ms"] = out["WS_ms"]
    if "WS_ms" not in out.columns and "wind_ms" in out.columns:
        out["WS_ms"] = out["wind_ms"]
    return out


def main():
    touched, written = 0, 0
    for path in sorted(WEATHER_DIR.glob(f"weather_regime_{STATE}_cluster*_hourly*.csv")):
        df = pd.read_csv(path)
        if "timestamp_utc" not in df.columns:
            continue
        df = add_local_columns(df)
        df.to_csv(path, index=False)
        touched += 1
        print(f"  {path.name}: +local_hour/local_date  ({len(df)} rows)")

        # multi-year file -> one file per year, named the way her per-year
        # gates look them up
        if "multiyear" in path.name and "year" in df.columns:
            cluster = path.name.split("cluster")[1].split("_")[0]
            for year, g in df.groupby("year"):
                out = WEATHER_DIR / f"weather_regime_{STATE}_cluster{cluster}_hourly_{year}.csv"
                g.reset_index(drop=True).to_csv(out, index=False)
                written += 1
    print(f"\n{touched} weather files updated, {written} per-year files written")
    print(f"local_hour check: 00:00 UTC -> {add_local_columns(pd.DataFrame({'timestamp_utc': ['2016-01-01 00:00:00+00:00']}))['local_hour'].iloc[0]} "
          f"(must be 5, not 6)")


if __name__ == "__main__":
    main()
