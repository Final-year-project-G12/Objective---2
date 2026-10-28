# Objective 2 — Rajasthan

Design optimisation of the PCM storage unit (capsule inner radius, PCM amount via capsule count, flow rate, arrangement) for
Rajasthan's three Objective 1 climate regimes, on a grey-box simulator.

**All documentation is in [`docs/README.md`](docs/README.md)**: model and metrics, weather and design space, the optimisation
pipeline, results, limitations, and the Objective 3 hand-off. `docs/PROGRESS.md` is the step-by-step log with the evidence for every gate.

Current version: v3 (PCM fraction cap 30 %), designs selected on 2021-2023 and tested once on the untouched years 2011-2015.

## Layout

```
objective2-rajasthan/
├── pipeline.py               # entry point for the current chain (stages: status, verify ... plots; see its docstring)
├── run_all_rajasthan.py      # tests + report + handoff + plots from saved results; --full runs the whole chain (hours)
├── config.py                 # shared paths
├── configs/
│   ├── system_config_shared.yaml   # shared system config (tank, collector, safety limits, solver step 150 s)
│   ├── design_space.yaml           # the approved design space (radius, PCM fraction, flow, arrangement) + geometry-engine bounds
│   └── states/rajasthan.yaml       # regimes, weather paths, mains temperature, O1 PCM top-3
├── src/
│   ├── simulation/           # single-node and multi-node tank, capsule enthalpy, collector, heat transfer, run_case
│   ├── metrics/              # thermal-storage metrics (E_del,45, tau_serve, ...)
│   ├── weather/              # point-year inventory, year roles, held-out lock
│   ├── design/               # design space, geometry engine, constraints
│   ├── optimize/             # paired baseline, evaluation, ANOVA, surrogates, NSGA-II
│   ├── handoff/              # Objective 3 environment contract v2
│   ├── plots/                # make_plots_results.py (figures 1-9)
│   └── verify/               # Phase-4 verification battery (gates.py)
├── scripts/g*.py             # one script per gate step (G2-G19)
├── tests/                    # python -m pytest tests
├── data/                     # objective1/ inputs, weather/point_years/, demand/, legacy/ (tables read by g2-g4)
├── results/                  # all outputs; results_registry.csv lists every headline number with its source
└── docs/                     # documentation (start at docs/README.md)
```

## Quick start (from this folder)

```
python -m pytest tests
python pipeline.py --state rajasthan --stage status
python run_all_rajasthan.py
```

Stages that would re-decide the frozen designs refuse while `results/held_out_test.lock` exists; see `docs/README.md`.
