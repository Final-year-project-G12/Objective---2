# 00 — Objective 2 Master Overview (Uttarakhand, Phases 1–8 — COMPLETE)

## What this covers

Objective 2 turns Objective 1's output — climate regimes + a shortlisted
PCM per regime — into a **physical PCM-storage design and a validated
simulator** that Objective 3 can build a controller against. This
consolidated set of docs covers **all eight phases** of the ~40-hour
per-state execution plan (`O2_Unified_PerState_Execution_Framework.md`),
implemented, verified, and completed for **Uttarakhand**. Objective 2 is
done for this state — see `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` for the
hand-off.

**This is the final, fully-corrected version of this document (2026-09-14)**,
after four rounds of fixes applied in sequence:
1. Objective 1 bug fixes (MCDM ranking, feasibility, physics validation) — upstream data rebuilt.
2. A stale Phase 1 config bug found and fixed: `configs/states/uttarakhand.yaml`'s `cluster_id` 1/2 had been swapped relative to the rebuilt Objective 1 clustering.
3. Two methodology revisions ported from `objective2-tamilnadu`: **Tm-target retargeting** (doc 12) and **design-bounds widening** (doc 13).
4. A selection-rule **scope correction**: the assignment asks Objective 2 to optimize a PCM design's parameters, not to decide whether to use PCM at all — the zero-mass "plain tank" option is kept in the comparison report but excluded from winning the final per-regime recommendation (`08_PHASE7_OPTIMIZATION.md`).

| Phase | Deliverable | Status |
|---|---|---|
| Phase 1 | D2.1 — frozen state config (`configs/states/uttarakhand.yaml`) | COMPLETE |
| Phase 2 | D2.2 — geometry & constraint engine (`src/design/`) | COMPLETE — max reachable PCM fraction 19.84% (widened bounds) |
| Phase 3 | D2.3 — grey-box enthalpy simulator (`src/simulation/`) | COMPLETE |
| Phase 4 | Simulator verification, Gates 1–5 (`src/verify/gates.py`) | COMPLETE — **GO** |
| Phase 5 | D2.4 — DOE (`src/doe/`) | COMPLETE — 142 valid / 73 rejected |
| Phase 6 | D2.5 — surrogate (`src/surrogate/`) — R²≈1.000 every regression target | COMPLETE |
| Phase 7 | D2.6 — optimization + simulator confirmation, PCM-only selection (`src/optimize/`) | COMPLETE |
| Phase 8 | D2.7/D2.8/D2.9 — robustness (real 10-yr historical weather ensemble), recommendation cards, Objective 3 contract (`src/robustness/`, `src/handoff/`) | COMPLETE |

## Code map

