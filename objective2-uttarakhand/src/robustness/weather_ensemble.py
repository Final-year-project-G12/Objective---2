"""
src/robustness/weather_ensemble.py
======================================
Phase 8 upgrade -- closes the audit gap "Monte Carlo limited to medoid
weather + noise (no historical-year ensemble)". Objective 1 already
pulled a full 10-year (2016-2025) daily ERA5/POWER archive
(data/objective1/daily_aggregates_<state>.csv, 133 population-grid
points x 10 years) to build the climate signature, but Objective 2's
Phase 8 Monte Carlo previously only ever perturbed the single medoid
weather year with a SYNTHETIC uniform annual scale/offset
(rng.uniform(0.93, 1.07) etc.) -- an assumed range, not an observed one.

This module builds an EMPIRICAL annual-weather ensemble instead: for
each of the state's climate regimes (GMM clusters), it computes the
population-weighted annual-mean GHI and ambient temperature for each of
the 10 real calendar years actually on disk, expressed as a (ghi_scale,
tamb_offset_C) pair relative to that cluster's own 10-year mean. Phase
8's Monte Carlo then samples one of these 10 REAL observed years per
draw (src/robustness/monte_carlo.py), instead of an assumed distribution
shape.

Still a proxy in one respect, documented rather than hidden: only daily
(not sub-daily/hourly) multi-year data was pulled for this project, so
the SHAPE of each hour within a day still comes from the single medoid
year's hourly file, with independent per-hour jitter layered on top (see
monte_carlo.py). The ANNUAL magnitude, which dominates solar_fraction
variance, is now real inter-annual variability, not an assumed range.
"""

import functools

import pandas as pd

from config import BASE_DIR


@functools.lru_cache(maxsize=None)
def _load_archive(state: str) -> pd.DataFrame:
    daily = pd.read_csv(BASE_DIR / "data" / "objective1" / f"daily_aggregates_{state}.csv",
                         usecols=["point_id", "date", "GHI_daily_kWh", "Ta_mean_true"])
    daily["year"] = daily["date"].str[:4].astype(int)

    assign = pd.read_csv(BASE_DIR / "data" / "objective1" / f"cluster_assignments_{state}.csv",
                          usecols=["point_id", "cluster_id", "population"])
    return daily.merge(assign, on="point_id", how="inner")


@functools.lru_cache(maxsize=None)
def build_historical_annual_ensemble(state: str) -> pd.DataFrame:
    """Returns one row per (cluster_id, year): population-weighted annual
    mean GHI_daily_kWh / Ta_mean_true for that year, plus ghi_scale and
    tamb_offset_C relative to that cluster's own 10-year mean. Also
    writes data/objective1/historical_annual_ensemble_<state>.csv so the
    table is inspectable without re-deriving it."""
    df = _load_archive(state)

    # population-weighted daily mean per (cluster, year, date), then a
    # plain mean across days -> population-weighted annual mean per
    # (cluster, year). Weighting once at the daily level and averaging
    # across ~365 equally-weighted days is equivalent to weighting the
    # whole year at once, and is simpler to reason about.
    df = df.copy()
    df["w_ghi"] = df["GHI_daily_kWh"] * df["population"]
    df["w_ta"] = df["Ta_mean_true"] * df["population"]

    daily_wmean = df.groupby(["cluster_id", "year", "date"]).agg(
        w_ghi_sum=("w_ghi", "sum"), w_ta_sum=("w_ta", "sum"), pop_sum=("population", "sum"),
    ).reset_index()
    daily_wmean["ghi_pw"] = daily_wmean["w_ghi_sum"] / daily_wmean["pop_sum"]
    daily_wmean["ta_pw"] = daily_wmean["w_ta_sum"] / daily_wmean["pop_sum"]

    annual = daily_wmean.groupby(["cluster_id", "year"]).agg(
        ghi_daily_kWh_mean=("ghi_pw", "mean"), ta_mean_true_mean=("ta_pw", "mean"),
        n_days=("date", "count"),
    ).reset_index()

    baseline = annual.groupby("cluster_id").agg(
        ghi_10yr_mean=("ghi_daily_kWh_mean", "mean"), ta_10yr_mean=("ta_mean_true_mean", "mean"),
    ).reset_index()
    annual = annual.merge(baseline, on="cluster_id", how="left")
    annual["ghi_scale"] = annual["ghi_daily_kWh_mean"] / annual["ghi_10yr_mean"]
    annual["tamb_offset_C"] = annual["ta_mean_true_mean"] - annual["ta_10yr_mean"]

    out_path = BASE_DIR / "data" / "objective1" / f"historical_annual_ensemble_{state}.csv"
    annual.sort_values(["cluster_id", "year"]).to_csv(out_path, index=False)
    return annual


def load_historical_ensemble(state: str, cluster_id: int):
    """Returns a list of (ghi_scale, tamb_offset_C) tuples -- one per real
    observed year -- for the given cluster, for Phase 8's Monte Carlo to
    sample from."""
    annual = build_historical_annual_ensemble(state)
    rows = annual[annual["cluster_id"] == cluster_id]
    return list(zip(rows["ghi_scale"].tolist(), rows["tamb_offset_C"].tolist()))


if __name__ == "__main__":
    import sys
    state = sys.argv[1] if len(sys.argv) > 1 else "uttarakhand"
    ensemble = build_historical_annual_ensemble(state)
    print(f"Historical annual weather ensemble for state={state}:")
    print(ensemble.to_string(index=False))
    print(f"\nSaved: data/objective1/historical_annual_ensemble_{state}.csv")
