"""Physics invariants that must hold regardless of design or weather.

These are the properties a reviewer would challenge, written as tests so a
future change that breaks one fails loudly instead of quietly shifting a
reported number. Each test states WHAT would be wrong if it failed, not
just that a number moved.

Run:  python -m pytest tests/ -q
"""

import copy

import numpy as np
import pytest

from src.io_utils import (load_system_config, load_design_bounds, get_regime,
                          get_pcm_properties, load_hourly_weather, load_demand_profile)
from src.design.constraints import check_design
from src.design.volume_fraction import (design_from_fraction, achieved_fraction,
                                        n_capsule_for_fraction)
from src.simulation.capsule_enthalpy import pcm_props_from_record
from src.simulation.capsule_mass import capsule_breakdown, props_with_wall_capacity
from src.simulation.demand_profile import load_demand_model, local_hour_index
from src.simulation.tank_model import DesignRuntime
from src.simulation.tank_model_multinode_fast import (run_year_multinode_fast,
                                                       _pav_increasing, _thomas_solve)

STATE = "tamilnadu"
RESIDUAL_GATE_PCT = 0.5


@pytest.fixture(scope="module")
def ctx():
    sysconf = copy.deepcopy(load_system_config())
    sysconf["tank"]["n_nodes"] = 10
    sysconf["solver"]["timestep_s"] = 150.0
    bounds = load_design_bounds()
    weather = load_hourly_weather(STATE, 0)
    demand = load_demand_model(load_demand_profile(STATE))
    props = pcm_props_from_record(get_pcm_properties(STATE, "RT57HC"),
                                  sysconf["pcm_integration"]["melting_half_width_K"])
    return dict(sysconf=sysconf, bounds=bounds, weather=weather, demand=demand,
                props=props, mains=get_regime(STATE, 0)["T_mains_est_C"])


def _runtime(geom, n_caps):
    return DesignRuntime(
        n_capsule=n_caps, capsule_diameter_m=geom["capsule_diameter_m"],
        capsule_area_m2=geom["capsule_surface_area_m2"],
        capsule_volume_m3=geom["capsule_volume_m3"],
        void_fraction=geom["void_fraction_used_for_hydraulics"],
        cross_section_area_m2=geom["tank_cross_section_area_m2"],
        bed_length_m=geom["stack_height_m"] or geom["tank_height_m"],
        flow_rate_kg_s=geom["flow_rate_kg_s"], tank_volume_m3=geom["tank_volume_m3"],
        tank_surface_area_m2=geom["tank_surface_area_m2"])


def _run(ctx, frac=0.15, diam=0.05, flow=0.03, arrangement="staggered", hours=None,
          sysconf=None):
    sysconf = sysconf or ctx["sysconf"]
    design = design_from_fraction(frac, diam, flow, arrangement, sysconf)
    geom = check_design(design, sysconf, ctx["bounds"])
    assert geom["valid"], f"test design rejected: {geom.get('reason')}"
    w = ctx["weather"] if hours is None else ctx["weather"].iloc[:hours]
    return run_year_multinode_fast(w, ctx["demand"], ctx["mains"],
                                   _runtime(geom, geom["n_capsule"]),
                                   ctx["props"], sysconf, record_hourly=True)


# ---------------------------------------------------------------- Gate 1

def test_energy_balance_closes(ctx):
    """Gate 1. If this fails the model is creating or destroying energy and
    every reported kWh is meaningless."""
    res = _run(ctx)
    assert res.energy["residual_pct_of_collector"] < RESIDUAL_GATE_PCT


def test_energy_balance_closes_without_pcm(ctx):
    """The plain-tank baseline must conserve too -- it is what every gain
    is measured against."""
    sysconf = ctx["sysconf"]
    design = design_from_fraction(0.15, 0.05, 0.03, "staggered", sysconf)
    geom = check_design(design, sysconf, ctx["bounds"])
    res = run_year_multinode_fast(ctx["weather"], ctx["demand"], ctx["mains"],
                                  _runtime(geom, 0), ctx["props"], sysconf,
                                  record_hourly=True)
    assert res.energy["residual_pct_of_collector"] < RESIDUAL_GATE_PCT


