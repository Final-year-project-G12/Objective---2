# 00 — Objective 2 Master Overview (Rajasthan, Phases 0–8 — COMPLETE)

## What this covers

Objective 2 turns Objective 1's output — climate regimes + a shortlisted
PCM per regime — into a **physical PCM-storage design and a validated
simulator** that Objective 3 can build a controller against. This set of
docs covers the phases implemented so far for **Rajasthan**, out of the
~40-hour per-state execution plan (`O2_Unified_PerState_Execution_Framework.md`):

| Phase | Deliverable | Status |
|---|---|---|
| Phase 0 | Frozen Objective 1 inputs + climate-signature sanity check (Bug-Fix 8) | COMPLETE — **PASSED, 3/3 regimes** |
| Phase 1 | D2.1 — frozen state config (`configs/states/rajasthan.yaml`) | COMPLETE |
| Phase 2 | D2.2 — geometry & constraint engine (`src/design/`) | COMPLETE |
| Phase 3 | D2.3 — grey-box enthalpy simulator (`src/simulation/`) | COMPLETE (smoke-tested) |
| Phase 4 | Simulator verification, Gates 1–5 (`src/verify/gates.py`) | COMPLETE — **GO, 5/5 gates clean**, `sim_v1_rajasthan` |
| Phase 5 | D2.4 — reduced DOE (`src/doe/`) | COMPLETE — **165 cases (111 valid / 54 infeasible-retained), 138/27 train/holdout** |
| Phase 6 | D2.5 — surrogate (`src/surrogate/`) | COMPLETE — **useful-energy hold-out R² = 0.9998 (target > 0.80)** |
| Phase 7 | D2.6 — optimization + simulator confirmation (`src/optimize/`) | COMPLETE — **plain tank wins all 3 regimes; 0/45 PCM candidates pass temperature safety** |
| Phase 8 | D2.7–D2.9 — robustness + recommendation cards + Obj3 handoff (`src/robustness/`, `src/handoff/`) | COMPLETE — **NOT robust (P(temp-safe) 0.33–0.51); 3 cards + contract written** |

Rajasthan has completed **all of Phases 1–8** — Phases 1–7 to Tamil Nadu's
level (Tamil Nadu itself stops at Phase 7), and Phase 8 built fresh
because `objective2-tamilnadu` has no `src/robustness/` or `src/handoff/`
to port (its `09_NEXT_STEPS.md` says so). `src/design/`,
`src/simulation/`, `src/doe/generate_cases.py` are byte-identical to
Tamil Nadu (state-agnostic by the framework doc); `verify/gates.py`
swaps only its per-state test inputs (3 clusters not 5; Rajasthan's PCM
shortlist; one extra informational Cluster-0 check); `doe/run_batch.py` +
`doe/split_cases.py`, `surrogate/{train,evaluate}.py` and
`optimize/{search,select_deployable}.py` differ only in the
`sim_v1_rajasthan` tag / flat `results/phaseN_*` paths / one sampling arg;
`surrogate/features.py` keeps TN's four feature groups but remaps column
names to Rajasthan's Objective 1 table headers (see `06_…`). Only
`src/plots/` (the Phase 2–7 justification figures) is still not copied
over.

## Code map (what actually exists today)

