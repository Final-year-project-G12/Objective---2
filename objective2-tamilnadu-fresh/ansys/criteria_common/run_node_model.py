"""
ansys/criteria_common/run_node_model.py
=======================================
Runs every criteria scenario through the optimiser's OWN evaluator
(src/optimize/evaluate.py: multi-node tank, N=10 nodes, dt=150 s, select years
2021-2023, paired against the water-only tank at the same flow) and writes, into
each scenario's folder:

    node_model_results.json     objectives, gates, funnel (S0/S1) status, deltas vs optimum
    node_model_day.csv          hour-by-hour behaviour of one representative day (+ the night after)
    node_model_day.png          that day: outlet temp, PCM temp, melt fraction  vs plain tank and optimum
    node_model_terminal.txt     the same numbers as the terminal printout

and ansys/criteria_common/SUMMARY_all_criteria.{csv,png}.

Run from the project root:   python ansys/criteria_common/run_node_model.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scenarios import SCENARIOS, PCM, REGIME, N_OPT_3D, drawn_count          # noqa: E402
from src.optimize.evaluate import evaluate_design, _weather                   # noqa: E402
from src.design.space import to_design, geometry_bounds                        # noqa: E402
from src.simulation.run_case import run_case                                   # noqa: E402
from src.io_utils import solver_overrides_for                                  # noqa: E402
from config import STATE                                                       # noqa: E402

ANSYS = ROOT / "ansys"
YEAR = 2021
PURPOSE = "select"
FLOW_FOR_PLAIN = None


def day_series(design, pcm, weather, flow):
    """Hourly frame for one design (pcm=None -> plain tank)."""
    dv = to_design(design["R_in"], design["fraction"], flow, design["arrangement"])
    r = run_case(STATE, REGIME, pcm, dv, design_bounds=geometry_bounds(), weather=weather,
                 tank_model="multinode", n_nodes=10, stack_anchor="center",
                 compute_tes_metrics=False, night_day_stride=0,
                 system_config_overrides=solver_overrides_for(PURPOSE))
    return r["hourly"]


def pick_day(h, weather):
    """A typical sunny day: the 75th-percentile daily irradiation day, days aligned to LOCAL midnight
    (hour_index 0 is not local midnight: it carries a fixed offset, so align on hour_of_day == 0).
    Returns the hourly-frame index of that day's 06:00."""
    hod = h.hour_of_day.values.astype(int)
    first = int(np.argmax(hod == 0))
    ghi = h.I_t_Wm2.values[first:]
    n_days = len(ghi) // 24 - 2                       # leave room for the following night
    daily = ghi[: n_days * 24].reshape(n_days, 24).sum(axis=1)
    target = np.percentile(daily, 75)
    d = int(np.argmin(np.abs(daily - target)))
    return d, first + d * 24 + 6


