/*
 * build_climate_note.js
 * =====================
 * "Climate parameters in the simulators" — what is used, where in the code,
 * how it changes through a run, and how to check the ANSYS image outputs.
 *
 * Every file:line reference and every number was read off the code and the
 * config, not recalled.
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, AlignmentType,
} = require("docx");

const ROOT = path.join(__dirname, "..");
const INK = "1A1A1A", MUTED = "5A5A5A", RULE = "C6C6C6", HDR = "EFEFEF",
      CODE = "1F4E5F", WARN = "8A3A2A";
const BODY = 20, SMALL = 17, CAP = 15;

const P = (text, o = {}) => new Paragraph({
  spacing: { after: o.after ?? 110, line: o.line ?? 250 },
  children: [new TextRun({
    text, bold: o.bold, italics: o.italics,
    size: o.size ?? BODY, color: o.color ?? INK, font: "Calibri",
  })],
});

const PR = (parts, o = {}) => new Paragraph({
  spacing: { after: o.after ?? 110, line: 250 },
  children: parts.map((p) => new TextRun({
    text: typeof p === "string" ? p : p.t,
    bold: typeof p === "string" ? false : !!p.b,
    italics: typeof p === "string" ? false : !!p.i,
    font: (typeof p === "object" && p.c) ? "Consolas" : "Calibri",
    color: (typeof p === "object" && p.c) ? CODE : INK,
    size: o.size ?? BODY,
  })),
});

const H1 = (text) => new Paragraph({
  spacing: { before: 280, after: 110 },
  children: [new TextRun({ text, bold: true, size: 26, color: INK, font: "Calibri" })],
});
const H2 = (text) => new Paragraph({
  spacing: { before: 170, after: 80 },
  children: [new TextRun({ text, bold: true, size: 21, color: INK, font: "Calibri" })],
});

const B = (text) => new Paragraph({
  bullet: { level: 0 }, spacing: { after: 60, line: 250 },
  children: [new TextRun({ text, size: BODY, color: INK, font: "Calibri" })],
});

// a monospace block, for equations and commands
const CODEP = (text) => new Paragraph({
  spacing: { before: 50, after: 90, line: 235 },
  shading: { type: ShadingType.CLEAR, fill: "F5F5F5", color: "auto" },
  indent: { left: 180 },
  children: [new TextRun({ text, size: SMALL, color: CODE, font: "Consolas" })],
});

function table(headers, rows, widths, opts = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (text, i, head) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    shading: head ? { type: ShadingType.CLEAR, fill: HDR, color: "auto" } : undefined,
    margins: { top: 45, bottom: 45, left: 80, right: 80 },
    children: [new Paragraph({
      spacing: { after: 0, line: 225 },
      children: [new TextRun({
        text: String(text), bold: head, size: SMALL,
        color: head ? INK : (opts.mono && i === opts.mono ? CODE : MUTED),
        font: (opts.mono && i === opts.mono && !head) ? "Consolas" : "Calibri",
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

const ch = [];

/* ─────────────────────────── title ─────────────────────────── */
ch.push(new Paragraph({
  spacing: { after: 50 },
  children: [new TextRun({
    text: "Climate parameters in the simulators",
    bold: true, size: 36, color: INK, font: "Calibri",
  })],
}));
ch.push(P("Objective 2 \u2014 PCM capsule tank, Tamil Nadu \u00b7 4 November 2026",
  { color: MUTED, size: SMALL, after: 60 }));
ch.push(P(
  "What climate data enters the models, exactly where in the code it enters, how the values move "
  + "through a simulated year, whether the live CFD demo is working, and how to check the ANSYS "
  + "images of the tank and capsules. Every file reference and number below was read off the code "
  + "and the configuration, not recalled.", { color: MUTED, size: SMALL, after: 200 }));

