# Tamil Nadu / ANSYS Fluent Redesign Plan (2026-10-26)

**What this document is.** A teammate's audit/redesign plan for the
**Rajasthan** implementation of Objective 2 —
`OBJECTIVE2_REDESIGN_PROPOSED_PLAN.md`, at the project root — was written
against a sibling codebase (`RJ/` in that document's own paths) that uses
**OpenFOAM** as its primary CFD cross-check. This document is the Tamil
Nadu / ANSYS Fluent equivalent: which of that plan's findings and
decisions transfer unchanged (because the Python simulator/DOE/surrogate
code is shared and state-agnostic), which don't apply here, and where this
project substitutes ANSYS Fluent for OpenFOAM as the CFD tool. It does
**not** replace that document — it is the state-specific adaptation the
project's own source plan calls for in its WP7 ("Consolidate
implementation across the four states").

Status tags follow the source document's own convention: **[V]** verified
directly in this project's own code/data, **[L]** from literature already
cited elsewhere in this project, **[P]** a proposed engineering decision,
**[O]** open/unresolved, **[A]** an assumption that should be confirmed.

---

## 1. The headline finding — confirmed and fixed for Tamil Nadu, not just inherited

The source plan's #1 finding was a demand-timing bug: `tank_model.py`
indexed the hot-water demand profile (defined in **local clock hours** —
morning/evening draw peaks) using the **UTC hour** of the weather
timestamp, never converting between them.

This was **not assumed to transfer from Rajasthan** — it was checked
directly against this project's own files **[V]**:
- `data/weather/weather_regime_tamilnadu_cluster*_hourly.csv` really is
  UTC-stamped (`timestamp_utc` column, ISO 8601 with `+00:00` offset,
  NASA POWER convention).
- `data/demand/demand_profile_tamilnadu.csv` really does peak at local
  clock hours 18–20 (evening) and a smaller peak at 8 (morning) — an
  ordinary household usage pattern, not something that would make sense
  applied to UTC hours directly.
- `src/simulation/tank_model.py:158` contained the identical line the
  source plan flagged: `hour_of_day = int(row["timestamp_utc"].hour) ...`
  — the raw UTC hour, never shifted to IST (UTC+5:30).

**Fixed** (2026-10-26): `hour_of_day = (row["timestamp_utc"].hour +
5.5) % 24`. `draw_mass_kg_for_hour()` already rounds a float hour, so no
other code needed to change. Re-ran Phase 4 (still 5/5 gates, released as
`sim_v2_tamilnadu`) and Phases 5–8 against the fix — see `RESULTS.md` for
the corrected numbers, which are **materially different** from everything
reported before today: different winning PCM per regime in some cases,
substantially larger PCM-vs-plain-tank gains, and (expected, once draws
stop coincidentally offloading hot water during peak charging) materially
higher nominal peak temperatures. None of this was hidden or softened —
`RESULTS.md`'s numbers are the corrected ones, with the pre-fix numbers
kept in `history/` for the record.

## 2. Decisions from the source plan's §6/§6A that already hold, or now hold, for Tamil Nadu

These are the source plan's **consolidated, guide-approved decisions**
(its §6/§6A, dated 2026-10-26). Because the simulator/geometry/DOE/
surrogate/optimizer code under `src/` is genuinely shared and
state-agnostic (`--state` only selects config/data paths — confirmed by
reading `pipeline.py` directly), most of these were either already true
for Tamil Nadu or apply identically once stated:

| # | Decision (source plan §6/§6A) | Tamil Nadu status |
|---|---|---|
| 1 | Demand timing bug confirmed real; fix first | **[V] Done** — §1 above |
| 2 | PCM shortlist = Objective 1's MCDM top-3 as written, not re-derived | **[V] Already true** — `configs/states/tamilnadu.yaml` was restored to O1's literal shortlist on 2026-09-18 (`history/18_OBJECTIVE1_SHORTLIST_RESTORED.md`), before this plan even existed |
| 3 | Shape family: spheres, thickness = inner radius; tube capsules dropped | **[V] Already true** — Tamil Nadu's `DesignVector`/`geometry.py` only ever modeled spherical capsules |
| 4 | Model fidelity: 1-D stratified multi-node tank (WP2 Level 2) approved | **[O] Not implemented for Tamil Nadu.** TN's `tank_model.py` is still the single-node (well-mixed) grey-box model. This is the single largest piece of unfinished work this plan inherits — see §6 |
| 6 | Sizing: fixed 50 L / 1.5 m² undersized per IS 12976:2023; disclose, optionally run a labelled non-authoritative sizing-sensitivity study | **[O] Not run for Tamil Nadu.** Worth doing — it's cheap (in-memory override, frozen files untouched) and directly answers "does PCM help more in a correctly-sized tank" |
| 7 | Shared-config unification: safety shield ON by default for all 4 states | **[O] Not implemented.** See §5 — this is a bigger change than it sounds (TN's shield today is only a *specification handed to Objective 3*, not a cutoff simulated inside Objective 2 itself) |
| 8 | Weather split Option A (2016–20 explore / 2021–23 pick / 2024–25 held-out test); one simulation set per Objective-1 cluster/medoid | **[A] Partially true, not confirmed identical.** TN's `configs/states/tamilnadu.yaml` currently simulates one medoid year per regime (`2016 ×3`, per the source plan's own WP7 table) — it has **not** been re-run across the 2016–2025 multi-year split the source plan specifies. This is a real gap, not yet closed |
| 9 | Practical-relevance threshold: paired multi-year gain vs. repeatability band, not a fixed percent; night/morning delivery metrics as primary, annual energy secondary | **[O] Not implemented.** TN's current selection rule (next section) uses the old annual-useful-energy-first criterion, not the new night/morning-delivery-first one |
| — | Tie-breaker order (overheat hours → night delivery → PCM mass → capsule count → safety margin) | **[P] TN has its own, similar-but-not-identical order already implemented** — see §3 |
| — | States in scope: all 4, Rajasthan first | Tamil Nadu is second in that port order; this document is that port |

## 3. Algorithms actually used in Tamil Nadu's Objective 2, vs. the alternatives

**Currently implemented (what actually runs today):**
- **DOE**: random-within-bounds sampling (`src/doe/generate_cases.py`),
  stratified by the 3 capsule arrangements, filtered by Phase 2's real
  geometry/constraint gate before any simulation is spent on an invalid
  design.
- **Surrogate**: `ExtraTreesRegressor` (scikit-learn), one model per
  performance target (`useful_energy_kWh`, `solar_fraction`,
  `unmet_energy_kWh`, `pump_energy_kWh`, `pcm_mass_kg`), plus an
  `ExtraTreesClassifier` for geometric feasibility and a `LinearRegression`
  baseline for comparison (`src/surrogate/train.py`).
- **Search**: `src/optimize/search.py` draws 600 random candidate design
  vectors per regime×PCM pair, scores them with the trained surrogate
  (fast), and keeps the top N (default 20) per pair.
- **Confirmation + selection**: every one of those top-N candidates is
  **re-run in the real simulator** (never trusting the surrogate alone —
  framework rule, Bug-Fix 5), then `src/optimize/select_deployable.py`
  applies a fixed, pre-declared tie-break: reject infeasible → require
  delivery/safety reliability → keep candidates within a 5% tolerance of
  the best useful energy → minimize pump energy, then PCM mass → prefer
  fewer capsules → prefer the larger temperature-constraint margin.

**Why this family, not something else:** this is explicitly a **single
optimization pass over a surrogate** (the project's own framework doc's
reduced spec — `search.py`'s own docstring: *"a single pass, not the full
loop. No active-learning, no NSGA-II."*). It was chosen because it's cheap
(600×12 surrogate evaluations is seconds; only ~240 real-simulator
re-runs, each ~1–4s) and because the design space here is small (4
continuous/categorical variables), so exhaustive-enough random search
finds designs the surrogate is confident about without needing a
genetic/evolutionary search loop.

**Decided future direction, not yet implemented anywhere (source plan
WP5, "Option B", approved by the guide 2026-10-26):** replace the
Extra-Trees + random-search pair above with a **5-member bootstrap-ensemble
feed-forward neural network** (2 hidden layers × 32 units) trained to
predict the same targets, searched with **NSGA-II** (population 100,
100–200 generations, 3 seeds) under an **active-learning** loop that adds
the most-uncertain/most-promising candidates back into the training set
between rounds. **Why this over what's running today**: Extra-Trees gives
no calibrated uncertainty estimate (needed for active learning or for
Pareto-front confidence bands) and random search only ever searches the
space it was told to sample — NSGA-II explicitly explores the Pareto
front between competing objectives (energy vs. pump cost vs. PCM mass vs.
safety margin) rather than ranking by one scalar objective with
after-the-fact tie-breaks.

**Alternatives considered and explicitly NOT chosen** (source plan WP5
comparison table, applies unchanged here since this is a modeling
decision, not a state-specific one):
- **Gaussian-Process Bayesian optimization** — kept only as a
  cross-check/comparison, not the primary method. GP scales poorly past a
  few hundred training points and this project's DOE sets are already
  in the low hundreds; an ensemble NN scales better and gives a similar
  predictive-uncertainty signal GP would.
- **XGBoost / response-surface (RSM) regression** — also kept only as a
  comparison baseline for the surrogate's accuracy, not as the deployed
  model. Gradient-boosted trees and polynomial RSM are both deterministic
  point predictors like Extra-Trees (no native ensemble-disagreement
  uncertainty), so neither solves the problem Extra-Trees already has for
  active learning.
- **Dense-grid search** — kept as a sanity check on NSGA-II's result (do
  they agree on the same region of the design space?), not as the search
  method itself, since a grid fine enough to trust on its own would cost
  far more simulator evaluations than random search + surrogate already
  does cheaply.

**Current status: none of WP5's NSGA-II/NN-ensemble work has been run for
Tamil Nadu (or, per the source plan's own §8 "What I did not do", for
Rajasthan either).** It is a real, approved, but unimplemented next step —
see §6.

## 4. CFD tier — ANSYS Fluent is Tamil Nadu's primary tool, not OpenFOAM

The source plan's WP2-C makes OpenFOAM primary (already built for
Rajasthan) and has ANSYS Fluent repeat a subset as an independent
cross-check. **Tamil Nadu inverts this**, for a concrete, already-done-work
reason: this project built out a complete, working PyFluent automation
pipeline covering **all 3** Tamil Nadu regimes with a genuine
solidification/melting phase-change model, whereas OpenFOAM's standard
solvers (`chtMultiRegionFoam`, conjugate heat transfer) have **no native
phase-change model at all** and were only ever run for Regime 0 as a
sensible-heating-only reference.

