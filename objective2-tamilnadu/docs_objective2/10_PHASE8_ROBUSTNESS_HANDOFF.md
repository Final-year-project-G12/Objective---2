# 10 — Phase 8 Audit: Robustness, Recommendation Cards, Objective 3 Hand-off

> **SUPERSEDED 2026-09-17.** Describes the pre-refresh robustness run and
> `obj3_environment_contract_tamilnadu.json` (`sim_v1`, no arrangement
> field). The current run (`sim_v2_tamilnadu`, arrangement +
> `arrangement_rationale` in every regime's design block, contract
> `supersession_note` field) is documented in
> `docs_objective2/tamilnadu_phase_docs/08_PROMPT_PHASE8_HANDOFF_TAMILNADU.md`.
> **Robustness headline changed**: all 3 current regimes are NOT robust
> (P(temp-safe) 0%/18%/0%) — re-check this doc's specific numbers against
> the current `robustness_summary.csv` before citing anything from here.

Files: `src/robustness/monte_carlo.py`, `src/robustness/weather_ensemble.py`,
`src/handoff/build_recommendation_cards.py`, `src/handoff/build_obj3_contract.py`. Run:
```
python pipeline.py --state tamilnadu --stage robustness
python pipeline.py --state tamilnadu --stage handoff
```
Output: `results/tamilnadu/robustness_results.csv` (600 rows — 120 draws ×
5 designs), `robustness_summary.csv` (5 rows), `recommendation_cards.md`,
`obj3_environment_contract_tamilnadu.json`.

This closes Objective 2 (D2.7, D2.8, D2.9) — every deliverable in the
framework doc's Section 1.2 table now has a file behind it for Tamil
Nadu, evaluated against the **current, corrected** Phase 7 selection: a
genuine PCM design in every regime (`14_SELECTION_RULE_SCOPE_CORRECTION.md`),
using the real-MCDM shortlist and safety-first tie-break
(`15_MCDM_RERANKING_AND_SAFETY_TIEBREAK.md`).

---

## Methodology (unchanged mechanics, now run against 5 PCM designs instead of 4 plain-tank + 1 PCM)

For each of Phase 7's 5 deployable designs — **all five now PCM, not four
plain-tank-plus-one-PCM** — 120 independent scenarios were drawn and
**re-run through the real full-year simulator** (never the surrogate):

