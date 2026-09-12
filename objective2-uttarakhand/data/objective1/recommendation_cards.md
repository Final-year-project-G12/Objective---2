# Objective 1 — Recommendation Cards (Uttarakhand)

Generated from 5 climate regimes (GMM clustering, 45 population points).


## Cluster 0

- **Points in regime:** 15
- **Population covered:** 2,729,553
- **Approx. medoid point:** UKP_0022 (29.375, 79.625)

**Climate signature (population-weighted mean):**

| Index | Value |
|---|---|
| GHI_daily_kWh | 4.800 |
| Ta_mean | 21.384 |
| DTR | 11.414 |
| kt_mean | 0.815 |
| cloudy_frac | 0.036 |
| CCI | 4.000 |
| HDD18 | 5900.079 |
| CDD24 | 6632.513 |
| RH_mean | 56.863 |
| HSI | 21.628 |
| monsoon_index | 0.697 |

**Derived targets:** Tm_target = 57.0 C, L_required = 128 kJ/kg

**Candidates screened:** 29 survived Phase 5 feasibility filtering

**Top-3 PCM candidates (consensus of TOPSIS + GRA, Borda-aggregated):**

| Rank | PCM | Family | Tm (C) | Latent heat (kJ/kg) | TOPSIS | GRA |
|---|---|---|---|---|---|---|
| 1 | PureTemp 58 | PureTemp | 58.0 | 225 | 0.641 | 0.657 |
| 2 | n-Octacosane (C28) | n-Alkane | 61.6 | 253 | 0.594 | 0.690 |
| 3 | PlusICE A58 | PCM Products | 58.0 | 215 | 0.629 | 0.645 |

*Kendall's W = 0.797 (moderate agreement — discuss the disagreement)*

**Caveats:** thermal conductivity / density / specific heat not reported in the source data for the literature-added candidates (see 06_build_pcm_database.py); cycling and corrosion vetoes only partially applied (see 07_feasibility_filter.py's docstring for what wasn't checked yet).


## Cluster 1

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
| monsoon_index | 0.730 |

**Derived targets:** Tm_target = 57.0 C, L_required = 138 kJ/kg

**Candidates screened:** 27 survived Phase 5 feasibility filtering

**Top-3 PCM candidates (consensus of TOPSIS + GRA, Borda-aggregated):**

| Rank | PCM | Family | Tm (C) | Latent heat (kJ/kg) | TOPSIS | GRA |
|---|---|---|---|---|---|---|
| 1 | PureTemp 58 | PureTemp | 58.0 | 225 | 0.610 | 0.645 |
| 2 | Palmitic-stearic acid/Expanded graphite | Eutectic composite | 55.2 | 176 | 0.626 | 0.672 |
| 3 | n-Octacosane (C28) | n-Alkane | 61.6 | 253 | 0.573 | 0.678 |

*Kendall's W = 0.716 (moderate agreement — discuss the disagreement)*

**Caveats:** thermal conductivity / density / specific heat not reported in the source data for the literature-added candidates (see 06_build_pcm_database.py); cycling and corrosion vetoes only partially applied (see 07_feasibility_filter.py's docstring for what wasn't checked yet).


## Cluster 2

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
| monsoon_index | 0.624 |

**Derived targets:** Tm_target = 57.0 C, L_required = 178 kJ/kg

**Candidates screened:** 29 survived Phase 5 feasibility filtering

**Top-3 PCM candidates (consensus of TOPSIS + GRA, Borda-aggregated):**

| Rank | PCM | Family | Tm (C) | Latent heat (kJ/kg) | TOPSIS | GRA |
|---|---|---|---|---|---|---|
| 1 | PureTemp 58 | PureTemp | 58.0 | 225 | 0.641 | 0.657 |
| 2 | n-Octacosane (C28) | n-Alkane | 61.6 | 253 | 0.594 | 0.690 |
| 3 | PlusICE A58 | PCM Products | 58.0 | 215 | 0.629 | 0.645 |

*Kendall's W = 0.797 (moderate agreement — discuss the disagreement)*

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
| monsoon_index | 0.699 |

**Derived targets:** Tm_target = 57.0 C, L_required = 118 kJ/kg

**Candidates screened:** 27 survived Phase 5 feasibility filtering

**Top-3 PCM candidates (consensus of TOPSIS + GRA, Borda-aggregated):**

| Rank | PCM | Family | Tm (C) | Latent heat (kJ/kg) | TOPSIS | GRA |
|---|---|---|---|---|---|---|
| 1 | PureTemp 58 | PureTemp | 58.0 | 225 | 0.610 | 0.645 |
| 2 | Palmitic-stearic acid/Expanded graphite | Eutectic composite | 55.2 | 176 | 0.626 | 0.672 |
| 3 | n-Octacosane (C28) | n-Alkane | 61.6 | 253 | 0.573 | 0.678 |

*Kendall's W = 0.716 (moderate agreement — discuss the disagreement)*

**Caveats:** thermal conductivity / density / specific heat not reported in the source data for the literature-added candidates (see 06_build_pcm_database.py); cycling and corrosion vetoes only partially applied (see 07_feasibility_filter.py's docstring for what wasn't checked yet).


## Cluster 4

- **Points in regime:** 8
- **Population covered:** 1,263,461
- **Approx. medoid point:** UKP_0037 (29.875, 78.625)

**Climate signature (population-weighted mean):**

| Index | Value |
|---|---|
| GHI_daily_kWh | 4.935 |
| Ta_mean | 18.847 |
| DTR | 10.787 |
| kt_mean | 0.812 |
| cloudy_frac | 0.034 |
| CCI | 3.388 |
| HDD18 | 8711.248 |
| CDD24 | 2622.492 |
| RH_mean | 59.271 |
| HSI | 21.998 |
| monsoon_index | 0.719 |

**Derived targets:** Tm_target = 57.0 C, L_required = 139 kJ/kg

**Candidates screened:** 29 survived Phase 5 feasibility filtering

**Top-3 PCM candidates (consensus of TOPSIS + GRA, Borda-aggregated):**

| Rank | PCM | Family | Tm (C) | Latent heat (kJ/kg) | TOPSIS | GRA |
|---|---|---|---|---|---|---|
| 1 | PureTemp 58 | PureTemp | 58.0 | 225 | 0.641 | 0.657 |
| 2 | n-Octacosane (C28) | n-Alkane | 61.6 | 253 | 0.594 | 0.690 |
| 3 | PlusICE A58 | PCM Products | 58.0 | 215 | 0.629 | 0.645 |

*Kendall's W = 0.797 (moderate agreement — discuss the disagreement)*

**Caveats:** thermal conductivity / density / specific heat not reported in the source data for the literature-added candidates (see 06_build_pcm_database.py); cycling and corrosion vetoes only partially applied (see 07_feasibility_filter.py's docstring for what wasn't checked yet).
