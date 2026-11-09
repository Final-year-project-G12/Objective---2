# objective3

Objective-3 hand-off material, kept out of Objective 2's `results/` on purpose.

The environment contract here must be regenerated after the Objective-2 rebuild completes: it was written from the pre-shield-fix designs.

The GENERATOR stays in the Objective-2 tree at `src/handoff/build_obj3_contract.py` (run via `python pipeline.py --stage handoff`), because `pipeline.py` imports that package and it also holds `build_recommendation_cards`, which is an Objective-2 deliverable.
