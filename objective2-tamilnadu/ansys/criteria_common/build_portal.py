"""
ansys/criteria_common/build_portal.py -> ansys/CRITERIA_PORTAL.html

One interactive page, a dropdown (7 criteria + "All together"):
  - per criteria: parameters table, time-to-X timing, the Fluent video (GIF, built by build_gifs.py)
    with START/MID/FINAL stills beside it, and a bottom Plotly graph of water/PCM temperature +
    liquid fraction vs time.
  - "All together": every criteria's water/PCM/liquid-fraction curves overlaid, the design-space /
    funnel panels, and the optimal-vs-others comparison table.

Reads only result files (criteria_*/criteria.json, node_model_results.json, node_model_day.csv,
*_discharge_timeseries.csv, figures/*_video.gif, figures/*_START/MID/END.png). Missing videos/frames
degrade gracefully (falls back to the three stills). Run any time; re-run after a new Fluent batch,
build_gifs.py and build_plotly.py to refresh.

    python ansys/criteria_common/build_portal.py
"""
import base64
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.io import to_html

ROOT = Path(__file__).resolve().parents[2]
ANS = ROOT / "ansys"
res = ROOT / "results"
PCM_DB = ROOT / "data" / "objective1" / "pcm_database_tamilnadu.csv"
COL = ["#2ca02c", "#1f77b4", "#d62728", "#ff7f0e", "#9467bd", "#8c564b", "#e377c2"]
T_CAPSULE_HOT_C, T_WATER_COLD_C, BAND_K = 70.0, 30.0, 10.0   # same constants the Fluent script uses


def pcm_physical_props(name):
    db = pd.read_csv(PCM_DB)
    row = db[db.name.str.strip().str.lower() == name.strip().lower()]
    if row.empty:
        row = db[db.name.str.contains(name.strip(), case=False, regex=False)]
    r = row.iloc[0]
    return {
        "Tm_C": float(r.Tm_C), "latent_kJ_kg": float(r.latent_heat_kJ_kg), "k_W_mK": float(r.TC_W_mK),
        "density_avg": float((r.density_solid_kg_m3 + r.density_liquid_kg_m3) / 2),
        "cp_avg_kJ_kgK": float((r.Cp_solid_kJ_kgK + r.Cp_liquid_kJ_kgK) / 2),
    }


def b64(p: Path) -> str:
    return "data:image/" + ("gif" if p.suffix == ".gif" else "png") + ";base64," + base64.b64encode(p.read_bytes()).decode()


def short(c):
    return c["title"].split(". ", 1)[1]


def load_all():
    out = []
    for i, f in enumerate(sorted(ANS.glob("criteria_[0-9]_*"))):
        c = json.loads((f / "criteria.json").read_text())
        n = json.loads((f / "node_model_results.json").read_text())
        ts_files = list(f.glob("*_discharge_timeseries.csv"))
        ts = pd.read_csv(ts_files[0]) if ts_files else None
        out.append(dict(folder=f, c=c, n=n, ts=ts, color=COL[i]))
    return out


def timing_block(c, n, ts):
    """Time-to-X metrics, all measured, none typed."""
    rows = [("Fluent discharge run duration", f"{ts.minute.iloc[-1]:.0f} simulated minutes" if ts is not None else "not run yet")]
    if ts is not None:
        lf0 = ts.liquid_fraction.iloc[0]
        for thr, label in ((0.5, "half its stored latent heat gone"), (0.05, "fully solidified")):
            below = ts[ts.liquid_fraction <= thr]
            rows.append((f"time to {label} (liq. fraction <= {thr})",
                        f"{below.minute.iloc[0]:.0f} min" if len(below) else f"not reached within {ts.minute.iloc[-1]:.0f} min"))
        rows.append(("tank water temperature rise", f"+{ts.water_avg_C.iloc[-1]-ts.water_avg_C.iloc[0]:.2f} K "
                     f"({ts.water_avg_C.iloc[0]:.1f} -> {ts.water_avg_C.iloc[-1]:.1f} C)"))
        rows.append(("heat given to the water (per metre depth)", f"{ts.heat_to_water_kJ_per_m.iloc[-1]:.0f} kJ"))
    rows.append(("node-model annual gain vs plain tank (g_window)", f"{n.get('g_window_kWh_yr', float('nan')):.1f} kWh/yr "
                 f"({n.get('pct_of_optimal_gain', float('nan')):.0f} % of optimal)"))
    rows.append(("selection verdict", n.get("verdict", "-")))
    return rows


