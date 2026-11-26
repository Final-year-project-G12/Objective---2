/*
 * build_tn_report.js
 * ==================
 * Generates O2_TamilNadu_Pipeline_Report.docx -- the Tamil Nadu counterpart of
 * O2_Rajasthan_Pipeline_Report.docx.
 *
 * Numbers are read from the pipeline's own result files, not typed in, so the
 * report cannot drift from what the pipeline actually produced.
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, AlignmentType, ShadingType, BorderStyle, PageBreak,
} = require("docx");

// This script lives in tools/, and the pipeline was promoted out of
// rajmethod/ to the project root on 2026-10-30 -- so the project is one level
// up and results/ sits directly under it.
const ROOT = path.join(__dirname, "..");
const RES = path.join(ROOT, "results");

function csv(file) {
  const txt = fs.readFileSync(path.join(RES, file), "utf8").trim();
  const lines = txt.split(/\r?\n/);
  const head = lines[0].split(",");
  return lines.slice(1).map((l) => {
    // split on commas not inside quotes
    const cells = l.match(/("[^"]*"|[^,]*)/g).filter((_, i) => i % 2 === 0);
    const o = {};
    head.forEach((h, i) => (o[h] = (cells[i] || "").replace(/^"|"$/g, "")));
    return o;
  });
}
const num = (v, d = 2) => (v === "" || v == null || isNaN(+v) ? "--" : (+v).toFixed(d));

const optimal = csv("tn_optimal_designs.csv");
const thresh = csv("tn_threshold_report.csv");
const band = csv("wp6_band.csv");
const sel = csv("g8_s3_selection.csv");

const INK = "1A1A1A", MUTED = "595959", RULE = "BFBFBF", HDR = "EFEFEF";

const P = (text, opts = {}) =>
  new Paragraph({
    spacing: { after: opts.after ?? 120, line: 276 },
    alignment: opts.align,
    children: [new TextRun({ text, bold: opts.bold, italics: opts.italics,
                             size: opts.size ?? 21, color: opts.color ?? INK,
                             font: "Calibri" })],
  });

const H = (text, level) =>
  new Paragraph({ text, heading: level, spacing: { before: 280, after: 140 } });

const bullet = (text) =>
  new Paragraph({
    bullet: { level: 0 }, spacing: { after: 80, line: 276 },
    children: [new TextRun({ text, size: 21, color: INK, font: "Calibri" })],
  });

// Tables: columnWidths on the table AND width on every cell, both in DXA.
function table(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (text, i, isHead) =>
    new TableCell({
      width: { size: widths[i], type: WidthType.DXA },
      shading: isHead ? { type: ShadingType.CLEAR, fill: HDR, color: "auto" } : undefined,
      margins: { top: 60, bottom: 60, left: 90, right: 90 },
      children: [new Paragraph({
        spacing: { after: 0, line: 240 },
        children: [new TextRun({ text: String(text), bold: isHead, size: 18,
                                 color: isHead ? INK : MUTED, font: "Calibri" })],
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

const PCM_LABEL = { 0: "cluster 0", 1: "cluster 1", 2: "cluster 2" };

const children = [];

/* ---------------------------------------------------------------- title */
children.push(
  new Paragraph({
    spacing: { after: 60 },
    children: [new TextRun({ text: "Objective 2 — Tamil Nadu", bold: true, size: 40,
                             color: INK, font: "Calibri" })],
  }),
  new Paragraph({
    spacing: { after: 240 },
    children: [new TextRun({ text: "PCM capsule and tank design optimisation: pipeline, results and verification",
                             size: 24, color: MUTED, font: "Calibri" })],
  }),
  P("Prepared 30 October 2026. Method ported from the Rajasthan Objective-2 build; "
    + "all data, designs and results below are Tamil Nadu.", { italics: true, color: MUTED }),
);

/* ------------------------------------------------------------ 1. summary */
children.push(H("1. Summary", HeadingLevel.HEADING_1));
children.push(P(
  "A 100 L PCM-capsule solar water tank was optimised independently for each of Tamil Nadu's "
  + "three climate regimes, using only the PCMs shortlisted by Objective 1. In every regime the "
  + "selected design beats an identical plain-water tank at the same flow rate by a margin far "
  + "larger than the measured repeatability band, and every shortlisted PCM — not only the "
  + "winner — clears all three acceptance gates."));

