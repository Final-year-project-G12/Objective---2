"""
scripts/c8_l4_taguchi.py   (level L4, step O2-7)
=================================================
Taguchi L9 screen on the common-plant box for ONE (regime, O1 PCM) pair, explore years 2016-2019, dt 150 s.
Factors (3 levels each, flow is FROZEN at 0.030 so it is not a factor; the stack anchor takes its place, rule R7):
  R_in 10/25/40 mm | PCM fraction 2/21/40 % | stack anchor bottom/center/top | arrangement single-layer/staggered/radial
Responses are PAIRED against the same-flow water-only tank: g_window, g_annual, d_overheat, t_pcm_max. Screening ranks factors only;
it never selects the final design. Usage: python scripts/c8_l4_taguchi.py <cluster_id> <pcm_rank 1..3>
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.io_utils import get_regime                         # noqa: E402
from src.optimize.anova import L9, anova                    # noqa: E402
from src.optimize.evaluate import evaluate_design           # noqa: E402
from config import STATE                                    # noqa: E402

R_LEVELS = (0.010, 0.025, 0.040)
F_LEVELS = (0.02, 0.21, 0.40)
ANCHORS = ("bottom", "center", "top")
ARR = ("single-layer", "staggered", "radial")
FACTORS = ["R_in_mm", "fraction", "anchor", "arrangement"]
RESP = ["g_window", "g_annual", "d_overheat", "t_pcm_max"]
FLOW = 0.030


def main(cid, rank):
    pcm = get_regime(STATE, cid)["pcm_shortlist"][rank - 1]
    rows = []
    for run, (a, b, c, d) in enumerate(L9, start=1):
        r, f, anc, arr = R_LEVELS[a], F_LEVELS[b], ANCHORS[c], ARR[d]
        res = evaluate_design(cid, pcm, r, f, FLOW, arr, purpose="explore", stack_anchor=anc)
        base = {"run": run, "regime": cid, "pcm": pcm, "R_in_mm": r * 1000, "fraction": f, "anchor": anc, "arrangement": arr}
        if not res["valid"]:
            rows.append({**base, "valid": False, "reason": res["reason"]}); continue
        for y in res["per_year"]:
            rows.append({**base, "N": res["N"], "valid": True, "reason": "", **y})
        print(cid, rank, run, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(f"results/c8_l4_taguchi_r{cid}_p{rank}.csv", index=False)
    ok = df[df.valid]
    if len(ok) >= 20:
        pd.concat([anova(ok, FACTORS, r) for r in RESP]).to_csv(f"results/c8_l4_anova_r{cid}_p{rank}.csv", index=False)
    print("invalid runs:", df[~df.valid][["run", "reason"]].drop_duplicates().to_dict("records"))


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
