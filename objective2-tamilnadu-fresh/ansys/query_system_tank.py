"""
query_system_tank.py
====================
Load the solved whole-system tank case in Fluent and report the real output:
volume-averaged / max / min temperature in each zone (tank water, PCM, shell,
collector panel, absorber, riser). This is the tank's Fluent output in numbers,
to go with the temperature contour (Figure 2b).
"""
import os
import ansys.fluent.core as pyfluent

ANSYS = r"C:\Users\jaswi\OneDrive\Desktop\ALL\SEM_7\project\jammalamadugu\new_obj\objective2_design_optimization\ansys"
WORK = r"C:\fluent_work"
CASE = os.path.join(ANSYS, "system_tank_pcm_panel_solved.cas.h5")

print("launching Fluent (no_gui_or_graphics)...", flush=True)
solver = pyfluent.launch_fluent(product_version="26.1.0", dimension=2, precision="double",
                                processor_count=2, ui_mode="no_gui_or_graphics",
                                start_timeout=180, cwd=WORK)
print("LAUNCH OK", flush=True)
solver.file.read_case_data(file_name=CASE, pdf_file_name="")
print("tank case+data loaded\n", flush=True)

ZONES = ["water", "pcm", "shell", "panel", "absorber", "riser"]
rd = solver.solution.report_definitions

def report(zone, kind):
    name = f"q_{zone}_{kind}"
    try:
        rd.volume[name] = {"report_type": f"volume-{kind}", "field": "temperature",
                           "cell_zones": [zone]}
        v = rd.compute(report_defs=[name])
        return float(list(v[0].values())[0][0])
    except Exception as e:
        return None

print(f"{'zone':10s} {'avg (C)':>10s} {'max (C)':>10s} {'min (C)':>10s}", flush=True)
print("-" * 44, flush=True)
for z in ZONES:
    a = report(z, "average"); mx = report(z, "max"); mn = report(z, "min")
    def c(k): return f"{k-273.15:10.2f}" if k is not None else f"{'n/a':>10s}"
    print(f"{z:10s} {c(a)} {c(mx)} {c(mn)}", flush=True)

try:
    solver.exit()
except Exception:
    pass
print("\nDONE", flush=True)
