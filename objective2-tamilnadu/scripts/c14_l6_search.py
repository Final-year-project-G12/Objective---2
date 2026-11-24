"""
scripts/c14_l6_search.py   (level L6, step O2-10, gate G2)
============================================================
NSGA-II + committee active learning + box-vertex step for ONE (regime, O1 PCM) pair on the common-plant box (R_in, fraction 2-40 %, arrangement;
flow frozen, anchor handled by the three-anchor robust objective). The surrogate is the family chosen in c11 for this pair; it only PROPOSES,
every reported number is a simulator run at the cheap fidelity of the DOE (dt 150 s, 2017, three anchors).
Objectives (minimised): -robust mean paired gain (g_window), overheat hours (PCM tank minus plain), PCM volume.
Constraints: exact geometry, predicted PCM peak + 1 C <= 65 C.
Active learning: up to 3 rounds of 6 most-uncertain Pareto candidates (NN / XGBoost / RSM committee) and the box-vertex step; stop when the
hypervolume of the SIMULATED front moves < 1 % twice. The final per-seed Pareto sets are simulated; per-seed hypervolume gives the seed spread.
Usage: python scripts/c14_l6_search.py <cluster_id> <pcm_rank>   -> results/c14_l6_{points,log,front,seeds}_r<c>_p<k>.csv
"""
import itertools
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.design.constraints import check_design                                                      # noqa: E402
from src.design.space import capsule_outer_volume_m3, count_for_fraction, geometry_bounds, to_design, v_tank_m3   # noqa: E402
from src.io_utils import get_regime, load_system_config                                              # noqa: E402
from src.optimize.nsga2 import hypervolume, nsga2, non_dominated_mask                                # noqa: E402
from src.optimize.robust_eval import robust_row                                                      # noqa: E402
from src.optimize.surrogates import ARR, FAMILIES                                                    # noqa: E402
from config import STATE                                                                             # noqa: E402

TARGETS = ("g_window_mean", "g_window_worst", "d_overheat_mean", "t_pcm_max_mean")
SEEDS, N_POP, N_GEN, PER_ROUND, MAX_ROUNDS, THIN = (1, 2, 3), 100, 100, 6, 3, 15
GUARD_C, PCM_LIMIT, YEARS, DT = 1.0, 65.0, [2017], 150.0
_geom = {}


def decode(u):
    r, f, arr = 0.010 + 0.030 * u[0], 0.02 + 0.38 * u[1], ARR[min(int(u[2] * 3), 2)]
    n = count_for_fraction(r, f)
    return r, n * capsule_outer_volume_m3(r) / v_tank_m3(), arr, n


def geom_ok(r, n, arr):
    k = (round(r, 7), n, arr)
    if k not in _geom:
        d0 = to_design(r, 0.1, 0.030, arr)
        dv = type(d0)(capsule_diameter_m=d0.capsule_diameter_m, n_capsule=n, flow_rate_kg_s=0.030, capsule_arrangement=arr)
        _geom[k] = bool(check_design(dv, load_system_config(), geometry_bounds())["valid"])
    return _geom[k]


def frame(U):
    return pd.DataFrame([dict(zip(("R_in_m", "fraction", "arrangement", "N"), decode(u))) for u in U])


def feats(df):
    return np.column_stack([df.R_in_m * 1000.0, df.fraction] + [(df.arrangement == a).astype(float) for a in ARR])


def pcm_volume_l(df):
    return df.N * 4.0 / 3.0 * np.pi * df.R_in_m ** 3 * 1000.0


def objectives(df, pred=None):
    g, d = (pred[:, 0], pred[:, 2]) if pred is not None else (df.g_window_mean.to_numpy(), df.d_overheat_mean.to_numpy())
    return np.column_stack([-g, d, pcm_volume_l(df).to_numpy()])


def evaluator(model):
    def ev(U):
        fr = frame(U)
        P = model.predict(feats(fr))
        geo = np.array([0.0 if geom_ok(r.R_in_m, int(r.N), r.arrangement) else 1e3 for r in fr.itertuples()])
        return objectives(fr, P), geo + np.maximum(0.0, P[:, 3] + GUARD_C - PCM_LIMIT)
    return ev


def simulate(cid, pcm, fr, origin):
    rows = []
    for k, r in enumerate(fr.itertuples()):
        row = robust_row(cid, pcm, float(r.R_in_m), float(r.fraction), r.arrangement, YEARS, DT)
        if row["valid"]:
            row.update({"origin": origin, "cand_pos": k})
            rows.append(row)
    return pd.DataFrame(rows)


def front_hv(df, ref):
    ok = df[df.feasible == True]                                                                     # noqa: E712
    if ok.empty:
        return 0.0, 0
    F = objectives(ok)
    m = non_dominated_mask(F)
    return hypervolume(F[m], ref), int(m.sum())


