"""
scripts/r24_check_o3_contract.py - check the Objective 3 contract for Rajasthan against its sources (nothing is rebuilt).
Run before Objective 3 loads it:  PYTHONPATH=. python scripts/r24_check_o3_contract.py
Fails (exit 1) when any check disagrees. Also checks that objective3/ holds identical copies of the results/ file.
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.handoff.build_obj3_contract_common100L import OUT, verify_against_sources  # noqa: E402
from src.weather import roles  # noqa: E402

RES = ROOT / "results"
fails, n = [], 0


def check(name, ok):
    global n
    n += 1
    if not ok:
        fails.append(name)
    print(("ok   " if ok else "FAIL ") + name)


c = json.loads(OUT.read_text(encoding="utf-8"))
check("contract matches its configs and selection files (build-time verification)", verify_against_sources(c) > 0)
check("plant: 100 L, 2.0 m2, 175 L/day, 45 C", (c["fixed_system"]["tank_volume_L"], c["fixed_system"]["collector_area_m2"],
      c["fixed_system"]["demand_daily_total_L"], c["global_limits"]["delivery_target_temp_C"]) == (100.0, 2.0, 175.0, 45.0))
check("flow fixed at 0.030 kg/s", abs(c["global_limits"]["flow_fixed_kg_s"] - 0.030) < 1e-12)
lock = json.loads(roles.test_lock_path().read_text())
check("test lock present and plant hash equals the contract's", lock["plant_hash"] == c["o2_confirmatory_test"]["plant_hash"])
check("test years are 2006-2010", sorted(c["o2_confirmatory_test"]["years"]) == [2006, 2007, 2008, 2009, 2010])
test = pd.read_csv(RES / "o2_test_2006_2010.csv")
rep = pd.read_csv(RES / "o2_report_2022_2025.csv")
for d in c["static_design_per_regime"]:
    k = d["regime_id"]
    ref = d["best_pcm_design_reference"]
    t = test[(test.regime == k) & (test.role == "chosen")]
    check(f"regime {k}: installed design is PCM and not water-only", d["installed_design"]["type"] == "pcm" and d["recommendation"] == "pcm")
    check(f"regime {k}: test g_window in contract equals the CSV mean",
          abs(ref["test_2006_2010"]["g_window_mean_kWh_yr"] - round(float(t.g_window.mean()), 4)) < 1e-9)
    check(f"regime {k}: test and report gains positive at every anchor and year",
          bool((t.groupby(["year", "anchor"]).g_window.mean() > 0).all()
               and (rep[(rep.regime == k) & (rep.role == "chosen")].groupby(["year", "anchor"]).g_window.mean() > 0).all()))
    check(f"regime {k}: worst-anchor test gain above the band",
          ref["test_2006_2010"]["g_window_worst_anchor_kWh_yr"] > d["repeatability_band"]["g_window"])
    check(f"regime {k}: PCM is in the O1 shortlist", ref["pcm"] in d["o1_pcm_shortlist"])
    check(f"regime {k}: no hard-limit hours", float(t.hours_over_limit.max()) == 0.0)
for f in ("obj3_environment_contract_rajasthan_common100L.json",):
    a, b = RES / f, ROOT / "objective3" / f
    check("objective3/ copy identical to results/ file", b.exists() and hashlib.sha256(a.read_bytes()).hexdigest() == hashlib.sha256(b.read_bytes()).hexdigest())
    sh = ROOT / "objective3" / (f + ".sha256")
    check("sha256 file matches", sh.exists() and sh.read_text().split()[0] == hashlib.sha256(a.read_bytes()).hexdigest())
print(f"\n{n - len(fails)}/{n} checks pass")
sys.exit(1 if fails else 0)