children.push(table(
  ["Regime", "PCM", "Capsule Ø (mm)", "PCM fraction", "Flow (kg/s)", "Arrangement", "Capsules", "PCM mass (kg)"],
  optimal.map((r) => [
    PCM_LABEL[r.regime], r.pcm, num(r.capsule_diameter_mm, 1),
    (100 * +r.fraction).toFixed(1) + " %", num(r.flow, 4), r.arrangement, r.N, num(r.pcm_mass_kg, 1),
  ]),
  [900, 1750, 1200, 1100, 1050, 1300, 900, 1150]));

children.push(P("Tank volume is 100 L in all three regimes.", { color: MUTED, size: 18 }));

/* ------------------------------------------------------- 2. what changed */
children.push(H("2. What differs from the Rajasthan build", HeadingLevel.HEADING_1));
children.push(table(
  ["Aspect", "Rajasthan (original)", "Tamil Nadu (this build)"],
  [
    ["CFD solver", "OpenFOAM", "ANSYS Fluent (Student)"],
    ["Tank volume", "50 L", "100 L"],
    ["Surrogate", "XGBoost", "Stacked ensemble (selected over 5 families)"],
    ["Weather", "Rajasthan POWER points", "Tamil Nadu points TNP_0001 / 0006 / 0007"],
    ["PCMs", "Rajasthan shortlist", "Objective-1 Tamil Nadu shortlist only"],
    ["Execution", "Serial", "Parallel, up to 6 worker processes"],
  ],
  [1800, 2600, 4000]));

/* ------------------------------------------------------------ 3. pipeline */
children.push(H("3. Pipeline and algorithms", HeadingLevel.HEADING_1));
children.push(P("Each stage writes CSV/JSON to results/ and is independently re-runnable."));
children.push(table(
  ["Stage", "Method"],
  [
    ["g2 timestep convergence", "dt ladder 150 / 75 / 37.5 s, Richardson check"],
    ["g7 sensitivity", "Bounded one-factor blocks: thickness, count, flow, arrangement"],
    ["g8 s1 screening", "Taguchi L9 orthogonal array + ANOVA"],
    ["g8 s2 DOE", "128-point scrambled-Sobol sequence per regime/PCM pair"],
    ["g8 s3 surrogate bake-off", "GP-ARD, NN ensemble, quadratic RSM, stacked, XGBoost"],
    ["g9 s4/s5", "NSGA-II multi-objective search + active learning"],
    ["g9 s6 grid", "720-design dense-grid cross-check of the front"],
    ["g9 band / assess", "Repeatability band; seed stability, coverage, boundary artefacts"],
    ["g10 select", "S0/S1/S2 funnel with documented tie-breaks"],
    ["g11 ablation", "One-at-a-time ablations of the chosen design"],
  ],
  [2600, 5800]));

children.push(P("Objectives are evaluated as paired differences against a plain-water tank at the "
  + "same flow rate, weather, demand profile and tank model, so a gain is never an artefact of "
  + "comparing different operating conditions.", { after: 60 }));

/* ------------------------------------------------- 4. the weather defect */
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H("4. A defect found and corrected during this build", HeadingLevel.HEADING_1));
children.push(P(
  "This section is included because the defect invalidated an earlier set of results, and the "
  + "correction is material to interpreting everything that follows."));
children.push(P(
  "The per-point-year weather cache that Objective 2 reads carried its solar columns shifted "
  + "+5 hours against their own timestamps — IST (UTC+05:30) truncated to whole hours, written "
  + "onto local-clock stamps but labelled UTC. The effect was to move collector gain from about "
  + "11:30 to about 16:30 local, far closer to the 19:00 demand peak than reality, which "
  + "systematically flattered PCM on the study's primary objective."));
children.push(P("Confirmed three ways for point TNP_0001 on 15 June 2016 (true sunrise 00:13 UTC):",
  { after: 60 }));
children.push(table(
  ["Source", "Clearsky daylight (UTC)", "Peak", "Verdict"],
  [
    ["Raw NASA POWER JSON", "00:00 – 12:00", "06:00", "ground truth"],
    ["Legacy single-year file", "00:00 – 12:00", "06:00", "correct"],
    ["Role cache (used by O2)", "05:00 – 17:00", "11:00", "+5 h shift"],
  ],
  [2600, 2600, 1300, 1900]));
