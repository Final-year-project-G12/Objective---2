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
from config import STATE


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
    """The engine must reject infeasible designs AND distinguish WHY.

    Tamil Nadu's 100 L tank produces two separate failure modes, where her
    50 L tank only ever hit the first:

      passage_blocked   radial packing cannot open a 5 % flow passage at the
                        larger radii (G7: radial maxes at 27.9 % at R=30 mm,
                        17.9 % at R=40 mm), so f=0.30 is unreachable there.
      bounds_violation  at R=10 mm the capsule COUNT needed for 30 % of a
                        100 L tank overruns the count rule's own ceiling --
                        a volume-scaling effect absent at 50 L, and it hits
                        every arrangement, not just radial.

    Both are correct rejections. The invariant is that the engine owns the
    verdict and names the reason; asserting "only radial ever fails" would be
    importing a Rajasthan tank size into a Tamil Nadu test.
    """
    cfg = load_system_config()
    verdicts = {}
    for r in (0.010, 0.025, 0.030, 0.040):
        for f in (0.02, 0.30):
            for a in space.ARRANGEMENTS:
                v = check_design(space.to_design(r, f, 0.03, a), cfg, space.geometry_bounds())
                verdicts[(r, f, a)] = v

    bad = {k: v["reason"] for k, v in verdicts.items() if not v["valid"]}
    assert bad, "nothing was rejected -- the engine is no longer judging"
    assert all(v["reason"] for v in verdicts.values() if not v["valid"]), \
        "a rejection carried no reason"

    # Mode 1: radial is the ONLY arrangement that blocks the flow passage.
    blocked = {k for k, why in bad.items() if why == "passage_blocked"}
    assert blocked, "radial packing no longer blocks at any tested radius"
    assert all(a == "radial" for _, _, a in blocked)
    assert (0.030, 0.30, "radial") in blocked and (0.040, 0.30, "radial") in blocked

    # Mode 2: the count ceiling at R=10 mm, f=0.30 binds for every arrangement.
    over = {k for k, why in bad.items() if why == "bounds_violation"}
    assert {a for _, _, a in over} == set(space.ARRANGEMENTS), \
        "the 100 L count ceiling should bind for every arrangement at R=10 mm"
    assert all(r == 0.010 and f == 0.30 for r, f, _ in over)

    # Low fraction is always reachable, whatever the radius or arrangement.
    assert all(verdicts[(r, 0.02, a)]["valid"]
               for r in (0.010, 0.025, 0.030, 0.040) for a in space.ARRANGEMENTS)


@pytest.mark.parametrize("cid,year,flow", [(0, 2018, 0.0225), (1, 2019, 0.0375)])
def test_plain_baseline_interpolation_matches_an_exact_plain_run(cid, year, flow):
    from src.weather import roles
    from src.weather.inventory import CURRENT_MEDOIDS
    w = roles.load_point_year(STATE, cid, CURRENT_MEDOIDS[cid], year, "explore")
    exact = run_case(STATE, cid, None, space.to_design(0.02, 0.05, flow, "staggered"),
                     design_bounds=space.geometry_bounds(), weather=w, tank_model="multinode",
                     compute_tes_metrics=True, night_day_stride=0)
    est = baseline.plain_at(cid, year, flow, "explore")
    assert est["E_del45_annual_kWh"] == pytest.approx(exact["tes"]["E_del45_annual_kWh"], rel=1e-4)
    assert est["useful_energy_kWh"] == pytest.approx(exact["metrics"]["useful_energy_kWh"], rel=1e-4)


