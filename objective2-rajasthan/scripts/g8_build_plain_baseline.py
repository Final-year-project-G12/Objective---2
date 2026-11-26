"""
scripts/g8_build_plain_baseline.py
=====================================
Rebuild (2026-11-23): exact water-only runs at the fixed flow 0.030 kg/s, per regime, for the explore and select roles at the cheap
(150 s) and full (37.5 s) time steps -> results/plain_baseline_<role>_dt<dt>_r<c>.csv. Never the test or report roles (they are
built inside the locked run). Usage: python scripts/g8_build_plain_baseline.py <cluster_id>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.design.box import CHEAP_DT_S, full_dt      # noqa: E402
from src.optimize.baseline import build_plain       # noqa: E402

if __name__ == "__main__":
    cid = int(sys.argv[1])
    for purpose in ("explore", "select"):
        for dt in (CHEAP_DT_S, full_dt()):
            df = build_plain(cid, purpose, dt)
            print(cid, purpose, dt, len(df), "years", flush=True)
