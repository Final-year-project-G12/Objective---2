"""
scripts/g7_paired.py
=======================
G7 - pairs the sensitivity rows of every regime against the water-only REF run and writes results/g7_sensitivity_paired.csv (read by fig8).
d_<m> = row - REF for the same regime, year and tank model; pct_useful and pct_del45 are d_ as a percentage of REF. The REF rows are dropped.
In objective2-rajasthan this file was assembled by hand with the same rule (checked: its d_* equal row - REF to 1e-14).
Usage: python scripts/g7_paired.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.weather.inventory import REGIMES

RD = Path("results")
KEY = ["regime", "year", "model"]
DIFF = ["useful_energy_kWh", "E_del45_annual_kWh", "E_del45_window_kWh", "tau_hold_mean_h", "tau_serve_mean_h", "serve_frac_45_mean",
        "E_rec45_mean_kWh"]

if __name__ == "__main__":
    raw = pd.concat([pd.read_csv(RD / f"g7_sensitivity_r{c}.csv", encoding="utf-8") for c in REGIMES], ignore_index=True)
    ref = raw[raw.block == "REF"].set_index(KEY)[DIFF]
    p = raw[raw.block != "REF"].join(ref, on=KEY, rsuffix="_ref")
    for m in DIFF:
        p[f"d_{m}"] = p[m] - p[f"{m}_ref"]
    p["pct_useful"] = 100 * p.d_useful_energy_kWh / p.useful_energy_kWh_ref
    p["pct_del45"] = 100 * p.d_E_del45_annual_kWh / p.E_del45_annual_kWh_ref
    p = p.drop(columns=[f"{m}_ref" for m in DIFF])
    p.to_csv(RD / "g7_sensitivity_paired.csv", index=False, encoding="utf-8")
    print(f"wrote {RD / 'g7_sensitivity_paired.csv'}: {len(p)} rows, valid {int(p.valid.astype(bool).sum())}, "
          f"unpaired {int(p.d_useful_energy_kWh.isna().sum())}")
