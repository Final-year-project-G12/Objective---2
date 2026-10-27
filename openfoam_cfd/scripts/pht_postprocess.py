#!/usr/bin/env python3
"""pht_postprocess.py -- summarise a porousHeatTransferFoam case (stdlib only).

Reads  postProcessing/probesBed/0/{T.solid,T.fluid}, written time directories, case_meta.json
Writes summary.json and hourly_bed.csv (t_s, mean T.solid, mean melt fraction).

Per probe: time the PCM leaves its solid state (T.solid >= T1) and becomes fully
melted (T.solid >= T2 = Tm+1 K). Melt fraction per cell is the linear map over the
+/-1 K band used by the grey-box (the solver's cubic h(T) differs negligibly there).
"""
import json
import os
import sys


def read_probes(path):
    locs, rows = [], []
    for ln in open(path):
        if ln.startswith("# Probe"):
            locs.append(ln.split("(")[1].split(")")[0])
        elif ln.startswith("#") or not ln.strip():
            continue
        else:
            rows.append([float(x) for x in ln.replace("(", " ").replace(")", " ").split()])
    return locs, rows


def first(rows, col, thr):
    for r in rows:
        if r[col] >= thr:
            return r[0]
    return None


def field_values(path):
    """All cell values of a scalar field file (uniform or nonuniform)."""
    lines = open(path).read().splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("internalField"):
            if "nonuniform" not in ln:
                return [float(ln.split("uniform")[1].replace(";", "").strip())]
            n = int(lines[i + 1].strip())
            return [float(x) for x in lines[i + 3: i + 3 + n]]
    raise ValueError("internalField not found in " + path)


def hourly_series(case, T1, T2):
    rows = []
    for name in os.listdir(case):
        try:
            tt = float(name)
        except ValueError:
            continue
        fp = os.path.join(case, name, "T.solid")
        if not os.path.exists(fp):
            continue
        v = field_values(fp)
        f = [min(1.0, max(0.0, (x - T1) / (T2 - T1))) for x in v]
        rows.append((tt, sum(v) / len(v), sum(f) / len(f)))
    rows.sort()
    return rows


def main(case):
    meta = json.load(open(os.path.join(case, "case_meta.json")))
    d = os.path.join(case, "postProcessing", "probesBed", "0")
    ls, rs = read_probes(os.path.join(d, "T.solid"))
    lf, rf = read_probes(os.path.join(d, "T.fluid"))
    Tm = (meta["Tm_C"] + 273.15) if "Tm_C" in meta else 333.0
    T1 = meta.get("T1", Tm - 1.0)
    T2 = meta.get("T2", Tm + 1.0)
    out = dict(meta=meta, n_rows=len(rs), probes=[])
    for i, loc in enumerate(ls):
        out["probes"].append(dict(location=loc, t_start_melt_s=first(rs, i + 1, T1),
                                  t_fully_melted_s=first(rs, i + 1, T2),
                                  T_solid_end_K=rs[-1][i + 1], T_fluid_end_K=rf[-1][i + 1]))
    out["t_end_s"] = rs[-1][0]
    out["fluid_outlet_series"] = [[r[0], r[-1]] for r in rf[:: max(1, len(rf) // 60)]]
    hs = hourly_series(case, T1, T2)
    with open(os.path.join(case, "hourly_bed.csv"), "w") as f:
        f.write("t_s,T_solid_mean_K,f_melt_mean\n")
        for r in hs:
            f.write("%g,%.4f,%.4f\n" % r)
    json.dump(out, open(os.path.join(case, "summary.json"), "w"), indent=1)
    for p in out["probes"]:
        print(p)


if __name__ == "__main__":
    main(sys.argv[1])
