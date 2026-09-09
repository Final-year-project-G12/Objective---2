# ASSAM OBJECTIVE 2 — WEATHER DATASET VALIDATION REPORT

**Date of Generation:** 2026-09-09  
**Source Dataset:** ERA5 Reanalysis NetCDF coordinate cache (`PCM-Selection-ML-model/era5-assam/data/raw/era5/points/`)  
**Target Architecture:** Objective 2 Multi-State Simulation Pipeline  
**Reference Year:** 2025 (Canonical 1-year continuous series)  

---

## 1. Provenance & Medoid Mapping

The hourly weather files correspond strictly to the final $K=3$ GMM climate regime medoids derived in Objective 1 Phase 3 (`05_cluster_assam.py`) and verified under Phase 11 (`final_project_verification.py`):

| Cluster | Regime Name | Medoid Point ID | Latitude ($^\circ$N) | Longitude ($^\circ$E) | Grid Population | Grid Weight | Output File |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **0** | Lower Brahmaputra Valley | `ASP_0012` | 26.375 | 92.125 | 140,778.8 | 0.01225 | `weather_regime_assam_cluster0_hourly.csv` |
| **1** | Upper Assam Tea Belt | `ASP_0092` | 26.875 | 94.875 | 53,803.3 | 0.00468 | `weather_regime_assam_cluster1_hourly.csv` |
| **2** | Barak Valley / Southern Hills | `ASP_0028` | 27.625 | 94.875 | 105,129.8 | 0.00915 | `weather_regime_assam_cluster2_hourly.csv` |

---

## 2. Temporal & Variable Schema Validation

Each regime file provides the complete standard Objective 2 weather schema:
- `timestamp_utc`: ISO-8601 UTC timestamp (`YYYY-MM-DD HH:MM:SS+00:00`)
- `GHI_Wm2`: Global Horizontal Irradiance ($W/m^2$), de-accumulated from ERA5 $SSRD$ using duration-overlap allocation
- `T_amb_C`: Ambient 2m dry-bulb temperature ($^\circ$C) from ERA5 $T_{2m}$
- `RH_pct`: Relative humidity (%) derived from ERA5 $T_{2m}$ and $D_{2m}$ via the standard Magnus-Tetens relationship
- `WS_ms` / `wind_ms`: 10m horizontal wind speed ($m/s$) calculated from ERA5 $u_{10}, v_{10}$ vector components
- `sp_Pa`: Surface barometric pressure ($Pa$)
- `GHI_clearsky_Wm2`: Clearsky solar radiation ($W/m^2$) de-accumulated from ERA5 $SSRD_c$
- `Tmains_C`: Mains water inlet temperature ($^\circ$C), dynamically modeled as $\max(5.0^\circ\text{C}, T_{\text{amb, daily mean}} - 6.0\text{ K})$
- `local_hour`, `local_date`, `point_id`, `cluster_id`, `year`: Standard tracking metadata

---

## 3. Data Integrity & Validation Audit

All 3 exported regime files passed rigorous automated data integrity assertions:

| Validation Metric | Cluster 0 (`ASP_0012`) | Cluster 1 (`ASP_0092`) | Cluster 2 (`ASP_0028`) | Requirement / Status |
| :--- | :--- | :--- | :--- | :--- |
| **Row Count** | 8,760 | 8,760 | 8,760 | Exactly 8,760 hours (non-leap 2025) — **PASSED** |
| **Start Timestamp** | 2025-01-01 00:00:00+00:00 | 2025-01-01 00:00:00+00:00 | 2025-01-01 00:00:00+00:00 | Exact year boundary — **PASSED** |
| **End Timestamp** | 2025-12-31 23:00:00+00:00 | 2025-12-31 23:00:00+00:00 | 2025-12-31 23:00:00+00:00 | Exact year boundary — **PASSED** |
| **Timestamp Continuity** | $\Delta t = 1.0\text{ h}$ constant | $\Delta t = 1.0\text{ h}$ constant | $\Delta t = 1.0\text{ h}$ constant | Zero missing hours, zero duplicates — **PASSED** |
| **Missing / Null Cells** | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 100% complete data matrix — **PASSED** |
| **GHI Validity** | Finite, $\ge 0.0$ | Finite, $\ge 0.0$ | Finite, $\ge 0.0$ | Strict physical non-negativity — **PASSED** |
| **Nighttime GHI** | Identically 0.0 $W/m^2$ | Identically 0.0 $W/m^2$ | Identically 0.0 $W/m^2$ | Zero nocturnal radiation verified — **PASSED** |
| **Annual GHI ($kWh/m^2$)** | 887.02 | 919.97 | 831.64 | Consistent with monsoonal valley attenuation |
| **Daily Mean GHI ($kWh/m^2/d$)** | 2.430 | 2.520 | 2.278 | Verified within Assam climate bounds |
| **Annual Mean $T_{\text{amb}}$ ($^\circ$C)** | 25.92 | 24.93 | 22.68 | Matches Objective 1 signature means |
| **Annual Mean RH (%)** | 77.8% | 81.1% | 81.3% | Confirms humid subtropical character (>70%) |
| **Annual Mean Wind ($m/s$)** | 1.71 | 1.29 | 1.12 | Moderate valley shelter effect |
| **Mean $T_{\text{mains}}$ ($^\circ$C)** | 19.92 | 18.93 | 16.68 | Matches O1 SWH spec estimates ($19.89, 19.10, 16.59$) |

---

## 4. Methodological Transparency & Limitations

1. **Duration-Overlap Energy Conservation:**  
   SSRD is a forward-accumulated forecast flux. Allocation to hourly bins uses proportional interval-duration overlap matching Objective 1's `10_physics_validation.py`. This provides strict First-Law energy conservation ($<0.0001\%$ error) without fabricating artificial sub-hourly variations.
2. **Direct DNI & DHI:**  
   ERA5 coordinate NetCDFs do not carry continuous hourly direct normal ($DNI$) or diffuse ($DHI$) irradiance (these are only calculated at 3 sun-event points in `assam_cleaned_physical.csv`). Rather than inventing synthetic decomposition models, direct beam/diffuse components are omitted, which conforms strictly to the grey-box lumped tank simulator requirements (`run_case.py`), where total incident flux $GHI$ on collector area $A_c$ drives thermal gain.
3. **Alternate/Member-Point Status:**  
   No secondary member-point hourly weather dataset is currently exported. Objective 2 will employ the identical method developed and approved for Rajasthan: **medoid-anchored simulation with Gaussian noise perturbation during Phase 8 Monte Carlo robustness testing**.
