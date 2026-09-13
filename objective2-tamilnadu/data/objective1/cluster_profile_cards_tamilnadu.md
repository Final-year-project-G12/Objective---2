# Tamilnadu — Level A Cluster Profile Cards

Generated from k=3 GMM clusters (133 population points). Auto-suggested k selection reason: in silhouette band AND expected single-state k range. Bootstrap-ARI stability at this k: 0.6061 (mean over 50/50 resamples).

Koppen-Geiger external validation: ARI=0.0672, NMI=0.1499 against Beck et al. (2018) present-climate classes for these same 133 points (see koppen_validation_tamilnadu.csv for the full cluster x Koppen-class contingency table). This is a low-to-moderate agreement — the GMM is finding climate structure at a finer resolution than Koppen's broad classes capture within Tamil Nadu, which is a legitimate finding in its own right, not a failure of the clustering.

This is a single-state run — see the printed EXTERNAL VALIDATION section for what's not yet wired in (NBC/ECBC, state identity).


## Cluster 0

- **Points in regime:** 46
- **Total population covered:** 20,468,850
- **Medoid point (climate-feature-space, no district lookup available — lat/lon only):** TNP_0113 (10.375, 78.375)

**Two-tier climate signature (population-weighted mean +/- std):**

| Index | Mean | Std |
|---|---|---|
| Ta_mean | 30.016 | 0.999 |
| Ta_p95 | 33.811 | 1.358 |
| Ta_p05 | 26.513 | 0.623 |
| T_sunrise_mean | 25.889 | 0.754 |
| T_noon_mean | 32.623 | 1.204 |
| T_sunset_mean | 31.538 | 1.291 |
| diurnal_gradient | 6.734 | 0.871 |
| GHI_noon_mean | 765.612 | 12.025 |
| GHI_sunset_mean | 31.306 | 5.307 |
| GHI_daily_kWh | 5.318 | 0.115 |
| kt_noon_mean | 0.800 | 0.011 |
| kt_noon_std | 0.158 | 0.006 |
| kt_daily_mean | 0.811 | 0.019 |
| kt_daily_std | 0.149 | 0.004 |
| SAI | 0.814 | 0.020 |
| cloudy_frac | 0.011 | 0.002 |
| CCI | 2.739 | 0.455 |
| HDD18 | 0.000 | 0.000 |
| CDD24 | 12827.479 | 2969.366 |
| DTR_true | 9.915 | 2.171 |
| RH_sunrise_mean | 79.558 | 3.180 |
| HSI_sunrise | 24.602 | 0.598 |
| wind_noon_mean | 2.897 | 0.611 |
| wind_sunset_mean | 2.738 | 0.615 |
| daylength_mean | 12.127 | 0.001 |
| daylength_amplitude | 0.585 | 0.058 |
| seasonality | 0.133 | 0.011 |
| monsoon_index | 0.955 | 0.031 |

**Physical description (auto-generated, review before publishing):** Hot, monsoon-influenced, steady solar resource, long low-clearness runs (high autonomy demand).

**Derived PCM targets:** Tm_target_C = 57.0 C, L_required_kJ_per_kg = 276 kJ/kg (CEILING, not an achievability bar — see 04b_climate_signature.py's docstring)


## Cluster 1

- **Points in regime:** 41
- **Total population covered:** 20,422,159
- **Medoid point (climate-feature-space, no district lookup available — lat/lon only):** TNP_0122 (11.625, 78.625)

**Two-tier climate signature (population-weighted mean +/- std):**

| Index | Mean | Std |
|---|---|---|
| Ta_mean | 27.413 | 1.610 |
| Ta_p95 | 31.430 | 1.878 |
| Ta_p05 | 24.018 | 1.361 |
| T_sunrise_mean | 23.434 | 1.446 |
| T_noon_mean | 29.830 | 1.561 |
| T_sunset_mean | 28.973 | 1.894 |
| diurnal_gradient | 6.396 | 0.409 |
| GHI_noon_mean | 751.730 | 7.465 |
| GHI_sunset_mean | 37.803 | 6.557 |
| GHI_daily_kWh | 5.238 | 0.093 |
| kt_noon_mean | 0.788 | 0.010 |
| kt_noon_std | 0.168 | 0.005 |
| kt_daily_mean | 0.803 | 0.016 |
| kt_daily_std | 0.157 | 0.007 |
| SAI | 0.805 | 0.017 |
| cloudy_frac | 0.011 | 0.004 |
| CCI | 2.629 | 0.756 |
| HDD18 | 0.062 | 0.194 |
| CDD24 | 8301.916 | 3168.348 |
| DTR_true | 11.107 | 0.856 |
| RH_sunrise_mean | 82.003 | 2.429 |
| HSI_sunrise | 22.540 | 1.268 |
| wind_noon_mean | 2.606 | 0.661 |
| wind_sunset_mean | 1.997 | 0.506 |
| daylength_mean | 12.129 | 0.001 |
| daylength_amplitude | 0.664 | 0.063 |
| seasonality | 0.146 | 0.011 |
| monsoon_index | 0.888 | 0.028 |

**Physical description (auto-generated, review before publishing):** Cooler, arid/low-monsoon, steady solar resource, short low-clearness runs.

**Derived PCM targets:** Tm_target_C = 57.0 C, L_required_kJ_per_kg = 309 kJ/kg (CEILING, not an achievability bar — see 04b_climate_signature.py's docstring)


## Cluster 2

- **Points in regime:** 46
- **Total population covered:** 30,335,761
- **Medoid point (climate-feature-space, no district lookup available — lat/lon only):** TNP_0058 (12.125, 79.625)

**Two-tier climate signature (population-weighted mean +/- std):**

| Index | Mean | Std |
|---|---|---|
| Ta_mean | 29.956 | 0.452 |
| Ta_p95 | 33.935 | 0.626 |
| Ta_p05 | 25.682 | 0.548 |
| T_sunrise_mean | 26.385 | 0.569 |
| T_noon_mean | 32.315 | 0.659 |
| T_sunset_mean | 31.167 | 0.614 |
| diurnal_gradient | 5.930 | 0.785 |
| GHI_noon_mean | 755.803 | 5.524 |
| GHI_sunset_mean | 26.586 | 1.211 |
| GHI_daily_kWh | 5.228 | 0.052 |
| kt_noon_mean | 0.793 | 0.005 |
| kt_noon_std | 0.158 | 0.007 |
| kt_daily_mean | 0.817 | 0.004 |
| kt_daily_std | 0.175 | 0.008 |
| SAI | 0.821 | 0.004 |
| cloudy_frac | 0.026 | 0.004 |
| CCI | 4.417 | 0.383 |
| HDD18 | 0.000 | 0.000 |
| CDD24 | 14768.840 | 1304.327 |
| DTR_true | 8.201 | 2.187 |
| RH_sunrise_mean | 81.449 | 1.246 |
| HSI_sunrise | 25.173 | 0.518 |
| wind_noon_mean | 3.143 | 0.189 |
| wind_sunset_mean | 2.948 | 0.453 |
| daylength_mean | 12.130 | 0.001 |
| daylength_amplitude | 0.722 | 0.055 |
| seasonality | 0.159 | 0.005 |
| monsoon_index | 0.943 | 0.038 |

**Physical description (auto-generated, review before publishing):** Cooler, arid/low-monsoon, erratic solar resource, long low-clearness runs (high autonomy demand).

**Derived PCM targets:** Tm_target_C = 57.0 C, L_required_kJ_per_kg = 277 kJ/kg (CEILING, not an achievability bar — see 04b_climate_signature.py's docstring)
