"""
tests/test_o2_designs.py
========================
Guards ansys/o2_designs.py, the loader the Fluent demos use to find "the design". Before 2026-11-24 the demos read the archived legacy file
results/tn_optimal_designs.csv and, when it was missing, fell back SILENTLY to a hard-coded legacy table (regime 0 -> n-Hexacosane).
These tests fail if the loader ever stops returning the common-plant funnel winners.
"""
import sys
from pathlib import Path

import pytest
import yaml

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "ansys"))
import o2_designs  # noqa: E402


def test_demo_designs_are_the_common_plant_winners():
    d = o2_designs.load()
    assert d is not None, "no design file found: the demos would fall back to the legacy table"
    assert d.source.str.contains("c16_funnel_winners").all() and d.source.str.contains("common plant").all()
    assert sorted(d.regime.tolist()) == [0, 1, 2]


def test_each_demo_pcm_is_in_objective_1s_shortlist_for_that_regime():
    d = o2_designs.load()
    regimes = yaml.safe_load(open(BASE / "configs" / "states" / "tamilnadu.yaml", encoding="utf-8"))["regimes"]
    shortlist = {r["cluster_id"]: r["pcm_shortlist"] for r in regimes}
    for _, r in d.iterrows():
        assert r.pcm in shortlist[int(r.regime)], f"regime {int(r.regime)}: {r.pcm} is not in Objective 1's shortlist"


def test_demo_designs_match_the_sealed_contract():
    import json
    run_dir = sorted((BASE / "results").glob("common100L_*"))
    if not run_dir:
        pytest.skip("one-shot test not run yet")
    contract = json.loads((run_dir[0] / "o3_contract_tamilnadu.json").read_text(encoding="utf-8"))
    d = o2_designs.load().set_index("regime")
    for reg in contract["regimes"]:
        k = reg["regime_id"]
        assert d.loc[k, "pcm"] == reg["pcm"]
        assert int(d.loc[k, "N"]) == reg["n_capsules"]
        assert abs(float(d.loc[k, "R_in_m"]) - reg["inner_radius_m"]) < 1e-12
