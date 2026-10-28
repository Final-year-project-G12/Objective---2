# 01 - Simulator, repairs and metrics (as implemented)

Evidence for every statement is in `docs/PROGRESS.md` (section numbers in brackets) and the tests named below.

## 1. Entry point

`src/simulation/run_case.py: run_case(state, cluster_id, pcm_name, design, ...)` builds the case and runs one weather year.
`pcm_name=None` gives the water-only tank with the same design vector. Useful options:

| Option | Meaning |
|---|---|
| `tank_model="single"` (default) / `"multinode"` | single mixed node (`src/simulation/tank_model.py`, kept as the regression reference) or the stratified tank (`src/simulation/tank_model_multinode.py`) |
| `n_nodes=10`, `stack_anchor="center"` | multi-node settings (the approved design space fixes both, `configs/design_space.yaml`) |
| `weather=<DataFrame>` | run a given point-year (see `02`) instead of the legacy regime file |
| `compute_tes_metrics=True`, `night_day_stride=k` | add the WP1 metrics and night scenarios every k-th day (`0` skips the scenarios) |
| `initial_state`, `stop_when_Tw_below_C` | used by the night scenarios |

The production time step is **150 s** (`solver.timestep_s` in `configs/system_config_shared.yaml`). The 300 s step failed the convergence criterion (plain tank changed 0.073-0.091 % on halving); 150 s passes
(largest change 0.0453 % on any halving, [section 4]).

## 2. Repairs to the model (Level 1) and what they changed

| Repair | Where | Effect |
|---|---|---|
| Demand follows **local** time (`local_hour`, the floor of IST) instead of UTC hour | `src/simulation/tank_model.py: _demand_hour_of_day` | plain-tank annual useful energy fell 30.7 / 34.9 / 32.4 % (regimes 0/1/2) [3]. A frame with only `timestamp_utc` is refused. |
| PCM mass from the **inner** sphere (D - 2 t_wall); wall heat capacity carried in the PCM node | `src/simulation/capsule_mass.py`, `src/simulation/capsule_enthalpy.py` | the older outer-volume mass overstated PCM by 11.5 / 5.9 % [4]. Aluminium density 2700 kg/m3 and cp 900 J/kg K are handbook values, not in the frozen config. |
| PCM conduction path uses the inner radius and inner area (thickness = inner radius) | `src/simulation/heat_transfer.py` | decision D3 |
| 29 February dropped, every year 8760 h | `io_utils.drop_leap_day`, `load_hourly_weather(drop_29_feb=True)` | |
| Pump energy flagged `pump_energy_meaningful=False` | `src/simulation/run_case.py` | Ergun pressure drop across the bed only; do not use as an objective |

## 3. Multi-node tank

N equal nodes (default 10). Draw is plug flow from the mains at the bottom; the outlet is the top node. The collector loop takes water
from the bottom node at the design flow and returns it at the node of equal temperature, so **flow sets the loop temperature rise
and the inlet level, not the collector heat** (the project collector F_R does not depend on flow). Upwind advection, axial conduction,
per-node ambient loss, inversion removal by pool-adjacent-violators (energy-conserving), capsules assigned to nodes by layer height
around the stack anchor, per-node through-flow for the Wakao-Kaguei coefficient. Kernel is numba-compiled; a year takes 1.4-3.1 s
at N = 10. Tests: `tests/test_multinode_tank.py` (N = 1 reproduces the single-node tank; energy closure below 1e-6 %; CFD draw case).

Reproduction of the existing OpenFOAM draw case (30 L at 55 C over 20 L at 25 C, 50 L tank): litres at or above 45 C = 19.8 / 22.5 /
25.2 / 26.1 for N = 5 / 10 / 20 / 40, a fully mixed node gives 0, the CFD gives 27 (`results/g4_cfd_draw_case.csv`).
This is agreement with another model, not validation. **The annual result is not converged in N**: N = 10 to 20 adds 0.7-1.0 % to useful
energy and 0.15-0.25 percentage points to the paired PCM gain; this is inside the repeatability band, not removed (section 05).

## 3b. Solver safeguards and the overheat shield (both tank models)

Carried over from the original simulator and still in the code (`src/simulation/tank_model.py` and the numba kernel in `src/simulation/tank_model_multinode.py`):

