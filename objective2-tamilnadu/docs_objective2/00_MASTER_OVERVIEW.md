# 00 — Objective 2 Master Overview (Tamil Nadu, Phases 1–8 — COMPLETE)

## What this covers

Objective 2 turns Objective 1's output — climate regimes + a shortlisted
PCM per regime — into a **physical PCM-storage design and a validated
simulator** that Objective 3 can build a controller against. This
consolidated set of docs covers **all eight phases** of the ~40-hour
per-state execution plan (`O2_Unified_PerState_Execution_Framework.md`),
implemented, verified, and completed for **Tamil Nadu**. Objective 2 is
done for this state — see `RESULTS.md` (project root) for the full
results digest and `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` for the hand-off.

| Phase | Deliverable | Status |
|---|---|---|
| Phase 1 | D2.1 — frozen state config (`configs/states/tamilnadu.yaml`) | COMPLETE |
| Phase 2 | D2.2 — geometry & constraint engine (`src/design/`) | COMPLETE |
| Phase 3 | D2.3 — grey-box enthalpy simulator (`src/simulation/`) | COMPLETE |
| Phase 4 | Simulator verification, Gates 1–5 (`src/verify/gates.py`) | COMPLETE — **GO** |
| Phase 5 | D2.4 — DOE (`src/doe/`) — 215 cases, 145 valid | COMPLETE |
| Phase 6 | D2.5 — surrogate (`src/surrogate/`) — R²>0.98 every target | COMPLETE |
| Phase 7 | D2.6 — optimization + simulator confirmation (`src/optimize/`) | COMPLETE |
| Phase 8 | D2.7/D2.8/D2.9 — robustness, recommendation cards, Objective 3 contract (`src/robustness/`, `src/handoff/`) | COMPLETE |

## Code map

```
objective2_design_optimization/
├── config.py                          # path constants (already existed)
├── build_input_package.py             # Phase 0 — freezes Obj1 outputs   (already existed)
├── build_regime_weather.py            # Phase 0 — per-regime weather     (already existed)
├── build_demand_profile.py            # Phase 0 — canonical demand curve (already existed)
├── pipeline.py                        # NEW — CLI entry point for Phases 2-4
├── configs/
│   ├── system_config_shared.yaml      # NEW — Phase 0A, frozen for all 4 states
│   ├── design_bounds_shared.yaml      # NEW — Phase 0A, frozen for all 4 states
│   └── states/tamilnadu.yaml          # NEW — Phase 1, this state's inputs
├── src/
│   ├── io_utils.py                    # NEW — shared config/data loaders
│   ├── design/
│   │   ├── schema.py                  # NEW — DesignVector
│   │   ├── geometry.py                # NEW — Phase 2 geometry + Ergun hydraulics
│   │   └── constraints.py             # NEW — Phase 2 valid/invalid + reason codes
│   ├── simulation/
│   │   ├── capsule_enthalpy.py        # NEW — Phase 3 enthalpy model
│   │   ├── collector_model.py         # NEW — Phase 3 flat-plate collector
│   │   ├── heat_transfer.py           # NEW — Phase 3 UA_eff (Wakao-Kaguei)
│   │   ├── hydraulic_model.py         # NEW — Phase 3 runtime pump-power wrapper
│   │   ├── demand_profile.py          # NEW — Phase 3 demand-curve model
│   │   ├── energy_balance.py          # NEW — Phase 3/4 energy accounting
│   │   ├── tank_model.py              # NEW — Phase 3 core timestep solver
│   │   └── run_case.py                # NEW — Phase 3 one-case orchestrator
│   ├── verify/
│   │   └── gates.py                   # NEW — Phase 4 Gates 1-5 + report writer
│   ├── doe/
│   │   ├── generate_cases.py          # NEW — Phase 5 LHS + boundary + baseline sampling
│   │   ├── run_batch.py               # NEW — Phase 5 runs every case through Phase 2+3
│   │   └── split_cases.py             # NEW — Phase 5 case-level train/holdout split
│   ├── surrogate/
│   │   ├── features.py                # NEW — Phase 6 feature table (design+climate+PCM+confidence)
│   │   ├── train.py                   # NEW — Phase 6 ExtraTrees + linear baseline + feasibility clf
│   │   └── evaluate.py                # NEW — Phase 6 error breakdown by regime/PCM
│   ├── optimize/
│   │   ├── search.py                  # NEW — Phase 7 surrogate-scored random search
│   │   └── select_deployable.py       # NEW — Phase 7 simulator-confirm + selection rule
│   ├── robustness/
│   │   └── monte_carlo.py             # NEW — Phase 8 Monte Carlo robustness analysis
│   ├── handoff/
│   │   ├── build_recommendation_cards.py  # NEW — Phase 8 per-regime cards
│   │   └── build_obj3_contract.py         # NEW — Phase 8 Objective 3 environment contract
│   └── plots/
│       └── make_plots.py              # NEW — justification figures for Phases 2-8
├── RESULTS.md                          # NEW — full results digest, all 8 phases
└── results/tamilnadu/
    ├── simulator_verification_report.txt      # Phase 4 output (GO)
    ├── design_cases.parquet / .csv            # Phase 5 output (215 cases)
    ├── surrogate_metrics.csv, surrogate/models.pkl   # Phase 6 output
    ├── surrogate_error_by_group.csv            # Phase 6 output
    ├── surrogate_top_candidates.csv            # Phase 7 intermediate output
    ├── optimized_designs.csv                   # Phase 7 PCM-comparison report
    ├── deployable_design_per_regime.csv        # Phase 7 final selection
    ├── robustness_results.csv, robustness_summary.csv  # Phase 8 Monte Carlo output
    ├── recommendation_cards.md                 # Phase 8 per-regime cards
    ├── obj3_environment_contract_tamilnadu.json  # Phase 8 Objective 3 hand-off
    └── plots/
        ├── interactive/*.html                  # 17 self-contained interactive figures
        └── static/*.png                        # same 17 figures as flat images
```

