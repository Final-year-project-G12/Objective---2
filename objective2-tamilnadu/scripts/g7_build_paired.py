"""
scripts/g7_build_paired.py
==========================
Builds results/g7_sensitivity_paired.csv from the per-regime G7 files.

WHY THIS EXISTS
---------------
src/plots/make_plots_results.py::fig_fraction_response reads
`g7_sensitivity_paired.csv`, but NOTHING in this repository writes it --
`g7_sensitivity.py` writes only `g7_sensitivity_r<cluster>.csv`. The pairing
step existed in the Rajasthan original and was not carried across in the port,
so the figure has been silently unbuildable since.

The data is all present, so the file is reconstructed rather than the figure
abandoned. g7_sensitivity.py's own docstring states the reference:

    "Reference tank: plain water-only, same weather, demand, shield and tank
     model (paired baseline)."

and those reference runs are on disk as the `REF` block -- plain water
(pcm="PLAIN", level="plain") at R_in = 20 mm, 0.030 kg/s, staggered, recorded
once per (regime, year, model).

So the paired gain of any design is its energy minus the REF run that shares
its regime, year AND tank model. Matching on model matters: the single-node
and multi-node references differ by ~200 kWh/yr on the same weather, so
pairing across models would manufacture a gain that is really a
model-switching artefact.

Run: python scripts/g7_build_paired.py
"""
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

OUT = REPO / "results"
# Every absolute energy measure that has a meaningful paired difference.
PAIRED = ["E_del45_window_kWh", "E_del45_annual_kWh", "useful_energy_kWh",
          "E_rec45_mean_kWh", "tau_serve_mean_h", "tau_hold_mean_h"]
KEY = ["regime", "year", "model"]


def main():
    frames = []
    for cid in range(3):
        p = OUT / f"g7_sensitivity_r{cid}.csv"
        if not p.exists():
            raise SystemExit(f"{p.name} missing -- run g7_sensitivity first")
        frames.append(pd.read_csv(p))
    d = pd.concat(frames, ignore_index=True)

    ref = d[d.block == "REF"]
    if ref.empty:
        raise SystemExit("no REF rows -- cannot pair without the plain-water reference")
    dup = ref.duplicated(KEY).sum()
    if dup:
        raise SystemExit(f"{dup} duplicate REF row(s) for the same {KEY}; pairing would be ambiguous")

    ref = ref.set_index(KEY)[PAIRED]
    joined = d.join(ref, on=KEY, rsuffix="_ref")
    for col in PAIRED:
        refcol = f"{col}_ref"
        if refcol not in joined:              # single PAIRED column -> no suffix collision
            refcol = col + "_ref"
        joined["d_" + col] = joined[col] - joined[refcol]

    missing = joined["d_E_del45_window_kWh"].isna() & (joined.block != "REF") & joined.valid.astype(bool)
    if missing.any():
        raise SystemExit(f"{int(missing.sum())} valid row(s) found no matching REF run -- "
                         "refusing to write a half-paired file")

    out = OUT / "g7_sensitivity_paired.csv"
    joined.to_csv(out, index=False)
    print(f"wrote {out}  ({len(joined)} rows, {len(ref)} reference runs)")

    b = joined[(joined.block == "B_count") & (joined.model == "multinode")
               & joined.valid.astype(bool)]
    print(f"\nB_count / multinode rows for fig8: {len(b)}")
    if len(b):
        s = b.groupby("regime").d_E_del45_window_kWh.agg(["min", "max"])
        print("paired window gain by regime (kWh/yr):")
        print(s.to_string())


if __name__ == "__main__":
    main()
