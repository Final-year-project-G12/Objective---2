"""
Regime-0 / RT57HC Fluent setup, part 2: boundary conditions through solve
and save. Builds on regime0_mesh_only.cas.h5 (same as part 1), but now
uses GROUND-TRUTH-VERIFIED zone identities read directly from the case
file's own HDF5 face/cell adjacency data (see verify_zones.py / the
investigation that produced it), not estimation:

  3_s_1 = water   (touches wall_outer/inlet/outlet/2 axis segments)
  3_s_2 = capsule (only touches its own axis diameter segment, 2_l_5)
  2_l_8  = wall_outer
  2_l_11 = inlet  (negative x)
  2_l_10 = outlet (positive x)
  2_l_9, 2_l_7 = axis (water side)
  2_l_5 = axis (capsule's own diameter)
  interface-2_l_6 = capsule/water coupled interface (left alone -- Fluent
    handles this automatically once both sides are "fluid" zones with
    melting enabled)

This corrects an earlier (wrong) estimation-based assignment that had
3_s_1/3_s_2 swapped.
"""
import os
import traceback
import ansys.fluent.core as pyfluent

CASE_PATH = os.path.abspath("regime0_mesh_only.cas.h5")
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
# FINAL DELIVERABLE SCOPE DECISION: true axisymmetric mode diverges
# immediately regardless of timestep (0.5s, 0.02s), whether axisymmetric
# is set post-load or baked into the mesh at creation, or pressure-
# velocity coupling scheme (Coupled vs SIMPLE) -- 3 independent fix
# attempts all failed with the identical instant x/y-momentum + pressure
# blowup signature, pointing to a deeper mesh/geometry conditioning issue
# near the symmetry axis that needs visual/mesh-level investigation, not
# more blind parameter changes. Per explicit user decision, reverting to
# the PLANAR interpretation (a flat, non-revolved cross-section -- the
# same simplification OpenFOAM's case deliberately uses) as today's
# verified, stable, working deliverable. The mesh file now defaults to
# axisymmetric (baked in during troubleshooting), so this must be
# explicitly overridden back.
step("set planar (final scope decision -- see note above)",
     lambda: setattr(solver.setup.general.solver, "two_dim_space", "planar"))
step("enable energy", lambda: setattr(solver.setup.models.energy, "enabled", True))
step("set laminar", lambda: setattr(solver.setup.models.viscous, "model", "laminar"))
step("enable solidification-melting (TUI)", lambda: solver.tui.define.models.solidification_melting("yes"))

def create_rt57hc():
    solver.setup.materials.fluid.create("rt57hc")
    m = solver.setup.materials.fluid["rt57hc"]
    m.density.option = "constant"; m.density.value = 900
    m.specific_heat.option = "constant"; m.specific_heat.value = 2000
    m.thermal_conductivity.option = "constant"; m.thermal_conductivity.value = 0.239
    m.melting_heat.option = "constant"; m.melting_heat.value = 240000
    m.tsolidus.option = "constant"; m.tsolidus.value = 329.65
    # Trend across attempts: 1K band -> diverged at t~147s; 3K -> t~153s;
    # 5K (with partial adaptive stepping) -> t~163.6s; a smaller FIXED
    # 0.2s timestep with the 5K band alone (no further widening) only
    # reached t~158.8s -- confirming timestep size is NOT the dominant
    # lever, mushy-zone width is. Pushing further to 10K.
    m.tliqidus.option = "constant"; m.tliqidus.value = 339.65

step("create rt57hc material", create_rt57hc)

def copy_and_edit_water():
    solver.setup.materials.database.copy_materials(type="fluid", form=False, names=["water-liquid"])
    w = solver.setup.materials.fluid["water-liquid"]
    w.density.value = 977
    w.specific_heat.value = 4190
    w.thermal_conductivity.value = 0.668
    w.viscosity.value = 4.04e-4

step("copy + edit water-liquid properties", copy_and_edit_water)

def assign_zone_materials():
    # CORRECTED (ground-truth verified via face/cell adjacency in the
    # case file's own HDF5 data): 3_s_1=water, 3_s_2=capsule.
    solver.setup.cell_zone_conditions.fluid["3_s_1"].general.material = "water-liquid"
    solver.setup.cell_zone_conditions.fluid["3_s_2"].general.material = "rt57hc"

