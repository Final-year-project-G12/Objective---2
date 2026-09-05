"""
build_regime_weather.py  —  Rajasthan
=========================================
Objective 1 produces weather PER POINT (raw hourly NASA POWER JSON, sun-event CSVs,
daily aggregates) but never a per-CLUSTER representative weather file. The Obj2
simulator/DOE wants one file per regime. This builds that.

For each Level-A cluster it uses the MEDOID point — nearest to the cluster mean in the
standardized (*_z) clustering space, via Objective 1's own physics_lib.find_medoid, the
same point 09_physics_validation_rajasthan.py simulates. build_input_package.py already
froze those medoids to medoid_points_{state}.csv and copied their raw NASA POWER cache;
this script reads from the frozen copies, not from Objective 1, so the weather actually
used is the version-locked one.

OUTPUTS (per cluster k):

  weather/weather_regime_{STATE}_cluster{k}_hourly.csv
      REAL hourly series for the medoid's most-complete year, loaded through
      physics_lib.load_nasapower_hourly_year (same completeness rule Objective 1
      applies: most recent year with a full 8760/8784-h record and <1% fill values,
      falling back to older years, then linear-interpolating the remaining gaps).
      Columns: timestamp_utc, GHI_Wm2, T_amb_C, RH_pct, WS_ms, local_hour,
      local_date, point_id, cluster_id, year.

  weather/weather_regime_{STATE}_cluster{k}_hourly_10yr.csv   (--all-years)
      Every qualifying year concatenated, 2016-2025, for multi-year DOE runs.

  weather/weather_regime_{STATE}_cluster{k}_daily.csv
      All available years at daily resolution, from the medoid subset of
      daily_aggregates_{STATE}.csv that build_input_package.py cut.

  weather/weather_regime_{STATE}_cluster{k}_sunevents.csv
      Sunrise / solar-noon / sunset rows, 2016-2025, from Objective 1's cleaned
      per-event table. Cheapest driver of the three; carries the ERA5 columns
      (DNI/DHI/cloud cover/pressure/SZA) that the NASA POWER hourly cache does not.

DIFFERENCE FROM THE TAMIL NADU PRECEDENT
    Tamil Nadu's version synthesises an hourly GHI/T_amb curve from daily aggregates,
    because its pipeline has no hourly cache to read. Rajasthan's does — 320 points x
    2016-2025 of genuine hourly ALLSKY_SFC_SW_DWN / T2M / RH2M / WS10M — so the hourly
    files here are measured reanalysis, not a reconstructed sinusoid. Say that
    explicitly in the methodology; it is a real fidelity difference between the two
    states' D2.3 inputs, not a cosmetic one.

HOW TO RUN (after build_input_package.py):
  python build_regime_weather.py
  python build_regime_weather.py --all-years     # also write the 10-year hourly files
  python build_regime_weather.py --skip-sunevents # skip the 1.5 GB streaming pass
"""

import argparse
import sys
import warnings

import pandas as pd

from config import (
    STATE, OBJ1_ROOT, OBJ1_PROCESSED_DIR, FROZEN_DIR, FROZEN_WEATHER_DIR,
    WEATHER_DIR, ensure_dirs,
)

sys.path.insert(0, str(OBJ1_ROOT))
import physics_lib as pl  # noqa: E402

MEDOID_FILE = FROZEN_DIR / f"medoid_points_{STATE}.csv"
DAILY_SUBSET_FILE = FROZEN_DIR / f"daily_aggregates_medoids_{STATE}.csv"
SUNEVENT_SOURCE = OBJ1_PROCESSED_DIR / f"climate_{STATE}_points_clean.csv"
SUNEVENT_CHUNKSIZE = 400_000


def load_medoids():
    if not MEDOID_FILE.exists():
        print(f"  ERROR: {MEDOID_FILE.name} not found — run build_input_package.py first.")
        sys.exit(1)
    return pd.read_csv(MEDOID_FILE)


