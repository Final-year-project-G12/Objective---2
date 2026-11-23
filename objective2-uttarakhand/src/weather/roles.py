"""
src/weather/roles.py
=======================
What each weather year may be used for, enforced in code. Common-plant rebuild (Unified Rebuild Plan, rule R3, adopted 2026-11-22):

    2016-2019  "explore"  screening, DOE, surrogate training, active learning, dense grid, ablations
    2020-2021  "select"   the frozen funnel chooses the final design
    2022-2023  "report"   report-only recent-climate check, AFTER the O2 test lock (no O2 choice may depend on them)
    2024-2025  "report"   report-only, after the O2 test lock; project-exposed (they were the legacy 50 L held-out test)
    2006-2010  "test"     the one-shot confirmatory test, run exactly ONCE under the lock

`load_point_year(..., purpose=...)` refuses a year whose role differs from the stated purpose. Test years additionally need
`acquire_test_lock()` in the same process; report years need the test lock to exist already (the design is frozen).

The lock path is keyed to the plant hash (SHA-256 of configs/system_config_shared.yaml, configs/design_space.yaml and the state yaml,
first 12 hex digits): results/locks/o2_test_<hash>.lock. A change to the plant or design space gives a new path, so a spent lock can
never be relabelled, and the legacy lock in results_legacy_50L_v3/ is never read. This is a guard rail inside the codebase, not a
security boundary; deleting a lock to re-run is a deliberate act that must be logged in docs/PROGRESS.md.

Legacy (50 L run, archived): 2016-2020 explore, 2021-2023 select, 2024-2025 test (lock heldout_c75ac0e6fb78, spent).
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.io_utils import BASE_DIR, drop_leap_day

WEATHER_POINT_YEARS_DIR = BASE_DIR / "data" / "weather/point_years"
INVENTORY_PATH = WEATHER_POINT_YEARS_DIR / "weather_inventory.csv"
LOCK_DIR = BASE_DIR / "results" / "locks"
PLANT_FILES = [BASE_DIR / "configs" / "system_config_shared.yaml", BASE_DIR / "configs" / "design_space.yaml",
               BASE_DIR / "configs" / "states" / "uttarakhand.yaml", BASE_DIR / "data" / "demand" / "demand_profile_uttarakhand.csv"]

YEAR_ROLES = {**{y: "test" for y in range(2006, 2011)},
              **{y: "explore" for y in range(2016, 2020)},
              **{y: "select" for y in (2020, 2021)},
              **{y: "report" for y in range(2022, 2026)}}
PURPOSES = ("explore", "select", "test", "report")


class HeldOutLockError(PermissionError):
    pass


_lock_held_by_this_process = False


def plant_hash() -> str:
    h = hashlib.sha256()
    for p in PLANT_FILES:
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()[:12]


def test_lock_path() -> Path:
    return LOCK_DIR / f"o2_test_{plant_hash()}.lock"


def role_of(year: int) -> str:
    try:
        return YEAR_ROLES[int(year)]
    except KeyError:
        raise ValueError(f"year {year} has no role (roles cover 2006-2010 and 2016-2025)") from None


def years_for(purpose: str):
    if purpose not in PURPOSES:
        raise ValueError(f"purpose must be one of {PURPOSES}, got {purpose!r}")
    return sorted(y for y, r in YEAR_ROLES.items() if r == purpose)


def acquire_test_lock(run_id: str, selection_fingerprint: str) -> Path:
    """Create the confirmatory-test lock (atomic, exclusive). Call once, immediately before the single 2006-2010 evaluation;
    `selection_fingerprint` ties it to the frozen selection."""
    global _lock_held_by_this_process
    path = test_lock_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise HeldOutLockError(f"the 2006-2010 test for this plant was already run (lock {path}); it may be run exactly once. "
                               f"Contents: {path.read_text()[:300]}") from None
    with os.fdopen(fd, "w") as fh:
        json.dump({"run_id": run_id, "selection_fingerprint": selection_fingerprint, "plant_hash": plant_hash(),
                   "utc": datetime.now(timezone.utc).isoformat()}, fh)
    _lock_held_by_this_process = True
    return path


def join_test_lock(run_id: str) -> Path:
    """For a worker process of the ONE locked test run: allowed only if the lock exists and names this run_id (the parent created it
    with acquire_test_lock in the same run). It never creates a lock, so it cannot be used to start a second test."""
    global _lock_held_by_this_process
    path = test_lock_path()
    if not path.exists():
        raise HeldOutLockError("no test lock: the test run has not been started (acquire_test_lock)")
    lock = json.loads(path.read_text())
    if lock.get("run_id") != run_id:
        raise HeldOutLockError(f"the lock belongs to run {lock.get('run_id')!r}, not {run_id!r}")
    _lock_held_by_this_process = True
    return path


def point_year_path(state: str, cluster_id: int, point_id: str, year: int) -> Path:
    return WEATHER_POINT_YEARS_DIR / state / f"cluster{cluster_id}_{point_id}_{year}.csv"


def load_point_year(state: str, cluster_id: int, point_id: str, year: int, purpose: str) -> pd.DataFrame:
    """Hourly weather for one accepted point-year, 29 Feb removed (8760 h)."""
    if purpose not in PURPOSES:
        raise ValueError(f"purpose must be one of {PURPOSES}, got {purpose!r}")
    role = role_of(year)
    if role != purpose:
        raise PermissionError(f"year {year} is a '{role}' year and may not be used for '{purpose}'")
    if role == "test" and not _lock_held_by_this_process:
        raise HeldOutLockError("test years can only be loaded after acquire_test_lock() in the same process")
    if role == "report" and not test_lock_path().exists():
        raise HeldOutLockError("report-only years can only be loaded after the O2 design is frozen and tested (lock missing)")
    path = point_year_path(state, cluster_id, point_id, year)
    if not path.exists():
        raise FileNotFoundError(f"{path} missing -- point-year rejected or not built (see weather_inventory.csv)")
    df = pd.read_csv(path, parse_dates=["timestamp_utc"])
    return drop_leap_day(df.sort_values("timestamp_utc").reset_index(drop=True))
