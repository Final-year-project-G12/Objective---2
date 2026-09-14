# Objective 1 — Recommendation Cards (Uttarakhand)

Generated from 5 climate regimes (GMM clustering, 45 population points).


## Cluster 0

- **Points in regime:** 7
- **Population covered:** 2,026,629
- **Approx. medoid point:** UKP_0037 (29.875, 78.625)

**Climate signature (population-weighted mean):**

| Index | Value |
|---|---|
| GHI_daily_kWh | 4.846 |
| Ta_mean | 22.631 |
| DTR | 11.325 |
| kt_mean | 0.817 |
| cloudy_frac | 0.036 |
| CCI | 3.619 |
| HDD18 | 4550.942 |
| CDD24 | 8465.706 |
| RH_mean | 56.181 |
| HSI | 20.215 |
| monsoon_index | 0.778 |

**Derived targets:** Tm_target = 57.0 C, L_required = 123 kJ/kg

**Candidates screened:** 29 survived Phase 5 feasibility filtering

**Top-3 PCM candidates (consensus of TOPSIS + GRA, Borda-aggregated):**

| Rank | PCM | Family | Tm (C) | Latent heat (kJ/kg) | TOPSIS | GRA |
|---|---|---|---|---|---|---|
| 1 | PureTemp 58 | PureTemp | 58.0 | 225 | 0.653 | 0.657 |
| 2 | n-Octacosane (C28) | n-Alkane | 61.6 | 253 | 0.592 | 0.690 |
| 3 | PlusICE A58 | PCM Products | 58.0 | 215 | 0.636 | 0.645 |

*Kendall's W = 0.796 (moderate agreement — discuss the disagreement)*

**Caveats:** thermal conductivity / density / specific heat not reported in the source data for the literature-added candidates (see 06_build_pcm_database.py); cycling and corrosion vetoes only partially applied (see 07_feasibility_filter.py's docstring for what wasn't checked yet).


## Cluster 1

- **Points in regime:** 3
- **Population covered:** 330,780
- **Approx. medoid point:** UKP_0041 (30.375, 79.375)

**Climate signature (population-weighted mean):**

| Index | Value |
|---|---|
| GHI_daily_kWh | 4.573 |
| Ta_mean | 9.447 |
| DTR | 10.557 |
| kt_mean | 0.685 |
| cloudy_frac | 0.043 |
| CCI | 3.000 |
| HDD18 | 32507.744 |
| CDD24 | 21.990 |
| RH_mean | 62.422 |
| HSI | 15.017 |
| monsoon_index | 0.732 |

**Derived targets:** Tm_target = 57.0 C, L_required = 178 kJ/kg

**Candidates screened:** 30 survived Phase 5 feasibility filtering

**Top-3 PCM candidates (consensus of TOPSIS + GRA, Borda-aggregated):**

| Rank | PCM | Family | Tm (C) | Latent heat (kJ/kg) | TOPSIS | GRA |
|---|---|---|---|---|---|---|
| 1 | PureTemp 53 | PureTemp | 53.0 | 225 | 0.692 | 0.642 |
| 2 | n-Hexacosane (C26) | n-Alkane | 56.5 | 256 | 0.630 | 0.726 |
| 3 | Myristic acid (C14) | Fatty acid | 53.0 | 199 | 0.679 | 0.629 |

*Kendall's W = 0.842 (strong agreement)*

**Caveats:** thermal conductivity / density / specific heat not reported in the source data for the literature-added candidates (see 06_build_pcm_database.py); cycling and corrosion vetoes only partially applied (see 07_feasibility_filter.py's docstring for what wasn't checked yet).


## Cluster 2

- **Points in regime:** 9
- **Population covered:** 2,451,044
- **Approx. medoid point:** UKP_0025 (30.375, 78.375)

**Climate signature (population-weighted mean):**

| Index | Value |
|---|---|
| GHI_daily_kWh | 4.901 |
| Ta_mean | 19.006 |
| DTR | 10.654 |
| kt_mean | 0.771 |
| cloudy_frac | 0.049 |
| CCI | 6.000 |
| HDD18 | 8726.151 |
| CDD24 | 3032.871 |
| RH_mean | 58.892 |
| HSI | 19.216 |
| monsoon_index | 0.776 |

**Derived targets:** Tm_target = 57.0 C, L_required = 138 kJ/kg

**Candidates screened:** 29 survived Phase 5 feasibility filtering

