"""
tests/test_o1_shortlist.py
=============================
The pipeline uses Objective 1's MCDM top-3 as written (data/objective1/mcdm_topk_by_cluster.csv; Uttarakhand, K = 4 regimes,
Objective 1 commit 6be0dcd); the shortlist in configs/states/uttarakhand.yaml must agree with it.
"""

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src import io_utils
from src.io_utils import get_pcm_properties, get_regime, list_regimes, o1_rank_ties, o1_top3

EXPECTED = {
    0: ["PureTemp 58", "n-Octacosane (C28)", "PlusICE A58"],
    1: ["PureTemp 58", "n-Octacosane (C28)", "PlusICE A58"],
    2: ["PureTemp 58", "savE® OM55", "n-Hexacosane (C26)"],
    3: ["PureTemp 53", "n-Hexacosane (C26)", "Myristic acid (C14)"],
}


def test_pcm_shortlist_is_the_o1_top3_as_written():
    assert list_regimes("uttarakhand") == [0, 1, 2, 3]
    for cid in list_regimes("uttarakhand"):
        r = get_regime("uttarakhand", cid)
        assert r["pcm_shortlist"] == EXPECTED[cid]


def test_state_yaml_shortlist_equals_the_o1_file():
    for r in io_utils.load_state_config("uttarakhand")["regimes"]:
        assert r["pcm_shortlist"] == o1_top3("uttarakhand")[int(r["cluster_id"])]


def test_matches_o1_file_and_every_pcm_is_in_the_database():
    df = pd.read_csv(io_utils.O1_TOPK_FILE)
    assert len(df) == 12 and (df.groupby("cluster_id").size() == 3).all()
    for cid, names in o1_top3("uttarakhand").items():
        assert set(names) == set(df.loc[df.cluster_id == cid, "name"])
        for n in names:
            assert get_pcm_properties("uttarakhand", n)["Tm_C"] > 0


def test_no_rank1_tie_in_any_regime():
    ties = o1_rank_ties("uttarakhand")
    assert all(len(ties[c]) == 1 for c in (0, 1, 2, 3))
