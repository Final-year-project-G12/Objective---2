# How to Run — Phases 1–8 (Uttarakhand) — Objective 2 complete

## Do you need MATLAB or any other simulator? No.

Everything in this project — the grey-box physics simulator (Phases 2–4),
the DOE (Phase 5), the machine-learning surrogate (Phase 6), and the
optimization/search (Phase 7) — is plain Python, runs in this same
environment, and needs nothing installed outside what's already here.
There is no MATLAB code, no `.m` file, no Simulink model, and no call out
to any external solver anywhere in this project.

## Prerequisites

Already satisfied in this project (verified working with Python 3.14):
`pandas`, `numpy`, `pyyaml`, `scipy`, `scikit-learn`, `pyarrow`,
`matplotlib`. No packages need to be installed for Phases 1–7.

You must run these from the `objective2-uttarakhand/` folder
(where `config.py` and `pipeline.py` live).

## 0. Phase 0 — building the data (run this once from your local machine)

These pre-existing scripts produce everything under `data/`:
```
python build_input_package.py
python build_regime_weather.py
python build_demand_profile.py
```
`build_input_package.py` reads from `era5-uttarakhand/data/processed/`
(your local Objective 1 output), copies the required CSVs into
`data/objective1/`, and writes `manifest.json` with SHA-256 hashes.
`build_regime_weather.py` requires your raw NASA POWER hourly cache
(`era5-uttarakhand/data/raw/nasapower/`). Only re-run if Uttarakhand's
Objective 1 pipeline is re-run (e.g. new PCM database, different K) —
then re-run Phase 2–4 too.

See `NEEDS_LOCAL_DATA.md` for the full checklist of what must exist locally
before running the pipeline stages below.

## 1. Phase 1 — nothing to execute directly (unless retargeting/widening, see below)

`configs/system_config_shared.yaml`, `configs/design_bounds_shared.yaml`
and `configs/states/uttarakhand.yaml` are static, frozen files — open and
read them, don't run them under normal use. Every Phase 2/3/4 command
below implicitly exercises the Phase 1 loader (`src/io_utils.py`).

**Two methodology revisions were applied on top of the originally-frozen
files (2026-09-14), ported from Tamil Nadu — see `12_TM_TARGET_RETARGETING.md`
and `13_DESIGN_BOUNDS_WIDENING.md`:**
```
python -m src.design.retarget_tm uttarakhand   # rewrites configs/states/uttarakhand.yaml in place
```
plus a manual widening of `capsule_count.max` (24→37) in
`configs/design_bounds_shared.yaml`. Both are already applied in this
repo; re-run `retarget_tm` only if Objective 1's PCM database or climate
signature changes again (it will re-derive targets from a fresh
simulator run and overwrite the config).

## 2. Phase 2 — geometry & constraint boundary self-test

```
python pipeline.py --state uttarakhand --stage geometry
```
Expected: 8 boundary cases printed, each `deterministic=True`, no crash.
Runtime: <1 second.

## 3. Phase 3 — run one simulation case

```
python pipeline.py --state uttarakhand --stage simulate \
    --cluster 0 --pcm "RT42" \
    --diameter 0.08 --count 19 --flow 0.030
```
Prints a JSON metrics dict (useful energy, solar fraction, unmet energy,
pump energy, PCM mass, max temperatures, safety-violation count, melt
fraction stats, energy residual %). Runtime: ~1–4 seconds.

Flags:
- `--cluster {0,1,2,3,4}` — Uttarakhand's 5 GMM climate regimes.
- `--pcm "<name>"` — any name from `data/objective1/pcm_database_uttarakhand.csv`
  (or one of the per-cluster shortlist names in `configs/states/uttarakhand.yaml`,
  post Tm-target retargeting, doc 12). Key PCMs: "RT42" (rank-1 in regimes
  0, 2, 4), "RT44HC" (rank-1 in regime 3), "savE® OM42" (rank-2/3 in
  regimes 0, 2, 3, 4). Regime 1 (coldest, smallest-sample) has no
  retargeted survivor and keeps its old shortlist: "PureTemp 53"
  (rank-1), "n-Hexacosane (C26)", "Myristic acid (C14)".
- `--no-pcm` — run the plain-tank baseline instead (ignores `--pcm`).
- `--diameter` (m, 0.02–0.08), `--count` (int, 8–37, widened from 8–24 — doc 13),
  `--flow` (kg/s, 0.010–0.050).

