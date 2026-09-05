# 01 — Phase 1 Audit: Frozen Configuration & State Setup

Files: `configs/system_config_shared.yaml`, `configs/design_bounds_shared.yaml`,
`configs/states/tamilnadu.yaml`. Loader: `src/io_utils.py`.

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

Two fields were added beyond the original framework table because Phase 3
needed them and they belong in the frozen config, not hard-coded in a
module: `melting_half_width_K` (the PCM database reports a single `Tm_C`,
not a measured solidus/liquidus interval — see Phase 3 doc) and
`initial_water_temp_C` / `initial_pcm_state` (Gate 2's "fully solid vs
fully liquid initial PCM" test needs these to be config-overridable).

## `design_bounds_shared.yaml` — what's frozen and why

Sphere-only, staggered-only (the framework doc's documented 40-hr corner
cut). Capsule diameter 0.02–0.08 m, capsule count 8–24 (integer), PCM
volume fraction 0.10–0.20 of tank volume, flow 0.010–0.050 kg/s.

**Design choice worth flagging explicitly:** for a sphere, the maximum PCM
conduction distance ("thickness") is just the radius = diameter/2. Rather
than sampling thickness and diameter as two independent variables (which
would let the geometry engine produce spheres whose declared "thickness"
doesn't match their actual radius), `capsule_diameter_m` is the sampled
variable and `pcm_thickness_m = diameter/2` is *derived* and then checked
against its own bound. See `02_PHASE2_GEOMETRY_CONSTRAINTS.md` for the
consequence of this (a real interaction between the two bounds).

## `configs/states/tamilnadu.yaml` — Phase 1's actual output

Every field was read directly off the frozen Objective 1 files already
sitting in `data/objective1/` (produced by the pre-existing
`build_input_package.py` / `build_regime_weather.py` /
`build_demand_profile.py` scripts) — nothing in this file is invented:

- **5 Level-A GMM regimes** (`cluster_id` 0–4), each with its population
  count, `Tm_target_C` (all 57.0 °C for TN), `T_mains_est_C`
  (24.0–26.0 °C across clusters), `L_required_kJ_per_kg`, and paths to that
  cluster's medoid hourly/daily weather files — read from
  `cluster_profiles_tamilnadu.csv`.
- **PCM shortlist per regime** — the Top-3 names per cluster from
  `mcdm_topk_by_cluster.csv`. `n-Octacosane (C28)` is Objective 1's
  consensus rank-1 PCM in **every** TN cluster (matches
  `FYP_Tamil_Nadu_Phase_Audits_Consolidated.md` §Phase 6 audit).
- **Demand profile**: 300 L/day, `data/demand/demand_profile_tamilnadu.csv`
  — matches `04b_climate_signature.py`'s `L_required` assumption
  (Avargani et al. 2021), per `build_demand_profile.py`'s own docstring.
- **Climate-signature sanity check (Bug-Fix 8)**: PASSED. Annual
  GHI_daily_kWh across the 5 clusters is 5.13–5.28 kWh/m²/day (inside the
  4.0–5.6 expected band for Tamil Nadu) and RH_mean is 62.5–70.2% —
  consistent with a coastal-humid signature, not e.g. Rajasthan's
  hot-dry/low-humidity one. This confirms the weather being consumed is
  genuinely Tamil Nadu's, not a mis-copied file.

## Known, documented Objective 1 limitation carried forward unchanged

Tamil Nadu has **no dedicated elevation script** (unlike Rajasthan's
`00c_attach_elevation.py`) — `02_combine_tamilnadu.py` uses a flat 150 m
elevation approximation. Objective 2 does not fix this; it is inherited
and noted, per the framework doc's rule that Objective 1 changes are a
stop-and-rebuild event, not a mid-run patch.

## How Phase 1 was verified

`load_state_config("tamilnadu")` in `src/io_utils.py` is exercised every
time any Phase 2/3/4 function runs (every one of them resolves its weather/
PCM/demand paths through it) — so every successful Phase 3/4 run in this
project is itself an implicit Phase 1 integration test. There is no
separate Phase 1 script to run; see `HOW_TO_RUN.md`.
