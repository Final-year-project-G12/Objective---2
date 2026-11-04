#!/bin/bash
# archive_sweep.sh
# ================
# MOVES superseded files into archive/ -- never deletes. Every path below is
# superseded by a named successor, and the successor is asserted to exist
# before its predecessor is moved, so a mistake in this script cannot silently
# strip the only copy of something.
#
# NOT touched (live inputs to work in progress):
#   *_v3_*                      current capsule cases, read by the v4 runs
#   pyfluent_v4_melt.py         the melting setup
#   system_tank_pcm_panel.*     the tank+PCM+panel deliverable
#   tank_drawcase_100L.msh      G4 draw case, built but not yet solved
#   verify_zones.py             still the zone ground-truth tool
set -u
cd "/c/Users/jaswi/OneDrive/Desktop/ALL/SEM_7/project/jammalamadugu/new_obj/objective2_design_optimization"

A=archive
mkdir -p "$A/ansys_superseded_v1" "$A/ansys_superseded_v2" \
         "$A/fluent_transcripts" "$A/openfoam_legacy" "$A/scratch"

moved=0
keep_safe() {   # keep_safe <successor-that-must-exist> <dest> <file>...
  local successor="$1" dest="$2"; shift 2
  if [ ! -e "$successor" ]; then
    echo "SKIP (successor $successor missing): $*"
    return
  fi
  for f in "$@"; do
    [ -e "$f" ] || continue
    mv "$f" "$dest/" && echo "  -> $dest/$(basename "$f")" && moved=$((moved+1))
  done
}

cd ansys_openfoam_case

echo "=== v1 capsule cases (superseded by v3) ==="
keep_safe regime0_v3_c26_melting.cas.h5 "../$A/ansys_superseded_v1" \
  regime0_rt57hc_melting.cas.h5 regime0_rt57hc_melting.dat.h5 \
  regime1_c26_melting.cas.h5 regime1_c26_melting.dat.h5 \
  regime2_c25_melting.cas.h5 regime2_c25_melting.dat.h5 \
  regime0_mesh_only.cas.h5 regime1_mesh_only.cas.h5 regime2_mesh_only.cas.h5 \
  regime0_capsule.cgns regime1_capsule.cgns regime2_capsule.cgns \
  regime0_capsule.msh regime1_capsule.msh regime2_capsule.msh \
  regime0_capsule_3d.msh \
  regime1_run3.log regime2_run4.log query_results3.log \
  import_and_save.jou import_and_save_regime1.jou import_and_save_regime2.jou

echo "=== v2 capsule cases (superseded by v3) ==="
keep_safe regime0_v3_c26_melting.cas.h5 "../$A/ansys_superseded_v2" \
  regime0_v2_c26_melting.cas.h5 regime0_v2_c26_melting.dat.h5 \
  regime1_v2_c26_melting.cas.h5 regime1_v2_c26_melting.dat.h5 \
  regime2_v2_c26_melting.cas.h5 regime2_v2_c26_melting.dat.h5 \
  regime0_v2_mesh_only.cas.h5 regime1_v2_mesh_only.cas.h5 regime2_v2_mesh_only.cas.h5 \
  regime0_v2_capsule.cgns regime1_v2_capsule.cgns regime2_v2_capsule.cgns \
  regime0_v2_capsule.msh regime1_v2_capsule.msh regime2_v2_capsule.msh \
  regime0_v2_solve.log regime1_v2_solve.log regime2_v2_solve.log \
  run_all_v2_solves.sh run_all_v2_solves_driver.log \
  import_and_save_regime0_v2.jou import_and_save_regime1_v2.jou \
  import_and_save_regime2_v2.jou \
  query_regime0_v2.log query_regime1_v2.log query_regime2_v2.log \
  pyfluent_v2_setup.py pyfluent_query_v2.py

echo "=== Fluent session transcripts (solver logs retained separately) ==="
for f in fluent-*.trn; do
  [ -e "$f" ] || continue
  mv "$f" "../$A/fluent_transcripts/" && echo "  -> fluent_transcripts/$f" && moved=$((moved+1))
done

echo "=== OpenFOAM legacy tree (this port uses ANSYS Fluent) ==="
if [ -d openfoam_case ]; then
  mv openfoam_case "../$A/openfoam_legacy/" && echo "  -> openfoam_legacy/openfoam_case" && moved=$((moved+1))
fi

echo "=== scratch / smoke-test leftovers ==="
for f in v4_smoketest.log v4_smoketest_melt_history.csv watchdog_y31bbJ_init \
         tn_report_v3.out tn_contours_v3.out export_fields.log; do
  [ -e "$f" ] || continue
  mv "$f" "../$A/scratch/" && echo "  -> scratch/$f" && moved=$((moved+1))
done

echo
echo "moved $moved item(s) into archive/ -- nothing deleted."
