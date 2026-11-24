"""
scripts/c3_weather_audit.py   (level L2, plan section 7.3 / step O2-1)
=======================================================================
WEATHER-ONLY audit of every medoid-year (no plant outcome is looked at): annual and seasonal GHI, lower-tail daily GHI, longest
run of cloudy days, ambient temperature, completeness. Each year is compared with the 2006-2025 distribution of the same
point. Reads the point-year CSVs directly (all roles), so it does not use the role loader and does not touch any lock.
Writes results/c3_weather_audit.csv and results/c3_weather_audit.md.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
inv = pd.read_csv(ROOT / "data/weather/point_years/weather_inventory.csv")
MED = {0: "TNP_0006", 1: "TNP_0007", 2: "TNP_0001"}
ROLE = dict(zip(inv.year, inv.role))


def longest_run(mask):
    best = cur = 0
    for v in mask:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best


rows = []
for cid, pid in MED.items():
    for y in sorted(ROLE):
        if y in range(2011, 2016):
            pass
        p = ROOT / f"data/weather/point_years/tamilnadu/cluster{cid}_{pid}_{y}.csv"
        d = pd.read_csv(p, parse_dates=["timestamp_utc"])
        d = d[~((d.timestamp_utc.dt.month == 2) & (d.timestamp_utc.dt.day == 29))]
        d["date"] = d.timestamp_utc.dt.date
        day = d.groupby("date").agg(ghi=("GHI_Wm2", lambda s: s.sum() / 1000.0), clr=("GHI_clearsky_Wm2", lambda s: s.sum() / 1000.0),
                                    t=("T_amb_C", "mean"))
        kt = (day.ghi / day.clr.replace(0, np.nan)).clip(0, 1.2)
        m = pd.to_datetime(day.index).month
        rows.append({"regime": cid, "point": pid, "year": y, "role": ROLE[y], "hours": len(d),
                     "nan_ghi": int(d.GHI_Wm2.isna().sum()),
                     "GHI_annual_kWh_m2": day.ghi.sum(), "GHI_daily_mean": day.ghi.mean(), "GHI_daily_p10": day.ghi.quantile(0.10),
                     "kt_mean": kt.mean(), "cloudy_days_kt<0.4": int((kt < 0.4).sum()),
                     "longest_cloudy_run_d": longest_run((kt < 0.4).to_numpy()),
                     "GHI_NEmonsoon_OctDec": day.ghi[(m >= 10)].mean(), "GHI_SWmonsoon_JunSep": day.ghi[(m >= 6) & (m <= 9)].mean(),
                     "T_amb_mean_C": day.t.mean()})
df = pd.DataFrame(rows)
for c in ("GHI_annual_kWh_m2", "kt_mean", "GHI_daily_p10", "longest_cloudy_run_d"):
    g = df.groupby("regime")[c]
    df[c + "_z"] = (df[c] - g.transform("mean")) / g.transform("std")
(ROOT / "results").mkdir(exist_ok=True)
df.to_csv(ROOT / "results/c3_weather_audit.csv", index=False)

lines = ["# Weather-only audit (L2) - Tamil Nadu medoids, 2006-2025", "",
         "No plant outcome used. z = distance from the point's own 2006-2025 mean in SDs.", ""]
for cid in MED:
    g = df[df.regime == cid]
    lines += [f"## Regime {cid} ({MED[cid]})", "", "| year | role | GHI kWh/m2 | z | kt | p10 daily | cloudy d | longest run d | NE-monsoon GHI | NaN |", "|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in g.iterrows():
        lines.append(f"| {r.year} | {r.role} | {r.GHI_annual_kWh_m2:.0f} | {r.GHI_annual_kWh_m2_z:+.1f} | {r.kt_mean:.3f} | {r.GHI_daily_p10:.2f} | {r['cloudy_days_kt<0.4']} | {r.longest_cloudy_run_d} | {r.GHI_NEmonsoon_OctDec:.2f} | {r.nan_ghi} |")
    lines.append("")
    for role in ("explore", "select", "test", "report"):
        s = g[g.role == role]
        lines.append(f"* {role}: mean annual GHI {s.GHI_annual_kWh_m2.mean():.0f} kWh/m2, mean kt {s.kt_mean.mean():.3f}")
    lines.append("")
(ROOT / "results/c3_weather_audit.md").write_text("\n".join(lines), encoding="utf-8")
print(df.groupby(["regime", "role"])[["GHI_annual_kWh_m2", "kt_mean", "GHI_daily_p10", "longest_cloudy_run_d"]].mean().round(2).to_string())
print("max |z| annual GHI:", df.GHI_annual_kWh_m2_z.abs().max().round(2), "| any NaN GHI:", int(df.nan_ghi.sum()), "| hours != 8760:", int((df.hours != 8760).sum()))
