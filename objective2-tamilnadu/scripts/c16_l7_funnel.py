"""
scripts/c16_l7_funnel.py   (level L7, step O2-13, gate G3)
===========================================================
Selection funnel S0 / S1 / S2, FROZEN before any select-year run (and long before the 2006-2010 test).

  Step 1 'freeze'  : writes configs/funnel_frozen.json (rules, thresholds, tie-breaks, signature hash). Refuses to overwrite.
  Step 2 'evaluate' <cluster_id>: for each of the regime's three O1 PCMs, takes the K=6 best feasible designs of the L6 search (by robust mean gain on
         explore years) and re-evaluates them at FULL fidelity (dt 37.5 s) on the SELECT years 2020-2021, three anchors (robust objective).
  Step 3 'select'  : applies the funnel per regime across its three PCMs and writes results/c16_funnel_winners.csv.

Funnel (frozen):
  S0 feasibility : geometry valid, PCM peak <= 65 C, water peak <= 75 C, zero hours over the hard limit, in every anchor and select year.
  S1 benefit     : worst-anchor mean paired gain (select years) must exceed the pair's repeatability band (c15) -> otherwise the pair is 'no PCM benefit'.
                   Among S0+S1 designs, the best robust MEAN gain defines the leader; every design within one band of the leader is 'tied'.
  S2 tie-break   : among tied designs choose the lowest overheat (d_overheat_mean), then the smallest PCM volume, then the higher robust mean gain.
  Regime result  : the same funnel applied across the regime's three PCMs. If no design passes S1, the regime's recommendation is WATER-ONLY.
Usage: python scripts/c16_l7_funnel.py freeze | evaluate <cluster_id> [<rank>] | select
"""
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
FROZEN = Path("configs/funnel_frozen.json")
K_FINALISTS, SELECT_YEARS = 6, [2020, 2021]


def freeze():
    if FROZEN.exists():
        sys.exit("funnel already frozen: " + str(FROZEN))
    rules = {"version": "funnel_v1_common100L_175Lday", "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "finalists_per_pair": K_FINALISTS, "select_years": SELECT_YEARS, "fidelity": {"dt_s": 37.5, "anchors": ["bottom", "center", "top"]},
             "S0": {"pcm_peak_max_C": 65.0, "water_peak_max_C": 75.0, "hours_over_limit": 0, "geometry": "valid in every anchor"},
             "S1": {"rule": "worst-anchor mean paired gain (select years) > CORE repeatability band of the pair (c15: years, timestep, nodes, PCM properties, anchor; mains and demand are separate scenario sensitivities, the full band including them is reported alongside); else no PCM benefit",
                    "tie": "designs within one band of the leader's robust mean gain are tied"},
             "S2": {"order": ["lowest d_overheat_mean", "smallest PCM volume", "highest robust mean gain"]},
             "regime_rule": "same funnel across the three O1 PCMs; no passing design -> water-only",
             "metric": "paired E_del45_window_kWh gain (PCM tank minus same-flow water-only tank)", "no_reselection_after_test": True}
    FROZEN.write_text(json.dumps(rules, indent=2), encoding="utf-8")
    sig = hashlib.sha256(FROZEN.read_bytes()).hexdigest()
    Path("configs/funnel_frozen.sha256").write_text(sig, encoding="utf-8")
    print("frozen", sig[:16])


def evaluate(cid, ranks=(1, 2, 3)):
    from src.io_utils import get_regime
    from src.optimize.robust_eval import robust_row
    from config import STATE
    assert FROZEN.exists(), "freeze the funnel first"
    rows = []
    for rank in ranks:
        pcm = get_regime(STATE, cid)["pcm_shortlist"][rank - 1]
        tag = f"r{cid}_p{rank}"
        pts = pd.read_csv(f"results/c14_l6_points_{tag}.csv")
        pts = pts[pts.feasible == True].sort_values("g_window_mean", ascending=False).drop_duplicates(subset=["R_in_m", "N", "arrangement"]).head(K_FINALISTS)  # noqa: E712
        for _, p in pts.iterrows():
            row = robust_row(cid, pcm, float(p.R_in_m), float(p.fraction_req if "fraction_req" in p else p.fraction), p.arrangement, SELECT_YEARS, dt_s=None, purpose="select")
            row.update({"pair": tag, "rank": rank, "explore_g_window_mean": float(p.g_window_mean)})
            rows.append(row)
            print(tag, round(row.get("g_window_mean", np.nan), 2), flush=True)
    pd.DataFrame(rows).to_csv(f"results/c16_select_eval_r{cid}_p{ranks[0]}.csv" if len(ranks) == 1 else f"results/c16_select_eval_r{cid}.csv", index=False)


def select():
    import glob
    rules = json.loads(FROZEN.read_text())
    ev = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("results/c16_select_eval_r*_p*.csv"))], ignore_index=True)
    bdf = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("results/c15_l7_band_r*_p*.csv"))]).set_index("pair")
    ev["band"] = ev.pair.map(bdf["band_rss_kWh"])
    ev["band_full"] = ev.pair.map(bdf["band_full_rss_kWh"])
    ev["S0"] = ((ev.valid == True) & (ev.t_pcm_max_worst <= 65.0) & (ev.hours_over_limit == 0) & (ev.feasible == True))   # noqa: E712
    ev["S1"] = ev.S0 & (ev.g_window_worst > ev.band)
    out = []
    for cid, g in ev.groupby("regime"):
        ok = g[g.S1]
        if ok.empty:
            out.append({"regime": cid, "recommendation": "WATER-ONLY (no PCM design passes S1)", "n_candidates": len(g)})
            continue
        lead = ok.g_window_mean.max()
        tied = ok[ok.g_window_mean >= lead - ok.band]
        win = tied.sort_values(["d_overheat_mean", "N", "g_window_mean"], ascending=[True, True, False]).iloc[0]
        out.append({"regime": cid, "recommendation": "PCM", "pcm": win.pcm, "pair": win.pair, "R_in_m": win.R_in_m, "fraction": win.fraction,
                    "fraction_req": win.fraction_req, "arrangement": win.arrangement, "N": int(win.N), "select_g_window_mean": win.g_window_mean,
                    "select_g_window_worst": win.g_window_worst, "band_kWh": win.band, "band_full_kWh": win.band_full, "gain_over_full_band": win.g_window_worst / win.band_full, "leader_gain": lead, "n_tied": len(tied),
                    "d_overheat_mean_h": win.d_overheat_mean, "t_pcm_max_C": win.t_pcm_max_worst, "funnel_sha256": Path("configs/funnel_frozen.sha256").read_text()})
    pd.DataFrame(out).to_csv("results/c16_funnel_winners.csv", index=False)
    ev.to_csv("results/c16_select_eval_all.csv", index=False)
    print(pd.DataFrame(out).to_string())


if __name__ == "__main__":
    {"freeze": freeze, "evaluate": lambda: evaluate(int(sys.argv[2]), (int(sys.argv[3]),) if len(sys.argv) > 3 else (1, 2, 3)), "select": select}[sys.argv[1]]()