# --------------------------------------------------------------- safety

def test_safety_limits_respected(ctx):
    """The two-part shield must hold both hard limits. A breach here is a
    feasibility failure, not a tuning issue."""
    res = _run(ctx)
    assert res.max_pcm_temp_C <= ctx["sysconf"]["safety"]["max_pcm_temp_C"]
    assert res.max_water_temp_C <= ctx["sysconf"]["safety"]["max_water_temp_C"]


def test_pcm_shield_does_not_stop_the_collector(ctx):
    """The defect that made PCM look useless: a PCM-side trip must NOT cap
    the water. With PCM present the water must still be able to run above
    the PCM's own 62 C trip, up toward its own 72 C bypass."""
    res = _run(ctx)
    assert res.max_water_temp_C > 65.0, (
        "water never exceeded 65 C with PCM present -- the PCM-side trip is "
        "throttling the collector again (see the two-part shield note)")


@pytest.mark.parametrize("frac,diam,flow", [
    (0.28, 0.041, 0.0113),   # the exact corner that breached in the 17,280-case DOE
    (0.28, 0.050, 0.0120),
    (0.29, 0.045, 0.0100),
])
def test_high_ua_corner_respects_pcm_limit(ctx, frac, diam, flow):
    """The PCM-side block must iterate to a FIXED POINT.

    Blocking one capsule group removes a heat sink, so the water runs
    hotter and can push a DIFFERENT group over its own trip. A two-pass
    implementation missed exactly that: 120 of 11,070 DOE designs peaked
    up to 68.51 C against a 65 C hard limit, all in the high-volume-
    fraction / many-small-capsules / low-flow corner. These are that
    corner.
    """
    res = _run(ctx, frac=frac, diam=diam, flow=flow)
    assert res.max_pcm_temp_C <= ctx["sysconf"]["safety"]["max_pcm_temp_C"], (
        f"PCM reached {res.max_pcm_temp_C:.2f} C -- the charge block is not "
        f"iterating to a fixed point")
    assert res.energy["residual_pct_of_collector"] < RESIDUAL_GATE_PCT


def test_pcm_discharge_is_never_blocked(ctx):
    """'Discharge never blocked': the PCM must deliver heat back to the
    water somewhere in the year."""
    res = _run(ctx)
    assert res.energy["E_discharge_kWh"] > 0.0


# ------------------------------------------------------- demand timing

def test_local_hour_covers_all_24_buckets(ctx):
    """G1. The old round() collapsed 24 local hours onto 12, so half the
    demand curve was never read."""
    idx = local_hour_index(ctx["weather"])
    assert sorted(set(idx.tolist())) == list(range(24))


def test_local_hour_is_floor_not_round(ctx):
    """00:00 UTC is 05:30 IST, which is hour 5 locally, not 6."""
    idx = local_hour_index(ctx["weather"])
    utc = ctx["weather"]["timestamp_utc"].dt.hour.to_numpy()
    assert idx[np.argmax(utc == 0)] == 5


# ------------------------------------------------------- capsule mass

def test_pcm_mass_uses_inner_sphere(ctx):
    """G2. Outer-volume mass overstates PCM; inner must be strictly less."""
    cap = capsule_breakdown(100, 0.05, 770.0, ctx["sysconf"])
    outer_mass = 100 * cap.outer_volume_m3 * 770.0
    assert cap.m_pcm_total_kg < outer_mass
    assert cap.inner_diameter_m == pytest.approx(
        0.05 - 2 * ctx["sysconf"]["pcm_integration"]["capsule_wall_thickness_m"])


def test_wall_capacity_raises_cp_but_not_latent(ctx):
    """The shell adds sensible capacity only -- aluminium does not melt."""
    cap = capsule_breakdown(100, 0.05, 770.0, ctx["sysconf"])
    aug = props_with_wall_capacity(ctx["props"], cap)
    assert aug.cp_solid_J_kgK > ctx["props"].cp_solid_J_kgK
    assert aug.cp_liquid_J_kgK > ctx["props"].cp_liquid_J_kgK
    assert aug.latent_heat_J_kg == ctx["props"].latent_heat_J_kg


