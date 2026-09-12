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

| Phase | Deliverable | Status |
|---|---|---|
| Phase 1 | D2.1 — frozen state config (`configs/states/uttarakhand.yaml`) | COMPLETE |
| Phase 2 | D2.2 — geometry & constraint engine (`src/design/`) | COMPLETE |
| Phase 3 | D2.3 — grey-box enthalpy simulator (`src/simulation/`) | COMPLETE |
| Phase 4 | Simulator verification, Gates 1–5 (`src/verify/gates.py`) | COMPLETE — **GO** |
| Phase 5 | D2.4 — DOE (`src/doe/`) | COMPLETE |
| Phase 6 | D2.5 — surrogate (`src/surrogate/`) — R²>0.9998 every target | COMPLETE |
| Phase 7 | D2.6 — optimization + simulator confirmation (`src/optimize/`) | COMPLETE |
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
│   ├── design_bounds_shared.yaml      # Phase 0A, frozen for all 4 states
│   └── states/uttarakhand.yaml        # Phase 1, this state's inputs
├── src/
│   ├── io_utils.py                    # shared config/data loaders
│   ├── design/
│   │   ├── schema.py                  # DesignVector
│   │   ├── geometry.py                # Phase 2 geometry + Ergun hydraulics
│   │   └── constraints.py             # Phase 2 valid/invalid + reason codes
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
│   │   └── select_deployable.py       # Phase 7 simulator-confirm + selection rule
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
    ├── design_cases.parquet / .csv            # Phase 5 output
    ├── surrogate_metrics.csv, surrogate/models.pkl   # Phase 6 output
    ├── surrogate_error_by_group.csv            # Phase 6 output
    ├── surrogate_top_candidates.csv            # Phase 7 intermediate output
    ├── optimized_designs.csv                   # Phase 7 PCM-comparison report
    ├── deployable_design_per_regime.csv        # Phase 7 final selection
    ├── robustness_results.csv, robustness_summary.csv  # Phase 8 Monte Carlo output (real 10-yr weather ensemble)
    ├── recommendation_cards.md                 # Phase 8 per-regime cards
    └── obj3_environment_contract_uttarakhand.json  # Phase 8 Objective 3 hand-off
```

Everything under `src/` is **state-agnostic** — `state="uttarakhand"` is just
a string passed in; running the same code for Tamil Nadu/Rajasthan/Assam
only requires their own `configs/states/<state>.yaml` plus their
`data/objective1/`, `data/weather/`, `data/demand/` folders (built the same
way `build_input_package.py` / `build_regime_weather.py` /
`build_demand_profile.py` already build Uttarakhand's).

## Headline result: Phase 4 verdict = **GO**

```
Gate 1 (conservation):        PASS   max residual = 0.002764 %  (limit: <0.5%)
Gate 2 (limiting cases):      PASS   10/10 checks
Gate 3 (baseline comparison): PASS   (see caveat below)
Gate 4 (published benchmark): PASS-WITH-CAVEAT (40.41% vs cited 54-84% band — see explanation)
Gate 5 (sensitivity):         PASS   3/3 checks

Go/No-Go: GO  ->  simulator released as sim_v1_uttarakhand
```

## The two findings worth reading before anything else

**1. PCM barely helps in 4 of 5 regimes.** Gate 3 (Phase 4) found that
**Objective 1's actual rank-1 PCM (PureTemp 58, Tm = 58.0 °C) does *not*
clearly beat a plain sensible-water tank** in the current 50 L
direct-encapsulation design, even at the maximum PCM volume fraction
achievable within the frozen design bounds (~12.9%). A diagnostic swap to a
synthetic PCM matched to the tank's actual operating range (Tm = 40 °C)
*does* beat the plain tank (41.27% vs 40.71% solar fraction), ruling out a
simulator bug. Phase 7's full 400-candidate-per-pair optimization confirmed
this across the full search: plain tank is selected in **4 of 5**
Uttarakhand regimes, and **PureTemp 58 wins only in regime 2** (the coldest,
highest-L_required regime) — where the PCM candidate's best-found useful
energy outright exceeded the regime's own plain-tank optimum, winning before
any tolerance tie-break was needed.

**2. No design meets the robustness framework rule — and Uttarakhand's
climate means demand reliability is universally weak.** Phase 8's Monte Carlo
robustness analysis (120 draws/design, PCM property/weather/demand/mains-
temperature uncertainty, fixed cross-state-comparable thresholds, and a real
10-year historical weather ensemble) found that **P(meets annual demand,
solar_fraction ≥ 50%) = 0.0% across ALL 5 regimes**. Uttarakhand's lower
ambient temperatures, higher mains temperatures relative to delivery
temperature, and moderate GHI combine to push nominal solar fractions into
the 28–41% range — structurally below the 50% fixed demand bar. The
temperature-safety picture is mixed: regime 2 (the PCM regime) is the
**safest** at 0.0% safety violations (the PCM absorbs excess heat), while
regimes 0 and 3 are worst (55.8% and 35.8% violation probability
respectively). See `10_PHASE8_ROBUSTNESS_HANDOFF.md` for the full table.

Both findings are the optimizer/analysis working correctly, not a defect
— exactly the kind of result Objective 2 exists to surface. The low solar
fractions are a genuine consequence of Uttarakhand's climate (colder
winters, high L_required in the cold regime, lower peak water temperatures
limiting PCM activation) under the frozen 50 L / 1.5 m² collector sizing,
not a code error. See `09_NEXT_STEPS.md` and
`OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` for what this implies.

## Documents in this folder

- `01_PHASE1_CONFIG_AND_STATE_SETUP.md` — frozen configs, per-state input file
- `02_PHASE2_GEOMETRY_CONSTRAINTS.md` — geometry engine, Ergun hydraulics, bounds finding
- `03_PHASE3_GREYBOX_SIMULATOR.md` — enthalpy model, energy balance, solver design + documented bugs fixed
- `04_PHASE4_VERIFICATION_GATES.md` — full Gate 1-5 methodology and results
- `06_PHASE5_DOE.md` — DOE sampling plan and result
- `07_PHASE6_SURROGATE.md` — surrogate features, models, hold-out accuracy
- `08_PHASE7_OPTIMIZATION.md` — optimization search, simulator confirmation, PCM-vs-plain-tank finding
- `09_NEXT_STEPS.md` — the PCM-design decision the team should make
- `10_PHASE8_ROBUSTNESS_HANDOFF.md` — Monte Carlo methodology, the demand/temperature findings, recommendation cards, Objective 3 contract
- `11_MULTIFIDELITY_SURROGATE.md` — Phase 6b's low-fidelity speedup and sample-efficiency experiment
- `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` — what Objective 3 needs from this project and what to do first
- `HOW_TO_RUN.md` — exact commands to reproduce everything above
- `../results/uttarakhand/recommendation_cards.md` — per-regime recommendation cards (generated output)
