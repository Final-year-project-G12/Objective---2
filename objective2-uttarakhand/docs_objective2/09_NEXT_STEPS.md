# 09 — The PCM-Design Decision the Team Faced, and How It Was Resolved

> **Status: RESOLVED (2026-09-14).** This document originally posed an
> open decision (below) before Phase 8 first ran. Both of the two
> substantive options it raised were **actioned**, in the order the team
> chose: (3) retarget `Tm_target_C`, then (2) widen the design bounds,
> then apply a further scope correction to the selection rule. See
> `12_TM_TARGET_RETARGETING.md`, `13_DESIGN_BOUNDS_WIDENING.md`, and
> `08_PHASE7_OPTIMIZATION.md` for what was actually done and what came out
> of it. This document is kept as a historical record of the decision
> point and the reasoning that led to actioning it, not as a live
> to-do list.

## The original decision (as posed, before Phase 8 first ran)

Phase 7's first run (400-candidate-per-pair search, pre-retargeting)
found that in all 5 regimes, every shortlisted PCM's best-found useful
energy landed within ~0.1% of the plain tank's — statistically
indistinguishable, with the pick effectively decided by the
pump-energy/PCM-mass tie-break rather than a real performance advantage.
Gate 3's capability check had already shown this was not a simulator
defect: a synthetic PCM matched to the tank's actual operating range
clearly beat plain tank, while the real, climate-anchored shortlist
(Tm≈57–58°C) did not.

Three options were on the table:

1. **Report it straight** — the flat PCM-vs-plain-tank landscape is
   itself a valid, citable finding.
2. **Widen the design bounds** to reach the documented 15–20% PCM-volume
   levels.
3. **Retarget `Tm_target_C`** to the tank's own real operating
   temperature rather than Objective 1's climate/delivery formula.

## What was actually decided and done

The team (via Tamil Nadu's implementation, later ported here) chose **(3)
then (2) together**, not (1) alone:

- **Retargeting** (doc 12) replaced each regime's `Tm_target_C` with the
  simulated median charging-hour water temperature, and re-selected the
  PCM shortlist against it. This is exactly option 3 above, executed via
  `src/design/retarget_tm.py` rather than "flagging it back to Objective
  1" — Objective 2 re-derived its own target from its own simulator
  output instead of waiting on an upstream change.
- **Bounds widening** (doc 13) raised `capsule_count.max` from 24 to 37,
  reaching 19.84% PCM volume fraction — option 2, applied as a genuinely
  shared-config change (Tamil Nadu's version of this doc explicitly
  flagged that Rajasthan/Assam/Uttarakhand should get it "whenever those
  states' Objective 2 is run next" — this is that run).
- **A further scope correction** (not one of the three original options,
  discovered afterward) excluded plain tank from winning the final
  selection at all, since the assignment presupposes a PCM design.

## What this resolved, and what it did not

**Resolved**: every regime's optimal PCM design now genuinely (if
narrowly, 0.01–0.14%) beats plain tank on useful energy — the flat,
indistinguishable landscape from before retargeting is gone.

**Not resolved, and now the central finding instead**: a PCM matched to
*typical* operating conditions still exceeds its own 65°C safety limit on
*peak* days in 4 of 5 regimes. Retargeting fixed the energy-comparison
question but exposed a sharper safety question — see
`08_PHASE7_OPTIMIZATION.md` and `10_PHASE8_ROBUSTNESS_HANDOFF.md`. This is
now squarely Objective 3's problem (active bypass/discharge control), not
something a further Objective 2 config change can resolve — no static PCM
choice avoids overheating on the sunniest days of the year without either
active control or a fundamentally larger tank/collector than the frozen
50 L / 1.5 m² sizing.

**Also unresolved**: regime 1 (the coldest regime) has no PCM in the
current database that survives a melting window centered on its own
retargeted target (27.8°C) — it keeps its old, equally-mismatched
shortlist. Expanding the PCM database with lower-melting-point candidates
suitable for very cold climates remains open work for whoever owns the
PCM database, not something Objective 2's code can fix by re-selecting
among existing options.
