"""
fluent_tank_discharge.py
========================
NEW IDEA (does not touch the existing scripts): the WHOLE TANK with the PCM
actually working. All 34 PCM capsules start HOT and fully melted; the tank water
starts COLD; there is no sun (evening / discharge). We run it transient and watch
every capsule SOLIDIFY while the surrounding tank water WARMS -- the coupled
"capsules heating the water, inside the tank" picture, all in one model.

Reuses the proven zone / material / melting setup of src/cfd/setup_system_case.py
(same mesh: tank + 34 capsules + collector panel; same PCM-as-fluid enthalpy-
porosity model; energy-only for stability). The only changes are the discharge
initial/boundary conditions:
  * external walls adiabatic (sealed, insulated) and NO solar flux
  * capsules patched hot & melted, water cold
  * transient, not steady

Energy-only (momentum frozen) is kept -- that is the setting under which this
multi-zone mushy case is stable (see setup_system_case.py notes). So melting
here is conduction-limited, consistent with the rest of the project.

Usage:
    python fluent_tank_discharge.py --regime 0 --hours 2          # headless, images+numbers
    python fluent_tank_discharge.py --regime 0 --hours 1 --live   # open the window and watch
"""
import argparse
import os
import traceback
from pathlib import Path

import pandas as pd
import ansys.fluent.core as pyfluent

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
PCM_DB = PROJECT / "data" / "objective1" / "pcm_database_tamilnadu.csv"
OPTIMAL_CSV = PROJECT / "results" / "tn_optimal_designs.csv"
MESH = HERE / "system_tank_pcm_panel.msh"
WORK = Path(r"C:\fluent_work")
OUTDIR = HERE / "figures" / "tank_discharge"
OUTDIR.mkdir(parents=True, exist_ok=True)

T_WATER_COLD = 303.15     # 30 C cold tank water at start of discharge
T_CAPSULE_HOT = 343.15    # 70 C fully-charged (melted) capsules
BAND_K = 10.0             # mushy band width (centred on Tm), as setup_system_case uses


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


def regime_pcm(regime):
    if OPTIMAL_CSV.exists():
        d = pd.read_csv(OPTIMAL_CSV)
        row = d[d.regime == regime]
        if len(row) and pd.notna(row.iloc[0].get("pcm")):
            return str(row.iloc[0]["pcm"])
    return {0: "PureTemp 58", 1: "RT57HC", 2: "RT57HC"}[regime]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regime", type=int, default=0, choices=(0, 1, 2))
    ap.add_argument("--hours", type=float, default=2.0)
    ap.add_argument("--dt", type=float, default=60.0)
    ap.add_argument("--live", action="store_true")
    args = ap.parse_args()

    if not MESH.exists():
        raise SystemExit(f"mesh not found: {MESH}")
    p = pcm_properties(regime_pcm(args.regime))
    n_steps = int(round(args.hours * 3600 / args.dt))
    tag = f"tank_regime{args.regime}_{p['name']}"
    print(f"\n=== WHOLE-TANK DISCHARGE — regime {args.regime}: {p['label']} ===", flush=True)
    print(f"  34 capsules start MELTED at {T_CAPSULE_HOT-273.15:.0f} C, "
          f"tank water starts COLD at {T_WATER_COLD-273.15:.0f} C, no sun", flush=True)
    print(f"  PCM: Tm {p['tm_k']-273.15:.1f} C, k {p['k']} W/mK, L {p['latent']/1000:.0f} kJ/kg", flush=True)
    print(f"  run: {args.dt} s x {n_steps} = {args.hours} h physical\n", flush=True)

    solver = pyfluent.launch_fluent(
        product_version="26.1.0", dimension=2, precision="double", processor_count=2,
        ui_mode="gui" if args.live else "no_gui", start_timeout=300, cwd=str(WORK))
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

    def zone_mean(field, zone):
        r = solver.solution.report_definitions
        nm = f"t_{field.replace('-', '_')}_{zone}"
        try:
            r.volume[nm] = {"report_type": "volume-average", "field": field, "cell_zones": [zone]}
        except Exception:
            pass
        return float(list(r.compute(report_defs=[nm])[0].values())[0][0])

    t_cap0 = zone_mean("temperature", "pcm")
    t_wat0 = zone_mean("temperature", "water")
    print(f"\n  start: capsules {t_cap0-273.15:.2f} C (melted), tank water {t_wat0-273.15:.2f} C", flush=True)
    if t_cap0 < T_CAPSULE_HOT - 3:
        solver.exit(); raise SystemExit(f"capsule patch did not take ({t_cap0:.1f} K) -- aborting")

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
    else:
        save_contour("temperature", f"{tag}_temp_START.png")

    step("transient", lambda: setattr(solver.setup.general.solver, "time", "unsteady-1st-order"))
    rc = solver.solution.run_calculation
    rc.parameters.time_step_size = args.dt
    rc.parameters.max_iter_per_time_step = 30

    steps_per_line = max(1, round(60 / args.dt))   # ~one line per simulated minute
    done = 0
    prev_tw = t_wat0
    print("\n  simulated    TANK WATER            PCM capsules", flush=True)
    print("  time         temperature           temperature   state", flush=True)
    print("  " + "-" * 60, flush=True)
    while done < n_steps:
        n = min(steps_per_line, n_steps - done)
        rc.parameters.time_step_count = n
        rc.calculate()
        done += n
        tw = zone_mean("temperature", "water")
        tc = zone_mean("temperature", "pcm")
        lf = zone_mean("liquid-fraction", "pcm")
        pcm_state = ("fully melted" if lf > 0.95 else "solidifying " if lf > 0.05 else "solid       ")
        water_state = "warming" if tw > prev_tw + 1e-3 else "steady "
        prev_tw = tw
        print(f"  t={done*args.dt/60:4.0f} min    {tw-273.15:6.2f} C ({water_state})     "
              f"{tc-273.15:6.2f} C   liq {lf:4.2f}  {pcm_state}", flush=True)
        if live_contour is not None:
            try: live_contour.display()
            except Exception: pass

    if not args.live:
        save_contour("temperature", f"{tag}_temp_END.png")
        save_contour("liquid-fraction", f"{tag}_liqfrac_END.png")
    print(f"\n  RESULT: tank water {t_wat0-273.15:.2f} C -> {tw-273.15:.2f} C; "
          f"capsules liquid fraction {lf:.3f} (started ~1.0)", flush=True)
    if args.live:
        input("Press Enter to close Fluent... ")
    solver.exit()
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
