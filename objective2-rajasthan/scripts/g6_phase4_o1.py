"""
scripts/g6_phase4_o1.py
==========================
G6 (O2, 2026-10-26) - re-run the Phase 4 verification battery on the repaired simulator
(G1 local-time demand, G2 repairs, dt = 150 s) with Objective 1's MCDM top-3 PCMs as the shortlist
(decision D2). Writes BESIDE the legacy report, never over it:

    results/phase4_verification_o1_pcms.txt

The retired retargeted shortlist (RT44HC, OM49, ... ) is not used; it is reported only as the
`pcm_shortlist_retargeted` comparison field of io_utils.get_regime().
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.verify.gates import run_all_gates

if __name__ == "__main__":
    out = Path("results/phase4_verification_o1_pcms.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    run_all_gates("rajasthan", report_path=out, include_stale_winners=False, o1_roster=True)
