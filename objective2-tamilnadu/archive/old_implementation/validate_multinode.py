import time
from src.io_utils import load_system_config, load_design_bounds, get_regime, get_pcm_properties, load_hourly_weather, load_demand_profile
from src.design.schema import DesignVector
from src.design.constraints import check_design
from src.simulation.capsule_enthalpy import pcm_props_from_record
from src.simulation.demand_profile import load_demand_model
from src.simulation.tank_model import DesignRuntime, run_year as run_year_single
from src.simulation.tank_model_multinode import run_year_multinode

state = "tamilnadu"
sysconf = load_system_config()
bounds = load_design_bounds()
regime = get_regime(state, 0)
pcm_rec = get_pcm_properties(state, "n-Hexacosane (C26)")
weather = load_hourly_weather(state, 0)
demand_df = load_demand_profile(state)
demand = load_demand_model(demand_df)

design = DesignVector(0.07221581517059644, 32, 0.020656140788615572, capsule_arrangement="radial")
geom = check_design(design, sysconf, bounds)
print("geom valid:", geom["valid"], geom.get("reason"))

pcm_props = pcm_props_from_record(pcm_rec, sysconf["pcm_integration"]["melting_half_width_K"])

dr = DesignRuntime(
    n_capsule=geom["n_capsule"], capsule_diameter_m=geom["capsule_diameter_m"],
    capsule_area_m2=geom["capsule_surface_area_m2"], capsule_volume_m3=geom["capsule_volume_m3"],
    void_fraction=geom["void_fraction_used_for_hydraulics"], cross_section_area_m2=geom["tank_cross_section_area_m2"],
    bed_length_m=geom["stack_height_m"] if geom["stack_height_m"] > 0 else geom["tank_height_m"],
    flow_rate_kg_s=geom["flow_rate_kg_s"], tank_volume_m3=geom["tank_volume_m3"],
    tank_surface_area_m2=geom["tank_surface_area_m2"],
)
mains_C = regime["T_mains_est_C"]

t0 = time.time()
res_single = run_year_single(weather, demand, mains_C, dr, pcm_props, sysconf, record_hourly=True)
t_single = time.time() - t0
print(f"\nSINGLE-NODE  time={t_single:.2f}s  residual%={res_single.energy['residual_pct_of_collector']:.5f}  "
      f"useful_kWh={res_single.energy['E_load_kWh']:.1f}  max_water={res_single.max_water_temp_C:.2f}  "
      f"max_pcm={res_single.max_pcm_temp_C:.2f}  mean_f_melt={res_single.hourly['f_melt'].mean():.4f}")

import copy
sysconf_n1 = copy.deepcopy(sysconf)
sysconf_n1["tank"]["n_nodes"] = 1
t0 = time.time()
res_multi_n1 = run_year_multinode(weather, demand, mains_C, dr, pcm_props, sysconf_n1, record_hourly=True)
t_multi1 = time.time() - t0
print(f"\nMULTI-NODE N=1  time={t_multi1:.2f}s  residual%={res_multi_n1.energy['residual_pct_of_collector']:.5f}  "
      f"useful_kWh={res_multi_n1.energy['E_load_kWh']:.1f}  max_water={res_multi_n1.max_water_temp_C:.2f}  "
      f"max_pcm={res_multi_n1.max_pcm_temp_C:.2f}  mean_f_melt={res_multi_n1.hourly['f_melt'].mean():.4f}")

sysconf_n10 = copy.deepcopy(sysconf)
sysconf_n10["tank"]["n_nodes"] = 10
t0 = time.time()
res_multi_n10 = run_year_multinode(weather, demand, mains_C, dr, pcm_props, sysconf_n10, record_hourly=True)
t_multi10 = time.time() - t0
print(f"\nMULTI-NODE N=10  time={t_multi10:.2f}s  residual%={res_multi_n10.energy['residual_pct_of_collector']:.5f}  "
      f"useful_kWh={res_multi_n10.energy['E_load_kWh']:.1f}  max_water={res_multi_n10.max_water_temp_C:.2f}  "
      f"max_pcm={res_multi_n10.max_pcm_temp_C:.2f}  mean_f_melt={res_multi_n10.hourly['f_melt'].mean():.4f}")

print("\n--- comparison ---")
print(f"single vs N=1 useful_kWh diff: {res_multi_n1.energy['E_load_kWh'] - res_single.energy['E_load_kWh']:.2f} kWh "
      f"({100*(res_multi_n1.energy['E_load_kWh']/res_single.energy['E_load_kWh']-1):.2f}%)")
print(f"N=1 vs N=10 useful_kWh diff: {res_multi_n10.energy['E_load_kWh'] - res_multi_n1.energy['E_load_kWh']:.2f} kWh "
      f"({100*(res_multi_n10.energy['E_load_kWh']/res_multi_n1.energy['E_load_kWh']-1):.2f}%)")
