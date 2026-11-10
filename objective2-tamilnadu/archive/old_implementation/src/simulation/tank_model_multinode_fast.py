"""
src/simulation/tank_model_multinode_fast.py
==============================================
numba-JIT-compiled production kernel for the multi-node (stratified) tank
model. Physically IDENTICAL to tank_model_multinode.py -- same equations,
same ordering, same energy accounting, same inversion-removal semantics --
but with the per-substep hot loop compiled to machine code instead of
interpreted.

WHY THIS EXISTS (measured, 2026-10-28)
--------------------------------------
The pure-Python/numpy version ran a 10-node year in ~114 s. That is not
because the arithmetic is expensive (N=10 is a 10x10 tridiagonal system --
tens of FLOPs), it is because the interpreted version pays per-CALL
overhead 105,120 times per simulated year (8760 h x 12 substeps at
dt=300 s), and three of those per-substep calls are expensive wrappers
around trivial work:

  1. np.linalg.solve  -- a dense LAPACK call (with its argument
     validation, work-array setup and O(N^3) factorization) for a matrix
     that is tridiagonal and tiny. Replaced here by an inlined Thomas
     algorithm (O(N), no call overhead, no allocation beyond two
     scratch vectors).
  2. sklearn.isotonic.IsotonicRegression().fit_transform(...) -- an
     estimator object constructed, validated and fitted from scratch
     EVERY substep to run pool-adjacent-violators over 10 points.
     Replaced here by the PAV algorithm written out directly (a
     stack-based O(N) scan -- the same algorithm sklearn runs
     internally, so the result is the same unique weighted-isotonic
     solution, just without the estimator machinery).
  3. ua_eff_total_w_k(...) -- recomputed the Wakao-Kaguei packed-bed
     Nusselt correlation (Reynolds, Prandtl^(1/3), Re^0.6) per PCM node
     per substep, even though it depends ONLY on superficial velocity
     and capsule diameter, both of which are fixed for the entire run.
     Hoisted out: the water-side and wall resistances are computed ONCE
     per year here, and only the f_melt-dependent PCM-side resistance
     (r_pcm, a single divide) is evaluated in the loop.

Rajasthan's report quotes 1.4-3.1 s/year for her 10-node kernel; that
figure is a numba-compiled kernel, which is why a like-for-like
interpreted port looked ~40x slower than "her" model despite solving the
same physics.

EQUIVALENCE IS A TESTED CLAIM, NOT AN ASSUMPTION
------------------------------------------------
tank_model_multinode.py is deliberately KEPT, unmodified, as the
regression reference (the same practice this project already follows for
the single-node model). validate_multinode_fast.py runs both on the same
design and asserts agreement; see
docs_objective2/RAJASTHAN_METHOD_PORT_PROGRESS.md for the logged run.

The one intentional numerical difference: a Thomas factorization and a
dense LU factorization of the same tridiagonal system are mathematically
identical but accumulate floating-point rounding differently, so
agreement is to ~1e-10 relative, not bit-for-bit.
"""

import numpy as np
import pandas as pd
from numba import njit

from src.simulation.capsule_enthalpy import PCMThermalProps, enthalpy_of_temperature
from src.simulation.heat_transfer import water_side_htc_w_m2k
from src.simulation.capsule_mass import capsule_breakdown, props_with_wall_capacity
from src.simulation.energy_balance import EnergyAccumulator
from src.simulation.demand_profile import DemandModel, local_hour_index
from src.simulation.tank_model import DesignRuntime, SimulationResult
from src.simulation.node_layout import capsule_node_band

N_HOURLY_COLS = 11


@njit(cache=True)
def _pav_increasing(y, w, n):
    """Weighted pool-adjacent-violators: the minimizer of
    sum(w_i*(y_i-z_i)^2) subject to z_0 <= z_1 <= ... <= z_{n-1}.

    Written out directly rather than calling sklearn's IsotonicRegression
    (which runs this same algorithm) because this is executed once per
    substep -- ~105k times per simulated year -- where estimator
    construction and input validation cost orders of magnitude more than
    the scan itself. Merging a violating pair by its weighted mean
    conserves sum(w_i*z_i) exactly, which is what makes the inversion
    removal energy-conserving.
    """
    block_value = np.empty(n)
    block_weight = np.empty(n)
    block_len = np.empty(n, dtype=np.int64)

    top = -1
    for i in range(n):
        top += 1
        block_value[top] = y[i]
        block_weight[top] = w[i]
        block_len[top] = 1
        while top > 0 and block_value[top - 1] > block_value[top]:
            w_merged = block_weight[top - 1] + block_weight[top]
            v_merged = (block_value[top - 1] * block_weight[top - 1]
                        + block_value[top] * block_weight[top]) / w_merged
            block_value[top - 1] = v_merged
            block_weight[top - 1] = w_merged
            block_len[top - 1] = block_len[top - 1] + block_len[top]
            top -= 1

    out = np.empty(n)
    idx = 0
    for b in range(top + 1):
        v = block_value[b]
        for _ in range(block_len[b]):
            out[idx] = v
            idx += 1
    return out


