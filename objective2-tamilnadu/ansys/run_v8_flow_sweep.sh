#!/bin/bash
# run_v8_flow_sweep.sh
# ====================
# Flow rate is one of the four parameters the optimiser searches. This sweeps it
# in Fluent with everything else fixed, so the CFD shows the same trade-off the
# tank model reports: more flow carries more heat past the capsule per second,
# but leaves each parcel of water less time to give it up.
#
# VELOCITY SCALING
#   The regime-0 deployable design is 0.0388 kg/s at an inlet velocity of
#   5.581517e-05 m/s on this unit cell, so the cell's velocity per kg/s is
#   5.581517e-05 / 0.0388 = 1.4386e-03. The three points below are the design
#   space's low end, middle and high end (0.010 / 0.030 / 0.050 kg/s) put
#   through that same scaling, so they are comparable to the optimiser's own
#   flow axis rather than arbitrary numbers.
#
# Everything else is held: same mesh, same PCM (C26), same 70 C water, same
# capsule starting at 30 C solid, same Coupled + first-order settings that made
# all four PCMs solve.
set -x
cd "/c/Users/jaswi/OneDrive/Desktop/ALL/SEM_7/project/jammalamadugu/new_obj/objective2_design_optimization/ansys"

export V4_SCHEME=Coupled
export V4_ORDER=first

MESH="C:\\fluent_work\\regime0_v3_mesh_only.cas.h5"
ZONES="3_s_1 3_s_2 2_l_7 2_l_9 2_l_8 2_l_10 2_l_11 2_l_5"
DT=20.0
NSTEPS=1080          # 6 h physical

run () {   # run <kg/s label> <velocity>
  echo "=== flow $1 kg/s (v=$2) starting $(date) ==="
  python pyfluent_v4_melt.py "$MESH" c26 $ZONES "$2" $DT $NSTEPS "v8_flow_$1" \
      > "v8_flow_$1.log" 2>&1
  echo "=== flow $1 done $(date), exit=$? ==="
}

run 0p010 1.4386e-05
run 0p030 4.3159e-05
run 0p050 7.1932e-05

echo "=== V8 FLOW SWEEP DONE $(date) ==="