/* ─────────────────── 1. which parameters ─────────────────── */
ch.push(H1("1. Which climate parameters are actually used"));
ch.push(P(
  "Each weather file holds twelve columns, but only three reach the physics. This is worth stating "
  + "plainly, because the presence of a column in the data is easily mistaken for its use in the model."));
ch.push(table(
  ["Column", "Used?", "What it drives"],
  [
    ["GHI_Wm2", "YES", "Solar input to the collector \u2014 the main driver"],
    ["T_amb_C", "YES", "Collector heat loss and tank standing loss"],
    ["local_hour / local_date", "YES", "Aligns the demand profile to local clock time"],
    ["GHI_clearsky_Wm2", "no (verification only)", "Used to check timestamps against solar geometry; never in the physics"],
    ["RH_pct", "no", "Carried from NASA POWER, unused"],
    ["wind_ms / WS_ms", "no", "Carried from NASA POWER, unused"],
    ["timestamp_utc, point_id, cluster_id, year", "no", "Bookkeeping"],
  ],
  [3000, 2100, 5000]));
ch.push(PR([
  { t: "A consequence worth knowing: ", b: true },
  "wind speed and humidity do not affect any result in this study. The collector's heat-loss "
  + "coefficient is a fixed ", { t: "F_R\u00b7U_L = 4.5 W/m\u00b2K", c: true },
  ", not a wind-dependent one, and the tank's standing loss uses a fixed ",
  { t: "U = 0.8 W/m\u00b2K", c: true }, ". A windier or more humid regime is therefore "
  + "indistinguishable from a calm dry one at the same irradiance and air temperature. For "
  + "Tamil Nadu's coastal regimes that is a real simplification, not a neutral one.",
]));
ch.push(P(
  "A fourth climate input is not hourly at all: mains water temperature. It is one constant per "
  + "regime, taken from Objective 1's climate signature (23.97\u201328.46 \u00b0C across the three "
  + "medoids). It does not vary by season.", { after: 150 }));

/* ─────────────────── 2. how they enter ─────────────────── */
ch.push(H1("2. How they enter the physics"));
ch.push(H2("Collector \u2014 the Hottel\u2013Whillier\u2013Bliss equation"));
ch.push(P("Both climate variables enter here, in one line:"));
ch.push(CODEP("Q_useful = A_c \u00d7 [ F_R(\u03c4\u03b1) \u00d7 I_t  \u2212  F_R\u00b7U_L \u00d7 (T_in \u2212 T_amb) ]"));
ch.push(table(
  ["Term", "Value / source", "Meaning"],
  [
    ["I_t", "GHI_Wm2, hourly", "Irradiance on the collector plane"],
    ["T_amb", "T_amb_C, hourly", "Ambient air temperature"],
    ["T_in", "from the tank state", "Water entering the collector"],
    ["A_c", "2.5 m\u00b2", "Collector area"],
    ["F_R(\u03c4\u03b1)", "0.75", "Optical efficiency \u00d7 heat-removal factor"],
    ["F_R\u00b7U_L", "4.5 W/m\u00b2K", "Loss coefficient (not wind-dependent)"],
  ],
  [1600, 3000, 5500]));
ch.push(PR([
  { t: "Note the sign structure. ", b: true },
  "Irradiance adds heat; the temperature difference removes it. On a hot afternoon the tank is "
  + "already warm, so ", { t: "T_in \u2212 T_amb", c: true },
  " is large and the collector loses more \u2014 which is why the useful gain is not simply "
  + "proportional to sunshine.",
]));
ch.push(H2("A simplification to be aware of"));
ch.push(PR([
  "The code uses GHI directly as plane-of-array irradiance (",
  { t: "I_t_Wm2 = GHI_Wm2", c: true },
  "). There is no tilt or transposition model, so collector tilt and orientation are not "
  + "represented. For a fixed tilt near the site latitude this under-states winter gain and "
  + "over-states summer gain. It applies identically to the PCM tank and its paired plain-water "
  + "tank, so the ", { t: "difference", i: true },
  " the study reports is largely insulated from it \u2014 but the absolute energy figures carry it.",
]));
ch.push(H2("Pump control"));
ch.push(PR([
  "Irradiance also acts as a switch. Below ", { t: "min_irradiance_cutoff_Wm2 = 10", c: true },
  " the circulation pump is treated as off and no collector loop runs. This is what makes the "
  + "collector follow the daily solar cycle rather than run continuously.",
], { after: 150 }));

