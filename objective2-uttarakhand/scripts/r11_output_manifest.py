"""
scripts/r11_output_manifest.py  -  plan rule R20: hash every output file of the rebuild
==========================================================================================
Writes results/o2_output_manifest.json: SHA-256 and size of every file under results/ (the rebuild namespace; the manifest itself
excluded), plus the hashes of the code that produced them (src/, scripts/, matlab/, configs/, pipeline.py), the plant hash, the
O2 test lock id and the git commit at generation. The legacy archive (results_legacy_50L_v3/) is listed by its own hash summary only.
Usage: python scripts/r11_output_manifest.py
"""
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.weather import roles     # noqa: E402

OUT = ROOT / "results" / "o2_output_manifest.json"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def tree(base, patterns):
    files = sorted({f for pat in patterns for f in base.glob(pat) if f.is_file() and "__pycache__" not in f.parts and f != OUT})
    return {str(f.relative_to(ROOT)).replace("\\", "/"): {"sha256": sha(f), "bytes": f.stat().st_size} for f in files}


def main():
    outputs = tree(ROOT / "results", ["**/*"])
    code = tree(ROOT, ["src/**/*.py", "scripts/**/*.py", "matlab/**/*.m", "configs/**/*.yaml", "pipeline.py", "run_all_uttarakhand.py",
                       "config.py", "jobs/*"])
    legacy = tree(ROOT / "results_legacy_50L_v3", ["**/*"])
    lock = roles.test_lock_path()
    m = {"plan_rule": "R20 (hash the config, kernel, weather, demand, contract and every output file)",
         "generated_utc": datetime.now(timezone.utc).isoformat(),
         "git_commit_at_generation": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
         "plant_hash": roles.plant_hash(), "o2_test_run_id": json.loads(lock.read_text())["run_id"] if lock.exists() else None,
         "n_output_files": len(outputs), "outputs": outputs, "code_and_configs": code,
         "legacy_archive_summary": {"n_files": len(legacy),
                                    "sha256_of_listing": hashlib.sha256(json.dumps(legacy, sort_keys=True).encode()).hexdigest()}}
    OUT.write_text(json.dumps(m, indent=1), encoding="utf-8")
    print("wrote", OUT, "|", len(outputs), "outputs,", len(code), "code/config files,", len(legacy), "legacy files")


if __name__ == "__main__":
    main()
