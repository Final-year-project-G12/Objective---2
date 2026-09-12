# 00 — Objective 2 Master Overview (Assam, Phases 0–7 run; Phase 8 not yet built)

## What this covers

Objective 2 turns Objective 1's output — climate regimes + a shortlisted
PCM per regime — into a **physical PCM-storage design and a validated
simulator** that Objective 3 can build a controller against. This file
was previously a leftover copy of `objective2-rajasthan`'s master
overview (wrong medoids, wrong PCMs, wrong demand volume, and Phase 8
numbers that were never produced for Assam). It has been rewritten from
Assam's actual `results/` files.

| Phase | Deliverable | Status |
|---|---|---|
| Phase 0 | Frozen Objective 1 inputs + climate-signature sanity check | PASSED (per `configs/states/assam.yaml`'s embedded check — no standalone `results/phase0_*` report file exists in this repo) |
| Phase 1 | D2.1 — frozen state config (`configs/states/assam.yaml`) | COMPLETE |
| Phase 2 | D2.2 — geometry & constraint engine (`src/design/`) | COMPLETE (state-agnostic, shared with all states) |
| Phase 3 | D2.3 — grey-box enthalpy simulator (`src/simulation/`) | COMPLETE (state-agnostic engine; no standalone `results/phase3_simulate_*.json` smoke-run files saved for Assam — see `04_…` Gate 1/2 cases for the closest equivalent numbers) |
| Phase 4 | Simulator verification, Gates 1–5 (`src/verify/gates.py`) | COMPLETE — **GO, but only 4/5 gates clean (Gate 3 FAILS)**, `sim_v1_assam` |
| Phase 5 | D2.4 — reduced DOE (`src/doe/`) | COMPLETE — **165 cases (111 valid / 54 infeasible-retained), 138/27 train/holdout** |
| Phase 6 | D2.5 — surrogate (`src/surrogate/`) | COMPLETE — **useful-energy hold-out R² = 0.9977 (target > 0.80)**, 29 features |
| Phase 7 | D2.6 — optimization + simulator confirmation | COMPLETE, run via a **bespoke `scripts/run_phase7_optimization.py`**, not the ported `src/optimize/` module — see caveat below. Result as reported: a PCM design "PASSED" in all 3 regimes. **Independently checked here: this verdict is wrong** — see "The safety-verdict bug" below. |
| Phase 8 | D2.7–D2.9 — robustness + recommendation cards + Obj3 handoff | **NOT RUN.** `src/robustness/monte_carlo.py` and `src/handoff/build_*.py` exist (ported, same as Rajasthan/Tamil Nadu) but there is no `results/phase8_*` file and no `obj3_environment_contract_assam.json` anywhere in this repo. Any document that previously described Phase 8 "results" for Assam was describing Rajasthan's numbers by mistake. |

## Climate regimes actually used (from `configs/states/assam.yaml` / `data/objective1/cluster_profiles_assam.csv`)

K_FINAL = 3 (Level-A GMM), same as Rajasthan's regime count but a
**different climate, different medoids, different PCM shortlist**:

| cluster_id | label | medoid | n_points | population | T_mains_est_C | L_required_kJ/kg |
|---|---|---|---|---|---|---|
| 0 | Lower Brahmaputra Valley (moist valley) | ASP_0012 | 33 | 4,757,891 | 19.89 | 252.09 |
| 1 | Upper Assam Tea Belt (warm valley) | ASP_0092 | 61 | 4,271,199 | 19.10 | 258.69 |
| 2 | Barak Valley & Southern Hills (elevated, cooler) | ASP_0028 | 35 | 2,466,324 | 16.59 | 279.70 |

`Tm_target_C = 44.0 °C` for all three regimes. PCM shortlist is
**identical across all 3 regimes**: `savE® OM48, savE® OM50, savE® OM46`
— per `assam.yaml`'s own note, this is **not** an Objective 1 MCDM
Top-3 in the usual sense: Objective 1's confirmed-feasible K=3 MCDM
ranking returned zero confirmed candidates, and the earlier K=4 ranking
was physically invalidated in Objective 1's own Phase 10 (ρ = −0.52 to
−0.64 correlation with actual solar-fraction performance; the old
rank-1 PCM RT44HC came last). The shortlist actually used here is
Objective 1's **Phase 9/10 physics-validated candidate universe**
(10-year simulation ranking), not a clustering+MCDM output — this is a
material difference from how Rajasthan/Tamil Nadu's shortlists were
built, and should be stated as such in the paper rather than described
as "MCDM Top-3."

