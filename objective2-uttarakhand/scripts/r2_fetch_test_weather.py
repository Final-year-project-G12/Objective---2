"""
scripts/r2_fetch_test_weather.py  -  rebuild level L2: the 2006-2010 confirmatory-test weather (plan rule R3)
==============================================================================================================
Downloads NASA POWER hourly data for the four regime medoids, 2006-2010, with exactly the request Objective 1 used for 2016-2025
(PCM-Selection-ML-model/era5-uttarakhand/01b_download_nasapower.py): hourly point API, community RE,
parameters ALLSKY_SFC_SW_DWN,CLRSKY_SFC_SW_DWN,T2M,RH2M,WS10M, format JSON, time-standard UTC. Coordinates are the O1 grid
coordinates from data/objective1/cluster_assignments_uttarakhand.csv (the same as in the 2016-2025 raw files).

Writes data/weather/raw_test_2006_2010/power_<point>_<year>.json (20 files). Only downloads and checks that the response is not
empty; it does not look at the values (they are the one-shot test years).
Usage: python scripts/r2_fetch_test_weather.py
"""
import json
import sys
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.weather.inventory import CURRENT_MEDOIDS      # noqa: E402

OUT = ROOT / "data" / "weather" / "raw_test_2006_2010"
YEARS = range(2006, 2011)
BASE = "https://power.larc.nasa.gov/api/temporal/hourly/point"
PARAMS = "ALLSKY_SFC_SW_DWN,CLRSKY_SFC_SW_DWN,T2M,RH2M,WS10M"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pts = pd.read_csv(ROOT / "data" / "objective1" / "cluster_assignments_uttarakhand.csv").set_index("point_id")
    s = requests.Session()
    for cid, pid in CURRENT_MEDOIDS.items():
        lat, lon = float(pts.loc[pid, "lat"]), float(pts.loc[pid, "lon"])
        for y in YEARS:
            f = OUT / f"power_{pid}_{y}.json"
            if f.exists() and f.stat().st_size > 10_000:
                print("skip", f.name)
                continue
            q = {"start": f"{y}0101", "end": f"{y}1231", "latitude": lat, "longitude": lon, "community": "RE",
                 "parameters": PARAMS, "format": "JSON", "time-standard": "UTC"}
            for attempt in range(1, 4):
                try:
                    r = s.get(BASE, params=q, timeout=120)
                    r.raise_for_status()
                    d = r.json()
                    if not any(d.get("properties", {}).get("parameter", {}).values()):
                        raise ValueError("empty parameter block")
                    f.write_text(json.dumps(d), encoding="utf-8")
                    print(f"ok   {f.name} ({f.stat().st_size // 1024} kB)")
                    break
                except Exception as e:                      # noqa: BLE001
                    print(f"retry {attempt} {f.name}: {e}")
                    time.sleep(5 * attempt)
            else:
                raise SystemExit(f"failed: {f.name}")
            time.sleep(1)


if __name__ == "__main__":
    main()
