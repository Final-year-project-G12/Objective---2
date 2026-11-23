"""
scripts/g8_s2_repair.py
==========================
G8 / S2 - re-run DOE rows whose status is 'error' (e.g. MemoryError from too many parallel jobs) with the SAME Sobol points and
replace them in place. Geometry-rejected rows are left as they are. Usage: python scripts/g8_s2_repair.py
"""
import glob
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.g8_s2_doe import evaluate_u, sobol_points  # noqa: E402
from src.io_utils import get_regime                     # noqa: E402


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
            row = evaluate_u(cid, pcm, U[did])
            row.update({"design_id": did, "u0": U[did][0], "u1": U[did][1], "u2": U[did][2], "runtime_s": float("nan")})
            for c in set(row) - set(df.columns):
                df[c] = float("nan")
            for c in df.columns:
                df.loc[i, c] = row.get(c, float("nan"))
            print("repaired", Path(f).name, did, row["status"], flush=True)
        df.to_csv(f, index=False)


if __name__ == "__main__":
    main()