/* ─────────────────── 3. where in the code ─────────────────── */
ch.push(H1("3. Where this lives in the code"));
ch.push(table(
  ["What", "File", "Where"],
  [
    ["Weather loaded for a regime/year", "src/weather/roles.py", "load_point_year()"],
    ["Weather handed to a simulation", "src/simulation/run_case.py", "run_case(), weather= argument"],
    ["Collector equation", "src/simulation/collector_model.py", "collector_output_w() line 56"],
    ["Linearised collector (for the implicit solve)", "src/simulation/collector_model.py", "collector_linear_coeffs() line 82"],
    ["Irradiance pump cutoff", "src/simulation/tank_model_multinode.py", "line 624"],
    ["Hourly loop + substepping", "src/simulation/tank_model_multinode.py", "lines 405\u2013440"],
    ["Hourly output record (I_t, T_amb)", "src/simulation/tank_model_multinode.py", "line 727"],
    ["Timestep choice by purpose", "src/io_utils.py", "dt_for() line 95"],
    ["Mains temperature per regime", "src/simulation/run_case.py", "line 66"],
    ["Collector / tank / shield constants", "configs/system_config_shared.yaml", "collector:, tank:, safety_shield:"],
    ["Ephemeris check on the weather", "scripts/tn_rebuild_weather_from_raw.py", "verify_against_ephemeris()"],
  ],
  [4000, 3700, 2400], { mono: 1 }));
ch.push(P(
  "The single-node model (src/simulation/tank_model.py) uses the same collector equation; the "
  + "multi-node model is the one the optimiser actually runs.", { color: MUTED, size: SMALL, after: 150 }));

/* ─────────────────── 4. how values change ─────────────────── */
ch.push(H1("4. How the values change during a run"));
ch.push(P(
  "A simulated year is stepped hour by hour. Within each hour the two climate values are held "
  + "constant \u2014 that is the resolution of the source data \u2014 while the tank state is advanced on a "
  + "much finer internal step."));
ch.push(H2("The stepping scheme"));
ch.push(table(
  ["Level", "Step", "What varies"],
  [
    ["Hour", "8,760 per year", "GHI and T_amb change; demand draw changes"],
    ["Solver step", "150 s searching, 37.5 s confirming", "Tank node temperatures, PCM enthalpy"],
    ["Substep (adaptive)", "up to 6\u00d7 finer inside the melt band", "PCM phase change only"],
  ],
  [2400, 3400, 4300]));
