# Objective 2 — Current Results (Tamil Nadu)

Consolidated, current-state results. For the detailed phase-by-phase
history of how this state was reached (including corrections made along
the way), see `history/`. This doc supersedes scattered results in
`history/00_MASTER_OVERVIEW.md` and `history/18_OBJECTIVE1_SHORTLIST_RESTORED.md`
as the single current reference — those still hold the full narrative if
you want it.

## 2026-10-27: tank/collector resized — all 3 robustness bars now met (read this first)

With the safety shield in place (below), every regime was genuinely
temperature-safe but P(meets annual demand) had collapsed to 0–4% — the
50 L / 1.5 m² tank/collector pairing (33.3 L/m²) sits below IS
12976:2023's 40–100 L/m² guidance and, confirmed directly, **couldn't
nominally reach 50% solar fraction even with zero PCM and no shield at
all** (a plain 50 L tank: 37.1% nominal). Shield-tuning alone (swept the
guard band from 3°C down to 0.5°C, effectively no margin) only moved this
to 37.7% — the bottleneck was never the PCM or the shield, it was the
tank being too small for a 300 L/day demand.

**Resized to 100 L / 2.5 m² (40 L/m², the conservative end of the IS
12976 band) — approved by the user 2026-10-26, now the official size for
every regime/state** (`configs/system_config_shared.yaml`, version
`config_v2.0_2026-10-26`). This is a genuinely standard domestic solar
water heater size (100 LPD is the smallest common off-the-shelf capacity
sold in India, typically paired with ~2–2.5 m² of collector), not an
invented or oversized value. A volume/area sweep was run before picking
it: 75 L/2.0 m² ≈ 50% nominal, 100 L/2.5 m² ≈ 61–65%, 150 L/3.0 m² ≈ 76%.
Phases 4–8 were re-run against the new size (Phase 2's capsule/packing
geometry is tank-size-agnostic and didn't need re-running).

**Result: every regime now meets all three Phase 8 robustness bars at
once** (`robust_per_framework_rule = True` in all 3) — P(meets delivery)
= 100% in every regime, P(meets annual demand) = 100%/94.2%/100%, and
**P(temperature-safe) stays at 100%** (the shield still works exactly as
before; a bigger tank didn't compromise safety). See "Robustness" below
for the full table.

## 2026-10-26: safety shield implemented

After the demand-timing fix below, Phase 8 showed **0% temperature-safe in
every regime** under a passive tank with no active control. The safety
shield — previously only a specification handed to Objective 3
(`build_obj3_contract.py`'s `_safety_shield()`) — is now **actually
enforced inside Objective 2's own simulator** (`src/simulation/
tank_model.py`): the collector is forced off (bypass) whenever water
reaches 72°C or PCM reaches 62°C (a 3°C guard band below the 75°C/65°C
hard limits), and for PCM designs the water-side trip is tightened to the
PCM's own 62°C threshold too — stopping the collector at 72°C alone still
let the tank's much larger hot-water mass keep conducting into the PCM
afterward and push it past 65°C anyway (confirmed empirically before this
tightening). Toggle: `configs/system_config_shared.yaml`'s
`safety.shield_enabled` (default `true`).

This alone got P(temperature-safe) to 100% but, on the original 50 L
tank, cost P(meets annual demand) heavily (down to 0–4%) — see the
resizing section above for how that was then resolved.

## What changed on 2026-10-26, first update (demand-timing fix)

A real bug was found and fixed in `src/simulation/tank_model.py`: the
household hot-water demand profile is defined in **local clock hours**
(peak draws in the evening, 18:00–20:00, plus a smaller morning peak), but
the code was indexing it with the **raw UTC hour** of the weather
timestamp instead of converting to local (IST, UTC+5:30) time first. Since
every hour of simulated draws landed ~5.5 hours away from where it should,
every number in every phase from Phase 3 onward was affected. This was
**independently confirmed for Tamil Nadu**, not assumed from elsewhere:
our weather files really are UTC-stamped, our demand profile really does
peak at local evening hours, and the identical buggy line was found and
fixed in our own `tank_model.py:158`. See `TAMILNADU_REDESIGN_PLAN.md` §1
for the full account.

## Phase status

| Phase | Deliverable | Status |
|---|---|---|
| 1 | Frozen state config (`configs/states/tamilnadu.yaml`), 3 climate regimes, Objective 1's own `Tm_target_C`/PCM shortlist (unedited) | Done |
| 2 | Geometry & constraint engine, arrangement-branched (3 packing models) | Done |
| 3 | Grey-box enthalpy simulator, arrangement pass-through, safety shield | Done |
| 4 | Simulator verification, Gates 1–5 — **re-run 2026-10-27 after the tank resize** | Done — **GO** (rule: residual<0.5% AND ≥3/5 gates clean), `sim_v2_tamilnadu`. 4/5 clean: Gate 3 (capability check: a matched-Tm synthetic PCM still doesn't beat plain tank in this direct-encapsulation design) FAILs honestly, same as it has at other points in this project's history — Gates 1/2/4/5 clean, Gate 4 now a clean PASS (67.5% solar fraction, inside the 54–84% cited band) |
| 5 | DOE, arrangement-stratified — re-run: 219 cases, 108 valid | Done |
| 6 | Surrogate, arrangement one-hot feature — re-trained on resized-tank data | Done |
| 7 | Optimization spans arrangement, simulator-confirmed — re-run | Done |
| 8 | Robustness, recommendation cards, Objective 3 contract — re-run, **all 3 regimes robust** | Done |
| CFD | ANSYS Fluent — re-run 2026-10-27 against the final (shield+resize) geometry, all 3 regimes, correct per-regime PCM. OpenFOAM: 1/3 regimes, pre-fix, heating-only, not re-run | Done (see `CFD_VERIFICATION.md`) |

## Algorithms used — what actually runs vs. what doesn't, and why

Full comparison table with code pointers: `TAMILNADU_REDESIGN_PLAN.md` §3.
Summary:

| Stage | Algorithm actually running | Alternatives considered, not used |
|---|---|---|
| DOE (Phase 5) | Random-within-bounds sampling, stratified by the 3 capsule arrangements, filtered by Phase 2's geometry/constraint gate before any simulation is spent (`src/doe/generate_cases.py`) | Full factorial / dense grid (kept only as a sanity cross-check, not the method — too expensive for 4 design variables) |
| Surrogate (Phase 6) | `ExtraTreesRegressor` per output (`useful_energy_kWh`, `solar_fraction`, `unmet_energy_kWh`, `pump_energy_kWh`, `pcm_mass_kg`) + `ExtraTreesClassifier` for geometric feasibility, `LinearRegression` kept as a baseline (`src/surrogate/train.py`) | XGBoost / response-surface regression (kept as accuracy baselines only); 5-member bootstrap-ensemble neural network (approved future direction, not yet built — no calibrated uncertainty needed for an active-learning loop that doesn't exist yet) |
| Search (Phase 7) | 600 random candidate design vectors per regime×PCM pair scored by the trained surrogate, keep top-20 (`src/optimize/search.py`) — **explicitly a single surrogate-scoring pass, not an optimization loop** (script's own docstring: *"no active-learning, no NSGA-II"*) | NSGA-II multi-objective genetic search (approved future direction, WP5 Option B — population 100, 100–200 generations); Gaussian-Process Bayesian optimization (kept as a comparison check, scales poorly past the low-hundreds DOE sizes this project uses) |
| Confirmation + selection | Every top-20 surrogate candidate is **re-run in the real grey-box simulator** (never trusting the surrogate alone), then a fixed, pre-declared tie-break rule picks the deployable design: reject infeasible → require delivery/safety reliability → within 5% of best useful energy → minimize pump energy → minimize PCM mass → fewer capsules → larger temperature margin (`src/optimize/select_deployable.py`) | — |
| Simulator (Phase 3/4) | Grey-box enthalpy tank model, backward-Euler lagged-PCM timestepping with adaptive sub-stepping near the melt band, hard temperature-trip safety shield (`src/simulation/tank_model.py`) | Full CFD for every DOE case (too slow for hundreds of candidates — CFD is instead used as an independent cross-check on the final selected designs only, see CFD section below) |
| Robustness (Phase 8) | Monte Carlo, 120 draws/design over weather-year and demand-profile uncertainty, reports P(meets delivery), P(meets annual demand), P(temperature-safe) (`src/robustness/`) | — |
| PCM shortlist (Phase 1) | Inherited unedited from Objective 1's own MCDM consensus ranking (TOPSIS + GRA + PROMETHEE + VIKOR, combined by Borda count — `src/design/mcdm_reranking.py`) | Objective 2 does not re-rank PCMs independently; it re-simulates/re-optimizes designs for the PCMs Objective 1 already shortlisted |

**None of Objective 2's own optimization (DOE/surrogate/search) was
re-architected by the three 2026-10-26/27 fixes (demand-timing bug,
safety shield, tank resize)** — those changed the *simulator* and the
*frozen config* the same algorithms run against, not the algorithms
themselves. The deployable designs below are a fresh *output* of the
unchanged pipeline run against the corrected inputs.

## Deployable design per regime (FINAL — bug-fixed + shield + 100L/2.5m² resize, 2026-10-27)

| Regime | PCM | Arrangement | Diameter | Capsules | Flow rate | Useful energy | Solar fraction | vs. plain tank | Max water / PCM temp (nominal) | Constraint margin |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | n-Hexacosane (C26) | radial | 72.216 mm | 32 | 0.02066 kg/s | 1668.65 kWh | 65.23% | −14.78% | 62.42°C / 62.30°C | +2.70°C |
| 1 | n-Hexacosane (C26) | radial | 75.306 mm | 33 | 0.01085 kg/s | 1763.44 kWh | 57.77% | −13.02% | 62.23°C / 61.94°C | +3.06°C |
| 2 | n-Pentacosane (C25) | single-layer | 79.764 mm | 35 | 0.02371 kg/s | 1679.40 kWh | 64.66% | −12.46% | 62.51°C / 62.29°C | +2.71°C |

**Every design meets the temperature-safety constraint with a genuine
positive margin** (not just under the shield's nominal operation — see
Robustness below, this holds under Monte Carlo uncertainty too).
Arrangement: radial wins outright in Regimes 0/1; Regime 2's single-layer
and radial are within the surrogate-vs-sim noise band (tied).

**PCM still loses to a plain tank in every regime** (−12.5% to −14.8% —
*wider* than the pre-resize shielded gap of −7.0% to −9.5%). This is a
real, disclosed finding, not softened: Gate 3's own capability check shows
the same thing directly — even a synthetic PCM with its melting point
matched to this tank's exact operating range still underperforms a plain
tank once the tank is this size. A bigger tank's much larger water
thermal mass buffers temperature swings on its own, so PCM's own
thermal-buffering contribution becomes proportionally smaller, not larger,
as the tank grows. This doesn't mean PCM "doesn't work" — it means this
specific combination (direct-encapsulation PCM, a simple reactive
all-or-nothing safety shield, and a plain tank large enough to meet the
demand on its own) doesn't need PCM's help to hit the demand/safety bars.
PCM's real case is for a tank that's water-side-constrained but
PCM-feasible — see `TAMILNADU_REDESIGN_PLAN.md` §5 for what this implies.

## Robustness (Phase 8, 120 Monte Carlo draws/design, re-run 2026-10-27 with the resized tank)

| Regime | PCM | P(meets delivery) | P(meets demand) | P(temperature-safe) | Max water temp (95th pct) | Robust? |
|---|---|---|---|---|---|---|
| 0 | n-Hexacosane (C26) | **1.00** | **1.00** | **1.00** | 62.5°C | **Yes** |
| 1 | n-Hexacosane (C26) | **1.00** | **0.942** | **1.00** | 62.3°C | **Yes** |
| 2 | n-Pentacosane (C25) | **1.00** | **1.00** | **1.00** | 62.6°C | **Yes** |

**All three robustness bars are met in every regime** (`robust_per_
framework_rule = True`) — P(meets demand) ≥ 75%, P(temperature-safe) ≥
95%, confirmed under the full Monte Carlo weather/demand/property
uncertainty sweep, not just nominally. This is the direct, verified answer
to "I want all 3 categories to cross the threshold": they do, in every
regime, simultaneously.

**How this was reached, in order** (each step's real cost/benefit, not
hidden): (1) fixed a demand-timing bug that had been silently making the
system look safer than it was; (2) added an actual safety shield to the
simulator, which achieved 100% temperature safety but collapsed demand
reliability to 0–4% on the original 50 L tank; (3) resized the tank/
collector to a standard 100 L/2.5 m² domestic pairing, which recovered
demand reliability without giving up any of the shield's safety margin.
Each step was individually verified (re-run through Phases 4–8, not
assumed) before moving to the next.

## CFD cross-verification (ANSYS Fluent) — re-run against the final geometry, 2026-10-27

Independent physics sanity check — not a re-optimization, doesn't change
any number above. Full methodology, every real pitfall found and fixed,
and scope limitations: `CFD_VERIFICATION.md`.

**Current.** The earlier "blocked by a license error" was a stray
`ansyscl.exe` process left over from a prior GUI session holding the
license checkout — killing it fixed the launch immediately; it was not a
real license expiry or a code issue. Fluent was then re-run against the
**final** (shield + 100L/2.5m² resize) geometry for all 3 regimes, using
the real per-regime PCM, capsule diameter, capsule count, and flow rate
from the table above:

| Regime | PCM (Tm) | Simulated duration | Capsule temp range | Liquid fraction melted |
|---|---|---|---|---|
| 0 | C26 (56.5°C) | 2140 s | 25.18–50.85°C | 0% |
| 1 | C26 (56.5°C) | 4530 s | 26.38–51.56°C | 0% |
| 2 | C25 (54.0°C) | 2700 s | 25.18–50.25°C | 0% |

0% melt in all 3 is the honest result of this simulated window — each run
covers its own advection travel time plus a ~200s margin, enough for the
hot-water front to reach the capsule (confirmed by the ~25°C temperature
rise in every regime) but not enough, for any of the 3 regimes this time,
to push the surface past its PCM's melting point. This doesn't contradict
Objective 2's own simulator, which independently confirms real melting at
these designs' real operating timescales (`sim_mean_f_melt`: 21.4% /
14.5% / 23.1% for Regimes 0/1/2) — Fluent's window here is intentionally
short (a sanity check, not a full-day simulation). The earlier 2026-10-26
re-run (bug-fixed/no-shield/50L geometry) did show a small 0.33% melt in
Regime 1, which is kept as the direct evidence that Fluent's
solidification model does cross into melting correctly once given enough
margin — see `CFD_VERIFICATION.md` for both runs side by side.

**Disclosed scope limitations** (unchanged, still real): Fluent uses a
planar (flat, non-revolved) geometry simplification — true axisymmetric
mode proved numerically unresolvable after 3 independent fix attempts in
the original work. OpenFOAM has no native phase-change model, was only
ever run for the original pre-fix Regime 0 geometry, and has not been
re-run since — ANSYS Fluent is this project's primary CFD cross-check
(see `TAMILNADU_REDESIGN_PLAN.md` §4). Neither tool's result is a
validated, production-grade CFD study.

## Open items

- **Safety shield is a correct but blunt first implementation.** It is a
  simple instantaneous temperature trip — it now achieves 100%
  temperature-safety AND (after the resize) good demand reliability, but
  it's still a reactive on/off rule, not an anticipatory one. Objective
  3's whole purpose is to do better than this with a learned policy.
- Gate 3 fails honestly (capability check) on this exact combination of
  direct-encapsulation PCM + a now-adequately-sized tank — see
  "Deployable design per regime" above for what this means and does not
  mean.
- Regime 1's P(meets annual demand) is 94.2%, not 100% like the other two
  — still comfortably above the 75% bar, but worth knowing it's the
  closest of the three to the line, if future weather-year data changes.
- The Fluent liquid-fraction initialization patch command fails on every
  run (a TUI argument error) — very likely inconsequential since
  temperature-based initialization already implies 0% melt at t=0, but
  never independently confirmed by fixing the actual call.
- Phase 6b (multi-fidelity surrogate) is archived, broken against the
  current DOE schema, never re-run — optional add-on, not a core phase.
- Multi-year (2016–2025) weather re-evaluation, the 1-D stratified tank,
  and the NN-ensemble + NSGA-II surrogate/optimizer are all
  decided-but-unimplemented next steps — see `TAMILNADU_REDESIGN_PLAN.md`
  §5–6 for the full list and recommended order.
