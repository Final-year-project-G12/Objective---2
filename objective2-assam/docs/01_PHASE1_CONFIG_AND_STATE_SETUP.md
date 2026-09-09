# 01 — Phase 1 Audit: Frozen Configuration & State Setup (Rajasthan)

Files: `configs/system_config_shared.yaml`, `configs/design_bounds_shared.yaml`,
`configs/states/rajasthan.yaml`. Loader: `src/io_utils.py`. Phase 0 sanity
check: `check_climate_signature.py`.

> `system_config_shared.yaml`, `design_bounds_shared.yaml`, and `src/io_utils.py`
> are **byte-identical** to `objective2-tamilnadu/`'s copies (verified). Only
> `configs/states/rajasthan.yaml` is state-specific — this audit therefore mirrors
> the Tamil Nadu reference audit's structure, with Rajasthan's own numbers.

## Purpose

Freeze everything Phase 2–4 needs, once, so the simulator can never be
compared against a moving target. Per
`O2_Unified_PerState_Execution_Framework.md`, Phase 0: the two
`*_shared.yaml` files are identical for all four states (Tamil Nadu,
Rajasthan, Assam, Uttarakhand); only `configs/states/<state>.yaml` varies.

## `system_config_shared.yaml` — what's frozen and why

| Category | Value | Source |
|---|---|---|
| Collector | 1.5 m², F_R(τα)=0.75, F_R·U_L=4.5 W/m²K | Domestic FPC baseline [Singh 2025] |
| Tank | 50 L, height:diameter=2:1, U_tank=0.8 W/m²K | Chen et al. 2025 Table 1 |
| PCM integration | Direct encapsulation, Al capsule wall (0.8mm, 205 W/mK) | Framework doc §3.1 |
| Pump | 0.010–0.050 kg/s, η=0.60 | Framework doc §3.1 |
| Safety | max water 75°C, max PCM 65°C, max pressure 3.5 bar | Framework doc §3.1 |
| Delivery | target 45°C | Framework doc §3.1 |
| Solver | backward-Euler (linear-implicit water node, lagged PCM), dt=300s, adaptive sub-stepping | Barqawi 2025 §4c |
| Selection | Pareto tolerance = 5% | Framework doc §9.5 (pre-declared, Bug-Fix 7) |
| Verification | Gate 1 pass <0.1%, warn <0.5%; Gate 4 benchmark band 54-84% | Framework doc §5, Singh 2025 |

Same two config-only additions as Tamil Nadu (not per-state, both live in
the shared file): `melting_half_width_K` (the PCM database reports a
single `Tm_C`, not a measured solidus/liquidus interval) and
`initial_water_temp_C` / `initial_pcm_state` (Gate 2's initial-condition
tests need these overridable).

**This is the config that produces the Cluster-0 safety finding in the
master overview.** `safety.max_pcm_temp_C = 65.0` and `tank.volume_L = 50.0`
are both frozen here, identical to Tamil Nadu — the finding is not a
Rajasthan-specific config choice, it is what this shared config does when
fed Rajasthan's much hotter collector input (see Phase 0 section below).

## `design_bounds_shared.yaml` — what's frozen and why

Sphere-only, staggered-only (the framework doc's documented 40-hr corner
cut). Capsule diameter 0.02–0.08 m, capsule count 8–24 (integer), PCM
volume fraction 0.10–0.20 of tank volume, flow 0.010–0.050 kg/s. Same
diameter/thickness derivation and the same consequence (max reachable PCM
fraction is 12.9%, not 20%) as Tamil Nadu — see `02_PHASE2_GEOMETRY_CONSTRAINTS.md`.

## `configs/states/rajasthan.yaml` — Phase 1's actual output

Every field was read directly off the frozen Objective 1 files already
sitting in `data/objective1/` — nothing in this file is invented:

