#!/usr/bin/env python3
"""
run_doe.py -- generate, run (in parallel, via WSL) and collect capsule CFD cases.

Modes
-----
  doe          Latin-hypercube over (d, mdot, dT) for each shortlisted PCM
  mesh         mesh-independence study at one reference design (3 meshes)
  sens         sensitivity of the ASSUMED liquid properties (mu, beta, Cu)
  conduction   pure-conduction twin (g=0) of every DOE case  -> convection gain
  all          mesh + sens + doe + conduction

Resumable: a case with kpi.json is skipped unless --force.

Examples (Windows PowerShell, from openfoam_cfd/scripts):
  python run_doe.py --mode mesh
  python run_doe.py --mode doe --n-per-pcm 16 --workers 8
  python run_doe.py --mode all  --workers 8
"""
import argparse
import csv
import json
import math
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import make_case as mc                      # noqa: E402
import postprocess as pp                    # noqa: E402

DISTRO = "Ubuntu-24.04"
IS_WIN = platform.system() == "Windows"


def to_wsl_path(p):
    p = os.path.abspath(p).replace("\\", "/")
    if len(p) > 1 and p[1] == ":":
        return f"/mnt/{p[0].lower()}{p[2:]}"
    return p


def run_in_wsl(case_dir):
    """Run scripts/run_one.sh on one case. Returns (rc, stdout)."""
    script = to_wsl_path(os.path.join(HERE, "run_one.sh")) if IS_WIN else os.path.join(HERE, "run_one.sh")
    cdir = to_wsl_path(case_dir) if IS_WIN else case_dir
    cmd = f"bash '{script}' '{cdir}'"
    argv = ["wsl", "-d", DISTRO, "-e", "bash", "-lc", cmd] if IS_WIN else ["bash", "-lc", cmd]
    for attempt in range(3):          # transient WSL launch failures under heavy parallel load
        r = subprocess.run(argv, capture_output=True, text=True, errors="replace")
        out = "\n".join(l for l in r.stdout.splitlines() if l.strip())
        if r.returncode == 0 or out:   # a real solver/mesh outcome (has output) is not retried
            break
        time.sleep(5 + 5 * attempt)
    if r.returncode != 0 and not out:
        out = "stderr: " + " ".join(l for l in r.stderr.splitlines()
                                    if "Failed to translate" not in l)[-300:]
    return r.returncode, out


def lhs(n, bounds, seed):
    from scipy.stats import qmc
    s = qmc.LatinHypercube(d=len(bounds), seed=seed).random(n)
    lo = np.array([b[0] for b in bounds])
    hi = np.array([b[1] for b in bounds])
    return lo + s * (hi - lo)


def one_case(job, cfg, batch_dir, force, window_h):
    cid = job["id"]
    cdir = os.path.join(batch_dir, cid)
    kpi_path = os.path.join(cdir, "kpi.json")
    if os.path.exists(kpi_path) and not force:
        return cid, "cached", json.load(open(kpi_path))
    os.makedirs(cdir, exist_ok=True)
    mc.build_case(cdir, job["pcm"], job["d"], job["mdot"], job["dT"], cfg=cfg,
                  tank_volume_L=job.get("tank_L"), conduction_only=job.get("conduction_only", False),
                  overrides=job.get("overrides"), cell_size_m=job.get("cell"),
                  t_end_h=job.get("t_end_h"))
    t0 = time.time()
    rc, out = run_in_wsl(cdir)
    if rc != 0:
        return cid, f"FAILED rc={rc} {out[-200:]}", None
    try:
        k = pp.extract(cdir, window_h=window_h, do_greybox=not job.get("conduction_only", False))
    except Exception as ex:
        return cid, f"POSTPROC FAILED {ex!r}", None
    k["wall_s"] = round(time.time() - t0, 1)
    k.update({kk: vv for kk, vv in job.items() if kk in ("tag", "cell", "overrides")})
    json.dump(k, open(kpi_path, "w"), indent=2)
    return cid, "ok", k


def execute(jobs, cfg, batch_dir, workers, force, window_h):
    rows, t0 = [], time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(one_case, j, cfg, batch_dir, force, window_h) for j in jobs]
        for i, f in enumerate(as_completed(futs), 1):
            cid, status, k = f.result()
            el = (time.time() - t0) / 60
            print(f"[{i:3d}/{len(jobs)}] {cid:42s} {status:10s} ({el:5.1f} min)", flush=True)
            if k:
                rows.append(k)
    return rows


