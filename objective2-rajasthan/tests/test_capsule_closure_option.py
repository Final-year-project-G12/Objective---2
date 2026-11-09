"""
tests/test_capsule_closure_option.py
=====================================
The optional CFD-recalibrated capsule closure (O2 OpenFOAM recalibration, 2026-10-29): the conduction coefficient c in
R_pcm = r / (c k_eff) (pcm_integration.conduction_coefficient_c) and the liquid-convection factor F
(pcm_integration.liquid_convection_enhancement). Both are OFF by default: the frozen config has no c key and F = 2.0, and
the code then reproduces c = 5, F = 2 bit-for-bit. A recalibrated value enters only through system_config_overrides.
"""

import copy
import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.design.geometry import sphere_surface_area_m2
from src.design.schema import DesignVector
from src.io_utils import get_pcm_properties, load_system_config
from src.simulation import run_case as rc
from src.simulation import tank_model_multinode as mn
from src.simulation.capsule_enthalpy import pcm_props_from_record
from src.simulation.heat_transfer import _water_dynamic_viscosity_pa_s, ua_eff_total_w_k

DV = DesignVector(capsule_diameter_m=0.0829, n_capsule=52, flow_rate_kg_s=0.0236, capsule_arrangement="single-layer")


def _props():
    cfg = load_system_config()
    return cfg, pcm_props_from_record(get_pcm_properties("rajasthan", "PureTemp 58"), cfg["pcm_integration"]["melting_half_width_K"])


def test_frozen_config_is_untouched_and_option_absent():
    integ = load_system_config()["pcm_integration"]
    assert "conduction_coefficient_c" not in integ
    assert integ["liquid_convection_enhancement"] == 2.0


def test_default_equals_explicit_c5_in_both_paths():
    cfg, props = _props()
    d = 0.0829
    area = sphere_surface_area_m2(d)
    explicit = copy.deepcopy(cfg)
    explicit["pcm_integration"]["conduction_coefficient_c"] = 5.0
    for f in (0.0, 1.0):
        assert ua_eff_total_w_k(52, d, area, 5e-4, props, f, cfg) == ua_eff_total_w_k(52, d, area, 5e-4, props, f, explicit)
    w, integ = cfg["water"], cfg["pcm_integration"]
    args = (52.0, d, area, 5e-4, 1.0, w["density_kg_m3"], w["conductivity_W_mK"], w["prandtl"], _water_dynamic_viscosity_pa_s(),
            integ["capsule_wall_thickness_m"], integ["capsule_wall_conductivity_W_mK"], props.conductivity_W_mK, integ["liquid_convection_enhancement"])
    assert mn._ua_node(*args) == mn._ua_node(*args, 5.0)


def test_c_scales_only_the_pcm_resistance_hand_calculation():
    cfg, props = _props()
    d, f = 0.0829, 0.0
    area = sphere_surface_area_m2(d)
    w, integ = cfg["water"], cfg["pcm_integration"]
    base = (1.0, d, area, 5e-4, f, w["density_kg_m3"], w["conductivity_W_mK"], w["prandtl"], _water_dynamic_viscosity_pa_s(),
            integ["capsule_wall_thickness_m"], integ["capsule_wall_conductivity_W_mK"], props.conductivity_W_mK, 2.0)
    r_in = d / 2.0 - integ["capsule_wall_thickness_m"]
    a_in = 4.0 * math.pi * r_in ** 2
    r5 = 1.0 / mn._ua_node(*base, 5.0)
    r10 = 1.0 / mn._ua_node(*base, 10.0)
    assert r5 - r10 == pytest.approx(r_in / (5.0 * props.conductivity_W_mK * a_in) - r_in / (10.0 * props.conductivity_W_mK * a_in), rel=1e-9)


def test_python_and_numba_paths_agree_for_a_changed_c():
    cfg, props = _props()
    cfg = copy.deepcopy(cfg)
    cfg["pcm_integration"]["conduction_coefficient_c"] = 8.0
    d = 0.0829
    area = sphere_surface_area_m2(d)
    w, integ = cfg["water"], cfg["pcm_integration"]
    got = mn._ua_node(25.0, d, area, 5e-4, 1.0, w["density_kg_m3"], w["conductivity_W_mK"], w["prandtl"], _water_dynamic_viscosity_pa_s(),
                      integ["capsule_wall_thickness_m"], integ["capsule_wall_conductivity_W_mK"], props.conductivity_W_mK,
                      integ["liquid_convection_enhancement"], 8.0)
    assert got == pytest.approx(ua_eff_total_w_k(25, d, area, 5e-4, props, 1.0, cfg), rel=1e-9)


def _year(overrides=None):
    from src.design import space
    from src.weather import roles
    from src.weather.inventory import CURRENT_MEDOIDS
    w = roles.load_point_year("rajasthan", 0, CURRENT_MEDOIDS[0], 2018, "explore")
    out = rc.run_case("rajasthan", 0, "PureTemp 58", space.to_design(0.04, 0.296, 0.0236, "single-layer"),
                      design_bounds=space.geometry_bounds(), weather=w, tank_model="multinode", n_nodes=10,
                      compute_tes_metrics=True, night_day_stride=0, system_config_overrides=overrides)
    assert out["valid"], out["reason"]
    return out["tes"]["E_del45_annual_kWh"], out["metrics"]["residual_pct_of_collector"]


def test_year_run_is_bit_identical_with_explicit_c5_and_changes_with_c():
    base, _ = _year()
    c5, _ = _year({"pcm_integration": {"conduction_coefficient_c": 5.0}})
    c10, res = _year({"pcm_integration": {"conduction_coefficient_c": 10.0}})
    assert c5 == base
    assert c10 != base
    assert res < 1e-6
