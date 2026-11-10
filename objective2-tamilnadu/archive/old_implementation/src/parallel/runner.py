"""
src/parallel/runner.py
=========================
Process-parallel batch simulation driver -- the execution layer every
expensive stage of the Rajasthan-method chain runs through (Sobol DOE,
Taguchi screening, NSGA-II generations, active-learning rounds, dense-grid
cross-check, repeatability band, robustness Monte Carlo, the diagnostic
studies).

THREE SEPARATE SPEEDUPS, STACKED
--------------------------------
1. Compiled kernel (src/simulation/tank_model_multinode_fast.py) -- the
   per-year cost itself.
2. Worker-side input caching (below). The serial path reloads, per case,
   an 8760-row weather CSV, the demand profile, the PCM database and two
   YAML configs FROM DISK. At a few thousand DOE cases that parse cost is
   on the order of the physics. Here each worker process parses each
   input at most once and reuses the parsed object for every case it is
   handed.
3. Process-level fan-out across cores. The simulator is pure CPU-bound
   Python/numba with no shared state between cases, so cases are
   embarrassingly parallel; threads would be useless (the GIL is held
   through the numpy/pandas setup around each run), processes are not.

WHY PROCESSES AND NOT A numba prange INSIDE THE KERNEL: the year loop is
strictly sequential (each substep's state feeds the next), so there is no
inner loop to parallelize. The parallelism available is ACROSS cases, and
that is where it is taken.

WORKER WARM-UP: the numba kernel is compiled with cache=True, and
warm_jit() is called in the PARENT before the pool is created, so the
on-disk compilation cache exists and each worker loads it (~0.2 s)
instead of all of them JIT-compiling the same kernel simultaneously.

THREAD OVERSUBSCRIPTION GUARD: numpy's BLAS backend spawns its own thread
pool per process; 12 worker processes each spawning 12 BLAS threads is
144 threads fighting over 12 cores. run_tasks_parallel() pins each
worker's BLAS/OMP thread count to 1 before the children are spawned (they
inherit the environment), so the only parallelism is the one this module
controls.
"""

import atexit
import multiprocessing
import os
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from src.io_utils import (BASE_DIR, load_system_config, load_design_bounds, get_regime,
                          get_pcm_properties, load_hourly_weather, load_demand_profile)
from src.design.schema import DesignVector
from src.design.constraints import check_design
from src.design.volume_fraction import (n_capsule_for_fraction, achieved_fraction,
                                        design_from_fraction)
from src.simulation.capsule_enthalpy import PCMThermalProps, pcm_props_from_record
from src.simulation.demand_profile import load_demand_model
from src.simulation.tank_model import DesignRuntime, run_year
from src.simulation.tank_model_multinode_fast import run_year_multinode_fast
from src.metrics.tes_metrics import e_del_target, gain_vs_plain, d_overheat, draw_mass_table

J_PER_KWH = 3.6e6

# A no-PCM baseline never touches PCM properties (n_capsule=0 short-circuits
# every PCM term), but run_year still wants a props object.
DUMMY_PCM = PCMThermalProps(Tm_C=57.0, latent_heat_J_kg=0.0, cp_solid_J_kgK=2000.0,
                             cp_liquid_J_kgK=2000.0, conductivity_W_mK=0.2, density_kg_m3=800.0)


# ---------------------------------------------------------------- caches
# lru_cache at module level == one cache per worker PROCESS, populated on
# that worker's first task and reused for every later task it receives.

@lru_cache(maxsize=1)
def cached_system_config():
    return load_system_config()


@lru_cache(maxsize=1)
def cached_design_bounds():
    return load_design_bounds()


@lru_cache(maxsize=8)
def cached_regime(state: str, cluster_id: int):
    return get_regime(state, cluster_id)


@lru_cache(maxsize=64)
def cached_pcm_props(state: str, pcm_name: str, half_width_K: float):
    return pcm_props_from_record(get_pcm_properties(state, pcm_name), half_width_K)


@lru_cache(maxsize=4)
def cached_demand(state: str, volume_multiplier: float, timing_shift_hours: float):
    return load_demand_model(load_demand_profile(state), volume_multiplier, timing_shift_hours)


