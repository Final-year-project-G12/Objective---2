"""ansys/criteria_common/build_plotly.py -> CRITERIA_interactive.html
Interactive Plotly page: how the 7 criteria differ and how the optimum is selected.
Reads result files only (results/*.csv, criteria_*/node_model_*, Fluent time series when present).
Run: python ansys/criteria_common/build_plotly.py
"""
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parents[2]
ANS = ROOT / "ansys"
res = ROOT / "results"
sel = json.loads((res / "g10_selection_r0.json").read_text())
band, band_d = sel["band"]["g_window"], sel["band"]["d_overheat"]
pool = pd.read_csv(res / "g10_selection_candidates_r0.csv")
doe = pd.read_csv(res / "g8_s2_r0_p3.csv")
doe = doe[(doe.valid == True) & (doe.feasible == True)]                          # noqa: E712
S = []
for f in sorted(ANS.glob("criteria_[0-9]_*")):
    c = json.loads((f / "criteria.json").read_text())
    n = json.loads((f / "node_model_results.json").read_text())
    S.append((f, c, n))
COL = ["#2ca02c", "#1f77b4", "#d62728", "#ff7f0e", "#9467bd", "#8c564b", "#e377c2"]


def short(c):
    return c["title"].split(". ", 1)[1]


def hov(c, n):
    return (f"<b>{c['title']}</b><br>R_in {c['design']['R_in']*1000:.0f} mm, N {n['N']}, PCM {n['pcm_mass_kg']:.1f} kg<br>"
            f"flow {c['design']['flow']:.4f}, {c['design']['arrangement']}<br>g_window {n['g_window_kWh_yr']:.1f} kWh/yr "
            f"({n['pct_of_optimal_gain']:.0f} % of optimal)<br>{n['verdict']}")


g_best = pool.g_window.max()
s0 = pool[pool.g_window >= g_best - band]
d_floor = s0.d_overheat.min()
s1 = s0[s0.d_overheat <= d_floor + band_d]
figs = []

# 1 -- the search space: every simulated design, with the 7 criteria on top
f1 = go.Figure()
f1.add_trace(go.Scatter(
    x=doe.pcm_mass_kg, y=doe.g_window, mode="markers", name="128 Sobol DOE designs (explore years)",
    marker=dict(size=6, color=doe.flow, colorscale="Viridis", colorbar=dict(title="flow kg/s"), opacity=.7),
    text=[f"R {r*1000:.0f} mm, N {nn}, flow {fl:.3f}, {a}" for r, nn, fl, a in zip(doe.R_in_m, doe.N, doe.flow, doe.arrangement)],
    hovertemplate="%{text}<br>PCM %{x:.1f} kg<br>g_window %{y:.0f}<extra>DOE</extra>"))
f1.add_trace(go.Scatter(
    x=pool.pcm_mass_kg, y=pool.g_window, mode="markers", name="90 optimiser candidates (select years)",
    marker=dict(size=8, symbol="diamond-open", color="black"),
    text=[f"{p}: R {r*1000:.0f} mm, N {nn}, flow {fl:.3f}" for p, r, nn, fl in zip(pool.pcm, pool.R_in_m, pool.N, pool.flow)],
    hovertemplate="%{text}<br>g_window %{y:.0f}<extra>candidate</extra>"))
for (f, c, n), col in zip(S, COL):
    f1.add_trace(go.Scatter(
        x=[n["pcm_mass_kg"]], y=[n["g_window_kWh_yr"]], mode="markers+text", text=[c["title"].split(".")[0]],
        textposition="top center", name=c["title"],
        marker=dict(size=18, symbol="star", color=col, line=dict(width=1.5, color="black")),
        hovertext=hov(c, n), hoverinfo="text"))
f1.add_hline(y=band, line_dash="dash", line_color="red", annotation_text=f"Rule A: noise band {band:.1f} kWh")
f1.add_hline(y=g_best - band, line_dash="dash", line_color="orange", annotation_text=f"S0 threshold {g_best-band:.0f}")
f1.update_layout(title="1. Where each criteria sits in the design space (more PCM = more gain, until the 30 % cap)",
                 xaxis_title="PCM mass [kg]", yaxis_title="g_window: extra 18:00-09:00 heat vs plain tank [kWh/yr]", height=600)
figs.append(f1)

# 2 -- selection funnel
steps = [("simulated candidates", len(pool)), ("feasible (PCM<=65, water<=75)", int(pool.feasible_select.sum())),
         (f"Rule A: gain > {band:.1f}", int((pool.g_window > band).sum())), (f"S0: within {band:.1f} of best", len(s0)),
         (f"S1: overheating within {band_d:.0f} h", len(s1)), ("S2: serve-time band", sel["n_S2"]),
         ("final pick (lowest mass, fewest N)", 1)]
f2 = go.Figure(go.Funnel(y=[s[0] for s in steps], x=[s[1] for s in steps], textinfo="value+percent initial",
                         marker=dict(color="#2ca02c")))
