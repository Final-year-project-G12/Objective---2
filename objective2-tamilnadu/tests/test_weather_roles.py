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
from src.weather.inventory import CURRENT_MEDOIDS
from config import STATE

MEDOID0 = CURRENT_MEDOIDS[0]


def test_year_roles_split():
    assert roles.years_for("explore") == [2016, 2017, 2018, 2019, 2020]
    assert roles.years_for("select") == [2021, 2022, 2023]
    assert roles.years_for("test") == [2011, 2012, 2013, 2014, 2015]
    assert roles.role_of(2024) == roles.role_of(2025) == "used_test_v1"      # v1 test years: used, accepted for no purpose
    with pytest.raises(ValueError):
        roles.role_of(2010)
    with pytest.raises(ValueError):
        roles.years_for("anything")


def test_purpose_must_match_role():
    with pytest.raises(PermissionError):
        roles.load_point_year(STATE, 0, MEDOID0, 2018, purpose="select")
    with pytest.raises(PermissionError):
        roles.load_point_year(STATE, 0, MEDOID0, 2022, purpose="explore")
    df = roles.load_point_year(STATE, 0, MEDOID0, 2018, purpose="explore")
    assert len(df) == 8760


def test_test_years_need_the_lock_and_the_lock_is_single_use(tmp_path, monkeypatch):
    monkeypatch.setattr(roles, "TEST_LOCK_PATH", tmp_path / "held_out_test.lock")
    monkeypatch.setattr(roles, "_lock_held_by_this_process", False)
    with pytest.raises(roles.HeldOutLockError):
        roles.load_point_year(STATE, 0, MEDOID0, 2013, purpose="test")
    roles.acquire_test_lock("run-001", "abc123")
    assert json.loads((tmp_path / "held_out_test.lock").read_text())["run_id"] == "run-001"
    # With the lock held the gate opens and real data comes back. Between
    # 2026-10-29 and 2026-10-30 this had to tolerate FileNotFoundError, because
    # 2011-2015 were quarantined for want of verifiable raw weather. They were
    # rebuilt from the LST raw set on 2026-10-30 (offset measured, not assumed;
    # every day geometry-checked), so the strict assertion is restored.
    assert len(roles.load_point_year(STATE, 0, MEDOID0, 2013, purpose="test")) == 8760
    for p in ("test", "explore", "select"):                       # the used v1 test years can never be loaded again
        with pytest.raises(PermissionError):
            roles.load_point_year(STATE, 0, MEDOID0, 2024, purpose=p)
    with pytest.raises(roles.HeldOutLockError):                  # second acquisition refused
        roles.acquire_test_lock("run-002", "abc123")
    # a fresh process (flag reset) still cannot load test years while the lock file exists unowned
    monkeypatch.setattr(roles, "_lock_held_by_this_process", False)
    with pytest.raises(roles.HeldOutLockError):
        roles.load_point_year(STATE, 0, MEDOID0, 2014, purpose="test")


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
    """45 point-years, 2011-2025, every one rebuilt from raw and geometry-checked.

    This went 45 -> 30 -> 45. On 2026-10-29 the per-point-year cache was found
    to carry a +5 h solar shift; 2016-2025 were rebuilt from the UTC raw set,
    but 2011-2015 had no raw source in hand and were QUARANTINED rather than
    left in place where g10_test could spend its one-shot run on unverifiable
    weather.

    On 2026-10-30 a second raw set was found in the retired tree
    (data/weather/raw_nasapower_LST/, 2011-2025, all three medoids) whose
    header reads `"time_standard": "LST"` -- which is the ORIGIN of the
    original defect: that set had been read as though its keys were UTC. The
    held-out years were rebuilt from it with the offset MEASURED against the
    2016-2025 overlap (-5 h, correlation 1.00000 on every point), stitched
    across the file boundary so each UTC year is complete, and every day
    checked against sunrise/sunset.

    So the inventory carries two provenances, and `time_standard` distinguishes
    them: "UTC" for the directly-read years, "LST->UTC(-5h, measured)" for
    these. Recording that difference is the point -- the original defect
    survived precisely because provenance metadata was trusted without being
    checked.
    """
    inv = pd.read_csv(roles.INVENTORY_PATH)
    assert len(inv) == 45 and set(inv.cluster_id) == {0, 1, 2}
    assert set(inv.year) == set(range(2011, 2026))
    assert inv["accepted"].all()
    assert (inv["pct_valid"] >= 98.0).all() and (inv["max_gap_h"] <= 3).all()
    assert inv["hourly_sequence_ok"].all() and (inv["n_hours_after_leap_drop"] == 8760).all()
    assert set(inv.groupby("year").role.first()) == {"test", "explore", "select", "used_test_v1"}
    for _, r in inv.iterrows():
        assert roles.point_year_path(STATE, r.cluster_id, r.point_id, r.year).exists()

    # the held-out years must be present AND carry their real provenance
    held = inv[inv.year.between(2011, 2015)]
    assert len(held) == 15 and (held.role == "test").all()
    assert (held.time_standard == "LST->UTC(-5h, measured)").all(), \
        "held-out provenance must not be recorded as plain UTC -- it was converted"
    assert (inv[inv.year >= 2016].time_standard == "UTC").all()


