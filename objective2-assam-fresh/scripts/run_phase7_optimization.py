"""
scripts/run_phase7_optimization.py
===================================
Phase 7 / Deliverable D2.6 — Multi-Objective Optimization & Simulator Re-Simulation for Assam.

Executes:
  1. Dense search over design variables (d, N, flow) across all 3 Assam regimes and 3 PCM candidates.
  2. First-stage screening with Phase 6 Feasibility Classifier (feasibility_classifier.pkl).
  3. Second-stage screening with Phase 2 physical constraint engine (check_design).
  4. Scoring with Phase 6 ExtraTrees performance surrogates.
  5. Multi-objective ranking using the 5% Near-Best Rule.
  6. Selection of top 15-20 candidates (phase7_top_candidates.csv).
  7. Final selection of 4-5 key candidates for full 8760-hour annual re-simulation with sim_v1_assam.
  8. Calculation of absolute and percentage prediction errors (surrogate vs actual).
  9. Generation of 5 Pareto and diagnostic plots in results/plots/.
 10. Comprehensive report in results/phase7_optimization_report.md.
"""

import sys
import json
import pickle
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.design.schema import DesignVector
from src.design.constraints import check_design
from src.simulation.run_case import run_case
from src.io_utils import load_design_bounds, load_system_config, load_state_config
from src.surrogate.features import build_feature_table, feature_target_split

SEARCH_SEED = 20260910
N_CANDIDATES_PER_PAIR = 1000
SAFE_TARGET = 5          # stop a pair once this many simulator-safe designs are found
MAX_SIM_PER_PAIR = 40    # simulation budget per regime x PCM pair (~5 s each)

RESULTS_DIR = BASE_DIR / "results"
MODELS_DIR = BASE_DIR / "models"
PLOTS_DIR = RESULTS_DIR / "plots"

PLOTS_DIR.mkdir(exist_ok=True, parents=True)


def load_surrogate_models():
    models = {}
    with open(MODELS_DIR / "feasibility_classifier.pkl", "rb") as f:
        models["feasibility"] = pickle.load(f)
    with open(MODELS_DIR / "useful_energy_regressor.pkl", "rb") as f:
        models["useful_energy_kWh"] = pickle.load(f)
    with open(MODELS_DIR / "solar_fraction_regressor.pkl", "rb") as f:
        models["solar_fraction"] = pickle.load(f)
    with open(MODELS_DIR / "unmet_energy_regressor.pkl", "rb") as f:
        models["unmet_energy_kWh"] = pickle.load(f)
    with open(MODELS_DIR / "pump_energy_regressor.pkl", "rb") as f:
        models["pump_energy_kWh"] = pickle.load(f)
    
    # Also load secondary models from results/phase6_surrogate_models.pkl if available
    saved_path = RESULTS_DIR / "phase6_surrogate_models.pkl"
    if saved_path.exists():
        with open(saved_path, "rb") as f:
            pkg = pickle.load(f)
            if "pcm_mass_kg" in pkg["models"]:
                models["pcm_mass_kg"] = pkg["models"]["pcm_mass_kg"]

    with open(MODELS_DIR / "feature_cols.json", "r") as f:
        feature_cols = json.load(f)

    return models, feature_cols


def generate_candidate_grid(bounds, n_candidates, seed):
    rng = np.random.default_rng(seed)
    # Sample uniformly within bounds
    d = rng.uniform(bounds["capsule_diameter_m"]["min"], bounds["capsule_diameter_m"]["max"], n_candidates)
    f = rng.uniform(bounds["flow_rate_kg_s"]["min"], bounds["flow_rate_kg_s"]["max"], n_candidates)
    c = rng.integers(bounds["capsule_count"]["min"], bounds["capsule_count"]["max"] + 1, n_candidates)
    return d, c, f


