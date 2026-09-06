# Objective 2 — Rajasthan

Per-state Objective 2 project for Rajasthan. Same layout, naming, and
frozen shared configs as `objective2-tamilnadu/` (the reference
implementation) — only the state-specific inputs differ (weather, regimes,
PCM shortlist, mains temperature, demand profile).

Start at [`docs/00_MASTER_OVERVIEW.md`](docs/00_MASTER_OVERVIEW.md) for
phase status (Phases 0–5 done — simulator verified **GO, 5/5 gates
clean** as `sim_v1_rajasthan`, and a **165-case DOE dataset** built;
Phase 6 onward not started yet) and the one finding carried forward
(every DOE case exceeds the 65 °C PCM safety limit under the frozen
collector sizing). [`results/README.md`](results/README.md) documents
every output file phase-by-phase, with the inference drawn from it.

## Layout

```
objective2-rajasthan/
├── config.py                         # shared paths (mirror of objective2-tamilnadu/config.py)
├── pipeline.py                       # CLI entry point (geometry/simulate/verify/doe wired; surrogate/optimize/plots arrive with their phase)
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
│   └── doe/                          # Phase 5 reduced DOE (generate_cases byte-identical to Tamil Nadu)
│       ├── generate_cases.py  run_batch.py  split_cases.py
├── docs/
│   ├── 00_MASTER_OVERVIEW.md          # phase status, code map, the safety-limit finding
│   ├── 01_PHASE1_CONFIG_AND_STATE_SETUP.md
│   ├── 02_PHASE2_GEOMETRY_CONSTRAINTS.md
│   ├── 03_PHASE3_GREYBOX_SIMULATOR.md
│   ├── 04_PHASE4_VERIFICATION_GATES.md
│   └── 05_PHASE5_DOE.md
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
python pipeline.py --state rajasthan --stage simulate --cluster 0 \
    --pcm "RT50" --diameter 0.08 --count 24 --flow 0.025
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
