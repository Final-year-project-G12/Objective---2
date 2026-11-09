# 03 - Optimisation pipeline (what was run, in order)

Same recipe as Rajasthan v3 (`../objective2-rajasthan/docs/03_OPTIMISATION_PIPELINE.md`), run on the real simulator for the **12 (regime, O1 PCM) pairs**:
4 regimes x top-3 PCMs. File names are in `results/`; the run log is in `docs/PROGRESS.md`. The whole chain G2-G10 selection ran unattended
on 2026-10-28 (about 6 h on 20 logical CPUs, `--jobs 6`).

| Step | Script | What it does | Main output |
|---|---|---|---|
| S1 screening | `scripts/g8_s1_screening.py` | Taguchi L9 over the 4 variables (fraction levels 2/16/30 %), 5 explore years per run, ANOVA | `g8_s1_r*_p*.csv`, `g8_s1_anova_r*_p*.csv` |
| S2 DOE | `scripts/g8_s2_doe.py` | 128 scrambled-Sobol points over the box (seed 20261026), same points for every pair, 5 explore years | `g8_s2_r*_p*.csv` (1,536 designs: 1,452 simulated, 84 geometry-rejected, 0 errors) |
| S3 surrogates | `scripts/g8_s3_compare.py`, `src/optimize/surrogates.py` | NN ensemble, XGBoost, quadratic ridge RSM; within-pair 5-fold and leave-one-year-out; rank agreement | `g8_s3_comparison.csv`, `g8_s3_selection.csv` (XGBoost in 11 pairs, RSM in r0_p2) |
| WP6 band | `scripts/g9_band.py` | repeatability band per objective: sqrt((year sd / sqrt 5)^2 + dt effect^2 + node-count effect^2 + property effect^2) | `wp6_band.csv`, `g9_band_r*.csv` |
| S4/S5 | `scripts/g9_s4_s5.py`, `src/optimize/nsga2.py` | NSGA-II on the per-pair winning surrogate, 3 seeds; committee-disagreement active learning; then the declared box-vertex step (`G9_WARM=1 G9_VERTICES=1`, suffix `_ext2`) and 3 more rounds | `g9_al_log_*`, `g9_points_*`, `g9_seed_front_*` |
| S6 dense grid | `scripts/g9_s6_grid.py` | 6 radii x 8 fractions (2-30 %) x 5 flows x 3 arrangements = 720 runs for the rank-1 PCM of each regime | `g9_s6_grid_r*_p1.csv` |
| G9 checks | `scripts/g9_assess.py` | seed spread inside the band; grid front covered by the final front within the band; boundary detector | `g9_seed_stability.csv`, `g9_grid_check.csv`, `g9_boundary_check.csv` |
| S7 selection | `scripts/g10_select.py` | re-simulates front designs on the select years; hard constraints, then the tie-break rule below | `g10_selection_r*.json`, `g10_selection_candidates_r*.csv` |
| S8 held-out | `scripts/g10_test.py --confirm-run-once` | chosen design plus the best design of each other O1 PCM, test years 2024-2025, once | `g10_heldout_results.csv`, `held_out_test.lock` |
| Ablations | `scripts/g11_ablation.py` | one variable at a time around the chosen design, negative and positive controls | `g11_ablation_r*.csv` |
| Diagnostics | `scripts/g13_issue4_shield_split.py` ... `scripts/g17_issue2_widen.py` | shield split, interior-anchor controls, stack position, evening decomposition, widened bounds | `g13_*` ... `g17_*` |
| G7 paired | `scripts/g7_paired.py` | collects the paired G7 rows (new script; Rajasthan built this file by hand) | `g7_sensitivity_paired.csv` |

`scripts/g18_issue1_compare.py` (with / without the box-vertex step, 12 extra active-learning runs) was **not** run for Uttarakhand: the step is
part of the declared recipe since Rajasthan v3, and the Rajasthan comparison is the evidence for it. `scripts/g12_registry.py` treats the g18 file as optional.

## Objectives and constraints

Minimised: `-g_window`, `-g_annual`, `d_overheat` (definitions in `01`). Constraint: PCM peak at most 65 C. The surrogate only ranks and
proposes; **every reported number is a simulator run**.

## Selection rule

1. Hard constraints on the select years: PCM peak at most 65 C, water peak at most 75 C.
2. S0: candidates whose `g_window` is within the band of the best. S1: within S0, those within the `d_overheat` band of the lowest.
   S2: within S1, those within the tau_serve uncertainty of the best tau_serve gain.
3. Pick the lowest PCM mass, then fewest capsules, then the larger margin to 65 C.
4. "Better than water-only" is claimed only if the paired select-year `g_window` exceeds its band (`meaningful_on_primary_metric` in the selection log).

Consequence for regime 3: no candidate exceeds the band (the best `g_window` is about zero or negative), so S0 holds the near-zero designs and the
tie-break picks the **smallest PCM mass** (2 % fraction, 4 capsules). That pick is the rule working as written, not a recommendation to fit PCM;
`meaningful_on_primary_metric` is `false` for regime 3 and `true` for regimes 0-2.

## Code changes needed for Uttarakhand (all in `docs/PROGRESS.md` section 2)

- Regime loops `range(3)` -> `src/weather/inventory.py: REGIMES` (0-3) in `pipeline.py`, `scripts/g10_test.py`, `scripts/g12_registry.py`, the plots, the hand-off.
- `src/io_utils.py: o1_top3` reads the `name` column of the Uttarakhand O1 file.
- `src/verify/gates.py` takes the O1 rank-1 PCM of each regime and adds a cold-mains case for regime 3.
- `scripts/g14_issue5_controls.py` reads the fraction cap from `configs/design_space.yaml` instead of the hard-coded 20 %.
- Tests that hard-coded 45 C read the configured 50 C target; the CFD draw tests keep 45 C by override.