# ------------------------------------------------- volume-fraction space

def test_fraction_round_trip(ctx):
    """The achieved fraction must be reported, and must track the request
    to within one capsule's worth."""
    for frac in (0.05, 0.15, 0.29):
        n = n_capsule_for_fraction(frac, 0.05, ctx["sysconf"])
        got = achieved_fraction(n, 0.05, ctx["sysconf"])
        one_capsule = achieved_fraction(1, 0.05, ctx["sysconf"])
        assert abs(got - frac) <= one_capsule


def test_fraction_bound_is_enforced(ctx):
    """The bound that silently did nothing before v3.0."""
    design = design_from_fraction(0.001, 0.05, 0.03, "staggered", ctx["sysconf"])
    geom = check_design(design, ctx["sysconf"], ctx["bounds"])
    assert not geom["valid"]
    assert geom["reason"] == "bounds_violation"


# ------------------------------------------------------ numeric kernels

def test_pav_is_monotone_and_conserves_energy():
    """PAV must enforce bottom-to-top monotonicity while conserving
    sum(mass*T) exactly -- that is what makes it energy-conserving."""
    rng = np.random.default_rng(0)
    for _ in range(50):
        T = rng.normal(50, 10, 10)
        w = rng.uniform(1, 5, 10)
        out = _pav_increasing(T, w, 10)
        assert np.all(np.diff(out) >= -1e-12)
        assert np.sum(w * out) == pytest.approx(np.sum(w * T), rel=1e-12)


def test_thomas_matches_dense_solve():
    """The tridiagonal solver must agree with a dense solve of the same
    system; they are mathematically identical."""
    rng = np.random.default_rng(1)
    for n in (1, 2, 5, 10, 20):
        diag = rng.uniform(10, 20, n)
        sub = np.concatenate([[0.0], -rng.uniform(0, 2, n - 1)]) if n > 1 else np.zeros(1)
        sup = np.concatenate([-rng.uniform(0, 2, n - 1), [0.0]]) if n > 1 else np.zeros(1)
        rhs = rng.uniform(100, 500, n)
        A = np.diag(diag)
        for i in range(1, n):
            A[i, i - 1] = sub[i]
        for i in range(n - 1):
            A[i, i + 1] = sup[i]
        assert _thomas_solve(sub, diag, sup, rhs, n) == pytest.approx(
            np.linalg.solve(A, rhs), rel=1e-10)


# ------------------------------------------------------------ sanity

def test_more_demand_cannot_increase_stored_energy(ctx):
    """Doubling the draw cannot leave MORE energy in the tank at year end."""
    base = _run(ctx)
    heavy_demand = load_demand_model(load_demand_profile(STATE), volume_multiplier=2.0)
    design = design_from_fraction(0.15, 0.05, 0.03, "staggered", ctx["sysconf"])
    geom = check_design(design, ctx["sysconf"], ctx["bounds"])
    heavy = run_year_multinode_fast(ctx["weather"], heavy_demand, ctx["mains"],
                                    _runtime(geom, geom["n_capsule"]), ctx["props"],
                                    ctx["sysconf"], record_hourly=True)
    assert heavy.energy["E_final_kWh"] <= base.energy["E_final_kWh"] + 1e-9


def test_zero_irradiance_year_delivers_no_collector_energy(ctx):
    """No sun, no collector heat -- the Gate 2 requirement."""
    dark = ctx["weather"].copy()
    dark["GHI_Wm2"] = 0.0
    design = design_from_fraction(0.15, 0.05, 0.03, "staggered", ctx["sysconf"])
    geom = check_design(design, ctx["sysconf"], ctx["bounds"])
    res = run_year_multinode_fast(dark.iloc[:720], ctx["demand"], ctx["mains"],
                                  _runtime(geom, geom["n_capsule"]), ctx["props"],
                                  ctx["sysconf"], record_hourly=True)
    assert res.energy["E_collector_kWh"] == pytest.approx(0.0, abs=1e-9)
