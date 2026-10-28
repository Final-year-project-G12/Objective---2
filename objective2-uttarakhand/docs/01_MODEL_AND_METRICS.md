# 01 - Simulator, repairs and metrics (as implemented)

The simulator code is the Rajasthan current-chain code (`objective2-rajasthan`, v3), ported unchanged except for the state name
(2026-10-28, `docs/PROGRESS.md` section 2). Evidence for every statement is in `docs/PROGRESS.md` (section numbers in brackets) and the tests named below.

## 1. Entry point

`src/simulation/run_case.py: run_case(state, cluster_id, pcm_name, design, ...)` builds the case and runs one weather year.
`pcm_name=None` gives the water-only tank with the same design vector. Useful options:

| Option | Meaning |
|---|---|
| `tank_model="single"` (default) / `"multinode"` | single mixed node (`src/simulation/tank_model.py`, kept as the regression reference) or the stratified tank (`src/simulation/tank_model_multinode.py`) |
| `n_nodes=10`, `stack_anchor="center"` | multi-node settings (the approved design space fixes both, `configs/design_space.yaml`) |
| `weather=<DataFrame>` | run a given point-year (see `02`) instead of the regime file |
| `compute_tes_metrics=True`, `night_day_stride=k` | add the WP1 metrics and night scenarios every k-th day (`0` skips the scenarios) |
| `initial_state`, `stop_when_Tw_below_C` | used by the night scenarios |

The production time step is **150 s** (`solver.timestep_s` in `configs/system_config_shared.yaml`; Rajasthan showed that 300 s fails the convergence check). For Uttarakhand, 150 s
passes the convergence criterion: the largest change on any halving (150 to 75 to 37.5 s) is 0.029 % and the largest closure residual 0.076 %
(`results/g2_timestep_convergence_150_75_37p5.csv`, [3]).

## 2. Repairs to the model (Level 1)

| Repair | Where |
|---|---|
| Demand follows **local** time (`local_hour`, the floor of IST) instead of UTC hour. the regime weather files carry `local_hour` / `local_date`; a frame with only `timestamp_utc` is refused | `src/simulation/tank_model.py: _demand_hour_of_day` |
| PCM mass from the **inner** sphere (D - 2 t_wall); wall heat capacity carried in the PCM node | `src/simulation/capsule_mass.py`, `src/simulation/capsule_enthalpy.py` |
| PCM conduction path uses the inner radius and inner area | `src/simulation/heat_transfer.py` |
| 29 February dropped, every year 8760 h | `io_utils.drop_leap_day`, `load_hourly_weather(drop_29_feb=True)` |
| Pump energy flagged `pump_energy_meaningful=False` | `src/simulation/run_case.py` |

The Uttarakhand demand profile has its morning peak at 07:30 local time (`tests/test_demand_timing.py` checks hours 7 and 8).

## 3. Multi-node tank

N equal nodes (default 10), plug-flow draw from the mains at the bottom, outlet at the top node; the collector loop takes water from the
bottom node and returns it at the node of equal temperature, so **flow sets the loop temperature rise and the inlet level, not the collector heat**.
A year takes 0.7-0.9 s at N = 10 and 1.5-2.4 s at N = 20 on the development machine (`results/g4_multinode_report.csv`). Tests: `tests/test_multinode_tank.py`.

Project OpenFOAM draw case (30 L at 55 C over 20 L at 25 C, 50 L tank; litres at or above 45 C): 19.8 / 22.5 / 25.2 / 26.1 for N = 5 / 10 / 20 / 40,
a fully mixed node gives 0, the CFD gives 27 (`results/g4_cfd_draw_case.csv`). The case counts litres at 45 C, so it is run with a 45 C delivery override.
**The annual result is not converged in N**: N = 10 to 20 adds 0.83-0.99 % to the useful energy, on the plain and the PCM tank alike; this is part of the
repeatability band, not removed.

## 4. Metrics (`src/metrics/tes_metrics.py`) and the Uttarakhand delivery target

The code computes the WP1 metrics at the delivery target `delivery.target_temp_C` in `configs/system_config_shared.yaml`. Rajasthan uses 45 C.
**Uttarakhand keeps its own target of 50 C**, so every metric below with the suffix 45 (the name kept from the code: `E_del45`, `tau_hold`,
`serve_frac_45`) is computed at **50 C** for this state. The column names were not renamed, so the files match Rajasthan's.

| Metric | Definition (in short) |
|---|---|
| E_rec,45 | energy recoverable above the target; PCM latent heat counts only when the melt temperature is above it |
| tau_hold / tau_serve | tau_hold: hours from 18:00 local that the tank alone keeps the outlet at or above the target (censored at 72 h). tau_serve: with the project demand and no sun, hours from 18:00 until the outlet first drops below the target (at most 15); serve_frac_45 is the share of the drawn volume at or above it |
| E_del,45 | sum of m_dot cp (min(T_out, target) - T_mains) over the draws, annual and in the **18:00-09:00 window** (`g_window` is the PCM tank minus the water-only tank) |
| closure residual | annual energy balance, criterion below 0.1 % |

With a 50 C target, tau_hold and tau_serve are close to zero for both tanks in regimes 1-3 at the mid design (`results/g3_metrics_report.csv`, [4]).

## 5. Same-flow paired baseline

`src/optimize/baseline.py` builds, per regime and year role (explore, select), a water-only tank result on a 17-flow grid
(`plain_baseline_{explore,select}_r{0,1,2,3}.csv`) and interpolates it. `src/optimize/evaluate.py: evaluate_design` returns:

- `g_window`, `g_annual`: E_del of the PCM tank minus the water-only tank at the same flow (kWh/yr)
- `d_overheat` (f3): shield hours (water + PCM side) of the PCM tank minus the water-only tank's water-side hours; the two parts are also
  reported separately (`results/g13_shield_split_r*.csv`)
- `t_pcm_max`, `t_water_max`, `pcm_mass_kg`, `feasible` (PCM peak at most 65 C in every year, water at most 75 C)

The held-out years use exact plain runs instead of the grid.

## 6. What is not modelled

No supercooling, no volume change on melting, no backup heater, no pump energy, a flow-independent collector F_R, a single lumped PCM
resistance; no CFD-derived resistance correction is applied.
