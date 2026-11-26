"""
export_contours.py
==================
Export REAL Fluent contour images (liquid-fraction + temperature) for the three
Tamil Nadu final designs, straight from the already-solved case+data files.

Uses Fluent's OWN native contour graphics object (the recipe proven live in
fluent_live_demo.py) and picture.save_picture -- so the image is rendered by
Fluent from the real mesh, with no matplotlib/Delaunay reconstruction and none
of the artifacts that produced before. Runs ui_mode="no_gui" so an offscreen
graphics engine is present (no_gui_or_graphics has none; plain gui dies when
launched from a background process).

Each design reads its solved .cas.h5/.dat.h5, then writes PNGs. Pictures are
saved one at a time so any partial success is kept.
"""
import os
import sys
import traceback

import ansys.fluent.core as pyfluent

WORK = r"C:\fluent_work"
ANSYS = r"C:\Users\jaswi\OneDrive\Desktop\ALL\SEM_7\project\jammalamadugu\new_obj\objective2_design_optimization\ansys"
OUT = os.path.join(ANSYS, "figures", "regime_contours")
os.makedirs(OUT, exist_ok=True)

# Final designs -> solved per-PCM case+data (same mesh geometry, final PCM identity).
# Regime 1 and 2 are both RT57HC, so both use the rt57hc solve.
DESIGNS = [
    dict(regime=0, pcm="PureTemp 58", base=os.path.join(ANSYS, "v7_puretemp58")),
    dict(regime=1, pcm="RT57HC",      base=os.path.join(ANSYS, "v7_rt57hc")),
    dict(regime=2, pcm="RT57HC",      base=os.path.join(ANSYS, "v7_rt57hc")),
]

FIELDS = [
    ("liquid-fraction", "liqfrac", "Liquid fraction (0 = solid, 1 = molten)"),
    ("temperature",     "temp",    "Static temperature (K)"),
]

print("launching Fluent (ui_mode=no_gui, offscreen graphics)...", flush=True)
solver = pyfluent.launch_fluent(
    product_version="26.1.0", dimension=2, precision="double",
    processor_count=2, ui_mode="no_gui", start_timeout=180, cwd=WORK,
)
print("LAUNCH OK", flush=True)

gfx = solver.results.graphics

# Picture settings: fixed high resolution, independent of any window.
try:
    gfx.picture.use_window_resolution = False
except Exception as e:
    print("  (use_window_resolution not settable:", type(e).__name__, e, ")", flush=True)
for attr, val in (("x_resolution", 1600), ("y_resolution", 1100)):
    try:
        setattr(gfx.picture, attr, val)
    except Exception as e:
        print(f"  ({attr} not settable: {type(e).__name__})", flush=True)

saved = []
for d in DESIGNS:
    cas, dat = d["base"] + ".cas.h5", d["base"] + ".dat.h5"
    tag = f"regime{d['regime']}_{d['pcm'].replace(' ', '').replace('.', '')}"
    print(f"\n=== regime {d['regime']}  {d['pcm']} ===", flush=True)
    if not (os.path.exists(cas) and os.path.exists(dat)):
        print(f"  MISSING {cas} / {dat}; skipping", flush=True)
        continue
    try:
        solver.file.read_case_data(file_name=cas, pdf_file_name="")
        print("  case+data loaded", flush=True)
    except Exception:
        traceback.print_exc()
        continue

    for field, fshort, desc in FIELDS:
        name = f"c_{fshort}"
        png = os.path.join(OUT, f"{tag}_{fshort}.png")
        try:
            # define contour (native Fluent graphics object)
            gfx.contour[name] = {
                "field": field,
                "surfaces_list": [],          # empty -> whole 2D domain
                "coloring": {"option": "banded"},
                "filled": True,
                "node_values": True,
            }
            c = gfx.contour[name]
            c.display()
            # fit the view to the geometry, then save
            try:
                gfx.views.auto_scale()
            except Exception:
                try:
                    gfx.views.restore_view(view_name="front")
                except Exception:
                    pass
            gfx.picture.save_picture(file_name=png)
            ok = os.path.exists(png) and os.path.getsize(png) > 0
            print(f"  {field:16s} -> {os.path.basename(png)}  {'OK' if ok else 'EMPTY'}"
                  f"  ({os.path.getsize(png) if ok else 0} bytes)", flush=True)
            if ok:
                saved.append(png)
        except Exception:
            print(f"  {field}: FAILED", flush=True)
            traceback.print_exc()

print("\n=== SAVED PICTURES ===", flush=True)
for p in saved:
    print(" ", p, flush=True)
print(f"total: {len(saved)}", flush=True)

try:
    solver.exit()
except Exception:
    pass
print("DONE", flush=True)