def test_evaluate_design_returns_paired_objectives_and_feasibility():
    """Structure and internal consistency of a paired evaluation.

    PCM is cluster 0's rank-3 PureTemp 58. The original test asked cluster 1
    for this PCM, which is not in cluster 1's shortlist at all (cluster 1 is
    RT57HC / C26 / C25) -- an invalid regime/PCM pairing carried over in the
    port.

    It also asserted g_annual > 0 at this single design point. That does not
    hold in Tamil Nadu and is not a property of the evaluator: across the
    128-point DOE the sign of g_annual swings with flow and arrangement at
    fixed fraction (r0_p3 at 8-13 % fraction spans -19.2 to +22.4 kWh/yr).
    The sign is a RESULT, tested against the DOE in
    test_pcm_vs_water_sign_is_a_regime_level_finding; what belongs here is
    that the aggregation is correct.
    """
    res = evaluate.evaluate_design(0, "PureTemp 58", 0.020, 0.10, 0.03, "staggered", purpose="explore",
                                   years=[2018, 2019])
    assert res["valid"] and len(res["per_year"]) == 2
    for k in evaluate.OBJECTIVE_KEYS + ("t_pcm_max", "pcm_mass_kg", "feasible"):
        assert k in res
    assert res["residual_pct"] < 1e-3
    assert res["feasible"] == (res["t_pcm_max"] <= 65.0)

    # each objective is the mean over years, and its sd the spread -- the
    # aggregation every surrogate downstream is fitted against
    for k in evaluate.OBJECTIVE_KEYS:
        assert res[k] == pytest.approx(np.mean([d[k] for d in res["per_year"]]))
        assert res[k + "_sd"] == pytest.approx(
            np.std([d[k] for d in res["per_year"]], ddof=1))
    # peak temperatures are worst-case over years, not averaged
    assert res["t_pcm_max"] == pytest.approx(max(d["t_pcm_max"] for d in res["per_year"]))
    assert res["pcm_mass_kg"] > 0


def test_infeasible_geometry_is_reported_not_simulated():
    # R=40 mm radial at f=0.30: radial packing tops out at 17.9 % there (G7),
    # so the passage constraint bites. Her fixture was R=30 mm at f=0.20,
    # which the 100 L tank can now actually accommodate (radial reaches
    # 27.9 % at R=30 mm) -- it is feasible here, so it tested nothing.
    res = evaluate.evaluate_design(1, "RT57HC", 0.040, 0.30, 0.03, "radial", purpose="explore", years=[2018])
    assert not res["valid"] and res["reason"] and "per_year" not in res
    assert res["reason"] == "passage_blocked"


def test_pcm_vs_water_sign_is_internally_consistent():
    """Whether PCM beats the same-flow water tank is a RESULT, read off the DOE.

    This test deliberately asserts only what must be true of any correct DOE,
    and PRINTS the per-regime signs rather than pinning them.

    Why it is not pinned: the first version of this test hard-coded shares
    measured from the DOE built on the +5 h-shifted weather cache (regime 1
    ranks 1-2 losing on annual energy in >92 % of designs, rank 3 winning the
    window in ~74 %). That weather was wrong -- it put solar noon at 16:30
    local instead of 11:30, i.e. far closer to the 19:00 demand peak -- so
    those shares measured an artefact, not Tamil Nadu. See the 2026-10-29
    entry in docs/RAJASTHAN_METHOD_PORT_PROGRESS.md.

    Once the rebuilt DOE lands, the printed shares are the honest input to
    the write-up, and a sign claim can be pinned here if it proves stable
    across regimes and ranks. Pinning it from a single run would just
    re-create the same mistake.
    """
    import pandas as pd
    res_dir = REPO_ROOT / "results"
    rows = []
    for cid in range(3):
        for rank in (1, 2, 3):
            p = res_dir / f"g8_s2_r{cid}_p{rank}.csv"
            if not p.exists():
                pytest.skip(f"DOE not complete: {p.name} missing")
            d = pd.read_csv(p)
            d = d[d.valid == True]                               # noqa: E712
            w, a = d.g_window.dropna(), d.g_annual.dropna()
            assert len(w) and len(a), f"{p.name} has no valid objective rows"
            # a paired objective is a DIFFERENCE, so both signs must be
            # reachable in principle; what must hold is that it is finite
            # and that the two objectives are not accidentally identical
            assert np.isfinite(w).all() and np.isfinite(a).all()
            assert not np.allclose(w.to_numpy(), a.to_numpy()), \
                f"{p.name}: g_window and g_annual are identical -- objectives collapsed"
            rows.append((cid, rank, d.pcm.iloc[0], (w > 0).mean(), (a > 0).mean()))

    print("\n  regime rank pcm                     g_window>0  g_annual>0")
    for cid, rank, pcm, sw, sa in rows:
        print(f"  {cid:6d} {rank:4d} {pcm:22s} {sw:10.1%} {sa:10.1%}")


def test_select_and_explore_baselines_exist_but_no_test_baseline():
    for c in range(3):
        assert baseline.grid_path("explore", c).exists() and baseline.grid_path("select", c).exists()
        assert not baseline.grid_path("test", c).exists()
