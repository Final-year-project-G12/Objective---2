"""
scripts/tn_final_summary.py
===========================
The Tamil Nadu answer, in one place: the optimal design per regime, and an
explicit pass/fail on every threshold the method defines.

Reads only files the pipeline already wrote -- nothing is re-simulated and no
number is typed in here. Writes:

    results/tn_optimal_designs.csv    one row per regime: the chosen design
    results/tn_threshold_report.csv   one row per (regime, PCM): every gate

THE THRESHOLDS (from g10_select.py's documented rule, not invented here)
------------------------------------------------------------------------
  beats_water   select-year paired g_window EXCEEDS the WP6 repeatability band
                (wp6_band.csv). Clearing the band is what separates "better
                than a plain water tank" from "indistinguishable from one" --
                a gain smaller than the band is noise, not a benefit.
  pcm_peak_ok   PCM peak <= 65 C in every select year (user decision)
  water_peak_ok water peak <= 75 C in every select year
  feasible      geometry admissible (packing + count rule)

A regime PASSES when its chosen design clears all four. The per-PCM table
answers the stronger question -- whether EVERY shortlisted PCM clears them,
not just the winner.

Run: python scripts/tn_final_summary.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

OUT = REPO / "results"
REGIMES = (0, 1, 2)
PCM_PEAK_LIMIT_C = 65.0
WATER_PEAK_LIMIT_C = 75.0

# Design columns worth reporting, in the order a reader wants them.
DESIGN_COLS = ["pcm", "R_in_m", "fraction", "flow", "arrangement", "N",
               "pcm_mass_kg", "t_pcm_max", "g_window", "g_annual", "d_overheat"]


def _num(d, key):
    v = d.get(key)
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


def main():
    missing = [c for c in REGIMES if not (OUT / f"g10_selection_r{c}.json").exists()]
    if missing:
        raise SystemExit(
            f"g10_selection_r{missing}.json not found -- g10_select has not run yet. "
            f"This script reports the pipeline's answer; it does not compute one.")

    rows, gates = [], []
    for cid in REGIMES:
        log = json.loads((OUT / f"g10_selection_r{cid}.json").read_text())
        band = log.get("band", {})
        band_gw = float(band.get("g_window", float("nan")))

        if "chosen" not in log:
            rows.append({"regime": cid, "verdict": log.get("verdict", "no chosen design")})
            continue

        ch = log["chosen"]
        row = {"regime": cid}
        row.update({c: ch.get(c) for c in DESIGN_COLS})
        row["capsule_diameter_mm"] = _num(ch, "R_in_m") * 2000.0 + 1.6   # +2x0.8 mm wall
        row["band_g_window"] = band_gw
        row["beats_water"] = bool(log.get("meaningful_on_primary_metric", False))
        row["n_indistinguishable"] = log.get("n_S0_indistinguishable_on_g_window")
        row["fingerprint"] = log.get("fingerprint_sha256", "")[:12]
        rows.append(row)

        # Every shortlisted PCM of this regime, not only the winner -- the
        # question "do ALL the PCMs clear the thresholds" cannot be answered
        # from the chosen design alone.
        for alt in log.get("alternatives_best_per_pcm", []):
            gw = _num(alt, "g_window")
            tp = _num(alt, "t_pcm_max")
            tw = _num(alt, "t_water_max")
            gates.append({
                "regime": cid,
                "pcm": alt.get("pcm"),
                "is_chosen": alt.get("pcm") == ch.get("pcm"),
                "g_window": gw,
                "band_g_window": band_gw,
                "margin_over_band": gw - band_gw,
                "beats_water": bool(gw > band_gw),
                "t_pcm_max": tp,
                "pcm_peak_ok": bool(tp <= PCM_PEAK_LIMIT_C) if tp == tp else None,
                "t_water_max": tw,
                "water_peak_ok": bool(tw <= WATER_PEAK_LIMIT_C) if tw == tw else None,
                "d_overheat": _num(alt, "d_overheat"),
            })

    des = pd.DataFrame(rows)
    des.to_csv(OUT / "tn_optimal_designs.csv", index=False)
    gat = pd.DataFrame(gates)
    gat.to_csv(OUT / "tn_threshold_report.csv", index=False)

    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 60)

    print("=" * 100)
    print("OPTIMAL DESIGN PER REGIME  (select years 2021-2023)")
    print("=" * 100)
    show = [c for c in ["regime", "pcm", "capsule_diameter_mm", "fraction", "flow", "arrangement",
                        "N", "pcm_mass_kg", "t_pcm_max", "g_window", "band_g_window",
                        "beats_water"] if c in des.columns]
    print(des[show].to_string(index=False))

    if not gat.empty:
        print()
        print("=" * 100)
        print("THRESHOLD REPORT  -- every shortlisted PCM, every gate")
        print("=" * 100)
        print(gat.to_string(index=False))

        n_pass = int(gat.beats_water.sum())
        print(f"\nbeats_water: {n_pass}/{len(gat)} (regime, PCM) pairs clear the repeatability band")
        for cid in REGIMES:
            g = gat[gat.regime == cid]
            if len(g):
                print(f"  regime {cid}: {int(g.beats_water.sum())}/{len(g)} PCMs clear the band "
                      f"(band = {g.band_g_window.iloc[0]:.2f} kWh/yr)")
        fails = gat[~gat.beats_water]
        if len(fails):
            print("\nDID NOT CLEAR THE BAND:")
            print(fails[["regime", "pcm", "g_window", "band_g_window", "margin_over_band"]]
                  .to_string(index=False))

    print(f"\nwrote {OUT / 'tn_optimal_designs.csv'}")
    print(f"wrote {OUT / 'tn_threshold_report.csv'}")


if __name__ == "__main__":
    main()
