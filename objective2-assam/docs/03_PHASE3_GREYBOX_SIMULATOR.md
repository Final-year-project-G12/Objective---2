# 03 — Phase 3 Audit: Grey-Box Enthalpy Simulator (Assam)

Files: `src/simulation/capsule_enthalpy.py`, `collector_model.py`,
`heat_transfer.py`, `hydraulic_model.py`, `demand_profile.py`,
`energy_balance.py`, `tank_model.py`, `run_case.py`.

> This engine is **state-agnostic** (byte-identical across all 4
> states) — the bug-fix history and submodel descriptions below are
> unchanged from the Rajasthan/Tamil Nadu audits. What's corrected here:
> the previous version of this doc quoted a Rajasthan smoke-run
> (`RT50`, cluster0, ~1581 kWh) as if it were Assam's. **No standalone
> `results/phase3_simulate_*.json` files exist for Assam** — the
> closest verified numbers are Phase 4's Gate 1/2 cases and Phase 5's
> `c0_baseline_noPCM` DOE row, used below instead of inventing a smoke
> run that was never saved.

## Purpose (D2.3)

The authoritative physics evaluator for Objective 2 — extends Objective
1's lumped-enthalpy tank to include capsule geometry, flow rate, heat
transfer and pump energy against real hourly medoid weather. One
simulation = one full year, hourly weather, sub-hourly (5-minute
nominal) internal stepping. For Assam this means Cluster 0/1/2's medoid
weather (`data/weather/weather_regime_assam_cluster*_hourly.csv`),
Assam's `data/demand/demand_profile_assam.csv` (100 L/day, not 300),
`data/objective1/pcm_database_assam.csv`, and
`configs/states/assam.yaml` for regime metadata and mains temperature.

## State vector & submodels

| Submodel | File | Method |
|---|---|---|
| Collector | `collector_model.py` | Hottel-Whillier-Bliss: `Q=A_c[F_R(τα)I - F_R U_L(T_in-T_amb)]`, zero output below a minimum-irradiance cutoff |
| PCM enthalpy | `capsule_enthalpy.py` | Piecewise `h(T)` with clipped liquid fraction `f=clip((h-h_s)/L, 0, 1)`; single-group (identical capsules) |
| Heat transfer | `heat_transfer.py` | `1/UA_eff = 1/(h_w A_w) + R_wall + R_pcm,eff`; `h_w` via Wakao & Kaguei (1982) packed-bed correlation |
| Hydraulics | `hydraulic_model.py` (wraps `design/geometry.py`) | Ergun equation, reported separately from thermal energy |
| Demand | `demand_profile.py` | Assam's 100 L/day two-pulse (07:00/19:00) curve, spread evenly across sub-hourly steps |
| Tank/water balance | `tank_model.py` | Linear-implicit (closed-form) backward Euler per sub-step, PCM temperature lagged one sub-step |

## Documented simplifications (same 7 items as every state — not repeated in full here)

Single-node direct-tank system; single thermal capsule group; melting
treated as a narrow ±1 K band around a single `Tm_C`; a ×2.0
liquid-convection enhancement factor above 50% liquid fraction; hourly
weather held constant across sub-steps; demand spread evenly within
each hour; pressure drop models only the packed-capsule-bed term. See
`objective2-rajasthan/docs/03_…` for the full itemized list — identical
engine, identical caveats.

## Bug fixes inherited (shared engine — not re-discovered per state)

Both fixes below were found and fixed once, in the shared engine, and
are present in every state's copy including Assam's:

1. **Reverse-collector-flow accounting leak** — sub-steps that would
   imply negative collector heat now re-solve with the collector off,
   keeping the solve and the energy accounting self-consistent.
2. **Adaptive sub-stepping for stiff (high-conductivity) capsules** —
   sub-step count now respects the PCM's own thermal time constant
   (`dt_sub ≤ 0.5·τ_pcm`), fixing a divergence in the "very high PCM
   conductivity" limiting case.

Gate 1's Assam residuals below confirm both fixes are intact here too.

## Solar-fraction definition used here

`solar_fraction = 1 − E_unmet / E_demand_ideal`, where `E_demand_ideal`
is the energy to heat the full 100 L/day draw from mains temperature to
the 45 °C delivery target (Assam's own `Tm_target_C = 44.0 °C` is the
per-regime latent-heat design target, distinct from this fixed 45 °C
solar-fraction reference — see `system_config_shared.yaml`), and
`E_unmet` is the accumulated shortfall. No auxiliary/backup heater is
modeled, so this is a strict fraction — same convention as every state.

## Nearest verified numbers for Assam (Phase 4 Gate 1 / Phase 5 baseline — not a standalone Phase 3 smoke-run file)

`c0_baseline_noPCM` (Cluster 0, no PCM, `d=0.08 m, n=8, flow=0.030 kg/s`
— from `results/phase5_design_cases.csv`):

| metric | value | note |
|---|---|---|
| `status` | complete (8760 h) | full year, no NaN/inf |
| `residual_pct_of_collector` | ~3e-12 % | effectively zero — Bug-Fix 1 intact |
| `useful_energy_kWh` | 680.92 | Assam's 100 L/day demand vs. Rajasthan's ~1581 kWh at 300 L/day — not comparable without rescaling |
| `solar_fraction` | 0.6251 | |
| `max_water_temp_C` | 66.84 | **> 65 °C PCM limit**, even for the plain (no-PCM) tank — same Gate-2-documented overheat as Rajasthan Cluster 0 |
| `pump_energy_kWh` | ~7e-10 | Ergun packed-bed term only, negligible |

Gate 1's five cases (`04_PHASE4_VERIFICATION_GATES.md`) all report
residuals of 0.000000% at the report's printed precision, across
Clusters 0–2 and `savE® OM48` plus a plain-tank baseline and a
bounds-extreme design — the engine behaves identically to every other
state's copy.

## How to run one case

```
python pipeline.py --state assam --stage simulate --cluster 0 \
    --pcm "savE® OM48" --diameter 0.0403 --count 24 --flow 0.046
python pipeline.py --state assam --stage simulate --cluster 1 --no-pcm
```

Prints the full metrics dict (useful energy, solar fraction,
delivery-temperature hours, unmet energy, pump energy, PCM mass, max
water/PCM temperature, safety-violation count, melt-fraction stats,
complete melt cycles, energy-balance residual %). A design that fails
the Phase 2 geometry gate prints `REJECTED at Phase 2 geometry gate`
and the simulator is never run. Running this and saving the output to
`results/phase3_simulate_*.json` (as done for Rajasthan/Tamil Nadu) has
not been done for Assam in this repo.
