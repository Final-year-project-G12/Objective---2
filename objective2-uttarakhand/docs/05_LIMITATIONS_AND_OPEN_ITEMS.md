# 05 - Limitations, deviations and open items

Numbers below are quoted from `docs/04_RESULTS.md` (generated) and the files it names.

## What the results do not support

0. **PCM does not help in regime 3.** In the cold, high-altitude regime (medoid UKP_0041, mains about 7 C, lowest sun) no design of any of the three
   O1 PCMs beats the water-only tank by more than the band on the select years, and the chosen (least-PCM) design is -6.1 kWh/yr on the
   2024-2025 test. The more PCM, the worse: at R 38 mm the gain falls from -20 kWh at 10 % to -56 kWh at 30 % (`g17_widen_r3.csv`), and the latent heat
   barely matters there (L = 0 changes the gain by -3 kWh). The honest output for regime 3 is "no PCM", and O3 should treat it as a water-only regime.
   The regime has only 3 grid points, so its weather basis is narrow.
1. **Boundary-limited on the PCM fraction in regimes 0-2.** Chosen designs: inner radius 39.3-39.8 mm, fraction 26-30 %. Widening the fraction from 30 % to
   40 % in a diagnostic run raises `g_window` by +30 / +23 / +23 kWh, beyond the bands of 22 / 19 / 20 kWh (`g17_widen_r*.csv`). The best amount is not found
   and is not claimed. The 25-30 % step of the ablation sweep is +14 to +16 kWh, inside the band, so the curve flattens but has not stopped rising.
2. **The radius edge is not limiting**: R 45 and 50 mm are worse than the chosen radius at the same fraction in regimes 0-2.
3. **The level of the gain depends on the capsule-stack position.** Bottom / centre / top changes the chosen design's select-year gain by 54 / 35 / 36 kWh
   in regimes 0-2 (bands 22 / 19 / 20); the sign survives every position (`g15_anchor_r*.csv`). Quote absolute kWh as "stack centred (model default)".
4. **The chosen PCM is not separated from the runner-up on the test years.** Regime 0: PlusICE A58 86.4 against the chosen PureTemp 58 76.0 kWh/yr
   (difference inside the band); regimes 1 and 2: the chosen PCM leads by 8.9 and 5.5 kWh, also inside the band (`g10_heldout_results.csv`). Inside a
   regime, PureTemp 58, PlusICE A58 and savE OM55 are interchangeable at the resolution of this model; n-Octacosane (C28) is clearly weaker.
5. **Night-serve duration is not improved** against the fixed 50 L tank (-0.11 to -0.16 h in regimes 0-2): the capsules displace water. The evening
   energy delivered up to 50 C is higher with PCM (+0.15 to +0.21 kWh per scenario night) and comes from the latent heat (`g16_serve_r*.csv`).
6. **Shield hours.** `d_overheat` is positive for every PCM design, but the water-side shield hours are LOWER with PCM in every design-year checked;
   the positive value is the PCM-side throttle at 62 C (`g13_shield_split_r*.csv`).
7. **Flow optima are not physical** (flow-independent collector F_R). A flow at the 0.010 floor is a model artefact (regime 3's 0.010 pick included).
8. **Delivery target 50 C.** Uttarakhand's metrics use 50 C, Rajasthan's 45 C; the kWh of the two states are not directly comparable.
9. **Tank-model convergence.** N = 10 to 20 changes useful energy by 0.8-1.0 %; part of the band, not removed.
10. **Weather.** One medoid point per regime, 10 years (2016-2025). The two test years are below-average GHI years in every regime but not the two lowest
    in every regime (`02_WEATHER_AND_DESIGN_SPACE.md`).
11. **No measurements.** The model has not been validated against hardware; the CFD agreement is model-to-model.

## Deviations from Rajasthan v3

- Held-out years 2024-2025 (Rajasthan v3: 2011-2015, because its 2024-2025 test was used in v1). No `used_test_v1` role exists here.
- Delivery target kept at 50 C.
- G2-G4 used one illustrative mid design per regime (`data/legacy/g2_g4_illustrative_designs.csv`) because there are no K = 4 legacy deployables.
- `scripts/g18_issue1_compare.py` (with / without the box-vertex step) was not run; the step is part of the declared recipe.
- `results/g7_sensitivity_paired.csv` is built by a script (`scripts/g7_paired.py`) rather than by hand.
- The legacy K = 5 chain (its results, docs, configs, build scripts and phase figures) was removed in the cleanup of 2026-10-28, as in Rajasthan; it is in git history only.

## Items for the guide / the O1 owner

1. **Regime 3:** confirm that a water-only recommendation is acceptable for the cold regime, or whether a different PCM (melting between the 50 C target
   and about 55 C) or a larger collector should be studied there. O1's top-3 for regime 3 (PureTemp 53, n-Hexacosane, Myristic acid) do not help in this model.
2. **Cap on the PCM fraction:** 30 % is still limiting in regimes 0-2 (item 1 above).
3. **Collector F_R(flow):** a cited flow-dependent correction would remove the flow artefact.
4. **Delivery target:** 50 C (Uttarakhand) vs 45 C (Rajasthan): decide whether the states should report at a common target.
5. **Phase 4 Gate 4:** solar fraction 0.24-0.30 at the illustrative designs (multi-node), below the published benchmark band; reported, not tuned.
