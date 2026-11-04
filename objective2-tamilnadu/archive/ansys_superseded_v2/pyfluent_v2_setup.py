"""
Parameterized Fluent setup for the POST-DEMAND-TIMING-FIX (2026-10-26)
deployable designs. All 3 Tamil Nadu regimes now use the same PCM
(n-Hexacosane / C26) per the corrected optimizer re-run, so this one
script replaces the three separate per-regime scripts -- only geometry
(inlet velocity, capsule radius used for the mushy-zone-adequacy check)
and the case/output paths differ per regime, passed as CLI args.

Ground-truth zone identities (verified independently per regime via
verify_zones.py against each regime's own *_v2_mesh_only.cas.h5 -- NOT
assumed to match the pre-fix regime0/1/2 meshes' naming, which this
confirmed differs in places):
  3_s_1 = water, 3_s_2 = capsule
  2_l_7 = inlet, 2_l_9 = outlet, 2_l_8 = wall_outer
  2_l_10, 2_l_11 = axis (water side), 2_l_5 = axis (capsule side)
This mapping is IDENTICAL across all 3 new meshes (confirmed by running
verify_zones.py on each individually) -- unlike the original regime0/1/2
meshes, which did not share a naming pattern. Still verified per-regime,
not assumed, before writing this script.

Usage:
  python pyfluent_v2_setup.py <case_path> <inlet_velocity_m_s> \
      <time_step_size_s> <time_step_count> <save_basename>
"""
import os
import sys
import traceback
import ansys.fluent.core as pyfluent

CASE_PATH = os.path.abspath(sys.argv[1])
INLET_VELOCITY = float(sys.argv[2])
DT = float(sys.argv[3])
N_STEPS = int(sys.argv[4])
SAVE_BASENAME = sys.argv[5]

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
    inl.momentum.velocity_magnitude.value = INLET_VELOCITY
    inl.thermal.temperature.option = "value"
    inl.thermal.temperature.value = 343.15

step(f"set inlet BC ({INLET_VELOCITY:.6e} m/s, 343.15K)", set_inlet)


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
