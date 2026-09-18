# How to Run — Phases 1–8 (Tamil Nadu) — Objective 2 complete, 2026-09-17

## Do you need MATLAB or any other simulator? No.

Everything in this project — the grey-box physics simulator (Phases 2–4),
the DOE (Phase 5), the machine-learning surrogate (Phase 6), and the
optimization/search (Phase 7) — is plain Python, runs in this same
environment, and needs nothing installed outside what's already here.
There is no MATLAB code, no `.m` file, no Simulink model, and no call out
to any external solver anywhere in this project.

## Prerequisites

Already satisfied in this project (verified working with Python 3.14):
`pandas`, `numpy`, `pyyaml`, `scipy`, `scikit-learn`, `pyarrow`. No
packages need to be installed for Phases 1–8. (`matplotlib`/`plotly`/
`kaleido` are only needed for the `plots` stage, which is a separate,
not-yet-updated follow-up — see the note at the bottom.)

You must run these from the `objective2_design_optimization/` folder
(where `config.py` and `pipeline.py` live).

## 0. Phase 0 — Objective 1 data refresh (2026-09-17)

```
python build_input_package.py
python build_regime_weather.py
python build_demand_profile.py
```
Only re-run these if `tamilnadu_pipeline` (Objective 1) is re-run again.
The 2026-09-17 run of these three scripts pulled a refreshed Objective 1
pipeline: GMM regime count **K=5→K=3**, real elevation (was a flat 150 m
placeholder), a rewritten MCDM/feasibility engine. See
`docs_objective2/16_OBJECTIVE1_DATA_REFRESH.md`.

## 1. Phase 1 — state config + arrangement restored in shared bounds

`configs/system_config_shared.yaml`, `configs/design_bounds_shared.yaml`,
and `configs/states/tamilnadu.yaml` are static, frozen files — open and
read them, don't run them directly. Two things changed 2026-09-17:

1. **`design_bounds_shared.yaml` gained a 3-way categorical
   `capsule_arrangement` bound** (`single-layer`/`staggered`/`radial` —
   was frozen to staggered-only). `capsule_count.max` stays 37 (widened
   from 24 in an earlier revision, doc 13 — unaffected by this change).
2. **`configs/states/tamilnadu.yaml` was rebuilt from scratch** (K=3
   regimes, not patched from the old K=5 file), then the existing
   Tm-retargeting + MCDM-reranking scripts were re-run against the fresh
   data (a one-line schema fix was needed first — see doc 16):

```
python -m src.design.retarget_tm tamilnadu
python -m src.design.mcdm_reranking tamilnadu --apply
```

Both already done for Tamil Nadu as of 2026-09-17. Re-running either
requires a Phase 2–8 re-run afterward (Phase 0 gate) — also already done.

## 2. Phase 2 — geometry & constraint boundary self-test

```
python pipeline.py --state tamilnadu --stage geometry
```
Expected: **24 boundary cases** (8 cases × 3 arrangements, up from 8 when
arrangement was frozen), each `deterministic=True`, no crash, plus a
cross-arrangement sanity check (same design under all 3 arrangements must
produce genuinely different `void_fraction`/`pressure_drop_pa` — confirms
the packing dispatcher is actually branching) and a max-reachable-fraction
table (single-layer/staggered: 37 capsules, 19.84%; radial: 21 capsules,
11.26% — a real, expected asymmetry). Runtime: <1 second.

## 3. Phase 3 — run one simulation case

```
python pipeline.py --state tamilnadu --stage simulate \
    --cluster 0 --pcm "n-Hexacosane (C26)" \
    --diameter 0.042 --count 16 --arrangement radial --flow 0.0112
```
(the current regime-0 deployable design.) Prints a JSON metrics dict
(useful energy, solar fraction, unmet energy, pump energy, PCM mass, max
temperatures, safety-violation count, melt fraction stats, energy residual
%, and now `arrangement`). Runtime: ~1–4 seconds.

Flags:
- `--cluster {0,1,2}` — Tamil Nadu's **3** GMM climate regimes (was 0-4).
- `--pcm "<name>"` — any name from `data/objective1/pcm_database_tamilnadu.csv`
  (or one of the per-cluster shortlist names in `configs/states/tamilnadu.yaml`).
- `--arrangement {single-layer,staggered,radial}` — **required as of
  2026-09-17** for internal callers (the CLI defaults to `staggered` for
  convenience if omitted).
- `--no-pcm` — run the plain-tank baseline instead (ignores `--pcm`).
- `--diameter` (m, 0.02–0.08), `--count` (int, 8–37), `--flow` (kg/s, 0.010–0.050).

To use this from Python directly instead of the CLI:
```python
from src.design.schema import DesignVector
from src.simulation.run_case import run_case

design = DesignVector(capsule_diameter_m=0.042, n_capsule=16,
                       flow_rate_kg_s=0.0112, capsule_arrangement="radial")
out = run_case("tamilnadu", cluster_id=0, pcm_name="n-Hexacosane (C26)", design=design)
print(out["metrics"])
```

