#!/usr/bin/env bash
# install_pht_solver.sh -- clone and build the Fetsov & Lutsenko packed-bed PCM solver
# (porousHeatTransferFoam) against the OpenFOAM v2406 installed in WSL.
#   Source : https://github.com/fetc95/pht-openfoam-lab53iacp   (CC BY-NC 4.0, non-commercial use)
#   Paper  : Fetsov & Lutsenko, J. Energy Storage 65 (2023) 107294
#   Verified 2026-10-16: builds with exit 0 on v2406 (author README targets v2412);
#   shipped example PCMValidations/GR27 runs 6 h of simulated time in ~40 s.
#   usage:  bash install_pht_solver.sh
source /usr/lib/openfoam/openfoam2406/etc/bashrc >/dev/null 2>&1
mkdir -p "$HOME/OpenFOAM"
cd "$HOME/OpenFOAM" || exit 1
[ -d OpenFOAM-PHT53IACP ] || git clone --depth 1 https://github.com/fetc95/pht-openfoam-lab53iacp.git OpenFOAM-PHT53IACP
source "$HOME/OpenFOAM/OpenFOAM-PHT53IACP/etc/bashrc"     # sets FOAM_PHT53_EXAMPLES etc.
export WM_NCOMPPROCS=${WM_NCOMPPROCS:-4}
cd "$WM_PROJECT_PHT53_DIR" && ./Allwmake > "$HOME/pht_build.log" 2>&1
echo "Allwmake exit $?  (log: ~/pht_build.log)"
ls "$FOAM_USER_APPBIN" | grep -i -E "pht|porous"
