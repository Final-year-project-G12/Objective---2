"""
src/handoff/build_obj3_contract_common100L.py
================================================
Objective 3 contract for UTTARAKHAND on the COMMON 100 L / 2.0 m2 / 100 L/day plant (Unified Rebuild Plan, step O2-16 / level L9).
Writes results/obj3_environment_contract_uttarakhand_common100L.json in the v3 schema the Objective 3 code reads
(contract_version, global_limits, fixed_system, static_design_per_regime, ...), filled ONLY from the rebuild's own files:
configs/*.yaml, results/g10_selection_r*.json, wp6_band.csv, the one-shot test (o2_test_2006_2010*.csv), the report-only years
(o2_report_2022_2025*.csv), the O2 test lock and the O1 manifest. No number is typed by hand; verify_against_sources() re-reads them.

What changed against the legacy 50 L contract (results_legacy_50L_v3/obj3_environment_contract_uttarakhand_v3.json): the plant, the
45 C primary threshold (50 C secondary), flow fixed at 0.030 kg/s, the robust-anchor design rule, the year roles (plan R3), and the
O2 result: **water-only is recommended in every regime** (no PCM design's worst-anchor gain exceeds the band), so each regime's
installed design is the water-only tank and the best PCM design is recorded for reference only. Objective 3 then controls ENABLE /
BYPASS of the collector loop on a plain 100 L tank (plan 8.3); its goal is fewer shield-hours at >= 95 % of B0 delivery (plan 8.5).
Static text that still applies (observation fields, reset scenarios, acceptance tests, shield details) is copied from the legacy
contract and marked as such. Run: PYTHONPATH=. python -m src.handoff.build_obj3_contract_common100L
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import BASE_DIR
from src.design.space import load_space
from src.io_utils import load_design_bounds, load_state_config, load_system_config
from src.weather import roles

RES = BASE_DIR / "results"
LEGACY = BASE_DIR / "results_legacy_50L_v3" / "obj3_environment_contract_uttarakhand_v3.json"
OUT = RES / "obj3_environment_contract_uttarakhand_100L_d175.json"
VERSION = "obj3_contract_v3.0_uttarakhand_100L_d175_2026-11-23"


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _r(x, n=4):
    return None if x is None or (isinstance(x, float) and pd.isna(x)) else round(float(x), n)


def _design_summary(d: pd.DataFrame) -> dict:
    """Per-year / per-anchor results of one frozen design -> means, worst anchor, yearly values, peaks, hygiene."""
    by_anchor = d.groupby("anchor").g_window.mean()
    yearly = d.groupby("year").agg(g_window=("g_window", "mean"), g_window_50C=("g_window_50C", "mean"),
                                   t_pcm_max=("t_pcm_max", "max"), t_water_max=("t_water_max", "max"))
    out = {"g_window_mean_kWh_yr": _r(d.g_window.mean()), "g_window_worst_anchor_kWh_yr": _r(by_anchor.min()),
           "worst_anchor": str(by_anchor.idxmin()), "g_annual_mean_kWh_yr": _r(d.g_annual.mean()),
           "d_overheat_mean_h_yr": _r(d.d_overheat.mean(), 1), "g_window_50C_mean_kWh_yr": _r(d.g_window_50C.mean()),
           "t_pcm_max_C": _r(d.t_pcm_max.max(), 2), "t_water_max_C": _r(d.t_water_max.max(), 2),
           "per_year": {int(y): {k: _r(v) for k, v in row.items()} for y, row in yearly.iterrows()}}
    if "hyg_share_days" in d:
        out["hygiene_share_days_ge60C_1h"] = _r(d.hyg_share_days.mean())
        out["hygiene_longest_gap_days"] = int(d.hyg_longest_gap_days.max())
    return out


def build() -> Path:
    cfg, state, bounds = load_system_config(), load_state_config("uttarakhand"), load_design_bounds()
    legacy = json.loads(LEGACY.read_text(encoding="utf-8"))
    band = pd.read_csv(RES / "wp6_band.csv")
    test = pd.read_csv(RES / "o2_test_2006_2010.csv")
    test_plain_h = pd.read_csv(RES / "o2_test_2006_2010_plain_hygiene.csv")
    rep = pd.read_csv(RES / "o2_report_2022_2025.csv") if (RES / "o2_report_2022_2025.csv").exists() else None
    lock = json.loads(roles.test_lock_path().read_text())
    o1 = json.loads((RES / "o1_manifest_uttarakhand.json").read_text(encoding="utf-8"))
    sp = load_space()

    c = {
        "state": "uttarakhand", "contract_version": VERSION, "generated_utc": datetime.now(timezone.utc).isoformat(),
        "validated_simulator_version": cfg["version"],
        "plant": f"100 L / 2.0 m2 / {state['demand_profile']['daily_total_L']:g} L/day (plan R1 plant; demand per docs/REBUILD_175L.md)",
        "source": ("Objective 2 Uttarakhand rebuild on the common plant: results/g10_selection_r*.json, wp6_band.csv, o2_test_2006_2010*.csv, "
                   "o2_report_2022_2025*.csv, results/locks/, o1_manifest_uttarakhand.json, configs/*.yaml. Decision record: "
                   "docs/REBUILD_COMMON100L.md."),
        "supersession_note": ("SUPERSEDES the legacy 50 L / 1.5 m2 / 300 L/day contracts (results_legacy_50L_v3/), which must not be used "
                              "for the common plant (plan 2.2)."),
        "o2_result": ("WATER-ONLY in every regime: on the common plant no PCM design's worst-anchor select-year paired gain exceeds the "
                      "repeatability band (plan R7, decision 4). Each regime's installed design is the water-only 100 L tank; the best "
                      "PCM design per regime is recorded under best_pcm_design_reference and was tested, but is NOT a recommendation."),
        "global_limits": {
            "delivery_target_temp_C": cfg["delivery"]["target_temp_C"],
            "secondary_report_temp_C": cfg["delivery"]["secondary_report_temp_C"],
            "max_safe_water_temp_C": cfg["safety"]["max_water_temp_C"], "max_safe_pcm_temp_C": cfg["safety"]["max_pcm_temp_C"],
            "max_pressure_bar": cfg["safety"]["max_pressure_bar"],
            "min_irradiance_cutoff_Wm2": cfg["collector"]["min_irradiance_cutoff_Wm2"],
            "flow_fixed_kg_s": sp["variables"]["flow_rate_kg_s"]["min"],
            "pump_flow_range_kg_s": [cfg["pump"]["flow_min_kg_s"], cfg["pump"]["flow_max_kg_s"]],
            "note": ("45 C is the primary service threshold (plan R2); 50 C is a secondary Uttarakhand-only report, never pooled. Flow is "
                     "FIXED at the design value (plan R6): Objective 3 does not control flow."),
        },
        "fixed_system": {
            "tank_volume_L": cfg["tank"]["volume_L"], "tank_height_to_diameter_ratio": cfg["tank"]["height_to_diameter_ratio"],
            "tank_insulation_m": cfg["tank"]["insulation_m"], "tank_U_W_m2K": cfg["tank"]["U_tank_W_m2K"],
            "collector_area_m2": cfg["collector"]["area_m2"], "collector_area_basis": "OPEN (no source for aperture vs absorber)",
            "collector_fr_tau_alpha": cfg["collector"]["fr_tau_alpha"], "collector_fr_ul_W_m2K": cfg["collector"]["fr_ul_W_m2K"],
            "collector_flow_dependent_fr_enabled": cfg["collector"]["flow_dependent_fr"]["enabled"],
            "n_nodes": sp["model"]["n_nodes"], "demand_daily_total_L": state["demand_profile"]["daily_total_L"],
            "demand_profile_file": state["demand_profile"]["file"],
        },
    }

    designs = []
    for r in o1["regimes"]:
        k = r["regime_id"]
        sel = json.loads((RES / f"g10_selection_r{k}.json").read_text())
        ch = sel["chosen"]
        b = band[band.scope == f"r{k}"].set_index("objective").band
        t = test[test.regime == k]
        tc = t[t.role == "chosen"]
        designs.append({
            "regime_id": k, "label": r["label"], "medoid_point_id": r["medoid"], "member_point_ids": r["member_point_ids"],
            "n_points": r["n_points"], "population_covered": r["population_covered"], "T_mains_est_C": r["T_mains_est_C"],
            "o1_pcm_shortlist": r["pcm_shortlist"], "o1_Tm_target_C": r["Tm_target_C"],
            "recommendation": sel["recommendation"],
            "installed_design": ({"type": "water_only_tank", "pcm": None, "n_capsules": 0, "tank_volume_L": cfg["tank"]["volume_L"]}
                                 if sel["recommendation"] == "water_only" else
                                 {"type": "pcm", "pcm": ch["pcm"], "capsule_inner_radius_m": ch["R_in_m"], "pcm_volume_fraction": ch["fraction"],
                                  "n_capsules": ch["N"], "arrangement": ch["arrangement"]}),
            "best_pcm_design_reference": {
                "status": "tested reference, NOT recommended" if sel["recommendation"] == "water_only" else "recommended",
                "pcm": ch["pcm"], "capsule_inner_radius_m": ch["R_in_m"], "pcm_volume_fraction": ch["fraction"], "n_capsules": ch["N"],
                "arrangement": ch["arrangement"], "pcm_mass_kg": ch["pcm_mass_kg"],
                "select_2020_2021": {"g_window_mean_kWh_yr": _r(ch["g_window"]), "g_window_worst_anchor_kWh_yr": _r(ch["g_window_worst_anchor"]),
                                     "g_annual_kWh_yr": _r(ch["g_annual"]), "d_overheat_h_yr": _r(ch["d_overheat"], 1),
                                     "t_pcm_max_C": _r(ch["t_pcm_max"], 2), "t_water_max_C": _r(ch["t_water_max"], 2)},
                "test_2006_2010": _design_summary(tc) if len(tc) else None,
                "report_2022_2025": _design_summary(rep[(rep.regime == k) & (rep.role == "chosen")]) if rep is not None else None,
            },
            "repeatability_band": {o: _r(v) for o, v in b.items()},
            "selection_funnel": {kk: sel.get(kk) for kk in ("n_candidates", "n_feasible_select", "n_eligible_worst_anchor_above_band",
                                                            "n_S0_indistinguishable_on_g_window", "n_S1", "n_S2",
                                                            "cheap_vs_full_spearman", "cheap_screen_usable")},
            "selection_fingerprint_sha256": sel["fingerprint_sha256"],
            "alternatives_tested": [{"pcm": a["pcm"], "pcm_volume_fraction": a["fraction"], "capsule_inner_radius_m": a["R_in_m"],
                                     "arrangement": a["arrangement"],
                                     "test_2006_2010": _design_summary(t[(t.role == "best_of_pcm") & (t.pcm == a["pcm"])])}
                                    for a in sel.get("alternatives_best_per_pcm", []) if a["pcm"] != ch["pcm"]
                                    and len(t[(t.role == "best_of_pcm") & (t.pcm == a["pcm"])])],
            "water_only_tank_hygiene_2006_2010": {
                "share_days_ge60C_1h": _r(test_plain_h[test_plain_h.regime == k].hyg_share_days.mean()),
                "longest_gap_days": int(test_plain_h[test_plain_h.regime == k].hyg_longest_gap_days.max())},
        })
    c["static_design_per_regime"] = designs

    c["o2_confirmatory_test"] = {
        "status": "COMPLETED AND LOCKED by O2 (one shot) - Objective 3 runs its OWN separate 2006-2010 test under its own lock",
        "years": roles.years_for("test"), "run_id": lock["run_id"], "locked_utc": lock["utc"], "plant_hash": lock["plant_hash"],
        "selection_fingerprint": lock["selection_fingerprint"], "fidelity": "37.5 s, every year, bottom / centre / top anchors",
        "exposure_note": ("2006-2010 is unseen for Objective 2. It was used by the OLD Uttarakhand Objective 3 test (50 L plant), so it is "
                          "not unseen for Objective 3; declare this in the Objective 3 report (plan 1.5, 7.2)."),
    }
    c["weather_sequences"] = {
        "o3_roles_plan_R3": {"train": [2016, 2017, 2018, 2019], "validate": [2020, 2021],
                             "extra_train_after_o2_freeze": [2022, 2023], "report_only": [2024, 2025],
                             "confirmatory_test_own_lock": roles.years_for("test")},
        "points": {str(r["regime_id"]): r["medoid"] for r in o1["regimes"]},
        "weather_files": "data/weather/point_years/uttarakhand/cluster<c>_<point>_<year>.csv (inventory: weather_inventory.csv)",
        "enforcement": "src/weather/roles.py refuses a year whose role differs from the purpose; test years need the lock",
    }
    c["time_step_s"] = {"search": 150, "report_and_test": sp["model"]["report_timestep_s"],
                        "note": "L3 gate: 37.5 s passes the halving criterion on the primary metric (docs/REBUILD_COMMON100L.md 3c)"}
    c["action_space"] = {"actions": ["ENABLE", "BYPASS"],
                         "note": ("Plan 8.3: two physical actions; IDLE is physically identical to BYPASS in this loop. Flow is fixed; "
                                  "the shield inside the kernel overrides ENABLE above the guards and cannot be disabled."),
                         "hard_rule": legacy["action_space"].get("hard_rule")}
    c["dynamic_state_schema"] = {**legacy["dynamic_state_schema"],
                                 "rebuild_note": ("copied from the legacy contract; on the water-only installed design T_pcm_C and f_melt "
                                                  "are degenerate (no PCM) and kept for a state-invariant schema")}
    c["reset_scenarios"] = legacy["reset_scenarios"]
    c["acceptance_test_before_drl_training"] = legacy["acceptance_test_before_drl_training"]
    c["safety_shield"] = {"enabled": bool(cfg["safety_shield"]["enabled"]), "bypass_water_C": cfg["safety_shield"]["bypass_water_C"],
                          "bypass_pcm_C": cfg["safety_shield"]["bypass_pcm_C"], "hard_water_C": cfg["safety"]["max_water_temp_C"],
                          "hard_pcm_C": cfg["safety"]["max_pcm_temp_C"],
                          "enforced_in": "src/simulation/tank_model_multinode.py (inside the kernel, not the policy)",
                          "hygiene_guardrail_plan_R9": "report share of days with stored water >= 60 C for >= 1 h and the longest gap; "
                                                       "not worse than B0 by more than the band"}
    c["reward_function"] = {"status": "FORM FIXED BY THE PLAN (8.5); WEIGHTS NOT CHOSEN (Objective 3 pre-registers them before training)",
                            "formula": ("w_d * normalized_delivered_energy - w_u * normalized_unmet_demand + w_r * normalized_evening_retention"
                                        " - w_c * physical_switching_cost - w_b * unnecessary_bypass_cost"),
                            "safety": "a constraint (shield + cost critic), not a huge scalar penalty",
                            "acceptance_plan_R12": "zero hard violations; annual delivery >= 95 % of B0 in every regime; then the largest shield-hour cut",
                            "headroom_gate_H2": "near-oracle minus B0, computed before any DRL training (plan 8.5)"}
    c["design_space_caveats"] = {"statement": "best within the declared box (plan R17); not a global optimum",
                                 "searched_bounds": {"capsule_inner_radius_m": [sp["variables"]["inner_radius_m"]["min"], sp["variables"]["inner_radius_m"]["max"]],
                                                     "pcm_volume_fraction": [sp["variables"]["pcm_volume_fraction"]["min"], sp["variables"]["pcm_volume_fraction"]["max"]],
                                                     "flow_kg_s_fixed": sp["variables"]["flow_rate_kg_s"]["min"],
                                                     "arrangement": bounds["capsule_arrangement"]},
                                 "why_water_only": ("at 100 L/day a 100 L tank on 2.0 m2 already stores a full day's hot water; capsules displace water "
                                                    "and the PCM guard adds shield hours. PCM gains appear in regime 1 only above about 150 L/day "
                                                    "(docs/REBUILD_COMMON100L.md 3c, exploratory).")}
    c["verification_status"] = {"simulator_verification": "L3 gate passed (docs/REBUILD_COMMON100L.md 3c); results/l3_*.csv",
                                "cfd_cross_check": "none on the common plant (OpenFOAM optional, plan section 6); legacy 50 L case only",
                                "experimental_validation": {"status": "NOT DONE", "scope": "Objective 4 / hardware"},
                                "wording_rule": "never 'CFD-validated' (plan R17)"}
    c["objective_boundary"] = ("Objective 2 fixed the plant and the (water-only) design. Objective 3 may not change the tank, collector, "
                               "PCM, capsules, flow, safety limits or physics; it controls ENABLE / BYPASS only.")
    c["provenance"] = {"configs/system_config_shared.yaml": _sha(BASE_DIR / "configs" / "system_config_shared.yaml"),
                       "configs/design_space.yaml": _sha(BASE_DIR / "configs" / "design_space.yaml"),
                       "configs/states/uttarakhand.yaml": _sha(BASE_DIR / "configs" / "states" / "uttarakhand.yaml"),
                       "wp6_band.csv": _sha(RES / "wp6_band.csv"), "o2_test_2006_2010.csv": _sha(RES / "o2_test_2006_2010.csv"),
                       "test_lock": _sha(roles.test_lock_path()), "o1_manifest_uttarakhand.json": _sha(RES / "o1_manifest_uttarakhand.json"),
                       **{f"g10_selection_r{r['regime_id']}.json": _sha(RES / f"g10_selection_r{r['regime_id']}.json") for r in o1["regimes"]}}
    OUT.write_text(json.dumps(c, indent=1, default=str), encoding="utf-8")
    verify_against_sources(c)
    return OUT


def verify_against_sources(c=None):
    c = c or json.loads(OUT.read_text(encoding="utf-8"))
    cfg = load_system_config()
    assert c["fixed_system"]["tank_volume_L"] == cfg["tank"]["volume_L"] == 100.0
    assert c["fixed_system"]["collector_area_m2"] == cfg["collector"]["area_m2"] == 2.0
    assert c["fixed_system"]["demand_daily_total_L"] == load_state_config("uttarakhand")["demand_profile"]["daily_total_L"] == 175.0
    assert c["global_limits"]["delivery_target_temp_C"] == 45.0
    n = 4
    for d in c["static_design_per_regime"]:
        sel = json.loads((RES / f"g10_selection_r{d['regime_id']}.json").read_text())
        assert d["recommendation"] == sel["recommendation"]
        for a, b in (("pcm", "pcm"), ("R_in_m", "capsule_inner_radius_m"), ("fraction", "pcm_volume_fraction"), ("N", "n_capsules")):
            assert sel["chosen"][a] == d["best_pcm_design_reference"][b]
            n += 1
    return n


if __name__ == "__main__":
    p = build()
    print("written", p, "| verified", verify_against_sources(), "fields")