**Demand: 100 L/day** (50 L morning @ 07:00 IST + 50 L evening @ 19:00
IST) — **not** 300 L/day. This matches Assam Objective 1's own SWH
design specification and 10-year physics validation, but it means
Assam's absolute energy numbers (~650–710 kWh/year useful energy) are
**not directly comparable** to Rajasthan/Tamil Nadu's (~1550–1700
kWh/year) without normalizing for the 3× smaller demand — a fact any
four-state comparison chapter must state explicitly.

Mains temperature range: 15–28 °C (framework doc, Assam row); point
estimates per regime 16.59–19.89 °C, noticeably colder than
Rajasthan's 24.5–25.8 °C.

## Headline results, phase by phase (from the actual `results/` files)

```
Phase 4 (verification gates): GO but only 4/5 gates clean — Gate 3 FAILS.
    Gate 1: PASS (residual 0.000000% on all 5 cases)
    Gate 2: PASS (10/10 + 1 informational: plain-tank Cluster 0 hits 66.83 °C,
            already above the 65 °C PCM limit, on solar input alone)
    Gate 3: FAIL — plain tank (SF 62.51%) beats BOTH the fixed-PCM design
            (SF 61.54%) AND the capability-check PCM matched to the tank's
            own operating range (SF 60.65%). Objective 1's rank-1 PCM
            (savE® OM48) does not beat the plain tank in this 50 L /
            12.9%-fraction geometry. This is a stronger warning than
            Rajasthan (where Gate 3 passed) or Tamil Nadu.
    Gate 4: PASS (61.76% inside the cited 54-84% band)
    Gate 5: PASS (3/3)
    Overall: 4/5 clean, residual well under 0.5% -> GO per the framework's
    ">=3/5 clean" rule -- but Gate 3's failure was a signal, later ignored
    by Phase 7 (see below).

Phase 5 (DOE): 165 cases, 111 valid / 54 infeasible (all bounds_violation,
    32.7% -- same diameter/thickness interaction as every other state),
    138 train / 27 holdout.

Phase 6 (surrogate): useful-energy holdout R^2 = 0.9977 (Extra Trees),
    0.9981 (Linear -- ties/slightly beats the tree here). Feasibility
    classifier 100%/100%. 29 features (not Rajasthan's 39 -- Assam's
    Objective 1 tables carry fewer climate columns).

Phase 7 (optimize): run via scripts/run_phase7_optimization.py (a
    DIFFERENT search than the ported src/optimize/search.py +
    select_deployable.py used elsewhere) -- 1,000 candidates/pair x 12
    pairs = 12,000 candidates, 7,966 feasible, a "5% Near-Best Rule" +
    6-tier hierarchical tie-break (not the simple pareto_tolerance_pct
    rule), 21 top candidates, 5 re-simulated in the real sim_v1_assam.
    REPORTED verdict: "PASS -- 0/0 safety violations, PASSED at <=95 C
    water / <=90 C PCM." ACTUAL verdict (checked against this project's
    own frozen 75 C / 65 C limits in system_config_shared.yaml): FAILS.
    See "The safety-verdict bug" below. This is not a one-off: 79/111
    (71%) of Phase 5's valid DOE rows already exceed the 65 C PCM limit,
    so most of the design space Phase 7 searched was unsafe to begin
    with -- Phase 7 needed the filter it skipped.

Phase 8 (robustness+handoff): NOT RUN for Assam. No results/phase8_*.csv,
    no obj3_environment_contract_assam.json anywhere in this repo.
```

## The safety-verdict bug — read this before citing Phase 7's "PASS"

`system_config_shared.yaml` (frozen, identical across all 4 states) sets:

