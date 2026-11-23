"""
scripts/g8_build_plain_baseline.py
=====================================
Build the water-only flow grids (17 flows x explore and select years) per regime for the paired baseline.
Usage: python scripts/g8_build_plain_baseline.py <cluster_id>   (explore + select roles only; never test)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.optimize.baseline import build_plain_grid

if __name__ == "__main__":
    cid = int(sys.argv[1])
    for purpose in ("explore", "select"):
        df = build_plain_grid(cid, purpose)
        print(cid, purpose, len(df), "rows", flush=True)
