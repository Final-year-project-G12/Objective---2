"""
scripts/c17_l9_test_and_contract.py   (level L9, steps O2-14, O2-15, O2-16, gate G4)
=====================================================================================
ONE-SHOT confirmatory evaluation of the funnel winners (configs/funnel_frozen.json, results/c16_funnel_winners.csv) on the 2006-2010 years, run exactly
once under the hash-keyed lock (src/weather/roles.acquire_test_lock). A second run fails closed. Then the REPORT-ONLY years 2022-2025 (no lock, no
selection effect), then the immutable O3 contract per regime with hashes.
Fidelity: dt 37.5 s, three anchors, paired against the same-flow water-only tank run exactly at the same dt.
Writes results/common100L_<hash>/{held_out_test.lock, c17_test_by_year.csv, c17_report_only_by_year.csv, c17_summary.csv, o3_contract_tamilnadu.json}.
Usage: python scripts/c17_l9_test_and_contract.py
"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.optimize.robust_eval import robust_row                       # noqa: E402
from src.weather import roles                                         # noqa: E402
from src.weather.inventory import CURRENT_MEDOIDS                     # noqa: E402
from config import STATE                                              # noqa: E402

DT = 37.5


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    win = pd.read_csv("results/c16_funnel_winners.csv")
    funnel_sig = Path("configs/funnel_frozen.sha256").read_text()
    out_dir = roles.TEST_LOCK_PATH.parent
    run_id = "test_" + time.strftime("%Y%m%d_%H%M%S")
    roles.acquire_test_lock(run_id, funnel_sig)                        # fails closed if already spent
    print("lock acquired", roles.TEST_LOCK_PATH, flush=True)
    test_rows, rep_rows = [], []
    for _, w in win.iterrows():
        cid = int(w.regime)
        if w.recommendation != "PCM":
            continue
        for y in roles.years_for("test"):
            r = robust_row(cid, w.pcm, float(w.R_in_m), float(w.fraction_req), w.arrangement, [y], dt_s=DT, purpose="test")
            r.update({"year": y, "role": "test", "run_id": run_id})
            test_rows.append(r)
            print("test", cid, y, round(r["g_window_mean"], 2), flush=True)
        for y in roles.years_for("report"):
            r = robust_row(cid, w.pcm, float(w.R_in_m), float(w.fraction_req), w.arrangement, [y], dt_s=DT, purpose="report")
            r.update({"year": y, "role": "report_only" + ("_project_exposed" if y >= 2024 else ""), "run_id": run_id})
            rep_rows.append(r)
            print("report", cid, y, round(r["g_window_mean"], 2), flush=True)
    t, rp = pd.DataFrame(test_rows), pd.DataFrame(rep_rows)
    t.to_csv(out_dir / "c17_test_by_year.csv", index=False)
    rp.to_csv(out_dir / "c17_report_only_by_year.csv", index=False)
    summ = []
    for cid, g in t.groupby("regime"):
        bw = float(win.set_index("regime").loc[cid, "band_kWh"])
        bfull = float(win.set_index("regime").loc[cid, "band_full_kWh"])
        gr = rp[rp.regime == cid]
        summ.append({"regime": cid, "pcm": g.pcm.iloc[0], "test_years": len(g), "test_gain_mean_kWh": g.g_window_mean.mean(), "test_gain_worst_anchor_mean_kWh": g.g_window_worst.mean(),
                     "test_gain_min_year_kWh": g.g_window_mean.min(), "years_pcm_better": int((g.g_window_mean > 0).sum()), "band_kWh": bw, "band_full_kWh": bfull, "gain_over_full_band": g.g_window_mean.mean() / bfull if bfull > 0 else np.nan,
                     "gain_over_band": g.g_window_mean.mean() / bw if bw > 0 else np.nan, "pcm_beats_plain_beyond_band": bool(g.g_window_worst.mean() > bw),
                     "test_overheat_extra_h": g.d_overheat_mean.mean(), "test_t_pcm_max_C": g.t_pcm_max_worst.max(), "hours_over_limit": g.hours_over_limit.max(),
                     "select_gain_kWh": float(win.set_index("regime").loc[cid, "select_g_window_mean"]),
                     "report_only_gain_mean_kWh": gr.g_window_mean.mean() if len(gr) else np.nan})
    pd.DataFrame(summ).to_csv(out_dir / "c17_summary.csv", index=False)
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=20).stdout.strip() or "no-git-commit"
    except Exception:                                                  # noqa: BLE001
        commit = "no-git-commit"
    contract = {"schema": "o3_contract_common100L_v1", "state": STATE, "run_id": run_id, "plant": {"tank_volume_L": 100, "collector_area_m2": 2.0, "demand_L_day": 175, "delivery_C": 45},
                "hardware_hash": roles.hardware_hash(), "kernel_commit": commit, "funnel_sha256": funnel_sig,
                "config_sha256": {f: sha(f) for f in roles._HARDWARE_FILES}, "legacy_contract_used": False,
                "weather_sha256": {f"cluster{c}_{p}_{y}": sha(roles.point_year_path(STATE, c, p, y)) for c, p in CURRENT_MEDOIDS.items() for y in list(range(2006, 2011)) + list(range(2016, 2026))},
                "regimes": []}
    for s in summ:
        w = win[win.regime == s["regime"]].iloc[0]
        contract["regimes"].append({"regime_id": int(s["regime"]), "medoid": CURRENT_MEDOIDS[int(s["regime"])], "pcm": w.pcm, "inner_radius_m": float(w.R_in_m), "n_capsules": int(w.N),
                                    "pcm_volume_fraction": float(w.fraction), "arrangement": w.arrangement, "flow_kg_s": 0.030, "stack_anchor": "robust(bottom,centre,top)",
                                    "band_kWh": float(w.band_kWh), "test": s})
    for _, w in win.iterrows():
        if w.recommendation != "PCM":
            contract["regimes"].append({"regime_id": int(w.regime), "recommendation": "WATER-ONLY"})
    (out_dir / "o3_contract_tamilnadu.json").write_text(json.dumps(contract, indent=2, default=float), encoding="utf-8")
    contract_sha = sha(out_dir / "o3_contract_tamilnadu.json")
    (out_dir / "o3_contract_tamilnadu.sha256").write_text(contract_sha, encoding="utf-8")
    print(pd.DataFrame(summ).to_string())
    print("contract sha", contract_sha[:16])


if __name__ == "__main__":
    main()
