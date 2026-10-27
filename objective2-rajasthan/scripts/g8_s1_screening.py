"""
scripts/g8_s1_screening.py
=============================
G8 / S1 (plan WP5 5.4) - Taguchi L9 screening of the four approved variables for ONE (regime, O1 PCM) pair,
replicated over the five explore years (2016-2020). Usage: python scripts/g8_s1_screening.py <cluster_id> <pcm_rank 1..3>

Levels (approved space): inner radius 10/25/40 mm; PCM fraction 2/16/30 %; flow 0.010/0.030/0.050 kg/s;
arrangement single-layer/staggered/radial. Responses (paired vs water-only at the same flow): g_window, g_annual,
d_overheat, t_pcm_max. Writes results/g8_s1_r<c>_p<rank>.csv (one row per run-year) and the ANOVA table.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.io_utils import get_regime
from src.optimize.anova import L9, anova
from src.optimize.evaluate import evaluate_design

R_LEVELS = (0.010, 0.025, 0.040)
F_LEVELS = (0.02, 0.16, 0.30)      # v3 box (cap 30 %); v1 used 0.02/0.11/0.20
Q_LEVELS = (0.010, 0.030, 0.050)
ARR = ("single-layer", "staggered", "radial")
FACTORS = ["R_in_mm", "fraction", "flow", "arrangement"]
RESP = ["g_window", "g_annual", "d_overheat", "t_pcm_max"]


def main(cid, rank):
    pcm = get_regime("rajasthan", cid)["pcm_shortlist"][rank - 1]
    rows = []
    for run, (a, b, c, d) in enumerate(L9, start=1):
        r, f, q, arr = R_LEVELS[a], F_LEVELS[b], Q_LEVELS[c], ARR[d]
        res = evaluate_design(cid, pcm, r, f, q, arr, purpose="explore")
        if not res["valid"]:
            rows.append({"run": run, "regime": cid, "pcm": pcm, "R_in_mm": r * 1000, "fraction": f, "flow": q,
                         "arrangement": arr, "valid": False, "reason": res["reason"]})
            continue
        for y in res["per_year"]:
            rows.append({"run": run, "regime": cid, "pcm": pcm, "R_in_mm": r * 1000, "fraction": f, "flow": q,
                         "arrangement": arr, "N": res["N"], "valid": True, "reason": "", **y})
        print(cid, rank, run, flush=True)
    df = pd.DataFrame(rows)
    out = Path(f"results/g8_s1_r{cid}_p{rank}.csv")
    df.to_csv(out, index=False)
    ok = df[df.valid]
    if len(ok) >= 20:
        tabs = [anova(ok, FACTORS, r) for r in RESP]
        pd.concat(tabs).to_csv(f"results/g8_s1_anova_r{cid}_p{rank}.csv", index=False)
    print("written", out)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