def run_search(state="assam"):
    print("==================================================")
    print("PHASE 7: MULTI-OBJECTIVE OPTIMIZATION FOR ASSAM")
    print("==================================================")

    models, feature_cols = load_surrogate_models()
    system_config = load_system_config()
    bounds = load_design_bounds()
    state_cfg = load_state_config(state)

    print(f"Loaded Phase 6 surrogate models ({len(models)} models, {len(feature_cols)} features).")

    pcm_list = ["savE® OM48", "savE® OM50", "savE® OM46"]
    regimes = state_cfg["regimes"]

    all_screened = []

    total_candidates_generated = 0
    total_physically_valid = 0

    print(f"\nSearching design space ({N_CANDIDATES_PER_PAIR} candidates per pair) ...")

    pair_idx = 0
    for reg in regimes:
        cid = reg["cluster_id"]
        cname = reg.get("label", f"Regime {cid}")

        # Search each PCM + plain tank baseline
        search_pcms = pcm_list + [None]
        for pcm_id in search_pcms:
            pair_seed = SEARCH_SEED + pair_idx * 137
            pair_idx += 1

            diam, count, flow = generate_candidate_grid(bounds, N_CANDIDATES_PER_PAIR, pair_seed)
            total_candidates_generated += N_CANDIDATES_PER_PAIR

            rows = []
            for i in range(N_CANDIDATES_PER_PAIR):
                dv = DesignVector(float(diam[i]), int(count[i]), float(flow[i]))
                
                # Physical constraint check (deterministic)
                geom = check_design(dv, system_config, bounds)
                if not geom["valid"]:
                    continue

                total_physically_valid += 1
                rows.append({
                    "regime_id": cid,
                    "regime_name": cname,
                    "pcm_id": pcm_id if pcm_id is not None else "NONE_plain_tank",
                    "capsule_diameter_m": dv.capsule_diameter_m,
                    "n_capsule": dv.n_capsule,
                    "flow_rate_kg_s": dv.flow_rate_kg_s,
                    "valid": True,
                    "geom_pcm_thickness_m": geom["pcm_thickness_m"],
                    "geom_pcm_volume_fraction": geom["pcm_volume_fraction"],
                    "geom_void_fraction": geom["void_fraction"],
                    "geom_pressure_drop_pa": geom["pressure_drop_pa"],
                    "geom_pump_power_w": geom["pump_power_w"],
                    "geom_reynolds_number_particle": geom["reynolds_number_particle"],
                })

            if not rows:
                continue

            pair_df = pd.DataFrame(rows)
            feat_df = build_feature_table(state, pair_df)
            X, _, _, _ = feature_target_split(feat_df, only_valid=False)
            X = X[feature_cols].fillna(-999.0)

            # Feasibility classifier screening
            clf = models["feasibility"]
            feas_probs = clf.predict_proba(X)
            class_1_idx = list(clf.classes_).index(1) if 1 in clf.classes_ else 0
            pair_df["feasibility_proba"] = feas_probs[:, class_1_idx]

            # Reject any predicted infeasible (proba < 0.5)
            pair_df = pair_df[pair_df["feasibility_proba"] >= 0.50].copy()
            if pair_df.empty:
                continue

            # Surrogate performance predictions
            pair_feat = build_feature_table(state, pair_df)
            X_valid, _, _, _ = feature_target_split(pair_feat, only_valid=False)
            X_valid = X_valid[feature_cols]

            pair_df["pred_useful_energy_kWh"] = models["useful_energy_kWh"].predict(X_valid)
            pair_df["pred_solar_fraction"] = models["solar_fraction"].predict(X_valid)
            pair_df["pred_unmet_energy_kWh"] = models["unmet_energy_kWh"].predict(X_valid)
            pair_df["pred_pump_energy_kWh"] = models["pump_energy_kWh"].predict(X_valid)
            if "pcm_mass_kg" in models:
                pair_df["pred_pcm_mass_kg"] = models["pcm_mass_kg"].predict(X_valid)
            else:
                pair_df["pred_pcm_mass_kg"] = 0.0

            all_screened.append(pair_df)

    candidates_df = pd.concat(all_screened, ignore_index=True)
    candidates_path = RESULTS_DIR / "phase7_optimization_candidates.csv"
    candidates_df.to_csv(candidates_path, index=False)
    print(f"\nGenerated {total_candidates_generated} total candidate vectors.")
    print(f"Physically feasible & classifier-accepted: {len(candidates_df)} candidates.")
    print(f"Saved screened candidates to {candidates_path.name}")

    # ==================================================
    # SIMULATOR-VERIFIED SAFETY FILTER (frozen 65 C PCM / 75 C water limits)
    # ==================================================
    # The Phase 6 surrogates do not predict temperature safety (71% of the DOE
    # breaches 65 C), so safety is enforced in the real simulator: candidates are
    # simulated in descending predicted-useful-energy order per regime x PCM pair
    # until SAFE_TARGET safe designs are found or MAX_SIM_PER_PAIR is reached.
    max_allowed_w = system_config["safety"]["max_water_temp_C"]
    max_allowed_pcm = system_config["safety"]["max_pcm_temp_C"]
    print(f"\nSafety-verified search: limits PCM <= {max_allowed_pcm} C, water <= {max_allowed_w} C, 0 violations")

    metric_map = [("useful_energy_kWh", "sim_useful_energy_kWh"), ("solar_fraction", "sim_solar_fraction"),
                  ("unmet_energy_kWh", "sim_unmet_energy_kWh"), ("pump_energy_kWh", "sim_pump_energy_kWh"),
                  ("pcm_mass_kg", "sim_pcm_mass_kg"), ("residual_pct_of_collector", "sim_residual_pct_of_collector"),
                  ("max_water_temp_C", "sim_max_water_temp_C"), ("max_pcm_temp_C", "sim_max_pcm_temp_C"),
                  ("n_safety_violations", "sim_n_safety_violations"), ("complete_melt_cycles", "sim_complete_melt_cycles"),
                  ("mean_f_melt", "sim_mean_f_melt"), ("delivery_temp_hours", "sim_delivery_temp_hours")]
    err_map = [("useful_energy", "pred_useful_energy_kWh", "sim_useful_energy_kWh", "_kWh"),
               ("solar_fraction", "pred_solar_fraction", "sim_solar_fraction", ""),
               ("unmet_energy", "pred_unmet_energy_kWh", "sim_unmet_energy_kWh", "_kWh"),
               ("pump_energy", "pred_pump_energy_kWh", "sim_pump_energy_kWh", "_kWh")]

    verified = []
    for reg in regimes:
        cid = reg["cluster_id"]
        for pcm_id in pcm_list + ["NONE_plain_tank"]:
            pool = candidates_df[(candidates_df["regime_id"] == cid) & (candidates_df["pcm_id"] == pcm_id)]
            pool = pool.sort_values("pred_useful_energy_kWh", ascending=False)
            pcm_name = None if pcm_id == "NONE_plain_tank" else pcm_id
            n_safe, n_sim = 0, 0
            for _, r in pool.iterrows():
                if n_safe >= SAFE_TARGET or n_sim >= MAX_SIM_PER_PAIR:
                    break
                dv = DesignVector(float(r["capsule_diameter_m"]), int(r["n_capsule"]), float(r["flow_rate_kg_s"]))
                sim_out = run_case(state, int(cid), pcm_name, dv, record_hourly=True)
                n_sim += 1
                if not sim_out["valid"]:
                    continue
                m = sim_out["metrics"]
                row = dict(r)
                row["sim_valid"] = True
                for k_src, k_dst in metric_map:
                    row[k_dst] = m[k_src]
                for name, pk, sk, suf in err_map:
                    row[f"err_{name}_abs{suf}"] = abs(row[pk] - row[sk])
                    row[f"err_{name}_pct"] = abs(row[pk] - row[sk]) / row[sk] * 100.0 if row[sk] else 0.0
                row["water_temp_safety_margin_C"] = max_allowed_w - m["max_water_temp_C"]
                row["pcm_temp_safety_margin_C"] = (max_allowed_pcm - m["max_pcm_temp_C"]) if pcm_name else 999.0
                row["meets_temperature_safety"] = bool(
                    m["max_water_temp_C"] <= max_allowed_w
                    and (pcm_name is None or m["max_pcm_temp_C"] <= max_allowed_pcm)
                    and m["n_safety_violations"] == 0)
                n_safe += int(row["meets_temperature_safety"])
                verified.append(row)
            print(f"  Regime {cid} {pcm_id}: simulated {n_sim}, safe {n_safe}")

    verified_df = pd.DataFrame(verified)
    verified_df.to_csv(RESULTS_DIR / "phase7_safety_verified_candidates.csv", index=False)
    safe_df = verified_df[verified_df["meets_temperature_safety"]].copy()
    print(f"Verified {len(verified_df)} candidates in the simulator; {len(safe_df)} meet the safety limits.")

    # ==================================================
    # 5% NEAR-BEST RULE ON THE SAFE, SIMULATOR-CONFIRMED POOL
    # ==================================================
    print("\nApplying 5% Near-Best Rule to the safe pool (simulated useful energy) ...")
    top_candidates_list = []
    final_selection = []
    unsafe_regimes = []
    for reg in regimes:
        cid = reg["cluster_id"]
        reg_pool = safe_df[(safe_df["regime_id"] == cid) & (safe_df["pcm_id"] != "NONE_plain_tank")]
        if reg_pool.empty:
            unsafe_regimes.append(cid)
            print(f"  [WARNING] Regime {cid}: NO PCM design meets the safety limits in the search -- no deployable PCM design.")
            continue
        best_useful = reg_pool["sim_useful_energy_kWh"].max()
        near_best = reg_pool[reg_pool["sim_useful_energy_kWh"] >= 0.95 * best_useful].copy()
        near_best["best_regime_useful_energy_kWh"] = best_useful
        near_best["useful_energy_fraction_of_best"] = near_best["sim_useful_energy_kWh"] / best_useful
        near_best = near_best.sort_values(
            by=["sim_unmet_energy_kWh", "sim_solar_fraction", "sim_pump_energy_kWh", "sim_pcm_mass_kg", "n_capsule", "pcm_temp_safety_margin_C"],
            ascending=[True, False, True, True, True, False])
        top_candidates_list.append(near_best)
        winner = near_best.iloc[0].to_dict()
        winner["selection_role"] = f"Optimal Regime {cid} Candidate (safety-verified)"
        final_selection.append(winner)

    top_df = pd.concat(top_candidates_list, ignore_index=True) if top_candidates_list else pd.DataFrame()
    top_df.to_csv(RESULTS_DIR / "phase7_top_candidates.csv", index=False)

    om48 = safe_df[(safe_df["regime_id"] == 0) & (safe_df["pcm_id"] == "savE® OM48")]
    if not om48.empty:
        u_row = om48.sort_values("sim_useful_energy_kWh", ascending=False).iloc[0].to_dict()
        u_row["selection_role"] = "Universal Cross-Regime Candidate (R0 OM48, safety-verified)"
        final_selection.append(u_row)
    plain = safe_df[(safe_df["regime_id"] == 0) & (safe_df["pcm_id"] == "NONE_plain_tank")]
    if not plain.empty:
        p_row = plain.sort_values("sim_useful_energy_kWh", ascending=False).iloc[0].to_dict()
        p_row["selection_role"] = "Regime 0 Plain Tank Baseline"
        final_selection.append(p_row)

    resim_df = pd.DataFrame(final_selection)
    resim_df.to_csv(RESULTS_DIR / "phase7_resimulation_results.csv", index=False)
    deployable_rows = resim_df[resim_df["selection_role"].str.startswith("Optimal Regime")].copy()
    deployable_rows.to_csv(RESULTS_DIR / "phase7_deployable_design_per_regime.csv", index=False)
    resim_df.to_csv(RESULTS_DIR / "phase7_optimized_designs.csv", index=False)
    print(f"Deployable PCM designs: {len(deployable_rows)} of {len(regimes)} regimes (no safe PCM design: {unsafe_regimes})")
    for _, r in deployable_rows.iterrows():
        print(f"  Regime {int(r['regime_id'])}: {r['pcm_id']} d={r['capsule_diameter_m']*1000:.1f}mm N={int(r['n_capsule'])} "
              f"flow={r['flow_rate_kg_s']:.3f} E={r['sim_useful_energy_kWh']:.1f}kWh maxPCM={r['sim_max_pcm_temp_C']:.1f}C")

    # ==================================================
    # GENERATE 5 HIGH-RESOLUTION PLOTS
    # ==================================================
    print("\nGenerating Phase 7 optimization visual artifacts in results/plots/ ...")

    # Plot 1: Pareto Front (Useful Energy vs Solar Fraction)
    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(
        candidates_df["pred_solar_fraction"],
        candidates_df["pred_useful_energy_kWh"],
        c=candidates_df["flow_rate_kg_s"],
        cmap="viridis", alpha=0.4, s=20, label="Sampled Feasible Pool"
    )
    plt.colorbar(scatter, label="Flow Rate (kg/s)")
    ax.scatter(
        top_df["pred_solar_fraction"],
        top_df["pred_useful_energy_kWh"],
        color="orange", edgecolors="k", s=60, label="Top 5% Near-Best Candidates", zorder=5
    )
    ax.scatter(
        resim_df["sim_solar_fraction"],
        resim_df["sim_useful_energy_kWh"],
        color="red", marker="*", s=180, edgecolors="k", label="Simulator Verified Optima", zorder=10
    )
    ax.set_xlabel("Solar Fraction")
    ax.set_ylabel("Useful Delivered Energy (kWh/year)")
    ax.set_title("Phase 7: Useful Delivered Energy vs Solar Fraction (Pareto Exploration)")
    ax.legend(loc="lower right")
    ax.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plot1_path = PLOTS_DIR / "phase7_pareto_front.png"
    fig.savefig(plot1_path, dpi=200)
    plt.close(fig)
    print(f"  Saved: {plot1_path.name}")

    # Plot 2: Useful Energy vs Unmet Energy
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(
        candidates_df["pred_unmet_energy_kWh"],
        candidates_df["pred_useful_energy_kWh"],
        color="steelblue", alpha=0.3, s=20, label="All Screened Designs"
    )
    ax.scatter(
        top_df["pred_unmet_energy_kWh"],
        top_df["pred_useful_energy_kWh"],
        color="gold", edgecolors="k", s=60, label="Top Near-Best Candidates", zorder=5
    )
    ax.scatter(
        resim_df["sim_unmet_energy_kWh"],
        resim_df["sim_useful_energy_kWh"],
        color="crimson", marker="*", s=180, edgecolors="k", label="Simulator Confirmed Optima", zorder=10
    )
    ax.set_xlabel("Unmet Auxiliary Energy Required (kWh/year) [Lower is Better]")
    ax.set_ylabel("Useful Solar Energy Delivered (kWh/year) [Higher is Better]")
    ax.set_title("Phase 7: Trade-off Between Useful Energy Delivery & Unmet Demand")
    ax.legend(loc="upper right")
    ax.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plot2_path = PLOTS_DIR / "phase7_useful_vs_unmet.png"
    fig.savefig(plot2_path, dpi=200)
    plt.close(fig)
    print(f"  Saved: {plot2_path.name}")

    # Plot 3: Useful Energy vs PCM Mass
    fig, ax = plt.subplots(figsize=(8, 6))
    pcm_cands = candidates_df[candidates_df["pcm_id"] != "NONE_plain_tank"]
    scatter = ax.scatter(
        pcm_cands["pred_pcm_mass_kg"],
        pcm_cands["pred_useful_energy_kWh"],
        c=pcm_cands["regime_id"], cmap="coolwarm", alpha=0.5, s=25, label="PCM Candidates"
    )
    cb = plt.colorbar(scatter, ticks=[0, 1, 2])
    cb.ax.set_yticklabels(["C0 (Valley)", "C1 (Tea Belt)", "C2 (Hills)"])
    cb.set_label("Climate Regime")
    ax.scatter(
        resim_df[resim_df["pcm_id"] != "NONE_plain_tank"]["sim_pcm_mass_kg"],
        resim_df[resim_df["pcm_id"] != "NONE_plain_tank"]["sim_useful_energy_kWh"],
        color="black", marker="D", s=80, edgecolors="white", label="Selected Optimal Designs", zorder=10
    )
    ax.set_xlabel("PCM Mass (kg)")
    ax.set_ylabel("Useful Delivered Energy (kWh/year)")
    ax.set_title("Phase 7: Impact of PCM Mass on Annual Delivered Energy")
    ax.legend(loc="lower right")
    ax.grid(True, linestyle=":", alpha=0.6)
    plt.tight_layout()
    plot3_path = PLOTS_DIR / "phase7_useful_vs_pcm_mass.png"
    fig.savefig(plot3_path, dpi=200)
    plt.close(fig)
    print(f"  Saved: {plot3_path.name}")

    # Plot 4: Design Variable Distributions (Top Candidates)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    axes[0].hist(top_df["capsule_diameter_m"] * 1000.0, bins=8, color="mediumseagreen", edgecolor="black", alpha=0.7)
    axes[0].set_xlabel("Capsule Diameter (mm)")
    axes[0].set_ylabel("Frequency")
    axes[0].set_title("Optimal Diameter Distribution")
    axes[0].grid(True, linestyle=":", alpha=0.6)

    axes[1].hist(top_df["n_capsule"], bins=np.arange(7.5, 25.5, 1), color="coral", edgecolor="black", alpha=0.7)
    axes[1].set_xlabel("Number of Capsules (N)")
    axes[1].set_ylabel("Frequency")
    axes[1].set_title("Optimal Capsule Count Distribution")
    axes[1].grid(True, linestyle=":", alpha=0.6)

    axes[2].hist(top_df["flow_rate_kg_s"], bins=8, color="mediumpurple", edgecolor="black", alpha=0.7)
    axes[2].set_xlabel("HTF Flow Rate (kg/s)")
    axes[2].set_ylabel("Frequency")
    axes[2].set_title("Optimal Flow Rate Distribution")
    axes[2].grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    plot4_path = PLOTS_DIR / "phase7_design_variable_distribution.png"
    fig.savefig(plot4_path, dpi=200)
    plt.close(fig)
    print(f"  Saved: {plot4_path.name}")

    # Plot 5: Surrogate vs Simulator Predictions for Re-Simulated Candidates
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    bar_width = 0.35
    x = np.arange(len(resim_df))
    labels = [f"R{int(r['regime_id'])}: {r['pcm_id'].split()[-1]}" for _, r in resim_df.iterrows()]

    axes[0].bar(x - bar_width/2, resim_df["pred_useful_energy_kWh"], bar_width, label="Surrogate Predicted", color="cornflowerblue", edgecolor="k")
    axes[0].bar(x + bar_width/2, resim_df["sim_useful_energy_kWh"], bar_width, label="Actual Simulator", color="salmon", edgecolor="k")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels, rotation=15)
    axes[0].set_ylabel("Useful Delivered Energy (kWh/year)")
    axes[0].set_title("Useful Energy: Surrogate vs Actual Simulator")
    axes[0].legend()
    axes[0].grid(True, linestyle=":", alpha=0.6)

    axes[1].bar(x - bar_width/2, resim_df["pred_solar_fraction"] * 100, bar_width, label="Surrogate Predicted", color="cornflowerblue", edgecolor="k")
    axes[1].bar(x + bar_width/2, resim_df["sim_solar_fraction"] * 100, bar_width, label="Actual Simulator", color="salmon", edgecolor="k")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, rotation=15)
    axes[1].set_ylabel("Solar Fraction (%)")
    axes[1].set_title("Solar Fraction: Surrogate vs Actual Simulator")
    axes[1].legend()
    axes[1].grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    plot5_path = PLOTS_DIR / "phase7_surrogate_vs_simulator.png"
    fig.savefig(plot5_path, dpi=200)
    plt.close(fig)
    print(f"  Saved: {plot5_path.name}")

    # ==================================================
    # REPORT (every pass/fail is computed from the data and the frozen config)
    # ==================================================
    report_path = RESULTS_DIR / "phase7_optimization_report.md"
    print(f"\nWriting report to {report_path.name} ...")

    def _status(ok):
        return "PASS" if ok else "**FAIL**"

    dep = deployable_rows.reset_index(drop=True)
    max_err_pct = float(resim_df["err_useful_energy_pct"].max()) if len(resim_df) else float("nan")
    all_regimes_covered = len(dep) == len(regimes)
    all_safe = bool(len(dep) > 0 and dep["meets_temperature_safety"].all())
    verdict = ("PASS -- every regime has a simulator-verified design inside the 65 C PCM / 75 C water limits"
               if (all_regimes_covered and all_safe) else
               f"PARTIAL/FAIL -- no safe PCM design found for regime(s) {unsafe_regimes}; those regimes have no deployable PCM recommendation")

    lines = []
    lines.append("# PHASE 7 -- ASSAM MULTI-OBJECTIVE OPTIMIZATION REPORT (safety-verified)\n")
    lines.append(f"**Simulator:** `sim_v1_assam`  \n**Safety limits (frozen `system_config_shared.yaml`):** PCM <= {max_allowed_pcm} C, water <= {max_allowed_w} C, 0 safety-violation sub-hours  \n"
                 f"**Screened surrogate pool:** {len(candidates_df):,} designs; **simulator-verified:** {len(verified_df)}; **safe:** {len(safe_df)}  \n"
                 f"**Verdict:** {verdict}  \n**Max surrogate-vs-simulator useful-energy error (selected rows):** {max_err_pct:.2f}%\n")
    lines.append("## Method\n")
    lines.append(f"1,000 random designs per regime x PCM pair (3 PCMs + plain tank), geometry check + feasibility classifier (p >= 0.5), "
                 f"Phase 6 surrogates for ranking. The surrogates do not predict temperature safety, so each pair is walked in descending predicted useful energy "
                 f"through the real simulator until {SAFE_TARGET} safe designs are found or {MAX_SIM_PER_PAIR} simulations are spent. "
                 f"The 5% near-best rule and the hierarchy (unmet energy, solar fraction, pump energy, PCM mass, capsule count, safety margin) are then applied to the "
                 f"SAFE simulator-confirmed pool using simulated values. Plain tank is a reference row only.\n")
    lines.append("## Search outcome per regime x PCM\n")
    lines.append("| Regime | PCM | Simulated | Safe |\n|---|---|---|---|")
    for (rid, pid), g in verified_df.groupby(["regime_id", "pcm_id"]):
        lines.append(f"| {int(rid)} | {pid} | {len(g)} | {int(g['meets_temperature_safety'].sum())} |")
    lines.append("\n## Selected designs (simulator values)\n")
    lines.append("| Role | Regime | PCM | d (mm) | N | Flow (kg/s) | Useful (kWh) | Solar frac | Unmet (kWh) | Max PCM (C) | PCM margin (C) | Max water (C) | Violations | Surrogate err (%) | Safe |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for _, r in resim_df.iterrows():
        pm = "n/a" if r["pcm_id"] == "NONE_plain_tank" else f"{r['pcm_temp_safety_margin_C']:.2f}"
        lines.append(f"| {r['selection_role']} | {int(r['regime_id'])} | {r['pcm_id']} | {r['capsule_diameter_m']*1000:.1f} | {int(r['n_capsule'])} | "
                     f"{r['flow_rate_kg_s']:.4f} | {r['sim_useful_energy_kWh']:.2f} | {r['sim_solar_fraction']*100:.2f}% | {r['sim_unmet_energy_kWh']:.2f} | "
                     f"{r['sim_max_pcm_temp_C']:.2f} | {pm} | {r['sim_max_water_temp_C']:.2f} | {int(r['sim_n_safety_violations'])} | "
                     f"{r['err_useful_energy_pct']:.2f} | {_status(r['meets_temperature_safety'])} |")
    lines.append("\n## Acceptance checks (computed)\n")
    lines.append("| Check | Standard | Result |\n|---|---|---|")
    if len(dep):
        lines.append(f"| Max water temp | <= {max_allowed_w} C | {_status((dep['sim_max_water_temp_C'] <= max_allowed_w).all())} (max {dep['sim_max_water_temp_C'].max():.2f} C) |")
        lines.append(f"| Max PCM temp | <= {max_allowed_pcm} C | {_status((dep['sim_max_pcm_temp_C'] <= max_allowed_pcm).all())} (max {dep['sim_max_pcm_temp_C'].max():.2f} C) |")
        lines.append(f"| Safety violations | exactly 0 | {_status((dep['sim_n_safety_violations'] == 0).all())} (max {int(dep['sim_n_safety_violations'].max())}) |")
        lines.append(f"| Energy residual | < 0.05% of collector input | {_status((dep['sim_residual_pct_of_collector'].abs() < 0.05).all())} (max {dep['sim_residual_pct_of_collector'].abs().max():.4f}%) |")
    lines.append(f"| Every regime has a safe PCM design | {len(regimes)} of {len(regimes)} | {_status(all_regimes_covered)} ({len(dep)} of {len(regimes)}) |")
    if unsafe_regimes:
        lines.append(f"\n**No deployable PCM design for regime(s) {unsafe_regimes}:** every simulated candidate breached the limits. "
                     f"Do not hand these regimes to Objective 3 as PCM designs.")
    lines.append("\nFull candidate-level data: `phase7_safety_verified_candidates.csv`.\n")
    lines.append(f"## Final verdict\n\n**{verdict}**\n")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Report written successfully to {report_path.name}")

    print("\n==================================================")
    print(f"PHASE 7 OPTIMIZATION COMPLETE -- {verdict}")
    print("==================================================")


if __name__ == "__main__":
    run_search("assam")
