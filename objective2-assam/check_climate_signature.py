"""
check_climate_signature.py
==========================
Phase 0 climate-signature sanity check for Rajasthan (Bug-Fix 8 in
O2_Unified_PerState_Execution_Framework.md, and the "Climate-signature
sanity check" line in docs_objective2/01_PHASE1_CONFIG_AND_STATE_SETUP.md).

WHY THIS EXISTS
  Objective 2 consumes whatever weather files sit under data/weather/. If
  the wrong state's files were copied in (or a regime was mislabelled),
  every downstream number — L_required, solar fraction, the whole PCM
  comparison — would be silently wrong but still "run fine". This script
  is the cheap up-front guard: it confirms the frozen Rajasthan weather
  actually looks like Rajasthan (hot, dry, high-clearness) and not like
  Tamil Nadu (coastal-humid) or Assam (humid-cloudy), and that the files
  are internally clean (no duplicate days, no calendar gaps, medoid ids
  match Objective 1).

  There is no simulator or geometry code here — this only reads the
  frozen data/ tree and configs/states/rajasthan.yaml.

WHAT IT CHECKS (per Level-A GMM regime, cluster_id 0/1/2)
  1. Mean GHI_daily_kWh in the dry-climate band 3.0-7.0 kWh/m2/day
     (framework doc §2: Rajasthan is the "high ~6.0" state; Objective 1's
     all-month population-weighted regime means land at ~5.0-5.4).
  2. Hot summer: Apr-Jun mean daily-max ambient in 33-47 C
     (Rajasthan summer maxima, framework doc state table).
  3. Medoid point id in the daily file == the id in
     medoid_points_rajasthan.csv (RJP_0132 / RJP_0202 / RJP_0055).
  4. No duplicate (point_id, date) rows; no missing calendar days over
     the file's own date span.
  5. Cross-check regime size against cluster_profiles_rajasthan.csv.
  Also prints the hot-dry corroborating indices (CDD24, DTR, Ta_p95,
  cloudy_frac, kt_daily) so the signature can be eyeballed.

OUTPUT
  - Console summary, one block per regime, ending in PASSED / STOP.
  - results/rajasthan/phase0_climate_signature_check.txt (same text).
  A STOP here means: do not proceed to Phase 2 — recheck Objective 1.

HOW TO RUN
  python check_climate_signature.py
"""

from pathlib import Path

import pandas as pd
import yaml

from config import BASE_DIR, DATA_DIR, CONFIGS_DIR, RESULTS_DIR

# ── Edit for your state / your project's expected signature ───────────────
STATE = "rajasthan"

GHI_BAND_KWH = (3.0, 7.0)         # dry climates sit high in this band
SUMMER_TMAX_BAND_C = (33.0, 47.0)  # Apr-Jun mean daily-max ambient, Rajasthan
SUMMER_MONTHS = (4, 5, 6)

WEATHER_DIR = DATA_DIR / "weather"
OBJ1_DIR = DATA_DIR / "objective1"
STATE_YAML = CONFIGS_DIR / "states" / f"{STATE}.yaml"
# NOTE: this project folder (objective2-rajasthan/) is already state-specific,
# so results/ is not nested per-state again (that previously produced a
# duplicate results/rajasthan/... copy alongside the flat file — removed).
OUT_DIR = RESULTS_DIR
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "phase0_climate_signature_check.txt"


class Tee:
    """Write every printed line to stdout AND collect it for the report file."""

    def __init__(self):
        self.lines = []

    def __call__(self, *parts):
        line = " ".join(str(p) for p in parts)
        print(line)
        self.lines.append(line)


