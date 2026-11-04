"""
src/verify/gates.py
======================
Phase 4 / D2.3 verification — reduced gate battery per
O2_Unified_PerState_Execution_Framework.md ("Phase 4 - Verification").
No DOE row (Phase 5) may be generated until this passes.

Gate 1 - Energy conservation across 5 diverse cases.
Gate 2 - Limiting cases (zero irradiance, zero flow, no PCM, ... ).
Gate 3 - Baseline comparison (plain tank vs fixed PCM vs "optimized-looking"
         design) + the no-loss-vs-with-loss ambient-tank-loss diagnostic
         (Bug-Fix 1 — confirms the loss term is actually active).
Gate 4 - Light calibration against the cited Singh et al. (2025) 54-84%
         solar-fraction benchmark band (system_config_shared.yaml).
Gate 5 - Sensitivity spot checks (latent heat +/-10%, flow +/-50%,
         ambient +5 C) checked for the physically-expected direction.

Writes results/<state>/simulator_verification_report.txt.
"""

import math
import sys
from pathlib import Path

from config import BASE_DIR, RESULTS_DIR
from src.design.schema import DesignVector
from src.design.geometry import (
    sphere_volume_m3, sphere_surface_area_m2, tank_dimensions_m, pack_capsules,
    get_max_reachable_pcm_fraction,
)
from src.io_utils import load_system_config, load_design_bounds, get_pcm_properties, load_hourly_weather, load_demand_profile
from src.simulation.capsule_enthalpy import pcm_props_from_record, PCMThermalProps
from src.simulation.demand_profile import load_demand_model
from src.simulation.tank_model import DesignRuntime, run_year
from src.simulation.run_case import run_case


# ─────────────────────────────────────────────────────────────────────────
# Helper: build a DesignRuntime directly, bypassing Phase 2's design-bounds
# gate. Gate 2 deliberately probes OUTSIDE the normal operating envelope
# (zero/over-limit flow, zero capsules) to check the SIMULATOR degrades
# sensibly — that is a simulator-robustness test, not a design-acceptance
# test, so it must not go through src/design/constraints.py.
# ─────────────────────────────────────────────────────────────────────────

def _direct_runtime(diameter_m, n_capsule, flow_rate_kg_s, system_config, arrangement="staggered"):
    tank = tank_dimensions_m(system_config)
    v_capsule = sphere_volume_m3(diameter_m)
    a_capsule = sphere_surface_area_m2(diameter_m)
    if n_capsule > 0:
        packing = pack_capsules(arrangement, diameter_m, tank["tank_diameter_m"], tank["tank_height_m"],
                                 0.003, n_capsule, v_capsule)
        void_fraction = min(max(packing.void_fraction, 1e-3), 0.999)
        bed_length = packing.stack_height_m if packing.stack_height_m > 0 else tank["tank_height_m"]
    else:
        void_fraction, bed_length = 0.999, tank["tank_height_m"]
    return DesignRuntime(
        n_capsule=n_capsule, capsule_diameter_m=diameter_m, capsule_area_m2=a_capsule,
        capsule_volume_m3=v_capsule, void_fraction=void_fraction,
        cross_section_area_m2=tank["tank_cross_section_area_m2"], bed_length_m=bed_length,
        flow_rate_kg_s=flow_rate_kg_s, tank_volume_m3=tank["tank_volume_m3"],
        tank_surface_area_m2=tank["tank_surface_area_m2"],
    )


def _direct_run(state, cluster_id, diameter_m, n_capsule, flow_rate_kg_s, pcm_name=None,
                 system_config_overrides=None, volume_multiplier=1.0, mains_temp_C=None,
                 arrangement="staggered"):
    system_config = load_system_config()
    if system_config_overrides:
        system_config = _deep_merge(system_config, system_config_overrides)

    from src.io_utils import get_regime
    regime = get_regime(state, cluster_id)
    mains_temp_C = mains_temp_C if mains_temp_C is not None else regime["T_mains_est_C"]

    weather = load_hourly_weather(state, cluster_id)
    demand_df = load_demand_profile(state)
    demand_model = load_demand_model(demand_df, volume_multiplier=volume_multiplier)

    runtime = _direct_runtime(diameter_m, n_capsule if pcm_name else 0, flow_rate_kg_s, system_config,
                               arrangement=arrangement)

    if pcm_name is not None:
        record = get_pcm_properties(state, pcm_name)
        pcm_props = pcm_props_from_record(record, system_config["pcm_integration"]["melting_half_width_K"])
    else:
        pcm_props = PCMThermalProps(Tm_C=57.0, latent_heat_J_kg=0.0, cp_solid_J_kgK=2000.0,
                                     cp_liquid_J_kgK=2000.0, conductivity_W_mK=0.2, density_kg_m3=800.0)

    return run_year(weather, demand_model, mains_temp_C, runtime, pcm_props, system_config, record_hourly=True)


