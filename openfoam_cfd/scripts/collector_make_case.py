#!/usr/bin/env python3
"""
collector_make_case.py -- conjugate-heat-transfer (chtMultiRegionFoam, OpenFOAM ESI v2406) case for ONE
riser strip of a flat-plate solar collector: copper absorber plate + riser tube + laminar water flow.

Why: the frozen config carries two collector numbers, F_R*(tau*alpha) = 0.75 and F_R*U_L = 4.5 W/m2K
("typical", system_config_shared.yaml). The CFD resolves plate-fin conduction and the developing laminar
flow in the riser and returns the useful gain directly, so F' and F_R can be CHECKED instead of assumed.

Geometry (half strip by symmetry; flow along +x), cross-section in y (across) and z (up)
  plate (copper, thickness t_p) on top; tube = SQUARE channel of side a below the plate centre with wall
  t_w; fin = plate beyond the tube out to the half pitch W/2.  A square channel of equal flow area
  replaces the round tube (blockMesh-only meshing): fully-developed laminar Nu is ~17 % lower than a round
  tube (3.6 vs 4.36), so F' is slightly conservative.  Back and edges adiabatic.
Top boundary: q'' = U_L (T_plate - T_amb) - S  implemented as externalWallHeatFluxTemperature,
  mode coefficient, h = U_L, Ta_eff = T_amb + S/U_L   (S = tau*alpha*G absorbed flux).
[ASSUMED] (typical domestic flat-plate collector, NOT in the project config):
  pitch W = 0.12 m, length L = 1.2 m, a = 8.9 mm (flow area of a 10 mm tube), t_w = 0.8 mm,
  t_p = 0.3 mm copper (k = 385), U_L = 5 W/m2K, tau*alpha = 0.80, G = 1000 W/m2.
From the project: collector area 1.5 m2 (-> n_risers = area/(W L)), loop flow 0.010-0.050 kg/s split
equally over the risers, water cp/rho/k/Pr.
"""
import argparse
import json
import math
import os

K0 = 273.15
HDR = "/* collector_make_case.py (Objective 2, Rajasthan) -- edit the generator */\n"


def ff(cls, obj, body, loc=None):
    l = f'    location    "{loc}";\n' if loc else ""
    return (HDR + "FoamFile\n{\n    version     2.0;\n    format      ascii;\n"
            f"    class       {cls};\n{l}    object      {obj};\n}}\n\n{body.rstrip()}\n")


