"""Helper: run DOE pair <rank> for regime <cid> once pair <wait_rank> of that regime has finished (128 rows). Usage: _chain_doe.py <cid> <rank> <wait_rank>"""
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

root = Path(__file__).resolve().parent.parent
cid, rank, wait = sys.argv[1:4]
f = root / f"results/c9_l5_doe_r{cid}_p{wait}.csv"
while True:
    try:
        if f.exists() and len(pd.read_csv(f)) >= 128:
            break
    except Exception:
        pass
    time.sleep(60)
subprocess.run([sys.executable, "scripts/c9_l5_doe.py", cid, rank], cwd=root)
