#!/usr/bin/env python3
"""
validate_sphere.py -- reproduce a PUBLISHED sphere-melting experiment with the
same OpenFOAM model used for the O2 capsule CFD, and score it against the
paper's own data.  (Improvement plan P0.1.)

Nothing in the spec is invented: every PCM property and every reference data
point must be copied from the paper (with the table/figure cited in the spec).
`null` values make the script refuse to run.

Benchmarks (2023-2026, you must supply the PDFs; see docs/AI_OPTIMISATION_PLAN_2023_2026.md Sec. 9):
  * Turski 2025, Energies -- PCM-filled capsules (RT44HC), lab-scale pilot (open access)
  * Rocha et al. 2023, Therm. Sci. Eng. Prog. -- two experimental datasets, A_mush protocol
  * Li et al. 2024, Appl. Therm. Eng. -- horizontal paraffin cylinder, Fo*Ste*Gr correlations
  * Jia et al. 2024, J. Energy Storage -- spherical capsule, 3-D vs axisymmetric, A_mush
  (Older benchmarks such as Assis 2007 / Tan 2009 are intentionally not required.)

USAGE
  1. cp validation/benchmark_template.yaml validation/assis2007.yaml
  2. Fill every `null` from the paper; digitise melt fraction vs time from the
     figures into CSV files (columns: time_s, melt_fraction) and list them.
  3. python validate_sphere.py validation/assis2007.yaml --workers 4
     python validate_sphere.py validation/assis2007.yaml --calibrate-cu   # sweep A_mush analogue

OUTPUT  results/validation_<name>.csv / .md  (+ plot if matplotlib is present)

WHAT IS COMPARED
  CFD  : mass-weighted liquid fraction of the PCM vs time (volFieldValue)
  Ref  : the digitised experimental (or the paper's numerical) curve
  Gate : |t50 error| and |t90 error| <= gate_pct (default 15 %), declared in the
         spec BEFORE running. With --calibrate-cu the Darcy constant is chosen on
         the `calibrate_on` cases and scored on the held-out `test_on` cases
         (Rocha 2023: a constant validated on one geometry failed by up to 38 %
         on another).
KNOWN MODEL DIFFERENCES vs a typical benchmark (state them in the paper)
  * No volumetric expansion, no solid sinking / close-contact melting.
  * Axisymmetric: the capsule axis is vertical, wall is isothermal.
  * Melt fraction is mass-weighted (many papers use volume-weighted).
"""
import argparse
import csv
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import make_case as mc          # noqa: E402
import run_doe as rd            # noqa: E402
import postprocess as pp        # noqa: E402

REQUIRED_PCM = ("Tm_C", "L_kJ_kg", "rho_s", "rho_l", "cp_s_J_kgK", "cp_l_J_kgK", "k_W_mK",
                "mu_Pa_s", "beta_1_K")


