"""
fluent_discharge_demo.py
========================
DISCHARGE demo: the reverse of fluent_live_demo.py. Here the PCM capsule starts
HOT and fully melted (a fully-charged capsule) sitting in COLD water, and we
watch it SOLIDIFY and release its stored heat INTO the water -- i.e. the PCM
heating the water. This is the evening / payoff half of the cycle.

Charging (fluent_live_demo.py):  hot water  -> melts the capsule  (water heats PCM)
Discharge (this file):           hot capsule -> warms the water   (PCM heats water)

The water pocket is sealed (inlet & outlet set to adiabatic walls, no forced
flow), so the water warms purely from the capsule's released heat -- the clean
way to show "the PCM heats the water". Melting here is conduction-limited, same
assumption the project uses throughout (buoyancy off on the symmetry mesh).

Per regime the PCM differs, so the discharge differs:
    Regime 0 -> PureTemp 58 (solidifies ~58 C)
    Regime 1 -> RT57HC      (solidifies ~57 C)
    Regime 2 -> RT57HC      (same PCM as Regime 1)

Usage:
    python fluent_discharge_demo.py --regime 0            # headless, saves images + numbers
    python fluent_discharge_demo.py --regime 0 --hours 1  # shorter
    python fluent_discharge_demo.py --regime 0 --live     # open the Fluent window and watch
"""
import argparse
import os
from pathlib import Path

import pandas as pd
import ansys.fluent.core as pyfluent

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
PCM_DB = PROJECT / "data" / "objective1" / "pcm_database_tamilnadu.csv"
OPTIMAL_CSV = PROJECT / "results" / "tn_optimal_designs.csv"
WORK = Path(r"C:\fluent_work")
OUTDIR = HERE / "figures" / "discharge"
OUTDIR.mkdir(parents=True, exist_ok=True)

