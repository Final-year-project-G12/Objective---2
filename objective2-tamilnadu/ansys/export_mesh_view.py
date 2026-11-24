"""
export_mesh_view.py
===================
Render the full system MESH (tank + 34 capsules + collector panel) as a native
Fluent picture. The settings-API mesh object was 'inactive' in no_gui; the TUI
display route works, so this uses solver.tui.display.*. Reads the solved system
case (its zone surfaces are already built) so the capsule outlines show.

Output -> ansys/figures/system_views/system_mesh.png
"""
import os, traceback
import ansys.fluent.core as pyfluent

ANSYS = r"C:\Users\jaswi\OneDrive\Desktop\ALL\SEM_7\project\jammalamadugu\new_obj\objective2_design_optimization\ansys"
WORK = r"C:\fluent_work"
OUT = os.path.join(ANSYS, "figures", "system_views")
os.makedirs(OUT, exist_ok=True)
SOLVED = os.path.join(ANSYS, "system_tank_pcm_panel_solved.cas.h5")
PNG = os.path.join(OUT, "system_mesh.png")

print("launching Fluent (no_gui)...", flush=True)
solver = pyfluent.launch_fluent(product_version="26.1.0", dimension=2, precision="double",
                                processor_count=2, ui_mode="no_gui", start_timeout=180, cwd=WORK)
print("LAUNCH OK", flush=True)
solver.file.read_case_data(file_name=SOLVED, pdf_file_name="")
print("case+data loaded", flush=True)

for attr, val in (("x_resolution", 1400), ("y_resolution", 1700)):
    try: setattr(solver.results.graphics.picture, attr, val)
    except Exception as e: print(f"  ({attr}: {type(e).__name__})", flush=True)

def try_call(desc, fn):
    try:
        fn(); print(f"  ok: {desc}", flush=True); return True
    except Exception as e:
        print(f"  skip {desc}: {type(e).__name__}: {e}", flush=True); return False

# display the mesh via TUI, fit view, then save
try_call("display.mesh()", lambda: solver.tui.display.mesh())
try_call("views.auto_scale", lambda: solver.tui.display.views.auto_scale())
try_call("views.restore front", lambda: solver.tui.display.views.restore_view("front"))

saved = False
# save picture: try the settings API first, then the TUI hardcopy
try:
    solver.results.graphics.picture.save_picture(file_name=PNG)
    saved = os.path.exists(PNG) and os.path.getsize(PNG) > 0
    print(f"  settings save_picture -> {'OK' if saved else 'EMPTY'}", flush=True)
except Exception:
    traceback.print_exc()
if not saved:
    try_call("set.picture.driver png", lambda: solver.tui.display.set.picture.driver("png"))
    try_call("tui save_picture", lambda: solver.tui.display.save_picture(PNG))
    saved = os.path.exists(PNG) and os.path.getsize(PNG) > 0

print(f"\nRESULT: {'OK ' + PNG if saved else 'FAILED to save mesh picture'}  "
      f"({os.path.getsize(PNG) if saved else 0} B)", flush=True)
try: solver.exit()
except Exception: pass
print("DONE", flush=True)
