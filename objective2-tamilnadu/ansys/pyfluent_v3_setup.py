"""
Parameterized Fluent setup for the FINAL (shield + resized-tank, 2026-10-27)
deployable designs. Unlike pyfluent_v2_setup.py (all 3 regimes = C26), the
final design has Regime 2 on n-Pentacosane (C25) while Regimes 0/1 stay on
n-Hexacosane (C26) -- so PCM identity is a CLI arg, not hardcoded. Zone
names are ALSO CLI args (not hardcoded) because this project's own
practice (verify_zones.py) found generic CGNS-import zone names are not
guaranteed to repeat across separately-imported meshes even when the
mesh construction is identical -- each v3 mesh's names are verified before
this script is invoked.

PCM properties (density/Cp solid+liquid averaged per this project's
existing convention, latent heat, thermal conductivity) read directly
from data/objective1/pcm_database_tamilnadu.csv -- never hand-typed.
Mushy-zone band widened to 10 K above each PCM's real Tm (proven Fluent
stability fix for this mesh/timestep resolution -- see CFD_VERIFICATION.md).

Usage:
  python pyfluent_v3_setup.py <case_path> <pcm:c26|c25> <water_zone> \
      <capsule_zone> <inlet_zone> <outlet_zone> <wall_outer_zone> \
      <axis_zone_1> <axis_zone_2> <axis_zone_3> \
      <inlet_velocity_m_s> <dt_s> <n_steps> <save_basename>
"""
import os
import sys
import traceback
import ansys.fluent.core as pyfluent

CASE_PATH = os.path.abspath(sys.argv[1])
PCM = sys.argv[2].lower()
Z_WATER, Z_CAPSULE, Z_INLET, Z_OUTLET, Z_WALL = sys.argv[3:8]
Z_AXIS = sys.argv[8:11]
INLET_VELOCITY = float(sys.argv[11])
DT = float(sys.argv[12])
N_STEPS = int(sys.argv[13])
SAVE_BASENAME = sys.argv[14]

PCM_PROPS = {
    # name, density (avg solid/liquid), cp (avg, J/kgK), k (W/mK), latent heat (J/kg), Tm (K)
    "c26": dict(name="c26", density=770, cp=2290, k=0.238, latent=256000, tm_k=329.65),
    "c25": dict(name="c25", density=801, cp=2220, k=0.239, latent=238000, tm_k=327.15),
}[PCM]

LOCAL_CWD = r"C:\fluent_work"
os.makedirs(LOCAL_CWD, exist_ok=True)


def step(name, fn):
    print(f"\n=== {name} ===")
    try:
        result = fn()
        print(f"OK: {name}")
        return result
    except Exception as e:
        print(f"FAILED: {name}: {type(e).__name__}: {e}")
        traceback.print_exc()
        return None


print("Launching Fluent...")
solver = pyfluent.launch_fluent(
    product_version="26.1.0", dimension=2, precision="double",
    processor_count=2, ui_mode="no_gui_or_graphics", start_timeout=120,
    cwd=LOCAL_CWD,
)
print("Connected.")

step("read case", lambda: solver.file.read_case(file_name=CASE_PATH, pdf_file_name=""))
step("set planar (confirmed deliverable scope)",
     lambda: setattr(solver.setup.general.solver, "two_dim_space", "planar"))
step("enable energy", lambda: setattr(solver.setup.models.energy, "enabled", True))
step("set laminar", lambda: setattr(solver.setup.models.viscous, "model", "laminar"))
step("enable solidification-melting (TUI)", lambda: solver.tui.define.models.solidification_melting("yes"))


def create_pcm():
    solver.setup.materials.fluid.create(PCM_PROPS["name"])
    m = solver.setup.materials.fluid[PCM_PROPS["name"]]
    m.density.option = "constant"; m.density.value = PCM_PROPS["density"]
    m.specific_heat.option = "constant"; m.specific_heat.value = PCM_PROPS["cp"]
    m.thermal_conductivity.option = "constant"; m.thermal_conductivity.value = PCM_PROPS["k"]
    m.melting_heat.option = "constant"; m.melting_heat.value = PCM_PROPS["latent"]
    m.tsolidus.option = "constant"; m.tsolidus.value = PCM_PROPS["tm_k"]
    m.tliqidus.option = "constant"; m.tliqidus.value = PCM_PROPS["tm_k"] + 10.0

