# 05 - Limitations, deviations and open items

## What the results do not support

0. **Still boundary-limited after the cap was raised to 30 % (v3, 2026-10-28).** Chosen designs: radius 39.5-40 mm, fraction 28.4-29.6 %. Share of the final rank-1 fronts at the cap / at the
   40 mm radius end: regime 0 56 % / 100 %, regime 1 0 % / 0 %, regime 2 83 % / 97 % (`g9_boundary_check.csv`); the ablation count sweep still rises +16.5 / +19.6 / +21.1 kWh from 25 % to 30 %
   (`g11_ablation_r*.csv`). The best PCM amount is therefore still unknown. Beyond 30 % the packing limits (28-48 % at R 40 mm) and the displaced water volume would start to bind, and no source read covers it.
   **Planned, not started:** test a 40 % cap as a further declared change with a new untouched test (about 11-12 h of computing; `docs/PROGRESS.md` section 27).
   Items 1-6 below were investigated on the v1 designs and not re-run on v3 (stack position, shield split, evening decomposition, control anchor).

1. **Boundary-limited on the PCM fraction (tested 2026-10-27).** Every chosen design sits at inner radius 40 mm and PCM fraction about 20 %.
   The widened-bound diagnostic (`g17_widen_r*.csv`, section 5e of `04_RESULTS.md`; the approved box itself is unchanged) shows the radius edge is NOT
   limiting (R 45 and 50 mm are worse at the same fraction) and neither is the upper flow bound (+3-4 kWh at 0.080 kg/s, inside the band), but the 20 %
   cap IS: g_window rises by +21 to +24 kWh at 25 %, +43 to +49 kWh at 30 % and +84 to +101 kWh at 40 %, with PCM and water peaks still within 65 / 75 C.
   The cap is administrative (packing accepts 28-48 % at R 40 mm; the only source read is the 10-20 % range of Chen 2025), so the designs are
   labelled boundary-limited and the true best amount is unknown. Whether to raise the cap (and re-run G9-G11 with a new untouched test) is a
   decision that was then taken on 2026-10-27: the cap is raised to 30 % (v3, `PROGRESS.md` section 26), so the finding below describes the v1 result; the v3 result will state whether 30 % is again limiting. Gains above 20 % also extrapolate beyond the sources read and reduce the water volume further.
2. **Level of the gain depends on an unvalidated modelling choice.** Moving the capsule stack from the tank centre to the bottom or the top
   changes `g_window` of the staggered design by roughly -27 to -37 kWh or +19 to +22 kWh, more than the band in all regimes
   (`results/g11_ablation_r*.csv`). Re-evaluated 2026-10-27 for the chosen design and the best design of every other O1 PCM on the
   select years (`g15_anchor_r*.csv`, section 5c of `04_RESULTS.md`): the sign of the gain survives every position (smallest gain 41.6 kWh); the
   chosen design's range over the three positions is 46 / 56 / 55 kWh against bands of 15.1 / 10.0 / 15.7; the best PCM per regime is the same at all
   positions but its margin over the runner-up is inside the band in regimes 0 and 2 at the bottom and centre; and in regimes 1 and 2 with the stack
   at the bottom another design of the same PCM is 22 kWh better than the chosen one. Quote absolute kWh only as "stack centred (model default),
   range over bottom / centre / top given beside it". The position is a mounting choice the model does not fix; no source read settles it.
3. **Flow optima are not physical.** The collector F_R in the project model does not depend on flow, so low flow always helps the stratified
   water tank. Flow at the 0.010 floor appears on up to 44 % of the Pareto sets (`g9_boundary_check.csv`) and is a model artefact.
   The chosen flows (0.021-0.048 kg/s) are inside the S0 sets and should not be over-interpreted.
4. **Night-serve duration is not improved against the fixed 50 L tank, and why (decomposed 2026-10-27).** tau_serve gain is -0.08 / -0.01 / -0.03 h
   and the serve fraction hits a floor (a 46 L evening draw on a 50 L tank cools the outlet below 45 C within about half an hour whatever is
   inside). The zero is the net of two effects (section 5d of `04_RESULTS.md`, `g16_serve_*.csv`): the capsules take about 20 % of the tank's water
   (a 40 L water-only tank serves 0.16-0.18 h less), and the PCM adds back +0.08 to +0.17 h against that displacement-matched tank. On energy the
   same scenario shows a clear gain: E_del45 +0.25 to +0.26 kWh per scenario night over the 50 L water-only tank in every regime and select year
   (latent heat is the source: with L = 0 it is lower than the water-only tank). What stays a finding: volume delivered at 45 C or above and the time to
   the first dip below 45 C are not better than in the same fixed tank. The plain 40 L tank is a diagnostic, not a baseline.