@njit(cache=True)
def _thomas_solve(sub_diag, diag, super_diag, rhs, n):
    """Thomas algorithm (tridiagonal Gaussian elimination without
    pivoting). Index convention matches the assembly below: sub_diag[k]
    couples row k to column k-1 (k>=1), super_diag[k] couples row k to
    column k+1 (k<=n-2).

    No pivoting is needed: every diagonal entry carries
    m*cp/dt + U*A + UA_pcm + mdot*cp (all strictly positive) while the
    off-diagonals are the negated conduction/advection couplings, so the
    matrix is irreducibly diagonally dominant by construction.
    """
    c = diag.copy()
    d = rhs.copy()
    for i in range(1, n):
        m = sub_diag[i] / c[i - 1]
        c[i] = c[i] - m * super_diag[i - 1]
        d[i] = d[i] - m * d[i - 1]

    x = np.empty(n)
    x[n - 1] = d[n - 1] / c[n - 1]
    for i in range(n - 2, -1, -1):
        x[i] = (d[i] - super_diag[i] * x[i + 1]) / c[i]
    return x


@njit(cache=True)
def _T_and_f_of_h(h, Ts_C, Tl_C, h_s, latent, cp_s, cp_l):
    """Inlined copy of capsule_enthalpy.temperature_and_liquid_fraction_of_enthalpy
    taking primitives (the original takes a PCMThermalProps dataclass,
    which is not nopython-compatible). TREF_C = 0 there, so the solid
    branch is h/cp_s."""
    h_l = h_s + latent
    if h < h_s:
        return h / cp_s, 0.0
    elif h <= h_l:
        f_raw = (h - h_s) / latent if latent > 0 else 1.0
        f = min(max(f_raw, 0.0), 1.0)
        return Ts_C + f * (Tl_C - Ts_C), f
    else:
        return Tl_C + (h - h_l) / cp_l, 1.0


