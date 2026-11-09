"""
scripts/g9_assess.py
=======================
G9 assessment (plan WP5 acceptance, WP6 band). Reads the S4/S5/S6 outputs and writes
  results/wp6_band.csv           repeatability band per objective (and per regime)
  results/g9_seed_stability.csv  per-pair hypervolume of each seed's SIMULATED front vs the band
  results/g9_al_summary.csv      active-learning trajectory per pair
  results/g9_grid_check.csv      NSGA-II/AL front vs the dense-grid front (epsilon indicator vs the band)
  results/g9_boundary_check.csv  share of final-front designs sitting at a bound (boundary-artefact detector)

Band definition (documented choice): band_k = sqrt( (sd_year,k / sqrt(5))^2 + d_dt,k^2 + d_nodes,k^2 + d_prop,k^2 )
 sd_year  mean over measured designs of the per-year sd of the paired gain (standard error of a 5-year mean)
 d_dt     RMS change of the 5-year paired gain when dt goes 150 s -> 75 s
 d_nodes  RMS change when N goes 10 -> 20
 d_prop   largest RMS change over latent heat +-10 % and conductivity +-20 %
Objectives are g_window [kWh/yr], g_annual [kWh/yr], d_overheat [h/yr].
"""

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.optimize.nsga2 import additive_epsilon, hypervolume, non_dominated_mask

OUT = Path("results")
OBJ = ["g_window", "g_annual", "d_overheat"]


def src(name, tag):
    """Use the extended (more AL rounds, warm start) file for a pair when one exists; the original stays on disk."""
    for suf in ("_ext2", "_ext"):
        ext = OUT / f"{name}_{tag}{suf}.csv"
        if ext.exists():
            return ext
    return OUT / f"{name}_{tag}.csv"


def F_of(df):
    return np.column_stack([-df["g_window"], -df["g_annual"], df["d_overheat"]])


def band_table():
    b = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(OUT / "g9_band_r*.csv")))])
    rows = []
    for scope, g in [("all", b)] + [(f"r{r}", d) for r, d in b.groupby("regime")]:
        for o in OBJ:
            go = g[g.objective == o]
            base = go[go.variant == "base"]
            sd_year = float(base.year_sd.mean() / np.sqrt(5))
            rms = lambda names: float(np.sqrt((go[go.variant.isin(names)].delta ** 2).mean()))  # noqa: E731
            d_dt, d_nodes = rms(["dt75"]), rms(["nodes20"])
            d_prop = max(rms(["latent-10", "latent+10"]), rms(["cond-20", "cond+20"]))
            rows.append({"scope": scope, "objective": o, "sd_year_se": sd_year, "d_dt": d_dt, "d_nodes": d_nodes,
                         "d_prop": d_prop, "band": float(np.sqrt(sd_year ** 2 + d_dt ** 2 + d_nodes ** 2 + d_prop ** 2)),
                         "n_designs": int(base.shape[0])})
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "wp6_band.csv", index=False)
    return t


