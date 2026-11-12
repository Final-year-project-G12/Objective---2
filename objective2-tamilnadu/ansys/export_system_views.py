"""
export_system_views.py
=======================
Render the COMPLETE tank + PCM capsules + collector panel as native Fluent
pictures (one image of the whole system), straight from the solved system case.
Same graphics path as export_contours.py: ui_mode="no_gui" offscreen engine +
results.graphics.picture.save_picture, so these are Fluent's own renders of the
real mesh, not matplotlib.

Outputs -> ansys/figures/system_views/
  system_mesh.png         the full system mesh (shows tank, 34 capsules, panel)
  system_temperature.png  temperature contour of the whole system
"""
import os
import traceback
import ansys.fluent.core as pyfluent

ANSYS = r"C:\Users\jaswi\OneDrive\Desktop\ALL\SEM_7\project\jammalamadugu\new_obj\objective2_design_optimization\ansys"
WORK = r"C:\fluent_work"
OUT = os.path.join(ANSYS, "figures", "system_views")
os.makedirs(OUT, exist_ok=True)

SETUP = os.path.join(ANSYS, "system_tank_pcm_panel_setup.cas.h5")
SOLVED = os.path.join(ANSYS, "system_tank_pcm_panel_solved.cas.h5")

print("launching Fluent (ui_mode=no_gui)...", flush=True)
solver = pyfluent.launch_fluent(
    product_version="26.1.0", dimension=2, precision="double",
    processor_count=2, ui_mode="no_gui", start_timeout=180, cwd=WORK,
)
print("LAUNCH OK", flush=True)
gfx = solver.results.graphics

for attr, val in (("x_resolution", 1400), ("y_resolution", 1700)):
    try:
        setattr(gfx.picture, attr, val)
    except Exception as e:
        print(f"  ({attr}: {type(e).__name__})", flush=True)

saved = []

# ---- 1) MESH view of the full system (shows the capsule layout) ----
try:
    solver.file.read_case(file_name=SETUP, pdf_file_name="")
    print("setup case loaded", flush=True)
    made = False
    for spec in (
        {"options": {"edges": True, "faces": True}, "coloring": {"option": "manual"}},
        {"options": {"edges": True, "faces": True}},
        {},
    ):
        try:
            gfx.mesh["sys_mesh"] = spec
            gfx.mesh["sys_mesh"].display()
            made = True
            print(f"  mesh displayed with spec keys {list(spec)}", flush=True)
            break
        except Exception as e:
            print(f"  mesh spec {list(spec)} failed: {type(e).__name__}: {e}", flush=True)
    if made:
        try:
            gfx.views.auto_scale()
        except Exception:
            pass
        png = os.path.join(OUT, "system_mesh.png")
        gfx.picture.save_picture(file_name=png)
        ok = os.path.exists(png) and os.path.getsize(png) > 0
        print(f"  system_mesh.png {'OK' if ok else 'EMPTY'} ({os.path.getsize(png) if ok else 0} B)", flush=True)
        if ok:
            saved.append(png)
except Exception:
    traceback.print_exc()

# ---- 2) TEMPERATURE contour of the full system ----
try:
    solver.file.read_case_data(file_name=SOLVED, pdf_file_name="")
    print("solved case+data loaded", flush=True)
    gfx.contour["sys_temp"] = {
        "field": "temperature",
        "surfaces_list": [],
        "coloring": {"option": "banded"},
        "filled": True,
        "node_values": True,
    }
    gfx.contour["sys_temp"].display()
    try:
        gfx.views.auto_scale()
    except Exception:
        pass
    png = os.path.join(OUT, "system_temperature.png")
    gfx.picture.save_picture(file_name=png)
    ok = os.path.exists(png) and os.path.getsize(png) > 0
    print(f"  system_temperature.png {'OK' if ok else 'EMPTY'} ({os.path.getsize(png) if ok else 0} B)", flush=True)
    if ok:
        saved.append(png)
except Exception:
    traceback.print_exc()

print("\n=== SAVED ===", flush=True)
for p in saved:
    print(" ", p, flush=True)
try:
    solver.exit()
except Exception:
    pass
print("DONE", flush=True)
