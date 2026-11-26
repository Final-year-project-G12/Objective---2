"""
scripts/a1_fetch_assam_power.py
===============================
Assembles the raw NASA POWER hourly JSONs for Assam's three regime medoids, 2011-2025, in
data/objective1/raw_weather/power_<point>_<year>.json (the layout the Tamil Nadu rebuild script reads).

  * ASP_0012 and ASP_0028, 2016-2025: copied from era5-assam/data/raw/nasapower (already downloaded in Objective 1).
  * everything else (ASP_0012/0028 2011-2015 and ASP_0092 2011-2025): downloaded from the NASA POWER hourly point API,
    community RE, parameters ALLSKY_SFC_SW_DWN, CLRSKY_SFC_SW_DWN, T2M, RH2M, WS10M, time-standard UTC -- the same
    request as Objective 1's 01b_download_nasapower.py and as Tamil Nadu's g19_fetch_test2_weather.py.
Only the three latitude/longitude pairs are sent. Approved by the user in chat 2026-11-19 ("Fetch NASA POWER").
Resumable: files that already exist and are larger than 10 kB are skipped.

Usage: python scripts/a1_fetch_assam_power.py
"""
import json
import shutil
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "objective1" / "raw_weather"
OBJ1_RAW = Path(r"D:/Final Year Project/PCM-Selection-ML-model/era5-assam/data/raw/nasapower")
POINTS = {"ASP_0012": (26.375, 92.125), "ASP_0092": (26.875, 94.875), "ASP_0028": (27.625, 94.875)}   # (lat, lon), O1 manifest
YEARS = range(2011, 2026)
BASE = "https://power.larc.nasa.gov/api/temporal/hourly/point"
PARAMS = "ALLSKY_SFC_SW_DWN,CLRSKY_SFC_SW_DWN,T2M,RH2M,WS10M"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    for pid, (lat, lon) in POINTS.items():
        for y in YEARS:
            f = OUT / f"power_{pid}_{y}.json"
            if f.exists() and f.stat().st_size > 10_000:
                continue
            local = OBJ1_RAW / f"power_{pid}_{y}.json"
            if local.exists():
                shutil.copy2(local, f)
                print("copied", f.name, flush=True)
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
    print("done:", len(list(OUT.glob("power_*.json"))), "files")


if __name__ == "__main__":
    main()
