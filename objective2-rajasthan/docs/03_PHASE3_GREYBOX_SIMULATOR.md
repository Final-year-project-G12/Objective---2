# 03 — Phase 3 Audit: Grey-Box Enthalpy Simulator (Rajasthan)

Files: `src/simulation/capsule_enthalpy.py`, `collector_model.py`,
`heat_transfer.py`, `hydraulic_model.py`, `demand_profile.py`,
`energy_balance.py`, `tank_model.py`, `run_case.py`.

> All eight modules are **byte-identical** to `objective2-tamilnadu/src/simulation/`
> (`diff -rq` returns nothing). Phase 3 is the state-agnostic physics engine;
> per `O2_Unified_PerState_Execution_Framework.md` it must not change per state.
> Rajasthan differs only in what `run_case.py` looks up through `src/io_utils.py`:
> weather (`data/weather/weather_regime_rajasthan_cluster*_hourly.csv`), demand
> (`data/demand/demand_profile_rajasthan.csv`), PCM records
> (`data/objective1/pcm_database_rajasthan.csv`), mains temperature and regime
> metadata (`configs/states/rajasthan.yaml`). This audit therefore mirrors the
> Tamil Nadu reference audit; the bug-fix history below is the shared engine's.

## Purpose (D2.3)

The authoritative physics evaluator for Objective 2 — extends Objective
1's lumped-enthalpy tank to include capsule geometry, flow rate, heat
transfer and pump energy against real hourly medoid weather. One
simulation = one full year, hourly weather, sub-hourly (5-minute nominal)
internal stepping.

## State vector & submodels

| Submodel | File | Method |
|---|---|---|
| Collector | `collector_model.py` | Hottel-Whillier-Bliss: `Q=A_c[F_R(τα)I - F_R U_L(T_in-T_amb)]`, zero output below a minimum-irradiance cutoff |
| PCM enthalpy | `capsule_enthalpy.py` | Piecewise `h(T)` with clipped liquid fraction `f=clip((h-h_s)/L, 0, 1)`; single-group (identical capsules) |
| Heat transfer | `heat_transfer.py` | `1/UA_eff = 1/(h_w A_w) + R_wall + R_pcm,eff`; `h_w` via Wakao & Kaguei (1982) packed-bed correlation |
| Hydraulics | `hydraulic_model.py` (wraps `design/geometry.py`) | Ergun equation, reported separately from thermal energy |
| Demand | `demand_profile.py` | 300 L/day canonical curve, spread evenly across sub-hourly steps |
| Tank/water balance | `tank_model.py` | Linear-implicit (closed-form) backward Euler per sub-step, PCM temperature lagged one sub-step |

## Documented simplifications (state them in the report, don't hide them)

1. **Single-node, direct-tank system** — the collector inlet IS the tank
   water temperature (no separate collector-loop node).
2. **Single thermal capsule group** — all capsules identical, see the same
   bulk water temperature.
3. **Melting treated as a narrow band** (`Tm ± melting_half_width_K`, 1 K)
   because the PCM database reports only a single `Tm_C`, not a measured
   solidus/liquidus interval.
4. **Liquid natural convection** inside the capsule is not resolved — a
   documented ×2.0 effective-conductivity enhancement factor is applied
   once liquid fraction ≥ 0.5.
5. **Hourly weather held constant** across the 12 five-minute sub-steps
   within each hour (zero-order hold) — the source NASA POWER data is
   hourly resolution.
6. **Sub-hourly demand timing** is spread evenly within each hour (the
   canonical demand file has hourly resolution, not sub-hourly).
7. **Pressure drop** only models the packed-capsule-bed term (Ergun) —
   pipe/valve losses in the rest of the loop are out of scope.

None of these are hidden inside the code — each function's docstring
states which resistance/energy terms are *measured*, *correlated*, or
*assumed*, per the framework doc's explicit requirement (§4.5).

## Bug found and fixed during Phase 4 testing: energy-conservation leak from implicit reverse-collector-flow

**Symptom**: Gate 1's very first run showed a 1.6% energy-balance residual
— above the 0.5% hard limit.

