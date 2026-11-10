# objective3 — handoff material

Objective-3 hand-off, kept out of Objective 2's `results/` on purpose.

| file | what |
|---|---|
| `obj3_environment_contract_tamilnadu_v3.json` | **the contract Objective 3 reads.** Built 2026-11-09 from the current Objective 2 results |
| `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` | how to use it, and the three constraints that must not be violated |

**Regenerate** after any change to Objective 2's results:

```bash
python scripts/g25_obj3_contract.py                      # direct
python scripts/tn_run_all.py --only g25_obj3_contract    # via the pipeline (stage 31)
```

The generator is `src/handoff/build_obj3_contract_tamilnadu.py`. It stays in the
Objective-2 tree because it reads Objective-2 results and is a pipeline stage.

**Superseded.** The 2026-10-27 contract and handoff document are archived at
`../archive/superseded_obj3_contract_2026-10-27/`. They describe designs that no
longer exist (50 L tank, radial capsules, n-Hexacosane) and claim PCM loses to a
plain tank — the opposite of the current held-out result. Do not use them.

`build_obj3_contract_v2.py` in `src/handoff/` is **Rajasthan-only** and cannot
produce a Tamil Nadu contract; it is kept for when Rajasthan is run.
