# Run the criteria LIVE in ANSYS Fluent (your terminal)

Rules: **close any other Fluent window first** (Student licence = 1 session). Run ONE case at a time.
If launch says "Unexpected license problem": `Get-Process fluent,ansyscl,cx* | Stop-Process -Force` (PowerShell) and retry.
Each case opens the Fluent window and re-draws the temperature contour every simulated minute, prints the
time table in the terminal, saves START/MID/END pictures + a CSV, then waits for Enter before closing.
Add `--hours 0.5` for a quicker look (default 2 h).

```bash
cd ansys/criteria_0_optimal_reference     && python fluent_tank_discharge_criteria.py --live
cd ansys/criteria_1_max_all               && python fluent_tank_discharge_criteria.py --live
cd ansys/criteria_2_min_all               && python fluent_tank_discharge_criteria.py --live
cd ansys/criteria_3_ok_not_optimal        && python fluent_tank_discharge_criteria.py --live
cd ansys/criteria_4_only_30_capsules      && python fluent_tank_discharge_criteria.py --live
cd ansys/criteria_5_10pct_of_optimal      && python fluent_tank_discharge_criteria.py --live
cd ansys/criteria_6_50pct_of_optimal      && python fluent_tank_discharge_criteria.py --live
```
(paths relative to `objective2_design_optimization/`; use `cd ..` between cases)

Headless, all seven in a row (no window, ~20 min each): `python ansys/criteria_common/run_all_fluent.py`
After any runs: `python ansys/criteria_common/plot_comparison.py` and `python ansys/criteria_common/build_plotly.py`
(the interactive page then also shows the Fluent curves), `python ansys/criteria_common/make_readmes.py`.

Interactive page: open `ansys/criteria_common/CRITERIA_interactive.html` in a browser.
