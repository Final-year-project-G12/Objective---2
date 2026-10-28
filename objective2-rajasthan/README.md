# Objective 2 — Rajasthan

Design optimisation of the PCM storage unit (capsule inner radius, PCM amount via capsule count, flow rate, arrangement) for
Rajasthan's three Objective 1 climate regimes, on a grey-box simulator.

**All documentation is in [`docs/README.md`](docs/README.md)**: model and metrics, weather and design space, the optimisation
pipeline, results, limitations, and the Objective 3 hand-off. `docs/PROGRESS.md` is the step-by-step log with the evidence for every gate.

Current version: v3 (PCM fraction cap 30 %), designs selected on 2021-2023 and tested once on the untouched years 2011-2015.
The documents of the legacy pipeline (phases 0-8, `sim_v1/v2_rajasthan`, `results/phase*`) were deleted on 2026-10-28 and are in
git history; what still applies from them is in `docs/01`, `docs/02` and `docs/05`.

## Layout

```
objective2-rajasthan/
├── pipeline.py               # entry point for the current chain (stages: status, verify ... plots; see its docstring)
├── run_all_rajasthan.py      # tests + report + handoff + plots from saved results; --full runs the whole chain (hours)
├── config.py                 # shared paths
├── configs/
│   ├── system_config_shared.yaml   # frozen, shared by all four states (tank, collector, demand, safety limits)
│   ├── design_space.yaml           # the approved design space (radius, PCM fraction, flow, arrangement)
│   ├── design_bounds_shared.yaml   # legacy bounds; only used through src/design/space.geometry_bounds()
│   ├── cfd_closure_v1.yaml         # provisional, not applied in the simulator
│   └── states/rajasthan.yaml
├── src/
│   ├── simulation/           # single-node and multi-node tank, capsule enthalpy, collector, heat transfer, run_case
│   ├── metrics/              # thermal-storage metrics (E_del,45, tau_serve, ...)
│   ├── weather/              # point-year inventory, year roles, held-out lock
│   ├── design/               # design space, geometry engine, constraints
│   ├── optimize/             # paired baseline, evaluation, ANOVA, surrogates, NSGA-II
│   ├── handoff/              # Objective 3 contract (build_obj3_contract_v2.py is current)
│   ├── plots/                # make_plots_results.py and make_plots_phases.py are current
│   └── doe/ surrogate/ robustness/ verify/   # legacy chain modules, not called by the entry points
├── scripts/g*.py             # one script per gate step (G2-G19)
├── tests/                    # python -m pytest tests
├── data/                     # objective1/ inputs, weather/point_years/, demand/, pcm/, legacy/ (one table kept for g2-g4)
├── results/                  # all outputs; results_registry.csv lists every headline number with its source
└── docs/                     # documentation (start at docs/README.md)
```

The root `check_*.py` scripts and `build_regime_weather.py` are one-off checks from the legacy pipeline
(see `docs/CLEANUP_PROPOSAL.md`); the entry points do not call them.

## Quick start (Python 3.10, from this folder)

```
python -m pytest tests
python pipeline.py --state rajasthan --stage status
python run_all_rajasthan.py
```

Stages that would re-decide the frozen designs refuse while `results/held_out_test.lock` exists; see `docs/README.md`.