```
objective2-rajasthan/
├── config.py                          # path constants
├── check_climate_signature.py         # Phase 0 — sanity check that the frozen weather is genuinely Rajasthan's
├── pipeline.py                        # CLI entry point — geometry/simulate/verify/doe/surrogate/optimize/handoff wired; plots raises "not wired yet"
├── configs/
│   ├── system_config_shared.yaml      # Phase 0A — frozen, byte-identical across all 4 states
│   ├── design_bounds_shared.yaml      # Phase 0A — frozen, byte-identical across all 4 states
│   └── states/rajasthan.yaml          # Phase 1 — this state's inputs (regimes, PCM shortlist, mains temp, demand)
├── src/
│   ├── io_utils.py                    # shared config/data loaders (byte-identical to Tamil Nadu)
│   ├── design/
│   │   ├── schema.py                  # DesignVector (byte-identical to Tamil Nadu)
│   │   ├── geometry.py                # geometry + Ergun hydraulics (byte-identical to Tamil Nadu)
│   │   └── constraints.py             # valid/invalid + reason codes + boundary self-test (byte-identical to Tamil Nadu)
│   ├── simulation/
│   │   ├── capsule_enthalpy.py        # enthalpy model (byte-identical to Tamil Nadu)
│   │   ├── collector_model.py         # flat-plate collector (byte-identical to Tamil Nadu)
│   │   ├── heat_transfer.py           # UA_eff, Wakao-Kaguei (byte-identical to Tamil Nadu)
│   │   ├── hydraulic_model.py         # runtime pump-power wrapper (byte-identical to Tamil Nadu)
│   │   ├── demand_profile.py          # demand-curve model (byte-identical to Tamil Nadu)
│   │   ├── energy_balance.py          # energy accounting (byte-identical to Tamil Nadu)
│   │   ├── tank_model.py              # core timestep solver, incl. both Phase-4-discovered bug fixes (byte-identical to Tamil Nadu)
│   │   └── run_case.py                # one-case orchestrator (byte-identical to Tamil Nadu)
│   ├── verify/
│   │   └── gates.py                  # Phase 4 — Gates 1–5 (ported from Tamil Nadu; state-specific test inputs swapped)
│   ├── doe/
│   │   ├── generate_cases.py        # Phase 5 — LHS + boundary + baseline case specs (byte-identical to Tamil Nadu)
│   │   ├── run_batch.py             # Phase 5 — run every case through geometry gate + simulator, 1 row/case (n_lhs_per_pair=12)
│   │   └── split_cases.py           # Phase 5 — stratified 80/20 case-level train/holdout split
│   ├── surrogate/
│   │   ├── features.py             # Phase 6 — feature table (TN groups; column names remapped to RJ Objective 1 headers)
│   │   ├── train.py                # Phase 6 — Extra Trees per target + linear baseline + feasibility classifier
│   │   └── evaluate.py             # Phase 6 — hold-out MAE broken down by regime and by PCM
│   ├── optimize/
│   │   ├── search.py              # Phase 7 — 400 random candidates/pair -> geometry gate -> surrogate score -> top 5
│   │   └── select_deployable.py   # Phase 7 — re-run top candidates in real simulator + pre-declared selection rule
│   ├── robustness/
│   │   └── monte_carlo.py         # Phase 8 D2.7 — 120 MC draws/regime (weather+demand+mains); P(demand), P(temp-safe), P5-P95
│   └── handoff/
│       ├── recommendation_card.py # Phase 8 D2.8 — one card per regime (results/phase8_recommendation_cards.md)
│       └── obj3_contract.py       # Phase 8 D2.9 — obj3_environment_contract_rajasthan.json
├── data/
│   ├── objective1/                    # frozen Objective 1 outputs (see data/README.md)
│   ├── weather/                       # per-regime medoid weather (hourly + daily), clusters 0-2
│   └── demand/demand_profile_rajasthan.csv
├── docs/
│   ├── 00_MASTER_OVERVIEW.md          # this file
│   ├── 01_PHASE1_CONFIG_AND_STATE_SETUP.md
│   ├── 02_PHASE2_GEOMETRY_CONSTRAINTS.md
│   ├── 03_PHASE3_GREYBOX_SIMULATOR.md
│   ├── 04_PHASE4_VERIFICATION_GATES.md
│   ├── 05_PHASE5_DOE.md
│   ├── 06_PHASE6_SURROGATE.md
│   ├── 07_PHASE7_OPTIMIZATION.md
│   └── 08_PHASE8_ROBUSTNESS_HANDOFF.md
└── results/
    ├── phase0_climate_signature_check.txt          # Phase 0 output (PASSED, 3/3)
    ├── phase2_geometry_boundary_selftest.txt       # Phase 2 output (8/8 deterministic)
    ├── phase3_simulate_cluster*_*.json             # Phase 3 output — 6 smoke-run cases
    ├── phase4_simulator_verification_report.txt    # Phase 4 output (GO, 5/5 gates clean)
    ├── phase5_design_cases.parquet                 # Phase 5 output — 165 rows, 1 per simulation (+ .csv copy)
    ├── phase6_surrogate_metrics.csv / _error_by_group.csv / _models.pkl (gitignored) / _feature_cols.json
    ├── phase7_surrogate_top_candidates.csv         # Phase 7 — 60 surrogate-ranked candidates (proposal only)
    ├── phase7_optimized_designs.csv                # Phase 7 — all 60 re-run in the real simulator (PCM-comparison report)
    ├── phase7_deployable_design_per_regime.csv     # Phase 7 — final selection, 1 row per regime
    ├── phase8_robustness.csv / _robustness_draws.csv   # Phase 8 D2.7 — per-regime summary + every MC draw
    ├── phase8_recommendation_cards.md              # Phase 8 D2.8 — one card per regime
    ├── obj3_environment_contract_rajasthan.json    # Phase 8 D2.9 — Objective 3 handoff contract
    └── README.md                                   # what each file above contains + the inference drawn from it
```

