# Objective 1 — Recommendation Cards (Tamil Nadu)

Generated from 5 climate regimes (GMM clustering, 133 population points).

**Physics validation summary (Phase 7):** mean Spearman rho across clusters = 0.177 (MCDM consensus rank vs. simulated annual solar fraction, grey-box lumped-enthalpy tank model driven by each cluster's medoid point's real 10-year daily climate data). See `10_physics_validation.py`'s docstring for the full stated assumption list (tank size, collector efficiency, draw schedule) before quoting this number without qualification.


## Cluster 0

- **Points in regime:** 8
- **Population covered:** 12,658,861
- **Medoid point (highest membership confidence):** TNP_0001 (13.125, 80.125)

**Climate signature (population-weighted mean):**

| Index | Value |
|---|---|
| GHI_daily_kWh | 5.150 |
| Ta_mean | 27.997 |
| DTR | 6.890 |
| kt_mean | 0.814 |
| cloudy_frac | 0.033 |
| CCI | 5.000 |
| HDD18 | 0.000 |
| CDD24 | 14763.138 |
| RH_mean | 70.246 |
| HSI | 15.888 |
| monsoon_index | 0.354 |

**Derived targets:** Tm_target = 57.0 C, L_required = 301 kJ/kg

**Candidates screened:** 15 survived Phase 5 feasibility filtering (melting window, absolute band, latent-heat floor, cycling, supercooling, corrosion veto, safety exclusion)

**Top-3 PCM candidates (Borda consensus of TOPSIS + GRA + PROMETHEE II + VIKOR):**

| Rank | PCM | Family | Tm (C) | Latent heat (kJ/kg) | TOPSIS | GRA | PROMETHEE | VIKOR_Q | MC Top-3 % |
|---|---|---|---|---|---|---|---|---|---|
| 1 | n-Octacosane (C28) | Literature | 61.6 | 253 | 0.694 | 0.713 | +0.470 | 0.000 | 76.8% |
| 2 | n-Hexacosane (C26) | Literature | 56.5 | 256 | 0.568 | 0.704 | +0.259 | 0.324 | 36.1% |
| 3 | PureTemp 58 | PureTemp | 58.0 | 225 | 0.557 | 0.606 | +0.084 | 0.307 | 39.8% |

*Kendall's W (4-method concordance) = 0.842 (strong agreement)*

**Phase 7 — simulated annual performance (grey-box lumped-enthalpy tank, real climate data):**

| PCM | Consensus rank | Simulated solar fraction | In 54-84% benchmark band? | Complete cycles/yr |
|---|---|---|---|---|
| n-Octacosane (C28) | 1 | 71.0% | Yes | 47 |
| n-Hexacosane (C26) | 2 | 53.6% | No | 117 |
| PureTemp 58 | 3 | 48.9% | No | 96 |
| RT57HC | 4 | 53.8% | No | 116 |
| PureTemp 53 | 5 | 38.1% | No | 189 |

*Spearman rho (MCDM rank vs. simulated solar fraction) for this cluster: -0.016 — weak agreement — diagnose before trusting the MCDM ranking here*

**Caveats:** thermal conductivity / density / specific heat not reported in the source data for the literature-added candidates (see 06_build_pcm_database.py); Phase 7's tank/collector parameters are stated assumptions, not measurements (see 10_physics_validation.py's docstring).


## Cluster 1

- **Points in regime:** 42
- **Population covered:** 19,812,762
- **Medoid point (highest membership confidence):** TNP_0005 (11.625, 78.125)

**Climate signature (population-weighted mean):**

| Index | Value |
|---|---|
| GHI_daily_kWh | 5.281 |
| Ta_mean | 26.390 |
| DTR | 11.446 |
| kt_mean | 0.810 |
| cloudy_frac | 0.010 |
| CCI | 2.246 |
| HDD18 | 0.036 |
| CDD24 | 9796.381 |
| RH_mean | 65.118 |
| HSI | 12.857 |
| monsoon_index | 0.455 |

**Derived targets:** Tm_target = 57.0 C, L_required = 322 kJ/kg

**Candidates screened:** 9 survived Phase 5 feasibility filtering (melting window, absolute band, latent-heat floor, cycling, supercooling, corrosion veto, safety exclusion)

**Top-3 PCM candidates (Borda consensus of TOPSIS + GRA + PROMETHEE II + VIKOR):**

| Rank | PCM | Family | Tm (C) | Latent heat (kJ/kg) | TOPSIS | GRA | PROMETHEE | VIKOR_Q | MC Top-3 % |
|---|---|---|---|---|---|---|---|---|---|
| 1 | n-Octacosane (C28) | Literature | 61.6 | 253 | 0.692 | 0.720 | +0.502 | 0.000 | 90.2% |
| 2 | RT64HC | Rubitherm Technologies | 64.0 | 250 | 0.543 | 0.641 | +0.219 | 0.485 | 46.4% |
| 3 | n-Hexacosane (C26) | Literature | 56.5 | 256 | 0.412 | 0.629 | +0.163 | 0.702 | 51.9% |