| Mechanism | What it does | Why it exists |
|---|---|---|
| Differential-controller re-solve | each sub-step is solved with the collector circulating; if that solve implies reverse collector flow (`a - b T < 0`) it is re-solved with the collector off | the first Gate 1 run had a 1.6 % energy residual because the solve used the negative collector term while the log clipped it to zero; the re-solve brought it to about 2e-5 % |
| Adaptive stiffness sub-stepping | sub-step length is forced below 0.5 x the PCM time constant m cp_min / UA (at most 60 sub-steps); a `T_pcm` clip to [-50, 500] C is counted in `n_clipped_steps` | the PCM node lags the water node by one sub-step; with a very high conductivity (Gate 2, k x 200) the old rule diverged to about 1e300 C |
| Water-side bypass | collector circulation stops while the (top-node) water is at or above `bypass_water_C` = 72 C (3 C below the 75 C limit) | IS 12976:2023 §8.2: "stop circulation in the collector loop until the storage temperature decreases" |
| PCM-side charge block | capsule UA is set to zero while the PCM is at or above `bypass_pcm_C` = 62 C **and** the water is hotter than the PCM; discharging is never blocked | keeps the PCM under its 65 C material limit; these are the PCM-side shield hours in `d_overheat` |

Values from `configs/system_config_shared.yaml` (`safety_shield`, `safety`).

## 4. Metrics (`src/metrics/tes_metrics.py`)

| Metric | Definition (in short) |
|---|---|
| E_stored | energy above mains temperature held by water and PCM |
| E_rec,45 | energy recoverable above 45 C; PCM latent heat counts only when the melt temperature is above 45 C |
| tau_hold,45 / tau_serve | tau_hold,45: hours from 18:00 local that the tank alone (no draw, no sun, real ambient) keeps the outlet at or above 45 C, censored at 72 h. tau_serve: with the project demand profile and no sun, hours from 18:00 until the end-of-hour outlet first drops below 45 C (at most 15); serve_frac_45 is the share of the drawn volume that was at or above 45 C |
| E_del,45 | sum of m_dot cp (min(T_out, 45 C) - T_mains) over the draws: energy delivered up to the 45 C target, annual and in the **18:00-09:00 window** (`g_window` in the results is the PCM tank minus the water-only tank) |
| peak temperatures, latent utilisation, cycles per day | from the hourly record |
| closure residual | annual energy balance, a criterion below 0.1 % (largest observed 0.0698 %) |
| solar fraction | 1 - E_unmet / E_demand_ideal, where E_demand_ideal heats the full 300 L/day draw from mains to 45 C (`src/simulation/run_case.py`). With no backup heater this is stricter than an installed system's figure; cross-tool solar-fraction comparisons can differ by up to 16 percentage points from definitions alone ([N'tsoukpoe 2026](https://consensus.app/papers/details/45814dd6d8315185abddf6a269d479d8/), found by web search, not yet extracted to the project's sources folder), so the Gate 4 band comparison (section 05) is indicative only |

Hand-calculated synthetic-day checks are in `tests/test_tes_metrics.py`. Night scenarios restart from the design's own 18:00 state.

## 5. Same-flow paired baseline

`src/optimize/baseline.py` builds, per regime and year role (explore, select only), a water-only tank result on a 17-flow grid
(`plain_baseline_{explore,select}_r{0,1,2}.csv`) and interpolates it (PCHIP, error against exact plain runs below 0.01 %).
`src/optimize/evaluate.py: evaluate_design` returns the paired objectives for one design over the years of a role:

- `g_window`, `g_annual`: E_del,45 of the PCM tank minus the water-only tank at the same flow (kWh/yr)
- `d_overheat` (f3, unchanged): shield hours (water + PCM side) of the PCM tank minus the water-only tank's water-side hours. The two parts are not comparable (the water-only tank has no PCM-side throttle), so since 2026-10-27 they are also reported separately (`d_shield_water_h`, `shield_pcm_h`; `results/g13_shield_split_r*.csv`, section 1b of `04_RESULTS.md`).
- `t_pcm_max`, `t_water_max`, `pcm_mass_kg`, `feasible` (PCM peak at most 65 C in every year, water at most 75 C)

The held-out years use exact plain runs instead of the grid (`evaluate_night` in the same file).

## 6. What is not modelled

No supercooling, no volume change on melting, no backup heater, no pump energy, a flow-independent collector F_R, a single lumped
PCM resistance r/(5k) with the project's liquid-convection factor (no CFD-derived correction is applied).

Further simplifications to state in the report:

- Melting is a narrow band Tm +/- 1 K (`melting_half_width_K`), because the PCM database gives one Tm, not a solidus/liquidus pair.
- Natural convection in the liquid PCM is not resolved: conductivity is multiplied by 2.0 (`liquid_convection_enhancement`) once
  the melt fraction reaches 0.5. This factor is assumed, not measured.
- Hourly weather is held constant over the sub-steps of each hour, and each hour's draw is spread evenly across it (both inputs are hourly).
- Hydraulics cover only the packed capsule bed (Ergun 1952); pipe and valve losses are out of scope.
- All capsules in a node are identical and see that node's water temperature.
- No backup heater. IS 12976:2023 §5 says auxiliary heating is not required in hot or tropical regions but is needed in cold,
  low-radiation ones, so this holds for Rajasthan but should be revisited for Uttarakhand.