**Top-3 PCM candidates (consensus of TOPSIS + GRA, Borda-aggregated):**

| Rank | PCM | Family | Tm (C) | Latent heat (kJ/kg) | TOPSIS | GRA |
|---|---|---|---|---|---|---|
| 1 | PureTemp 58 | PureTemp | 58.0 | 225 | 0.646 | 0.637 |
| 2 | savE® OM55 | PLUSS savE | 55.0 | 188 | 0.632 | 0.685 |
| 3 | n-Hexacosane (C26) | n-Alkane | 56.5 | 256 | 0.596 | 0.727 |

*Kendall's W = 0.782 (moderate agreement — discuss the disagreement)*

**Caveats:** thermal conductivity / density / specific heat not reported in the source data for the literature-added candidates (see 06_build_pcm_database.py); cycling and corrosion vetoes only partially applied (see 07_feasibility_filter.py's docstring for what wasn't checked yet).


## Cluster 3

- **Points in regime:** 10
- **Population covered:** 3,700,876
- **Approx. medoid point:** UKP_0014 (29.375, 78.875)

**Climate signature (population-weighted mean):**

| Index | Value |
|---|---|
| GHI_daily_kWh | 4.749 |
| Ta_mean | 23.821 |
| DTR | 11.509 |
| kt_mean | 0.845 |
| cloudy_frac | 0.028 |
| CCI | 3.336 |
| HDD18 | 3220.240 |
| CDD24 | 10288.302 |
| RH_mean | 54.777 |
| HSI | 19.035 |
| monsoon_index | 0.751 |

**Derived targets:** Tm_target = 57.0 C, L_required = 118 kJ/kg

**Candidates screened:** 27 survived Phase 5 feasibility filtering

**Top-3 PCM candidates (consensus of TOPSIS + GRA, Borda-aggregated):**

| Rank | PCM | Family | Tm (C) | Latent heat (kJ/kg) | TOPSIS | GRA |
|---|---|---|---|---|---|---|
| 1 | PureTemp 58 | PureTemp | 58.0 | 225 | 0.621 | 0.645 |
| 2 | savE® OM55 | PLUSS savE | 55.0 | 188 | 0.640 | 0.676 |
| 3 | Palmitic-stearic acid/Expanded graphite | Eutectic composite | 55.2 | 176 | 0.639 | 0.672 |

*Kendall's W = 0.708 (moderate agreement — discuss the disagreement)*

**Caveats:** thermal conductivity / density / specific heat not reported in the source data for the literature-added candidates (see 06_build_pcm_database.py); cycling and corrosion vetoes only partially applied (see 07_feasibility_filter.py's docstring for what wasn't checked yet).


## Cluster 4

- **Points in regime:** 16
- **Population covered:** 1,966,385
- **Approx. medoid point:** UKP_0018 (29.625, 79.625)

**Climate signature (population-weighted mean):**

| Index | Value |
|---|---|
| GHI_daily_kWh | 4.840 |
| Ta_mean | 18.468 |
| DTR | 11.103 |
| kt_mean | 0.811 |
| cloudy_frac | 0.036 |
| CCI | 4.000 |
| HDD18 | 9096.808 |
| CDD24 | 2166.598 |
| RH_mean | 59.112 |
| HSI | 23.321 |
| monsoon_index | 0.754 |

**Derived targets:** Tm_target = 57.0 C, L_required = 140 kJ/kg

**Candidates screened:** 29 survived Phase 5 feasibility filtering

**Top-3 PCM candidates (consensus of TOPSIS + GRA, Borda-aggregated):**

| Rank | PCM | Family | Tm (C) | Latent heat (kJ/kg) | TOPSIS | GRA |
|---|---|---|---|---|---|---|
| 1 | PureTemp 58 | PureTemp | 58.0 | 225 | 0.653 | 0.657 |
| 2 | n-Octacosane (C28) | n-Alkane | 61.6 | 253 | 0.592 | 0.690 |
| 3 | PlusICE A58 | PCM Products | 58.0 | 215 | 0.636 | 0.645 |

*Kendall's W = 0.796 (moderate agreement — discuss the disagreement)*

**Caveats:** thermal conductivity / density / specific heat not reported in the source data for the literature-added candidates (see 06_build_pcm_database.py); cycling and corrosion vetoes only partially applied (see 07_feasibility_filter.py's docstring for what wasn't checked yet).