| | Tamil Nadu (this project) | Rajasthan (source plan) |
|---|---|---|
| Primary CFD tool | ANSYS Fluent (PyFluent) | OpenFOAM |
| Phase-change physics modeled | Yes — enthalpy-porosity solidification/melting, all 3 regimes | No — OpenFOAM case is conduction-only |
| Regimes covered | 3/3 (Fluent), 1/3 (OpenFOAM, heating-only) | per source plan's own WP7 table |
| Role in the pipeline | Verification/cross-check only — never inside the optimizer loop | Same restriction (source plan §6A item 9) |

This is the same non-negotiable rule the source plan states for its own
CFD tier, and it applies identically here: **neither CFD tool is allowed
to change the four fixed design variables** (capsule diameter, count, flow
rate, arrangement) — it only checks whether the optimizer's already-chosen
design behaves physically sensibly under independent heat-transfer
physics. See `CFD_VERIFICATION.md` for the full methodology, the real
numerical instabilities found and fixed (narrow mushy-zone stiffness,
axisymmetric-mode divergence), and the current results.

**2026-10-26 re-run**: the original Fluent cross-check (done against the
*pre-demand-timing-fix* designs) is now out of date, since §1's fix
changed the deployable design in every regime. New meshes, geometry and
flow rates were built directly from the corrected
`deployable_design_per_regime.csv` and re-run — see `CFD_VERIFICATION.md`
for the updated results.

