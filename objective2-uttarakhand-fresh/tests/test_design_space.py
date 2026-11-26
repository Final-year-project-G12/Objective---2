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
from src.design.constraints import check_design
from src.io_utils import load_system_config
from src.optimize import baseline, evaluate
from src.simulation.run_case import run_case


def test_approved_ranges_are_what_the_user_approved():
    v = space.load_space()["variables"]
    assert v["inner_radius_m"] == {"min": 0.010, "max": 0.040}
    assert v["pcm_volume_fraction"] == {"min": 0.02, "max": 0.30}
    assert v["flow_rate_kg_s"] == {"min": 0.010, "max": 0.050}
    assert v["arrangement"] == ["single-layer", "staggered", "radial"]
    assert space.load_space()["constraints"]["pcm_peak_limit_C"] == 65.0
    assert space.load_space()["model"]["n_nodes"] == 10


@pytest.mark.parametrize("r", [0.010, 0.0175, 0.025, 0.040])
@pytest.mark.parametrize("f", [0.02, 0.05, 0.12, 0.20, 0.30])
def test_count_rule_keeps_the_fraction_inside_2_to_30_percent(r, f):
    dv = space.to_design(r, f, 0.03, "staggered")
    frac = dv.n_capsule * space.capsule_outer_volume_m3(r) / space.v_tank_m3()
    assert 0.02 - 1e-9 <= frac <= 0.30 + 1e-9
    assert dv.capsule_diameter_m == pytest.approx(2 * (r + 0.0008))


def test_geometry_engine_is_still_the_judge_of_feasibility():
    cfg = load_system_config()
    bad = [(r, f, a) for r in (0.010, 0.025, 0.030, 0.040) for f in (0.02, 0.30)
           for a in space.ARRANGEMENTS
           if not check_design(space.to_design(r, f, 0.03, a), cfg, space.geometry_bounds())["valid"]]
    # radial packing cannot reach 30 % at the larger radii (G7: max feasible 15.4 % at R=30 mm); the engine must say so
    assert ("radial" in {a for _, _, a in bad}) and all(a == "radial" for _, _, a in bad)
    assert (0.030, 0.30, "radial") in bad


@pytest.mark.parametrize("cid,year,flow", [(0, 2018, 0.0225), (1, 2019, 0.0375)])
def test_plain_baseline_interpolation_matches_an_exact_plain_run(cid, year, flow):
    from src.weather import roles
    from src.weather.inventory import CURRENT_MEDOIDS
    w = roles.load_point_year("uttarakhand", cid, CURRENT_MEDOIDS[cid], year, "explore")
    exact = run_case("uttarakhand", cid, None, space.to_design(0.02, 0.05, flow, "staggered"),
                     design_bounds=space.geometry_bounds(), weather=w, tank_model="multinode",
                     compute_tes_metrics=True, night_day_stride=0)
    est = baseline.plain_at(cid, year, flow, "explore")
    assert est["E_del45_annual_kWh"] == pytest.approx(exact["tes"]["E_del45_annual_kWh"], rel=1e-4)
    assert est["useful_energy_kWh"] == pytest.approx(exact["metrics"]["useful_energy_kWh"], rel=1e-4)


def test_evaluate_design_returns_paired_objectives_and_feasibility():
    res = evaluate.evaluate_design(1, "PureTemp 58", 0.020, 0.10, 0.03, "staggered", purpose="explore",
                                   years=[2018, 2019])
    assert res["valid"] and len(res["per_year"]) == 2
    for k in evaluate.OBJECTIVE_KEYS + ("t_pcm_max", "pcm_mass_kg", "feasible"):
        assert k in res
    assert res["residual_pct"] < 1e-3
    assert res["feasible"] == (res["t_pcm_max"] <= 65.0)
    # a PCM tank at 10 % fraction should add delivered energy over the same-flow water tank (G7 sign)
    assert res["g_annual"] > 0


def test_infeasible_geometry_is_reported_not_simulated():
    res = evaluate.evaluate_design(1, "PureTemp 58", 0.030, 0.20, 0.03, "radial", purpose="explore", years=[2018])
    assert not res["valid"] and res["reason"] and "per_year" not in res


def test_select_and_explore_baselines_exist_but_no_test_baseline():
    from src.weather.inventory import REGIMES
    for c in REGIMES:
        assert baseline.grid_path("explore", c).exists() and baseline.grid_path("select", c).exists()
        assert not baseline.grid_path("test", c).exists()
