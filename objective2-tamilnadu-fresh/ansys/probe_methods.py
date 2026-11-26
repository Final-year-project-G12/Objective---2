import ansys.fluent.core as pyfluent
s = pyfluent.launch_fluent(product_version="26.1.0", dimension=2, precision="double",
                           processor_count=2, ui_mode="no_gui_or_graphics",
                           start_timeout=120, cwd=r"C:\fluent_work")
s.file.read_case(file_name=r"C:\fluent_work\regime0_v3_mesh_only.cas.h5", pdf_file_name="")
s.setup.general.solver.two_dim_space = "planar"
s.setup.models.energy.enabled = True
s.setup.models.viscous.model = "laminar"
s.tui.define.models.solidification_melting("yes")
m = s.solution.methods
print("METHODS CHILDREN:", [a for a in dir(m) if not a.startswith('_') and a.islower()][:40])
for attr in ("p_v_coupling", "discretization_scheme", "pseudo_time_method"):
    try:
        o = getattr(m, attr)
        print(f"\n--- {attr} ---")
        print("  state:", o())
        try:
            print("  allowed:", o.get_attr("allowed-values"))
        except Exception: pass
    except Exception as e:
        print(f"\n--- {attr}: {type(e).__name__}: {e}")
try:
    print("\np_v_coupling.flow_scheme allowed:",
          m.p_v_coupling.flow_scheme.get_attr("allowed-values"))
except Exception as e:
    print("flow_scheme:", e)
s.exit()
