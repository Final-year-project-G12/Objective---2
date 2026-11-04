import ansys.fluent.core as pyfluent
s = pyfluent.launch_fluent(product_version="26.1.0", dimension=2, precision="double",
                           processor_count=2, ui_mode="no_gui_or_graphics",
                           start_timeout=120, cwd=r"C:\fluent_work")
s.file.read_case(file_name=r"C:\fluent_work\regime0_v3_mesh_only.cas.h5", pdf_file_name="")
s.setup.general.solver.two_dim_space = "planar"
s.setup.models.energy.enabled = True
s.setup.models.viscous.model = "laminar"
s.tui.define.models.solidification_melting("yes")
try:
    urf = s.solution.controls.under_relaxation
    print("UNDER-RELAXATION KEYS:")
    for k in urf.get_attr("allowed-values") or []:
        print("  ", k)
except Exception as e:
    print("allowed-values failed:", e)
try:
    print("\nstate:", s.solution.controls.under_relaxation())
except Exception as e:
    print("state failed:", e)
s.exit()
