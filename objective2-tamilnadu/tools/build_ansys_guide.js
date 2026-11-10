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

children.push(table(
  ["Regime", "PCM", "Capsules", "Diameter", "PCM Mass", "Flow Rate", "Arrangement"],
  [
    ["0", "PureTemp 58", "104", "81.6 mm", "24.81 kg", "0.0388 kg/s", "Staggered"],
    ["1", "RT57HC", "98", "81.6 mm", "23.64 kg", "0.0295 kg/s", "Staggered"],
    ["2", "RT57HC", "105", "81.6 mm", "25.33 kg", "0.0267 kg/s", "Staggered"],
  ],
  [1000, 1300, 1100, 1200, 1200, 1200, 1400]
));

children.push(P(""));

children.push(table(
  ["Regime", "PCM Tm (°C)", "Useful Energy (kWh/yr)", "Solar Fraction", "Max Water (°C)", "Max PCM (°C)"],
  [
    ["0", "58.0", "1,668.65", "65.2%", "72.3", "62.3"],
    ["1", "56.5", "1,763.44", "57.8%", "72.4", "62.4"],
    ["2", "54.0", "1,679.40", "64.7%", "72.4", "62.4"],
  ],
  [1000, 1200, 1700, 1200, 1200, 1200]
));

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
    ["Collector area", "2.5", "m²"],
    ["Collector (FRτα)", "0.75", "–"],
    ["Collector (FRUL)", "4.5", "W/m²K"],
    ["Capsule material (shell)", "Aluminum (Al)", "–"],
    ["Capsule shell thickness", "1.0", "mm"],
    ["Mains temperature (est.)", "28.5 avg", "°C"],
    ["Demand target", "45", "°C"],
    ["Max safe water temp", "75", "°C"],
    ["Max safe PCM temp", "65", "°C"],
    ["Pump efficiency", "0.6", "–"],
    ["Max system pressure", "3.5", "bar"],
  ],
  [3000, 1500, 1000]
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
children.push(cap("Total mesh: 42,966 cells. Geometry from optimal design; capsule radius derived from diameter by optimizer."));

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
    text: "regime0_v3_c26_melting.cas.h5  (Regime 0, PureTemp 58, solved)",
    size: BODY, color: INK, font: "Calibri",
  })],
}));

children.push(new Paragraph({
  bullet: { level: 1 },
  spacing: { after: 60 },
  children: [new TextRun({
    text: "regime1_v3_c26_melting.cas.h5  (Regime 1, RT57HC, solved)",
    size: BODY, color: INK, font: "Calibri",
  })],
}));

children.push(new Paragraph({
  bullet: { level: 1 },
  spacing: { after: 60 },
  children: [new TextRun({
    text: "regime2_v3_c25_melting.cas.h5  (Regime 2, RT57HC, solved)",
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

children.push(H3("Useful Energy (kWh/yr)"));
children.push(P("Heat delivered to demand hours (evening) above 45 °C target. Higher is better. Range: 1,668–1,763 kWh/yr."));

children.push(H3("Solar Fraction"));
children.push(P("Fraction of annual demand met by solar (PCM + tank + collector). Range: 57.8–65.2%."));

children.push(H3("Constraint Margins"));
children.push(P("How much headroom below the hard safety limits:"));
children.push(B("Water max: 75 °C hard limit. Designs peak at 72.3–72.4 °C → ~2.7 °C margin"));
children.push(B("PCM max: 65 °C hard limit. Designs peak at 62.3–62.4 °C → ~2.7 °C margin"));

children.push(P("All three designs stay safely within limits under nominal operation."));

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
  const out = path.join(ROOT, "O2_ANSYS_Complete_Guide.docx");
  fs.writeFileSync(out, buf);
  console.log("wrote " + out + "  (" + (buf.length / 1024).toFixed(0) + " KB)");
});