**Root cause**: the water-node solve is linear in `T_w_new` and includes
the collector term `Q_collector = a - b·T_w_new`. On days where the tank
gets hot enough that the linear solve implied `a - b·T_w_new < 0` (i.e.
the collector loop, run in reverse, would extract heat — physically what
a real system's differential controller prevents by stopping the pump),
the **solve** used that negative value to compute `T_w_new`, but the
**energy accounting** clipped logged `Q_collector` to `max(...,0)` for
reporting. The result: real heat was silently removed from the tank in
the solve but never subtracted from logged `E_collector`, so logged input
energy systematically overstated what actually warmed the water.

**Fix** (`tank_model.py`, search "Differential-controller re-solve"): each
sub-step now solves once assuming circulation; if that solve implies
reverse flow, it **re-solves with the collector off** for that sub-step
(mimicking a real differential thermostat) before logging anything. This
makes the physics and the accounting self-consistent by construction.

**Result**: residual dropped from ~1.6% to **~0.00002%** (essentially
floating-point noise). On Rajasthan Cluster 0 (RJP_0132) the sample run
below reports `residual_pct_of_collector ≈ 6e-4 %` — same regime, well
under the 0.1% Gate-1 pass threshold.

## Numerical-stability fix: adaptive sub-stepping for stiff (high-conductivity) capsules

**Symptom**: Gate 2's "very high PCM conductivity" limiting-case test
(`TC_W_mK × 200`) produced an astronomically large, clearly-diverged
`T_pcm` (~10^300).

**Root cause**: the PCM temperature is updated one sub-step behind the
water temperature (a semi-implicit/IMEX coupling, chosen so the water-node
solve stays a closed-form linear equation — see the module docstring for
why). This is stable as long as each sub-step is short relative to the
PCM's own thermal time constant `τ = m_pcm·cp/UA_eff`. The original
sub-stepping rule only added extra sub-steps when `T_pcm` was near the
melting band — it never checked `τ` itself, so an artificially large `UA`
(from the 200× conductivity multiplier) made `τ` shorter than one 5-minute
sub-step, and the lagged coupling oscillated and diverged.

**Fix** (`tank_model.py`, search "Adaptive stiffness check"): before
choosing the sub-step count, the code now estimates `UA_eff` at the
current state, computes `τ_pcm = m_pcm·cp_min/UA_eff`, and forces
`dt_sub ≤ 0.5·τ_pcm` (capped at 60 sub-steps/step as a safety valve). A
hard numerical backstop (`T_pcm` clipped to [-50, 500] °C, counted as a
"clipped step") also exists so an extreme, physically-unreasonable
property combination can never silently propagate `NaN`/`inf` through a
whole year of stepping.

**Result**: the high-conductivity case now gives a *smaller* mean
|T_w−T_pcm| gap than the nominal-conductivity case (0.098 °C vs 0.326 °C)
— the physically-correct direction — instead of diverging.

## Solar-fraction definition used here

`solar_fraction = 1 − E_unmet / E_demand_ideal`, where `E_demand_ideal` is
the energy required to heat the full 300 L/day draw from mains temperature
to the 45 °C delivery target, and `E_unmet` is the accumulated shortfall
whenever delivered water falls below 45 °C. This is the standard
"fraction of ideal demand actually met at target temperature" definition;
there is **no auxiliary/backup heater modeled**, so this project's solar
fraction is stricter than a real installed system's (which would top up
the shortfall electrically).

## Phase 3 smoke run — Rajasthan Cluster 0 (RJP_0132)

```
python pipeline.py --state rajasthan --stage simulate --cluster 0 --pcm "RT50" --diameter 0.08 --count 24 --flow 0.025
```

| metric | value | note |
|---|---|---|
| `status` | complete (8760 h) | full year, no NaN/inf |
| `residual_pct_of_collector` | ~6.4e-4 % | ≪ 0.1% Gate-1 pass — Bug-Fix 1 intact |
| `useful_energy_kWh` | ~1581 | vs Tamil Nadu Cluster 0 ~1660 (different weather) |
| `solar_fraction` | ~0.55 | strict definition, no backup heater |
| `pump_energy_kWh` | ~1e-8 | Ergun packed-bed term only; negligible at this flow |
| `max_pcm_temp_C` | ~69 | **> 65 °C safety limit**; `n_safety_violations` ~896 |

**Observation for Phase 4, not a simulator bug:** RT50 (Tm 50 °C) at the
maximum-loading geometry in hot Cluster 0 is repeatedly driven past the
65 °C PCM stability limit (896 flagged sub-hours, 127 complete melt
cycles). That is a real physical result and exactly what Gate 2's safety
check and the Phase 7 selection rule are meant to reject — this specific
design/PCM pairing is not deployable as-is. The `--no-pcm` baseline and
the mid-geometry cases (`d=0.04, n=12`, flow 0.010 and 0.050) all complete
cleanly with residuals ~3e-4 %.

## How to run one case

```
python pipeline.py --state rajasthan --stage simulate --cluster 0 --pcm "RT50" --diameter 0.08 --count 24 --flow 0.025
python pipeline.py --state rajasthan --stage simulate --cluster 1 --no-pcm
```
Prints the full metrics dict (useful energy, solar fraction,
delivery-temperature hours, unmet energy, pump energy, PCM mass, max
water/PCM temperature, safety-violation count, melt-fraction stats,
complete melt cycles, energy-balance residual %). One call ≈ 1–4 seconds.
A design that fails the Phase 2 geometry gate (e.g. `--count 1`) prints
`REJECTED at Phase 2 geometry gate: reason=bounds_violation` and the
simulator is never run.