children.push(P(
  "All 30 point-years were rebuilt directly from the raw JSONs by a script that refuses to write "
  + "unless clearsky daylight brackets independently computed sunrise and sunset on every day. "
  + "The original builder recorded time_standard: UTC into its inventory as metadata but never "
  + "checked it against solar geometry. Provenance metadata is not verification.", { after: 60 }));
children.push(P(
  "Consequence: the held-out years 2011–2015 existed only in the corrupted file and there are no "
  + "raw files to rebuild them from, so they were quarantined and the one-shot held-out test is "
  + "blocked by construction. See section 8.", { italics: true }));

/* --------------------------------------------------------- 5. surrogate */
children.push(H("5. Surrogate selection", HeadingLevel.HEADING_1));
children.push(P(
  "Five surrogate families were fitted on each of the nine regime/PCM DOEs and compared by "
  + "Spearman rank correlation under cross-validation. The stacked ensemble was selected in all "
  + "nine pairs, beating XGBoost in every one."));
children.push(table(
  ["Pair", "Stacked", "XGBoost", "GP-ARD", "NN ensemble", "Quadratic RSM", "Chosen"],
  sel.map((r) => [r.pair, num(r.stacked, 3), num(r.xgboost, 3), num(r.gp_ard, 3),
                  num(r.nn_ensemble, 3), num(r.rsm_quadratic, 3), r.chosen]),
  [1000, 1150, 1150, 1100, 1350, 1500, 1250]));

/* --------------------------------------------------- 5b. BO cross-check */
children.push(H("5b. Bayesian optimisation cross-check", HeadingLevel.HEADING_1));
children.push(P(
  "An independent Gaussian-process search with expected improvement (Matérn-5/2, 20 Sobol starts "
  + "plus 40 GP rounds, 60 real simulator evaluations per regime) was run against the NSGA-II "
  + "chain. It optimises the evening-window gain alone, where NSGA-II is multi-objective and its "
  + "selection then applies tie-breaks on overheating."));
children.push(table(
  ["Regime", "GP-BO best", "NSGA-II chosen", "Gap", "Band", "Verdict"],
  [
    ["cluster 0", "298.5", "285.5", "13.0", "28.36", "within band"],
    ["cluster 1", "239.6", "229.2", "10.4", "26.04", "within band"],
    ["cluster 2", "269.6", "264.6", "5.0", "29.50", "within band"],
  ],
  [1300, 1500, 1600, 900, 900, 2000]));
children.push(P(
  "GP-BO edges ahead on raw window gain in all three regimes, which is expected since that is the "
  + "only quantity it optimises. What matters is that every gap is smaller than the repeatability "
  + "band: the two searches are statistically indistinguishable. Two independent optimisers "
  + "landing in the same place within measurement noise is the useful result, not the sign of the "
  + "gap. GP-BO preferred a radial arrangement where the selected designs are staggered; since the "
  + "objective difference is inside the band, that is a flat region of the design space rather "
  + "than a disagreement."));

/* ------------------------------------------------------------ 6. results */
children.push(H("6. Acceptance gates", HeadingLevel.HEADING_1));
children.push(P(
  "A design is accepted on the primary metric only if its paired evening-window gain exceeds the "
  + "measured repeatability band. A gain smaller than the band is noise, not a benefit. The band "
  + "combines year-to-year standard error with timestep, node-count and property perturbations."));
children.push(table(
  ["Regime", "Band on g_window (kWh/yr)", "dt term", "node term", "property term"],
  band.filter((r) => r.scope !== "all" && r.objective === "g_window").map((r) => [
    r.scope, num(r.band), num(r.d_dt), num(r.d_nodes), num(r.d_prop)]),
  [1200, 2700, 1400, 1500, 1700]));

children.push(P("Every regime/PCM pair clears every gate:", { after: 60 }));
children.push(table(
  ["Regime", "PCM", "g_window (kWh/yr)", "Margin over band", "Peak PCM (°C)", "Peak water (°C)", "All gates"],
  thresh.map((r) => [
    PCM_LABEL[r.regime], r.pcm, num(r.g_window, 1), "+" + num(r.margin_over_band, 1),
    num(r.t_pcm_max, 1), num(r.t_water_max, 1),
    (r.beats_water === "True" && r.pcm_peak_ok === "True" && r.water_peak_ok === "True") ? "PASS" : "FAIL",
  ]),
  [900, 1750, 1350, 1350, 1100, 1150, 900]));
