"""
tests/test_tes_metrics.py
============================
G3 (O2, 2026-10-26) — WP1 metric unit tests: hand-calculated synthetic
days, closure on a real run, agreement of E_del,45 with solar_fraction, and an
analytic no-draw cool-down for tau_hold,45.
"""

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.design.schema import DesignVector
from src.io_utils import load_hourly_weather, load_system_config
from src.metrics import tes_metrics as tm
from src.simulation import run_case as rc
from src.simulation.capsule_enthalpy import PCMThermalProps

KWH = 3.6e6
CP = 4180.0
TARGET, MAINS = 45.0, 25.0


def _ctx(m_w=50.0, m_pcm=0.0, props=None):
    return {"m_w_kg": m_w, "m_pcm_kg": m_pcm, "pcm_props": props, "cp_w": CP, "mains_temp_C": MAINS,
            "target_C": TARGET, "has_pcm": props is not None}


def _frame(T_w, T_pcm, hours=48):
    """Constant-state synthetic hourly frame (no draws until a test injects them)."""
    h = np.arange(hours)
    return pd.DataFrame({"hour_index": h, "hour_of_day": h % 24, "T_w_C": T_w, "T_pcm_C": T_pcm,
                         "Q_collector_Wh": 0.0, "Q_load_Wh": 0.0, "Q_loss_Wh": 0.0, "draw_kg": 0.0,
                         "vol_ge_target_kg": 0.0, "Edel_target_Wh": 0.0, "T_w_min_C": T_w, "T_w_max_C": T_w,
                         "T_pcm_max_C": T_pcm, "f_melt_min": 0.0, "f_melt_max": 0.0})


# ---- the three synthetic days (plan WP1 acceptance 2), plain tank, 50 kg water, mains 25 C -------------
def test_day1_hot_tank_60C():
    ctx = _ctx()
    assert tm.stored_energy_kWh([60.0], [60.0], ctx)[0] == pytest.approx(50 * CP * 35 / KWH)
    assert tm.recoverable_energy_kWh([60.0], [60.0], ctx)[0] == pytest.approx(50 * CP * 15 / KWH)   # 0.8708 kWh


def test_day2_tank_below_threshold_recovers_nothing():
    ctx = _ctx()
    assert tm.recoverable_energy_kWh([40.0], [40.0], ctx)[0] == 0.0
    assert tm.stored_energy_kWh([40.0], [40.0], ctx)[0] == pytest.approx(50 * CP * 15 / KWH)


def test_day3_window_delivery_and_compliance():
    # 100 kg drawn at 19:00 from a 60 C tank (delivers 100*cp*(45-25)) and 100 kg at 07:00 from 40 C (100*cp*15)
    df = _frame(60.0, 60.0)
    e19, e07 = 100 * CP * 20 / 3600, 100 * CP * 15 / 3600          # Wh
    df.loc[df.hour_of_day == 19, ["draw_kg", "vol_ge_target_kg", "Edel_target_Wh"]] = [100.0, 100.0, e19]
    df.loc[df.hour_of_day == 7, ["draw_kg", "vol_ge_target_kg", "Edel_target_Wh"]] = [100.0, 0.0, e07]
    summ = {"E_stored_initial_kWh": 0.0, "sum_abs_df": 0.0, "draw_kg_total": 400.0, "vol_ge_target_kg": 200.0}
    out = tm.compute_all(df, summ, _ctx())
    assert out["E_del45_annual_kWh"] == pytest.approx(2 * (e19 + e07) / 1000.0)
    assert out["E_del45_window_kWh"] == pytest.approx(2 * (e19 + e07) / 1000.0)   # 19:00 and 07:00 are in 18:00-09:00
    assert out["compliance_vol_frac_annual"] == pytest.approx(0.5)
    assert out["E_rec45_mean_kWh"] == pytest.approx(50 * CP * 15 / KWH)


def test_pcm_recoverable_energy_hand_calc():
    props = PCMThermalProps(Tm_C=50.0, latent_heat_J_kg=200e3, cp_solid_J_kgK=2000.0, cp_liquid_J_kgK=2200.0,
                            conductivity_W_mK=0.2, density_kg_m3=800.0, melting_half_width_K=1.0)
    ctx = _ctx(m_w=50.0, m_pcm=1.0, props=props)
    # liquid at 60 C: h(60)-h(45) = 2000*(49-45) + 200e3 + 2200*(60-51) = 227.8 kJ
    e = tm.recoverable_energy_kWh([45.0], [60.0], ctx)[0]
    assert e == pytest.approx(227800.0 / KWH)
    # a PCM that melts BELOW the threshold only gives its sensible heat above 45 C
    low = PCMThermalProps(Tm_C=40.0, latent_heat_J_kg=200e3, cp_solid_J_kgK=2000.0, cp_liquid_J_kgK=2200.0,
                          conductivity_W_mK=0.2, density_kg_m3=800.0, melting_half_width_K=1.0)
    e_low = tm.recoverable_energy_kWh([45.0], [60.0], _ctx(50.0, 1.0, low))[0]
    assert e_low == pytest.approx(2200.0 * 15 / KWH)
    # no double counting: stored PCM energy at T_pcm equals m*(h(T)-h(T_mains)) exactly
    assert tm.stored_energy_kWh([MAINS], [60.0], ctx)[0] == pytest.approx(
        (tm.enthalpy_of_temperature(60.0, props) - tm.enthalpy_of_temperature(MAINS, props)) / KWH)


