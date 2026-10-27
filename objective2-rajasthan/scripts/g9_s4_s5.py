"""
scripts/g9_s4_s5.py
======================
G9 / S4 + S5 (plan WP5 5.4) for ONE (regime, O1 PCM) pair. Usage: python scripts/g9_s4_s5.py <cluster_id> <pcm_rank>

S4  NSGA-II (population 100, 100 generations, 3 seeds, src/optimize/nsga2.py) on the per-pair winning surrogate
    (g8_s3_selection.csv). Objectives (minimised): f1 = -g_window, f2 = -g_annual, f3 = d_overheat. Constraints: exact geometry
    feasibility; predicted PCM peak + 1.0 C guard <= 65 C (the guard is about one surrogate RMSE; real feasibility is
    always re-checked in the simulator).
S5  active learning, up to 5 rounds: from the union of the three seeds' Pareto sets pick 10 candidates of largest
    committee (NN + XGBoost + RSM) disagreement, simulate them on the EXPLORE years, add them, refit, re-run NSGA-II.
    Stop when the hypervolume of the simulator-evaluated front moves < 1 % for two rounds.
Final: each seed's last Pareto set (thinned to 25) is simulated; per-seed hypervolume of the SIMULATED front gives the
seed spread (gate: spread inside the WP6 band, checked in g9_assess.py).
Only the simulator's numbers are ever reported; surrogate values are used to propose candidates.
Writes results/g9_al_log_r<c>_p<k>.csv, g9_points_r<c>_p<k>.csv (every simulated design, with its origin),
g9_seed_front_r<c>_p<k>.csv.
"""

import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.design.constraints import check_design
from src.design.space import count_for_fraction, geometry_bounds, to_design, capsule_outer_volume_m3, v_tank_m3
from src.io_utils import get_regime, load_system_config
from src.optimize.evaluate import evaluate_design
from src.optimize.nsga2 import hypervolume, nsga2, non_dominated_mask
from src.optimize.surrogates import FAMILIES, TARGETS, feature_matrix

GUARD_C = 1.0
PCM_LIMIT = 65.0
SEEDS = (1, 2, 3)
N_POP, N_GEN = 100, 100
PER_ROUND = 10
MAX_ROUNDS = int(os.environ.get("G9_MAX_ROUNDS", 5))      # G9 follow-up: r0_p1 re-run with more rounds (warm start, "_ext" outputs)
WARM = bool(os.environ.get("G9_WARM"))
VERTICES = bool(os.environ.get("G9_VERTICES"))           # G9 follow-up 2: simulate the design-box vertices before more AL rounds
FROM_SUFFIX = os.environ.get("G9_FROM_SUFFIX", "")        # which saved state to continue from ("" original, "_ext" first extension)
SUFFIX = ("_ext2" if VERTICES else "_ext") if WARM else ""
THIN = 25
if os.environ.get("G9_FAST"):                       # smoke test only: tiny budget, files go to results/_smoke
    N_POP, N_GEN, PER_ROUND, MAX_ROUNDS, THIN, SEEDS = 20, 5, 3, 1, 4, (1,)
READDIR = Path("results")                  # saved states are always read from here
OUTDIR = Path(os.environ.get("G9_OUTDIR") or ("results/_smoke" if os.environ.get("G9_FAST") else "results"))   # G9_OUTDIR: issue-1 diagnostic runs write elsewhere
ARR = ("single-layer", "staggered", "radial")
_geom_cache = {}


def decode(u):
    r = 0.010 + 0.030 * u[0]
    f = 0.02 + 0.28 * u[1]       # v3 box: 2-30 %
    q = 0.010 + 0.040 * u[2]
    arr = ARR[min(int(u[3] * 3), 2)]
    n = count_for_fraction(r, f)
    frac = n * capsule_outer_volume_m3(r) / v_tank_m3()
    return r, frac, q, arr, n


def geometry_ok(r, n, q, arr):
    key = (round(r, 7), n, round(q, 6), arr)
    if key not in _geom_cache:
        dv = to_design(r, 0.1, q, arr)
        dv = type(dv)(capsule_diameter_m=dv.capsule_diameter_m, n_capsule=n, flow_rate_kg_s=q, capsule_arrangement=arr)
        _geom_cache[key] = bool(check_design(dv, load_system_config(), geometry_bounds())["valid"])
    return _geom_cache[key]


def to_frame(U):
    rows = []
    for u in U:
        r, frac, q, arr, n = decode(u)
        rows.append({"R_in_m": r, "fraction": frac, "flow": q, "arrangement": arr, "N": n})
    return pd.DataFrame(rows)


