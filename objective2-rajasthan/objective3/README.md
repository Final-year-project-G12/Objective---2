# objective3 - handoff material (Rajasthan, common plant)

Objective 3 hand-off for the common-plant Rajasthan run (100 L tank, 2.0 m2 collector, declared 175 L/day). Built 2026-11-26 after the one-shot test and the report-only years.

| file | what |
|---|---|
| `obj3_environment_contract_rajasthan_common100L.json` | the contract Objective 3 reads: plant, limits, the three PCM designs and their test results, action space, state schema, reward terms, acceptance tests, weather roles, caveats |
| `obj3_environment_contract_rajasthan_common100L.json.sha256` | its hash |
| `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` | how to use it, the constraints, what the design is not |

The authoritative file is `../results/obj3_environment_contract_rajasthan_common100L.json`; the copy here is for convenience. Check before loading:

```bash
PYTHONPATH=. python scripts/r24_check_o3_contract.py      # 25 checks, exits 1 if anything disagrees with the sources
```

Rebuild (only if Objective 2 inputs change; the one-shot test lock stays spent):

```bash
python pipeline.py --state rajasthan --stage handoff
python scripts/r23_publish_o3_contract.py                 # copies into objective3/ and writes the sha256
```

**Superseded, do not use:** `../results_legacy_50L_v3/obj3_environment_contract_rajasthan*.json` (50 L tank, 1.5 m2, 300 L/day, 2011-2015 test). The Objective 3 repository for Rajasthan, which lives outside this folder, still points at that legacy contract and has not been changed.
Unlike the Tamil Nadu folder there is no separate sealed "result record" file: the lock `../results/locks/o2_test_eb67320ff3cb.lock` and the selection fingerprints inside the contract play that role.