def main(cid, rank):
    t0 = time.time()
    pcm = get_regime(STATE, cid)["pcm_shortlist"][rank - 1]
    tag = f"r{cid}_p{rank}"
    train = pd.read_csv(f"results/c9_l5_doe_{tag}.csv")
    train = train[train.status == "ok"].copy()
    train["origin"] = "doe"
    chosen = pd.read_csv("results/c11_l5_surrogate_selection.csv").set_index("pair").loc[tag, "chosen"]
    F0 = objectives(train[train.feasible == True])                                                   # noqa: E712
    ref = F0.max(axis=0) + 0.05 * (F0.max(axis=0) - F0.min(axis=0) + 1e-9)
    log, small, prev = [], 0, None
    for rnd in range(MAX_ROUNDS + 1):
        X, Y = feats(train), train[list(TARGETS)].to_numpy(float)
        model = FAMILIES[chosen]().fit(X, Y)
        sets = [nsga2(evaluator(model), 3, n_pop=N_POP, n_gen=N_GEN, seed=s * 101 + rnd) for s in SEEDS]
        cand = frame(np.vstack([r["X"][(r["G"] <= 0) & non_dominated_mask(r["F"])] for r in sets])).drop_duplicates().reset_index(drop=True)
        hv, npar = front_hv(train, ref)
        entry = {"round": rnd, "n_train": len(train), "hv_simulated_front": hv, "n_front": npar, "n_candidates": len(cand),
                 "elapsed_s": time.time() - t0}
        if rnd == MAX_ROUNDS or (rnd >= 2 and small >= 2):
            log.append(entry)
            break
        seen = set(zip(train.R_in_m.round(6), train.N, train.arrangement))
        cand = cand[[k not in seen for k in zip(cand.R_in_m.round(6), cand.N, cand.arrangement)]]
        if cand.empty:
            log.append({**entry, "note": "no new candidates"})
            break
        P = np.stack([FAMILIES[f]().fit(X, Y).predict(feats(cand)) for f in ("nn_ensemble", "xgboost", "rsm_quadratic")])
        cand = cand.assign(unc=(P.std(axis=0) / (Y.std(axis=0) + 1e-12)).max(axis=1)).sort_values("unc", ascending=False)
        z = np.column_stack([cand.R_in_m / 0.03, cand.fraction / 0.4, cand.arrangement.map({a: i for i, a in enumerate(ARR)}) / 2.0])
        sel = []
        for i in range(len(cand)):
            if all(np.linalg.norm(z[i] - z[j]) > 0.05 for j in sel):
                sel.append(i)
            if len(sel) == PER_ROUND:
                break
        sim = simulate(cid, pcm, cand.iloc[sel], f"al_round{rnd + 1}")
        if len(sim):
            train = pd.concat([train, sim], ignore_index=True)
        log.append(entry)
        hv_new, _ = front_hv(train, ref)
        small = small + 1 if (prev is not None and abs(hv_new - hv) / max(hv, 1e-9) < 0.01) else 0
        prev = hv
        print(tag, "round", rnd + 1, "hv", round(hv_new, 3), "n_train", len(train), flush=True)
        if rnd == 1:                                                                                 # vertex step
            V = np.array([[a, b, c] for a, b in itertools.product((0.0, 1.0), repeat=2) for c in (0.0, 0.5, 0.99)])
            vs = simulate(cid, pcm, frame(V).drop_duplicates().reset_index(drop=True), "vertex")
            if len(vs):
                train = pd.concat([train, vs], ignore_index=True)
            print(tag, "vertices simulated", len(vs), flush=True)
    # final: union of the three seeds' Pareto sets (thinned to THIN designs), each simulated once; per-seed hypervolume from its own members
    per_seed = {}
    for s_, res in zip(SEEDS, sets):
        ok = (res["G"] <= 0) & non_dominated_mask(res["F"])
        per_seed[s_] = frame(res["X"][ok]).drop_duplicates().reset_index(drop=True)
    union = pd.concat(list(per_seed.values())).drop_duplicates(subset=["R_in_m", "N", "arrangement"]).sort_values("R_in_m").reset_index(drop=True)
    if len(union) > THIN:
        union = union.iloc[np.linspace(0, len(union) - 1, THIN).astype(int)]
    seedf = simulate(cid, pcm, union, "final_union")
    hvs = []
    for s_, fr in per_seed.items():
        keys = set(zip(fr.R_in_m.round(6), fr.N, fr.arrangement))
        mem = seedf[[k in keys for k in zip(seedf.R_in_m.round(6), seedf.N, seedf.arrangement)]]
        hvs.append({"seed": s_, "hv": front_hv(mem, ref)[0], "n": len(mem), "n_front_surrogate": len(fr)})
    allp = pd.concat([train, seedf], ignore_index=True).drop_duplicates(subset=["R_in_m", "N", "arrangement"], keep="last")
    ok = allp[allp.feasible == True]                                                                 # noqa: E712
    front = ok[non_dominated_mask(objectives(ok))] if len(ok) else ok
    out = Path("results")
    allp.to_csv(out / f"c14_l6_points_{tag}.csv", index=False)
    front.to_csv(out / f"c14_l6_front_{tag}.csv", index=False)
    pd.DataFrame(log).to_csv(out / f"c14_l6_log_{tag}.csv", index=False)
    pd.DataFrame(hvs).assign(surrogate=chosen).to_csv(out / f"c14_l6_seeds_{tag}.csv", index=False)
    print("done", tag, f"{time.time() - t0:.0f}s", "front", len(front), "best robust gain", round(allp.g_window_mean.max(), 2), flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
