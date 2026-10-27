#!/bin/bash
set -x
cd "/c/Users/jaswi/OneDrive/Desktop/ALL/SEM_7/project/jammalamadugu/new_obj/objective2_design_optimization/ansys_openfoam_case"

echo "=== Regime 0 v2 solve starting $(date) ===" 
python pyfluent_v2_setup.py regime0_v2_mesh_only.cas.h5 7.9831e-5 2.0 828 regime0_v2_c26_melting > regime0_v2_solve.log 2>&1
echo "=== Regime 0 v2 solve done $(date), exit=$? ==="

echo "=== Regime 1 v2 solve starting $(date) ==="
python pyfluent_v2_setup.py regime1_v2_mesh_only.cas.h5 1.4696e-4 2.0 328 regime1_v2_c26_melting > regime1_v2_solve.log 2>&1
echo "=== Regime 1 v2 solve done $(date), exit=$? ==="

echo "=== Regime 2 v2 solve starting $(date) ==="
python pyfluent_v2_setup.py regime2_v2_mesh_only.cas.h5 3.2150e-5 2.0 1805 regime2_v2_c26_melting > regime2_v2_solve.log 2>&1
echo "=== Regime 2 v2 solve done $(date), exit=$? ==="

echo "=== ALL DONE $(date) ==="
