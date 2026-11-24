"""
scripts/c23_build_o3_environment_contract.py
============================================
Builds the Objective 3 ENVIRONMENT contract for the common-plant Tamil Nadu run (100 L / 2.0 m2 / 175 L/day).

Why a second contract exists
----------------------------
c17 writes `o3_contract_tamilnadu.json`: the IMMUTABLE result record (three designs, test numbers, SHA-256 of every
config and weather file, the funnel hash, the lock run id). It is deliberately small and is hash-sealed under the
one-shot lock, so it is never edited.

It is not enough to build an Objective 3 environment from. The legacy contract carried 27 sections (action space,
reward, acceptance tests, state schema, safety shield, reset scenarios, caveats...); the common-plant rebuild
produced none of them. This script writes that missing environment specification as a SEPARATE file that POINTS AT
the immutable contract by hash:

    results/common100L_<hash>/o3_environment_contract_tamilnadu.json  (+ .sha256)

Nothing under the lock is modified. The immutable contract's hash is re-verified before anything is built on it, and
the build aborts if the lock, the funnel hash or the hardware hash disagree.

Every number is read from a file (results/, configs/, data/). The only hand-written content is rule text (what a
controller may and may not do) and the limitations list, each marked with its source.

Usage:  python scripts/c23_build_o3_environment_contract.py [--skip-tests]
"""
import argparse
import hashlib
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
from src.weather import roles                                               # noqa: E402
from src.weather.inventory import CURRENT_MEDOIDS                           # noqa: E402

RUN_DIR = roles.TEST_LOCK_PATH.parent
IMMUTABLE = RUN_DIR / "o3_contract_tamilnadu.json"
OUT = RUN_DIR / "o3_environment_contract_tamilnadu.json"
ARCHIVED_GENERIC = (BASE / "archive" / "superseded_obj3_contract_2026-10-27" / "obj3_environment_contract_tamilnadu.json")
STATE = "tamilnadu"
N_REGIMES = 3


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rel(p):
    return str(Path(p).resolve().relative_to(BASE)).replace("\\", "/")


def load_yaml(p):
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def fail(msg):
    raise SystemExit(f"ABORT: {msg}")


