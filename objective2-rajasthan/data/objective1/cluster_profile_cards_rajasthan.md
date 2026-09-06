# Rajasthan — Level A Cluster Profile Cards

Generated from k=3 GMM clusters (320 population points). Auto-suggested k selection reason: in silhouette band AND expected single-state k range. Bootstrap-ARI stability at this k: 0.8273 (mean over 50/50 resamples).

Koppen-Geiger external validation: ARI=0.1891, NMI=0.3186 against Beck et al. (2018) present-climate classes for these same 320 points (see koppen_validation_rajasthan.csv for the full cluster x Koppen-class contingency table). This is a low-to-moderate agreement — the GMM is finding climate structure at a finer resolution than Koppen's broad classes capture within Rajasthan, which is a legitimate finding in its own right, not a failure of the clustering.

This is a single-state run — see the printed EXTERNAL VALIDATION section for what's not yet wired in (NBC/ECBC, state identity).


## Cluster 0

- **Points in regime:** 114
- **Total population covered:** 22,568,150
- **Medoid point (climate-feature-space, no district lookup available — lat/lon only):** RJP_0132 (24.375, 74.125)

**Two-tier climate signature (population-weighted mean +/- std):**

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

**Physical description (auto-generated, review before publishing):** Cooler, arid/low-monsoon, erratic solar resource, short low-clearness runs.

**Derived PCM targets:** Tm_target_C = 57.0 C, L_required_kJ_per_kg = 313 kJ/kg (CEILING, not an achievability bar — see 04_climate_signature_rajasthan.py's docstring)


## Cluster 1

- **Points in regime:** 103
- **Total population covered:** 17,959,813
- **Medoid point (climate-feature-space, no district lookup available — lat/lon only):** RJP_0202 (26.875, 73.625)

**Two-tier climate signature (population-weighted mean +/- std):**

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

**Physical description (auto-generated, review before publishing):** Hot, monsoon-influenced, steady solar resource, long low-clearness runs (high autonomy demand).

**Derived PCM targets:** Tm_target_C = 57.0 C, L_required_kJ_per_kg = 304 kJ/kg (CEILING, not an achievability bar — see 04_climate_signature_rajasthan.py's docstring)


## Cluster 2

- **Points in regime:** 103
- **Total population covered:** 29,775,240
- **Medoid point (climate-feature-space, no district lookup available — lat/lon only):** RJP_0055 (26.625, 76.375)

**Two-tier climate signature (population-weighted mean +/- std):**

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

**Physical description (auto-generated, review before publishing):** Cooler, arid/low-monsoon, erratic solar resource, short low-clearness runs.

**Derived PCM targets:** Tm_target_C = 57.0 C, L_required_kJ_per_kg = 320 kJ/kg (CEILING, not an achievability bar — see 04_climate_signature_rajasthan.py's docstring)
