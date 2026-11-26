"""
scripts/a2_build_regime_weather.py
==================================
Lays out the regime-level weather files from the accepted point-years (data/weather/point_years/assam/, built by
src/weather/inventory.py from the NASA POWER JSONs):

  weather_regime_assam_cluster{c}_hourly_multiyear.csv    2011-2025, all years, one file per regime
  weather_regime_assam_cluster{c}_hourly_{year}.csv       one file per year (the per-year gates and Objective 3 look these up)
  weather_regime_assam_cluster{c}_hourly.csv              the legacy single-year file named in states/assam.yaml: 2016,
                                                          the same choice Tamil Nadu made for its legacy file

The point-year files are the single source; nothing here re-reads the raw JSON. Usage: python scripts/a2_build_regime_weather.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import WEATHER_DIR, STATE   # noqa: E402
from src.weather.inventory import CURRENT_MEDOIDS, YEARS   # noqa: E402

COLUMNS = ["timestamp_utc", "GHI_Wm2", "GHI_clearsky_Wm2", "T_amb_C", "RH_pct",
           "wind_ms", "point_id", "cluster_id", "year", "local_hour", "local_date", "WS_ms"]
LEGACY_YEAR = 2016


def main():
    src = WEATHER_DIR / "point_years" / STATE
    for cid, pid in CURRENT_MEDOIDS.items():
        frames = []
        for y in YEARS:
            df = pd.read_csv(src / f"cluster{cid}_{pid}_{y}.csv")[COLUMNS]
            df.to_csv(WEATHER_DIR / f"weather_regime_{STATE}_cluster{cid}_hourly_{y}.csv", index=False)
            if y == LEGACY_YEAR:
                df.to_csv(WEATHER_DIR / f"weather_regime_{STATE}_cluster{cid}_hourly.csv", index=False)
            frames.append(df)
        multi = pd.concat(frames, ignore_index=True)
        multi.to_csv(WEATHER_DIR / f"weather_regime_{STATE}_cluster{cid}_hourly_multiyear.csv", index=False)
        print(f"cluster {cid} ({pid}): {len(multi)} rows, {multi.year.min()}-{multi.year.max()}")


if __name__ == "__main__":
    main()
