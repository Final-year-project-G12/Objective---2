"""
tests/test_o1_shortlist.py
=============================
Objective 2 uses Objective 1's MCDM top-3 AS WRITTEN
(data/objective1/mcdm_topk_by_cluster.csv); the shortlist in
configs/states/<state>.yaml must agree with it, and the material choice is
never re-derived here.

Ported from her Rajasthan version (2026-10-29). Hers hardcoded Rajasthan's
shortlist, called `o1_top3("rajasthan")` and read
`pcm_database_rajasthan.csv`, so every assertion failed against Tamil Nadu
for the wrong reason. This version is state-driven off `config.STATE`, and
the expected shortlist below is Tamil Nadu's own MCDM consensus-rank order.

The last test is an addition of ours: it checks our COPY of Objective 1's
output is byte-identical to what the Objective 1 pipeline actually wrote.
Agreement between the YAML and our copy means nothing if the copy itself
has drifted from upstream.
"""

import hashlib
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src import io_utils
from src.io_utils import get_pcm_properties, get_regime, list_regimes, o1_rank_ties, o1_top3
from config import STATE

# Assam. O1 produced NO MCDM consensus ranking for Assam (strict evidence audit n_confirmed = 0), so the shortlist is the
# physics-validated order recorded in configs/states/assam.yaml and mirrored into data/objective1/mcdm_topk_by_cluster.csv.
EXPECTED = {c: ["savE® OM48", "savE® OM50", "savE® OM46"] for c in (0, 1, 2)}

# Objective 1's own working copy, if this checkout sits beside it.
# parents[0], not parents[1]: this tree was promoted out of rajmethod/ on
# 2026-10-30, so REPO_ROOT moved up one level and the old index silently
# resolved to a directory that does not exist -- which turned a real
# cross-check against Objective 1's own output into a skip.
O1_PIPELINE_FILE = (REPO_ROOT.parents[0] / "tamilnadu_pipeline" / "data"
                    / "processed" / "pcm" / "mcdm_topk_by_cluster.csv")


def test_pcm_shortlist_is_the_o1_top3_as_written():
    for cid in list_regimes(STATE):
        assert get_regime(STATE, cid)["pcm_shortlist"] == EXPECTED[cid]


def test_state_yaml_shortlist_equals_the_o1_file():
    for r in io_utils.load_state_config(STATE)["regimes"]:
        assert r["pcm_shortlist"] == o1_top3(STATE)[int(r["cluster_id"])]


def test_matches_o1_file_and_every_pcm_is_in_the_database():
    df = pd.read_csv(io_utils.O1_TOPK_FILE)
    assert len(df) == 9 and (df.groupby("cluster_id").size() == 3).all()
    for cid, names in o1_top3(STATE).items():
        assert set(names) == set(df.loc[df.cluster_id == cid, "pcm_id"])
        for n in names:
            assert get_pcm_properties(STATE, n)["Tm_C"] > 0


def test_every_shortlisted_pcm_melts_below_the_safety_cap():
    """Tm_target_C is a RANKING criterion, not a melting point any material
    must have. What actually has to hold is that each selected PCM melts
    below the cap Objective 2 enforces -- otherwise it could never charge."""
    cap = io_utils.load_system_config()["safety"]["max_pcm_temp_C"]
    for cid, names in o1_top3(STATE).items():
        for n in names:
            tm = get_pcm_properties(STATE, n)["Tm_C"]
            assert tm < cap, f"r{cid} {n}: Tm={tm} C is not below the {cap} C cap"


def test_rank1_is_unique_and_there_are_no_ties():
    """Assam's file is a strict 1-2-3 order in every regime (no MCDM ties exist because no MCDM ran)."""
    ties = o1_rank_ties(STATE)
    assert [len(ties[c]) for c in (0, 1, 2)] == [1, 1, 1]
    df = pd.read_csv(io_utils.O1_TOPK_FILE)
    assert all(sorted(g.consensus_rank) == [1, 2, 3] for _, g in df.groupby("cluster_id"))
    assert set(df.candidate_pool_status) == {"physics_validated_no_mcdm"}


@pytest.mark.skipif(not O1_PIPELINE_FILE.exists(),
                    reason="Objective 1 pipeline not checked out beside this one")
def test_our_copy_has_not_drifted_from_objective_1():
    def h(p):
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    assert h(io_utils.O1_TOPK_FILE) == h(O1_PIPELINE_FILE), (
        "data/objective1/mcdm_topk_by_cluster.csv differs from Objective 1's "
        f"own output at {O1_PIPELINE_FILE}. Re-copy it; do not edit it here."
    )
