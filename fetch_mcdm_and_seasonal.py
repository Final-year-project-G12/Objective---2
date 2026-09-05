"""
fetch_mcdm_and_seasonal.py  —  Rajasthan
=========================================
Builds the last two Tamil-Nadu-shaped files:

  1. mcdm_full_scores_by_cluster.csv   (TN: 08_mcdm_ranking.py's OUT_FULL)
  2. level_b_seasonal_topk.csv  +  level_b_seasonal_summary.md
                                       (TN: 11_level_b_seasonal_analysis.py)

Neither is written by the Rajasthan Objective 1 pipeline, so both are produced
here by IMPORTING era5-rajasthan/08_mcdm_ranking_rajasthan.py and calling its
own functions. Nothing is re-implemented, so these cannot drift from O1's
ranking engine.

WHY THE SCORES WERE MISSING, NOT ABSENT
---------------------------------------
08_mcdm_ranking_rajasthan.py's run_pipeline_once() already RETURNS the raw
scores as its third value — {"TOPSIS": ci, "PROMETHEE_II": phi, "VIKOR": q,
"GRA": gamma} (line 762). main() binds that to `_` and throws it away, keeping
only the integer ranks. This script re-runs the same deterministic per-cluster
block (matrix -> entropy weights -> corrosion reweight -> blend -> the four
methods) and keeps the scores. The Monte Carlo columns are NOT recomputed —
they are joined from the existing mcdm_rankings_rajasthan.csv, so the frozen
MC numbers stay exactly the ones O1 reported.

WHERE RAJASTHAN DIFFERS FROM TAMIL NADU
----------------------------------------
* CRITERIA. Rajasthan ranks on 8 criteria (Tm_fitness, latent_heat,
  vol_latent_heat, thermal_conductivity, cycling, supercooling, corrosion,
  cost); Tamil Nadu uses 5. So there are 8 weight_* columns here, not 5, and
  they carry Rajasthan's names.
* METHODS. Rajasthan adds CoCoSo alongside TOPSIS/PROMETHEE II/VIKOR/GRA.
  Score columns keep Tamil Nadu's names where the concept is the same
  (topsis_score, gra_grade, promethee_flow, vikor_Q/S/R) so TN-written
  downstream code finds them.
* SEASONAL. Tamil Nadu's Level B re-ranks with a hand-rolled 5-criterion
  TOPSIS. This uses Rajasthan's own build_criteria_matrix() + topsis() on its
  8 criteria, with that cluster's blended weights — same question, Rajasthan's
  engine. The L_required_season formula is identical in both states
  (300 kg draw x 4.186 x (50 - T_mains) x 0.5 / 50 kg PCM).

HOW TO RUN:
  python fetch_mcdm_and_seasonal.py
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Read Objective 2's own config FIRST, into plain values. era5-rajasthan has its
# own config.py and 08 does `from config import ...`, so the name has to be free
# when that module is executed below.
from config import OBJ1_ROOT, OBJ1_PROCESSED_DIR, STATE, FROZEN_DIR, ensure_dirs

OBJ1_ROOT = Path(OBJ1_ROOT)
OBJ1_PROCESSED_DIR = Path(OBJ1_PROCESSED_DIR)
FROZEN_DIR = Path(FROZEN_DIR)
CLEAN_POINTS = OBJ1_PROCESSED_DIR / f"climate_{STATE}_points_clean.csv"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ── Import Objective 1's ranking engine ─────────────────────────────────────
_saved_config = sys.modules.pop("config", None)
sys.path.insert(0, str(OBJ1_ROOT))
_spec = importlib.util.spec_from_file_location(
    "mcdm08", OBJ1_ROOT / f"08_mcdm_ranking_{STATE}.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)
sys.path.remove(str(OBJ1_ROOT))
sys.modules.pop("config", None)
if _saved_config is not None:
    sys.modules["config"] = _saved_config

# 04_climate_signature_rajasthan.py:201/233-250 — identical to Tamil Nadu's
# 11_level_b_seasonal_analysis.py:62-71.
T_DELIVERY_C = 50.0
NIGHT_DRAW_TOTAL_KG = 300.0
CP_WATER = 4.186
ASSUMED_PCM_MASS_KG = 50.0
SHARE_PCM = 0.5
WINDOW_LOWER_OFFSET, WINDOW_UPPER_OFFSET = 5.0, 8.0
SEASON_ORDER = ["Winter", "Summer", "Monsoon", "Retreat"]

# 07_feasibility_filter_rajasthan.py:156,162 — the feasibility constants live in
# 07, not 08, so they are restated here. LATENT_HEAT_KAPPA=0.7 is also exactly
# Tamil Nadu 11_level_b_seasonal_analysis.py's LATENT_HEAT_FRACTION, so the
# seasonal screen is the same on both sides. Note this is the FIXED baseline
# kappa, not the per-cluster calibrated one the annual run ended up using.
ABSOLUTE_TM_MIN, ABSOLUTE_TM_MAX = 42.0, 70.0
LATENT_HEAT_KAPPA = 0.7


# ═══════════════════════════════════════════════════════════════════════════
# 1. mcdm_full_scores_by_cluster.csv
# ═══════════════════════════════════════════════════════════════════════════
def build_full_scores():
    print("\n" + "=" * 74)
    print("  [1/2] mcdm_full_scores_by_cluster.csv")
    print("=" * 74)

    survivors, profiles, profile_fp_id = M.load_survivors()
    rich = pd.concat([M.load_rich_pcm_properties(), M.literature_rich_properties()],
                     ignore_index=True, sort=False)
    survivors = survivors.merge(rich, on=["pcm_id", "family"], how="left",
                                suffixes=("", "_rich"))
    hsi_min, hsi_max = profiles["HSI_sunrise"].min(), profiles["HSI_sunrise"].max()
    prior_w = (M.ahp_weights_from_pairwise(np.array(M.PAIRWISE_MATRIX))[0]
               if M.PAIRWISE_MATRIX is not None else M.LITERATURE_WEIGHTS_TABLE13)

    rows = []
    weights_by_cluster = {}
    for prof in profiles.itertuples():
        cid, tm_target, cluster_hsi = prof.cluster_id, prof.Tm_target_C, prof.HSI_sunrise
        cand = survivors[survivors["cluster_id"] == cid].reset_index(drop=True)

        matrix = M.build_criteria_matrix(cand, tm_target)
        ent_w = M.entropy_weights(matrix)
        cluster_prior_w = M.reweight_corrosion_for_cluster(prior_w, cluster_hsi,
                                                           hsi_min, hsi_max)
        blend_w = M.blended_weights(ent_w, cluster_prior_w)
        weights_by_cluster[cid] = blend_w

        borda, ranks, scores = M.run_pipeline_once(cand, blend_w, tm_target, matrix)
        _, vikor_S, vikor_R = M.vikor(matrix, blend_w)
        copeland_scores = M.copeland(ranks)
        W = M.kendalls_w(ranks)

        consensus_rank = borda.rank(ascending=False, method="min").astype(int)
        copeland_rank = copeland_scores.rank(ascending=False, method="min").astype(int)

        for _, c in cand.iterrows():
            pid = c["pcm_id"]
            r = c.to_dict()
            r["name"] = pid                       # Tamil Nadu's key column
            r["Tm_target_C"] = tm_target
            r["L_required_kJ_per_kg"] = prof.L_required_kJ_per_kg
            for crit in M.CRITERIA:               # raw criteria values
                r[crit] = matrix.loc[pid, crit]
            r["topsis_score"] = float(scores["TOPSIS"][pid])
            r["promethee_flow"] = float(scores["PROMETHEE_II"][pid])
            r["vikor_Q"] = float(scores["VIKOR"][pid])
            r["vikor_S"] = float(vikor_S[pid])
            r["vikor_R"] = float(vikor_R[pid])
            r["gra_grade"] = float(scores["GRA"][pid])
            r["topsis_rank"] = int(ranks["TOPSIS"][pid])
            r["promethee_rank"] = int(ranks["PROMETHEE_II"][pid])
            r["vikor_rank"] = int(ranks["VIKOR"][pid])
            r["gra_rank"] = int(ranks["GRA"][pid])
            if "CoCoSo" in ranks:
                r["cocoso_rank"] = int(ranks["CoCoSo"][pid])
            r["borda_score"] = float(borda[pid])
            r["copeland_score"] = int(copeland_scores[pid])
            r["consensus_rank"] = int(consensus_rank[pid])
            r["copeland_rank"] = int(copeland_rank[pid])
            r["kendall_w"] = float(W)
            r["borda_copeland_agree"] = bool(consensus_rank[pid] == copeland_rank[pid])
            for crit in M.CRITERIA:
                r[f"weight_{crit}"] = blend_w[crit]
                r[f"entropy_weight_{crit}"] = ent_w[crit]
                r[f"prior_weight_{crit}"] = cluster_prior_w[crit]
            rows.append(r)

        print(f"  cluster {cid}: {len(cand)} candidates, Kendall W={W:.3f}, "
              f"top-1 by Borda = {borda.idxmax()}")

    full = pd.DataFrame(rows)

    # Monte Carlo columns come from O1's frozen table — never recomputed here.
    mc_src = OBJ1_PROCESSED_DIR / f"mcdm_rankings_{STATE}.csv"
    if mc_src.exists():
        mc = pd.read_csv(mc_src)
        mc_cols = [c for c in mc.columns if c.startswith("mc_")]
        full = full.merge(mc[["cluster_id", "pcm_id"] + mc_cols],
                          on=["cluster_id", "pcm_id"], how="left")
        # Tamil Nadu's names for the same three quantities
        full["top3_inclusion_probability"] = full.get("mc_top3_inclusion_pct")
        full["top1_retention_rate"] = full.get("mc_top1_retention_pct")
        full["mean_spearman_rho_vs_baseline"] = full.get(
            "mc_mean_spearman_vs_baseline_cluster")
        full["n_draws"] = M.N_DRAWS
        print(f"  joined {len(mc_cols)} Monte Carlo columns from {mc_src.name} "
              f"(N_DRAWS={M.N_DRAWS}, not recomputed)")

    full["upstream_cluster_profile_fingerprint"] = profile_fp_id
    dest = FROZEN_DIR / "mcdm_full_scores_by_cluster.csv"
    full.to_csv(dest, index=False)
    print(f"\n  [OK] mcdm_full_scores_by_cluster.csv  ({len(full)} rows, "
          f"{len(full.columns)} cols)")

    # Cross-check the ranks against O1's own frozen table.
    if mc_src.exists():
        ref = pd.read_csv(mc_src)[["cluster_id", "pcm_id", "TOPSIS_rank",
                                   "PROMETHEE_II_rank", "VIKOR_rank", "GRA_rank",
                                   "borda_score"]]
        chk = full.merge(ref, on=["cluster_id", "pcm_id"], suffixes=("", "_o1"))
        pairs = [("topsis_rank", "TOPSIS_rank"), ("promethee_rank", "PROMETHEE_II_rank"),
                 ("vikor_rank", "VIKOR_rank"), ("gra_rank", "GRA_rank"),
                 ("borda_score", "borda_score_o1")]
        bad = {a: int((chk[a] != chk[b]).sum()) for a, b in pairs}
        status = "IDENTICAL to O1" if not any(bad.values()) else f"MISMATCH {bad}"
        print(f"  rank cross-check vs mcdm_rankings_{STATE}.csv: {status}")
    return full, weights_by_cluster, profiles


# ═══════════════════════════════════════════════════════════════════════════
# 2. level_b_seasonal_topk.csv
# ═══════════════════════════════════════════════════════════════════════════
def build_seasonal(full, weights_by_cluster, profiles):
    print("\n" + "=" * 74)
    print("  [2/2] level_b_seasonal_topk.csv")
    print("=" * 74)

    assign = pd.read_csv(OBJ1_PROCESSED_DIR / f"cluster_assignments_{STATE}_levelA.csv")
    if not CLEAN_POINTS.exists():
        print(f"  [ABORT] {CLEAN_POINTS} not found")
        return
    print(f"  reading {CLEAN_POINTS.name} "
          f"({CLEAN_POINTS.stat().st_size / 1e9:.2f} GB, 3 columns only) ...")
    physical = pd.read_csv(CLEAN_POINTS, usecols=["point_id", "season", "era5_T_amb"])

    survivors, profs, _ = M.load_survivors()
    rich = pd.concat([M.load_rich_pcm_properties(), M.literature_rich_properties()],
                     ignore_index=True, sort=False)
    pcm_db = survivors.merge(rich, on=["pcm_id", "family"], how="left",
                             suffixes=("", "_rich"))

    rows, md = [], [f"# Level B — Seasonal PCM Sensitivity ({STATE.title()})\n"]

    for prof in profiles.itertuples():
        cid = prof.cluster_id
        # Rajasthan's regime-capped target, the analogue of Tamil Nadu's
        # Tm_target_C_regime_capped.
        tm_target = getattr(prof, "Tm_target_capped_C", prof.Tm_target_C)
        weights = weights_by_cluster[cid]

        members = assign.loc[assign["cluster_id"] == cid, "point_id"].unique()
        cluster_phys = physical[physical["point_id"].isin(members)]
        cand_all = pcm_db[pcm_db["cluster_id"] == cid]

        annual = full[full["cluster_id"] == cid].sort_values("consensus_rank")
        annual_top1 = annual["pcm_id"].iloc[0]
        md.append(f"\n## Cluster {int(cid)}  (annual/Level-A #1: **{annual_top1}**)\n")
        md.append("| Season | #1 PCM | #2 PCM | #3 PCM | Flips from annual? |")
        md.append("|---|---|---|---|---|")

        for season in SEASON_ORDER:
            srows = cluster_phys[cluster_phys["season"] == season]
            if srows.empty:
                continue
            ta_mean = float(srows["era5_T_amb"].mean())
            t_mains = ta_mean - 2.0
            q_night = NIGHT_DRAW_TOTAL_KG * CP_WATER * (T_DELIVERY_C - t_mains)
            l_required = (q_night * SHARE_PCM) / ASSUMED_PCM_MASS_KG

            lo, hi = tm_target - WINDOW_LOWER_OFFSET, tm_target + WINDOW_UPPER_OFFSET
            floor = LATENT_HEAT_KAPPA * l_required
            surv = cand_all[
                cand_all["Tm_C"].between(lo, hi)
                & cand_all["Tm_C"].between(ABSOLUTE_TM_MIN, ABSOLUTE_TM_MAX)
                & (cand_all["latent_heat_kJ_kg"] >= floor)].copy()

            if len(surv) < 2:
                md.append(f"| {season} | (< 2 survivors at "
                          f"L_required={l_required:.0f}) | - | - | - |")
                rows.append({"cluster_id": cid, "season": season,
                             "Ta_mean_season": ta_mean,
                             "L_required_season": l_required,
                             "top1": "-", "top2": "-", "top3": "-",
                             "n_survivors_season": len(surv),
                             "flips_from_annual": None})
                continue

            matrix = M.build_criteria_matrix(surv.reset_index(drop=True), tm_target)
            ci = M.topsis(matrix, weights)
            ranked = ci.sort_values(ascending=False)
            top3 = list(ranked.index[:3]) + ["-"] * max(0, 3 - len(ranked))
            flips = top3[0] != annual_top1

            rows.append({"cluster_id": cid, "season": season,
                         "Ta_mean_season": ta_mean,
                         "L_required_season": l_required,
                         "top1": top3[0], "top2": top3[1], "top3": top3[2],
                         "n_survivors_season": len(surv),
                         "flips_from_annual": flips})
            md.append(f"| {season} | {top3[0]} | {top3[1]} | {top3[2]} | "
                      f"{'**YES**' if flips else 'No'} |")

        print(f"\n  Cluster {int(cid)} (annual #1: {annual_top1}, "
              f"Tm_target_capped={tm_target:.1f}C):")
        for r in [r for r in rows if r["cluster_id"] == cid]:
            flag = "  <-- FLIPS" if r["flips_from_annual"] else ""
            print(f"    {r['season']:8s}  Ta_mean={r['Ta_mean_season']:5.1f}C  "
                  f"L_required={r['L_required_season']:5.0f}  "
                  f"n={r['n_survivors_season']:2d}  #1={r['top1']}{flag}")

    out = pd.DataFrame(rows)
    out.to_csv(FROZEN_DIR / "level_b_seasonal_topk.csv", index=False)
    (FROZEN_DIR / "level_b_seasonal_summary.md").write_text("\n".join(md),
                                                            encoding="utf-8")
    print(f"\n  [OK] level_b_seasonal_topk.csv  ({len(out)} rows)")
    print("  [OK] level_b_seasonal_summary.md")

    valid = out[out["flips_from_annual"].notna()]
    n_flips = int(valid["flips_from_annual"].sum())
    print(f"\n  {n_flips}/{len(valid)} (cluster, season) combinations pick a "
          f"#1 PCM different from that cluster's annual choice.")
    if n_flips:
        print("  [FINDING] Seasonal flips detected — direct empirical motivation for "
              "the adaptive-control objective (O3's DRL controller), from this "
              "project's own data.")
    else:
        print("  No flips — also a valid finding: the delivery-temperature-anchored "
              "Tm_target rule is robust across Rajasthan's seasonal swing.")


if __name__ == "__main__":
    ensure_dirs()
    full, weights, profiles = build_full_scores()
    build_seasonal(full, weights, profiles)
    print("\n" + "=" * 74)
    print("  DONE — re-run build_input_package.py to refresh manifest.json")
    print("=" * 74)
