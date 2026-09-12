# Rajasthan — Phase 8 Recommendation Cards

Pure aggregation of Phase 4 (cluster_profile_cards_rajasthan.md), Phase 6 (mcdm_full_rankings.csv), and Phase 7 (physics_validation_rajasthan.csv) — no new PCM-selection decisions made here. Cross-phase cluster-identity precondition PASSED (fingerprint 2542_3_1788975613.315; medoid cross-check on all 3 clusters) — see this script's own console log for the full check.

## Cross-cluster summary

| Cluster | #1 pick | Borda score | MC Top-3 incl. % | Spearman rho (vs Borda) | Caveats |
|---|---|---|---|---|---|
| 0 | RT50† | 26.00 | 81.8% | 0.218 | rho<0.4, W<0.6 |
| 1 | Palmitic-Stearic eutectic (64.2/35.8)† | 53.00 | 94.8% | -0.023 | rho<=0 |
| 2 | Paraffin/HDPE PCM2† | 57.00 | 58.7% | 0.258 | rho<0.4, W<0.6 |

† see this cluster's own card below (Caveats section) before quoting this row on its own — this table intentionally carries only a pointer, not the full caveat text, so it stays scannable; the full text is one section away, not three.


---

## Cluster 0

### 1. Cluster identity

- **Cluster ID:** 0
- **Medoid point:** RJP_0094 — Udaipur, Rajasthan (lat/lon 24.125, 74.125)
- **Member point count:** 109
- **State distribution:** Rajasthan: 100.0%
- **Total population covered:** 21,755,737
- **Mean maximum membership probability:** 0.9985

### 2. Climate signature (population-weighted mean +/- std, from cluster_profile_cards_rajasthan.md — not recomputed)

| Index | Mean | Std |
|---|---|---|
| Ta_mean | 27.130 | 0.698 |
| Ta_p95 | 35.638 | 1.349 |
| Ta_p05 | 17.457 | 1.005 |
| T_sunrise_mean | 21.956 | 0.618 |
| T_noon_mean | 29.727 | 0.718 |
| T_sunset_mean | 29.708 | 0.825 |
| diurnal_gradient | 7.771 | 0.369 |
| GHI_noon_mean | 750.289 | 8.563 |
| GHI_sunset_mean | 27.761 | 1.885 |
| GHI_daily_kWh | 5.164 | 0.073 |
| kt_noon_mean | 0.840 | 0.012 |
| kt_noon_std | 0.214 | 0.013 |
| kt_daily_mean | 0.867 | 0.008 |
| kt_daily_std | 0.181 | 0.011 |
| SAI | 0.867 | 0.008 |
| cloudy_frac | 0.016 | 0.005 |
| CCI | 0.645 | 0.035 |
| HDD18 | 1100.408 | 449.769 |
| CDD24 | 12372.140 | 1527.682 |
| DTR_true | 13.518 | 0.215 |
| RH_sunrise_mean | 70.984 | 1.934 |
| HSI_sunrise | 20.767 | 0.534 |
| wind_noon_mean | 2.644 | 0.220 |
| wind_sunset_mean | 2.265 | 0.143 |
| daylength_mean | 12.153 | 0.002 |
| daylength_amplitude | 1.534 | 0.050 |
| seasonality | 0.219 | 0.011 |
| monsoon_index | 0.928 | 0.033 |

*Auto-generated physical description (Phase 4, review before publishing):* Cooler, arid/low-monsoon, erratic solar resource, short low-clearness runs.

### 3. Derived targets

