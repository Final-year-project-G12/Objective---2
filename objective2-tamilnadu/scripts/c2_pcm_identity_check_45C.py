"""
scripts/c2_pcm_identity_check_45C.py   (level L1 follow-up, Option B check)
===========================================================================
Option B keeps O1's shortlist (Tm 54-58 C, sized by O1 for a 60 C service / 67 C target). O2 now serves at 45 C. A re-rank at
45 C would move O1's target to ~52 C, so lower-melting PCMs could win. Instead of guessing, SIMULATE: one fixed mid design
(R_in 25 mm, 30 % fraction, 0.030 kg/s, staggered) per regime for the three O1 PCMs and every database PCM with Tm 44-59 C
(known conductivity), on 2 explore years, and compare the paired gain at 45 C delivery (g_window) and overheat.
This ranks PCM identity under the common plant; it is a screen, not a design optimum (each PCM would have its own optimum).
Usage: python scripts/c2_pcm_identity_check_45C.py <cluster_id>
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import io_utils                       # noqa: E402
from src.optimize import evaluate              # noqa: E402
from config import STATE                       # noqa: E402

YEARS = [2017, 2018]
DESIGN = dict(r_in_m=0.025, fraction=0.30, flow=0.030, arrangement="staggered")


def main(cid):
    db = io_utils.load_pcm_database(STATE)
    o1 = set(io_utils.o1_top3(STATE)[cid])
    cand = db[(db.Tm_C.between(44, 59.5)) & db.TC_W_mK.notna()].copy()
    names = list(dict.fromkeys(list(o1) + cand.name.tolist()))
    rows = []
    for n in names:
        try:
            r = evaluate.evaluate_design(cid, n, purpose="explore", years=YEARS, **DESIGN)
        except Exception as e:                                          # noqa: BLE001
            rows.append({"cluster": cid, "pcm": n, "error": repr(e)[:120]}); continue
        row = evaluate.flatten(r)
        row["in_O1_shortlist"] = n in o1
        row["Tm_C"] = float(db.loc[db.name == n, "Tm_C"].iloc[0])
        row["latent_kJ_kg"] = float(db.loc[db.name == n, "latent_heat_kJ_kg"].iloc[0])
        rows.append(row)
        print(cid, n, round(row.get("g_window", float("nan")), 1), flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(Path("results") / f"c2_pcm_identity_45C_r{cid}.csv", index=False)


if __name__ == "__main__":
    main(int(sys.argv[1]))
