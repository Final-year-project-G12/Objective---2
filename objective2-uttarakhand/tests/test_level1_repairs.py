"""
tests/test_level1_repairs.py
===============================
G2 (O2, 2026-10-26) — WP2 Level 1 defect repairs: PCM mass from the
inner volume, capsule-wall thermal mass, exact (invertible) enthalpy with wall,
29-Feb removal, and always-on per-run summary outputs.
"""

import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.design.schema import DesignVector
from src.io_utils import load_hourly_weather, get_pcm_properties
from src.simulation import run_case as rc
from src.simulation.capsule_enthalpy import (
    PCMThermalProps, enthalpy_of_temperature, temperature_and_liquid_fraction_of_enthalpy,
)
from src.simulation.capsule_mass import capsule_masses, wall_cp_per_kg_pcm, AL_DENSITY_KG_M3
from src.weather.inventory import REGIMES


def test_pcm_mass_uses_inner_volume_exactly():
    n, d, t, rho = 37, 0.040, 0.0008, 800.0
    m = capsule_masses(n, d, t, rho)
    expected = n * math.pi / 6.0 * (d - 2 * t) ** 3 * rho
    assert m["m_pcm_kg"] == pytest.approx(expected, rel=1e-6)
    # PCM + wall volumes tile the outer sphere exactly
    v_wall = m["m_wall_kg"] / AL_DENSITY_KG_M3
    assert m["v_pcm_total_m3"] + v_wall == pytest.approx(m["v_outer_total_m3"], rel=1e-9)


def test_old_overstatement_matches_plan_arithmetic():
    # plan §3.2 item 3: outer-volume mass overstates PCM by 11.5 % at 40 mm, 5.9 % at 80 mm
    for d, pct in ((0.040, 11.5), (0.080, 5.9)):
        m = capsule_masses(1, d, 0.0008, 800.0)
        outer = math.pi / 6.0 * d ** 3 * 800.0
        assert 100 * (1 - m["m_pcm_kg"] / outer) == pytest.approx(pct, abs=0.1)


def test_wall_that_swallows_the_capsule_is_rejected():
    with pytest.raises(ValueError):
        capsule_masses(1, 0.001, 0.0008, 800.0)


@pytest.mark.parametrize("wall_cp", [0.0, 410.0])
def test_enthalpy_is_invertible_and_monotone_with_wall(wall_cp):
    p = PCMThermalProps(Tm_C=45.0, latent_heat_J_kg=200e3, cp_solid_J_kgK=2000.0, cp_liquid_J_kgK=2200.0,
                        conductivity_W_mK=0.2, density_kg_m3=800.0, wall_cp_J_kgK=wall_cp)
    prev = -1e18
    for T in [10, 30, 43.9, 44.0, 44.5, 45.0, 45.5, 46.0, 46.1, 60, 80]:
        h = enthalpy_of_temperature(T, p)
        assert h > prev
        prev = h
        T_back, f = temperature_and_liquid_fraction_of_enthalpy(h, p)
        assert T_back == pytest.approx(T, abs=1e-9)
    # energy to cross the whole band = latent + wall sensible over the band
    dh = enthalpy_of_temperature(p.Tl_C, p) - enthalpy_of_temperature(p.Ts_C, p)
    assert dh == pytest.approx(200e3 + wall_cp * 2.0, rel=1e-12)


def test_wall_adds_sensible_heat_capacity():
    base = PCMThermalProps(45.0, 200e3, 2000.0, 2200.0, 0.2, 800.0)
    with_wall = PCMThermalProps(45.0, 200e3, 2000.0, 2200.0, 0.2, 800.0, wall_cp_J_kgK=500.0)
    d_base = enthalpy_of_temperature(30, base) - enthalpy_of_temperature(20, base)
    d_wall = enthalpy_of_temperature(30, with_wall) - enthalpy_of_temperature(20, with_wall)
    assert d_wall - d_base == pytest.approx(500.0 * 10.0)


def test_wall_cp_per_kg_pcm():
    m = capsule_masses(10, 0.05, 0.0008, 800.0)
    assert wall_cp_per_kg_pcm(m, 900.0) == pytest.approx(m["m_wall_kg"] * 900.0 / m["m_pcm_kg"])


def test_no_29_feb_and_8760_hours_every_regime():
    for c in REGIMES:
        w = load_hourly_weather("uttarakhand", c)
        assert len(w) == 8760
        assert not w["local_date"].astype(str).str.endswith("-02-29").any()
    assert len(load_hourly_weather("uttarakhand", 1, drop_29_feb=False)) == 8784


def test_run_case_reports_inner_mass_and_summaries_without_hourly():
    pcm = "RT44HC"
    dv = DesignVector(capsule_diameter_m=0.0429, n_capsule=37, flow_rate_kg_s=0.0428,
                      capsule_arrangement="single-layer")
    out = rc.run_case("uttarakhand", 0, pcm, dv, record_hourly=False)["metrics"]
    rho = get_pcm_properties("uttarakhand", pcm)["density_solid_kg_m3"]
    assert out["pcm_mass_kg"] == pytest.approx(37 * math.pi / 6 * (0.0429 - 0.0016) ** 3 * rho, rel=1e-6)
    assert out["capsule_wall_mass_kg"] > 0
    for k in ("mean_f_melt", "min_f_melt", "max_f_melt", "delivery_temp_hours"):
        assert out[k] is not None
    assert out["pump_energy_meaningful"] is False
    assert out["residual_pct_of_collector"] <= 0.1
