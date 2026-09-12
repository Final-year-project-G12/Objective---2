# 10 — Phase 8 Audit: Robustness, Recommendation Cards, Objective 3 Hand-off

Files: `src/robustness/monte_carlo.py`, `src/handoff/build_recommendation_cards.py`,
`src/handoff/build_obj3_contract.py`. Run:
```
python pipeline.py --state uttarakhand --stage robustness
python pipeline.py --state uttarakhand --stage handoff
```
Output: `results/uttarakhand/robustness_results.csv` (600 rows — 120 draws ×
5 designs), `robustness_summary.csv` (5 rows), `recommendation_cards.md`,
`obj3_environment_contract_uttarakhand.json`.

This closes Objective 2 (D2.7, D2.8, D2.9) — every deliverable in the
framework doc's Section 1.2 table now has a file behind it for Uttarakhand.

---

## Alignment with Tamil Nadu and Rajasthan implementations (methodology consistency)

The same three methodology choices adopted for Tamil Nadu (aligned to
Rajasthan) are used here for cross-state comparability:

| | Choice used |
|---|---|
| Weather noise | **two-level**: annual GHI scale drawn from one of 10 real observed years for this regime (`weather_ensemble.py`) × independent per-hour noise ~ N(1, 0.04); annual T_amb offset from the same real observed year + per-hour noise ~ N(0, 0.4)°C |
| "Meets demand/delivery" thresholds | **fixed, state-independent**: `solar_fraction ≥ 0.45` (delivery), `solar_fraction ≥ 0.50` (demand) |
| Draws per design | **120** (aligned with Tamil Nadu and Rajasthan for exact comparability) |

**Why the fixed threshold matters especially for Uttarakhand**: Uttarakhand's
nominal solar fractions (28.0–40.7% across the 5 selected designs) are
*all below the fixed 50% demand bar* — and most are below the 45% delivery
bar too. Under a self-referential threshold ("unmet ≤ 150% of nominal"),
every regime would trivially score near 100% reliable. The fixed threshold
reveals the true picture: **P(meets delivery, SF≥45%) is 0.0–23.3% and
P(meets demand, SF≥50%) is 0.0% across all 5 regimes.** This is a genuine
climate consequence, not a code artifact — Uttarakhand's colder mains
temperatures and similar GHI to Tamil Nadu combine to push solar fractions
structurally below 50%.

---

## Real historical-year weather ensemble (audit gap closed — carried forward from Tamil Nadu)

The annual GHI-scale/ambient-offset component of each Monte Carlo draw is
drawn from a real **10-year (2016–2025) daily ERA5/POWER archive**
(`data/objective1/daily_aggregates_uttarakhand.csv`, computed by
`src/robustness/weather_ensemble.py`), rather than an assumed uniform range.
Per-hour jitter within the chosen year is still synthetic (sub-daily
multi-year data was not pulled for this project, stated here, not hidden).

---

## Methodology (D2.7 — reduced 40-hr spec: 120 draws, never fewer than 50)

For each of Phase 7's 5 deployable designs, 120 independent scenarios
were drawn and **re-run through the real full-year simulator** (never the
surrogate):

| Source | Distribution |
|---|---|
| PCM latent heat (PCM regimes only) | ±10% uniform |
| Weather — GHI | annual scale drawn from one of 10 REAL observed years for this regime (`weather_ensemble.py`) × per-hour iid noise ~ N(1, 0.04), clipped [0.5, 1.5] |
| Weather — ambient temperature | annual offset drawn from the same real observed year + per-hour iid noise ~ N(0, 0.4)°C |
| Demand | ±20% volume (uniform), ±30 min timing shift (uniform) |
| Mains/inlet temperature | ±2°C (uniform) |

Reported per design: P(meets delivery temperature) := `solar_fraction ≥
0.45`; P(meets annual demand) := `solar_fraction ≥ 0.50`; useful-energy
5th/50th/95th percentile; solar-fraction 5th–95th percentile; max-water-
temperature 95th percentile; P(any safety-temperature violation). "Robust"
per the framework's rule of thumb: P(demand) ≥ 75% **and** P(temperature-safe) ≥ 95%.

---

## Result — real historical-year weather, fixed absolute thresholds

| Regime | Design | P(meets delivery SF≥45%) | P(meets demand SF≥50%) | P(temp-safe) | Robust? | Useful energy P5–P50–P95 (kWh) | Max water T P95 |
|---|---|---|---|---|---|---|---|
| 0 | Plain tank | 23.3% | 0.0% | 44.2% | No | 1576.5 – 1678.5 – 1755.4 | 79.6°C |
| 1 | Plain tank | 1.7% | 0.0% | 91.7% | No | 1522.6 – 1629.0 – 1727.5 | 76.1°C |
| 2 | PureTemp 58 | 0.0% | 0.0% | **100.0%** | No | 1435.4 – 1514.6 – 1650.1 | 62.1°C |
| 3 | Plain tank | 22.5% | 0.0% | 64.2% | No | 1479.9 – 1557.8 – 1659.1 | 78.9°C |
| 4 | Plain tank | 2.5% | 0.0% | 83.3% | No | 1541.9 – 1630.7 – 1718.5 | 76.6°C |

