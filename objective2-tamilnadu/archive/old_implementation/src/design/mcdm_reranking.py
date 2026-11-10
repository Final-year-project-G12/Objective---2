"""
src/design/mcdm_reranking.py
=============================
Re-ranks each regime's PCM shortlist against the CURRENT (retargeted)
Tm_target_C using Objective 1's actual 4-method MCDM engine (TOPSIS +
GRA + PROMETHEE II + VIKOR, Borda-count consensus), instead of
`retarget_tm.py`'s simpler "closest |Tm - target|" substitute.

WHY THIS EXISTS: `retarget_tm.py` (doc 12) explicitly disclosed that its
shortlist re-selection was "a simpler, explicitly documented substitute
for Objective 1's full 4-method MCDM consensus, not a re-implementation
of it." That was never verified to actually agree or disagree with the
real method until now. Running the real method (this module) against
the current Tm targets shows it does NOT agree -- every regime's top-3
changes (see results/<state>/mcdm_reranked_shortlist_report.csv after
running this).

METHOD (ported directly from tamilnadu_pipeline/08_mcdm_ranking.py --
same criteria, weights, and consensus rule, so this is the genuine
Objective 1 algorithm applied to Objective 2's new targets, not a new
invention):
  Criteria (all benefit-oriented after transform): f_Tm (Gaussian
  melting-point fitness, sigma=4K), latent_heat_margin_ratio
  (latent_heat_kJ_kg / L_required_kJ_per_kg), rho_H_MJ_m3, TC_W_mK,
  cycles_confidence.
  Weights: 0.5*entropy-derived + 0.5*AHP-prior blend (identical AHP
  prior values to 08_mcdm_ranking.py).
  Methods: TOPSIS, GRA (zeta=0.5), PROMETHEE II (q=0.10, p=0.30 of the
  [0,1] range), VIKOR (v=0.5).
  Consensus: Borda count across the four methods' ranks.

ELIGIBILITY POOL: Objective 1's `feasibility_survivors_by_cluster.csv`,
re-filtered exactly as `retarget_tm.py` does -- melting window
recomputed against the CURRENT Tm_target_C ([target-5, target+8] C),
other pass flags (latent heat/cycling/supercooling/corrosion/safety)
reused unchanged, plus the REQUIRED_SIMULATOR_PROPERTIES completeness
check (a candidate must have every property the simulator needs, not
just pass Objective 1's feasibility flags on paper).

THIS SCRIPT IS READ-ONLY WITH RESPECT TO THE PIPELINE: it does NOT
overwrite `configs/states/<state>.yaml`'s `pcm_shortlist`, and Phases
5-8 are NOT re-run by this module. It only writes a comparison report so
the new shortlist can be reviewed before deciding whether to adopt it
(which would require the same Phase 5-8 re-run any shortlist change
does, per the framework's Phase 0 gate).

Run: python -m src.design.mcdm_reranking tamilnadu
"""

import sys

import numpy as np
import pandas as pd
import yaml

from config import BASE_DIR, RESULTS_DIR, CONFIGS_DIR
from src.io_utils import load_state_config
from src.design.retarget_tm import (
    WINDOW_LO_OFFSET, WINDOW_HI_OFFSET, REQUIRED_SIMULATOR_PROPERTIES,
    _rewrite_yaml_preserving_header,
)

# ─── identical constants to tamilnadu_pipeline/08_mcdm_ranking.py ──────────
SIGMA_TM = 4.0
ENTROPY_AHP_LAMBDA = 0.5
GRA_ZETA = 0.5
PROMETHEE_Q, PROMETHEE_P = 0.10, 0.30
VIKOR_V = 0.5
AHP_PRIOR = {
    "f_Tm": 0.24 / 0.80,
    "latent_heat_margin_ratio": 0.20 / 0.80,
    "rho_H_MJ_m3": 0.12 / 0.80,
    "TC_W_mK": 0.13 / 0.80,
    "cycles_confidence": 0.11 / 0.80,
}
CRITERIA = list(AHP_PRIOR.keys())
TOP_N = 3


def gaussian_tm_fitness(tm, tm_target, sigma=SIGMA_TM):
    return np.exp(-((tm - tm_target) ** 2) / (2 * sigma ** 2))


