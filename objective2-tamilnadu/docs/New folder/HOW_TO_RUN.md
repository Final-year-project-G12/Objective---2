# How to Run — Phases 1–7 (Tamil Nadu)

## Do you need MATLAB or any other simulator? No.

Everything in this project — the grey-box physics simulator (Phases 2–4),
the DOE (Phase 5), the machine-learning surrogate (Phase 6), and the
optimization/search (Phase 7) — is plain Python, runs in this same
environment, and needs nothing installed outside what's already here.
There is no MATLAB code, no `.m` file, no Simulink model, and no call out
to any external solver anywhere in this project. If a future phase (e.g.
higher-fidelity CFD sensitivity checks, mentioned as optional in the
framework doc) ever needed one, it would be a deliberate, separate
addition — not something silently required by what's built so far.

## Prerequisites

Already satisfied in this project (verified working with Python 3.14):
`pandas`, `numpy`, `pyyaml`, `scipy`, `scikit-learn`, `pyarrow`,
`matplotlib`. No packages need to be installed for Phases 1–7.

You must run these from the `objective2_design_optimization/` folder
(where `config.py` and `pipeline.py` live).

## 0. Phase 0 — already done, don't re-run unless Objective 1 changes

These pre-existing scripts already produced everything under `data/`:
```
python build_input_package.py
python build_regime_weather.py
python build_demand_profile.py
```
Only re-run these if Tamil Nadu's Objective 1 pipeline is re-run (e.g. new
PCM database, different K, elevation fix) — then re-run Phase 2–4 too.

## 1. Phase 1 — nothing to execute directly

`configs/system_config_shared.yaml`, `configs/design_bounds_shared.yaml`
and `configs/states/tamilnadu.yaml` are static, already-frozen files — open
and read them, don't run them. Every Phase 2/3/4 command below implicitly
exercises the Phase 1 loader (`src/io_utils.py`).

## 2. Phase 2 — geometry & constraint boundary self-test

```
python pipeline.py --state tamilnadu --stage geometry
```
Expected: 8 boundary cases printed, each `deterministic=True`, no crash.
Runtime: <1 second.

## 3. Phase 3 — run one simulation case

```
python pipeline.py --state tamilnadu --stage simulate \
    --cluster 0 --pcm "n-Octacosane (C28)" \
    --diameter 0.08 --count 19 --flow 0.030
```
Prints a JSON metrics dict (useful energy, solar fraction, unmet energy,
pump energy, PCM mass, max temperatures, safety-violation count, melt
fraction stats, energy residual %). Runtime: ~1–4 seconds.

Flags:
- `--cluster {0,1,2,3,4}` — Tamil Nadu's 5 GMM climate regimes.
- `--pcm "<name>"` — any name from `data/objective1/pcm_database_tamilnadu.csv`
  (or one of the per-cluster shortlist names in `configs/states/tamilnadu.yaml`).
- `--no-pcm` — run the plain-tank baseline instead (ignores `--pcm`).
- `--diameter` (m, 0.02–0.08), `--count` (int, 8–24), `--flow` (kg/s, 0.010–0.050).

To use this from Python directly instead of the CLI:
```python
from src.design.schema import DesignVector
from src.simulation.run_case import run_case

design = DesignVector(capsule_diameter_m=0.08, n_capsule=19, flow_rate_kg_s=0.030)
out = run_case("tamilnadu", cluster_id=0, pcm_name="n-Octacosane (C28)", design=design)
print(out["metrics"])
```

## 4. Phase 4 — full verification gate battery

```
python pipeline.py --state tamilnadu --stage verify
```
Runs all 5 gates (~20 simulation cases total), prints a full readout, and
writes `results/tamilnadu/simulator_verification_report.txt`. Runtime:
~30–60 seconds. Expected final line: `Go/No-Go: GO`.

## 5. Phase 5 — generate and run the DOE batch

```
python pipeline.py --state tamilnadu --stage doe
```
Generates 215 cases (LHS + boundary + no-PCM baselines across all 5
regimes × 3 shortlisted PCMs), runs each through the Phase 2 geometry gate
and (if valid) the Phase 3 simulator, then applies the case-level
train/holdout split. Runtime: **~7 minutes** (215 cases × ~1.9s each) —
this is the slowest stage; the others are fast. Writes:
- `results/tamilnadu/design_cases.parquet` (+ `.csv`), with a `split`
  column (`train`/`holdout`) added at the end.

Expected result: 145 valid, 70 rejected (all `bounds_violation` — see
`docs_objective2/06_PHASE5_DOE.md` for why that's expected, not a bug).

## 6. Phase 6 — train and evaluate the surrogate

```
python pipeline.py --state tamilnadu --stage surrogate
```
Requires Phase 5's `design_cases.parquet` to exist. Trains an
ExtraTreesRegressor per performance target + a LinearRegression baseline
+ an ExtraTreesClassifier for feasibility, then reports hold-out error
broken down by regime and by PCM. Runtime: a few seconds. Writes:
- `results/tamilnadu/surrogate_metrics.csv`
- `results/tamilnadu/surrogate_error_by_group.csv`
- `results/tamilnadu/surrogate/models.pkl` (the trained models, reused by Phase 7)

Expected result: R² > 0.98 on every regression target; feasibility
classifier accuracy/infeasible-recall = 1.0 (see
`docs_objective2/07_PHASE6_SURROGATE.md` for why the feasibility result is
this clean, and one target — pump energy — where the linear baseline
actually ties the tree model).

## 7. Phase 7 — optimization pass + simulator confirmation

```
python pipeline.py --state tamilnadu --stage optimize
```
Requires Phase 6's trained models. Searches 400 candidates per regime×PCM
pair with the surrogate, re-runs the top 5 per pair (100 total) in the
**real** simulator, and applies the pre-declared selection rule. Runtime:
~3-5 minutes (dominated by the 100 real simulator re-runs). Writes:
- `results/tamilnadu/surrogate_top_candidates.csv` (surrogate-only, intermediate)
- `results/tamilnadu/optimized_designs.csv` (every simulator-confirmed candidate — the PCM-comparison report)
- `results/tamilnadu/deployable_design_per_regime.csv` (the final selection, one row per regime)

Expected result: mean surrogate-vs-simulator error ≈0.02% (0/100 large
errors); plain tank selected in 4/5 regimes, n-Octacosane in regime 4 —
see `docs_objective2/08_PHASE7_OPTIMIZATION.md` for the full explanation
of why, and `09_NEXT_STEPS.md` for the decision this implies before Phase 8.

## Adding a second state later (Rajasthan / Assam / Uttarakhand)

Nothing under `src/` needs to change — it is state-agnostic. You need:
1. That state's `data/objective1/`, `data/weather/`, `data/demand/` built
   the same way Tamil Nadu's were (`build_input_package.py` /
   `build_regime_weather.py` / `build_demand_profile.py`, with `STATE`
   changed at the top of each).
2. A new `configs/states/<state>.yaml` following the same structure as
   `configs/states/tamilnadu.yaml` (regimes, `Tm_target_C`,
   `T_mains_est_C`, weather paths, PCM shortlist, demand profile path).
3. Then: `python pipeline.py --state <state> --stage verify`.

Do **not** edit `configs/system_config_shared.yaml` or
`configs/design_bounds_shared.yaml` per state — they are frozen for all
four states by design (see `01_PHASE1_CONFIG_AND_STATE_SETUP.md`).
