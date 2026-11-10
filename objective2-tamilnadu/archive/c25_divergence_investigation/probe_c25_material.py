"""Read back what Fluent actually stored for c25 and c26.

Three hypotheses have now been proposed for the C25 divergence (timestep,
loss of Darcy damping at full melt, melt mobility) and the first two were
wrong. So stop theorising and read the solver's own state: if a property did
not bind, that explains it; if every property is correct, the cause is
numerical and the fix belongs in the solver settings, not the material.
"""
import ansys.fluent.core as pyfluent

PROPS = {
    "c26": dict(density=770, cp=2290, k=0.238, latent=256000, tm_k=329.65),
    "c25": dict(density=801, cp=2220, k=0.239, latent=238000, tm_k=327.15),
}

solver = pyfluent.launch_fluent(
    product_version="26.1.0", dimension=2, precision="double",
    processor_count=2, ui_mode="no_gui_or_graphics", start_timeout=120,
    cwd=r"C:\fluent_work",
)
solver.file.read_case(file_name=r"C:\fluent_work\regime0_v3_mesh_only.cas.h5", pdf_file_name="")
solver.setup.general.solver.two_dim_space = "planar"
solver.setup.models.energy.enabled = True
solver.setup.models.viscous.model = "laminar"
solver.tui.define.models.solidification_melting("yes")

for name, p in PROPS.items():
    solver.setup.materials.fluid.create(name)
    m = solver.setup.materials.fluid[name]
    m.density.option = "constant"; m.density.value = p["density"]
    m.specific_heat.option = "constant"; m.specific_heat.value = p["cp"]
    m.thermal_conductivity.option = "constant"; m.thermal_conductivity.value = p["k"]
    m.melting_heat.option = "constant"; m.melting_heat.value = p["latent"]
    m.tsolidus.option = "constant"; m.tsolidus.value = p["tm_k"]
    m.tliqidus.option = "constant"; m.tliqidus.value = p["tm_k"] + 10.0
    m.viscosity.option = "constant"; m.viscosity.value = 10.0

for name in PROPS:
    m = solver.setup.materials.fluid[name]
    print(f"\n=== {name} as Fluent holds it ===")
    for attr in ("density", "specific_heat", "thermal_conductivity", "viscosity",
                 "melting_heat", "tsolidus", "tliqidus"):
        try:
            o = getattr(m, attr)
            print(f"  {attr:22s} option={o.option()!r:12s} value={o.value()}")
        except Exception as e:
            print(f"  {attr:22s} READ FAILED: {type(e).__name__}: {e}")
    # the mushy-zone constant is the Darcy damping coefficient; if it differs
    # between materials that alone would explain a material-specific blow-up
    for attr in ("mushy_zone_constant", "mushy_zone_parameter"):
        try:
            print(f"  {attr:22s} = {getattr(m, attr)()}")
        except Exception:
            pass

solver.exit()
print("\ndone.")