def panel_html(item, idx):
    f, c, n, ts = item["folder"], item["c"], item["n"], item["ts"]
    d = c["design"]
    figs = f / "figures"
    gif_t = figs / "temp_video.gif"
    gif_l = figs / "liqfrac_video.gif"
    media = []
    if gif_t.exists():
        media.append(("Temperature - full discharge (animated)", b64(gif_t)))
    if gif_l.exists():
        media.append(("Liquid fraction - full discharge (animated)", b64(gif_l)))
    stills = []
    for lab, fn in (("START", f"{c['key']}_temp_START.png"), ("MID", f"{c['key']}_temp_MID.png"),
                    ("END", f"{c['key']}_temp_END.png"), ("END liq.frac", f"{c['key']}_liqfrac_END.png")):
        p = figs / fn
        if p.exists():
            stills.append((lab, b64(p)))

    wall_mm = 0.8
    param_rows = [
        ("PCM", f"{c['pcm']} (Regime {c['regime']})"),
        ("Capsule inner radius R_in", f"{d['R_in']*1000:.1f} mm"),
        ("Capsule outer diameter (R_in + 0.8mm Al wall)", f"{2*(d['R_in']*1000+wall_mm):.1f} mm"),
        ("Capsules, real 3-D design", f"{c['n_3d']} ({c['frac_of_optimal_N']*100:.0f} % of optimal 104)"),
        ("PCM volume fraction", f"{c['fraction_pct']:.1f} %"),
        ("PCM mass", f"{n.get('pcm_mass_kg', float('nan')):.1f} kg"),
        ("Flow rate", f"{d['flow']:.4f} kg/s"),
        ("Arrangement", d["arrangement"]),
        ("Drawn in Fluent (2-D proxy)", f"{c['proxy']['drawn_capsules']} capsules, inner R {c['proxy']['r_in_2d_m']*1000:.1f} mm"),
    ]

    pp = pcm_physical_props(c["pcm"])
    pcm_prop_rows = [
        ("Melting point Tm", f"{pp['Tm_C']:.1f} C  (mushy band {pp['Tm_C']-BAND_K/2:.1f}-{pp['Tm_C']+BAND_K/2:.1f} C)"),
        ("Latent heat of fusion", f"{pp['latent_kJ_kg']:.0f} kJ/kg"),
        ("Thermal conductivity k", f"{pp['k_W_mK']:.3f} W/m.K"),
        ("Density (solid/liquid avg)", f"{pp['density_avg']:.0f} kg/m3"),
        ("Specific heat cp (solid/liquid avg)", f"{pp['cp_avg_kJ_kgK']:.2f} kJ/kg.K"),
    ]
    run_rows = [
        ("Capsules start at (fully melted)", f"{T_CAPSULE_HOT_C:.0f} C"),
        ("Tank water starts at (cold, no sun)", f"{T_WATER_COLD_C:.0f} C"),
        ("Timestep", f"{c['run']['dt_s']:.0f} s"),
        ("Mesh", f"{c['mesh']['nx']} x {c['mesh']['ny']} cells (2-D planar slice)"),
        ("Solver", "ANSYS Fluent 26.1 Student, energy-only (momentum frozen), enthalpy-porosity melting model"),
    ]
    gate_rows = [
        ("Peak PCM temperature (safety limit 65 C)", f"{n.get('t_pcm_max_C', float('nan')):.2f} C  "
         f"{'PASS' if n.get('gate_pcm_le_65') else 'FAIL'}"),
        ("Peak water temperature (safety limit 75 C)", f"{n.get('t_water_max_C', float('nan')):.2f} C  "
         f"{'PASS' if n.get('gate_water_le_75') else 'FAIL'}"),
        ("g_annual (extra heat, whole year, vs plain tank)", f"{n.get('g_annual_kWh_yr', float('nan')):.1f} kWh/yr"),
        ("d_overheat (extra safety-shield hours/yr, lower better)", f"{n.get('d_overheat_h_yr', float('nan')):.0f} h/yr"),
        ("Repeatability (noise) band on g_window", f"{n.get('bands',{}).get('g_window_band', float('nan')):.1f} kWh/yr"),
    ]

    fig = None
    if ts is not None:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=ts.minute, y=ts.water_avg_C, name="tank water avg T [C]", line=dict(color="#1f77b4")), secondary_y=False)
        fig.add_trace(go.Scatter(x=ts.minute, y=ts.pcm_avg_C, name="capsule (PCM) avg T [C]", line=dict(color="#d62728")), secondary_y=False)
        fig.add_trace(go.Scatter(x=ts.minute, y=ts.liquid_fraction, name="PCM liquid fraction", line=dict(color="#2ca02c", dash="dot")), secondary_y=True)
        fig.update_yaxes(title_text="temperature [C]", secondary_y=False)
        fig.update_yaxes(title_text="liquid fraction", range=[0, 1.05], secondary_y=True)
        fig.update_xaxes(title_text="simulated time [min]")
        fig.update_layout(title=f"{c['title']} - ANSYS Fluent whole-tank discharge vs time", height=430, legend=dict(orientation="h", y=-0.2))

    rows_html = "".join(f"<tr><td>{k}</td><td><b>{v}</b></td></tr>" for k, v in param_rows)
    pcmprop_html = "".join(f"<tr><td>{k}</td><td><b>{v}</b></td></tr>" for k, v in pcm_prop_rows)
    run_html = "".join(f"<tr><td>{k}</td><td><b>{v}</b></td></tr>" for k, v in run_rows)
    gate_html = "".join(f"<tr><td>{k}</td><td><b>{v}</b></td></tr>" for k, v in gate_rows)
    timing_html = "".join(f"<tr><td>{k}</td><td><b>{v}</b></td></tr>" for k, v in timing_block(c, n, ts))
    media_html = "".join(f"<div class='mediabox'><h4>{lab}</h4><img src='{src}'></div>" for lab, src in media)
    stills_html = "".join(f"<div class='mediabox small'><h4>{lab}</h4><img src='{src}'></div>" for lab, src in stills)
    chart_html = to_html(fig, full_html=False, include_plotlyjs=False) if fig is not None else "<p><i>Fluent not run for this criteria yet.</i></p>"

    return f"""
<div class="panel" id="panel-{idx}" style="display:{'block' if idx == 0 else 'none'}">
  <h2>{c['title']}</h2>
  <p class="rule">{c['rule']}</p>
  <div class="cols">
    <div class="col">
      <h3>Design parameters</h3>
      <table class="ptable">{rows_html}</table>
    </div>
    <div class="col">
      <h3>PCM physical properties ({c['pcm']})</h3>
      <table class="ptable">{pcmprop_html}</table>
    </div>
  </div>
  <div class="cols">
    <div class="col">
      <h3>Fluent run settings (boundary/initial conditions)</h3>
      <table class="ptable">{run_html}</table>
    </div>
    <div class="col">
      <h3>Safety gates &amp; annual objectives (node model)</h3>
      <table class="ptable">{gate_html}</table>
    </div>
  </div>
  <h3>Timing &amp; result (this Fluent run)</h3>
  <table class="ptable">{timing_html}</table>
  <h3>Why it is (not) optimal</h3>
  <p>{c['why_not_optimal']}</p>
  <h3>ANSYS Fluent - video of the whole discharge</h3>
  <div class="mediarow">{media_html if media_html else "<p><i>No video yet - run with --frame-every, then build_gifs.py.</i></p>"}</div>
  <h3>Start / mid / end stills</h3>
  <div class="mediarow">{stills_html}</div>
  <h3>Temperature &amp; liquid fraction vs time</h3>
  {chart_html}
</div>"""


