# Rajasthan — Phase 8 Recommendation Cards

Pure aggregation of Phase 4 (cluster_profile_cards_rajasthan.md), Phase 6 (mcdm_full_rankings.csv), and Phase 7 (physics_validation_rajasthan.csv) — no new PCM-selection decisions made here. Cross-phase cluster-identity precondition PASSED (fingerprint 2557_3_1789381466.393; medoid cross-check on all 3 clusters) — see this script's own console log for the full check.

## Cross-cluster summary

| Cluster | #1 pick | Borda score | MC Top-3 incl. % | Spearman rho (vs Borda) | Caveats |
|---|---|---|---|---|---|
| 0 | Palmitic-stearic acid/Expanded graphite† | 10.00 | 99.5% | 0.105 | rho<0.4, undersized pool |
| 1 | PureTemp 60† | 27.00 | 99.3% | -0.190 | rho<=0 |
| 2 | n-Heptacosane (C27)† | 36.00 | 91.6% | -0.091 | rho<=0, W<0.6 |

† see this cluster's own card below (Caveats section) before quoting this row on its own — this table intentionally carries only a pointer, not the full caveat text, so it stays scannable; the full text is one section away, not three.


---

## Cluster 0

### 1. Cluster identity

- **Cluster ID:** 0
- **Medoid point:** RJP_0132 — Udaipur, Rajasthan (lat/lon 24.375, 74.125)
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

