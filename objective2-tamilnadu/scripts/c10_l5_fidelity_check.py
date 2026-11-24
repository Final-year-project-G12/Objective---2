"""
scripts/c10_l5_fidelity_check.py   (level L5, multi-fidelity rank agreement)
==============================================================================
Re-runs the top-8 CHEAP-fidelity finalists of each (regime, PCM) pair at FULL fidelity (dt 37.5 s, years 2017-2018, all three anchors)
and tests the rule registered BEFORE this run (configs/l5_fidelity_preregistration.json): Spearman(cheap, full) >= 0.8 and
max |gain difference| <= 0.5 kWh, in at least 7 of 9 pairs. The like-for-like comparison is on the SAME year (2017) so only the
fidelity (dt) differs; the 2018 value and the 2-year mean are reported too. Usage: python scripts/c10_l5_fidelity_check.py <cluster_id>
-> results/c10_l5_fidelity_r<c>.csv
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.optimize.evaluate import evaluate_design             # noqa: E402

PRE = json.loads(Path("configs/l5_fidelity_preregistration.json").read_text())
ANCHORS, YEARS, DT, TOP = PRE["full_fidelity"]["anchors"], PRE["full_fidelity"]["years"], PRE["full_fidelity"]["dt_s"], 8


def main(cid, ranks=(1, 2, 3)):
    rows = []
    for rank in ranks:
        d = pd.read_csv(f"results/c9_l5_doe_r{cid}_p{rank}.csv")
        d = d[d.valid.astype(str) == "True"].sort_values("g_window_mean", ascending=False).head(TOP)
        for _, r in d.iterrows():
            res = {a: evaluate_design(cid, r.pcm, r.R_in_m, r.fraction_req, 0.030, r.arrangement, years=YEARS, stack_anchor=a, dt_s=DT) for a in ANCHORS}
            g17 = np.mean([[y["g_window"] for y in res[a]["per_year"] if y["year"] == 2017][0] for a in ANCHORS])
            g18 = np.mean([[y["g_window"] for y in res[a]["per_year"] if y["year"] == 2018][0] for a in ANCHORS])
            rows.append({"regime": cid, "pair": f"r{cid}_p{rank}", "pcm": r.pcm, "design_id": int(r.design_id), "R_in_m": r.R_in_m,
                         "fraction_req": r.fraction_req, "arrangement": r.arrangement, "cheap_g_window_mean": r.g_window_mean,
                         "full_g_window_2017": g17, "full_g_window_2018": g18, "full_g_window_2yr": (g17 + g18) / 2})
            print(cid, rank, int(r.design_id), flush=True)
    pd.DataFrame(rows).to_csv(f"results/c10_l5_fidelity_r{cid}_p{ranks[0]}.csv" if len(ranks) == 1 else f"results/c10_l5_fidelity_r{cid}.csv", index=False)


if __name__ == "__main__":
    main(int(sys.argv[1]), (int(sys.argv[2]),) if len(sys.argv) > 2 else (1, 2, 3))