`src/design/`, `src/simulation/` and `src/doe/generate_cases.py` are
**state-agnostic** — verified directly (`diff -rq` against
`objective2-tamilnadu/` returns nothing, see `02_…` / `03_…` / `05_…`).
`src/verify/gates.py`, `src/doe/{run_batch,split_cases}.py`,
`src/surrogate/{train,evaluate}.py` and
`src/optimize/{search,select_deployable}.py` are the TN implementations
with only their per-state inputs / output paths / one sampling argument
changed — logic, thresholds, hyper-parameters, the >15% large-error rule
and the pre-declared selection rule all unchanged. `src/surrogate/features.py`
keeps TN's four feature groups but remaps the climate/confidence column
names to Rajasthan's Objective 1 table headers (`06_…`). `src/robustness/`
and `src/handoff/` are new (no TN reference — TN stops at Phase 7), built
along the seams TN's `09_NEXT_STEPS.md` named: perturb only through
`run_case`'s existing knobs + a temporary `load_hourly_weather` wrap for
weather noise, so `run_case` stays byte-identical (`08_…`).

## Headline result: Phases 0–8 complete

```
Phase 0 (climate signature):  PASSED   3/3 regimes — genuinely hot-dry/high-clearness Rajasthan weather
Phase 2 (geometry self-test): PASS     8/8 boundary cases deterministic, matches Tamil Nadu line-for-line
Phase 3 (simulator smoke run): completes cleanly, energy residual ~3-16e-4% (well under 0.1% Gate-1 threshold)
Phase 4 (verification gates):  GO      5/5 gates clean — sim_v1_rajasthan; verifies one gate cleaner than Tamil Nadu
Phase 5 (reduced DOE):         165 cases — 111 valid / 54 infeasible-retained (all bounds_violation, 32.7% ≈ TN's 32.6%); 138 train / 27 holdout
Phase 6 (surrogate):          useful-energy hold-out R²=0.9998 (Extra Trees), past the >0.80 exit target; feasibility classifier 100%/100%
Phase 7 (optimize + confirm): plain tank wins all 3 regimes; surrogate-vs-sim mean error 0.025% (0/60 >15%); 0/45 PCM candidates pass temperature safety
Phase 8 (robustness+handoff): NOT robust — P(temp-safe) 0.33–0.51 across regimes (P(demand) 0.78–0.98 OK); 3 recommendation cards + obj3 contract written
```