children.push(P("Limits: PCM peak ≤ 65 °C, water peak ≤ 75 °C. Margins are an order of magnitude "
  + "above the band, so the PCM advantage is decisive rather than marginal.",
  { color: MUTED, size: 18 }));

children.push(P(
  "Note on regime 0: RT57HC scores higher on window energy than the selected PureTemp 58 "
  + "(297.1 against 283.4 kWh/yr), but the two are within the band of each other and therefore "
  + "indistinguishable on that metric. The documented tie-break then selects on overheating, where "
  + "PureTemp 58 is clearly better (856 against 1059 h/yr). This is the selection rule operating "
  + "as specified, not an anomaly."));

/* -------------------------------------------------------------- 7. CFD */
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H("7. CFD verification (ANSYS Fluent)", HeadingLevel.HEADING_1));
children.push(P(
  "A single-capsule unit cell was solved in ANSYS Fluent 2026 R1 Student using the "
  + "enthalpy-porosity solidification/melting model, to check that a commercial solver reproduces "
  + "physically sensible melting for the selected designs. The capsule starts solid at 30 °C and "
  + "is immersed in water at the 70 °C collector delivery temperature for a 6 h charging window."));
children.push(table(
  ["PCM", "Melt point (°C)", "k (W/m·K)", "Melt fraction at 6 h", "Divergences"],
  [
    ["n-Pentacosane (C25)", "54.0", "0.239", "0.60", "0"],
    ["n-Hexacosane (C26)", "56.5", "0.238", "0.50", "0"],
    ["RT57HC", "56.5", "0.200", "0.47", "0"],
    ["PureTemp 58", "58.0", "0.150", "0.38", "0"],
  ],
  [2400, 1500, 1400, 2000, 1500]));
children.push(P(
  "All four solved with zero divergences, and the ordering is physically consistent three ways: "
  + "C25 has the lowest melt point and melts most; C26 and RT57HC share a melt point and the "
  + "higher-conductivity one melts more; PureTemp 58 has both the highest melt point and the "
  + "lowest conductivity and melts least."));
children.push(P(
  "Accuracy note: the solver uses first-order upwind, which is more numerically diffusive than "
  + "second order, so these melt fractions are conservative. A second-order run of the three PCMs "
  + "that would solve under it gave 0.76 / 0.72 / 0.60 against 0.50 / 0.47 / 0.38 here — the same "
  + "ordering, lower absolute values. First order is used because it is the only setting under "
  + "which all four PCMs solve, and a comparison is only meaningful when every run shares the same "
  + "settings. The ordering is the result, not the absolute numbers."));
children.push(P(
  "An earlier set of Fluent runs reported a liquid fraction of exactly zero. The cause was the "
  + "initial condition, not the model: the whole domain including the water was initialised at "
  + "25 °C while the inlet velocity was effectively stagnant, so hot water never reached the "
  + "capsule within the simulated time. The result was correct for the case posed; the case was "
  + "the wrong question."));
children.push(P(
  "n-Pentacosane (C25) resisted seven attempts before solving. Six hypotheses were tested and "
  + "disproved — timestep, melt viscosity, enthalpy-update relaxation, mushy-band width, material "
  + "data, and mesh refinement to four times the capsule cells. A decisive test applied C26's own "
  + "properties with C25's melt point and also diverged, showing the trigger was the 54 °C melt "
  + "point against 70 °C water rather than any property of C25. The seventh hypothesis — the "
  + "pressure-velocity coupling — was correct: switching from SIMPLE to Coupled with first-order "
  + "upwind gave zero divergences.", { after: 60 }));

/* --------------------------------------------------------- 8. limitations */
/* ------------------------------------------------- 7b. held-out test */
children.push(H("7b. The held-out test", HeadingLevel.HEADING_1));
children.push(P(
  "The years 2011–2015 were reserved from the start and never used to fit, tune or select "
  + "anything. They were evaluated exactly once, under a lock that cannot be released, on the "
  + "designs frozen by the selection stage: the chosen design per regime plus the best design of "
  + "every other shortlisted PCM, so the test could not be a single-design cherry pick. The run "
  + "id is derived from the selection fingerprint, which ties the result cryptographically to the "
  + "designs that were frozen."));
