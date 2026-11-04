# Prompt 3 — Basic Fluent/OpenFOAM Verification for {STATE}'s Designs

Optional, after `02_OBJECTIVE2_CONFIG_AND_RUN.md` has produced real
deployable designs for {STATE}. This replicates the Tamil Nadu CFD
cross-check (`../CFD_VERIFICATION.md`) using the
same proven approach and tools — paste this (with `{STATE}` replaced):

---

Objective 2's deployable designs for {STATE} now exist in
`results/{STATE}/deployable_design_per_regime.csv`. I want the same basic
ANSYS Fluent cross-verification already done for Tamil Nadu — read
`docs_objective2/CFD_VERIFICATION.md` first for
the full methodology and every real pitfall already found and fixed, so
you don't have to rediscover them. In short, reuse these exact,
already-working pieces from `ansys_openfoam_case/`:

- **Mesh generation**: `build_mesh_regime.py <R_CAPSULE_m> <basename>` —
  already parameterized, just needs {STATE}'s real per-regime capsule
  radius (diameter/2 from the deployable-design CSV). The half-disk clip
  it does is required — don't regenerate mesh logic from scratch, reuse
  this script.
- **CGNS conversion + Fluent import**: convert the `.msh` to `.cgns` via
  gmsh directly (`gmsh.open(...); gmsh.write(name + '.cgns')`), then
  import via the proven headless TUI route (`import_and_save.jou`'s
  pattern: `/file/import/cgns/mesh` then the filename on the next line,
  then `/file/write-case "<name>_mesh_only.cas.h5"`) — **do not** import
  CGNS through PyFluent's settings API (`solver.file.import_.read(...)`)
  directly; that segfaults (SIGSEGV in `CeetronSAM.dll`) reliably in this
  environment.
- **Zone identities are NOT portable between regimes or states** —
  verify each new mesh's own zone names independently using
  `verify_zones.py <case_file.cas.h5>` (reads the case file's own HDF5
  face/cell adjacency data) before writing any boundary condition. Do not
  assume {STATE}'s zone names match Tamil Nadu's (`3_s_1`/`2_l_7`/etc.) —
  confirmed they differ even between Tamil Nadu's own 3 regimes.
- **Full setup+solve**: adapt `pyfluent_v3_setup.py` as the template — it
  is the current, most general version (supersedes the older
  `pyfluent_regime1_setup.py`/`pyfluent_full_setup2.py`/`pyfluent_v2_setup.py`,
  which either hardcoded one regime or assumed one PCM for every regime —
  Tamil Nadu itself needed 2 different PCMs across its 3 regimes in the
  final design, so don't assume {STATE} needs only one either). It takes
  PCM identity and all 9 zone names as CLI args rather than hardcoding
  them — real PCM properties from {STATE}'s own
  `pcm_database_tamilnadu.csv`-equivalent, real computed inlet velocity
  (`(total_flow_kg_s / capsule_count) / rho_water / (pi * (1.7*R_CAPSULE)^2)`),
  solidus = real `Tm_C + 273.15`, **liquidus = solidus + 10** (a 10K
  numerical mushy-zone widening — this is required for solver stability
  regardless of the real PCM's actual melting-point sharpness; a narrower
  numerical band reliably diverges when the melt front crosses it,
  confirmed across 3+ independent tests).
- **Use planar mode, not axisymmetric** — true axisymmetric caused an
  immediate, unresolvable divergence after 3 independent fix attempts in
  Tamil Nadu's case (see `CFD_VERIFICATION.md` for the full diagnosis).
  Unless you have a new, specific reason to believe {STATE}'s geometry is
  different enough to behave better, default to planar and disclose it as
  a scope limitation, the same way Tamil Nadu's results do.
- **Choose simulated duration from the real advection travel time**, not
  an arbitrary fixed number: `travel_time_s = (L_AXIAL/2 - R_CAPSULE) /
  inlet_velocity_m_s` — run for meaningfully longer than this. How much
  longer actually matters: Tamil Nadu's pre-resize design had enough
  margin in one regime to show real melting onset (0.33% liquid
  fraction), but after the tank/collector was resized (see
  `00_OVERVIEW.md`'s 2026-10-26/27 note), every regime's travel time grew
  enough that the same ~200s margin showed 0% melt everywhere — a
  genuinely different, honest result at a different design point, not a
  regression. Don't assume a fixed margin that worked for one of
  {STATE}'s designs will show melting for another; check the actual
  travel time for each regime's actual selected design.
- **ANSYS Student license pitfalls** (found during Tamil Nadu's final
  re-run, cost real debugging time): a `"Unexpected license problem;
  exiting"` error is not necessarily an expired/exhausted license — check
  for (and kill) any stray `ansyscl.exe` process still running from a
  *previous* Fluent session (including a GUI session closed with
  Stop-Process) before assuming the license itself is the problem. Also,
  **do not launch multiple PyFluent sessions concurrently** — even two
  `processor_count=2` sessions together exceeded the Student license's
  parallel-session cap and both failed with connection-refused/timeout
  errors that look like separate bugs but aren't; run regimes strictly
  one at a time.

Report final results the same way as Tamil Nadu's `CFD_VERIFICATION.md`:
a table of PCM / simulated duration / capsule temperature range / liquid
fraction melted, per regime, with the real numbers queried from Fluent's
own volume report definitions (`pyfluent_query_v2.py`'s pattern, reusable
as-is since it only reads the generic `3_s_2` capsule zone) — not
estimated or assumed.
