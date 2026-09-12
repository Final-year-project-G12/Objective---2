# Objective 2 — Rajasthan

Per-state Objective 2 project for Rajasthan. Same layout, naming, and
frozen shared configs as `objective2-tamilnadu/` (the reference
implementation) — only the state-specific inputs differ (weather, regimes,
PCM shortlist, mains temperature, demand profile).

Start at [`docs/00_MASTER_OVERVIEW.md`](docs/00_MASTER_OVERVIEW.md) for
phase status (**Phases 0–8 complete** — the full Objective 2 ~40-hour
deliverable set: simulator verified **GO** as `sim_v1_rajasthan`, a
165-case DOE, a tree surrogate at useful-energy hold-out R² = 0.9998, a
simulator-confirmed optimization pass, and a 120-draw robustness pass +
recommendation cards + Objective 3 contract). **Headline result:** under
the frozen config the deployable design in all three regimes is a plain
sensible tank (the Objective 1 PCM shortlist gains < 0.15 % useful energy
and 0/45 PCM candidates clear the 65 °C limit) — and Phase 8 shows that
plain tank is **not robustly safe** (P(temp-safe) 0.45–0.57), so an
active overheat bypass is handed to Objective 3 as a requirement (see
[`docs/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md`](docs/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md)).
[`results/README.md`](results/README.md) documents every output file
phase-by-phase, with the inference drawn from it.

## Layout

```
objective2-rajasthan/
├── config.py                         # shared paths (mirror of objective2-tamilnadu/config.py)
├── pipeline.py                       # CLI entry point — all 9 stages wired (geometry/simulate/verify/doe/surrogate/optimize/robustness/handoff/plots)
├── check_climate_signature.py        # Phase 0 sanity check (Bug-Fix 8)
├── configs/
│   ├── system_config_shared.yaml     # FROZEN — byte-identical for all 4 states, do not edit
│   ├── design_bounds_shared.yaml     # FROZEN — byte-identical for all 4 states, do not edit
│   └── states/rajasthan.yaml         # Phase 1 output — the only state-varying config
├── src/
│   ├── io_utils.py                   # frozen-config / state-config / weather / PCM loaders
│   ├── design/                       # Phase 2 geometry & constraint engine (byte-identical to Tamil Nadu)
│   │   ├── schema.py  geometry.py  constraints.py
│   ├── simulation/                   # Phase 3 grey-box enthalpy simulator (byte-identical to Tamil Nadu)
│   │   ├── capsule_enthalpy.py  collector_model.py  heat_transfer.py  hydraulic_model.py
│   │   ├── demand_profile.py  energy_balance.py  tank_model.py  run_case.py
│   ├── verify/                       # Phase 4 gate battery (ported from Tamil Nadu; state-specific test inputs swapped)
│   │   └── gates.py
│   ├── doe/                          # Phase 5 reduced DOE (generate_cases byte-identical to Tamil Nadu)
│   │   ├── generate_cases.py  run_batch.py  split_cases.py
│   ├── surrogate/                    # Phase 6 tree surrogate (train/evaluate ported from Tamil Nadu; features remapped to RJ Obj1 headers)
│   │   ├── features.py  train.py  evaluate.py
│   ├── optimize/                     # Phase 7 surrogate search + simulator confirmation + selection rule (ported from Tamil Nadu)
│   │   ├── search.py  select_deployable.py
│   ├── robustness/                   # Phase 8 D2.7 — Monte Carlo robustness (built here first; TN's later pass adopted this methodology)
│   │   └── monte_carlo.py            # run_all() — naming matches objective2-tamilnadu/src/robustness/
│   ├── handoff/                      # Phase 8 D2.8/D2.9 — recommendation cards + Objective 3 contract
│   │   ├── build_recommendation_cards.py  build_obj3_contract.py   # run() — naming matches objective2-tamilnadu/src/handoff/
│   └── plots/                        # Phase 2-8 justification figures (ported from Tamil Nadu; flat paths, 3-regime grids)
│       └── make_plots.py
├── docs/
│   ├── 00_MASTER_OVERVIEW.md          # phase status, code map, the safety-limit finding
│   ├── 01_PHASE1_CONFIG_AND_STATE_SETUP.md
│   ├── 02_PHASE2_GEOMETRY_CONSTRAINTS.md
│   ├── 03_PHASE3_GREYBOX_SIMULATOR.md
│   ├── 04_PHASE4_VERIFICATION_GATES.md
│   ├── 05_PHASE5_DOE.md
│   ├── 06_PHASE6_SURROGATE.md
│   ├── 07_PHASE7_OPTIMIZATION.md
│   ├── 08_PHASE8_ROBUSTNESS_HANDOFF.md
│   ├── OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md
│   └── plots/                        # 00_INDEX.md + 7 per-phase figure walkthroughs
├── data/
│   ├── objective1/                   # frozen Objective 1 outputs (cluster_profiles, mcdm_topk, pcm_database, ...)
│   ├── weather/                      # per-regime daily + hourly weather (clusters 0-2)
│   └── demand/demand_profile_rajasthan.csv   # canonical 300 L/day draw profile
└── results/                          # everything this project writes; results/README.md documents each
                                       # output file's contents + the inference drawn from it
```