- **3 Level-A GMM regimes** (`cluster_id` 0–2) — Rajasthan's Objective 1
  clustering chose `K_FINAL=3` (Tamil Nadu chose 5; this is Objective 1's
  own model-selection result, not an Objective 2 choice). Each regime
  carries its population count, `Tm_target_C` (57.0 °C for all 3
  Rajasthan clusters, same value as Tamil Nadu — both states' Objective 1
  pipelines use the same delivery-anchored target), `T_mains_est_C`
  (24.5–25.8 °C across clusters — noticeably lower spread than Tamil
  Nadu's, but read directly off `climate_signature_rajasthan.csv`, not
  estimated), `L_required_kJ_per_kg`, and paths to that cluster's medoid
  hourly/daily weather files — read from `cluster_profiles_rajasthan.csv`.
- **PCM shortlist per regime** — the Top-3 names per cluster from
  `mcdm_topk_by_cluster.csv`: Cluster 0 gets `RT50, RT45HC, Lauric acid
  (C12)`; Clusters 1 and 2 both get `savE® OM50, Paraffin/HDPE PCM3,
  Paraffin/HDPE PCM6` (same Top-3 set for both — Objective 1's MCDM
  consensus, not a copy-paste error; both clusters are the state's
  "hot, higher-demand" regimes per `cluster_profile_cards_rajasthan.md`).
- **Demand profile**: 300 L/day, `data/demand/demand_profile_rajasthan.csv`
  — matches `04_climate_signature_rajasthan.py`'s `NIGHT_DRAW_TOTAL_L=300`
  assumption (Avargani et al. 2021), and deliberately kept identical to
  Tamil Nadu's total so the four-state comparison stays fair (per
  `build_demand_profile.py`'s own docstring).
- **Mains temperature**: 18–30 °C range from the framework doc's Rajasthan
  state-input row; the per-regime point estimate the simulator actually
  uses (`T_mains_est_C`, 24.5–25.8 °C) is the population-weighted mean of
  the point-level column in `climate_signature_rajasthan.csv`, already
  inside that range.
- **Elevation**: unlike Tamil Nadu (which has no dedicated elevation
  script), Rajasthan's Objective 1 has `00c_attach_elevation.py` — a real
  per-point elevation attach, not a flat approximation. This is carried
  through unchanged into Objective 2 (nothing in Phase 1–3 reads elevation
  directly, but it is part of the frozen climate signature record).

## Phase 0 — climate-signature sanity check (Bug-Fix 8): PASSED, 3/3 regimes

`check_climate_signature.py` confirms the frozen weather under
`data/weather/` is genuinely Rajasthan's (hot, dry, high-clearness), not
another state's, and that each daily file is internally clean. Full
output: `results/phase0_climate_signature_check.txt` — see
`results/README.md` for what each line means and the inference drawn.

Summary of what passed, per regime:

| Cluster | Medoid | Mean GHI (kWh/m²/d) | Apr–Jun mean daily-max T_a (°C) | CDD24 | Verdict |
|---|---|---|---|---|---|
| 0 | RJP_0132 | 5.12 | 39.8 | 12,348 | PASS |
| 1 | RJP_0202 | 5.40 | 40.3 | 15,837 | PASS |
| 2 | RJP_0055 | 5.06 | 41.1 | 14,789 | PASS |

All three sit inside the expected 3.0–7.0 kWh/m²/day dry-climate GHI band
and the 33–47 °C Rajasthan summer daily-max band; medoid ids and regime
sizes both match Objective 1's own `cluster_profiles_rajasthan.csv` and
`medoid_points_rajasthan.csv` exactly; zero duplicate (point_id, date)
rows and zero calendar gaps across all 3,653 days (2016–2025) in every
regime's weather file. The hot-dry signature (high CDD24, large DTR,
high daytime clearness, low cloud fraction) is confirmed independently of
the GHI/temperature bands, and is visibly different from Tamil Nadu's
coastal-humid or Assam's humid-cloudy signatures — this is the evidence
that the weather actually being simulated is Rajasthan's, not a
mis-copied file from another state's `data/weather/` folder.

## How Phase 1 was verified

`load_state_config("rajasthan")` in `src/io_utils.py` is exercised every
time any Phase 2/3 function runs (every one of them resolves its weather/
PCM/demand paths through it) — so every successful Phase 2/3 run in this
project is itself an implicit Phase 1 integration test, same as Tamil
Nadu. There is no separate Phase 1 script beyond the Phase 0 sanity check;
see `HOW_TO_RUN`-equivalent commands in `../README.md`.