T_WATER_COLD = 303.15     # 30 C -- cold demand/tank water at the start of discharge
T_CAPSULE_HOT = 343.15    # 70 C -- a fully-charged (melted) capsule
MUSHY_BAND_K = 10.0
ZONES = dict(water="3_s_1", capsule="3_s_2", inlet="2_l_7", outlet="2_l_9",
             wall="2_l_8", axis=["2_l_10", "2_l_11", "2_l_5"])


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
    ap.add_argument("--dt", type=float, default=20.0)
    ap.add_argument("--live", action="store_true", help="open the Fluent window (gui) and watch")
    args = ap.parse_args()

    pcm_name = regime_pcm(args.regime)
    p = pcm_properties(pcm_name)
    n_steps = int(round(args.hours * 3600 / args.dt))
    tag = f"regime{args.regime}_{p['name']}"
    print(f"\n=== DISCHARGE demo — regime {args.regime}: {p['label']} ===", flush=True)
    print(f"  capsule starts HOT & melted at {T_CAPSULE_HOT-273.15:.0f} C, "
          f"water starts COLD at {T_WATER_COLD-273.15:.0f} C", flush=True)
    print(f"  PCM: Tm {p['tm_k']-273.15:.1f} C, k {p['k']} W/mK, L {p['latent']/1000:.0f} kJ/kg", flush=True)
    print(f"  run: {args.dt} s x {n_steps} = {args.hours} h physical\n", flush=True)

    mesh = WORK / f"regime{args.regime}_v3_mesh_only.cas.h5"
    if not mesh.exists():
        raise SystemExit(f"mesh not found: {mesh}")

    solver = pyfluent.launch_fluent(
        product_version="26.1.0", dimension=2, precision="double", processor_count=2,
        ui_mode="gui" if args.live else "no_gui", start_timeout=180, cwd=str(WORK))
    print("LAUNCH OK", flush=True)

    solver.file.read_case(file_name=str(mesh), pdf_file_name="")
    solver.setup.general.solver.two_dim_space = "planar"
    solver.setup.models.energy.enabled = True
    solver.setup.models.viscous.model = "laminar"
    solver.tui.define.models.solidification_melting("yes")

    # PCM material
    solver.setup.materials.fluid.create(p["name"])
    m = solver.setup.materials.fluid[p["name"]]
    m.density.option = "constant"; m.density.value = p["density"]
    m.specific_heat.option = "constant"; m.specific_heat.value = p["cp"]
    m.thermal_conductivity.option = "constant"; m.thermal_conductivity.value = p["k"]
    m.melting_heat.option = "constant"; m.melting_heat.value = p["latent"]
    m.tsolidus.option = "constant"; m.tsolidus.value = p["tm_k"]
    m.tliqidus.option = "constant"; m.tliqidus.value = p["tm_k"] + MUSHY_BAND_K
    m.viscosity.option = "constant"; m.viscosity.value = 3.5e-3

    # water
    solver.setup.materials.database.copy_materials(type="fluid", form=False, names=["water-liquid"])
    w = solver.setup.materials.fluid["water-liquid"]
    w.density.value = 977; w.specific_heat.value = 4190
    w.thermal_conductivity.value = 0.668; w.viscosity.value = 4.04e-4

    solver.setup.cell_zone_conditions.fluid[ZONES["water"]].general.material = "water-liquid"
    solver.setup.cell_zone_conditions.fluid[ZONES["capsule"]].general.material = p["name"]

    # SEAL the water pocket: inlet & outlet become adiabatic walls, so the water
    # only warms from the capsule (no charging flow in during discharge).
    bc = solver.setup.boundary_conditions
    for z in (ZONES["inlet"], ZONES["outlet"]):
        bc.set_zone_type(zone_list=[z], new_type="wall")
    for z in ZONES["axis"]:
        bc.set_zone_type(zone_list=[z], new_type="axis")
    for z in (ZONES["inlet"], ZONES["outlet"], ZONES["wall"]):
        try:
            wall = bc.wall[z]
            wall.thermal.thermal_condition = "Heat Flux"
            wall.thermal.heat_flux.value = 0
        except Exception as e:
            print(f"  (wall {z}: {type(e).__name__})", flush=True)

    # initialise COLD everywhere, then patch the capsule HOT (fully melted)
    init = solver.solution.initialization
    init.initialization_type = "standard"
    init.defaults["temperature"] = T_WATER_COLD
    init.initialize()
    solver.tui.solve.patch(ZONES["capsule"], "()", "temperature", str(T_CAPSULE_HOT))

    def zone_mean(field, zone):
        r = solver.solution.report_definitions
        nm = f"d_{field.replace('-', '_')}_{zone}"
        try:
            r.volume[nm] = {"report_type": "volume-average", "field": field, "cell_zones": [zone]}
        except Exception:
            pass
        return float(list(r.compute(report_defs=[nm])[0].values())[0][0])

    t_cap0 = zone_mean("temperature", ZONES["capsule"])
    t_wat0 = zone_mean("temperature", ZONES["water"])
    print(f"  start: capsule {t_cap0-273.15:.2f} C (melted), water {t_wat0-273.15:.2f} C\n", flush=True)
    if t_cap0 < T_CAPSULE_HOT - 2:
        solver.exit()
        raise SystemExit(f"capsule patch did not take ({t_cap0:.1f} K) -- aborting")

    gfx = solver.results.graphics
    def save_contour(field, fname):
        try:
            gfx.contour["dc"] = {"field": field, "surfaces_list": [],
                                 "coloring": {"option": "banded"}, "filled": True, "node_values": True}
            gfx.contour["dc"].display()
            try: gfx.views.auto_scale()
            except Exception: pass
            png = str(OUTDIR / fname)
            gfx.picture.save_picture(file_name=png)
            ok = os.path.exists(png) and os.path.getsize(png) > 0
            print(f"  saved {fname}: {'OK' if ok else 'EMPTY'}", flush=True)
        except Exception as e:
            print(f"  (save {fname}: {type(e).__name__}: {e})", flush=True)

    live_contour = None
    if args.live:
        try:
            gfx.contour["dc_live"] = {"field": "temperature", "surfaces_list": [],
                                      "coloring": {"option": "banded"}, "filled": True,
                                      "node_values": True}
            live_contour = gfx.contour["dc_live"]
            live_contour.display()
            print("  temperature contour opened -- it re-renders every minute\n", flush=True)
        except Exception as e:
            print(f"  (live contour setup skipped: {type(e).__name__}: {e})\n", flush=True)
    else:
        save_contour("temperature", f"{tag}_temp_START.png")

    solver.setup.general.solver.time = "unsteady-1st-order"
    rc = solver.solution.run_calculation
    rc.parameters.time_step_size = args.dt
    rc.parameters.max_iter_per_time_step = 40

    # one printed line per SIMULATED minute, so it scrolls slowly and readably.
    steps_per_min = max(1, round(60 / args.dt))
    done = 0
    prev_tw = t_wat0
    print("  simulated    WATER                 PCM (capsule)", flush=True)
    print("  time         temperature           temperature   state", flush=True)
    print("  " + "-" * 60, flush=True)
    while done < n_steps:
        n = min(steps_per_min, n_steps - done)
        rc.parameters.time_step_count = n
        rc.calculate()
        done += n
        tw = zone_mean("temperature", ZONES["water"])
        tc = zone_mean("temperature", ZONES["capsule"])
        lf = zone_mean("liquid-fraction", ZONES["capsule"])
        pcm_state = ("fully melted" if lf > 0.95 else
                     "solidifying " if lf > 0.05 else
                     "solid       ")
        water_state = "warming" if tw > prev_tw + 1e-3 else "steady "
        prev_tw = tw
        mins = done * args.dt / 60
        print(f"  t={mins:4.0f} min    {tw-273.15:6.2f} C ({water_state})     "
              f"{tc-273.15:6.2f} C   liq {lf:4.2f}  {pcm_state}", flush=True)
        if live_contour is not None:
            try:
                live_contour.display()
            except Exception:
                pass

    if not args.live:
        save_contour("temperature", f"{tag}_temp_END.png")
        save_contour("liquid-fraction", f"{tag}_liqfrac_END.png")

    print(f"\n  RESULT: water warmed from {t_wat0-273.15:.2f} C to {tw-273.15:.2f} C; "
          f"capsule liquid fraction {lf:.3f} (started 1.0)", flush=True)
    if args.live:
        input("Press Enter to close Fluent... ")
    solver.exit()
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