ch.push(PR([
  { t: "The timestep is not fixed \u2014 it refines itself where the physics is stiff. ", b: true },
  "At each step the code checks whether any capsule node is within 2 K of its melt band. If so it "
  + "subdivides that step ", { t: "6\u00d7", c: true },
  ". It also computes a thermal time constant per node (",
  { t: "\u03c4 = m_pcm \u00b7 cp_eff / UA", c: true },
  ") and refines further if the step is long relative to \u03c4, up to a cap. So the model spends its "
  + "effort where the PCM is actually melting and runs coarsely the rest of the time.",
]));
ch.push(PR([
  "Two timesteps are used deliberately: ", { t: "150 s", c: true },
  " while searching the design space, and ", { t: "37.5 s", c: true },
  " for anything reported. The convergence gate is that annual useful energy changes by less than "
  + "0.05 % when the step is halved; on this 100 L tank only 37.5 s meets it (0.041 %), where 150 s "
  + "gives 0.054 %. The coarse step is used for ranking designs, where the discretisation error "
  + "(0.17 % worst case) sits far inside the repeatability band, so it cannot change the ordering.",
]));
ch.push(H2("What makes the numbers rise and fall"));
ch.push(B("Through a day: irradiance rises after sunrise, the pump starts above 10 W/m\u00b2, the tank's top node warms first because the collector return enters high. Draw-offs at the morning and evening demand peaks pull warm water out and push mains water in at the bottom."));
ch.push(B("Through the melt: once a capsule reaches its melt point its temperature nearly stops rising while it absorbs latent heat \u2014 the plateau that makes a PCM worth having. On discharge it releases that heat and holds the tank warmer for longer."));
ch.push(B("Through the year: Tamil Nadu's three regimes differ mainly in annual irradiance (1,791\u20132,074 kWh/m\u00b2) and in mains temperature, which is why each regime gets its own optimised design rather than one shared answer."));
ch.push(H2("A control that responds to temperature"));
ch.push(PR([
  "A safety shield interrupts circulation when the tank gets too hot: it bypasses above ",
  { t: "72 \u00b0C water", c: true }, " or ", { t: "62 \u00b0C PCM", c: true },
  ". This is why peak temperatures in the results cluster below the limits rather than running "
  + "away on the sunniest days \u2014 the model stops charging rather than overheating.",
], { after: 150 }));

/* ─────────────────── 5. live simulation ─────────────────── */
ch.push(H1("5. Is the live simulation working?"));
ch.push(PR([
  { t: "Yes, with one honest qualification. ", b: true },
  "The script ", { t: "ansys/fluent_live_demo.py", c: true },
  " opens ANSYS Fluent with its graphics window and re-renders a liquid-fraction contour as the "
  + "solve advances, so the melt front moves on screen. It reads the optimal design straight from "
  + "the optimiser's output, so what it shows is the selected design and not a demo case.",
]));
ch.push(PR([
  { t: "The qualification: ", b: true },
  "it was verified in headless mode, where it reproduced the trusted batch run exactly (liquid "
  + "fraction 0.0394 at 0.3 h, matching to four decimals). The windowed version has not been "
  + "watched running, because that needs a desktop session. The logic is identical \u2014 only the ",
  { t: "ui_mode", c: true }, " flag differs \u2014 but the statement that the window renders is an "
  + "expectation, not something observed.",
]));
ch.push(P("To run it, from the project root:"));
ch.push(CODEP("cd ansys\npython fluent_live_demo.py                  # regime 0, 6 h, with window\npython fluent_live_demo.py --regime 1\npython fluent_live_demo.py --hours 1         # quick look\npython fluent_live_demo.py --headless        # no window, verify setup"));
ch.push(PR([
  { t: "Before running: ", b: true },
  "the Student licence allows one Fluent session at a time. Close any other Fluent window. A "
  + "launch failure reading ", { t: "Unexpected license problem", c: true },
  " is usually a stray ", { t: "ansyscl.exe", c: true },
  " from an earlier session rather than a real licence fault.",
], { after: 150 }));

/* ─────────────────── 6. checking the images ─────────────────── */
ch.push(H1("6. How to check the tank and capsule images"));
ch.push(P(
  "The three figures in ansys/figures/ are not drawings \u2014 each comes from a solved case, and each "
  + "can be traced back to the numbers behind it. Here is how to verify each one yourself."));

ch.push(H2("Figure 1 \u2014 tank, capsules and collector panel (01_system_mesh_zones.png)"));
ch.push(P("It claims six cell zones over 42,966 cells. Check the mesh directly, without launching Fluent:"));
ch.push(CODEP("python ansys/verify_zones.py \"C:\\fluent_work\\regime0_v3_mesh_only.cas.h5\""));
ch.push(P(
  "It reads the case file's HDF5 structure and prints every cell and face zone with its cell count "
  + "and geometric extent, so you can confirm which zone is the inlet and which the outlet from "
  + "their x-positions rather than trusting a label. This matters: zone names are not guaranteed to "
  + "repeat between separately imported meshes, even when the geometry is identical."));

