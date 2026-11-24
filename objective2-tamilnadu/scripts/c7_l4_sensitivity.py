"""
scripts/c7_l4_sensitivity.py   (level L4, step O2-6)
=====================================================
One-at-a-time sensitivity on the common plant, one regime per call. Reference design: R_in 25 mm, 30 %, staggered, 0.030 kg/s,
center anchor, each of the regime's O1 PCMs, explore years 2017-2018, dt 150 s. EVERY case is PAIRED: the water-only twin is
run under the same perturbation (same weather, demand, mains, collector, flow, shield), so the gain is PCM minus plain.
Blocks: collector (F_R*tau-alpha, F_R*U_L +/-10 %), area 2.5 m2 (legacy), mains +/-3 C, demand 70/150/300 L/day, stack anchor,
PCM properties (latent +/-10 %, Tm +/-1.5 K, conductivity +/-20 %), flow 0.015 / 0.050 kg/s with the F_R(flow) model ON (sensitivity only).
Usage: python scripts/c7_l4_sensitivity.py <cluster_id>   -> results/c7_l4_sensitivity_r<id>.csv
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import io_utils                                   # noqa: E402
from src.design.space import geometry_bounds, to_design    # noqa: E402
from src.io_utils import get_pcm_properties, get_regime, load_system_config   # noqa: E402
from src.simulation.run_case import run_case               # noqa: E402
from src.weather import roles                              # noqa: E402
from src.weather.inventory import CURRENT_MEDOIDS          # noqa: E402
from config import STATE                                   # noqa: E402

YEARS = (2017, 2018)
BASE = dict(r=0.025, f=0.30, flow=0.030, arr="staggered")
CFG = load_system_config()
FR_TA, FR_UL = CFG["collector"]["fr_tau_alpha"], CFG["collector"]["fr_ul_W_m2K"]


def cases(pcm_rec):
    tm, lh, k = pcm_rec["Tm_C"], pcm_rec["latent_heat_kJ_kg"], pcm_rec["TC_W_mK"]
    C = lambda **kw: {"system_config_overrides": {"collector": kw}}                  # noqa: E731
    return [
        ("reference", "reference", {}),
        ("collector", "F_R*tau-alpha -10%", C(fr_tau_alpha=FR_TA * 0.9)), ("collector", "F_R*tau-alpha +10%", C(fr_tau_alpha=FR_TA * 1.1)),
        ("collector", "F_R*U_L -10%", C(fr_ul_W_m2K=FR_UL * 0.9)), ("collector", "F_R*U_L +10%", C(fr_ul_W_m2K=FR_UL * 1.1)),
        ("collector", "area 2.5 m2 (legacy)", C(area_m2=2.5)),
        ("mains", "mains -3 C", {"mains": -3.0}), ("mains", "mains +3 C", {"mains": +3.0}),
        ("demand", "70 L/day", {"vol": 0.7}), ("demand", "150 L/day", {"vol": 1.5}), ("demand", "300 L/day (legacy)", {"vol": 3.0}),
        ("anchor", "anchor bottom", {"anchor": "bottom"}), ("anchor", "anchor top", {"anchor": "top"}),
        ("pcm", "latent -10%", {"ovr": {"latent_heat_kJ_kg": lh * 0.9}}), ("pcm", "latent +10%", {"ovr": {"latent_heat_kJ_kg": lh * 1.1}}),
        ("pcm", "Tm -1.5 K", {"ovr": {"Tm_C": tm - 1.5}}), ("pcm", "Tm +1.5 K", {"ovr": {"Tm_C": tm + 1.5}}),
        ("pcm", "conductivity -20%", {"ovr": {"TC_W_mK": k * 0.8}}), ("pcm", "conductivity +20%", {"ovr": {"TC_W_mK": k * 1.2}}),
        ("flow", "flow 0.015 + F_R(flow) ON", {"flow": 0.015, "frflow": True}), ("flow", "flow 0.050 + F_R(flow) ON", {"flow": 0.050, "frflow": True}),
        ("flow", "flow 0.015 (F_R const)", {"flow": 0.015}), ("flow", "flow 0.050 (F_R const)", {"flow": 0.050}),
    ]


def run_pair(cid, w, pcm, spec, mains_C):
    flow = spec.get("flow", BASE["flow"])
    dv = to_design(BASE["r"], BASE["f"], flow, BASE["arr"])
    ov = {"solver": {"timestep_s": 150.0}}
    for k, v in (spec.get("system_config_overrides") or {}).items():
        ov.setdefault(k, {}).update(v)
    if spec.get("frflow"):
        ov.setdefault("collector", {}).setdefault("flow_dependent_fr", {})["enabled"] = True
    kw = dict(design_bounds=geometry_bounds(), weather=w, tank_model="multinode", n_nodes=10, compute_tes_metrics=True,
              night_day_stride=0, system_config_overrides=ov, volume_multiplier=spec.get("vol", 1.0),
              mains_temp_override_C=None if "mains" not in spec else mains_C + spec["mains"])
    a = run_case(STATE, cid, pcm, dv, stack_anchor=spec.get("anchor", "center"), pcm_record_overrides=spec.get("ovr"), **kw)
    b = run_case(STATE, cid, None, dv, **kw)
    ta, tb, ma, mb = a["tes"], b["tes"], a["metrics"], b["metrics"]
    return {"g_window": ta["E_del45_window_kWh"] - tb["E_del45_window_kWh"], "g_annual": ta["E_del45_annual_kWh"] - tb["E_del45_annual_kWh"],
            "plain_window": tb["E_del45_window_kWh"], "pcm_window": ta["E_del45_window_kWh"],
            "d_overheat_h": (ma["shield_water_h"] + ma["shield_pcm_h"]) - mb["shield_water_h"], "pcm_max_C": ma["max_pcm_temp_C"]}


def main(cid):
    mains_C = get_regime(STATE, cid)["T_mains_est_C"]
    ws = {y: roles.load_point_year(STATE, cid, CURRENT_MEDOIDS[cid], y, "explore") for y in YEARS}
    rows = []
    for pcm in io_utils.o1_top3(STATE)[cid]:
        rec = get_pcm_properties(STATE, pcm)
        for block, label, spec in cases(rec):
            per = [run_pair(cid, ws[y], pcm, spec, mains_C) for y in YEARS]
            row = {"regime": cid, "pcm": pcm, "block": block, "case": label}
            for k in per[0]:
                row[k] = sum(p[k] for p in per) / len(per)
            rows.append(row)
            print(cid, pcm, label, round(row["g_window"], 2), flush=True)
    df = pd.DataFrame(rows)
    ref = df[df.block == "reference"].set_index("pcm").g_window
    df["delta_vs_ref"] = df.g_window - df.pcm.map(ref)
    df.to_csv(Path("results") / f"c7_l4_sensitivity_r{cid}.csv", index=False)


if __name__ == "__main__":
    main(int(sys.argv[1]))