## 4. Phase 4 — full verification gate battery

```
python pipeline.py --state tamilnadu --stage verify
```
Runs all 5 gates (arrangement-aware — Gates 1–3 now cover all three
arrangements), prints a full readout, and writes
`results/tamilnadu/simulator_verification_report.txt`. Runtime: ~1 minute.
Expected: **5/5 gates PASS**, max residual 0.000303%, Gate 4 genuinely
inside the cited 54-84% benchmark band (59.03%). `Go/No-Go: GO`, simulator
released as `sim_v2_tamilnadu`.

## 5. Phase 5 — generate and run the DOE batch

```
python pipeline.py --state tamilnadu --stage doe
```
Generates **219 cases** (arrangement-stratified: 12 LHS + 12 boundary per
regime×PCM pair × 3 arrangements, 9 pairs, + 3 no-PCM baselines), runs each
through the Phase 2 geometry gate and (if valid) the Phase 3 simulator,
then applies the case-level train/holdout split. Runtime: **~30 minutes**
(219 cases × ~8s average — the slowest stage; other stages are fast).
Writes `results/tamilnadu/design_cases.parquet` (+ `.csv`) with `split`
and `arrangement` columns.

Expected result: **108 valid, 111 rejected**. Rejection rate is NOT
uniform across arrangements — report it per-arrangement, not pooled:
radial 66.7% (48/72, all `passage_blocked` on top of the shared
`bounds_violation` rate — radial's lower max-reachable-fraction ceiling
from Phase 2 showing up directly here), single-layer 44.4% (32/72),
staggered 41.3% (31/75). 27/30 regime×PCM×arrangement combos have ≥1
holdout case.

## 6. Phase 6 — train and evaluate the surrogate

```
python pipeline.py --state tamilnadu --stage surrogate
```
Requires Phase 5's `design_cases.parquet`. Trains an ExtraTreesRegressor
per performance target (now on **28 features**, including a 3-column
arrangement one-hot) + a LinearRegression baseline + an ExtraTreesClassifier
for feasibility, reports hold-out error broken down by regime/PCM/
**arrangement**, and prints an arrangement feature-importance diagnostic.
Runtime: a few seconds. Writes `surrogate_metrics.csv`,
`surrogate_error_by_group.csv` (now ~200 rows incl. the
regime×pcm×arrangement breakdown), `surrogate/models.pkl`.

Expected result (81 train / 27 holdout rows): `useful_energy_kWh` R²=1.000
(clears the >0.80 exit bar comfortably despite the small dataset);
`pcm_mass_kg`/`pump_energy_kWh` favor the linear baseline (expected —
both are near-linear functions of the design vector); feasibility
classifier accuracy/infeasible-recall = 1.0. Arrangement combined feature
importance is <0.01 for every target — reported honestly as "minimal
effect" (arrangement mainly gates feasibility, which the separate
classifier learns perfectly, not the continuous thermal targets).

## 7. Phase 7 — optimization pass + simulator confirmation

```
python pipeline.py --state tamilnadu --stage optimize
```
Requires Phase 6's trained models. Searches **600** candidates per
regime×PCM pair (raised from 400 — candidates now split ~3 ways by
arrangement before the geometry gate, so 600 keeps each arrangement's
post-gate budget close to the old per-arrangement equivalent) with the
surrogate, samples arrangement uniformly, re-runs the top 20 per pair
(`--top-n-per-pair`, default 20; 12 regime×PCM(+no-PCM) groups × 20 = 240
total) in the **real** simulator, computes an `arrangement_rationale` per
winner, and applies the unchanged PCM-only, safety-first selection rule.
Runtime: **~15-25 minutes** (dominated by 240 real simulator re-runs).
Writes `surrogate_top_candidates.csv`, `optimized_designs.csv`,
`deployable_design_per_regime.csv` (now with `arrangement` +
`arrangement_rationale` columns).

Expected result: mean surrogate-vs-simulator error **0.05%** (0/240 large
errors) — **radial arrangement won in all 3 regimes**, honestly qualified:
regimes 0/1 "tied within noise" against single-layer (margin inside the
0.05% noise band), regime 2 had no other arrangement confirmed to compare
against at all. See `docs_objective2/tamilnadu_phase_docs/
07_PROMPT_PHASE7_OPTIMIZE_TAMILNADU.md` for the full table. 2 of 3 regimes
have **negative** nominal constraint margin (-6.93°C, -6.05°C) — flagged
in `deployment_note`, not hidden; regime 1 is barely positive (+0.02°C).

## 7b. Phase 6b — multi-fidelity surrogate augmentation (optional, currently broken)

```
python pipeline.py --state tamilnadu --stage multifidelity
```
**Not part of the 2026-09-17 batch — will currently raise `TypeError`.**
`src/surrogate/multifidelity.py` still constructs `DesignVector(...)`
without the now-required `capsule_arrangement` field. Fix that one call
site and re-run against the refreshed DOE before using this stage. See
`docs_objective2/11_MULTIFIDELITY_SURROGATE.md`.

