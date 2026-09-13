# Objective 1 — Recommendation Cards (Tamil Nadu)

Generated from 3 climate regimes (GMM clustering, 133 population points).

**Physics validation summary (Phase 7):** mean Spearman rho across clusters = 0.666 (MCDM consensus rank vs. simulated annual solar fraction, grey-box lumped-enthalpy tank model driven by each cluster's medoid point's real 10-year daily climate data). See `10_physics_validation.py`'s docstring for the full stated assumption list (tank size, collector efficiency, draw schedule) before quoting this number without qualification.


## Cluster 0

- **Points in regime:** 46
- **Population covered:** 20,468,850
- **Medoid point (highest membership confidence):** TNP_0011 (8.125, 77.375)

**Climate signature (population-weighted mean):**

| Index | Value |
|---|---|
| GHI_daily_kWh | 5.318 |
| Ta_mean | 30.016 |
| DTR_true | 9.915 |
| kt_daily_mean | 0.811 |
| cloudy_frac | 0.011 |
| CCI | 2.739 |
| HDD18 | 0.000 |
| CDD24 | 12827.479 |
| RH_sunrise_mean | 79.558 |
| HSI_sunrise | 24.602 |
| monsoon_index | 0.955 |

**Derived targets:** Tm_target = 57.0 C, L_required = 276 kJ/kg

**Candidates screened:** 13 survived Phase 5 feasibility filtering (melting window, absolute band, latent-heat floor, cycling, supercooling, corrosion veto, safety exclusion)

**Top-3 PCM candidates (Borda consensus of TOPSIS + GRA + PROMETHEE II + VIKOR):**

| Rank | PCM | Family | Tm (C) | Latent heat (kJ/kg) | TOPSIS | GRA | PROMETHEE | VIKOR_Q | MC Top-3 % |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PureTemp 53 |  | 53.0 | 225 | 0.784 | 0.138 | +0.139 | 0.108 | 54.9% |
| 2 | Myristic acid |  | 53.0 | 190 | 0.930 | 0.203 | +0.043 | 0.017 | 75.8% |
| 3 | Myristic acid (C14) |  | 53.0 | 199 | 0.798 | 0.135 | +0.122 | 0.113 | 79.1% |

*Kendall's W (4-method concordance) = 0.584 (weak agreement — this regime's PCM choice is genuinely ambiguous)*

*Borda and Copeland consensus disagree on #1 for this cluster — report both, per plan v3.0 Section 9.5.*

**Phase 7 — simulated annual performance (grey-box lumped-enthalpy tank, real climate data):**

| PCM | Consensus rank | Simulated solar fraction | In 54-84% benchmark band? | Complete cycles/yr |
|---|---|---|---|---|
| PureTemp 53 | 1 | 45.2% | No | 167 |
| Myristic acid | 2 | 43.5% | No | 170 |
| Myristic acid (C14) | 3 | 43.5% | No | 170 |
| n-Tetracosane (C24) | 4 | 37.4% | No | 202 |
| Palmitic-Stearic eutectic (64.2/35.8) | 5 | 40.4% | No | 197 |

*Spearman rho (MCDM rank vs. simulated solar fraction) for this cluster: 0.839 — strong agreement*

**Caveats:** thermal conductivity / density / specific heat not reported in the source data for the literature-added candidates (see 06_build_pcm_database.py); Phase 7's tank/collector parameters are stated assumptions, not measurements (see 10_physics_validation.py's docstring).


## Cluster 1

- **Points in regime:** 41
- **Population covered:** 20,422,159
- **Medoid point (highest membership confidence):** TNP_0007 (10.875, 76.875)

**Climate signature (population-weighted mean):**

| Index | Value |
|---|---|
| GHI_daily_kWh | 5.238 |
| Ta_mean | 27.413 |
| DTR_true | 11.107 |
| kt_daily_mean | 0.803 |
| cloudy_frac | 0.011 |
| CCI | 2.629 |
| HDD18 | 0.062 |
| CDD24 | 8301.916 |
| RH_sunrise_mean | 82.003 |
| HSI_sunrise | 22.540 |
| monsoon_index | 0.888 |

**Derived targets:** Tm_target = 57.0 C, L_required = 309 kJ/kg

**Candidates screened:** 13 survived Phase 5 feasibility filtering (melting window, absolute band, latent-heat floor, cycling, supercooling, corrosion veto, safety exclusion)

**Top-3 PCM candidates (Borda consensus of TOPSIS + GRA + PROMETHEE II + VIKOR):**