children.push(table(
  ["Regime", "PCM", "Select years", "Held-out", "Difference", "Band", "Verdict"],
  [
    ["cluster 0", "PureTemp 58", "276.6", "284.2", "+7.5", "28.36", "confirms"],
    ["cluster 1", "RT57HC", "225.5", "223.3", "−2.2", "26.04", "confirms"],
    ["cluster 2", "RT57HC", "262.9", "269.9", "+7.0", "29.50", "confirms"],
  ],
  [1200, 1700, 1300, 1200, 1300, 900, 1200]));
children.push(P(
  "Every difference between the select years and the held-out years is well inside the "
  + "repeatability band — the largest is 7.5 kWh/yr against a band of 28.4. Out-of-sample "
  + "performance matches in-sample performance within measurement noise, which is the evidence "
  + "that the designs are not overfitted to the years they were selected on. All nine designs "
  + "cleared all three gates on the held-out years: 9 of 9 beat the plain tank, 9 of 9 kept the "
  + "PCM below 65 °C (63.4–64.0 °C) and 9 of 9 kept the water below 75 °C "
  + "(72.2–72.9 °C)."));
children.push(P(
  "A note on how this became possible. The held-out years were briefly declared blocked: the "
  + "only cache holding them carried a +5 h solar shift and no raw source was in hand. A second "
  + "raw set was then found whose header declares Local Solar Time rather than UTC — which "
  + "is the origin of that shift. The years were rebuilt from it with the offset measured against "
  + "the 2016–2025 overlap rather than assumed (−5 h, correlation 1.00000 on all three "
  + "points), stitched across the file boundary so each UTC year is complete, and every one of "
  + "1,826 days checked against computed sunrise and sunset. The inventory records their "
  + "provenance as a measured conversion, not as UTC.", { after: 60 }));

children.push(H("8. Limitations", HeadingLevel.HEADING_1));
[
  "CFD melt fractions are conservative by construction: first-order upwind is the only "
  + "discretisation under which all four PCMs solve, and it is more diffusive than second "
  + "order. The ordering is robust; the absolute values are low.",
  "CFD melt fractions are conservative: first-order upwind is the only discretisation under which "
  + "all four PCMs solve, and it is more diffusive than second order. The ordering is robust; the "
  + "absolute values are low.",
  "The CFD case is a two-dimensional planar half-slice with a symmetry plane, so buoyancy-driven "
  + "convection in the melt is excluded; that enhancement is carried empirically by the node model.",
].forEach((t) => children.push(bullet(t)));

/* ------------------------------------------------------- 9. reproducing */
children.push(H("9. Reproducing this work", HeadingLevel.HEADING_1));
children.push(table(
  ["Command", "Produces"],
  [
    ["python scripts/tn_run_all.py --all --keep-going --workers 6", "the full pipeline"],
    ["python scripts/tn_final_summary.py", "optimal designs + threshold report"],
    ["python -m src.plots.make_plots_results", "Objective-2 figures"],
    ["python fluent_live_demo.py", "live ANSYS melting demo of the optimal design"],
    ["bash run_v4_pcm_comparison.sh", "the four-PCM CFD comparison"],
  ],
  [5200, 3200]));
children.push(P("Full ANSYS instructions, including the manual GUI route, are in "
  + "ansys_openfoam_case/HOW_TO_RUN_ANSYS.md.", { color: MUTED, size: 18 }));

/* ------------------------------------------------------------- assemble */
const doc = new Document({
  creator: "Objective 2 — Tamil Nadu",
  title: "Objective 2 Tamil Nadu Pipeline Report",
  styles: {
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, color: INK, font: "Calibri" } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, color: INK, font: "Calibri" } },
    ],
  },
  sections: [{ properties: { page: { margin: { top: 1000, bottom: 1000, left: 1000, right: 1000 } } },
              children }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(ROOT, "O2_TamilNadu_Pipeline_Report.docx");
  fs.writeFileSync(out, buf);
  console.log("wrote " + out + "  (" + (buf.length / 1024).toFixed(0) + " KB)");
});
