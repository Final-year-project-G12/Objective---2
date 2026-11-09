/*
 * build_simulator_note.js
 * =======================
 * One-page .docx of docs/SIMULATOR_AND_CFD.md: what we simulate with, why,
 * and why the CFD tool changed between Rajasthan and Tamil Nadu.
 *
 * Deliberately sized to ONE A4 page: 9 pt body, 8 pt tables, narrow margins,
 * tight line spacing. What did not survive that budget stays in the markdown
 * version, which the footer points to.
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, ImageRun, AlignmentType,
} = require("docx");

const ROOT = path.join(__dirname, "..");
const INK = "1A1A1A", MUTED = "5A5A5A", RULE = "C8C8C8", HDR = "F0F0F0";
const BODY = 18;      // 9 pt — docx sizes are half-points
const SMALL = 15;     // 7.5 pt for tables
const CAPTION = 14;

const P = (text, o = {}) => new Paragraph({
  spacing: { after: o.after ?? 50, line: o.line ?? 202 },
  children: [new TextRun({
    text, bold: o.bold, italics: o.italics,
    size: o.size ?? BODY, color: o.color ?? INK, font: "Calibri",
  })],
});

// alternating normal / bold runs in one paragraph
const PR = (parts, o = {}) => new Paragraph({
  spacing: { after: o.after ?? 50, line: 202 },
  children: parts.map((p) => new TextRun({
    text: typeof p === "string" ? p : p.t,
    bold: typeof p === "string" ? false : !!p.b,
    size: o.size ?? BODY, color: INK, font: "Calibri",
  })),
});

const H = (text) => new Paragraph({
  spacing: { before: 105, after: 50 },
  children: [new TextRun({ text, bold: true, size: 20, color: INK, font: "Calibri" })],
});

const B = (text) => new Paragraph({
  bullet: { level: 0 },
  spacing: { after: 32, line: 210 },
  children: [new TextRun({ text, size: BODY, color: INK, font: "Calibri" })],
});

function table(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (text, i, head) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    shading: head ? { type: ShadingType.CLEAR, fill: HDR, color: "auto" } : undefined,
    margins: { top: 30, bottom: 30, left: 65, right: 65 },
    children: [new Paragraph({
      spacing: { after: 0, line: 205 },
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


// ── figures ───────────────────────────────────────────────────────────────
// Side by side rather than stacked: the structure figure is portrait (0.86)
// and the melt figure is wide (2.41), so stacking them would cost about twice
// the vertical space on a page that is already tight. Widths are chosen so
// both render at nearly the same height.
const FIG = path.join(ROOT, "ansys", "figures");
const img = (file, wPx, ratio) => new Paragraph({
  spacing: { after: 40 },
  alignment: AlignmentType.CENTER,
  children: [new ImageRun({
    type: "png",
    data: fs.readFileSync(path.join(FIG, file)),
    transformation: { width: wPx, height: Math.round(wPx / ratio) },
  })],
});
const cap = (text) => new Paragraph({
  spacing: { after: 0, line: 195 },
  children: [new TextRun({ text, size: CAPTION, color: MUTED, font: "Calibri" })],
});

function figurePair() {
  const cell = (children, w) => new TableCell({
    width: { size: w, type: WidthType.DXA },
    margins: { top: 40, bottom: 40, left: 60, right: 60 },
    children,
  });
  return new Table({
    width: { size: 10106, type: WidthType.DXA },
    columnWidths: [3500, 6606],
    borders: {
      top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE },
      left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
      insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE },
    },
    rows: [new TableRow({ children: [
      cell([
        img("01_system_mesh_zones.png", 150, 1076 / 1257),
        cap("Figure 1 — the modelled system: 100 L tank, 34 PCM capsules, collector channel, "
          + "absorber plate and riser, as six separate Fluent cell zones over 42,966 cells."),
        cap("It is the geometry check: confirming the thing meshed is the thing meant, before any "
          + "physics is solved on it."),
      ], 3500),
      cell([
        img("03_pcm_melt_comparison.png", 372, 2025 / 840),
        cap("Figure 2 — all four shortlisted PCMs melted on one mesh under one duty, so the only "
          + "difference between the curves is the material itself."),
        cap("The ordering follows melt point and conductivity exactly as predicted, which is the "
          + "independent confirmation the fast tank model needed."),
      ], 6606),
    ]})],
  });
}

const children = [];

children.push(new Paragraph({
  spacing: { after: 30 },
  children: [new TextRun({
    text: "What we simulate with, and why",
    bold: true, size: 28, color: INK, font: "Calibri",
  })],
}));
children.push(P("Objective 2 — PCM capsule tank, Tamil Nadu · 31 October 2026",
  { color: MUTED, size: SMALL, after: 110 }));

children.push(H("The objective"));
children.push(PR([
  "For each of Tamil Nadu's three climate regimes, find the ",
  { t: "capsule size, number of capsules, PCM and flow rate", b: true },
  " that make a ", { t: "100 L", b: true },
  " solar water tank deliver the most useful hot water in the evening, and establish whether "
  + "that beats an identical tank with no PCM at all. Three sub-goals follow: search the design "
  + "space over full years of real weather against a paired plain tank; prove the benefit exceeds "
  + "the measured repeatability band, since a smaller gain is noise; and confirm the physics "
  + "independently in CFD.", ], { after: 36 }));

children.push(H("Two simulators, two jobs"));
children.push(table(
  ["", "Tank model", "ANSYS Fluent"],
  [
    ["scope", "whole tank, whole year", "one capsule, six hours"],
    ["runtime", "seconds per simulated year", "about 30 minutes per PCM"],
    ["role", "the optimiser's evaluator — it chooses the design", "independent physics check — it chooses nothing"],
    ["melt front", "not resolved; carried as an empirical factor", "resolved by enthalpy-porosity"],
  ],
  [1300, 4400, 4400]));
children.push(P(
  "Not alternatives. The search ran over 1,100 design evaluations before anything was chosen: at "
  + "CFD speed that is years of compute. CFD is how we test the assumptions that buy the speed.",
  { after: 40 }));

children.push(H("Why ANSYS Fluent here, where Rajasthan used OpenFOAM"));
children.push(PR([
  "A capability difference, not a preference: ",
  { t: "OpenFOAM's standard solvers have no native solidification/melting model.", b: true },
  " Its chtMultiRegionFoam resolves conjugate heat transfer well, but with sensible heating only "
  + "— no latent heat, no phase change. For a study whose premise is that a PCM stores heat in "
  + "its phase change, a solver that cannot melt the material shows only half the physics.",
], { after: 40 }));
children.push(table(
  ["", "Rajasthan (source study)", "Tamil Nadu (this study)"],
  [
    ["CFD solver", "OpenFOAM chtMultiRegionFoam", "ANSYS Fluent 2026 R1 Student"],
    ["phase change in CFD", "not modelled — sensible heating only", "enthalpy-porosity, melt front resolved"],
    ["tank volume", "50 L", "100 L, collector scaled to keep 40 L/m²"],
    ["surrogate model", "XGBoost", "stacked ensemble, chosen over 5 families in all 9 pairs"],
    ["tank model", "hers", "hers, adopted unchanged"],
  ],
  [1700, 4200, 4200]));
children.push(P(
  "The last row matters: the tank model is the source study's own code, so a difference in results "
  + "is a difference in inputs, not method. Absolute energy is not comparable across a 50 L and a "
  + "100 L tank; the algorithms and pass/fail criteria are.", { after: 36 }));

children.push(H("What we run in Fluent"));
children.push(P(
  "A half-disk capsule in a water annulus, meshed in gmsh, solved 2-D planar: solid at 30 °C in "
  + "water held at the 70 °C collector delivery temperature for a six-hour charging window. "
  + "Geometry, PCM identity and flow rate are read from the optimiser's own output. It yields melt "
  + "curves for all four PCMs, a flow-rate sweep showing the benefit saturating where the optimiser "
  + "settled, and the whole-system heat path.", { after: 40 }));

children.push(figurePair());

children.push(H("Stated limits"));
children.push(P(
  "First-order upwind is the only discretisation under which all four PCMs solve and is more "
  + "diffusive than second order, so melt fractions are conservative — read the ordering, not the "
  + "absolute values. The mesh is a symmetry half-slice, so buoyancy in the melt is excluded: that "
  + "is the enhancement the tank model carries empirically, by design. The whole-system case runs "
  + "energy-only, so it shows the heat path, not melting.",
  { after: 30 }));
children.push(P(
  "Full CFD history: docs/SIMULATOR_AND_CFD.md and docs/CFD_VERIFICATION.md.",
  { italics: true, color: MUTED, size: CAPTION, after: 0 }));

const doc = new Document({
  creator: "Objective 2 — Tamil Nadu",
  title: "What we simulate with, and why",
  sections: [{
    properties: { page: { margin: { top: 720, bottom: 576, left: 850, right: 850 } } },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(ROOT, "O2_Simulators_and_CFD_1page.docx");
  fs.writeFileSync(out, buf);
  console.log("wrote " + out + "  (" + (buf.length / 1024).toFixed(0) + " KB)");
});
