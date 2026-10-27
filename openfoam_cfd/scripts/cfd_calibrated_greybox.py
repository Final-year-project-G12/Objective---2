#!/usr/bin/env python3
"""
cfd_calibrated_greybox.py -- feed the OpenFOAM capsule results back into the
project's Objective-2 optimisation and ask: does CFD change the answer?

PIPELINE (multi-fidelity, the structure Barqawi 2025 / Eldokaishi 2022 use,
with CFD as the high-fidelity tier):

  1. CFD DOE (results/cfd_doe_results.csv) gives, per capsule design, the scale
     phi on the grey-box PCM resistance R_pcm = phi * r/(5 k_eff) that makes
     the lumped model reproduce the CFD 90 % melt time  (postprocess.py).
  2. An ExtraTrees surrogate phi(d, mdot, dT, Tm, L, k) is fitted
     (same model family as the project's Phase 6).
  3. The project's own annual simulator (src/simulation/run_case.py) is run
     twice on the SAME Phase-5 designs: frozen closure (phi = 1) and
     CFD-calibrated closure (phi from step 2). Nothing in src/ is edited:
     the capsule conductance function is replaced in memory only.
  4. Paired comparison -> does the ranking, the best design or the
     PCM-vs-plain-tank margin move?  (the honest answer may be "no": the
     project's own G0 analysis says heat transfer is not the bottleneck.)
  5. AI step: ExtraTrees on the calibrated annual results, random search over
     the constrained design space (src.design.constraints.check_design), top-k
     re-confirmed in the calibrated simulator -> recommendation table.

Run (from openfoam_cfd/scripts, project venv):
  python cfd_calibrated_greybox.py --workers 6
"""
import argparse
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import _paths                                   # noqa: E402
PROJ = _paths.project_root()
sys.path.insert(0, PROJ)

STATE = "rajasthan"
# Phase-7 deployable PCM per regime (results/phase7_deployable_design_per_regime.csv)
PAIRS = [(0, "RT44HC"), (1, "savE® OM49"), (2, "Lauric acid (C12)")]
DT_REF_K = 15.0          # representative charging excess temperature for phi lookup

_G = {}                  # per-process globals: phi value for the case being run


# ---------------------------------------------------------------------------
def fit_phi_model(cfd_csv):
    from sklearn.ensemble import ExtraTreesRegressor
    import make_case as mc
    cfg = mc.load_cfg()
    df = pd.read_csv(cfd_csv)
    df = df[(df.qc_energy_ok == True) & np.isfinite(df["R_pcm_scale_equivalent"])]  # noqa: E712
    if len(df) < 6:
        raise SystemExit(f"only {len(df)} usable CFD rows in {cfd_csv}; run the DOE first")
    props = {n: mc.load_pcm(cfg, n) for n in df.pcm.unique()}
    X = np.array([[r.d_m, r.mdot_kg_s, r.dT_K, props[r.pcm]["Tm_C"], props[r.pcm]["L_kJ_kg"],
                   props[r.pcm]["k"]] for r in df.itertuples()])
    y = np.log(df["R_pcm_scale_equivalent"].values)
    m = ExtraTreesRegressor(n_estimators=400, min_samples_leaf=1, random_state=7).fit(X, y)
    return m, props, df


def phi_for(model, props, pcm, d, mdot, dT=DT_REF_K):
    p = props[pcm]
    x = np.array([[d, mdot, dT, p["Tm_C"], p["L_kJ_kg"], p["k"]]])
    return float(np.exp(model.predict(x)[0]))


# ---------------------------------------------------------------------------
def _worker_init(patch):
    """Replace the capsule conductance in tank_model by a phi-scaled copy."""
    import src.simulation.tank_model as tm
    from src.simulation.capsule_enthalpy import effective_conductivity_W_mK
    from src.simulation.heat_transfer import water_side_htc_w_m2k
    if not patch:
        return

    def ua_eff_total_w_k(n_capsule, capsule_diameter_m, capsule_area_m2, superficial_velocity_m_s,
                         pcm_props, f_melt, system_config):
        if n_capsule <= 0:
            return 0.0
        integ = system_config["pcm_integration"]
        h_w = water_side_htc_w_m2k(superficial_velocity_m_s, capsule_diameter_m, system_config)
        r_conv = 1.0 / (h_w * capsule_area_m2) if h_w > 0 else float("inf")
        r_wall = integ["capsule_wall_thickness_m"] / (integ["capsule_wall_conductivity_W_mK"] * capsule_area_m2)
        k_eff = effective_conductivity_W_mK(pcm_props, f_melt, integ["liquid_convection_enhancement"])
        r_pcm = _G.get("phi", 1.0) * (capsule_diameter_m / 2.0) / (5.0 * k_eff * capsule_area_m2)
        return n_capsule / (r_conv + r_wall + r_pcm)

    tm.ua_eff_total_w_k = ua_eff_total_w_k


