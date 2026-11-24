"""
src/weather/roles.py
=======================
Common-plant rebuild (2026-11-20), rule R3 of docs/plan/Unified_Objectives_2_3_Rebuild_Plan_Four_States_REVISED_v1.docx.
Enforces, in code, what each weather year may be used for:

    2016-2019  "explore"  screening, DOE, surrogate training, active learning, dense grid
    2020-2021  "select"   the funnel chooses the final O2 design
    2006-2010  "test"     the single CONFIRMATORY test, run exactly ONCE, after the funnel is frozen
    2022-2025  "report"   report-only recent-climate check after the O2 lock (2024-2025 are project-exposed); never used to choose
    2011-2015  "legacy"   spent as the old held-out test; accepted for NO purpose in the common protocol

`load_point_year(..., purpose=...)` refuses a year whose role differs from the stated purpose. The test years
additionally require `acquire_test_lock()`, which atomically creates
results/common100L_<hardware_hash>/held_out_test.lock and refuses if it exists. The lock path is keyed to a hash of the
plant / design-space / state configs, so a change of hardware or physics opens a NEW namespace instead of reusing (or
being blocked by) a spent lock; the old results/held_out_test.lock belongs to the legacy plant and is never read here.
This is a guard rail inside the codebase, not a security boundary.
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
LEGACY_LOCK_PATH = BASE_DIR / "results" / "held_out_test.lock"       # old hardware: archived, never read or written

YEAR_ROLES = {**{y: "test" for y in range(2006, 2011)},
              **{y: "legacy" for y in range(2011, 2016)},
              **{y: "explore" for y in range(2016, 2020)},
              **{y: "select" for y in range(2020, 2022)},
              **{y: "report" for y in range(2022, 2026)}}
PURPOSES = ("explore", "select", "test", "report")
_HARDWARE_FILES = ("configs/system_config_shared.yaml", "configs/design_space.yaml", "configs/states/tamilnadu.yaml",
                   "data/demand/demand_profile_tamilnadu.csv")


def hardware_hash() -> str:
    """12-hex SHA-256 of the files that define the plant, design box, state inputs and demand."""
    h = hashlib.sha256()
    for rel in _HARDWARE_FILES:
        h.update(rel.encode())
        h.update((BASE_DIR / rel).read_bytes())
    return h.hexdigest()[:12]


def lock_path() -> Path:
    return BASE_DIR / "results" / f"common100L_{hardware_hash()}" / "held_out_test.lock"


TEST_LOCK_PATH = lock_path()


class HeldOutLockError(PermissionError):
    pass


_lock_held_by_this_process = False


def role_of(year: int) -> str:
    try:
        return YEAR_ROLES[int(year)]
    except KeyError:
        raise ValueError(f"year {year} is outside the 2006-2025 record") from None


def years_for(purpose: str):
    if purpose not in PURPOSES:
        raise ValueError(f"purpose must be one of {PURPOSES}, got {purpose!r}")
    return [y for y, r in YEAR_ROLES.items() if r == purpose]


def acquire_test_lock(run_id: str, selection_fingerprint: str) -> Path:
    """Create the held-out lock (atomic, exclusive). Call once, immediately before the
    single held-out evaluation; `selection_fingerprint` ties it to the frozen selection."""
    global _lock_held_by_this_process
    if TEST_LOCK_PATH.resolve() == LEGACY_LOCK_PATH.resolve():
        raise HeldOutLockError("refusing to use the legacy lock path")
    TEST_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(TEST_LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise HeldOutLockError(
            f"held-out 2006-2010 confirmatory test already run for this hardware hash (lock {TEST_LOCK_PATH}); it may be run exactly once. "
            f"Contents: {TEST_LOCK_PATH.read_text()[:300]}") from None
    with os.fdopen(fd, "w") as fh:
        json.dump({"run_id": run_id, "selection_fingerprint": selection_fingerprint,
                   "utc": datetime.now(timezone.utc).isoformat()}, fh)
    _lock_held_by_this_process = True
    return TEST_LOCK_PATH


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
    path = point_year_path(state, cluster_id, point_id, year)
    if not path.exists():
        raise FileNotFoundError(f"{path} missing -- point-year rejected or not built (see weather_inventory.csv)")
    df = pd.read_csv(path, parse_dates=["timestamp_utc"])
    return drop_leap_day(df.sort_values("timestamp_utc").reset_index(drop=True))
