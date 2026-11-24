# objective3 — handoff material

Objective-3 hand-off for the **common-plant** Tamil Nadu run (100 L / 2.0 m² / 175 L/day). Rebuilt 2026-11-24.

| file | what |
|---|---|
| `o3_environment_contract_tamilnadu.json` | **the contract Objective 3 reads**: plant, limits, designs, action space, state schema, reward terms, acceptance tests, weather roles, caveats |
| `o3_contract_tamilnadu.json` | the **immutable result record** (sealed under the one-shot lock; the environment contract points at it by hash) |
| `*.sha256` | their hashes |
| `OBJECTIVE3_INPUTS_AND_NEXT_STEPS.md` | how to use it, the constraints, what the design is not |

The authoritative copies are in `../results/common100L_5e66ebc47a07/`. Check before loading:

```bash
python scripts/c24_check_o3_environment_contract.py
```

Rebuild only if Objective 2's inputs change (the one-shot test lock stays spent):

```bash
python scripts/c23_build_o3_environment_contract.py
```

**Superseded, archived, do not use:**
- `../archive/superseded_obj3_contract_2026-11-09/`: legacy plant (2.5 m², 300 L/day, 98–105 capsules, 2011–15 test).
- `../archive/superseded_obj3_contract_2026-10-27/`: older still (50 L tank, C26/C25, radial capsules).

`scripts/g25_obj3_contract.py` and `src/handoff/build_obj3_contract_tamilnadu.py` are **disabled** (they rebuild the legacy contract).
`src/handoff/build_obj3_contract_v2.py` is Rajasthan-only.
