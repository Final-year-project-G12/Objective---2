"""
fluent_tank_discharge_criteria.py
=================================
COPY of ../fluent_tank_discharge.py (the whole-tank discharge idea: all capsules start
HOT and fully melted, tank water starts COLD, no sun, sealed insulated tank ->
watch the capsules SOLIDIFY while the water WARMS), driven by this folder's
`criteria.json` instead of the fixed 34-capsule mesh.

What differs from ../fluent_tank_discharge.py (and nothing else):
  * the mesh is built here, for THIS criteria's capsule count / radius
    (make_system_mesh.py = copy of src/cfd/make_system_mesh.py + an n_capsules argument);
  * a time-series CSV is written (every simulated minute) and a terminal table is
    printed every --print-every minutes, with energy columns;
  * START / MID / END pictures of temperature and liquid fraction are saved;
  * the physics set-up (materials, melting model, adiabatic walls, energy-only,
    patch capsules hot) is byte-for-byte the original's.

2-D PROXY: see criteria.json["proxy"] - the planar slice draws `drawn_capsules`
capsules of inner radius `r_in_2d_m`; the optimum is 34 capsules / 20 mm.

Usage (from this folder):
    python fluent_tank_discharge_criteria.py --hours 2              # headless: images + numbers
    python fluent_tank_discharge_criteria.py --hours 1 --live       # open the Fluent window and watch
"""
import argparse
import csv
import json
import sys
import time
import traceback
from pathlib import Path

import pandas as pd
import ansys.fluent.core as pyfluent

HERE = Path(__file__).resolve().parent                  # this criteria folder
PROJECT = HERE.parents[1]                               # objective2_design_optimization/
PCM_DB = PROJECT / "data" / "objective1" / "pcm_database_tamilnadu.csv"
CRIT = json.loads((HERE / "criteria.json").read_text(encoding="utf-8"))
MESH = HERE / "mesh" / "tank_criteria.msh"
WORK = Path(r"C:\fluent_work")
OUTDIR = HERE / "figures"
OUTDIR.mkdir(parents=True, exist_ok=True)
MESH.parent.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(HERE))
from make_system_mesh import write_system_msh            # noqa: E402

T_WATER_COLD = 303.15     # 30 C cold tank water at start of discharge
T_CAPSULE_HOT = 343.15    # 70 C fully-charged (melted) capsules
BAND_K = 10.0             # mushy band width (centred on Tm), as setup_system_case uses
NX, NY = CRIT["mesh"]["nx"], CRIT["mesh"]["ny"]