@njit(cache=True)
def _simulate_year_core(
    n_hours, n_substeps_per_hour,
    ghi_arr, tamb_arr, draw_mass_per_hour_of_day, hour_of_day_idx_arr,
    N, has_pcm, pcm_start, n_pcm_nodes,
    m_water_node_kg, m_pcm_per_node_kg, n_capsule_per_node,
    cond_UA_per_link, cp_w, mains_temp_C, u_tank, a_node,
    delivery_target_C, max_water_C, max_pcm_C,
    shield_enabled, shield_predictive, water_trip_C, pcm_trip_C,
    collector_cutoff_Wm2, fr_tau_alpha_area, fr_ul_area, flow_rate_kg_s,
    r_conv_wall_const, pcm_r_coeff, pcm_conductivity_W_mK, enhancement,
    Ts_C, Tl_C, h_s_J_kg, latent_heat_J_kg, cp_solid, cp_liquid,
    T_w_init, h_pcm_init, T_pcm_init, f_melt_init, record_hourly,
):
    T_w = T_w_init.copy()
    h_pcm_node = h_pcm_init.copy()
    T_pcm_node = T_pcm_init.copy()
    f_melt_node = f_melt_init.copy()

    diag = np.empty(N)
    rhs = np.empty(N)
    sub_diag = np.zeros(N)
    super_diag = np.zeros(N)
    ua_per_node = np.zeros(N)

    E_collector_J = 0.0
    E_load_J = 0.0
    E_loss_J = 0.0
    E_unmet_J = 0.0
    E_charge_J = 0.0
    E_discharge_J = 0.0

    max_water_temp = T_w[0]
    for k in range(1, N):
        if T_w[k] > max_water_temp:
            max_water_temp = T_w[k]
    if has_pcm:
        max_pcm_temp = T_pcm_node[pcm_start]
        for k in range(pcm_start + 1, pcm_start + n_pcm_nodes):
            if T_pcm_node[k] > max_pcm_temp:
                max_pcm_temp = T_pcm_node[k]
    else:
        max_pcm_temp = max_water_temp

    n_safety = 0
    # Split counters, as the report reports them (d_shield_water_h vs
    # shield_pcm_h): the two mechanisms are different events and collapsing
    # them loses the ability to compute d_overheat her way.
    n_shield_water = 0
    n_shield_pcm = 0
    last_f_melt_mean = 0.0
    complete_cycles = 0
    was_fully_liquid = False

    if record_hourly:
        hourly_out = np.zeros((n_hours, N_HOURLY_COLS))
    else:
        hourly_out = np.zeros((1, N_HOURLY_COLS))

    dt_sub = 3600.0 / n_substeps_per_hour

    for i in range(n_hours):
        I_t = ghi_arr[i]
        T_amb = tamb_arr[i]
        draw_mass_per_substep_kg = draw_mass_per_hour_of_day[hour_of_day_idx_arr[i]] / n_substeps_per_hour
        mdot_draw = draw_mass_per_substep_kg / dt_sub

        hour_q_collector = 0.0
        hour_q_load = 0.0
        hour_q_pcm = 0.0
        hour_q_loss = 0.0
        hour_q_unmet = 0.0
        hour_shield_water = 0.0
        hour_shield_pcm = 0.0

        for _sub in range(n_substeps_per_hour):
            if I_t <= collector_cutoff_Wm2:
                a_coll = 0.0
                b_coll = 0.0
                circulating = False
            else:
                a_coll = fr_tau_alpha_area * I_t + fr_ul_area * T_amb
                b_coll = fr_ul_area
                circulating = True

            # LAGGED shield: trips on start-of-substep ("last measured")
            # temperatures. Dt-dependent by construction -- the collector
            # keeps running for the whole substep after the threshold is
            # already crossed, so the overshoot scales with dt. Kept for
            # reproducing earlier results; see the predictive branch below.
            # Water-side bypass only -- the PCM never stops the collector.
            if shield_enabled and not shield_predictive and circulating:
                if T_w[N - 1] >= water_trip_C:
                    circulating = False
                    n_shield_water += 1
                    hour_shield_water += 1.0

            mdot_coll = flow_rate_kg_s if circulating else 0.0
            q_collector_trial = 0.0
            if circulating:
                q_collector_trial = a_coll - b_coll * T_w[0]
                if q_collector_trial < 0.0:
                    q_collector_trial = 0.0

            j_charge = 0
            if circulating:
                if mdot_coll > 0.0:
                    T_return = T_w[0] + q_collector_trial / (mdot_coll * cp_w)
                else:
                    T_return = T_w[0]
                best_diff = abs(T_w[0] - T_return)
                for k in range(1, N):
                    d_k = abs(T_w[k] - T_return)
                    if d_k < best_diff:
                        best_diff = d_k
                        j_charge = k

            # Only the f_melt-dependent PCM-side resistance varies in time;
            # the water-side and wall resistances are folded into
            # r_conv_wall_const once per year by the caller.
            pcm_blocked_this_substep = False
            if has_pcm:
                for k in range(pcm_start, pcm_start + n_pcm_nodes):
                    k_eff = pcm_conductivity_W_mK * (enhancement if f_melt_node[k] >= 0.5 else 1.0)
                    if k_eff > 0.0:
                        r_pcm = pcm_r_coeff / k_eff      # D3: inner radius / inner area
                    else:
                        r_pcm = 1.0e18
                    r_total = r_conv_wall_const + r_pcm
                    ua_per_node[k] = n_capsule_per_node[k] / r_total if r_total > 0.0 else 0.0

                    # PCM-SIDE CHARGE BLOCK (report section 3.4): zero this
                    # capsule group's conductance while the PCM is at/above
                    # its 62 C trip AND the water is hotter than it, i.e.
                    # only in the CHARGING direction. Discharge is never
                    # blocked, so a hot capsule can always still give heat
                    # back to the water -- which is the whole point of the
                    # store. Crucially this does NOT stop the collector:
                    # the water keeps heating toward its own 72 C bypass.
                    if shield_enabled and T_pcm_node[k] >= pcm_trip_C and T_w[k] > T_pcm_node[k]:
                        ua_per_node[k] = 0.0
                        pcm_blocked_this_substep = True

            # Assemble and solve, ITERATING the PCM-side block to a fixed
            # point. The block has to be decided from the END-of-substep
            # PCM temperature, not the start-of-substep one, for the same
            # reason the water-side bypass does: deciding it on stale
            # temperatures let a PCM node cross from just under 62 C to a
            # measured 73.9 C within ONE 300 s substep -- past its 65 C
            # hard limit -- because at high volume fraction the capsule
            # group's UA is large and the PCM node's thermal time constant
            # is far shorter than the substep.
            #
            # WHY A FIXED POINT AND NOT TWO PASSES. Blocking a node removes
            # a heat sink, so the remaining water runs HOTTER, which can
            # push a different capsule group over its own trip -- a group
            # that was fine in the first solve. A two-pass version missed
            # exactly those: the 17,280-case DOE came back with 120 designs
            # peaking up to 68.51 C, and they were precisely the high-UA
            # corner (median 757 capsules at 41 mm and 0.0113 kg/s, vs 120
            # at 60 mm for the rest). Iterating until no new group needs
            # blocking closes it. The loop is monotone -- a blocked node is
            # never unblocked within a substep -- so it terminates in at
            # most n_pcm_nodes passes; the +2 is slack for the final
            # no-change confirmation.
            max_passes = (n_pcm_nodes + 2) if (shield_enabled and has_pcm) else 1
            for _pass in range(max_passes):
                for k in range(N):
                    mc_dt = m_water_node_kg[k] * cp_w / dt_sub
                    diag[k] = mc_dt + u_tank * a_node + ua_per_node[k]
                    rhs[k] = mc_dt * T_w[k] + u_tank * a_node * T_amb + ua_per_node[k] * T_pcm_node[k]
                    sub_diag[k] = 0.0
                    super_diag[k] = 0.0

                for k in range(1, N):
                    diag[k] += cond_UA_per_link
                    sub_diag[k] -= cond_UA_per_link
                for k in range(N - 1):
                    diag[k] += cond_UA_per_link
                    super_diag[k] -= cond_UA_per_link

                if mdot_draw > 0.0:
                    mdot_cp = mdot_draw * cp_w
                    for k in range(N):
                        diag[k] += mdot_cp
                    rhs[0] += mdot_cp * mains_temp_C
                    for k in range(1, N):
                        sub_diag[k] -= mdot_cp

                if circulating:
                    rhs[j_charge] += q_collector_trial

                if N == 1:
                    T_w_new = np.empty(1)
                    T_w_new[0] = rhs[0] / diag[0]
                else:
                    T_w_new = _thomas_solve(sub_diag, diag, super_diag, rhs, N)

                if _pass == max_passes - 1 or not (shield_enabled and has_pcm):
                    break
                newly_blocked = False
                for k in range(pcm_start, pcm_start + n_pcm_nodes):
                    if ua_per_node[k] > 0.0 and m_pcm_per_node_kg[k] > 0.0:
                        q_k = ua_per_node[k] * (T_w_new[k] - T_pcm_node[k])
                        if q_k > 0.0:   # charging direction only; discharge never blocked
                            h_proj = h_pcm_node[k] + q_k * dt_sub / m_pcm_per_node_kg[k]
                            T_proj, _f_proj = _T_and_f_of_h(h_proj, Ts_C, Tl_C, h_s_J_kg,
                                                            latent_heat_J_kg, cp_solid, cp_liquid)
                            if T_proj >= pcm_trip_C:
                                ua_per_node[k] = 0.0
                                newly_blocked = True
                                pcm_blocked_this_substep = True
                if not newly_blocked:
                    break

            if pcm_blocked_this_substep:
                n_shield_pcm += 1
                hour_shield_pcm += 1.0

            # PREDICTIVE shield: solve once assuming the collector runs,
            # and if that solve lands at or past a trip threshold, cut the
            # collector and re-solve this same substep with the source
            # removed. The matrix itself does not depend on whether the
            # collector circulates (only rhs[j_charge] does), so the
            # re-solve is one extra Thomas sweep on affected substeps only.
            #
            # This is the SAME pattern tank_model.py already uses for its
            # differential-controller reverse-flow check ("solve once
            # assuming circulation, re-solve with the collector off if that
            # would imply reverse flow"), applied to the safety shield.
            #
            # Why it matters: the lagged shield's overshoot is an artifact
            # of deciding on stale temperatures, and it scales with dt --
            # measured at 9.3 C of false PCM overshoot at dt=300 s, against
            # a Richardson-extrapolated true value of exactly the 62 C trip
            # point. A real controller with a working sensor cuts the pump
            # before a 9 C excursion; this models that, and is dt-robust
            # rather than requiring a 16x finer timestep to hide the lag.
            #
            # This is the WATER-side bypass only. The PCM is protected by
            # the UA charge block above, not by stopping the collector --
            # see the water_trip_C / pcm_trip_C note in the wrapper.
            #
            # The water-side test is over EVERY node, not just the outlet:
            # the collector injects into whichever node matches its return
            # temperature (often an interior one), and the inversion-removal
            # step then lifts the nodes above it. Testing only the top node
            # let interior heating slip past the trip and showed up as a
            # measured 64.88 C peak against a 62 C trip. The reported
            # max_water_temp_C is itself a max over all nodes, so the trip
            # has to be too, or the shield cannot enforce the metric it is
            # judged by.
            if shield_enabled and shield_predictive and circulating:
                w_max_new = T_w_new[0]
                for k in range(1, N):
                    if T_w_new[k] > w_max_new:
                        w_max_new = T_w_new[k]
                if w_max_new >= water_trip_C:
                    rhs[j_charge] -= q_collector_trial
                    q_collector_trial = 0.0
                    circulating = False
                    n_shield_water += 1
                    hour_shield_water += 1.0
                    if N == 1:
                        T_w_new[0] = rhs[0] / diag[0]
                    else:
                        T_w_new = _thomas_solve(sub_diag, diag, super_diag, rhs, N)

            # ---- energy accounting from the RAW solve (pre-inversion-removal),
            # so reported flows match what the matrix equations actually
            # balanced -- see tank_model_multinode.py for the full reasoning. ----
            q_collector = q_collector_trial if circulating else 0.0
            q_load = mdot_draw * cp_w * (T_w_new[N - 1] - mains_temp_C)
            if q_load < 0.0:
                q_load = 0.0
            if mdot_draw > 0.0:
                deficit = delivery_target_C - T_w_new[N - 1]
                q_unmet = mdot_draw * cp_w * deficit if deficit > 0.0 else 0.0
            else:
                q_unmet = 0.0

            q_loss_total = 0.0
            for k in range(N):
                q_loss_total += u_tank * a_node * (T_w_new[k] - T_amb)

            q_pcm_total = 0.0
            if has_pcm:
                for k in range(pcm_start, pcm_start + n_pcm_nodes):
                    q_pcm_k = ua_per_node[k] * (T_w_new[k] - T_pcm_node[k])
                    q_pcm_total += q_pcm_k
                    if m_pcm_per_node_kg[k] > 0.0:
                        h_pcm_node[k] += q_pcm_k * dt_sub / m_pcm_per_node_kg[k]
                        T_pcm_node[k], f_melt_node[k] = _T_and_f_of_h(
                            h_pcm_node[k], Ts_C, Tl_C, h_s_J_kg, latent_heat_J_kg, cp_solid, cp_liquid)

            T_w = _pav_increasing(T_w_new, m_water_node_kg, N)

            cur_max_w = T_w[0]
            for k in range(1, N):
                if T_w[k] > cur_max_w:
                    cur_max_w = T_w[k]
            if cur_max_w > max_water_temp:
                max_water_temp = cur_max_w

            cur_max_pcm = -1.0e9
            if has_pcm:
                cur_max_pcm = T_pcm_node[pcm_start]
                for k in range(pcm_start + 1, pcm_start + n_pcm_nodes):
                    if T_pcm_node[k] > cur_max_pcm:
                        cur_max_pcm = T_pcm_node[k]
                if cur_max_pcm > max_pcm_temp:
                    max_pcm_temp = cur_max_pcm

            if cur_max_w >= max_water_C or (has_pcm and cur_max_pcm >= max_pcm_C):
                n_safety += 1

            E_collector_J += q_collector * dt_sub
            E_load_J += q_load * dt_sub
            E_loss_J += q_loss_total * dt_sub
            E_unmet_J += q_unmet * dt_sub
            if q_pcm_total >= 0.0:
                E_charge_J += q_pcm_total * dt_sub
            else:
                E_discharge_J += -q_pcm_total * dt_sub

            hour_q_collector += q_collector * dt_sub
            hour_q_load += q_load * dt_sub
            hour_q_pcm += q_pcm_total * dt_sub
            hour_q_loss += q_loss_total * dt_sub
            hour_q_unmet += q_unmet * dt_sub

        if has_pcm:
            s_f = 0.0
            for k in range(pcm_start, pcm_start + n_pcm_nodes):
                s_f += f_melt_node[k]
            mean_f_melt = s_f / n_pcm_nodes
        else:
            mean_f_melt = 0.0

        if was_fully_liquid and mean_f_melt < 0.5:
            was_fully_liquid = False
        if mean_f_melt >= 0.999 and not was_fully_liquid:
            complete_cycles += 1
            was_fully_liquid = True
        last_f_melt_mean = mean_f_melt

        if record_hourly:
            hourly_out[i, 0] = T_w[N - 1]
            hourly_out[i, 1] = T_w[0]
            s_t = 0.0
            if has_pcm:
                for k in range(pcm_start, pcm_start + n_pcm_nodes):
                    s_t += T_pcm_node[k]
                hourly_out[i, 2] = s_t / n_pcm_nodes
            else:
                for k in range(N):
                    s_t += T_w[k]
                hourly_out[i, 2] = s_t / N
            hourly_out[i, 3] = mean_f_melt
            hourly_out[i, 4] = hour_q_collector / 3600.0
            hourly_out[i, 5] = hour_q_load / 3600.0
            hourly_out[i, 6] = hour_q_pcm / 3600.0
            hourly_out[i, 7] = hour_q_loss / 3600.0
            hourly_out[i, 8] = hour_q_unmet / 3600.0
            hourly_out[i, 9] = hour_shield_water
            hourly_out[i, 10] = hour_shield_pcm

    return (hourly_out, T_w, T_pcm_node, h_pcm_node,
            E_collector_J, E_load_J, E_loss_J, E_unmet_J, E_charge_J, E_discharge_J,
            max_water_temp, max_pcm_temp, n_safety, n_shield_water, n_shield_pcm,
            last_f_melt_mean, complete_cycles)


