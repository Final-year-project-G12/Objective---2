# 09 — The PCM-Design Decision Every State's Team Faces

Each state's own `09_NEXT_STEPS.md` (or Assam's equivalent framing inside
`07_PHASE7_OPTIMIZATION.md`) raises the same unresolved decision
independently. Collected here because it is a **cross-state, shared-config
decision**, not a per-state one — resolving it for one state without
resolving it for all four would break comparability.

## The decision

Across Tamil Nadu, Rajasthan, and Uttarakhand (the three
properly-validated states), Objective 1's shortlisted PCM justifies its
added mass/cost over a plain sensible tank in **at most 1 regime per
state**, and only where the local climate happens to keep the tank cold
enough for the PCM to cycle. In Rajasthan, it justifies it in **zero**
regimes — no shortlisted PCM there ever stays under the 65 °C stability
limit. (Assam's Phase 7 currently reports the opposite pattern — PCM
winning in all 3 regimes — but that result is not trustworthy; see
`08_PHASE7_OPTIMIZATION.md`.)

The team needs to decide which of the following is Objective 2's actual
conclusion, before Objective 3 builds a controller around it:

1. **Report it straight**: "for a 50 L direct-encapsulation tank at the
   frozen design bounds, Objective 1's shortlisted PCMs justify their
   mass in only the coldest, highest-`L_required` regime per state (or
   none, in a hot-dry state like Rajasthan)" — a valid, citable,
   comparative-across-states finding, and arguably the most interesting
   single result this project produces once framed this way.
2. **Widen the design bounds** (larger `capsule_diameter_m` or
   `capsule_count` ceiling in `design_bounds_shared.yaml`) to reach the
   documented 15–20% PCM-volume levels from Chen et al. (2025) and
   re-run Phases 2–7 for all four states — a **Phase-0-gate decision**
   (the file is frozen for all four states by design), not a quiet local
   edit to one state's copy.
3. **Flag the `Tm_target_C` derivation back to Objective 1**: every
   state's Gate 3 capability check shows a PCM melting point matched to
   the tank's *actual* operating range (not the climate/delivery-anchored
   value Objective 1 computes) does beat plain water — sometimes
   decisively (Tamil Nadu: 55.19% vs 52.26%; Uttarakhand: 41.27% vs
   40.71%). This suggests Objective 1's PCM-ranking criterion and
   Objective 2's actual operating envelope are not as tightly coupled as
   intended.
4. **Add an explicit high-temperature bypass/relief valve to the physics
   model itself**, rather than leaving it purely as a control-layer
   (Objective 3) concern — every state's Phase 7/8 finds that even the
   *safest* selected designs are frequently pushed past the 65/75 °C
   limits with no active protection modeled anywhere in Phases 1–7. This
   would change which designs pass the safety filter in Phase 7, not
   just how Objective 3 reacts to violations after the fact.

This is a judgment call for the guide/team, not something a DOE or
surrogate script should silently decide — and it applies to all four
states at once, since options 2 and 4 both touch the frozen shared
config.

## What NOT to do

Do not resolve this decision independently per state (e.g., widen bounds
for Rajasthan only, or add a bypass for Uttarakhand only) — the whole
point of running one shared framework across four states is cross-state
comparability (`O2_Unified_PerState_Execution_Framework.md` §0.1); a
per-state divergence here would silently break every four-state
comparison this project is set up to make.
