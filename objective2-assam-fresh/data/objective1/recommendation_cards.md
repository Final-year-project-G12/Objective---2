# Rajasthan — Phase 8 Recommendation Cards

Pure aggregation of Phase 4 (cluster_profile_cards_rajasthan.md), Phase 6 (mcdm_rankings_rajasthan.csv), and Phase 7 (physics_validation_rajasthan.csv) — no new PCM-selection decisions made here. Cross-phase cluster-identity precondition PASSED (fingerprint 2552_3_1786473072.891; medoid cross-check on all 3 clusters) — see this script's own console log for the full check.

## Cross-cluster summary

| Cluster | #1 pick | Borda score | MC Top-3 incl. % | Spearman rho (vs Borda) | Caveats |
|---|---|---|---|---|---|
| 0 | RT50† | 25.00 | 90.8% | -0.385 | rho<=0, W<0.6 |
| 1 | savE® OM50† | 50.00 | 83.2% | 0.125 | rho<0.4 |
| 2 | savE® OM50† | 59.00 | 93.9% | -0.097 | rho<=0 |

† see this cluster's own card below (Caveats section) before quoting this row on its own — this table intentionally carries only a pointer, not the full caveat text, so it stays scannable; the full text is one section away, not three.


---

## Cluster 0

### 1. Cluster identity

- **Cluster ID:** 0
- **Medoid point:** RJP_0132 — Udaipur, Rajasthan (lat/lon 24.375, 74.125)
- **Member point count:** 114
- **State distribution:** Rajasthan: 100.0%
- **Total population covered:** 22,568,150
- **Mean maximum membership probability:** 0.9981

### 2. Climate signature (population-weighted mean +/- std, from cluster_profile_cards_rajasthan.md — not recomputed)

| Index | Mean | Std |
|---|---|---|
| Ta_mean | 27.092 | 0.687 |
| Ta_p95 | 35.595 | 1.320 |
| Ta_p05 | 17.456 | 1.000 |
| T_sunrise_mean | 21.887 | 0.608 |
| T_noon_mean | 29.712 | 0.714 |
| T_sunset_mean | 29.677 | 0.812 |
| diurnal_gradient | 7.825 | 0.380 |
| GHI_noon_mean | 736.474 | 8.692 |
| GHI_sunset_mean | 56.901 | 1.299 |
| GHI_daily_kWh | 5.170 | 0.080 |
| kt_noon_mean | 0.850 | 0.014 |
| kt_noon_std | 0.223 | 0.014 |
| kt_daily_mean | 0.867 | 0.008 |
| kt_daily_std | 0.179 | 0.013 |
| SAI | 0.867 | 0.008 |
| cloudy_frac | 0.016 | 0.005 |
| CCI | 0.648 | 0.038 |
| HDD18 | 1099.960 | 442.039 |
| CDD24 | 12347.931 | 1503.629 |
| DTR_true | 13.523 | 0.212 |
| RH_sunrise_mean | 70.923 | 2.037 |
| HSI_sunrise | 20.706 | 0.525 |
| wind_noon_mean | 2.634 | 0.219 |
| wind_sunset_mean | 2.261 | 0.142 |
| daylength_mean | 12.153 | 0.002 |
| daylength_amplitude | 1.535 | 0.050 |
| seasonality | 0.219 | 0.011 |
| monsoon_index | 0.930 | 0.035 |

*Auto-generated physical description (Phase 4, review before publishing):* Cooler, arid/low-monsoon, erratic solar resource, short low-clearness runs.

### 3. Derived targets