*Kendall's W (4-method concordance) = 0.956 (strong agreement)*

**Phase 7 — simulated annual performance (grey-box lumped-enthalpy tank, real climate data):**

| PCM | Consensus rank | Simulated solar fraction | In 54-84% benchmark band? | Complete cycles/yr |
|---|---|---|---|---|
| n-Octacosane (C28) | 1 | 64.6% | Yes | 65 |
| RT64HC | 2 | 76.4% | Yes | 43 |
| n-Hexacosane (C26) | 3 | 55.9% | Yes | 152 |
| n-Nonacosane (C29) | 4 | 76.1% | Yes | 43 |
| RT57HC | 5 | 56.6% | Yes | 148 |

*Spearman rho (MCDM rank vs. simulated solar fraction) for this cluster: 0.717 — partial agreement*

**Caveats:** thermal conductivity / density / specific heat not reported in the source data for the literature-added candidates (see 06_build_pcm_database.py); Phase 7's tank/collector parameters are stated assumptions, not measurements (see 10_physics_validation.py's docstring).


## Cluster 2

- **Points in regime:** 39
- **Population covered:** 18,057,219
- **Medoid point (highest membership confidence):** TNP_0009 (12.875, 79.125)

**Climate signature (population-weighted mean):**

| Index | Value |
|---|---|
| GHI_daily_kWh | 5.284 |
| Ta_mean | 27.935 |
| DTR | 9.176 |
| kt_mean | 0.820 |
| cloudy_frac | 0.022 |
| CCI | 4.000 |
| HDD18 | 0.000 |
| CDD24 | 14734.214 |
| RH_mean | 67.342 |
| HSI | 13.649 |
| monsoon_index | 0.398 |

**Derived targets:** Tm_target = 57.0 C, L_required = 302 kJ/kg

**Candidates screened:** 13 survived Phase 5 feasibility filtering (melting window, absolute band, latent-heat floor, cycling, supercooling, corrosion veto, safety exclusion)

**Top-3 PCM candidates (Borda consensus of TOPSIS + GRA + PROMETHEE II + VIKOR):**

| Rank | PCM | Family | Tm (C) | Latent heat (kJ/kg) | TOPSIS | GRA | PROMETHEE | VIKOR_Q | MC Top-3 % |
|---|---|---|---|---|---|---|---|---|---|
| 1 | n-Octacosane (C28) | Literature | 61.6 | 253 | 0.683 | 0.688 | +0.462 | 0.000 | 77.8% |
| 2 | PureTemp 58 | PureTemp | 58.0 | 225 | 0.530 | 0.588 | +0.048 | 0.345 | 44.1% |
| 3 | n-Hexacosane (C26) | Literature | 56.5 | 256 | 0.453 | 0.644 | +0.146 | 0.692 | 16.1% |

*Kendall's W (4-method concordance) = 0.835 (strong agreement)*

**Phase 7 — simulated annual performance (grey-box lumped-enthalpy tank, real climate data):**

| PCM | Consensus rank | Simulated solar fraction | In 54-84% benchmark band? | Complete cycles/yr |
|---|---|---|---|---|
| n-Octacosane (C28) | 1 | 68.8% | Yes | 61 |
| PureTemp 58 | 2 | 59.6% | Yes | 110 |
| n-Hexacosane (C26) | 3 | 53.9% | No | 138 |
| PureTemp 60 | 4 | 47.6% | No | 68 |
| PureTemp 53 | 5 | 47.8% | No | 209 |

*Spearman rho (MCDM rank vs. simulated solar fraction) for this cluster: 0.355 — weak agreement — diagnose before trusting the MCDM ranking here*

**Caveats:** thermal conductivity / density / specific heat not reported in the source data for the literature-added candidates (see 06_build_pcm_database.py); Phase 7's tank/collector parameters are stated assumptions, not measurements (see 10_physics_validation.py's docstring).


## Cluster 3

- **Points in regime:** 22
- **Population covered:** 10,252,755
- **Medoid point (highest membership confidence):** TNP_0004 (9.875, 78.125)

**Climate signature (population-weighted mean):**

| Index | Value |
|---|---|
| GHI_daily_kWh | 5.424 |
| Ta_mean | 27.787 |
| DTR | 10.394 |
| kt_mean | 0.827 |
| cloudy_frac | 0.011 |
| CCI | 3.000 |
| HDD18 | 0.000 |
| CDD24 | 14121.353 |
| RH_mean | 62.542 |
| HSI | 9.567 |
| monsoon_index | 0.328 |

**Derived targets:** Tm_target = 57.0 C, L_required = 304 kJ/kg