| Rank | PCM | Family | Tm (C) | Latent heat (kJ/kg) | TOPSIS | GRA | PROMETHEE | VIKOR_Q | MC Top-3 % |
|---|---|---|---|---|---|---|---|---|---|
| 1 | n-Tetracosane (C24) |  | 52.0 | 255 | 0.835 | 0.134 | +0.294 | 0.000 | 91.3% |
| 2 | PlusICE A52 |  | 52.0 | 220 | 0.827 | 0.132 | +0.217 | 0.099 | 69.4% |
| 3 | savE® OM50 |  | 50.0 | 189 | 0.495 | 0.133 | +0.179 | 0.476 | 40.7% |

*Kendall's W (4-method concordance) = 0.592 (weak agreement — this regime's PCM choice is genuinely ambiguous)*

**Phase 7 — simulated annual performance (grey-box lumped-enthalpy tank, real climate data):**

| PCM | Consensus rank | Simulated solar fraction | In 54-84% benchmark band? | Complete cycles/yr |
|---|---|---|---|---|
| n-Tetracosane (C24) | 1 | 52.8% | No | 144 |
| PlusICE A52 | 2 | 52.8% | No | 144 |
| savE® OM50 | 3 | 40.2% | No | 198 |
| Paraffin/HDPE PCM2 | 4 | 37.5% | No | 179 |
| Paraffin/HDPE PCM6 | 5 | 37.1% | No | 190 |

*Spearman rho (MCDM rank vs. simulated solar fraction) for this cluster: 0.679 — partial agreement*

**Caveats:** thermal conductivity / density / specific heat not reported in the source data for the literature-added candidates (see 06_build_pcm_database.py); Phase 7's tank/collector parameters are stated assumptions, not measurements (see 10_physics_validation.py's docstring).


## Cluster 2

- **Points in regime:** 46
- **Population covered:** 30,335,761
- **Medoid point (highest membership confidence):** TNP_0001 (13.125, 80.125)

**Climate signature (population-weighted mean):**

| Index | Value |
|---|---|
| GHI_daily_kWh | 5.228 |
| Ta_mean | 29.956 |
| DTR_true | 8.201 |
| kt_daily_mean | 0.817 |
| cloudy_frac | 0.026 |
| CCI | 4.417 |
| HDD18 | 0.000 |
| CDD24 | 14768.840 |
| RH_sunrise_mean | 81.449 |
| HSI_sunrise | 25.173 |
| monsoon_index | 0.943 |

**Derived targets:** Tm_target = 57.0 C, L_required = 277 kJ/kg

**Candidates screened:** 16 survived Phase 5 feasibility filtering (melting window, absolute band, latent-heat floor, cycling, supercooling, corrosion veto, safety exclusion)

**Top-3 PCM candidates (Borda consensus of TOPSIS + GRA + PROMETHEE II + VIKOR):**

| Rank | PCM | Family | Tm (C) | Latent heat (kJ/kg) | TOPSIS | GRA | PROMETHEE | VIKOR_Q | MC Top-3 % |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Palmitic-Stearic eutectic (64.2/35.8) |  | 52.3 | 182 | 0.962 | 0.220 | +0.173 | 0.000 | 89.4% |
| 2 | n-Tetracosane (C24) |  | 52.0 | 255 | 0.803 | 0.135 | +0.263 | 0.101 | 40.9% |
| 3 | PlusICE A52 |  | 52.0 | 220 | 0.794 | 0.133 | +0.195 | 0.176 | 34.2% |

*Kendall's W (4-method concordance) = 0.641 (moderate agreement — discuss the disagreement)*

**Phase 7 — simulated annual performance (grey-box lumped-enthalpy tank, real climate data):**

| PCM | Consensus rank | Simulated solar fraction | In 54-84% benchmark band? | Complete cycles/yr |
|---|---|---|---|---|
| Palmitic-Stearic eutectic (64.2/35.8) | 1 | 42.8% | No | 206 |
| n-Tetracosane (C24) | 2 | 34.2% | No | 208 |
| PlusICE A52 | 3 | 33.1% | No | 211 |
| savE® OM50 | 4 | 41.5% | No | 242 |
| Paraffin/Expanded graphite (92% paraffin) | 4 | 33.4% | No | 210 |

*Spearman rho (MCDM rank vs. simulated solar fraction) for this cluster: 0.480 — partial agreement*

**Caveats:** thermal conductivity / density / specific heat not reported in the source data for the literature-added candidates (see 06_build_pcm_database.py); Phase 7's tank/collector parameters are stated assumptions, not measurements (see 10_physics_validation.py's docstring).
