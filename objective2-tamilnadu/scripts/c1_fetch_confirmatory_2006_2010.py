"""
scripts/c1_fetch_confirmatory_2006_2010.py
============================================
Common-plant rebuild, level L2 / data gate (rule R3): fetch the 2006-2010 hourly weather for the three Tamil Nadu
medoid points. These five years become the single confirmatory test set for O2 (and later O3).

Same source, same request and same parameters as scripts' original NASA POWER download (01b_download_nasapower.py):
hourly point API, community RE, ALLSKY/CLRSKY SW, T2M, RH2M, WS10M, UTC. NASA POWER hourly data start in 2001.
Only downloads; it does not look at the values. Writes data/objective1/raw_weather/power_<point>_<year>.json.
Usage: python scripts/c1_fetch_confirmatory_2006_2010.py
"""
import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "objective1" / "raw_weather"
POINTS = {"TNP_0006": (10.875, 78.625), "TNP_0007": (10.875, 76.875), "TNP_0001": (13.125, 80.125)}  # regime 0,1,2 medoids
YEARS = range(2006, 2011)
BASE = "https://power.larc.nasa.gov/api/temporal/hourly/point"
PARAMS = "ALLSKY_SFC_SW_DWN,CLRSKY_SFC_SW_DWN,T2M,RH2M,WS10M"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    for pid, (lat, lon) in POINTS.items():
        for y in YEARS:
            f = OUT / f"power_{pid}_{y}.json"
            if f.exists() and f.stat().st_size > 10_000:
                print("skip", f.name)
                continue
            q = {"start": f"{y}0101", "end": f"{y}1231", "latitude": lat, "longitude": lon, "community": "RE",
                 "parameters": PARAMS, "format": "JSON", "time-standard": "UTC"}
            for attempt in range(1, 4):
                try:
                    r = s.get(BASE, params=q, timeout=180)
                    r.raise_for_status()
                    d = r.json()
                    if not d.get("properties", {}).get("parameter"):
                        raise ValueError("empty parameter block")
                    f.write_text(json.dumps(d), encoding="utf-8")
                    print("ok", f.name, round(f.stat().st_size / 1e3), "KB", flush=True)
                    break
                except Exception as e:                                  # noqa: BLE001
                    print("fail", attempt, f.name, repr(e)[:200], flush=True)
                    time.sleep(20)
            else:
                sys.exit(f"could not download {f.name}")
            time.sleep(1.0)


if __name__ == "__main__":
    main()
