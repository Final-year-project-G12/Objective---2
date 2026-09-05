"""
pipeline.py
=============
Objective 2 entry point (Phases 1-4 implemented so far). One parameterized
script for every state — `--state` only ever selects which config/weather/
PCM/demand files are read; the code path is identical regardless of state
(O2_Unified_PerState_Execution_Framework.md file-layout contract).

USAGE
  python pipeline.py --state tamilnadu --stage geometry     # Phase 2 self-test
  python pipeline.py --state tamilnadu --stage simulate      # Phase 3 demo run (1 case)
  python pipeline.py --state tamilnadu --stage verify        # Phase 4 gates 1-5

  python pipeline.py --state tamilnadu --stage simulate --cluster 2 \\
      --pcm "n-Hexacosane (C26)" --diameter 0.06 --count 18 --flow 0.035
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


def main():
    ap = argparse.ArgumentParser(description="Objective 2 pipeline (Phases 1-7)")
    ap.add_argument("--state", required=True, help="e.g. tamilnadu")
    ap.add_argument("--stage", required=True,
                     choices=["geometry", "simulate", "verify", "doe", "surrogate", "optimize", "plots"])
    ap.add_argument("--cluster", type=int, default=0, help="climate regime cluster_id (simulate stage)")
    ap.add_argument("--pcm", default="n-Octacosane (C28)", help="PCM name from mcdm_topk_by_cluster.csv")
    ap.add_argument("--diameter", type=float, default=0.08, help="capsule diameter, m")
    ap.add_argument("--count", type=int, default=19, help="capsule count")
    ap.add_argument("--flow", type=float, default=0.030, help="flow rate, kg/s")
    ap.add_argument("--no-pcm", action="store_true", help="run the plain-tank baseline (ignores --pcm)")
    args = ap.parse_args()

    if args.stage == "geometry":
        print(f"Phase 2 — geometry & constraint boundary self-test (state-agnostic; state={args.state} unused here)")
        run_boundary_self_test()

    elif args.stage == "simulate":
        pcm_name = None if args.no_pcm else args.pcm
        design = DesignVector(capsule_diameter_m=args.diameter, n_capsule=args.count, flow_rate_kg_s=args.flow)
        print(f"Phase 3 — running 1 full-year case: state={args.state} cluster={args.cluster} "
              f"pcm={pcm_name} design={design.as_dict()}")
        out = run_case(args.state, args.cluster, pcm_name, design, record_hourly=True)
        if not out["valid"]:
            print(f"REJECTED at Phase 2 geometry gate: reason={out['reason']}")
            return
        print(json.dumps(out["metrics"], indent=2, default=str))

    elif args.stage == "verify":
        print(f"Phase 4 — running verification gates 1-5 for state={args.state}")
        run_all_gates(args.state)

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

    elif args.stage == "plots":
        print(f"Generating Phase 2-7 justification plots for state={args.state}")
        make_all_plots(args.state)


if __name__ == "__main__":
    main()