def all_together_html(items):
    f1 = make_subplots(rows=1, cols=3, subplot_titles=("tank water mean T [C]", "capsule mean T [C]", "PCM liquid fraction"))
    for it in items:
        if it["ts"] is None:
            continue
        d, col, c = it["ts"], it["color"], it["c"]
        lab = f"{short(c)} ({c['proxy']['drawn_capsules']} drawn / {c['n_3d']} real)"
        for j, y in enumerate(("water_avg_C", "pcm_avg_C", "liquid_fraction")):
            f1.add_trace(go.Scatter(x=d.minute, y=d[y], name=lab, legendgroup=c["key"], showlegend=(j == 0),
                                    line=dict(color=col)), 1, j + 1)
    f1.update_xaxes(title_text="simulated minutes")
    f1.update_layout(title="ANSYS Fluent - every criteria overlaid vs time", height=480)

    rows = [it["n"] for it in items]
    labs = [short(it["c"]) for it in items]
    f2 = make_subplots(rows=1, cols=2, subplot_titles=("g_window: annual gain vs plain tank [kWh/yr]", "PCM mass [kg]"))
    f2.add_trace(go.Bar(x=labs, y=[r.get("g_window_kWh_yr") for r in rows], marker_color=COL, showlegend=False), 1, 1)
    f2.add_trace(go.Bar(x=labs, y=[r.get("pcm_mass_kg") for r in rows], marker_color=COL, showlegend=False), 1, 2)
    f2.update_layout(title="Node model - how the optimal compares with every alternative", height=420)

    table_rows = "".join(
        f"<tr><td>{short(it['c'])}</td><td>{it['c']['n_3d']}</td><td>{it['n'].get('pcm_mass_kg', float('nan')):.1f}</td>"
        f"<td>{it['c']['design']['flow']:.4f}</td><td>{it['n'].get('g_window_kWh_yr', float('nan')):.1f}</td>"
        f"<td>{it['n'].get('pct_of_optimal_gain', float('nan')):.0f} %</td><td>{it['n'].get('verdict','')}</td></tr>"
        for it in items)
    return f"""
<div class="panel" id="panel-all" style="display:none">
  <h2>All together - optimal vs every alternative, over time</h2>
  <p>Regime 0, PureTemp 58, 100 L tank (H/D=2), 2.5 m2 flat-plate collector. Every criteria was simulated in BOTH the
  optimiser's node model (the annual kWh numbers, which chose the optimum) and ANSYS Fluent (the whole-tank discharge
  curves below) - see <a href="../docs/OBJ2_DATA_FLOW_INPUT_TO_OUTPUT.md">the data-flow doc</a> for how the two connect.</p>
  {to_html(f1, full_html=False, include_plotlyjs=False)}
  {to_html(f2, full_html=False, include_plotlyjs=False)}
  <table class="ptable wide">
    <tr><th>criteria</th><th>N capsules</th><th>PCM kg</th><th>flow</th><th>g_window kWh/yr</th><th>% of optimal</th><th>verdict</th></tr>
    {table_rows}
  </table>
</div>"""