The full Objective 1 file inventory, schema-alignment notes, and climate
regime medoids are documented in
[`../data/objective1/rajasthan/README.md`](../data/objective1/rajasthan/README.md).

## Climate regimes (Level-A GMM, K_FINAL = 3)

| cluster_id | medoid | members | PCM shortlist (Objective 1 MCDM Top-3) |
|---|---|---|---|
| 0 | RJP_0132 | 114 | RT50, RT45HC, Lauric acid (C12) |
| 1 | RJP_0202 | 103 | savE® OM50, Paraffin/HDPE PCM3, Paraffin/HDPE PCM6 |
| 2 | RJP_0055 | 103 | savE® OM50, Paraffin/HDPE PCM3, Paraffin/HDPE PCM6 |

Mains water temperature: 18–30 °C (framework doc, Rajasthan row).
Demand: 300 L/day (state-invariant, matches Objective 1's `L_required` assumption).

## How to run

### Phase 0 — climate-signature sanity check (Bug-Fix 8)

```
python check_climate_signature.py
```

Confirms the frozen weather under `data/weather/` genuinely looks like
Rajasthan (hot, dry, high-clearness) and not another state's, that each
daily file is internally clean (no duplicate days, no calendar gaps), and
that medoid ids / regime sizes match Objective 1. Writes
`results/phase0_climate_signature_check.txt`. Exit code 0 =
PASSED, 1 = STOP and recheck Objective 1. Current status: **PASSED (3/3
regimes)**. See [`results/README.md`](results/README.md) for what each
line means and the inference drawn from it.

### Phase 1 — nothing to execute

`configs/system_config_shared.yaml`, `configs/design_bounds_shared.yaml`
and `configs/states/rajasthan.yaml` are static, already-frozen files — open
and read them, don't run them. See
[`docs/01_PHASE1_CONFIG_AND_STATE_SETUP.md`](docs/01_PHASE1_CONFIG_AND_STATE_SETUP.md)
for how every field in `rajasthan.yaml` was read off Objective 1's frozen
outputs.

### Phase 2 — geometry & constraint boundary self-test

```
python pipeline.py --state rajasthan --stage geometry
```

Runs 8 boundary cases (min/max diameter × min/max count, flow above/below
limits, an oversized capsule) twice each and checks the valid/reason
output is byte-identical. Expected: all 8 `deterministic=True`, exit 0.
The `src/design/` engine is byte-identical to `objective2-tamilnadu/src/design/`
(Phase 2 is state-agnostic) and the run matches Tamil Nadu's line-for-line.
Saved to [`results/phase2_geometry_boundary_selftest.txt`](results/phase2_geometry_boundary_selftest.txt).
See [`docs/02_PHASE2_GEOMETRY_CONSTRAINTS.md`](docs/02_PHASE2_GEOMETRY_CONSTRAINTS.md),
including the finding that the max reachable PCM loading is **12.9%** (not
the 15–20% seen in the literature) within the frozen bounds.

### Phase 3 — grey-box enthalpy simulator, one full-year case

```
python pipeline.py --state rajasthan --stage simulate --cluster 0 --pcm "RT50" --diameter 0.08 --count 24 --flow 0.025
python pipeline.py --state rajasthan --stage simulate --cluster 1 --no-pcm
```

Runs one calendar year of hourly medoid weather with 5-minute internal
sub-stepping and prints the metrics dict (useful energy, solar fraction,
unmet energy, pump energy, delivery-temp hours, max water/PCM temp, safety
violations, `residual_pct_of_collector`). `src/simulation/` is
byte-identical to `objective2-tamilnadu/src/simulation/` (Phase 3 is
state-agnostic); only the weather / demand / PCM / mains inputs differ.
Energy-balance residual on the Cluster 0 smoke run is ~6e-4 % — well under
the 0.1% Gate-1 threshold (Bug-Fixes 1–2 intact). Six smoke-run cases
(3 plain-tank baselines + 3 RT50 geometries) are saved as JSON under
`results/phase3_simulate_*.json` — see
[`results/README.md`](results/README.md) for the full table and the
Cluster-0 PCM safety-limit finding. See
[`docs/03_PHASE3_GREYBOX_SIMULATOR.md`](docs/03_PHASE3_GREYBOX_SIMULATOR.md)
for the simulator methodology.

### Phase 4 — reduced verification gate battery (Gates 1–5)

```
python pipeline.py --state rajasthan --stage verify
```

Runs the framework doc's 5-gate battery end-to-end (~2–3 min, ~40
full-year simulations): energy conservation, limiting cases, baseline
comparison, published-benchmark calibration, sensitivity. `src/verify/gates.py`
is ported from `objective2-tamilnadu/src/verify/gates.py` — same gate
logic/thresholds/verdicts — with only the state-specific test inputs
swapped (3 clusters not 5; PCMs `RT50` / `savE® OM50`), plus one
informational non-gating Gate 2 line recording Cluster 0's plain-tank
overheating. Writes `results/phase4_simulator_verification_report.txt`;
exit 0 = GO, 1 = NO-GO. **Current status: GO, 5/5 gates clean** (verifies
one gate cleaner than Tamil Nadu — RT50's 48 °C melt point beats the plain
tank here, and the solar fraction lands inside the cited benchmark band).
See [`docs/04_PHASE4_VERIFICATION_GATES.md`](docs/04_PHASE4_VERIFICATION_GATES.md).

