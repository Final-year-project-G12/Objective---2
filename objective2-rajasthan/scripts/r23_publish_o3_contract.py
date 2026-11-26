"""Copy the Rajasthan Objective 3 contract into objective3/ with its sha256 (run after the handoff stage)."""
import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
f = "obj3_environment_contract_rajasthan_common100L.json"
shutil.copy2(ROOT / "results" / f, ROOT / "objective3" / f)
h = hashlib.sha256((ROOT / "objective3" / f).read_bytes()).hexdigest()
(ROOT / "objective3" / (f + ".sha256")).write_text(f"{h}  {f}\n")
print("published", f, h)