To use this from Python directly instead of the CLI:
```python
from src.design.schema import DesignVector
from src.simulation.run_case import run_case

design = DesignVector(capsule_diameter_m=0.08, n_capsule=19, flow_rate_kg_s=0.030)
out = run_case("uttarakhand", cluster_id=0, pcm_name="RT42", design=design)
print(out["metrics"])
```

## 4. Phase 4 — full verification gate battery

```
python pipeline.py --state uttarakhand --stage verify
```
Runs all 5 gates (~20 simulation cases total), prints a full readout, and
writes `results/uttarakhand/simulator_verification_report.txt`. Runtime:
~30–60 seconds. Expected final line: `Go/No-Go: GO`.

## 5. Phase 5 — generate and run the DOE batch

```
python pipeline.py --state uttarakhand --stage doe
```
Generates 215 cases (LHS + boundary + no-PCM baselines across all 5
regimes × 3 shortlisted PCMs), runs each through the Phase 2 geometry gate
and (if valid) the Phase 3 simulator, then applies the case-level
train/holdout split. Runtime: **~7 minutes** (215 cases × ~1.9s each) —
this is the slowest stage; the others are fast. Writes:
- `results/uttarakhand/design_cases.parquet` (+ `.csv`), with a `split`
  column (`train`/`holdout`) added at the end.

