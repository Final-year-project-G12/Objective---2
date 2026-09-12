"""
pipeline.py
=============
Objective 2 entry point for Rajasthan. One parameterized script for every
state — `--state` only ever selects which config/weather/PCM/demand files
are read; the code path is identical regardless of state
(O2_Unified_PerState_Execution_Framework.md file-layout contract).

Structure and CLI contract mirror objective2-tamilnadu/pipeline.py. All
eight Objective 2 phases are wired for Rajasthan:

  geometry   — Phase 2 geometry & constraint boundary self-test
  simulate   — Phase 3 grey-box enthalpy simulator, one full-year case
  verify     — Phase 4 reduced verification gate battery (Gates 1-5)
  doe        — Phase 5 reduced DOE: generate + simulate + 80/20 split
  surrogate  — Phase 6 tree surrogate: train + hold-out eval by regime/PCM
  optimize   — Phase 7 one surrogate pass + simulator confirmation + selection rule
  robustness — Phase 8a light robustness (Monte Carlo re-runs through the real simulator)
  handoff    — Phase 8b recommendation cards + Objective 3 environment contract
  plots      — Phase 2-8 justification figures (Plotly; needs plotly + kaleido)

Stage split (robustness / handoff) and import layout match
objective2-tamilnadu/pipeline.py exactly.

USAGE
  python pipeline.py --state rajasthan --stage geometry
  python pipeline.py --state rajasthan --stage simulate --cluster 0 --pcm "RT50" --diameter 0.08 --count 24 --flow 0.025
  python pipeline.py --state rajasthan --stage simulate --cluster 0 --no-pcm
  python pipeline.py --state rajasthan --stage verify
  python pipeline.py --state rajasthan --stage doe
  python pipeline.py --state rajasthan --stage surrogate
  python pipeline.py --state rajasthan --stage optimize
  python pipeline.py --state rajasthan --stage robustness [--mc-draws 120]
  python pipeline.py --state rajasthan --stage handoff
  python pipeline.py --state rajasthan --stage plots
"""

import argparse
import json

from src.design.schema import DesignVector
from src.design.constraints import run_boundary_self_test
from src.simulation.run_case import run_case
from src.verify.gates import run_all_gates
from src.doe.run_batch import run_batch
from src.doe.split_cases import run_split
from src.surrogate.train import train_surrogate
from src.surrogate.evaluate import evaluate_by_group
from src.optimize.select_deployable import run_phase7
from src.plots.make_plots import main as make_all_plots
from src.robustness.monte_carlo import run_all as run_robustness, N_DRAWS as N_DRAWS_DEFAULT
from src.handoff.build_recommendation_cards import run as build_recommendation_cards
from src.handoff.build_obj3_contract import run as build_obj3_contract


def main():
    ap = argparse.ArgumentParser(description="Objective 2 pipeline — Rajasthan (all 8 phases wired)")
    ap.add_argument("--state", required=True, help="e.g. rajasthan")
    ap.add_argument("--stage", required=True,
                    choices=["geometry", "simulate", "verify", "doe", "surrogate", "optimize",
                             "robustness", "handoff", "plots"])
    ap.add_argument("--cluster", type=int, default=0, help="climate regime cluster_id (simulate stage)")
    ap.add_argument("--pcm", default="RT50", help="PCM name from mcdm_topk_by_cluster.csv")
    ap.add_argument("--diameter", type=float, default=0.08, help="capsule diameter, m")
    ap.add_argument("--count", type=int, default=19, help="capsule count")
    ap.add_argument("--flow", type=float, default=0.030, help="flow rate, kg/s")
    ap.add_argument("--no-pcm", action="store_true", help="run the plain-tank baseline (ignores --pcm)")
    ap.add_argument("--mc-draws", type=int, default=N_DRAWS_DEFAULT,
                    help="Phase 8 Monte Carlo draws per regime (robustness stage; min 50)")
    args = ap.parse_args()

    if args.stage == "geometry":
        print(f"Phase 2 — geometry & constraint boundary self-test "
              f"(state-agnostic; state={args.state} unused here)")
        _rows, all_deterministic = run_boundary_self_test()
        raise SystemExit(0 if all_deterministic else 1)

    elif args.stage == "simulate":
        pcm_name = None if args.no_pcm else args.pcm
        design = DesignVector(capsule_diameter_m=args.diameter, n_capsule=args.count,
                              flow_rate_kg_s=args.flow)
        print(f"Phase 3 — running 1 full-year case: state={args.state} cluster={args.cluster} "
              f"pcm={pcm_name} design={design.as_dict()}")
        out = run_case(args.state, args.cluster, pcm_name, design, record_hourly=True)
        if not out["valid"]:
            print(f"REJECTED at Phase 2 geometry gate: reason={out['reason']}")
            return
        print(json.dumps(out["metrics"], indent=2, default=str))

    elif args.stage == "verify":
        print(f"Phase 4 — running verification gates 1-5 for state={args.state}")
        _gates, go_no_go = run_all_gates(args.state)
        raise SystemExit(0 if go_no_go == "GO" else 1)

    elif args.stage == "doe":
        print(f"Phase 5 — generating and running the DOE batch for state={args.state}")
        run_batch(args.state)
        print("\nApplying case-level train/hold-out split ...")
        run_split(args.state)

    elif args.stage == "surrogate":
        print(f"Phase 6 — training the surrogate for state={args.state}")
        train_surrogate(args.state)
        print("\nEvaluating hold-out error by regime/PCM ...")
        evaluate_by_group(args.state)

    elif args.stage == "optimize":
        print(f"Phase 7 — optimization pass + simulator confirmation for state={args.state}")
        run_phase7(args.state)

    elif args.stage == "robustness":
        print(f"Phase 8a — Monte Carlo robustness analysis for state={args.state}")
        run_robustness(args.state, args.mc_draws)

    elif args.stage == "handoff":
        print(f"Phase 8b — recommendation cards + Objective 3 contract for state={args.state}")
        build_recommendation_cards(args.state)
        build_obj3_contract(args.state)

    elif args.stage == "plots":
        print(f"Generating Phase 2-8 justification plots for state={args.state}")
        make_all_plots(args.state)


if __name__ == "__main__":
    main()