def minmax_normalize(df, cols):
    M = df[cols].copy()
    for c in cols:
        lo, hi = M[c].min(), M[c].max()
        M[c] = (M[c] - lo) / (hi - lo) if hi > lo else 0.5
    return M.fillna(0.0).values


def entropy_weights(matrix):
    X = matrix.copy()
    col_sums = X.sum(axis=0)
    col_sums = np.where(col_sums == 0, 1e-12, col_sums)
    P = X / col_sums
    n = X.shape[0]
    k = 1.0 / np.log(n) if n > 1 else 1.0
    with np.errstate(divide="ignore", invalid="ignore"):
        e = -k * np.nansum(np.where(P > 0, P * np.log(P), 0), axis=0)
    d = 1 - e
    return d / d.sum() if d.sum() > 0 else np.ones(len(d)) / len(d)


def topsis(matrix, weights):
    norm = matrix / (np.sqrt((matrix ** 2).sum(axis=0)) + 1e-12)
    weighted = norm * weights
    v_plus, v_minus = weighted.max(axis=0), weighted.min(axis=0)
    s_plus = np.sqrt(((weighted - v_plus) ** 2).sum(axis=1))
    s_minus = np.sqrt(((weighted - v_minus) ** 2).sum(axis=1))
    return s_minus / (s_plus + s_minus + 1e-12)


def gra(matrix, weights, zeta=GRA_ZETA):
    ref = matrix.max(axis=0)
    delta = np.abs(matrix - ref)
    delta_min, delta_max = delta.min(), delta.max()
    coeff = (delta_min + zeta * delta_max) / (delta + zeta * delta_max + 1e-12)
    return (coeff * weights).sum(axis=1)


def promethee_ii(matrix, weights, q=PROMETHEE_Q, p=PROMETHEE_P):
    n, k = matrix.shape
    phi_plus = np.zeros(n)
    phi_minus = np.zeros(n)
    for j in range(k):
        col = matrix[:, j]
        d = col[:, None] - col[None, :]
        pref = np.clip((np.abs(d) - q) / (p - q + 1e-12), 0, 1)
        pref = np.where(d > 0, pref, 0.0)
        phi_plus += weights[j] * pref.sum(axis=1)
        phi_minus += weights[j] * pref.sum(axis=0)
    denom = max(n - 1, 1)
    return (phi_plus - phi_minus) / denom


def vikor(matrix, weights, v=VIKOR_V):
    f_star, f_minus = matrix.max(axis=0), matrix.min(axis=0)
    span = np.where((f_star - f_minus) == 0, 1e-12, f_star - f_minus)
    weighted_gap = weights * (f_star - matrix) / span
    S, R = weighted_gap.sum(axis=1), weighted_gap.max(axis=1)
    s_star, s_minus = S.min(), S.max()
    r_star, r_minus = R.min(), R.max()
    Q = (v * (S - s_star) / (s_minus - s_star + 1e-12) +
         (1 - v) * (R - r_star) / (r_minus - r_star + 1e-12))
    return Q


def borda_consensus(elig: pd.DataFrame) -> pd.Series:
    n = len(elig)
    names = elig["name"]
    b = pd.Series(0.0, index=names)
    for col in ["topsis_rank", "gra_rank", "promethee_rank", "vikor_rank"]:
        b += (n - elig.set_index("name")[col] + 1)
    return b