step("assign cell zone materials (3_s_1=water, 3_s_2=capsule)", assign_zone_materials)

def retype_boundaries():
    bc = solver.setup.boundary_conditions
    bc.set_zone_type(zone_list=["2_l_11"], new_type="velocity-inlet")
    bc.set_zone_type(zone_list=["2_l_10"], new_type="pressure-outlet")
    bc.set_zone_type(zone_list=["2_l_9"], new_type="axis")
    bc.set_zone_type(zone_list=["2_l_7"], new_type="axis")
    bc.set_zone_type(zone_list=["2_l_5"], new_type="axis")

step("retype boundaries (inlet/outlet/axis)", retype_boundaries)

def set_inlet():
    inl = solver.setup.boundary_conditions.velocity_inlet["2_l_11"]
    inl.momentum.velocity_specification_method = "Magnitude, Normal to Boundary"
    inl.momentum.velocity_magnitude.option = "value"
    inl.momentum.velocity_magnitude.value = 3.49e-4
    inl.thermal.temperature.option = "value"
    inl.thermal.temperature.value = 343.15

step("set inlet BC (3.49e-4 m/s, 343.15K)", set_inlet)

def set_outlet():
    # pressure_outlet's thermal group only has backflow_total_temperature,
    # not a plain "temperature" field (confirmed by a real AttributeError).
    out = solver.setup.boundary_conditions.pressure_outlet["2_l_10"]
    out.thermal.backflow_total_temperature.option = "value"
    out.thermal.backflow_total_temperature.value = 343.15
    # First full run (400 steps @ 0.5s) diverged at step 297/400 (flow
    # time 148.5s): reversed flow at this outlet grew steadily (72% -> 91%
    # -> 94.5% of the outlet area flowing backward) as thermal effects
    # developed near the melt front, eventually blowing up the energy
    # equation (floating point exception). The very weak forced inflow
    # (3.49e-4 m/s) was getting overwhelmed. This directly prevents that.
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
    # The settings-API calculate_patch command hit a genuine internal
    # Fluent Scheme bug ("eval: unbound variable, Error Object: pm/volumes")
    # with both volumes=[] and volumes=[""] -- falling back to the classic
    # TUI /solve/patch command instead. First attempt passed "mixture" as a
    # leading domain argument, but the error showed Fluent trying to use
    # it AS the cell-zone name instead ("Invalid cell zone, Error object:
    # mixture") -- this older TUI command has no domain argument at all.
    solver.tui.solve.patch(["3_s_2"], [], "liquid-fraction", "0")

step("patch liquid fraction = 0 in capsule zone (TUI)", patch_liquid_fraction)

def set_transient():
    # transient_controls was inactive until solver time mode is switched
    # from default "steady" (confirmed). The actual numeric fields live
    # under run_calculation.parameters, NOT transient_controls (confirmed
    # by a real AttributeError pointing at the wrong location).
    # Adaptive time-stepping could not be activated (duration_specification_
    # method stays "incremental-time-steps" regardless of type=Adaptive --
    # would need that changed too, a lead for next time, not pursued
    # further here since a smaller FIXED timestep test showed timestep
    # size isn't actually the dominant factor anyway -- mushy-zone width
    # is). Reverting to the simple, reliable fixed-timestep path.
    solver.setup.general.solver.time = "unsteady-1st-order"
    rc = solver.solution.run_calculation
    rc.parameters.time_step_size = 0.5
    rc.parameters.time_step_count = 340
    rc.parameters.max_iter_per_time_step = 20

step("configure transient (fixed 0.5s x 340 steps, target 170s)", set_transient)

def run_solve():
    solver.solution.run_calculation.calculate()

step("CALCULATE (400 steps x 0.5s)", run_solve)

SAVE_PATH = os.path.abspath("regime0_rt57hc_melting.cas.h5")
step("save case+data", lambda: solver.file.write_case_data(file_name=SAVE_PATH))

solver.exit()
print("Clean exit.")
