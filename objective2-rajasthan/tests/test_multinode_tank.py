"""
tests/test_multinode_tank.py
===============================
G4 (O2 redesign, 2026-10-26) — checks on the 1-D stratified multi-node tank
(src/simulation/tank_model_multinode.py): numba enthalpy equals the reference
Python enthalpy, N=1 reproduces the single-node model, exact energy closure,
buoyancy, capsule layout, and the project-CFD stratified-draw case.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.design.schema import DesignVector
from src.simulation import run_case as rc
from src.simulation import tank_model_multinode as mn
from src.simulation.capsule_enthalpy import (
    PCMThermalProps, enthalpy_of_temperature, temperature_and_liquid_fraction_of_enthalpy,
)

DV = DesignVector(capsule_diameter_m=0.0429, n_capsule=37, flow_rate_kg_s=0.0428, capsule_arrangement="single-layer")


def test_numba_enthalpy_equals_reference():
    for wall in (0.0, 410.0):
        p = PCMThermalProps(Tm_C=45.0, latent_heat_J_kg=200e3, cp_solid_J_kgK=2000.0, cp_liquid_J_kgK=2200.0,
                            conductivity_W_mK=0.2, density_kg_m3=800.0, wall_cp_J_kgK=wall)
        args = (p.Ts_C, p.Tl_C, p.latent_heat_J_kg, p.cp_solid_J_kgK, p.cp_liquid_J_kgK, p.wall_cp_J_kgK)
        for T in (10.0, 43.9, 44.0, 44.5, 45.0, 45.7, 46.0, 50.0, 80.0):
            h = enthalpy_of_temperature(T, p)
            assert mn._h_of_T(T, *args) == pytest.approx(h, rel=1e-12)
            T_back, f = mn._T_f_of_h(h, *args)
            T_ref, f_ref = temperature_and_liquid_fraction_of_enthalpy(h, p)
            assert (T_back, f) == pytest.approx((T_ref, f_ref), abs=1e-9)


def test_one_node_plain_tank_reproduces_single_node_model():
    a = rc.run_case("rajasthan", 0, None, DV, record_hourly=False)["metrics"]
    b = rc.run_case("rajasthan", 0, None, DV, tank_model="multinode", n_nodes=1, record_hourly=False)["metrics"]
    assert b["useful_energy_kWh"] == pytest.approx(a["useful_energy_kWh"], rel=1e-5)
    assert b["unmet_energy_kWh"] == pytest.approx(a["unmet_energy_kWh"], rel=1e-5)
    assert b["loss_energy_kWh"] == pytest.approx(a["loss_energy_kWh"], rel=1e-5)


def test_energy_closes_exactly_and_year_is_fast():
    import time
    for pcm in (None, "RT44HC"):
        t0 = time.time()
        m = rc.run_case("rajasthan", 0, pcm, DV, tank_model="multinode", n_nodes=10, record_hourly=False)["metrics"]
        assert m["residual_pct_of_collector"] < 1e-6            # exact: load booked unclipped
        assert time.time() - t0 < 20.0                          # G4 runtime criterion (one simulated year)
        assert m["max_water_temp_C"] < 75.0


def test_buoyancy_removes_inversion_and_conserves_energy():
    m = np.array([5.0, 5.0, 5.0, 5.0])
    T = np.array([60.0, 30.0, 40.0, 20.0])          # hot at the bottom: unstable
    e0 = float((m * T).sum())
    mn._mix_inversions(T, m, 4)
    assert (np.diff(T) >= -1e-9).all()
    assert float((m * T).sum()) == pytest.approx(e0)


def test_layout_counts_and_anchor():
    geom = {"tank_height_m": 1.0, "tank_diameter_m": 0.3, "n_capsule": 25, "n_layers": 5, "capsules_per_layer": 6,
            "stack_height_m": 0.5}
    bottom = mn.layout_from_geometry(geom, 10, "bottom")
    top = mn.layout_from_geometry(geom, 10, "top")
    centre = mn.layout_from_geometry(geom, 10, "center")
    for lay in (bottom, top, centre):
        assert lay.capsules_per_node.sum() == 25
    assert bottom.capsules_per_node[:5].sum() == 25 and bottom.capsules_per_node[5:].sum() == 0
    assert top.capsules_per_node[5:].sum() == 25
    assert centre.capsules_per_node[2:8].sum() == 25
    plain = mn.layout_from_geometry({**geom, "n_capsule": 0, "n_layers": 0}, 10)
    assert plain.capsules_per_node.sum() == 0


def _cfd_draw_volume_l(n_nodes, hot_fraction=0.6, hot_c=55.0, cold_c=25.0, uniform_c=None, monkeypatch=None):
    """Project CFD tank-draw case (openfoam_cfd/docs/COMPONENT_CFD_NOTES.md): 50 L tank, 30 L at 55 C over 20 L at
    25 C, 0.03 kg/s of 25 C mains at the bottom. Returns litres delivered at >= 45 C."""
    w = pd.DataFrame({"timestamp_utc": pd.date_range("2025-01-01", periods=2, freq="h", tz="UTC"), "GHI_Wm2": 0.0,
                      "T_amb_C": 25.0, "local_hour": [0, 1], "local_date": "2025-01-01"})
    monkeypatch.setattr(rc, "load_hourly_weather", lambda s, c, **kw: w)
    monkeypatch.setattr(rc, "load_demand_profile",
                        lambda s: pd.DataFrame({"hour": range(24), "draw_mass_kg": [0.03 * 3600] + [0.0] * 23}))
    T = np.full(n_nodes, cold_c)
    T[int(round(n_nodes * (1 - hot_fraction))):] = hot_c
    if uniform_c is not None:
        T[:] = uniform_c
    out = rc.run_case("rajasthan", 0, None, DV, tank_model="multinode", n_nodes=n_nodes, mains_temp_override_C=25.0,
                      initial_state={"T_nodes": T, "h_nodes": np.zeros(n_nodes), "T_w_C": float(T.mean())},
                      system_config_overrides={"solver": {"timestep_s": 30}}, record_hourly=True)
    return float(out["hourly"]["vol_ge_target_kg"].iloc[0])


def test_stratified_tank_delivers_hot_water_where_mixed_tank_delivers_none(monkeypatch):
    # fully mixed 43 C (= energy-equivalent of the stratified state): nothing at >= 45 C
    assert _cfd_draw_volume_l(1, uniform_c=43.0, monkeypatch=monkeypatch) == 0.0
    assert _cfd_draw_volume_l(10, uniform_c=43.0, monkeypatch=monkeypatch) == 0.0
    v10 = _cfd_draw_volume_l(10, monkeypatch=monkeypatch)
    v20 = _cfd_draw_volume_l(20, monkeypatch=monkeypatch)
    v40 = _cfd_draw_volume_l(40, monkeypatch=monkeypatch)
    # CFD: 27 L (90 % of the 30 L hot volume); ideal plug flow would give 30 L. The 1-D model converges toward
    # that from below as numerical diffusion falls with N.
    assert 18.0 <= v10 <= 30.0
    assert v10 <= v20 <= v40 <= 30.0
    assert abs(v40 - 27.0) < 2.0


def test_stratification_persists_without_draw(monkeypatch):
    w = pd.DataFrame({"timestamp_utc": pd.date_range("2025-01-01", periods=7, freq="h", tz="UTC"), "GHI_Wm2": 0.0,
                      "T_amb_C": 25.0, "local_hour": np.arange(7), "local_date": "2025-01-01"})
    monkeypatch.setattr(rc, "load_hourly_weather", lambda s, c, **kw: w)
    T = np.full(10, 25.0)
    T[4:] = 55.0
    out = rc.run_case("rajasthan", 0, None, DV, volume_multiplier=0.0, tank_model="multinode", n_nodes=10,
                      initial_state={"T_nodes": T, "h_nodes": np.zeros(10), "T_w_C": 43.0}, record_hourly=True)
    h = out["hourly"]
    assert (h["T_w_C"] - h["T_bottom_C"]).min() > 15.0          # still stratified after 7 h
    assert (h["T_w_C"] >= h["T_bottom_C"]).all()


def test_multinode_metrics_and_night_scenarios_run():
    out = rc.run_case("rajasthan", 0, "RT44HC", DV, tank_model="multinode", n_nodes=10, compute_tes_metrics=True,
                      night_day_stride=60)
    tes = out["tes"]
    assert tes["closure_residual_pct"] < 1e-3
    assert len(out["night_daily"]) >= 5
    assert np.isfinite(tes["E_rec45_mean_kWh"]) and tes["E_stored_max_kWh"] >= tes["E_rec45_max_kWh"] >= 0.0


def test_numba_ua_equals_reference_ua():
    from src.io_utils import load_system_config, get_pcm_properties
    from src.simulation.capsule_enthalpy import pcm_props_from_record
    from src.simulation.heat_transfer import ua_eff_total_w_k, _water_dynamic_viscosity_pa_s
    from src.design.geometry import sphere_surface_area_m2
    cfg = load_system_config()
    integ, water = cfg["pcm_integration"], cfg["water"]
    props = pcm_props_from_record(get_pcm_properties("rajasthan", "PureTemp 60"), integ["melting_half_width_K"])
    for d, f, v in ((0.0216, 0.0, 1e-4), (0.0429, 1.0, 5e-4), (0.0816, 0.6, 0.0)):
        area = sphere_surface_area_m2(d)
        ref = ua_eff_total_w_k(25, d, area, v, props, f, cfg)
        got = mn._ua_node(25.0, d, area, v, f, water["density_kg_m3"], water["conductivity_W_mK"], water["prandtl"],
                          _water_dynamic_viscosity_pa_s(), integ["capsule_wall_thickness_m"],
                          integ["capsule_wall_conductivity_W_mK"], props.conductivity_W_mK,
                          integ["liquid_convection_enhancement"])
        assert got == pytest.approx(ref, rel=1e-9)
