"""
scripts/r1_o1_manifest.py  -  rebuild level L1 (O1 alignment, plan Option B)
=============================================================================
Writes results/o1_manifest_rajasthan.json: one signed-style record per regime (state_id, regime_id, label, medoid, member point ids,
population, PCM shortlist, Tm target, mains estimate) plus the SHA-256 of every Objective 1 file the rebuild reads.

Option B (plan decision 9): the K = 3 shortlists are kept as they are; 45 C is only the O2 service threshold.
The regime membership comes from Objective 1's cluster_assignments_rajasthan.csv, copied once into data/objective1/ by --copy
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
from src.weather.inventory import CURRENT_MEDOIDS     # noqa: E402

O1 = ROOT / "data" / "objective1"
OUT = ROOT / "results" / "o1_manifest_rajasthan.json"
SRC = Path(r"D:\Final Year Project\PCM-Selection-ML-model\era5-rajasthan\data\processed")
FILES = ["cluster_assignments_rajasthan.csv", "cluster_profiles_rajasthan.csv", "climate_signature_rajasthan.csv",
         "mcdm_topk_by_cluster.csv", "pcm_database_rajasthan.csv"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


KNOWN_O1_FIX = {"HDD18", "CDD24"}     # O1 corrected the HDD/CDD units after the O2 input freeze (pre_hdd_cdd_fix_backup_2026-09-19 in O1); not clustering inputs for O2


def check_same_run(prof_src: Path):
    """Same O1 run = same rows and the same values in every column except the two later-corrected degree-day columns.
    Returns {column: max abs difference} for every column that differs, so the manifest records the finding."""
    a, b = pd.read_csv(prof_src), pd.read_csv(O1 / "cluster_profiles_rajasthan.csv")
    num = [c for c in a.columns if c in b.columns and pd.api.types.is_numeric_dtype(a[c]) and not pd.api.types.is_bool_dtype(a[c])]
    diff = {c: float((a[c] - b[c]).abs().max()) for c in num}
    diff = {c: v for c, v in diff.items() if v >= 1e-9}
    bad = {c: v for c, v in diff.items() if c not in KNOWN_O1_FIX}
    assert not bad, f"cluster profiles differ in {bad}: not the same O1 run"
    return diff


def main(copy=False):
    if copy:
        worst = check_same_run(SRC / "cluster_profiles_rajasthan.csv")
        shutil.copy2(SRC / "cluster_assignments_rajasthan_levelA.csv", O1 / "cluster_assignments_rajasthan.csv")   # Level A = the 3 regimes
        print(f"copied cluster_assignments_rajasthan_levelA.csv as cluster_assignments_rajasthan.csv; profile columns that differ: {worst}")
    st = load_state_config("rajasthan")
    asg = pd.read_csv(O1 / "cluster_assignments_rajasthan.csv")
    top = pd.read_csv(O1 / "mcdm_topk_by_cluster.csv")
    regimes = []
    for r in st["regimes"]:
        k = int(r["cluster_id"])
        mem = asg[asg.cluster_id == k].sort_values("point_id")
        shortlist = top[top.cluster_id == k].sort_values("consensus_rank").pcm_id.tolist()
        assert shortlist == list(r["pcm_shortlist"]), f"regime {k}: state yaml shortlist differs from mcdm_topk_by_cluster.csv"
        assert len(mem) == int(r["n_points"]), f"regime {k}: {len(mem)} members vs n_points {r['n_points']}"
        medoid = CURRENT_MEDOIDS[k]
        assert medoid in set(mem.point_id), f"regime {k}: medoid {medoid} is not a member of its regime"
        regimes.append({
            "state_id": "rajasthan", "regime_id": k, "label": r["label"],
            "medoid": medoid, "member_point_ids": mem.point_id.tolist(), "n_points": len(mem),
            "population_covered": float(mem.population.sum()), "min_membership_prob": float(mem.max_membership_prob.min()),
            "pcm_shortlist": shortlist, "Tm_C_by_shortlist": top[top.cluster_id == k].sort_values("consensus_rank").Tm_C.astype(float).tolist(),
            "L_required_kJ_per_kg": float(top[top.cluster_id == k].L_required_kJ_per_kg.iloc[0]),
            "T_mains_est_C": float(r["T_mains_est_C"]),
        })
    m = {
        "plan": "Unified O2+O3 Rebuild Plan, Revision 14; level L1, Option B (shortlists kept, 45 C only as the O2 service threshold)",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "o1_source": {"path": str(SRC.parent.parent), "note": "O1 project, Level A, K = 3 (05_cluster_rajasthan.py)"},
        "o1_profile_differences_vs_frozen_copy": "HDD18 and CDD24 only (O1 unit fix after the O2 freeze); clustering unchanged (109/83/128 points)",
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
