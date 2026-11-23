"""
tests/test_design_space.py
=============================
G8 (O2, 2026-10-26) - the approved design space, the same-flow baseline interpolation and the
evaluation function.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.design import space
from src.design.box import full_dt
from src.design.constraints import check_design
from src.io_utils import load_system_config
from src.optimize import baseline, evaluate
from src.simulation.run_case import run_case


def test_approved_ranges_are_what_the_user_approved():
    v = space.load_space()["variables"]
    assert v["inner_radius_m"] == {"min": 0.010, "max": 0.040}
    assert v["pcm_volume_fraction"] == {"min": 0.02, "max": 0.40}          # rebuild, plan R4
    assert v["flow_rate_kg_s"] == {"min": 0.030, "max": 0.030}            # rebuild, plan R6: fixed, not searched
    assert space.geometry_bounds()["flow_rate_kg_s"] == {"min": 0.010, "max": 0.050}   # the pump range still judges validity
    assert v["arrangement"] == ["single-layer", "staggered", "radial"]
    assert space.load_space()["constraints"]["pcm_peak_limit_C"] == 65.0
    assert space.load_space()["model"]["n_nodes"] == 10


@pytest.mark.parametrize("r", [0.010, 0.0175, 0.025, 0.040])
@pytest.mark.parametrize("f", [0.02, 0.05, 0.12, 0.20, 0.30, 0.40])
def test_count_rule_keeps_the_fraction_inside_2_to_40_percent(r, f):
    dv = space.to_design(r, f, 0.03, "staggered")
    frac = dv.n_capsule * space.capsule_outer_volume_m3(r) / space.v_tank_m3()
    assert 0.02 - 1e-9 <= frac <= 0.40 + 1e-9
    assert dv.capsule_diameter_m == pytest.approx(2 * (r + 0.0008))


def test_geometry_engine_is_still_the_judge_of_feasibility():
    cfg = load_system_config()
    res = {(r, f, a): check_design(space.to_design(r, f, 0.03, a), cfg, space.geometry_bounds())
           for r in (0.010, 0.025, 0.030, 0.040) for f in (0.02, 0.30, 0.40) for a in space.ARRANGEMENTS}
    bad = {k: v["reason"] for k, v in res.items() if not v["valid"]}
    # 100 L tank (rebuild): only packing rejects designs (the blocked flow passage), never an administrative count bound
    assert set(bad.values()) == {"passage_blocked"}
    assert (0.030, 0.30, "radial") in bad and (0.040, 0.40, "radial") in bad
    assert not any(f == 0.02 for (_, f, _) in bad)                              # 2 % always packs
    assert all(not bad.get((r, 0.40, "staggered")) for r in (0.025, 0.030, 0.040))   # the 40 % cap is reachable


# Rebuild (2026-11-23): the water-only baseline is EXACT runs at the fixed flow 0.030 kg/s (scripts/g8_build_plain_baseline.py, L4).
needs_baseline = pytest.mark.skipif(not baseline.grid_path("explore", 0).exists(),
                                    reason="rebuild: plain baseline not built yet (plan level L4)")


@needs_baseline
@pytest.mark.parametrize("cid,year", [(0, 2018), (1, 2019)])
def test_cached_baseline_equals_an_exact_plain_run_at_the_fixed_flow(cid, year):
    from src.design.box import flow_fixed
    from src.weather import roles
    from src.weather.inventory import CURRENT_MEDOIDS
    w = roles.load_point_year("uttarakhand", cid, CURRENT_MEDOIDS[cid], year, "explore")
    exact = run_case("uttarakhand", cid, None, space.to_design(0.02, 0.05, flow_fixed(), "staggered"),
                     design_bounds=space.geometry_bounds(), weather=w, tank_model="multinode",
                     compute_tes_metrics=True, night_day_stride=0, system_config_overrides={"solver": {"timestep_s": 150}})
    est = baseline.plain_at(cid, year, flow_fixed(), "explore", dt=150)
    assert est["E_del45_window_kWh"] == pytest.approx(exact["tes"]["E_del45_window_kWh"], rel=1e-12)
    assert est["useful_energy_kWh"] == pytest.approx(exact["metrics"]["useful_energy_kWh"], rel=1e-12)


@needs_baseline
def test_evaluate_design_returns_robust_anchor_objectives_and_feasibility():
    res = evaluate.evaluate_design(1, "PureTemp 58", 0.020, 0.10, 0.03, "staggered", purpose="explore", years=[2018, 2019])
    assert res["valid"] and len(res["per_year"]) == 2 * 3                      # 2 years x 3 robust anchors
    for k in evaluate.OBJECTIVE_KEYS + ("t_pcm_max", "pcm_mass_kg", "feasible", "g_window_worst_anchor", "worst_anchor"):
        assert k in res
    assert res["residual_pct"] < 1e-3
    assert res["feasible"] == (res["t_pcm_max"] <= 65.0 and res["t_water_max"] <= 75.0)
    per_anchor = [res[f"g_window_{a}"] for a in ("bottom", "center", "top")]
    assert res["g_window_worst_anchor"] == pytest.approx(min(per_anchor))
    assert res["g_window"] == pytest.approx(np.mean(per_anchor))
    # NOTE: the legacy assertion "10 % PCM gains over water-only" held on the 50 L / 300 L/day plant and does NOT hold on the common
    # 100 L / 100 L/day plant (docs/REBUILD_COMMON100L.md section 3c), so it is not asserted.


@needs_baseline
def test_infeasible_geometry_is_reported_not_simulated():
    res = evaluate.evaluate_design(1, "PureTemp 58", 0.040, 0.40, 0.03, "radial", purpose="explore", years=[2018])
    assert not res["valid"] and res["reason"] and "per_year" not in res


@needs_baseline
def test_select_and_explore_baselines_exist_but_no_test_baseline():
    from src.weather.inventory import REGIMES
    for c in REGIMES:
        for dt in (150, full_dt()):
            assert baseline.grid_path("explore", c, dt).exists() and baseline.grid_path("select", c, dt).exists()
            assert not baseline.grid_path("test", c, dt).exists() and not baseline.grid_path("report", c, dt).exists()
