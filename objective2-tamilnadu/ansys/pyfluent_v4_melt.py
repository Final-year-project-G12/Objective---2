"""
pyfluent_v4_melt.py
===================
The MELTING case: the v3 setup re-posed so the PCM actually changes phase,
plus natural convection in the melt, run for every shortlisted Tamil Nadu PCM
so the four can be compared on the same mesh and the same charging duty.

WHY V3 PRODUCED liquid-fraction = 0
-----------------------------------
v3 was not "too short" and the PCM was not mis-specified -- the inlet was
already 343.15 K (70 C), well above every candidate's melt point. The fault
was the INITIAL CONDITION combined with the flow rate:

    pyfluent_v3_setup.py:148   init.defaults["temperature"] = 298.15

That sets the WHOLE domain to 25 C, water included, while the inlet velocity
is 7.98e-5 m/s -- essentially stagnant. Hot water therefore had to travel the
length of the domain by advection at ~0.08 mm/s to reach the capsule. Over the
2140 s simulated it never arrived: the capsule peaked at 323.997 K (50.85 C),
short of C26's 329.65 K, so the enthalpy-porosity model correctly reported no
melt. The result was right for the case that was posed; the case was the wrong
question.

WHAT THIS CASE POSES INSTEAD
----------------------------
The physically meaningful question for this study is: during an established
charging window, does a capsule melt, and how do the candidates differ? So the
capsule starts cold and solid while the WATER starts at the collector delivery
temperature -- the capsule is immersed in hot water from t=0, which is what a
capsule mid-tank actually experiences once the collector loop is warm.

    water zone    343.15 K (70 C), the charging delivery temperature
    capsule zone  303.15 K (30 C), solid, below every candidate's solidus

WHY BUOYANCY IS OFF BY DEFAULT ON THIS MESH
-------------------------------------------
It is tempting to blame "momentum frozen" for the lack of melt and switch on
gravity + Boussinesq. That is the wrong fix HERE, for a geometry reason:
verify_zones.py shows this mesh is a HALF-SLICE with a symmetry plane at y=0
(zones 2_l_5, 2_l_10 and 2_l_11 all lie on y=0, and the domain spans
y=0..0.061 only). Gravity acting perpendicular to a symmetry plane is
physically inconsistent -- buoyancy would drive flow straight through a
boundary that exists precisely to forbid it, and the enthalpy-porosity model
would be resolving a plume it is not allowed to let cross.

So melting here is driven by the INITIAL CONDITION, not by momentum, and the
conduction resistance of the PCM (k ~ 0.15-0.24 W/mK) is the rate-limiting
step anyway -- far larger than the water-side convective resistance. The
convective enhancement of the melt film is handled empirically in the node
model (pcm_integration.liquid_convection_enhancement), which is the right
division of labour: CFD resolves the conduction-limited melt front, the node
model carries the empirical enhancement over a full year.

--convection re-enables gravity + Boussinesq for anyone who later rebuilds
this case on a full (non-symmetric) domain where buoyancy is admissible.

STABILITY
---------
The enthalpy-porosity model with buoyancy is the classic case that diverges on
a coarse mesh. Three levers, all carried over from this project's own
CFD_VERIFICATION.md practice:
  * 10 K mushy band above the real Tm (already v3 practice)
  * mushy-zone constant 1e5 (Fluent default; lower = more permeable, less stiff)
  * dt 0.5 s with 40 iterations/step, against v3's 10 s x 20

--no-convection falls back to conduction-only (gravity off). That still melts,
because melting here is driven by the hot-water initial condition, not by
momentum -- so there is always a result to report even if buoyancy diverges.

Usage:
  python pyfluent_v4_melt.py <case_path> <pcm_key> <water_zone> <capsule_zone> \
      <inlet_zone> <outlet_zone> <wall_outer_zone> <axis1> <axis2> <axis3> \
      <inlet_velocity_m_s> <dt_s> <n_steps> <save_basename> [--convection]
"""
import csv
import os
import sys
import traceback

