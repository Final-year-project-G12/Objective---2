#!/usr/bin/env python3
"""
tank_make_case.py -- OpenFOAM (ESI v2406) case for the solar-water-heater STORAGE TANK:
vertical cylinder, axisymmetric 2-D wedge, laminar water, Boussinesq buoyancy.

Tank geometry and loss are the project's frozen values (configs/system_config_shared.yaml):
  50 L, H/D = 2 (D = 0.317 m, H = 0.634 m), overall wall U = 0.8 W/m2K (5 cm foam).
Water: cp 4186, rho 1000, k 0.63, Pr 4.3 (frozen); expansion beta = 4.6e-4 1/K is a STANDARD
water property near 50 C that the project config does not contain -> flagged as assumed.

Scenarios (--mode)
  idle    no flow; uniform start; standing loss only.  Used to VERIFY the loss boundary
          condition against the lumped analytic solution  T(t)-Ta = (T0-Ta) exp(-U A t/(m cp)).
  charge  collector return enters the TOP port (hot, T_in), water leaves the BOTTOM port.
  draw    mains water enters the BOTTOM port, hot water leaves the TOP port (hourly draw).

Ports: a central circular port of radius r_port on each end face (default 10 mm, i.e. a 20 mm
pipe). Axis x is vertical (gravity = -x), y is the radius.

LIMITS (state them): laminar flow (Re_port ~ 1e3-3e3 at 0.01-0.05 kg/s, near the transitional
range: a turbulence model is the next upgrade), no diffuser/stratifier, no internal coil, no PCM
(the capsule bed is stage 2), axisymmetric (the real inlet and outlet are rarely on the axis).
"""
import argparse
import json
import math
import os

K0 = 273.15
HEADER = "/* tank_make_case.py (Objective 2, Rajasthan) -- edit the generator, not this file */\n"


def ff(cls, obj, body, loc=None):
    l = f'    location    "{loc}";\n' if loc else ""
    return (HEADER + "FoamFile\n{\n    version     2.0;\n    format      ascii;\n"
            f"    class       {cls};\n{l}    object      {obj};\n}}\n\n{body.rstrip()}\n")


