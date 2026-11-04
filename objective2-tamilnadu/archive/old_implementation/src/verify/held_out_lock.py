"""
src/verify/held_out_lock.py
==============================
The one-shot held-out test on the TEST years (2011-2015), with an atomic
single-use lock file.

Her report: "The held-out test uses an atomic single-use lock file
(results/held_out_test.lock, run id heldout_...). A second run raises
HeldOutLockError. This is a guard rail in code, not a security boundary,
and the lock must never be deleted to retry."

WHY A LOCK AT ALL. A held-out test is only held out once. If you can re-run
it after seeing the answer, it silently becomes a validation set you tuned
against, and the number it reports stops meaning what it claims. The lock
makes the single-use property a property of the CODE rather than of
someone's discipline. It is a guard rail, not security: anyone can delete
the file. The point is that deleting it is a deliberate, visible act.

The lock records a SHA-256 fingerprint of exactly what was tested -- the
designs, the years, the config versions and the model settings -- so a
later reader can tell whether a claimed held-out result corresponds to the
designs actually in the report, rather than to a different set run later.
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import RESULTS_DIR
from src.io_utils import load_design_bounds, load_system_config
from src.parallel.runner import SimTask, run_tasks_parallel
from src.weather.fetch_multiyear_weather import YEAR_ROLES

TEST_YEARS = sorted(y for y, role in YEAR_ROLES.items() if role == "test")
LOCK_NAME = "held_out_test.lock"


class HeldOutLockError(RuntimeError):
    pass


def _fingerprint(designs: pd.DataFrame, years, n_nodes, timestep_s) -> str:
    payload = {
        "designs": designs.sort_index(axis=1).to_dict(orient="records"),
        "years": list(years),
        "n_nodes": n_nodes,
        "timestep_s": timestep_s,
        "design_bounds_version": load_design_bounds().get("version"),
        "safety": load_system_config()["safety"],
        "tank": load_system_config()["tank"],
    }
    blob = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _acquire(lock_path: Path, fingerprint: str, years) -> dict:
    """Atomic create-or-fail. O_EXCL is the whole mechanism: if the file
    already exists the create fails, and no race can produce two winners."""
    record = {
        "run_id": f"heldout_{fingerprint[:12]}",
        "fingerprint_sha256": fingerprint,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "test_years": list(years),
        "note": "Single-use. Do not delete to retry -- a re-run would make this "
                 "a tuned validation set, not a held-out test.",
    }
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        existing = json.loads(lock_path.read_text(encoding="utf-8"))
        raise HeldOutLockError(
            f"held-out test already run: run_id={existing.get('run_id')} at "
            f"{existing.get('created_utc')} (fingerprint "
            f"{existing.get('fingerprint_sha256', '')[:12]}...). "
            f"{'The designs match, so the existing result still applies.' if existing.get('fingerprint_sha256') == fingerprint else 'The designs DIFFER from that run -- a new held-out test would need new test years, not a deleted lock.'}"
        )
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2)
    return record


def run_held_out_test(designs: pd.DataFrame, state: str = "tamilnadu",
                       years=tuple(TEST_YEARS), n_nodes: int = 10,
                       timestep_s: float = 150.0, out_dir: Path = None):
    """Simulates the chosen designs on the test years, ONCE.

    `designs` must be the final chosen design per regime -- one row each,
    with pcm_name / capsule_diameter_m / n_capsule / flow_rate_kg_s /
    arrangement / cluster_id.
    """
    for y in years:
        if YEAR_ROLES.get(y) != "test":
            raise ValueError(f"year {y} is role {YEAR_ROLES.get(y)!r}, not 'test'")

    out_dir = out_dir or (RESULTS_DIR / state)
    fingerprint = _fingerprint(designs, years, n_nodes, timestep_s)
    record = _acquire(out_dir / LOCK_NAME, fingerprint, years)

    tasks = []
    for _, d in designs.iterrows():
        for y in years:
            tasks.append(SimTask(
                task_id=f"heldout_c{int(d['cluster_id'])}_y{y}", state=state,
                cluster_id=int(d["cluster_id"]), pcm_name=d["pcm_name"],
                capsule_diameter_m=float(d["capsule_diameter_m"]),
                n_capsule=int(d["n_capsule"]),
                flow_rate_kg_s=float(d["flow_rate_kg_s"]),
                arrangement=d["arrangement"], model="multinode",
                n_nodes=n_nodes, timestep_s=timestep_s, year=y, paired_plain=True))

    df = run_tasks_parallel(tasks, chunksize=1, progress_every=max(1, len(tasks) // 10),
                            label="held-out")
    df["run_id"] = record["run_id"]
    df["fingerprint_sha256"] = fingerprint
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "held_out_test_results.csv", index=False)
    return df, record