- **Tm_target_C:** 57.0 C — assumes an **INDIRECT** system configuration (T_delivery=50C + heat-exchanger approach dT=7C, per 04_climate_signature_rajasthan.py's TM_TARGET_C definition, Objective1_PCM_Climate_Framework_Plan_v3 Section 6.3).
- **Tm_target_capped_C:** 48.4 C (poor-insolation-day achievable ceiling, kt_p05-derived — differs from the base target above).
- **L_required_kJ_per_kg:** 626 kJ/kg (CEILING, not an achievability bar — see 04_climate_signature_rajasthan.py's docstring).
- **Dominant constraint driving the Top-1 pick:** melting-point fitness (from the criterion-contribution decomposition — see each Top-3 candidate's 'Criterion contributions' line under Rank 1/2/3 -> item 6, below).

### 4. Candidates screened

- **Entered Phase 5's filter:** 62
- **Survived at fixed kappa=0.7 (primary/diagnostic run):** 0
- **Survived at calibrated kappa=0.2 (status=in_band, the pool Phase 6/7/8 actually rank/simulate/report):** 9  (candidate_pool_status: **healthy**)
- **Melting-window relaxation:** widened +/-8K (4 relaxation round(s))
- **Exclusion breakdown (fixed kappa=0.7 run, 62 candidates evaluated):**
    - c1 melting window: 3 excluded
    - c2 absolute band [42,70C]: 1 excluded
    - c3 latent heat floor (kappa=0.7): 62 excluded
    - c4 cycling (>=300): 0 excluded, 7 flagged unreported (not excluded)
    - c5 supercooling (<=8K): 0 excluded, 7 flagged unknown (not excluded)
    - c6 charging feasibility (Tm<=Tm_target_capped): 50 excluded
    - c7 corrosion veto: 0 excluded
    - c8 safety exclusion: 0 excluded

### 5-6. Rank 1 / 2 / 3, with per-candidate criterion contributions (item 6)

**[FLAG] Borda and Copeland DISAGREE on Top-3 membership for this cluster** — Borda Top-3: ['RT50', 'RT45HC', 'Lauric acid (C12)']; Copeland Top-3: ['RT45HC', 'RT50', 'n-Docosane (C22)']. Both reported below/in the summary rather than picking one silently.

**#1 — RT50** (Rubitherm Technologies, Organic (RT-line))
- Tm=48.0 C, L=160 kJ/kg, k=0.200 W/m.K
- Consensus Borda score: **25.00**  |  Copeland score: **8**  |  Per-method rank: TOPSIS=1, PROMETHEE-II=1, VIKOR=1, GRA=8
- Monte Carlo Top-3 inclusion probability: **90.8%** (Top-1 retention: 61.6%)
- **Criterion contributions:** RT50 ranked #1 driven primarily by melting-point fitness (+0.13) and supercooling (inverse) (+0.12), partially offset by below-peer latent heat (-0.01).
- **Simulated performance (Phase 7):** annual solar fraction 64.2%, 4285 hours/year meeting delivery temp

**#2 — RT45HC** (Rubitherm Technologies, Organic (RT-line))
- Tm=45.0 C, L=240 kJ/kg, k=0.200 W/m.K
- Consensus Borda score: **22.00**  |  Copeland score: **4**  |  Per-method rank: TOPSIS=2, PROMETHEE-II=3, VIKOR=3, GRA=6
- Monte Carlo Top-3 inclusion probability: **60.8%** (Top-1 retention: 20.8%)
- **Criterion contributions:** RT45HC ranked #2 driven primarily by supercooling (inverse) (+0.07) and latent heat (+0.01), partially offset by below-peer melting-point fitness (-0.04).
- **Simulated performance (Phase 7):** annual solar fraction 64.2%, 4286 hours/year meeting delivery temp

**#3 — Lauric acid (C12)** (Literature, Organic fatty acid)
- Tm=44.8 C, L=184 kJ/kg, k=0.200 W/m.K
- Consensus Borda score: **20.00**  |  Copeland score: **1**  |  Per-method rank: TOPSIS=3, PROMETHEE-II=5, VIKOR=5, GRA=3
- Monte Carlo Top-3 inclusion probability: **62.3%** (Top-1 retention: 9.4%)
- **Criterion contributions:** Lauric acid (C12) ranked #3 driven primarily by supercooling (inverse) (+0.07) and cycling stability (+0.00), partially offset by below-peer melting-point fitness (-0.04).
- **Simulated performance (Phase 7):** annual solar fraction 63.9%, 4270 hours/year meeting delivery temp

### 7. Physics validation context

- **Spearman rho (MCDM Borda rank vs. simulated solar-fraction rank):** -0.385 (Copeland-vs-simulation rho=-0.402, reported alongside Borda since they disagreed on Top-3)
- **Context for this rho — read together, not the bare number alone:** n=9 candidates, Kendall's W=0.3875 (ambiguous, BELOW the 0.6 ambiguous threshold), candidate_pool_status=healthy.
- **This cluster's rho is PROVISIONAL pending the Phase 5/6 candidate-pool expansion** — with W<0.6 and/or an undersized pool, a low rho here may reflect the MCDM ranking's own pre-existing instability rather than a genuine physics/MCDM disagreement; see physics_validation_summary_rajasthan.txt for the full caveat-aware interpretation.
- **Physics-validation band: NEGATIVE** (rho<=0.4, genuine negative result).
- **The Top-1/2/3 ordering shown above is the MCDM CONSENSUS ONLY — it is NOT independently confirmed by physics simulation for this cluster** (rho=-0.385, band=NEGATIVE). See physics_validation_summary_rajasthan.txt for the full per-cluster interpretation before quoting this Top-3 as physics-validated.

### 8. Caveats

- **Imputed/unmeasured property in Top-3 candidate RT50:** solid thermal conductivity, liquid thermal conductivity, cycling-stability count, flammability rating.
- **Imputed/unmeasured property in Top-3 candidate RT45HC:** solid thermal conductivity, liquid thermal conductivity, cycling-stability count, flammability rating.
- **Imputed/unmeasured property in Top-3 candidate Lauric acid (C12):** solid density, solid specific heat, solid thermal conductivity, thermal conductivity, cycling-stability count, flammability rating.
- **Feasibility window was relaxed** by +/-8K (4 round(s)) for this cluster, AND the latent-heat floor was calibrated down from kappa=0.7 to kappa=0.2 (status=in_band) — this Top-3 would not exist under the fixed-kappa=0.7 diagnostic run (0 survivors there).
- **Kendall's W = 0.3875, BELOW the 0.6 ambiguous-agreement threshold** (plan doc Section 9.5) — the four MCDM methods did not strongly agree with each other for this cluster's candidate pool.
- **Physics validation does not confirm this Top-3 ranking** (rho=-0.385, band=NEGATIVE) — treat the ordering above as the MCDM consensus, not an independently-verified performance ranking, for this cluster.

---

## Cluster 1

### 1. Cluster identity

- **Cluster ID:** 1
- **Medoid point:** RJP_0202 — Nagaur, Rajasthan (lat/lon 26.875, 73.625)
- **Member point count:** 103
- **State distribution:** Rajasthan: 100.0%
- **Total population covered:** 17,959,813
- **Mean maximum membership probability:** 0.9956

### 2. Climate signature (population-weighted mean +/- std, from cluster_profile_cards_rajasthan.md — not recomputed)

| Index | Mean | Std |
|---|---|---|
| Ta_mean | 27.783 | 0.595 |
| Ta_p95 | 36.443 | 0.736 |
| Ta_p05 | 16.200 | 1.674 |
| T_sunrise_mean | 21.931 | 0.472 |
| T_noon_mean | 30.353 | 0.476 |
| T_sunset_mean | 31.066 | 1.049 |
| diurnal_gradient | 8.422 | 0.233 |
| GHI_noon_mean | 764.241 | 8.420 |
| GHI_sunset_mean | 57.602 | 1.611 |
| GHI_daily_kWh | 5.352 | 0.145 |
| kt_noon_mean | 0.896 | 0.013 |
| kt_noon_std | 0.171 | 0.018 |
| kt_daily_mean | 0.902 | 0.014 |
| kt_daily_std | 0.135 | 0.010 |
| SAI | 0.902 | 0.014 |
| cloudy_frac | 0.005 | 0.002 |
| CCI | 0.798 | 0.048 |
| HDD18 | 1634.045 | 620.729 |
| CDD24 | 15837.033 | 1901.590 |
| DTR_true | 13.816 | 0.308 |
| RH_sunrise_mean | 67.404 | 2.101 |
| HSI_sunrise | 20.597 | 0.371 |
| wind_noon_mean | 3.237 | 0.362 |
| wind_sunset_mean | 2.880 | 0.356 |
| daylength_mean | 12.158 | 0.003 |
| daylength_amplitude | 1.685 | 0.084 |
| seasonality | 0.209 | 0.015 |
| monsoon_index | 1.040 | 0.038 |

*Auto-generated physical description (Phase 4, review before publishing):* Hot, monsoon-influenced, steady solar resource, long low-clearness runs (high autonomy demand).

### 3. Derived targets

- **Tm_target_C:** 57.0 C — assumes an **INDIRECT** system configuration (T_delivery=50C + heat-exchanger approach dT=7C, per 04_climate_signature_rajasthan.py's TM_TARGET_C definition, Objective1_PCM_Climate_Framework_Plan_v3 Section 6.3).
- **Tm_target_capped_C:** 52.3 C (poor-insolation-day achievable ceiling, kt_p05-derived — differs from the base target above).
- **L_required_kJ_per_kg:** 608 kJ/kg (CEILING, not an achievability bar — see 04_climate_signature_rajasthan.py's docstring).
- **Dominant constraint driving the Top-1 pick:** supercooling (inverse) (from the criterion-contribution decomposition — see each Top-3 candidate's 'Criterion contributions' line under Rank 1/2/3 -> item 6, below).

### 4. Candidates screened

- **Entered Phase 5's filter:** 62
- **Survived at fixed kappa=0.7 (primary/diagnostic run):** 0
- **Survived at calibrated kappa=0.3 (status=in_band, the pool Phase 6/7/8 actually rank/simulate/report):** 14  (candidate_pool_status: **healthy**)
- **Melting-window relaxation:** widened +/-8K (4 relaxation round(s))
- **Exclusion breakdown (fixed kappa=0.7 run, 62 candidates evaluated):**
    - c1 melting window: 3 excluded
    - c2 absolute band [42,70C]: 1 excluded
    - c3 latent heat floor (kappa=0.7): 62 excluded
    - c4 cycling (>=300): 0 excluded, 7 flagged unreported (not excluded)
    - c5 supercooling (<=8K): 0 excluded, 7 flagged unknown (not excluded)
    - c6 charging feasibility (Tm<=Tm_target_capped): 39 excluded
    - c7 corrosion veto: 0 excluded
    - c8 safety exclusion: 0 excluded

### 5-6. Rank 1 / 2 / 3, with per-candidate criterion contributions (item 6)

**#1 — savE® OM50** (Pluss Advanced Technologies, Organic)
- Tm=50.0 C, L=189 kJ/kg, k=0.336 W/m.K
- Consensus Borda score: **50.00**  |  Copeland score: **13**  |  Per-method rank: TOPSIS=1, PROMETHEE-II=1, VIKOR=1, GRA=3
- Monte Carlo Top-3 inclusion probability: **83.2%** (Top-1 retention: 43.6%)
- **Criterion contributions:** savE® OM50 ranked #1 driven primarily by supercooling (inverse) (+0.06) and melting-point fitness (+0.02), partially offset by below-peer latent heat (-0.00).
- **Simulated performance (Phase 7):** annual solar fraction 66.0%, 4403 hours/year meeting delivery temp

**#2 — Paraffin/HDPE PCM3** (Literature, Organic blend)
- Tm=49.9 C, L=187 kJ/kg, k=0.206 W/m.K
- Consensus Borda score: **44.00**  |  Copeland score: **11**  |  Per-method rank: TOPSIS=2, PROMETHEE-II=3, VIKOR=3, GRA=4
- Monte Carlo Top-3 inclusion probability: **69.6%** (Top-1 retention: 27.7%)
- **Criterion contributions:** Paraffin/HDPE PCM3 ranked #2 driven primarily by supercooling (inverse) (+0.06) and melting-point fitness (+0.02), partially offset by below-peer latent heat (-0.00).
- **Simulated performance (Phase 7):** annual solar fraction 65.3%, 4393 hours/year meeting delivery temp

**#3 — Paraffin/HDPE PCM6** (Literature, Organic blend)
- Tm=50.3 C, L=187 kJ/kg, k=0.206 W/m.K
- Consensus Borda score: **37.00**  |  Copeland score: **9**  |  Per-method rank: TOPSIS=3, PROMETHEE-II=7, VIKOR=4, GRA=5
- Monte Carlo Top-3 inclusion probability: **37.7%** (Top-1 retention: 7.8%)
- **Criterion contributions:** Paraffin/HDPE PCM6 ranked #3 driven primarily by melting-point fitness (+0.03) and supercooling (inverse) (+0.01), partially offset by below-peer latent heat (-0.00).
- **Simulated performance (Phase 7):** annual solar fraction 65.3%, 4393 hours/year meeting delivery temp

### 7. Physics validation context

- **Spearman rho (MCDM Borda rank vs. simulated solar-fraction rank):** 0.125
- **Context for this rho — read together, not the bare number alone:** n=14 candidates, Kendall's W=0.6346 (moderate), candidate_pool_status=healthy.
- **Physics-validation band: NEGATIVE** (rho<=0.4, genuine negative result).
- **The Top-1/2/3 ordering shown above is the MCDM CONSENSUS ONLY — it is NOT independently confirmed by physics simulation for this cluster** (rho=0.125, band=NEGATIVE). See physics_validation_summary_rajasthan.txt for the full per-cluster interpretation before quoting this Top-3 as physics-validated.

### 8. Caveats

- **Imputed/unmeasured property in Top-3 candidate savE® OM50:** thermal conductivity.
- **Imputed/unmeasured property in Top-3 candidate Paraffin/HDPE PCM3:** latent heat, solid density, liquid density, solid specific heat, liquid specific heat, solid thermal conductivity, liquid thermal conductivity, thermal conductivity, cycling-stability count, flammability rating.
- **Imputed/unmeasured property in Top-3 candidate Paraffin/HDPE PCM6:** latent heat, solid density, liquid density, solid specific heat, liquid specific heat, solid thermal conductivity, liquid thermal conductivity, thermal conductivity, cycling-stability count, flammability rating.
- **Feasibility window was relaxed** by +/-8K (4 round(s)) for this cluster, AND the latent-heat floor was calibrated down from kappa=0.7 to kappa=0.3 (status=in_band) — this Top-3 would not exist under the fixed-kappa=0.7 diagnostic run (0 survivors there).
- **Physics validation does not confirm this Top-3 ranking** (rho=0.125, band=NEGATIVE) — treat the ordering above as the MCDM consensus, not an independently-verified performance ranking, for this cluster.

---

## Cluster 2

### 1. Cluster identity

- **Cluster ID:** 2
- **Medoid point:** RJP_0055 — Dausa, Rajasthan (lat/lon 26.625, 76.375)
- **Member point count:** 103
- **State distribution:** Rajasthan: 100.0%
- **Total population covered:** 29,775,240
- **Mean maximum membership probability:** 0.9974

### 2. Climate signature (population-weighted mean +/- std, from cluster_profile_cards_rajasthan.md — not recomputed)

| Index | Mean | Std |
|---|---|---|
| Ta_mean | 26.524 | 0.388 |
| Ta_p95 | 35.863 | 0.504 |
| Ta_p05 | 14.615 | 0.912 |
| T_sunrise_mean | 21.266 | 0.476 |
| T_noon_mean | 29.441 | 0.334 |
| T_sunset_mean | 28.865 | 0.544 |
| diurnal_gradient | 8.175 | 0.367 |
| GHI_noon_mean | 742.229 | 8.156 |
| GHI_sunset_mean | 53.266 | 1.804 |
| GHI_daily_kWh | 4.997 | 0.166 |
| kt_noon_mean | 0.879 | 0.011 |
| kt_noon_std | 0.191 | 0.020 |
| kt_daily_mean | 0.874 | 0.011 |
| kt_daily_std | 0.157 | 0.009 |
| SAI | 0.874 | 0.011 |
| cloudy_frac | 0.009 | 0.002 |
| CCI | 0.767 | 0.053 |
| HDD18 | 2237.040 | 329.788 |
| CDD24 | 14788.921 | 1803.687 |
| DTR_true | 13.696 | 0.187 |
| RH_sunrise_mean | 72.961 | 2.926 |
| HSI_sunrise | 20.260 | 0.399 |
| wind_noon_mean | 2.557 | 0.222 |
| wind_sunset_mean | 2.139 | 0.164 |
| daylength_mean | 12.159 | 0.003 |
| daylength_amplitude | 1.723 | 0.079 |
| seasonality | 0.225 | 0.021 |
| monsoon_index | 1.028 | 0.047 |

*Auto-generated physical description (Phase 4, review before publishing):* Cooler, arid/low-monsoon, erratic solar resource, short low-clearness runs.

### 3. Derived targets

- **Tm_target_C:** 57.0 C — assumes an **INDIRECT** system configuration (T_delivery=50C + heat-exchanger approach dT=7C, per 04_climate_signature_rajasthan.py's TM_TARGET_C definition, Objective1_PCM_Climate_Framework_Plan_v3 Section 6.3).
- **Tm_target_capped_C:** 51.1 C (poor-insolation-day achievable ceiling, kt_p05-derived — differs from the base target above).
- **L_required_kJ_per_kg:** 640 kJ/kg (CEILING, not an achievability bar — see 04_climate_signature_rajasthan.py's docstring).
- **Dominant constraint driving the Top-1 pick:** supercooling (inverse) (from the criterion-contribution decomposition — see each Top-3 candidate's 'Criterion contributions' line under Rank 1/2/3 -> item 6, below).

### 4. Candidates screened

- **Entered Phase 5's filter:** 62
- **Survived at fixed kappa=0.7 (primary/diagnostic run):** 0
- **Survived at calibrated kappa=0.2 (status=in_band, the pool Phase 6/7/8 actually rank/simulate/report):** 16  (candidate_pool_status: **healthy**)
- **Melting-window relaxation:** widened +/-8K (4 relaxation round(s))
- **Exclusion breakdown (fixed kappa=0.7 run, 62 candidates evaluated):**
    - c1 melting window: 4 excluded
    - c2 absolute band [42,70C]: 1 excluded
    - c3 latent heat floor (kappa=0.7): 62 excluded
    - c4 cycling (>=300): 0 excluded, 7 flagged unreported (not excluded)
    - c5 supercooling (<=8K): 0 excluded, 7 flagged unknown (not excluded)
    - c6 charging feasibility (Tm<=Tm_target_capped): 42 excluded
    - c7 corrosion veto: 0 excluded
    - c8 safety exclusion: 0 excluded

### 5-6. Rank 1 / 2 / 3, with per-candidate criterion contributions (item 6)

**#1 — savE® OM50** (Pluss Advanced Technologies, Organic)
- Tm=50.0 C, L=189 kJ/kg, k=0.336 W/m.K
- Consensus Borda score: **59.00**  |  Copeland score: **15**  |  Per-method rank: TOPSIS=1, PROMETHEE-II=1, VIKOR=1, GRA=2
- Monte Carlo Top-3 inclusion probability: **93.9%** (Top-1 retention: 55.8%)
- **Criterion contributions:** savE® OM50 ranked #1 driven primarily by supercooling (inverse) (+0.06) and melting-point fitness (+0.04), partially offset by below-peer latent heat (-0.00).
- **Simulated performance (Phase 7):** annual solar fraction 64.5%, 4346 hours/year meeting delivery temp

**#2 — Paraffin/HDPE PCM3** (Literature, Organic blend)
- Tm=49.9 C, L=187 kJ/kg, k=0.206 W/m.K
- Consensus Borda score: **55.00**  |  Copeland score: **13**  |  Per-method rank: TOPSIS=2, PROMETHEE-II=2, VIKOR=2, GRA=3
- Monte Carlo Top-3 inclusion probability: **85.2%** (Top-1 retention: 30.7%)
- **Criterion contributions:** Paraffin/HDPE PCM3 ranked #2 driven primarily by supercooling (inverse) (+0.06) and melting-point fitness (+0.04), partially offset by below-peer thermal conductivity (-0.00).
- **Simulated performance (Phase 7):** annual solar fraction 63.9%, 4331 hours/year meeting delivery temp

**#3 — Paraffin/HDPE PCM6** (Literature, Organic blend)
- Tm=50.3 C, L=187 kJ/kg, k=0.206 W/m.K
- Consensus Borda score: **48.00**  |  Copeland score: **11**  |  Per-method rank: TOPSIS=3, PROMETHEE-II=6, VIKOR=3, GRA=4
- Monte Carlo Top-3 inclusion probability: **52.0%** (Top-1 retention: 10.5%)
- **Criterion contributions:** Paraffin/HDPE PCM6 ranked #3 driven primarily by melting-point fitness (+0.06) and supercooling (inverse) (+0.00), partially offset by below-peer thermal conductivity (-0.00).
- **Simulated performance (Phase 7):** annual solar fraction 63.9%, 4331 hours/year meeting delivery temp

### 7. Physics validation context

- **Spearman rho (MCDM Borda rank vs. simulated solar-fraction rank):** -0.097
- **Context for this rho — read together, not the bare number alone:** n=16 candidates, Kendall's W=0.6342 (moderate), candidate_pool_status=healthy.
- **Physics-validation band: NEGATIVE** (rho<=0.4, genuine negative result).
- **The Top-1/2/3 ordering shown above is the MCDM CONSENSUS ONLY — it is NOT independently confirmed by physics simulation for this cluster** (rho=-0.097, band=NEGATIVE). See physics_validation_summary_rajasthan.txt for the full per-cluster interpretation before quoting this Top-3 as physics-validated.

### 8. Caveats

- **Imputed/unmeasured property in Top-3 candidate savE® OM50:** thermal conductivity.
- **Imputed/unmeasured property in Top-3 candidate Paraffin/HDPE PCM3:** latent heat, solid density, liquid density, solid specific heat, liquid specific heat, solid thermal conductivity, liquid thermal conductivity, thermal conductivity, cycling-stability count, flammability rating.
- **Imputed/unmeasured property in Top-3 candidate Paraffin/HDPE PCM6:** latent heat, solid density, liquid density, solid specific heat, liquid specific heat, solid thermal conductivity, liquid thermal conductivity, thermal conductivity, cycling-stability count, flammability rating.
- **Feasibility window was relaxed** by +/-8K (4 round(s)) for this cluster, AND the latent-heat floor was calibrated down from kappa=0.7 to kappa=0.2 (status=in_band) — this Top-3 would not exist under the fixed-kappa=0.7 diagnostic run (0 survivors there).
- **Physics validation does not confirm this Top-3 ranking** (rho=-0.097, band=NEGATIVE) — treat the ordering above as the MCDM consensus, not an independently-verified performance ranking, for this cluster.