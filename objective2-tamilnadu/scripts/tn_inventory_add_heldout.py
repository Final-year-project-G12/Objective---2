"""
scripts/tn_inventory_add_heldout.py
===================================
Adds the 2011-2015 held-out point-years to weather_inventory.csv.

They are not produced by src/weather/inventory.build_point_year, which reads a
UTC raw file and derives everything from it. The held-out years come from the
LST set and were converted and geometry-checked by
tn_rebuild_heldout_from_lst.py, so their QC statistics are computed here from
the written cache, and `time_standard` records LST-converted rather than UTC so
the provenance difference is visible in the inventory itself and not lost.

Run: python scripts/tn_inventory_add_heldout.py
"""
import hashlib
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.weather import roles                       # noqa: E402
from config import STATE                            # noqa: E402

LST_DIR = REPO_ROOT / "data" / "weather" / "raw_nasapower_LST"
MEDOIDS = {0: "TNP_0006", 1: "TNP_0007", 2: "TNP_0001"}
YEARS = list(range(2011, 2016))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    inv = pd.read_csv(roles.INVENTORY_PATH)
    existing = {(int(r.cluster_id), int(r.year)) for r in inv.itertuples()}
    rows = []

    for cid, point_id in MEDOIDS.items():
        for year in YEARS:
            if (cid, year) in existing:
                print(f"  cluster {cid} {year}: already in inventory, skipped")
                continue
            cache = roles.point_year_path(STATE, cid, point_id, year)
            if not cache.exists():
                print(f"  cluster {cid} {year}: cache missing, skipped")
                continue
            d = pd.read_csv(cache, parse_dates=["timestamp_utc"])
            ghi = d["GHI_Wm2"]
            clear = d["GHI_clearsky_Wm2"]
            expected = 8784 if year % 4 == 0 else 8760
            # the loader drops 29 February on read, so the on-disk row count is
            # the full year and the post-drop count is what the roles layer sees
            after_leap = len(d[~((d.timestamp_utc.dt.month == 2) & (d.timestamp_utc.dt.day == 29))])
            gaps = int(ghi.isna().sum())
            raw = LST_DIR / f"power_{point_id}_{year}.json"
            rows.append({
                "state": STATE, "cluster_id": cid, "point_id": point_id, "year": year,
                "role": "test",
                "raw_file": raw.name,
                "raw_sha256": sha256(raw) if raw.exists() else "",
                # NOT "UTC": these came from the LST set and were converted by a
                # measured -5 h offset. Recording the real provenance is the
                # whole lesson of the 2026-10-29 defect.
                "time_standard": "LST->UTC(-5h, measured)",
                "n_hours_expected": expected,
                "n_keys_found": len(d),
                "hourly_sequence_ok": bool(d.timestamp_utc.is_monotonic_increasing
                                           and d.timestamp_utc.diff().dropna().eq(
                                               pd.Timedelta(hours=1)).all()),
                "n_invalid_hours": gaps,
                "pct_valid": round(100.0 * (1 - gaps / max(len(d), 1)), 4),
                "n_gaps": gaps,
                "max_gap_h": int(ghi.isna().astype(int).groupby(
                    ghi.notna().cumsum()).sum().max() or 0),
                "n_other_vars_missing_hours": int(d[["T_amb_C", "RH_pct", "wind_ms"]].isna().any(axis=1).sum()),
                "accepted": True,
                "reject_reason": "",
                "n_filled_hours": 0,
                "n_negative_ghi": int((ghi < 0).sum()),
                "n_ghi_above_clearsky_1p1": int((ghi > 1.1 * clear).sum()),
                "GHI_annual_kWh_m2": round(float(ghi.fillna(0).sum()) / 1000.0, 5),
                "T_amb_mean_C": float(d["T_amb_C"].mean()),
                "n_hours_after_leap_drop": after_leap,
            })
            print(f"  cluster {cid} {year}: {len(d)} rows, GHI {rows[-1]['GHI_annual_kWh_m2']:.1f} kWh/m2, "
                  f"{rows[-1]['pct_valid']:.2f}% valid")

    if not rows:
        print("\nnothing to add.")
        return
    out = pd.concat([inv, pd.DataFrame(rows)], ignore_index=True)
    out = out.sort_values(["cluster_id", "year"]).reset_index(drop=True)
    out.to_csv(roles.INVENTORY_PATH, index=False)
    print(f"\ninventory now {len(out)} rows ({len(rows)} added), years "
          f"{int(out.year.min())}-{int(out.year.max())}")


if __name__ == "__main__":
    main()
