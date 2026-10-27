"""
scripts/g19_fetch_test2_weather.py
====================================
v3 (cap 30 %) untouched test years. All of 2016-2025 were already assigned (explore / select / used test), so the new
one-shot test uses 2011-2015 at the same three medoid points, from the same source and with the same request as the
original download (PCM-Selection-ML-model/era5-rajasthan/01b_download_nasapower.py): NASA POWER hourly point API,
community RE, parameters ALLSKY_SFC_SW_DWN,CLRSKY_SFC_SW_DWN,T2M,RH2M,WS10M, UTC. Approved by the user in chat 2026-10-27
("Earlier years").

Writes data/weather/raw_test_2011_2015/power_<point>_<year>.json (15 files). Only downloads; does not look at the values.
Usage: python scripts/g19_fetch_test2_weather.py
"""
import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "weather/raw_test_2011_2015"
POINTS = {"RJP_0132": (24.375, 74.125), "RJP_0192": (26.875, 73.375), "RJP_0083": (26.625, 75.875)}   # (lat, lon), from the 2024 raw files
YEARS = range(2011, 2016)
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
                    r = s.get(BASE, params=q, timeout=120)
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