## 5. Safety shield — now implemented inside the simulator (2026-10-26)

The source plan's §6A item 2 decides the shield should be ON by default
for all 4 states *inside Objective 2's own simulated system* (affecting
Phase 7/8 numbers directly), not only specified for Objective 3 to
implement later. This is now done for Tamil Nadu:
`src/simulation/tank_model.py` forces the collector off (bypass) whenever
water reaches 72°C or PCM reaches 62°C (`configs/system_config_shared.yaml`'s
new `safety.shield_enabled`/`shield_guard_band_C` fields, read by both the
simulator and `build_obj3_contract.py`'s existing `_safety_shield()` spec,
so the two stay in sync rather than describing different behaviors).

**A real subtlety found while implementing this**: stopping the collector
at water's own 72°C guard band was not enough on its own — the tank's much
larger hot-water thermal mass kept conducting heat into the PCM for a
while *after* the collector shut off, carrying PCM from under 62°C to
over 70°C before the tank could cool down (confirmed empirically: an
earlier version of this fix left `n_safety_violations` in the tens of
thousands per year). Since direct encapsulation means the PCM's lower
65°C limit is the real binding constraint whenever PCM is present, the
water-side trip is now tightened to `min(water_trip, pcm_trip)` for PCM
designs specifically — plain-tank baselines keep the looser 72°C trip,
since they have no PCM to protect.