5. **Shield hours (corrected reading, 2026-10-27).** `d_overheat` is positive for every PCM design in every year, but it adds a PCM-side
   throttle (62 C, blocks charging when the capsules are full) that a water-only tank cannot have. Split like for like, the PCM tank has
   FEWER water-side shield hours than the water-only tank in every design-year checked (`g13_shield_split_r*.csv`, section 1b of
   `04_RESULTS.md`); the PCM-side throttle hours are real and reported separately. f3 in the optimisation is still the combined `d_overheat`
   (option B, decided 2026-10-27), so fronts and selections are unchanged. The held-out file has no such split and was not re-run.
6. **Thickness effect (re-tested 2026-10-27).** From the chosen (20 %) designs only R_in = 40 mm is valid at constant PCM mass. From an interior
   anchor (R 25 mm, 10 %, 0.030 kg/s) all radii are valid: R 10 and 15 mm are clearly worse (-8.5 to -31 kWh), R 30 and 40 mm are within the
   band of R 25 mm (section 5b of `04_RESULTS.md`), so the 40 mm edge optimum is a plateau, not a distinct peak. The outer volume still varies a little with R.
7. **Arrangement** is a null on `g_window` at the centre anchor in all three regimes (largest gap 4.4 / 8.9 / 8.1 kWh against bands of 15.1 / 10.0 / 15.7); it matters only for overheating hours, where the differences exceed the band for some pairs of arrangements.
8. **Tank-model convergence.** N = 10 versus 20 changes the paired gain by 0.15-0.25 percentage points; this is part of the band, not removed.
9. **Weather.** One medoid point per cluster, 10 years; the held-out years are the two lowest-GHI years, so the held-out gain is a harsher case.
10. **No measurements.** The model has not been validated against any hardware or field data; the CFD agreement is model-to-model.

## Deviations from the plan and from the first runs (all disclosed in the progress log)

- Time step 150 s via a code-level override because 300 s failed the convergence gate.
- Demand follows the floor of the local hour (`local_hour`), as instructed.
- Surrogate comparison: the NN ensemble won nowhere; it is used only as a committee member for active learning.
- G9 regime 0 needed a method change (box-vertex step, `03`) after failing the dense-grid check twice. It is now a declared step; the with/without comparison for all nine pairs (section 5f of `04_RESULTS.md`) shows it is what makes regime 0 pass and is not needed for regimes 1 and 2.
- Positive control "PCM fraction x2" was uninformative from the chosen designs (cap); re-run from an interior anchor it passes (+31 to +44 kWh, section 5b of `04_RESULTS.md`, `scripts/g14_issue5_controls.py`).
- The WP2-C CFD runs and the porting to the other three states were out of scope; `configs/cfd_closure_v1.yaml` is provisional and unapplied.
- Legacy results (`results/phase*`, `fix*` and the old plots folder) were moved to an archive folder after approval and that folder was deleted on 2026-10-28 at the user's request (only the one input table the evidence scripts g2/g3/g4 read was kept, in `data/legacy/`)
  (progress log section 16). `pipeline.py` and `run_all_rajasthan.py` were rewritten for this chain (section 17); the old copies are in
  the deleted legacy archive. Still the old chain: the legacy modules under `src/{doe,surrogate,optimize/search.py,robustness}` and
  `src/plots/make_plots.py`, which nothing in the entry points calls. `--stage all` has not been executed end to end (hours; refused
  by the held-out lock); each stage's commands were printed with `--dry-run` and the reporting stages were run.

## Items for Dr. Deepika / the O1 owner

1. **Conductivity discrepancy:** O1's ranking table and the PCM database disagree on thermal conductivity (savE OM55 0.429 vs 0.13 W/m K;
   Palmitic-stearic/EG 0.452 vs 0.16; PureTemp 60 0.208 vs 0.20; n-Heptacosane 0.210 vs 0.2415). The simulator reads the database.
2. **Sizing:** 33.3 L per m2 of collector is below the 40-100 L/m2 range of IS 12976:2023 (decision D8). The compact-tank case is the
   fixed condition of this work; the standards-compliant resizing study (older pipeline) has not been repeated on the new model.
3. **Collector F_R(flow):** adding a cited flow-dependent collector correction would remove the flow artefact.
4. **Cap on the PCM fraction:** raise to 30 % or keep 20 % for comparability with Chen 2025.
5. **Safety:** several O1 PCMs exceed 65 C at some designs (Palmitic-stearic/EG and PureTemp 58 at the mid design, log section 8). The 65 C
   rule is now a feasibility constraint; the O3 shield design should cover PCMs already above their melt band.
6. **Phase 4 Gate 4:** solar fraction of the repaired model (about 0.36 single-node, 0.30-0.33 multi-node at the old designs) is below the 54-84 %
   benchmark band; this is reported, not tuned (50 L tank for 300 L/day, no backup heater).
7. **O3 motivation:** since O1's selection is stable per region, O3's case rests on hour-by-hour operation under weather and demand
   variability, plus the nulls above (no tau_serve gain, the PCM-side throttle hours) that a controller could address.
