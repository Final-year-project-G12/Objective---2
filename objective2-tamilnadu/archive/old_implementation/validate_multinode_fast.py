"""Equivalence + speed validation for the numba kernel
(src/simulation/tank_model_multinode_fast.py) against the pure-Python
reference (src/simulation/tank_model_multinode.py).

The fast kernel is only allowed into production if it reproduces the
reference's physics, so this asserts agreement on every quantity the
selection funnel and the robustness gates actually read -- not just
runtime. Tolerances are set for Thomas-vs-dense-LU rounding (~1e-10
relative), not for "close enough".
"""

import copy
import sys
import time

import numpy as np

from src.io_utils import (load_system_config, load_design_bounds, get_regime,
                          get_pcm_properties, load_hourly_weather, load_demand_profile)
from src.design.schema import DesignVector
from src.design.constraints import check_design
from src.simulation.capsule_enthalpy import pcm_props_from_record
from src.simulation.demand_profile import load_demand_model
from src.simulation.tank_model import DesignRuntime
from src.simulation.tank_model_multinode import run_year_multinode
from src.simulation.tank_model_multinode_fast import run_year_multinode_fast

state = "tamilnadu"
sysconf = load_system_config()
bounds = load_design_bounds()
regime = get_regime(state, 0)
pcm_rec = get_pcm_properties(state, "n-Hexacosane (C26)")
weather = load_hourly_weather(state, 0)
demand = load_demand_model(load_demand_profile(state))

design = DesignVector(0.07221581517059644, 32, 0.020656140788615572, capsule_arrangement="radial")
geom = check_design(design, sysconf, bounds)
print("geom valid:", geom["valid"], geom.get("reason"))

pcm_props = pcm_props_from_record(pcm_rec, sysconf["pcm_integration"]["melting_half_width_K"])
dr = DesignRuntime(
    n_capsule=geom["n_capsule"], capsule_diameter_m=geom["capsule_diameter_m"],
    capsule_area_m2=geom["capsule_surface_area_m2"], capsule_volume_m3=geom["capsule_volume_m3"],
    void_fraction=geom["void_fraction_used_for_hydraulics"],
    cross_section_area_m2=geom["tank_cross_section_area_m2"],
    bed_length_m=geom["stack_height_m"] if geom["stack_height_m"] > 0 else geom["tank_height_m"],
    flow_rate_kg_s=geom["flow_rate_kg_s"], tank_volume_m3=geom["tank_volume_m3"],
    tank_surface_area_m2=geom["tank_surface_area_m2"],
)
mains_C = regime["T_mains_est_C"]

SHIELD_MODE = sys.argv[1] if len(sys.argv) > 1 else "predictive"
conf10 = copy.deepcopy(sysconf)
conf10["tank"]["n_nodes"] = 10
conf10["safety"]["shield_predictive"] = (SHIELD_MODE == "predictive")
print(f"shield mode: {SHIELD_MODE} (shield_predictive={conf10['safety']['shield_predictive']})")

t0 = time.time()
ref = run_year_multinode(weather, demand, mains_C, dr, pcm_props, conf10, record_hourly=True)
t_ref = time.time() - t0
print(f"\nREFERENCE (pure Python)  N=10  time={t_ref:.2f}s")

t0 = time.time()
fast_cold = run_year_multinode_fast(weather, demand, mains_C, dr, pcm_props, conf10, record_hourly=True)
t_fast_cold = time.time() - t0

t0 = time.time()
fast = run_year_multinode_fast(weather, demand, mains_C, dr, pcm_props, conf10, record_hourly=True)
t_fast = time.time() - t0
print(f"NUMBA KERNEL             N=10  time={t_fast:.3f}s  (first call incl. JIT compile: {t_fast_cold:.2f}s)")
print(f"SPEEDUP (warm): {t_ref / t_fast:.1f}x")

print("\n--- equivalence ---")
checks = []


def cmp(label, a, b, rtol=1e-8, atol=0.0):
    a, b = float(a), float(b)
    denom = max(abs(a), 1e-12)
    rel = abs(a - b) / denom
    ok = abs(a - b) <= atol + rtol * denom
    checks.append((label, ok, rel))
    print(f"  {'OK ' if ok else 'FAIL'} {label:34s} ref={a:16.8f}  fast={b:16.8f}  rel={rel:.3e}")


for key in ["E_collector_kWh", "E_load_kWh", "E_loss_kWh", "E_unmet_kWh",
            "E_charge_kWh", "E_discharge_kWh", "E_initial_kWh", "E_final_kWh",
            "residual_pct_of_collector"]:
    cmp(key, ref.energy[key], fast.energy[key], rtol=1e-7)

cmp("max_water_temp_C", ref.max_water_temp_C, fast.max_water_temp_C, rtol=1e-9)
cmp("max_pcm_temp_C", ref.max_pcm_temp_C, fast.max_pcm_temp_C, rtol=1e-9)
cmp("final_f_melt", ref.final_f_melt, fast.final_f_melt, rtol=1e-7, atol=1e-9)
cmp("n_safety_violations", ref.n_safety_violations, fast.n_safety_violations, rtol=0.0, atol=0.0)
cmp("n_shield_activations", ref.n_shield_activations, fast.n_shield_activations, rtol=0.0, atol=0.0)
cmp("complete_melt_cycles", ref.complete_melt_cycles, fast.complete_melt_cycles, rtol=0.0, atol=0.0)

print("\n--- hourly series (whole-year) ---")
for col in ["T_w_C", "T_w_bottom_C", "T_pcm_C", "f_melt",
            "Q_collector_Wh", "Q_load_Wh", "Q_pcm_Wh", "Q_loss_Wh", "Q_unmet_Wh"]:
    a = ref.hourly[col].to_numpy(dtype=float)
    b = fast.hourly[col].to_numpy(dtype=float)
    max_abs = float(np.max(np.abs(a - b)))
    scale = max(float(np.max(np.abs(a))), 1e-12)
    rel = max_abs / scale
    ok = rel < 1e-6
    checks.append((f"hourly:{col}", ok, rel))
    print(f"  {'OK ' if ok else 'FAIL'} {col:16s} max|diff|={max_abs:.6e}  rel-to-peak={rel:.3e}")

n_fail = sum(1 for _, ok, _ in checks if not ok)
print(f"\nresidual: ref={ref.energy['residual_pct_of_collector']:.5f}%  "
      f"fast={fast.energy['residual_pct_of_collector']:.5f}%  (gate: <0.5%)")
assert fast.energy["residual_pct_of_collector"] < 0.5, "fast kernel fails the Gate-1 energy gate"
assert n_fail == 0, f"{n_fail} equivalence check(s) FAILED -- fast kernel is not physics-equivalent"
print(f"\nPASS: numba kernel is equivalent to the reference on all {len(checks)} checks, "
      f"{t_ref / t_fast:.1f}x faster.")