def wr(d, rel, txt):
    p = os.path.join(d, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", newline="\n") as f:
        f.write(txt)


def geometry(W=0.12, L=1.2, a=0.0089, t_w=0.0008, t_p=0.0003):
    y0, y1, y2, y3 = 0.0, a / 2, a / 2 + t_w, W / 2
    z0, z1, z2, z3 = -(a + t_w), -a, 0.0, t_p
    return (y0, y1, y2, y3), (z0, z1, z2, z3)


def analytic(mdot_riser, T_in, T_amb, G, tau_alpha, U_L, W, L, a, t_w, t_p, k_cu=385.0):
    """Duffie & Beckman flat-plate relations for the same strip (for comparison with the CFD)."""
    cp, k, mu, rho = 4186.0, 0.63, 4.3 * 0.63 / 4186.0, 1000.0
    Dh = a
    h_f = 3.61 * k / Dh                                 # square duct, laminar, uniform wall temperature/flux
    D = a + 2 * t_w
    m = math.sqrt(U_L / (k_cu * t_p))
    x = m * (W - D) / 2
    F = math.tanh(x) / x
    P = 4 * a                                           # wetted perimeter of the channel
    Fp = (1 / U_L) / (W * (1 / (U_L * (D + (W - D) * F)) + 1 / (P * h_f)))
    A = W * L
    mc = mdot_riser * cp
    FR = (mc / (A * U_L)) * (1 - math.exp(-A * U_L * Fp / mc))
    S = tau_alpha * G
    Qu = A * FR * (S - U_L * (T_in - T_amb))
    return dict(F_prime=Fp, F_R=FR, Q_riser_W=Qu, T_out_C=T_in + Qu / mc, eta=Qu / (A * G), h_f=h_f)


def build(out, *, mdot_loop=0.03, T_in_C=30.0, T_amb_C=25.0, G=1000.0, tau_alpha=0.80, U_L=5.0,
          W=0.12, L=1.2, a=0.0089, t_w=0.0008, t_p=0.0003, k_cu=385.0, area_m2=1.5, nx=100, t_end=300.0):
    n_risers = area_m2 / (W * L)
    mdot = mdot_loop / n_risers
    S = tau_alpha * G
    Ta_eff = T_amb_C + K0 + S / U_L          # kelvin
    mu = 4.3 * 0.63 / 4186.0
    u_in = mdot / 1000.0 / (a * a)
    Re = 1000.0 * u_in * a / mu
    (y0, y1, y2, y3), (z0, z1, z2, z3) = geometry(W, L, a, t_w, t_p)
    ny1, nyw, ny3 = 8, 2, 14
    nz1, nzw, nzp = 8, 2, 2
    X = (0.0, L)
    verts, vid = [], {}

    def V(x, y, z):
        k = (round(x, 9), round(y, 9), round(z, 9))
        if k not in vid:
            verts.append(k)
            vid[k] = len(verts) - 1
        return vid[k]

    def hexb(ya, yb, za, zb):
        return [V(X[0], ya, za), V(X[1], ya, za), V(X[1], yb, za), V(X[0], yb, za),
                V(X[0], ya, zb), V(X[1], ya, zb), V(X[1], yb, zb), V(X[0], yb, zb)]

    B = [  # name, zone, (ya,yb,za,zb), cells
        ("water", "water", (y0, y1, z1, z2), (nx, ny1, nz1)),
        ("cuBottom", "copper", (y0, y1, z0, z1), (nx, ny1, nzw)),
        ("cuSideLow", "copper", (y1, y2, z0, z1), (nx, nyw, nzw)),
        ("cuSideUp", "copper", (y1, y2, z1, z2), (nx, nyw, nz1)),
        ("plate1", "copper", (y0, y1, z2, z3), (nx, ny1, nzp)),
        ("plate2", "copper", (y1, y2, z2, z3), (nx, nyw, nzp)),
        ("plate3", "copper", (y2, y3, z2, z3), (nx, ny3, nzp)),
    ]
    H = {n: hexb(*box) for n, _, box, _ in B}
    # block-face vertex lists: x0 / xL / y_a / y_b / z_a / z_b
    f = lambda n: dict(x0=(0, 3, 7, 4), xL=(1, 2, 6, 5), ya=(0, 1, 5, 4), yb=(3, 2, 6, 7), za=(0, 1, 2, 3), zb=(4, 5, 6, 7))
    face = lambda n, k: "(" + " ".join(str(H[n][i]) for i in f(n)[k]) + ")"
    bm = ["scale 1;", "vertices\n("]
    bm += [f"    ({x:.9g} {y:.9g} {z:.9g})" for x, y, z in verts]
    bm += [");", "blocks\n("]
    bm += [f"    hex ({' '.join(str(i) for i in H[n])}) {zone} ({c[0]} {c[1]} {c[2]}) simpleGrading (1 1 1)"
           for n, zone, _, c in B]
    bm += [");", "edges ();", "boundary\n("]
    patches = {
        "inlet": [face("water", "x0")],
        "outlet": [face("water", "xL")],
        "symWater": [face("water", "ya")],
        "symCu": [face("cuBottom", "ya"), face("plate1", "ya")],
        "top": [face(n, "zb") for n in ("plate1", "plate2", "plate3")],
        "cuEnds": [face(n, k) for n in H if n != "water" for k in ("x0", "xL")],
        "back": [face("cuBottom", "za"), face("cuSideLow", "za"), face("cuSideLow", "yb"),
                 face("cuSideUp", "yb"), face("plate3", "za")],
        "edge": [face("plate3", "yb")],
    }
    ptype = {"symWater": "symmetryPlane", "symCu": "symmetryPlane"}
    for nme, fl in patches.items():
        bm.append(f"    {nme} {{ type {ptype.get(nme, 'patch')}; faces ({' '.join(fl)}); }}")
    bm += [");", "mergePatchPairs ();"]
    wr(out, "system/blockMeshDict", ff("dictionary", "blockMeshDict", "\n".join(bm)))

    wr(out, "constant/regionProperties", ff("dictionary", "regionProperties",
                                             "regions ( fluid (water) solid (copper) );", "constant"))
    wr(out, "constant/g", ff("uniformDimensionedVectorField", "g",
                             "dimensions [0 1 -2 0 0 0 0];\nvalue (0 0 0);", "constant"))
    wr(out, "constant/water/thermophysicalProperties", ff("dictionary", "thermophysicalProperties", f"""
thermoType
{{
    type            heRhoThermo;
    mixture         pureMixture;
    transport       const;
    thermo          hConst;
    equationOfState rhoConst;
    specie          specie;
    energy          sensibleEnthalpy;
}}
pRef 100000;
mixture
{{
    specie          {{ molWeight 18.0; }}
    equationOfState {{ rho 1000; }}
    thermodynamics  {{ Cp 4186; Hf 0; }}
    transport       {{ mu {mu:.6g}; Pr 4.3; }}
}}
""", "constant/water"))
    wr(out, "constant/water/turbulenceProperties", ff("dictionary", "turbulenceProperties", "simulationType laminar;", "constant/water"))
    wr(out, "constant/copper/thermophysicalProperties", ff("dictionary", "thermophysicalProperties", f"""
thermoType
{{
    type            heSolidThermo;
    mixture         pureMixture;
    transport       constIso;
    thermo          hConst;
    equationOfState rhoConst;
    specie          specie;
    energy          sensibleEnthalpy;
}}
mixture
{{
    specie          {{ molWeight 63.5; }}
    transport       {{ kappa {k_cu}; }}
    thermodynamics  {{ Hf 0; Cp 385; }}
    equationOfState {{ rho 8960; }}
}}
""", "constant/copper"))

    Tin, Tamb = T_in_C + K0, T_amb_C + K0
    # fields written per region AFTER splitMeshRegions (run script copies 0.regions -> 0)
    cpl_w = ("compressible::turbulentTemperatureCoupledBaffleMixed; Tnbr T; kappaMethod fluidThermo; "
             f"value uniform {Tin:.6g};")
    cpl_c = ("compressible::turbulentTemperatureCoupledBaffleMixed; Tnbr T; kappaMethod solidThermo; "
             f"value uniform {Tin:.6g};")
    wr(out, "0.regions/water/T", ff("volScalarField", "T", f"""
dimensions [0 0 0 1 0 0 0];
internalField uniform {Tin:.6g};
boundaryField
{{
    ".*"          {{ type zeroGradient; }}
    inlet         {{ type fixedValue; value uniform {Tin:.6g}; }}
    outlet        {{ type inletOutlet; inletValue uniform {Tin:.6g}; value uniform {Tin:.6g}; }}
    symWater      {{ type symmetryPlane; }}
    "water_to_.*" {{ type {cpl_w} }}
}}
"""))
    wr(out, "0.regions/water/U", ff("volVectorField", "U", f"""
dimensions [0 1 -1 0 0 0 0];
internalField uniform ({u_in:.6g} 0 0);
boundaryField
{{
    ".*"          {{ type noSlip; }}
    inlet         {{ type fixedValue; value uniform ({u_in:.6g} 0 0); }}
    outlet        {{ type inletOutlet; inletValue uniform (0 0 0); value uniform ({u_in:.6g} 0 0); }}
    symWater      {{ type symmetryPlane; }}
}}
"""))
    wr(out, "0.regions/water/p_rgh", ff("volScalarField", "p_rgh", """
dimensions [1 -1 -2 0 0 0 0];
internalField uniform 100000;
boundaryField
{
    ".*"          { type fixedFluxPressure; value uniform 100000; }
    inlet         { type fixedFluxPressure; value uniform 100000; }
    outlet        { type fixedValue; value uniform 100000; }
    symWater      { type symmetryPlane; }
}
"""))
    wr(out, "0.regions/water/p", ff("volScalarField", "p", """
dimensions [1 -1 -2 0 0 0 0];
internalField uniform 100000;
boundaryField
{
    ".*"          { type calculated; value uniform 100000; }
    symWater      { type symmetryPlane; }
}
"""))
    wr(out, "0.regions/copper/p", ff("volScalarField", "p", """
dimensions [1 -1 -2 0 0 0 0];
internalField uniform 100000;
boundaryField
{
    ".*"          { type calculated; value uniform 100000; }
    symCu         { type symmetryPlane; }
}
"""))
    wr(out, "0.regions/copper/T", ff("volScalarField", "T", f"""
dimensions [0 0 0 1 0 0 0];
internalField uniform {Tin:.6g};
boundaryField
{{
    ".*"           {{ type zeroGradient; }}
    symCu          {{ type symmetryPlane; }}
    top
    {{
        type            externalWallHeatFluxTemperature;
        mode            coefficient;
        Ta              constant {Ta_eff:.6g};
        h               constant {U_L};
        kappaMethod     solidThermo;
        value           uniform {Tin:.6g};
    }}
    "copper_to_.*" {{ type {cpl_c} }}
}}
"""))

    wr(out, "system/controlDict", ff("dictionary", "controlDict", f"""
application     chtMultiRegionFoam;
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         {t_end:.9g};
deltaT          0.05;
adjustTimeStep  yes;
maxCo           0.8;
maxDi           1e6;      // implicit solid: the thin-plate diffusion number must not limit dt
maxDeltaT       0.5;
writeControl    adjustableRunTime;
writeInterval   {t_end / 5:.9g};
purgeWrite      0;
writeFormat     ascii;
writePrecision  8;
timeFormat      general;
timePrecision   8;
runTimeModifiable true;
""", "system"))
    wr(out, "system/fvSolution", ff("dictionary", "fvSolution", "PIMPLE { nOuterCorrectors 1; }", "system"))
    wr(out, "system/fvSchemes", ff("dictionary", "fvSchemes", """
ddtSchemes { default Euler; }
gradSchemes { default Gauss linear; }
divSchemes { default none; }
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
""", "system"))
    wr(out, "system/water/fvSchemes", ff("dictionary", "fvSchemes", """
ddtSchemes { default Euler; }
gradSchemes { default Gauss linear; }
divSchemes
{
    default none;
    div(phi,U) Gauss linearUpwind grad(U);
    div(phi,K) Gauss linear;
    div(phi,h) Gauss limitedLinear 1;
    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
""", "system/water"))
    wr(out, "system/water/fvSolution", ff("dictionary", "fvSolution", """
solvers
{
    rho { solver PCG; preconditioner DIC; tolerance 1e-7; relTol 0.1; }
    rhoFinal { $rho; tolerance 1e-7; relTol 0; }
    p_rgh { solver PCG; preconditioner DIC; tolerance 1e-8; relTol 0.01; }
    p_rghFinal { $p_rgh; relTol 0; }
    "(U|h)" { solver PBiCGStab; preconditioner DILU; tolerance 1e-8; relTol 0.01; }
    "(U|h)Final" { $U; relTol 0; }
}
PIMPLE { momentumPredictor yes; nCorrectors 2; nNonOrthogonalCorrectors 0; }
relaxationFactors { equations { "h.*" 1; "U.*" 1; } }
""", "system/water"))
    wr(out, "system/copper/fvSchemes", ff("dictionary", "fvSchemes", """
ddtSchemes { default Euler; }
gradSchemes { default Gauss linear; }
divSchemes { default none; }
laplacianSchemes { default none; laplacian(alpha,h) Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
""", "system/copper"))
    wr(out, "system/copper/fvSolution", ff("dictionary", "fvSolution", """
solvers { h { solver PCG; preconditioner DIC; tolerance 1e-8; relTol 0.01; } hFinal { $h; relTol 0; } }
PIMPLE { nNonOrthogonalCorrectors 0; }
""", "system/copper"))
    wr(out, "system/water/outletT", ff("dictionary", "outletT", """
type            surfaceFieldValue;
libs            (fieldFunctionObjects);
regionType      patch;
name            outlet;
operation       weightedAreaAverage;
weightField     phi;
fields          (T);
writeFields     no;
log             yes;
""", "system/water"))
    meta = dict(case="collector_strip", mdot_loop=mdot_loop, n_risers=n_risers, mdot_riser=mdot, T_in_C=T_in_C,
                T_amb_C=T_amb_C, G=G, tau_alpha=tau_alpha, S=S, U_L=U_L, W=W, L=L, a=a, t_w=t_w, t_p=t_p,
                k_cu=k_cu, u_in=u_in, Re_channel=Re, nx=nx, t_end=t_end,
                n_cells=nx * (ny1 * nz1 + ny1 * nzw + nyw * nzw + nyw * nz1 + ny1 * nzp + nyw * nzp + ny3 * nzp))
    meta["analytic"] = analytic(mdot, T_in_C, T_amb_C, G, tau_alpha, U_L, W, L, a, t_w, t_p, k_cu)
    with open(os.path.join(out, "case_meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    return meta


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mdot-loop", type=float, default=0.03)
    ap.add_argument("--T-in", type=float, default=30.0)
    ap.add_argument("--T-amb", type=float, default=25.0)
    ap.add_argument("--G", type=float, default=1000.0)
    ap.add_argument("--tau-alpha", type=float, default=0.80)
    ap.add_argument("--U-L", type=float, default=5.0)
    ap.add_argument("--nx", type=int, default=100)
    ap.add_argument("--t-end", type=float, default=300.0)
    a = ap.parse_args()
    m = build(a.out, mdot_loop=a.mdot_loop, T_in_C=a.T_in, T_amb_C=a.T_amb, G=a.G, tau_alpha=a.tau_alpha,
              U_L=a.U_L, nx=a.nx, t_end=a.t_end)
    print(json.dumps({k: (round(v, 5) if isinstance(v, float) else v) for k, v in m.items() if k != "analytic"}, indent=1))
    print("analytic (Duffie-Beckman) :", json.dumps({k: round(v, 4) for k, v in m["analytic"].items()}))
