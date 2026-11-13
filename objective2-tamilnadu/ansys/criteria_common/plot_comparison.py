"""ansys/criteria_common/plot_comparison.py - overlays every criteria's Fluent time series (water T, capsule T, liquid fraction)."""
import json
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ANSYS = Path(__file__).resolve().parents[1]
fig, ax = plt.subplots(1, 3, figsize=(17, 5))
rows = []
for f in sorted(ANSYS.glob("criteria_[0-9]_*")):
    csvs = list(f.glob("*_discharge_timeseries.csv"))
    if not csvs:
        continue
    c = json.loads((f / "criteria.json").read_text())
    d = pd.read_csv(csvs[0])
    lab = f"{c['title']} [{c['proxy']['drawn_capsules']} drawn / {c['n_3d']} real]"
    ax[0].plot(d.minute, d.water_avg_C, label=lab)
    ax[1].plot(d.minute, d.pcm_avg_C, label=lab)
    ax[2].plot(d.minute, d.liquid_fraction, label=lab)
    rows.append({"criteria": c["title"], "drawn": c["proxy"]["drawn_capsules"], "n_3d": c["n_3d"],
                 "water_start_C": d.water_avg_C.iloc[0], "water_end_C": d.water_avg_C.iloc[-1],
                 "water_rise_K": d.water_avg_C.iloc[-1] - d.water_avg_C.iloc[0],
                 "pcm_end_C": d.pcm_avg_C.iloc[-1], "liq_frac_end": d.liquid_fraction.iloc[-1],
                 "heat_to_water_kJ_per_m": d.heat_to_water_kJ_per_m.iloc[-1]})
for a, t, y in zip(ax, ("Tank-water mean temperature", "Capsule (PCM) mean temperature", "PCM liquid fraction"),
                   ("C", "C", "-")):
    a.set_title(t); a.set_xlabel("simulated time [min]"); a.set_ylabel(y); a.grid(alpha=.3)
ax[0].legend(fontsize=7)
fig.suptitle("ANSYS Fluent whole-tank discharge - all criteria (capsules start melted at 70 C, water 30 C, no sun)")
fig.tight_layout()
fig.savefig(Path(__file__).with_name("FLUENT_comparison_all_criteria.png"), dpi=130)
pd.DataFrame(rows).round(3).to_csv(Path(__file__).with_name("FLUENT_summary_all_criteria.csv"), index=False)
print(pd.DataFrame(rows).round(2).to_string())
