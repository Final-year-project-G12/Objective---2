"""ansys/criteria_common/make_how_they_change.py -> ansys/HOW_THEY_CHANGE.md (numbers from the Fluent CSVs + node model)."""
import json
from pathlib import Path
import pandas as pd

A = Path(__file__).resolve().parents[1]
L = ["# How the criteria change - ANSYS Fluent whole-tank discharge + node model", "",
     "Capsules start melted at 70 C, tank water at 30 C, no sun, sealed tank. Fluent shows the SHAPE and TIME behaviour on a 2-D slice "
     "(drawn capsules = round(N*34/104), radius = 0.5 R_in); energy per year comes from the node model.", "",
     "![comparison](criteria_common/FLUENT_comparison_all_criteria.png)", "",
     "![summary](criteria_common/SUMMARY_all_criteria.png)", "",
     "Interactive version: `criteria_common/CRITERIA_interactive.html`.", ""]
rows = []
for f in sorted(A.glob("criteria_[0-9]_*")):
    c = json.loads((f / "criteria.json").read_text()); n = json.loads((f / "node_model_results.json").read_text())
    ts = list(f.glob("*_discharge_timeseries.csv"))
    L += [f"## {c['title']}", "",
          f"{c['rule']}", "",
          f"Real design: R_in {c['design']['R_in']*1000:.0f} mm, **{c['n_3d']} capsules** ({n['pcm_mass_kg']:.1f} kg PCM), flow {c['design']['flow']:.4f} kg/s, "
          f"{c['design']['arrangement']}. Drawn in Fluent: {c['proxy']['drawn_capsules']} capsules.", "",
          f"Node model: g_window **{n['g_window_kWh_yr']:.1f} kWh/yr ({n['pct_of_optimal_gain']:.0f} % of optimal)**, overheating {n['d_overheat_h_yr']:.0f} h/yr. "
          f"Verdict: {n['verdict']}.", ""]
    if ts:
        d = pd.read_csv(ts[0]); end = d.iloc[-1]
        L += ["| minute | water avg C | water max C | capsule avg C | liquid fraction | heat to water kJ/m |", "|---|---|---|---|---|---|"]
        for m in sorted(set([0, 15, 30, 45, d.minute.max()])):
            r = d.iloc[(d.minute - m).abs().argmin()]
            L.append(f"| {r.minute:.0f} | {r.water_avg_C:.2f} | {r.water_max_C:.2f} | {r.pcm_avg_C:.2f} | {r.liquid_fraction:.3f} | {r.heat_to_water_kJ_per_m:.0f} |")
        L.append("")
        rows.append((c["title"], c["proxy"]["drawn_capsules"], end.water_avg_C - d.water_avg_C.iloc[0], end.liquid_fraction, end.heat_to_water_kJ_per_m))
        for k in ("temp_START", "temp_END", "liqfrac_END"):
            p = list((f / "figures").glob(f"*_{k}.png"))
            if p:
                L.append(f"![{k}]({f.name}/figures/{p[0].name})")
        L.append("")
if rows:
    base = rows[0]
    L += ["## What changes between criteria (Fluent, end of run)", "", "| criteria | drawn capsules | water rise K | liquid fraction left | heat to water kJ/m | vs optimal |", "|---|---|---|---|---|---|"]
    for t, k, dt, lf, q in rows:
        L.append(f"| {t} | {k} | {dt:.2f} | {lf:.3f} | {q:.0f} | {100*q/base[4]:.0f} % |")
    L += ["", "Reading: more drawn capsules = more PCM area releasing latent heat = larger water temperature rise, and the optimum (34 drawn) "
          "releases the most; few capsules release little heat and finish solidifying sooner. Max-all has the same slice as the optimum "
          "(only flow differs, which acts in the node model)."]
(A / "HOW_THEY_CHANGE.md").write_text("\n".join(L), encoding="utf-8"); print("written")