def main():
    items = load_all()
    options = "".join(f"<option value='{i}'>{it['c']['title']}</option>" for i, it in enumerate(items))
    options += "<option value='all'>-- ALL TOGETHER (compare every criteria over time) --</option>"
    panels = "".join(panel_html(it, i) for i, it in enumerate(items))
    panels += all_together_html(items)

    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Objective 2 - criteria portal</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
body {{ font-family: -apple-system,Segoe UI,Roboto,sans-serif; max-width:1300px; margin:20px auto; padding:0 16px; color:#1a1a1a; }}
h1 {{ margin-bottom:4px; }} .sub {{ color:#555; margin-top:0; }}
select#picker {{ font-size:16px; padding:8px 12px; margin:14px 0 22px; width:100%; max-width:520px; }}
.panel h2 {{ border-bottom:3px solid #2ca02c; padding-bottom:6px; }}
.rule {{ font-style:italic; color:#333; background:#f3f7f2; padding:8px 12px; border-left:4px solid #2ca02c; }}
.cols {{ display:flex; gap:28px; flex-wrap:wrap; }} .col {{ flex:1; min-width:320px; }}
table.ptable {{ border-collapse:collapse; width:100%; }}
table.ptable td, table.ptable th {{ border:1px solid #ddd; padding:6px 10px; text-align:left; font-size:14px; }}
table.ptable tr:nth-child(even) {{ background:#fafafa; }}
table.ptable.wide th {{ background:#2ca02c; color:white; }}
.mediarow {{ display:flex; gap:14px; flex-wrap:wrap; }}
.mediabox {{ text-align:center; }} .mediabox img {{ max-width:420px; border:1px solid #ccc; border-radius:4px; }}
.mediabox.small img {{ max-width:260px; }}
.mediabox h4 {{ margin:4px 0; font-size:13px; color:#444; }}
</style></head><body>
<h1>Objective 2 - what if the design is not the optimum?</h1>
<p class="sub">Regime 0, PureTemp 58, 100 L tank. Pick a criteria below, or "ALL TOGETHER" to compare every one against time.</p>
<select id="picker" onchange="pick(this.value)">{options}</select>
{panels}
<script>
function pick(v) {{
  document.querySelectorAll('.panel').forEach(function(p) {{ p.style.display = 'none'; }});
  document.getElementById('panel-' + v).style.display = 'block';
  window.dispatchEvent(new Event('resize'));
}}
</script>
</body></html>"""
    out = ANS / "CRITERIA_PORTAL.html"
    out.write_text(html, encoding="utf-8")
    print(out, f"{out.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
