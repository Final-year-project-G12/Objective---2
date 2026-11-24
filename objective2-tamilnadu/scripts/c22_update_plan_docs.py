"""
scripts/c22_update_plan_docs.py
=================================
Updates the two plan documents in docs/plan/ IN PLACE (idempotent) with Revision 11: the user decisions and execution changes made while
rebuilding Objective 2 (demand 175 L/day, PCMs only from Objective 1, robust three-anchor objective, MATLAB scope, ...). The original text is kept;
a Revision 11 paragraph is inserted after the Revision 10 paragraph and the R1 rule cell is amended. A backup of each original is written once
to docs/plan/_original/.
Usage: python scripts/c22_update_plan_docs.py
"""
import copy
import shutil
from pathlib import Path

import docx

ROOT = Path(__file__).resolve().parent.parent
FILES = [ROOT / "docs/plan/Unified_Objectives_2_3_Rebuild_Plan_Four_States_REVISED_v1.docx", ROOT / "docs/plan/tamilnadu_new.docx"]
MARK = "Revision 11 (23 November 2026"

REV11 = (MARK + ", execution amendments made while rebuilding Objective 2; user decisions marked U): "
         "(1) U - the common daily demand is changed from 100 to 175 L/day of 45 C water; tank 100 L and collector 2.0 m2 are unchanged. Basis: a 100 LPD heater is rated at about 60 C stored water, "
         "which is roughly 175 L/day of 45 C water (171-191 L/day for Tamil Nadu mains of 24-28.5 C). At 100 L/day the plain tank already met 99 % of the demand and PCM could not add energy "
         "(plant scan: paired gain -0.6 kWh/yr at 100 L/day, +75 at 150, +154 at 200, +212 at 300 L/day, 2.0 m2); 100 and 150 L/day and the legacy 2.5 m2 / 300 L/day become sensitivity cases. "
         "(2) U - PCMs are taken only from the Objective 1 shortlist; no PCM is added in Objective 2 (a 45 C screen found the Objective 1 PCMs, melting at 54-58 C, give about zero paired gain on this plant while 44-47 C PCMs gave "
         "+1.6 to +5.8 kWh/yr at 100 L/day; this is kept as a stated limitation and a pointer for an Objective 1 re-run at 45 C). Option B (keep the Objective 1 shortlist) is therefore final. "
         "(3) The Objective 1 files were re-synced (Objective 1 had been re-run on 10 November: shortlist, rankings and cluster labels identical; regime-0 'medoid' is a 24-way tie and the O2 medoids TNP_0006 / TNP_0007 / TNP_0001 are kept). "
         "(4) Flow frozen at 0.030 kg/s; the search box is three variables (inner radius 10-40 mm, PCM fraction 2-40 %, arrangement); the stack anchor is NOT a search variable: every design is simulated at bottom, centre and top and "
         "ranked on the mean paired gain, rejected if the worst-anchor gain is below zero or inside the repeatability band (rule R7). The Taguchi L9 uses the anchor in place of flow. "
         "(5) Multi-fidelity rule pre-registered before any full-fidelity run: cheap = dt 150 s, year 2017; full = dt 37.5 s, years 2017-2018; Spearman >= 0.8 and max difference <= 0.5 kWh in at least 7 of 9 pairs, else the cheap screen is not used for selection. "
         "(6) The search objectives are robust paired gain, overheat-guard hours and PCM volume; the dense-grid check uses 162 points; the repeatability band used by the funnel is the root-sum-square of year, timestep, node-count, PCM-property and stack-anchor effects (core band); mains and demand are scenario shifts that move the expected gain, so they are reported as separate sensitivities and the full band including them is reported alongside (this deviates from plan section 5, which lists demand and mains inside the band; it was decided before the real select and test runs, after a smoke test showed that demand +/-20 % alone shifts the gain by about 99 kWh, and it matches the size of the legacy 26-30 kWh band); "
         "the S0/S1/S2 funnel is frozen in configs/funnel_frozen.json before any select-year run. "
         "(7) Reporting: PCM tanks always show more overheat-guard hours than the plain tank (they hold less water in the same 100 L), so overheat hours are reported as a stated trade-off, not as a benefit; "
         "delivered energy, hold time, serve time and peak water temperature are the benefit categories. "
         "(8) Scope of the MATLAB checkpoint M1 is extended (U): the seven Objective 2 design criteria of the Fluent study (optimal, max, min, not-optimal-but-working, 30 capsules, 10 % and 50 % of optimal) are shown in MATLAB as the tank with its PCM capsules "
         "(water temperature, capsule liquid fraction, heat given to the water, differences between criteria) on a real charging day and on the Fluent-style discharge, driven by the Objective 2 multi-node kernel outputs and using the Objective 2 parameters "
         "(radius, count, fraction, arrangement, anchor, flow, PCM properties, demand, mains). ANSYS Fluent (L8) is re-run for the new optimum and the six alternatives so that ANSYS and MATLAB show the same seven criteria. "
         "This MATLAB view is a visualisation of simulator output, not an independent MATLAB re-implementation of the physics and not CFD or experiment. "
         "(9) Run order: L0-L2 are unchanged by the demand amendment; everything that depends on demand (L3 checks, L4 sensitivity and Taguchi, L5-L9) was re-run at 175 L/day; results obtained at 100 L/day are archived in archive/.")

R1_NEW = ("100 L tank, 2.0 m2 collector, 175 L/day of 45 C water (Revision 11; was 100 L/day). Demand = litres drawn from the tank per day against a 45 C delivery threshold. "
          "Sensitivity only (never for selection): demand 100 and 150 L/day, legacy 2.5 m2 / 300 L/day.")


def set_text(par, text):
    for r in par.runs[1:]:
        r._element.getparent().remove(r._element)
    if par.runs:
        par.runs[0].text = text
    else:
        par.add_run(text)


def update(path: Path):
    bak = path.parent / "_original" / path.name
    if not bak.exists():
        bak.parent.mkdir(exist_ok=True)
        shutil.copy2(path, bak)
    d = docx.Document(str(path))
    pars = d.paragraphs
    existing = [p for p in pars if p.text.startswith(MARK)]
    if existing:
        set_text(existing[0], REV11)
    else:
        anchor = next((p for p in pars if p.text.startswith("Revision 10 (19 November 2026")), None) or             next(p for p in pars if "Revision 9:" in p.text)
        new = copy.deepcopy(anchor._element)
        anchor._element.addnext(new)
        newp = docx.text.paragraph.Paragraph(new, anchor._parent)
        set_text(newp, REV11)
    n = 0
    for t in d.tables:
        for row in t.rows:
            cells = row.cells
            if len(cells) >= 3 and cells[0].text.strip() == "R1" and cells[1].text.strip() == "Plant":
                set_text(cells[2].paragraphs[0], R1_NEW)
                n += 1
    d.save(str(path))
    return n


if __name__ == "__main__":
    for f in FILES:
        print(f.name, "R1 cells updated:", update(f))
