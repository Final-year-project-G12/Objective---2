# Objective 2 - Rajasthan: redesigned pipeline (2026-10-27)

**Status: current.** These documents describe what is actually in the code and the saved results after the redesign
(`docs/REDESIGN_PROGRESS.md` is the day-by-day log with every gate). The older `docs/00_*` ... `docs/09_*`,
`docs/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` and `archive_pre_redesign/results/README.md` describe the pre-redesign pipeline (UTC-indexed demand,
single-node tank, retargeted PCMs, 327-case DOE) and carry a banner saying so. Their numbers are **not** valid for the redesigned model.

Scope: this folder only (Rajasthan). Fixed and not optimised: 50 L tank, 1.5 m2 collector, 300 L/day demand, the O1 PCM top-3
(`configs/system_config_shared.yaml` is frozen and unchanged). Nothing is committed to git by this work.

## Contents

| File | What it covers |
|---|---|
| [`01_MODEL_AND_METRICS.md`](01_MODEL_AND_METRICS.md) | simulator (single-node and multi-node tank), the repairs, the WP1 metrics, paired baseline |
| [`02_WEATHER_AND_DESIGN_SPACE.md`](02_WEATHER_AND_DESIGN_SPACE.md) | weather inventory, year roles and the held-out lock, approved design space |
| [`03_OPTIMISATION_PIPELINE.md`](03_OPTIMISATION_PIPELINE.md) | screening, DOE, surrogates, NSGA-II + active learning, dense-grid check, selection, ablations |
| [`04_RESULTS.md`](04_RESULTS.md) | generated tables of the results (chosen designs, held-out test, optimiser checks, ablations) |
| [`05_LIMITATIONS_AND_OPEN_ITEMS.md`](05_LIMITATIONS_AND_OPEN_ITEMS.md) | what the results do not support, deviations, items for Dr. Deepika |
| [`06_OBJECTIVE3_HANDOFF.md`](06_OBJECTIVE3_HANDOFF.md) | the regenerated environment contract for Objective 3 |
| `../CLEANUP_PROPOSAL.md` | proposal for archiving stale files (nothing moved yet) |
| `../REDESIGN_PROGRESS.md` | the single progress log, gates G1-G11 with evidence |
| `../../results/redesign/results_registry.csv` | every headline number with its source file (`scripts/g12_registry.py`) |

## Headline findings (all in `04_RESULTS.md`, with the files they come from)

1. The old demand-timing bug (UTC instead of local time) changed the plain-tank annual energy by about 31 % in regime 0 (log section 3).
2. With the repaired model, the best designs inside the approved box all sit at its edge: inner radius 40 mm and PCM fraction about 20 %. A diagnostic with widened bounds shows only the fraction cap limits the result (the radius and upper flow edges do not): the designs are boundary-limited on the fraction (section 5e of `04_RESULTS.md`).
   The benefit is on delivered energy in the night-and-morning window (about 94-99 kWh per year over the same-flow water-only tank); it is
   far above the repeatability band (10-16 kWh) and it holds on the 2024-2025 held-out years.
3. Nulls and negatives: the night-serve duration (tau_serve) is not improved against the same fixed 50 L tank (water displacement cancels the PCM benefit; the evening E_del45 energy is higher with PCM by about 0.25 kWh per scenario night, section 5d of `04_RESULTS.md`), `d_overheat` is positive for every PCM design but mixes a water-side term (lower with PCM in every design-year checked) with a PCM-side throttle
   (section 1b of `04_RESULTS.md`), and thickness at constant mass is informative only from an interior anchor: small radii are worse and R 30-40 mm are within the band of R 25 mm (section 5b of `04_RESULTS.md`).
4. The level of the result depends on a modelling assumption (where the capsule stack sits in the tank) by more than the band: 46 / 56 / 55 kWh range for the chosen designs over bottom / centre / top, against bands of 10-16 kWh; the sign of the gain does not (section 5c of `04_RESULTS.md`).

## Entry points

`pipeline.py` and `run_all_rajasthan.py` run the chain described here (the old ones are in `archive_pre_redesign/code/`).

