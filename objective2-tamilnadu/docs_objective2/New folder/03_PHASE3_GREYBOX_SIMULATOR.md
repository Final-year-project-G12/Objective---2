# 03 — Phase 3 Audit: Grey-Box Enthalpy Simulator

Files: `src/simulation/capsule_enthalpy.py`, `collector_model.py`,
`heat_transfer.py`, `hydraulic_model.py`, `demand_profile.py`,
`energy_balance.py`, `tank_model.py`, `run_case.py`.

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
floating-point noise) — see `04_PHASE4_VERIFICATION_GATES.md` Gate 1.

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

## How to run one case

```
python pipeline.py --state tamilnadu --stage simulate --cluster 0 \
    --pcm "n-Octacosane (C28)" --diameter 0.08 --count 19 --flow 0.030
```
Prints the full metrics dict (useful energy, solar fraction,
delivery-temperature hours, unmet energy, pump energy, PCM mass, max
water/PCM temperature, safety-violation count, melt-fraction stats,
complete melt cycles, energy-balance residual %). One call ≈ 1–4 seconds.
