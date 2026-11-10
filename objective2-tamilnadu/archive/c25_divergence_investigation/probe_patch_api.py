"""Find the patch call this Fluent build actually accepts.

v3 used solver.tui.solve.patch([zone], [], "liquid-fraction", "0") -> "invalid
command"; v4's first attempt used the settings API with domain= -> "Key
'domain' is invalid". Rather than guess a third time, launch once and try the
candidates in order, reporting which bind.
"""
import os
import traceback

import ansys.fluent.core as pyfluent

LOCAL_CWD = r"C:\fluent_work"
CASE = r"C:\fluent_work\regime0_v3_mesh_only.cas.h5"
Z_CAPSULE = "3_s_2"

solver = pyfluent.launch_fluent(
    product_version="26.1.0", dimension=2, precision="double",
    processor_count=2, ui_mode="no_gui_or_graphics", start_timeout=120,
    cwd=LOCAL_CWD,
)
solver.file.read_case(file_name=CASE, pdf_file_name="")
solver.setup.general.solver.two_dim_space = "planar"
solver.setup.models.energy.enabled = True
solver.setup.models.viscous.model = "laminar"
solver.tui.define.models.solidification_melting("yes")
solver.solution.initialization.initialization_type = "standard"
solver.solution.initialization.defaults["temperature"] = 343.15
solver.solution.initialization.initialize()

print("\n### signature of settings patch ###")
try:
    import inspect
    print(inspect.signature(solver.solution.initialization.patch))
except Exception as e:
    print("sig failed:", e)
try:
    print(solver.solution.initialization.patch.__doc__[:1500])
except Exception as e:
    print("doc failed:", e)

CANDIDATES = [
    ("settings: cell_zones+variable+value",
     lambda: solver.solution.initialization.patch(
         cell_zones=[Z_CAPSULE], variable="temperature", value=303.15)),
    ("settings: zones+variable+value",
     lambda: solver.solution.initialization.patch(
         zones=[Z_CAPSULE], variable="temperature", value=303.15)),
    ("tui: strings",
     lambda: solver.tui.solve.patch(Z_CAPSULE, "()", "temperature", "303.15")),
    ("tui: quoted zone, empty register, var, val",
     lambda: solver.tui.solve.patch(Z_CAPSULE, "", "temperature", "303.15")),
    ("tui: list-of-zone then blank",
     lambda: solver.tui.solve.patch([Z_CAPSULE], [], "temperature", "303.15")),
]

for label, fn in CANDIDATES:
    print(f"\n### TRY {label} ###")
    try:
        fn()
        print(f"*** SUCCESS: {label}")
    except Exception as e:
        print(f"--- failed: {type(e).__name__}: {e}")

# Whatever bound, read the capsule temperature back: a patch that "succeeds"
# without changing the field is the failure mode that cost v3 its result.
try:
    r = solver.solution.report_definitions
    r.volume["t_chk"] = {"report_type": "volume-average",
                         "field": "temperature", "cell_zones": [Z_CAPSULE]}
    val = list(r.compute(report_defs=["t_chk"])[0].values())[0][0]
    print(f"\n### capsule mean T after patching = {val} K "
          f"(want 303.15, init was 343.15) ###")
except Exception:
    traceback.print_exc()

solver.exit()
print("done.")
