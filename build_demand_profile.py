"""
build_demand_profile.py  —  Rajasthan
=========================================
Exports the canonical hot-water draw profile as a file, so every Objective 2 script
(simulator, DOE, surrogate) drives off ONE documented schedule instead of each
re-deriving or guessing a number.

READ THIS BEFORE COMPARING WITH THE TAMIL NADU VERSION
-------------------------------------------------------
The Tamil Nadu build_demand_profile.py exists to RESOLVE a contradiction in that
pipeline: its 04b climate-signature step assumes 300 L/day while its
10_physics_validation.py simulator only draws 150 kg/day (75 kg x 2 pulses). Those two
steps were sizing different households.

**Rajasthan has no such contradiction, so this script does not invent a profile — it
exports the one already in the pipeline.** Both Rajasthan steps agree at 300 L/day:

  04_climate_signature_rajasthan.py:233   NIGHT_DRAW_TOTAL_L      = 300.0
  physics_lib.py:340                      DRAW_TOTAL_KG_PER_DAY   = 300.0

and physics_lib already carries a real hourly SHAPE (hourly_draw_fractions(), a
two-Gaussian bimodal curve) rather than instantaneous pulses. This script imports that
function directly and writes it out. Change the shape in physics_lib.py, re-run this,
and O1's L_required and O2's simulated solar fraction stay describing one household —
which is the whole point of the file.

STATED ASSUMPTIONS (present them as assumptions, not measured data):
  Total daily draw: 300 L/day — Avargani et al. 2021's tested volume, already cited
    throughout this project and already the basis of L_required_kJ_per_kg in
    climate_signature_rajasthan.csv.
  Shape: two Gaussian peaks at 07:00 and 19:00 local (IST, UTC+5:30), sigma 1.5 h,
    weighted 0.42 morning / 0.58 evening — evening-dominant, matching the DHW
    consumption literature reviewed for this project (bathing + cooking) and matching
    the Tamil Nadu script's own peak HOURS. No measured Indian household draw-profile
    data was available, so this is a documented synthetic shape.
  The 0.42/0.58 split is a project assumption, not individually cited. It lives in
    physics_lib.hourly_draw_fractions() — change it there, not here, so the O1
    simulator changes with it.

NOTE ON THE SPLIT vs TAMIL NADU: TN uses 0.35/0.65 and normalises each Gaussian bump
before weighting; Rajasthan uses 0.42/0.58 and normalises the combined curve. The two
are close but not identical, so a cross-state comparison of absolute solar fraction
should say which profile each state used.

OUTPUT:
  demand/demand_profile_{STATE}.csv
    One row per local hour (0-23): hour, draw_fraction (sums to 1.0), draw_volume_L,
    draw_mass_kg, cumulative_fraction. Same profile for every cluster and season — a
    stated simplification, not measured per-regime demand.

HOW TO RUN:
  python build_demand_profile.py
"""

import sys

import numpy as np
import pandas as pd

from config import STATE, OBJ1_ROOT, DEMAND_DIR, ensure_dirs

sys.path.insert(0, str(OBJ1_ROOT))
import physics_lib as pl  # noqa: E402

WATER_DENSITY_KG_L = 1.0

# Cross-check target: 04_climate_signature_rajasthan.py's NIGHT_DRAW_TOTAL_L.
# If this ever stops matching physics_lib.DRAW_TOTAL_KG_PER_DAY, the pipeline has
# drifted into the exact inconsistency the Tamil Nadu script had to paper over.
SIGNATURE_NIGHT_DRAW_TOTAL_L = 300.0


def build_profile():
    """The profile Objective 1's own simulator runs on — imported, not re-derived."""
    fracs = pl.hourly_draw_fractions()
    total_kg = pl.DRAW_TOTAL_KG_PER_DAY
    hours = np.arange(24)
    return pd.DataFrame({
        "hour": hours,
        "draw_fraction": fracs,
        "draw_volume_L": fracs * total_kg / WATER_DENSITY_KG_L,
        "draw_mass_kg": fracs * total_kg,
        "cumulative_fraction": np.cumsum(fracs),
    })


def main():
    print("=" * 72)
    print(f"  Export Canonical Demand Profile — {STATE.title()}")
    print("=" * 72)

    ensure_dirs()
    total_kg = pl.DRAW_TOTAL_KG_PER_DAY

    print(f"\n  Source          : physics_lib.hourly_draw_fractions()  "
          f"({OBJ1_ROOT.name})")
    print(f"  Daily total     : {total_kg:.0f} kg/day "
          f"(physics_lib.DRAW_TOTAL_KG_PER_DAY)")
    print(f"  Timezone offset : UTC+{pl.TIMEZONE_OFFSET_HOURS} (IST) — 'hour' is LOCAL")

    if abs(total_kg - SIGNATURE_NIGHT_DRAW_TOTAL_L) > 1e-6:
        print(f"\n  [FAIL] physics_lib draws {total_kg:.1f} kg/day but "
              f"04_climate_signature assumes {SIGNATURE_NIGHT_DRAW_TOTAL_L:.1f} L/day. "
              f"Objective 1's L_required and Objective 2's simulation would be sizing "
              f"different households. Reconcile before using this file.")
        sys.exit(1)
    print(f"  Consistency     : OK — matches 04_climate_signature's "
          f"NIGHT_DRAW_TOTAL_L ({SIGNATURE_NIGHT_DRAW_TOTAL_L:.0f} L/day), so "
          f"L_required and the O2 simulator size the same household")

    df = build_profile()
    out = DEMAND_DIR / f"demand_profile_{STATE}.csv"
    df.to_csv(out, index=False)

    peak = df.loc[df["draw_volume_L"].idxmax()]
    morning = df.loc[df["hour"] < 13, "draw_fraction"].sum()
    print(f"\n  Peak hourly draw: {peak['draw_volume_L']:.1f} L at "
          f"{int(peak['hour']):02d}:00 local")
    print(f"  Morning/evening : {morning * 100:.0f}% / {(1 - morning) * 100:.0f}%")
    print(f"  Sum check       : {df['draw_fraction'].sum():.6f}  (should be 1.000000)")
    print(f"\n  Saved: {out}")

    print("\n  NEXT STEPS (documented so they don't get lost):")
    print("  - If real/measured Indian household draw data turns up, change "
          "hourly_draw_fractions() in physics_lib.py — NOT this script — so Objective 1 "
          "and Objective 2 move together, then re-run this.")
    print("  - To vary demand by season, extend physics_lib with a season argument and "
          "write demand_profile_{state}_{season}.csv per season here.")
    print("=" * 72)


if __name__ == "__main__":
    main()
