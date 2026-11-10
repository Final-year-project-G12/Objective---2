"""B5 port (2026-11-10): Assam's tank model indexes the demand profile by local_hour, refuses a UTC frame without it, and has an optional shield."""
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from src.simulation.tank_model import _demand_hour_of_day
from src.design.schema import DesignVector
from src.simulation.run_case import run_case

DV = DesignVector(capsule_diameter_m=0.05, n_capsule=14, flow_rate_kg_s=0.030)


def test_local_hour_is_used_and_utc_without_it_is_refused():
    assert _demand_hour_of_day(pd.Series({"local_hour": 7, "timestamp_utc": pd.Timestamp("2020-01-01 01:30")}), 5) == 7
    with pytest.raises(ValueError):
        _demand_hour_of_day(pd.Series({"timestamp_utc": pd.Timestamp("2020-01-01 01:30")}), 5)
    assert _demand_hour_of_day(pd.Series({"GHI_Wm2": 1.0}), 29) == 5


def test_shield_is_off_by_default_and_stops_safety_violations_when_on():
    base = run_case("assam", 0, "savE® OM48", DV, record_hourly=False)["metrics"]
    shielded = run_case("assam", 0, "savE® OM48", DV, record_hourly=False, system_config_overrides={"safety_shield": {"enabled": True}})["metrics"]
    assert base["n_shield_water_activations"] == 0 and base["n_shield_pcm_activations"] == 0
    assert shielded["n_shield_water_activations"] > 0
    assert shielded["n_safety_violations"] == 0
    assert shielded["max_water_temp_C"] < base["max_water_temp_C"]
    assert abs(shielded["residual_pct_of_collector"]) < 1e-6
