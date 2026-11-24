"""ansys/criteria_common/build_compare_page.py -> ansys/CRITERIA_COMPARE.html

Interactive page: pick a criteria, see its MP4, its design numbers and how it differs from the optimum;
all 7 Fluent discharge curves are overlaid and the picked one is highlighted. Open the HTML from the ansys folder
(it links to the mp4 files by relative path). Needs internet once for plotly (CDN).
"""
import json
from pathlib import Path

import pandas as pd

ANS = Path(__file__).resolve().parents[1]
COL = ["#2ca02c", "#1f77b4", "#d62728", "#ff7f0e", "#9467bd", "#8c564b", "#e377c2"]

items = []
for i, f in enumerate(sorted(ANS.glob("criteria_[0-9]_*"))):
    c = json.loads((f / "criteria.json").read_text())
    n = json.loads((f / "node_model_results.json").read_text())
    ts = pd.read_csv(next(f.glob("*_discharge_timeseries.csv")))
    items.append(dict(
        key=f.name, title=c["title"], color=COL[i], video=f"{f.name}/figures/{f.name}.mp4",
        rule=c["rule"], why=c.get("why_not_optimal", ""), verdict=n["verdict"],
        R=c["design"]["R_in"] * 1000, N=n["N"], drawn=c["proxy"]["drawn_capsules"], mass=n["pcm_mass_kg"],
        flow=c["design"]["flow"], arr=c["design"]["arrangement"], gain=n["g_window_kWh_yr"], pct=n["pct_of_optimal_gain"],
        over=n["d_overheat_h_yr"], tpcm=n["t_pcm_max_C"],
        t=ts.minute.round(2).tolist(), water=ts.water_avg_C.round(3).tolist(), pcm=ts.pcm_avg_C.round(3).tolist(),
        lf=ts.liquid_fraction.round(4).tolist(), heat=ts.heat_to_water_kJ_per_m.round(1).tolist()))