def _nulls(obj, path=""):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out += _nulls(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += _nulls(v, f"{path}[{i}]")
    elif obj is None:
        out.append(path)
    return out


def load_spec(path):
    spec = yaml.safe_load(open(path, encoding="utf-8"))
    nulls = _nulls(spec)
    if nulls:
        raise SystemExit("Spec still has null fields -- copy them from the paper:\n  " + "\n  ".join(nulls))
    for k in REQUIRED_PCM:
        if k not in spec["pcm"]:
            raise SystemExit(f"pcm.{k} missing")
    return spec


def read_ref(path, base):
    p = path if os.path.isabs(path) else os.path.join(base, path)
    a = np.genfromtxt(p, delimiter=",", names=True)
    return a["time_s"], a["melt_fraction"]


def first_cross(t, y, thr):
    return pp.first_crossing(np.asarray(t), np.asarray(y), thr)


def run_case(spec, case, cu, root, cell):
    pc = spec["pcm"]
    props = dict(name=pc.get("name", "benchmark_pcm"), Tm_C=pc["Tm_C"], L_kJ_kg=pc["L_kJ_kg"],
                 rho_s=pc["rho_s"], rho_l=pc["rho_l"], cp_s=pc["cp_s_J_kgK"], cp_l=pc["cp_l_J_kgK"],
                 k=pc["k_W_mK"])
    cfg = mc.load_cfg()
    cfg["numerics"]["cell_size_m"] = cell
    cid = f"{case['id']}_Cu{cu:.0e}".replace("+", "")
    cdir = os.path.join(root, cid)
    os.makedirs(cdir, exist_ok=True)
    mc.build_case(cdir, props["name"], case["d_m"], 0.0, case["wall_dT_K"], cfg=cfg,
                  bc_mode="isothermal", pcm_props=props, t_init_abs_C=case["T_init_C"],
                  t_end_h=case["t_end_s"] / 3600.0, sample_every_s=case.get("sample_every_s", 10.0),
                  overrides={"dyn_viscosity_Pa_s": pc["mu_Pa_s"], "thermal_expansion_1_K": pc["beta_1_K"],
                             "mushy_Cu": cu})
    rc, out = rd.run_in_wsl(cdir)
    if rc != 0:
        return dict(case=cid, status=f"FAILED rc={rc} {out[-120:]}")
    k = pp.extract(cdir, window_h=case["t_end_s"] / 3600.0, do_greybox=False)
    ma = pp.read_dat(os.path.join(cdir, "postProcessing", "meltAndTemp", "0", "volFieldValue.dat"))
    return dict(case=cid, status="ok", t=ma[:, 0], f=np.clip(ma[:, 2], 0, 1), qc=k["qc_energy_ok"],
                resid=k["energy_residual_pct"])


def score(res, ref_t, ref_f, gate):
    t, f = res["t"], res["f"]
    out = {}
    for thr in (0.5, 0.9):
        tc, tr = first_cross(t, f, thr), first_cross(ref_t, ref_f, thr)
        out[f"t{int(thr*100)}_cfd_s"] = tc
        out[f"t{int(thr*100)}_ref_s"] = tr
        out[f"t{int(thr*100)}_err_pct"] = 100.0 * (tc - tr) / tr if np.isfinite(tc) and np.isfinite(tr) and tr > 0 else np.nan
    n = np.interp(ref_t, t, f)
    out["rmse_f"] = float(np.sqrt(np.mean((n - ref_f) ** 2)))
    out["max_abs_f"] = float(np.max(np.abs(n - ref_f)))
    errs = [abs(out["t50_err_pct"]), abs(out["t90_err_pct"])]
    out["pass_gate"] = bool(all(np.isfinite(errs)) and max(errs) <= gate)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--cell-size", type=float, default=0.001)
    ap.add_argument("--calibrate-cu", action="store_true")
    a = ap.parse_args()

    spec = load_spec(a.spec)
    base = os.path.dirname(os.path.abspath(a.spec))
    name = spec["name"]
    gate = float(spec["gate_pct"])
    cu_list = [float(x) for x in spec.get("cu_sweep", [1e5])] if a.calibrate_cu else [1e5]
    root = os.path.join(ROOT, "cases_validation", name)

    jobs = [(c, cu) for c in spec["cases"] for cu in cu_list]
    print(f"[{name}] {len(jobs)} runs ({len(spec['cases'])} cases x {len(cu_list)} Cu), cell {a.cell_size} m")
    t0 = time.time()
    results = {}
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(run_case, spec, c, cu, root, a.cell_size): (c, cu) for c, cu in jobs}
        for fu in futs:
            c, cu = futs[fu]
            results[(c["id"], cu)] = fu.result()
            print(f"  {c['id']:18s} Cu={cu:8.0e} {results[(c['id'], cu)]['status']}", flush=True)

    rows = []
    for (cid, cu), r in results.items():
        c = next(x for x in spec["cases"] if x["id"] == cid)
        row = dict(case=cid, Cu=cu, d_m=c["d_m"], wall_dT_K=c["wall_dT_K"], role=c.get("role", "test"),
                   status=r["status"])
        if r["status"] == "ok":
            rt, rf = read_ref(c["reference_csv"], base)
            row.update(score(r, rt, rf, gate))
            row["qc_energy_ok"] = r["qc"]
            row["energy_residual_pct"] = r["resid"]
        rows.append(row)

    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    out_csv = os.path.join(ROOT, "results", f"validation_{name}.csv")
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)

    # calibrate on `calibrate_on`, report on the held-out cases
    lines = [f"# Validation: {spec.get('citation', name)}", "",
             f"Gate: |t50| and |t90| error <= {gate:.0f} %, mesh {a.cell_size*1e3:.1f} mm.", ""]
    ok = [r for r in rows if r["status"] == "ok"]
    if a.calibrate_cu and ok:
        best, best_e = None, 1e9
        for cu in cu_list:
            cal = [r for r in ok if r["Cu"] == cu and r["role"] == "calibrate"]
            if not cal:
                continue
            e = np.nanmean([max(abs(r["t50_err_pct"]), abs(r["t90_err_pct"])) for r in cal])
            lines.append(f"- Cu = {cu:.0e}: mean calibration error {e:.1f} %")
            if e < best_e:
                best, best_e = cu, e
        lines.append(f"\n**Chosen Cu = {best:.0e}** (calibration error {best_e:.1f} %).\n")
        test = [r for r in ok if r["Cu"] == best and r["role"] == "test"]
        lines.append("Held-out cases:")
        for r in test:
            lines.append(f"- {r['case']}: t50 {r['t50_err_pct']:+.1f} %, t90 {r['t90_err_pct']:+.1f} %, "
                         f"RMSE(f) {r['rmse_f']:.3f}  -> {'PASS' if r['pass_gate'] else 'FAIL'}")
        verdict = "PASS" if test and all(r["pass_gate"] for r in test) else "FAIL"
    else:
        lines.append("| case | d [mm] | wall dT [K] | t50 err | t90 err | RMSE(f) | gate |")
        lines.append("|---|---|---|---|---|---|---|")
        for r in ok:
            lines.append(f"| {r['case']} | {r['d_m']*1e3:.0f} | {r['wall_dT_K']:.0f} | "
                         f"{r['t50_err_pct']:+.1f} % | {r['t90_err_pct']:+.1f} % | {r['rmse_f']:.3f} | "
                         f"{'PASS' if r['pass_gate'] else 'FAIL'} |")
        verdict = "PASS" if ok and all(r["pass_gate"] for r in ok) else "FAIL"
    lines.append(f"\n**Overall: {verdict}**")
    open(os.path.join(ROOT, "results", f"validation_{name}.md"), "w", encoding="utf-8").write("\n".join(lines))
    print("\n".join(lines))
    print(f"\nwrote {out_csv}  ({(time.time()-t0)/60:.1f} min)")


if __name__ == "__main__":
    main()