```
objective2-uttarakhand/
├── config.py                          # path constants
├── build_input_package.py             # Phase 0 — freezes Obj1 outputs -> data/objective1/
├── build_regime_weather.py            # Phase 0 — per-regime weather
├── build_demand_profile.py            # Phase 0 — canonical demand curve
├── pipeline.py                        # CLI entry point for Phases 2-8
├── configs/
│   ├── system_config_shared.yaml      # Phase 0A, frozen for all 4 states
│   ├── design_bounds_shared.yaml      # Phase 0A, widened 2026-09-14 (doc 13)
│   └── states/uttarakhand.yaml        # Phase 1, retargeted 2026-09-14 (doc 12)
├── src/
│   ├── io_utils.py                    # shared config/data loaders
│   ├── design/
│   │   ├── schema.py                  # DesignVector
│   │   ├── geometry.py                # Phase 2 geometry + Ergun hydraulics
│   │   ├── constraints.py             # Phase 2 valid/invalid + reason codes
│   │   └── retarget_tm.py             # Tm_target_C retargeting (doc 12, ported from Tamil Nadu)
│   ├── simulation/
│   │   ├── capsule_enthalpy.py        # Phase 3 enthalpy model
│   │   ├── collector_model.py         # Phase 3 flat-plate collector
│   │   ├── heat_transfer.py           # Phase 3 UA_eff (Wakao-Kaguei)
│   │   ├── hydraulic_model.py         # Phase 3 runtime pump-power wrapper
│   │   ├── demand_profile.py          # Phase 3 demand-curve model
│   │   ├── energy_balance.py          # Phase 3/4 energy accounting
│   │   ├── tank_model.py              # Phase 3 core timestep solver
│   │   └── run_case.py                # Phase 3 one-case orchestrator
│   ├── verify/
│   │   └── gates.py                   # Phase 4 Gates 1-5 + report writer
│   ├── doe/
│   │   ├── generate_cases.py          # Phase 5 LHS + boundary + baseline sampling
│   │   ├── run_batch.py               # Phase 5 runs every case through Phase 2+3
│   │   └── split_cases.py             # Phase 5 case-level train/holdout split
│   ├── surrogate/
│   │   ├── features.py                # Phase 6 feature table (design+climate+PCM+confidence)
│   │   ├── train.py                   # Phase 6 ExtraTrees + linear baseline + feasibility clf
│   │   ├── evaluate.py                # Phase 6 error breakdown by regime/PCM
│   │   └── multifidelity.py           # Phase 6b low-fidelity speedup + sample-efficiency experiment
│   ├── optimize/
│   │   ├── search.py                  # Phase 7 surrogate-scored random search
│   │   └── select_deployable.py       # Phase 7 simulator-confirm + PCM-only selection rule (scope-corrected)
│   ├── robustness/
│   │   ├── monte_carlo.py             # Phase 8 Monte Carlo robustness analysis
│   │   └── weather_ensemble.py        # Phase 8 real 10-year historical weather ensemble
│   ├── handoff/
│   │   ├── build_recommendation_cards.py  # Phase 8 per-regime cards
│   │   └── build_obj3_contract.py         # Phase 8 Objective 3 environment contract
│   └── plots/
│       └── make_plots.py              # justification figures for Phases 2-8
└── results/uttarakhand/
    ├── simulator_verification_report.txt      # Phase 4 output (GO)
    ├── tm_retargeting_report.csv               # doc 12 before/after evidence
    ├── design_cases.parquet / .csv            # Phase 5 output
    ├── surrogate_metrics.csv, surrogate/models.pkl   # Phase 6 output
    ├── surrogate_error_by_group.csv            # Phase 6 output
    ├── surrogate_top_candidates.csv            # Phase 7 intermediate output
    ├── optimized_designs.csv                   # Phase 7 PCM-comparison report (plain tank included, for reference)
    ├── deployable_design_per_regime.csv        # Phase 7 final selection (PCM-only)
    ├── robustness_results.csv, robustness_summary.csv  # Phase 8 Monte Carlo output (real 10-yr weather ensemble)
    ├── recommendation_cards.md                 # Phase 8 per-regime cards
    └── obj3_environment_contract_uttarakhand.json  # Phase 8 Objective 3 hand-off
```

Everything under `src/` is **state-agnostic** — `state="uttarakhand"` is just
a string passed in; running the same code for Tamil Nadu/Rajasthan/Assam
only requires their own `configs/states/<state>.yaml` plus their
`data/objective1/`, `data/weather/`, `data/demand/` folders.

## Headline result: Phase 4 verdict = **GO**

```
Gate 1 (conservation):        PASS   max residual = 0.004708 %  (limit: <0.5%)
Gate 2 (limiting cases):      PASS   10/10 checks
Gate 3 (baseline comparison): PASS   RT42 (retargeted PCM) beats plain tank cleanly
Gate 4 (published benchmark): PASS-WITH-CAVEAT (39.20% vs cited 54-84% band — see explanation)
Gate 5 (sensitivity):         PASS   3/3 checks

Go/No-Go: GO  ->  simulator released as sim_v1_uttarakhand
```

## The three findings worth reading before anything else

**1. After retargeting the PCM melting point to the tank's real operating
range, every regime's optimal PCM design genuinely (if narrowly) beats
plain water.** The original climate-anchored PCM shortlist (Tm≈57–58°C)
did not clearly beat plain tank in Gate 3 — the tank's real charging-hour
water temperature runs far below 57°C. Retargeting `Tm_target_C` to each
regime's own simulated median charging temperature (27.8–42.1°C, see doc
12) and re-selecting the shortlist against that fixed Gate 3 cleanly:
a matched-Tm PCM now beats plain tank (39.25% vs 39.01% solar fraction).
Phase 7's 400-candidate-per-regime-PCM-pair search (now searching a wider
design space too, doc 13) confirms every regime's best PCM candidate beats
its own plain-tank candidate by 0.01–0.14% useful energy — narrow, but
consistently positive everywhere, including regime 1 where no retargeted
PCM exists in the database (it keeps its old, climate-anchored shortlist
as a documented fallback — see doc 12).