@lru_cache(maxsize=8)
def cached_weather(state: str, cluster_id: int):
    """The regime's own single frozen medoid year (Objective 1 output)."""
    return load_hourly_weather(state, cluster_id)


@lru_cache(maxsize=8)
def _cached_weather_multiyear(state: str, cluster_id: int):
    path = BASE_DIR / "data" / "weather" / f"weather_regime_{state}_cluster{cluster_id}_hourly_multiyear.csv"
    df = pd.read_csv(path, parse_dates=["timestamp_utc"])
    return df.sort_values("timestamp_utc").reset_index(drop=True)


@lru_cache(maxsize=256)
def cached_weather_year(state: str, cluster_id: int, year: int):
    """One calendar year out of the 15-year fetch (src/weather/
    fetch_multiyear_weather.py) -- the explore/select/test year roles run
    through here."""
    df = _cached_weather_multiyear(state, cluster_id)
    out = df[df["year"] == year].reset_index(drop=True)
    if len(out) == 0:
        raise ValueError(f"no weather rows for {state} cluster {cluster_id} year {year}")
    return out


def _weather_for(task):
    w = (cached_weather_year(task.state, task.cluster_id, task.year) if task.year is not None
         else cached_weather(task.state, task.cluster_id))
    if task.ghi_multiplier != 1.0 or task.tamb_delta_C != 0.0:
        w = w.copy()
        w["GHI_Wm2"] = (w["GHI_Wm2"] * task.ghi_multiplier).clip(lower=0.0)
        w["T_amb_C"] = w["T_amb_C"] + task.tamb_delta_C
    return w


def _deep_merge(base: dict, overrides: dict) -> dict:
    out = dict(base)
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


# ----------------------------------------------------------------- tasks

@dataclass(frozen=True)
class SimTask:
    """One simulation request. Deliberately small and immutable: this is
    what crosses the process boundary, so it carries IDs and numbers, never
    DataFrames or config dicts (the worker resolves those from its own
    cache)."""
    task_id: str
    state: str
    cluster_id: int
    pcm_name: object                      # str, or None for the water-only tank
    capsule_diameter_m: float
    flow_rate_kg_s: float
    # Exactly ONE of these two specifies how much PCM. pcm_volume_fraction
    # is the v3.0 searched variable (design_bounds_shared.yaml); n_capsule
    # is kept for studies that genuinely vary the count directly (the
    # capsule-count ablation) and for reproducing v2.0 cases.
    pcm_volume_fraction: object = None
    n_capsule: object = None
    arrangement: str = "staggered"
    model: str = "multinode"              # "multinode" (confirm) | "single" (search)
    n_nodes: int = 10
    stack_anchor: str = "center"
    timestep_s: float = None              # None = whatever system_config says
    year: object = None                   # int calendar year, or None = frozen medoid year
    volume_multiplier: float = 1.0
    timing_shift_hours: float = 0.0
    ghi_multiplier: float = 1.0
    tamb_delta_C: float = 0.0
    paired_plain: bool = False            # also run the water-only twin -> g_window/g_annual/d_overheat
    pcm_property_overrides: tuple = ()    # (("TC_W_mK", 0.21), ...) for the property-sensitivity studies
    # Dotted-path system_config overrides, e.g.
    # (("safety.max_pcm_temp_C", 75.0), ("collector.area_m2", 2.0)).
    # A tuple of pairs rather than a dict so SimTask stays frozen/hashable
    # and cheap to pickle across the process boundary.
    system_config_overrides: tuple = ()


def _config_for(task) -> dict:
    overrides = {"tank": {"n_nodes": task.n_nodes, "stack_anchor": task.stack_anchor}}
    if task.timestep_s is not None:
        overrides["solver"] = {"timestep_s": task.timestep_s}
    for dotted, value in task.system_config_overrides:
        node = overrides
        parts = dotted.split(".")
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = value
    return _deep_merge(cached_system_config(), overrides)