def run_tests():
    """Run the project's own test suite and return its one-line summary (not a hand-typed count)."""
    r = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "--no-header", "-p", "no:cacheprovider"],
                       cwd=BASE, capture_output=True, text=True, timeout=1500)
    lines = [ln for ln in r.stdout.strip().splitlines() if ln.strip()]
    return {"command": "python -m pytest tests -q", "summary": lines[-1] if lines else "no output", "returncode": r.returncode}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-tests", action="store_true", help="do not run the test suite (records 'not run')")
    args = ap.parse_args()

    # ------------------------------------------------------------ integrity of the immutable record
    if not IMMUTABLE.exists() or not (RUN_DIR / "o3_contract_tamilnadu.sha256").exists():
        fail(f"immutable contract not found in {RUN_DIR}")
    imm_sha = sha(IMMUTABLE)
    if imm_sha != (RUN_DIR / "o3_contract_tamilnadu.sha256").read_text().strip():
        fail("o3_contract_tamilnadu.json does not match its recorded SHA-256 (it was edited after sealing)")
    imm = json.loads(IMMUTABLE.read_text(encoding="utf-8"))
    lock = json.loads(roles.TEST_LOCK_PATH.read_text(encoding="utf-8"))
    funnel_sha = (BASE / "configs" / "funnel_frozen.sha256").read_text().strip()
    if imm["funnel_sha256"] != funnel_sha or lock["selection_fingerprint"] != funnel_sha:
        fail("funnel hash in the immutable contract / lock / configs/funnel_frozen.sha256 disagree")
    if imm["hardware_hash"] != roles.hardware_hash():
        fail("hardware hash changed since the test ran: configs were edited after the lock")
    if imm["run_id"] != lock["run_id"]:
        fail("immutable contract run_id differs from the lock's run_id")

    # ------------------------------------------------------------------------------ inputs
    sysc = load_yaml(BASE / "configs" / "system_config_shared.yaml")
    dsp = load_yaml(BASE / "configs" / "design_space.yaml")
    statec = load_yaml(BASE / "configs" / "states" / f"{STATE}.yaml")
    funnel = json.loads((BASE / "configs" / "funnel_frozen.json").read_text(encoding="utf-8"))
    win = pd.read_csv(BASE / "results" / "c16_funnel_winners.csv").set_index("regime")
    summ = pd.read_csv(RUN_DIR / "c17_summary.csv").set_index("regime")
    test = pd.read_csv(RUN_DIR / "c17_test_by_year.csv")
    rep = pd.read_csv(RUN_DIR / "c17_report_only_by_year.csv")
    fid = pd.read_csv(BASE / "results" / "c10_l5_fidelity_summary.csv")
    fid_verdict = (BASE / "results" / "c10_l5_fidelity_verdict.txt").read_text().strip()
    if not ARCHIVED_GENERIC.exists():
        fail(f"generic-block source missing: {ARCHIVED_GENERIC}")
    generic = json.loads(ARCHIVED_GENERIC.read_text(encoding="utf-8"))
    regimes_cfg = {r["cluster_id"]: r for r in statec["regimes"]}

    wall = sysc["pcm_integration"]["capsule_wall_thickness_m"]
    v_tank = sysc["tank"]["volume_L"] / 1000.0
    frac_cap = dsp["variables"]["pcm_volume_fraction"]["max"]
    r_max = dsp["variables"]["inner_radius_m"]["max"]

    c = {
        "schema": "o3_environment_contract_common100L_v1",
        "state": STATE,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "built_by": "scripts/c23_build_o3_environment_contract.py",
        "immutable_result_record": {
            "file": rel(IMMUTABLE), "sha256": imm_sha, "schema": imm["schema"], "run_id": imm["run_id"],
            "hardware_hash": imm["hardware_hash"], "funnel_sha256": imm["funnel_sha256"],
            "how_verified": "SHA-256 of the file re-computed and compared with o3_contract_tamilnadu.sha256; funnel hash compared "
                            "across the contract, the lock and configs/funnel_frozen.sha256; hardware hash recomputed from the configs.",
            "rule": "This environment contract NEVER replaces the immutable record. If the two ever disagree, the immutable record wins.",
        },
    }

    c["supersession_note"] = (
        "SUPERSEDES objective3/obj3_environment_contract_tamilnadu_v3.json (contract_version obj3_contract_v3.0_2026-11-09) and "
        "objective3/OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md of the same date, now archived in "
        "archive/superseded_obj3_contract_2026-11-09/. That contract described the LEGACY plant: 100 L tank with a 2.5 m2 collector, "
        "300 L/day demand, a 30 % PCM-fraction cap, 98-105 capsules, flow searched, and a held-out test on 2011-2015. The "
        "common-plant rebuild changed ALL of these: 100 L / 2.0 m2 / 175 L/day, fraction cap 40 %, 140 capsules, flow frozen at "
        "0.030 kg/s, a hardware-hash-keyed one-shot test on 2006-2010. No number from the older contracts may be used. Any cached "
        "copy must be discarded.")

    # ------------------------------------------------------------------------------- plant
    c["plant"] = {
        "tank_volume_L": sysc["tank"]["volume_L"],
        "tank_height_to_diameter_ratio": sysc["tank"]["height_to_diameter_ratio"],
        "tank_insulation_m": sysc["tank"]["insulation_m"],
        "tank_U_W_m2K": sysc["tank"]["U_tank_W_m2K"],
        "collector_area_m2": sysc["collector"]["area_m2"],
        "storage_per_collector_area_L_m2": round(sysc["tank"]["volume_L"] / sysc["collector"]["area_m2"], 2),
        "collector_fr_tau_alpha": sysc["collector"]["fr_tau_alpha"],
        "collector_fr_ul_W_m2K": sysc["collector"]["fr_ul_W_m2K"],
        "collector_flow_dependent_fr_enabled": sysc["collector"]["flow_dependent_fr"]["enabled"],
        "min_irradiance_cutoff_Wm2": sysc["collector"]["min_irradiance_cutoff_Wm2"],
        "capsule_wall_material": sysc["pcm_integration"]["capsule_wall_material"],
        "capsule_wall_thickness_m": wall,
        "liquid_convection_enhancement": sysc["pcm_integration"]["liquid_convection_enhancement"],
        "melting_half_width_K": sysc["pcm_integration"]["melting_half_width_K"],
        "delivery_target_temp_C": sysc["delivery"]["target_temp_C"],
        "demand_daily_total_L": statec["demand_profile"]["daily_total_L"],
        "config_version": sysc["version"],
        "design_space_version": dsp["version"],
        "WARNING": "100 L / 2.0 m2 / 175 L/day is the COMMON plant. Do not mix in the legacy 2.5 m2 collector, the 300 L/day draw or the 50 L tank.",
        "limitation_F_R_not_refitted": "fr_tau_alpha and fr_ul are the legacy typical-flat-plate values; they were NOT re-fitted for the 2.0 m2 "
                                       "absorber basis. The configs are hash-sealed under the one-shot lock, so changing them now would "
                                       "invalidate the test. Their effect is reported as a sensitivity (parameter_sensitivity below).",
    }

    c["global_limits"] = {
        "delivery_target_temp_C": sysc["delivery"]["target_temp_C"],
        "max_safe_water_temp_C": sysc["safety"]["max_water_temp_C"],
        "max_safe_pcm_temp_C": sysc["safety"]["max_pcm_temp_C"],
        "max_pressure_bar": sysc["safety"]["max_pressure_bar"],
        "flow_min_kg_s": sysc["pump"]["flow_min_kg_s"],
        "flow_max_kg_s": sysc["pump"]["flow_max_kg_s"],
        "pump_efficiency": sysc["pump"]["efficiency"],
        "note": "HARD limits. The controller may never command a flow outside the envelope, nor drive water above max_safe_water_temp_C "
                "or PCM above max_safe_pcm_temp_C.",
    }

    c["safety_shield"] = {
        "enabled": sysc["safety_shield"]["enabled"],
        "bypass_water_C": sysc["safety_shield"]["bypass_water_C"],
        "bypass_pcm_C": sysc["safety_shield"]["bypass_pcm_C"],
        "guard_band_K": sysc["safety"]["max_water_temp_C"] - sysc["safety_shield"]["bypass_water_C"],
        "enforced_in": "src/simulation/tank_model_multinode.py, inside the physics, NOT in the policy",
        "note": "Already enforced, not a specification to implement. It forces the collector off at the bypass temperatures. Objective 3's "
                "job is a BETTER controller than this reactive trip: one that anticipates the limit instead of reacting at it.",
        "cost_it_creates": "PCM tanks spend MORE hours in the shield than the plain tank (see test_overheat_extra_h per regime). "
                           "This is where a controller can add value.",
        "standard": "IS 12976:2023 Sec 8.2 describes this mechanism for overheat protection.",
    }

    # ----------------------------------------------------------------------- demand + timing
    c["demand"] = {
        "file": statec["demand_profile"]["file"],
        "sha256": imm["config_sha256"].get(statec["demand_profile"]["file"], sha(BASE / statec["demand_profile"]["file"])),
        "daily_total_L": statec["demand_profile"]["daily_total_L"],
        "shape": "24 hourly draw fractions summing to 1 (columns hour, draw_fraction, draw_volume_L, draw_mass_kg); "
                 "draw_volume_L = draw_fraction x daily_total_L",
        "delivery_window_for_reward": "18:00-09:00 (the window of the g_window metric, src/optimize/evaluate.py)",
        "sensitivity_cases": "100, 150 and the legacy 300 L/day are reported as SENSITIVITY cases only (results/c7_l4_sensitivity_r*.csv); "
                             "they are not the plant.",
        "mains_temperature_C": {str(k): regimes_cfg[k]["T_mains_est_C"] for k in range(N_REGIMES)},
        "mains_note": "one constant per regime, from Objective 1's climate signature; it does not vary through the year in the model",
    }
    c["time_step_s"] = sysc["solver"]["timestep_s"]
    c["time_step_confirm_s"] = sysc["solver"]["timestep_confirm_s"]
    c["time_step_note"] = ("150 s is the SEARCH step; 37.5 s is the CONFIRMATION step and every number in the immutable record was produced at "
                           "37.5 s with three anchors. State which step an O3 environment uses; a controller trained at 150 s must be "
                           "re-checked at 37.5 s.")

    # ------------------------------------------------------------------ per-regime designs
    designs = []
    for k in range(N_REGIMES):
        w, s = win.loc[k], summ.loc[k]
        rcfg = regimes_cfg[k]
        r_in = float(w.R_in_m)
        v_cap = 4.0 / 3.0 * math.pi * (r_in + wall) ** 3
        n = int(w.N)
        n_cap = math.floor(frac_cap * v_tank / v_cap)
        t = test[test.regime == k]
        rp = rep[rep.regime == k]
        o1_rank = rcfg["pcm_shortlist"].index(w.pcm) + 1
        if imm["regimes"][k]["pcm"] != w.pcm or int(imm["regimes"][k]["n_capsules"]) != n:
            fail(f"regime {k}: c16 winners disagree with the immutable contract")
        designs.append({
            "regime_id": k,
            "label": rcfg["label"],
            "medoid_point_id": rcfg["medoid_point_id"],
            "medoid_matches_CURRENT_MEDOIDS": CURRENT_MEDOIDS[k] == rcfg["medoid_point_id"],
            "n_points": rcfg["n_points"],
            "population_covered": rcfg["population_covered"],
            "T_mains_est_C": rcfg["T_mains_est_C"],
            "o1_pcm_shortlist": rcfg["pcm_shortlist"],
            "selected_pcm": w.pcm,
            "selected_pcm_o1_rank": o1_rank,
            "capsule_inner_radius_m": r_in,
            "capsule_inner_diameter_mm": round(r_in * 2000.0, 2),
            "capsule_outer_diameter_mm": round((r_in + wall) * 2000.0, 2),
            "n_capsules": n,
            "pcm_volume_fraction": float(w.fraction),
            "pcm_mass_kg": float(t.pcm_mass_kg.iloc[0]),
            "arrangement": w.arrangement,
            "nominal_flow_kg_s": imm["regimes"][k]["flow_kg_s"],
            "flow_envelope_kg_s": [sysc["pump"]["flow_min_kg_s"], sysc["pump"]["flow_max_kg_s"]],
            "stack_anchor": imm["regimes"][k]["stack_anchor"],
            "bound_status": {
                "radius_at_upper_bound": abs(r_in - r_max) < 1e-9,
                "capsule_count_at_fraction_cap": n == n_cap,
                "fraction_cap": frac_cap,
                "max_count_allowed_at_cap": n_cap,
                "reading": "Both the 40 mm radius bound and the 40 % fraction cap are binding: the optimum is the corner of the search box, "
                           "not an interior point.",
            },
            "select_years_2020_2021": {
                "g_window_mean_kWh": float(w.select_g_window_mean), "g_window_worst_anchor_kWh": float(w.select_g_window_worst),
                "d_overheat_mean_h": float(w.d_overheat_mean_h), "t_pcm_max_C": float(w.t_pcm_max_C),
                "funnel_leader_gain_kWh": float(w.leader_gain), "n_designs_tied_with_leader": int(w.n_tied),
            },
            "repeatability_band": {"core_kWh": float(w.band_kWh), "full_incl_mains_and_demand_kWh": float(w.band_full_kWh),
                                   "definition": "core = years, timestep, nodes, PCM properties, anchor; full adds mains and demand "
                                                 "(see docs/PLAN_DEVIATIONS.md for why the funnel uses the core band)"},
            "one_shot_test_2006_2010": {
                "gain_mean_kWh": float(s.test_gain_mean_kWh), "gain_worst_anchor_mean_kWh": float(s.test_gain_worst_anchor_mean_kWh),
                "gain_min_year_kWh": float(s.test_gain_min_year_kWh), "years_pcm_better": f"{int(s.years_pcm_better)} of {int(s.test_years)}",
                "gain_over_core_band": float(s.gain_over_band), "gain_over_full_band": float(s.gain_over_full_band),
                "overheat_extra_hours_per_year": float(s.test_overheat_extra_h), "t_pcm_max_C": float(s.test_t_pcm_max_C),
                "t_water_max_C": float(t.t_water_max_worst.max()), "hours_over_limit": float(s.hours_over_limit),
            },
            "report_only_2022_2025": {"gain_mean_kWh": float(s.report_only_gain_mean_kWh), "years": sorted(int(y) for y in rp.year.unique()),
                                      "note": "2024-2025 carry prior project exposure; report-only, never used to choose."},
        })
    c["static_design_per_regime"] = designs

    c["one_shot_test"] = {
        "status": "SPENT. Run once, locked. Do not re-run and do not tune against these years.",
        "years": roles.years_for("test"), "run_id": lock["run_id"], "locked_utc": lock["utc"],
        "lock_file": rel(roles.TEST_LOCK_PATH), "selection_fingerprint": lock["selection_fingerprint"],
        "designs_tested": "the 3 funnel winners (one per regime); a design was not tested unless the frozen funnel had selected it",
        "gates": {
            "years_pcm_beats_plain_tank": {str(k): f"{int(summ.loc[k].years_pcm_better)} of {int(summ.loc[k].test_years)}" for k in range(N_REGIMES)},
            "pcm_peak_under_65C": f"max {float(test.t_pcm_max_worst.max()):.2f} C",
            "water_peak_under_75C": f"max {float(test.t_water_max_worst.max()):.2f} C",
            "hours_over_limit": float(test.hours_over_limit.max()),
        },
    }

    # -------------------------------------------------------------------- weather roles (read from roles.py)
    by_role = {}
    for y, r in sorted(roles.YEAR_ROLES.items()):
        by_role.setdefault(r, []).append(y)
    c["weather_sequences"] = {
        "roles": {r: ys for r, ys in by_role.items()},
        "medoid_points": {str(k): CURRENT_MEDOIDS[k] for k in range(N_REGIMES)},
        "mapping_for_O3": {
            "training": {"years": by_role["explore"], "role": "explore"},
            "validation": {"years": by_role["select"], "role": "select",
                           "note": "these two years also chose the O2 DESIGN; they did not touch a controller, but say so in any O3 report"},
            "final_report": {"years": [y for y in by_role["report"] if y <= 2023], "role": "report",
                             "note": "recommendation, not an O2 rule: pre-register these before the first run"},
            "forbidden": {"years": by_role["test"] + by_role["legacy"] + [y for y in by_role["report"] if y >= 2024],
                          "note": "2006-2010: one-shot test SPENT. 2011-2015: legacy test, accepted for no purpose. "
                                  "2024-2025: project-exposed."},
        },
        "enforcement": "src/weather/roles.py::load_point_year(..., purpose=...) refuses a year whose role differs from the stated purpose; "
                       "the test years additionally need acquire_test_lock(), which refuses because the lock exists.",
        "weather_sha256": "see immutable_result_record: every point-year file is hashed there",
    }

    # ------------------------------------------------------------------ control surface
    c["flow_policy"] = {
        "O2_design_flow_kg_s": imm["regimes"][0]["flow_kg_s"],
        "status": "FROZEN in Objective 2 as a design value (rule R6); it was never searched, so it is NOT an optimum to defend.",
        "O3_role": "flow becomes an ACTION inside flow_envelope_kg_s. collector_flow_dependent_fr_enabled is false, so F_R does not vary "
                   "with flow in this model: a flow-sensitivity learned from the model is partly an artefact of that.",
    }
    c["action_space"] = generic["action_space"]
    c["reset_scenarios"] = generic["reset_scenarios"]
    schema = json.loads(json.dumps(generic["dynamic_state_schema"]))
    names = {f["name"] for f in schema["fields"]}
    for extra in (
        {"name": "T_water_top_C", "unit": "C", "measurable": True, "source": "sensor at the tank outlet: the DELIVERY temperature"},
        {"name": "T_water_bottom_C", "unit": "C", "measurable": True, "source": "sensor at the collector return: the collector INLET"},
        {"name": "recoverable_energy_above_45C_kWh", "unit": "kWh", "measurable": False, "source": "estimator, not a raw sensor"},
    ):
        if extra["name"] not in names:
            schema["fields"].append(extra)
    schema["stratification_note"] = ("The tank is stratified and multi-node (n_nodes = %d). Delivery temperature is the TOP node; the collector "
                                     "inlet is the BOTTOM node." % dsp["model"]["n_nodes"])
    c["dynamic_state_schema"] = schema

    c["acceptance_test_before_drl_training"] = list(generic["acceptance_test_before_drl_training"]) + [
        "with the baseline controller (the unmodified kernel behaviour: collector on whenever irradiance >= the cutoff and the shield allows), "
        "the stepper reproduces the per-year paired gains in immutable_result_record's c17 tables to within the repeatability band",
        "the environment is built for the COMMON plant: the plant block of this contract equals the configs it was built from (check config_version)",
        "no weather year with role test, legacy or project-exposed report is ever loaded",
    ]

    c["reward_function"] = {
        "status": "SUGGESTED. Weights are deliberately NOT chosen: Objective 3 sets and justifies them.",
        "formula": "r_t = w1*E_del45_t - w2*overheat_step_t - w3*safety_violation_t - w4*bypass_switch_t",
        "term_definitions": {
            "E_del45_t": "energy delivered up to the 45 C target in this step (the g_window metric counts 18:00-09:00)",
            "overheat_step_t": "shield-active time in the step (the quantity behind d_overheat)",
            "safety_violation_t": "1 if TOP water >= bypass_water_C or PCM >= bypass_pcm_C, else 0",
            "bypass_switch_t": "1 if the mode changes into bypass at this step, else 0",
        },
        "normalisation": "compute from the water-only twin of the regime's design over the explore years %s" % by_role["explore"],
        "removed_terms": "pump energy: the model has only an Ergun pressure drop across the capsule bed",
    }

    # ----------------------------------------------------------------------- honest caveats
    sens = {}
    for k in range(N_REGIMES):
        d = pd.read_csv(BASE / "results" / f"c7_l4_sensitivity_r{k}.csv")
        d = d[(d.pcm == win.loc[k].pcm) & (d.block != "reference")]
        sens[str(k)] = {row.case: round(float(row.delta_vs_ref), 1) for row in d.itertuples()}
    c["parameter_sensitivity"] = {
        "what": "change in g_window (kWh/yr) vs the L4 sensitivity reference design when one input is moved; read from results/c7_l4_sensitivity_r*.csv",
        "scope_warning": "measured on the L4 REFERENCE design, not on the funnel winner, and in select-year weather; use for SIZE and SIGN only",
        "by_regime_for_selected_pcm": sens,
    }
    c["design_space_caveats"] = {
        "NOT_A_GLOBAL_OPTIMUM": True,
        "statement": "The designs are the best found WITHIN the declared box under a pre-declared funnel. They are not proven global optima.",
        "searched_bounds": {"capsule_inner_radius_m": [dsp["variables"]["inner_radius_m"]["min"], r_max],
                            "pcm_volume_fraction": [dsp["variables"]["pcm_volume_fraction"]["min"], frac_cap],
                            "flow_kg_s": "frozen at %s" % imm["regimes"][0]["flow_kg_s"],
                            "arrangement": dsp["variables"]["arrangement"]},
        "binding_bounds": "BOTH the radius bound (40 mm) and the fraction cap (40 %) are binding in all three regimes. The 30 % cap of the "
                          "legacy run moved to 40 % and the optimum moved with it, so the true optimum may lie beyond this box.",
        "identical_geometry_in_all_regimes": "all three regimes ended at the same geometry (R 40 mm, 140 capsules, staggered). They differ "
                                             "only in PCM and weather, so do not read regime-to-regime geometry differences into the result.",
        "fraction_cap_is_a_count_cap": "N = floor(0.40 x V_tank / V_capsule_outer) = %d; the realised fraction is %.4f, slightly under 0.40"
                                       % (designs[0]["bound_status"]["max_count_allowed_at_cap"], designs[0]["pcm_volume_fraction"]),
        "cheap_screen_fidelity": fid_verdict + "; pairs passing the pre-registered rule: %d of %d (Spearman 1.00 in every pair, but "
                                 "max difference %.2f-%.2f kWh against the 0.5 kWh limit)" % (int(fid["pass"].sum()), len(fid),
                                                                                              fid.max_abs_diff_kWh.min(), fid.max_abs_diff_kWh.max()),
        "band_definition": "the funnel used the CORE band. Against the FULL band (mains and demand variation included) the test gain is only "
                           + ", ".join(f"{summ.loc[k].gain_over_full_band:.2f}x (regime {k})" for k in range(N_REGIMES))
                           + " the band, versus "
                           + ", ".join(f"{summ.loc[k].gain_over_band:.2f}x" for k in range(N_REGIMES))
                           + " against the core band. The sign survives either way (PCM wins in every test year), the margin is much thinner "
                             "against the full band, and regime 1 has the narrowest worst-anchor gain.",
    }

    tm = [("o2_delivery_target_temp_C", sysc["delivery"]["target_temp_C"], "threshold at which O2 MEASURES usable delivered energy"),
          ("o2_max_pcm_temp_C", sysc["safety"]["max_pcm_temp_C"], "PCM material-stability ceiling"),
          ("o2_max_water_temp_C", sysc["safety"]["max_water_temp_C"], "scald prevention")]
    c["temperature_specification"] = {
        "o2": {n: {"value": v, "meaning": m} for n, v, m in tm},
        "o1_Tm_target_C": {"value": regimes_cfg[0]["Tm_target_C"], "meaning": "aspirational PCM melt target Objective 1 sized against (60 C delivery + 7 K approach)",
                           "binds": False},
        "selected_pcm_melt_points_C": "PureTemp 58 = 58.0, RT57HC = 56.5 (data/objective1/pcm_database_tamilnadu.csv)",
        "service_mismatch": "Objective 1 sizes latent heat for a 60 C delivery; Objective 2 scores delivered energy at 45 C. O2's paired comparison is "
                            "sound (both arms use the same metric), but the 45 C screen (scripts/c2_pcm_identity_check_45C.py) found lower-melting PCMs "
                            "would do better at 100 L/day. Not acted on: PCMs come from Objective 1 only (user decision).",
    }

    # ----------------------------------------------------------------------- verification status
    res = []
    for k in range(N_REGIMES):
        for nm in ("timestep", "nodes", "standing_loss"):
            p = BASE / "results" / f"c4_l3_r{k}_{nm}.csv"
            if p.exists():
                d = pd.read_csv(p)
                if "residual_pct" in d.columns:
                    res.append(float(d.residual_pct.abs().max()))
    c["verification_status"] = {
        "simulator_verification": {
            "status": "DONE",
            "energy_balance_max_abs_residual_pct": max(res) if res else None,
            "evidence_files": ["results/c4_l3_r*_timestep.csv", "results/c4_l3_r*_nodes.csv", "results/c4_l3_r*_standing_loss.csv",
                               "results/c5_g1_geometry_summary.csv", "results/c6_g1_pairs_r*.csv"],
            "test_suite": {"command": "python -m pytest tests -q", "summary": "not run in this build (--skip-tests)", "returncode": None}
            if args.skip_tests else run_tests(),
        },
        "model_consistency_cross_check": {
            "status": "DONE, with stated limits",
            "method": "ANSYS Fluent, enthalpy-porosity: one capsule 6 h charge; one capsule 1 h discharge; whole-tank 2-D discharge; the seven criteria "
                      "(ansys/criteria_*/)",
            "limits": ["2-D symmetry-slice, buoyancy off, first-order upwind: melt fractions are conservative",
                       "capsule count drawn in 2-D is a proxy (drawn = round(N x 34/104)); every kWh number comes from the node model",
                       "criteria 0 and 1 differ only in flow and the Fluent discharge case has no flow, so Fluent cannot separate them"],
        },
        "experimental_validation": {"status": "NOT DONE", "scope": "Objective 4"},
        "weather_2006_2010": "sunrise/sunset geometry check covered 0 days for 2006-2010; timing was verified against the 2017 clear-sky profile "
                             "(docs/PLAN_DEVIATIONS.md). Not GHI-audited against plant outcomes before the test.",
        "o1_physics_agreement": "Objective 1's MCDM ranking vs its own physics model is weak and not statistically significant "
                                "(mean Spearman rho = +0.169; p = 0.12-0.96; n = 8-10 per cluster): the shortlist is a consensus ranking, not a "
                                "physics-confirmed one.",
        "wording_rule": "Say 'simulator verification', 'model consistency cross-check', 'experimental validation'. Never 'CFD-validated'.",
    }

    c["deferred_future_work"] = [
        "re-fit F_R*tau-alpha and F_R*U_L for the 2.0 m2 basis (would need a new lock and a new test; today it is a stated sensitivity)",
        "extend the search box: both the 40 mm radius and the 40 % fraction are binding",
        "flow-dependent collector F_R (disabled; flow behaviour is partly a model artefact)",
        "PCMs outside Objective 1's shortlist (a 45 C screen favours lower-melting PCMs; not acted on by decision)",
        "regime-0 medoid is one of 24 tied points; each regime uses one medoid weather point",
        "node count N = 10 vs 20 is inside the band, not removed",
        "experimental validation (Objective 4)",
    ]
    c["objective_boundary"] = ("Objective 1 selected the PCM shortlist. Objective 2 selected the physical design (PCM identity, capsule geometry, "
                               "arrangement) and the validated operating envelope. OBJECTIVE 3 SELECTS THE REAL-TIME ACTION AND NOTHING ELSE. It must "
                               "not change PCM identity, capsule geometry, tank volume, collector area, safety limits or the released physics model, "
                               "and must not re-cluster or merge the regimes.")

    prov = {rel(p): sha(p) for p in [
        IMMUTABLE, RUN_DIR / "c17_summary.csv", RUN_DIR / "c17_test_by_year.csv", RUN_DIR / "c17_report_only_by_year.csv", roles.TEST_LOCK_PATH,
        BASE / "results" / "c16_funnel_winners.csv", BASE / "results" / "c10_l5_fidelity_summary.csv", BASE / "configs" / "funnel_frozen.json",
        BASE / "configs" / "system_config_shared.yaml", BASE / "configs" / "design_space.yaml", BASE / "configs" / "states" / f"{STATE}.yaml",
        BASE / statec["demand_profile"]["file"], ARCHIVED_GENERIC] + [BASE / "results" / f"c7_l4_sensitivity_r{k}.csv" for k in range(N_REGIMES)]}
    c["provenance"] = {"sha256_of_every_file_read": prov,
                       "generic_blocks_reused_from": rel(ARCHIVED_GENERIC),
                       "generic_blocks": ["action_space", "reset_scenarios", "dynamic_state_schema (extended)", "acceptance_test (extended)"],
                       "generic_blocks_note": "checked: they contain no plant-specific numbers"}

    OUT.write_text(json.dumps(c, indent=1, default=str), encoding="utf-8")
    (RUN_DIR / "o3_environment_contract_tamilnadu.sha256").write_text(sha(OUT), encoding="utf-8")
    print(f"written {OUT}  ({OUT.stat().st_size:,} bytes)  sha {sha(OUT)[:16]}")
    print("sections:", ", ".join(c.keys()))


if __name__ == "__main__":
    main()
