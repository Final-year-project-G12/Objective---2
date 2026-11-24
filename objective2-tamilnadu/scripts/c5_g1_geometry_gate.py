"""
scripts/c5_g1_geometry_gate.py   (level L3, step O2-3, gate G1 geometry part)
==============================================================================
Geometry-engine feasibility over the whole common-plant box: R_in 10-40 mm x PCM fraction 2-40 % x 3 arrangements.
Records the rejection code for every infeasible point (no overlap / blocked passage / count mismatch) and the largest
accepted fraction per radius and arrangement. A CAD drawing is not part of this gate.
Writes results/c5_g1_geometry_grid.csv and results/c5_g1_geometry_summary.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.design.constraints import check_design          # noqa: E402
from src.design.space import ARRANGEMENTS, geometry_bounds, to_design, count_range   # noqa: E402
from src.io_utils import load_system_config               # noqa: E402

cfg, bounds = load_system_config(), geometry_bounds()
rows = []
for r in np.round(np.arange(0.010, 0.0401, 0.0025), 4):
    for a in ARRANGEMENTS:
        for f in np.round(np.arange(0.02, 0.4001, 0.02), 3):
            dv = to_design(float(r), float(f), 0.030, a)
            g = check_design(dv, cfg, bounds)
            rows.append({"R_in_mm": r * 1000, "arrangement": a, "fraction_req": f, "N": dv.n_capsule, "valid": bool(g["valid"]),
                         "reason": g.get("reason") or "", "fraction_actual": g.get("pcm_volume_fraction"),
                         "passage": g.get("passage_fraction")})
df = pd.DataFrame(rows)
df.to_csv("results/c5_g1_geometry_grid.csv", index=False)
s = (df.assign(ok=df.valid).groupby(["arrangement", "R_in_mm"]).apply(
    lambda g: pd.Series({"n_points": len(g), "n_valid": int(g.valid.sum()),
                         "max_valid_fraction_req": g[g.valid].fraction_req.max() if g.valid.any() else np.nan,
                         "reasons": ";".join(sorted(set(g[~g.valid].reason)))})).reset_index())
s.to_csv("results/c5_g1_geometry_summary.csv", index=False)
print("valid %d / %d" % (df.valid.sum(), len(df)))
print(df[~df.valid].reason.value_counts().to_string())
print(s.pivot_table(index="R_in_mm", columns="arrangement", values="max_valid_fraction_req").to_string())
print("valid at fraction 0.40:", df[(df.fraction_req == 0.4) & df.valid].groupby("arrangement").size().to_dict())