def _runtime_from_geom(geom, n_capsule_effective) -> DesignRuntime:
    return DesignRuntime(
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


def simulate_one(task: SimTask) -> dict:
    """Runs ONE task and returns a flat dict of scalars (no DataFrames --
    hourly series stay inside the worker, so inter-process traffic is a
    few hundred bytes per case instead of a few hundred kilobytes).

    An invalid geometry is a RESULT, not an error: it comes back with
    valid=False and the rejection reason, exactly as run_case() does, so a
    DOE/optimizer can count and plot its own rejected region.
    """
    sysconf = _config_for(task)
    bounds = cached_design_bounds()

    if (task.pcm_volume_fraction is None) == (task.n_capsule is None):
        raise ValueError(f"task {task.task_id}: specify exactly one of "
                         f"pcm_volume_fraction or n_capsule")
    if task.pcm_volume_fraction is not None:
        n_capsule = n_capsule_for_fraction(task.pcm_volume_fraction,
                                           task.capsule_diameter_m, sysconf)
    else:
        n_capsule = int(task.n_capsule)

    design = DesignVector(task.capsule_diameter_m, n_capsule, task.flow_rate_kg_s,
                          capsule_arrangement=task.arrangement)
    geom = check_design(design, sysconf, bounds)
    base = {"task_id": task.task_id, "cluster_id": task.cluster_id, "pcm_name": task.pcm_name,
            "capsule_diameter_m": task.capsule_diameter_m, "n_capsule": n_capsule,
            "pcm_volume_fraction_requested": task.pcm_volume_fraction,
            # The ACHIEVED fraction, not the requested one: n_capsule is an
            # integer, so the request is generally not hit exactly, and it
            # is the achieved value that describes the physics actually run.
            "pcm_volume_fraction": achieved_fraction(n_capsule, task.capsule_diameter_m, sysconf),
            "flow_rate_kg_s": task.flow_rate_kg_s, "arrangement": task.arrangement,
            "model": task.model, "n_nodes": task.n_nodes if task.model == "multinode" else 1,
            "timestep_s": sysconf["solver"]["timestep_s"],
            "year": task.year, "valid": bool(geom["valid"]), "reason": geom.get("reason")}
    if not geom["valid"]:
        return base

    regime = cached_regime(task.state, task.cluster_id)
    mains_C = regime["T_mains_est_C"]
    weather = _weather_for(task)
    demand = cached_demand(task.state, task.volume_multiplier, task.timing_shift_hours)
    half_width = sysconf["pcm_integration"]["melting_half_width_K"]

    if task.pcm_name is None:
        pcm_props, n_caps = DUMMY_PCM, 0
    elif task.pcm_property_overrides:
        rec = {**get_pcm_properties(task.state, task.pcm_name), **dict(task.pcm_property_overrides)}
        pcm_props, n_caps = pcm_props_from_record(rec, half_width), geom["n_capsule"]
    else:
        pcm_props = cached_pcm_props(task.state, task.pcm_name, half_width)
        n_caps = geom["n_capsule"]

    run_fn = run_year if task.model == "single" else run_year_multinode_fast
    runtime = _runtime_from_geom(geom, n_caps)

    t0 = time.perf_counter()
    res = run_fn(weather, demand, mains_C, runtime, pcm_props, sysconf, record_hourly=True)
    wall_s = time.perf_counter() - t0

    cp_w = sysconf["water"]["cp_J_kgK"]
    target_C = sysconf["delivery"]["target_temp_C"]
    n_days, rem_hours = divmod(len(weather), 24)
    table = draw_mass_table(demand)
    total_draw_kg = float(n_days * table.sum() + table[:rem_hours].sum())
    e_demand_ideal = total_draw_kg * cp_w * (target_C - mains_C) / J_PER_KWH
    sf = (1.0 - res.energy["E_unmet_kWh"] / e_demand_ideal) if e_demand_ideal > 0 else None
    sf = min(max(sf, 0.0), 1.0) if sf is not None else None

    out = {
        **base,
        "mains_temp_C": mains_C,
        "useful_energy_kWh": res.energy["E_load_kWh"],
        "solar_fraction": sf,
        "unmet_energy_kWh": res.energy["E_unmet_kWh"],
        "collector_energy_kWh": res.energy["E_collector_kWh"],
        "loss_energy_kWh": res.energy["E_loss_kWh"],
        "charge_energy_kWh": res.energy["E_charge_kWh"],
        "discharge_energy_kWh": res.energy["E_discharge_kWh"],
        "residual_pct_of_collector": res.energy["residual_pct_of_collector"],
        "pcm_mass_kg": n_caps * geom["capsule_volume_m3"] * pcm_props.density_kg_m3,
        "max_water_temp_C": res.max_water_temp_C,
        "max_pcm_temp_C": res.max_pcm_temp_C,
        "n_safety_violations": res.n_safety_violations,
        "n_shield_activations": res.n_shield_activations,
        "final_f_melt": res.final_f_melt,
        "complete_melt_cycles": res.complete_melt_cycles,
        "mean_f_melt": float(res.hourly["f_melt"].mean()),
        "delivery_temp_hours": int((res.hourly["T_w_C"] >= target_C).sum()),
        "e_del_45_annual_kWh": e_del_target(res.hourly, demand, mains_C, cp_w, target_C, False),
        "e_del_45_window_kWh": e_del_target(res.hourly, demand, mains_C, cp_w, target_C, True),
        "n_hours_simulated": len(weather),
        "sim_wall_s": wall_s,
    }

    # ---- paired water-only twin: identical flow/weather/demand/geometry,
    # zero capsules. This is what g_window and d_overheat are differences
    # AGAINST, and it is run here, in the same worker, so the comparison is
    # never made across differently-configured runs.
    if task.paired_plain and task.pcm_name is not None:
        plain_runtime = _runtime_from_geom(geom, 0)
        res_plain = run_fn(weather, demand, mains_C, plain_runtime, DUMMY_PCM, sysconf,
                           record_hourly=True)
        out["g_annual_kWh"] = gain_vs_plain(res.hourly, res_plain.hourly, demand, mains_C,
                                            cp_w, target_C, window_only=False)
        out["g_window_kWh"] = gain_vs_plain(res.hourly, res_plain.hourly, demand, mains_C,
                                            cp_w, target_C, window_only=True)
        out.update(d_overheat(res.hourly, res_plain.hourly))
        out["plain_useful_energy_kWh"] = res_plain.energy["E_load_kWh"]
        out["plain_max_water_temp_C"] = res_plain.max_water_temp_C
        out["sim_wall_s"] = time.perf_counter() - t0

    return out


# ------------------------------------------------------------- execution

def warm_jit():
    """Compile (or load) the numba kernel in THIS process, so the on-disk
    cache is populated before workers are spawned. Uses a 48-hour slice so
    it costs a fraction of a second after the first ever call."""
    sysconf = _deep_merge(load_system_config(), {"tank": {"n_nodes": 10}})
    bounds = load_design_bounds()

    def mid(key):
        return (bounds[key]["min"] + bounds[key]["max"]) / 2.0

    # Mid-box, so the warm-up design is geometrically valid (a box CORNER
    # can fail the packing/passage check, which would leave the kernel
    # uncompiled and every worker compiling it at once). Capsule count is
    # derived from the mid volume fraction (v3.0 parameterization).
    design = design_from_fraction(mid("pcm_volume_fraction"), mid("capsule_diameter_m"),
                                  mid("flow_rate_kg_s"), "staggered", sysconf)
    geom = check_design(design, sysconf, bounds)
    if not geom["valid"]:
        raise RuntimeError(f"warm_jit's mid-box design was rejected: {geom.get('reason')}")
    weather = load_hourly_weather("tamilnadu", 0).iloc[:48]
    demand = load_demand_model(load_demand_profile("tamilnadu"))
    props = pcm_props_from_record(get_pcm_properties("tamilnadu", "n-Hexacosane (C26)"),
                                  sysconf["pcm_integration"]["melting_half_width_K"])
    run_year_multinode_fast(weather, demand, get_regime("tamilnadu", 0)["T_mains_est_C"],
                            _runtime_from_geom(geom, geom["n_capsule"]), props, sysconf,
                            record_hourly=False)


_POOL = None
_POOL_WORKERS = None


def _get_pool(n_workers: int):
    """One pool per PROCESS, reused across every stage.

    Worker startup is not free: a spawned worker re-imports the module
    tree, which measured 12.0 s before the import diet (sklearn alone was
    10.6 s of it; see src/simulation/node_layout.py) and 3.0 s after. A
    fresh pool per call pays that for every worker, every stage -- on an
    11-worker pool that was ~132 s per batch, which utterly dominated
    short stages like the 54-case DOE smoke test (2.2 min wall for ~80 s
    of actual physics). Keeping the pool alive pays it ONCE per session.

    Not a context manager on purpose: the pool outlives any single call.
    It is torn down by `shutdown_pool()` or at interpreter exit.
    """
    global _POOL, _POOL_WORKERS
    if _POOL is not None and _POOL_WORKERS != n_workers:
        shutdown_pool()
    if _POOL is None:
        _POOL = ProcessPoolExecutor(max_workers=n_workers)
        _POOL_WORKERS = n_workers
    return _POOL


def shutdown_pool():
    global _POOL, _POOL_WORKERS
    if _POOL is not None:
        _POOL.shutdown(wait=True)
    _POOL, _POOL_WORKERS = None, None


atexit.register(shutdown_pool)


def run_tasks_parallel(tasks, n_workers: int = None, chunksize: int = 1,
                       progress_every: int = 0, label: str = "") -> pd.DataFrame:
    """Runs every task across a process pool; returns one DataFrame row per
    task, in input order.

    n_workers defaults to cpu_count()-1 (one core left for the parent and
    the OS, which measurably beats using all of them when the parent is
    also assembling results).
    """
    tasks = list(tasks)
    if not tasks:
        return pd.DataFrame()

    # On Windows, workers are SPAWNED: each one re-imports the __main__
    # module. A calling script without an `if __name__ == "__main__":`
    # guard therefore re-runs its own top-level code inside every worker,
    # each of which then tries to build its own pool -- which surfaces as
    # a bare BrokenProcessPool from somewhere deep in concurrent.futures.
    # Catching it here names the actual mistake instead.
    if multiprocessing.parent_process() is not None:
        raise RuntimeError(
            "run_tasks_parallel() was called inside a worker process. The calling "
            "script is missing an `if __name__ == \"__main__\":` guard around its "
            "top-level code, so each spawned worker re-ran it. Wrap the script body "
            "in a main() behind that guard.")

    n_workers = n_workers or max(1, (os.cpu_count() or 2) - 1)
    n_workers = min(n_workers, len(tasks))

    # Pin per-worker BLAS/OpenMP threads BEFORE the children are spawned --
    # they inherit this environment, which stops 12 processes from each
    # starting their own 12-thread pool (see module docstring).
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                "NUMEXPR_NUM_THREADS", "NUMBA_NUM_THREADS"):
        os.environ.setdefault(var, "1")

    warm_jit()

    pool = _get_pool(n_workers)
    t0 = time.time()
    rows = []
    for i, row in enumerate(pool.map(simulate_one, tasks, chunksize=chunksize), start=1):
        rows.append(row)
        if progress_every and (i % progress_every == 0 or i == len(tasks)):
            el = time.time() - t0
            rate = i / el
            eta = (len(tasks) - i) / rate if rate > 0 else float("nan")
            print(f"  [{label}] {i}/{len(tasks)} cases  {el/60:.1f} min elapsed  "
                  f"{rate:.2f} cases/s  ETA {eta/60:.1f} min", flush=True)

    el = time.time() - t0
    print(f"  [{label}] done: {len(tasks)} cases in {el/60:.2f} min "
          f"({el/len(tasks):.3f} s/case wall, {n_workers} workers)", flush=True)
    return pd.DataFrame(rows)


def run_tasks_serial(tasks, progress_every: int = 0, label: str = "") -> pd.DataFrame:
    """Same contract as run_tasks_parallel, single process -- kept so every
    parallel result can be reproduced without the pool (and so the
    speedup claim stays measurable rather than asserted)."""
    tasks = list(tasks)
    warm_jit()
    t0 = time.time()
    rows = []
    for i, task in enumerate(tasks, start=1):
        rows.append(simulate_one(task))
        if progress_every and i % progress_every == 0:
            print(f"  [{label}|serial] {i}/{len(tasks)}  {(time.time()-t0)/60:.1f} min", flush=True)
    el = time.time() - t0
    print(f"  [{label}|serial] done: {len(tasks)} cases in {el/60:.2f} min "
          f"({el/len(tasks):.3f} s/case)", flush=True)
    return pd.DataFrame(rows)
