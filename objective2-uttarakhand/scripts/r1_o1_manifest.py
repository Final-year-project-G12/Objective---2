"""
scripts/r1_o1_manifest.py  -  rebuild level L1 (O1 alignment, plan Option B)
=============================================================================
Writes results/o1_manifest_uttarakhand.json: one signed-style record per regime (state_id, regime_id, label, medoid, member point ids,
population, PCM shortlist, Tm target, mains estimate) plus the SHA-256 of every Objective 1 file the rebuild reads.

Option B (plan decision 9): the K = 4 shortlists are kept as they are; 45 C is only the O2 service threshold.
The regime membership comes from Objective 1's cluster_assignments_uttarakhand.csv, copied once into data/objective1/ by --copy
(source path in config.OBJ1_ASSIGNMENTS_SRC; read-only). The script checks that it belongs to the same O1 run as the cluster profiles
already in data/objective1/ (same counts per regime, same medoids, profile values equal to 1e-9).

Usage:  python scripts/r1_o1_manifest.py [--copy]
"""
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.io_utils import load_state_config          # noqa: E402

O1 = ROOT / "data" / "objective1"
OUT = ROOT / "results" / "o1_manifest_uttarakhand.json"
SRC = Path(r"D:\PCM-Selection-ML-model\era5-uttarakhand\data\processed\clustering")
FILES = ["cluster_assignments_uttarakhand.csv", "cluster_profiles_uttarakhand.csv", "climate_signature_uttarakhand.csv",
         "mcdm_topk_by_cluster.csv", "pcm_database_uttarakhand.csv"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def check_same_run(prof_src: Path):
    a, b = pd.read_csv(prof_src), pd.read_csv(O1 / "cluster_profiles_uttarakhand.csv")
    num = [c for c in a.columns if c in b.columns and pd.api.types.is_numeric_dtype(a[c])]
    worst = max(float((a[c] - b[c]).abs().max()) for c in num)
    assert worst < 1e-9, f"cluster profiles differ by {worst}: not the same O1 run"
    return worst


def main(copy=False):
    if copy:
        worst = check_same_run(SRC / "cluster_profiles_uttarakhand.csv")
        shutil.copy2(SRC / "cluster_assignments_uttarakhand.csv", O1 / "cluster_assignments_uttarakhand.csv")
        print(f"copied cluster_assignments_uttarakhand.csv (profiles agree to {worst:.1e})")
    st = load_state_config("uttarakhand")
    asg = pd.read_csv(O1 / "cluster_assignments_uttarakhand.csv")
    top = pd.read_csv(O1 / "mcdm_topk_by_cluster.csv")
    regimes = []
    for r in st["regimes"]:
        k = int(r["cluster_id"])
        mem = asg[asg.cluster_id == k].sort_values("point_id")
        shortlist = top[top.cluster_id == k].sort_values("consensus_rank").name.tolist()
        assert shortlist == list(r["pcm_shortlist"]), f"regime {k}: state yaml shortlist differs from mcdm_topk_by_cluster.csv"
        assert len(mem) == int(r["n_points"]), f"regime {k}: {len(mem)} members vs n_points {r['n_points']}"
        medoid = r["medoid_point"]
        assert medoid in set(mem.point_id), f"regime {k}: medoid {medoid} is not a member of its regime"
        regimes.append({
            "state_id": "uttarakhand", "regime_id": k, "label": r["label"],
            "medoid": medoid, "member_point_ids": mem.point_id.tolist(), "n_points": len(mem),
            "population_covered": float(mem.population.sum()), "min_membership_prob": float(mem.max_membership_prob.min()),
            "pcm_shortlist": shortlist, "Tm_target_C": float(top[top.cluster_id == k].Tm_target_C.iloc[0]),
            "T_mains_est_C": float(r["T_mains_est_C"]),
        })
    m = {
        "plan": "Unified O2+O3 Rebuild Plan, Revision 13; level L1, Option B (shortlists kept, 45 C only as the O2 service threshold)",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "o1_source": {"path": str(SRC.parent.parent.parent), "note": "O1 project, K_FINAL = 4 (05_cluster_uttarakhand.py)"},
        "files_sha256": {f: sha(O1 / f) for f in FILES},
        "regimes": regimes,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(m, indent=1), encoding="utf-8")
    print("wrote", OUT)
    for r in regimes:
        print(f"  regime {r['regime_id']}: medoid {r['medoid']}, {r['n_points']} points, pop {r['population_covered']:,.0f}, "
              f"shortlist {r['pcm_shortlist']}")


if __name__ == "__main__":
    main(copy="--copy" in sys.argv)
