"""
tests/test_demand_timing.py
==============================
G1 (O2, 2026-10-26): the demand profile is defined in LOCAL clock
hours (07:00 / 19:00 peaks), but tank_model.py used to index it with the UTC
hour of the weather timestamp -- which put the 46 L "evening" draw at ~00:30
local. These tests pin the fix: the draw must follow the local clock, with the
expectation computed independently from timestamp_utc -> Asia/Kolkata, not
from the `local_hour` column the simulator reads.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.design.schema import DesignVector
from src.io_utils import load_demand_profile, load_hourly_weather
from src.simulation import run_case as run_case_module
from src.simulation.demand_profile import load_demand_model
from src.simulation.tank_model import _demand_hour_of_day
from config import STATE

CLUSTER = 0
PEAK_HOURS_LOCAL = (7, 19)   # draw peaks of demand_profile_rajasthan.csv


def _ist_hour(ts: pd.Series) -> pd.Series:
    return ts.dt.tz_convert("Asia/Kolkata").dt.hour


def test_local_hour_column_matches_ist_clock():
    w = load_hourly_weather(STATE, CLUSTER)
    assert (w["local_hour"] == _ist_hour(w["timestamp_utc"])).all()


def test_peak_draw_lands_at_local_0700_and_1900():
    w = load_hourly_weather(STATE, CLUSTER).iloc[:24 * 14]
    demand = load_demand_model(load_demand_profile(STATE))
    draw = pd.Series([demand.draw_mass_kg_for_hour(_demand_hour_of_day(w.iloc[i], i))
                      for i in range(len(w))], index=w.index)
    ist = _ist_hour(w["timestamp_utc"])
    # ASSAM PORT: Assam's profile is two equal point draws (50 L at 07:00 and 50 L at 19:00 local; ASSAM_DEMAND_VALIDATION.md),
    # not Tamil Nadu's Gaussian morning and larger evening. The invariant is WHERE the draws land on the local clock.
    by_hour = draw.groupby(ist).mean()
    assert set(by_hour.index[by_hour > 0]) == {7, 19}, "draw must occur only at local 07:00 and 19:00"
    assert by_hour[7] == pytest.approx(by_hour[19], rel=1e-6), "the two draws are meant to be equal"
    assert by_hour[7] > 0


def test_utc_only_frame_is_refused():
    row = pd.Series({"timestamp_utc": pd.Timestamp("2025-01-01 00:00", tz="UTC"), "GHI_Wm2": 0.0})
    with pytest.raises(ValueError):
        _demand_hour_of_day(row, 0)


def test_run_case_records_local_hour(monkeypatch):
    w = load_hourly_weather(STATE, CLUSTER).iloc[:72].copy()
    monkeypatch.setattr(run_case_module, "load_hourly_weather", lambda s, c: w)
    dv = DesignVector(capsule_diameter_m=0.05, n_capsule=16, flow_rate_kg_s=0.03,
                      capsule_arrangement="staggered")
    out = run_case_module.run_case(STATE, CLUSTER, None, dv, record_hourly=True)
    hourly = out["hourly"]
    assert len(hourly) == 72
    assert (hourly["hour_of_day"].to_numpy() == _ist_hour(w["timestamp_utc"]).to_numpy()).all()
