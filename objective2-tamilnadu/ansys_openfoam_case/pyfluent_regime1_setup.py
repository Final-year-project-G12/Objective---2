"""
Regime 1 / n-Hexacosane (C26) Fluent setup -- direct port of the finalized,
proven Regime-0 pipeline (pyfluent_full_setup2.py), with:
  - real C26 properties (pcm_database_tamilnadu.csv): Tm=56.5C, latent=256
    kJ/kg, k=0.238 W/mK, rho=770 kg/m3 (solid=liquid, no imputed split),
    Cp=2.2 kJ/kgK (solid-phase value used, consistent with Regime 0's choice)
  - real geometry: capsule diameter 44.038mm, 26 capsules, flow 0.021863 kg/s
  - real computed inlet velocity: 1.955182e-4 m/s (see compute done this
    session: (0.021863/26)/977 / (pi*(1.7*0.022019)^2))
  - GROUND-TRUTH-VERIFIED zone identities for THIS regime's mesh (confirmed
    via verify_zones.py against regime1_mesh_only.cas.h5's own HDF5 data --
    NOT assumed to match Regime 0's naming, which differs):
      3_s_1 = water, 3_s_2 = capsule
      2_l_7 = inlet (x=-0.088), 2_l_9 = outlet (x=+0.088)
      2_l_8 = wall_outer
      2_l_10, 2_l_11 = axis (water side), 2_l_5 = axis (capsule side)
  - same proven stability fixes as Regime 0: planar mode (axisymmetric
    unresolved), 10K-equivalent widened mushy zone, prevent_reverse_flow,
    fixed 0.5s timestep / 340 steps / 170s target
"""
import os
import traceback
import ansys.fluent.core as pyfluent

CASE_PATH = os.path.abspath("regime1_mesh_only.cas.h5")
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

def create_c26():
    solver.setup.materials.fluid.create("c26")
    m = solver.setup.materials.fluid["c26"]
    m.density.option = "constant"; m.density.value = 770
    m.specific_heat.option = "constant"; m.specific_heat.value = 2200
    m.thermal_conductivity.option = "constant"; m.thermal_conductivity.value = 0.238
    m.melting_heat.option = "constant"; m.melting_heat.value = 256000
    m.tsolidus.option = "constant"; m.tsolidus.value = 329.65
    m.tliqidus.option = "constant"; m.tliqidus.value = 339.65

step("create c26 material", create_c26)

def copy_and_edit_water():
    solver.setup.materials.database.copy_materials(type="fluid", form=False, names=["water-liquid"])
    w = solver.setup.materials.fluid["water-liquid"]
    w.density.value = 977
    w.specific_heat.value = 4190
    w.thermal_conductivity.value = 0.668
    w.viscosity.value = 4.04e-4

step("copy + edit water-liquid properties", copy_and_edit_water)

def assign_zone_materials():
    solver.setup.cell_zone_conditions.fluid["3_s_1"].general.material = "water-liquid"
    solver.setup.cell_zone_conditions.fluid["3_s_2"].general.material = "c26"

step("assign cell zone materials (3_s_1=water, 3_s_2=capsule)", assign_zone_materials)

def retype_boundaries():
    bc = solver.setup.boundary_conditions
    bc.set_zone_type(zone_list=["2_l_7"], new_type="velocity-inlet")
    bc.set_zone_type(zone_list=["2_l_9"], new_type="pressure-outlet")
    bc.set_zone_type(zone_list=["2_l_10"], new_type="axis")
    bc.set_zone_type(zone_list=["2_l_11"], new_type="axis")
    bc.set_zone_type(zone_list=["2_l_5"], new_type="axis")

step("retype boundaries (inlet=2_l_7/outlet=2_l_9/axis)", retype_boundaries)

def set_inlet():
    inl = solver.setup.boundary_conditions.velocity_inlet["2_l_7"]
    inl.momentum.velocity_specification_method = "Magnitude, Normal to Boundary"
    inl.momentum.velocity_magnitude.option = "value"
    inl.momentum.velocity_magnitude.value = 1.955182e-4
    inl.thermal.temperature.option = "value"
    inl.thermal.temperature.value = 343.15

step("set inlet BC (1.955182e-4 m/s, 343.15K)", set_inlet)

def set_outlet():
    out = solver.setup.boundary_conditions.pressure_outlet["2_l_9"]
    out.thermal.backflow_total_temperature.option = "value"
    out.thermal.backflow_total_temperature.value = 343.15
    out.momentum.prevent_reverse_flow = True

step("set outlet BC (343.15K backflow)", set_outlet)

def set_wall_outer():
    w = solver.setup.boundary_conditions.wall["2_l_8"]
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
    solver.tui.solve.patch(["3_s_2"], [], "liquid-fraction", "0")

step("patch liquid fraction = 0 in capsule zone (TUI)", patch_liquid_fraction)

def set_transient():
    solver.setup.general.solver.time = "unsteady-1st-order"
    rc = solver.solution.run_calculation
    rc.parameters.time_step_size = 0.5
    rc.parameters.time_step_count = 1000
    rc.parameters.max_iter_per_time_step = 20

step("configure transient (fixed 0.5s x 1000 steps, target 500s)", set_transient)

def run_solve():
    solver.solution.run_calculation.calculate()

step("CALCULATE (1000 steps x 0.5s)", run_solve)

SAVE_PATH = os.path.abspath("regime1_c26_melting.cas.h5")
step("save case+data", lambda: solver.file.write_case_data(file_name=SAVE_PATH))

solver.exit()
print("Clean exit.")