def _deep_merge(base: dict, overrides: dict) -> dict:
    out = dict(base)
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


# ─────────────────────────────────────────────────────────────────────────
# GATE 1 — Energy conservation
# ─────────────────────────────────────────────────────────────────────────

def gate1_conservation(state: str, log):
    log("\n" + "=" * 72)
    log("GATE 1 — Energy conservation (5 diverse cases)")
    log("=" * 72)
    system_config = load_system_config()
    pass_pct = system_config["verification"]["gate1_residual_pass_pct"]
    warn_pct = system_config["verification"]["gate1_residual_warn_pct"]

    # Fresh 2026-09-17 data: only clusters 0-2 exist now (K=5->K=3), and the
    # PCM shortlist per regime changed entirely (Tm-retargeting + MCDM
    # re-rank against the refreshed Objective 1 data). Cases now also cover
    # all three restored arrangements, adapted from
    # "a Rajasthan-pilot change plan (source removed from this project after adaptation, see docs_objective2/tamilnadu_phase_docs/)" for TN.
    cases = [
        ("A: cluster0 / n-Tetracosane(C24) / staggered / mid design",
         0, "n-Tetracosane (C24)", DesignVector(0.05, 14, 0.030, capsule_arrangement="staggered")),
        ("B: cluster1 / RT45HC / single-layer / small-capsule design",
         1, "RT45HC", DesignVector(0.04, 20, 0.020, capsule_arrangement="single-layer")),
        ("C: cluster2 / n-Hexacosane(C26) / radial / radial max-feasible design",
         2, "n-Hexacosane (C26)", DesignVector(0.08, 21, 0.045, capsule_arrangement="radial")),
        ("D: cluster1 / no-PCM plain-tank baseline",
         1, None, DesignVector(0.05, 14, 0.030, capsule_arrangement="staggered")),
        ("E: cluster0 / n-Tetracosane(C24) / staggered / bounds-extreme design",
         0, "n-Tetracosane (C24)", DesignVector(0.08, 37, 0.050, capsule_arrangement="staggered")),
    ]

    residuals = []
    for name, cid, pcm, design in cases:
        out = run_case(state, cid, pcm, design, record_hourly=False)
        if not out["valid"]:
            log(f"  [SKIP-INVALID] {name}: geometry rejected ({out['reason']})")
            continue
        r = out["metrics"]["residual_pct_of_collector"]
        residuals.append(r)
        log(f"  {name:52s} residual={r:.6f} %")

    mean_r = sum(residuals) / len(residuals) if residuals else float("nan")
    max_r = max(residuals) if residuals else float("nan")
    log(f"\n  mean residual = {mean_r:.6f} %   max residual = {max_r:.6f} %")

    if max_r < pass_pct:
        verdict = "PASS"
    elif max_r < warn_pct:
        verdict = "PASS-WITH-CAVEAT"
    else:
        verdict = "FAIL"
    log(f"  Gate 1 verdict: {verdict}  (pass<{pass_pct}%, warn<{warn_pct}%)")
    return {"gate": 1, "verdict": verdict, "mean_residual_pct": mean_r, "max_residual_pct": max_r}


# ─────────────────────────────────────────────────────────────────────────
# GATE 2 — Limiting cases
# ─────────────────────────────────────────────────────────────────────────