**The headline finding — demand reliability is universally zero for
Uttarakhand under fixed thresholds.** Every regime's nominal solar fraction
(28.0–40.7%) is structurally below the 50% fixed demand bar, so no draw
from any regime meets P(demand)≥75%. This is not a simulator defect — it
is the physical consequence of Uttarakhand's cold mains temperatures
(7.4–21.8°C), the high L_required (up to 178 kJ/kg), and the 50 L/1.5 m²
frozen hardware sizing. Objective 3 must treat the low solar-fraction
envelope as a fundamental constraint, not a modelling gap to tune away.

**The temperature-safety picture is reversed vs Tamil Nadu.** In Tamil Nadu,
the PCM regime (regime 4) was the *worst* for safety (40.8%). In
Uttarakhand, regime 2's PCM design is the **safest** (0.0% violations,
P(temp-safe)=100%), because the colder climate prevents the tank from
overheating — the PCM absorbs excess heat before it can reach 75°C. Regimes
0 and 3 are the most problematic (55.8% and 35.8% violation probability
respectively), both plain-tank designs in warmer regimes. This is a
climate-specific reversal worth highlighting in a multi-state comparison.

**Regime 0's 55.8% is not purely a robustness finding — it starts from an
already-marginal nominal design.** `deployable_design_per_regime.csv`
shows regime 0's selected plain tank at `constraint_margin_C = -0.137`
(max water 75.14 °C, already 0.14 °C over the 75 °C limit with 1
nominal safety violation) — Phase 7's selection-rule fallback picked it
because *no* candidate tried in that regime cleared the safety filter
(`selection_rule_pool_size=20` = every confirmed candidate, not a
within-tolerance subset; see `08_PHASE7_OPTIMIZATION.md`). So regime 0's
55.8% Monte Carlo violation rate is "a design that's already at the edge
tips over under about half of realistic draws," not "a safe design that
sometimes fails under stress" — worth stating precisely in any paper
section citing this number.

**This strengthens the Phase 7 finding**: regime 2's PCM win is not just
a marginal useful-energy advantage — it is also the most temperature-safe
design in the state, confirming that PureTemp 58 is genuinely beneficial in
this cold, high-demand regime on multiple axes.

---

## Recommendation cards (D2.8)

One card per regime in `results/uttarakhand/recommendation_cards.md`,
aggregating: regime/climate context, PCM shortlist with Objective 1 rank,
selected design, simulator-confirmed performance, robustness probabilities
(fixed-threshold definition), surrogate-vs-simulator delta (Phase 7), the
selection rationale, and an explicit caveats block. Generated by
`python pipeline.py --state uttarakhand --stage handoff`.

---

## Objective 3 environment contract (D2.9)

`results/uttarakhand/obj3_environment_contract_uttarakhand.json` — one
static design block per regime, plus:
- **`global_limits`** — shared-across-regimes summary block (delivery
  target, both temperature limits, pressure limit, irradiance cutoff,
  flow envelope).
- **`safety_shield`** — trips with a **3°C precautionary guard band**
  below each hard limit (bypass at 72°C water / 62°C PCM, not at the
  75°C/65°C hard limits themselves).
- **`reward_function`** — a fully specified default reward (formula,
  normalized reference magnitudes computed from this state's own 5
  selected designs, default weights `w1..w5` with an explicit rationale
  for each, precise `Penalty_safety_t`/`Penalty_bypass_t` definitions
  tied to the same guard-band trigger as the safety shield, and a tuning
  procedure).
- **`deferred_future_work`** — an explicit list (four-state comparison,
  active-learning/NSGA-II, sub-daily/hourly multi-year weather records,
  widened PCM-volume bounds, hardware validation).

Also present: a 15-field dynamic-state schema with explicit
sensor-measurability flags, both a discrete and a recommended
continuous-flow hybrid action space, 3 PCM-state reset scenarios, and the
6-item pre-training acceptance-test checklist.

---

## Exit check

Every one of Uttarakhand's 5 Level-A regimes has a recommendation card and
appears in the contract file. **This is the Objective 2 "done" line for the
~40-hour version.** Explicitly deferred and named as future work: the full
four-state comparison, the active-learning optimization loop, and sub-daily/
hourly multi-year weather records (the annual weather magnitude is a real
10-year ensemble; only the within-year hourly shape remains a
single-medoid-year proxy).

---

## The one caveat that must travel with these results

Objective 2's Uttarakhand conclusion has two components:
(1) Under the frozen shared collector/tank config and the pre-declared
selection rule, none of Objective 1's shortlisted PCMs provide more than
a fraction-of-a-percent nominal benefit over plain water in 4/5 regimes —
the cold-climate regime 2 is the exception where PCM genuinely wins.
(2) **No selected design meets either the demand or temperature-safety
robustness bars** — P(demand SF≥50%)=0.0% everywhere, and P(temp-safe)
ranges 44.2–100.0% (only regime 2's PCM design achieves 100%; all others
fail the 95% target). Objective 3 must treat overheat protection and
demand reliability as first-class control objectives for all Uttarakhand
regimes, and any future recommendation for widening the PCM-volume bounds
must come with a climate-specific revisit of whether the frozen 1.5 m² /
50 L sizing is appropriate for Uttarakhand's colder, more demanding
conditions.