def wr(d, rel, txt):
    p = os.path.join(d, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", newline="\n") as f:
        f.write(txt)


def tank_dims(volume_L, ratio):
    V = volume_L / 1000.0
    D = (4 * V / (math.pi * ratio)) ** (1 / 3)
    return D, ratio * D


def build(out, *, mode, volume_L=50.0, ratio=2.0, r_port=0.010, mdot=0.03, T_in_C=60.0,
          T_init_C=25.0, T_hot_C=55.0, hot_fraction=0.5, T_amb_C=25.0, U_wall=0.8,
          t_end_s=3600.0, dz=0.004, write_every=60.0, viz=False, beta=4.6e-4):
    D, H = tank_dims(volume_L, ratio)
    R = D / 2.0
    wedge = 5.0
    hw = math.radians(wedge / 2.0)
    nx = max(40, int(round(H / dz)))
    ny1 = max(3, int(round(r_port / dz)))
    ny2 = max(8, int(round((R - r_port) / dz)))
    mu = 4.3 * 0.63 / 4186.0                     # Pr = mu cp / k  (frozen water numbers)
    area_port = math.pi * r_port ** 2
    u_port = mdot / 1000.0 / area_port
    Re_port = 1000.0 * u_port * 2 * r_port / mu
    T_amb = T_amb_C + K0

    # ---- mesh (two blocks across the radius so the port is a patch) ----------------
    verts, vid = [], {}

    def V(x, y, plane):
        key = (round(x, 9), round(y, 9), plane if y > 1e-12 else 0)
        if key not in vid:
            z = (plane if y > 1e-12 else 0) * y * math.sin(hw)
            verts.append((x, y * math.cos(hw), z))
            vid[key] = len(verts) - 1
        return vid[key]

    def quad(c):                                      # c: 4 (x,y) corners, CCW in the x-y plane
        return [V(x, y, -1) for x, y in c] + [V(x, y, +1) for x, y in c]

    A = [(0, 0), (H, 0), (H, r_port), (0, r_port)]
    B = [(0, r_port), (H, r_port), (H, R), (0, R)]
    hexA, hexB = quad(A), quad(B)

    def face(pts):                                    # pts: 2 (x,y) endpoints of an edge
        (x1, y1), (x2, y2) = pts
        return f"({V(x1, y1, -1)} {V(x2, y2, -1)} {V(x2, y2, +1)} {V(x1, y1, +1)})"

    gr = 1.0 / 3.0                                    # finer cells toward the side wall
    bm = ["scale 1;\nvertices\n("]
    bm += [f"    ({x:.9g} {y:.9g} {z:.9g})" for x, y, z in verts]
    bm += [");", "blocks\n(",
           f"    hex ({' '.join(map(str, hexA))}) ({nx} {ny1} 1) simpleGrading (1 1 1)",
           f"    hex ({' '.join(map(str, hexB))}) ({nx} {ny2} 1) simpleGrading (1 {1.0 / gr:g} 1)", ");",
           "edges ();", "boundary\n("]
    bm += [f"    portBottom {{ type patch; faces ({face([(0, 0), (0, r_port)])}); }}",
           f"    portTop {{ type patch; faces ({face([(H, 0), (H, r_port)])}); }}",
           "    wall { type wall; faces (",
           f"        {face([(0, r_port), (0, R)])}",
           f"        {face([(H, r_port), (H, R)])}",
           f"        {face([(0, R), (H, R)])}", "    ); }"]
    fr_back = " ".join(f"({' '.join(str(h[i]) for i in (0, 1, 2, 3))})" for h in (hexA, hexB))
    fr_front = " ".join(f"({' '.join(str(h[i]) for i in (4, 5, 6, 7))})" for h in (hexA, hexB))
    bm += [f"    back {{ type wedge; faces ({fr_back}); }}",
           f"    front {{ type wedge; faces ({fr_front}); }}", ");", "mergePatchPairs ();"]
    wr(out, "system/blockMeshDict", ff("dictionary", "blockMeshDict", "\n".join(bm)))

    # ---- physics ----------------------------------------------------------------------
    wr(out, "constant/thermophysicalProperties", ff("dictionary", "thermophysicalProperties", f"""
thermoType
{{
    type            heRhoThermo;
    mixture         pureMixture;
    transport       const;
    thermo          hConst;
    equationOfState Boussinesq;
    specie          specie;
    energy          sensibleEnthalpy;
}}
pRef            100000;
mixture
{{
    specie          {{ molWeight 18.0; }}
    equationOfState {{ rho0 1000; T0 {T_amb:.6g}; beta {beta}; }}
    thermodynamics  {{ Cp 4186; Hf 0; }}
    transport       {{ mu {mu:.6g}; Pr 4.3; }}
}}
""", "constant"))
    wr(out, "constant/turbulenceProperties", ff("dictionary", "turbulenceProperties", "simulationType laminar;"))
    wr(out, "constant/g", ff("uniformDimensionedVectorField", "g",
                             "dimensions [0 1 -2 0 0 0 0];\nvalue (-9.81 0 0);", "constant"))

    # ---- boundary conditions per mode ------------------------------------------------
    flow = mode in ("charge", "draw")
    if mode == "charge":            # hot water in at the top, leaves at the bottom
        Tin_K = T_in_C + K0
        in_patch, out_patch, u_in = "portTop", "portBottom", (-u_port, 0, 0)
        T_init = T_init_C + K0
    elif mode == "draw":            # cold mains in at the bottom, hot water out at the top
        Tin_K = T_init_C + K0 if T_init_C < T_hot_C else T_hot_C + K0
        Tin_K = 25.0 + K0           # mains temperature (Rajasthan config: 18-30 C, 25.13 C point estimate)
        in_patch, out_patch, u_in = "portBottom", "portTop", (u_port, 0, 0)
        T_init = T_hot_C + K0
    else:
        in_patch = out_patch = None
        T_init = T_hot_C + K0

    def T_bc():
        s = f"""    wall
    {{
        type            externalWallHeatFluxTemperature;
        mode            coefficient;
        Ta              constant {T_amb:.6g};
        h               constant {U_wall};
        kappaMethod     fluidThermo;
        value           uniform {T_init:.6g};
    }}
"""
        if flow:
            s += f"    {in_patch} {{ type fixedValue; value uniform {Tin_K:.6g}; }}\n"
            s += f"    {out_patch} {{ type inletOutlet; inletValue uniform {Tin_K:.6g}; value uniform {T_init:.6g}; }}\n"
        else:
            s += "    portTop { type zeroGradient; }\n    portBottom { type zeroGradient; }\n"
        return s

    wedge_p = "    front { type wedge; }\n    back { type wedge; }\n"
    wr(out, "0/T", ff("volScalarField", "T",
                      f"dimensions [0 0 0 1 0 0 0];\ninternalField uniform {T_init:.6g};\nboundaryField\n{{\n{T_bc()}{wedge_p}}}"))
    if flow:
        uin = f"    {in_patch} {{ type fixedValue; value uniform ({u_in[0]:.6g} 0 0); }}\n" \
              f"    {out_patch} {{ type zeroGradient; }}\n"
        pr = f"    {in_patch} {{ type fixedFluxPressure; value uniform 100000; }}\n" \
             f"    {out_patch} {{ type fixedValue; value uniform 100000; }}\n"
        pp = f"    {in_patch} {{ type calculated; value uniform 100000; }}\n" \
             f"    {out_patch} {{ type calculated; value uniform 100000; }}\n"
    else:
        uin = "    portTop { type noSlip; }\n    portBottom { type noSlip; }\n"
        pr = "    portTop { type fixedFluxPressure; value uniform 100000; }\n    portBottom { type fixedFluxPressure; value uniform 100000; }\n"
        pp = "    portTop { type calculated; value uniform 100000; }\n    portBottom { type calculated; value uniform 100000; }\n"
    wr(out, "0/U", ff("volVectorField", "U",
                      f"dimensions [0 1 -1 0 0 0 0];\ninternalField uniform (0 0 0);\nboundaryField\n{{\n    wall {{ type noSlip; }}\n{uin}{wedge_p}}}"))
    wr(out, "0/p_rgh", ff("volScalarField", "p_rgh",
                          f"dimensions [1 -1 -2 0 0 0 0];\ninternalField uniform 100000;\nboundaryField\n{{\n    wall {{ type fixedFluxPressure; value uniform 100000; }}\n{pr}{wedge_p}}}"))
    wr(out, "0/p", ff("volScalarField", "p",
                      f"dimensions [1 -1 -2 0 0 0 0];\ninternalField uniform 100000;\nboundaryField\n{{\n    wall {{ type calculated; value uniform 100000; }}\n{pp}{wedge_p}}}"))

    # initial layers for draw: hot on top (hot_fraction of the height), mains-temperature below
    if mode == "draw":
        x_cut = H * (1.0 - hot_fraction)
        wr(out, "system/setFieldsDict", ff("dictionary", "setFieldsDict", f"""
defaultFieldValues ( volScalarFieldValue T {T_init:.6g} );
regions
(
    boxToCell
    {{
        box (-1 -1 -1) ({x_cut:.6g} 1 1);
        fieldValues ( volScalarFieldValue T {Tin_K:.6g} );
    }}
);
""", "system"))

    # ---- numerics -----------------------------------------------------------------------
    heights = [H * f for f in (0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95)]
    pts = "\n            ".join(f"({x:.6g} {0.5 * R:.6g} 0)" for x in heights)
    wr(out, "system/controlDict", ff("dictionary", "controlDict", f"""
application     buoyantPimpleFoam;
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         {t_end_s:.9g};
deltaT          0.05;
adjustTimeStep  yes;
maxCo           0.5;
maxDeltaT       5;
writeControl    adjustableRunTime;
writeInterval   {write_every:.9g};
purgeWrite      {0 if viz else 2};
writeFormat     ascii;
writePrecision  7;
timeFormat      general;
timePrecision   7;
runTimeModifiable true;
functions
{{
    meanT
    {{
        type volFieldValue; libs (fieldFunctionObjects); regionType all; operation volAverage;
        fields (T); writeFields no; log no; writeControl adjustableRunTime; writeInterval 30;
    }}
    outletT
    {{
        type surfaceFieldValue; libs (fieldFunctionObjects); regionType patch; name {out_patch or 'portTop'};
        operation weightedAreaAverage; weightField phi; fields (T); writeFields no; log no;
        writeControl adjustableRunTime; writeInterval 30;
    }}
    profile
    {{
        type probes; libs (sampling); writeControl adjustableRunTime; writeInterval 30;
        fields (T);
        probeLocations
        (
            {pts}
        );
    }}
}}
""", "system"))
    wr(out, "system/fvSchemes", ff("dictionary", "fvSchemes", """
ddtSchemes { default Euler; }
gradSchemes { default Gauss linear; }
divSchemes
{
    default none;
    div(phi,U) Gauss linearUpwind grad(U);
    div(phi,h) Gauss limitedLinear 1;
    div(phi,K) Gauss linear;
    div(phi,Ekp) Gauss linear;
    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
""", "system"))
    wr(out, "system/fvSolution", ff("dictionary", "fvSolution", """
solvers
{
    "rho.*" { solver diagonal; }
    p_rgh { solver PCG; preconditioner DIC; tolerance 1e-8; relTol 0.01; }
    p_rghFinal { $p_rgh; relTol 0; }
    "(U|h)" { solver PBiCGStab; preconditioner DILU; tolerance 1e-8; relTol 0.01; }
    "(U|h)Final" { $U; relTol 0; }
}
PIMPLE
{
    momentumPredictor yes;
    nOuterCorrectors 1;
    nCorrectors 2;
    nNonOrthogonalCorrectors 0;
    pRefCell 0;
    pRefValue 100000;
}
""", "system"))
    meta = dict(case="tank", mode=mode, volume_L=volume_L, ratio=ratio, D_m=D, H_m=H, r_port_m=r_port,
                mdot_kg_s=mdot, u_port_m_s=u_port, Re_port=Re_port, T_in_C=(Tin_K - K0) if flow else None,
                T_init_C=T_init - K0, T_hot_C=T_hot_C, hot_fraction=hot_fraction, T_amb_C=T_amb_C, U_wall=U_wall,
                n_cells=nx * (ny1 + ny2), nx=nx, beta_assumed=beta, probe_heights_m=heights,
                wall_area_m2=2 * math.pi * R * H + 2 * math.pi * R ** 2, mass_kg=1000.0 * volume_L / 1000.0,
                t_end_s=t_end_s)
    with open(os.path.join(out, "case_meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    return meta


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", choices=["idle", "charge", "draw"], default="idle")
    ap.add_argument("--volume-L", type=float, default=50.0)
    ap.add_argument("--ratio", type=float, default=2.0, help="height/diameter")
    ap.add_argument("--r-port", type=float, default=0.010)
    ap.add_argument("--mdot", type=float, default=0.03)
    ap.add_argument("--T-in", type=float, default=60.0, help="charge: collector return temperature [C]")
    ap.add_argument("--T-init", type=float, default=25.0, help="charge: initial tank temperature [C]")
    ap.add_argument("--T-hot", type=float, default=55.0, help="idle/draw: initial hot-layer temperature [C]")
    ap.add_argument("--hot-fraction", type=float, default=0.5, help="draw: hot layer fraction of the height")
    ap.add_argument("--T-amb", type=float, default=25.0)
    ap.add_argument("--U-wall", type=float, default=0.8)
    ap.add_argument("--t-end-s", type=float, default=3600.0)
    ap.add_argument("--dz", type=float, default=0.004)
    ap.add_argument("--write-every", type=float, default=60.0)
    ap.add_argument("--viz", action="store_true", help="keep all written times for ParaView")
    a = ap.parse_args()
    m = build(a.out, mode=a.mode, volume_L=a.volume_L, ratio=a.ratio, r_port=a.r_port, mdot=a.mdot, T_in_C=a.T_in,
              T_init_C=a.T_init, T_hot_C=a.T_hot, hot_fraction=a.hot_fraction, T_amb_C=a.T_amb, U_wall=a.U_wall,
              t_end_s=a.t_end_s, dz=a.dz, write_every=a.write_every, viz=a.viz)
    print(json.dumps({k: m[k] for k in ("mode", "D_m", "H_m", "n_cells", "u_port_m_s", "Re_port")}, indent=1))


if __name__ == "__main__":
    main()
