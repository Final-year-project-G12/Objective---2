"""
build_demand_profile.py
===========================
Fills the gap: no demand_profile file exists anywhere in the Objective 1
pipeline. Worse, two DIFFERENT undocumented draw assumptions are already
buried in the Obj1 code and disagree with each other:

  - 04b_climate_signature.py's L_required calculation assumes a flat
    DRAW_VOLUME_L = 300 L/day over a single 7-hour overnight window
    (cited to Avargani et al. 2021).
  - 10_physics_validation.py's actual tank simulation only draws
    DRAW_MASS_KG = 75 kg TWICE a day (07:00 and 19:00 local) = 150 kg/day
    total — HALF of the 300 L/day the signature step assumed.

That mismatch means the L_required numbers baked into
climate_signature_*.csv and the solar-fraction numbers coming out of the
Phase 7 physics validation are not simulating the same household. This
script produces ONE canonical, documented demand profile so every
downstream Obj2 script (simulator, DOE, surrogate) uses the same number
instead of guessing or re-deriving it.

STATED ASSUMPTION (say this plainly in your methodology — do not present
it as measured data):
  Total daily draw: 300 L/day — matches Avargani et al. 2021's tested
  volume (already cited in this project's literature summaries) and
  matches 04b's own L_required calculation, so at minimum Objective 1's
  L_required figures stay internally consistent with what Objective 2
  now simulates.
  Shape: two peaks (morning ~06:00-09:00, evening ~18:00-21:00), evening
  peak larger than morning — the standard dual-peak residential draw
  shape used in Edwards et al. 2015 (cited via Eldokaishi2022 and
  Barqawi2025's literature summaries in this project) and consistent
  with Indian household bathing/cooking timing discussed in
  Chopra2023 and AlMamun2023's summaries. No measured Indian household
  draw-profile data was available for this project, so this is a
  documented synthetic shape, not measured.
  Split: 35% morning / 65% evening (evening bath + cooking draw
  typically dominates in the Indian residential literature reviewed for
  this project) — this specific split ratio is a project assumption,
  not itself individually cited; change EVENING_SHARE below and re-run
  if you have better data.

OUTPUT:
  data/objective1/demand/demand_profile_{STATE}.csv
    One row per hour (0-23): hour, draw_fraction (sums to 1.0 over the
    day), draw_volume_L, draw_mass_kg (≈ volume at water density 1 kg/L).
  Same file applies to every cluster/regime for now (uniform household
  behaviour assumption) — see NEXT_STEPS note at the bottom of this
  script's printed output for how to extend this per-season/per-regime
  later if you get real demand data.

HOW TO RUN:
  python build_demand_profile.py
"""

import numpy as np
import pandas as pd

from config import DATA_DIR

# ── Edit for your state / your project's demand assumption ────────────────
STATE = "tamilnadu"

DAILY_TOTAL_L = 300.0     # matches 04b_climate_signature.py's DRAW_VOLUME_L
                           # (Avargani et al. 2021) — kept identical on purpose,
                           # see module docstring
MORNING_PEAK_HOUR = 7.5    # 07:30 local
EVENING_PEAK_HOUR = 19.0   # 19:00 local
PEAK_WIDTH_HOURS = 1.5     # std-dev-like spread of each draw peak
EVENING_SHARE = 0.65       # fraction of daily volume in the evening peak
WATER_DENSITY_KG_L = 1.0

OUT_DIR = DATA_DIR / "demand"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def gaussian_bump(hours, center, width):
    return np.exp(-0.5 * ((hours - center) / width) ** 2)


def build_profile():
    hours = np.arange(24)
    morning = gaussian_bump(hours, MORNING_PEAK_HOUR, PEAK_WIDTH_HOURS)
    evening = gaussian_bump(hours, EVENING_PEAK_HOUR, PEAK_WIDTH_HOURS)

    morning_share = 1.0 - EVENING_SHARE
    morning_norm = morning / morning.sum() * morning_share
    evening_norm = evening / evening.sum() * EVENING_SHARE
    draw_fraction = morning_norm + evening_norm
    draw_fraction = draw_fraction / draw_fraction.sum()   # exact-sum-to-1 safety

    df = pd.DataFrame({
        "hour": hours,
        "draw_fraction": draw_fraction,
        "draw_volume_L": draw_fraction * DAILY_TOTAL_L,
        "draw_mass_kg": draw_fraction * DAILY_TOTAL_L * WATER_DENSITY_KG_L,
    })
    return df


def main():
    print("=" * 68)
    print(f"  Build Canonical Demand Profile — {STATE}")
    print("=" * 68)
    print(f"\n  Daily total     : {DAILY_TOTAL_L:.0f} L  (matches 04b's L_required assumption)")
    print(f"  Morning peak    : {MORNING_PEAK_HOUR:.1f}h  ({(1-EVENING_SHARE)*100:.0f}% of volume)")
    print(f"  Evening peak    : {EVENING_PEAK_HOUR:.1f}h  ({EVENING_SHARE*100:.0f}% of volume)")

    df = build_profile()
    out = OUT_DIR / f"demand_profile_{STATE}.csv"
    df.to_csv(out, index=False)

    print(f"\n  Peak hourly draw: {df['draw_volume_L'].max():.1f} L "
          f"at hour {int(df.loc[df['draw_volume_L'].idxmax(), 'hour'])}:00")
    print(f"  Sum check       : {df['draw_fraction'].sum():.6f}  (should be 1.000000)")
    print(f"\n  Saved: {out}")
    print("\n  [IMPORTANT] This resolves an existing inconsistency: "
          "10_physics_validation.py's simulator currently only draws 150 kg/day "
          "(75 kg x 2), HALF of the 300 L/day this file and 04b's L_required both "
          "assume. When you build the Obj2 simulator, drive it from THIS file "
          "(300 L/day total, hourly-shaped) so Obj1's L_required numbers and "
          "Obj2's simulated solar fraction are evaluating the same household.")
    print("\n  NEXT STEPS (not done here, documented so you don't forget):")
    print("  - If you get a real/measured Indian household draw profile, replace "
          "build_profile() with it and keep this same output schema.")
    print("  - To vary demand by season (e.g. more bathing in summer), extend this "
          "script to write demand_profile_{state}_{season}.csv per season instead "
          "of one file for the whole year.")
    print("=" * 68)


if __name__ == "__main__":
    main()
