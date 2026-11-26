"""
scripts/g10_select.py
========================
G10 / WP6 / S7 - final design selection per regime on the SELECT years (2021-2023). Reproducible from seeds and files.

Candidates: for every O1 PCM of the regime, the non-dominated feasible designs (explore years) from g9_points_*.csv,
thinned to <= 30 per pair. Each candidate is re-simulated on the select years (src/optimize/evaluate.py).
Hard constraints on the select years: PCM peak <= 65 C and water peak <= 75 C in every year (user decision), exact geometry.
Rule (decisions D9/D10, plan section 6A):
  A  "better than water-only": select-year paired g_window must exceed the WP6 band (wp6_band.csv, regime scope) -- else the
     regime is reported as NO MEANINGFUL BENEFIT on the primary metric and the best design is still shown, not hidden.
  B  S0 = candidates within band(g_window) of the best g_window;
     S1 = those in S0 within band(d_overheat) of the lowest overheating; (tie-breaker a)
     S2 = those in S1 within the measured tau_serve band of the best tau_serve gain; (tie-breaker b)
     pick: lowest PCM mass (c), then fewest capsules (d), then largest margin to 65 C (e).
  Everything left in S0 that cannot be told apart by the band is reported as INDISTINGUISHABLE, not as a win.
Frozen for the one-shot held-out test (g10_test.py): the chosen design per regime plus the best g_window design of every
other O1 PCM of that regime, so the test is not a one-design cherry pick. The selection log carries a SHA-256 fingerprint.
Usage: python scripts/g10_select.py <cluster_id>      -> results/g10_selection_r<c>.json and _candidates.csv
"""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.io_utils import get_regime
from src.optimize.evaluate import evaluate_design, evaluate_night
from src.optimize.nsga2 import non_dominated_mask

OUT = Path("results")
MAX_PER_PAIR = 30
NIGHT_TOP = 12                  # tau_serve is computed for the best-g_window candidates only (cost)


def front_candidates(cid, rank):
    src = next((OUT / f"g9_points_r{cid}_p{rank}{suf}.csv" for suf in ("_ext2", "_ext", "")
                if (OUT / f"g9_points_r{cid}_p{rank}{suf}.csv").exists()))      # latest G9 state of the pair (see progress log 11.1-11.3)
    print("candidates from", src.name, flush=True)
    pts = pd.read_csv(src)
    ok = pts[pts.feasible == True].drop_duplicates(subset=["R_in_m", "N", "flow", "arrangement"])  # noqa: E712
    F = np.column_stack([-ok.g_window, -ok.g_annual, ok.d_overheat])
    fr = ok[non_dominated_mask(F)].sort_values("g_annual")
    if len(fr) > MAX_PER_PAIR:
        fr = fr.iloc[np.linspace(0, len(fr) - 1, MAX_PER_PAIR).astype(int)]
    return fr


def main(cid):
    band = pd.read_csv(OUT / "wp6_band.csv")
    b = band[band.scope == f"r{cid}"].set_index("objective").band
    pcms = get_regime("uttarakhand", cid)["pcm_shortlist"]
    rows = []
    for rank, pcm in enumerate(pcms, start=1):
        for c in front_candidates(cid, rank).itertuples():
            res = evaluate_design(cid, pcm, float(c.R_in_m), float(c.fraction), float(c.flow), c.arrangement, purpose="select")
            if not res["valid"]:
                continue
            rows.append({"pcm": pcm, "pcm_rank": rank, "R_in_m": c.R_in_m, "fraction": res["fraction"], "N": res["N"],
                         "flow": c.flow, "arrangement": c.arrangement, "g_window": res["g_window"], "g_annual": res["g_annual"],
                         "d_overheat": res["d_overheat"], "g_window_sd": res["g_window_sd"], "t_pcm_max": res["t_pcm_max"],
                         "t_water_max": res["t_water_max"], "feasible_select": res["feasible"], "pcm_mass_kg": res["pcm_mass_kg"],
                         "explore_g_window": c.g_window, "explore_g_annual": c.g_annual})
            print(cid, pcm, len(rows), flush=True)
    cand = pd.DataFrame(rows)
    feas = cand[cand.feasible_select].copy()
    best = feas.sort_values("g_window", ascending=False)
    top = best.head(NIGHT_TOP)
    tau = []
    for r in top.itertuples():
        nm = evaluate_night(cid, r.pcm, r.R_in_m, r.fraction, r.flow, r.arrangement, "select", stride=15)
        d = pd.DataFrame(nm)
        tau.append({"idx": r.Index, "gain_tau_serve_h": d.gain_tau_serve_mean_h.mean(),
                    "gain_tau_serve_se": d.gain_tau_serve_mean_h.std(ddof=1) / np.sqrt(len(d)),
                    "gain_tau_hold_h": d.gain_tau_hold_mean_h.mean(), "gain_serve_frac": d.gain_serve_frac_45_mean.mean()})
    tau = pd.DataFrame(tau).set_index("idx")
    cand = cand.join(tau)
    feas = cand[cand.feasible_select].copy()                      # re-take after the join so the tau columns are present
    best = feas.sort_values("g_window", ascending=False)

    log = {"regime": cid, "n_candidates": int(len(cand)), "n_feasible_select": int(len(feas)),
           "band": {k: float(v) for k, v in b.items()}}
    if feas.empty:
        log.update(verdict="no feasible candidate on the select years")
    else:
        g_best = best.g_window.iloc[0]
        s0 = best[best.g_window >= g_best - b["g_window"]]
        s1 = s0[s0.d_overheat <= s0.d_overheat.min() + b["d_overheat"]]
        s1t = s1.dropna(subset=["gain_tau_serve_h"])
        tau_band = float(s1t.gain_tau_serve_se.mean()) if len(s1t) else 0.0
        s2 = s1t[s1t.gain_tau_serve_h >= s1t.gain_tau_serve_h.max() - tau_band] if len(s1t) else s1
        pick = s2.sort_values(["pcm_mass_kg", "N", "t_pcm_max"]).iloc[0]
        log.update({
            "meaningful_on_primary_metric": bool(pick.g_window > b["g_window"]),
            "chosen": {k: (v.item() if hasattr(v, "item") else v) for k, v in pick.items() if not k.startswith("gain_") or pd.notna(v)},
            "n_S0_indistinguishable_on_g_window": int(len(s0)), "n_S1": int(len(s1)), "n_S2": int(len(s2)),
            "tau_serve_band_h": tau_band,
            "alternatives_best_per_pcm": [
                {k: (v.item() if hasattr(v, "item") else v) for k, v in best[best.pcm == p].iloc[0].items()}
                for p in pcms if (best.pcm == p).any()],
        })
    body = json.dumps(log, sort_keys=True, default=str)
    log["fingerprint_sha256"] = hashlib.sha256((body + cand.round(9).to_csv()).encode()).hexdigest()
    cand.to_csv(OUT / f"g10_selection_candidates_r{cid}.csv", index=False)
    (OUT / f"g10_selection_r{cid}.json").write_text(json.dumps(log, indent=1, default=str))
    print("written", cid, log.get("meaningful_on_primary_metric"), log["fingerprint_sha256"][:12])


if __name__ == "__main__":
    main(int(sys.argv[1]))