def pcm_properties(name):
    db = pd.read_csv(PCM_DB)
    row = db[db.name.str.strip().str.lower() == name.strip().lower()]
    if row.empty:
        row = db[db.name.str.contains(name.strip(), case=False, regex=False)]
    if row.empty:
        raise SystemExit(f"PCM {name!r} not found in {PCM_DB.name}")
    r = row.iloc[0]
    return {
        "name": "".join(c for c in r["name"].lower() if c.isalnum())[:20],
        "label": r["name"],
        "density": float((r.density_solid_kg_m3 + r.density_liquid_kg_m3) / 2),
        "cp": float((r.Cp_solid_kJ_kgK + r.Cp_liquid_kJ_kgK) / 2 * 1000),
        "k": float(r.TC_W_mK),
        "latent": float(r.latent_heat_kJ_kg * 1000),
        "tm_k": float(r.Tm_C) + 273.15,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=CRIT["run"]["hours"])
    ap.add_argument("--dt", type=float, default=CRIT["run"]["dt_s"])
    ap.add_argument("--print-every", type=float, default=10.0, help="terminal table row every N simulated minutes")
    ap.add_argument("--frame-every", type=float, default=5.0, help="save a temp+liqfrac frame every N simulated minutes (for the video)")
    ap.add_argument("--live", action="store_true")
    args = ap.parse_args()
    FRAMES = OUTDIR / "frames"
    FRAMES.mkdir(parents=True, exist_ok=True)

    p = pcm_properties(CRIT["pcm"])
    n_steps = int(round(args.hours * 3600 / args.dt))
    tag = CRIT["key"]

    # ---- build THIS criteria's mesh -------------------------------------------------
    info = write_system_msh(MESH, r_in_m=CRIT["proxy"]["r_in_2d_m"], n_capsules=CRIT["proxy"]["drawn_capsules"],
                            fraction=0.15, arrangement=CRIT["design"]["arrangement"], nx=NX, ny=NY)
    cell_area = (info["domain_W_m"] / NX) * (info["domain_H_m"] / NY)         # m2 of one mesh cell (per 1 m depth)
    a_water = info["cell_zones"]["water"] * cell_area
    a_pcm = info["cell_zones"].get("pcm", 0) * cell_area
    print(f"\n=== WHOLE-TANK DISCHARGE - {CRIT['title']} ===", flush=True)
    print(f"  3-D design : R_in {CRIT['design']['R_in']*1000:.1f} mm, {CRIT['n_3d']} capsules "
          f"({CRIT['frac_of_optimal_N']*100:.0f} % of optimal 104), fraction {CRIT['fraction_pct']:.1f} %, "
          f"flow {CRIT['design']['flow']:.4f} kg/s, {CRIT['design']['arrangement']}", flush=True)
    print(f"  drawn here : {info['n_capsules_drawn']} capsules, inner R {CRIT['proxy']['r_in_2d_m']*1000:.1f} mm "
          f"(2-D proxy), mesh {info['n_cells']} cells; PCM area {a_pcm*1e4:.1f} cm2, water area {a_water*1e4:.0f} cm2", flush=True)
    print(f"  capsules start MELTED at {T_CAPSULE_HOT-273.15:.0f} C, tank water starts COLD at {T_WATER_COLD-273.15:.0f} C, no sun", flush=True)
    print(f"  PCM: {p['label']}, Tm {p['tm_k']-273.15:.1f} C, k {p['k']} W/mK, L {p['latent']/1000:.0f} kJ/kg", flush=True)
    print(f"  run: {args.dt} s x {n_steps} = {args.hours} h physical\n", flush=True)

    solver = pyfluent.launch_fluent(
        product_version="26.1.0", dimension=2, precision="double", processor_count=2,
        ui_mode="gui" if args.live else "no_gui", start_timeout=300, cwd=str(WORK), start_watchdog=False)
    print("LAUNCH OK", flush=True)

    def step(label, fn):
        try:
            fn(); print(f"  ok: {label}", flush=True)
        except Exception as e:
            print(f"  FAILED {label}: {type(e).__name__}: {e}", flush=True)
            traceback.print_exc()

    step("read mesh", lambda: solver.settings.file.read_mesh(file_name=str(MESH)))
    step("planar", lambda: setattr(solver.setup.general.solver, "two_dim_space", "planar"))
    step("energy on", lambda: setattr(solver.setup.models.energy, "enabled", True))
    step("laminar", lambda: setattr(solver.setup.models.viscous, "model", "laminar"))
    step("solidification-melting on",
         lambda: solver.tui.define.models.solidification_melting("yes"))

    def make_pcm():
        solver.setup.materials.fluid.create(p["name"])
        m = solver.setup.materials.fluid[p["name"]]
        m.density.option = "constant"; m.density.value = p["density"]
        m.specific_heat.option = "constant"; m.specific_heat.value = p["cp"]
        m.thermal_conductivity.option = "constant"; m.thermal_conductivity.value = p["k"]
        m.melting_heat.option = "constant"; m.melting_heat.value = p["latent"]
        half = BAND_K / 2.0
        m.tsolidus.option = "constant"; m.tsolidus.value = p["tm_k"] - half
        m.tliqidus.option = "constant"; m.tliqidus.value = p["tm_k"] + half
    step("create PCM material", make_pcm)

    def make_water():
        solver.setup.materials.database.copy_materials(type="fluid", form=False, names=["water-liquid"])
        w = solver.setup.materials.fluid["water-liquid"]
        w.density.value = 985.0; w.specific_heat.value = 4186.0
        w.thermal_conductivity.value = 0.63; w.viscosity.value = 5.0e-4
    step("water material", make_water)
    step("aluminium material",
         lambda: solver.setup.materials.database.copy_materials(type="solid", form=False, names=["aluminum"]))

    def assign():
        fz = solver.setup.cell_zone_conditions.fluid
        sz = solver.setup.cell_zone_conditions.solid
        for z in ("water", "panel", "riser"):
            fz[z].general.material = "water-liquid"
        fz["pcm"].general.material = p["name"]
        for z in ("shell", "absorber"):
            sz[z].general.material = "aluminum"
    step("assign zone materials", assign)

    # Discharge: NO sun, sealed insulated tank -> every external wall adiabatic.
    def walls():
        w = solver.setup.boundary_conditions.wall
        for name in ("wall_absorber_ext", "wall_water_ext", "wall_riser_ext", "wall_panel_ext"):
            try:
                w[name].thermal.thermal_condition = "Heat Flux"
                w[name].thermal.heat_flux.value = 0.0
            except Exception as e:
                print(f"    (wall {name}: {type(e).__name__})", flush=True)
    step("adiabatic external walls (no solar)", walls)

    # energy-only (freeze momentum) -- the stable setting for this mushy case
    def freeze_flow():
        eq = solver.settings.solution.controls.equations
        for key in ("flow", "Flow"):
            if key in eq:
                eq[key] = False
                return
    step("freeze flow (energy-only)", freeze_flow)

    # initialise COLD everywhere, then patch the CAPSULES hot & melted
    step("initialize cold", lambda: (
        setattr(solver.solution.initialization, "initialization_type", "standard"),
        solver.tui.solve.initialize.set_defaults("temperature", str(T_WATER_COLD)),
        solver.solution.initialization.standard_initialize()))
    step("patch capsules hot",
         lambda: solver.tui.solve.patch("pcm", "()", "temperature", str(T_CAPSULE_HOT)))

    def zone_stat(field, zone, kind="average"):
        r = solver.solution.report_definitions
        nm = f"s_{kind}_{field.replace('-', '_')}_{zone}"
        try:
            r.volume[nm] = {"report_type": f"volume-{kind}", "field": field, "cell_zones": [zone]}
        except Exception:
            pass
        return float(list(r.compute(report_defs=[nm])[0].values())[0][0])

    t_cap0 = zone_stat("temperature", "pcm")
    t_wat0 = zone_stat("temperature", "water")
    print(f"\n  start: capsules {t_cap0-273.15:.2f} C (melted), tank water {t_wat0-273.15:.2f} C", flush=True)
    if t_cap0 < T_CAPSULE_HOT - 3:
        solver.exit(); raise SystemExit(f"capsule patch did not take ({t_cap0:.1f} K) -- aborting")
    lf0 = zone_stat("liquid-fraction", "pcm")

    g = solver.settings.results.graphics
    try:
        g.picture.use_window_resolution = False
        g.picture.x_resolution = 1500; g.picture.y_resolution = 1100
    except Exception:
        pass

    def save_contour(field, fname):
        try:
            name = f"tc_{field.replace('-', '_')}"
            if name not in g.contour:
                g.contour.create(name)
            c = g.contour[name]
            c.field = field; c.surfaces_list = []; c.filled = True; c.node_values = True
            c.display()
            g.picture.save_picture(file_name=str(OUTDIR / fname))
            ok = (OUTDIR / fname).exists()
            print(f"  saved {fname}: {'OK' if ok else 'EMPTY'}", flush=True)
        except Exception as e:
            print(f"  (save {fname}: {type(e).__name__}: {e})", flush=True)

    live_contour = None
    if args.live:
        try:
            g.contour.create("tc_live")
            live_contour = g.contour["tc_live"]
            live_contour.field = "temperature"; live_contour.surfaces_list = []
            live_contour.filled = True; live_contour.node_values = True
            live_contour.display()
            print("  temperature contour opened -- re-renders each step\n", flush=True)
        except Exception as e:
            print(f"  (live contour: {type(e).__name__})\n", flush=True)
    save_contour("temperature", f"{tag}_temp_START.png")
    save_contour("liquid-fraction", f"{tag}_liqfrac_START.png")

    def save_frame(minute_label):
        try:
            name = "tc_temperature"
            if name not in g.contour:
                g.contour.create(name)
            c = g.contour[name]; c.field = "temperature"; c.surfaces_list = []; c.filled = True; c.node_values = True
            c.range_option.option = "auto-range-off"
            c.range_option.auto_range_off.minimum = T_WATER_COLD; c.range_option.auto_range_off.maximum = T_CAPSULE_HOT
            c.display()
            g.picture.save_picture(file_name=str(FRAMES / f"temp_{minute_label}.png"))
            name2 = "tc_liquid_fraction"
            if name2 not in g.contour:
                g.contour.create(name2)
            c2 = g.contour[name2]; c2.field = "liquid-fraction"; c2.surfaces_list = []; c2.filled = True; c2.node_values = True
            c2.range_option.option = "auto-range-off"
            c2.range_option.auto_range_off.minimum = 0.0; c2.range_option.auto_range_off.maximum = 1.0
            c2.display()
            g.picture.save_picture(file_name=str(FRAMES / f"liqfrac_{minute_label}.png"))
        except Exception as e:
            print(f"  (frame {minute_label}: {type(e).__name__}: {e})", flush=True)
    save_frame("000")

    step("transient", lambda: setattr(solver.setup.general.solver, "time", "unsteady-1st-order"))
    rc = solver.solution.run_calculation
    rc.parameters.time_step_size = args.dt
    rc.parameters.max_iter_per_time_step = 30

    steps_per_min = max(1, round(60 / args.dt))
    print_every = max(1, int(round(args.print_every)))
    csv_path = HERE / f"{tag}_discharge_timeseries.csv"
    fh = open(csv_path, "w", newline="")
    wr = csv.writer(fh)
    wr.writerow(["minute", "water_avg_C", "water_max_C", "pcm_avg_C", "pcm_min_C", "liquid_fraction",
                 "heat_to_water_kJ_per_m", "pcm_energy_released_kJ_per_m"])
    rho_w, cp_w = 985.0, 4186.0
    t_wall0 = time.time()

    done = 0
    tw, tc, lf = t_wat0, t_cap0, lf0
    prev_tw = t_wat0
    hdr = (f"  {'sim time':>9s} | {'TANK WATER avg':>14s} {'max':>7s} | {'PCM avg':>8s} {'PCM min':>8s} | "
           f"{'liq.frac':>8s} {'state':<13s} | {'heat->water':>11s} | wall")
    print("\n" + hdr, flush=True)
    print("  " + "-" * (len(hdr) - 2), flush=True)
    wr.writerow([0, f"{t_wat0-273.15:.3f}", f"{t_wat0-273.15:.3f}", f"{t_cap0-273.15:.3f}", f"{t_cap0-273.15:.3f}",
                 f"{lf0:.4f}", "0.0", "0.0"]); fh.flush()
    while done < n_steps:
        n = min(steps_per_min, n_steps - done)
        rc.parameters.time_step_count = n
        rc.calculate()
        done += n
        minute = done * args.dt / 60.0
        tw = zone_stat("temperature", "water")
        twmx = zone_stat("temperature", "water", "max")
        tc = zone_stat("temperature", "pcm")
        tcmn = zone_stat("temperature", "pcm", "min")
        lf = zone_stat("liquid-fraction", "pcm")
        q_w = rho_w * cp_w * a_water * (tw - t_wat0) / 1000.0           # kJ per metre of depth
        q_p = a_pcm * p["density"] * (p["latent"] * (lf0 - lf) + p["cp"] * (t_cap0 - tc)) / 1000.0
        wr.writerow([f"{minute:.2f}", f"{tw-273.15:.3f}", f"{twmx-273.15:.3f}", f"{tc-273.15:.3f}", f"{tcmn-273.15:.3f}",
                     f"{lf:.4f}", f"{q_w:.2f}", f"{q_p:.2f}"]); fh.flush()
        state = "fully melted" if lf > 0.95 else "solidifying" if lf > 0.05 else "solid"
        if int(round(minute)) % print_every == 0 or done >= n_steps:
            print(f"  t={minute:6.0f}min | {tw-273.15:10.2f} C {twmx-273.15:7.2f} | {tc-273.15:6.2f} C {tcmn-273.15:6.2f} C | "
                  f"{lf:8.3f} {state:<13s} | {q_w:8.1f} kJ | {time.time()-t_wall0:5.0f}s", flush=True)
        if live_contour is not None:
            try: live_contour.display()
            except Exception: pass
        if done == n_steps // 2:
            save_contour("temperature", f"{tag}_temp_MID.png")
            save_contour("liquid-fraction", f"{tag}_liqfrac_MID.png")
        if int(round(minute)) % max(1, int(round(args.frame_every))) == 0:
            save_frame(f"{int(round(minute)):04d}")
    fh.close()
    save_frame(f"{int(round(minute)):04d}_FINAL")

    save_contour("temperature", f"{tag}_temp_END.png")
    save_contour("liquid-fraction", f"{tag}_liqfrac_END.png")
    print(f"\n  RESULT [{CRIT['title']}]: tank water {t_wat0-273.15:.2f} C -> {tw-273.15:.2f} C "
          f"(+{tw-t_wat0:.2f} K); capsules liquid fraction {lf0:.3f} -> {lf:.3f}; "
          f"heat given to water {rho_w*cp_w*a_water*(tw-t_wat0)/1000:.1f} kJ per m depth", flush=True)
    print(f"  time series: {csv_path.name}", flush=True)
    if args.live:
        input("Press Enter to close Fluent... ")
    solver.exit()
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