HTML = """<!doctype html><html><head><meta charset="utf-8"><title>Criteria comparison</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
body{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f5f5f7;color:#222}
header{background:#A4123F;color:#fff;padding:14px 22px}
header h1{margin:0;font-size:20px} header p{margin:4px 0 0;font-size:13px;opacity:.9}
#tabs{display:flex;flex-wrap:wrap;gap:6px;padding:12px 22px}
#tabs button{border:2px solid #ccc;background:#fff;border-radius:18px;padding:6px 12px;cursor:pointer;font-size:13px}
#tabs button.on{color:#fff;border-color:transparent}
main{display:grid;grid-template-columns:minmax(380px,1fr) minmax(380px,1fr);gap:14px;padding:0 22px 22px}
.card{background:#fff;border-radius:10px;padding:12px;box-shadow:0 1px 3px #0002}
video{width:100%;border-radius:6px;background:#000}
table{border-collapse:collapse;width:100%;font-size:13px} td,th{padding:4px 6px;border-bottom:1px solid #eee;text-align:left}
td.d{font-weight:600} .pos{color:#1a7f37}.neg{color:#c62828}
.wide{grid-column:1/-1} h3{margin:0 0 8px;font-size:15px}
@media(max-width:900px){main{grid-template-columns:1fr}}
</style></head><body>
<header><h1>Objective 2 - how the 7 designs differ (Tamil Nadu regime 0, PureTemp 58, 100 L tank)</h1>
<p>Pick a design. Fluent: capsules start melted at 70 C in 30 C water, no sun, 60 minutes. Yearly gain comes from the node model on 2021-23.</p></header>
<div id="tabs"></div>
<main>
<div class="card"><h3 id="vt"></h3><video id="vid" controls loop muted playsinline></video>
<p style="font-size:12px;color:#666;margin:6px 0 0">Left: temperature. Right: liquid fraction of the PCM (1 = fully melted).</p></div>
<div class="card"><h3>Design vs the optimum</h3><table id="tbl"></table><p id="why" style="font-size:13px"></p></div>
<div class="card"><h3>Water temperature in the tank (mean)</h3><div id="p1" style="height:300px"></div></div>
<div class="card"><h3>PCM liquid fraction</h3><div id="p2" style="height:300px"></div></div>
<div class="card"><h3>Heat given to the water (kJ per metre of tank depth)</h3><div id="p3" style="height:300px"></div></div>
<div class="card"><h3>Yearly extra evening heat (kWh/yr) and overheating hours</h3><div id="p4" style="height:300px"></div></div>
<div class="card wide"><h3>All designs side by side (videos)</h3>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:10px">
<div><b>Temperature</b><video controls loop muted playsinline src="videos/COMPARE_temperature_all_criteria.mp4"></video></div>
<div><b>Liquid fraction</b><video controls loop muted playsinline src="videos/COMPARE_liquid_fraction_all_criteria.mp4"></video></div></div></div>
</main>
<script>
const D=__DATA__; let cur=0; const opt=D[0];
const tabs=document.getElementById('tabs');
D.forEach((d,i)=>{const b=document.createElement('button');b.textContent=d.title;b.onclick=()=>show(i);b.id='b'+i;tabs.appendChild(b)});
function diff(v,o,unit,dp,lowerBetter){const x=v-o;if(Math.abs(x)<1e-9)return '<td>-</td>';const s=(x>0?'+':'')+x.toFixed(dp)+unit;return '<td class="d">'+s+'</td>'}
function show(i){cur=i;const d=D[i];
 D.forEach((e,k)=>{const b=document.getElementById('b'+k);b.className=k==i?'on':'';b.style.background=k==i?e.color:'#fff'});
 document.getElementById('vt').textContent=d.title;
 const v=document.getElementById('vid');v.src=d.video;v.play().catch(()=>{});
 const rows=[['Capsule radius',d.R.toFixed(0)+' mm',d.R-opt.R,' mm',0],['Capsules (real)',d.N,d.N-opt.N,'',0],['Capsules drawn in Fluent',d.drawn,d.drawn-opt.drawn,'',0],
  ['PCM mass',d.mass.toFixed(1)+' kg',d.mass-opt.mass,' kg',1],['Flow',d.flow.toFixed(3)+' kg/s',d.flow-opt.flow,'',3],['Arrangement',d.arr,0,'',0],
  ['Extra evening heat',d.gain.toFixed(1)+' kWh/yr',d.gain-opt.gain,' kWh',1],['% of optimal',d.pct.toFixed(0)+' %',d.pct-100,' %',0],
  ['Overheating',d.over.toFixed(0)+' h/yr',d.over-opt.over,' h',0],['Peak PCM temp',d.tpcm.toFixed(1)+' C (limit 65)',d.tpcm-opt.tpcm,' C',1]];
 document.getElementById('tbl').innerHTML='<tr><th></th><th>This design</th><th>vs optimum</th></tr>'+rows.map(r=>'<tr><td>'+r[0]+'</td><td>'+r[1]+'</td>'+(i==0?'<td>-</td>':diff(r[2],0,r[3],r[4]))+'</tr>').join('')
   +'<tr><td>Verdict</td><td colspan=2>'+d.verdict+'</td></tr>';
 document.getElementById('why').innerHTML='<b>What it is:</b> '+d.rule+(d.why?'<br><b>Why not optimal:</b> '+d.why:'');
 draw();}
function traces(y,hl){return D.map((d,k)=>({x:d.t,y:d[y],name:d.title,mode:'lines',line:{color:d.color,width:k==hl?5:1.5},opacity:k==hl?1:.35}))}
function draw(){const lay=(yt)=>({margin:{t:10,l:50,r:10,b:40},xaxis:{title:'minutes after sun goes off'},yaxis:{title:yt},showlegend:false});
 Plotly.react('p1',traces('water',cur),lay('water mean T [C]'));
 Plotly.react('p2',traces('lf',cur),lay('liquid fraction'));
 Plotly.react('p3',traces('heat',cur),lay('kJ/m'));
 Plotly.react('p4',[{type:'bar',x:D.map(d=>d.title.split('.')[0]),y:D.map(d=>d.gain),marker:{color:D.map((d,k)=>k==cur?d.color:'#bbb')},name:'kWh/yr',text:D.map(d=>d.gain.toFixed(0)),textposition:'outside'},
  {type:'scatter',mode:'lines+markers',x:D.map(d=>d.title.split('.')[0]),y:D.map(d=>d.over),yaxis:'y2',name:'overheating h/yr',line:{color:'#c62828'}}],
  {margin:{t:10,l:50,r:50,b:40},xaxis:{title:'criteria number'},yaxis:{title:'kWh/yr'},yaxis2:{overlaying:'y',side:'right',title:'overheating h/yr'},showlegend:true,legend:{orientation:'h',y:1.15}});}
show(0);
</script></body></html>"""
out = ANS / "CRITERIA_COMPARE.html"
out.write_text(HTML.replace("__DATA__", json.dumps(items)), encoding="utf-8")
print(out, out.stat().st_size // 1024, "KB")
