# 03 - Optimisation pipeline (what was run, in order)

Everything below runs on the real simulator for the 9 (regime, O1 PCM) pairs: 3 regimes x top-3 PCMs. File names are in
`results/`; each step's evidence and caveats are in `docs/PROGRESS.md` (section in brackets).

| Step | Script | What it does | Main output |
|---|---|---|---|
| S1 screening | `scripts/g8_s1_screening.py` | Taguchi L9 over the 4 variables (v3 fraction levels 2/16/30 %), 5 explore years per run, ANOVA (`src/optimize/anova.py`) | `g8_s1_r*_p*.csv`, `g8_s1_anova_r*_p*.csv` [10] |
| S2 DOE | `scripts/g8_s2_doe.py` (+ `g8_s2_repair.py` for 4 memory-error rows) | 128 scrambled-Sobol points over the v3 box (seed 20261026), same points for every pair, 5 explore years | `g8_s2_r*_p*.csv` (1,152 designs: 1,143 simulated, 9 geometry-rejected) [10] |
| S3 surrogates | `scripts/g8_s3_compare.py`, `src/optimize/surrogates.py` | NN ensemble (5 x (32,32) tanh), XGBoost, quadratic ridge RSM; within-pair 5-fold and leave-one-year-out; rank (Spearman) and RMSE/year-sd, not global R2 | `g8_s3_comparison.csv`, `g8_s3_selection.csv` [10] |
| WP6 band | `scripts/g9_band.py` | repeatability band per objective: sqrt((year sd / sqrt 5)^2 + dt effect^2 + node-count effect^2 + property effect^2) | `wp6_band.csv`, `g9_band_r*.csv` [11] |
| S4/S5 | `scripts/g9_s4_s5.py`, `src/optimize/nsga2.py` | hand-written NSGA-II (SBX, polynomial mutation, constrained domination, exact hypervolume) on the per-pair winning surrogate, 3 seeds; committee-disagreement active learning, 10 designs per round, stopping when hypervolume moves under 1 % for two rounds | `g9_al_log_*`, `g9_points_*`, `g9_seed_front_*`, `g9_ref_*` [11] |
| S6 dense grid | `scripts/g9_s6_grid.py` | v3: 6 radii x 8 fractions (2-30 %) x 5 flows x 3 arrangements = 720 simulator runs (v1: 6 fractions to 20 %, 540 runs) for the rank-1 PCM of each regime | `g9_s6_grid_r*_p1.csv` [11] |
| G9 checks | `scripts/g9_assess.py` | seed spread inside the band; grid front covered by the final front within the band (additive epsilon); boundary detector | `g9_seed_stability.csv`, `g9_grid_check.csv`, `g9_boundary_check.csv`, `g9_al_summary.csv` [11] |
| S7 selection | `scripts/g10_select.py` | re-simulates up to 30 front designs per pair on the select years; hard constraints, then the tie-break rule below; writes a fingerprinted log | `g10_selection_r*.json`, `g10_selection_candidates_r*.csv` [12] |
| S8 held-out | `scripts/g10_test.py --confirm-run-once` | chosen design plus the best design of each other O1 PCM, all five test years (v1: 2024 and 2025), once (v3: untouched years 2011-2015; v1 used 2024-2025) | `g10_heldout_results.csv`, `held_out_test.lock` [12.1] |
| Ablations | `scripts/g11_ablation.py` | one variable at a time around the chosen design with negative and positive controls | `g11_ablation_r*.csv` [13] |

## Objectives and constraints

Minimised: `-g_window`, `-g_annual`, `d_overheat` (definitions in `01`). Constraint: PCM peak at most 65 C (1 C guard on the surrogate
prediction during the search). The surrogate is used only to rank and propose; **every reported number is a simulator run**, because
the surrogates' absolute error is larger than the year-to-year scale (progress log section 10, S3 reading).

## Selection rule (decisions D9 and D10)

1. Hard constraints on the select years: PCM peak at most 65 C, water peak at most 75 C.
2. S0: candidates whose `g_window` is within the band of the best. S1: within S0, those within the `d_overheat` band of the lowest overheating.
   S2: within S1, those within the measured tau_serve uncertainty of the best tau_serve gain.
3. Pick the lowest PCM mass, then fewest capsules, then the larger margin to 65 C. Candidates the band cannot tell apart are reported as
   indistinguishable, not as a win.
4. "Better than water-only" is claimed only if the paired select-year `g_window` exceeds its band.

## Deviations from the first G9 run (method change, disclosed)

The first active-learning runs (5 rounds) passed the seed-stability check for all pairs but **failed the dense-grid check for regime 0**
(epsilon 24.9 / 25.6 kWh against bands of 13.8 / 13.3). Extra rounds alone did not fix it (23.5 / 24.1). The cause, read from the saved
grid, was a box-corner design (40 mm, about 20 %, flow 0.010, staggered) whose overheating is a cliff the surrogate smooths. The fix was
to simulate all 24 box vertices (2^3 corners x 3 arrangements) before three more rounds (`G9_WARM=1 G9_VERTICES=1`, output suffix
`_ext2`), and the same step was applied to the other 8 pairs so the PCM comparison inside a regime stays fair. After it, all three
regimes pass. The vertices are defined by the approved box, but they are also part of the dense grid, so the grid check is not fully
independent of this change. `scripts/g9_assess.py` and `scripts/g10_select.py` read the newest file of each pair (`_ext2`, then
`_ext`, then the original); the older files are kept. Details: progress log sections 11.1-11.3.

**Declared method step (2026-10-27).** The box-vertex step was not in the plan and was added after regime 0 PCM 1 failed; it is now a documented step of S5
for every pair, regime and seed (defined by the approved box only, before any refit). Its effect was measured by running all nine pairs with and without it at equal
rounds (section 5f of `04_RESULTS.md`, `scripts/g18_issue1_compare.py`): without it regime 0 PCM 1 still fails the dense-grid check (23.5 kWh against a band of 13.8), with it
it passes (3.1); the rank-1 pairs of regimes 1 and 2 pass either way. Because the vertices are part of the dense grid, the grid check remains partly dependent on the step.

## Other bugs found while running

- `scripts/g10_select.py` first crashed after simulating, because the tau_serve columns were joined after the feasible table had been copied; fixed and rerun.
- The active-learning error diagnostic merged duplicate rows in an early version; fixed with positional alignment (`cand_pos`). Error
  columns of the three pairs finished before that fix (first rounds) come from the old alignment and are not quoted.
