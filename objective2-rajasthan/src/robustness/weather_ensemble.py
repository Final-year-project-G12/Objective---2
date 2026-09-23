"""
src/robustness/weather_ensemble.py
======================================
Step 6.2 of the 2026-09-20 fix plan ("Objective2 rajasthan fix plan.md")
-- PORTED FROM objective2-tamilnadu/src/robustness/weather_ensemble.py.
Closes the audit gap "Monte Carlo limited to medoid weather + noise (no
historical-year ensemble)": Phase 8's robustness pass previously only
ever perturbed the single medoid weather year with a SYNTHETIC uniform
annual scale/offset (rng.uniform(0.93, 1.07) etc, still used by
src/robustness/monte_carlo.py's old _sample_scenario as of this port) --
an assumed range, not an observed one. Objective 1 already pulled a full
10-year (2016-2025) daily NASA POWER archive
(data/objective1/daily_aggregates_rajasthan.csv, 320 population-grid
points x 10 years) to build the climate signature; this module turns
that into an EMPIRICAL annual-weather ensemble: for each Rajasthan GMM
cluster, the population-weighted annual-mean GHI and ambient temperature
for each of the 10 real calendar years actually on disk, expressed as a
(ghi_scale, tamb_offset_C) pair relative to that cluster's own 10-year
mean. Phase 8's Monte Carlo can then sample one of these 10 REAL observed
years per draw, instead of an assumed distribution shape.

ADAPTATION FOR RAJASTHAN (columns differ from Tamil Nadu's
daily_aggregates_tamilnadu.csv): this file has `GHI_Wh_m2` (daily total,
Wh/m2 -- divided by 1000 for kWh/m2) and `T2M_mean` (daily mean ambient
temperature, deg C) rather than Tamil Nadu's already-kWh `GHI_daily_kWh`
and `Ta_mean_true`. No column is silently assumed; both are read
explicitly by name below.

Still a proxy in one respect, documented rather than hidden (same
caveat as Tamil Nadu's version): only daily (not sub-daily/hourly)
multi-year data was pulled for this project, so the SHAPE of each hour
within a day still comes from the single medoid year's hourly file, with
independent per-hour jitter layered on top (see monte_carlo.py). The
ANNUAL magnitude, which dominates solar_fraction variance, is now real
inter-annual variability, not an assumed range.
"""

import functools

import pandas as pd

from config import BASE_DIR


@functools.lru_cache(maxsize=None)
def _load_archive(state: str) -> pd.DataFrame:
    daily = pd.read_csv(BASE_DIR / "data" / "objective1" / f"daily_aggregates_{state}.csv",
                         usecols=["point_id", "date", "GHI_Wh_m2", "T2M_mean"])
    daily["GHI_daily_kWh"] = daily["GHI_Wh_m2"] / 1000.0
    daily["Ta_mean_true"] = daily["T2M_mean"]
    daily["year"] = daily["date"].str[:4].astype(int)

    assign = pd.read_csv(BASE_DIR / "data" / "objective1" / f"cluster_assignments_{state}.csv",
                          usecols=["point_id", "cluster_id", "population"])
    return daily.merge(assign, on="point_id", how="inner")


@functools.lru_cache(maxsize=None)
def build_historical_annual_ensemble(state: str) -> pd.DataFrame:
    """Returns one row per (cluster_id, year): population-weighted annual
    mean GHI_daily_kWh / Ta_mean_true for that year, plus ghi_scale and
    tamb_offset_C relative to that cluster's own multi-year mean. Also
    writes data/objective1/historical_annual_ensemble_<state>.csv so the
    table is inspectable without re-deriving it."""
    df = _load_archive(state)

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
        ghi_baseline_mean=("ghi_daily_kWh_mean", "mean"), ta_baseline_mean=("ta_mean_true_mean", "mean"),
    ).reset_index()
    annual = annual.merge(baseline, on="cluster_id", how="left")
    annual["ghi_scale"] = annual["ghi_daily_kWh_mean"] / annual["ghi_baseline_mean"]
    annual["tamb_offset_C"] = annual["ta_mean_true_mean"] - annual["ta_baseline_mean"]

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
    state = sys.argv[1] if len(sys.argv) > 1 else "rajasthan"
    ensemble = build_historical_annual_ensemble(state)
    print(f"Historical annual weather ensemble for state={state}:")
    print(ensemble.to_string(index=False))
    print(f"\nSaved: data/objective1/historical_annual_ensemble_{state}.csv")
