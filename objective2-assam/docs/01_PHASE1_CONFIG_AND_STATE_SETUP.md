# 01 — Phase 1 Audit: Frozen Configuration & State Setup (Assam)

Files: `configs/system_config_shared.yaml`, `configs/design_bounds_shared.yaml`,
`configs/states/assam.yaml`. Loader: `src/io_utils.py`.

> Rewritten from Assam's actual `configs/states/assam.yaml` — the
> previous version of this doc described Rajasthan's regimes, PCMs, and
> 300 L/day demand with no Assam content.

## `system_config_shared.yaml` / `design_bounds_shared.yaml` — frozen, shared across all 4 states

Same collector (1.5 m², F_R(τα)=0.75), tank (50 L, H:D=2:1, U_tank=0.8
W/m²K), safety limits (**max water 75 °C, max PCM 65 °C**, max pressure
3.5 bar), delivery target (45 °C — see caveat below on Assam's own
`Tm_target_C`), and sphere-only/staggered-only design bounds (diameter
0.02–0.08 m, count 8–24, flow 0.010–0.050 kg/s) as every other state.
These files are byte-identical across states by design — nothing here
is Assam-specific.

## `configs/states/assam.yaml` — Phase 1's actual output

- **3 Level-A GMM regimes** (`cluster_id` 0–2, K_FINAL=3, same regime
  count as Rajasthan but a different climate and different medoids):

  | Cluster | Label | Medoid | n_points | Population | T_mains_est_C | L_required_kJ/kg |
  |---|---|---|---|---|---|---|
  | 0 | Lower Brahmaputra Valley (moist valley) | ASP_0012 | 33 | 4,757,891 | 19.89 | 252.09 |
  | 1 | Upper Assam Tea Belt (warm valley) | ASP_0092 | 61 | 4,271,199 | 19.10 | 258.69 |
  | 2 | Barak Valley & Southern Hills (elevated, cooler) | ASP_0028 | 35 | 2,466,324 | 16.59 | 279.70 |

  `Tm_target_C = 44.0 °C` for all 3 clusters (lower than Rajasthan's
  57.0 °C — Assam's colder mains water needs a smaller lift to the
  45 °C delivery target, consistent with the framework's delivery-
  anchored `Tm_target_C` derivation).

- **PCM shortlist**: identical across all 3 regimes —
  `savE® OM48, savE® OM50, savE® OM46`. Per `assam.yaml`'s own embedded
  note, this is **not** a standard Objective 1 MCDM Top-3: Objective 1's
  confirmed-feasible K=3 MCDM ranking for Assam returned **zero**
  confirmed candidates, and an earlier K=4 MCDM ranking was physically
  invalidated in Objective 1's own Phase 10 (ρ = −0.52 to −0.64
  correlation between MCDM rank and actual simulated solar-fraction
  performance; the old rank-1 PCM, RT44HC, came last). The 3 PCMs used
  here are Objective 1's **Phase 9/10 physics-validated candidate
  universe** instead — a materially different provenance from
  Rajasthan/Tamil Nadu's shortlists, and it should be described that way
  in any paper section rather than as "MCDM Top-3."

- **Demand profile**: **100 L/day** (50 L @ 07:00 IST + 50 L @ 19:00
  IST), `data/demand/demand_profile_assam.csv` — matches Assam
  Objective 1's own SWH design specification and 10-year physics
  validation. **This is 1/3 of Rajasthan/Tamil Nadu's 300 L/day**, so
  Assam's absolute energy numbers are not directly comparable across
  states without normalizing for demand.

- **Mains temperature**: 15–28 °C range (framework doc, Assam row);
  per-regime point estimates 16.59–19.89 °C — noticeably colder than
  Rajasthan's 24.5–25.8 °C, consistent with Assam's humid-subtropical,
  less solar-intense climate.

## Phase 0 — climate-signature sanity check: PASSED (embedded, no standalone report file)

Unlike Rajasthan (which has a separate `check_climate_signature.py` /
`results/phase0_climate_signature_check.txt`), Assam's Phase 0 check
result is recorded directly inside `assam.yaml`'s
`climate_signature_sanity_check` block rather than as a standalone
results file:

- Annual GHI daily band expected 2.0–4.5 kWh/m²/day;
  `cluster_profiles_assam.csv` reports 3.68–4.08 kWh/m²/day (climate
  estimate) and the exported 2025 hourly weather gives 2.28–2.52
  kWh/m²/day daily mean across the 3 medoids — both inside/consistent
  with the expected humid-subtropical band.
- `Ta_mean` 22.6–25.9 °C, `RH_mean` 75.8–79.0% — matches the stated
  "humid-subtropical, monsoonal cloud attenuation, RH > 70%" signature,
  visibly different from Rajasthan's hot-dry signature.
- Zero timestamp gaps across all 3 medoids' 2025 hourly series (8,760
  hours each).
- **Status: PASSED.**

If a standalone `results/phase0_climate_signature_check.txt` is wanted
for Assam (for consistency with Rajasthan/Tamil Nadu's audit trail),
`check_climate_signature.py` would need to be run with `--state assam`
— not done in this repo as of this audit.

## How Phase 1 was verified

Same as every state: `load_state_config("assam")` in `src/io_utils.py`
is exercised on every Phase 2+ run, so every successful downstream run
is an implicit Phase 1 integration test.
