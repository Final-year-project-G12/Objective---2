"""
scripts/r3_probe_pcm_gain.py  -  rebuild L3 diagnostic (2026-11-22): does any PCM design gain on the common plant?
====================================================================================================================
EXPLORATORY, explore year 2018 only, 150 s, 10 nodes; not a search and not a reported design. It produced the numbers recorded in
docs/REBUILD_COMMON100L.md section 3c:
  part 1  regimes 0, 1, 3; rank-1 PCM; R_in 20 / 40 mm x PCM 5 / 15 / 30 % x single-layer / staggered x anchor bottom / centre / top;
          paired E_del45_window gain against the same-flow, same-anchor water-only tank.
  part 2  regimes 1 and 3; R_in 40 mm staggered, centre; PCM 5 / 15 / 30 %; demand 100 / 150 / 300 L/day at 45 C and 100 L/day at 50 C
          (demand through volume_multiplier, threshold through delivery.target_temp_C).
Usage: python scripts/r3_probe_pcm_gain.py [part1|part2]
"""
import itertools
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.design.space import geometry_bounds, to_design          # noqa: E402
from src.io_utils import get_regime                               # noqa: E402
from src.simulation.run_case import run_case                      # noqa: E402
from src.weather import roles                                     # noqa: E402
from src.weather.inventory import CURRENT_MEDOIDS                 # noqa: E402


def kw(cid, **extra):
    return dict(design_bounds=geometry_bounds(), weather=roles.load_point_year("uttarakhand", cid, CURRENT_MEDOIDS[cid], 2018, "explore"),
                tank_model="multinode", n_nodes=10, compute_tes_metrics=True, night_day_stride=0, record_hourly=False, **extra)


def part1():
    rows = []
    for cid in (0, 1, 3):
        pcm = get_regime("uttarakhand", cid)["pcm_shortlist"][0]
        for anc in ("bottom", "center", "top"):
            pl = run_case("uttarakhand", cid, None, to_design(0.04, 0.1, 0.03, "staggered"), stack_anchor=anc, **kw(cid))["tes"]["E_del45_window_kWh"]
            for R, f, a in itertools.product((0.02, 0.04), (0.05, 0.15, 0.30), ("single-layer", "staggered")):
                r = run_case("uttarakhand", cid, pcm, to_design(R, f, 0.03, a), stack_anchor=anc, **kw(cid))
                if r["metrics"] is not None:
                    rows.append(dict(regime=cid, anchor=anc, R=R, f=f, arr=a, g=r["tes"]["E_del45_window_kWh"] - pl))
    d = pd.DataFrame(rows)
    d.to_csv(ROOT / "results" / "l3_probe_pcm_gain_designs.csv", index=False)
    print(d.groupby(["regime", "anchor"]).g.agg(["max", "min"]).round(1))


def part2():
    rows = []
    for cid in (1, 3):
        pcm = get_regime("uttarakhand", cid)["pcm_shortlist"][0]
        for lab, vm, tgt in (("100 L/day, 45 C", 1.0, 45), ("150 L/day, 45 C", 1.5, 45), ("300 L/day, 45 C", 3.0, 45), ("100 L/day, 50 C", 1.0, 50)):
            k = kw(cid, stack_anchor="center", volume_multiplier=vm, system_config_overrides={"delivery": {"target_temp_C": tgt}})
            pl = run_case("uttarakhand", cid, None, to_design(0.04, 0.15, 0.03, "staggered"), **k)["tes"]["E_del45_window_kWh"]
            for f in (0.05, 0.15, 0.30):
                g = run_case("uttarakhand", cid, pcm, to_design(0.04, f, 0.03, "staggered"), **k)["tes"]["E_del45_window_kWh"] - pl
                rows.append(dict(regime=cid, case=lab, fraction=f, g_window=g))
    d = pd.DataFrame(rows)
    d.to_csv(ROOT / "results" / "l3_probe_pcm_gain_demand.csv", index=False)
    print(d.pivot_table(index=["regime", "case"], columns="fraction", values="g_window").round(1))


if __name__ == "__main__":
    {"part1": part1, "part2": part2}[sys.argv[1] if len(sys.argv) > 1 else "part1"]()
