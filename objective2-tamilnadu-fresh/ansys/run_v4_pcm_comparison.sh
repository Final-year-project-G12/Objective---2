#!/bin/bash
# run_v4_pcm_comparison.sh
# ========================
# The four shortlisted Tamil Nadu PCMs, melted on the SAME mesh under the SAME
# charging duty, so the only thing that differs between the four runs is the
# PCM itself. That is what makes the melt curves comparable -- running each PCM
# on its own regime mesh (as v3 did) confounds PCM identity with capsule size
# and flow rate, so no PCM-vs-PCM statement could be made from it.
#
# Mesh: regime0_v3 (1105 capsule cells, 1585 water cells), inlet 5.5815e-5 m/s.
# Duty: water held at 343.15 K (70 C), capsule starts 303.15 K solid.
# Time: 20 s x 1080 = 21600 s = 6 h physical -- a full charging day, not the
#       Fourier time. The 40-step smoke test showed why: with the water nearly
#       stagnant (5.6e-5 m/s) the capsule warms with a time constant of ~1100 s
#       for the SENSIBLE part alone, and C26's latent heat (256 kJ/kg) is 4.2x
#       the sensible heat needed to reach its solidus. A 2 h window would have
#       left every candidate in the low-melt-fraction regime where they are
#       indistinguishable; 6 h is the duty that actually separates them.
set -x
cd "/c/Users/jaswi/OneDrive/Desktop/ALL/SEM_7/project/jammalamadugu/new_obj/objective2_design_optimization/ansys_openfoam_case"

MESH="C:\\fluent_work\\regime0_v3_mesh_only.cas.h5"
ZONES="3_s_1 3_s_2 2_l_7 2_l_9 2_l_8 2_l_10 2_l_11 2_l_5"
VEL=5.581517e-05
DT=20.0
NSTEPS=1080

for PCM in c26 rt57hc c25 puretemp58; do
  echo "=== $PCM melting run starting $(date) ==="
  python pyfluent_v4_melt.py "$MESH" $PCM $ZONES $VEL $DT $NSTEPS "v4_${PCM}_melt" \
      > "v4_${PCM}_melt.log" 2>&1
  echo "=== $PCM done $(date), exit=$? ==="
done

echo "=== ALL V4 RUNS DONE $(date) ==="