def main():
    band = band_table()
    bv = band[band.scope == "all"].set_index("objective").band.reindex(OBJ).to_numpy()
    print("band (all regimes):", dict(zip(OBJ, bv.round(3))))

    seed_rows, al_rows, bound_rows = [], [], []
    for f in [f for f in sorted(glob.glob(str(OUT / "g9_points_r*_p*.csv"))) if not f.endswith(("_ext.csv", "_ext2.csv"))]:
        tag = Path(f).stem.replace("g9_points_", "")
        pts = pd.read_csv(f)
        ref_row = pd.read_csv(src("g9_ref", tag)).iloc[0]
        ref = np.array([-ref_row.ref_g_window, -ref_row.ref_g_annual, ref_row.ref_d_overheat])
        sf = pd.read_csv(src("g9_seed_front", tag))
        hvs = {}
        for s, g in sf.groupby("seed"):
            ok = g[g.feasible == True]  # noqa: E712
            F = F_of(ok)
            hvs[s] = hypervolume(F[non_dominated_mask(F)], ref) if len(ok) else 0.0
        allok = sf[sf.feasible == True]  # noqa: E712
        Fall = F_of(allok)
        Fm = Fall[non_dominated_mask(Fall)]
        hv_ref = hypervolume(Fm, ref)
        hv_band = abs(hv_ref - hypervolume(Fm + bv, ref))          # hypervolume lost if every objective got worse by the band
        spread = max(hvs.values()) - min(hvs.values())
        seed_rows.append({"pair": tag, **{f"hv_seed{s}": v for s, v in hvs.items()}, "hv_spread": spread,
                          "hv_union": hv_ref, "hv_band": hv_band, "spread_within_band": bool(spread <= hv_band),
                          "feasible_fraction_final": float(sf.feasible.mean())})
        lg = pd.read_csv(src("g9_al_log", tag))
        al_rows.append({"pair": tag, "rounds": int(lg["round"].max()), "n_train_final": int(lg.n_train.max()),
                        "hv_first": float(lg.hv_simulated_front.iloc[0]), "hv_last": float(lg.hv_simulated_front.iloc[-1]),
                        "hv_gain_pct": 100 * (lg.hv_simulated_front.iloc[-1] / lg.hv_simulated_front.iloc[0] - 1),
                        "mean_abs_err_g_annual_first_round": float(lg.mean_abs_err_g_annual.dropna().iloc[0]) if lg.mean_abs_err_g_annual.notna().any() else np.nan,
                        "mean_abs_err_tpcm_first_round": float(lg.mean_abs_err_tpcm.dropna().iloc[0]) if lg.mean_abs_err_tpcm.notna().any() else np.nan})
        # boundary-artefact detector on the final front (feasible, non-dominated among ALL simulated points)
        ok = pts[pts.feasible == True]  # noqa: E712
        front = ok[non_dominated_mask(F_of(ok))]
        for name, mask in {
            "R_in at 10 mm end (<=11 mm)": front.R_in_m <= 0.011, "R_in at 40 mm end (>=39 mm)": front.R_in_m >= 0.039,
            "fraction at 2 % floor (<=2.5 %)": front.fraction <= 0.025, "fraction at 30 % cap (>=29.5 %)": front.fraction >= 0.295,
            "flow at 0.010 floor (<=0.0125)  [MODEL ARTEFACT]": front.flow <= 0.0125,
            "flow at 0.050 cap (>=0.0475)": front.flow >= 0.0475}.items():
            bound_rows.append({"pair": tag, "bound": name, "share_of_front": float(mask.mean()), "n_front": len(front)})
    pd.DataFrame(seed_rows).to_csv(OUT / "g9_seed_stability.csv", index=False)
    pd.DataFrame(al_rows).to_csv(OUT / "g9_al_summary.csv", index=False)
    pd.DataFrame(bound_rows).to_csv(OUT / "g9_boundary_check.csv", index=False)

    grid_rows = []
    for f in sorted(glob.glob(str(OUT / "g9_s6_grid_r*_p1.csv"))):
        tag = Path(f).stem.replace("g9_s6_grid_", "")
        g = pd.read_csv(f)
        gok = g[(g.status == "ok") & (g.feasible == True)]  # noqa: E712
        if len(gok) == 0:
            continue
        Fg_all = F_of(gok)
        Fg = Fg_all[non_dominated_mask(Fg_all)]
        pts = pd.read_csv(src("g9_points", tag))
        pok = pts[pts.feasible == True]  # noqa: E712
        Fp_all = F_of(pok)
        Fp = Fp_all[non_dominated_mask(Fp_all)]
        ref = np.maximum(Fg_all.max(axis=0), Fp_all.max(axis=0))
        ref = ref + 0.05 * (ref - np.minimum(Fg_all.min(axis=0), Fp_all.min(axis=0)))
        eps, worst = additive_epsilon(Fp, Fg)          # does our front cover the grid front?
        grid_rows.append({"pair": tag, "n_grid_ok": len(g[g.status == "ok"]), "n_grid_rejected": int((g.status == "geometry_rejected").sum()),
                          "n_grid_feasible": len(gok), "n_grid_front": len(Fg), "n_final_front": len(Fp),
                          "hv_grid": hypervolume(Fg, ref), "hv_final": hypervolume(Fp, ref),
                          "hv_ratio_final_over_grid": hypervolume(Fp, ref) / hypervolume(Fg, ref),
                          "eps_g_window": -worst[0] if False else worst[0], "eps_g_annual": worst[1], "eps_d_overheat": worst[2],
                          "band_g_window": bv[0], "band_g_annual": bv[1], "band_d_overheat": bv[2],
                          "within_band": bool(np.all(worst <= bv))})
    pd.DataFrame(grid_rows).to_csv(OUT / "g9_grid_check.csv", index=False)
    for name in ("g9_seed_stability", "g9_al_summary", "g9_grid_check", "g9_boundary_check"):
        print("\n", name); print(pd.read_csv(OUT / f"{name}.csv").round(3).to_string(index=False))


if __name__ == "__main__":
    main()
