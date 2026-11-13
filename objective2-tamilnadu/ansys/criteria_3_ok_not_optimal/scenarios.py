"""
ansys/criteria_common/scenarios.py
==================================
ONE place that defines the seven "what-if" design criteria (the optimum + six
alternatives) for the whole-tank discharge study, and how each 3-D design is
turned into the 2-D Fluent picture.

All designs are Regime 0, PureTemp 58, 100 L tank, 2.5 m2 collector -- the same
case as the optimiser's chosen design (results/tn_optimal_designs.csv).

THE 2-D PROXY RULE (why "34 capsules" stands for 104)
-----------------------------------------------------
The Fluent mesh is a PLANAR slice of the tank, which physically cannot hold the
real 3-D capsule count (104 spheres of 81.6 mm).  Following the project's
convention that the 34-capsule slice *is* the optimal design, every scenario is
drawn with

    drawn capsules  = round( N_3D * 34 / 104 )        (1 drawn  ~ 3.06 real)
    drawn inner R   = R_in_3D * 0.5                    (40 mm real -> 20 mm drawn)

so the optimum is exactly the existing 34-capsule / 20 mm picture and every
other scenario is drawn at the same scale relative to it.  Energy numbers come
from the node model (the optimiser's own evaluator); the Fluent picture is for
the SHAPE and TIME-BEHAVIOUR of the discharge, not for absolute kWh.
"""
import math

V_TANK_M3 = 0.100
WALL_M = 0.0008
N_OPT_3D = 104
N_OPT_2D = 34
R_SCALE_2D = 0.5

PCM = "PureTemp 58"
REGIME = 0


def v_outer(r_in):
    return 4.0 / 3.0 * math.pi * (r_in + WALL_M) ** 3


def frac_for_count(r_in, n):
    return n * v_outer(r_in) / V_TANK_M3


def drawn_count(n3d):
    return max(1, int(round(n3d * N_OPT_2D / N_OPT_3D)))


# (folder, short title, 3-D design, "what is it" / "why") ----------------------
OPT = dict(R_in=0.0399999921398018, fraction=0.29587085509033423,
           flow=0.0387608549268862, arrangement="staggered")

SCENARIOS = [
    dict(key="criteria_0_optimal_reference", title="0. OPTIMAL (reference)",
         design=dict(OPT),
         rule="The optimiser's selected design (S0/S1/S2 funnel winner): the largest "
              "radius, ~30 % PCM fraction, a high-but-not-maximum flow.",
         why_not_optimal="It IS the optimum - reference for every other run."),
    dict(key="criteria_1_max_all", title="1. MAX of every parameter",
         design=dict(R_in=0.040, fraction=0.30, flow=0.050, arrangement="staggered"),
         rule="Every knob at its upper bound: R_in 40 mm, PCM fraction 30 %, flow 0.050 kg/s, "
              "densest packing (staggered).  N follows from R and fraction (the 30 % cap at R = 40 mm gives N = 105).",
         why_not_optimal="Radius and fraction were ALREADY at their bounds in the optimum (R 40 mm, 29.6 % of a 30 % cap), "
                         "so the only real changes are +1 capsule and a higher flow (0.050 vs 0.0388). The gain is "
                         "marginally higher but the difference sits INSIDE the repeatability band, so the funnel "
                         "treats it as a tie and breaks it on cost: more PCM mass, more capsules, more overheating."),
    dict(key="criteria_2_min_all", title="2. MIN of every parameter",
         design=dict(R_in=0.010, fraction=0.02, flow=0.010, arrangement="single-layer"),
         rule="Every knob at its lower bound: R_in 10 mm, PCM fraction 2 %, flow 0.010 kg/s, "
              "loosest packing (single-layer).  N = 380 tiny capsules but only ~2 % of the tank volume (1.4 kg of PCM).",
         why_not_optimal="Almost no PCM (1.4 kg, 2 % of the tank), so almost no latent storage: the gain (2.2 kWh/yr) is "
                         "~1 % of the optimum and far inside the repeatability band - indistinguishable from plain water."),
    dict(key="criteria_3_ok_not_optimal", title="3. NOT optimal, but working",
         design=dict(R_in=0.040, fraction=0.2276, flow=0.0227, arrangement="staggered"),
         rule="A real evaluated candidate from the optimiser's own list (results/g10_selection_candidates_r0.csv): "
              "N = 80 capsules, flow 0.0227.  Passes every hard gate and beats the plain tank clearly.",
         why_not_optimal="Falls outside S0 (not within the tie-band of the best g_window): ~23 % less PCM "
                         "and a slower flow (0.0227 vs 0.0388), so it delivers ~32 % less extra evening heat. "
                         "Trade-off: far less overheating (shield-hours) - so it is a genuinely working, cheaper design."),
    dict(key="criteria_4_only_30_capsules", title="4. YOUR WISH: only 30 capsules",
         design=dict(R_in=0.040, fraction=frac_for_count(0.040, 30),
                     flow=OPT["flow"], arrangement="staggered"),
         rule="Only 30 real capsules (R_in 40 mm, optimal flow, staggered) = 8.5 % PCM fraction.",
         why_not_optimal="Under a third of the optimal PCM mass (7.2 kg vs 24.8 kg): the store is used up quickly in "
                         "the evening, so only ~30 % of the optimal benefit is delivered."),
    dict(key="criteria_5_10pct_of_optimal", title="5. 10 % of the optimal PCM",
         design=dict(R_in=0.040, fraction=frac_for_count(0.040, 10),
                     flow=OPT["flow"], arrangement="staggered"),
         rule="N = 10 % of 104 = 10 capsules (R_in, flow, arrangement kept optimal: 10 % of the radius or "
              "flow would fall below the design-space / pump bounds).",
         why_not_optimal="Only 2.4 kg of PCM: the latent store is almost negligible - the ~27 kWh/yr gain is below "
                         "the 28.4 kWh repeatability band, i.e. not distinguishable from a plain tank."),
    dict(key="criteria_6_50pct_of_optimal", title="6. 50 % of the optimal PCM",
         design=dict(R_in=0.040, fraction=frac_for_count(0.040, 52),
                     flow=OPT["flow"], arrangement="staggered"),
         rule="N = 50 % of 104 = 52 capsules (R_in, flow, arrangement kept optimal).",
         why_not_optimal="Half the PCM gives ~54 % of the gain - the benefit grows roughly in proportion to PCM mass "
                         "up to the 30 % volume cap, which is why the optimiser pushes to the cap."),
]