- **Tm_target_C:** 57.0 C — assumes an **INDIRECT** system configuration (T_delivery=50C + heat-exchanger approach dT=7C, per 04_climate_signature_rajasthan.py's TM_TARGET_C definition, Objective1_PCM_Climate_Framework_Plan_v3 Section 6.3).
- **Tm_target_capped_C:** 48.4 C (poor-insolation-day achievable ceiling, kt_p05-derived — differs from the base target above).
- **L_required_kJ_per_kg:** 312 kJ/kg (CEILING, not an achievability bar — see 04_climate_signature_rajasthan.py's docstring).
- **Dominant constraint driving the Top-1 pick:** melting-point fitness (from the criterion-contribution decomposition — see each Top-3 candidate's 'Criterion contributions' line under Rank 1/2/3 -> item 6, below).

### 4. Candidates screened

- **Entered Phase 5's filter:** 62
- **Survived at fixed kappa=0.7 (primary/diagnostic run):** 4
- **Survived at calibrated kappa=0.5 (status=in_band, the pool Phase 6/7/8 actually rank/simulate/report):** 9  (candidate_pool_status: **healthy**)
- **Melting-window relaxation:** widened +/-8K (4 relaxation round(s))
- **Exclusion breakdown (fixed kappa=0.7 run, 62 candidates evaluated):**
    - c1 melting window: 3 excluded
    - c2 absolute band [42,70C]: 1 excluded
    - c3 latent heat floor (kappa=0.7): 37 excluded
    - c4 cycling (>=300): 0 excluded, 7 flagged unreported (not excluded)
    - c5 supercooling (<=8K): 0 excluded, 7 flagged unknown (not excluded)
    - c6 charging feasibility (Tm<=Tm_target_capped): 50 excluded
    - c7 corrosion veto: 0 excluded
    - c8 safety exclusion: 0 excluded

### 5-6. Rank 1 / 2 / 3, with per-candidate criterion contributions (item 6)

**#1 — RT50** (Rubitherm Technologies, Organic (RT-line))
- Tm=48.0 C, L=160 kJ/kg, k=0.200 W/m.K
- Consensus Borda score: **26.00**  |  Copeland score: **8**  |  Per-method rank: TOPSIS=1, PROMETHEE-II=1, VIKOR=1, GRA=7
- Monte Carlo Top-3 inclusion probability: **81.8%** (Top-1 retention: 49.8%)
- **Criterion contributions:** RT50 ranked #1 driven primarily by melting-point fitness (+0.23) and supercooling (inverse) (+0.04), partially offset by below-peer latent heat (-0.01).
- **Simulated performance (Phase 7):** annual solar fraction 64.9%, 4297 hours/year meeting delivery temp

**#2 — n-Tricosane (C23)** (Literature, Organic n-alkane)
- Tm=47.5 C, L=232 kJ/kg, k=0.209 W/m.K
- Consensus Borda score: **22.00**  |  Copeland score: **4**  |  Per-method rank: TOPSIS=2, PROMETHEE-II=4, VIKOR=2, GRA=6
- Monte Carlo Top-3 inclusion probability: **67.9%** (Top-1 retention: 31.1%)
- **Criterion contributions:** n-Tricosane (C23) ranked #2 driven primarily by melting-point fitness (+0.15) and latent heat (+0.00), partially offset by below-peer supercooling (inverse) (-0.07).
- **Simulated performance (Phase 7):** annual solar fraction 65.3%, 4302 hours/year meeting delivery temp

**#3 — n-Docosane (C22)** (Literature, Organic n-alkane)
- Tm=44.5 C, L=249 kJ/kg, k=0.200 W/m.K
- Consensus Borda score: **18.00**  |  Copeland score: **2**  |  Per-method rank: TOPSIS=7, PROMETHEE-II=3, VIKOR=6, GRA=2
- Monte Carlo Top-3 inclusion probability: **40.0%** (Top-1 retention: 5.7%)
- **Criterion contributions:** n-Docosane (C22) ranked #3 driven primarily by supercooling (inverse) (+0.02) and latent heat (+0.01), partially offset by below-peer melting-point fitness (-0.08).
- **Simulated performance (Phase 7):** annual solar fraction 65.0%, 4299 hours/year meeting delivery temp

### 7. Physics validation context

- **Spearman rho (MCDM Borda rank vs. simulated solar-fraction rank):** 0.218
- **Context for this rho — read together, not the bare number alone:** n=9 candidates, Kendall's W=0.3521 (ambiguous, BELOW the 0.6 ambiguous threshold), candidate_pool_status=healthy.
- **This cluster's rho is PROVISIONAL pending the Phase 5/6 candidate-pool expansion** — with W<0.6 and/or an undersized pool, a low rho here may reflect the MCDM ranking's own pre-existing instability rather than a genuine physics/MCDM disagreement; see physics_validation_summary_rajasthan.txt for the full caveat-aware interpretation.
- **Physics-validation band: NEGATIVE** (rho<=0.4, genuine negative result).
- **The Top-1/2/3 ordering shown above is the MCDM CONSENSUS ONLY — it is NOT independently confirmed by physics simulation for this cluster** (rho=0.218, band=NEGATIVE). See physics_validation_summary_rajasthan.txt for the full per-cluster interpretation before quoting this Top-3 as physics-validated.

### 8. Caveats

- **Imputed/unmeasured property in Top-3 candidate RT50:** solid thermal conductivity, liquid thermal conductivity, cycling-stability count, flammability rating.
- **Imputed/unmeasured property in Top-3 candidate n-Tricosane (C23):** solid density, liquid density, solid specific heat, liquid specific heat, solid thermal conductivity, liquid thermal conductivity, thermal conductivity, cycling-stability count, flammability rating.
- **Imputed/unmeasured property in Top-3 candidate n-Docosane (C22):** solid specific heat, liquid specific heat, solid thermal conductivity, liquid thermal conductivity, cycling-stability count, flammability rating.
- **Feasibility window was relaxed** by +/-8K (4 round(s)) for this cluster, AND the latent-heat floor was calibrated down from kappa=0.7 to kappa=0.5 (status=in_band) — this Top-3 would not exist under the fixed-kappa=0.7 diagnostic run (0 survivors there).
- **Kendall's W = 0.3521, BELOW the 0.6 ambiguous-agreement threshold** (plan doc Section 9.5) — the four MCDM methods did not strongly agree with each other for this cluster's candidate pool.
- **Physics validation does not confirm this Top-3 ranking** (rho=0.218, band=NEGATIVE) — treat the ordering above as the MCDM consensus, not an independently-verified performance ranking, for this cluster.

---

## Cluster 1

### 1. Cluster identity

- **Cluster ID:** 1
- **Medoid point:** RJP_0192 — Nagaur, Rajasthan (lat/lon 26.875, 73.375)
- **Member point count:** 83
- **State distribution:** Rajasthan: 100.0%
- **Total population covered:** 14,033,429
- **Mean maximum membership probability:** 1.0000

### 2. Climate signature (population-weighted mean +/- std, from cluster_profile_cards_rajasthan.md — not recomputed)

| Index | Mean | Std |
|---|---|---|
| Ta_mean | 27.984 | 0.585 |
| Ta_p95 | 36.607 | 0.756 |
| Ta_p05 | 16.180 | 1.730 |
| T_sunrise_mean | 22.043 | 0.494 |
| T_noon_mean | 30.451 | 0.476 |
| T_sunset_mean | 31.457 | 0.935 |
| diurnal_gradient | 8.407 | 0.217 |
| GHI_noon_mean | 772.816 | 8.421 |
| GHI_sunset_mean | 29.217 | 4.814 |
| GHI_daily_kWh | 5.381 | 0.150 |
| kt_noon_mean | 0.880 | 0.009 |
| kt_noon_std | 0.161 | 0.012 |
| kt_daily_mean | 0.907 | 0.011 |
| kt_daily_std | 0.131 | 0.009 |
| SAI | 0.907 | 0.011 |
| cloudy_frac | 0.004 | 0.002 |
| CCI | 0.811 | 0.044 |
| HDD18 | 1615.046 | 650.400 |
| CDD24 | 16440.402 | 1633.101 |
| DTR_true | 13.797 | 0.331 |
| RH_sunrise_mean | 67.234 | 2.206 |
| HSI_sunrise | 20.682 | 0.389 |
| wind_noon_mean | 3.338 | 0.367 |
| wind_sunset_mean | 3.005 | 0.317 |
| daylength_mean | 12.158 | 0.003 |
| daylength_amplitude | 1.691 | 0.089 |
| seasonality | 0.209 | 0.017 |
| monsoon_index | 1.048 | 0.038 |

*Auto-generated physical description (Phase 4, review before publishing):* Hot, monsoon-influenced, steady solar resource, long low-clearness runs (high autonomy demand).

### 3. Derived targets

- **Tm_target_C:** 57.0 C — assumes an **INDIRECT** system configuration (T_delivery=50C + heat-exchanger approach dT=7C, per 04_climate_signature_rajasthan.py's TM_TARGET_C definition, Objective1_PCM_Climate_Framework_Plan_v3 Section 6.3).
- **Tm_target_capped_C:** 52.6 C (poor-insolation-day achievable ceiling, kt_p05-derived — differs from the base target above).
- **L_required_kJ_per_kg:** 302 kJ/kg (CEILING, not an achievability bar — see 04_climate_signature_rajasthan.py's docstring).
- **Dominant constraint driving the Top-1 pick:** melting-point fitness (from the criterion-contribution decomposition — see each Top-3 candidate's 'Criterion contributions' line under Rank 1/2/3 -> item 6, below).

### 4. Candidates screened

- **Entered Phase 5's filter:** 62
- **Survived at fixed kappa=0.7 (primary/diagnostic run):** 7
- **Survived at calibrated kappa=0.6 (status=in_band, the pool Phase 6/7/8 actually rank/simulate/report):** 15  (candidate_pool_status: **healthy**)
- **Melting-window relaxation:** widened +/-8K (4 relaxation round(s))
- **Exclusion breakdown (fixed kappa=0.7 run, 62 candidates evaluated):**
    - c1 melting window: 3 excluded
    - c2 absolute band [42,70C]: 1 excluded
    - c3 latent heat floor (kappa=0.7): 34 excluded
    - c4 cycling (>=300): 0 excluded, 7 flagged unreported (not excluded)
    - c5 supercooling (<=8K): 0 excluded, 7 flagged unknown (not excluded)
    - c6 charging feasibility (Tm<=Tm_target_capped): 38 excluded
    - c7 corrosion veto: 0 excluded
    - c8 safety exclusion: 0 excluded

### 5-6. Rank 1 / 2 / 3, with per-candidate criterion contributions (item 6)

**#1 — Palmitic-Stearic eutectic (64.2/35.8)** (Eutectic, Organic)
- Tm=52.3 C, L=182 kJ/kg, k=not available
- Consensus Borda score: **53.00**  |  Copeland score: **14**  |  Per-method rank: TOPSIS=1, PROMETHEE-II=4, VIKOR=1, GRA=1
- Monte Carlo Top-3 inclusion probability: **94.8%** (Top-1 retention: 71.1%)
- **Criterion contributions:** Palmitic-Stearic eutectic (64.2/35.8) ranked #1 driven primarily by melting-point fitness (+0.16) and corrosion class (inverse) (+0.00), partially offset by below-peer latent heat (-0.00).
- **Simulated performance (Phase 7):** annual solar fraction 66.1%, 4426 hours/year meeting delivery temp

**#2 — n-Tetracosane (C24)** (Literature, Organic n-alkane)
- Tm=52.0 C, L=255 kJ/kg, k=0.209 W/m.K
- Consensus Borda score: **50.00**  |  Copeland score: **12**  |  Per-method rank: TOPSIS=2, PROMETHEE-II=1, VIKOR=2, GRA=5
- Monte Carlo Top-3 inclusion probability: **43.8%** (Top-1 retention: 8.6%)
- **Criterion contributions:** n-Tetracosane (C24) ranked #2 driven primarily by melting-point fitness (+0.14) and latent heat (+0.01), partially offset by below-peer supercooling (inverse) (-0.03).
- **Simulated performance (Phase 7):** annual solar fraction 66.1%, 4432 hours/year meeting delivery temp

**#3 — PlusICE A52** (PCM Products Ltd., Organic PCM)
- Tm=52.0 C, L=220 kJ/kg, k=0.205 W/m.K
- Consensus Borda score: **41.00**  |  Copeland score: **10**  |  Per-method rank: TOPSIS=3, PROMETHEE-II=2, VIKOR=3, GRA=11
- Monte Carlo Top-3 inclusion probability: **40.4%** (Top-1 retention: 6.5%)
- **Criterion contributions:** PlusICE A52 ranked #3 driven primarily by melting-point fitness (+0.14) and latent heat (+0.00), partially offset by below-peer supercooling (inverse) (-0.03).
- **Simulated performance (Phase 7):** annual solar fraction 65.9%, 4421 hours/year meeting delivery temp

### 7. Physics validation context

- **Spearman rho (MCDM Borda rank vs. simulated solar-fraction rank):** -0.023
- **Context for this rho — read together, not the bare number alone:** n=15 candidates, Kendall's W=0.6397 (moderate), candidate_pool_status=healthy.
- **Physics-validation band: NEGATIVE** (rho<=0.4, genuine negative result).
- **The Top-1/2/3 ordering shown above is the MCDM CONSENSUS ONLY — it is NOT independently confirmed by physics simulation for this cluster** (rho=-0.023, band=NEGATIVE). See physics_validation_summary_rajasthan.txt for the full per-cluster interpretation before quoting this Top-3 as physics-validated.

### 8. Caveats

- **Imputed/unmeasured property in Top-3 candidate Palmitic-Stearic eutectic (64.2/35.8):** no manufacturer datasheet (literature-sourced candidate — thermal properties used by the physics simulation come from physics_lib.py's documented literature-default fallback, not MICE/RF/PMM imputation).
- **Imputed/unmeasured property in Top-3 candidate n-Tetracosane (C24):** solid specific heat, liquid specific heat, solid thermal conductivity, liquid thermal conductivity, thermal conductivity, cycling-stability count, flammability rating.
- **Imputed/unmeasured property in Top-3 candidate PlusICE A52:** thermal conductivity, cycling-stability count, flammability rating.
- **Feasibility window was relaxed** by +/-8K (4 round(s)) for this cluster, AND the latent-heat floor was calibrated down from kappa=0.7 to kappa=0.6 (status=in_band) — this Top-3 would not exist under the fixed-kappa=0.7 diagnostic run (0 survivors there).
- **Physics validation does not confirm this Top-3 ranking** (rho=-0.023, band=NEGATIVE) — treat the ordering above as the MCDM consensus, not an independently-verified performance ranking, for this cluster.

---

## Cluster 2

### 1. Cluster identity

- **Cluster ID:** 2
- **Medoid point:** RJP_0083 — Jaipur, Rajasthan (lat/lon 26.625, 75.875)
- **Member point count:** 128
- **State distribution:** Rajasthan: 100.0%
- **Total population covered:** 34,514,036
- **Mean maximum membership probability:** 0.9995

### 2. Climate signature (population-weighted mean +/- std, from cluster_profile_cards_rajasthan.md — not recomputed)

| Index | Mean | Std |
|---|---|---|
| Ta_mean | 26.696 | 0.489 |
| Ta_p95 | 35.879 | 0.495 |
| Ta_p05 | 14.987 | 1.306 |
| T_sunrise_mean | 21.437 | 0.513 |
| T_noon_mean | 29.606 | 0.484 |
| T_sunset_mean | 29.044 | 0.627 |
| diurnal_gradient | 8.168 | 0.363 |
| GHI_noon_mean | 749.251 | 9.901 |
| GHI_sunset_mean | 21.628 | 4.450 |
| GHI_daily_kWh | 5.033 | 0.188 |
| kt_noon_mean | 0.855 | 0.007 |
| kt_noon_std | 0.184 | 0.014 |
| kt_daily_mean | 0.875 | 0.010 |
| kt_daily_std | 0.156 | 0.009 |
| SAI | 0.875 | 0.010 |
| cloudy_frac | 0.008 | 0.002 |
| CCI | 0.765 | 0.051 |
| HDD18 | 2149.120 | 468.125 |
| CDD24 | 14590.109 | 1871.080 |
| DTR_true | 13.716 | 0.191 |
| RH_sunrise_mean | 72.097 | 3.414 |
| HSI_sunrise | 20.370 | 0.394 |
| wind_noon_mean | 2.624 | 0.260 |
| wind_sunset_mean | 2.188 | 0.195 |
| daylength_mean | 12.159 | 0.003 |
| daylength_amplitude | 1.713 | 0.083 |
| seasonality | 0.223 | 0.021 |
| monsoon_index | 1.025 | 0.045 |

*Auto-generated physical description (Phase 4, review before publishing):* Cooler, arid/low-monsoon, erratic solar resource, short low-clearness runs.

### 3. Derived targets

- **Tm_target_C:** 57.0 C — assumes an **INDIRECT** system configuration (T_delivery=50C + heat-exchanger approach dT=7C, per 04_climate_signature_rajasthan.py's TM_TARGET_C definition, Objective1_PCM_Climate_Framework_Plan_v3 Section 6.3).
- **Tm_target_capped_C:** 51.1 C (poor-insolation-day achievable ceiling, kt_p05-derived — differs from the base target above).
- **L_required_kJ_per_kg:** 318 kJ/kg (CEILING, not an achievability bar — see 04_climate_signature_rajasthan.py's docstring).
- **Dominant constraint driving the Top-1 pick:** melting-point fitness (from the criterion-contribution decomposition — see each Top-3 candidate's 'Criterion contributions' line under Rank 1/2/3 -> item 6, below).

### 4. Candidates screened

- **Entered Phase 5's filter:** 62
- **Survived at fixed kappa=0.7 (primary/diagnostic run):** 5
- **Survived at calibrated kappa=0.5 (status=in_band, the pool Phase 6/7/8 actually rank/simulate/report):** 17  (candidate_pool_status: **healthy**)
- **Melting-window relaxation:** widened +/-8K (4 relaxation round(s))
- **Exclusion breakdown (fixed kappa=0.7 run, 62 candidates evaluated):**
    - c1 melting window: 3 excluded
    - c2 absolute band [42,70C]: 1 excluded
    - c3 latent heat floor (kappa=0.7): 39 excluded
    - c4 cycling (>=300): 0 excluded, 7 flagged unreported (not excluded)
    - c5 supercooling (<=8K): 0 excluded, 7 flagged unknown (not excluded)
    - c6 charging feasibility (Tm<=Tm_target_capped): 42 excluded
    - c7 corrosion veto: 0 excluded
    - c8 safety exclusion: 0 excluded

### 5-6. Rank 1 / 2 / 3, with per-candidate criterion contributions (item 6)

**[FLAG] Borda and Copeland DISAGREE on Top-3 membership for this cluster** — Borda Top-3: ['Paraffin/HDPE PCM2', 'savE® OM50', 'Paraffin/HDPE PCM6']; Copeland Top-3: ['Paraffin/HDPE PCM2', 'savE® OM48', 'savE® OM50']. Both reported below/in the summary rather than picking one silently.

**#1 — Paraffin/HDPE PCM2** (Literature, Organic blend)
- Tm=50.6 C, L=187 kJ/kg, k=0.205 W/m.K
- Consensus Borda score: **57.00**  |  Copeland score: **15**  |  Per-method rank: TOPSIS=1, PROMETHEE-II=2, VIKOR=1, GRA=7
- Monte Carlo Top-3 inclusion probability: **58.7%** (Top-1 retention: 20.8%)
- **Criterion contributions:** Paraffin/HDPE PCM2 ranked #1 driven primarily by melting-point fitness (+0.12) and volumetric latent heat (+0.00), partially offset by below-peer supercooling (inverse) (-0.01).
- **Simulated performance (Phase 7):** annual solar fraction 63.9%, 4315 hours/year meeting delivery temp

**#2 — savE® OM50** (Pluss Advanced Technologies, Organic)
- Tm=50.0 C, L=189 kJ/kg, k=0.336 W/m.K
- Consensus Borda score: **55.00**  |  Copeland score: **13**  |  Per-method rank: TOPSIS=4, PROMETHEE-II=1, VIKOR=4, GRA=4
- Monte Carlo Top-3 inclusion probability: **78.4%** (Top-1 retention: 37.8%)
- **Criterion contributions:** savE® OM50 ranked #2 driven primarily by melting-point fitness (+0.08) and supercooling (inverse) (+0.02), partially offset by below-peer latent heat (-0.00).
- **Simulated performance (Phase 7):** annual solar fraction 64.7%, 4331 hours/year meeting delivery temp

**#3 — Paraffin/HDPE PCM6** (Literature, Organic blend)
- Tm=50.3 C, L=187 kJ/kg, k=0.206 W/m.K
- Consensus Borda score: **51.00**  |  Copeland score: **10**  |  Per-method rank: TOPSIS=3, PROMETHEE-II=5, VIKOR=3, GRA=6
- Monte Carlo Top-3 inclusion probability: **55.1%** (Top-1 retention: 19.4%)
- **Criterion contributions:** Paraffin/HDPE PCM6 ranked #3 driven primarily by melting-point fitness (+0.10) and supercooling (inverse) (+0.00), partially offset by below-peer thermal conductivity (-0.00).
- **Simulated performance (Phase 7):** annual solar fraction 64.0%, 4318 hours/year meeting delivery temp

### 7. Physics validation context

- **Spearman rho (MCDM Borda rank vs. simulated solar-fraction rank):** 0.258 (Copeland-vs-simulation rho=0.221, reported alongside Borda since they disagreed on Top-3)
- **Context for this rho — read together, not the bare number alone:** n=17 candidates, Kendall's W=0.5539 (ambiguous, BELOW the 0.6 ambiguous threshold), candidate_pool_status=healthy.
- **This cluster's rho is PROVISIONAL pending the Phase 5/6 candidate-pool expansion** — with W<0.6 and/or an undersized pool, a low rho here may reflect the MCDM ranking's own pre-existing instability rather than a genuine physics/MCDM disagreement; see physics_validation_summary_rajasthan.txt for the full caveat-aware interpretation.
- **Physics-validation band: NEGATIVE** (rho<=0.4, genuine negative result).
- **The Top-1/2/3 ordering shown above is the MCDM CONSENSUS ONLY — it is NOT independently confirmed by physics simulation for this cluster** (rho=0.258, band=NEGATIVE). See physics_validation_summary_rajasthan.txt for the full per-cluster interpretation before quoting this Top-3 as physics-validated.

### 8. Caveats

- **Imputed/unmeasured property in Top-3 candidate Paraffin/HDPE PCM2:** latent heat, solid density, liquid density, solid specific heat, liquid specific heat, solid thermal conductivity, liquid thermal conductivity, thermal conductivity, cycling-stability count, flammability rating.
- **Imputed/unmeasured property in Top-3 candidate savE® OM50:** thermal conductivity.
- **Imputed/unmeasured property in Top-3 candidate Paraffin/HDPE PCM6:** latent heat, solid density, liquid density, solid specific heat, liquid specific heat, solid thermal conductivity, liquid thermal conductivity, thermal conductivity, cycling-stability count, flammability rating.
- **Feasibility window was relaxed** by +/-8K (4 round(s)) for this cluster, AND the latent-heat floor was calibrated down from kappa=0.7 to kappa=0.5 (status=in_band) — this Top-3 would not exist under the fixed-kappa=0.7 diagnostic run (0 survivors there).
- **Kendall's W = 0.5539, BELOW the 0.6 ambiguous-agreement threshold** (plan doc Section 9.5) — the four MCDM methods did not strongly agree with each other for this cluster's candidate pool.
- **Physics validation does not confirm this Top-3 ranking** (rho=0.258, band=NEGATIVE) — treat the ordering above as the MCDM consensus, not an independently-verified performance ranking, for this cluster.