Expected result: 142 valid, 73 rejected (all `bounds_violation` — see
`docs_objective2/06_PHASE5_DOE.md` for why that's expected).

## 6. Phase 6 — train and evaluate the surrogate

```
python pipeline.py --state uttarakhand --stage surrogate
```
Requires Phase 5's `design_cases.parquet` to exist. Trains an
ExtraTreesRegressor per performance target + a LinearRegression baseline
+ an ExtraTreesClassifier for feasibility, then reports hold-out error
broken down by regime and by PCM. Runtime: a few seconds. Writes:
- `results/uttarakhand/surrogate_metrics.csv`
- `results/uttarakhand/surrogate_error_by_group.csv`
- `results/uttarakhand/surrogate/models.pkl` (the trained models, reused by Phase 7)

Expected result: R² > 0.9998 on every regression target; feasibility
classifier accuracy/infeasible-recall = 1.0 (see
`docs_objective2/07_PHASE6_SURROGATE.md` for why the feasibility result is
this clean).

## 7. Phase 7 — optimization pass + simulator confirmation

```
python pipeline.py --state uttarakhand --stage optimize
```
Requires Phase 6's trained models. Searches 400 candidates per regime×PCM
pair with the surrogate, re-runs the top **20** per pair (400 total) in the
**real** simulator, and applies the scope-corrected, PCM-only selection
rule (plain tank excluded from winning — doc in `08_PHASE7_OPTIMIZATION.md`).
Runtime: ~15-20 minutes (dominated by the 400 real simulator re-runs —
widened from 100 to match Tamil Nadu's more thorough search). Writes:
- `results/uttarakhand/surrogate_top_candidates.csv` (surrogate-only, intermediate)
- `results/uttarakhand/optimized_designs.csv` (every simulator-confirmed candidate, plain tank included for reference)
- `results/uttarakhand/deployable_design_per_regime.csv` (the final PCM-only selection, one row per regime)

Expected result: mean surrogate-vs-simulator error ~0.03% (0/400
large errors); every regime selects a genuine PCM design (RT42 in regimes
0/2/3, savE® OM42 in regime 4, Myristic acid (C14) in regime 1 — its old,
climate-mismatched fallback), each beating its own regime's best plain-tank
candidate by 0.01–0.14% useful energy. **4 of 5 regimes' selected designs
exceed the 65°C PCM safety limit at nominal conditions** (only regime 1 is
safe, and only because its PCM barely activates) — see
`docs_objective2/08_PHASE7_OPTIMIZATION.md` for the full table.

## 7b. Phase 6b — multi-fidelity surrogate augmentation (optional, extra evidence)

```
python pipeline.py --state uttarakhand --stage multifidelity
```

Requires Phase 5's `design_cases.parquet` (does not require Phase 6/7 to
have run). Re-runs the same 215 DOE case specs at a cheap LOW-fidelity
simulator setting (fixed timestep, no adaptive sub-stepping —
`src/simulation/tank_model.py`'s `fidelity="low"`), measures the speedup
vs. a fresh order-randomized same-process runtime benchmark, then runs a
sample-efficiency experiment. Runtime: ~10 minutes (both fidelities re-run
across 215 cases, plus the fair-timing benchmark). Writes:
- `results/uttarakhand/design_cases_lowfid.parquet` (+ `.csv`)
- `results/uttarakhand/multifidelity_runtime_benchmark.csv`
- `results/uttarakhand/multifidelity_speedup_report.json`
- `results/uttarakhand/multifidelity_sample_efficiency.csv`

See `docs_objective2/11_MULTIFIDELITY_SURROGATE.md` for methodology and
results: **2.02× speedup** (up from 1.58× pre-widening) — this time
genuinely larger than Tamil Nadu's 1.53×, because the widened design
space (doc 13) now includes designs with more PCM mass (up to 16.8%
volume fraction) that cycle more actively and trigger adaptive
sub-stepping more often in high fidelity.

## 8. Phase 8 — robustness analysis

```
python pipeline.py --state uttarakhand --stage robustness
```
Requires Phase 7's `deployable_design_per_regime.csv`. Runs 120 Monte
Carlo draws (PCM latent heat ±10%, two-level weather noise [annual
scale/offset from real 10-year ensemble + per-hour jitter], demand
±20%/±30min, mains temperature ±2°C) per each of the 5 selected designs —
**600 full-year simulator re-runs total**, never the surrogate. Runtime:
**~25-40 minutes** (the slowest single stage) — safe to run unattended. Writes:
- `results/uttarakhand/robustness_results.csv` (600 rows, every draw)
- `results/uttarakhand/robustness_summary.csv` (5 rows, per-regime probabilities/intervals)

Expected result: P(meets delivery temperature, SF≥45%) ranges 0.0–29.2%;
P(meets annual demand, SF≥50%) = **0.0% for all 5 regimes** (Uttarakhand's
nominal solar fractions, 28.1–40.9%, are structurally below the 50% bar —
a genuine climate finding, not comparable to Tamil Nadu's/Rajasthan's
much warmer-mains-water results, see doc 10); P(temperature-safe) is
**0.0%** in regimes 0, 2 and 3 (nominal margin already ≤ −5°C — Monte
Carlo uncertainty cannot rescue an already-unsafe nominal design), 7.5%
in regime 4, and **100.0%** in regime 1 (Myristic acid (C14) — safe only
because it's too climate-mismatched to activate) — see
`docs_objective2/10_PHASE8_ROBUSTNESS_HANDOFF.md`.

## 9. Phase 8 — recommendation cards + Objective 3 hand-off contract

```
python pipeline.py --state uttarakhand --stage handoff
```
Requires Phase 8's robustness summary (falls back gracefully with
"Not yet run" placeholders if robustness hasn't been run yet). Runtime:
a few seconds. Writes:
- `results/uttarakhand/recommendation_cards.md` — one card per regime
- `results/uttarakhand/obj3_environment_contract_uttarakhand.json` — the frozen Objective 3 hand-off package

See `docs_objective2/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` for how
Objective 3 should consume the contract file.

## 10. Plots — justification figures for Phases 2-8

```
python pipeline.py --state uttarakhand --stage plots
```
Requires Phases 5-7 to have already been run. Phase 8 plots are included
automatically if `robustness_summary.csv` exists. Needs `plotly` and
`kaleido` (`pip install kaleido` if not already installed). Runtime:
~1-2 minutes. Writes figures to:
- `results/uttarakhand/plots/interactive/<name>.html` — **open this one** —
  self-contained, fully interactive, works offline in any browser.
- `results/uttarakhand/plots/static/<name>.png` — flat image for reports/slides.

**Troubleshooting — "Couldn't close or kill browser subprocess" / the
plots stage fails partway through**: `kaleido` (the PNG-export engine)
runs a headless Chrome instance per image and can leave orphaned
`chrome.exe` processes behind if a run is interrupted. Fix:
```powershell
Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force
python pipeline.py --state uttarakhand --stage plots
```
(This stops **every** `chrome.exe` process on the machine, including any
real browser windows open elsewhere — close/save those first.)

## Running a different state (Tamil Nadu / Rajasthan / Assam)

Nothing under `src/` needs to change — it is state-agnostic. You need:
1. That state's `data/objective1/`, `data/weather/`, `data/demand/` built
   via their own `build_input_package.py` / `build_regime_weather.py` /
   `build_demand_profile.py` runs (with `STATE` changed at the top of each).
2. A `configs/states/<state>.yaml` following the same structure.
3. Then run every stage in order for that state: `geometry` → `verify`
   → `doe` → `surrogate` → `optimize` → `robustness` → `handoff` → `plots`,
   each with `--state <state>` in place of `uttarakhand`.

Do **not** edit `configs/system_config_shared.yaml` or
`configs/design_bounds_shared.yaml` per state — they are frozen for all
four states by design.