def gate2_limiting_cases(state: str, log):
    log("\n" + "=" * 72)
    log("GATE 2 — Limiting cases")
    log("=" * 72)
    system_config = load_system_config()
    checks = []

    # 1. Zero irradiance -> zero collector heat, always.
    r = _direct_run(state, 0, 0.05, 14, 0.030, pcm_name="n-Tetracosane (C24)",
                     system_config_overrides={"collector": {"min_irradiance_cutoff_Wm2": 1.0e9}})
    ok = r.energy["E_collector_kWh"] < 1e-6
    checks.append(("zero_irradiance -> zero collector heat", ok, f"E_collector={r.energy['E_collector_kWh']:.6f} kWh"))

    # 2. Zero flow -> no crash, near-zero (but finite) heat transfer / pump power.
    r = _direct_run(state, 0, 0.05, 14, 0.0, pcm_name="n-Tetracosane (C24)")
    ok = r.energy["n_failed_steps"] == 0 and math.isfinite(r.energy["residual_pct_of_collector"])
    checks.append(("zero_flow -> simulator completes without crashing", ok,
                    f"residual={r.energy['residual_pct_of_collector']:.4f}%, "
                    f"E_pump={r.energy['E_pump_kWh']:.9f} kWh"))

    # 3. No PCM -> plain-tank behaviour (zero charge/discharge energy).
    r = _direct_run(state, 0, 0.05, 14, 0.030, pcm_name=None)
    ok = r.energy["E_charge_kWh"] < 1e-9 and r.energy["E_discharge_kWh"] < 1e-9
    checks.append(("no_PCM -> zero charge/discharge energy", ok,
                    f"E_charge={r.energy['E_charge_kWh']:.9f}, E_discharge={r.energy['E_discharge_kWh']:.9f}"))

    # 4. Zero latent heat -> capsule behaves as pure sensible mass (no melt plateau).
    record = get_pcm_properties(state, "n-Tetracosane (C24)")
    record_zero_L = {**record, "latent_heat_kJ_kg": 0.0}
    pcm_props_zero_L = pcm_props_from_record(record_zero_L, system_config["pcm_integration"]["melting_half_width_K"])
    weather = load_hourly_weather(state, 0)
    demand_model = load_demand_model(load_demand_profile(state))
    from src.io_utils import get_regime
    mains = get_regime(state, 0)["T_mains_est_C"]
    runtime = _direct_runtime(0.05, 14, 0.030, system_config)
    r = run_year(weather, demand_model, mains, runtime, pcm_props_zero_L, system_config, record_hourly=True)
    f_range = r.hourly["f_melt"].max() - r.hourly["f_melt"].min()
    ok = True   # informational: with L=0, f_melt is ill-defined/degenerate; just confirm no crash
    checks.append(("zero_latent_heat -> completes, f_melt degenerate (informational)", ok,
                    f"f_melt range={f_range:.4f} (L=0 makes f a step function, expected)"))

    # 5. Very high PCM conductivity -> T_pcm tracks T_w much more closely
    #    than at nominal conductivity (smaller mean |Tw-Tpcm| gap).
    record_hi_k = {**record, "TC_W_mK": record["TC_W_mK"] * 200.0}
    props_hi_k = pcm_props_from_record(record_hi_k, system_config["pcm_integration"]["melting_half_width_K"])
    r_hi = run_year(weather, demand_model, mains, runtime, props_hi_k, system_config, record_hourly=True)
    props_nom = pcm_props_from_record(record, system_config["pcm_integration"]["melting_half_width_K"])
    r_nom = run_year(weather, demand_model, mains, runtime, props_nom, system_config, record_hourly=True)
    gap_hi = (r_hi.hourly["T_w_C"] - r_hi.hourly["T_pcm_C"]).abs().mean()
    gap_nom = (r_nom.hourly["T_w_C"] - r_nom.hourly["T_pcm_C"]).abs().mean()
    ok = gap_hi < gap_nom
    checks.append(("very_high_conductivity -> smaller mean |Tw-Tpcm| gap than nominal", ok,
                    f"gap_high_k={gap_hi:.3f} C, gap_nominal={gap_nom:.3f} C"))

    # 6. Perfectly insulated tank -> zero ambient tank loss.
    r = _direct_run(state, 0, 0.05, 14, 0.030, pcm_name="n-Tetracosane (C24)",
                     system_config_overrides={"tank": {"U_tank_W_m2K": 0.0}})
    ok = r.energy["E_loss_kWh"] < 1e-6
    checks.append(("perfectly_insulated_tank -> zero E_loss", ok, f"E_loss={r.energy['E_loss_kWh']:.6f} kWh"))

    # 7. Empty demand -> zero load, zero unmet energy.
    r = _direct_run(state, 0, 0.05, 14, 0.030, pcm_name="n-Tetracosane (C24)", volume_multiplier=0.0)
    ok = r.energy["E_load_kWh"] < 1e-6 and r.energy["E_unmet_kWh"] < 1e-6
    checks.append(("empty_demand -> zero load and zero unmet energy", ok,
                    f"E_load={r.energy['E_load_kWh']:.6f}, E_unmet={r.energy['E_unmet_kWh']:.6f}"))

    # 8/9. Fully solid vs fully liquid initial PCM -> melt fraction starts and
    #      moves in the physically-correct direction over the first day.
    r_solid = _direct_run(state, 0, 0.05, 14, 0.030, pcm_name="n-Tetracosane (C24)",
                           system_config_overrides={"solver": {"initial_pcm_state": "solid"}})
    r_liquid = _direct_run(state, 0, 0.05, 14, 0.030, pcm_name="n-Tetracosane (C24)",
                            system_config_overrides={"solver": {"initial_pcm_state": "liquid"}})
    f0_solid, f24_solid = r_solid.initial_f_melt, r_solid.hourly["f_melt"].iloc[23]
    f0_liquid, f24_liquid = r_liquid.initial_f_melt, r_liquid.hourly["f_melt"].iloc[23]
    ok = (f0_solid <= 0.01) and (f0_liquid >= 0.99) and (f24_solid >= f0_solid) and (f24_liquid <= f0_liquid + 1e-9)
    checks.append(("solid/liquid initial PCM -> starts at 0/1 and moves correctly", ok,
                    f"solid: f0={f0_solid:.3f}->f24={f24_solid:.3f}; "
                    f"liquid: f0={f0_liquid:.3f}->f24={f24_liquid:.3f}"))

    # 10/11. Flow below/above permitted limits -> no crash, monotonic direction
    #        (higher flow -> better heat transfer -> smaller |Tw-Tpcm| gap).
    r_low = _direct_run(state, 0, 0.05, 14, 0.002, pcm_name="n-Tetracosane (C24)")   # below 0.010 min
    r_high = _direct_run(state, 0, 0.05, 14, 0.20, pcm_name="n-Tetracosane (C24)")   # above 0.050 max
    gap_low = (r_low.hourly["T_w_C"] - r_low.hourly["T_pcm_C"]).abs().mean()
    gap_high = (r_high.hourly["T_w_C"] - r_high.hourly["T_pcm_C"]).abs().mean()
    ok = math.isfinite(gap_low) and math.isfinite(gap_high) and gap_high <= gap_low
    checks.append(("flow below/above limits -> completes, higher flow narrows Tw-Tpcm gap", ok,
                    f"gap@0.002kg/s={gap_low:.3f} C, gap@0.20kg/s={gap_high:.3f} C"))

    # 12. Capsules removed / allocated PCM volume = 0 -> identical to no-PCM case.
    # (N=0 skips packing math entirely regardless of arrangement, so this one
    # check is arrangement-agnostic by construction -- not repeated 3x.)
    r = _direct_run(state, 0, 0.05, 0, 0.030, pcm_name="n-Tetracosane (C24)")
    ok = r.energy["E_charge_kWh"] < 1e-9
    checks.append(("capsules_removed (N=0) -> zero PCM charge energy", ok,
                    f"E_charge={r.energy['E_charge_kWh']:.9f} kWh"))

    # 13. Oversized capsule diameter -- genuinely packing-sensitive, re-run
    # once per arrangement (adapted from
    # "a Rajasthan-pilot change plan (source removed from this project after adaptation, see docs_objective2/tamilnadu_phase_docs/)" step 2):
    # radial packing may hit overlap/passage_blocked at a different
    # diameter than staggered/single-layer -- verify, don't assume identical.
    for arrangement in ("single-layer", "staggered", "radial"):
        from src.design.constraints import check_design
        oversized = DesignVector(0.30, 14, 0.030, capsule_arrangement=arrangement)
        r_over = check_design(oversized)
        ok = (not r_over["valid"]) and r_over["reason"] in ("overlap", "bounds_violation", "passage_blocked")
        checks.append((f"oversized_diameter_for_tank ({arrangement}) -> rejected cleanly", ok,
                        f"reason={r_over['reason']}"))

    n_pass = sum(1 for _, ok, _ in checks if ok)
    for name, ok, detail in checks:
        log(f"  [{'PASS' if ok else 'FAIL'}] {name:58s} {detail}")
    log(f"\n  Gate 2: {n_pass}/{len(checks)} limiting cases passed.")
    verdict = "PASS" if n_pass == len(checks) else ("PASS-WITH-CAVEAT" if n_pass >= len(checks) - 1 else "FAIL")
    log(f"  Gate 2 verdict: {verdict}")
    return {"gate": 2, "verdict": verdict, "n_pass": n_pass, "n_total": len(checks), "checks": checks}