def run_year_multinode_fast(weather_hourly: pd.DataFrame, demand: DemandModel, mains_temp_C: float,
                             design: DesignRuntime, pcm_props: PCMThermalProps, system_config: dict,
                             record_hourly: bool = True) -> SimulationResult:
    """Drop-in replacement for tank_model_multinode.run_year_multinode:
    identical signature, identical SimulationResult. All per-year-constant
    quantities are reduced to primitives here; the hot loop runs compiled."""
    tank_cfg = system_config.get("tank", {})
    N = int(tank_cfg.get("n_nodes", 10))
    stack_anchor = tank_cfg.get("stack_anchor", "center")
    mix_enh = float(tank_cfg.get("axial_mixing_enhancement", 5.0))

    solver = system_config["solver"]
    n_substeps_per_hour = int(round(3600 / solver["timestep_s"]))

    water_cfg = system_config["water"]
    cp_w = float(water_cfg["cp_J_kgK"])
    rho_w = float(water_cfg["density_kg_m3"])
    k_w = float(water_cfg.get("k_W_mK", 0.63))

    u_tank = float(system_config["tank"]["U_tank_W_m2K"])
    a_node = float(design.tank_surface_area_m2) / N

    delivery_target_C = float(system_config["delivery"]["target_temp_C"])
    max_water_C = float(system_config["safety"]["max_water_temp_C"])
    max_pcm_C = float(system_config["safety"]["max_pcm_temp_C"])
    has_pcm = bool(design.n_capsule > 0)

    shield_enabled = bool(system_config["safety"].get("shield_enabled", False))
    # Predictive (end-of-substep) shield decision. Default TRUE: the
    # lagged alternative was measured to manufacture up to 9.3 C of false
    # PCM overshoot at dt=300 s (src/verify/dt_convergence.py), which
    # would make NSGA-II reject feasible designs and accept infeasible
    # ones, since PCM peak <= 65 C is an optimizer CONSTRAINT. Set
    # safety.shield_predictive: false to reproduce pre-2026-10-28 numbers.
    shield_predictive = bool(system_config["safety"].get("shield_predictive", True))
    guard_band_C = float(system_config["safety"].get("shield_guard_band_C", 3.0))

    # TWO SEPARATE MECHANISMS, per Manvitha's report section 3.4 ("Table 9.
    # Mechanisms kept in both tank models"):
    #
    #   water-side bypass  : "Collector stops while top-node water is at or
    #                         above 72 C"                  (IS 12976:2023 8.2)
    #   PCM-side charge block : "Capsule UA set to zero while PCM at or above
    #                         62 C and water hotter than PCM; discharge never
    #                         blocked"
    #
    # These are NOT the same trip. Tamil Nadu previously collapsed them into
    # one by taking water_trip = min(72, 62) = 62 and stopping the COLLECTOR
    # whenever the PCM got hot, which starved the entire tank to protect the
    # capsules: water was pinned at 62 C, so PCMs melting at 54-58 C had
    # only ~4.5 C of charging window, barely melted (f_melt 0.006-0.08) and
    # acted as dead mass -- measured g_window of -36 to -267 kWh/yr across
    # every regime and volume fraction.
    #
    # Rajasthan never stops the collector for the PCM's sake. She decouples
    # the capsules thermally (UA -> 0, charging direction only) and lets the
    # water keep heating to its own 72 C bypass. That is why her water peaks
    # at 73.3 C while her PCM peaks at 64.1 C, under the SAME 65/75 C limits
    # this project already has.
    water_trip_C = max_water_C - guard_band_C      # 72 C -- water's own limit, never the PCM's
    pcm_trip_C = max_pcm_C - guard_band_C          # 62 C -- blocks CHARGING only, not the collector

    # G2/D3: PCM mass comes from the INNER sphere (D - 2 t_wall) and the
    # aluminium shell's heat capacity is folded into the PCM node via an
    # augmented cp. The OUTER volume is still what displaces water in the
    # tank, so v_pcm_total_m3 (packing/displacement) stays on the outer
    # geometry while the mass does not. See src/simulation/capsule_mass.py.
    if has_pcm:
        cap = capsule_breakdown(design.n_capsule, design.capsule_diameter_m,
                                pcm_props.density_kg_m3, system_config)
        pcm_props = props_with_wall_capacity(pcm_props, cap)
        m_pcm_total_kg = cap.m_pcm_total_kg
    else:
        cap = None
        m_pcm_total_kg = 0.0
    v_pcm_total_m3 = design.n_capsule * design.capsule_volume_m3 if has_pcm else 0.0
    v_node_nominal_m3 = design.tank_volume_m3 / N

    if has_pcm:
        n_pcm_nodes = max(1, int(np.ceil(v_pcm_total_m3 / v_node_nominal_m3)))
        pcm_nodes = capsule_node_band(N, n_pcm_nodes, stack_anchor)
        pcm_start = int(pcm_nodes[0])
    else:
        n_pcm_nodes = 0
        pcm_nodes = np.array([], dtype=int)
        pcm_start = 0

    is_pcm_node = np.zeros(N, dtype=bool)
    is_pcm_node[pcm_nodes] = True
    n_capsule_per_node = np.where(is_pcm_node, design.n_capsule / max(n_pcm_nodes, 1), 0.0)
    v_pcm_per_node_m3 = np.where(is_pcm_node, v_pcm_total_m3 / max(n_pcm_nodes, 1), 0.0)
    m_pcm_per_node_kg = np.where(is_pcm_node, m_pcm_total_kg / max(n_pcm_nodes, 1), 0.0)

    v_water_node_m3 = v_node_nominal_m3 - v_pcm_per_node_m3
    m_water_node_kg = np.maximum(v_water_node_m3, 1e-9) * rho_w

    tank_height_m = design.tank_volume_m3 / max(design.cross_section_area_m2, 1e-9)
    dz_m = tank_height_m / N
    cond_UA_per_link = mix_enh * k_w * design.cross_section_area_m2 / max(dz_m, 1e-9)

    superficial_velocity = (design.flow_rate_kg_s / rho_w / design.cross_section_area_m2
                             if design.cross_section_area_m2 > 0 else 0.0)

    # ---- year-constant capsule resistances, hoisted out of the loop ----
    if has_pcm:
        integ = system_config["pcm_integration"]
        # Water-side convection and the thin wall act on the OUTER surface.
        h_w = water_side_htc_w_m2k(superficial_velocity, design.capsule_diameter_m, system_config)
        r_conv = 1.0 / (h_w * design.capsule_area_m2) if h_w > 0 else 1e18
        r_wall = integ["capsule_wall_thickness_m"] / (
            integ["capsule_wall_conductivity_W_mK"] * design.capsule_area_m2)
        r_conv_wall_const = float(r_conv + r_wall)
        enhancement = float(integ["liquid_convection_enhancement"])
        # D3: the PCM-side conduction path is on the INNER radius and INNER
        # area. r_pcm = r_in / (5 k_eff A_in), and only k_eff varies during
        # the run, so the geometric part is collapsed to one constant.
        pcm_r_coeff = float((cap.inner_diameter_m / 2.0) / (5.0 * cap.inner_area_m2))
        pcm_conductivity_W_mK = float(pcm_props.conductivity_W_mK)
    else:
        r_conv_wall_const, pcm_r_coeff = 1e18, 0.0
        pcm_conductivity_W_mK, enhancement = 0.0, 1.0

    collector_cfg = system_config["collector"]
    collector_cutoff_Wm2 = float(collector_cfg["min_irradiance_cutoff_Wm2"])
    fr_tau_alpha_area = float(collector_cfg["area_m2"] * collector_cfg["fr_tau_alpha"])
    fr_ul_area = float(collector_cfg["area_m2"] * collector_cfg["fr_ul_W_m2K"])

    # ---- initial state (identical to the reference implementation) ----
    T_w_init = np.full(N, float(solver["initial_water_temp_C"]))
    if has_pcm:
        init_state = solver["initial_pcm_state"]
        if init_state == "solid":
            T_pcm_init_val = pcm_props.Ts_C - 5.0
        elif init_state == "liquid":
            T_pcm_init_val = pcm_props.Tl_C + 5.0
        else:
            T_pcm_init_val = pcm_props.Tm_C
        h_pcm_init = np.full(N, float(enthalpy_of_temperature(T_pcm_init_val, pcm_props)))
        T_pcm_init = np.full(N, float(T_pcm_init_val))
    else:
        h_pcm_init = np.zeros(N)
        T_pcm_init = T_w_init.copy()
    f_melt_init = np.zeros(N)

    E_initial_J = (float(np.sum(m_water_node_kg * cp_w * T_w_init))
                   + float(np.sum(m_pcm_per_node_kg * h_pcm_init)))

    n_hours = len(weather_hourly)
    ghi_arr = weather_hourly["GHI_Wm2"].to_numpy(dtype=float)
    tamb_arr = weather_hourly["T_amb_C"].to_numpy(dtype=float)
    # G1: local (IST) hour by FLOOR -- see demand_profile.local_hour_index.
    hour_of_day_idx_arr = local_hour_index(weather_hourly)
    hour_of_day_arr = hour_of_day_idx_arr.astype(float)

    draw_mass_per_hour_of_day = np.array(
        [demand.draw_mass_kg_for_hour(h) for h in range(24)], dtype=float)

    (hourly_out, T_w_final, T_pcm_final, h_pcm_final,
     E_collector_J, E_load_J, E_loss_J, E_unmet_J, E_charge_J, E_discharge_J,
     max_water_temp, max_pcm_temp, n_safety, n_shield_water, n_shield_pcm,
     last_f_melt_mean, complete_cycles) = _simulate_year_core(
        n_hours, n_substeps_per_hour,
        ghi_arr, tamb_arr, draw_mass_per_hour_of_day, hour_of_day_idx_arr,
        N, has_pcm, pcm_start, n_pcm_nodes,
        m_water_node_kg, m_pcm_per_node_kg, n_capsule_per_node,
        float(cond_UA_per_link), cp_w, float(mains_temp_C), u_tank, a_node,
        delivery_target_C, max_water_C, max_pcm_C,
        shield_enabled, shield_predictive, float(water_trip_C), float(pcm_trip_C),
        collector_cutoff_Wm2, fr_tau_alpha_area, fr_ul_area, float(design.flow_rate_kg_s),
        r_conv_wall_const, pcm_r_coeff, pcm_conductivity_W_mK, enhancement,
        float(pcm_props.Ts_C), float(pcm_props.Tl_C), float(pcm_props.h_s_J_kg),
        float(pcm_props.latent_heat_J_kg), float(pcm_props.cp_solid_J_kgK),
        float(pcm_props.cp_liquid_J_kgK),
        T_w_init, h_pcm_init, T_pcm_init, f_melt_init, bool(record_hourly),
    )

    acc = EnergyAccumulator(
        E_collector_J=E_collector_J, E_load_J=E_load_J, E_loss_J=E_loss_J,
        E_pump_J=0.0, E_unmet_J=E_unmet_J,
        E_charge_J=E_charge_J, E_discharge_J=E_discharge_J,
        E_initial_J=E_initial_J,
        E_final_J=(float(np.sum(m_water_node_kg * cp_w * T_w_final))
                   + float(np.sum(m_pcm_per_node_kg * h_pcm_final))),
        n_steps=n_hours * n_substeps_per_hour, n_failed_steps=0,
    )

    if record_hourly:
        hourly_df = pd.DataFrame({
            "hour_index": np.arange(n_hours),
            "hour_of_day": hour_of_day_arr,
            "I_t_Wm2": ghi_arr,
            "T_amb_C": tamb_arr,
            "T_w_C": hourly_out[:, 0],
            "T_w_bottom_C": hourly_out[:, 1],
            "T_w_top_C": hourly_out[:, 0],
            "T_pcm_C": hourly_out[:, 2],
            "f_melt": hourly_out[:, 3],
            "Q_collector_Wh": hourly_out[:, 4],
            "Q_load_Wh": hourly_out[:, 5],
            "Q_pcm_Wh": hourly_out[:, 6],
            "Q_loss_Wh": hourly_out[:, 7],
            "Q_pump_Wh": np.zeros(n_hours),
            "Q_unmet_Wh": hourly_out[:, 8],
            # Split, then the total. shield_activations is kept as the sum
            # so existing readers of that column keep working; the two
            # mechanisms are also exposed separately because d_overheat is
            # defined on the split (report section 7.5).
            "shield_water_activations": hourly_out[:, 9].astype(int),
            "shield_pcm_activations": hourly_out[:, 10].astype(int),
            "shield_activations": (hourly_out[:, 9] + hourly_out[:, 10]).astype(int),
        })
    else:
        hourly_df = pd.DataFrame()

    return SimulationResult(
        hourly=hourly_df, energy=acc.residual_report(),
        max_water_temp_C=float(max_water_temp), max_pcm_temp_C=float(max_pcm_temp),
        n_safety_violations=int(n_safety), final_f_melt=float(last_f_melt_mean),
        complete_melt_cycles=int(complete_cycles), initial_f_melt=0.0,
        n_clipped_steps=0,
        n_shield_activations=int(n_shield_water + n_shield_pcm),
        n_shield_water_activations=int(n_shield_water),
        n_shield_pcm_activations=int(n_shield_pcm),
    )
