"""
tests/test_weather_roles.py
==============================
G5 (O2, 2026-10-26) — year-role enforcement, the held-out-test lock, gap
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
    assert roles.years_for("explore") == [2016, 2017, 2018, 2019, 2020]
    assert roles.years_for("select") == [2021, 2022, 2023]
    assert roles.years_for("test") == [2024, 2025]
    with pytest.raises(ValueError):
        roles.role_of(2015)
    with pytest.raises(ValueError):
        roles.years_for("anything")


def test_purpose_must_match_role():
    with pytest.raises(PermissionError):
        roles.load_point_year("uttarakhand", 0, "UKP_0014", 2018, purpose="select")
    with pytest.raises(PermissionError):
        roles.load_point_year("uttarakhand", 0, "UKP_0014", 2022, purpose="explore")
    df = roles.load_point_year("uttarakhand", 0, "UKP_0014", 2018, purpose="explore")
    assert len(df) == 8760


def test_test_years_need_the_lock_and_the_lock_is_single_use(tmp_path, monkeypatch):
    monkeypatch.setattr(roles, "TEST_LOCK_PATH", tmp_path / "held_out_test.lock")
    monkeypatch.setattr(roles, "_lock_held_by_this_process", False)
    with pytest.raises(roles.HeldOutLockError):
        roles.load_point_year("uttarakhand", 0, "UKP_0014", 2024, purpose="test")
    roles.acquire_test_lock("run-001", "abc123")
    assert json.loads((tmp_path / "held_out_test.lock").read_text())["run_id"] == "run-001"
    assert len(roles.load_point_year("uttarakhand", 0, "UKP_0014", 2024, purpose="test")) == 8760
    for p in ("explore", "select"):                                # test years are never available to the other purposes
        with pytest.raises(PermissionError):
            roles.load_point_year("uttarakhand", 0, "UKP_0014", 2025, purpose=p)
    with pytest.raises(roles.HeldOutLockError):                  # second acquisition refused
        roles.acquire_test_lock("run-002", "abc123")
    # a fresh process (flag reset) still cannot load test years while the lock file exists unowned
    monkeypatch.setattr(roles, "_lock_held_by_this_process", False)
    with pytest.raises(roles.HeldOutLockError):
        roles.load_point_year("uttarakhand", 0, "UKP_0014", 2025, purpose="test")


def test_real_lock_records_the_single_held_out_run():
    """After G10 (2026-10-27) the real lock exists. It must name the run that produced g10_heldout_results.csv and refuse a second run."""
    import json as _json
    if not roles.TEST_LOCK_PATH.exists():
        pytest.skip("held-out test not run yet")
    lock = _json.loads(roles.TEST_LOCK_PATH.read_text())
    held = pd.read_csv(roles.TEST_LOCK_PATH.parent / "g10_heldout_results.csv")
    assert set(held.run_id) == {lock["run_id"]}
    with pytest.raises(roles.HeldOutLockError):
        roles.acquire_test_lock("another-run", "x")


def test_inventory_meets_acceptance_rule():
    inv = pd.read_csv(roles.INVENTORY_PATH)
    assert len(inv) == 40 and set(inv.cluster_id) == {0, 1, 2, 3}
    assert inv["accepted"].all()
    assert (inv["pct_valid"] >= 98.0).all() and (inv["max_gap_h"] <= 3).all()
    assert inv["hourly_sequence_ok"].all() and (inv["n_hours_after_leap_drop"] == 8760).all()
    assert set(inv.groupby("year").role.first()) == {"explore", "select", "test"}
    for _, r in inv.iterrows():
        assert roles.point_year_path("uttarakhand", r.cluster_id, r.point_id, r.year).exists()


def test_test_years_are_below_average_ghi_in_every_cluster():
    """Rajasthan's plan claim ("2024-2025 are the two lowest-GHI years") does NOT hold for Uttarakhand: 2023 is lower
    than 2024 in regime 0 and the lowest year of all in regime 3. What does hold, and is stated instead: 2025 is the
    lowest-GHI year in regimes 0-2, and the test years' mean GHI is below the explore+select mean in every regime,
    so the held-out test is harsher than average."""
    inv = pd.read_csv(roles.INVENTORY_PATH)
    for c, g in inv.groupby("cluster_id"):
        test = g[g.role == "test"].GHI_annual_kWh_m2.mean()
        rest = g[g.role != "test"].GHI_annual_kWh_m2.mean()
        assert test < rest
        if c != 3:
            assert int(g.loc[g.GHI_annual_kWh_m2.idxmin(), "year"]) == 2025


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
