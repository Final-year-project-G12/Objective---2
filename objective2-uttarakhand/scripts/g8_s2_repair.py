"""
scripts/g8_s2_repair.py
==========================
G8 / S2 - re-run the DOE rows whose status is 'error' (all four were MemoryError from nine parallel jobs plus other
memory use, not design-related) with the SAME Sobol points, and replace them in place. Rows that were rejected by the
exact geometry gate are left as they are. Usage: python scripts/g8_s2_repair.py
"""

import glob
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.g8_s2_doe import design_from_u, sobol_points  # noqa: E402
from src.io_utils import get_regime  # noqa: E402
from src.optimize.evaluate import evaluate_design, flatten  # noqa: E402


def main():
    U = sobol_points()
    for f in sorted(glob.glob("results/g8_s2_r*_p*.csv")):
        df = pd.read_csv(f)
        bad = df.index[df.status == "error"].tolist()
        if not bad:
            continue
        cid, rank = (int(x) for x in Path(f).stem.replace("g8_s2_r", "").split("_p"))
        pcm = get_regime("uttarakhand", cid)["pcm_shortlist"][rank - 1]
        for i in bad:
            did = int(df.loc[i, "design_id"])
            u = U[did]
            r, fr, q, arr = design_from_u(u)
            res = evaluate_design(cid, pcm, r, fr, q, arr, purpose="explore")
            row = flatten(res)
            row["status"] = "ok" if res["valid"] else "geometry_rejected"
            for yr in res.get("per_year", []):
                for k in ("g_window", "g_annual", "g_useful", "d_overheat", "t_pcm_max"):
                    row[f"{k}_{yr['year']}"] = yr[k]
            row.update({"design_id": did, "u0": u[0], "u1": u[1], "u2": u[2], "u3": u[3], "runtime_s": float("nan")})
            for c in df.columns:
                df.loc[i, c] = row.get(c, float("nan")) if c in row else float("nan")
            print("repaired", Path(f).name, did, row["status"], flush=True)
        df.to_csv(f, index=False)


if __name__ == "__main__":
    main()