import ansys.fluent.core as pyfluent

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
FLAGS = {a for a in sys.argv[1:] if a.startswith("--")}

CASE_PATH = os.path.abspath(ARGS[0])
PCM = ARGS[1].lower()
Z_WATER, Z_CAPSULE, Z_INLET, Z_OUTLET, Z_WALL = ARGS[2:7]
Z_AXIS = ARGS[7:10]
INLET_VELOCITY = float(ARGS[10])
DT = float(ARGS[11])
N_STEPS = int(ARGS[12])
SAVE_BASENAME = ARGS[13]
CONVECTION = "--convection" in FLAGS      # off by default -- see the symmetry-plane note above

# Properties as in v3 (sourced from data/objective1/pcm_database_tamilnadu.csv),
# extended to all four shortlisted PCMs so the comparison covers the whole
# Objective-1 shortlist rather than the two the deployable designs happen to use.
# beta = volumetric thermal expansion of the LIQUID, needed for Boussinesq;
# ~0.001 /K is the standard value for paraffins/alkanes in this class.
PCM_PROPS = {
    "rt57hc":     dict(name="rt57hc",     density=800, cp=2000, k=0.200, latent=250000, tm_k=329.65, beta=1.0e-3),
    "c26":        dict(name="c26",        density=770, cp=2290, k=0.238, latent=256000, tm_k=329.65, beta=1.0e-3),
    "c25":        dict(name="c25",        density=801, cp=2220, k=0.239, latent=238000, tm_k=327.15, beta=1.0e-3),
    "puretemp58": dict(name="puretemp58", density=850, cp=2110, k=0.150, latent=226000, tm_k=331.15, beta=1.0e-3),
    # DIAGNOSTIC ONLY, not a real material: C26's properties carrying C25's
    # melt point. C25 is the only PCM that diverges here, and it survived
    # changes to timestep, melt viscosity, the delh under-relaxation and the
    # mushy band. Those four all treat the symptom. This isolates the CAUSE by
    # changing exactly one number: if this diverges, the trigger is the 54 C
    # melt point against 70 C water on this mesh; if it runs, the trigger is
    # one of C25's other properties.
    "c26_at_c25_tm": dict(name="c26_at_c25_tm", density=770, cp=2290, k=0.238,
                          latent=256000, tm_k=327.15, beta=1.0e-3),
}[PCM]

T_WATER_INIT = 343.15      # 70 C -- collector delivery during charging
T_CAPSULE_INIT = 303.15    # 30 C -- solid, below every candidate's solidus
# Mushy band above each PCM's real Tm, as CFD_VERIFICATION.md records for v3.
#
# A 20 K band was tried for C25 and did NOT help, which also disproved the
# overshoot explanation: at 20 K the liquidus (347.15 K) sits ABOVE the 343.15 K
# water, so no cell can leave the mushy band at all, and it still diverged.
# Kept at 10 K so the three PCMs that already ran cleanly need no re-run.
MUSHY_BAND_K = 10.0

LOCAL_CWD = r"C:\fluent_work"
os.makedirs(LOCAL_CWD, exist_ok=True)

HISTORY_PATH = os.path.abspath(f"{SAVE_BASENAME}_melt_history.csv")


