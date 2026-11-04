"""
scripts/tn_rebuild_select_baseline.py
========================================
Rebuild ONLY the `select`-role water-only flow grids, at the confirmation
timestep.

Why this exists instead of just re-running her
`g8_build_plain_baseline.py`: that script rebuilds explore AND select for a
regime. After G2 (2026-10-29) the two roles no longer share a timestep --
explore stays at the 150 s search step, select moves to the 37.5 s
confirmation step (see src/io_utils.dt_for). The explore grids are already
correct and cost 5 years x 17 flows each to redo, so there is no reason to
touch them.

`build_plain_grid` reads the step from `dt_for(purpose)` itself, so nothing
is passed in here -- this file only decides WHICH grids get rebuilt, and
runs the three regimes concurrently.

Run:  python scripts/tn_rebuild_select_baseline.py
"""

import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PURPOSE = "select"


def _one(cid):
    from src.io_utils import dt_for
    from src.optimize.baseline import build_plain_grid, grid_path
    t0 = time.time()
    df = build_plain_grid(cid, PURPOSE)
    return (cid, len(df), dt_for(PURPOSE), grid_path(PURPOSE, cid).name,
            (time.time() - t0) / 60)


def main():
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                "NUMEXPR_NUM_THREADS"):
        os.environ.setdefault(var, "1")

    from src.io_utils import dt_for
    print(f"rebuilding '{PURPOSE}' plain baselines at dt={dt_for(PURPOSE)} s "
          f"(explore grids left alone at dt={dt_for('explore')} s)", flush=True)

    t0 = time.time()
    with ProcessPoolExecutor(max_workers=3) as ex:
        for cid, n, dt, name, mins in ex.map(_one, (0, 1, 2)):
            print(f"  r{cid}  {n:3d} rows  dt={dt} s  -> {name}  ({mins:.1f} min)",
                  flush=True)
    print(f"done in {(time.time()-t0)/60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
