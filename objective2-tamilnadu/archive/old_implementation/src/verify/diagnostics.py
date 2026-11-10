"""
src/verify/diagnostics.py
============================
The diagnostic studies from her report's G11 and G13-G18, run on the
chosen designs. These do not change any selection -- they probe WHY the
chosen design behaves as it does, and each one is capable of contradicting
a claim made elsewhere in the report.

  G13  shield split          water-side vs PCM-side shield hours, like for
                              like against the water-only tank. Her
                              d_overheat is "positive by construction"
                              because the water-only tank has no PCM-side
                              throttle; the split is what makes that
                              statement checkable instead of circular.
  G14  interior-anchor       capsules at the stack centre vs bottom vs top.
       controls               Tests whether the "center" default is doing
                              work or is an arbitrary choice.
  G15  evening/night-serve   tau_hold,45 and tau_serve,45 decomposition.
       decomposition          Her finding was that night-serve DURATION is
                              NOT improved (capsules displace water) even
                              though evening ENERGY rises -- a negative
                              result she reports rather than buries.
  G16  stack-position        same as G14 but sweeping the anchor while
       sensitivity            holding everything else fixed, to size the
                              effect rather than just detect it.
  G17  widened-bounds        re-run with the design box widened, to show
       diagnostic             whether the optimum sits against a bound (in
                              which case the bound, not the physics, is
                              what chose it).
  G18  box-vertex ablation   the front WITHOUT the box-vertex step, to
                              demonstrate that the step mattered.
  G11  one-at-a-time         each design variable moved alone from the
       ablations              chosen design, to show local sensitivity.

Every study returns a DataFrame and writes a CSV, so the registry can pick
them up without re-running anything.
"""

import numpy as np
import pandas as pd

from src.io_utils import load_design_bounds, load_system_config
from src.parallel.runner import SimTask, run_tasks_parallel

ANCHORS = ["bottom", "center", "top"]


def _base_task(d, state, year, *, tag, n_nodes=10, dt=150.0, anchor="center",
                overrides=(), diameter=None, n_capsule=None, flow=None):
    return SimTask(
        task_id=f"{tag}_c{int(d['cluster_id'])}_y{year}",
        state=state, cluster_id=int(d["cluster_id"]), pcm_name=d["pcm_name"],
        capsule_diameter_m=float(diameter if diameter is not None else d["capsule_diameter_m"]),
        n_capsule=int(n_capsule if n_capsule is not None else d["n_capsule"]),
        flow_rate_kg_s=float(flow if flow is not None else d["flow_rate_kg_s"]),
        arrangement=d["arrangement"], model="multinode", n_nodes=n_nodes,
        stack_anchor=anchor, timestep_s=dt, year=year, paired_plain=True,
        system_config_overrides=tuple(overrides))


def g13_shield_split(designs, state, years, **kw):
    """Water-side vs PCM-side shield hours, with the water-only twin's
    water-side hours alongside."""
    tasks = [_base_task(d, state, y, tag="g13", **kw)
             for _, d in designs.iterrows() for y in years]
    df = run_tasks_parallel(tasks, label="G13 shield-split")
    keep = ["cluster_id", "pcm_name", "year", "valid", "d_overheat_h",
            "shield_hours_pcm_tank", "shield_hours_plain_tank", "n_shield_activations"]
    return df[[c for c in keep if c in df.columns]]


def g14_g16_stack_position(designs, state, years, **kw):
    """Anchor swept bottom/center/top -- G14's control and G16's
    sensitivity are the same experiment read two ways."""
    tasks = []
    for _, d in designs.iterrows():
        for anchor in ANCHORS:
            for y in years:
                t = _base_task(d, state, y, tag=f"g16_{anchor}", anchor=anchor, **kw)
                tasks.append(t)
    df = run_tasks_parallel(tasks, label="G14/G16 stack-position")
    df["stack_anchor"] = [t.stack_anchor for t in tasks]
    return df


def g17_widened_bounds(designs, state, years, widen: float = 1.5, **kw):
    """Move each design variable beyond its bound by `widen`x the box
    half-width, one at a time, to see whether the chosen design is pinned
    against a bound."""
    b = load_design_bounds()
    sysconf = load_system_config()
    rows = []
    tasks, labels = [], []
    for _, d in designs.iterrows():
        for var, key in [("capsule_diameter_m", "capsule_diameter_m"),
                          ("flow_rate_kg_s", "flow_rate_kg_s")]:
            lo, hi = b[key]["min"], b[key]["max"]
            span = hi - lo
            for direction, val in [("below", lo - widen * span * 0.1),
                                    ("above", hi + widen * span * 0.1)]:
                val = max(val, 1e-6)
                kwargs = {var.replace("capsule_diameter_m", "diameter").replace("flow_rate_kg_s", "flow"): val}
                for y in years:
                    tasks.append(_base_task(d, state, y, tag=f"g17_{var}_{direction}",
                                            **kwargs, **kw))
                    labels.append((int(d["cluster_id"]), var, direction, val))
    if not tasks:
        return pd.DataFrame()
    df = run_tasks_parallel(tasks, label="G17 widened-bounds")
    df["widened_var"] = [l[1] for l in labels]
    df["direction"] = [l[2] for l in labels]
    df["widened_value"] = [l[3] for l in labels]
    return df