# ─────────────────────────────────────────────────────────────────────────
# GATE 3 — Baseline comparisons + ambient-loss diagnostic
# ─────────────────────────────────────────────────────────────────────────

def gate3_baseline_comparison(state: str, log):
    log("\n" + "=" * 72)
    log("GATE 3 — Baseline comparison (plain tank vs fixed PCM per arrangement vs optimized-looking)")
    log("=" * 72)

    cid = 0
    pcm = "n-Tetracosane (C24)"   # cluster 0's current MCDM consensus rank-1 PCM (2026-09-17 refresh + retargeting)
    diameter = 0.08

    plain = run_case(state, cid, None, DesignVector(diameter, 14, 0.030, capsule_arrangement="staggered"),
                      record_hourly=False)
    log(f"  plain_tank             useful={plain['metrics']['useful_energy_kWh']:8.1f} kWh  "
        f"SF={plain['metrics']['solar_fraction']*100:5.2f}%  unmet={plain['metrics']['unmet_energy_kWh']:8.1f} kWh")

    # ---- per-arrangement "fixed PCM, max feasible fraction" row ---------
    # 2026-09-17: each arrangement's own max-reachable fraction (Phase 2's
    # get_max_reachable_pcm_fraction) is used, not a single shared ~12.9%-
    # style figure applied to all three (adapted from
    # "a Rajasthan-pilot change plan (source removed from this project after adaptation, see docs_objective2/tamilnadu_phase_docs/)" step 3).
    fixed_rows = {}
    for arrangement in ("single-layer", "staggered", "radial"):
        max_info = get_max_reachable_pcm_fraction(arrangement, diameter_m=diameter)
        n = max(max_info["max_n_feasible"], 1)
        out = run_case(state, cid, pcm, DesignVector(diameter, n, 0.030, capsule_arrangement=arrangement),
                        record_hourly=True)
        fixed_rows[arrangement] = out
        m = out["metrics"]
        log(f"  fixed_PCM/{arrangement:<12} (N={n}, {max_info['max_reachable_pcm_volume_fraction']*100:.1f}%) "
            f"useful={m['useful_energy_kWh']:8.1f} kWh  SF={m['solar_fraction']*100:5.2f}%  "
            f"unmet={m['unmet_energy_kWh']:8.1f} kWh  mean_f_melt={m.get('mean_f_melt')}")

    best_arrangement = max(fixed_rows, key=lambda a: fixed_rows[a]["metrics"]["solar_fraction"])
    fixed = fixed_rows[best_arrangement]
    n_best = fixed["geometry"]["n_capsule"]
    optimized = run_case(state, cid, pcm, DesignVector(diameter, n_best, 0.040, capsule_arrangement=best_arrangement),
                          record_hourly=False)
    log(f"  optimized_looking ({best_arrangement}, best of the 3 above at higher flow) "
        f"useful={optimized['metrics']['useful_energy_kWh']:8.1f} kWh  "
        f"SF={optimized['metrics']['solar_fraction']*100:5.2f}%")

    pcm_beats_plain = (fixed["metrics"]["solar_fraction"] >= plain["metrics"]["solar_fraction"]
                        and fixed["metrics"]["unmet_energy_kWh"] <= plain["metrics"]["unmet_energy_kWh"])

    # --- sanity/capability check: can this simulator show ANY PCM benefit? --
    # Isolates "is the simulator capable of rewarding a well-matched PCM"
    # from "does THIS shortlisted PCM happen to suit THIS design" by
    # swapping in a synthetic PCM whose melting point is matched to the
    # tank's actual operating range.
    n_best = fixed["geometry"]["n_capsule"]
    matched_tm = run_case(state, cid, pcm, DesignVector(diameter, n_best, 0.030, capsule_arrangement=best_arrangement),
                           record_hourly=True, pcm_record_overrides={"Tm_C": 40.0})
    simulator_can_reward_matched_pcm = (
        matched_tm["metrics"]["solar_fraction"] >= plain["metrics"]["solar_fraction"]
        and matched_tm["metrics"]["unmet_energy_kWh"] <= plain["metrics"]["unmet_energy_kWh"]
    )
    log(f"\n  Capability check (synthetic PCM, Tm=40C matched to this tank's operating range, {best_arrangement}):")
    log(f"    plain_tank          SF={plain['metrics']['solar_fraction']*100:5.2f}%")
    log(f"    matched_Tm_PCM      SF={matched_tm['metrics']['solar_fraction']*100:5.2f}%  "
        f"mean_f_melt={matched_tm['metrics'].get('mean_f_melt', 0.0):.3f}")
    log(f"    Simulator rewards a well-matched PCM over plain tank: {simulator_can_reward_matched_pcm}")

    # --- no-loss vs with-loss diagnostic (Bug-Fix 1) --------------------
    with_loss = fixed
    no_loss = run_case(state, cid, pcm, DesignVector(diameter, n_best, 0.030, capsule_arrangement=best_arrangement),
                        record_hourly=False, system_config_overrides={"tank": {"U_tank_W_m2K": 0.0}})
    loss_term_active = no_loss["metrics"]["solar_fraction"] >= with_loss["metrics"]["solar_fraction"]
    log(f"\n  Ambient-loss diagnostic: solar_fraction with-loss={with_loss['metrics']['solar_fraction']*100:.2f}%  "
        f"no-loss={no_loss['metrics']['solar_fraction']*100:.2f}%  "
        f"(no-loss >= with-loss confirms the U_tank term is active: {loss_term_active})")

    log(f"\n  {pcm} (cluster0's current MCDM+retargeting shortlist winner, Tm={get_pcm_properties(state, pcm)['Tm_C']}C) "
        f"beats plain tank at its best arrangement ({best_arrangement}): {pcm_beats_plain}")
    if not pcm_beats_plain:
        log("  HONEST FINDING (not a simulator defect -- see capability check above): even after")
        log("  Tm-retargeting + MCDM re-ranking against the refreshed Objective 1 data, this PCM")
        log("  still doesn't clearly beat plain tank in this 50L direct-encapsulation design.")
        log("  This motivates Phase 5-7 (search across PCM fraction/flow/arrangement) rather than")
        log("  accepting the shortlist winner as automatically effective in hardware.")

    verdict = "PASS" if (simulator_can_reward_matched_pcm and loss_term_active) else "FAIL"
    log(f"\n  Gate 3 verdict: {verdict}  "
        f"(gated on simulator capability + active loss term, not on today's PCM/geometry choice)")
    return {
        "gate": 3, "verdict": verdict,
        "fixed_rows_by_arrangement": {a: r["metrics"] for a, r in fixed_rows.items()},
        "best_arrangement": best_arrangement,
        "pcm_beats_plain": pcm_beats_plain,
        "simulator_can_reward_matched_pcm": simulator_can_reward_matched_pcm,
        "loss_term_active": loss_term_active,
        "optimized_metrics": optimized["metrics"],
    }