def test_held_out_years_never_overlap_the_tuning_years():
    """What actually has to hold: nothing used to choose a design may appear
    in the held-out set, and the spent v1 years are usable for nothing.

    Replaces her `test_test_years_are_the_two_lowest_ghi_years_in_every_cluster`,
    which asserted `lowest_two == {2024, 2025}`. That is a fact about
    RAJASTHAN's irradiance, not a property of the method, and it is false for
    Tamil Nadu -- the two lowest-GHI years here are 2021/2025 (r0),
    2022/2021 (r1) and 2025/2024 (r2). Re-pointing the expected set at Tamil
    Nadu's answer would be writing the test to match the data, so the
    state-specific claim is dropped and the invariant is asserted instead.
    (Her test's premise is stale for her too: the live held-out years are the
    v3 set 2011-2015, not the v1 2024-2025 pair it names.)
    """
    inv = pd.read_csv(roles.INVENTORY_PATH)
    tuning = set(roles.years_for("explore")) | set(roles.years_for("select"))
    held_out = set(roles.years_for("test"))
    assert not (tuning & held_out)

    spent = {y for y in inv.year.unique() if roles.role_of(int(y)) == "used_test_v1"}
    assert not (spent & tuning) and not (spent & held_out)
    for purpose in roles.PURPOSES:
        for y in spent:
            with pytest.raises(PermissionError):
                roles.load_point_year(STATE, 0, MEDOID0, int(y), purpose=purpose)


def test_inventory_records_the_ghi_ranking_it_was_built_from():
    """The inventory must carry annual GHI per point-year, so the held-out
    choice can be audited against irradiance after the fact. The RANKING is
    recorded, not asserted -- see the test above for why."""
    inv = pd.read_csv(roles.INVENTORY_PATH)
    assert inv["GHI_annual_kWh_m2"].notna().all() and (inv["GHI_annual_kWh_m2"] > 0).all()
    for cid, g in inv.groupby("cluster_id"):
        assert len(set(g.nsmallest(2, "GHI_annual_kWh_m2").year)) == 2, (
            f"r{cid}: annual GHI is tied across years, so 'lowest' is undefined")


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
    (tmp_path / f"power_RJP_TEST_{year}.json").write_text(json.dumps(
        {"properties": {"parameter": par}, "header": {"time_standard": "UTC"}}))


def test_short_gap_is_filled_and_flagged(tmp_path):
    _synthetic_raw(tmp_path, gaps=[(1000, 3)])
    row, df = inv_mod.build_point_year(0, "RJP_TEST", 2019, raw_dir=tmp_path, write=False)
    assert row["accepted"] and row["n_filled_hours"] == 3 and row["max_gap_h"] == 3
    assert df["filled"].sum() == 3 and (df["GHI_Wm2"] >= 0).all() and df["GHI_Wm2"].notna().all()


def test_long_gap_rejects_the_point_year_but_keeps_the_row(tmp_path):
    _synthetic_raw(tmp_path, gaps=[(1000, 4)])
    row, df = inv_mod.build_point_year(0, "RJP_TEST", 2019, raw_dir=tmp_path, write=False)
    assert not row["accepted"] and df is None and "gap 4 h" in row["reject_reason"]


def test_below_98_percent_valid_rejects(tmp_path):
    _synthetic_raw(tmp_path, missing_frac=0.03)
    row, df = inv_mod.build_point_year(0, "RJP_TEST", 2019, raw_dir=tmp_path, write=False)
    assert not row["accepted"] and "valid" in row["reject_reason"]


def test_missing_raw_file_is_listed_not_dropped(tmp_path):
    row, df = inv_mod.build_point_year(0, "RJP_NOPE", 2019, raw_dir=tmp_path, write=False)
    assert not row["accepted"] and row["reject_reason"] == "raw file missing" and df is None


# Her version pinned a Rajasthan point id per cluster (RJP_0132/0192/0083);
# the medoid is looked up per state instead so the pairs stay meaningful here.
#
# Both fixtures above were wrong in the port, in ways that cancelled into one
# confusing failure:
#
#   * the YEAR. All three Tamil Nadu legacy regime files are 2016, not 2025 --
#     cluster 0 was comparing a 2016 file against a 2025 cache.
#   * the 29-FEB FILTER. The cache on disk holds the FULL year as fetched
#     (8784 rows in a leap year); `roles.load_point_year` is what drops 29
#     February, by UTC date. Re-filtering a raw read on `local_date` deletes
#     five extra rows, because local_date is IST (UTC+5:30): UTC 28-Feb
#     19:00..23:00 carries the local date 2016-02-29. That produced the
#     original "8760 == 8755".
#
# So the comparison is made through the loader the pipeline actually uses,
# not against a hand-filtered raw read.
@pytest.mark.parametrize("cluster,year", [(0, 2016), (1, 2016), (2, 2016)])
def test_new_cache_matches_existing_regime_weather_file(cluster, year):
    point = CURRENT_MEDOIDS[cluster]
    old = load_hourly_weather(STATE, cluster)            # already 29-Feb-free, from the same raw source
    new = roles.load_point_year(STATE, cluster, point, year, "explore")
    assert len(old) == len(new) == 8760
    assert (old["timestamp_utc"].to_numpy() == new["timestamp_utc"].to_numpy()).all()
    assert np.allclose(old["GHI_Wm2"], new["GHI_Wm2"]) and np.allclose(old["T_amb_C"], new["T_amb_C"])
    assert (old["local_hour"].to_numpy() == new["local_hour"].to_numpy()).all()