## 8. Phase 8 — robustness analysis

```
python pipeline.py --state tamilnadu --stage robustness
```
Requires Phase 7's `deployable_design_per_regime.csv`. Runs 120 Monte
Carlo draws (PCM latent heat ±10%, two-level weather noise [annual
scale/offset drawn from a real 10-year historical ensemble + per-hour
jitter], demand ±20%/±30min, mains temperature ±2°C) per each of the
**3** selected designs — **360 full-year simulator re-runs total**, never
the surrogate. Runtime: **~20-30 minutes**. Writes
`robustness_results.csv` (360 rows), `robustness_summary.csv` (3 rows).

Expected result: P(meets delivery temperature) = 100% for all 3 regimes;
P(meets annual demand) = 100%/77%/95%; **P(temperature-safe) = 0%/18%/0%**
— every regime fails the 95% safety bar, directly following from Phase
7's negative/marginal nominal margins. Reported plainly, not hidden — see
`docs_objective2/tamilnadu_phase_docs/08_PROMPT_PHASE8_HANDOFF_TAMILNADU.md`.

## 9. Phase 8 — recommendation cards + Objective 3 hand-off contract

```
python pipeline.py --state tamilnadu --stage handoff
```
Requires Phase 8's robustness summary. Runtime: a few seconds. Writes
`recommendation_cards.md` (one card per regime, now with "Selected
arrangement" + "Arrangement rationale" lines) and
`obj3_environment_contract_tamilnadu.json` (`contract_version:
"obj3_contract_v2.0_2026-09-17"`, `validated_simulator_version:
"sim_v2_tamilnadu"`, each regime's design block carries
`capsule_arrangement` + `arrangement_rationale`, plus a top-level
`supersession_note` explaining what changed from any pre-2026-09-17
contract).

See `docs_objective2/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` for how
Objective 3 should consume the contract file (its own content is
superseded/flagged — re-read the warning box at its top).

## 10. Plots — updated for this batch (2026-09-17)

```
python pipeline.py --state tamilnadu --stage plots
```
`src/plots/make_plots.py` was repaired and regenerated against the
K=3/arrangement-searched results: every `DesignVector(...)` call now
passes `capsule_arrangement`, stale cluster IDs (3/4, which no longer
exist) and stale PCM names were fixed, hardcoded case counts (215/145/100)
are now computed dynamically, and `phase2_validity_map` was redesigned as
a 3-panel per-arrangement comparison (a single map would now be
misleading, since the valid region genuinely differs by arrangement — the
regenerated plot visually confirms Phase 2's radial-ceiling finding).
`phase8_robustness_probabilities` also gained a third bar,
**P(temperature-safe)**, with a 95% threshold line — previously this
chart showed delivery/demand reliability only; temperature safety is the
headline Phase 8 finding (0%/18%/0%, all three regimes fail the bar) and
is now visible in the chart itself, not only the summary CSV/text.

Old, pre-refresh plot files and the stale `results/tamilnadu/
multifidelity_*` data that had silently fed the Phase 6b plot (from a
Sep 7/12 run, long superseded) were deleted before regenerating, not left
mixed in. Phase 6b's plot now correctly **skips** (prints "skipped — run
--stage multifidelity first") since that stage itself is still not part
of this batch (see §7b) — it is no longer silently rendered from stale
data.

Runtime: ~1-2 minutes for kaleido's PNG export (18 figures... 17, since
Phase 6b is skipped). `docs_objective2/plots/*.md` (per-figure
descriptions) still describe the OLD plot set's specific numbers/findings
and have not been rewritten — the images themselves are current, but
don't cite the *prose* in those docs for current numbers yet.

## Adding a second state later (Rajasthan / Assam / Uttarakhand)

Nothing under `src/` needs to change — it is state-agnostic. You need:
1. That state's `data/objective1/`, `data/weather/`, `data/demand/` built
   the same way Tamil Nadu's were.
2. A new `configs/states/<state>.yaml` following the same structure as
   `configs/states/tamilnadu.yaml`.
3. Confirm that state's copy of `design_bounds_shared.yaml` has the same
   arrangement-restoration edit applied (see
   `docs_objective2/17_ARRANGEMENT_RESTORATION.md`'s cross-cutting rule —
   no state may diverge from the shared config independently).
4. Then run every stage in order for that state: `geometry` → `verify` →
   `doe` → `surrogate` → `optimize` → `robustness` → `handoff`, each with
   `--state <state>` in place of `tamilnadu`.
5. Check whether that state's `Tm_target_C` needs the same retargeting
   treatment Tamil Nadu needed (docs 12–15) — not assumed, checked.

**Do not rebuild the four-state comparison table** until all four states
have this identical arrangement-restoration + (where applicable) data-
refresh batch applied — per `obj2_revised`'s cross-state validity checks
(identical shared-config hash, identical simulator version, identical
selection rule).

Do **not** edit `configs/system_config_shared.yaml` or
`configs/design_bounds_shared.yaml` per state — they are frozen for all
four states by design.
