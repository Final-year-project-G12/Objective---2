"""
src/io_utils.py
================
Shared config/data loaders used by every Phase 1-4 module. Centralized here
so geometry.py, tank_model.py, gates.py etc. never hand-roll their own YAML
or CSV parsing, and so a shared-config change is visible in one place.

Nothing here is state-specific except the `state` argument you pass in.
"""

from pathlib import Path
import functools

import yaml
import pandas as pd

from config import BASE_DIR, CONFIGS_DIR, DATA_DIR

STATES_DIR = CONFIGS_DIR / "states"


def _load_yaml(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@functools.lru_cache(maxsize=None)
def load_system_config():
    """FROZEN shared config — collector/tank/PCM-integration/pump/safety/solver."""
    return _load_yaml(CONFIGS_DIR / "system_config_shared.yaml")


@functools.lru_cache(maxsize=None)
def load_design_bounds():
    """FROZEN shared design-space bounds."""
    return _load_yaml(CONFIGS_DIR / "design_bounds_shared.yaml")


@functools.lru_cache(maxsize=None)
def load_state_config(state: str):
    """Per-state config (Phase 1 output) — the only state-varying input."""
    return _load_yaml(STATES_DIR / f"{state}.yaml")


def get_regime(state: str, cluster_id: int) -> dict:
    """One regime's entry from states/<state>.yaml (weather paths, Tm_target,
    T_mains, PCM shortlist names)."""
    cfg = load_state_config(state)
    for r in cfg["regimes"]:
        if int(r["cluster_id"]) == int(cluster_id):
            return r
    raise KeyError(f"cluster_id {cluster_id} not found in states/{state}.yaml")


def list_regimes(state: str):
    return [r["cluster_id"] for r in load_state_config(state)["regimes"]]


@functools.lru_cache(maxsize=None)
def load_pcm_database(state: str) -> pd.DataFrame:
    cfg = load_state_config(state)
    path = BASE_DIR / cfg["pcm_database_file"]
    return pd.read_csv(path)


def get_pcm_properties(state: str, pcm_name: str) -> dict:
    """Full property record for one PCM by name, from the frozen Objective 1
    database (data/objective1/pcm_database_<state>.csv). Never invents a
    property Objective 1 didn't report."""
    df = load_pcm_database(state)
    row = df[df["name"] == pcm_name]
    if row.empty:
        raise KeyError(f"PCM '{pcm_name}' not found in pcm_database for state={state}")
    return row.iloc[0].to_dict()


def load_hourly_weather(state: str, cluster_id: int) -> pd.DataFrame:
    regime = get_regime(state, cluster_id)
    path = BASE_DIR / regime["weather_hourly"]
    df = pd.read_csv(path, parse_dates=["timestamp_utc"])
    return df.sort_values("timestamp_utc").reset_index(drop=True)


def load_demand_profile(state: str) -> pd.DataFrame:
    cfg = load_state_config(state)
    path = BASE_DIR / cfg["demand_profile"]["file"]
    return pd.read_csv(path)