### Phase 5 — reduced DOE (generate + simulate + 80/20 split)

```
python pipeline.py --state rajasthan --stage doe
```

Generates 165 design cases (9 regime×PCM pairs × [12 LHS + 6 boundary] +
3 no-PCM baselines), runs each through the Phase 2 geometry gate and, if
valid, a full Phase 3 simulated year, then adds a stratified 80/20
`split` column. `src/doe/generate_cases.py` is byte-identical to
`objective2-tamilnadu/`; `run_batch.py`/`split_cases.py` differ only in
the `sim_v1_rajasthan` tag, the flat output path, and `n_lhs_per_pair=12`
(TN uses 8 — RJ has 3 regimes not 5, so more draws per pair to hit the
framework's 150–300 target). Runtime ~13 min. Writes
`results/phase5_design_cases.parquet` (+ `.csv`) — one row per simulation
with the design vector, `geom_*` outputs, performance metrics,
`valid`/`reason`, and `split`. **Result: 111 valid / 54
infeasible-retained (all `bounds_violation`, 32.7% ≈ TN's 32.6%); 138
train / 27 holdout.** Every valid case exceeds the 65 °C PCM safety limit
— see [`docs/05_PHASE5_DOE.md`](docs/05_PHASE5_DOE.md).

### Phase 6 — tree surrogate (train + hold-out eval)

```
python pipeline.py --state rajasthan --stage surrogate
```

Trains one `ExtraTreesRegressor` (300 trees) per performance target from
the 93 valid `train` rows of the Phase 5 parquet, each against a
`LinearRegression` baseline on the same split, plus an
`ExtraTreesClassifier` for feasibility. `train.py`/`evaluate.py` are
ported from `objective2-tamilnadu/` (same model family, hyper-params,
split logic); `features.py` keeps TN's four feature groups but remaps the
climate/confidence column names to Rajasthan's Objective 1 table headers
(39 features vs TN's 36). Runtime ~10 s. Writes
`results/phase6_surrogate_metrics.csv`,
`results/phase6_surrogate_error_by_group.csv`,
`results/phase6_surrogate_models.pkl` (git-ignored),
`results/phase6_surrogate_feature_cols.json`. **Result: useful-energy
hold-out R² = 0.9998 (exit target > 0.80); solar_fraction & unmet_energy
R² ≥ 0.9996; feasibility classifier 100% accuracy / 100% infeasible
recall.** Linear ties or slightly beats the tree on three low-variance
targets — reported honestly. The surrogate is a proposal ranker, not the
oracle (Bug-Fix 5). See [`docs/06_PHASE6_SURROGATE.md`](docs/06_PHASE6_SURROGATE.md).

### Phase 7 — one optimization pass + simulator confirmation

```
python pipeline.py --state rajasthan --stage optimize
```

Searches 400 random design vectors per regime×PCM pair (12 pairs),
filters each through the real Phase 2 geometry gate, scores survivors
with the Phase 6 surrogate, takes the top 5 per pair (**60 candidates**),
**re-runs every one in the real simulator** (non-negotiable, Bug-Fix 5),
then applies the pre-declared selection rule (`pareto_tolerance_pct = 5%`:
reject temperature-unsafe → within 5 % of best useful energy → min pump
energy → min PCM mass → min capsule count → max margin).
`src/optimize/{search,select_deployable}.py` are ported from
`objective2-tamilnadu/` unchanged except the flat `results/phase7_*`
paths. Runtime ~6 min. Writes `results/phase7_surrogate_top_candidates.csv`,
`results/phase7_optimized_designs.csv`,
`results/phase7_deployable_design_per_regime.csv`. **Result: plain
(sensible-only) tank is the deployable design in all 3 regimes**;
surrogate-vs-simulator mean error 0.025 % (0/60 > 15 %); only 15/60
candidates pass temperature safety and **all 15 are plain-tank** (0/45 PCM
candidates pass). See [`docs/07_PHASE7_OPTIMIZATION.md`](docs/07_PHASE7_OPTIMIZATION.md).

### Phase 8 — light robustness + recommendation cards + Objective 3 handoff

```
python pipeline.py --state rajasthan --stage robustness --mc-draws 120
python pipeline.py --state rajasthan --stage handoff
```

`robustness` runs **120 Monte Carlo draws per regime** (360 total) on the
Phase 7 deployable designs — perturbing weather (GHI + T_amb noise via
`run_case`'s `weather_perturbation` keyword), demand volume (±20 %),
demand timing (±30 min) and mains temp (±2 °C). `handoff` then writes one
recommendation card per regime (D2.8) and the Objective 3 environment
contract (D2.9). `src/robustness/` + `src/handoff/` are this project's own
Phase 8 build; Tamil Nadu's later Phase 8 pass adopted this methodology
(two-level noise, fixed thresholds, 120 draws) and, in the other
direction, contributed the `weather_perturbation` seam and finer-grained
metrics folded back in here — see
[`docs/08_PHASE8_ROBUSTNESS_HANDOFF.md`](docs/08_PHASE8_ROBUSTNESS_HANDOFF.md),
"Alignment with the Tamil Nadu implementation." File/function naming
(`build_recommendation_cards.py` / `build_obj3_contract.py`, entry point
`run(state)`; `monte_carlo.py`'s `run_all(state, n_draws)`) and the
two-stage `robustness`/`handoff` split now match
`objective2-tamilnadu/pipeline.py` exactly. Runtime ~18 min for
`robustness`, seconds for `handoff`. Writes
`results/phase8_robustness.csv` (+ `_draws.csv`),
`results/phase8_recommendation_cards.md`,
`results/obj3_environment_contract_rajasthan.json`. **Result: NOT robust
— P(temp-safe) = 0.45–0.57 across the three regimes** (P(meet annual
demand) 0.80–0.99 clears its bar). Even the plain tank breaches the
75 °C water scald limit in roughly half of draws under realistic
variability, so the contract's `safety_shield` forces a `bypass` action
at `T_water ≥ 72 °C` — an Objective 3 requirement, not an option. Exit
check met: 3 cards + 3 regimes in the contract. Full Objective 3 hand-off
brief: [`docs/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md`](docs/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md).

### Plots — Phase 2–8 justification figures

```
python pipeline.py --state rajasthan --stage plots
```

Regenerates all **17 figures** from the current phase outputs (re-runs
one Phase 3 sample case + the Phase 4 gate cases; reads Phases 5–8 files),
saved twice under `results/plots/`: `static/*.png` (committed) and
`interactive/*.html` (self-contained, git-ignored). `src/plots/make_plots.py`
is ported from `objective2-tamilnadu/` — figure code unchanged, only the
flat `results/phaseN_*` paths, 3-regime subplot grids and Rajasthan's PCM
names differ; the two Phase 8 figures (robustness probabilities,
useful-energy P5–P95 intervals) were added this pass. Needs `plotly` +
`kaleido` (installed). Runtime ~1–2 min. Each figure's "what it shows /
what to infer / viva caption" walkthrough is in
[`docs/plots/`](docs/plots/00_INDEX.md).


```powershell

python check_climate_signature.py                          # Phase 0 sanity check
python pipeline.py --state rajasthan --stage geometry       # Phase 2
python pipeline.py --state rajasthan --stage simulate --cluster 0 --pcm "RT50" --diameter 0.08 --count 24 --flow 0.025   # Phase 3 (example case)
python pipeline.py --state rajasthan --stage verify         # Phase 4 (~2-3 min)
python pipeline.py --state rajasthan --stage doe             # Phase 5 (~13 min)
python pipeline.py --state rajasthan --stage surrogate       # Phase 6 (~10 s)
python pipeline.py --state rajasthan --stage optimize        # Phase 7 (~6 min)
python pipeline.py --state rajasthan --stage robustness --mc-draws 120   # Phase 8a (~18 min)
python pipeline.py --state rajasthan --stage handoff          # Phase 8b (seconds)
python pipeline.py --state rajasthan --stage plots            # Phase 2-8 figures (~1-2 min, needs plotly+kaleido)
```