- **Tm_target_C:** 67.0 C — assumes an **INDIRECT** system configuration (T_delivery=60C + heat-exchanger approach dT=7C, per 04_climate_signature_rajasthan.py's TM_TARGET_C definition, Objective1_PCM_Climate_Framework_Plan_v3 Section 6.3).
- **Tm_target_capped_C:** 55.5 C (poor-insolation-day achievable ceiling, kt_p05-derived — differs from the base target above).
- **L_required_kJ_per_kg:** 438 kJ/kg (CEILING, not an achievability bar — see 04_climate_signature_rajasthan.py's docstring).
- **Dominant constraint driving the Top-1 pick:** melting-point fitness (from the criterion-contribution decomposition — see each Top-3 candidate's 'Criterion contributions' line under Rank 1/2/3 -> item 6, below).

### 4. Candidates screened

- **Entered Phase 5's filter:** 62
- **Survived at fixed kappa=0.7 (primary/diagnostic run):** 0
- **Survived at calibrated kappa=0.0 (status=insufficient_even_at_kappa_0, the pool Phase 6/7/8 actually rank/simulate/report):** 4  (candidate_pool_status: **undersized**)
- **Melting-window relaxation:** widened +/-8K (4 relaxation round(s))
- **Exclusion breakdown (fixed kappa=0.7 run, 62 candidates evaluated):**
    - c1 melting window: 30 excluded
    - c2 absolute band [42,70C]: 1 excluded
    - c3 latent heat floor (kappa=0.7): 62 excluded
    - c4 cycling (>=300): 0 excluded, 7 flagged unreported (not excluded)
    - c5 supercooling (<=8K): 0 excluded, 7 flagged unknown (not excluded)
    - c6 charging feasibility (Tm<=Tm_target_capped): 28 excluded
    - c7 corrosion veto: 0 excluded
    - c8 safety exclusion: 0 excluded

### 5-6. Rank 1 / 2 / 3, with per-candidate criterion contributions (item 6)

**#1 — Palmitic-stearic acid/Expanded graphite** (Literature, Organic/eutectic composite)
- Tm=55.2 C, L=176 kJ/kg, k=0.452 W/m.K
- Consensus Borda score: **10.00**  |  Copeland score: **2**  |  Per-method rank: TOPSIS=1, PROMETHEE-II=2, VIKOR=1, GRA=2
- Monte Carlo Top-3 inclusion probability: **99.5%** (Top-1 retention: 52.4%)
- **Criterion contributions:** Palmitic-stearic acid/Expanded graphite ranked #1 driven primarily by melting-point fitness (+0.07) and supercooling (inverse) (+0.04).
- **Simulated performance (Phase 7):** annual solar fraction 65.7%, 4283 hours/year meeting delivery temp

**#2 — savE® OM55** (Pluss Advanced Technologies, Organic)
- Tm=55.0 C, L=188 kJ/kg, k=0.429 W/m.K
- Consensus Borda score: **10.00**  |  Copeland score: **2**  |  Per-method rank: TOPSIS=2, PROMETHEE-II=1, VIKOR=2, GRA=1
- Monte Carlo Top-3 inclusion probability: **99.9%** (Top-1 retention: 67.6%)
- **Criterion contributions:** savE® OM55 ranked #2 driven primarily by melting-point fitness (+0.03) and supercooling (inverse) (+0.03), partially offset by below-peer thermal conductivity (-0.00).
- **Simulated performance (Phase 7):** annual solar fraction 65.5%, 4278 hours/year meeting delivery temp

**#3 — Myristic acid/NBR-0.5** (Literature, Organic/polymer blend)
- Tm=54.6 C, L=142 kJ/kg, k=0.462 W/m.K
- Consensus Borda score: **4.00**  |  Copeland score: **-1**  |  Per-method rank: TOPSIS=3, PROMETHEE-II=3, VIKOR=3, GRA=3
- Monte Carlo Top-3 inclusion probability: **85.8%** (Top-1 retention: 2.8%)
- **Criterion contributions:** Myristic acid/NBR-0.5 ranked #3 driven primarily by thermal conductivity (+0.00), partially offset by below-peer supercooling (inverse) (-0.03).
- **Simulated performance (Phase 7):** annual solar fraction 65.5%, 4276 hours/year meeting delivery temp

### 7. Physics validation context

- **Spearman rho (MCDM Borda rank vs. simulated solar-fraction rank):** 0.105
- **Context for this rho — read together, not the bare number alone:** n=4 candidates, Kendall's W=0.9000 (strong), candidate_pool_status=undersized (undersized, n<8).
- **This cluster's rho is PROVISIONAL pending the Phase 5/6 candidate-pool expansion** — with W<0.6 and/or an undersized pool, a low rho here may reflect the MCDM ranking's own pre-existing instability rather than a genuine physics/MCDM disagreement; see physics_validation_summary_rajasthan.txt for the full caveat-aware interpretation.
- **Physics-validation band: NEGATIVE** (rho<=0.4, genuine negative result).
- **The Top-1/2/3 ordering shown above is the MCDM CONSENSUS ONLY — it is NOT independently confirmed by physics simulation for this cluster** (rho=0.105, band=NEGATIVE). See physics_validation_summary_rajasthan.txt for the full per-cluster interpretation before quoting this Top-3 as physics-validated.

### 8. Caveats

- **Imputed/unmeasured property in Top-3 candidate Palmitic-stearic acid/Expanded graphite:** solid density, liquid density, solid specific heat, liquid specific heat, solid thermal conductivity, liquid thermal conductivity, thermal conductivity, cycling-stability count, flammability rating.
- **Imputed/unmeasured property in Top-3 candidate savE® OM55:** thermal conductivity.
- **Imputed/unmeasured property in Top-3 candidate Myristic acid/NBR-0.5:** solid density, liquid density, solid specific heat, liquid specific heat, solid thermal conductivity, liquid thermal conductivity, thermal conductivity, cycling-stability count, flammability rating.
- **Feasibility window was relaxed** by +/-8K (4 round(s)) for this cluster, AND the latent-heat floor was calibrated down from kappa=0.7 to kappa=0.0 (status=insufficient_even_at_kappa_0) — this Top-3 would not exist under the fixed-kappa=0.7 diagnostic run (0 survivors there).
- **Candidate pool undersized** (4 survivors, below the 8-20 'healthy' band) — Top-3 from this few candidates is still meaningful but carries more sampling noise than a healthy-sized pool.
- **Physics validation does not confirm this Top-3 ranking** (rho=0.105, band=NEGATIVE) — treat the ordering above as the MCDM consensus, not an independently-verified performance ranking, for this cluster.

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

- **Tm_target_C:** 67.0 C — assumes an **INDIRECT** system configuration (T_delivery=60C + heat-exchanger approach dT=7C, per 04_climate_signature_rajasthan.py's TM_TARGET_C definition, Objective1_PCM_Climate_Framework_Plan_v3 Section 6.3).
- **Tm_target_capped_C:** 61.1 C (poor-insolation-day achievable ceiling, kt_p05-derived — differs from the base target above).
- **L_required_kJ_per_kg:** 427 kJ/kg (CEILING, not an achievability bar — see 04_climate_signature_rajasthan.py's docstring).
- **Dominant constraint driving the Top-1 pick:** melting-point fitness (from the criterion-contribution decomposition — see each Top-3 candidate's 'Criterion contributions' line under Rank 1/2/3 -> item 6, below).

### 4. Candidates screened

- **Entered Phase 5's filter:** 62
- **Survived at fixed kappa=0.7 (primary/diagnostic run):** 0
- **Survived at calibrated kappa=0.5 (status=in_band, the pool Phase 6/7/8 actually rank/simulate/report):** 8  (candidate_pool_status: **healthy**)
- **Melting-window relaxation:** widened +/-8K (4 relaxation round(s))
- **Exclusion breakdown (fixed kappa=0.7 run, 62 candidates evaluated):**
    - c1 melting window: 28 excluded
    - c2 absolute band [42,70C]: 1 excluded
    - c3 latent heat floor (kappa=0.7): 62 excluded
    - c4 cycling (>=300): 0 excluded, 7 flagged unreported (not excluded)
    - c5 supercooling (<=8K): 0 excluded, 7 flagged unknown (not excluded)
    - c6 charging feasibility (Tm<=Tm_target_capped): 19 excluded
    - c7 corrosion veto: 0 excluded
    - c8 safety exclusion: 0 excluded

### 5-6. Rank 1 / 2 / 3, with per-candidate criterion contributions (item 6)

**#1 — PureTemp 60** (PureTemp, Organic bio-based PCM)
- Tm=61.0 C, L=220 kJ/kg, k=0.208 W/m.K
- Consensus Borda score: **27.00**  |  Copeland score: **7**  |  Per-method rank: TOPSIS=1, PROMETHEE-II=1, VIKOR=1, GRA=2
- Monte Carlo Top-3 inclusion probability: **99.3%** (Top-1 retention: 78.1%)
- **Criterion contributions:** PureTemp 60 ranked #1 driven primarily by melting-point fitness (+0.27) and supercooling (inverse) (+0.02), partially offset by below-peer latent heat (-0.00).
- **Simulated performance (Phase 7):** annual solar fraction 66.3%, 4375 hours/year meeting delivery temp

**#2 — CrodaTherm 60** (CrodaTherm, Organic PCM)
- Tm=59.8 C, L=217 kJ/kg, k=0.200 W/m.K
- Consensus Borda score: **23.00**  |  Copeland score: **5**  |  Per-method rank: TOPSIS=2, PROMETHEE-II=2, VIKOR=2, GRA=3
- Monte Carlo Top-3 inclusion probability: **93.6%** (Top-1 retention: 22.5%)
- **Criterion contributions:** CrodaTherm 60 ranked #2 driven primarily by melting-point fitness (+0.11) and supercooling (inverse) (+0.05), partially offset by below-peer latent heat (-0.00).
- **Simulated performance (Phase 7):** annual solar fraction 66.1%, 4374 hours/year meeting delivery temp

**#3 — n-Heptacosane (C27)** (Literature, Organic n-alkane)
- Tm=59.0 C, L=236 kJ/kg, k=0.210 W/m.K
- Consensus Borda score: **17.00**  |  Copeland score: **3**  |  Per-method rank: TOPSIS=3, PROMETHEE-II=3, VIKOR=3, GRA=6
- Monte Carlo Top-3 inclusion probability: **56.1%** (Top-1 retention: 2.9%)
- **Criterion contributions:** n-Heptacosane (C27) ranked #3 driven primarily by melting-point fitness (+0.03) and supercooling (inverse) (+0.02), partially offset by below-peer volumetric latent heat (-0.00).
- **Simulated performance (Phase 7):** annual solar fraction 66.4%, 4375 hours/year meeting delivery temp

### 7. Physics validation context

- **Spearman rho (MCDM Borda rank vs. simulated solar-fraction rank):** -0.190
- **Context for this rho — read together, not the bare number alone:** n=8 candidates, Kendall's W=0.7500 (moderate), candidate_pool_status=healthy.
- **Physics-validation band: NEGATIVE** (rho<=0.4, genuine negative result).
- **The Top-1/2/3 ordering shown above is the MCDM CONSENSUS ONLY — it is NOT independently confirmed by physics simulation for this cluster** (rho=-0.190, band=NEGATIVE). See physics_validation_summary_rajasthan.txt for the full per-cluster interpretation before quoting this Top-3 as physics-validated.

### 8. Caveats

- **Imputed/unmeasured property in Top-3 candidate PureTemp 60:** thermal conductivity, cycling-stability count, flammability rating.
- **Imputed/unmeasured property in Top-3 candidate CrodaTherm 60:** thermal conductivity, cycling-stability count, flammability rating.
- **Imputed/unmeasured property in Top-3 candidate n-Heptacosane (C27):** solid specific heat, liquid specific heat, solid thermal conductivity, liquid thermal conductivity, cycling-stability count, flammability rating.
- **Feasibility window was relaxed** by +/-8K (4 round(s)) for this cluster, AND the latent-heat floor was calibrated down from kappa=0.7 to kappa=0.5 (status=in_band) — this Top-3 would not exist under the fixed-kappa=0.7 diagnostic run (0 survivors there).
- **Physics validation does not confirm this Top-3 ranking** (rho=-0.190, band=NEGATIVE) — treat the ordering above as the MCDM consensus, not an independently-verified performance ranking, for this cluster.

---

## Cluster 2

### 1. Cluster identity

- **Cluster ID:** 2
- **Medoid point:** RJP_0083 — Jaipur, Rajasthan (lat/lon 26.625, 75.875)
- **Member point count:** 128
- **State distribution:** Rajasthan: 100.0%
- **Total population covered:** 34,514,036
- **Mean maximum membership probability:** 0.9994

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

- **Tm_target_C:** 67.0 C — assumes an **INDIRECT** system configuration (T_delivery=60C + heat-exchanger approach dT=7C, per 04_climate_signature_rajasthan.py's TM_TARGET_C definition, Objective1_PCM_Climate_Framework_Plan_v3 Section 6.3).
- **Tm_target_capped_C:** 59.2 C (poor-insolation-day achievable ceiling, kt_p05-derived — differs from the base target above).
- **L_required_kJ_per_kg:** 443 kJ/kg (CEILING, not an achievability bar — see 04_climate_signature_rajasthan.py's docstring).
- **Dominant constraint driving the Top-1 pick:** melting-point fitness (from the criterion-contribution decomposition — see each Top-3 candidate's 'Criterion contributions' line under Rank 1/2/3 -> item 6, below).

### 4. Candidates screened

- **Entered Phase 5's filter:** 62
- **Survived at fixed kappa=0.7 (primary/diagnostic run):** 0
- **Survived at calibrated kappa=0.3 (status=in_band, the pool Phase 6/7/8 actually rank/simulate/report):** 11  (candidate_pool_status: **healthy**)
- **Melting-window relaxation:** widened +/-8K (4 relaxation round(s))
- **Exclusion breakdown (fixed kappa=0.7 run, 62 candidates evaluated):**
    - c1 melting window: 28 excluded
    - c2 absolute band [42,70C]: 1 excluded
    - c3 latent heat floor (kappa=0.7): 62 excluded
    - c4 cycling (>=300): 0 excluded, 7 flagged unreported (not excluded)
    - c5 supercooling (<=8K): 0 excluded, 7 flagged unknown (not excluded)
    - c6 charging feasibility (Tm<=Tm_target_capped): 22 excluded
    - c7 corrosion veto: 0 excluded
    - c8 safety exclusion: 0 excluded

### 5-6. Rank 1 / 2 / 3, with per-candidate criterion contributions (item 6)

**#1 — n-Heptacosane (C27)** (Literature, Organic n-alkane)
- Tm=59.0 C, L=236 kJ/kg, k=0.210 W/m.K
- Consensus Borda score: **36.00**  |  Copeland score: **10**  |  Per-method rank: TOPSIS=1, PROMETHEE-II=1, VIKOR=1, GRA=5
- Monte Carlo Top-3 inclusion probability: **91.6%** (Top-1 retention: 55.1%)
- **Criterion contributions:** n-Heptacosane (C27) ranked #1 driven primarily by melting-point fitness (+0.21) and supercooling (inverse) (+0.02), partially offset by below-peer thermal conductivity (-0.01).
- **Simulated performance (Phase 7):** annual solar fraction 64.6%, 4270 hours/year meeting delivery temp

**#2 — PureTemp 58** (PureTemp, Organic bio-based PCM)
- Tm=58.0 C, L=225 kJ/kg, k=0.210 W/m.K
- Consensus Borda score: **33.00**  |  Copeland score: **8**  |  Per-method rank: TOPSIS=3, PROMETHEE-II=4, VIKOR=2, GRA=2
- Monte Carlo Top-3 inclusion probability: **73.1%** (Top-1 retention: 27.3%)
- **Criterion contributions:** PureTemp 58 ranked #2 driven primarily by melting-point fitness (+0.08) and supercooling (inverse) (+0.01), partially offset by below-peer thermal conductivity (-0.01).
- **Simulated performance (Phase 7):** annual solar fraction 65.1%, 4286 hours/year meeting delivery temp

**#3 — PlusICE A58** (PCM Products Ltd., Organic PCM)
- Tm=58.0 C, L=215 kJ/kg, k=0.203 W/m.K
- Consensus Borda score: **30.00**  |  Copeland score: **6**  |  Per-method rank: TOPSIS=2, PROMETHEE-II=6, VIKOR=3, GRA=3
- Monte Carlo Top-3 inclusion probability: **66.5%** (Top-1 retention: 18.8%)
- **Criterion contributions:** PlusICE A58 ranked #3 driven primarily by melting-point fitness (+0.08) and supercooling (inverse) (+0.01), partially offset by below-peer thermal conductivity (-0.01).
- **Simulated performance (Phase 7):** annual solar fraction 64.4%, 4266 hours/year meeting delivery temp

### 7. Physics validation context

- **Spearman rho (MCDM Borda rank vs. simulated solar-fraction rank):** -0.091
- **Context for this rho — read together, not the bare number alone:** n=11 candidates, Kendall's W=0.5545 (ambiguous, BELOW the 0.6 ambiguous threshold), candidate_pool_status=healthy.
- **This cluster's rho is PROVISIONAL pending the Phase 5/6 candidate-pool expansion** — with W<0.6 and/or an undersized pool, a low rho here may reflect the MCDM ranking's own pre-existing instability rather than a genuine physics/MCDM disagreement; see physics_validation_summary_rajasthan.txt for the full caveat-aware interpretation.
- **Physics-validation band: NEGATIVE** (rho<=0.4, genuine negative result).
- **The Top-1/2/3 ordering shown above is the MCDM CONSENSUS ONLY — it is NOT independently confirmed by physics simulation for this cluster** (rho=-0.091, band=NEGATIVE). See physics_validation_summary_rajasthan.txt for the full per-cluster interpretation before quoting this Top-3 as physics-validated.

### 8. Caveats

- **Imputed/unmeasured property in Top-3 candidate n-Heptacosane (C27):** solid specific heat, liquid specific heat, solid thermal conductivity, liquid thermal conductivity, cycling-stability count, flammability rating.
- **Imputed/unmeasured property in Top-3 candidate PureTemp 58:** thermal conductivity, cycling-stability count, flammability rating.
- **Imputed/unmeasured property in Top-3 candidate PlusICE A58:** thermal conductivity, cycling-stability count, flammability rating.
- **Feasibility window was relaxed** by +/-8K (4 round(s)) for this cluster, AND the latent-heat floor was calibrated down from kappa=0.7 to kappa=0.3 (status=in_band) — this Top-3 would not exist under the fixed-kappa=0.7 diagnostic run (0 survivors there).
- **Kendall's W = 0.5545, BELOW the 0.6 ambiguous-agreement threshold** (plan doc Section 9.5) — the four MCDM methods did not strongly agree with each other for this cluster's candidate pool.
- **Physics validation does not confirm this Top-3 ranking** (rho=-0.091, band=NEGATIVE) — treat the ordering above as the MCDM consensus, not an independently-verified performance ranking, for this cluster.