**Result**: P(temperature-safe) is now 100% in every regime (Monte Carlo
confirmed, not just nominal) — but **PCM no longer beats a plain tank
anywhere** (−7.0% to −9.5%, down from the pre-shield +0.25–0.74%), and
P(meets annual demand) collapsed to 0–4% (the shield is a blunt,
instantaneous on/off rule, so it trades away real delivery reliability for
safety). See `RESULTS.md`'s "safety shield now implemented" section and
§6 below for the three-stage comparison and what this means for Objective
3. This is reported as the honest finding it is, not softened: once a PCM
genuinely has to respect its own (lower than water's) temperature limit
under a simple reactive controller, this fixed, undersized (50L/1.5m²)
tank's "PCM beats plain tank" result goes away entirely — Objective 3's
whole task is to recover it with a smarter controller than an instant trip.

## 5c. Tank/collector resized to a standard domestic size (2026-10-27)

The shield (§5) fixed temperature safety completely but, on the original
50 L/1.5 m² tank, cost demand reliability heavily (P(meets annual demand)
down to 0–4%). Diagnosed directly, not guessed: a guard-band sweep (3°C
down to 0.5°C) only moved nominal solar fraction from 36.3% to 37.7% —
and critically, **a plain tank with zero PCM and the same shield also
only reached 37.1%** in the same regime. This proved the bottleneck was
never the PCM or the shield — it was IS 12976:2023 undersizing (source
plan §6A item 3 had already flagged the 33.3 L/m² ratio as below the
40–100 L/m² guidance band), independent of anything PCM-related.

Tested a volume/collector sweep (plain tank, same shield) before choosing
a value: 75 L/2.0 m² ≈ 50.1% nominal, **100 L/2.5 m² ≈ 61–65%**, 150 L/
3.0 m² ≈ 75.6%. **100 L/2.5 m² (40 L/m², the conservative end of the IS
12976 band) was approved by the user and is now the official size for
every regime and, per the shared-config rule, every future state** —
this is not a labelled what-if diagnostic, it replaces the frozen v1.0
tank/collector values (`system_config_shared.yaml`, now
`config_v2.0_2026-10-26`). It is also a genuinely standard commercial
domestic SWH size (100 LPD is the smallest common off-the-shelf capacity
in India), addressing the user's own check that the result stay realistic.

**Result**: all three Phase 8 robustness bars are now met simultaneously
in every regime (P(meets delivery)/P(meets demand)/P(temperature-safe)
all ≥ their thresholds, Monte Carlo confirmed) — see `RESULTS.md`. The
cost: PCM's gap behind a plain tank widened, not narrowed (−12.5% to
−14.8%, vs. −7.0% to −9.5% before the resize), confirmed independently by
Gate 4's own capability check (a synthetic, perfectly-Tm-matched PCM still
loses to plain tank at this tank size). A bigger tank's water thermal mass
buffers temperature swings well enough alone that PCM's marginal
contribution shrinks as the tank grows, in this direct-encapsulation,
reactive-shield design. This is the real, disclosed shape of the result,
not a tuning failure.

