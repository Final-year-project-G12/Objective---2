# 01 — Phase 1 Audit: Frozen Configuration & State Setup

Files: `configs/system_config_shared.yaml`, `configs/design_bounds_shared.yaml`,
`configs/states/uttarakhand.yaml`. Loader: `src/io_utils.py`.

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
| Delivery | target 50.0°C (matches Obj1's T_DELIVERY_C) | See delivery note below |
| Solver | backward-Euler (linear-implicit water node, lagged PCM), dt=300s, adaptive sub-stepping | Barqawi 2025 §4c |
| Selection | Pareto tolerance = 5% | Framework doc §9.5 (pre-declared, Bug-Fix 7) |
| Verification | Gate 1 pass <0.1%, warn <0.5%; Gate 4 benchmark band 54-84% | Framework doc §5, Singh 2025 |

**Delivery temperature note**: the shared config uses `target_temp_C: 50.0` (not
45°C), to match Objective 1's `04b_climate_signature.py`'s `T_DELIVERY_C=50.0`,
which is the temperature the entire MCDM PCM shortlist was actually selected
against (`Tm_target_C=57.0` derives from this). This is a FROZEN shared
value — changing it means Phases 3–8 must re-run for this state.

Two fields were added beyond the original framework table because Phase 3
needed them: `melting_half_width_K` (the PCM database reports a single
`Tm_C`, not a measured solidus/liquidus interval) and `initial_water_temp_C`
/ `initial_pcm_state` (Gate 2's "fully solid vs fully liquid initial PCM"
test needs these to be config-overridable).

## `design_bounds_shared.yaml` — what's frozen and why

Sphere-only, staggered-only (the framework doc's documented 40-hr corner
cut). Capsule diameter 0.02–0.08 m, capsule count 8–24 (integer), PCM
volume fraction 0.10–0.20 of tank volume, flow 0.010–0.050 kg/s.

**Design choice worth flagging explicitly:** for a sphere, the maximum PCM
conduction distance ("thickness") is just the radius = diameter/2. Rather
than sampling thickness and diameter as two independent variables,
`capsule_diameter_m` is the sampled variable and `pcm_thickness_m =
diameter/2` is *derived* and then checked against its own bound. See
`02_PHASE2_GEOMETRY_CONSTRAINTS.md` for the consequence of this (a real
interaction between the two bounds).

## `configs/states/uttarakhand.yaml` — Phase 1's actual output

Every field was read directly off Uttarakhand's Objective 1 console output
(post-fix: `ASSUMED_PCM_MASS_KG=150`, `covariance_type="diag"`) from the
`05_cluster_uttarakhand.py`, `07_feasibility_filter.py`, and
`08_mcdm_ranking.py` runs. Nothing in this file is invented:

- **5 Level-A GMM regimes** (`cluster_id` 0–4), each with its population
  count, `Tm_target_C` (all 57.0 °C — climate/delivery-anchored, same
  derivation as Tamil Nadu), `T_mains_est_C` (7.4–21.8 °C, DERIVED as
  `Ta_mean − 2.0` — marked in the yaml for local cross-check), `L_required_kJ_per_kg`
  (118–178 kJ/kg, highest in regime 2 due to coldest ambient), and paths to
  that cluster's medoid hourly/daily weather files.
- **PCM shortlist per regime** — the Top-3 names per cluster from
  `mcdm_topk_by_cluster.csv`. **PureTemp 58 (Tm = 58.0 °C)** appears as
  rank-1 in every regime (regimes 0, 2, 4) or rank-1 (regimes 1, 3). Key
  regime-specific variations: regimes 1 and 3 shortlist "Palmitic-stearic
  acid/Expanded graphite" as rank-2 instead of PlusICE A58.
- **Demand profile**: 300 L/day, `data/demand/demand_profile_uttarakhand.csv`
  — matches `04b_climate_signature.py`'s `L_required` assumption
  (Avargani et al. 2021), per `build_demand_profile.py`'s own docstring.
- **Climate-signature sanity check**: Annual GHI_daily_kWh across the 5
  clusters is 4.57–4.93 kWh/m²/day (inside the 4.5–5.0 expected band for
  Uttarakhand). RH_mean was not captured in the console output at
  config-write time — cross-check against `cluster_profiles_uttarakhand.csv`
  once data is copied in locally.

## Known, documented Objective 1 limitations carried forward unchanged

Uttarakhand has **no dedicated elevation-attachment script**, and three
inconsistent elevation values coexist: 0 m in `00b_build_suntimes.py`,
1200 m flat `DEFAULT_ALT_M` in `02_combine`, and a pressure-derived
`elev_proxy` in `04b` (itself clipped by `era5_P_atm ≥ 850 hPa`, which
affects ~37% of high-elevation readings). Objective 2 does not fix this; it
is inherited and noted. This is a stronger limitation than Tamil Nadu's
(which used a flat 150 m approximation), because Uttarakhand has genuinely
large elevation variation — any future revision of the elevation treatment in
Objective 1 would require Objective 2 to re-run from Phase 2 onward.

## How Phase 1 was verified

`load_state_config("uttarakhand")` in `src/io_utils.py` is exercised every
time any Phase 2/3/4 function runs — so every successful Phase 3/4 run in
this project is itself an implicit Phase 1 integration test. There is no
separate Phase 1 script to run; see `HOW_TO_RUN.md`.