def build_hourly(cid, point_id, year=None):
    """One year of real hourly weather, via Objective 1's own loader."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("always")
            df = pl.load_nasapower_hourly_year(point_id, FROZEN_WEATHER_DIR, year=year)
    except (FileNotFoundError, ValueError) as exc:
        print(f"    [WARN] cluster {cid} ({point_id}): {exc}")
        return None
    df = df.reset_index().rename(columns={"index": "timestamp_utc"})
    df["point_id"] = point_id
    df["cluster_id"] = cid
    df["year"] = df.attrs.get("year_used") if df.attrs else None
    return df


def build_hourly_all_years(cid, point_id):
    years = pl.list_available_years(point_id, FROZEN_WEATHER_DIR)
    frames = []
    for y in sorted(years):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                d = pl.load_nasapower_hourly_year(point_id, FROZEN_WEATHER_DIR, year=y)
        except (FileNotFoundError, ValueError):
            print(f"      year {y}: incomplete/failed completeness check — skipped")
            continue
        d = d.reset_index().rename(columns={"index": "timestamp_utc"})
        d["year"] = y
        frames.append(d)
    if not frames:
        return None
    out = pd.concat(frames, ignore_index=True)
    out["point_id"] = point_id
    out["cluster_id"] = cid
    return out


def build_daily(cid, point_id, daily_all):
    if daily_all is None:
        return None
    sub = daily_all[daily_all["point_id"] == point_id].copy()
    if sub.empty:
        print(f"    [WARN] cluster {cid} ({point_id}): no rows in "
              f"{DAILY_SUBSET_FILE.name}")
        return None
    sub["cluster_id"] = cid
    return sub


def build_sunevents(medoids):
    """One streaming pass over the 1.5 GB cleaned per-event table, split by regime."""
    if not SUNEVENT_SOURCE.exists():
        print(f"  [SKIP] {SUNEVENT_SOURCE.name} not found.")
        return {}

    point_to_cluster = dict(zip(medoids["point_id"], medoids["cluster_id"]))
    targets = {int(c): WEATHER_DIR / f"weather_regime_{STATE}_cluster{int(c)}_sunevents.csv"
               for c in medoids["cluster_id"]}
    for p in targets.values():
        p.unlink(missing_ok=True)

    header_written, kept, seen = set(), {c: 0 for c in targets}, 0
    print(f"  streaming {SUNEVENT_SOURCE.name} "
          f"({SUNEVENT_SOURCE.stat().st_size / 1e6:.0f} MB) — a couple of minutes ...")
    for i, chunk in enumerate(pd.read_csv(SUNEVENT_SOURCE, chunksize=SUNEVENT_CHUNKSIZE,
                                          low_memory=False), 1):
        seen += len(chunk)
        hit = chunk[chunk["point_id"].isin(point_to_cluster)]
        if hit.empty:
            continue
        hit = hit.assign(cluster_id=hit["point_id"].map(point_to_cluster))
        for cid, part in hit.groupby("cluster_id"):
            cid = int(cid)
            part.to_csv(targets[cid], mode="a", index=False,
                        header=cid not in header_written)
            header_written.add(cid)
            kept[cid] += len(part)
        if i % 5 == 0:
            print(f"    … {seen:,} rows scanned, {sum(kept.values()):,} kept")
    return kept


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all-years", action="store_true",
                    help="also write the concatenated 10-year hourly file per regime")
    ap.add_argument("--skip-sunevents", action="store_true",
                    help="skip the streaming pass over the 1.5 GB per-event table")
    args = ap.parse_args()

    print("=" * 72)
    print(f"  Build Per-Regime Representative Weather — {STATE.title()}")
    print("=" * 72)

    ensure_dirs()
    medoids = load_medoids()
    print(f"\n  Regimes: {len(medoids)}   (medoids from {MEDOID_FILE.name})")

    daily_all = None
    if DAILY_SUBSET_FILE.exists():
        daily_all = pd.read_csv(DAILY_SUBSET_FILE, parse_dates=["date"])
    else:
        print(f"  [WARN] {DAILY_SUBSET_FILE.name} not found — daily files will be skipped.")

    n_hourly, n_daily, n_multi = 0, 0, 0
    for row in medoids.itertuples(index=False):
        cid, point_id = int(row.cluster_id), row.point_id
        print(f"\n  Cluster {cid}  (medoid {point_id}) ...")

        hourly = build_hourly(cid, point_id)
        if hourly is not None:
            out = WEATHER_DIR / f"weather_regime_{STATE}_cluster{cid}_hourly.csv"
            hourly.to_csv(out, index=False)
            print(f"    [OK] hourly -> {out.name}  ({len(hourly):,} rows, "
                  f"year {hourly['year'].iloc[0]})")
            n_hourly += 1

        if args.all_years:
            multi = build_hourly_all_years(cid, point_id)
            if multi is not None:
                out = WEATHER_DIR / f"weather_regime_{STATE}_cluster{cid}_hourly_10yr.csv"
                multi.to_csv(out, index=False)
                print(f"    [OK] hourly (all years) -> {out.name}  "
                      f"({len(multi):,} rows, {multi['year'].nunique()} years)")
                n_multi += 1

        daily = build_daily(cid, point_id, daily_all)
        if daily is not None:
            out = WEATHER_DIR / f"weather_regime_{STATE}_cluster{cid}_daily.csv"
            daily.to_csv(out, index=False)
            print(f"    [OK] daily  -> {out.name}  ({len(daily):,} rows, "
                  f"{pd.to_datetime(daily['date']).dt.year.nunique()} years)")
            n_daily += 1

    n_sun = 0
    if not args.skip_sunevents:
        print("\n  Sun-event series (sunrise/noon/sunset, 2016-2025) ...")
        kept = build_sunevents(medoids)
        for cid, n in sorted(kept.items()):
            print(f"    [OK] cluster {cid}: {n:,} rows")
            n_sun += 1

    print("\n" + "=" * 72)
    print(f"  DONE — hourly: {n_hourly}/{len(medoids)}   daily: {n_daily}/{len(medoids)}"
          + (f"   10-yr hourly: {n_multi}/{len(medoids)}" if args.all_years else "")
          + (f"   sun-event: {n_sun}/{len(medoids)}" if not args.skip_sunevents else ""))
    print(f"  Output: {WEATHER_DIR}")
    print("=" * 72)


if __name__ == "__main__":
    main()