```
python pipeline.py --state rajasthan --stage status                 # which outputs exist, is the held-out lock set
python pipeline.py --state rajasthan --stage <stage>                # verify sensitivity baseline screening doe surrogate band optimize
                                                                    # select ablation report handoff plots (heldout refuses: lock set)
python pipeline.py --state rajasthan --stage simulate --cluster 0 --pcm-rank 1 --radius-mm 40 --fraction 0.2 --flow 0.025 --purpose select
python run_all_rajasthan.py                                         # tests + report + handoff + plots from saved results (about 1 min)
python run_all_rajasthan.py --full --dry-run                        # print the whole chain; --full itself is hours
```

Stages that would re-decide the frozen designs (baseline ... select) refuse while `results/redesign/held_out_test.lock` exists unless
`--allow-invalidate` is passed, because a re-run would make the one held-out evaluation meaningless. Details at the top of `pipeline.py`.
Figures: see the table below.
note below.

## Figures (`results/redesign/plots/`, code `src/plots/make_plots_redesign.py`)

| File | Shows |
|---|---|
| `fig1_front_vs_grid.png` | optimiser points against the 540-design grid, selected design starred (grid exists for the rank-1 PCM only) |
| `fig2_g9_grid_check.png` | G9 epsilon gap as a share of the band, 9 pairs |
| `fig3_gain_by_year_role.png` | chosen design g_window on explore / select / held-out years with the band |
| `fig4_heldout_pcm_comparison.png` | held-out g_window of the chosen and the other O1 PCMs |
| `fig5_heldout_nulls_and_costs.png` | night-serve gain, extra shield hours, PCM peak (65 C line) |
| `fig6_ablations.png` | G11 changes in g_window against the band |
| `fig7_surrogate_comparison.png` | G8 surrogate families by rank agreement |
| `fig8_fraction_response.png` | G7 gain against PCM fraction |
| `fig9_boundary_share.png` | fronts sitting at a bound of the design box |

## How to reproduce (Python 3.10, from this folder)

The individual scripts behind each stage:

```
python -m pytest tests                                              # 79 tests
python scripts/g2_timestep_convergence.py 150,75,37.5 out.csv       # G2 time step (arguments: dt list, output file)
python scripts/g3_metrics_report.py                                 # G3 metrics
python scripts/g4_multinode_report.py                               # G4 multi-node tank
python -c "from src.weather.inventory import build_inventory; build_inventory()"   # G5 weather (writes data/weather_redesign/)
python scripts/g6_phase4_o1.py                                      # G6 verification on the O1 PCMs
python scripts/g7_sensitivity.py <regime>                           # G7 sensitivity study (regimes 0 1 2)
python scripts/g7_flow_baseline_and_packing.py                      # G7 same-flow baseline and packing limits
python scripts/g8_build_plain_baseline.py <regime>                  # plain-tank flow grid (explore and select years)
python scripts/g8_s1_screening.py <regime> <pcm_rank>               # S1 Taguchi L9 (rank 1..3)
python scripts/g8_s2_doe.py <regime> <pcm_rank>                     # S2 Sobol DOE
python scripts/g8_s3_compare.py                                     # S3 surrogate comparison
python scripts/g9_band.py <regime>                                  # WP6 repeatability band
python scripts/g9_s4_s5.py <regime> <pcm_rank>                      # S4/S5 active learning (see 03 for the follow-up variants)
python scripts/g9_s6_grid.py <regime> [pcm_rank]                    # S6 dense grid
python scripts/g9_assess.py                                         # G9 checks
python scripts/g10_select.py <regime>                               # selection, regimes 0 1 2
python scripts/g10_test.py --confirm-run-once                       # held-out test: ONLY ONCE, refuses if the lock exists
python scripts/g11_ablation.py <regime>                             # ablations
python scripts/g12_registry.py ; python scripts/g12_results_doc.py  # registry and results tables
python -m src.handoff.build_obj3_contract_v2                        # Objective 3 contract v2 (needs PYTHONPATH=. if config is not found)
```

Exact arguments of each script are in its docstring. Runtimes on the development machine: one year of the multi-node tank takes a few
seconds; the nine active-learning runs took about 40-80 minutes in parallel, the selection about 5 minutes per regime.
