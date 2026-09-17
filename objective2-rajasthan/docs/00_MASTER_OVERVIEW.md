# 00 — Objective 2 Master Overview (Rajasthan, Phases 0–8 — COMPLETE)

## What this covers

Objective 2 turns Objective 1's output — climate regimes + a shortlisted
PCM per regime — into a **physical PCM-storage design and a validated
simulator** that Objective 3 can build a controller against, searching
all **four** parameters the objective statement names: capsule diameter,
**capsule arrangement**, capsule count, and flow rate
(`Objective2 Consolidated plan.md` §2). This set of docs covers the
phases implemented for **Rajasthan**, run as the pilot state for that
corrected 4-variable design vector.

| Phase | Deliverable | Status |
|---|---|---|
| Phase 0 | Frozen Objective 1 inputs + climate-signature sanity check (Bug-Fix 8) | COMPLETE — **PASSED, 3/3 regimes** |
| Phase 1 | D2.1 — frozen state config (`configs/states/rajasthan.yaml`) | COMPLETE |
| Phase 2 | D2.2 — geometry & constraint engine, 3-way arrangement-branched (`src/design/`) | COMPLETE |
| Phase 3 | D2.3 — grey-box enthalpy simulator (`src/simulation/`) | COMPLETE (smoke-tested, all 3 arrangements) |
| Phase 4 | Simulator verification, Gates 1–5 (`src/verify/gates.py`) | COMPLETE — **GO, 5/5 gates clean**, `sim_v2_rajasthan` |
| Phase 5 | D2.4 — arrangement-stratified DOE (`src/doe/`) | COMPLETE — **219 cases (128 valid / 91 infeasible-retained), 165/54 train/holdout** |
| Phase 6 | D2.5 — surrogate with arrangement one-hot feature (`src/surrogate/`) | COMPLETE — **useful-energy hold-out R² = 0.9997 (target > 0.80)**; arrangement importance near-zero (finding, not a defect) |
| Phase 7 | D2.6 — optimization spanning arrangement + simulator confirmation (`src/optimize/`) | COMPLETE — **60/60 candidates pass temperature safety; PCM wins all 3 regimes; regime 2 winner is `radial`** |
| Phase 8 | D2.7–D2.9 — robustness + recommendation cards + Obj3 handoff (`src/robustness/`, `src/handoff/`) | COMPLETE — **ROBUST in all 3 regimes (P(temp-safe) = 1.00); arrangement carried through cards + contract** |

## How this project relates to Tamil Nadu, and to the other two states

`src/simulation/` (all 8 submodels except one pass-through field in
`run_case.py`) remains **byte-identical** to `objective2-tamilnadu/` —
Phase 3 physics is genuinely state- and arrangement-agnostic.
`src/design/` (`schema.py`, `geometry.py`, `constraints.py`) **diverges**
from Tamil Nadu as of 2026-09-17: this project restored capsule
arrangement as a searched categorical variable
(`Objective2 Consolidated plan.md` §0.1), which Tamil Nadu, Assam, and
Uttarakhand have not yet received. `src/verify/gates.py`,
`src/doe/{generate_cases,run_batch,split_cases}.py`,
`src/surrogate/{features,train,evaluate}.py`, and
`src/optimize/{search,select_deployable}.py` are the Tamil Nadu
implementations with per-state inputs/paths swapped **and** the
arrangement-restoration changes applied (see each phase's own doc for
exactly what changed). `src/robustness/` and `src/handoff/` were this
project's own first-built Phase 8 implementation (Tamil Nadu adopted this
project's methodology for its own later Phase 8 pass); this project in
turn folded back one of Tamil Nadu's later improvements (`run_case()`'s
clean `weather_perturbation` keyword).