Everything under `src/` is **state-agnostic** — `state="tamilnadu"` is just
a string passed in; running the same code for Rajasthan/Assam/Uttarakhand
only requires their own `configs/states/<state>.yaml` plus their
`data/objective1/`, `data/weather/`, `data/demand/` folders (built the same
way `build_input_package.py` / `build_regime_weather.py` /
`build_demand_profile.py` already build Tamil Nadu's).

## Headline result: Phase 4 verdict = **GO**

```
Gate 1 (conservation):        PASS   max residual = 0.00008 %  (limit: <0.5%)
Gate 2 (limiting cases):      PASS   10/10 checks
Gate 3 (baseline comparison): PASS   (see caveat below)
Gate 4 (published benchmark): PASS-WITH-CAVEAT (52% vs cited 54-84% band)
Gate 5 (sensitivity):         PASS   3/3 checks

Go/No-Go: GO  ->  simulator released as sim_v1_tamilnadu
```

## The two findings worth reading before anything else

**1. PCM barely helps in this design.** Gate 3 (Phase 4) found that
**Objective 1's actual rank-1 PCM (n-Octacosane, Tm = 61.6 °C) does *not*
clearly beat a plain sensible-water tank** in the current 50 L
direct-encapsulation design, even at the maximum PCM volume fraction
achievable within the frozen design bounds (~12.9%, not the documented
20% — see `02_PHASE2_GEOMETRY_CONSTRAINTS.md`). A diagnostic swap to a
synthetic PCM matched to the tank's actual operating range (Tm = 40 °C)
*does* beat the plain tank decisively (55.2% vs 52.3% solar fraction),
ruling out a simulator bug. Phase 7's full 400-candidate-per-pair
optimization confirmed this with much stronger evidence: every
shortlisted PCM beats plain water by only ~0.08% at its best-found
geometry — two orders of magnitude below the 5% selection tolerance — so
the deployable-design rule picks the zero-PCM-mass plain tank in **4 of
5** Tamil Nadu regimes (`08_PHASE7_OPTIMIZATION.md`).

**2. No design is temperature-robust under realistic uncertainty, and the
PCM regime is worst on every axis.** Phase 8's Monte Carlo robustness
analysis (120 draws/design, PCM property/weather/demand/mains-temperature
uncertainty, fixed cross-state-comparable thresholds) found that
delivery-temperature reliability is never a problem, but **none** of the
5 regimes meets the framework's 95% temperature-safety bar — plain-tank
regimes range 67–87% safe, and the one PCM regime is worst at just
**44%** safe, because a PCM design must respect two temperature limits
instead of one. That same PCM regime is also the *only* one to fail the
75% demand-reliability bar (70%) — the only regime failing both criteria
at once (`10_PHASE8_ROBUSTNESS_HANDOFF.md`). This is a genuine consequence
of having no active high-temperature safety shield anywhere in Phases
1–7's physics, not a bug — and it is now a specified, non-optional
requirement (with a 3°C precautionary guard band) in the Objective 3
hand-off contract.

Both findings are the optimizer/analysis working correctly, not a defect
— exactly the kind of result Objective 2 exists to surface. See
`09_NEXT_STEPS.md` for the PCM-design decision and
`OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` for what Objective 3 must do about
the safety finding.

## Documents in this folder

- `01_PHASE1_CONFIG_AND_STATE_SETUP.md` — frozen configs, per-state input file
- `02_PHASE2_GEOMETRY_CONSTRAINTS.md` — geometry engine, Ergun hydraulics, bounds finding
- `03_PHASE3_GREYBOX_SIMULATOR.md` — enthalpy model, energy balance, solver design + the energy-conservation bug that was found and fixed
- `04_PHASE4_VERIFICATION_GATES.md` — full Gate 1-5 methodology and results
- `06_PHASE5_DOE.md` — 215-case DOE sampling plan and result
- `07_PHASE6_SURROGATE.md` — surrogate features, models, hold-out accuracy
- `08_PHASE7_OPTIMIZATION.md` — optimization search, simulator confirmation, the PCM-vs-plain-tank finding
- `09_NEXT_STEPS.md` — the PCM-design decision the team should make
- `10_PHASE8_ROBUSTNESS_HANDOFF.md` — Monte Carlo methodology, the temperature-safety finding, recommendation cards, Objective 3 contract
- `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` — what Objective 3 needs from this project and what to do first
- `plots/00_INDEX.md` and `plots/02_...` through `plots/08_...md` — the 17
  justification figures (interactive HTML + static PNG) for Phases 2-8,
  with what each one shows, what to infer, and how to explain it
- `HOW_TO_RUN.md` — exact commands to reproduce everything above (and whether any external simulator/MATLAB is needed — it isn't)
- `../RESULTS.md` (project root) — the complete results digest for all 8 phases