def g11_one_at_a_time(designs, state, years, rel_steps=(-0.25, -0.1, 0.1, 0.25), **kw):
    """Each design variable moved alone from the chosen value."""
    tasks, labels = [], []
    for _, d in designs.iterrows():
        for var in ["capsule_diameter_m", "n_capsule", "flow_rate_kg_s"]:
            base = float(d[var])
            for step in rel_steps:
                val = base * (1.0 + step)
                kwargs = {"diameter": val} if var == "capsule_diameter_m" else \
                         {"n_capsule": max(1, int(round(val)))} if var == "n_capsule" else \
                         {"flow": val}
                for y in years:
                    tasks.append(_base_task(d, state, y, tag=f"g11_{var}_{step:+.2f}",
                                            **kwargs, **kw))
                    labels.append((int(d["cluster_id"]), var, step, val))
    df = run_tasks_parallel(tasks, label="G11 one-at-a-time")
    df["ablated_var"] = [l[1] for l in labels]
    df["rel_step"] = [l[2] for l in labels]
    df["ablated_value"] = [l[3] for l in labels]
    return df


def g15_serve_decomposition(designs, state, years, **kw):
    """tau_hold / tau_serve from the evening-coast scenario, PCM tank vs
    water-only twin. Expected (and reported either way) to show energy up
    but duration flat-to-down, because capsules displace water."""
    from src.io_utils import (get_regime, get_pcm_properties, load_demand_profile,
                              load_design_bounds as _lb)
    from src.design.constraints import check_design
    from src.design.schema import DesignVector
    from src.simulation.capsule_enthalpy import pcm_props_from_record
    from src.simulation.demand_profile import load_demand_model
    from src.simulation.tank_model import DesignRuntime
    from src.simulation.tank_model_multinode_fast import run_year_multinode_fast
    from src.metrics.tes_metrics import evening_scenario
    from src.parallel.runner import cached_weather_year, DUMMY_PCM
    import copy

    sysconf = copy.deepcopy(load_system_config())
    sysconf["tank"]["n_nodes"] = kw.get("n_nodes", 10)
    sysconf["solver"]["timestep_s"] = kw.get("dt", 150.0)
    bounds = _lb()
    demand = load_demand_model(load_demand_profile(state))
    rows = []
    for _, d in designs.iterrows():
        cid = int(d["cluster_id"])
        regime = get_regime(state, cid)
        props = pcm_props_from_record(get_pcm_properties(state, d["pcm_name"]),
                                      sysconf["pcm_integration"]["melting_half_width_K"])
        design = DesignVector(float(d["capsule_diameter_m"]), int(d["n_capsule"]),
                              float(d["flow_rate_kg_s"]), capsule_arrangement=d["arrangement"])
        geom = check_design(design, sysconf, bounds)
        if not geom["valid"]:
            continue
        for y in years:
            weather = cached_weather_year(state, cid, y)
            # 18:00 local on a mid-summer day; hour index found from the frame
            hod = weather["timestamp_utc"].dt.hour.to_numpy()
            start = int(np.argmax((np.arange(len(hod)) > 24 * 180) & (((hod + 5) % 24) == 18)))
            for label, n_caps, pp in [("pcm", geom["n_capsule"], props),
                                       ("plain", 0, DUMMY_PCM)]:
                dr = DesignRuntime(
                    n_capsule=n_caps, capsule_diameter_m=geom["capsule_diameter_m"],
                    capsule_area_m2=geom["capsule_surface_area_m2"],
                    capsule_volume_m3=geom["capsule_volume_m3"],
                    void_fraction=geom["void_fraction_used_for_hydraulics"],
                    cross_section_area_m2=geom["tank_cross_section_area_m2"],
                    bed_length_m=geom["stack_height_m"] or geom["tank_height_m"],
                    flow_rate_kg_s=geom["flow_rate_kg_s"],
                    tank_volume_m3=geom["tank_volume_m3"],
                    tank_surface_area_m2=geom["tank_surface_area_m2"])
                ev = evening_scenario(run_year_multinode_fast, weather, demand,
                                      regime["T_mains_est_C"], dr, pp, sysconf, start)
                rows.append({"cluster_id": cid, "pcm_name": d["pcm_name"], "year": y,
                             "tank": label, "tau_hold_45_h": ev.tau_hold_45_h,
                             "tau_serve_45_h": ev.tau_serve_45_h,
                             "serve_frac_45": ev.serve_frac_45})
    return pd.DataFrame(rows)