## 5b. What this plan does NOT adopt yet for Tamil Nadu (open, flagged honestly)

- **1-D stratified multi-node tank** (source plan WP2 Level 2) — TN's
  tank is still single-node/well-mixed.
- **NN-ensemble + NSGA-II + active learning** ("Option B", §3 above) —
  decided direction, not yet built for either state.
- **Multi-year (2016–2025) weather evaluation** — TN still simulates one
  medoid year per regime.
- ~~IS 12976:2023 sizing-sensitivity diagnostic~~ — superseded by §5c:
  what started as a planned labelled diagnostic became the actual,
  official resize once the plain-tank test showed how large the gap was.

None of these were silently skipped — each is a genuine, bounded scope
decision to finish and verify the demand-timing fix and the ANSYS
cross-check first, rather than changing several things in the same pass
and losing the ability to attribute which change caused which result.

## 6. Recommended next steps, in dependency order

1. ~~Confirm and fix the demand-timing bug~~ **Done (§1).**
2. ~~Re-run Phases 4–8 against the fix~~ **Done — see `RESULTS.md`.**
3. ~~Re-run the ANSYS Fluent cross-check against the corrected (pre-shield)
   designs~~ **Done once** (superseded by item 6 below).
4. ~~Implement the in-simulator safety shield, re-run Phases 4–8~~ **Done
   (§5).**
5. ~~Resize the tank/collector to a realistic, IS-12976-compliant
   domestic size, re-run Phases 4–8~~ **Done (§5c) — all three Phase 8
   robustness bars now met simultaneously in every regime.**
6. ~~Re-run the ANSYS Fluent cross-check against the final (shield +
   resize) geometry~~ **Done 2026-10-27** — see `CFD_VERIFICATION.md`.
   (The earlier "blocked on a license error" was a stray `ansyscl.exe`
   process left over from a prior GUI session holding the license
   checkout; killing it fixed the launch immediately. All 3 regimes
   solved cleanly; 0% melt in the simulated window in all 3 — an honest
   result, not a failure, consistent with Objective 2's own simulator
   still showing real melting at the designs' real timescales.)
7. Multi-year (2016–2025) weather re-evaluation per the source plan's
   Option A split.
8. A smarter (non-instantaneous-trip) shield or discharge policy — the
   current shield is deliberately simple (reactive on/off); even though
   all 3 robustness bars are now met, an anticipatory version could widen
   the margin further and may matter more for other states/regimes whose
   weather is harsher.
9. 1-D stratified tank (WP2 Level 2) and the NN-ensemble + NSGA-II
   surrogate/optimizer (WP5 "Option B") — the two largest pieces of work,
   intentionally last since they are the least bounded.

## 7. Document map (what changed in this reorganization)

- This file is **new**.
- `RESULTS.md`, `HOW_TO_RUN.md`, `CFD_VERIFICATION.md` — updated in place
  with the corrected 2026-10-26 numbers and new ANSYS run instructions.
- `OBJECTIVE2_REDESIGN_PROPOSED_PLAN.md` (project root) — kept as-is,
  unedited (it is a teammate's authored document about a different
  state's codebase); this file is its Tamil Nadu/ANSYS companion, not a
  replacement.
- Nothing was deleted. Historical, phase-by-phase narrative docs remain
  in `docs_objective2/history/` — see `history/README.md`.