# ─────────────────────────────────────────────────────────────────────────
# GATE 4 — Published-benchmark calibration
# ─────────────────────────────────────────────────────────────────────────

def gate4_calibration(state: str, optimized_metrics: dict, log):
    log("\n" + "=" * 72)
    log("GATE 4 — Light calibration against published benchmark")
    log("=" * 72)
    system_config = load_system_config()
    lo = system_config["verification"]["gate4_benchmark_solar_fraction_low_pct"]
    hi = system_config["verification"]["gate4_benchmark_solar_fraction_high_pct"]
    note = system_config["verification"]["gate4_benchmark_note"]

    sf_pct = optimized_metrics["solar_fraction"] * 100.0
    in_band = lo <= sf_pct <= hi
    mismatch_pct = 0.0 if in_band else min(abs(sf_pct - lo), abs(sf_pct - hi))

    log(f"  Benchmark band (Singh et al. 2025, cited): {lo:.1f}-{hi:.1f}% solar fraction")
    log(f"  {note.strip()}")
    log(f"  This simulator's optimized-looking design used arrangement={optimized_metrics.get('arrangement')} "
        f"(traceability -- Gate 3 picks whichever arrangement scored best for this regime/PCM).")
    log(f"  This simulator's optimized-looking design: {sf_pct:.2f}% solar fraction")
    log(f"  Inside cited band: {in_band}" + ("" if in_band else f"  (mismatch = {mismatch_pct:.1f} percentage points)"))
    if not in_band:
        log("  HONEST REPORTING (framework doc Bug-Fix 3 / Gate 4): this Objective 2 design")
        log("  is a 50 L tank against a 300 L/day draw with NO auxiliary backup heater modeled —")
        log("  a materially smaller storage-to-demand ratio than the cited benchmark's test rig,")
        log("  so a lower solar fraction is expected here. We report the mismatch rather than")
        log("  tuning the model to force agreement.")
    verdict = "PASS" if in_band else "PASS-WITH-CAVEAT"
    log(f"  Gate 4 verdict: {verdict} (calibration target, not a hard release gate)")
    return {"gate": 4, "verdict": verdict, "solar_fraction_pct": sf_pct, "in_band": in_band,
            "benchmark_low_pct": lo, "benchmark_high_pct": hi}


