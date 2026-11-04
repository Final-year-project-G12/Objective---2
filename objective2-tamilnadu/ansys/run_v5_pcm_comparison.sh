#!/bin/bash
# run_v5_pcm_comparison.sh
# ========================
# v4 re-run with the molten PCM made immobile (viscosity 10 Pa s), which is the
# momentum counterpart of the already-documented decision to exclude buoyancy
# on this symmetry-plane mesh.
#
# WHY ALL FOUR ARE RE-RUN, not just C25
# -------------------------------------
# Only C25 diverged in v4 -- it is the only candidate whose liquidus (337.15 K)
# is low enough to FULLY melt inside the window, and a cell at liquid fraction
# 1 loses its enthalpy-porosity Darcy damping, freeing the melt to chase
# numerical noise. The other three stalled at 0.60-0.76 melt fraction, kept
# their damping, and ran with zero divergences.
#
# It would therefore be cheaper to re-run C25 alone. That is not done, because
# the whole point of this set is that the four differ ONLY in the PCM. Mixing
# one viscosity treatment for C25 with another for the rest would put a second
# difference into the comparison and quietly invalidate it. Identical settings
# cost ~2 h and keep the figure honest.
set -x
cd "/c/Users/jaswi/OneDrive/Desktop/ALL/SEM_7/project/jammalamadugu/new_obj/objective2_design_optimization/ansys_openfoam_case"

MESH="C:\\fluent_work\\regime0_v3_mesh_only.cas.h5"
ZONES="3_s_1 3_s_2 2_l_7 2_l_9 2_l_8 2_l_10 2_l_11 2_l_5"
VEL=5.581517e-05
DT=20.0
NSTEPS=1080

for PCM in c25 c26 rt57hc puretemp58; do      # C25 first: it is the one at risk
  echo "=== $PCM v5 melting run starting $(date) ==="
  python pyfluent_v4_melt.py "$MESH" $PCM $ZONES $VEL $DT $NSTEPS "v5_${PCM}" \
      > "v5_${PCM}.log" 2>&1
  echo "=== $PCM v5 done $(date), exit=$? ==="
done

echo "=== ALL V5 RUNS DONE $(date) ==="