def load_regimes():
    with open(STATE_YAML, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg["regimes"]


def check_regime(say, regime, profiles, medoids):
    cid = int(regime["cluster_id"])
    daily_path = BASE_DIR / regime["weather_daily"]
    d = pd.read_csv(daily_path, parse_dates=["date"]).sort_values("date").reset_index(drop=True)

    point_id = str(d["point_id"].iloc[0])
    ghi_mean = d["GHI_daily_kWh"].mean()
    ta_mean = d["Ta_mean_C"].mean()
    summer = d[d["date"].dt.month.isin(SUMMER_MONTHS)]
    ta_summer_max = summer["Ta_max_C"].mean()
    ta_abs_max = d["Ta_max_C"].max()

    n_dup = int(d.duplicated(subset=["point_id", "date"]).sum())
    full_span = pd.date_range(d["date"].min(), d["date"].max(), freq="D")
    n_gap = len(set(full_span) - set(d["date"]))

    prof = profiles.loc[cid] if cid in profiles.index else None
    regime_size_o1 = int(prof["n_points"]) if prof is not None else None
    medoid_o1 = str(medoids.loc[cid, "point_id"]) if cid in medoids.index else None

    ghi_ok = GHI_BAND_KWH[0] <= ghi_mean <= GHI_BAND_KWH[1]
    summer_ok = SUMMER_TMAX_BAND_C[0] <= ta_summer_max <= SUMMER_TMAX_BAND_C[1]
    medoid_ok = (medoid_o1 is None) or (point_id == medoid_o1)
    size_ok = (regime_size_o1 is None) or (int(regime["n_points"]) == regime_size_o1)
    clean = (n_dup == 0 and n_gap == 0)
    ok = ghi_ok and summer_ok and medoid_ok and size_ok and clean

    say("")
    say(f"Rajasthan Cluster {cid} medoid ({point_id}): "
        f"mean GHI {ghi_mean:.2f} kWh/m2/d, mean Ta {ta_mean:.1f} C, "
        f"regime size {regime['n_points']} points")
    say(f"    GHI in {GHI_BAND_KWH} kWh/m2/d .......... {'OK' if ghi_ok else 'FAIL'}")
    say(f"    Apr-Jun mean daily-max Ta {ta_summer_max:.1f} C "
        f"(abs max {ta_abs_max:.1f} C) in {SUMMER_TMAX_BAND_C} ... {'OK' if summer_ok else 'FAIL'}")
    say(f"    medoid id matches Objective 1 ......... {'OK' if medoid_ok else 'FAIL'} "
        f"(O1: {medoid_o1})")
    say(f"    regime size matches cluster_profiles .. {'OK' if size_ok else 'FAIL'} "
        f"(O1: {regime_size_o1})")
    say(f"    duplicate (point_id,date) rows ........ {n_dup}    calendar gaps: {n_gap}   "
        f"[{'OK' if clean else 'FAIL'}]")
    say(f"    date span ............................ {d['date'].min().date()} .. "
        f"{d['date'].max().date()}  ({len(d)} days)")
    say(f"    Tm_target / L_required (O1 ceiling) ... {regime['Tm_target_C']:.1f} C / "
        f"{regime['L_required_kJ_per_kg']:.1f} kJ/kg")
    if prof is not None:
        say(f"    hot-dry corroboration (O1 profile) ... "
            f"CDD24={prof['CDD24']:.0f}  DTR={prof['DTR_true']:.1f} C  "
            f"Ta_p95={prof['Ta_p95']:.1f} C  cloudy_frac={prof['cloudy_frac']:.3f}  "
            f"kt_daily={prof['kt_daily_mean']:.2f}")
    say(f"    --> regime {cid}: {'PASS' if ok else 'STOP -- recheck Objective 1'}")
    return ok


def main():
    say = Tee()
    say("=" * 72)
    say("PHASE 0 -- RAJASTHAN CLIMATE-SIGNATURE SANITY CHECK (Bug-Fix 8)")
    say("=" * 72)
    say(f"state yaml : {STATE_YAML.relative_to(BASE_DIR)}")
    say(f"weather dir: {WEATHER_DIR.relative_to(BASE_DIR)}")

    profiles = pd.read_csv(OBJ1_DIR / f"cluster_profiles_{STATE}.csv").set_index("cluster_id")
    medoids = pd.read_csv(OBJ1_DIR / f"medoid_points_{STATE}.csv").set_index("cluster_id")
    regimes = load_regimes()

    results = [check_regime(say, r, profiles, medoids) for r in regimes]
    all_ok = all(results)

    say("")
    say("=" * 72)
    say(f"OVERALL: {'PASSED -- safe to proceed to Phase 1/2' if all_ok else 'STOP -- recheck Objective 1'}")
    say("Signature is hot-dry / high-clearness "
        "(not Tamil Nadu coastal-humid, not Assam humid-cloudy).")
    say(f"{sum(results)}/{len(results)} regimes passed.")
    say("=" * 72)

    OUT_FILE.write_text("\n".join(say.lines) + "\n", encoding="utf-8")
    say(f"\nSaved: {OUT_FILE.relative_to(BASE_DIR)}")

    raise SystemExit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