def _run_job(job):
    from src.design.schema import DesignVector
    from src.simulation.run_case import run_case
    _G["phi"] = job.get("phi", 1.0)
    dv = DesignVector(job["d"], int(job["n"]), job["mdot"], job["arr"])
    t0 = time.time()
    out = run_case(STATE, job["regime"], job["pcm"], dv, record_hourly=False)
    m = out["metrics"]
    row = dict(job_id=job["job_id"], regime=job["regime"], pcm=job["pcm"], d=job["d"], n=job["n"],
               mdot=job["mdot"], arr=job["arr"], phi=job.get("phi", 1.0), variant=job["variant"],
               valid=out["valid"], reason=out["reason"], wall_s=round(time.time() - t0, 1))
    if m:
        row.update({k: m[k] for k in ("useful_energy_kWh", "solar_fraction", "max_pcm_temp_C",
                                      "max_water_temp_C", "n_safety_violations", "complete_melt_cycles",
                                      "pump_energy_kWh", "pcm_mass_kg", "final_f_melt")
                    if k in m})
        row["pcm_vol_frac"] = out["geometry"].get("pcm_volume_fraction")
    return row


def run_jobs(jobs, workers, patch):
    rows = []
    with ProcessPoolExecutor(max_workers=workers, initializer=_worker_init, initargs=(patch,)) as ex:
        for i, r in enumerate(ex.map(_run_job, jobs, chunksize=1), 1):
            rows.append(r)
            if i % 10 == 0 or i == len(jobs):
                print(f"  {i}/{len(jobs)} done", flush=True)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cfd-csv", default=os.path.join(ROOT, "results", "cfd_doe_results.csv"))
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--n-candidates", type=int, default=6000)
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--seed", type=int, default=20261015)
    a = ap.parse_args()
    outdir = os.path.join(ROOT, "results")
    os.makedirs(outdir, exist_ok=True)

    print("[1/5] fitting phi(d, mdot, dT, pcm) from CFD ...")
    phi_model, props, cfd = fit_phi_model(a.cfd_csv)
    print(f"      {len(cfd)} CFD cases; phi range {cfd.R_pcm_scale_equivalent.min():.2f}"
          f" - {cfd.R_pcm_scale_equivalent.max():.2f}, median {cfd.R_pcm_scale_equivalent.median():.2f}")

    # ---- paired re-simulation of the project's own Phase-5 designs ----------
    p5 = pd.read_csv(os.path.join(PROJ, "results", "phase5_design_cases.csv"))
    p5 = p5[p5.valid == True]                                                   # noqa: E712
    jobs, jid = [], 0
    for reg, pcm in PAIRS:
        sub = p5[(p5.regime_id == reg) & (p5.pcm_id == pcm)]
        for r in sub.itertuples():
            base = dict(regime=reg, pcm=pcm, d=r.capsule_diameter_m, n=int(r.n_capsule),
                        mdot=r.flow_rate_kg_s, arr=r.arrangement)
            phi = phi_for(phi_model, props, pcm, base["d"], base["mdot"])
            jobs.append(dict(job_id=jid, variant="frozen", phi=1.0, **base)); jid += 1
            jobs.append(dict(job_id=jid, variant="cfd", phi=phi, **base)); jid += 1
    print(f"[2/5] annual grey-box runs: {len(jobs)} (frozen + CFD-calibrated, paired) ...")
    res = run_jobs(jobs, a.workers, patch=True)
    res.to_csv(os.path.join(outdir, "o2_cfd_paired_annual.csv"), index=False)

    # ---- plain-tank reference (no PCM, closure irrelevant) -------------------
    from src.design.schema import DesignVector
    from src.simulation.run_case import run_case
    plain = {}
    for reg, _ in PAIRS:
        m = run_case(STATE, reg, None, DesignVector(0.08, 8, 0.03, "staggered"), record_hourly=False)["metrics"]
        plain[reg] = m["useful_energy_kWh"]

    # ---- paired comparison ----------------------------------------------------
    from scipy.stats import spearmanr
    lines = ["# CFD-calibrated vs frozen grey-box (paired, same Phase-5 designs)\n"]
    summ = []
    for reg, pcm in PAIRS:
        w = res[(res.regime == reg) & (res.pcm == pcm) & (res.valid == True)]          # noqa: E712
        fz = w[w.variant == "frozen"].set_index(["d", "n", "mdot", "arr"])
        cf = w[w.variant == "cfd"].set_index(["d", "n", "mdot", "arr"])
        j = fz.join(cf, lsuffix="_fz", rsuffix="_cfd", how="inner")
        if j.empty:
            continue
        rho = spearmanr(j.useful_energy_kWh_fz, j.useful_energy_kWh_cfd).correlation
        dE = (j.useful_energy_kWh_cfd - j.useful_energy_kWh_fz)
        bf, bc = j.useful_energy_kWh_fz.idxmax(), j.useful_energy_kWh_cfd.idxmax()
        summ.append(dict(regime=reg, pcm=pcm, n=len(j), spearman=rho,
                         mean_dE_kWh=dE.mean(), max_abs_dE_kWh=dE.abs().max(),
                         mean_dE_pct=100 * (dE / j.useful_energy_kWh_fz).mean(),
                         best_frozen=bf, best_cfd=bc, same_best=(bf == bc),
                         best_frozen_E=j.useful_energy_kWh_fz.max(), best_cfd_E=j.useful_energy_kWh_cfd.max(),
                         plain_tank_E=plain[reg],
                         margin_vs_plain_frozen_pct=100 * (j.useful_energy_kWh_fz.max() / plain[reg] - 1),
                         margin_vs_plain_cfd_pct=100 * (j.useful_energy_kWh_cfd.max() / plain[reg] - 1),
                         phi_mean=j.phi_cfd.mean()))
    S = pd.DataFrame(summ)
    S.to_csv(os.path.join(outdir, "o2_cfd_paired_summary.csv"), index=False)
    print(S.round(4).to_string())

    # ---- AI step: surrogate + constrained search + confirmation ---------------
    from sklearn.ensemble import ExtraTreesRegressor
    from src.design.constraints import check_design
    from src.io_utils import load_system_config, load_design_bounds
    sc, db = load_system_config(), load_design_bounds()
    rng = np.random.default_rng(a.seed)
    arrs = list(db["capsule_arrangement"])
    cal = res[(res.variant == "cfd") & (res.valid == True)]                             # noqa: E712
    recs = []
    for reg, pcm in PAIRS:
        w = cal[(cal.regime == reg) & (cal.pcm == pcm)]
        if len(w) < 12:
            continue
        enc = lambda df: np.column_stack([df.d, df.n, df.mdot, [arrs.index(x) for x in df.arr]])   # noqa: E731
        sur = ExtraTreesRegressor(n_estimators=500, random_state=11).fit(enc(w), w.useful_energy_kWh)
        cand, tries = [], 0
        from src.design.schema import DesignVector as DV
        while len(cand) < a.n_candidates and tries < a.n_candidates * 6:
            tries += 1
            d = rng.uniform(db["capsule_diameter_m"]["min"], db["capsule_diameter_m"]["max"])
            n = int(rng.integers(db["capsule_count"]["min"], db["capsule_count"]["max"] + 1))
            md = rng.uniform(db["flow_rate_kg_s"]["min"], db["flow_rate_kg_s"]["max"])
            ar = arrs[int(rng.integers(0, len(arrs)))]
            if check_design(DV(d, n, md, ar), sc, db)["valid"]:
                cand.append((d, n, md, ar))
        C = pd.DataFrame(cand, columns=["d", "n", "mdot", "arr"])
        C["pred"] = sur.predict(enc(C))
        top = C.sort_values("pred", ascending=False).head(a.top_k)
        cj = []
        for t in top.itertuples():
            phi = phi_for(phi_model, props, pcm, t.d, t.mdot)
            cj.append(dict(job_id=10_000 + len(cj), variant="confirm_cfd", phi=phi, regime=reg, pcm=pcm,
                           d=t.d, n=t.n, mdot=t.mdot, arr=t.arr))
        conf = run_jobs(cj, min(a.workers, len(cj)), patch=True)
        conf["pred_useful_energy_kWh"] = top.pred.values
        conf["plain_tank_E"] = plain[reg]
        conf["vs_plain_pct"] = 100 * (conf.useful_energy_kWh / plain[reg] - 1)
        recs.append(conf)
    if recs:
        R = pd.concat(recs)
        R.to_csv(os.path.join(outdir, "o2_cfd_calibrated_recommendation.csv"), index=False)
        print("\nCFD-calibrated recommendations (confirmed in simulator):")
        print(R[["regime", "pcm", "d", "n", "mdot", "arr", "phi", "useful_energy_kWh",
                 "pred_useful_energy_kWh", "vs_plain_pct", "max_pcm_temp_C"]].round(4).to_string(index=False))

    with open(os.path.join(outdir, "o2_cfd_paired_summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        try:
            f.write(S.round(4).to_markdown(index=False))
        except Exception:                      # tabulate not installed
            f.write(S.round(4).to_string(index=False))
        f.write("\n")
    print("\nDone. Files in", outdir)


if __name__ == "__main__":
    main()