def step(name, fn):
    """Run a setup step, logging but tolerating failure.

    Appropriate for steps whose failure is visible in the result (a material
    property that did not take shows up as an absurd temperature). NOT
    appropriate for the initial condition -- see critical().
    """
    print(f"\n=== {name} ===", flush=True)
    try:
        result = fn()
        print(f"OK: {name}", flush=True)
        return result
    except Exception as e:
        print(f"FAILED: {name}: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
        return None


def critical(name, fn):
    """Run a step whose failure invalidates the run, and abort if it fails.

    v3 wrapped its liquid-fraction patch in the tolerant form. The patch raised
    'invalid command', the message scrolled past in a 120 kB log, and the solve
    proceeded from the wrong initial state to a published-looking answer. A
    wrong number that looks right is worse than a crash, so these abort.
    """
    print(f"\n=== {name} ===", flush=True)
    try:
        result = fn()
        print(f"OK: {name}", flush=True)
        return result
    except Exception as e:
        print(f"ABORT: {name}: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
        try:
            solver.exit()
        except Exception:
            pass
        sys.exit(2)


print(f"Launching Fluent for {PCM_PROPS['name']} "
      f"(Tm={PCM_PROPS['tm_k'] - 273.15:.1f}C, convection={CONVECTION})...", flush=True)
solver = pyfluent.launch_fluent(
    product_version="26.1.0", dimension=2, precision="double",
    processor_count=2, ui_mode="no_gui_or_graphics", start_timeout=120,
    cwd=LOCAL_CWD,
)
print("Connected.", flush=True)

step("read case", lambda: solver.file.read_case(file_name=CASE_PATH, pdf_file_name=""))
step("set planar", lambda: setattr(solver.setup.general.solver, "two_dim_space", "planar"))
step("enable energy", lambda: setattr(solver.setup.models.energy, "enabled", True))
step("set laminar", lambda: setattr(solver.setup.models.viscous, "model", "laminar"))
step("enable solidification-melting (TUI)",
     lambda: solver.tui.define.models.solidification_melting("yes"))

if CONVECTION:
    def enable_gravity():
        solver.setup.general.operating_conditions.gravity.enable = True
        solver.setup.general.operating_conditions.gravity.components = [0.0, -9.81]
        # Boussinesq needs a reference temperature; use the capsule's start state
        # so buoyancy is measured against the cold, solid condition.
        solver.setup.general.operating_conditions.operating_temperature.value = T_CAPSULE_INIT

    step("enable gravity (0, -9.81) for natural convection in the melt", enable_gravity)


def create_pcm():
    solver.setup.materials.fluid.create(PCM_PROPS["name"])
    m = solver.setup.materials.fluid[PCM_PROPS["name"]]
    if CONVECTION:
        # Boussinesq: constant density everywhere except the buoyancy term, the
        # standard treatment for melting driven by small density differences.
        m.density.option = "boussinesq"
        m.density.value = PCM_PROPS["density"]
        m.thermal_expansion_coefficient.option = "constant"
        m.thermal_expansion_coefficient.value = PCM_PROPS["beta"]
    else:
        m.density.option = "constant"
        m.density.value = PCM_PROPS["density"]
    m.specific_heat.option = "constant"; m.specific_heat.value = PCM_PROPS["cp"]
    m.thermal_conductivity.option = "constant"; m.thermal_conductivity.value = PCM_PROPS["k"]
    m.melting_heat.option = "constant"; m.melting_heat.value = PCM_PROPS["latent"]
    m.tsolidus.option = "constant"; m.tsolidus.value = PCM_PROPS["tm_k"]
    m.tliqidus.option = "constant"; m.tliqidus.value = PCM_PROPS["tm_k"] + MUSHY_BAND_K
    # Molten-PCM viscosity. Deliberately set ~3 orders above real molten
    # paraffin (3.5e-3 Pa s) to make the melt IMMOBILE.
    #
    # This is not a fudge; it is the momentum counterpart of the modelling
    # decision recorded at the top of this file. Buoyancy is excluded because
    # the mesh has a symmetry plane, so there is no physical driving force for
    # melt motion in this case -- yet enthalpy-porosity stops damping momentum
    # the moment a cell reaches liquid fraction 1, leaving the molten PCM free
    # to chase numerical noise.
    #
    # That is exactly what broke C25, and only C25: its liquidus (337.15 K) is
    # the lowest of the four, so it is the only candidate that FULLY melts
    # inside the 6 h window. The three that stall below liquid fraction 1 keep
    # their Darcy damping and ran with zero divergences; C25 lost its damping,
    # then diverged -- to the 5000 K ceiling at dt=20 s and to the 1 K floor at
    # dt=5 s, which is the signature of a momentum instability rather than a
    # timestep problem.
    #
    # Making the melt immobile keeps the physics self-consistent (conduction-
    # limited melting, empirical convection enhancement carried by the node
    # model) and applies identically to all four PCMs, so the comparison stays
    # fair.
    #
    # RETRACTED: the 10 Pa s "immobile melt" value this comment originally
    # argued for is WRONG and is not used. Tested directly afterwards, C26 --
    # which runs clean at 3.5e-3 with every other setting identical -- diverged
    # to 4714 C at 10 Pa s. The stiff viscous term destabilises the momentum
    # equations instead of calming them, so raising viscosity made things worse
    # for every PCM, not just C25. Real molten-paraffin viscosity is used.
    m.viscosity.option = "constant"
    m.viscosity.value = 3.5e-3


step(f"create {PCM_PROPS['name']} (Tm={PCM_PROPS['tm_k'] - 273.15:.1f}C, {MUSHY_BAND_K:.0f}K mushy band)",
     create_pcm)


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


step(f"assign materials ({Z_WATER}=water, {Z_CAPSULE}={PCM_PROPS['name']})", assign_zone_materials)


def retype_boundaries():
    bc = solver.setup.boundary_conditions
    bc.set_zone_type(zone_list=[Z_INLET], new_type="velocity-inlet")
    bc.set_zone_type(zone_list=[Z_OUTLET], new_type="pressure-outlet")
    for z in Z_AXIS:
        bc.set_zone_type(zone_list=[z], new_type="axis")


step(f"retype boundaries (inlet={Z_INLET}, outlet={Z_OUTLET}, axis={Z_AXIS})", retype_boundaries)


def set_inlet():
    inl = solver.setup.boundary_conditions.velocity_inlet[Z_INLET]
    inl.momentum.velocity_specification_method = "Magnitude, Normal to Boundary"
    inl.momentum.velocity_magnitude.option = "value"
    inl.momentum.velocity_magnitude.value = INLET_VELOCITY
    inl.thermal.temperature.option = "value"
    inl.thermal.temperature.value = T_WATER_INIT


step(f"set inlet ({INLET_VELOCITY:.4e} m/s, {T_WATER_INIT}K)", set_inlet)


def set_outlet():
    out = solver.setup.boundary_conditions.pressure_outlet[Z_OUTLET]
    out.thermal.backflow_total_temperature.option = "value"
    out.thermal.backflow_total_temperature.value = T_WATER_INIT
    out.momentum.prevent_reverse_flow = True


step("set outlet (backflow 343.15K)", set_outlet)

step("set wall_outer adiabatic",
     lambda: (setattr(solver.setup.boundary_conditions.wall[Z_WALL].thermal,
                      "thermal_condition", "Heat Flux"),
              setattr(solver.setup.boundary_conditions.wall[Z_WALL].thermal.heat_flux,
                      "value", 0)))


def initialize():
    """Initialize the whole domain HOT, then patch the capsule back to cold.

    This is the correction to v3. Initializing everything to 298.15 K left the
    capsule surrounded by cold water that never warmed in time; initializing to
    the delivery temperature and patching only the capsule puts the capsule in
    the condition it is actually in during charging.
    """
    init = solver.solution.initialization
    init.initialization_type = "standard"
    init.defaults["temperature"] = T_WATER_INIT
    init.initialize()


step(f"standard initialize domain at {T_WATER_INIT}K (water hot)", initialize)


def _zone_mean(field):
    """Volume-average of `field` over the capsule zone."""
    r = solver.solution.report_definitions
    name = f"chk_{field.replace('-', '_')}"
    try:
        r.volume[name] = {"report_type": "volume-average",
                          "field": field, "cell_zones": [Z_CAPSULE]}
    except Exception:
        pass
    return float(list(r.compute(report_defs=[name])[0].values())[0][0])


def patch_verified(field, value, tol):
    """Patch the capsule zone and CONFIRM the field actually moved.

    The argument form matters and is not guessable: probe_patch_api.py tried
    five variants against this build and only the positional-TUI form bound --
    the settings API rejects both `cell_zones` and `zones` as invalid keys, and
    v3's `tui.solve.patch([zone], [], ...)` raised 'invalid command'.

    More importantly, v3 LOGGED that failure and carried on. The capsule was
    then left at whatever initialization had set, and the run produced a
    confident, wrong liquid-fraction of 0. So a patch here is not trusted
    because the call returned -- the value is read back and a mismatch is
    fatal.
    """
    solver.tui.solve.patch(Z_CAPSULE, "()", field, str(value))
    got = _zone_mean(field)
    if abs(got - value) > tol:
        raise RuntimeError(
            f"patch of {field} did not take: capsule mean is {got:.4f}, "
            f"expected {value:.4f} (tol {tol}). Refusing to solve a case whose "
            f"initial condition is not the one intended -- this is exactly how "
            f"v3 reported liquid_fraction=0 from a capsule that was never cold.")
    print(f"  verified: capsule {field} = {got:.4f}")


critical(f"patch capsule to {T_CAPSULE_INIT}K and VERIFY",
         lambda: patch_verified("temperature", T_CAPSULE_INIT, 0.5))

def verify_fully_solid():
    """Confirm the capsule is fully solid -- without patching liquid-fraction.

    'liquid-fraction' is not a patchable TUI variable in this build (it returns
    'invalid command'), and it does not need to be: the enthalpy-porosity model
    derives liquid fraction FROM temperature, and the patch above put the
    capsule at 303.15 K, which is 26.5 K below C26's 329.65 K solidus. So the
    solid state is implied. What matters is that it is checked rather than
    assumed -- v3's whole error was assuming an initial condition it never
    confirmed.
    """
    lf = _zone_mean("liquid-fraction")
    if lf > 1e-3:
        raise RuntimeError(
            f"capsule liquid fraction is {lf:.4f}, not 0, despite being patched to "
            f"{T_CAPSULE_INIT} K (solidus {PCM_PROPS['tm_k']} K). The melt curve "
            f"would start part-melted and understate the melting time.")
    print(f"  verified: capsule liquid-fraction = {lf:.6f} (fully solid)")


critical("verify capsule is fully solid at t=0", verify_fully_solid)


def set_methods():
    """Pressure-velocity coupling and discretisation order.

    This is the lever CFD_VERIFICATION.md recorded as still open after six
    other hypotheses for the C25 divergence were disproved. probe_methods.py
    read the real options off the solver rather than guessing them:

        p_v_coupling.flow_scheme   SIMPLE (default) | SIMPLEC | PISO | Coupled
        discretization_scheme      mom / pressure / temperature

    Defaults here stay at Fluent's own (SIMPLE, second order) so the three
    PCMs that already ran cleanly are unaffected. V4_SCHEME and V4_ORDER opt
    into the stabilised combination for the case that needs it.
    """
    scheme = os.environ.get("V4_SCHEME", "")
    order = os.environ.get("V4_ORDER", "")
    if scheme:
        try:
            solver.solution.methods.p_v_coupling.flow_scheme = scheme
            print(f"  p-v coupling = {scheme}")
        except Exception as e:
            print(f"  p-v coupling {scheme!r} NOT set: {type(e).__name__}: {e}")
    if order == "first":
        d = solver.solution.methods.discretization_scheme
        for key, val in (("mom", "first-order-upwind"),
                         ("temperature", "first-order-upwind"),
                         ("pressure", "standard")):
            try:
                d[key] = val
            except Exception as e:
                print(f"  discretisation {key} NOT set: {type(e).__name__}: {e}")
        print(f"  discretisation = {d()}")


step("pressure-velocity coupling / discretisation", set_methods)


def set_under_relaxation():
    """Under-relax the liquid-fraction update -- the standard enthalpy-porosity fix.

    Diagnosis trail for C25, which is the only PCM that diverges here:
      * not the timestep -- dt 20 s blew up to the 5000 K ceiling, dt 5 s blew
        up to the 1 K floor. A timestep problem gets better when dt shrinks.
      * not the material -- probe_c25_material.py read every property back from
        the solver and all seven bind correctly, viscosity included.
      * not melt mobility -- viscosity at 10 Pa s (3 orders above molten
        paraffin, i.e. immobile) still diverged, and at liquid fraction 0.19.

    What is left is the latent-heat source itself. C25 has the lowest liquidus
    of the four (337.15 K), so against 343.15 K water it carries 6.0 K of
    superheat where C26 carries 3.5 K -- the near-wall cells cross the whole
    mushy band in a single step and the liquid-fraction update oscillates.
    Under-relaxing that update is the documented remedy, and it is applied to
    ALL FOUR PCMs so the comparison is not contaminated by a per-PCM setting.
    """
    urf = solver.solution.controls.under_relaxation
    print(f"  before: {urf()}")
    # 'delh' is the enthalpy / liquid-fraction update factor that the
    # solidification-melting model adds (default 0.9); probe_urf.py confirmed
    # the available keys are exactly body-force, delh, density, mom, pressure
    # and temperature -- the TUI names guessed earlier ('liquid-fraction-update',
    # 'energy') are not among them, which is why that attempt silently changed
    # nothing and reproduced the identical 919.27 K divergence.
    for key, val in (("delh", float(os.environ.get("V4_DELH", 0.2))),
                     ("temperature", float(os.environ.get("V4_URF_T", 0.8))),
                     ("mom", 0.5)):
        try:
            urf[key] = val
        except Exception as e:
            print(f"  under-relaxation {key} NOT set: {type(e).__name__}: {e}")
    print(f"  after:  {urf()}")


step("under-relax liquid-fraction update (enthalpy-porosity stability)",
     set_under_relaxation)


def set_transient():
    solver.setup.general.solver.time = "unsteady-1st-order"
    rc = solver.solution.run_calculation
    rc.parameters.time_step_size = DT
    rc.parameters.time_step_count = N_STEPS
    rc.parameters.max_iter_per_time_step = 40


step(f"configure transient ({DT}s x {N_STEPS} = {DT * N_STEPS:.0f}s physical)", set_transient)


def run_in_chunks():
    """Solve in chunks, recording the melt curve as it goes.

    The deliverable is the melt HISTORY (liquid fraction against time) for each
    PCM, not just the end state -- that is what makes the four comparable. So
    the run is broken into chunks and probed between them; a divergence part way
    through still leaves a usable partial curve on disk.
    """
    rc = solver.solution.run_calculation
    chunk = max(1, N_STEPS // 20)
    rows = [{"time_s": 0.0, "liquid_fraction": 0.0, "T_capsule_mean_K": T_CAPSULE_INIT}]
    done = 0
    while done < N_STEPS:
        n = min(chunk, N_STEPS - done)
        rc.parameters.time_step_count = n
        rc.calculate()
        done += n
        try:
            lf, tm = _zone_mean("liquid-fraction"), _zone_mean("temperature")
        except Exception as e:
            print(f"  probe failed at t={done * DT:.0f}s: {e}", flush=True)
            lf, tm = float("nan"), float("nan")
        rows.append({"time_s": done * DT, "liquid_fraction": lf, "T_capsule_mean_K": tm})
        print(f"  t={done * DT:8.0f}s  liquid_fraction={lf:.4f}  T_mean={tm:.2f}K", flush=True)
        with open(HISTORY_PATH, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["time_s", "liquid_fraction", "T_capsule_mean_K"])
            w.writeheader()
            w.writerows(rows)
    return rows


step(f"SOLVE {N_STEPS} steps, probing the melt curve", run_in_chunks)

step("save case+data",
     lambda: solver.file.write_case_data(file_name=os.path.abspath(f"{SAVE_BASENAME}.cas.h5")))

solver.exit()
print(f"Clean exit. Melt history -> {HISTORY_PATH}", flush=True)