```yaml
safety:
  max_water_temp_C: 75.0
  max_pcm_temp_C: 65.0
```

`scripts/run_phase7_optimization.py` reads these correctly and computes
`water_temp_safety_margin_C = 75 - sim_max_water_temp_C` and
`pcm_temp_safety_margin_C = 65 - sim_max_pcm_temp_C` for every candidate
(lines ~349–352) — this is the same real safety envelope Rajasthan and
Tamil Nadu's Phase 7 used to reject PCM candidates. Reading
`results/phase7_deployable_design_per_regime.csv` directly:

| Regime | PCM selected | Max PCM temp (°C) | PCM margin to 65 °C | Max water temp (°C) | Water margin to 75 °C | `n_safety_violations` |
|---|---|---|---|---|---|---|
| 0 | savE® OM46 | 66.21 | **−1.21** | 66.51 | +9.01 | 13 |
| 1 | savE® OM48 | 67.95 | **−2.95** | 68.60 | +6.40 | 313 |
| 2 | savE® OM48 | 70.09 | **−5.09** | 70.71 | +4.29 | 215 |

**All 3 of Assam's Phase 7 "deployable" designs exceed the frozen 65 °C
PCM material-stability limit**, by 1.2–5.1 °C, and log 13–313
safety-violation sub-hours over the simulated year — this is exactly
the failure mode Rajasthan/Tamil Nadu's Phase 7 was designed to filter
out (`meets_temperature_safety` in the ported `select_deployable.py`),
and it is the same physical phenomenon as Rajasthan's Gate-2/Phase-5
overheating finding, not a new bug in the simulator.

`results/phase7_optimization_report.md` §5 nonetheless prints:

```
Max PCM Temp   Acceptance Standard <= 90.0°C   ... PASSED
```

That 90 °C figure does not exist anywhere in this project's frozen
config — it is invented in the report-generation code
(`scripts/run_phase7_optimization.py`, line ~573/602), which computes
the correct negative margin against the real 65 °C limit and then
**prints a hardcoded "PASSED" against a different, unrelated 90 °C
threshold without checking the actual sign of the margin it just
computed.** This is a genuine bug in the report template, not a policy
decision to relax the limit — nowhere is a deliberate 90 °C PCM / 95 °C
water limit documented or justified for Assam.

**Practical consequence:** as things stand, Assam has **no
Phase-7-validated deployable design** under this project's own
pre-declared safety rule. The honest options, in order of preference:
1. Re-run Phase 7's selection against the correct 65 °C / 75 °C limits
   (likely forcing the plain tank in some or all regimes, as it did for
   Rajasthan and 4/5 of Tamil Nadu's regimes) — the physically
   consistent choice, and the one that matches how the other two states'
   Phase 7 was done.
2. If a deliberately wider PCM temperature ceiling for Assam is wanted
   (e.g. because the shortlisted PCMs' Tm ≈ 44–51 °C sit differently
   here), that must be a stated, justified change to
   `system_config_shared.yaml` or a documented per-state override — not
   a silent mismatch between the config and the report.

## What remains (not built)

- **Phase 8 end-to-end for Assam**: run `python pipeline.py --state assam
  --stage robustness` then `--stage handoff` (code already exists,
  ported and untouched) once Phase 7's deployable designs are on solid
  ground.
- **The safety-verdict bug above must be resolved** before any Phase 7
  Assam number is cited in the paper as "validated" or "deployable."
- **A Phase-0 standalone report file** (`results/phase0_climate_signature_check.txt`)
  and **Phase-3 smoke-run JSON files** (`results/phase3_simulate_*.json`)
  don't exist for Assam the way they do for Rajasthan/Tamil Nadu — the
  underlying checks were done (see `assam.yaml`'s embedded Phase 0 note
  and Phase 4's Gate 1/2 cases) but not saved as separate artifacts.
- **`docs/01`–`docs/08` and `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md`** have
  been updated to Assam's actual numbers alongside this file; `docs/plots/`
  was not audited in this pass (still describes the figures generically
  and wasn't found to contain fabricated numbers, only unverified
  Rajasthan-era captions in places — treat with the same caution).