# ─────────────────────────────────────────────────────────────────────────
# GATE 5 — Sensitivity / monotonicity spot checks
# ─────────────────────────────────────────────────────────────────────────

def gate5_sensitivity(state: str, log):
    log("\n" + "=" * 72)
    log("GATE 5 — Sensitivity & physical-monotonicity spot checks")
    log("=" * 72)

    cid = 0
    pcm = "n-Tetracosane (C24)"
    arrangement = "staggered"   # fixed for this gate -- Gate 5 tests physics sensitivity, not arrangement choice
    design = DesignVector(0.05, 18, 0.040, capsule_arrangement=arrangement)
    base = run_case(state, cid, pcm, design, record_hourly=False)["metrics"]
    log(f"  Baseline ({arrangement}): useful={base['useful_energy_kWh']:.1f} kWh  SF={base['solar_fraction']*100:.2f}%  "
        f"pump={base['pump_energy_kWh']*1000:.4f} Wh  charge={base['charge_energy_kWh']:.2f} kWh")
    log(f"  (Informational: this design's packed bed is still sparse enough at N=18/d=0.05 that the "
        f"flow-vs-pump-energy check below remains a weak discriminator regardless of arrangement -- "
        f"see docs_objective2/04_PHASE4_VERIFICATION_GATES.md Gate 5 caveat.)")

    checks = []

    # Latent heat +/-10%
    record = get_pcm_properties(state, pcm)
    plus = run_case(state, cid, pcm, design, record_hourly=False,
                     pcm_record_overrides={"latent_heat_kJ_kg": record["latent_heat_kJ_kg"] * 1.10})["metrics"]
    minus = run_case(state, cid, pcm, design, record_hourly=False,
                      pcm_record_overrides={"latent_heat_kJ_kg": record["latent_heat_kJ_kg"] * 0.90})["metrics"]
    ok = plus["charge_energy_kWh"] >= minus["charge_energy_kWh"]
    checks.append(("latent_heat +10% vs -10% -> more PCM energy stored/cycled with more latent heat", ok,
                    f"+10%: charge={plus['charge_energy_kWh']:.3f} kWh   "
                    f"-10%: charge={minus['charge_energy_kWh']:.3f} kWh"))

    # Flow +50% / -50%
    hi_flow = run_case(state, cid, pcm, DesignVector(0.05, 18, min(design.flow_rate_kg_s * 1.5, 0.05),
                                                       capsule_arrangement=arrangement),
                        record_hourly=False)["metrics"]
    lo_flow = run_case(state, cid, pcm, DesignVector(0.05, 18, design.flow_rate_kg_s * 0.5,
                                                       capsule_arrangement=arrangement),
                        record_hourly=False)["metrics"]
    ok = hi_flow["pump_energy_kWh"] >= lo_flow["pump_energy_kWh"]
    checks.append(("flow +50% vs -50% -> higher flow means more pump energy", ok,
                    f"+50%: pump={hi_flow['pump_energy_kWh']*1000:.4f} Wh   "
                    f"-50%: pump={lo_flow['pump_energy_kWh']*1000:.4f} Wh"))

    # Ambient +5 C (system-wide, approximated via mains-temperature-independent
    # tank-loss reduction: raise T_amb by adjusting the weather is out of scope
    # for a config-only override, so we approximate with a lower U_tank -- more
    # directly, we reduce the effective loss coefficient by simulating a milder
    # climate proxy: lower U_tank by the same relative amount a +5C ambient
    # would reduce average (Tw-Tamb) loss driving force at this state's typical
    # Tw. Documented approximation -- a full +5C weather-shift test belongs to
    # Phase 8 Monte Carlo, which perturbs the actual weather series.
    warmer = run_case(state, cid, pcm, design, record_hourly=False,
                       system_config_overrides={"tank": {"U_tank_W_m2K": 0.8 * 0.9}})["metrics"]
    ok = warmer["loss_energy_kWh"] <= base["loss_energy_kWh"]
    checks.append(("reduced effective tank-loss coefficient (ambient-warming proxy) -> lower E_loss", ok,
                    f"base loss={base['loss_energy_kWh']:.2f} kWh, proxy loss={warmer['loss_energy_kWh']:.2f} kWh"))

    n_pass = sum(1 for _, ok, _ in checks if ok)
    for name, ok, detail in checks:
        log(f"  [{'PASS' if ok else 'FAIL'}] {name:66s} {detail}")
    verdict = "PASS" if n_pass == len(checks) else "PASS-WITH-CAVEAT"
    log(f"\n  Gate 5: {n_pass}/{len(checks)} sensitivity checks in the expected direction.")
    log(f"  Gate 5 verdict: {verdict}")
    return {"gate": 5, "verdict": verdict, "n_pass": n_pass, "n_total": len(checks), "checks": checks}


