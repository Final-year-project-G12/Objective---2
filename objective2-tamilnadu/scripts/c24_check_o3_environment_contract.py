"""
scripts/c24_check_o3_environment_contract.py
============================================
Independent check of results/common100L_<hash>/o3_environment_contract_tamilnadu.json.

It does NOT reuse the generator's code: it re-reads the source files itself and compares. Exit code 1 if any check fails.
Run it after c23, and again before Objective 3 loads the contract.

Usage:  python scripts/c24_check_o3_environment_contract.py
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
from src.weather import roles                                               # noqa: E402

RUN = roles.TEST_LOCK_PATH.parent
ENV = RUN / "o3_environment_contract_tamilnadu.json"
IMM = RUN / "o3_contract_tamilnadu.json"
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"   ({detail})" if detail and not ok else ""))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    c = json.loads(ENV.read_text(encoding="utf-8"))
    sysc = yaml.safe_load(open(BASE / "configs" / "system_config_shared.yaml", encoding="utf-8"))
    statec = yaml.safe_load(open(BASE / "configs" / "states" / "tamilnadu.yaml", encoding="utf-8"))
    win = pd.read_csv(BASE / "results" / "c16_funnel_winners.csv").set_index("regime")
    summ = pd.read_csv(RUN / "c17_summary.csv").set_index("regime")
    lock = json.loads(roles.TEST_LOCK_PATH.read_text(encoding="utf-8"))

    check("schema is the common-plant environment schema", c["schema"] == "o3_environment_contract_common100L_v1")
    check("this file matches its recorded SHA-256", sha(ENV) == (RUN / "o3_environment_contract_tamilnadu.sha256").read_text().strip())

    # immutable record is unchanged and is the one this contract points at
    check("immutable record unchanged since sealing", sha(IMM) == (RUN / "o3_contract_tamilnadu.sha256").read_text().strip())
    check("contract points at the sealed immutable record", c["immutable_result_record"]["sha256"] == sha(IMM))
    check("lock run_id == contract run_id", lock["run_id"] == c["one_shot_test"]["run_id"] == c["immutable_result_record"]["run_id"])
    check("funnel hash agrees (lock, config file, contract)",
          lock["selection_fingerprint"] == (BASE / "configs" / "funnel_frozen.sha256").read_text().strip() == c["immutable_result_record"]["funnel_sha256"])
    check("hardware hash still equals the hash the test ran under", roles.hardware_hash() == c["immutable_result_record"]["hardware_hash"],
          "a config was edited after the lock")

    # plant
    p = c["plant"]
    check("plant: 100 L tank, 2.0 m2 collector, 175 L/day, 45 C",
          (p["tank_volume_L"], p["collector_area_m2"], p["demand_daily_total_L"], p["delivery_target_temp_C"]) == (100.0, 2.0, 175.0, 45.0))
    check("plant equals configs", p["collector_area_m2"] == sysc["collector"]["area_m2"] and p["tank_volume_L"] == sysc["tank"]["volume_L"]
          and p["demand_daily_total_L"] == statec["demand_profile"]["daily_total_L"])
    d = pd.read_csv(BASE / statec["demand_profile"]["file"])
    check("demand CSV sums to the contract's daily total", abs(d.draw_volume_L.sum() - c["demand"]["daily_total_L"]) < 1e-6)

    # designs
    for k in range(3):
        g = c["static_design_per_regime"][k]
        w, s = win.loc[k], summ.loc[k]
        check(f"regime {k}: PCM, capsules, radius, fraction equal c16 winners",
              g["selected_pcm"] == w.pcm and g["n_capsules"] == int(w.N) and abs(g["capsule_inner_radius_m"] - w.R_in_m) < 1e-12
              and abs(g["pcm_volume_fraction"] - w.fraction) < 1e-12)
        check(f"regime {k}: test gain equals c17 summary",
              abs(g["one_shot_test_2006_2010"]["gain_mean_kWh"] - s.test_gain_mean_kWh) < 1e-9
              and abs(g["one_shot_test_2006_2010"]["gain_worst_anchor_mean_kWh"] - s.test_gain_worst_anchor_mean_kWh) < 1e-9)
        check(f"regime {k}: selected PCM is in Objective 1's shortlist for that regime", g["selected_pcm"] in g["o1_pcm_shortlist"])
        check(f"regime {k}: flow envelope is the pump range", g["flow_envelope_kg_s"] == [sysc["pump"]["flow_min_kg_s"], sysc["pump"]["flow_max_kg_s"]])
        check(f"regime {k}: PCM keeps the 5 of 5 test-year win", g["one_shot_test_2006_2010"]["years_pcm_better"] == "5 of 5")

    # weather roles
    seq = c["weather_sequences"]["mapping_for_O3"]
    allowed = set(seq["training"]["years"]) | set(seq["validation"]["years"]) | set(seq["final_report"]["years"])
    check("training/validation/report years are never test, legacy or project-exposed",
          all(roles.YEAR_ROLES[y] in ("explore", "select", "report") and y < 2024 for y in allowed))
    check("forbidden list covers every test and legacy year",
          set(range(2006, 2016)) <= set(seq["forbidden"]["years"]))
    check("roles in the contract equal src/weather/roles.py",
          {int(y): r for r, ys in c["weather_sequences"]["roles"].items() for y in ys} == dict(roles.YEAR_ROLES))

    # completeness and contamination
    required = ["action_space", "reset_scenarios", "dynamic_state_schema", "acceptance_test_before_drl_training", "reward_function",
                "safety_shield", "global_limits", "design_space_caveats", "verification_status", "deferred_future_work", "objective_boundary",
                "provenance", "one_shot_test", "weather_sequences", "flow_policy", "demand", "plant", "static_design_per_regime"]
    check("every section an Objective 3 environment needs is present", all(k in c for k in required),
          str([k for k in required if k not in c]))
    text = json.dumps(c)
    check("no legacy capsule counts as a design (104, 98, 105)",
          all(g["n_capsules"] == 140 for g in c["static_design_per_regime"]) and '"n_capsules": 104' not in text)
    check("no legacy collector area as the plant value", '"collector_area_m2": 2.5' not in text)
    check("tests recorded as passing in the contract",
          c["verification_status"]["simulator_verification"]["test_suite"]["returncode"] == 0,
          str(c["verification_status"]["simulator_verification"]["test_suite"]))

    # provenance: nothing a contract depends on has changed since the build
    stale = [f for f, h in c["provenance"]["sha256_of_every_file_read"].items() if sha(BASE / f) != h]
    check("every file the contract was built from is unchanged since the build", not stale, str(stale))

    n_fail = results.count(False)
    print(f"\n{len(results) - n_fail} passed, {n_fail} failed")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