f2.update_layout(title=f"2. How the optimum is selected (regime 0, three PCMs) -> {sel['chosen']['pcm']}, N={sel['chosen']['N']}",
                 height=480)
figs.append(f2)

# 3 -- compare parameters / objectives
labs = [short(c) for _, c, _ in S]
f3 = make_subplots(rows=2, cols=3, vertical_spacing=.25,
                   subplot_titles=("g_window kWh/yr (higher better)", "PCM mass kg", "d_overheat h/yr (lower better)",
                                   "capsules N (real)", "flow kg/s", "peak PCM temp C (limit 65)"))
vals = [[n["g_window_kWh_yr"] for _, _, n in S], [n["pcm_mass_kg"] for _, _, n in S], [n["d_overheat_h_yr"] for _, _, n in S],
        [n["N"] for _, _, n in S], [c["design"]["flow"] for _, c, _ in S], [n["t_pcm_max_C"] for _, _, n in S]]
for i, v in enumerate(vals):
    f3.add_trace(go.Bar(x=labs, y=v, marker_color=COL, showlegend=False, text=[f"{x:.3g}" for x in v], textposition="outside"),
                 row=i // 3 + 1, col=i % 3 + 1)
f3.update_layout(title="3. How the parameters and objectives differ between criteria", height=720)
figs.append(f3)

# 4 -- one sunny day
f4 = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=.06,
                   subplot_titles=("outlet (top) water temperature [C]", "PCM temperature [C]", "PCM melt fraction"))
xlab = []
for i, ((f, c, n), col) in enumerate(zip(S, COL)):
    d = pd.read_csv(f / "node_model_day.csv")
    x = list(range(len(d)))
    xlab = [f"{h:02d}:00" for h in d.hour_of_day]
    f4.add_trace(go.Scatter(x=x, y=d.T_out_design_C, name=short(c), legendgroup=c["key"],
                            line=dict(color=col, width=3 if i == 0 else 2)), 1, 1)
    f4.add_trace(go.Scatter(x=x, y=d.T_pcm_C, name=short(c), legendgroup=c["key"], showlegend=False, line=dict(color=col)), 2, 1)
    f4.add_trace(go.Scatter(x=x, y=d.f_melt, name=short(c), legendgroup=c["key"], showlegend=False, line=dict(color=col)), 3, 1)
d0 = pd.read_csv(S[0][0] / "node_model_day.csv")
f4.add_trace(go.Scatter(x=list(range(len(d0))), y=d0.T_out_plain_C, name="plain water tank (optimal's flow)",
                        line=dict(color="black", dash="dash")), 1, 1)
f4.add_hline(y=45, line_dash="dot", row=1, col=1, annotation_text="45 C target")
f4.add_hline(y=58, line_dash="dot", row=2, col=1, annotation_text="PureTemp 58 Tm")
f4.update_xaxes(tickvals=list(range(0, len(xlab), 3)), ticktext=xlab[::3], row=3, col=1)
f4.update_layout(title="4. One sunny day + night (click the legend to hide/show; 18:00-09:00 is the scored window)", height=850)
figs.append(f4)

# 5 -- Fluent whole-tank discharge (only criteria that have been run)
fl = [(f, c) for f, c, _ in S if list(f.glob("*_discharge_timeseries.csv"))]
if fl:
    f5 = make_subplots(rows=1, cols=3, subplot_titles=("tank water mean T [C]", "capsule mean T [C]", "PCM liquid fraction"))
    for f, c in fl:
        d = pd.read_csv(list(f.glob("*_discharge_timeseries.csv"))[0])
        col = COL[int(c["key"].split("_")[1])]
        for j, y in enumerate(("water_avg_C", "pcm_avg_C", "liquid_fraction")):
            f5.add_trace(go.Scatter(x=d.minute, y=d[y], name=f"{short(c)} ({c['proxy']['drawn_capsules']} drawn)",
                                    legendgroup=c["key"], showlegend=(j == 0), line=dict(color=col)), 1, j + 1)
    f5.update_xaxes(title_text="simulated minutes")
    f5.update_layout(title="5. ANSYS Fluent whole-tank discharge (criteria run so far)", height=480)
    figs.append(f5)

html = ["<html><head><meta charset='utf-8'><title>Objective 2 criteria study</title></head>"
        "<body style='font-family:sans-serif;max-width:1250px;margin:auto'>",
        "<h1>Objective 2 - what if the design is not the optimum?</h1><p>Regime 0, PureTemp 58, 100 L tank. "
        "Every point is a real simulator run; the optimiser's choice is the green star (criteria 0).</p>"]
for i, fg in enumerate(figs):
    html.append(fg.to_html(full_html=False, include_plotlyjs="cdn" if i == 0 else False))
html.append("</body></html>")
out = Path(__file__).with_name("CRITERIA_interactive.html")
out.write_text("\n".join(html), encoding="utf-8")
print(out, out.stat().st_size // 1024, "KB")
