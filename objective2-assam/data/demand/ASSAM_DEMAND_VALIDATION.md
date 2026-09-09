# Assam Demand Profile Validation (Option B — Discrete Flushes)

## 1. Context & Methodology
In Assam Objective 1 ([10_physics_validation.py](file:///m:/Final_year_pro/PCM-Selection-ML-model/era5-assam/10_physics_validation.py#L112) and [05b_swh_design_specification.py](file:///m:/Final_year_pro/PCM-Selection-ML-model/era5-assam/05b_swh_design_specification.py)), the domestic SWH specification standardizes on a **100 L/day (100 kg/day)** consumption profile divided into two discrete draw flushes:
- **Morning Peak:** 50 kg at **07:00 IST**
- **Evening Peak:** 50 kg at **19:00 IST**
- **Other Hours:** 0 kg

## 2. Validation Metrics
- Total daily draw: $50.0 + 50.0 = 100.0\text{ kg/day}$ ($100.0\text{ L/day}$ at $\rho \approx 1000\text{ kg/m}^3$)
- Morning fraction: 0.50 (Hour 7)
- Evening fraction: 0.50 (Hour 19)
- Off-peak draw: strictly 0.00 kg across all 22 other hours
- Verified compatible with `src.simulation.demand_profile.DemandModel`.