| Source | Distribution |
|---|---|
| PCM latent heat | ±10% uniform |
| Weather — GHI/T_amb | annual (GHI scale, T_amb offset) sampled from one of 10 REAL observed years for this cluster (`weather_ensemble.py`, built from Objective 1's 10-year 2016-2025 daily archive) + small smoothing jitter, × per-hour iid noise ~ N(1, 0.04) for GHI and ~N(0, 0.4)°C for T_amb |
| Demand | ±20% volume (uniform), ±30 min timing shift (uniform) |
| Mains/inlet temperature | ±2°C (uniform) |

Reported per design: P(meets delivery temperature) := `solar_fraction ≥
0.45`; P(meets annual demand) := `solar_fraction ≥ 0.50` (both fixed,
state-independent thresholds — a self-referential threshold would let a
weak design look "just as reliable" as a strong one purely by having an
easy bar to clear); useful-energy 5th/50th/95th percentile;
solar-fraction 5th–95th percentile; max-water-temperature 95th
percentile; P(any safety-temperature violation). "Robust" per the
framework's rule of thumb: P(demand) ≥ 75% **and** P(temperature-safe) ≥
95%.

## Historical-year weather ensemble (`src/robustness/weather_ensemble.py`)

Objective 1 already pulled a full 10-year (2016–2025) daily ERA5/POWER
archive (`data/objective1/daily_aggregates_tamilnadu.csv`, 133
population-grid points, all 10 years complete) to build its climate
signature — Phase 8 previously never used it past that step, drawing
instead from an assumed uniform noise range. This module computes each
regime's population-weighted annual-mean GHI/temperature for each real
observed year, expressed as a `(ghi_scale, tamb_offset_C)` pair relative
to that regime's own 10-year mean, and Phase 8's Monte Carlo now samples
one of these 10 real years per draw instead of an assumed distribution.
Real observed variability turned out narrower than the range originally
assumed (~0.97×–1.05× GHI vs. the assumed ±7%), a verifiable improvement
in kind even where the resulting numbers move only modestly.

## Result — all 5 designs are now PCM, regime 4 genuinely safe

| Regime | Design | P(meets delivery) | P(meets demand) | P(temp-safe) | Robust? | Useful energy P5–P50–P95 (kWh) | Max water T P95 |
|---|---|---|---|---|---|---|---|
| 0 | n-Tetracosane (C24) | 100% | 80.8% | **0%** | No | 1592 – 1682 – 1782 | 75.0°C |
| 1 | n-Tetracosane (C24) | 100% | 90.8% | **0%** | No | 1706 – 1826 – 1940 | 78.4°C |
| 2 | n-Hexacosane (C26) | 100% | 94.2% | **0%** | No | 1632 – 1742 – 1844 | 78.1°C |
| 3 | n-Hexacosane (C26) | 100% | 98.3% | **0%** | No | 1710 – 1805 – 1900 | 78.0°C |
| 4 | **RT45HC** | 100% | 76.7% | **30.8%** | No | 1535 – 1620 – 1706 | 74.3°C |

Delivery-temperature reliability is never the problem (100% everywhere).
Demand reliability is generally solid (81–98% in regimes 0–3; 76.7% in
regime 4, the only one below the 75% target). **Temperature safety is
where the real story now sits**: regimes 0–3 are **0% safe across all 120
draws each** — not a rare tail risk, never safe — because their nominal
designs already ran several degrees over the 65°C PCM limit before any
uncertainty was even applied (see `08_PHASE7_OPTIMIZATION.md`'s minimal-
PCM-dose test). Regime 4's design (RT45HC, chosen by the safety-first
tie-break, doc 15) has a real +0.39°C nominal margin — not the previous
selection's razor-thin 0.009°C — and is safe in **30.8%** of draws under
real weather/demand/property variability, the best of the five regimes
and a meaningful improvement over the ~22–25% the earlier, lower-margin
pick achieved, though still well short of the 95% target.

**This is the honest, load-bearing consequence of Objective 2 now
answering its actual problem statement** (optimal PCM design, not
whether to use PCM) — the safety gap moves from being hidden behind a
"pick plain tank instead" fallback to being an explicit, quantified,
per-regime number Objective 3 must close. No result here was tuned to
produce this outcome: the safety-first tie-break (doc 15) only changed
*which already energy-qualified candidate* wins where a safe one exists
in the search results; it did not relax any limit or invent a new
candidate.

## A real bug found and fixed during earlier development (retained, now largely moot)

The first robustness implementation computed `p_exceeds_max_safe_temp` by
checking `max_pcm_temp_C > 65°C` on every design, including (at the time)
plain-tank designs, where `T_pcm = T_w` exactly — wrongly flagging
ordinary hot water as a *PCM* over-temperature. Caught by cross-checking
against `n_safety_violations > 0` (computed inside the simulator itself,
immune to this bug). The fix (gating the PCM check on `has_pcm`) remains
in the code; it no longer changes anything about the reported numbers
now that every design uses PCM, but is kept for correctness in case a
future run ever reintroduces a plain-tank candidate into this pipeline.

## Recommendation cards (D2.8)

One card per regime in `results/tamilnadu/recommendation_cards.md`,
regenerated against the 5 PCM designs — regime/climate context, PCM
shortlist with Objective 1-style rank, selected design, simulator-
confirmed performance, this phase's robustness probabilities, surrogate-
vs-simulator delta (Phase 7), the selection rationale, and an explicit
caveats block.