**Net effect:** Rajasthan is now the reference implementation for the
corrected 4-variable design vector — Tamil Nadu, Assam, and Uttarakhand
must each receive the identical `design_bounds_shared.yaml` edit and
Phase 2–8 rerun before any four-state comparison is valid (per
`00_MASTER_CHANGE_PLAN.md`'s cross-cutting rule and
`Objective2 Consolidated plan.md` §8's cross-state validity checks).

## Code map (what actually exists today)

```
objective2-rajasthan/
├── config.py                          # path constants
├── check_climate_signature.py         # Phase 0 — sanity check that the frozen weather is genuinely Rajasthan's
├── pipeline.py                        # CLI entry point — all 9 stages wired: geometry/simulate/verify/doe/surrogate/optimize/robustness/handoff/plots
├── configs/
│   ├── system_config_shared.yaml      # Phase 0A — frozen, byte-identical across all 4 states
│   ├── design_bounds_shared.yaml      # Phase 0A — frozen for TN/Assam/Uttarakhand; Rajasthan's copy diverges since 2026-09-17 (arrangement enum, count 8-37)
│   └── states/rajasthan.yaml          # Phase 1 — this state's inputs (regimes, PCM shortlist, mains temp, demand)
├── src/
│   ├── io_utils.py                    # shared config/data loaders (byte-identical to Tamil Nadu)
│   ├── design/
│   │   ├── schema.py                  # DesignVector — capsule_arrangement now required, no default
│   │   ├── geometry.py                # geometry + Ergun hydraulics — 3 arrangement-branched packing models (pack_staggered/pack_single_layer/pack_radial)
│   │   └── constraints.py             # valid/invalid + reason codes + 24-case (8x3-arrangement) boundary self-test + cross-arrangement sanity check
│   ├── simulation/
│   │   ├── capsule_enthalpy.py        # enthalpy model (byte-identical to Tamil Nadu)
│   │   ├── collector_model.py         # flat-plate collector (byte-identical to Tamil Nadu)
│   │   ├── heat_transfer.py           # UA_eff, Wakao-Kaguei (byte-identical to Tamil Nadu)
│   │   ├── hydraulic_model.py         # runtime pump-power wrapper (byte-identical to Tamil Nadu)
│   │   ├── demand_profile.py          # demand-curve model (byte-identical to Tamil Nadu)
│   │   ├── energy_balance.py          # energy accounting (byte-identical to Tamil Nadu)
│   │   ├── tank_model.py              # core timestep solver, incl. both Phase-4-discovered bug fixes + safety shield (byte-identical to Tamil Nadu)
│   │   └── run_case.py                # one-case orchestrator — now also logs the sampled arrangement (pass-through only)
│   ├── verify/
│   │   └── gates.py                  # Phase 4 — Gates 1–5, arrangement-aware since 2026-09-17 (ported from Tamil Nadu; state-specific test inputs swapped)
│   ├── doe/
│   │   ├── generate_cases.py        # Phase 5 — LHS + boundary + baseline case specs, arrangement-stratified since 2026-09-17
│   │   ├── run_batch.py             # Phase 5 — run every case through geometry gate + simulator, 1 row/case (n_lhs_per_pair=12), per-arrangement rejection reporting
│   │   └── split_cases.py           # Phase 5 — stratified 80/20 case-level train/holdout split, now by (regime, pcm, arrangement, valid)
│   ├── surrogate/
│   │   ├── features.py             # Phase 6 — feature table (TN groups; column names remapped to RJ Objective 1 headers; +3 arrangement one-hot columns)
│   │   ├── train.py                # Phase 6 — Extra Trees per target + linear baseline + feasibility classifier + arrangement-importance diagnostic
│   │   └── evaluate.py             # Phase 6 — hold-out MAE broken down by regime, by PCM, and by (regime, pcm, arrangement)
│   ├── optimize/
│   │   ├── search.py              # Phase 7 — 600 random candidates/pair (arrangement sampled uniformly) -> geometry gate -> surrogate score -> top 5
│   │   └── select_deployable.py   # Phase 7 — re-run top candidates in real simulator + pre-declared selection rule + arrangement_rationale
│   ├── robustness/
│   │   └── monte_carlo.py                 # Phase 8 D2.7 — run_all(): 120 MC draws/regime via run_case's weather_perturbation seam, using the winner's own arrangement; p_meets_*, p_temperature_violation, p_exceeds_max_safe_temp, P5-P95
│   ├── handoff/
│   │   ├── build_recommendation_cards.py  # Phase 8 D2.8 — run(): one card per regime incl. Selected arrangement + rationale (results/phase8_recommendation_cards.md)
│   │   └── build_obj3_contract.py         # Phase 8 D2.9 — run(): obj3_environment_contract_rajasthan.json, geometry block carries the real per-regime arrangement
│   └── plots/
│       └── make_plots.py          # Phase 2-8 justification figures (Plotly; ported from Tamil Nadu, flat paths + 3-regime grids)
├── data/
│   ├── objective1/                    # frozen Objective 1 outputs (see data/README.md)
│   ├── weather/                       # per-regime medoid weather (hourly + daily), clusters 0-2
│   └── demand/demand_profile_rajasthan.csv
├── docs/
│   ├── 00_MASTER_OVERVIEW.md          # this file
│   ├── 00_MASTER_CHANGE_PLAN.md       # the 2026-09-17 arrangement-restore change plan (Phase 1-8 prompts, now folded into each phase doc below)
│   ├── 01_PHASE1_CONFIG_AND_STATE_SETUP.md
│   ├── 02_PHASE2_GEOMETRY_CONSTRAINTS.md
│   ├── 03_PHASE3_GREYBOX_SIMULATOR.md
│   ├── 04_PHASE4_VERIFICATION_GATES.md
│   ├── 05_PHASE5_DOE.md
│   ├── 06_PHASE6_SURROGATE.md
│   ├── 07_PHASE7_OPTIMIZATION.md
│   ├── 08_PHASE8_ROBUSTNESS_HANDOFF.md
│   ├── 09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md   # every discovered divergence/finding, including §9 (arrangement freeze RESOLVED)
│   ├── OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md   # the Objective 3 hand-off brief (ported from Tamil Nadu)
│   └── plots/                        # 00_INDEX.md + per-phase figure walkthroughs (viva/report captions)
└── results/
    ├── phase0_climate_signature_check.txt          # Phase 0 output (PASSED, 3/3)
    ├── phase2_geometry_boundary_selftest.txt       # Phase 2 output — stale (8/8, pre-arrangement-restore); current 24/24 result lives in docs/02_… + console output only
    ├── phase3_simulate_cluster*_*.json             # Phase 3 output — 6 smoke-run cases, stale (pre-arrangement-restore); current 3-arrangement smoke run documented in docs/03_…
    ├── phase4_simulator_verification_report.txt    # Phase 4 output (GO, 5/5 gates clean, sim_v2_rajasthan) — current, regenerated 2026-09-17
    ├── phase5_design_cases.parquet                 # Phase 5 output — 219 rows, 1 per simulation (+ .csv copy), incl. `arrangement` column
    ├── phase6_surrogate_metrics.csv / _error_by_group.csv / _models.pkl (gitignored) / _feature_cols.json / _arrangement_importance.csv
    ├── phase7_surrogate_top_candidates.csv         # Phase 7 — 60 surrogate-ranked candidates (proposal only), incl. `arrangement`
    ├── phase7_optimized_designs.csv                # Phase 7 — all 60 re-run in the real simulator (PCM-comparison report)
    ├── phase7_deployable_design_per_regime.csv     # Phase 7 — final selection, 1 row per regime, incl. `arrangement` + `arrangement_rationale`
    ├── phase8_robustness.csv / _robustness_draws.csv   # Phase 8 D2.7 — per-regime summary + every MC draw
    ├── phase8_recommendation_cards.md              # Phase 8 D2.8 — one card per regime, incl. Selected arrangement + rationale
    ├── obj3_environment_contract_rajasthan.json    # Phase 8 D2.9 — Objective 3 handoff contract, incl. real per-regime arrangement + supersedes note
    ├── plots/static/*.png + plots/interactive/*.html (gitignored)   # Phase 2-8 figures (not regenerated for the arrangement restore — see docs/plots/00_INDEX.md)
    └── README.md                                   # what each file above contains (predates the 2026-09-17 arrangement restore — see its own pointer note)
```

## Headline result: Phases 0–8 complete, arrangement restored

```
Phase 0 (climate signature):  PASSED   3/3 regimes — genuinely hot-dry/high-clearness Rajasthan weather
Phase 2 (geometry self-test): PASS     24/24 boundary cases deterministic (8 cases x 3 arrangements); cross-arrangement dispatcher confirmed genuine
Phase 3 (simulator smoke run): completes cleanly for all 3 arrangements, residual 0.000636% identical across arrangements (well under 0.1% Gate-1 threshold)
Phase 4 (verification gates):  GO      5/5 gates clean — sim_v2_rajasthan
Phase 5 (arrangement-stratified DOE): 219 cases — 128 valid / 91 infeasible-retained (all bounds_violation); rejection rate comparable across arrangements (38.7-44.4%); 165 train / 54 holdout
Phase 6 (surrogate):          useful-energy hold-out R²=0.9997 (Extra Trees), past the >0.80 exit target; feasibility classifier 100%/100%; arrangement importance near-zero (0.00002-0.0024, a finding)
Phase 7 (optimize + confirm): PCM wins all 3 regimes; surrogate-vs-sim mean error 0.03% (0/60 >15%); 60/60 candidates pass temperature safety; regime 2 winner is radial (tied within noise)
Phase 8 (robustness+handoff): ROBUST in all 3 regimes — P(temp-safe) = 1.00 (P(demand) 0.85-0.98); 3 recommendation cards + obj3 contract written, all carrying real arrangement
```

**2026-09-17 — capsule arrangement restored as a searched variable**
(`Objective2 Consolidated plan.md`, `00_MASTER_CHANGE_PLAN.md`), Rajasthan
run as the pilot state. Previously `design_bounds_shared.yaml` froze
`capsule_arrangement` to `[staggered]` as part of the same "40-hr scope
cut" that froze `capsule_shape` to `[sphere]` — but arrangement is one of
the four parameters the objective statement explicitly names, so this was
a real scope gap. Implemented end-to-end through all 8 phases: Phase 2
gained three packing models (staggered/single-layer/radial) and a
per-arrangement max-reachable-fraction table; the shared count ceiling
widened 24→37 to make the 15-20% Chen-style PCM-loading levels
geometrically reachable (now 19.84% at the diameter ceiling, for all
three arrangements); Phase 5's DOE and Phase 6's surrogate both became
arrangement-stratified/arrangement-aware; Phase 7's search now samples
arrangement uniformly (600 candidates/pair, up from 400) and reports an
`arrangement_rationale` per winner; Phase 8's robustness, cards, and
Objective 3 contract all carry the real per-regime arrangement.

**Headline finding: arrangement has near-zero effect on every performance
target in this design-space region** (Phase 6's feature-importance
diagnostic, Phase 3's traced root cause — `void_fraction` only reaches the
hydraulics/pump-power path, itself negligible in this system's energy
balance). Two of three regimes' Phase 7 winners are "tied within noise"
across all three arrangements; only Regime 2 (savE® OM50) has a decisive
non-staggered winner (`radial`), and even that is a tie-break among
near-identical candidates, not a real energy advantage. This does not
change the deployability conclusion below — restoring arrangement as a
genuine search variable answers the "is arrangement doing anything here"
question with real evidence instead of an assumption, which is itself the
point of the correction, whichever way the answer comes out.

**The PCM-vs-plain-tank and safety-shield conclusions carry over
unchanged from the pre-arrangement-restore run** (see
`09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` §0/§6-§8 for that full history):
the rule-based overheat safety shield
(`system_config_shared.yaml: safety_shield.enabled`, adopted 2026-09-13)
remains the pipeline default, and `apply_selection_rule()`'s PCM-only
selection pool (2026-09-14) remains in place. Combined with the
arrangement restoration, all three Rajasthan regimes deploy a real PCM
design — RT50 (staggered) / Paraffin-HDPE PCM3 (staggered) / savE® OM50
(radial) — each with a small (0.10–0.17%) useful-energy edge over the
best plain-tank geometry found by the same search, and each robust at
Monte Carlo scale (P(temp-safe) = 1.00). Full detail:
`docs/07_PHASE7_OPTIMIZATION.md`, `docs/08_PHASE8_ROBUSTNESS_HANDOFF.md`.

Phase 4 detail: Gate 1 max residual 0.0016% (pass < 0.1%); Gate 2 12/12
limiting cases; Gate 3 all three arrangements land at 55.13% solar
fraction for the max-feasible PCM design, beating the plain tank's
54.97%; Gate 4 solar fraction 55.06% (staggered optimized-looking design)
is **inside** the cited 54–84% band. Phase 5 detail: 9 regime×PCM pairs ×
(12 LHS + 12 boundary, split across 3 arrangements) + 3 no-PCM baselines;
91 infeasible rows all `bounds_violation` from the diameter/thickness
bound interaction (`02_…`), kept with reason codes, regardless of
arrangement. Full readouts in `04_…` / `05_…` and the matching
`results/phase4_*` / `results/phase5_*` files.

## Documents in this folder

- `00_MASTER_CHANGE_PLAN.md` — the 2026-09-17 arrangement-restore change
  plan; its per-phase content is now folded into each `0N_PHASEN_*.md`
  doc below rather than living only here.
- `01_PHASE1_CONFIG_AND_STATE_SETUP.md` — frozen configs (arrangement
  enum + widened count bound since 2026-09-17), this state's input file,
  the Phase 0 sanity check
- `02_PHASE2_GEOMETRY_CONSTRAINTS.md` — the 3-way arrangement-branched
  geometry engine, Ergun hydraulics, the per-arrangement max-reachable-
  fraction table (identical across arrangements — a finding, not a bug)
- `03_PHASE3_GREYBOX_SIMULATOR.md` — enthalpy model, energy balance,
  solver design, both bug fixes, the arrangement pass-through finding
  (affects only pump power), Rajasthan's own Cluster-0 smoke-run numbers
- `04_PHASE4_VERIFICATION_GATES.md` — the reduced 5-gate battery, now
  arrangement-aware; Rajasthan result: GO, 5/5 gates clean, `sim_v2_rajasthan`
- `05_PHASE5_DOE.md` — the arrangement-stratified DOE: 219-case sampling
  plan, the 91 retained infeasible rows, the 80/20 split, per-arrangement
  rejection rates
- `06_PHASE6_SURROGATE.md` — the tree surrogate: 42 features (TN's groups,
  RJ column names, + 3 arrangement one-hot), hold-out R²≈1.0 on the key
  targets, the arrangement feature-importance diagnostic (near-zero — a
  finding), the honest linear-vs-tree comparison
- `07_PHASE7_OPTIMIZATION.md` — search spanning arrangement + 60-candidate
  simulator confirmation + the pre-declared (PCM-only) selection rule +
  `arrangement_rationale`; result: a shortlisted PCM deployable in all 3
  regimes, 60/60 candidates pass safety, regime 2's winner is `radial`
- `08_PHASE8_ROBUSTNESS_HANDOFF.md` — 120-draw Monte Carlo (ROBUST in all
  3 regimes: P(temp-safe) = 1.00), the D2.8 recommendation cards (now with
  arrangement + rationale), the D2.9 Objective 3 contract (now with real
  per-regime arrangement)
- `09_LIMITATIONS_AND_KNOWN_DIVERGENCES.md` — every discovered
  divergence/finding across this project's history, including §9's record
  of the arrangement freeze being resolved
- `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` — the Objective 3 hand-off brief:
  what the contract contains, what it means physically, concrete first
  steps, and what Objective 2 explicitly left unresolved
- `plots/00_INDEX.md` (+ per-phase files) — a walkthrough of the Phase
  2–8 figures generated before the arrangement restore: what each shows,
  what to infer, and the one-line viva/report caption. **Not regenerated**
  for the 2026-09-17 change — treat plot captions referencing "staggered"
  as describing the pre-restore geometry engine.
- `../results/README.md` — what every file in `results/` contains,
  written before the 2026-09-17 arrangement restore (see its own pointer
  note at the top)

## What remains (not built)

- **Nothing in the Tamil Nadu tree that Rajasthan lacks.** `src/plots/`
  is ported and `--stage plots` is wired; the full per-state pipeline is
  mirrored.
- **The other three states have not received the arrangement-restore
  change.** Tamil Nadu, Assam, and Uttarakhand's copies of
  `design_bounds_shared.yaml` and their own Phase 2–8 code still describe
  the staggered-only design vector — per `00_MASTER_CHANGE_PLAN.md`'s
  cross-cutting rule, no four-state comparison is valid until they receive
  the identical edit and rerun.
- Named future work carried in the Objective 3 contract's
  `deferred_future_work`: the four-state comparison, an active-learning
  optimization loop / full NSGA-II, full-draw robustness with a real
  alternate weather series, and experimental hardware validation
  (Objective 4 scope).
