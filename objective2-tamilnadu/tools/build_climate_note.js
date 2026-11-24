/*
 * build_climate_note.js
 * =====================
 * O2_Climate_Parameters_and_Simulators.docx — Q&A.
 * The 8 ORIGINAL questions (climate parameters / equation / pump / timestep /
 * PCM purpose / melting figure / which PCM / safety) PLUS 4 added questions
 * (the two simulators, where values come from, optimum & 100 L, blue->red
 * colour). 12 in total, listed in a contents box up front. Clear, simple,
 * well spaced, a few real ANSYS images. 4-5 pages.
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, ImageRun, AlignmentType,
} = require("docx");

const ROOT = path.join(__dirname, "..");
const FIG = path.join(ROOT, "ansys", "figures");
const CONT = path.join(FIG, "regime_contours");

const INK = "1A1A1A", MUTED = "5A5A5A", RULE = "C8C8C8", HDR = "EFEFEF",
      ACCENT = "1F5C73", QBG = "EAF1F4";
const BODY = 22, SMALL = 18, CAP = 16;

const P = (text, o = {}) => new Paragraph({
  spacing: { after: o.after ?? 130, line: o.line ?? 268 },
  children: [new TextRun({
    text, bold: o.bold, italics: o.italics,
    size: o.size ?? BODY, color: o.color ?? INK, font: "Calibri",
  })],
});
const PR = (parts, o = {}) => new Paragraph({
  spacing: { after: o.after ?? 130, line: 268 },
  children: parts.map((p) => new TextRun({
    text: typeof p === "string" ? p : p.t,
    bold: typeof p === "string" ? false : !!p.b,
    italics: typeof p === "string" ? false : !!p.i,
    size: o.size ?? BODY, color: INK, font: "Calibri",
  })),
});
const B = (text) => new Paragraph({
  bullet: { level: 0 }, spacing: { after: 70, line: 256 },
  children: [new TextRun({ text, size: BODY, color: INK, font: "Calibri" })],
});

function table(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (text, i, head) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    shading: head ? { type: ShadingType.CLEAR, fill: HDR, color: "auto" } : undefined,
    margins: { top: 45, bottom: 45, left: 75, right: 75 },
    children: [new Paragraph({
      spacing: { after: 0, line: 244 },
      children: [new TextRun({
        text: String(text), bold: head, size: SMALL,
        color: head ? INK : MUTED, font: "Calibri",
      })],
    })],
  });
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    borders: {
      top: { style: BorderStyle.SINGLE, size: 2, color: RULE },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: RULE },
      left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 1, color: RULE },
      insideVertical: { style: BorderStyle.NONE },
    },
    rows: [
      new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, i, true)) }),
      ...rows.map((r) => new TableRow({ children: r.map((c, i) => cell(c, i, false)) })),
    ],
  });
}

const QUESTIONS = [
  // 8 original
  "Which climate parameters are used?",
  "Which equation is used for the collector?",
  "When does the pump stop?",
  "Why is an adaptive timestep used?",
  "What is the purpose of the PCM?",
  "Which ANSYS figure proves the PCM melts?",
  "Which PCM melts the most?",
  "What are the safety limits?",
  // 4 added
  "The two simulators — which one decides the design?",
  "Where do the parameter values come from, and how do I change them?",
  "Is the optimal design found in ANSYS — and why is the tank 100 L?",
  "Why does the picture change colour from blue to red?",
  "What does each ANSYS view of the tank actually show?",
  "What happens with fewer capsules (say only 30), and how is the final design chosen?",
  "Why 175 L/day, and does the PCM win in every way?",
];

let QN = 0;
function Q() {
  const text = QUESTIONS[QN];
  QN += 1;
  return new Paragraph({
    spacing: { before: 230, after: 80 },
    shading: { type: ShadingType.CLEAR, fill: QBG, color: "auto" },
    border: { left: { style: BorderStyle.SINGLE, size: 18, color: ACCENT, space: 8 } },
    children: [
      new TextRun({ text: `Q${QN}.  `, bold: true, size: 24, color: ACCENT, font: "Calibri" }),
      new TextRun({ text, bold: true, size: 24, color: INK, font: "Calibri" }),
    ],
  });
}

const img = (file, wPx, ratio) => new Paragraph({
  spacing: { before: 70, after: 40 }, alignment: AlignmentType.CENTER,
  children: [new ImageRun({
    type: "png", data: fs.readFileSync(file),
    transformation: { width: wPx, height: Math.round(wPx / ratio) },
  })],
});
const cap = (text) => new Paragraph({
  spacing: { after: 120, line: 232 }, alignment: AlignmentType.CENTER,
  children: [new TextRun({ text, size: CAP, color: MUTED, font: "Calibri", italics: true })],
});
const CODE = (text) => new Paragraph({
  spacing: { after: 70, before: 30 },
  shading: { type: ShadingType.CLEAR, fill: "F5F5F5", color: "auto" },
  indent: { left: 150 },
  children: [new TextRun({ text, size: SMALL, color: "1F4E5F", font: "Consolas" })],
});

const ch = [];

// ── title ──
ch.push(new Paragraph({
  spacing: { after: 40 },
  children: [new TextRun({
    text: "Climate Parameters & Simulators — Q&A",
    bold: true, size: 38, color: INK, font: "Calibri",
  })],
}));
ch.push(P("Objective 2 · Tamil Nadu · PCM capsule tank — the common questions, answered simply",
  { color: MUTED, size: SMALL, after: 120 }));

// ── contents box: list all questions ──
ch.push(new Paragraph({
  spacing: { before: 40, after: 60 },
  children: [new TextRun({ text: "Questions in this document", bold: true, size: 22, color: ACCENT, font: "Calibri" })],
}));
const contentsRows = QUESTIONS.map((q, i) => new TableRow({
  children: [
    new TableCell({
      width: { size: 700, type: WidthType.DXA },
      margins: { top: 28, bottom: 28, left: 80, right: 40 },
      children: [new Paragraph({ children: [new TextRun({ text: `Q${i + 1}`, bold: true, size: SMALL, color: ACCENT, font: "Calibri" })] })],
    }),
    new TableCell({
      width: { size: 9100, type: WidthType.DXA },
      margins: { top: 28, bottom: 28, left: 40, right: 80 },
      children: [new Paragraph({ children: [new TextRun({
        text: q + (i === 7 ? "    (Q1–Q8 original · Q9–Q15 added)" : ""),
        size: SMALL, color: i < 8 ? INK : "1F5C73", font: "Calibri",
      })] })],
    }),
  ],
}));
ch.push(new Table({
  width: { size: 9800, type: WidthType.DXA },
  columnWidths: [700, 9100],
  borders: {
    top: { style: BorderStyle.SINGLE, size: 2, color: RULE },
    bottom: { style: BorderStyle.SINGLE, size: 2, color: RULE },
    left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
    insideHorizontal: { style: BorderStyle.SINGLE, size: 1, color: "E4E4E4" },
    insideVertical: { style: BorderStyle.NONE },
  },
  rows: contentsRows,
}));
ch.push(P("", { after: 60 }));

// ═════════════════════ ORIGINAL 8 ═════════════════════

// Q1
ch.push(Q());
ch.push(PR([
  "Three: ", { t: "solar irradiance (GHI)", b: true }, ", ",
  { t: "ambient air temperature", b: true }, ", and the ",
  { t: "local time / date", b: true },
  ". GHI is the main driver (heat into the collector), air temperature sets the heat loss, and the "
  + "time/date lines the hot-water demand up with the clock. A fourth input, mains water temperature, is "
  + "one fixed value per regime. Wind and humidity sit in the data file but are not used.",
]));

// Q2
ch.push(Q());
ch.push(PR([
  "The ", { t: "Hottel–Whillier–Bliss equation", b: true },
  " for a flat-plate collector, which balances heat gained from the sun against heat lost to the air:",
]));
ch.push(CODE("Q_useful = A_c × [ F_R(τα) × I_t  −  F_R·U_L × (T_in − T_amb) ]"));
ch.push(P("I_t is the irradiance, T_amb the air temperature, T_in the water entering the collector; the fixed numbers (area 2.0 m², F_R(τα) = 0.75, F_R·U_L = 4.5; the F_R values are legacy typical values, not re-fitted for 2.0 m²) come from the config file."));
ch.push(PR([
  { t: "Is it from a paper? ", b: true },
  "Yes — it is a standard collector equation (classic work by Hottel & Whillier and by Bliss in the "
  + "1950s; textbook form in Duffie & Beckman, Solar Engineering of Thermal Processes). In this project the "
  + "collector model follows the Hottel–Whillier form cited in ",
  { t: "Eldokaishi et al. 2022", b: true },
  " (Applied Thermal Engineering 204:118009), referenced in src/simulation/collector_model.py.",
]));

// Q3
ch.push(Q());
ch.push(PR([
  "Below ", { t: "10 W/m²", b: true },
  " of irradiance. Under that, the sun is too weak to be worth running the pump, so the collector loop "
  + "is treated as off — which is what makes the collector follow the daily sunrise–sunset cycle.",
]));

// Q4
ch.push(Q());
ch.push(PR([
  "To capture the ", { t: "PCM phase change (melting) accurately", b: true },
  ". Melting happens in a narrow temperature band where the physics changes fast, so when a capsule is "
  + "inside that band the timestep is refined (up to 6× finer) to resolve it; elsewhere it runs coarsely "
  + "to stay fast. (Search runs at 150 s, every reported number at 37.5 s.)",
]));

// Q5
ch.push(Q());
ch.push(PR([
  "To ", { t: "store latent heat", b: true },
  ". When the PCM melts it absorbs a large amount of heat at nearly constant temperature, and when it "
  + "solidifies it releases that heat back. This lets the tank hold useful warmth into the evening, after "
  + "the sun is gone — the whole reason for adding a PCM.",
]));

// Q6
ch.push(Q());
ch.push(PR([
  { t: "Figure 3", b: true },
  " — the PCM melt comparison. It shows all four shortlisted PCMs melting on the same mesh under the "
  + "same heat, with the liquid fraction climbing over time. Figures 1 and 2 only show the geometry and the "
  + "heat path; Figure 3 is the one that shows melting.",
]));
try {
  ch.push(img(path.join(FIG, "03_pcm_melt_comparison.png"), 460, 2025 / 840));
  ch.push(cap("Figure 3 — all four PCMs melted under one duty. The only difference between the curves is the material itself, so it isolates the melting behaviour."));
} catch (e) {}

// Q7
ch.push(Q());
ch.push(PR([
  { t: "C25 (n-Pentacosane)", b: true },
  ". It has the lowest melt point (54 °C) and the highest conductivity, so heat reaches it soonest and it "
  + "crosses its melt point first. The order from most to least melted is C25 > C26 > RT57HC > PureTemp 58 "
  + "— exactly what melt point and conductivity predict.",
]));

// Q8
ch.push(Q());
ch.push(PR([
  { t: "72 °C for the water and 62 °C for the PCM", b: true },
  ". These are the bypass points of the safety shield: if the tank water reaches 72 °C or the PCM reaches "
  + "62 °C, circulation stops so nothing overheats. They sit 3 °C below the hard limits (75 °C water, 65 °C "
  + "PCM), as a guard band.",
]));

// ═════════════════════ ADDED 4 ═════════════════════

// Q9
ch.push(Q());
ch.push(PR([
  "Two, with different jobs. The ", { t: "fast tank model (Python)", b: true },
  " covers the whole 100 L tank for a full year in seconds and ", { t: "ranks the designs — it chooses", b: true },
  " the winner. ", { t: "ANSYS Fluent", b: true },
  " covers one capsule in detail and only checks the melting physics. So the tank model decides and ANSYS "
  + "confirms; a different CFD tool would re-confirm the same design, not change it.",
]));

// Q10
ch.push(Q());
ch.push(PR([
  "From files, never typed by hand. Fixed constants (tank 100 L, collector, safety limits) are in ",
  { t: "configs/system_config_shared.yaml", b: true }, "; the ranges the optimiser may vary (capsule size, "
  + "PCM amount, layout; flow is frozen at 0.030 kg/s) are in ", { t: "configs/design_space.yaml", b: true },
  "; PCM properties come from the Objective 1 database; the final chosen numbers are in ",
  { t: "results/c16_funnel_winners.csv", b: true },
  ". To change one, widen the min/max in design_space.yaml and re-run the optimiser, or edit the CSV / "
  + "pass --regime for a one-off ANSYS run.",
]));

// Q11
ch.push(Q());
ch.push(PR([
  { t: "No — the optimum is not found in ANSYS. ", b: true },
  "The fast tank model plus the NSGA-II search pick the best design inside the bounds; ANSYS only confirms "
  + "it melts correctly. The tank is fixed at ", { t: "100 L", b: true },
  " because it is the common plant for all four states (Rajasthan used 50 L), locked as “not optimised”; "
  + "with the 2.0 m² collector that is 50 litres per m², inside the 40–100 L/m² range of Indian Standard "
  + "IS 12976:2023. The daily draw is 175 L/day: at 100 L/day the plain tank already met 99 % of demand, so a PCM "
  + "had nothing to add.",
]));

// Q12
ch.push(Q());
ch.push(PR([
  "The colour is just the ", { t: "value being plotted", b: true },
  ", low = blue to high = red. In the melt picture that value is ", { t: "liquid fraction", b: true },
  " (0 = solid → blue, 1 = molten → red), so the colours move as the PCM melts. The field and its banded "
  + "scale are set in ansys/fluent_live_demo.py (around line 278) and Fluent maps min→blue, max→red "
  + "automatically. What drives the value is the melting model (solidification_melting, line 209) plus the "
  + "melt point, latent heat and conductivity and the hot-water temperature/flow — hotter/faster water, a "
  + "lower melt point or higher conductivity all turn blue to red sooner.",
]));
try {
  ch.push(img(path.join(CONT, "regime0_PureTemp58_liqfrac.png"), 420, 968 / 720));
  ch.push(cap("Liquid-fraction contour: red = molten water, the blue dome = PCM still solid, the green ring = the melt front. The colours ARE the liquid-fraction value."));
} catch (e) {}

// Q13
ch.push(Q());
ch.push(P("There are three things you can open in ANSYS, and each shows a different part of the story:"));
ch.push(table(
  ["View (file → what to display)", "What it shows / means"],
  [
    ["Tank geometry + capsules — system_tank_pcm_panel_setup.cas.h5 → Mesh",
     "The STRUCTURE only: the 100 L tank, the 34 PCM capsules in a staggered layout, and the collector panel, absorber and riser — each a coloured zone. It is the geometry check (the thing modelled is the thing meant). No physics yet, just the shapes."],
    ["Tank temperature / heat path — system_tank_pcm_panel_solved.cas.h5 → Contours → Temperature",
     "WHERE THE HEAT IS: absorber ~139 °C → panel ~125 °C → riser ~61 °C → tank water ~32 °C → PCM ~31.6 °C. It proves heat flows correctly from the hot collector down into the cool tank. It is an energy-only snapshot, so the PCM stays solid — it shows the heat path, not melting."],
    ["A capsule melting live (animated) — python fluent_live_demo.py",
     "The PCM ACTUALLY MELTING: one capsule in hot water, the liquid-fraction contour re-drawing as the solve runs, so the blue solid core shrinks and the melt front moves inward over time. This is the proof the PCM stores heat by melting — and it is the only one of the three that animates."],
  ],
  [3600, 6200]));
ch.push(PR([
  { t: "In short: ", b: true },
  "the first shows the shape, the second shows the heat reaching the tank, and the third shows the PCM "
  + "melting. The first two are static solved snapshots you can zoom and rotate; only the live demo moves.",
]));

// ── numbers for Q14 / Q15 are READ from the Objective-2 outputs at build time (nothing typed by hand) ──
function readCsv(file) {
  const rows = []; let row = [], cur = "", q = false;
  const text = fs.readFileSync(file, "utf8");
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"' && text[i + 1] === '"') { cur += '"'; i++; } else if (c === '"') q = false; else cur += c; }
    else if (c === '"') q = true;
    else if (c === ",") { row.push(cur); cur = ""; }
    else if (c === "\n" || c === "\r") { if (c === "\r" && text[i + 1] === "\n") i++; row.push(cur); cur = ""; if (row.length > 1 || row[0] !== "") rows.push(row); row = []; }
    else cur += c;
  }
  if (cur !== "" || row.length) { row.push(cur); rows.push(row); }
  return rows.slice(1).map((r) => Object.fromEntries(rows[0].map((h, i) => [h, r[i]])));
}
const RES = path.join(ROOT, "results");
const RUN_DIR = fs.readdirSync(RES).filter((d) => d.startsWith("common100L_")).sort()[0];
const ENV = JSON.parse(fs.readFileSync(path.join(RES, RUN_DIR, "o3_environment_contract_tamilnadu.json"), "utf8"));
const CN = readCsv(path.join(ROOT, "ansys", "criteria_common", "SUMMARY_all_criteria.csv"));
const CF = readCsv(path.join(ROOT, "ansys", "criteria_common", "FLUENT_summary_all_criteria.csv"));
const T = ENV.static_design_per_regime.map((d) => d.one_shot_test_2006_2010);
const rg = (a, d = 1) => `${Math.min(...a).toFixed(d)}–${Math.max(...a).toFixed(d)}`;

// Q14
ch.push(Q());
ch.push(P("Seven designs were tried for Regime 0 (PureTemp 58): the optimum, six alternatives that each change something, including your 30-capsule idea. Each runs in the fast tank model, which applies the same selection funnel that chose the optimum (so every design gets a verdict), and in ANSYS Fluent as a one-hour whole-tank discharge."));
ch.push(table(
  ["Design", "Capsules", "Gain (% of optimal)", "Water warms (Fluent, 1 h)", "Why it is not the final design"],
  CN.map((c, i) => [c.criteria, c.N, `${Math.round(Number(c.pct_of_optimal))} %`, `+${Number(CF[i].water_rise_K).toFixed(1)} K`, c.verdict]),
  [2300, 800, 1100, 1300, 4300]));
ch.push(PR([
  { t: "So with only 30 capsules ", b: true },
  `the PCM still works and still beats the plain tank, but it delivers ${Math.round(Number(CN[4].pct_of_optimal))} % of the optimal gain and warms the water ${Number(CF[4].water_rise_K).toFixed(1)} K instead of ${Number(CF[0].water_rise_K).toFixed(1)} K: too little PCM to matter much. `,
  { t: "How the final one is chosen: ", b: true },
  "a design must pass the hard limits (PCM ≤ 65 °C, water ≤ 75 °C), beat the plain tank by more than the noise band, stay within one band of the best gain, and then the one with the fewest overheat hours wins. "
  + "More PCM is not automatically better: designs 1 and 3 tie the optimum on gain and lose only on overheating.",
]));
try {
  ch.push(img(path.join(ROOT, "ansys", "criteria_common", "FLUENT_comparison_all_criteria.png"), 560, 2210 / 650));
  ch.push(cap("ANSYS Fluent, one hour: water temperature, capsule temperature and liquid fraction for all seven designs. More PCM warms the water more; the minimum design runs out of stored heat within about ten minutes."));
} catch (e) {}

// Q15
ch.push(Q());
ch.push(PR([
  "At the first target, ", { t: "100 L/day", b: true },
  ", the plain tank already covered 99 % of the demand, so a PCM had nothing to add (its gain was about −0.6 kWh/yr). A plant scan found the rule: ",
  { t: "a PCM only adds delivered energy when the plain tank leaves demand unmet", b: true },
  " (with the 2.0 m² collector: about +75 kWh/yr at 150 L/day and +154 at 200). ",
  { t: "175 L/day", b: true },
  " of 45 °C water is the 45 °C equivalent of a 100 L/day heater rated at 60 °C, so it is a realistic draw, not a tuned one.",
]));
ch.push(PR([
  { t: "Does the PCM win in every way? No. ", b: true },
  `On the one-shot test (2006–2010) it beats the plain tank in every year of every regime, by ${rg(T.map((t) => t.gain_mean_kWh))} kWh/yr. But it is always worse on overheat-guard hours: `
  + `+${rg(T.map((t) => t.overheat_extra_hours_per_year), 0)} hours a year, because the capsules take the place of water in a fixed 100 L tank. And the margin depends on how noise is counted: `
  + `${rg(T.map((t) => t.gain_over_core_band))}× the core noise band, but only ${rg(T.map((t) => t.gain_over_full_band))}× the full band that also includes mains-temperature and demand changes. `
  + "The sign is solid; the size is less certain.",
]));

ch.push(P(""));
ch.push(P("Further detail: O2_ANSYS_Complete_Guide.docx (click-by-click ANSYS steps and all figures) and the project's docs/ folder (SIMULATOR_AND_CFD.md, CFD_VERIFICATION.md, RESULTS.md).",
  { italics: true, color: MUTED, size: CAP, after: 0 }));

const doc = new Document({
  creator: "Objective 2 — Tamil Nadu",
  title: "Climate Parameters & Simulators — Q&A",
  sections: [{
    properties: { page: { margin: { top: 850, bottom: 750, left: 950, right: 950 } } },
    children: ch,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(ROOT, "docs", "reports", "O2_Climate_Parameters_and_Simulators.docx");
  fs.writeFileSync(out, buf);
  console.log("wrote " + out + "  (" + (buf.length / 1024).toFixed(0) + " KB)");
});