**2. Even a well-matched PCM still exceeds the safety limit on hot days in
4 of 5 regimes — this is now the central engineering finding.** Per the
selection-rule scope correction, Objective 2 always recommends a PCM
design (never plain tank) and reports temperature safety as a deployment
precondition rather than a selection filter. The result: regimes 0, 2, 3
and 4's selected PCM designs all have a **negative** nominal
`constraint_margin_C` (their own body temperature exceeds the 65°C PCM
limit by 4.2–7.8°C on the reference simulated year), because a PCM
matched to *typical* charging conditions still tracks water temperature
on *peak* sunny days when nothing caps the tank below 75°C. Only regime 1
(coldest mains, and — not by design — a PCM so mismatched to its own cold
climate that it barely activates) stays safely under both limits
(margin +11.9°C). **Objective 3 must implement active bypass/discharge
control for regimes 0, 2, 3 and 4 before hardware deployment** — this is
reported as a specified precondition, not a disqualification of the
design (see `08_PHASE7_OPTIMIZATION.md`).

**3. Demand reliability is structurally near-zero for Uttarakhand — this
is a genuine climate finding, not a bug, and should not be expected to
resemble Tamil Nadu's or Rajasthan's results.** Uttarakhand's mains water
(7.45–21.82°C) is far colder than Tamil Nadu's or Rajasthan's (~24–26°C),
so heating the same 300 L/day draw to the same 50°C delivery target from a
colder start costs substantially more energy for the same 50 L / 1.5 m²
system. Nominal solar fractions land at 28.1–41.4% for Uttarakhand versus
51.4–54.8% for Tamil Nadu under the same fixed 50%-solar-fraction "meets
demand" bar — Tamil Nadu's designs mostly already clear that bar, so most
Monte Carlo draws do too (its own robustness plots show 70–100%
demand-reliability). Uttarakhand's designs never get close, so **P(meets
annual demand) = 0.0% across all 5 regimes** under the identical,
cross-state-comparable Monte Carlo methodology. See
`10_PHASE8_ROBUSTNESS_HANDOFF.md` for the full table.

All three findings are the optimizer/analysis working correctly, not a
defect — exactly the kind of result Objective 2 exists to surface. See
`09_NEXT_STEPS.md` and `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` for what
this implies for Objective 3.

## Documents in this folder

- `01_PHASE1_CONFIG_AND_STATE_SETUP.md` — frozen configs, per-state input file, the cluster-ID fix
- `02_PHASE2_GEOMETRY_CONSTRAINTS.md` — geometry engine, Ergun hydraulics, bounds finding
- `03_PHASE3_GREYBOX_SIMULATOR.md` — enthalpy model, energy balance, solver design + documented bugs fixed
- `04_PHASE4_VERIFICATION_GATES.md` — full Gate 1-5 methodology and results
- `06_PHASE5_DOE.md` — DOE sampling plan and result
- `07_PHASE6_SURROGATE.md` — surrogate features, models, hold-out accuracy
- `08_PHASE7_OPTIMIZATION.md` — optimization search, simulator confirmation, PCM-vs-plain-tank finding, scope correction
- `09_NEXT_STEPS.md` — the PCM-design decision the team faced, and how it was resolved
- `10_PHASE8_ROBUSTNESS_HANDOFF.md` — Monte Carlo methodology, the demand/temperature findings, recommendation cards, Objective 3 contract
- `11_MULTIFIDELITY_SURROGATE.md` — Phase 6b's low-fidelity speedup and sample-efficiency experiment
- `12_TM_TARGET_RETARGETING.md` — the PCM melting-point retargeting revision (ported from Tamil Nadu)
- `13_DESIGN_BOUNDS_WIDENING.md` — the capsule-count bound widening revision (ported from Tamil Nadu)
- `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` — what Objective 3 needs from this project and what to do first
- `HOW_TO_RUN.md` — exact commands to reproduce everything above
- `../results/uttarakhand/recommendation_cards.md` — per-regime recommendation cards (generated output)
