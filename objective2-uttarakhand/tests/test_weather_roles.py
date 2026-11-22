"""
tests/test_weather_roles.py
==============================
G5 (O2, 2026-10-26; common-plant rebuild roles 2026-11-22) — year-role enforcement, the confirmatory-test lock, gap
handling of the weather inventory, and agreement with the existing regime weather files.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.weather import inventory as inv_mod
from src.weather import roles
from src.io_utils import load_hourly_weather


def test_year_roles_split():
    """Common-plant rebuild, plan rule R3."""
    assert roles.years_for("explore") == [2016, 2017, 2018, 2019]
    assert roles.years_for("select") == [2020, 2021]
    assert roles.years_for("report") == [2022, 2023, 2024, 2025]
    assert roles.years_for("test") == [2006, 2007, 2008, 2009, 2010]
    for y in (2005, 2011, 2015, 2026):
        with pytest.raises(ValueError):
            roles.role_of(y)
    with pytest.raises(ValueError):
        roles.years_for("anything")


def test_purpose_must_match_role():
    with pytest.raises(PermissionError):
        roles.load_point_year("uttarakhand", 0, "UKP_0014", 2018, purpose="select")
    with pytest.raises(PermissionError):
        roles.load_point_year("uttarakhand", 0, "UKP_0014", 2020, purpose="explore")
    with pytest.raises(PermissionError):                         # the legacy test years are now report-only
        roles.load_point_year("uttarakhand", 0, "UKP_0014", 2024, purpose="test")
    assert len(roles.load_point_year("uttarakhand", 0, "UKP_0014", 2018, purpose="explore")) == 8760
    assert len(roles.load_point_year("uttarakhand", 0, "UKP_0014", 2021, purpose="select")) == 8760


def test_test_and_report_years_need_the_lock_and_the_lock_is_single_use(tmp_path, monkeypatch):
    monkeypatch.setattr(roles, "LOCK_DIR", tmp_path)
    monkeypatch.setattr(roles, "_lock_held_by_this_process", False)
    with pytest.raises(roles.HeldOutLockError):
        roles.load_point_year("uttarakhand", 0, "UKP_0014", 2008, purpose="test")
    with pytest.raises(roles.HeldOutLockError):                  # report-only years wait for the frozen, tested design
        roles.load_point_year("uttarakhand", 0, "UKP_0014", 2023, purpose="report")
    path = roles.acquire_test_lock("run-001", "abc123")
    lock = json.loads(path.read_text())
    assert lock["run_id"] == "run-001" and lock["plant_hash"] == roles.plant_hash()
    assert len(roles.load_point_year("uttarakhand", 0, "UKP_0014", 2008, purpose="test")) == 8760
    assert len(roles.load_point_year("uttarakhand", 0, "UKP_0014", 2023, purpose="report")) == 8760
    for p in ("explore", "select", "report"):                     # test years are never available to the other purposes
        with pytest.raises(PermissionError):
            roles.load_point_year("uttarakhand", 0, "UKP_0014", 2010, purpose=p)
    with pytest.raises(roles.HeldOutLockError):                  # second acquisition refused
        roles.acquire_test_lock("run-002", "abc123")
    monkeypatch.setattr(roles, "_lock_held_by_this_process", False)
    with pytest.raises(roles.HeldOutLockError):                  # a fresh process cannot load test years while the lock exists
        roles.load_point_year("uttarakhand", 0, "UKP_0014", 2006, purpose="test")


def test_lock_path_is_keyed_to_the_plant_and_never_the_legacy_lock():
    """Plan section 7.5: the new lock lives under results/locks/ and its name carries the plant hash; the spent legacy lock
    (archived with the 50 L results) is a different file and is never consulted."""
    p = roles.test_lock_path()
    assert p.parent == roles.LOCK_DIR and roles.plant_hash() in p.name
    legacy = REPO_ROOT / "results_legacy_50L_v3" / "held_out_test.lock"
    assert legacy.exists() and p.resolve() != legacy.resolve()
    assert json.loads(legacy.read_text())["run_id"] == "heldout_c75ac0e6fb78"


def test_inventory_meets_acceptance_rule():
    inv = pd.read_csv(roles.INVENTORY_PATH)
    assert len(inv) == 60 and set(inv.cluster_id) == {0, 1, 2, 3}
    assert set(inv.year) == set(range(2006, 2011)) | set(range(2016, 2026))
    assert inv["accepted"].all()
    assert (inv["pct_valid"] >= 98.0).all() and (inv["max_gap_h"] <= 3).all()
    assert inv["hourly_sequence_ok"].all() and (inv["n_hours_after_leap_drop"] == 8760).all()
    assert (inv.role == inv.year.map(roles.role_of)).all()
    for _, r in inv.iterrows():
        assert roles.point_year_path("uttarakhand", r.cluster_id, r.point_id, r.year).exists()


def test_test_years_come_from_the_same_source_as_the_rest():
    """The 2006-2010 raw files were fetched with O1's NASA POWER request (scripts/r2_fetch_test_weather.py): same parameters,
    same UTC time standard, same point coordinates as the 2016-2025 raw files."""
    inv = pd.read_csv(roles.INVENTORY_PATH)
    assert set(inv.time_standard) == {"UTC"}
    raw = REPO_ROOT / "data" / "weather" / "raw_test_2006_2010"
    for pid in inv.point_id.unique():
        d = json.loads((raw / f"power_{pid}_2006.json").read_text())
        assert set(d["properties"]["parameter"]) == {"ALLSKY_SFC_SW_DWN", "CLRSKY_SFC_SW_DWN", "T2M", "RH2M", "WS10M"}
        pts = pd.read_csv(REPO_ROOT / "data" / "objective1" / "cluster_assignments_uttarakhand.csv").set_index("point_id")
        lon, lat = d["geometry"]["coordinates"][:2]
        assert (lat, lon) == (pts.loc[pid, "lat"], pts.loc[pid, "lon"])


def _synthetic_raw(tmp_path, year=2019, gaps=(), missing_frac=0.0):
    idx = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h", tz="UTC")
    keys = [t.strftime("%Y%m%d%H") for t in idx]
    ghi = np.where((idx.hour >= 1) & (idx.hour <= 12), 500.0, 0.0)
    t2m = np.full(len(idx), 25.0)
    for start, length in gaps:
        ghi[start:start + length] = -999.0
    if missing_frac:
        ghi[np.linspace(0, len(idx) - 1, int(missing_frac * len(idx))).astype(int)] = -999.0
    par = {"ALLSKY_SFC_SW_DWN": dict(zip(keys, ghi.tolist())), "CLRSKY_SFC_SW_DWN": dict(zip(keys, (ghi * 0 + 900).tolist())),
           "T2M": dict(zip(keys, t2m.tolist())), "RH2M": dict(zip(keys, [40.0] * len(keys))),
           "WS10M": dict(zip(keys, [2.0] * len(keys)))}
    (tmp_path / f"power_UKP_TEST_{year}.json").write_text(json.dumps(
        {"properties": {"parameter": par}, "header": {"time_standard": "UTC"}}))


def test_short_gap_is_filled_and_flagged(tmp_path):
    _synthetic_raw(tmp_path, gaps=[(1000, 3)])
    row, df = inv_mod.build_point_year(0, "UKP_TEST", 2019, raw_dir=tmp_path, write=False)
    assert row["accepted"] and row["n_filled_hours"] == 3 and row["max_gap_h"] == 3
    assert df["filled"].sum() == 3 and (df["GHI_Wm2"] >= 0).all() and df["GHI_Wm2"].notna().all()


def test_long_gap_rejects_the_point_year_but_keeps_the_row(tmp_path):
    _synthetic_raw(tmp_path, gaps=[(1000, 4)])
    row, df = inv_mod.build_point_year(0, "UKP_TEST", 2019, raw_dir=tmp_path, write=False)
    assert not row["accepted"] and df is None and "gap 4 h" in row["reject_reason"]


def test_below_98_percent_valid_rejects(tmp_path):
    _synthetic_raw(tmp_path, missing_frac=0.03)
    row, df = inv_mod.build_point_year(0, "UKP_TEST", 2019, raw_dir=tmp_path, write=False)
    assert not row["accepted"] and "valid" in row["reject_reason"]


def test_missing_raw_file_is_listed_not_dropped(tmp_path):
    row, df = inv_mod.build_point_year(0, "UKP_NOPE", 2019, raw_dir=tmp_path, write=False)
    assert not row["accepted"] and row["reject_reason"] == "raw file missing" and df is None


@pytest.mark.parametrize("cluster,year,point", [(0, 2016, "UKP_0014"), (1, 2016, "UKP_0029"), (2, 2016, "UKP_0025"),
                                                 (3, 2016, "UKP_0041")])
def test_new_cache_matches_existing_regime_weather_file(cluster, year, point):
    old = load_hourly_weather("uttarakhand", cluster)            # already 29-Feb-free, from the same raw source
    new = pd.read_csv(roles.point_year_path("uttarakhand", cluster, point, year), parse_dates=["timestamp_utc"])
    new = new[~new["local_date"].str.endswith("-02-29")].reset_index(drop=True)
    assert len(old) == len(new) == 8760
    assert (old["timestamp_utc"].to_numpy() == new["timestamp_utc"].to_numpy()).all()
    assert np.allclose(old["GHI_Wm2"], new["GHI_Wm2"]) and np.allclose(old["T_amb_C"], new["T_amb_C"])
    assert (old["local_hour"].to_numpy() == new["local_hour"].to_numpy()).all()