def write_csv(rows, path):
    if not rows:
        return
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in r.items()})
    print("wrote", path, f"({len(rows)} rows)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=["doe", "mesh", "sens", "conduction", "all"], default="doe")
    ap.add_argument("--n-per-pcm", type=int, default=16)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=20261015)
    ap.add_argument("--tank-L", type=float, default=None,
                    help="tank volume used to turn flow into h (50 frozen, 112.5 = IS 12976 Case A)")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--config", default=mc.DEFAULT_CFG)
    ap.add_argument("--out", default=None, help="case root (default cases/ or cases_<tag>/)")
    ap.add_argument("--tag", default="", help="suffix for result files and case dir, e.g. 'fine'")
    ap.add_argument("--cell-size", type=float, default=None,
                    help="override numerics.cell_size_m (e.g. 0.0008 for the fine-mesh DOE)")
    a = ap.parse_args()
    suffix = f"_{a.tag}" if a.tag else ""
    if a.out is None:
        a.out = os.path.join(ROOT, f"cases_{a.tag}" if a.tag else "cases")

    cfg = mc.load_cfg(a.config)
    if a.cell_size:
        cfg["numerics"]["cell_size_m"] = float(a.cell_size)
    ds = cfg["design_space"]
    window_h = cfg["scenario"]["charge_window_h"]
    pcms = cfg["pcm_shortlist"]
    jobs_by_batch = {}

    if a.mode in ("mesh", "all"):
        ref = dict(pcm=pcms[0], d=0.06, mdot=0.03, dT=15.0)
        jobs_by_batch["mesh"] = [dict(id=f"mesh_{round(c * 1e4):03d}", tag="mesh", cell=c, **ref)
                                 for c in (0.0020, 0.0012, 0.0008)]
    if a.mode in ("sens", "all"):
        ref = dict(pcm=pcms[0], d=0.06, mdot=0.03, dT=15.0)
        v = []
        for nm, base, fac in (("mu", cfg["assumed_liquid_properties"]["dyn_viscosity_Pa_s"], (0.5, 2.0)),
                              ("beta", cfg["assumed_liquid_properties"]["thermal_expansion_1_K"], (0.5, 2.0)),
                              ("Cu", cfg["assumed_liquid_properties"]["mushy_Cu"], (0.1, 10.0))):
            key = {"mu": "dyn_viscosity_Pa_s", "beta": "thermal_expansion_1_K", "Cu": "mushy_Cu"}[nm]
            for f in fac:
                v.append(dict(id=f"sens_{nm}_x{f:g}", tag=f"sens_{nm}_x{f:g}",
                              overrides={key: float(base) * f}, **ref))
        jobs_by_batch["sens"] = v
    if a.mode in ("doe", "conduction", "all"):
        b = [(ds["capsule_diameter_m"]["min"], ds["capsule_diameter_m"]["max"]),
             (ds["flow_rate_kg_s"]["min"], ds["flow_rate_kg_s"]["max"]),
             (ds["dT_drive_K"]["min"], ds["dT_drive_K"]["max"])]
        doe, cond = [], []
        t_water_max = 72.0           # [FROZEN] safety_shield.bypass_water_C
        for pi, pcm in enumerate(pcms):
            tm = mc.load_pcm(cfg, pcm)["Tm_C"]
            bb = list(b)
            bb[2] = (b[2][0], min(b[2][1], t_water_max - tm))   # hot water may not exceed the shield limit
            X = lhs(a.n_per_pcm, bb, a.seed + pi)
            for i, (d, md, dT) in enumerate(X):
                tag = f"p{pi}_{i:02d}"
                base = dict(pcm=pcm, d=float(d), mdot=float(md), dT=float(dT), tank_L=a.tank_L)
                doe.append(dict(id=f"doe_{tag}", tag="doe", **base))
                cond.append(dict(id=f"cond_{tag}", tag="cond", conduction_only=True, **base))
        if a.mode in ("doe", "all"):
            jobs_by_batch["doe"] = doe
        if a.mode in ("conduction", "all"):
            jobs_by_batch["conduction"] = cond

    allrows = {}
    for batch, jobs in jobs_by_batch.items():
        print(f"\n=== batch '{batch}': {len(jobs)} cases, {a.workers} workers ===", flush=True)
        rows = execute(jobs, cfg, os.path.join(a.out, batch), a.workers, a.force, window_h)
        write_csv(rows, os.path.join(ROOT, "results", f"cfd_{batch}_results{suffix}.csv"))
        allrows[batch] = rows

    # convection gain: conduction-only melt time / full-physics melt time
    if "doe" in allrows and "conduction" in allrows:
        cmap = {r["case"].replace("cond_", ""): r for r in allrows["conduction"]}
        out = []
        for r in allrows["doe"]:
            c = cmap.get(r["case"].replace("doe_", ""))
            if c and np.isfinite(r["t_melt_90_s"]) and np.isfinite(c["t_melt_90_s"]):
                out.append(dict(case=r["case"], pcm=r["pcm"], d_m=r["d_m"], mdot_kg_s=r["mdot_kg_s"],
                                dT_K=r["dT_K"], t90_cfd_s=r["t_melt_90_s"], t90_conduction_s=c["t_melt_90_s"],
                                convection_gain=c["t_melt_90_s"] / r["t_melt_90_s"]))
        write_csv(out, os.path.join(ROOT, "results", f"cfd_convection_gain{suffix}.csv"))


if __name__ == "__main__":
    main()
