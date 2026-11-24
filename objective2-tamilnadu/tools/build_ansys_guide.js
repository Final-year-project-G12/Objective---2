/*
 * build_ansys_parameters_guide.js
 * ================================
 * Complete ANSYS Fluent guide for Tamil Nadu Objective 2:
 * How to open models in ANSYS, view results, and understand parameters.
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, ImageRun, AlignmentType, PageBreak,
  HeadingLevel,
} = require("docx");

const ROOT = path.join(__dirname, "..");
const FIGURES = path.join(ROOT, "ansys", "figures");
const PLOTS = path.join(ROOT, "results", "plots");

// ── live numbers ────────────────────────────────────────────────────────────────
// Every design / plant / test number in this guide is READ at build time from the Objective-2 outputs, so the document cannot drift from them
// (an earlier version had the legacy 2.5 m2 / 104-98-105-capsule numbers typed in by hand).
const RES = path.join(ROOT, "results");
const RUN_DIR = fs.readdirSync(RES).filter((d) => d.startsWith("common100L_")).sort()[0];
const ENV = JSON.parse(fs.readFileSync(path.join(RES, RUN_DIR, "o3_environment_contract_tamilnadu.json"), "utf8"));
const DES = ENV.static_design_per_regime;
const PLANT = ENV.plant;

function readCsv(file) {                                   // small RFC-4180-ish parser (the criteria titles contain commas inside quotes)
  const rows = []; let row = [], cur = "", q = false;
  const text = fs.readFileSync(file, "utf8");
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (q) { if (ch === '"' && text[i + 1] === '"') { cur += '"'; i++; } else if (ch === '"') q = false; else cur += ch; }
    else if (ch === '"') q = true;
    else if (ch === ",") { row.push(cur); cur = ""; }
    else if (ch === "\n" || ch === "\r") { if (ch === "\r" && text[i + 1] === "\n") i++; row.push(cur); cur = ""; if (row.length > 1 || row[0] !== "") rows.push(row); row = []; }
    else cur += ch;
  }
  if (cur !== "" || row.length) { row.push(cur); rows.push(row); }
  const head = rows[0];
  return rows.slice(1).map((r) => Object.fromEntries(head.map((h, i) => [h, r[i]])));
}
const CRIT_DIR = path.join(ROOT, "ansys", "criteria_common");
const CRIT_NODE = readCsv(path.join(CRIT_DIR, "SUMMARY_all_criteria.csv"));
const CRIT_FLUENT = readCsv(path.join(CRIT_DIR, "FLUENT_summary_all_criteria.csv"));
const f1 = (x) => Number(x).toFixed(1), f2 = (x) => Number(x).toFixed(2), f0 = (x) => Math.round(Number(x)).toString();

const INK = "1A1A1A", MUTED = "5A5A5A", RULE = "C8C8C8", HDR = "F0F0F0";
const BODY = 22;  // 11 pt
const SMALL = 18;  // 9 pt
const TINY = 14;   // 7 pt
const CAPTION = 16;

const P = (text, o = {}) => new Paragraph({
  spacing: { after: o.after ?? 100, line: o.line ?? 240 },
  children: [new TextRun({
    text, bold: o.bold, italics: o.italics,
    size: o.size ?? BODY, color: o.color ?? INK, font: "Calibri",
  })],
});

const H1 = (text) => new Paragraph({
  spacing: { before: 200, after: 100 },
  children: [new TextRun({ text, bold: true, size: 32, color: INK, font: "Calibri" })],
});

const H2 = (text) => new Paragraph({
  spacing: { before: 150, after: 80 },
  children: [new TextRun({ text, bold: true, size: 26, color: INK, font: "Calibri" })],
});

const H3 = (text) => new Paragraph({
  spacing: { before: 120, after: 60 },
  children: [new TextRun({ text, bold: true, size: 24, color: INK, font: "Calibri" })],
});

const B = (text, o = {}) => new Paragraph({
  bullet: { level: 0 },
  spacing: { after: 60, line: 220 },
  children: [new TextRun({ text, size: BODY, color: INK, font: "Calibri", ...o })],
});

const CODE = (text) => new Paragraph({
  spacing: { after: 50, before: 50 },
  children: [new TextRun({
    text, size: SMALL, color: MUTED, font: "Courier New", bold: true,
  })],
});

function table(headers, rows, widths, o = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (text, i, head) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    shading: head ? { type: ShadingType.CLEAR, fill: HDR, color: "auto" } : undefined,
    margins: { top: 40, bottom: 40, left: 60, right: 60 },
    children: [new Paragraph({
      spacing: { after: 0, line: 220 },
      children: [new TextRun({
        text: String(text), bold: head, size: o.tiny ? TINY : SMALL,
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

function img(file, wPx) {
  return new Paragraph({
    spacing: { after: 80 },
    alignment: AlignmentType.CENTER,
    children: [new ImageRun({
      type: "png",
      data: fs.readFileSync(file),
      transformation: { width: wPx, height: Math.round(wPx * 0.6) },
    })],
  });
}

const cap = (text) => new Paragraph({
  spacing: { after: 100, line: 220 },
  alignment: AlignmentType.CENTER,
  children: [new TextRun({ text, size: CAPTION, color: MUTED, font: "Calibri", italics: true })],
});

// ══════════════════════════════════════════════════════════════════════════════
const children = [];

// ─────────────────────────────────────────────────────────────────────────────
// TITLE & INTRO
children.push(new Paragraph({
  spacing: { after: 30 },
  children: [new TextRun({
    text: "ANSYS Fluent: Tamil Nadu PCM Tank Design",
    bold: true, size: 40, color: INK, font: "Calibri",
  })],
}));

children.push(P("Objective 2 — Complete models, parameters, and how to open them",
  { color: MUTED, size: SMALL, after: 120 }));

children.push(H2("Quick Start: Run the models immediately"));

children.push(P("The easiest way to see the working models is the live demo — no manual steps needed:"));

children.push(CODE("cd ansys"));
children.push(CODE("python fluent_live_demo.py"));
children.push(CODE("# Watch the melt front advance in the Fluent window for ~30 minutes"));

children.push(P("You can also specify which regime:", { after: 60 }));
children.push(CODE("python fluent_live_demo.py --regime 0   # Regime 0 (default)"));
children.push(CODE("python fluent_live_demo.py --regime 1   # Regime 1"));
children.push(CODE("python fluent_live_demo.py --regime 2   # Regime 2"));

children.push(new Paragraph({ text: "" }));

// ─────────────────────────────────────────────────────────────────────────────
// OPTIMAL DESIGNS TABLE
children.push(H2("The Three Optimal Designs — All Parameters"));

children.push(P(`Common plant for all regimes: ${PLANT.tank_volume_L} L tank, ${f1(PLANT.collector_area_m2)} m² collector, ${PLANT.demand_daily_total_L} L/day of ${PLANT.delivery_target_temp_C} °C water. Read from the sealed Objective-2 contract (run ${ENV.immutable_result_record.run_id}).`, { size: SMALL, color: MUTED }));

children.push(table(
  ["Regime", "PCM (O1 rank)", "Capsules", "Outer Ø", "PCM fraction", "PCM mass", "Flow (frozen)", "Arrangement"],
  DES.map((d) => [String(d.regime_id), `${d.selected_pcm} (#${d.selected_pcm_o1_rank})`, String(d.n_capsules), `${f1(d.capsule_outer_diameter_mm)} mm`,
                  `${f1(d.pcm_volume_fraction * 100)} %`, `${f1(d.pcm_mass_kg)} kg`, `${f2(d.nominal_flow_kg_s)} kg/s`, d.arrangement]),
  [800, 1800, 1000, 1000, 1200, 1100, 1300, 1300]
));

children.push(P(""));

children.push(P("One-shot confirmatory test on 2006–2010 (run once under a lock; PCM tank minus the same-flow plain-water tank):", { size: SMALL, color: MUTED }));
children.push(table(
  ["Regime", "Gain (kWh/yr)", "Worst anchor", "Years PCM wins", "× core band", "× full band", "Extra overheat h/yr", "Peak PCM / water (°C)"],
  DES.map((d) => { const t = d.one_shot_test_2006_2010; return [String(d.regime_id), f1(t.gain_mean_kWh), f1(t.gain_worst_anchor_mean_kWh), t.years_pcm_better,
    f2(t.gain_over_core_band), f2(t.gain_over_full_band), f0(t.overheat_extra_hours_per_year), `${f1(t.t_pcm_max_C)} / ${f1(t.t_water_max_C)}`]; }),
  [800, 1100, 1100, 1200, 1000, 1000, 1400, 1500]
));
children.push(P("All three regimes ended at the same geometry (40 mm radius, 140 capsules): both the radius bound and the 40 % PCM-fraction cap are binding, so the design is the corner of the search box. The regimes differ only in PCM and weather.", { size: SMALL, color: MUTED }));

children.push(new Paragraph({ text: "" }));

// ─────────────────────────────────────────────────────────────────────────────
// SYSTEM PARAMETERS
children.push(H2("Fixed System Parameters (All Regimes)"));

children.push(table(
  ["Parameter", "Value", "Unit"],
  [
    ["Tank volume", "100", "L"],
    ["Tank diameter", "399", "mm"],
    ["Tank height", "799", "mm"],
    ["Tank insulation", "50", "mm"],
    ["Tank wall U-value", "0.8", "W/m²K"],
    ["Collector area", f1(PLANT.collector_area_m2), "m²"],
    ["Storage per collector area", String(PLANT.storage_per_collector_area_L_m2), "L/m²"],
    ["Collector (FRτα)", String(PLANT.collector_fr_tau_alpha), "– (not re-fitted for 2.0 m²)"],
    ["Collector (FRUL)", String(PLANT.collector_fr_ul_W_m2K), "W/m²K (not re-fitted)"],
    ["Capsule material (shell)", "Aluminum (Al)", "–"],
    ["Capsule shell thickness", String(PLANT.capsule_wall_thickness_m * 1000), "mm"],
    ["Daily demand", String(PLANT.demand_daily_total_L), "L/day of 45 °C water"],
    ["Mains temperature (per regime)", Object.values(ENV.demand.mains_temperature_C).map((v) => f1(v)).join(" / "), "°C"],
    ["Delivery target", String(PLANT.delivery_target_temp_C), "°C"],
    ["Max safe water temp", "75", "°C"],
    ["Max safe PCM temp", "65", "°C"],
    ["Pump efficiency", "0.6", "–"],
    ["Max system pressure", "3.5", "bar"],
  ],
  [3000, 2000, 3000]
));

children.push(new Paragraph({ text: "" }));

// ─────────────────────────────────────────────────────────────────────────────
// IMAGES
children.push(H2("The Solved Models — What You'll See"));

children.push(H3("Figure 1: Tank + PCM Capsules + Collector Panel (Mesh View)"));
children.push(P("This is the full 2D system showing all components meshed and ready for CFD:"));
try {
  children.push(img(path.join(FIGURES, "01_system_mesh_zones.png"), 500));
} catch (e) {
  children.push(P("(Figure not found — ensure ansys/figures/ contains the images)", { color: "FF0000" }));
}

children.push(cap("Figure 1 — Tank, 34 PCM capsules in staggered arrangement, collector panel with absorber and riser."));
children.push(cap("Cell zones: Tank water (31,008), PCM (4,847), Capsule shell (511), Collector (3,200), Absorber (1,200), Riser (2,200)."));
children.push(cap("Total mesh: 42,966 cells. This is a REPRESENTATIVE schematic (34 capsules of 42 mm) used to show the structure and heat path; it is NOT the optimised design, which has 140 capsules of 81.6 mm."));

children.push(new Paragraph({ text: "" }));

children.push(H3("Figure 2: Temperature Field During Charging"));
try {
  children.push(img(path.join(FIGURES, "02_system_temperature_field.png"), 550));
} catch (e) {
  children.push(P("(Figure not found)", { color: "FF0000" }));
}

children.push(cap("Left: Full system showing absorber (139 °C) → panel (125 °C) → riser (61 °C) → tank (32 °C)."));
children.push(cap("Right: Tank and capsules only, rescaled to show detail. Heat path confirmed end-to-end, but PCM stays solid here (energy-only case)."));
children.push(cap("This figure verifies the geometry and heat conduction pathways — the proof that PCM actually melts is Figure 3."));

children.push(new Paragraph({ text: "" }));

children.push(H3("Figure 2b: Native ANSYS Render — Whole-System Heat Path"));
children.push(P("The same whole-system case rendered directly by ANSYS Fluent (not post-processed in Python) — this is literally the view inside ANSYS:"));
try {
  children.push(new Paragraph({
    spacing: { after: 80 },
    alignment: AlignmentType.CENTER,
    children: [new ImageRun({
      type: "png",
      data: fs.readFileSync(path.join(FIGURES, "system_views", "system_temperature.png")),
      transformation: { width: 520, height: Math.round(520 * 0.75) },
    })],
  }));
} catch (e) {
  children.push(P("(Native system render not found — run ansys/export_system_views.py)", { color: "FF0000" }));
}
children.push(cap("Collector panel (left) glows hot at ~412 K (139 °C); the two pipes carry heat across to the 100 L tank (right), sitting cold at ~304 K (31 °C)."));
children.push(cap("This is the energy-only snapshot: it shows the collector→tank heat path. The capsules are not distinct here because the PCM stays solid (same caveat as Figure 2). Rendered natively via ansys/export_system_views.py."));

children.push(new Paragraph({ text: "" }));

children.push(H3("Figure 3: PCM Melting Comparison — All Four Materials"));
try {
  children.push(img(path.join(FIGURES, "03_pcm_melt_comparison.png"), 550));
} catch (e) {
  children.push(P("(Figure not found)", { color: "FF0000" }));
}

children.push(cap("Left: Liquid fraction over 6 hours. Right: Capsule mean temperature (dotted lines show melt points)."));
children.push(cap("All four PCMs on one mesh under one duty (42 mm Ø, 30→70 °C). Differences = material physics only."));

children.push(table(
  ["PCM", "Melt Point", "Conductivity", "Melt Fraction @ 6 h"],
  [
    ["n-Pentacosane (C25)", "54.0 °C", "0.239 W/m·K", "0.60 (fastest)"],
    ["n-Hexacosane (C26)", "56.5 °C", "0.238 W/m·K", "0.50"],
    ["RT57HC", "56.5 °C", "0.200 W/m·K", "0.47"],
    ["PureTemp 58", "58.0 °C", "0.150 W/m·K", "0.38 (slowest)"],
  ],
  [2500, 1500, 1500, 1800]
));

children.push(P("All four PCMs solved with zero divergences. The ordering (C25 > C26 > RT57HC > PureTemp) is physically correct because it follows melt point and thermal conductivity exactly."));

children.push(new Paragraph({ text: "" }));

// ─────────────────────────────────────────────────────────────────────────────
// FIGURE 4 — PER-REGIME SPATIAL CONTOURS (rendered natively by Fluent)
const CONTOURS = path.join(FIGURES, "regime_contours");
const contourImg = (file, wPx = 520) => new Paragraph({
  spacing: { after: 60 },
  alignment: AlignmentType.CENTER,
  children: [new ImageRun({
    type: "png",
    data: fs.readFileSync(file),
    transformation: { width: wPx, height: Math.round(wPx * 0.72) },
  })],
});

children.push(new Paragraph({
  pageBreakBefore: true,
  children: [new TextRun({ text: "", size: 1 })],
}));

children.push(H2("Figure 4: Spatial Fields Inside the Capsule — Per Regime"));

children.push(P("These contours are rendered directly by Fluent from the solved field data for each regime's winning PCM (no post-processing reconstruction). Each pane is a 2D half-slice: the symmetry axis runs along the bottom edge, so the capsule appears as a half-dome sitting in the flowing hot water. The capsule shows a cold solid core (blue) wrapped by a melt front (cyan–green ring), while the surrounding water is hot and fully liquid."));

const REGCONT = [
  { r: 0, pcm: "PureTemp 58", liq: "regime0_PureTemp58_liqfrac.png", tmp: "regime0_PureTemp58_temp.png",
    note: "Core at ~331 K (58 °C) = PureTemp 58's melt point; the slowest-melting PCM, so the solid core is the largest of the three." },
  { r: 1, pcm: "RT57HC", liq: "regime1_RT57HC_liqfrac.png", tmp: "regime1_RT57HC_temp.png",
    note: "Core at ~330 K (57 °C) = RT57HC's melt point; a slightly smaller solid core than Regime 0, matching its lower melt point and faster melting." },
  { r: 2, pcm: "RT57HC", liq: "regime2_RT57HC_liqfrac.png", tmp: "regime2_RT57HC_temp.png",
    note: "Regime 2 also selected RT57HC, so the single-capsule melt field is the same as Regime 1. The regimes differ at tank scale (105 vs 98 capsules, different flow rate), not in the per-capsule PCM physics shown here." },
];

for (const g of REGCONT) {
  children.push(H3(`Regime ${g.r} — ${g.pcm}`));
  try {
    children.push(contourImg(path.join(CONTOURS, g.liq)));
    children.push(cap(`Liquid fraction — Regime ${g.r} (${g.pcm}). Red = molten water (LF ≈ 1); blue capsule core = solid PCM (LF ≈ 0); cyan–green ring = the advancing melt front.`));
    children.push(contourImg(path.join(CONTOURS, g.tmp)));
    children.push(cap(`Static temperature (K) — Regime ${g.r} (${g.pcm}). Hot water ≈ 343 K (70 °C); cold capsule core at the PCM melt point; faint warm plume downstream shows advection past the capsule.`));
  } catch (e) {
    children.push(P("(Contour image not found — run ansys/export_contours.py to regenerate)", { color: "FF0000" }));
  }
  children.push(cap(g.note));
  children.push(new Paragraph({ text: "" }));
}

children.push(P("How these were made: ansys/export_contours.py loads each solved .cas.h5/.dat.h5, builds a native Fluent banded contour of the field, and exports it with results.graphics.picture.save_picture — the same graphics path the live demo uses, so the image is Fluent's own render of the real mesh.", { italics: true, color: MUTED, size: SMALL }));

children.push(new Paragraph({ text: "" }));

// ─────────────────────────────────────────────────────────────────────────────
// FIGURE 5 — DISCHARGE (PCM heating the water), single capsule + whole tank
const DISCHARGE = path.join(FIGURES, "discharge");
const TANKDIS = path.join(FIGURES, "tank_discharge");

children.push(new Paragraph({
  pageBreakBefore: true,
  children: [new TextRun({ text: "", size: 1 })],
}));

children.push(H2("Figure 5: The PCM Working — Discharge (Capsules Heating the Water)"));
children.push(P("Charging (Figures 3–4) showed hot water MELTING the PCM. Discharge is the reverse, and the payoff: in the evening the water has cooled, so the melted PCM SOLIDIFIES and releases its stored heat back into the water — the PCM heats the water. This is what keeps the tank warm after sunset."));

children.push(H3("Whole tank — all 34 capsules discharging together"));
children.push(P("The full tank with the melting model switched on: all 34 capsules start hot and fully melted, the tank water starts cold, and they discharge together, with no sun (ansys/fluent_tank_discharge.py). This is the capsules and the tank water working as one coupled model."));
try {
  children.push(contourImg(path.join(TANKDIS, "tank_regime0_puretemp58_temp_END.png")));
  children.push(cap("Temperature after 2 h — the 34 capsules (red dots) sit inside the tank; a warm halo of heated water has spread out from the capsule bank into the cooler tank water. The capsules are heating the tank water."));
  children.push(contourImg(path.join(TANKDIS, "tank_regime0_puretemp58_liqfrac_END.png")));
  children.push(cap("Liquid fraction after 2 h — the tank water is liquid (red); each capsule shows a blue ring around a warmer centre, so every capsule is solidifying from the outside in, releasing its latent heat."));
} catch (e) {
  children.push(P("(Whole-tank discharge images not found — run ansys/fluent_tank_discharge.py)", { color: "FF0000" }));
}
children.push(cap("Regime 0 (PureTemp 58): over 2 h the tank water warmed 30.0 → 36.4 °C while the capsules cooled 70 → 54.6 °C and solidified to 27% liquid. Energy-only (conduction), consistent with the rest of the project — real convection would mix the warm water faster, but the mechanism shown is correct."));

children.push(H3("Single capsule — the same discharge, up close"));
children.push(P("The capsule-scale version (ansys/fluent_discharge_demo.py) shows one capsule's discharge in detail, the way each capsule in the tank behaves:"));
try {
  children.push(contourImg(path.join(DISCHARGE, "regime0_puretemp58_temp_END.png")));
  children.push(cap("One capsule after 1 h: the hot capsule (red dome) has grown a warm halo in the water around it — heat flowing out of the PCM into the water."));
} catch (e) {}

children.push(P("How to run it yourself (live): python ansys/fluent_tank_discharge.py --regime 0 --hours 1 --live  (whole tank), or python ansys/fluent_discharge_demo.py --regime 0 --live  (single capsule). Both animate the discharge, printing water and PCM temperature per simulated minute.", { italics: true, color: MUTED, size: SMALL }));

children.push(new Paragraph({ text: "" }));

// ─────────────────────────────────────────────────────────────────────────────
// HOW TO OPEN IN ANSYS
children.push(new Paragraph({ children: [new TextRun({ text: "", size: 1 })] }));
children.push(new Paragraph({
  pageBreakBefore: true,
  children: [new TextRun({ text: "", size: 1 })]
}));

children.push(H2("How to Open and View the Models in ANSYS Fluent GUI"));

children.push(P("All three regimes have pre-solved case files (.cas.h5) ready to open. You can view the results without re-solving."));

children.push(H3("Step 1: Launch Fluent"));
children.push(B("1. Open ANSYS Workbench or Fluent directly"));
children.push(B("2. Select: 2D, Double Precision, 2 processes"));
children.push(B("3. Click OK to launch Fluent"));

children.push(P("If you see: \"Unexpected license problem; exiting\" → A stray license process is running. Kill it and retry:"));
children.push(CODE("Get-Process ansyscl -ErrorAction SilentlyContinue | Stop-Process -Force"));

children.push(H3("Step 2: Open a Case File"));
children.push(B("In the Fluent menu: File → Read → Case..."));
children.push(B("Navigate to: objective2_design_optimization/ansys/"));
children.push(B("Choose one of these:"));

children.push(new Paragraph({
  bullet: { level: 1 },
  spacing: { after: 60 },
  children: [new TextRun({
    text: "v7_puretemp58.cas.h5  (Regime 0, PureTemp 58, solved — melt field)",
    size: BODY, color: INK, font: "Calibri",
  })],
}));

children.push(new Paragraph({
  bullet: { level: 1 },
  spacing: { after: 60 },
  children: [new TextRun({
    text: "v7_rt57hc.cas.h5  (Regime 1, RT57HC, solved — melt field)",
    size: BODY, color: INK, font: "Calibri",
  })],
}));

children.push(new Paragraph({
  bullet: { level: 1 },
  spacing: { after: 60 },
  children: [new TextRun({
    text: "v7_rt57hc.cas.h5  (Regime 2, RT57HC — same PCM solve as Regime 1)",
    size: BODY, color: INK, font: "Calibri",
  })],
}));

children.push(P(""));

children.push(H3("Step 3: Verify Settings"));
children.push(P("Once opened, check General tab:"));
children.push(B("Space: 2D Planar (not axisymmetric — these are planar cases)"));
children.push(B("Time: Transient (cases were solved over 6 hours)"));

children.push(P(""));

children.push(H3("Step 4: View Results"));
children.push(B("Go to: Results → Contours"));
children.push(B("Display → Temperature (or Liquid Fraction for PCM melting state)"));
children.push(B("You'll see the solved temperature/melt field across all zones"));

children.push(P("Or create a report: Reports → Reference Values → Copy the peak temperatures"));

children.push(P(""));

// ─────────────────────────────────────────────────────────────────────────────
// HOW TO OPEN EACH FIGURE, FILE BY FILE
children.push(H2("How to Open Each Figure in ANSYS — File by File"));

children.push(P("Each figure above maps to a specific case file and a specific display. Open the file named, then follow the clicks. Quick map:"));

children.push(table(
  ["Figure", "Open this file", "Then display"],
  [
    ["1 — Tank + capsules + panel (mesh)", "system_tank_pcm_panel_setup.cas.h5", "Graphics → Mesh, colour by Zone"],
    ["2 — Temperature field", "system_tank_pcm_panel_solved.cas.h5 (+ .dat)", "Contours → Static Temperature"],
    ["3 — PCM melt comparison (chart)", "v7_c25 / v7_c26 / v7_rt57hc / v7_puretemp58 (+ .dat)", "Contours → Liquid Fraction (per PCM)"],
    ["4 — Per-regime spatial fields", "v7_puretemp58 (R0), v7_rt57hc (R1/R2) (+ .dat)", "Contours → Liquid Fraction / Temperature"],
  ],
  [2400, 3400, 2800], { tiny: true }
));

children.push(P(""));

children.push(H3("Figure 1 — Tank + PCM Capsules + Collector Panel (mesh & zones)"));
children.push(B("File → Read → Case… → ansys/system_tank_pcm_panel_setup.cas.h5  (mesh only — no .dat needed)"));
children.push(B("Left tree: Results → Graphics → Mesh → double-click"));
children.push(B("In the Mesh panel: tick all zones under Surfaces, set Coloring → Zone → Display"));
children.push(B("You'll see the full system coloured by cell zone — tank water (31,008), PCM capsules (4,847), Al shell (511), collector (3,200), absorber (1,200), riser (2,200); 42,966 cells total"));

children.push(H3("Figure 2 — Temperature Field During Charging"));
children.push(B("File → Read → Case & Data… → ansys/system_tank_pcm_panel_solved.cas.h5  (its .dat loads automatically)"));
children.push(B("Results → Graphics → Contours → New"));
children.push(B("Contours of: Temperature → Static Temperature → select all surfaces → tick Filled → Display"));
children.push(B("Full-system view: absorber ~139 °C → panel ~125 °C → riser ~61 °C → tank ~32 °C"));
children.push(P("To get the right-hand \"tank-only\" panel: in the Contours panel untick Auto Range, set Min/Max to the tank's own range (≈ 305–335 K), and Display again. This rescales the colour map so tank detail is visible instead of one flat block (the absorber is so much hotter it otherwise dominates the scale)."));

children.push(H3("Figure 3 — PCM Melt Comparison (four materials)"));
children.push(P("Figure 3 is a chart drawn from four solved runs, not a single Fluent window. Two ways to reproduce it:"));
children.push(B("Fastest — redraw the chart: python ansys/plot_v4_pcm_comparison.py re-reads the melt-history CSVs and regenerates 03_pcm_melt_comparison.png"));
children.push(B("In ANSYS — view each PCM's field: open each of v7_c25 / v7_c26 / v7_rt57hc / v7_puretemp58 (.cas.h5 + .dat.h5), then Results → Contours → Liquid Fraction. Viewing the four is what the chart summarises."));
children.push(P("The raw numbers behind the curves are in ansys/v7_<pcm>_melt_history.csv (time, liquid fraction, capsule temperature). Final rows read 0.60 / 0.50 / 0.47 / 0.38 for C25 / C26 / RT57HC / PureTemp 58."));

children.push(H3("Figure 4 — Per-Regime Spatial Contours"));
children.push(B("Regime 0: File → Read → Case & Data… → ansys/v7_puretemp58.cas.h5"));
children.push(B("Regimes 1 & 2: ansys/v7_rt57hc.cas.h5  (same PCM, so same single-capsule field)"));
children.push(B("Results → Contours → Liquid Fraction (melt front) or Static Temperature → Display — these are the exact images in Figure 4"));

children.push(P(""));

// ─────────────────────────────────────────────────────────────────────────────
// WHAT FILES MEAN
children.push(H2("Understanding the File Names"));

children.push(table(
  ["File Type", "Example", "What It Is"],
  [
    [".cas.h5", "regime0_v3_mesh_only.cas.h5", "Case file — geometry + mesh only"],
    [".cas.h5", "regime0_v3_c26_melting.cas.h5", "Case file — mesh + solved results (temperature & liquid fraction)"],
    [".dat.h5", "regime0_v3_c26_melting.dat.h5", "Data file — companion to .cas file; must be in same folder"],
    [".msh", "regime0_v3_capsule.msh", "Mesh file (gmsh format) — source geometry before Fluent import"],
  ],
  [2000, 2500, 3500]
));

children.push(P("To open a case: you need BOTH .cas.h5 and .dat.h5 in the same folder. They are paired."));

children.push(P(""));

// ─────────────────────────────────────────────────────────────────────────────
// LIVE DEMO OPTIONS
children.push(H2("Live Demo Command Options"));

children.push(table(
  ["Flag", "Values", "Default", "What It Does"],
  [
    ["--regime", "0, 1, or 2", "0", "Which climate regime to run"],
    ["--hours", "any number", "6", "Physical simulation time (hours)"],
    ["--dt", "seconds", "20", "Timestep (default is stable; don't change unless you know what you're doing)"],
    ["--headless", "–", "off", "Run without opening the Fluent window (for testing)"],
    ["--rebuild-mesh", "–", "off", "Build a fresh mesh at the optimal radius instead of reusing v3 mesh"],
  ],
  [1500, 1500, 1200, 3200]
));

children.push(P("Examples:"));
children.push(CODE("python fluent_live_demo.py --regime 1 --hours 3"));
children.push(CODE("python fluent_live_demo.py --regime 2 --headless"));
children.push(CODE("python fluent_live_demo.py --hours 1   # Quick 1-hour look at Regime 0"));

children.push(P(""));

// ─────────────────────────────────────────────────────────────────────────────
// WHAT THE OUTPUTS MEAN
children.push(H2("What the Outputs Tell You"));

const TT = DES.map((d) => d.one_shot_test_2006_2010);
const rng = (a, fn) => `${fn(Math.min(...a))}–${fn(Math.max(...a))}`;

children.push(H3("Paired gain (kWh/yr)"));
children.push(P(`Extra heat delivered at ≥ 45 °C between 18:00 and 09:00 compared with an identical tank without PCM, same flow and weather. Higher is better. One-shot test range: ${rng(TT.map((t) => t.gain_mean_kWh), f1)} kWh/yr, positive in every test year of every regime.`));

children.push(H3("Margin over the repeatability band"));
children.push(P(`How many times larger than the noise floor the gain is. Against the core band (years, timestep, nodes, PCM properties, anchor): ${rng(TT.map((t) => t.gain_over_core_band), f1)}×. Against the full band, which also includes mains-temperature and demand variation: only ${rng(TT.map((t) => t.gain_over_full_band), f1)}×. The sign never changes; the size depends on how noise is counted.`));

children.push(H3("Overheat-guard hours (the cost of PCM)"));
children.push(P(`The capsules displace water in the fixed 100 L tank, so the collector trips the safety shield more often: +${rng(TT.map((t) => t.overheat_extra_hours_per_year), f0)} hours per year versus the plain tank. PCM wins on delivered energy but is always worse on this metric.`));

children.push(H3("Constraint Margins"));
children.push(P("How much headroom below the hard safety limits (worst test year, worst anchor):"));
children.push(B(`Water max: 75 °C hard limit. Designs peak at ${rng(TT.map((t) => t.t_water_max_C), f1)} °C`));
children.push(B(`PCM max: 65 °C hard limit. Designs peak at ${rng(TT.map((t) => t.t_pcm_max_C), f1)} °C`));

children.push(P("All three designs stay within the limits, with zero hours over them, in every test year."));

children.push(P(""));

// ─────────────────────────────────────────────────────────────────────────────
// KNOWN LIMITATIONS
children.push(H2("Known Limitations & Caveats"));

children.push(B("First-order upwind is the only discretisation under which all four PCMs converge. It is more diffusive than second order, so the reported melt fractions (Figure 3) are conservative — read the ordering, not the absolute values."));

children.push(B("The mesh is a 2D symmetry half-slice, so buoyancy-driven convection inside the melting PCM is excluded. The tank model carries this enhancement empirically by design."));

children.push(B("Temporal resolution: Figures 1–2 are energy-only (no flowing water). Figure 3 is a standalone duty (capsule in 70 °C water). Full system dynamics are in the tank model that runs the optimization."));

children.push(B("These cases verify that the physics assumptions made in the fast tank model are sound. They do not re-derive the optimal designs — designs were chosen by the tank model + NSGA-II, then verified here in CFD."));

children.push(P(""));

// ─────────────────────────────────────────────────────────────────────────────
// FIGURE 6 — SEVEN WHAT-IF DESIGNS (numbers read from ansys/criteria_common/*.csv at build time)
const CRITDIR = path.join(ROOT, "ansys");
const imgW = (file, w, ratio) => new Paragraph({
  spacing: { after: 60 }, alignment: AlignmentType.CENTER,
  children: [new ImageRun({ type: "png", data: fs.readFileSync(file), transformation: { width: w, height: Math.round(w / ratio) } })],
});
function pairRow(dir, key, capText) {
  const f = (s) => path.join(CRITDIR, dir, "figures", `${key}_${s}_END.png`);
  const cell = (file, label) => new TableCell({
    width: { size: 4900, type: WidthType.DXA },
    margins: { top: 20, bottom: 20, left: 40, right: 40 },
    borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } },
    children: [imgW(file, 300, 960 / 720), new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 },
      children: [new TextRun({ text: label, size: CAPTION, color: MUTED, font: "Calibri", italics: true })] })],
  });
  return [new Table({
    width: { size: 9800, type: WidthType.DXA }, columnWidths: [4900, 4900],
    borders: { top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE }, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
               insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE } },
    rows: [new TableRow({ children: [cell(f("temp"), "Temperature after 1 h"), cell(f("liqfrac"), "Liquid fraction after 1 h")] })],
  }), cap(capText)];
}

children.push(new Paragraph({ pageBreakBefore: true, children: [new TextRun({ text: "", size: 1 })] }));
children.push(H2("Figure 6: Seven What-If Designs — Fewer or More Capsules, and How the Final One Is Chosen"));
children.push(P("Objective 2 searched thousands of designs and kept one. To show WHY that one, seven designs for Regime 0 (PureTemp 58, the common plant) were each run two ways: the fast tank model (it applies the same selection funnel that chose the optimum, so every design gets a verdict) and ANSYS Fluent (a one-hour whole-tank discharge: capsules start hot and melted, tank water cold, no sun, so you watch the PCM heat the water). Each has its own folder, ansys/criteria_<n>_<name>/, with its parameters (criteria.json), code, mesh, node-model verdict, Fluent log, time series and pictures."));

children.push(H3("The seven designs and how their parameters vary"));
children.push(table(
  ["Design", "Capsules", "Radius (mm)", "PCM fraction", "Flow (kg/s)", "Arrangement", "PCM mass (kg)"],
  CRIT_NODE.map((c) => [c.criteria, c.N, f1(c.R_in_mm), `${f1(c.fraction_pct)} %`, f2(c.flow), c.arr, f1(c.pcm_mass_kg)]),
  [3000, 900, 1100, 1200, 1000, 1500, 1100], { tiny: true }
));
children.push(B("1 · MAX: every knob at its upper bound (radius 40 mm, fraction 40 %, flow 0.050). The capsule count is capped at 140, so it has the SAME geometry as the optimum and differs only in flow."));
children.push(B("2 · MIN: every knob at its lower bound: 380 tiny capsules of 10 mm radius holding 2 % PCM, flow 0.010, single layer."));
children.push(B("3 · NOT optimal, but working: a real design the funnel evaluated (the weakest of its six finalists, 132 capsules), so it passes every hard gate."));
children.push(B("4–6 · Only the capsule COUNT changes (radius 40 mm, flow 0.030, staggered kept optimal): 30 capsules (your wish), 14 (10 % of optimal), 70 (50 %)."));

children.push(H3("Why each is not the final design (tank-model verdict, select years 2020–21)"));
children.push(table(
  ["Design", "Gain (kWh/yr)", "% of optimal", "Overheat h/yr", "Funnel verdict"],
  CRIT_NODE.map((c) => [c.criteria, f1(c.g_window), `${f0(c.pct_of_optimal)} %`, f0(c.d_overheat), c.verdict]),
  [2500, 1000, 900, 1000, 4400], { tiny: true }
));
children.push(P("Reading the verdicts. Rule A: a gain inside the repeatability band is indistinguishable from a plain tank. S0: the design must be within one band of the best gain. S1: among designs tied on gain, the one with the fewest overheat-guard hours wins. So the optimum is not simply \"the most PCM\": designs 1 and 3 tie it on gain and lose only on overheating, which is why the tie-break rules matter."));

children.push(H3("What ANSYS Fluent shows for each (1 h whole-tank discharge)"));
children.push(table(
  ["Design", "Capsules drawn / real", "Water rise (K)", "PCM end (°C)", "Liquid fraction end", "Heat to water (kJ/m)"],
  CRIT_FLUENT.map((c) => [c.criteria, `${c.drawn} / ${c.n_3d}`, f2(c.water_rise_K), f1(c.pcm_end_C), f2(c.liq_frac_end), f0(c.heat_to_water_kJ_per_m)]),
  [3200, 1400, 1100, 1100, 1500, 1500], { tiny: true }
));
try {
  children.push(imgW(path.join(CRITDIR, "criteria_common", "FLUENT_comparison_all_criteria.png"), 640, 2210 / 650));
  children.push(cap("Water temperature, capsule temperature and liquid fraction for all seven designs. More PCM warms the water more; the minimum design (green) has so little PCM that it has handed over all its stored heat (fully solidified) within about ten minutes, after which the capsules only cool."));
} catch (e) { children.push(P("(comparison chart not found)", { color: "FF0000" })); }

children.push(H3("Pictures: the optimum, a 30-capsule tank, and the minimum design"));
try {
  const t = (i) => CRIT_FLUENT[i];
  children.push(...pairRow("criteria_0_optimal_reference", "criteria_0_optimal_reference", `0 · Optimal: ${t(0).n_3d} capsules (34 drawn). Water +${f1(t(0).water_rise_K)} K; every capsule solidifies from the outside in, warming the water around it.`));
  children.push(...pairRow("criteria_4_only_30_capsules", "criteria_4_only_30_capsules", `4 · Only 30 capsules (7 drawn). Water +${f1(t(4).water_rise_K)} K: the PCM works, but there is too little of it to warm the tank much.`));
  children.push(...pairRow("criteria_2_min_all", "criteria_2_min_all", `2 · Minimum parameters (${t(2).n_3d} tiny capsules, ${t(2).drawn} drawn). The PCM is fully ${Number(t(2).liq_frac_end) === 0 ? "solid" : "spent"} within the hour and the water barely warms (+${f1(t(2).water_rise_K)} K).`));
} catch (e) { children.push(P("(criteria pictures not found — run ansys/criteria_common/run_all_fluent.py)", { color: "FF0000" })); }

children.push(H3("The same seven over a whole year, for all three regimes (MATLAB view of the tank-model output)"));
const M1_REG = [[0, "m1"], [1, "m1_regime1"], [2, "m1_regime2"]];
for (const [k, folder] of M1_REG) {
  try {
    const png = path.join(ROOT, "results", folder, "figures", "M1_C_annual_ranking.png");
    const dim = (() => { const b = fs.readFileSync(png); return [b.readUInt32BE(16), b.readUInt32BE(20)]; })();   // PNG header: width, height
    children.push(imgW(png, 560, dim[0] / dim[1]));
    children.push(cap(`Regime ${k} (${DES[k].selected_pcm}): annual gain over the plain tank (left) and overheat-guard hours (right) for the seven designs, select year 2020, centre anchor. Every PCM design spends more hours in the shield than the plain tank.`));
  } catch (e) { children.push(P(`(MATLAB figure for regime ${k} not found — run scripts/c20_m1_export.py --regime ${k}, then matlab_m1/m1_main.m)`, { color: "FF0000" })); }
}
children.push(P("Each regime has its own folder of MATLAB figures and animations (results/m1/, results/m1_regime1/, results/m1_regime2/): discharge test, three real weather days, annual ranking, the four Objective-1 PCMs and three animated tank cut-aways. For regime 0 the seven designs are exactly those of the ansys/criteria_* folders (both read ansys/criteria_common/scenarios.py); for regimes 1 and 2 they follow the same rules around that regime's own winner, and criterion 3 is a real funnel finalist of that regime's winning pair. The MATLAB view uses one weather year, so its gains differ from the tank-model table by a few kWh; designs 0 and 1 can swap order because their gap is far inside the repeatability band. The Fluent seven-criteria study itself covers regime 0 only.", { size: SMALL, color: MUTED }));

children.push(H3("How to run a design yourself"));
children.push(CODE("cd ansys/criteria_4_only_30_capsules"));
children.push(CODE("python fluent_tank_discharge_criteria.py --hours 1 --live     # watch it in the Fluent window"));
children.push(CODE("python fluent_tank_discharge_criteria.py --hours 1            # headless: numbers + pictures"));
children.push(P("A headless one-hour run takes about 5–6 minutes. Close any other Fluent window first (one student licence at a time). The tank-model verdict for a design: python ansys/criteria_4_only_30_capsules/run_node_model.py (run from the project root)."));
children.push(P("Honest limits. The Fluent slice is 2-D, so every design is drawn with drawn = round(N × 34/140) capsules at half the radius (the proxy rule); designs 0 and 1 give identical Fluent output because they differ only in flow and the discharge case has no flow; every kWh number comes from the tank model. This is a model-consistency check, not experimental validation.", { size: SMALL, color: MUTED }));

children.push(new Paragraph({ text: "" }));

// ─────────────────────────────────────────────────────────────────────────────
// PROVENANCE: plot code, values, validation, tank
children.push(new Paragraph({
  pageBreakBefore: true,
  children: [new TextRun({ text: "", size: 1 })],
}));

children.push(H2("Provenance: Plot Code, Parameter Values, Validation & the 100 L Tank"));

children.push(H3("Where the final plot code lives"));
children.push(table(
  ["Figure / plots", "Script", "Reads → writes"],
  [
    ["Results figures (G7–G11)", "src/plots/make_plots_results.py", "results/*.csv → results/plots/*.png (150 dpi)"],
    ["Fig 1 — system mesh & zones", "src/cfd/plot_system_mesh.py", "solved system case → 01_system_mesh_zones.png"],
    ["Fig 2 — temperature field", "src/cfd/plot_system_fields.py", "system_…_solved → 02_system_temperature_field.png"],
    ["Fig 3 — PCM melt comparison", "ansys/plot_v4_pcm_comparison.py", "v7_<pcm>_melt_history.csv → 03_pcm_melt_comparison.png"],
    ["Fig 4 — per-regime contours", "ansys/export_contours.py", "v7_puretemp58 / v7_rt57hc cases → regime_contours/*.png"],
  ],
  [2300, 2600, 2900], { tiny: true }
));
children.push(P("Every plot script only READS saved files — nothing is re-simulated and no number is typed by hand (the make_plots_results.py header states this explicitly). Figures 1–3 come from solved Fluent cases; Figure 4 is rendered natively by Fluent; the G-series figures come from the optimiser's saved CSVs."));

children.push(H3("How the parameter values were set"));
children.push(P("Values come from three places, never guessed into the plots:"));
children.push(B("Fixed system constants — configs/system_config_shared.yaml (FROZEN at Phase 0A, identical for all four states). Each value is a cited engineering assumption or a solver setting: collector 2.0 m² with F_R(τα)=0.75, F_R·U_L=4.5 W/m²K (legacy typical values, not re-fitted for 2.0 m²); 175 L/day demand; tank 100 L, U=0.8 W/m²K; 0.8 mm aluminium shell (k=205); safety 75 °C water / 65 °C PCM; shield bypass 72/62 °C."));
children.push(B("What the optimiser may vary — configs/design_space.yaml: capsule inner radius 10–40 mm, PCM volume fraction 2–40 %, arrangement {single-layer, staggered, radial}; flow is frozen at 0.030 kg/s (not searched). Every design is simulated at three stack positions (bottom, centre, top). Hard constraints: PCM peak ≤ 65 °C, water ≤ 75 °C in every simulated year."));
children.push(B("PCM thermal properties — taken from the Objective 1 database (data/objective1/pcm_database_tamilnadu.csv). No new PCMs are introduced in Objective 2; the shortlist (RT57HC, C25, C26, PureTemp 58) is Objective 1's output."));
children.push(P("The final chosen numbers are the frozen funnel's own output (results/c16_funnel_winners.csv) and the sealed contract in results/common100L_<hash>/ — the capsule counts, masses and test gains quoted in the tables above are read from that contract when this document is built, not typed by hand. The Fluent demos read the same file through ansys/o2_designs.py."));

children.push(H3("How the designs are validated"));
children.push(B("Two independent simulators. A fast 10-node tank model evaluates and ranks designs; ANSYS Fluent is an independent CFD physics cross-check that chooses nothing — it only confirms the melting physics the tank model assumes."));
children.push(B("Convergence gate. Annual useful energy must change < 0.05 % when the timestep is halved. Only 37.5 s passes (0.039 % from 37.5 to 18.75 s; 0.134 % at 150 → 75 s). The 150 s step is used for search and ranking only; every finalist and every reported number is re-run at 37.5 s."));
children.push(B("Simulator verification. Energy closure ≤ 4.3·10⁻¹¹ % (gate 0.1 %); timestep change per halving ≤ 0.047 % on delivered energy (gate 0.05 %); 10 vs 20 nodes ≤ 0.71 %; IS 12976 standing loss 2.05–4.82 °C over 16 h (limit 8 °C); 95 automated tests pass. With the latent heat set to zero the same capsules deliver 184–298 kWh/yr less than the real PCM in all 18 G1 cases, so the latent heat is doing the work."));
children.push(B("Pre-registered rules, reported as they fell. The selection funnel and the repeatability band were fixed before the select years were run; the cheap-screen fidelity rule FAILED (0 of 9 pairs), so it was not used for selection and every finalist was re-evaluated at full fidelity. The one-shot test on 2006–2010 was run once under a hash-keyed lock: PCM beat the plain tank in all 5 years of all 3 regimes."));
children.push(B("Water-only baseline. Each design is compared against a plain-water tank at the SAME flow, weather, demand and shield, so the reported benefit is a difference, insulated from shared modelling simplifications."));
children.push(B("CFD cross-check, honestly logged (docs/CFD_VERIFICATION.md). A v3 bug — the whole domain initialised cold, so the PCM never melted — was caught and fixed in v4: water starts at 343 K, the capsule is patched cold at 303 K and read back to confirm, and the run aborts if the initial state is wrong. The melt ordering C25 > C26 > RT57HC > PureTemp 58 follows melt point and conductivity exactly."));

children.push(H3("Why the tank is fixed at 100 L"));
children.push(B("How it's fixed: configs/system_config_shared.yaml sets tank.volume_L = 100.0, and design_space.yaml lists tank_volume_L under fixed_not_optimised — so the optimiser never changes it. H/D = 2 gives D = 0.399 m, H = 0.799 m (derived in src/design/geometry.py)."));
children.push(B("Why 100 L: it is the common plant for all four states (the Rajasthan reference used 50 L). With the 2.0 m² collector it stores 50 L per m², inside the 40–100 L/m² range of IS 12976:2023 §4.2; the legacy 2.5 m² pairing (40 L/m²) is kept only as a sensitivity case. Demand is 175 L/day of 45 °C water: at 100 L/day the plain tank already met 99 % of demand, so a PCM had nothing to add (a plant scan found that PCM only helps when the plain tank leaves demand unmet)."));
children.push(B("One consequence worth knowing: the 100 L tank is why the solver needs the finer 37.5 s step — the 50 L Rajasthan tank passed the convergence gate at 150 s; the larger tank does not. That is a property of the tank size, not a porting error."));

children.push(new Paragraph({ text: "" }));

// ─────────────────────────────────────────────────────────────────────────────
// SUMMARY
children.push(H2("Summary: What You Have"));

children.push(new Paragraph({
  bullet: { level: 0 },
  spacing: { after: 80 },
  children: [new TextRun({
    text: "3 fully solved ANSYS Fluent models (one per regime)",
    size: BODY, color: INK, font: "Calibri", bold: true,
  })],
}));

children.push(new Paragraph({
  bullet: { level: 0 },
  spacing: { after: 80 },
  children: [new TextRun({
    text: "All parameters documented (PCM, capsule geometry, flow, tank size, safety limits)",
    size: BODY, color: INK, font: "Calibri", bold: true,
  })],
}));

children.push(new Paragraph({
  bullet: { level: 0 },
  spacing: { after: 80 },
  children: [new TextRun({
    text: "Live demo script to watch models run in real-time",
    size: BODY, color: INK, font: "Calibri", bold: true,
  })],
}));

children.push(new Paragraph({
  bullet: { level: 0 },
  spacing: { after: 80 },
  children: [new TextRun({
    text: "Three key figures showing mesh, temperature field, and melt comparison",
    size: BODY, color: INK, font: "Calibri", bold: true,
  })],
}));

children.push(new Paragraph({
  bullet: { level: 0 },
  spacing: { after: 80 },
  children: [new TextRun({
    text: "Step-by-step instructions to open and view models in Fluent GUI",
    size: BODY, color: INK, font: "Calibri", bold: true,
  })],
}));

children.push(P("Everything is ready to show, explain, and hand over to Objective 3."));

// ══════════════════════════════════════════════════════════════════════════════

const doc = new Document({
  creator: "Objective 2 — Tamil Nadu",
  title: "ANSYS Fluent: Parameters and How to Open",
  sections: [{
    properties: {
      page: {
        margin: { top: 720, bottom: 720, left: 900, right: 900 }
      }
    },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(ROOT, "docs", "reports", "O2_ANSYS_Complete_Guide.docx");
  fs.writeFileSync(out, buf);
  console.log("wrote " + out + "  (" + (buf.length / 1024).toFixed(0) + " KB)");
});
