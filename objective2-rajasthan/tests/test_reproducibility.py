"""
tests/test_reproducibility.py
================================
Step 1 (fix plan, 2026-09-20 "Objective2 rajasthan fix plan.md") exit check:

Two DOE / search seed derivations must be identical across separate Python
processes. Before the fix, src/doe/generate_cases.py and
src/optimize/search.py derived per-PCM seeds from the builtin hash(str),
which is randomized per-process (PYTHONHASHSEED) unless explicitly seeded --
so the "fixed seed" reproducibility claim silently broke on every fresh
process. _stable_hash() (zlib.crc32) replaces it.

This test spawns two subprocesses with different, explicit PYTHONHASHSEED
values (so it actually exercises the randomization that caused the bug,
rather than accidentally reusing one process's hash seed) and asserts the
derived case tables / search seeds are byte-identical.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

_GEN_CASES_SNIPPET = """
import json
from src.doe.generate_cases import generate_all_cases
cases, manifest = generate_all_cases("rajasthan")
rows = [[c.case_id, c.seed, c.capsule_diameter_m, c.n_capsule, c.flow_rate_kg_s, c.arrangement]
        for c in cases]
print(json.dumps(rows))
"""

_SEARCH_SEED_SNIPPET = """
import json
from src.doe.generate_cases import _stable_hash

SEARCH_SEED = 20260905
pcm_ids = ["RT35", "RT42HC", "OM37", None]
seeds = []
for regime_id in range(3):
    for pcm_id in pcm_ids:
        seed = SEARCH_SEED + regime_id * 97 + (_stable_hash(pcm_id) % 997 if pcm_id else 0)
        seeds.append(seed)
print(json.dumps(seeds))
"""


def _run_snippet(snippet: str, hash_seed: str) -> str:
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = hash_seed
    result = subprocess.run(
        [sys.executable, "-c", snippet],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"snippet failed (rc={result.returncode}):\n{result.stderr}")
    return result.stdout.strip()


def test_doe_case_table_is_process_independent():
    out_a = _run_snippet(_GEN_CASES_SNIPPET, hash_seed="1")
    out_b = _run_snippet(_GEN_CASES_SNIPPET, hash_seed="99999")
    rows_a, rows_b = json.loads(out_a), json.loads(out_b)
    assert rows_a == rows_b, "DOE case table (case_id, seed, design vector) differs across processes"


def test_search_seed_is_process_independent():
    out_a = _run_snippet(_SEARCH_SEED_SNIPPET, hash_seed="1")
    out_b = _run_snippet(_SEARCH_SEED_SNIPPET, hash_seed="99999")
    assert json.loads(out_a) == json.loads(out_b), "search.py per-(regime, PCM) seeds differ across processes"


if __name__ == "__main__":
    test_doe_case_table_is_process_independent()
    test_search_seed_is_process_independent()
    print("OK: DOE case table and search seeds are process-independent.")
