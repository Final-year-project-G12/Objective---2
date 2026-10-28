# Objective 2 - Uttarakhand: current pipeline (2026-10-28)

**Status: current.** Port of the Rajasthan current chain (v3, PCM fraction cap 30 %) to Uttarakhand with Objective 1's new K = 4 regimes.
`docs/PROGRESS.md` is the log of the port and every gate. The legacy K = 5 chain (UTC-indexed demand, single-node tank) was removed in the
cleanup of 2026-10-28, as in Rajasthan; it is in git history only. The full report is `Objective2_Uttarakhand_Report_v3.docx` (PDF beside it).

Scope: this folder only. Fixed and not optimised: 50 L tank, collector area, the Uttarakhand demand profile, the O1 PCM top-3, **delivery target 50 C**
(`configs/system_config_shared.yaml`). Held-out test years 2024-2025, used once. Nothing is committed to git by this work.

## Contents

| File | What it covers |
|---|---|
| [`01_MODEL_AND_METRICS.md`](01_MODEL_AND_METRICS.md) | simulator, repairs, WP1 metrics at the 50 C target, paired baseline |
| [`02_WEATHER_AND_DESIGN_SPACE.md`](02_WEATHER_AND_DESIGN_SPACE.md) | K = 4 regimes and medoids, weather inventory, year roles, shortlist, design space |
| [`03_OPTIMISATION_PIPELINE.md`](03_OPTIMISATION_PIPELINE.md) | screening, DOE, surrogates, NSGA-II + active learning, dense grid, selection, ablations, code changes for Uttarakhand |
| [`04_RESULTS.md`](04_RESULTS.md) | generated tables and readings (chosen designs, held-out test, optimiser checks, ablations, diagnostics) |
| [`05_LIMITATIONS_AND_OPEN_ITEMS.md`](05_LIMITATIONS_AND_OPEN_ITEMS.md) | what the results do not support, deviations from Rajasthan, items for the guide |
| [`06_OBJECTIVE3_HANDOFF.md`](06_OBJECTIVE3_HANDOFF.md) | the Objective 3 environment contract v2 |
| [`plots/10_PLOTS.md`](plots/10_PLOTS.md) | the nine result figures |
| `PROGRESS.md` | the progress log, gates G1-G12 |
| `../results/results_registry.csv` | every headline number with its source file (`scripts/g12_registry.py`) |

## Headline findings (all in `04_RESULTS.md`, with the files they come from)

1. **Regimes 0-2: PCM helps.** Chosen designs PureTemp 58 / PureTemp 58 / savE OM55 at inner radius about 40 mm and fraction 26-30 %. Gain in the 18:00-09:00
   window over the same-flow water-only tank: 80.0 / 72.1 / 63.0 kWh/yr on the select years and 76.0 / 61.8 / 56.4 kWh/yr on the 2024-2025 test years
   (weakest test year 74.6 / 60.7 / 49.6), against bands of 22.0 / 19.4 / 20.0 kWh. All 4 dense-grid checks and all 12 seed-stability checks pass.
2. **Regime 3 (cold, high altitude): PCM does not help.** No design of PureTemp 53, n-Hexacosane or Myristic acid beats the water-only tank beyond the
   6.1 kWh band; the gain falls as PCM is added. The selection log says `meaningful_on_primary_metric: false`; the honest recommendation is water-only.
3. **Still boundary-limited at the 30 % cap** in regimes 0-2: 30 % to 40 % adds +23 to +30 kWh in a diagnostic run, beyond the band. The best PCM amount is not found.
4. **PCM choice inside a regime is not resolved.** On the test years the runner-up PCM is within the band of the chosen one in every regime (in regime 0 PlusICE A58
   is 10.4 kWh ahead, inside the 22 kWh band).
5. Nulls and costs: night-serve duration is shorter with PCM than in the same 50 L tank (water displacement); evening energy up to 50 C is higher. `d_overheat`
   is positive, but the water-side shield hours are lower with PCM in every design-year; the positive part is the PCM-side throttle. The gain level depends on
   the capsule-stack position by 35-54 kWh, the sign does not.

## Entry points

```
python pipeline.py --state uttarakhand --stage status                 # which outputs exist, is the held-out lock set
python pipeline.py --state uttarakhand --stage <stage>                # verify sensitivity baseline screening doe surrogate band optimize
                                                                      # select ablation report handoff plots (heldout refuses: lock set)
python run_all_uttarakhand.py                                         # tests + report + handoff + plots from saved results
python run_all_uttarakhand.py --full --dry-run                        # print the whole chain; --full itself is about 6 h
```

Stages that would re-decide the frozen designs refuse while `results/held_out_test.lock` exists unless `--allow-invalidate` is passed.

## Figures (`results/plots/`)

`fig1`-`fig9` from `src/plots/make_plots_results.py` (front vs grid, G9 check, gain by year role, held-out PCM comparison, nulls and costs, ablations,
surrogates, G7 fraction response, boundary share), listed in `plots/10_PLOTS.md`.

## How to reproduce (Python 3.12, from this folder)

```
python -m pytest tests
python scripts/g2_timestep_convergence.py 150,75,37.5 results/g2_timestep_convergence_150_75_37p5.csv
python scripts/g3_metrics_report.py ; python scripts/g4_multinode_report.py
python -c "from src.weather.inventory import build_inventory; build_inventory()"
python pipeline.py --state uttarakhand --stage verify                  # ... then sensitivity baseline screening doe surrogate band optimize select
python scripts/g7_paired.py                                             # paired G7 file for fig8
python scripts/g10_test.py --confirm-run-once                           # held-out test: ONLY ONCE (already done; refuses now)
python scripts/g11_ablation.py <regime>                                 # and scripts/g13 ... g17 with <regime> = 0 1 2 3
python scripts/g12_registry.py ; python scripts/g12_results_doc.py ; python scripts/g12_verify_docs.py
```
