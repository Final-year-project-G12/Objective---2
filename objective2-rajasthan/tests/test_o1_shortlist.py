"""
tests/test_o1_shortlist.py
=============================
The pipeline uses Objective 1's MCDM top-3 as written (data/objective1/mcdm_topk_by_cluster.csv); the
shortlist in configs/states/rajasthan.yaml must agree with it.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src import io_utils
from src.io_utils import get_pcm_properties, get_regime, list_regimes, o1_rank_ties, o1_top3

EXPECTED = {
    0: ["savE® OM55", "Palmitic-stearic acid/Expanded graphite", "Myristic acid/NBR-0.5"],
    1: ["PureTemp 60", "CrodaTherm 60", "n-Heptacosane (C27)"],
    2: ["n-Heptacosane (C27)", "PureTemp 58", "PlusICE A58"],
}


def test_pcm_shortlist_is_the_o1_top3_as_written():
    for cid in list_regimes("rajasthan"):
        r = get_regime("rajasthan", cid)
        assert r["pcm_shortlist"] == EXPECTED[cid]


def test_state_yaml_shortlist_equals_the_o1_file():
    for r in io_utils.load_state_config("rajasthan")["regimes"]:
        assert r["pcm_shortlist"] == o1_top3("rajasthan")[int(r["cluster_id"])]


def test_matches_o1_file_and_every_pcm_is_in_the_database():
    df = pd.read_csv(io_utils.O1_TOPK_FILE)
    assert len(df) == 9 and (df.groupby("cluster_id").size() == 3).all()
    for cid, names in o1_top3("rajasthan").items():
        assert set(names) == set(df.loc[df.cluster_id == cid, "pcm_id"])
        for n in names:
            assert get_pcm_properties("rajasthan", n)["Tm_C"] > 0


def test_cluster0_rank1_tie_is_visible_not_hidden():
    ties = o1_rank_ties("rajasthan")
    assert len(ties[0]) == 2 and len(ties[1]) == 1 and len(ties[2]) == 1
