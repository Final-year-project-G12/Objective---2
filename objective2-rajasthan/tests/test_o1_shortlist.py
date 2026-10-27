"""
tests/test_o1_shortlist.py
=============================
G6 (O2, decision D2): the main pipeline uses Objective 1's MCDM top-3 as written; the
retargeted shortlist is kept only as a labelled comparison.
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
RETIRED = {0: ["savE® OM42", "RT44HC", "RT47"], 1: ["n-Tricosane (C23)", "savE® OM49", "RT45HC"],
           2: ["RT45HC", "Lauric acid (C12)", "n-Docosane (C22)"]}


def test_pcm_shortlist_is_the_o1_top3_as_written():
    for cid in list_regimes("rajasthan"):
        r = get_regime("rajasthan", cid)
        assert r["pcm_shortlist"] == EXPECTED[cid]
        assert r["pcm_shortlist_source"] == "o1_mcdm_topk_by_cluster.csv"


def test_retargeted_shortlist_only_survives_as_labelled_comparison():
    for cid in list_regimes("rajasthan"):
        assert get_regime("rajasthan", cid)["pcm_shortlist_retargeted"] == RETIRED[cid]
    assert not set(RETIRED[0]) & set(EXPECTED[0])


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


def test_legacy_switch_reproduces_old_behaviour(monkeypatch):
    monkeypatch.setattr(io_utils, "SHORTLIST_SOURCE", "retargeted")
    assert get_regime("rajasthan", 0)["pcm_shortlist"] == RETIRED[0]