def objectives(df_targets):
    return np.column_stack([-df_targets["g_window"], -df_targets["g_annual"], df_targets["d_overheat"]])


def fit_models(train, chosen):
    X, Y = feature_matrix(train), train[list(TARGETS)].to_numpy(float)
    models = {chosen: FAMILIES[chosen]().fit(X, Y)}
    return models, X, Y


def committee_uncertainty(train, cand_frame):
    """Normalised max-over-targets std across the three families' predictions at the candidates."""
    X, Y = feature_matrix(train), train[list(TARGETS)].to_numpy(float)
    Xc = feature_matrix(cand_frame)
    P = np.stack([FAMILIES[f]().fit(X, Y).predict(Xc) for f in FAMILIES])      # fam x n x targets
    return (P.std(axis=0) / (Y.std(axis=0) + 1e-12)).max(axis=1)


def make_evaluator(model):
    def evaluate(U):
        fr = to_frame(U)
        P = model.predict(feature_matrix(fr))
        pred = pd.DataFrame(P, columns=list(TARGETS))
        F = objectives(pred)
        geo = np.array([0.0 if geometry_ok(r.R_in_m, int(r.N), r.flow, r.arrangement) else 1e3
                        for r in fr.itertuples()])
        G = geo + np.maximum(0.0, pred["t_pcm_max"].to_numpy() + GUARD_C - PCM_LIMIT)
        return F, G
    return evaluate


def sim_rows(cid, pcm, frame, origin):
    out = []
    for pos, r in enumerate(frame.itertuples()):
        res = evaluate_design(cid, pcm, float(r.R_in_m), float(r.fraction), float(r.flow), r.arrangement, purpose="explore")
        if not res["valid"]:
            continue
        # N may differ by one from the surrogate-side rounding: record what was actually simulated
        row = {k: res[k] for k in ("R_in_m", "fraction", "flow", "arrangement", "N", "g_window", "g_annual", "g_useful",
                                   "d_overheat", "t_pcm_max", "pcm_mass_kg", "feasible")}
        row["origin"] = origin
        row["cand_pos"] = pos                      # position in the proposed batch (aligns surrogate vs simulator)
        out.append(row)
    return pd.DataFrame(out)


def front_hv(df, ref):
    ok = df[df.feasible == True]  # noqa: E712
    if ok.empty:
        return 0.0, 0
    F = objectives(ok)
    m = non_dominated_mask(F)
    return hypervolume(F[m], ref), int(m.sum())


