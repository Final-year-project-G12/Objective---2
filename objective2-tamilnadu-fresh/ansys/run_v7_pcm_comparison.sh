#!/bin/bash
# run_v7_pcm_comparison.sh
# ========================
# All four shortlisted PCMs, including n-Pentacosane (C25), which no earlier
# attempt could solve.
#
# WHAT CHANGED
#   p-v coupling    SIMPLE -> Coupled
#   discretisation  second-order -> first-order upwind (mom, temperature)
#
# This was the one lever left untested after six other hypotheses for the C25
# divergence were disproved (timestep, melt viscosity, delh under-relaxation,
# mushy-band width, material data, mesh refinement -- see CFD_VERIFICATION.md).
# A 60-step probe with these two settings produced ZERO divergences where every
# previous C25 attempt produced 43-158.
#
# All four PCMs are re-run, not just C25: the comparison is only meaningful if
# the runs differ in nothing but the material. Mixing a Coupled/first-order C25
# with SIMPLE/second-order results for the others would put a numerical
# difference into a figure that claims to show a material difference.
set -x
cd "/c/Users/jaswi/OneDrive/Desktop/ALL/SEM_7/project/jammalamadugu/new_obj/objective2_design_optimization/ansys"

export V4_SCHEME=Coupled
export V4_ORDER=first

MESH="C:\\fluent_work\\regime0_v3_mesh_only.cas.h5"
ZONES="3_s_1 3_s_2 2_l_7 2_l_9 2_l_8 2_l_10 2_l_11 2_l_5"
VEL=5.581517e-05
DT=20.0
NSTEPS=1080          # 6 h physical

for PCM in c25 c26 rt57hc puretemp58; do      # C25 first: the one at risk
  echo "=== $PCM v7 starting $(date) ==="
  python pyfluent_v4_melt.py "$MESH" $PCM $ZONES $VEL $DT $NSTEPS "v7_${PCM}" \
      > "v7_${PCM}.log" 2>&1
  echo "=== $PCM v7 done $(date), exit=$? ==="
done

echo "=== ALL V7 RUNS DONE $(date) ==="