def test_crossing_interpolation():
    assert tm.crossing_hours(60.0, [50.0, 40.0], 45.0) == (pytest.approx(1.5), False)
    assert tm.crossing_hours(40.0, [39.0], 45.0) == (0.0, False)
    assert tm.crossing_hours(60.0, [59.0, 58.0], 45.0) == (2.0, True)


# ---- real-simulator checks --------------------------------------------------------------------------
def test_closure_and_agreement_with_solar_fraction(monkeypatch):
    # Full year: the 0.1 % criterion is an annual one (a 30-day January slice has only ~90 kWh of
    # collector energy, so the same absolute error reads 0.34 % there -- identical in the solver's own
    # accumulator, which is why this metric is trusted).
    dv = DesignVector(capsule_diameter_m=0.0429, n_capsule=37, flow_rate_kg_s=0.0428,
                      capsule_arrangement="single-layer")
    out = rc.run_case("uttarakhand", 0, "RT44HC", dv, compute_tes_metrics=True, night_day_stride=100)
    tes, met = out["tes"], out["metrics"]
    assert tes["closure_residual_pct"] <= 0.1                      # recomputed from hourly records
    assert tes["closure_residual_pct"] == pytest.approx(met["residual_pct_of_collector"], abs=1e-6)
    # E_del,45 reproduces solar_fraction: SF = E_del45 / (m cp (45 - T_mains)) while T_w >= T_mains
    target = load_system_config()["delivery"]["target_temp_C"]            # 50 C for Uttarakhand (45 C elsewhere)
    e_ideal = out["hourly"]["draw_kg"].sum() * CP * (target - met["mains_temp_C"]) / KWH
    # solar_fraction counts a draw taken while the tank is colder than the mains as NEGATIVE delivery; E_del,45
    # clips that at zero (water colder than mains is not useful heat). So E_del,45/E_ideal >= SF, and the gap is
    # exactly that clipped (cold-tank winter-night) energy -- small here.
    sf_from_edel = tes["E_del45_annual_kWh"] / e_ideal
    assert 0.0 <= sf_from_edel - met["solar_fraction"] < 2e-3
    assert 0.0 <= tes["compliance_vol_frac_annual"] <= 1.0
    assert tes["E_rec45_max_kWh"] >= tes["E_rec45_mean_kWh"] >= 0.0
    assert len(out["night_daily"]) >= 1


def test_tau_hold_matches_analytic_cooldown(monkeypatch):
    # No draw, no sun, constant 25 C ambient, plain tank starting at 60 C: Newton cooling
    # T(t) = Tamb + (T0-Tamb) exp(-UA t / C)  =>  t45 = C/UA * ln((T0-Tamb)/(45-Tamb)).
    n = 400
    w = pd.DataFrame({"timestamp_utc": pd.date_range("2025-01-01", periods=n, freq="h", tz="UTC"),
                      "GHI_Wm2": 0.0, "T_amb_C": 25.0, "local_hour": np.arange(n) % 24,
                      "local_date": "2025-01-01"})
    monkeypatch.setattr(rc, "load_hourly_weather", lambda s, c, **kw: w)
    dv = DesignVector(capsule_diameter_m=0.05, n_capsule=16, flow_rate_kg_s=0.03, capsule_arrangement="staggered")
    out = rc.run_case("uttarakhand", 0, None, dv, volume_multiplier=0.0, initial_state={"T_w_C": 60.0},
                      compute_tes_metrics=True)
    cfg = load_system_config()
    g = out["geometry"]
    C = g["tank_volume_m3"] * cfg["water"]["density_kg_m3"] * cfg["water"]["cp_J_kgK"]
    UA = cfg["tank"]["U_tank_W_m2K"] * g["tank_surface_area_m2"]
    target = cfg["delivery"]["target_temp_C"]                                   # the simulator's threshold (50 C here)
    t45 = C / UA * math.log((60.0 - 25.0) / (target - 25.0)) / 3600.0           # hours from t=0
    nd = out["night_daily"]
    assert 18 < t45 < 66                                                        # 45 C: ~56 h; 50 C (Uttarakhand): ~31 h
    for k in range(3):                                                          # day starts at t = 18 + 24k h
        t_start = 18 + 24 * k
        expected = t45 - t_start if t_start < t45 else 0.0                      # already below target at the start -> 0
        assert nd["tau_hold_h"].iloc[k] == pytest.approx(expected, abs=0.05)