def main(cid, rank):
    t0 = time.time()
    pcm = get_regime("rajasthan", cid)["pcm_shortlist"][rank - 1]
    tag = f"r{cid}_p{rank}"
    doe = pd.read_csv(f"results/g8_s2_{tag}.csv")
    doe = doe[doe.status == "ok"].copy()
    doe["origin"] = "doe"
    cols = ["R_in_m", "fraction", "flow", "arrangement", "N", "g_window", "g_annual", "g_useful", "d_overheat",
            "t_pcm_max", "pcm_mass_kg", "feasible", "origin"]
    train = doe[cols].reset_index(drop=True)
    chosen = pd.read_csv("results/g8_s3_selection.csv").set_index("pair").loc[tag, "chosen"]
    F0 = objectives(train[train.feasible == True])  # noqa: E712
    span = F0.max(axis=0) - F0.min(axis=0)
    ref = F0.max(axis=0) + 0.05 * span                   # fixed for the whole pair
    log, prev_hv, small = [], None, 0
    start = 0
    if WARM:                                    # continue from the saved AL state: DOE + AL rounds only, final-seed points dropped
        prev = pd.read_csv(READDIR / f"g9_points_{tag}{FROM_SUFFIX}.csv")
        train = prev[prev.origin.str.startswith(("doe", "al_round"))][cols].reset_index(drop=True)
        log = pd.read_csv(READDIR / f"g9_al_log_{tag}{FROM_SUFFIX}.csv").to_dict("records")
        start = int(max(int(o.replace("al_round", "")) for o in prev.origin.unique() if o.startswith("al_round")))
        print(tag, "warm start at round", start, "n_train", len(train), flush=True)
        if VERTICES:                            # all 2^3 box corners (r, fraction, flow) x 3 arrangements; defined by the box only
            import itertools
            U = np.array([[a, b, c, d] for a, b, c in itertools.product((0.0, 1.0), repeat=3) for d in (0.0, 0.5, 0.99)])
            vfr = to_frame(U).drop_duplicates().reset_index(drop=True)
            vsim = sim_rows(cid, pcm, vfr, "vertex")
            print(tag, "vertices simulated", len(vsim), "of", len(vfr), flush=True)
            train = pd.concat([train, vsim[cols]], ignore_index=True)
            MAX_ROUNDS_EFF = start + 3

    MAX_ROUNDS_EFF = locals().get('MAX_ROUNDS_EFF', MAX_ROUNDS)
    for rnd in range(start, MAX_ROUNDS_EFF + 1):
        model = fit_models(train, chosen)[0][chosen]
        evaluate = make_evaluator(model)
        sets = []
        for s in SEEDS:
            res = nsga2(evaluate, 4, n_pop=N_POP, n_gen=N_GEN, seed=s * 101 + rnd)
            sets.append(res)
        cand_U = np.vstack([r["X"][(r["G"] <= 0) & non_dominated_mask(r["F"])] for r in sets])
        cand = to_frame(cand_U).drop_duplicates().reset_index(drop=True)
        hv, npar = front_hv(train, ref)
        entry = {"round": rnd, "n_train": len(train), "hv_simulated_front": hv, "n_front": npar,
                 "n_candidates": len(cand), "elapsed_s": time.time() - t0}
        if rnd == MAX_ROUNDS_EFF or (rnd >= 2 and small >= 2):
            log.append(entry)
            break
        # --- active learning: most uncertain, diverse candidates
        key = lambda d: set(zip(d.R_in_m.round(6), d.N, d.flow.round(5), d.arrangement))   # noqa: E731
        seen = key(train)
        cand = cand[[k not in seen for k in zip(cand.R_in_m.round(6), cand.N, cand.flow.round(5), cand.arrangement)]]
        if cand.empty:
            log.append({**entry, "note": "no new candidates"})
            break
        unc = committee_uncertainty(train, cand)
        cand = cand.assign(unc=unc).sort_values("unc", ascending=False)
        chosen_rows, sel = [], []
        z = np.column_stack([cand.R_in_m / 0.03, cand.fraction / 0.3, cand.flow / 0.04,
                             cand.arrangement.map({a: i for i, a in enumerate(ARR)}) / 2.0])
        for i in range(len(cand)):
            if all(np.linalg.norm(z[i] - z[j]) > 0.05 for j in sel):
                sel.append(i)
            if len(sel) == PER_ROUND:
                break
        batch = cand.iloc[sel]
        pred = model.predict(feature_matrix(batch))
        sim = sim_rows(cid, pcm, batch, f"al_round{rnd + 1}")
        if len(sim):
            pos = sim["cand_pos"].to_numpy(int)
            entry["mean_abs_err_g_annual"] = float(np.mean(np.abs(sim["g_annual"].to_numpy() - pred[pos, 1])))
            entry["mean_abs_err_tpcm"] = float(np.mean(np.abs(sim["t_pcm_max"].to_numpy() - pred[pos, 3])))
            train = pd.concat([train, sim[cols]], ignore_index=True)
        log.append(entry)
        hv_new, _ = front_hv(train, ref)
        small = small + 1 if (prev_hv is not None and abs(hv_new - hv) / max(hv, 1e-9) < 0.01) else 0
        prev_hv = hv
        print(tag, "round", rnd + 1, "hv", round(hv_new, 2), "n_train", len(train), flush=True)

    # ---- final: per-seed simulated fronts
    seed_rows = []
    for s, res in zip(SEEDS, sets):
        ok = (res["G"] <= 0) & non_dominated_mask(res["F"])
        fr = to_frame(res["X"][ok]).drop_duplicates()
        if len(fr) > THIN:                                            # thin evenly along f2 (annual gain)
            fr = fr.iloc[np.linspace(0, len(fr) - 1, THIN).astype(int)]
        sim = sim_rows(cid, pcm, fr, f"final_seed{s}")
        sim["seed"] = s
        seed_rows.append(sim)
    seedf = pd.concat(seed_rows, ignore_index=True)
    allp = pd.concat([train, seedf.drop(columns="seed")], ignore_index=True)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(log).to_csv(OUTDIR / f"g9_al_log_{tag}{SUFFIX}.csv", index=False)
    allp.to_csv(OUTDIR / f"g9_points_{tag}{SUFFIX}.csv", index=False)
    seedf.to_csv(OUTDIR / f"g9_seed_front_{tag}{SUFFIX}.csv", index=False)
    pd.DataFrame([{"ref_g_window": -ref[0], "ref_g_annual": -ref[1], "ref_d_overheat": ref[2], "surrogate": chosen}]
                 ).to_csv(OUTDIR / f"g9_ref_{tag}{SUFFIX}.csv", index=False)
    print("done", tag, f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