**Candidates screened:** 13 survived Phase 5 feasibility filtering (melting window, absolute band, latent-heat floor, cycling, supercooling, corrosion veto, safety exclusion)

**Top-3 PCM candidates (Borda consensus of TOPSIS + GRA + PROMETHEE II + VIKOR):**

| Rank | PCM | Family | Tm (C) | Latent heat (kJ/kg) | TOPSIS | GRA | PROMETHEE | VIKOR_Q | MC Top-3 % |
|---|---|---|---|---|---|---|---|---|---|
| 1 | n-Octacosane (C28) | Literature | 61.6 | 253 | 0.683 | 0.688 | +0.462 | 0.000 | 77.8% |
| 2 | PureTemp 58 | PureTemp | 58.0 | 225 | 0.530 | 0.588 | +0.048 | 0.345 | 44.1% |
| 3 | n-Hexacosane (C26) | Literature | 56.5 | 256 | 0.453 | 0.644 | +0.146 | 0.692 | 16.1% |

*Kendall's W (4-method concordance) = 0.835 (strong agreement)*

**Phase 7 — simulated annual performance (grey-box lumped-enthalpy tank, real climate data):**

| PCM | Consensus rank | Simulated solar fraction | In 54-84% benchmark band? | Complete cycles/yr |
|---|---|---|---|---|
| n-Octacosane (C28) | 1 | 51.3% | No | 71 |
| PureTemp 58 | 2 | 39.1% | No | 152 |
| n-Hexacosane (C26) | 3 | 43.0% | No | 174 |
| PureTemp 60 | 4 | 63.9% | Yes | 83 |
| PureTemp 53 | 5 | 46.0% | No | 249 |

*Spearman rho (MCDM rank vs. simulated solar fraction) for this cluster: -0.171 — weak agreement — diagnose before trusting the MCDM ranking here*

**Caveats:** thermal conductivity / density / specific heat not reported in the source data for the literature-added candidates (see 06_build_pcm_database.py); Phase 7's tank/collector parameters are stated assumptions, not measurements (see 10_physics_validation.py's docstring).


## Cluster 4

- **Points in regime:** 22
- **Population covered:** 10,445,174
- **Medoid point (highest membership confidence):** TNP_0007 (10.875, 76.875)

**Climate signature (population-weighted mean):**

| Index | Value |
|---|---|
| GHI_daily_kWh | 5.129 |
| Ta_mean | 26.039 |
| DTR | 8.836 |
| kt_mean | 0.782 |
| cloudy_frac | 0.013 |
| CCI | 3.157 |
| HDD18 | 0.053 |
| CDD24 | 8454.738 |
| RH_mean | 69.867 |
| HSI | 20.251 |
| monsoon_index | 0.399 |

**Derived targets:** Tm_target = 57.0 C, L_required = 326 kJ/kg

**Candidates screened:** 9 survived Phase 5 feasibility filtering (melting window, absolute band, latent-heat floor, cycling, supercooling, corrosion veto, safety exclusion)

**Top-3 PCM candidates (Borda consensus of TOPSIS + GRA + PROMETHEE II + VIKOR):**

| Rank | PCM | Family | Tm (C) | Latent heat (kJ/kg) | TOPSIS | GRA | PROMETHEE | VIKOR_Q | MC Top-3 % |
|---|---|---|---|---|---|---|---|---|---|
| 1 | n-Octacosane (C28) | Literature | 61.6 | 253 | 0.692 | 0.720 | +0.502 | 0.000 | 90.2% |
| 2 | RT64HC | Rubitherm Technologies | 64.0 | 250 | 0.543 | 0.641 | +0.219 | 0.485 | 46.4% |
| 3 | n-Hexacosane (C26) | Literature | 56.5 | 256 | 0.412 | 0.629 | +0.163 | 0.702 | 51.9% |

*Kendall's W (4-method concordance) = 0.956 (strong agreement)*

**Phase 7 — simulated annual performance (grey-box lumped-enthalpy tank, real climate data):**

| PCM | Consensus rank | Simulated solar fraction | In 54-84% benchmark band? | Complete cycles/yr |
|---|---|---|---|---|
| n-Octacosane (C28) | 1 | 30.9% | No | 24 |
| RT64HC | 2 | 80.1% | Yes | 3 |
| n-Hexacosane (C26) | 3 | 44.4% | No | 73 |
| n-Nonacosane (C29) | 4 | 80.0% | Yes | 3 |
| RT57HC | 5 | 44.4% | No | 73 |

*Spearman rho (MCDM rank vs. simulated solar fraction) for this cluster: -0.000 — weak agreement — diagnose before trusting the MCDM ranking here*

**Caveats:** thermal conductivity / density / specific heat not reported in the source data for the literature-added candidates (see 06_build_pcm_database.py); Phase 7's tank/collector parameters are stated assumptions, not measurements (see 10_physics_validation.py's docstring).