Phase 4 detail: Gate 1 max residual 0.0016% (pass < 0.1%); Gate 2 10/10
limiting cases; Gate 3 **RT50 beats the plain tank** in Rajasthan (SF
55.08% vs 54.97%) — unlike TN's n-Octacosane, which didn't; Gate 4 solar
fraction 55.07% is **inside** the cited 54–84% band (TN's was just below).
Phase 5 detail: 9 regime×PCM pairs × (12 LHS + 6 boundary) + 3 no-PCM
baselines; 54 infeasible rows all `bounds_violation` from the
diameter/thickness bound interaction (`02_…`), kept with reason codes.
Full readouts in `04_…` / `05_…` and the matching `results/phase4_*` /
`results/phase5_*` files.

## The one finding carried forward — DOE scale, then robustness scale

Objective 1's rank-1 PCM for Rajasthan's Cluster 0 (**RT50**, `Tm = 48 °C`)
gets driven **past the 65 °C PCM material-stability limit for a large
fraction of the year, regardless of PCM loading**. Phase 3 smoke runs saw
896–3,142 violation sub-hours; the Phase 4 Gate 2 report records that the
**plain tank alone** (no PCM) reaches 68.6 °C in Cluster 0. **Phase 5
generalises it:** across all 111 valid DOE cases, `max_pcm_temp_C` spans
68.2–72.7 °C and **108 / 111 log `n_safety_violations > 0`** — every
regime, every one of the six shortlisted PCMs. This is a consequence of
Rajasthan's hot-dry, high-clearness solar input against the frozen 1.5 m²
collector / 50 L tank, not a capsule-sizing problem. Phase 6's surrogate
learned this dataset faithfully (it does not "fix" the physics — it
predicts the same overheating). **Phase 7 resolved it as designed:** with
the 65 °C PCM limit applied as a hard selection filter, **0 / 45 PCM
candidates** passed temperature safety in any regime (vs 15/15 plain-tank
candidates), so the deployable design for all three regimes is a **plain
(sensible-only) 50 L tank**. The best PCM geometry the search found beats
the best plain-tank geometry by only +0.07–0.15 % useful energy — two
orders of magnitude under the 5 % Pareto tolerance — and fails safety
anyway. This is the same negative result Phase 4 Gate 3 and Phase 5
reached, now confirmed by a 400-candidate-per-pair search with full
simulator re-confirmation. See `07_PHASE7_OPTIMIZATION.md`.

**Phase 8 pushed it one step further:** 120 Monte Carlo draws per regime
(weather + demand + mains variability) show the fallback **plain tank is
not robustly safe either** — P(temp-safe) = 0.33–0.51, i.e. it breaches
the 75 °C water scald limit in half to two-thirds of draws (P95 max water
83–87 °C), while still meeting the demand bar (P(demand) 0.78–0.98). So
the Objective 2 conclusion for Rajasthan is a **load-bearing negative**:
no shortlisted PCM is deployable, and the sensible-only fallback needs an
**active overheat bypass** to be safe. That bypass is an Objective 3
control action — hence the `obj3_environment_contract_rajasthan.json`
safety-shield block forces `bypass` at `T_water ≥ 72 °C`. The follow-up
(widen PCM bounds **and** add the bypass shield, or revisit the frozen
1.5 m² / 50 L sizing for hot-dry climates) is out of Objective 2's 40-hr
scope, named rather than silently dropped.

## Documents in this folder

- `01_PHASE1_CONFIG_AND_STATE_SETUP.md` — frozen configs, this state's input file, the Phase 0 sanity check
- `02_PHASE2_GEOMETRY_CONSTRAINTS.md` — geometry engine, Ergun hydraulics, bounds finding (identical engine to Tamil Nadu; the 12.9%-not-20% finding carries over unchanged since it depends only on the frozen shared bounds, not the state)
- `03_PHASE3_GREYBOX_SIMULATOR.md` — enthalpy model, energy balance, solver design, both bug fixes (inherited, already fixed in the shared engine), plus Rajasthan's own Cluster-0 smoke-run numbers
- `04_PHASE4_VERIFICATION_GATES.md` — the reduced 5-gate battery, ported from Tamil Nadu with state-specific test inputs; Rajasthan result: GO, 5/5 gates clean, `sim_v1_rajasthan`
- `05_PHASE5_DOE.md` — the reduced DOE: 165-case sampling plan, the 54 retained infeasible rows, the 80/20 split, and the DOE-scale safety-limit finding
- `06_PHASE6_SURROGATE.md` — the tree surrogate: 39 features (TN's groups, RJ column names), hold-out R²≈1.0 on the key targets, the honest linear-vs-tree comparison, the feature-name adaptation table
- `07_PHASE7_OPTIMIZATION.md` — one surrogate pass + 60-candidate simulator confirmation + the pre-declared selection rule; result: plain tank deployable in all 3 regimes, 0/45 PCM candidates pass safety
- `08_PHASE8_ROBUSTNESS_HANDOFF.md` — 120-draw Monte Carlo (NOT robust: P(temp-safe) 0.33–0.51), the D2.8 recommendation cards, the D2.9 Objective 3 contract
- `../results/README.md` — what every file in `results/` contains and what to infer from it, phase by phase

## What remains (not built yet)

- `src/plots/` — the Phase 2–7 justification figures. Copy from
  `objective2-tamilnadu/src/plots/`; wire `--stage plots` in `pipeline.py`
  (it currently raises a clear "not wired yet" `SystemExit`). This is the
  only piece of the Tamil Nadu tree not yet mirrored here.
- Named future work carried in the Objective 3 contract's
  `deferred_future_work`: the four-state comparison, an active-learning
  optimization loop / full NSGA-II, full-draw robustness with a real
  alternate weather series, and widened design bounds for 15–20 % PCM
  fraction (a Phase-0-gate decision, since the bounds are frozen).
