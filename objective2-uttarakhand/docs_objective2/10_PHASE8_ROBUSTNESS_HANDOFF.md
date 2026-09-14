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

**This is the final version of this doc (2026-09-14)**, run against the
Tm-retargeted, bounds-widened, scope-corrected (PCM-only) Phase 7 designs.

---

## Alignment with Tamil Nadu and Rajasthan implementations (methodology consistency)

The same methodology choices used for Tamil Nadu and Rajasthan are used
here for cross-state comparability:

| | Choice used |
|---|---|
| Weather noise | **two-level**: annual GHI scale drawn from one of 10 real observed years for this regime (`weather_ensemble.py`) × independent per-hour noise ~ N(1, 0.04); annual T_amb offset from the same real observed year + per-hour noise ~ N(0, 0.4)°C |
| "Meets demand/delivery" thresholds | **fixed, state-independent**: `solar_fraction ≥ 0.45` (delivery), `solar_fraction ≥ 0.50` (demand) |
| Draws per design | **120** (aligned with Tamil Nadu and Rajasthan for exact comparability) |

**Why the fixed threshold matters, and why Uttarakhand's plot will not
resemble Tamil Nadu's or Rajasthan's.** Both of those states' mains water
is ~24–26°C; Uttarakhand's is 7.45–21.82°C. Heating the same 300 L/day
draw to the same 50°C delivery target from a colder start costs
substantially more energy for the identical 50 L / 1.5 m² system, so the
fixed 50%-solar-fraction bar is **not equally hard to clear across
states** — it doesn't need to be, since it's testing whether *this*
system, *as sized*, can deliver *this* draw at *this* climate:

| | Mains temp | Nominal solar fraction | vs. 50% bar |
|---|---|---|---|
| Tamil Nadu | ~24–26°C | 51.4–54.8% | above |
| Rajasthan | ~24.5–25.8°C | (similarly warm climate) | above |
| **Uttarakhand** | **7.45–21.82°C** | **28.1–40.9%** | **10–22 points below** |

Tamil Nadu's and Rajasthan's designs mostly already clear 50% nominally,
so most Monte Carlo draws also clear it — hence their own Phase 8 plots
show 70–100% demand-reliability bars. Uttarakhand's designs never get
close, so under the *identical* Monte Carlo methodology, essentially no
favorable draw pushes any regime over 50% either. **This is the correct,
expected result of running the same fixed-threshold framework against a
genuinely colder climate — it is not a sign that anything is broken, and
it should not be forced to look like the warmer states' plots.**

---

## Real historical-year weather ensemble

The annual GHI-scale/ambient-offset component of each Monte Carlo draw is
drawn from a real **10-year (2016–2025) daily ERA5/POWER archive**
(`data/objective1/daily_aggregates_uttarakhand.csv`, via
`src/robustness/weather_ensemble.py`), rather than an assumed uniform
range. Per-hour jitter within the chosen year is still synthetic
(sub-daily multi-year data was not pulled for this project).

---

## Methodology (D2.7 — 120 draws)

For each of Phase 7's 5 deployable (PCM-only) designs, 120 independent
scenarios were drawn and **re-run through the real full-year simulator**:

| Source | Distribution |
|---|---|
| PCM latent heat | ±10% uniform |
| Weather — GHI | annual scale drawn from one of 10 REAL observed years for this regime × per-hour iid noise ~ N(1, 0.04), clipped [0.5, 1.5] |
| Weather — ambient temperature | annual offset drawn from the same real observed year + per-hour iid noise ~ N(0, 0.4)°C |
| Demand | ±20% volume (uniform), ±30 min timing shift (uniform) |
| Mains/inlet temperature | ±2°C (uniform) |

Reported per design: P(meets delivery temperature) := `solar_fraction ≥
0.45`; P(meets annual demand) := `solar_fraction ≥ 0.50`; useful-energy
5th/50th/95th percentile; solar-fraction 5th–95th percentile; max-water-
temperature 95th percentile; P(any safety-temperature violation). "Robust"
per the framework's rule of thumb: P(demand) ≥ 75% **and** P(temperature-safe) ≥ 95%.

---

## Result

