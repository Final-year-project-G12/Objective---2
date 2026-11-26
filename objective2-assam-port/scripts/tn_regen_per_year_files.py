"""
scripts/tn_regen_per_year_files.py
==================================
Regenerates data/weather/weather_regime_tamilnadu_cluster{c}_hourly_{year}.csv
(2011-2025, all 3 regimes) from the verified point-year files.

WHY: those per-year files were split from the multiyear CSV at 08:02 on
2026-10-29, BEFORE the LST->UTC rebuild (17:53 same day). They kept the old
+5 h shift (GHI peak at UTC hour 11 instead of ~06) and, for leap years,
were 8760 rows. The point-year files and *_hourly_multiyear.csv were rebuilt
and are correct; the per-year files were never re-split.

Source = data/weather/point_years/tamilnadu (rebuilt from raw LST with a
measured offset and an ephemeris gate). Each output is re-verified:
  * GHI mean-profile peak at UTC hour 5-7 (IST noon = 06:30 UTC)
  * no GHI in the 18:00-22:00 UTC band (that is local night)
  * full-year hourly row count (8760/8784), strictly hourly
  * identical to the point-year source and (2016-2025) to the multiyear file
Nothing is written for a regime unless every check passes.
"""
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from config import WEATHER_DIR, STATE   # noqa: E402

PY = WEATHER_DIR / "point_years" / STATE
MEDOIDS = {0: "ASP_0012", 1: "ASP_0092", 2: "ASP_0028"}
YEARS = range(2011, 2026)


def check(df, year):
    t = pd.to_datetime(df["timestamp_utc"], utc=True)
    n = 8784 if (year % 4 == 0 and (year % 100 or year % 400 == 0)) else 8760
    assert len(df) == n, f"{year}: {len(df)} rows, expected {n}"
    assert t.diff().dropna().eq(pd.Timedelta(hours=1)).all(), f"{year}: not hourly"
    assert (t.dt.year == year).all(), f"{year}: stray years"
    g = df["GHI_Wm2"].groupby(t.dt.hour).mean()
    assert g.idxmax() in (5, 6, 7), f"{year}: GHI peaks at UTC {g.idxmax()}"
    assert g.loc[18:22].max() < 1.0, f"{year}: GHI at local night"


def main():
    out = {}
    for cid, pid in MEDOIDS.items():
        mult = pd.read_csv(WEATHER_DIR / f"weather_regime_{STATE}_cluster{cid}_hourly_multiyear.csv")
        for y in YEARS:
            df = pd.read_csv(PY / f"cluster{cid}_{pid}_{y}.csv")
            check(df, y)
            if y >= 2016:
                m = mult[mult.year == y].reset_index(drop=True)
                assert len(m) == len(df) and (m["GHI_Wm2"].values == df["GHI_Wm2"].values).all(), \
                    f"cluster{cid} {y}: differs from multiyear file"
            old = WEATHER_DIR / f"weather_regime_{STATE}_cluster{cid}_hourly_{y}.csv"
            if "year_role" not in df.columns and old.exists():
                role = pd.read_csv(old, usecols=["year_role"])["year_role"].iloc[0]
                df.insert(df.columns.get_loc("local_hour"), "year_role", role)
            out[old] = df
    for p, df in out.items():
        df.to_csv(p, index=False)
    print(f"verified and wrote {len(out)} per-year files")


if __name__ == "__main__":
    main()