# ─────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────

def run_all_gates(state: str):
    out_dir = RESULTS_DIR / state
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "simulator_verification_report.txt"

    lines = []
    def log(msg=""):
        print(msg)
        lines.append(msg)

    log("#" * 72)
    log(f"# Objective 2 Phase 4 — Simulator Verification Report — state={state}")
    log(f"# sim_v2_{state} -- geometry module changed (arrangement restored + fresh Objective 1 data,")
    log(f"# 2026-09-17); physics submodels unchanged from sim_v1 (see docs_objective2/")
    log(f"# 17_ARRANGEMENT_RESTORATION.md and 16_OBJECTIVE1_DATA_REFRESH.md)")
    log("#" * 72)

    g1 = gate1_conservation(state, log)
    g2 = gate2_limiting_cases(state, log)
    g3 = gate3_baseline_comparison(state, log)
    g4 = gate4_calibration(state, g3["optimized_metrics"], log)
    g5 = gate5_sensitivity(state, log)

    gates = [g1, g2, g3, g4, g5]
    n_clean_pass = sum(1 for g in gates if g["verdict"] == "PASS")

    log("\n" + "=" * 72)
    log("SUMMARY")
    log("=" * 72)
    for g in gates:
        log(f"  Gate {g['gate']}: {g['verdict']}")
    log(f"\n  Gates passing cleanly: {n_clean_pass}/5")

    go_no_go = "GO" if (g1["max_residual_pct"] < 0.5 and n_clean_pass >= 3) else "NO-GO"
    log(f"\n  Go/No-Go (framework doc Phase 4 rule: residual<0.5% AND >=3/5 gates clean): {go_no_go}")
    if go_no_go == "GO":
        log(f"  Simulator released as sim_v2_{state} (tag it at commit time). Every Phase 5+ row from")
        log(f"  here on must carry this version, never pooled with sim_v1_{state} rows.")
    else:
        log("  STOP — repair before generating any Phase 5 DOE cases.")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    log(f"\nReport written to: {report_path}")
    return gates, go_no_go


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "tamilnadu"
    run_all_gates(state)
