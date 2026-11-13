"""ansys/criteria_common/make_readmes.py - writes README.md in every criteria folder + ansys/CRITERIA_STUDY_README.md
from criteria.json + node_model_results.json (+ Fluent time series when present). Nothing typed by hand."""
import json
from pathlib import Path

import pandas as pd

ANSYS = Path(__file__).resolve().parents[1]
rows = []
for f in sorted(ANSYS.glob("criteria_[0-9]_*")):
    c = json.loads((f / "criteria.json").read_text())
    n = json.loads((f / "node_model_results.json").read_text()) if (f / "node_model_results.json").exists() else {}
    d = c["design"]
    L = [f"# {c['title']}", "",
         f"**Rule:** {c['rule']}", "",
         "## Parameters", "",
         "| parameter | this criteria | optimal |", "|---|---|---|",
         f"| capsule inner radius | {d['R_in']*1000:.1f} mm | 40.0 mm |",
         f"| capsules (real, 3-D) | {c['n_3d']} ({c['frac_of_optimal_N']*100:.0f} % of optimal) | 104 |",
         f"| PCM volume fraction | {c['fraction_pct']:.1f} % | 29.6 % |",
         f"| flow | {d['flow']:.4f} kg/s | 0.0388 kg/s |",
         f"| arrangement | {d['arrangement']} | staggered |",
         f"| PCM | {c['pcm']} (Regime {c['regime']}) | PureTemp 58 |",
         f"| **drawn in Fluent (2-D proxy)** | **{c['proxy']['drawn_capsules']} capsules, inner R {c['proxy']['r_in_2d_m']*1000:.1f} mm** | 34, 20 mm |", ""]
    if n.get("valid"):
        dl = n["delta_vs_optimal"]
        L += ["## Result of the optimiser's own simulator (select years 2021-23, vs plain water tank)", "",
              "| metric | this criteria | optimal | difference |", "|---|---|---|---|",
              f"| PCM mass | {n['pcm_mass_kg']:.1f} kg | {n['pcm_mass_kg']-dl['pcm_mass_kg']:.1f} kg | {dl['pcm_mass_kg']:+.1f} |",
              f"| **g_window** (extra evening heat) | **{n['g_window_kWh_yr']:.1f} kWh/yr** | {n['g_window_kWh_yr']-dl['g_window']:.1f} | {dl['g_window']:+.1f}  ({n['pct_of_optimal_gain']:.0f} % of optimal) |",
              f"| g_annual | {n['g_annual_kWh_yr']:.1f} kWh/yr | {n['g_annual_kWh_yr']-dl['g_annual']:.1f} | {dl['g_annual']:+.1f} |",
              f"| d_overheat (lower better) | {n['d_overheat_h_yr']:.0f} h/yr | {n['d_overheat_h_yr']-dl['d_overheat']:.0f} | {dl['d_overheat']:+.0f} |",
              f"| peak PCM T | {n['t_pcm_max_C']:.2f} C (limit 65) | | {'PASS' if n['gate_pcm_le_65'] else 'FAIL'} |",
              f"| peak water T | {n['t_water_max_C']:.2f} C (limit 75) | | {'PASS' if n['gate_water_le_75'] else 'FAIL'} |", "",
              "## How the final design is selected - and where this one stops", "",
              f"* Rule A (gain > {n['bands']['g_window_band']:.1f} kWh noise band): **{'pass' if n['rule_A_beats_plain_beyond_band'] else 'FAIL'}**",
              f"* S0 (within the band of the best g_window {n['bands']['g_best_pool']:.1f}): **{'in' if n['in_S0_tied_with_best'] else 'OUT'}**",
              f"* S1 (low overheating, only for S0 members): **{'in' if n['in_S1_low_overheat'] else ('out' if n['in_S0_tied_with_best'] else 'n/a')}**",
              f"* **Verdict:** {n['verdict']}", "",
              f"**Why it is not optimal:** {c['why_not_optimal']}", ""]
    L += ["## Files", "",
          "| file | what |", "|---|---|",
          "| `criteria.json` | design, 2-D proxy, run settings |",
          "| `fluent_tank_discharge_criteria.py` | copy of `../fluent_tank_discharge.py` driven by this criteria (builds its own mesh, runs Fluent, prints the time table, saves pictures) |",
          "| `make_system_mesh.py` | mesh builder with an exact `n_capsules` argument |",
          "| `run_node_model.py`, `scenarios.py` | the objective-value side (gates, funnel verdict, one-day time behaviour) |",
          "| `node_model_terminal.txt`, `node_model_results.json`, `node_model_day.csv/.png` | its output |",
          "| `fluent_terminal.log`, `*_discharge_timeseries.csv`, `figures/*.png` | Fluent output (after `python fluent_tank_discharge_criteria.py`) |", ""]
    ts = list(f.glob("*_discharge_timeseries.csv"))
    if ts:
        t = pd.read_csv(ts[0])
        L += ["## Fluent whole-tank discharge (this run)", "",
              f"water {t.water_avg_C.iloc[0]:.2f} -> {t.water_avg_C.iloc[-1]:.2f} C; capsules {t.pcm_avg_C.iloc[0]:.2f} -> {t.pcm_avg_C.iloc[-1]:.2f} C; "
              f"liquid fraction {t.liquid_fraction.iloc[0]:.2f} -> {t.liquid_fraction.iloc[-1]:.2f}; "
              f"heat given to the water {t.heat_to_water_kJ_per_m.iloc[-1]:.0f} kJ per metre of depth.", ""]
        for img in sorted((f / 'figures').glob("*.png")):
            L.append(f"![{img.name}](figures/{img.name})")
    (f / "README.md").write_text("\n".join(L), encoding="utf-8")
    rows.append((c, n))

M = ["# Criteria study - what happens if the design is not the optimum?", "",
     "Regime 0, PureTemp 58, 100 L tank. Every row is a real run of the optimiser's simulator "
     "(multi-node tank, select years 2021-23) paired with the plain-water tank; the Fluent folders show the "
     "same designs as a whole-tank discharge (capsules melted at 70 C, water 30 C, no sun).", "",
     "**2-D proxy:** the planar Fluent slice draws `round(N*34/104)` capsules of inner radius `0.5*R_in` - the optimum is the "
     "existing 34-capsule / 20 mm picture. Flow rate and arrangement act in the node model only (the discharge has no flow).", "",
     "| folder | R_in | N real (drawn) | PCM kg | flow | arrangement | g_window kWh/yr | % of optimal | verdict |", "|---|---|---|---|---|---|---|---|---|"]
for c, n in rows:
    d = c["design"]
    M.append(f"| [{c['key']}]({c['key']}/README.md) | {d['R_in']*1000:.0f} mm | {c['n_3d']} ({c['proxy']['drawn_capsules']}) | "
             f"{n.get('pcm_mass_kg', float('nan')):.1f} | {d['flow']:.3f} | {d['arrangement']} | "
             f"{n.get('g_window_kWh_yr', float('nan')):.1f} | {n.get('pct_of_optimal_gain', float('nan')):.0f} % | {n.get('verdict','')} |")
M += ["", "![summary](criteria_common/SUMMARY_all_criteria.png)", "",
      "Data flow of the whole objective: `../docs/OBJ2_DATA_FLOW_INPUT_TO_OUTPUT.md`."]
(ANSYS / "CRITERIA_STUDY_README.md").write_text("\n".join(M), encoding="utf-8")
print("readmes written")
