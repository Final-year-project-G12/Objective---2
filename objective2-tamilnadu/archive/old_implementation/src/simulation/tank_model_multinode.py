"""
src/simulation/tank_model_multinode.py
=========================================
Multi-node (stratified) tank model — ports the concept from Manvitha's
Rajasthan report (section 3.3, "G4"): N equal-volume water nodes stacked
bottom-to-top instead of one well-mixed water node, so the tank can
develop a real thermocline (hot water floating on top, cold mains water
at the bottom) instead of instantly mixing every draw/charge event across
the whole tank volume.

The single-node model (tank_model.py) is kept, unmodified, as the
regression reference — same practice Rajasthan's own report describes
("The single-node tank (tank_model.py) is kept as the regression
reference").

DISCLOSED MODELING CHOICES (we do not have Manvitha's actual multi-node
source code, only her report's one-paragraph description — these choices
are our own, built to be physically defensible and energy-conservative,
not a byte-for-byte reproduction):

  * Node indexing: i=0 is the BOTTOM node (mains inlet / collector draw
    point), i=N-1 is the TOP node (delivery outlet).
  * Draw (demand): plug-flow upward advection. Mains water enters node 0;
    the top node's outflow is the delivered water. This is the one
    genuinely open-loop (mass-exchanging-with-the-outside-world) stream.
  * Collector charging: modeled as a LOCAL heat source (no mass transport)
    injected into whichever node's current temperature is closest to the
    collector's computed return temperature -- "returns at the node of
    equal temperature" from the report, implemented as a stratified
    charging placement rather than literal mass recirculation (the
    collector loop is a closed loop external to the tank; treating its
    net effect as a local energy source at the best-matching node is
    energy-conservative without needing a second, non-trivial mass-flow
    topology through the stack). Collector inlet/outlet coefficients
    still use node 0's temperature (the coldest water the collector pump
    would realistically draw from), matching collector_linear_coeffs'
    existing (a - b*T) form.
  * Axial conduction between adjacent nodes uses water's own conductivity
    with a mixing-enhancement factor (system_config["tank"].get(
    "axial_mixing_enhancement", 5.0)) -- pure molecular conduction at
    these length scales is negligible; some enhancement is standard
    practice in 1-D stratified tank models to represent the turbulent
    mixing that isn't resolved by a 1-D node stack.
  * Ambient loss area is split evenly across the N nodes (A_tank/N each)
    -- we do not have a separate cap-vs-side-wall area breakdown in the
    existing geometry record, so this is a documented simplification, not
    a top/bottom/side-resolved loss model.
  * Capsules are assigned to a contiguous band of nodes sized to just
    contain the PCM volume, placed by `system_config["tank"]
    ["stack_anchor"]` ("bottom"/"center"/"top", default "center") --
    matches the report's "capsules assigned to nodes by layer height
    around the stack anchor".
  * Energy-conserving inversion removal: after each substep's implicit
    solve, if the resulting profile has a hotter node sitting BELOW a
    colder one (a physically unstable inversion -- buoyancy would mix it
    out instantly in reality, faster than this model's timestep
    resolves), the inverted nodes are merged via mass-weighted averaging
    (exactly what PAV / isotonic regression does: the smallest
    monotonicity-restoring, least-squares-optimal merge). We use
    `sklearn.isotonic.IsotonicRegression(increasing=True)` weighted by
    node mass, which is the pool-adjacent-violators algorithm itself.

VALIDATION: at N=1 this reduces to a single well-mixed node and should
agree with tank_model.py's own single-node result to within the two
models' structural differences (this one solves all nodes simultaneously
and places collector charge by temperature-matching, which is a no-op at
N=1); see docs_objective2/RAJASTHAN_METHOD_PORT_PROGRESS.md for the
validation run log.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

from src.simulation.capsule_enthalpy import (
    PCMThermalProps, enthalpy_of_temperature, temperature_and_liquid_fraction_of_enthalpy,
)
from src.simulation.collector_model import collector_linear_coeffs
from src.simulation.heat_transfer import ua_eff_total_w_k
from src.simulation.capsule_mass import capsule_breakdown, props_with_wall_capacity
from src.simulation.energy_balance import EnergyAccumulator
from src.simulation.demand_profile import DemandModel, local_hour_index
from src.simulation.tank_model import DesignRuntime, SimulationResult
from src.simulation.node_layout import capsule_node_band as _capsule_node_band

IST_OFFSET_HOURS = 5.5




def _restore_monotonic_stratification(T_new: np.ndarray, node_mass: np.ndarray) -> np.ndarray:
    """Energy-conserving inversion removal via pool-adjacent-violators
    (sklearn's IsotonicRegression IS the PAV algorithm): enforces
    T[0] <= T[1] <= ... <= T[N-1] (bottom to top) with the mass-weighted
    least-squares-optimal merge of any violating run, which conserves
    sum(mass*T) exactly (energy-conserving, since E = mass*cp*T and cp is
    uniform)."""
    n = len(T_new)
    if n <= 1:
        return T_new
    iso = IsotonicRegression(increasing=True, out_of_bounds="clip")
    x = np.arange(n, dtype=float)
    T_fixed = iso.fit_transform(x, T_new, sample_weight=node_mass)
    return T_fixed


def run_year_multinode(weather_hourly: pd.DataFrame, demand: DemandModel, mains_temp_C: float,
                        design: DesignRuntime, pcm_props: PCMThermalProps, system_config: dict,
                        record_hourly: bool = True) -> SimulationResult:
    tank_cfg = system_config.get("tank", {})
    N = int(tank_cfg.get("n_nodes", 10))
    stack_anchor = tank_cfg.get("stack_anchor", "center")
    mix_enh = float(tank_cfg.get("axial_mixing_enhancement", 5.0))

    solver = system_config["solver"]
    dt_total_s = solver["timestep_s"]
    n_substeps_per_hour = int(round(3600 / dt_total_s))

    water_cfg = system_config["water"]
    cp_w = water_cfg["cp_J_kgK"]
    rho_w = water_cfg["density_kg_m3"]
    k_w = water_cfg.get("k_W_mK", 0.63)

    u_tank = system_config["tank"]["U_tank_W_m2K"]
    a_tank_total = design.tank_surface_area_m2
    a_node = a_tank_total / N

    delivery_target_C = system_config["delivery"]["target_temp_C"]
    max_water_C = system_config["safety"]["max_water_temp_C"]
    max_pcm_C = system_config["safety"]["max_pcm_temp_C"]
    has_pcm = design.n_capsule > 0

    shield_enabled = system_config["safety"].get("shield_enabled", False)
    # See tank_model_multinode_fast.py for the measurement that motivated
    # the predictive default (9.3 C of false PCM overshoot at dt=300 s with
    # the lagged decision). Both models carry the flag so the equivalence
    # test covers both branches.
    shield_predictive = bool(system_config["safety"].get("shield_predictive", True))
    guard_band_C = system_config["safety"].get("shield_guard_band_C", 3.0)
    # Two SEPARATE mechanisms (report section 3.4) -- the water-side bypass
    # stops the collector at water's own 72 C limit; the PCM-side block
    # only zeroes capsule UA in the charging direction at 62 C and never
    # stops the collector. See tank_model_multinode_fast.py for the full
    # note and the measurements that forced the split.
    water_trip_C = max_water_C - guard_band_C
    pcm_trip_C = max_pcm_C - guard_band_C

    # G2/D3: PCM mass from the INNER sphere, shell heat capacity folded
    # into the PCM node via an augmented cp. Outer volume still sets water
    # displacement. See src/simulation/capsule_mass.py.
    if has_pcm:
        cap = capsule_breakdown(design.n_capsule, design.capsule_diameter_m,
                                pcm_props.density_kg_m3, system_config)
        pcm_props = props_with_wall_capacity(pcm_props, cap)
        m_pcm_total_kg = cap.m_pcm_total_kg
        # D3 geometric part of the PCM-side resistance: r_in / (5 A_in)
        pcm_r_coeff = (cap.inner_diameter_m / 2.0) / (5.0 * cap.inner_area_m2)
    else:
        cap = None
        m_pcm_total_kg = 0.0
        pcm_r_coeff = None
    v_pcm_total_m3 = design.n_capsule * design.capsule_volume_m3 if has_pcm else 0.0
    v_node_nominal_m3 = design.tank_volume_m3 / N

    if has_pcm:
        n_pcm_nodes = max(1, int(np.ceil(v_pcm_total_m3 / v_node_nominal_m3)))
        pcm_nodes = _capsule_node_band(N, n_pcm_nodes, stack_anchor)
    else:
        n_pcm_nodes = 0
        pcm_nodes = np.array([], dtype=int)

    is_pcm_node = np.zeros(N, dtype=bool)
    is_pcm_node[pcm_nodes] = True
    n_capsule_per_node = np.where(is_pcm_node, design.n_capsule / max(n_pcm_nodes, 1), 0.0)
    v_pcm_per_node_m3 = np.where(is_pcm_node, v_pcm_total_m3 / max(n_pcm_nodes, 1), 0.0)
    m_pcm_per_node_kg = np.where(is_pcm_node, m_pcm_total_kg / max(n_pcm_nodes, 1), 0.0)

    v_water_node_m3 = v_node_nominal_m3 - v_pcm_per_node_m3
    m_water_node_kg = np.maximum(v_water_node_m3, 1e-9) * rho_w

    tank_height_m = design.tank_volume_m3 / max(design.cross_section_area_m2, 1e-9)
    dz_m = tank_height_m / N
    cond_UA_per_link = mix_enh * k_w * design.cross_section_area_m2 / max(dz_m, 1e-9)  # W/K, between adjacent nodes

    superficial_velocity = (design.flow_rate_kg_s / rho_w / design.cross_section_area_m2
                             if design.cross_section_area_m2 > 0 else 0.0)

    # ---- initial state -----------------------------------------------
    T_w = np.full(N, solver["initial_water_temp_C"], dtype=float)
    if has_pcm:
        init_state = solver["initial_pcm_state"]
        if init_state == "solid":
            T_pcm_init = pcm_props.Ts_C - 5.0
        elif init_state == "liquid":
            T_pcm_init = pcm_props.Tl_C + 5.0
        else:
            T_pcm_init = pcm_props.Tm_C
        h_pcm_node = np.full(N, enthalpy_of_temperature(T_pcm_init, pcm_props))
        T_pcm_node = np.full(N, T_pcm_init)
        f_melt_node = np.zeros(N)
    else:
        h_pcm_node = np.zeros(N)
        T_pcm_node = T_w.copy()
        f_melt_node = np.zeros(N)

    acc = EnergyAccumulator()
    acc.E_initial_J = float(np.sum(m_water_node_kg * cp_w * T_w)) + float(np.sum(m_pcm_per_node_kg * h_pcm_node))
    initial_f_melt = 0.0

    max_water_temp, max_pcm_temp = float(T_w.max()), (float(T_pcm_node[pcm_nodes].max()) if has_pcm else T_w.max())
    n_safety = 0
    n_clipped_steps = 0
    last_f_melt_mean, complete_cycles = 0.0, 0
    was_fully_liquid = False
    n_shield_water = 0
    n_shield_pcm = 0

    rows = []
    n_hours = len(weather_hourly)
    ghi_arr = weather_hourly["GHI_Wm2"].to_numpy(dtype=float)
    tamb_arr = weather_hourly["T_amb_C"].to_numpy(dtype=float)
    # G1: local (IST) hour by FLOOR -- see demand_profile.local_hour_index.
    hour_of_day_arr = local_hour_index(weather_hourly).astype(float)

    for i in range(n_hours):
        I_t = ghi_arr[i]
        T_amb = tamb_arr[i]
        hour_of_day = hour_of_day_arr[i]

        draw_mass_hour_kg = demand.draw_mass_kg_for_hour(hour_of_day)
        draw_mass_per_substep_kg = draw_mass_hour_kg / n_substeps_per_hour

        hour_q_collector = hour_q_load = hour_q_pcm = hour_q_loss = 0.0
        hour_q_pump = hour_q_unmet = 0.0
        hour_shield_water = 0
        hour_shield_pcm = 0

        for sub in range(n_substeps_per_hour):
            dt_sub = 3600.0 / n_substeps_per_hour
            mdot_draw = draw_mass_per_substep_kg / dt_sub if dt_sub > 0 else 0.0

            a_coll, b_coll, circulating = collector_linear_coeffs(I_t, T_amb, system_config)

            # Lagged WATER-side bypass (dt-dependent -- see the fast kernel).
            if shield_enabled and not shield_predictive and circulating:
                if T_w[-1] >= water_trip_C:
                    circulating = False
                    n_shield_water += 1
                    hour_shield_water += 1

            mdot_coll = design.flow_rate_kg_s if circulating else 0.0
            # Collector inlet = bottom node (coldest realistic draw point).
            q_collector_trial = max(a_coll - b_coll * T_w[0], 0.0) if circulating else 0.0
            T_return = (T_w[0] + q_collector_trial / (mdot_coll * cp_w)
                        if mdot_coll > 0 else T_w[0])
            j_charge = int(np.argmin(np.abs(T_w - T_return))) if circulating else -1

            # ---- assemble the implicit (backward-Euler) tridiagonal system,
            # vectorized across nodes (no per-node Python loop) and solved
            # via a banded solver instead of a dense N x N one -- same exact
            # equations as the original per-node version, just computed
            # without per-substep Python-level iteration (this runs
            # n_hours * n_substeps_per_hour times per simulated year, so
            # the per-call overhead dominates runtime at N this small). ----
            # ua_eff_total_w_k(n,...) == n * ua_per_capsule (linear in n_capsule,
            # independent of n itself) -- calling with n=1 gives ua_per_capsule
            # directly and exactly for any node's fractional capsule count,
            # without a round()-then-rescale trick.
            pcm_blocked_this_substep = False
            if has_pcm:
                ua_per_node = np.zeros(N)
                for k in pcm_nodes:
                    ua_pc_k = ua_eff_total_w_k(1, design.capsule_diameter_m, design.capsule_area_m2,
                                                superficial_velocity, pcm_props, f_melt_node[k], system_config,
                                                pcm_r_coeff=pcm_r_coeff)
                    ua_per_node[k] = n_capsule_per_node[k] * ua_pc_k
                    # PCM-side charge block: UA -> 0 while the PCM is at/above
                    # its own trip AND the water is hotter (charging only);
                    # discharge is never blocked. Does not stop the collector.
                    if shield_enabled and T_pcm_node[k] >= pcm_trip_C and T_w[k] > T_pcm_node[k]:
                        ua_per_node[k] = 0.0
                        pcm_blocked_this_substep = True
            else:
                ua_per_node = np.zeros(N)
            # Assemble/solve, iterating the PCM-side block to a FIXED
            # POINT: blocking one group makes the water hotter, which can
            # push a different group over its own trip. Two passes missed
            # 120 of 11,070 DOE designs (peaks to 68.51 C against a 65 C
            # limit), all in the high-UA corner. Mirrors the fast kernel.
            max_passes = (n_pcm_nodes + 2) if (shield_enabled and has_pcm) else 1
            for _pass in range(max_passes):
                diag = m_water_node_kg * cp_w / dt_sub + u_tank * a_node + ua_per_node
                rhs = m_water_node_kg * cp_w / dt_sub * T_w + u_tank * a_node * T_amb + ua_per_node * T_pcm_node

                sub_diag = np.zeros(N)   # coupling of row k to column k-1, k=1..N-1
                super_diag = np.zeros(N)  # coupling of row k to column k+1, k=0..N-2

                if N > 1:
                    diag[1:] += cond_UA_per_link           # every node but the bottom has a lower neighbor
                    diag[:-1] += cond_UA_per_link           # every node but the top has an upper neighbor
                    sub_diag[1:] -= cond_UA_per_link
                    super_diag[:-1] -= cond_UA_per_link

                if mdot_draw > 0:
                    diag += mdot_draw * cp_w                # every node loses its own outflow upward
                    rhs[0] += mdot_draw * cp_w * mains_temp_C
                    if N > 1:
                        sub_diag[1:] -= mdot_draw * cp_w     # every node but the bottom gains inflow from below

                if circulating:
                    rhs[j_charge] += q_collector_trial

                if N == 1:
                    T_w_new = rhs / diag
                else:
                    # Measured 2026-10-28: scipy.linalg.solve_banded was tried
                    # here and was ~5x SLOWER than a dense solve for N this
                    # small (N=10 went from 123s/year to 649s/year) -- LAPACK's
                    # banded-solve setup overhead dominates at this size, so a
                    # plain dense solve is used instead despite the matrix
                    # being tridiagonal. The numba kernel uses a hand-written
                    # Thomas algorithm instead; this stays dense so the two
                    # implementations differ in as few places as possible.
                    A = np.diag(diag)
                    A[np.arange(N - 1) + 1, np.arange(N - 1)] = sub_diag[1:]
                    A[np.arange(N - 1), np.arange(N - 1) + 1] = super_diag[:-1]
                    T_w_new = np.linalg.solve(A, rhs)

                if _pass == max_passes - 1 or not (shield_enabled and has_pcm):
                    break
                newly_blocked = False
                for k in pcm_nodes:
                    if ua_per_node[k] > 0 and m_pcm_per_node_kg[k] > 0:
                        q_k = ua_per_node[k] * (T_w_new[k] - T_pcm_node[k])
                        if q_k > 0:   # charging direction only
                            h_proj = h_pcm_node[k] + q_k * dt_sub / m_pcm_per_node_kg[k]
                            T_proj, _ = temperature_and_liquid_fraction_of_enthalpy(h_proj, pcm_props)
                            if T_proj >= pcm_trip_C:
                                ua_per_node[k] = 0.0
                                newly_blocked = True
                                pcm_blocked_this_substep = True
                if not newly_blocked:
                    break

            if pcm_blocked_this_substep:
                n_shield_pcm += 1
                hour_shield_pcm += 1

            # Predictive shield: re-solve this substep with the collector
            # source removed if the trial solve lands past a trip
            # threshold. Mirrors the fast kernel exactly (and the existing
            # differential-controller re-solve pattern in tank_model.py).
            # Water-side test over EVERY node, not just the outlet -- see
            # the fast kernel for the measurement that motivated it.
            if shield_enabled and shield_predictive and circulating:
                if float(T_w_new.max()) >= water_trip_C:
                    rhs[j_charge] -= q_collector_trial
                    q_collector_trial = 0.0
                    circulating = False
                    n_shield_water += 1
                    hour_shield_water += 1
                    if N == 1:
                        T_w_new = rhs / diag
                    else:
                        T_w_new = np.linalg.solve(A, rhs)
            # Energy accounting (q_load, q_loss, q_pcm below) is computed
            # from this RAW solve, before any inversion-removal smoothing --
            # it must match what the matrix equations above actually solved
            # for, or the Gate-1-style residual check picks up a spurious
            # mismatch between "energy reported as having flowed" and
            # "energy the matrix equations balanced". Inversion removal
            # (PAV) is applied afterward, only to the STATE carried forward
            # into the next sub-step -- it redistributes energy among nodes
            # (conserving sum(mass*T) exactly) to represent the buoyant
            # remixing a real inversion triggers faster than this model's
            # time resolution, but it is a state correction, not a flux this
            # sub-step actually had.

            q_collector = q_collector_trial if circulating else 0.0
            q_load = max(mdot_draw * cp_w * (T_w_new[-1] - mains_temp_C), 0.0)
            q_unmet = (mdot_draw * cp_w * max(delivery_target_C - T_w_new[-1], 0.0)
                       if mdot_draw > 0 else 0.0)
            q_loss_total = float(np.sum(u_tank * a_node * (T_w_new - T_amb)))

            # ---- PCM node update (explicit, using just-solved T_w_new) ----
            # Reuses ua_per_node computed above -- the SAME conductance the
            # water-node matrix equations were built with, so the water
            # node's heat loss to each PCM node exactly equals what that
            # node's enthalpy gains (required for energy conservation).
            q_pcm_total = 0.0
            for k in pcm_nodes if has_pcm else []:
                q_pcm_k = ua_per_node[k] * (T_w_new[k] - T_pcm_node[k])
                q_pcm_total += q_pcm_k
                if m_pcm_per_node_kg[k] > 0:
                    h_pcm_node[k] += q_pcm_k * dt_sub / m_pcm_per_node_kg[k]
                    T_pcm_node[k], f_melt_node[k] = temperature_and_liquid_fraction_of_enthalpy(
                        h_pcm_node[k], pcm_props)

            T_w = _restore_monotonic_stratification(T_w_new, m_water_node_kg)
            max_water_temp = max(max_water_temp, float(T_w.max()))
            if has_pcm:
                max_pcm_temp = max(max_pcm_temp, float(T_pcm_node[pcm_nodes].max()))
            if T_w.max() >= max_water_C or (has_pcm and T_pcm_node[pcm_nodes].max() >= max_pcm_C):
                n_safety += 1

            q_pump = 0.0  # tracked separately via hydraulic_model at the caller level, same as tank_model.py
            acc.add_step(q_collector, q_load, q_pcm_total, q_loss_total, q_pump, q_unmet, dt_sub)

            hour_q_collector += q_collector * dt_sub
            hour_q_load += q_load * dt_sub
            hour_q_pcm += q_pcm_total * dt_sub
            hour_q_loss += q_loss_total * dt_sub
            hour_q_pump += q_pump * dt_sub
            hour_q_unmet += q_unmet * dt_sub

        mean_f_melt = float(f_melt_node[pcm_nodes].mean()) if has_pcm else 0.0
        if was_fully_liquid and mean_f_melt < 0.5:
            was_fully_liquid = False
        if mean_f_melt >= 0.999 and not was_fully_liquid:
            complete_cycles += 1
            was_fully_liquid = True
        last_f_melt_mean = mean_f_melt

        if record_hourly:
            rows.append({
                "hour_index": i, "hour_of_day": hour_of_day, "I_t_Wm2": I_t, "T_amb_C": T_amb,
                "T_w_C": float(T_w[-1]), "T_w_bottom_C": float(T_w[0]), "T_w_top_C": float(T_w[-1]),
                "T_pcm_C": float(T_pcm_node[pcm_nodes].mean()) if has_pcm else float(T_w.mean()),
                "f_melt": mean_f_melt,
                "Q_collector_Wh": hour_q_collector / 3600, "Q_load_Wh": hour_q_load / 3600,
                "Q_pcm_Wh": hour_q_pcm / 3600, "Q_loss_Wh": hour_q_loss / 3600,
                "Q_pump_Wh": hour_q_pump / 3600, "Q_unmet_Wh": hour_q_unmet / 3600,
                "shield_water_activations": hour_shield_water,
                "shield_pcm_activations": hour_shield_pcm,
                "shield_activations": hour_shield_water + hour_shield_pcm,
            })

    acc.E_final_J = float(np.sum(m_water_node_kg * cp_w * T_w)) + float(np.sum(m_pcm_per_node_kg * h_pcm_node))
    acc.n_failed_steps = n_clipped_steps

    hourly_df = pd.DataFrame(rows) if record_hourly else pd.DataFrame()
    energy = acc.residual_report()

    return SimulationResult(
        hourly=hourly_df, energy=energy,
        max_water_temp_C=max_water_temp, max_pcm_temp_C=max_pcm_temp,
        n_safety_violations=n_safety, final_f_melt=last_f_melt_mean,
        complete_melt_cycles=complete_cycles, initial_f_melt=initial_f_melt,
        n_clipped_steps=n_clipped_steps,
        n_shield_activations=n_shield_water + n_shield_pcm,
        n_shield_water_activations=n_shield_water,
        n_shield_pcm_activations=n_shield_pcm,
    )
