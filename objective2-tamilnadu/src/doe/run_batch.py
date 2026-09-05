"""
src/doe/run_batch.py
=======================
Phase 5 / D2.4 — runs every case produced by generate_cases.py through the
Phase 2 geometry gate and (if valid) the Phase 3 simulator, and writes one
row per CASE (not per timestep) to results/<state>/design_cases.parquet
(+ a .csv copy for quick inspection without a parquet reader).

Keeps failed/infeasible cases with their reason code — never silently
drops them (framework doc §6.2: "Keep failed and infeasible cases. They
define the feasibility boundary...").
"""

import time
import sys

import pandas as pd

from config import RESULTS_DIR
from src.design.schema import DesignVector
from src.simulation.run_case import run_case
from src.doe.generate_cases import generate_all_cases

SIMULATOR_VERSION = "sim_v1_tamilnadu"   # released in Phase 4 — see docs_objective2/04_...


def run_case_spec(state: str, spec):
    design = DesignVector(capsule_diameter_m=spec.capsule_diameter_m,
                           n_capsule=spec.n_capsule, flow_rate_kg_s=spec.flow_rate_kg_s)
    t0 = time.time()
    out = run_case(state, spec.regime_id, spec.pcm_id, design, record_hourly=False)
    runtime_s = time.time() - t0

    row = {
        "case_id": spec.case_id, "regime_id": spec.regime_id,
        "pcm_id": spec.pcm_id if spec.pcm_id is not None else "NONE_plain_tank",
        "sampling_method": spec.sampling_method, "seed": spec.seed,
        "capsule_diameter_m": spec.capsule_diameter_m, "n_capsule": spec.n_capsule,
        "flow_rate_kg_s": spec.flow_rate_kg_s,
        "simulator_version": SIMULATOR_VERSION, "runtime_s": runtime_s,
        "valid": out["valid"], "reason": out["reason"],
    }

    geom = out["geometry"]
    for k in ("pcm_thickness_m", "pcm_volume_fraction", "void_fraction",
              "pressure_drop_pa", "pump_power_w", "reynolds_number_particle",
              "hydraulic_diameter_m", "below_min_pcm_fraction"):
        row[f"geom_{k}"] = geom.get(k)

    if out["valid"]:
        row.update(out["metrics"])
    return row


def run_batch(state: str, n_lhs_per_pair: int = 8, progress_every: int = 20):
    cases, manifest = generate_all_cases(state, n_lhs_per_pair=n_lhs_per_pair)
    print(f"Running {len(cases)} DOE cases for state={state} "
          f"(simulator={SIMULATOR_VERSION}) ...")

    rows = []
    t_start = time.time()
    for i, spec in enumerate(cases):
        rows.append(run_case_spec(state, spec))
        if (i + 1) % progress_every == 0 or (i + 1) == len(cases):
            elapsed = time.time() - t_start
            print(f"  {i+1}/{len(cases)} cases done ({elapsed:.1f}s elapsed)")

    df = pd.DataFrame(rows)
    out_dir = RESULTS_DIR / state
    out_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = out_dir / "design_cases.parquet"
    csv_path = out_dir / "design_cases.csv"
    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False)

    n_valid = int(df["valid"].sum())
    n_invalid = len(df) - n_valid
    print(f"\nDONE — {len(df)} cases total: {n_valid} valid/simulated, {n_invalid} rejected at Phase 2 geometry.")
    if n_invalid:
        print("Rejection reasons:")
        print(df.loc[~df["valid"], "reason"].value_counts().to_string())
    print(f"\nSaved: {parquet_path}")
    print(f"Saved: {csv_path}")
    return df, manifest


if __name__ == "__main__":
    state = sys.argv[1] if len(sys.argv) > 1 else "tamilnadu"
    run_batch(state)