def rank_cluster_mcdm(elig: pd.DataFrame, tm_target: float) -> pd.DataFrame:
    """Runs the full TOPSIS+GRA+PROMETHEE+VIKOR+Borda stack on one
    regime's eligible-candidate table. Returns it sorted best-first."""
    elig = elig.copy().reset_index(drop=True)
    l_required = elig["L_required_kJ_per_kg"].iloc[0]
    elig["f_Tm"] = gaussian_tm_fitness(elig["Tm_C"], tm_target)
    elig["latent_heat_margin_ratio"] = elig["latent_heat_kJ_kg"] / l_required
    med = elig["cycles_confidence"].median()
    elig["cycles_confidence"] = elig["cycles_confidence"].fillna(med if med == med else 0.5)

    M = minmax_normalize(elig, CRITERIA)
    w_entropy = entropy_weights(M)
    w_ahp = np.array([AHP_PRIOR[c] for c in CRITERIA])
    w_ahp = w_ahp / w_ahp.sum()
    w_final = ENTROPY_AHP_LAMBDA * w_entropy + (1 - ENTROPY_AHP_LAMBDA) * w_ahp
    w_final = w_final / w_final.sum()

    elig["topsis_score"] = topsis(M, w_final)
    elig["gra_grade"] = gra(M, w_final)
    elig["promethee_flow"] = promethee_ii(M, w_final)
    elig["vikor_Q"] = vikor(M, w_final)

    elig["topsis_rank"] = elig["topsis_score"].rank(ascending=False, method="min").astype(int)
    elig["gra_rank"] = elig["gra_grade"].rank(ascending=False, method="min").astype(int)
    elig["promethee_rank"] = elig["promethee_flow"].rank(ascending=False, method="min").astype(int)
    elig["vikor_rank"] = elig["vikor_Q"].rank(ascending=True, method="min").astype(int)

    elig["borda_score"] = elig["name"].map(borda_consensus(elig))
    elig["consensus_rank"] = elig["borda_score"].rank(ascending=False, method="min").astype(int)
    for i, c in enumerate(CRITERIA):
        elig[f"weight_{c}"] = w_final[i]

    return elig.sort_values("consensus_rank").reset_index(drop=True)


def eligible_candidates(feasibility_df: pd.DataFrame, pcm_db_df: pd.DataFrame,
                         cluster_id: int, tm_target: float) -> pd.DataFrame:
    """Identical eligibility logic to retarget_tm.select_shortlist_for_target,
    but returns the full eligible table (not just top-3) for MCDM ranking."""
    complete = pcm_db_df.dropna(subset=REQUIRED_SIMULATOR_PROPERTIES)["name"]
    df = feasibility_df[feasibility_df["cluster_id"] == cluster_id].copy()
    lo, hi = tm_target + WINDOW_LO_OFFSET, tm_target + WINDOW_HI_OFFSET
    df["new_pass_melting_window"] = df["Tm_C"].between(lo, hi)
    # See retarget_tm.select_shortlist_for_target: 2026-09-17 Objective 1
    # refresh renamed these columns to the c1-c8 string scheme.
    df["new_passes_all"] = (
        df["new_pass_melting_window"]
        & (df["c2_absolute_band"] == "pass")
        & (df["c3_latent_heat"] == "pass")
        & (df["c4_cycling"] == "pass")
        & (df["c5_supercooling"] == "pass")
        & df["survives_c7_corrosion"].fillna(False)
        & df["survives_c8_safety"].fillna(False)
        & df["name"].isin(complete)
    )
    return df[df["new_passes_all"]].copy()


