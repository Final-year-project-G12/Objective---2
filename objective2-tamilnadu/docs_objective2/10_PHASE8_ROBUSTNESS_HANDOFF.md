# 10 — Phase 8 Audit: Robustness, Recommendation Cards, Objective 3 Hand-off

Files: `src/robustness/monte_carlo.py`, `src/handoff/build_recommendation_cards.py`,
`src/handoff/build_obj3_contract.py`. Run:
```
python pipeline.py --state tamilnadu --stage robustness
python pipeline.py --state tamilnadu --stage handoff
```
Output: `results/tamilnadu/robustness_results.csv` (600 rows — 120 draws ×
5 designs), `robustness_summary.csv` (5 rows), `recommendation_cards.md`,
`obj3_environment_contract_tamilnadu.json`.

This closes Objective 2 (D2.7, D2.8, D2.9) — every deliverable in the
framework doc's Section 1.2 table now has a file behind it for Tamil Nadu.

---

## Alignment with the Rajasthan implementation (methodology revision)

The Rajasthan implementation of this same framework
(`O2_Framework_Audit_Report.md`'s companion Phase 8 doc) made three
methodology choices this project's first Phase 8 pass did not match.
Since the whole point of running the same framework per-state is
**cross-state comparability** (`O2_Unified_PerState_Execution_Framework.md`
§0.1), all three were adopted here, replacing the original implementation
rather than living alongside it:

| | First Tamil Nadu version | Now (aligned to Rajasthan) |
|---|---|---|
| Weather noise | single constant GHI multiplier + single constant ambient offset for the whole year | **two-level**: annual GHI scale ~ U(0.93,1.07) × independent per-hour noise ~ N(1,0.04); annual T_amb offset ~ U(−1.5,+1.5)°C + per-hour noise ~ N(0,0.4)°C |
| "Meets demand/delivery" thresholds | relative to each design's *own* nominal value (`delivery_hours >= 50% of nominal`, `unmet_energy <= 150% of nominal`) | **fixed, state-independent**: `solar_fraction >= 0.45` (delivery), `solar_fraction >= 0.50` (demand) |
| Draws per design | 100 | **120** (both are inside the framework's 100–200 band; matched for exact comparability) |

**Why the threshold change matters, concretely**: a self-referential
threshold lets a weak nominal design look "just as reliable" as a strong
one purely by having an easy bar to clear — every regime trivially scored
P(meets demand)=100% under the old definition, which hid real
differences between regimes. Under the fixed threshold, **P(meets
demand) now ranges 70–96% across regimes** (see the result table below) —
a materially more informative and cross-state-comparable metric, and one
that surfaces a result the old definition completely hid: **regime 4's
PCM design now fails the demand bar too, not only the safety bar.**

No results from the first version are still authoritative; every number
below and in `RESULTS.md` reflects the aligned methodology. `run_case`
itself did not need to change — the two-level weather noise is expressed
as per-hour numpy arrays passed through the same `weather_perturbation`
keys (`ghi_multiplier`, `tamb_delta_C`) it already accepted; pandas
broadcasts an array against the hourly weather series exactly like a
scalar.

---

## Second upgrade: a real historical-year weather ensemble (audit gap closed)

An external framework audit flagged that even the aligned methodology
above still drew its *annual* GHI-scale/ambient-offset component from an
**assumed** distribution (`U(0.93,1.07)`, `U(-1.5,+1.5)°C`) rather than
anything actually observed — "Monte Carlo limited to medoid weather +
noise (no historical-year ensemble)." This was a fair criticism: Objective
1 had already pulled a full **10-year (2016–2025) daily ERA5/POWER
archive** (`data/objective1/daily_aggregates_tamilnadu.csv`, 133
population-grid points × 10 complete years, confirmed by direct
inspection) to build its climate signature, and that archive was sitting
unused past `04b_climate_signature.py` — Phase 8 never touched it.

**Fix**: a new module, `src/robustness/weather_ensemble.py`, computes for
each climate regime the population-weighted annual-mean GHI and ambient
temperature for each of the 10 real observed calendar years, expressed as
a `(ghi_scale, tamb_offset_C)` pair relative to that regime's own 10-year
mean. `monte_carlo.py`'s `_sample_scenario()` now draws one of these 10
REAL years per Monte Carlo draw (with a small ±1%/±0.1°C smoothing jitter
so 120 draws are not restricted to exactly 10 discrete values), instead
of sampling from the assumed uniform range. Per-hour jitter within the
chosen year is unchanged (still synthetic — sub-daily multi-year data was
not pulled for this project, and this is stated here, not hidden).

**What actually happened when real data replaced the assumption**: Tamil
Nadu's true observed inter-annual GHI variability turns out to be
*narrower* than the ±7% originally assumed (real range across the 5
regimes' 10 years: roughly 0.97×–1.05×; real T_amb offset range: roughly
−0.8°C to +0.8°C, both computed by `weather_ensemble.py` and saved to
`data/objective1/historical_annual_ensemble_tamilnadu.csv` for inspection)
— so most regimes' temperature-safety probabilities moved up by a few
points and demand probabilities moved by less than 2 points each. **No
regime's qualitative verdict changed.** This is exactly what should happen
if the original assumed range was a reasonable, if unverified, proxy for
the real thing — the upgrade's value is turning "we assumed a plausible
range" into "we used the actual 10 years this region experienced,"
which is the more defensible claim in a methodology section, even though
the numbers moved only slightly.

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
0.45`; P(meets annual demand) := `solar_fraction ≥ 0.50` (both fixed,
matching the Phase 3 doc's own solar_fraction definition — "fraction of
the ideal 300 L/day @ 45°C demand actually delivered at or above the
target"); useful-energy 5th/50th/95th percentile; solar-fraction 5th–95th
percentile; max-water-temperature 95th percentile; P(any
safety-temperature violation). "Robust" per the framework's rule of
thumb: P(demand) ≥ 75% **and** P(temperature-safe) ≥ 95%.

## A real bug found and fixed during the first Phase 8 pass (still relevant — the fix is retained)

The first implementation computed `p_exceeds_max_safe_temp` by checking
`max_pcm_temp_C > 65°C` on **every** design, including the four plain-tank
designs. But `tank_model.py` sets `T_pcm = T_w` exactly when there is no
PCM (there's nothing else for that field to mean) — so this wrongly
flagged ordinary hot water above 65°C (very common; the water safety
limit is 75°C) as a *PCM* over-temperature. Caught by cross-checking
against `n_safety_violations > 0` (computed inside the simulator itself,
immune to this bug) on the raw per-draw data before trusting the
aggregate — the two now agree exactly, as they must by construction.
This fix carried forward unchanged into the aligned methodology above.

## Result — real historical-year weather, fixed absolute thresholds

| Regime | Design | P(meets delivery) | P(meets demand) | P(temp-safe) | Robust? | Useful energy P5–P50–P95 (kWh) | Max water T P95 |
|---|---|---|---|---|---|---|---|
| 0 | Plain tank | 100% | 89.2% | 92.5% | No | 1568 – 1668 – 1763 | 75.1°C |
| 1 | Plain tank | 100% | 90.0% | 80.0% | No | 1700 – 1800 – 1931 | 77.3°C |
| 2 | Plain tank | 100% | 94.2% | 71.7% | No | 1659 – 1744 – 1867 | 77.6°C |
| 3 | Plain tank | 100% | 95.0% | 79.2% | No | 1716 – 1810 – 1920 | 77.1°C |
| 4 | n-Octacosane | 100% | **69.2%** | **40.8%** | No | 1531 – 1616 – 1703 | 73.8°C |

Delivery-temperature reliability is never the problem (100% everywhere,
same as before and same as under the earlier synthetic-noise version).
Demand satisfaction still uses the fixed bar (not a self-referential one),
so **regime 4 (the one regime using PCM) is still revealed as the weakest
performer on both axes at once** — 69.2% demand reliability (below the
75% target) *and* 40.8% temperature safety (worst of all five, below the
95% target by the widest margin). Real observed weather variability is
narrower than the earlier assumed range, which nudged every regime's
temperature-safety number up by a few points (plain-tank range moved from
67–87% to 71.7–92.5%) without changing which regime is worst or which
bars fail.

**This strengthens, not just repeats, the project's central finding**:
across Gate 3 (Phase 4), the full 400-candidate search (Phase 7), the
feature-importance analysis (Phase 6), and now the robustness analysis
(Phase 8) — four independent methods all point at the same PCM regime as
the weakest link in the Tamil Nadu deployment, not merely "marginally
less good."

## Recommendation cards (D2.8)

One card per regime in `results/tamilnadu/recommendation_cards.md`,
aggregating: regime/climate context, PCM shortlist with Objective 1 rank,
selected design, simulator-confirmed performance, this phase's robustness
probabilities (now on the fixed-threshold definition, with P50 and
max-water-P95 reported alongside P5/P95), surrogate-vs-simulator delta
(Phase 7), the selection rationale, and an explicit caveats block.

## Objective 3 environment contract (D2.9)

`results/tamilnadu/obj3_environment_contract_tamilnadu.json` — one static
design block per regime, plus (added to match Rajasthan's contract
structure):
- **`global_limits`** — a shared-across-regimes summary block (delivery
  target, both temperature limits, pressure limit, irradiance cutoff,
  flow envelope) so Objective 3 code that needs "the" envelope rather
  than iterating every regime has one place to read it.
- **`safety_shield`** — now trips with a **3°C precautionary guard band**
  below each hard limit (bypass at 72°C water / 62°C PCM, not at the
  75°C/65°C hard limits themselves), matching Rajasthan's 72°C trigger
  exactly. The original version only tripped exactly at the hard limit —
  a real safety-engineering gap, since by the time a sensor reads exactly
  75.0°C, real lag may already have overshot it. Given Phase 8's own
  P(temp-safe) numbers (40.8-92.5%), this margin is not a formality.
- **`reward_function`** — a FULLY SPECIFIED default reward (formula,
  normalized reference magnitudes computed from this state's own 5
  selected designs, default weights `w1..w5` with an explicit rationale
  for each, precise `Penalty_safety_t`/`Penalty_bypass_t` definitions tied
  to the same guard-band trigger as the safety shield above, and a tuning
  procedure) -- replacing the original version's `"weights": "NOT YET
  CHOSEN"` placeholder, which an external audit correctly flagged as
  blocking Objective 3 from starting training immediately. See
  `src/handoff/build_obj3_contract.py`'s `_reward_function_spec()`.
- **`deferred_future_work`** — an explicit list (four-state comparison,
  active-learning/NSGA-II, sub-daily/hourly multi-year weather records --
  the annual magnitude is now real (see above), but within-year hourly
  shape is still a single medoid year -- widened PCM-volume bounds,
  hardware validation), matching Rajasthan's equivalent block in spirit.

Also present, unchanged from the first version: a 15-field dynamic-state
schema with explicit sensor-measurability flags, both a discrete and a
recommended continuous-flow hybrid action space, 3 PCM-state reset
scenarios, and the 6-item pre-training acceptance-test checklist.

## Exit check

Every one of Tamil Nadu's 5 Level-A regimes has a recommendation card and
appears in the contract file. **This is the Objective 2 "done" line for
the ~40-hour version.** Explicitly deferred and named as future work (not
silently dropped, and now enumerated in the contract's own
`deferred_future_work` field): the full four-state comparison, the
active-learning optimization loop, and sub-daily/hourly multi-year weather
records (the annual weather magnitude is now a real 10-year ensemble, see
above; only the within-year hourly shape remains a single-medoid-year
proxy).

## The one caveat that must travel with these results

Objective 2's Tamil Nadu conclusion is **negative and load-bearing, with
two independent components**: (1) under the frozen shared collector/tank
config and the pre-declared selection rule, no Objective 1 shortlisted
PCM provides more than a fraction-of-a-percent nominal benefit over plain
water, so the plain tank is selected in 4/5 regimes; and (2) **no
selected design — PCM or plain tank — is robustly safe** without an
active bypass (71.7–92.5% temperature-safe for plain tank, 40.8% for the
one PCM design, all below the 95% target). Objective 3 must treat overheat
protection as a first-class control objective for every Tamil Nadu
regime, not only the PCM one, and any future PCM recommendation needs
either widened design bounds **plus** a bypass shield, or a
climate-specific revisit of the frozen 1.5 m² / 50 L sizing — the same
conclusion Rajasthan's audit reached independently, which is itself
evidence this is a climate-general finding, not a one-state artifact.
