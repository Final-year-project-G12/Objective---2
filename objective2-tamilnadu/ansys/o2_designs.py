"""
ansys/o2_designs.py
===================
The Objective-2 designs the Fluent demos run, read from the CURRENT results (common plant: 100 L / 2.0 m2 / 175 L/day).

Why this file exists: the demos used to read results/tn_optimal_designs.csv, which belongs to the LEGACY plant and was archived in the
common-plant rebuild. With the file gone, fluent_live_demo.py silently fell back to a hard-coded legacy table (regime 0 -> n-Hexacosane),
so a live demo would have shown the wrong PCM without saying so. One loader, one source of truth.

Precedence:
  1. results/c16_funnel_winners.csv  (the frozen funnel's winners; PCM mass from results/common100L_<hash>/c17_test_by_year.csv)
  2. results/tn_optimal_designs.csv  LEGACY, only if (1) is absent; the returned `source` says so.

load() returns a DataFrame with columns: regime, pcm, R_in_m, fraction, N, pcm_mass_kg, source   (None if neither file exists).
"""
from pathlib import Path

import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
WINNERS = PROJECT / "results" / "c16_funnel_winners.csv"
LEGACY = PROJECT / "results" / "tn_optimal_designs.csv"


def load():
    if WINNERS.exists():
        d = pd.read_csv(WINNERS)
        d = d[d.recommendation == "PCM"]
        mass = {}
        for p in sorted((PROJECT / "results").glob("common100L_*/c17_test_by_year.csv")):
            mass = pd.read_csv(p).groupby("regime").pcm_mass_kg.first().to_dict()
        return pd.DataFrame({
            "regime": d.regime.astype(int).values, "pcm": d.pcm.values, "R_in_m": d.R_in_m.values,
            "fraction": d.fraction.values, "N": d.N.astype(int).values,
            "pcm_mass_kg": [mass.get(int(r)) for r in d.regime],
            "source": "results/c16_funnel_winners.csv (common plant)"})
    if LEGACY.exists():
        d = pd.read_csv(LEGACY)
        out = d.rename(columns={"R_in_m": "R_in_m"})[["regime", "pcm", "R_in_m", "fraction", "N", "pcm_mass_kg"]].copy()
        out["source"] = "results/tn_optimal_designs.csv (LEGACY plant: 2.5 m2, 300 L/day)"
        return out.reset_index(drop=True)
    return None


if __name__ == "__main__":
    d = load()
    print("no design file found" if d is None else d.to_string(index=False))
