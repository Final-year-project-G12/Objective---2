# 00 — Objective 2 Master Overview (Rajasthan, Phases 0–5)

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
| Phase 6 | D2.5 — surrogate (`src/surrogate/`) | **NOT STARTED** |
| Phase 7 | D2.6 — optimization + simulator confirmation (`src/optimize/`) | **NOT STARTED** |

Rajasthan is **behind** Tamil Nadu (the reference implementation, which
has completed Phases 1–7). `src/design/`, `src/simulation/`, `src/verify/`
and `src/doe/` here are **ported from** Tamil Nadu's — `design/`,
`simulation/` and `doe/generate_cases.py` are byte-identical (state-agnostic
by the framework doc); `verify/gates.py` swaps only its per-state test
inputs (3 clusters not 5; Rajasthan's PCM shortlist; one extra
informational Cluster-0 check); `doe/run_batch.py` + `doe/split_cases.py`
differ only in the `sim_v1_rajasthan` tag, the flat `results/phaseN_*`
output path, and `n_lhs_per_pair=12` (not TN's 8 — see `05_…`). Only
Phase 6 onward (`surrogate/`, `optimize/`, `plots/`) still needs to be
copied over. See the bottom of this file for what that means concretely.

## Code map (what actually exists today)

```
objective2-rajasthan/
├── config.py                          # path constants
├── check_climate_signature.py         # Phase 0 — sanity check that the frozen weather is genuinely Rajasthan's
├── pipeline.py                        # CLI entry point — geometry/simulate/verify/doe wired; surrogate/optimize/plots raise "not wired yet"
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
│   └── doe/
│       ├── generate_cases.py        # Phase 5 — LHS + boundary + baseline case specs (byte-identical to Tamil Nadu)
│       ├── run_batch.py             # Phase 5 — run every case through geometry gate + simulator, 1 row/case (n_lhs_per_pair=12)
│       └── split_cases.py           # Phase 5 — stratified 80/20 case-level train/holdout split
├── data/
│   ├── objective1/                    # frozen Objective 1 outputs (see data/README.md)
│   ├── weather/                       # per-regime medoid weather (hourly + daily), clusters 0-2
│   └── demand/demand_profile_rajasthan.csv
├── docs/
│   ├── 00_MASTER_OVERVIEW.md          # this file
│   ├── 01_PHASE1_CONFIG_AND_STATE_SETUP.md
│   ├── 02_PHASE2_GEOMETRY_CONSTRAINTS.md
│   ├── 03_PHASE3_GREYBOX_SIMULATOR.md
│   └── 04_PHASE4_VERIFICATION_GATES.md
└── results/
    ├── phase0_climate_signature_check.txt          # Phase 0 output (PASSED, 3/3)
    ├── phase2_geometry_boundary_selftest.txt       # Phase 2 output (8/8 deterministic)
    ├── phase3_simulate_cluster0_RT50_maxload.json  # Phase 3 output — max-loading case, cluster 0
    ├── phase3_simulate_cluster0_RT50_mid_flow010.json
    ├── phase3_simulate_cluster0_RT50_mid_flow050.json
    ├── phase3_simulate_cluster0_baseline_noPCM.json
    ├── phase3_simulate_cluster1_baseline_noPCM.json
    ├── phase3_simulate_cluster2_baseline_noPCM.json
    ├── phase4_simulator_verification_report.txt    # Phase 4 output (GO, 5/5 gates clean)
    ├── phase5_design_cases.parquet                 # Phase 5 output — 165 rows, 1 per simulation (+ .csv copy)
    └── README.md                                   # what each file above contains + the inference drawn from it
```

`src/design/`, `src/simulation/` and `src/doe/generate_cases.py` are
**state-agnostic** — verified directly (`diff -rq` against
`objective2-tamilnadu/` returns nothing, see `02_…` / `03_…` / `05_…`).
`src/verify/gates.py` and `src/doe/{run_batch,split_cases}.py` are the TN
implementations with only their per-state inputs / output paths / one
sampling argument changed — logic, thresholds and verdict rules unchanged;
see `04_…` / `05_…`.

## Headline result so far: Phases 0–5 done, simulator verified GO, DOE dataset built

```
Phase 0 (climate signature):  PASSED   3/3 regimes — genuinely hot-dry/high-clearness Rajasthan weather
Phase 2 (geometry self-test): PASS     8/8 boundary cases deterministic, matches Tamil Nadu line-for-line
Phase 3 (simulator smoke run): completes cleanly, energy residual ~3-16e-4% (well under 0.1% Gate-1 threshold)
Phase 4 (verification gates):  GO      5/5 gates clean — sim_v1_rajasthan; verifies one gate cleaner than Tamil Nadu
Phase 5 (reduced DOE):         165 cases — 111 valid / 54 infeasible-retained (all bounds_violation, 32.7% ≈ TN's 32.6%); 138 train / 27 holdout
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

## The one finding carried forward — now quantified at DOE scale

Objective 1's rank-1 PCM for Rajasthan's Cluster 0 (**RT50**, `Tm = 48 °C`)
gets driven **past the 65 °C PCM material-stability limit for a large
fraction of the year, regardless of PCM loading**. Phase 3 smoke runs saw
896–3,142 violation sub-hours; the Phase 4 Gate 2 report records that the
**plain tank alone** (no PCM) reaches 68.6 °C in Cluster 0. **Phase 5
generalises it:** across all 111 valid DOE cases, `max_pcm_temp_C` spans
68.2–72.7 °C and **108 / 111 log `n_safety_violations > 0`** — every
regime, every one of the six shortlisted PCMs. This is a consequence of
Rajasthan's hot-dry, high-clearness solar input against the frozen 1.5 m²
collector / 50 L tank, not a capsule-sizing problem. **Phase 6–7 must
carry this as a hard selection constraint** (or the frozen collector
sizing needs a hot-dry-state revisit) — in the same spirit as Tamil
Nadu's 15%/20%-not-reachable finding. Do not silently raise the safety
limit or drop the violation count. (It failed no Phase 4 gate: Gate 2 is
a simulator-robustness battery; the 65 °C limit is a Phase 7
design-selection constraint.)

## Documents in this folder

- `01_PHASE1_CONFIG_AND_STATE_SETUP.md` — frozen configs, this state's input file, the Phase 0 sanity check
- `02_PHASE2_GEOMETRY_CONSTRAINTS.md` — geometry engine, Ergun hydraulics, bounds finding (identical engine to Tamil Nadu; the 12.9%-not-20% finding carries over unchanged since it depends only on the frozen shared bounds, not the state)
- `03_PHASE3_GREYBOX_SIMULATOR.md` — enthalpy model, energy balance, solver design, both bug fixes (inherited, already fixed in the shared engine), plus Rajasthan's own Cluster-0 smoke-run numbers
- `04_PHASE4_VERIFICATION_GATES.md` — the reduced 5-gate battery, ported from Tamil Nadu with state-specific test inputs; Rajasthan result: GO, 5/5 gates clean, `sim_v1_rajasthan`
- `05_PHASE5_DOE.md` — the reduced DOE: 165-case sampling plan, the 54 retained infeasible rows, the 80/20 split, and the DOE-scale safety-limit finding
- `../results/README.md` — what every file in `results/` contains and what to infer from it, phase by phase

## What Phase 6 onward will need (not built yet)

Per the framework doc and the Tamil Nadu reference implementation:

- `src/surrogate/`, `src/optimize/`, `src/plots/` — copy unchanged;
  nothing in these is state-specific beyond the `--state` flag. The
  surrogate trains from `results/phase5_design_cases.parquet` (its
  `split` column), so it must read that flat path, not TN's
  `results/<state>/design_cases.parquet`.
- A `pipeline.py` dispatch update to wire `surrogate`/`optimize`/`plots`
  the way `objective2-tamilnadu/pipeline.py` already does (Rajasthan's
  `pipeline.py` currently wires `geometry`/`simulate`/`verify`/`doe` and
  raises a clear "not wired yet" `SystemExit` for the remaining three
  stages, rather than silently no-op-ing).