def main(only=None):
    t0 = time.time()
    scs = [x for x in SCENARIOS if only is None or x['key'] in (only, SCENARIOS[0]['key'])]
    sel = json.loads((ROOT / "results" / "g10_selection_r0.json").read_text())
    band_g, band_d = sel["band"]["g_window"], sel["band"]["d_overheat"]
    pool = pd.read_csv(ROOT / "results" / "g10_selection_candidates_r0.csv")
    pool = pool[pool.feasible_select == True]                                  # noqa: E712
    g_best = pool.g_window.max()
    s0 = pool[pool.g_window >= g_best - band_g]
    d_floor = s0.d_overheat.min()

    w = _weather(REGIME, YEAR, PURPOSE)
    results = {}
    for sc in scs:
        d = sc["design"]
        print(f"[{sc['key']}] evaluating ...", flush=True)
        r = evaluate_design(REGIME, PCM, d["R_in"], d["fraction"], d["flow"], d["arrangement"], purpose=PURPOSE)
        results[sc["key"]] = r
        print("   ", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()
                      if k in ("valid", "reason", "N", "g_window", "g_annual", "d_overheat",
                               "t_pcm_max", "t_water_max", "pcm_mass_kg", "feasible")}, flush=True)

    opt = results[SCENARIOS[0]["key"]]

    # ---- representative day, plain + every scenario ----
    plain_flow = {sc["key"]: sc["design"]["flow"] for sc in SCENARIOS}
    h_ref = day_series(SCENARIOS[0]["design"], PCM, w, SCENARIOS[0]["design"]["flow"])
    day, start = pick_day(h_ref, w)
    sl = slice(start, start + 30)                    # 06:00 of the day -> 12:00 the next day
    series = {}
    plains = {}
    for sc in scs:
        d = sc["design"]
        if not results[sc["key"]]["valid"]:
            continue
        series[sc["key"]] = day_series(d, PCM, w, d["flow"]).iloc[sl].reset_index(drop=True)
        plains[sc["key"]] = day_series(d, None, w, d["flow"]).iloc[sl].reset_index(drop=True)
    print(f"representative day index {day} of {YEAR}; node-model day runs done ({time.time()-t0:.0f}s)", flush=True)

    rows = []
    for sc in scs:
        key = sc["key"]
        if only is not None and key != only:
            continue
        folder = ANSYS / key
        folder.mkdir(parents=True, exist_ok=True)
        r = results[key]
        d = sc["design"]
        out = {"key": key, "title": sc["title"], "rule": sc["rule"], "regime": REGIME, "pcm": PCM,
               "design": d, "valid": r["valid"], "reason": r["reason"], "N_3d": r["N"],
               "drawn_capsules_2d": drawn_count(r["N"]), "frac_of_optimal_N": r["N"] / N_OPT_3D}
        lines = []
        P = lines.append
        P("=" * 78)
        P(f" {sc['title']}   (Regime {REGIME}, {PCM}, node-model on select years 2021-23)")
        P("=" * 78)
        P(f" rule      : {sc['rule']}")
        P(f" parameters: R_in={d['R_in']*1000:.1f} mm  (capsule dia {2*(d['R_in']+0.0008)*1000:.1f} mm)"
          f"  fraction={r.get('fraction', d['fraction'])*100:.1f} %  flow={d['flow']:.4f} kg/s  {d['arrangement']}")
        if not r["valid"]:
            P(f" GEOMETRY INVALID: {r['reason']}")
            out["verdict"] = f"geometry invalid ({r['reason']})"
        else:
            gate_pcm = r["t_pcm_max"] <= 65.0
            gate_w = r["t_water_max"] <= 75.0
            rule_a = r["g_window"] > band_g
            in_s0 = r["g_window"] >= g_best - band_g
            in_s1 = in_s0 and r["d_overheat"] <= d_floor + band_d
            out.update({
                "N": r["N"], "pcm_mass_kg": r["pcm_mass_kg"], "g_window_kWh_yr": r["g_window"],
                "g_window_sd": r["g_window_sd"], "g_annual_kWh_yr": r["g_annual"],
                "d_overheat_h_yr": r["d_overheat"], "t_pcm_max_C": r["t_pcm_max"],
                "t_water_max_C": r["t_water_max"],
                "gate_pcm_le_65": bool(gate_pcm), "gate_water_le_75": bool(gate_w),
                "rule_A_beats_plain_beyond_band": bool(rule_a),
                "in_S0_tied_with_best": bool(in_s0), "in_S1_low_overheat": bool(in_s1),
                "pct_of_optimal_gain": 100.0 * r["g_window"] / opt["g_window"],
                "delta_vs_optimal": {
                    "N": r["N"] - opt["N"], "pcm_mass_kg": r["pcm_mass_kg"] - opt["pcm_mass_kg"],
                    "g_window": r["g_window"] - opt["g_window"], "g_annual": r["g_annual"] - opt["g_annual"],
                    "d_overheat": r["d_overheat"] - opt["d_overheat"],
                    "flow": d["flow"] - SCENARIOS[0]["design"]["flow"]},
                "bands": {"g_window_band": band_g, "d_overheat_band": band_d, "g_best_pool": float(g_best)},
            })
            P(f" capsules  : N = {r['N']} real  ({N_OPT_3D} optimal -> {100*r['N']/N_OPT_3D:.0f} %)   "
              f"PCM mass = {r['pcm_mass_kg']:.1f} kg  (optimal {opt['pcm_mass_kg']:.1f} kg)")
            P(f" drawn in Fluent (2-D proxy): {drawn_count(r['N'])} capsules")
            P("")
            P(" OBJECTIVES  (3 select years, paired with the water-only tank at the same flow)")
            P(f"   g_window  (extra deliverable heat 18:00-09:00) : {r['g_window']:8.1f} kWh/yr  "
              f"+/-{r['g_window_sd']:.1f} (year sd)   [optimal {opt['g_window']:.1f}]  -> {out['pct_of_optimal_gain']:.0f} % of optimal")
            P(f"   g_annual  (extra deliverable heat, whole year) : {r['g_annual']:8.1f} kWh/yr   [optimal {opt['g_annual']:.1f}]")
            P(f"   d_overheat (extra shield-hours, lower = better): {r['d_overheat']:8.1f} h/yr     [optimal {opt['d_overheat']:.1f}]")
            P(f"   peak PCM temperature                           : {r['t_pcm_max']:8.2f} C       (limit 65)  {'PASS' if gate_pcm else 'FAIL'}")
            P(f"   peak water temperature                         : {r['t_water_max']:8.2f} C       (limit 75)  {'PASS' if gate_w else 'FAIL'}")
            P("")
            P(" SELECTION FUNNEL (scripts/g10_select.py rules, regime-0 candidate pool)")
            P(f"   Rule A  gain > repeatability band ({band_g:.1f} kWh) : {'PASS' if rule_a else 'FAIL (indistinguishable from plain tank)'}")
            P(f"   S0      within {band_g:.1f} kWh of the best g_window ({g_best:.1f}) : {'IN' if in_s0 else 'OUT  <- eliminated here'}")
            P(f"   S1      (only if in S0) overheating within {band_d:.0f} h of the lowest in S0 ({d_floor:.0f}) : "
              f"{'IN' if in_s1 else ('OUT' if in_s0 else 'n/a')}")
            if key == SCENARIOS[0]["key"]:
                verdict = "OPTIMAL (this is the selected design)"
            elif not rule_a:
                verdict = "eliminated at Rule A (gain inside the noise band = no better than a plain tank)"
            elif not in_s0:
                verdict = "works and beats plain water, but eliminated at S0 (too far below the best g_window)"
            elif not in_s1:
                verdict = "tied on g_window, eliminated at S1 (more overheating)"
            else:
                verdict = (f"statistically TIED with the optimum (gain difference {r['g_window']-opt['g_window']:+.1f} kWh is inside "
                           f"the {band_g:.1f} kWh band); loses the final tie-break: PCM mass {r['pcm_mass_kg']:.2f} vs "
                           f"{opt['pcm_mass_kg']:.2f} kg, {r['N']} vs {opt['N']} capsules")
            out["verdict"] = verdict
            P(f"   VERDICT : {verdict}")
            P("")
            P(" WHY IT IS (NOT) OPTIMAL: " + sc["why_not_optimal"])
            P("")
            # hourly table
            s, pl, op = series[key], plains[key], series[SCENARIOS[0]["key"]]
            hod = s.hour_of_day.astype(int).values
            P(f" HOW IT VARIES WITH TIME - one sunny day (day {day} of {YEAR}), 06:00 -> 12:00 next day")
            P("   hour | outlet T this design | outlet T plain tank | gain C | PCM T C | melt frac | optimal outlet T")
            P("   -----+----------------------+---------------------+--------+---------+-----------+-----------------")
            for i in range(len(s)):
                P(f"   {hod[i]:02d}:00|        {s.T_w_C[i]:6.2f}        |       {pl.T_w_C[i]:6.2f}        |"
                  f" {s.T_w_C[i]-pl.T_w_C[i]:+6.2f} | {s.T_pcm_C[i]:6.2f}  |   {s.f_melt[i]:5.2f}   |      {op.T_w_C[i]:6.2f}")
            eve = [i for i in range(len(s)) if 18 <= hod[i] or hod[i] < 9][:]
            best_hr = int(np.argmax((s.T_w_C - pl.T_w_C).values))
            out["day"] = {"index": day, "max_gain_C": float((s.T_w_C - pl.T_w_C).max()),
                          "hour_of_max_gain": int(hod[best_hr]), "peak_melt_fraction": float(s.f_melt.max()),
                          "melt_fraction_at_18h": float(s.f_melt[list(hod).index(18)])}
            P("   NB: single-hour outlet temperatures can be below the plain tank (the PCM tank has already given its heat);")
            P("       the optimiser scores the TOTAL heat delivered at >=45 C over the whole 18:00-09:00 window (g_window).")
            P("")
            P(f"   peak melt fraction {s.f_melt.max():.2f}; largest outlet gain vs plain tank "
              f"{(s.T_w_C-pl.T_w_C).max():+.2f} C at {hod[best_hr]:02d}:00")

            df = pd.DataFrame({"hour_of_day": hod, "T_out_design_C": s.T_w_C, "T_out_plain_C": pl.T_w_C,
                               "T_out_optimal_C": op.T_w_C, "T_pcm_C": s.T_pcm_C, "f_melt": s.f_melt,
                               "f_melt_optimal": op.f_melt, "T_mean_design_C": s.T_w_mean_C})
            df.to_csv(folder / "node_model_day.csv", index=False)
            fig, ax = plt.subplots(3, 1, figsize=(9, 9), sharex=True)
            x = np.arange(len(s))
            ax[0].plot(x, pl.T_w_C, "k--", label="plain water tank")
            ax[0].plot(x, op.T_w_C, color="tab:green", alpha=.7, label="optimal (104 capsules)")
            ax[0].plot(x, s.T_w_C, "r", lw=2, label=sc["title"].split(". ", 1)[1])
            ax[0].axhline(45, color="grey", ls=":"); ax[0].text(0.5, 45.5, "45 C delivery target", fontsize=8)
            ax[0].set_ylabel("outlet (top) water T [C]"); ax[0].legend(fontsize=8); ax[0].grid(alpha=.3)
            ax[1].plot(x, s.T_pcm_C, "r", lw=2, label="PCM temperature (this design)")
            ax[1].plot(x, op.T_pcm_C if "T_pcm_C" in op else s.T_pcm_C, color="tab:green", alpha=.7, label="PCM temperature (optimal)")
            ax[1].axhline(58, color="grey", ls=":"); ax[1].text(0.5, 58.4, "PureTemp 58 melting point", fontsize=8)
            ax[1].set_ylabel("PCM T [C]"); ax[1].legend(fontsize=8); ax[1].grid(alpha=.3)
            ax[2].plot(x, s.f_melt, "r", lw=2, label="this design"); ax[2].plot(x, op.f_melt, color="tab:green", alpha=.7, label="optimal")
            ax[2].set_ylabel("PCM melt fraction"); ax[2].set_ylim(-0.05, 1.05); ax[2].legend(fontsize=8); ax[2].grid(alpha=.3)
            ax[2].set_xticks(x[::3]); ax[2].set_xticklabels([f"{h:02d}:00" for h in hod[::3]], rotation=45)
            ax[2].axvspan(12, 27, color="navy", alpha=.07)
            ax[2].text(12.3, 0.9, "evening/night window 18:00-09:00", fontsize=8)
            fig.suptitle(f"{sc['title']} - node model, one sunny day + night")
            fig.tight_layout()
            fig.savefig(folder / "node_model_day.png", dpi=130)
            plt.close(fig)

        (folder / "node_model_terminal.txt").write_text("\n".join(lines), encoding="utf-8")
        (folder / "node_model_results.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
        print("\n".join(lines), flush=True)
        rows.append({"criteria": sc["title"], "N": out.get("N"), "R_in_mm": d["R_in"] * 1000,
                     "fraction_pct": 100 * r.get("fraction", d["fraction"]), "flow": d["flow"], "arr": d["arrangement"],
                     "pcm_mass_kg": out.get("pcm_mass_kg"), "g_window": out.get("g_window_kWh_yr"),
                     "pct_of_optimal": out.get("pct_of_optimal_gain"), "g_annual": out.get("g_annual_kWh_yr"),
                     "d_overheat": out.get("d_overheat_h_yr"), "t_pcm_max": out.get("t_pcm_max_C"),
                     "t_water_max": out.get("t_water_max_C"), "verdict": out["verdict"]})

    if only is not None:
        print(f"DONE ({only}) in {time.time()-t0:.0f}s", flush=True)
        return
    summ = pd.DataFrame(rows)
    summ.to_csv(ANSYS / "criteria_common" / "SUMMARY_all_criteria.csv", index=False)
    fig, ax = plt.subplots(figsize=(10, 5))
    lab = [r.split(". ", 1)[1] if ". " in r else r for r in summ.criteria]
    colors = ["tab:green" if i == 0 else "tab:blue" for i in range(len(summ))]
    ax.bar(range(len(summ)), summ.g_window.fillna(0), color=colors)
    ax.axhline(band_g, color="red", ls="--"); ax.text(len(summ) - 1.4, band_g + 5, "repeatability band (Rule A)", color="red", fontsize=8)
    ax.axhline(g_best - band_g, color="orange", ls="--"); ax.text(len(summ) - 1.4, g_best - band_g + 5, "S0 threshold", color="orange", fontsize=8)
    for i, v in enumerate(summ.g_window.fillna(0)):
        ax.text(i, v + 4, f"{v:.0f}", ha="center", fontsize=9)
    ax.set_xticks(range(len(summ))); ax.set_xticklabels([l[:40] for l in lab], rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("g_window: extra evening-window heat vs plain tank [kWh/yr]")
    ax.set_title("Regime 0 / PureTemp 58 - what each criteria set delivers (node model, select years)")
    fig.tight_layout(); fig.savefig(ANSYS / "criteria_common" / "SUMMARY_all_criteria.png", dpi=130)
    print(f"\nALL DONE in {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
