"""
scripts/g8_s1_screening.py
=============================
G8 / S1 (plan O2-7) - Taguchi L9 screening for ONE (regime, O1 PCM) pair on the explore years 2016-2019 (150 s), every run at every
robust anchor. Rebuild levels (2026-11-23): inner radius 10/25/40 mm; PCM fraction 2/21/40 % (the 40 % level added, plan O2-7);
arrangement single-layer/staggered/radial. Flow is fixed (plan R6), so L9 column C is left empty (Taguchi error column).
Responses (paired vs the water-only tank, per year and anchor): g_window, g_annual, d_overheat, t_pcm_max. ANOVA factors: R_in,
fraction, arrangement and the anchor (full factorial on the anchor), error from the year replicates.
Usage: python scripts/g8_s1_screening.py <cluster_id> <pcm_rank 1..3>
Writes results/g8_s1_r<c>_p<rank>.csv (one row per run-year-anchor) and results/g8_s1_anova_r<c>_p<rank>.csv.
Screening ranks factors only; it never selects a design.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.design.box import f_bounds, flow_fixed, r_bounds       # noqa: E402
from src.io_utils import get_regime                             # noqa: E402
from src.optimize.anova import L9, anova                        # noqa: E402
from src.optimize.evaluate import evaluate_design               # noqa: E402
from src.weather import roles                                   # noqa: E402

(R0, R1), (F0, F1) = r_bounds(), f_bounds()
R_LEVELS = (R0, (R0 + R1) / 2, R1)
F_LEVELS = (F0, round((F0 + F1) / 2, 4), F1)
ARR = ("single-layer", "staggered", "radial")
FACTORS = ["R_in_mm", "fraction", "arrangement", "anchor"]
RESP = ["g_window", "g_annual", "d_overheat", "t_pcm_max"]


def main(cid, rank):
    pcm = get_regime("rajasthan", cid)["pcm_shortlist"][rank - 1]
    rows = []
    for run, (a, b, _c, d) in enumerate(L9, start=1):
        r, f, arr = R_LEVELS[a], F_LEVELS[b], ARR[d]
        res = evaluate_design(cid, pcm, r, f, flow_fixed(), arr, purpose="explore", years=roles.years_for("explore"),
                              fidelity="cheap")
        base = {"run": run, "regime": cid, "pcm": pcm, "R_in_mm": r * 1000, "fraction": f, "arrangement": arr}
        if not res["valid"]:
            rows.append({**base, "valid": False, "reason": res["reason"]})
            continue
        for y in res["per_year"]:
            rows.append({**base, "N": res["N"], "valid": True, "reason": "", **y})
        print(cid, rank, run, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(f"results/g8_s1_r{cid}_p{rank}.csv", index=False)
    ok = df[df.valid]
    if len(ok) >= 20:
        pd.concat([anova(ok, FACTORS, r) for r in RESP]).to_csv(f"results/g8_s1_anova_r{cid}_p{rank}.csv", index=False)
    print("written", cid, rank, flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