ch.push(H2("Figure 2 \u2014 temperature field (02_system_temperature_field.png)"));
ch.push(PR([
  "The numbers in its caption (absorber 139 \u00b0C \u2192 panel 125 \u00b0C \u2192 riser 61 \u00b0C \u2192 water 32.2 \u00b0C) "
  + "come from the solved system case. ", { t: "Read this figure as a geometry and heat-path "
  + "check, not as evidence the PCM works.", b: true },
  " Its own caption says why: the case runs energy-only with momentum frozen, so nothing "
  + "circulates, the water only reaches 32 \u00b0C and no PCM melts in it. Melting evidence is Figure 3.",
]));

ch.push(H2("Figure 3 \u2014 PCM melt comparison (03_pcm_melt_comparison.png)"));
ch.push(P("This is the one that carries the physics result. Three independent ways to check it:"));
ch.push(B("Regenerate it: python ansys/plot_v4_pcm_comparison.py re-reads the raw melt histories and redraws the figure. If the curves change, the plot was not matching the data."));
ch.push(B("Read the raw numbers: ansys/v7_<pcm>_melt_history.csv holds time, liquid fraction and capsule temperature for every solver chunk. The final rows should give 0.60 / 0.50 / 0.47 / 0.38 for C25 / C26 / RT57HC / PureTemp 58."));
ch.push(B("Check the solver was clean: grep -c \"Divergence detected\" ansys/v7_*.log should return 0 for all four. A diverged run can still produce a plausible-looking curve."));
ch.push(PR([
  { t: "What makes the result believable ", b: true },
  "is not the picture but the ordering. C25 has the lowest melt point and melts most; C26 and "
  + "RT57HC share a melt point and the higher-conductivity one melts more; PureTemp 58 has the "
  + "highest melt point and lowest conductivity and melts least. Three independent physical "
  + "relationships, all satisfied. A plotting error would be unlikely to preserve all three.",
]));
ch.push(PR([
  { t: "One limit to read with it: ", b: true },
  "the solver uses first-order upwind, which is more diffusive than second order, so these melt "
  + "fractions are conservative. A second-order run of the three PCMs that would converge under it "
  + "reached higher fractions in the same order. First order is used because it is the only setting "
  + "under which all four PCMs solve, and a comparison needs identical settings. Read the ordering, "
  + "not the absolute values.",
]));
ch.push(H2("Opening a case in Fluent yourself"));
ch.push(P("To inspect any solved case interactively, launch Fluent (2D, double precision) and read the case and data together:"));
ch.push(CODEP("File > Read > Case & Data...  \u2192  C:\\fluent_work\\v7_c26.cas.h5"));
ch.push(P(
  "Then Results > Graphics > Contours on Liquid Fraction or Temperature. The full manual route, "
  + "with every panel value, is in ansys/HOW_TO_RUN_ANSYS.md.", { after: 120 }));

ch.push(P(
  "Related: docs/SIMULATOR_AND_CFD.md (why there are two simulators), docs/CFD_VERIFICATION.md "
  + "(the full CFD history), docs/RESULTS.md (the numbers).",
  { italics: true, color: MUTED, size: CAP, after: 0 }));

const doc = new Document({
  creator: "Objective 2 \u2014 Tamil Nadu",
  title: "Climate parameters in the simulators",
  sections: [{
    properties: { page: { margin: { top: 1000, bottom: 900, left: 1000, right: 1000 } } },
    children: ch,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(ROOT, "O2_Climate_Parameters_and_Simulators.docx");
  fs.writeFileSync(out, buf);
  console.log("wrote " + out + "  (" + (buf.length / 1024).toFixed(0) + " KB)");
});