## Objective 3 environment contract (D2.9)

`results/tamilnadu/obj3_environment_contract_tamilnadu.json` — one static
design block per regime (all five now describing a PCM design, not four
plain-tank + one PCM), plus:
- **`global_limits`** — shared-across-regimes delivery/safety/pressure/
  irradiance/flow envelope summary.
- **`safety_shield`** — trips with a **3°C precautionary guard band**
  below each hard limit (bypass at 72°C water / 62°C PCM, not at the
  75°C/65°C hard limits themselves). Given Phase 8's own P(temp-safe)
  numbers (0–30.8%, all five regimes), this margin is not a formality — it
  is the difference between a controller that anticipates the limit and
  one that reacts to already having crossed it.
- **`reward_function`** — a FULLY SPECIFIED default reward (formula,
  normalized reference magnitudes computed from this state's own 5
  selected designs, default weights `w1..w5` with rationale, precise
  `Penalty_safety_t`/`Penalty_bypass_t` definitions tied to the same
  guard-band trigger as the safety shield, and a tuning procedure).
- **`deferred_future_work`** — four-state comparison, active-learning/
  NSGA-II, sub-daily/hourly multi-year weather records, hardware
  validation. (Widened design bounds, the Tm-target/selection-rule fixes,
  and the MCDM-shortlist/safety-tiebreak fixes are no longer deferred —
  all are now applied; see docs 12–15.)

Also present, unchanged: a 15-field dynamic-state schema with explicit
sensor-measurability flags, both a discrete and a recommended continuous-
flow hybrid action space, 3 PCM-state reset scenarios, and the 6-item
pre-training acceptance-test checklist.

## Exit check

Every one of Tamil Nadu's 5 Level-A regimes has a recommendation card and
appears in the contract file, and every one is now a genuine PCM design.
**This is the Objective 2 "done" line.** Explicitly deferred and named as
future work (not silently dropped): the full four-state comparison, the
active-learning optimization loop, and sub-daily/hourly multi-year
weather records.

## The one caveat that must travel with these results

Objective 2's Tamil Nadu conclusion is **positive on the PCM design
question and load-bearing on safety**: (1) with `Tm_target_C` correctly
matched to this tank's real operating range, design bounds widened to
reach the literature's tested PCM-volume levels, the real MCDM shortlist
adopted, and a safety-first tie-break applied, every regime's optimal PCM
design beats plain water on useful energy (+0.04% to +0.30%) — a genuine
improvement, and the actual Objective 2 deliverable; and (2) **none of
the five is robust to the 95% bar without an active bypass** (0% safe in
four regimes, 30.8% in the fifth — the best-performing regime now has a
real, not razor-thin, nominal margin too). Objective 3 must treat overheat
protection as a first-class, universal control objective for every Tamil
Nadu regime — not a regime-specific edge case — before any of these
designs reaches hardware.

## Literature

- **[Chopra2023]** is the direct methodological precedent for using Monte
  Carlo sampling (rather than one deterministic run) to assess a solar
  water-heating system's real-world feasibility/reliability — the same
  role this phase's 120-draws-per-design Monte Carlo plays.
- **[Mansouri2025]** and **[Ghodusinejad2026]** ground the general
  uncertainty-in-renewable-forecasting framing behind the per-hour
  GHI/ambient-temperature noise model layered on top of the historical
  year draw.
- **[Rubitherm2024]** is again the datasheet source for the 65°C PCM
  limit whose margin (negative in regimes 0–3, now a real positive
  +0.39°C in regime 4 post-doc-15) drives every regime's P(temp-safe)
  result in the table above.
- **[Sivaraj2023]** and **[Emami2026]** (see `OBJECTIVE3_INPUTS_AND_
  NEXT_STEPS.md` for the fuller mapping) ground the reward-function and
  action-space design in `obj3_environment_contract_tamilnadu.json`.
