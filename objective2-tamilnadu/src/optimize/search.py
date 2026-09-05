"""
src/optimize/search.py
=========================
Phase 7 / D2.6 — "one optimization pass" over the surrogate, per the
framework doc's reduced spec: "Search the surrogate over the design grid -
coarse grid, random search, or a single weighted-sum run ... State it's a
single pass, not the full loop." No active-learning, no NSGA-II.

For each regime x shortlisted-PCM pair:
  1. Random-search candidate design vectors within design_bounds_shared.yaml.
  2. Apply Phase 2's REAL geometry/constraint gate to each candidate first
     (deterministic, free) -- a candidate the geometry engine already
     rejects is never even scored by the surrogate.
  3. Score surviving candidates with the Phase 6 surrogate (useful energy,
     solar fraction, unmet energy, pump energy, PCM mass, predicted
     feasibility probability).
  4. Rank by predicted useful energy (primary objective, framework doc
     §9.1) and return the top N for src/optimize/select_deployable.py to
     re-run in the REAL simulator -- surrogate output is a proposal
     ranking, never a final result (Bug-Fix 5).
"""

import pickle

import numpy as np
import pandas as pd

from src.design.schema import DesignVector
from src.design.constraints import check_design
from src.io_utils import load_design_bounds, load_system_config
from src.surrogate.features import build_feature_table, feature_target_split

N_CANDIDATES_PER_PAIR = 400
SEARCH_SEED = 20260905


def _random_candidates(bounds, n, seed):
    rng = np.random.default_rng(seed)
    d = rng.uniform(bounds["capsule_diameter_m"]["min"], bounds["capsule_diameter_m"]["max"], n)
    f = rng.uniform(bounds["flow_rate_kg_s"]["min"], bounds["flow_rate_kg_s"]["max"], n)
    c = rng.integers(bounds["capsule_count"]["min"], bounds["capsule_count"]["max"] + 1, n)
    return d, c, f


def _candidate_row(regime_id, pcm_id, design: DesignVector, geom: dict) -> dict:
    return {
        "regime_id": regime_id, "pcm_id": pcm_id if pcm_id is not None else "NONE_plain_tank",
        "capsule_diameter_m": design.capsule_diameter_m, "n_capsule": design.n_capsule,
        "flow_rate_kg_s": design.flow_rate_kg_s, "valid": True,
        "geom_pcm_thickness_m": geom["pcm_thickness_m"],
        "geom_pcm_volume_fraction": geom["pcm_volume_fraction"],
        "geom_void_fraction": geom["void_fraction"],
        "geom_pressure_drop_pa": geom["pressure_drop_pa"],
        "geom_pump_power_w": geom["pump_power_w"],
        "geom_reynolds_number_particle": geom["reynolds_number_particle"],
    }


def search_regime_pcm(state: str, regime_id: int, pcm_id, models: dict, feature_cols: list,
                       n_candidates: int = N_CANDIDATES_PER_PAIR, top_n: int = 5, seed: int = None):
    seed = seed if seed is not None else SEARCH_SEED + regime_id * 97 + (hash(pcm_id) % 997 if pcm_id else 0)
    bounds = load_design_bounds()
    system_config = load_system_config()
    diam, count, flow = _random_candidates(bounds, n_candidates, seed)

    rows = []
    for i in range(n_candidates):
        design = DesignVector(float(diam[i]), int(count[i]), float(flow[i]))
        geom = check_design(design, system_config, bounds)
        if not geom["valid"]:
            continue
        rows.append(_candidate_row(regime_id, pcm_id, design, geom))

    if not rows:
        return pd.DataFrame()

    cand_df = pd.DataFrame(rows)
    feat_df = build_feature_table(state, cand_df)
    X, _, _, _ = feature_target_split(feat_df, only_valid=False)
    X = X[feature_cols]   # exact column order/set the trained models expect

    for target, model in models.items():
        if target == "feasibility":
            proba = model.predict_proba(X)
            cand_df["predicted_feasible_proba"] = proba[:, list(model.classes_).index(1)] if 1 in model.classes_ else 1.0
        else:
            cand_df[f"pred_{target}"] = model.predict(X)

    cand_df = cand_df.sort_values("pred_useful_energy_kWh", ascending=False)
    return cand_df.head(top_n).reset_index(drop=True)


def search_all_pairs(state: str, top_n: int = 5):
    from config import RESULTS_DIR
    from src.io_utils import load_state_config

    out_dir = RESULTS_DIR / state
    with open(out_dir / "surrogate" / "models.pkl", "rb") as f:
        saved = pickle.load(f)
    models, feature_cols = saved["models"], saved["feature_cols"]

    cfg = load_state_config(state)
    all_top = []
    for regime in cfg["regimes"]:
        cid = regime["cluster_id"]
        for pcm_id in regime["pcm_shortlist"]:
            top = search_regime_pcm(state, cid, pcm_id, models, feature_cols, top_n=top_n)
            if not top.empty:
                all_top.append(top)
        # also search the no-PCM baseline design space for this regime once
        top_plain = search_regime_pcm(state, cid, None, models, feature_cols, top_n=top_n)
        if not top_plain.empty:
            all_top.append(top_plain)

    result = pd.concat(all_top, ignore_index=True) if all_top else pd.DataFrame()
    result.to_csv(out_dir / "surrogate_top_candidates.csv", index=False)
    print(f"Surrogate proposed {len(result)} top candidates "
          f"across {result.groupby(['regime_id', 'pcm_id']).ngroups if len(result) else 0} regime x PCM pairs.")
    print(f"Saved: {out_dir / 'surrogate_top_candidates.csv'}")
    return result


if __name__ == "__main__":
    import sys
    state = sys.argv[1] if len(sys.argv) > 1 else "tamilnadu"
    search_all_pairs(state)
