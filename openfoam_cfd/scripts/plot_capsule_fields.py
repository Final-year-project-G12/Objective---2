#!/usr/bin/env python3
"""
plot_capsule_fields.py -- quick-look images of a --viz capsule case WITHOUT ParaView.

  python plot_capsule_fields.py ../cases_viz/rt44_d060 --times 0 300 600 1200 1800 2400

Reads cell centres (computed once with OpenFOAM's writeCellCentres in WSL), the liquid
fraction  solidificationMeltingSource1:alpha1  and temperature T from the written time
directories, mirrors the axisymmetric half-disk, and writes
<case>/snapshots_liquid_fraction.png  and  snapshots_temperature.png.

Gravity points along -x in these cases, so the vertical axis is the capsule axis with "up" = +x.
"""
import argparse
import os
import re
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np


def wsl(p):
    p = os.path.abspath(p).replace("\\", "/")
    return f"/mnt/{p[0].lower()}{p[2:]}"


def ensure_centres(case):
    """OpenFOAM v2406 rejects paths containing spaces, so run on a copy in the Linux home."""
    cfile = os.path.join(case, "0", "C")
    if not os.path.exists(cfile):
        src = wsl(case)
        cmd = ("source /usr/lib/openfoam/openfoam2406/etc/bashrc >/dev/null 2>&1; "
               "T=$HOME/o2_runs/cc_tmp; rm -rf $T; mkdir -p $T/0; "
               f"cp -r '{src}/constant' '{src}/system' $T/ && cp '{src}/0/T' $T/0/ && cd $T && "
               f"postProcess -func writeCellCentres -time 0 > /dev/null 2>&1; cp $T/0/C '{src}/0/C'")
        subprocess.run(["wsl", "-d", "Ubuntu-24.04", "-e", "bash", "-c", cmd], capture_output=True)
    return cfile


def read_list(path, vector=False):
    txt = open(path, encoding="utf-8").read()
    m = re.search(r"internalField\s+nonuniform\s+List<(scalar|vector)>\s*\n?\s*(\d+)\s*\n?\s*\(", txt)
    if not m:
        m2 = re.search(r"internalField\s+uniform\s+([^;]+);", txt)
        return None if not m2 else float(m2.group(1))
    n = int(m.group(2))
    body = txt[m.end():]
    if vector:
        vals = re.findall(r"\(\s*([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s*\)", body)[:n]
        return np.array(vals, dtype=float)
    vals = re.findall(r"^\s*([-+0-9.eE]+)\s*$", body.split("\n)\n")[0], flags=re.M)[:n]
    return np.array(vals, dtype=float)


def nearest_time(case, t):
    ts = []
    for d in os.listdir(case):
        try:
            ts.append(float(d))
        except ValueError:
            pass
    ts = sorted(ts)
    return min(ts, key=lambda x: abs(x - t))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("case")
    ap.add_argument("--times", type=float, nargs="*", default=[0, 300, 600, 1200, 1800, 2400])
    a = ap.parse_args()
    case = os.path.abspath(a.case)
    C = read_list(ensure_centres(case), vector=True)
    x, y = C[:, 0], C[:, 1]                      # x: axis (up), y: radius
    xs = np.concatenate([x, x])
    ys = np.concatenate([y, -y])                 # mirror across the axis
    tri = mtri.Triangulation(ys, xs)
    # drop long thin triangles bridging the two halves' outer rim
    pts = np.column_stack([ys, xs])
    tt = tri.triangles
    edge = np.max(np.linalg.norm(pts[tt] - pts[np.roll(tt, 1, axis=1)], axis=2), axis=1)
    tri.set_mask(edge > 3.5 * np.median(edge))

    for field, name, cmap, label, vmin, vmax in (
            ("solidificationMeltingSource1:alpha1", "liquid_fraction", "coolwarm", "liquid fraction [-]", 0, 1),
            ("T", "temperature", "inferno", "T [K]", None, None)):
        times = [nearest_time(case, t) for t in a.times]
        vals = []
        for t in times:
            # a ':' in a field name becomes U+F03A when a WSL-written file is seen from Windows
            cands = [os.path.join(case, f"{t:g}", fn) for fn in (field, field.replace(":", "\uf03a"))]
            f = next((c for c in cands if os.path.exists(c)), None)
            v = read_list(f) if f else (np.zeros(len(x)) if "alpha1" in field else None)
            if v is None or np.isscalar(v):
                v = np.full(len(x), v if v is not None else np.nan)
            vals.append(v)
        lo = vmin if vmin is not None else min(np.nanmin(v) for v in vals)
        hi = vmax if vmax is not None else max(np.nanmax(v) for v in vals)
        fig, axs = plt.subplots(1, len(times), figsize=(2.3 * len(times), 3.6), constrained_layout=True)
        for ax, t, v in zip(np.atleast_1d(axs), times, vals):
            tc = ax.tripcolor(tri, np.concatenate([v, v]), cmap=cmap, vmin=lo, vmax=hi, shading="gouraud")
            ax.set_aspect("equal")
            ax.set_title(f"t = {t / 60:.0f} min", fontsize=9)
            ax.set_xticks([])
            ax.set_yticks([])
        fig.colorbar(tc, ax=axs, shrink=0.8, label=label)
        out = os.path.join(case, f"snapshots_{name}.png")
        fig.savefig(out, dpi=140)
        print("wrote", out)


if __name__ == "__main__":
    main()