step(f"create {PCM_PROPS['name']} material (Tm={PCM_PROPS['tm_k']-273.15:.1f}C, 10K mushy band)", create_pcm)


def copy_and_edit_water():
    solver.setup.materials.database.copy_materials(type="fluid", form=False, names=["water-liquid"])
    w = solver.setup.materials.fluid["water-liquid"]
    w.density.value = 977
    w.specific_heat.value = 4190
    w.thermal_conductivity.value = 0.668
    w.viscosity.value = 4.04e-4

step("copy + edit water-liquid properties", copy_and_edit_water)


def assign_zone_materials():
    solver.setup.cell_zone_conditions.fluid[Z_WATER].general.material = "water-liquid"
    solver.setup.cell_zone_conditions.fluid[Z_CAPSULE].general.material = PCM_PROPS["name"]

step(f"assign cell zone materials ({Z_WATER}=water, {Z_CAPSULE}=capsule)", assign_zone_materials)


def retype_boundaries():
    bc = solver.setup.boundary_conditions
    bc.set_zone_type(zone_list=[Z_INLET], new_type="velocity-inlet")
    bc.set_zone_type(zone_list=[Z_OUTLET], new_type="pressure-outlet")
    for z in Z_AXIS:
        bc.set_zone_type(zone_list=[z], new_type="axis")

step(f"retype boundaries (inlet={Z_INLET}/outlet={Z_OUTLET}/axis={Z_AXIS})", retype_boundaries)


def set_inlet():
    inl = solver.setup.boundary_conditions.velocity_inlet[Z_INLET]
    inl.momentum.velocity_specification_method = "Magnitude, Normal to Boundary"
    inl.momentum.velocity_magnitude.option = "value"
    inl.momentum.velocity_magnitude.value = INLET_VELOCITY
    inl.thermal.temperature.option = "value"
    inl.thermal.temperature.value = 343.15

step(f"set inlet BC ({INLET_VELOCITY:.6e} m/s, 343.15K)", set_inlet)


def set_outlet():
    out = solver.setup.boundary_conditions.pressure_outlet[Z_OUTLET]
    out.thermal.backflow_total_temperature.option = "value"
    out.thermal.backflow_total_temperature.value = 343.15
    out.momentum.prevent_reverse_flow = True

step("set outlet BC (343.15K backflow)", set_outlet)


def set_wall_outer():
    w = solver.setup.boundary_conditions.wall[Z_WALL]
    w.thermal.thermal_condition = "Heat Flux"
    w.thermal.heat_flux.value = 0

step("set wall_outer adiabatic", set_wall_outer)


def initialize():
    init = solver.solution.initialization
    init.initialization_type = "standard"
    init.defaults["temperature"] = 298.15
    init.initialize()

step("standard initialize at 298.15K", initialize)


def patch_liquid_fraction():
    solver.tui.solve.patch([Z_CAPSULE], [], "liquid-fraction", "0")

step("patch liquid fraction = 0 in capsule zone (TUI)", patch_liquid_fraction)


def set_transient():
    solver.setup.general.solver.time = "unsteady-1st-order"
    rc = solver.solution.run_calculation
    rc.parameters.time_step_size = DT
    rc.parameters.time_step_count = N_STEPS
    rc.parameters.max_iter_per_time_step = 20

step(f"configure transient ({DT}s x {N_STEPS} steps, target {DT*N_STEPS}s)", set_transient)


def run_solve():
    solver.solution.run_calculation.calculate()

step(f"CALCULATE ({N_STEPS} steps x {DT}s)", run_solve)

SAVE_PATH = os.path.abspath(f"{SAVE_BASENAME}.cas.h5")
step("save case+data", lambda: solver.file.write_case_data(file_name=SAVE_PATH))

solver.exit()
print("Clean exit.")