| Regime | Design | P(meets delivery SF≥45%) | P(meets demand SF≥50%) | P(temp-safe) | Robust? | Useful energy P5–P50–P95 (kWh) | Max water T P95 |
|---|---|---|---|---|---|---|---|
| 0 | RT42 | 8.3% | 0.0% | **0.0%** | No | 1472.5 – 1542.1 – 1624.0 | 78.3°C |
| 1 | Myristic acid (C14) | 0.0% | 0.0% | **100.0%** | No | 1417.6 – 1531.9 – 1654.4 | 61.5°C |
| 2 | RT42 | 3.3% | 0.0% | **0.0%** | No | 1514.0 – 1617.9 – 1716.7 | 76.0°C |
| 3 | RT42 | 29.2% | 0.0% | **0.0%** | No | 1470.9 – 1548.2 – 1645.0 | 79.8°C |
| 4 | savE® OM42 | 0.8% | 0.0% | **7.5%** | No | 1538.7 – 1630.8 – 1704.2 | 72.5°C |

**Finding 1 — demand reliability is universally zero.** Every regime's
nominal solar fraction (28.1–40.9%) is structurally below the 50% fixed
demand bar (see the cross-state comparison above) — genuinely a climate
consequence of Uttarakhand's cold mains water, not a modelling gap.

**Finding 2 — temperature safety collapses to near-zero in 3 of 5 regimes
under Monte Carlo uncertainty, exactly matching the nominal-margin sign.**
Regimes 0, 2 and 3 (all nominal margin ≤ −5°C) go to **0.0%** temp-safe —
every single one of 120 draws breaches the safety limit; there is no
uncertainty band wide enough to matter when the nominal design is already
6–8°C over the limit. Regime 4 (nominal margin −4.2°C, the smallest
deficit among the unsafe regimes) manages 7.5% — a handful of favorable
draws (cooler year, lower demand) squeak under the limit. **Regime 1** —
the one region whose selected PCM is *coincidentally* too mismatched to
its own climate to activate meaningfully (doc 12) — is the only design
that is robust to temperature safety (100.0%, zero violations across 120
draws).

**This is a stronger and more actionable finding than the pre-retargeting
robustness picture.** Previously, safety and PCM choice looked decoupled
in a way that reinforced the framing "the optimizer's PCM choice doesn't
matter much either way." Now, with plain tank excluded and safety no
longer gating selection, the finding is unambiguous: **4 of 5 Uttarakhand
regimes' Objective-2-optimal PCM hardware design will overheat under
essentially all realistic operating conditions without an active
bypass/discharge controller** — this is now the single most
consequential number Objective 3 needs from this project.

---

## Recommendation cards (D2.8)

One card per regime in `results/uttarakhand/recommendation_cards.md`,
aggregating: regime/climate context, PCM shortlist with Objective 1 rank
(or the retargeting outcome), selected design, simulator-confirmed
performance, robustness probabilities, surrogate-vs-simulator delta, the
selection rationale, and an explicit caveats block. Generated by
`python pipeline.py --state uttarakhand --stage handoff`.

---

## Objective 3 environment contract (D2.9)

`results/uttarakhand/obj3_environment_contract_uttarakhand.json` — one
static design block per regime (all 5 now have real PCM capsule geometry,
none are plain-tank), plus `global_limits`, a `safety_shield` block
(3°C precautionary guard band: bypass at 72°C water / 62°C PCM), a fully
specified default `reward_function`, `deferred_future_work`, a 15-field
dynamic-state schema, both action-space options, 3 PCM-state reset
scenarios, and the 6-item pre-training acceptance-test checklist.

---

## Exit check

Every one of Uttarakhand's 5 Level-A regimes has a recommendation card,
a PCM-based design (never plain tank), and appears in the contract file.
This is the Objective 2 "done" line for the ~40-hour version, now
incorporating the same methodology revisions (Tm-retargeting,
bounds-widening, scope correction) that Tamil Nadu applied.

---

## The one caveat that must travel with these results

Objective 2's Uttarakhand conclusion now has three components:
(1) After retargeting the PCM melting point to this tank's real operating
range, every regime's selected PCM design genuinely (if narrowly) beats
plain water on useful energy — a real, if small, physical benefit that
did not exist before retargeting.
(2) **4 of 5 regimes' selected PCM designs exceed the 65°C PCM
temperature limit at nominal conditions, and Monte Carlo confirms this is
essentially certain (0.0–7.5% temperature-safe) under realistic
uncertainty** — only regime 1, whose PCM is too mismatched to its own
climate to activate, stays safe (100.0%). Objective 3 must implement
active overheat protection for regimes 0, 2, 3 and 4 as a precondition
for deployment, not an optional refinement.
(3) **No design meets the demand-reliability bar** — P(demand SF≥50%)=0.0%
everywhere — a genuine, expected consequence of Uttarakhand's cold mains
water under the frozen 50 L / 1.5 m² sizing, not comparable to Tamil
Nadu's or Rajasthan's much warmer-climate results and not evidence of a
pipeline defect.
