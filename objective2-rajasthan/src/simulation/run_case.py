"""
src/simulation/run_case.py
=============================
Phase 3 / D2.3 — orchestrates ONE complete simulation case: a design vector
+ a climate regime + a shortlisted PCM + a demand scenario, run for one
full year of (real, medoid) hourly weather. This is the function Phase 4's
verification gates and Phase 5's DOE will both call — one row out, one
simulation in, never one row per timestep (framework doc Sec 6.2).

Everything state-specific is looked up through src/io_utils.py; nothing in
this module hard-codes "tamilnadu" — pass a different `state` string and it
runs identically for any other state's frozen inputs.
"""

from src.design.schema import DesignVector
from src.design.constraints import check_design
from src.io_utils import (
    load_system_config, load_design_bounds, get_regime, get_pcm_properties,
    load_hourly_weather, load_demand_profile,
)
from src.simulation.capsule_enthalpy import pcm_props_from_record
from src.simulation.demand_profile import load_demand_model
from src.simulation.tank_model import DesignRuntime, run_year

J_PER_KWH = 3.6e6


def run_case(state: str, cluster_id: int, pcm_name: str, design: DesignVector,
             system_config: dict = None, design_bounds: dict = None,
             volume_multiplier: float = 1.0, timing_shift_hours: float = 0.0,
             mains_temp_override_C: float = None, system_config_overrides: dict = None,
             pcm_record_overrides: dict = None, record_hourly: bool = True):
    """Returns a dict: {geometry, valid, reason, metrics, hourly (DataFrame)}.

    If the design is geometrically invalid, the simulator is never run
    (metrics=None, reason carries the rejection code) — mirrors the
    framework doc's "geometry engine rejects invalid designs transparently"
    requirement.
    """
    system_config = system_config or load_system_config()
    if system_config_overrides:
        system_config = _deep_merge(system_config, system_config_overrides)
    design_bounds = design_bounds or load_design_bounds()

    geom = check_design(design, system_config, design_bounds)
    if not geom["valid"]:
        return {"geometry": geom, "valid": False, "reason": geom["reason"], "metrics": None, "hourly": None}

    regime = get_regime(state, cluster_id)
    mains_temp_C = mains_temp_override_C if mains_temp_override_C is not None else regime["T_mains_est_C"]

    pcm_record = get_pcm_properties(state, pcm_name) if pcm_name is not None else None
    if pcm_record is not None and pcm_record_overrides:
        pcm_record = {**pcm_record, **pcm_record_overrides}
    pcm_props = (pcm_props_from_record(pcm_record, system_config["pcm_integration"]["melting_half_width_K"])
                 if pcm_record is not None else None)

    weather = load_hourly_weather(state, cluster_id)
    demand_df = load_demand_profile(state)
    demand_model = load_demand_model(demand_df, volume_multiplier, timing_shift_hours)

    n_capsule_effective = geom["n_capsule"] if pcm_props is not None else 0
    runtime = DesignRuntime(
        n_capsule=n_capsule_effective,
        capsule_diameter_m=geom["capsule_diameter_m"],
        capsule_area_m2=geom["capsule_surface_area_m2"],
        capsule_volume_m3=geom["capsule_volume_m3"],
        void_fraction=geom["void_fraction_used_for_hydraulics"],
        cross_section_area_m2=geom["tank_cross_section_area_m2"],
        bed_length_m=geom["stack_height_m"] if geom["stack_height_m"] > 0 else geom["tank_height_m"],
        flow_rate_kg_s=geom["flow_rate_kg_s"],
        tank_volume_m3=geom["tank_volume_m3"],
        tank_surface_area_m2=geom["tank_surface_area_m2"],
    )

    if pcm_props is None:
        # plain-tank baseline: dummy props never used because n_capsule=0
        from src.simulation.capsule_enthalpy import PCMThermalProps
        pcm_props = PCMThermalProps(Tm_C=57.0, latent_heat_J_kg=0.0, cp_solid_J_kgK=2000.0,
                                     cp_liquid_J_kgK=2000.0, conductivity_W_mK=0.2, density_kg_m3=800.0)

    result = run_year(weather, demand_model, mains_temp_C, runtime, pcm_props, system_config,
                       record_hourly=record_hourly)

    target_temp_C = system_config["delivery"]["target_temp_C"]
    cp_w = system_config["water"]["cp_J_kgK"]
    total_draw_kg = sum(demand_model.draw_mass_kg_for_hour(h % 24) for h in range(len(weather)))
    e_demand_ideal_kWh = total_draw_kg * cp_w * (target_temp_C - mains_temp_C) / J_PER_KWH
    e_unmet_kWh = result.energy["E_unmet_kWh"]
    solar_fraction = (1.0 - e_unmet_kWh / e_demand_ideal_kWh) if e_demand_ideal_kWh > 0 else None
    solar_fraction = min(max(solar_fraction, 0.0), 1.0) if solar_fraction is not None else None

    delivery_hours = int((result.hourly["T_w_C"] >= target_temp_C).sum()) if record_hourly and len(result.hourly) else None

    metrics = {
        "state": state, "cluster_id": cluster_id, "pcm_name": pcm_name,
        "mains_temp_C": mains_temp_C,
        "useful_energy_kWh": result.energy["E_load_kWh"],
        "solar_fraction": solar_fraction,
        "delivery_temp_hours": delivery_hours,
        "unmet_energy_kWh": e_unmet_kWh,
        "pump_energy_kWh": result.energy["E_pump_kWh"],
        "collector_energy_kWh": result.energy["E_collector_kWh"],
        "loss_energy_kWh": result.energy["E_loss_kWh"],
        "charge_energy_kWh": result.energy["E_charge_kWh"],
        "discharge_energy_kWh": result.energy["E_discharge_kWh"],
        "residual_pct_of_collector": result.energy["residual_pct_of_collector"],
        "pcm_mass_kg": n_capsule_effective * geom["capsule_volume_m3"] * pcm_props.density_kg_m3,
        "max_water_temp_C": result.max_water_temp_C,
        "max_pcm_temp_C": result.max_pcm_temp_C,
        "n_safety_violations": result.n_safety_violations,
        "final_f_melt": result.final_f_melt,
        "complete_melt_cycles": result.complete_melt_cycles,
        "n_hours_simulated": len(weather),
    }
    if record_hourly and len(result.hourly):
        metrics["mean_f_melt"] = float(result.hourly["f_melt"].mean())
        metrics["min_f_melt"] = float(result.hourly["f_melt"].min())
        metrics["max_f_melt"] = float(result.hourly["f_melt"].max())

    return {"geometry": geom, "valid": True, "reason": None, "metrics": metrics, "hourly": result.hourly}


def _deep_merge(base: dict, overrides: dict) -> dict:
    out = dict(base)
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out
