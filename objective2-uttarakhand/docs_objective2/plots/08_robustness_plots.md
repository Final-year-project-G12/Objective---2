# Phase 8 Plots — Robustness & Objective 3 Hand-off

Files: `phase8_robustness_probabilities.*`, `phase8_useful_energy_intervals.*`.
Data source: `results/uttarakhand/robustness_summary.csv` (5 rows, each aggregating
120 full-year Monte Carlo simulator re-runs under a 10-year historical weather ensemble)
and `deployable_design_per_regime.csv` for nominal unperturbed benchmarks.

**This is the final version of this doc (2026-09-14)**, run against the
Tm-retargeted, bounds-widened, scope-corrected (PCM-only) Phase 7 designs.

---

## Plot 1 — Robustness probabilities per regime

**What it is**: Three compliance probabilities per regime evaluated across 120
independent annual simulations:
1. **Purple bars**: $P(\text{meets delivery temperature, SF} \ge 0.45)$
2. **Blue bars**: $P(\text{meets annual demand, SF} \ge 0.50)$
3. **Green bars**: $P(\text{temperature safe}) = 1 - P(\text{overheat violation})$

With reference lines at $75\%$ (demand threshold) and $95\%$ (temperature safety threshold).

**What we infer**:
- **Blue bars are invisible everywhere — $P(\text{meets demand}) = 0.0\%$ in
  all 5 regimes.** Uttarakhand's cold mains water (7.45–21.82°C) combined
  with a high thermal draw (300 L/day at 60°C) in an unassisted 50 L tank
  caps nominal solar fractions at 28.1–40.9% — 10–22 points below the
  fixed, cross-state 50% bar. This is a genuine climate finding: Tamil
  Nadu's and Rajasthan's much warmer mains water (~24–26°C) lets their
  designs clear this same bar nominally, so their own Phase 8 plots show
  70–100% demand-reliability bars — Uttarakhand's plot is not supposed to
  look like theirs.
- **Purple bars are also low everywhere** (0.0–29.2%) — regime 3 (warmest
  mains) reaches the highest delivery-reliability at 29.2%.
- **Green bars now split sharply into "essentially zero" or "essentially
  certain," directly reflecting each design's nominal safety margin
  sign**: regimes 0, 2 and 3 (nominal margin ≤ −5°C) are **0.0%**
  temperature-safe — every single one of 120 Monte Carlo draws breaches
  the limit, because the nominal design is already several degrees over
  before any uncertainty is even added. Regime 4 (nominal margin −4.2°C,
  the smallest deficit among the unsafe regimes) manages **7.5%** — a
  handful of favorable draws squeak under the limit. **Regime 1** is the
  sole green bar at **100.0%** — not because its design is well-engineered
  for safety, but because its PCM (Myristic acid (C14)) is too
  climate-mismatched to its own ~28°C operating range to ever activate
  enough to threaten the limit (see `12_TM_TARGET_RETARGETING.md`).

**How to justify it**: *"Using fixed, state-independent thresholds and a real
10-year historical weather ensemble reveals two things at once: Uttarakhand's
climate structurally cannot meet a 50% demand bar with this hardware sizing
(genuinely different from Tamil Nadu's and Rajasthan's warmer-climate results,
not a modelling error), and — more urgently — the scope-corrected optimizer's
energy-optimal PCM choice is temperature-unsafe at nominal conditions in 4 of
5 regimes, with Monte Carlo confirming this is not a rare edge case but the
near-certain outcome. Objective 3's active bypass/discharge control is not
optional for regimes 0, 2, 3 and 4."*

---

## Plot 2 — Useful-energy 5th–50th–95th percentile intervals per regime

**What it is**: Horizontal uncertainty bars spanning the 5th percentile ($P_{05}$)
to the 95th percentile ($P_{95}$) of annual useful energy across 120 historical
weather draws per regime, with a circle marking the distribution median ($P_{50}$)
and a black diamond indicating the single nominal unperturbed design point from Phase 7.

**What we infer**:
- **Regime 0** (RT42): $[1472.5, 1624.0]\text{ kWh}$, Median $= 1542.1\text{ kWh}$, Nominal $= 1539.0\text{ kWh}$
- **Regime 1** (Myristic acid (C14)): $[1417.6, 1654.4]\text{ kWh}$, Median $= 1531.9\text{ kWh}$, Nominal $= 1525.9\text{ kWh}$
- **Regime 2** (RT42): $[1514.0, 1716.7]\text{ kWh}$, Median $= 1617.9\text{ kWh}$, Nominal $= 1626.4\text{ kWh}$
- **Regime 3** (RT42): $[1470.9, 1645.0]\text{ kWh}$, Median $= 1548.2\text{ kWh}$, Nominal $= 1565.5\text{ kWh}$
- **Regime 4** (savE® OM42): $[1538.7, 1704.2]\text{ kWh}$, Median $= 1630.8\text{ kWh}$, Nominal $= 1625.9\text{ kWh}$

- In every regime, the nominal diamond sits comfortably within the interval, closely
  aligned with the distribution median.
- This demonstrates that Phase 7's single-year optimization did not select an
  unstable or fortunate outlier; rather, the nominal selections accurately reflect
  expected multi-year operational performance — the useful-energy picture is
  robust even though the temperature-safety picture, above, is not.

**How to justify it**: *"The 120-draw historical weather ensemble confirms that
our deployable design benchmarks are energy-robust and centered within their
multi-year probability distributions — the fragility this project reports is
specifically a temperature-safety one, not an energy-delivery one."*