def rerank_all(state: str, top_n: int = TOP_N) -> pd.DataFrame:
    """Main entry: for every regime in the CURRENT (already-retargeted)
    state config, re-ranks eligible candidates with the real MCDM stack
    and writes a before/after comparison report. Does NOT modify
    configs/states/<state>.yaml -- read-only with respect to the
    pipeline (see module docstring)."""
    cfg = load_state_config(state)
    # Kappa-calibrated pool -- see retarget_tm.retarget_all's comment for why
    # the plain (uncalibrated) feasibility file is not used here.
    feasibility_df = pd.read_csv(BASE_DIR / "data" / "objective1" / "feasibility_survivors_by_cluster_kappa_calibrated.csv")
    pcm_db_df = pd.read_csv(BASE_DIR / "data" / "objective1" / f"pcm_database_{state}.csv")

    rows = []
    full_rows = []
    for regime in cfg["regimes"]:
        cid = regime["cluster_id"]
        tm_target = regime["Tm_target_C"]
        current_shortlist = regime["pcm_shortlist"]

        elig = eligible_candidates(feasibility_df, pcm_db_df, cid, tm_target)
        if len(elig) < 2:
            print(f"  regime {cid}: <2 eligible candidates ({len(elig)}) -- MCDM needs >=2, skipping")
            continue

        ranked = rank_cluster_mcdm(elig, tm_target)
        if "cluster_id" not in ranked.columns:
            ranked.insert(0, "cluster_id", cid)
        full_rows.append(ranked)

        mcdm_shortlist = ranked.head(top_n)["name"].tolist()
        same_set = set(current_shortlist) == set(mcdm_shortlist)

        rows.append({
            "cluster_id": cid,
            "Tm_target_C": tm_target,
            "n_eligible": len(elig),
            "current_shortlist_nearest_tm": "; ".join(current_shortlist),
            "mcdm_shortlist_borda_consensus": "; ".join(mcdm_shortlist),
            "same_set": same_set,
            "mcdm_top1_Tm_C": ranked.iloc[0]["Tm_C"],
            "mcdm_top1_latent_heat_kJ_kg": ranked.iloc[0]["latent_heat_kJ_kg"],
        })
        flag = "" if same_set else "  <-- DIFFERS from current shortlist"
        print(f"  regime {cid} (Tm_target={tm_target}, n_eligible={len(elig)}): "
              f"MCDM top-{top_n} = {mcdm_shortlist}{flag}")

    report_df = pd.DataFrame(rows)
    out_dir = RESULTS_DIR / state
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "mcdm_reranked_shortlist_report.csv"
    report_df.to_csv(report_path, index=False)
    print(f"\nSaved: {report_path}")

    if full_rows:
        full_df = pd.concat(full_rows, ignore_index=True)
        full_path = out_dir / "mcdm_reranked_full_scores.csv"
        full_df.to_csv(full_path, index=False)
        print(f"Saved: {full_path}  (full per-candidate scores, all methods, all regimes)")

    n_diff = (~report_df["same_set"]).sum() if len(report_df) else 0
    print(f"\n{n_diff}/{len(report_df)} regimes: full-MCDM shortlist differs from the "
          f"current nearest-Tm shortlist. NOTE: configs/states/{state}.yaml was NOT "
          f"modified by this script -- review the report above/on disk, then decide "
          f"whether to adopt the MCDM shortlist (which requires a Phase 5-8 re-run).")
    return report_df


def apply_mcdm_shortlist(state: str, top_n: int = TOP_N) -> pd.DataFrame:
    """Adopts the full-MCDM shortlist as this state's `pcm_shortlist`,
    per regime, in `configs/states/<state>.yaml` -- REPLACES the
    nearest-Tm shortlist retarget_tm.py originally wrote (Tm_target_C
    itself is untouched, only pcm_shortlist changes). Backs up the
    pre-change file first (mirrors retarget_tm.py's own backup
    convention). Per the framework's Phase 0 gate, this REQUIRES
    re-running Phases 5-8 afterward -- this function does not do that
    itself, see pipeline.py."""
    report_df = rerank_all(state, top_n=top_n)

    state_path = CONFIGS_DIR / "states" / f"{state}.yaml"
    backup_path = state_path.with_suffix(state_path.suffix + ".bak_pre_mcdm_rerank")
    with open(state_path, "r", encoding="utf-8") as f:
        raw_text = f.read()
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(raw_text)
    print(f"\nBacked up pre-change config to: {backup_path}")

    cfg = load_state_config(state)
    shortlist_by_cluster = {
        int(row["cluster_id"]): row["mcdm_shortlist_borda_consensus"].split("; ")
        for _, row in report_df.iterrows()
    }
    for regime in cfg["regimes"]:
        cid = int(regime["cluster_id"])
        if cid in shortlist_by_cluster:
            old = regime["pcm_shortlist"]
            regime["pcm_shortlist"] = shortlist_by_cluster[cid]
            print(f"  regime {cid}: pcm_shortlist {old} -> {shortlist_by_cluster[cid]}")

    with open(state_path, "w", encoding="utf-8") as f:
        f.write(_rewrite_yaml_preserving_header(raw_text, cfg))
    print(f"Saved: {state_path} (pcm_shortlist replaced with full-MCDM consensus per regime; "
          f"Tm_target_C unchanged)")
    return report_df


if __name__ == "__main__":
    state_arg = sys.argv[1] if len(sys.argv) > 1 else "tamilnadu"
    apply = "--apply" in sys.argv[2:]
    if apply:
        apply_mcdm_shortlist(state_arg)
    else:
        rerank_all(state_arg)
