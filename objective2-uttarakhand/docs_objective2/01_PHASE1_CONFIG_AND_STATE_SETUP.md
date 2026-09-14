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

**Regenerated 2026-09-13** directly from `data/objective1/cluster_profiles_uttarakhand.csv`
and `data/objective1/mcdm_topk_by_cluster.csv`, after Objective 1's 2026-09-13
bug-fix pass (MCDM ranking/feasibility/physics-validation fixes, corrected
`run_all_uttarakhand.py` phase skip) changed the GMM's point assignments.

**Bug found and fixed**: the *previous* version of this file was a
hand-written snapshot from an earlier Objective 1 run and was never
regenerated after that fix — it silently went stale against the freshly
rebuilt `data/weather/` files (which always reflect the *current*
clustering). Specifically, **cluster_id 1 and 2 were swapped**: the old
config's `cluster_id: 1` entry (T_mains≈17.0°C, 9 points) actually described
what is now `cluster_id: 2`, and its `cluster_id: 2` entry (T_mains≈7.4°C,
3 points, small-sample) actually described what is now `cluster_id: 1`.
Cluster 0 and 4's point counts also shifted (15→7 and 8→16 respectively) —
not a pure relabeling, a genuine re-clustering. Since
`src/simulation/run_case.py` reads `mains_temp_C` directly from this file's
`regime["T_mains_est_C"]` (never recomputed from the weather data at
runtime), every Phase 4–8 run against the stale config used the wrong mains
temperature, wrong `L_required` target, and wrong PCM shortlist for 3 of the
5 cluster IDs. All phases have been re-run against the corrected file.

Every field is now read directly off the current CSVs, not a console
transcript:

- **5 Level-A GMM regimes** (`cluster_id` 0–4), each with its population
  count, `T_mains_est_C` (7.45–21.82 °C, copied from
  `cluster_profiles_uttarakhand.csv`'s own `T_mains_est_C` column),
  `L_required_kJ_per_kg` (118.0–178.1 kJ/kg, highest in **regime 1** — now
  the coldest, smallest-sample regime — due to coldest ambient), and paths
  to that cluster's medoid hourly/daily weather files.
- **`Tm_target_C` and `pcm_shortlist` were subsequently retargeted
  (2026-09-14, see `12_TM_TARGET_RETARGETING.md`)** — this section
  describes the values as originally set from Objective 1's own MCDM
  consensus (`Tm_target_C` a flat 57.0°C for every regime, from a
  climate-blind delivery-anchored formula), which is what
  `mcdm_topk_by_cluster.csv` still reports and what the table below
  reflects. **The live `configs/states/uttarakhand.yaml` now has
  different, per-regime retargeted values** (27.8–42.1°C, and a
  different PCM shortlist in 4 of 5 regimes) — see doc 12 for the
  current, actually-used values.
- **PCM shortlist per regime (Objective 1's original MCDM consensus,
  before retargeting)** — the Top-3 names per cluster from
  `mcdm_topk_by_cluster.csv`. **PureTemp 58 (Tm = 58.0 °C)** is
  rank-1 in regimes 0, 2, 3, 4. **Regime 1 is the outlier**: its rank-1 PCM
  is **PureTemp 53** (Tm = 53.0 °C, a better match for this regime's colder
  operating temperatures), with n-Hexacosane (C26) and Myristic acid (C14)
  as rank-2/3 — none of which overlap with any other regime's shortlist.
  Regimes 2 and 3 shortlist "savE® OM55" as rank-2. Regime 1 is also the
  only regime where retargeting later found no better candidate, so this
  original shortlist is what's actually still in use there (doc 12).
- **Demand profile**: 300 L/day, `data/demand/demand_profile_uttarakhand.csv`
  — matches `04b_climate_signature.py`'s `L_required` assumption
  (Avargani et al. 2021), per `build_demand_profile.py`'s own docstring.
- **Climate-signature sanity check**: Annual GHI_daily_kWh across the 5
  clusters is 4.57–4.90 kWh/m²/day (inside the 4.5–5.0 expected band for
  Uttarakhand) — essentially unchanged by the re-clustering, since GHI
  varies little across regimes here. RH_mean was not captured in the console
  output at config-write time — cross-check against
  `cluster_profiles_uttarakhand.csv` directly if needed.

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
