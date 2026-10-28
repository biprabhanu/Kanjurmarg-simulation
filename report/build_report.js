// Builds the technical report (DOCX + Markdown) from data/*.csv and charts/*.png.
//   node report/build_report.js
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, AlignmentType, HeadingLevel,
  WidthType, ShadingType, BorderStyle, Footer, Header, PageNumber, LevelFormat, PageBreak,
  TabStopType, VerticalAlign,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const DATA = (f) => path.join(ROOT, "data", f);
const CHART = (f) => path.join(ROOT, "charts", f);

// ------------------------------------------------------------------ CSV helpers
function readCsv(file) {
  const lines = fs.readFileSync(file, "utf8").trim().split(/\r?\n/);
  const split = (l) => {
    const out = []; let cur = ""; let q = false;
    for (const ch of l) {
      if (ch === '"') q = !q; else if (ch === "," && !q) { out.push(cur); cur = ""; } else cur += ch;
    }
    out.push(cur); return out;
  };
  const head = split(lines[0]);
  return lines.slice(1).map((l) => { const v = split(l); const o = {}; head.forEach((h, i) => (o[h] = v[i])); return o; });
}
const summary = readCsv(DATA("scenario_summary.csv"));
const unc = readCsv(DATA("route_split_uncertainty.csv"));
const splits = readCsv(DATA("gate_route_splits.csv"));
const alloc = readCsv(DATA("expected_route_allocation.csv"));
const assumptions = readCsv(DATA("assumptions_register.csv"));
const tests = JSON.parse(fs.readFileSync(path.join(ROOT, "build", "test_results.json"), "utf8"));
const f = (v, d = 2) => Number(v).toFixed(d);
const S = (sc, fac) => summary.find((r) => r.scenario === sc && r.facility === fac);

// ------------------------------------------------------------------ style constants
const TEAL = "00A19B", BLUE = "2563EB", RED = "D93025", INK = "1F2933", MUTED = "5F6B7A", LIGHT = "F1F4F7", RULE = "C7CDD4";
const FONT = "Arial";
const CONTENT_W = 9026; // A4 with 1" margins

// Markdown mirror (used for the Google Doc and as a plain-text fallback)
const md = [];

// ------------------------------------------------------------------ block builders
function runs(text, base = {}) {
  // **bold** inline markup (underscores are left alone so file names render correctly)
  const parts = text.split(/(\*\*[^*]+\*\*)/g).filter((p) => p !== "");
  return parts.map((p) => {
    if (p.startsWith("**")) return new TextRun({ text: p.slice(2, -2), bold: true, ...base });
    return new TextRun({ text: p, ...base });
  });
}
const body = [];
let figN = 0, tabN = 0;
let listInstance = 0, lastWasN = false;

function H1(t) {
  lastWasN = false;
  body.push(new Paragraph({ heading: HeadingLevel.HEADING_1, keepNext: true, spacing: { before: 360 }, children: [new TextRun(t)] }));
  md.push(`\n## ${t}\n`);
}
function H2(t) {
  lastWasN = false;
  body.push(new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true, children: [new TextRun(t)] }));
  md.push(`\n### ${t}\n`);
}
function P(t, opts = {}) {
  lastWasN = false;
  body.push(new Paragraph({ children: runs(t), spacing: { after: 120, line: 300 }, alignment: AlignmentType.JUSTIFIED, ...opts }));
  md.push(t + "\n");
}
function B(t, level = 0) {
  lastWasN = false;
  body.push(new Paragraph({ children: runs(t), numbering: { reference: "bullets", level }, spacing: { after: 60, line: 288 } }));
  md.push(`${"  ".repeat(level)}- ${t}`);
}
function N(t) {
  if (!lastWasN) { listInstance++; md.push(""); }
  body.push(new Paragraph({ children: runs(t), numbering: { reference: "numbers", level: 0, instance: listInstance }, spacing: { after: 60, line: 288 } }));
  md.push(`1. ${t}`);
  lastWasN = true;
}
function EQ(t, label) {
  lastWasN = false;
  body.push(new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 100, after: 140 },
    children: [new TextRun({ text: t, italics: true, font: "Cambria Math", size: 23 }),
      ...(label ? [new TextRun({ text: "     (" + label + ")", size: 20, color: MUTED })] : [])],
  }));
  md.push(`\n**${t}**   (${label})\n`);
}
function CALLOUT(title, text, color = TEAL) {
  lastWasN = false;
  body.push(new Paragraph({
    shading: { type: ShadingType.CLEAR, fill: LIGHT, color: "auto" },
    border: { left: { style: BorderStyle.SINGLE, size: 24, color, space: 8 } },
    spacing: { before: 120, after: 160, line: 288 }, indent: { left: 160, right: 160 },
    children: [new TextRun({ text: title + "  ", bold: true, color }), ...runs(text)],
  }));
  md.push(`\n> **${title}** ${text}\n`);
}
function SOURCE(t) {
  body.push(new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: t, italics: true, size: 17, color: MUTED })] }));
  md.push(`*${t}*\n`);
}
function TABLE(caption, headers, rows, widths, opts = {}) {
  lastWasN = false;
  tabN++;
  const total = widths.reduce((a, b) => a + b, 0);
  const scale = CONTENT_W / total;
  const w = widths.map((x) => Math.round(x * scale));
  w[w.length - 1] += CONTENT_W - w.reduce((a, b) => a + b, 0);
  body.push(new Paragraph({ keepNext: true, spacing: { before: 160, after: 80 },
    children: [new TextRun({ text: `Table ${tabN}. `, bold: true, color: INK }), new TextRun({ text: caption, color: INK })] }));
  const border = { style: BorderStyle.SINGLE, size: 4, color: "DCE1E8" };
  const borders = { top: border, bottom: border, left: border, right: border };
  const mkCell = (t, i, header, highlight) => new TableCell({
    width: { size: w[i], type: WidthType.DXA }, borders,
    shading: { type: ShadingType.CLEAR, color: "auto", fill: header ? "1F2933" : highlight ? "E6F6F5" : "FFFFFF" },
    margins: { top: 60, bottom: 60, left: 100, right: 100 }, verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ alignment: i === 0 || opts.leftAll ? AlignmentType.LEFT : AlignmentType.RIGHT,
      children: runs(String(t), { size: 18, color: header ? "FFFFFF" : INK, bold: header ? true : undefined }) })],
  });
  body.push(new Table({
    width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: w,
    rows: [new TableRow({ tableHeader: true, children: headers.map((h, i) => mkCell(h, i, true)) }),
      ...rows.map((r, ri) => new TableRow({ children: r.map((c, i) => mkCell(c, i, false, opts.highlightRows && opts.highlightRows.includes(ri))) }))],
  }));
  md.push(`\n**Table ${tabN}. ${caption}**\n`);
  md.push("| " + headers.join(" | ") + " |");
  md.push("|" + headers.map((_, i) => (i === 0 || opts.leftAll ? "---" : "---:")).join("|") + "|");
  rows.forEach((r) => md.push("| " + r.map((c) => String(c).replace(/\|/g, "/")).join(" | ") + " |"));
  md.push("");
  if (opts.source) SOURCE(opts.source); else body.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
}
function FIG(file, caption, widthIn = 6.3) {
  lastWasN = false;
  figN++;
  const buf = fs.readFileSync(CHART(file));
  const wpx = buf.readUInt32BE(16), hpx = buf.readUInt32BE(20);
  const W = widthIn * 96, H = Math.round((W * hpx) / wpx);
  body.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 60 },
    children: [new ImageRun({ type: "png", data: buf, transformation: { width: W, height: H },
      altText: { title: `Figure ${figN}`, description: caption, name: file } })] }));
  body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
    children: [new TextRun({ text: `Figure ${figN}. `, bold: true, size: 18 }), ...runs(caption, { size: 18, color: MUTED })] }));
  md.push(`\n![Figure ${figN}](../charts/${file})\n\n**Figure ${figN}.** ${caption}\n`);
}

// ==================================================================================================
// TITLE PAGE  (version 3 — revised route splits)
// ==================================================================================================
const titlePage = [
  new Paragraph({ spacing: { before: 1800 }, children: [new TextRun({ text: "IE 301 · OPERATIONAL ANALYSIS OF MULTIMODAL INTERCHANGE HUBS", bold: true, size: 20, color: TEAL, characterSpacing: 40 })] }),
  new Paragraph({ spacing: { before: 240, after: 240 }, border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: TEAL, space: 12 } },
    children: [new TextRun({ text: "Kanjurmarg Station: Stochastic Simulation of Foot Overbridge Utilization Under Increased Passenger Demand", bold: true, size: 48, color: INK, font: FONT })] }),
  new Paragraph({ spacing: { before: 200, after: 120 }, children: [new TextRun({ text: "Technical report — five-gate model, Ghatkopar-referenced demand scenarios, utilization results and limitations", size: 26, color: MUTED })] }),
  new Paragraph({ spacing: { before: 600 }, children: [new TextRun({ text: "Department of Industrial Engineering and Operations Research, IIT Bombay", size: 22, color: INK })] }),
  new Paragraph({ spacing: { before: 60 }, children: [new TextRun({ text: "IE 301 project team  ·  October 2026  ·  Version 3 (revised route splits)", size: 22, color: INK })] }),
  new Paragraph({ spacing: { before: 900 }, children: [] }),
];
md.push("# Kanjurmarg Station: Stochastic Simulation of Foot Overbridge Utilization Under Increased Passenger Demand\n");
md.push("*IE 301 · Operational Analysis of Multimodal Interchange Hubs — Technical report · Department of IEOR, IIT Bombay · October 2026 · Version 3 (revised route splits)*\n");

const b2 = S("Baseline", "FOB 2"), b3 = S("Baseline", "FOB 3"), p2 = S("+50 pax/min", "FOB 2"), p3 = S("+50 pax/min", "FOB 3"), q2 = S("+100 pax/min", "FOB 2"), q3 = S("+100 pax/min", "FOB 3");
const U = (sc, fac) => unc.find((r) => r.scenario === sc && r.facility === fac);
const OBS2 = 70.0 / 321.6 * 100, OBS3 = 33.3 / 360 * 100;
const kpis = [
  ["FOB 2 baseline utilization", `${f(b2.mean_util_pct, 1)}%`, `→ ${f(q2.mean_util_pct, 1)}% with +100 pax/min`, TEAL],
  ["FOB 3 baseline utilization", `${f(b3.mean_util_pct, 1)}%`, `→ ${f(q3.mean_util_pct, 1)}% with +100 pax/min`, BLUE],
  ["Busiest simulated minute", `${f(q2.max_util_pct_overall, 1)}%`, "FOB 2, +100 pax/min (of reference capacity)", INK],
];
const keyBox = new Table({
  width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [3008, 3009, 3009],
  rows: [new TableRow({ children: kpis.map(([a, b, c, col]) => new TableCell({
    width: { size: 3008, type: WidthType.DXA },
    borders: { top: { style: BorderStyle.SINGLE, size: 18, color: col }, bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" }, left: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" }, right: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" } },
    shading: { type: ShadingType.CLEAR, color: "auto", fill: LIGHT }, margins: { top: 120, bottom: 120, left: 140, right: 140 },
    children: [new Paragraph({ children: [new TextRun({ text: a, size: 16, color: MUTED, bold: true })] }),
      new Paragraph({ spacing: { before: 60 }, children: [new TextRun({ text: b, size: 44, bold: true, color: col })] }),
      new Paragraph({ children: [new TextRun({ text: c, size: 16, color: MUTED })] })],
  })) })],
});
md.push("| Key result | Value | Note |\n|---|---:|---|");
kpis.forEach(([a, b, c]) => md.push(`| ${a} | **${b}** | ${c} |`));
md.push("");
titlePage.push(keyBox);
const titleNote = "Utilization = one-minute FOB crossings ÷ reference capacity (W × 60 pax/m/min); mean of 30 stochastic replications. Gate route splits are modelling estimates (with random noise), the East-side split and the 500 pax/min Ghatkopar reference are assumptions, and the +50/+100 pax/min scenarios are input rates, not ridership forecasts. Simplified conceptual layout — not to scale.";
titlePage.push(new Paragraph({ spacing: { before: 300 }, children: [new TextRun({ text: titleNote, size: 17, italics: true, color: MUTED })] }));
md.push(`*${titleNote}*\n`);
titlePage.push(new Paragraph({ children: [new PageBreak()] }));
titlePage.push(new Paragraph({ children: [new TextRun({ text: "Contents", bold: true, size: 32, color: INK })], spacing: { after: 200 } }));
["1. Executive Summary", "2. Problem Definition and Objectives", "3. Scope and Simplified Station Layout", "4. Observed Data and Input Parameters", "5. Gate Route-Choice Assumptions", "6. Ghatkopar-Referenced Demand Scenarios", "7. Stochastic Arrival and Route-Choice Model", "8. Capacity and Utilization Calculations", "9. AnyLogic Implementation", "10. Experimental Design", "11. Simulation Results", "12. Interpretation", "13. Assumptions, Limitations, and Additional Data Required", "14. Conclusion", "15. Reproducibility Appendix"].forEach((t) =>
  titlePage.push(new Paragraph({ spacing: { after: 90 }, border: { bottom: { style: BorderStyle.DOTTED, size: 4, color: "DCE1E8", space: 4 } }, children: [new TextRun({ text: t, size: 22, color: INK })] })));
titlePage.push(new Paragraph({ children: [new PageBreak()] }));

// ==================================================================================================
// 1. EXECUTIVE SUMMARY
// ==================================================================================================
H1("1. Executive Summary");
P("A stochastic AnyLogic model estimates FOB 2 and FOB 3 utilization at Kanjurmarg for three scenarios: baseline, **+50** and **+100 pax/min** of extra entering demand (10% and 20% of an assumed 500 pax/min Ghatkopar flow; 80% via Huma, 20% via Gandhi Nagar). Five gates, FOB 1 closed, Poisson arrivals, gate route splits with ±3 pp noise, 30 replications × 60 min.");
TABLE("Mean one-minute utilization (% of reference capacity, ± 95% CI).", ["Scenario", "FOB 2", "FOB 3"], [
  ["Baseline", `${f(b2.mean_util_pct, 1)} ± ${f(b2.mean_util_ci95_halfwidth, 1)}`, `${f(b3.mean_util_pct, 1)} ± ${f(b3.mean_util_ci95_halfwidth, 1)}`],
  ["+50 pax/min", `${f(p2.mean_util_pct, 1)} ± ${f(p2.mean_util_ci95_halfwidth, 1)}`, `${f(p3.mean_util_pct, 1)} ± ${f(p3.mean_util_ci95_halfwidth, 1)}`],
  ["+100 pax/min", `${f(q2.mean_util_pct, 1)} ± ${f(q2.mean_util_ci95_halfwidth, 1)}`, `${f(q3.mean_util_pct, 1)} ± ${f(q3.mean_util_ci95_halfwidth, 1)}`],
], [1.5, 1, 1]);
B(`FOB 2 is about twice as loaded as FOB 3 in every scenario. +100 pax/min adds about ${f(q2.change_vs_baseline_mean_util_pct, 0)} points on FOB 2 and ${f(q3.change_vs_baseline_mean_util_pct, 0)} on FOB 3.`);
B(`Busiest single minute in any run: ${f(q2.max_util_pct_overall, 1)}% (FOB 2, +100 pax/min). Both bridges stay below reference capacity.`);
B(`Expected baseline flows from the assumed splits (${f(b2.expected_flow_pax_per_min, 1)} and ${f(b3.expected_flow_pax_per_min, 1)} pax/min) are close to the observed 70.0 and 33.3 pax/min. This is a consistency check, not validation.`);

// ==================================================================================================
// 2. PROBLEM
// ==================================================================================================
H1("2. Problem Definition and Objectives");
P("Kanjurmarg is expected to become an interchange with Metro Lines 4 and 6. With FOB 1 closed, bridge movement relies on FOB 2 and FOB 3. Questions:");
N("How is gate demand split between direct PF1/PF1A, FOB 2, FOB 3 and the skywalk?");
N("What are baseline FOB 2 and FOB 3 utilizations?");
N("What changes with +50 and +100 pax/min?");
N("How variable are the results?");
N("How do estimated FOB flows compare with observed counts?");
N("Does extra demand change the FOB 2 / FOB 3 balance?");
CALLOUT("Scope note.", "+50 and +100 pax/min are scenario inputs, not ridership forecasts.", BLUE);

// ==================================================================================================
// 3. SCOPE
// ==================================================================================================
H1("3. Scope and Simplified Station Layout");
P("West side (north → south): Naval Colony gate, FOB 2, Huma gate, FOB 3, Gandhi Nagar gate. FOB 1 is closed. An east-side **skywalk connects FOB 2 and FOB 3** (connector, not an FOB) with Northeast and Southeast exits.");
FIG("fig1_station_layout.png", "Simplified layout in the AnyLogic model (not to scale). Red = entering, blue = leaving.", 5.4);
TABLE("Model scope.", ["Included", "Excluded"], [
  ["Five gates, entering and leaving streams + 2 extra-demand streams", "Ticketing, buses, autos, metro operations"],
  ["Routes: direct PF1/PF1A, FOB 2, FOB 3, skywalk → FOB 3", "Stair/escalator capacity, density, queuing"],
  ["FOB 2 and FOB 3 one-minute utilization", "Skywalk utilization (not an FOB)"],
], [1, 1], { leftAll: true });

// ==================================================================================================
// 4. OBSERVED DATA
// ==================================================================================================
H1("4. Observed Data and Input Parameters");
TABLE("Baseline gate demand (pax/min).", ["Gate", "Entering", "Leaving", "Total", "Status"], [
  ["Naval Colony", "10.00", "42.00", "52.00", "Observed"], ["Huma", "27.20", "50.00", "77.20", "Observed"],
  ["Gandhi Nagar", "33.33", "6.66", "39.99", "Observed"],
  ["Northeast", "10.00", "5.00", "15.00", "**Assumed: 50% of East-side count**"], ["Southeast", "10.00", "5.00", "15.00", "**Assumed: 50% of East-side count**"],
  ["**Total**", "**90.53**", "**108.66**", "**199.19**", ""],
], [1.4, 0.9, 0.9, 0.9, 2], { source: "Source: IE 301 project report, Section 2.2." });
TABLE("Observed FOB flows and widths (benchmark only).", ["Facility", "Observed flow (pax/min)", "Width (m)", "Width status"], [
  ["FOB 1", "Closed", "–", "Not in use"], ["FOB 2", "70.0", "5.36", "Recorded; to be verified"],
  ["FOB 3", "33.3", "6.0", "**Unverified**"],
], [1.1, 1.3, 0.8, 2.6], { source: "Source: project report Sections 2.3 and 4.6." });

// ==================================================================================================
// 5. GATE ROUTE-CHOICE ASSUMPTIONS
// ==================================================================================================
H1("5. Gate Route-Choice Assumptions");
P("Route splits are **modelling assumptions, not measured choices**. The same split applies to entering and leaving passengers at a gate.");
TABLE("Route-choice probabilities by gate.", ["Gate", "Direct PF1/PF1A", "Via FOB 2", "Via FOB 3", "Skywalk → FOB 3"],
  splits.map((r) => [r.gate, `${f(100 * r.direct_pf1_pf1a, 0)}%`, `${f(100 * r.via_fob2, 0)}%`, `${f(100 * r.via_fob3, 0)}%`, `${f(100 * r.skywalk_then_fob3, 0)}%`]),
  [2.2, 1.1, 0.9, 0.9, 1.1], { source: "Last two rows apply to the additional demand only. Skywalk users are counted on FOB 3." });
H2("5.1 Route-split noise");
P("Each replication draws each gate's split from a Dirichlet distribution around these values (κ = 99, about ±3 pp for a 10–15% share). Zero shares stay zero.");
EQ("(p_PF1, p_FOB2, p_FOB3, p_sky) ~ Dirichlet(κ · p̄),   κ = 99", "5.1");
H2("5.2 Expected flows vs observed counts");
TABLE("Expected baseline flows (no randomness) vs observed.", ["Facility", "Expected (pax/min)", "Expected U", "Observed (pax/min)", "Observed U"], [
  ["FOB 2", f(b2.expected_flow_pax_per_min, 1), `${f(b2.expected_util_pct, 1)}%`, "70.0", `${f(OBS2, 1)}%`],
  ["FOB 3", f(b3.expected_flow_pax_per_min, 1), `${f(b3.expected_util_pct, 1)}%`, "33.3", `${f(OBS3, 1)}%`],
], [1, 1.2, 1, 1.2, 1], { source: "FOB 2 = 13.0 + 23.2 + 14.0 + 14.25 + 4.5; FOB 3 = 7.8 + 11.6 + 2.0 + 10.5 + 0.75 (skywalk)." });
CALLOUT("Not validation.", "The splits were chosen as estimates; their agreement with observed counts is a consistency check only.", RED);

// ==================================================================================================
// 6. DEMAND SCENARIOS
// ==================================================================================================
H1("6. Ghatkopar-Referenced Demand Scenarios");
EQ("+50 pax/min = 500 × 0.10,     +100 pax/min = 500 × 0.20", "6.1");
TABLE("Additional entering demand by gate (pax/min).", ["Scenario", "Huma (80%)", "Gandhi Nagar (20%)", "Total"], [
  ["Baseline", "0", "0", "0"], ["+50 pax/min", "+40", "+10", "+50"], ["+100 pax/min", "+80", "+20", "+100"],
], [1.4, 1, 1.2, 0.8], { source: "500 pax/min Ghatkopar flow is assumed. Baseline rates are unchanged." });
const ea = (sc, route) => Number(alloc.find((r) => r.scenario === sc && r.route === route).additional_vs_baseline);
TABLE("Expected routing of the additional demand (pax/min).", ["Route", "+50 pax/min", "+100 pax/min"], [
  ["Direct PF1/PF1A", `+${f(ea("+50 pax/min", "Direct PF1/PF1A"), 0)}`, `+${f(ea("+100 pax/min", "Direct PF1/PF1A"), 0)}`],
  ["FOB 2", `+${f(ea("+50 pax/min", "FOB 2"), 0)}`, `+${f(ea("+100 pax/min", "FOB 2"), 0)}`],
  ["FOB 3", `+${f(ea("+50 pax/min", "FOB 3"), 0)}`, `+${f(ea("+100 pax/min", "FOB 3"), 0)}`],
], [2, 1, 1], { source: "Huma extra × (50/35/15); Gandhi Nagar extra × (40/40/20)." });

// ==================================================================================================
// 7. STOCHASTIC MODEL
// ==================================================================================================
H1("7. Stochastic Arrival and Route-Choice Model");
TABLE("Distributions.", ["Element", "Distribution", "Parameters"], [
  ["Arrivals (12 streams)", "Poisson process", "λ = gate rate; extra streams 0.8·Δ and 0.2·Δ"],
  ["Inter-arrival time", "Exponential", "Mean 60/λ s"],
  ["Gate split per replication", "Dirichlet", "κ = 99"],
  ["Route per passenger", "Categorical (inverse CDF)", "That replication's split"],
  ["Walking speed", "Deterministic", "1.30 m/s"],
], [1.6, 1.6, 2.2], { leftAll: true });
EQ("Δt = −ln(1 − U) · 60/λ,   U ~ Uniform(0, 1)", "7.1");
P("A crossing is counted once, in the minute the passenger reaches the deck mid-point. 95% CI over n = 30: x̄ ± 2.045 · s/√30. Seeds 1001–1030 are reused in every scenario (common random numbers). Empty start, no warm-up.");

// ==================================================================================================
// 8. CAPACITY
// ==================================================================================================
H1("8. Capacity and Utilization Calculations");
EQ("C = W × 60 pax/m/min,     U = Q / C × 100%", "8.1");
TABLE("Reference capacities.", ["Facility", "W (m)", "C (pax/min)"], [["FOB 2", "5.36", "321.6"], ["FOB 3", "6.0 (unverified)", "360.0"]], [1, 1, 1]);
CALLOUT("Limit.", "U is a reference-capacity ratio, not a level-of-service or safety measure; stairs, counter-flow and platoons are not modelled.", RED);

// ==================================================================================================
// 9. ANYLOGIC
// ==================================================================================================
H1("9. AnyLogic Implementation");
TABLE("Model structure (Kanjurmarg_FOB_Simulation.alp, AnyLogic 8.8).", ["Element", "Role"], [
  ["Arrival(stream)", "Poisson arrival, route choice, new passenger"],
  ["Waypoint / Crossing", "Move passengers; count FOB crossings per minute"],
  ["minuteTick (60 s)", "Utilization, gauges, deck colours, time plot"],
  ["runBatch()", "30 replications × 3 scenarios; results to console and CSV"],
  ["gateSplits, extraSplits, splitNoiseKappa", "Editable route splits and noise"],
], [2, 3], { leftAll: true });
P("Screen: station layout (decks coloured by live utilization), FOB 2 and FOB 3 utilization gauges (now, mean, peak) and a utilization-over-time plot.");
CALLOUT("Verification.", "Model code compiles against AnyLogic API stand-ins; its headless run reproduced replication 1 exactly (4,157 FOB 2 and 2,058 FOB 3 crossings). Opening in AnyLogic itself is still to be confirmed.", BLUE);

// ==================================================================================================
// 10. EXPERIMENTAL DESIGN
// ==================================================================================================
H1("10. Experimental Design");
TABLE("Experiments.", ["Factor", "Setting"], [
  ["Scenarios", "Baseline, +50, +100 pax/min"],
  ["Runs", "60 min × 30 replications per scenario, seeds 1001–1030"],
  ["Route-split noise", "On (κ = 99); a fixed-split set (κ = 0) is used only to size its effect"],
], [1.5, 4], { leftAll: true });

// ==================================================================================================
// 11. RESULTS
// ==================================================================================================
H1("11. Simulation Results");
const resRows = [];
for (const sc of ["Baseline", "+50 pax/min", "+100 pax/min"]) for (const fac of ["FOB 2", "FOB 3"]) {
  const r = S(sc, fac);
  resRows.push([sc, fac, `${f(r.mean_util_pct, 1)} ± ${f(r.mean_util_ci95_halfwidth, 1)}`, f(r.p95_util_pct_mean_of_reps, 1), f(r.max_util_pct_overall, 1)]);
}
TABLE("One-minute utilization (%), 30 replications.", ["Scenario", "FOB", "Mean ± 95% CI", "P95 minute", "Busiest minute"],
  resRows, [1.3, 0.8, 1.3, 1.1, 1.1], { source: "Source: data/scenario_summary.csv." });
FIG("fig2_fob_comparison.png", "FOB 2 vs FOB 3 mean utilization by scenario.", 6.0);
FIG("fig3_utilization_timeseries.png", "Utilization over the hour, baseline vs +100 pax/min (band = 5th–95th percentile).", 6.3);
P(`About ${f(U("+100 pax/min", "FOB 2").variance_share_from_split_noise_pct, 0)}–${f(U("Baseline", "FOB 3").variance_share_from_split_noise_pct, 0)}% of the replication-to-replication variance comes from route-split noise rather than random arrivals.`);

// ==================================================================================================
// 12. INTERPRETATION
// ==================================================================================================
H1("12. Interpretation");
const af = (route, sc = "Baseline") => Number(alloc.find((r) => r.scenario === sc && r.route === route).expected_flow_pax_per_min);
const totBase = af("Direct PF1/PF1A") + af("FOB 2") + af("FOB 3") + af("Skywalk then FOB 3");
const sh2 = (a, b) => f(100 * Number(a.mean_flow_pax_per_min) / (Number(a.mean_flow_pax_per_min) + Number(b.mean_flow_pax_per_min)), 0);
N(`**Demand split:** ${f(100 * af("Direct PF1/PF1A") / totBase, 0)}% direct PF1/PF1A, ${f(100 * af("FOB 2") / totBase, 0)}% FOB 2, ${f(100 * af("FOB 3") / totBase, 0)}% FOB 3, ${f(100 * af("Skywalk then FOB 3") / totBase, 1)}% skywalk.`);
N(`**Baseline:** FOB 2 ${f(b2.mean_util_pct, 1)}%, FOB 3 ${f(b3.mean_util_pct, 1)}%.`);
N(`**Extra demand:** +${f(p2.change_vs_baseline_mean_util_pct, 1)} / +${f(q2.change_vs_baseline_mean_util_pct, 1)} points on FOB 2 and +${f(p3.change_vs_baseline_mean_util_pct, 1)} / +${f(q3.change_vs_baseline_mean_util_pct, 1)} on FOB 3 for +50 / +100 pax/min.`);
N(`**Variability:** busiest minutes are about ${f(100 * (b2.max_util_pct_mean_of_reps / b2.mean_util_pct - 1), 0)}% (FOB 2) and ${f(100 * (b3.max_util_pct_mean_of_reps / b3.mean_util_pct - 1), 0)}% (FOB 3) above the hourly mean.`);
N(`**Observed counts:** simulated baseline (${f(b2.mean_util_pct, 1)}%, ${f(b3.mean_util_pct, 1)}%) is close to observed (${f(OBS2, 1)}%, ${f(OBS3, 1)}%) — a consistency check, not validation.`);
N(`**Balance:** FOB 2 carries ${sh2(b2, b3)}% of FOB flow at baseline and ${sh2(q2, q3)}% at +100 pax/min.`);
CALLOUT("Implication.", "Deck width is not binding even at +100 pax/min; FOB 2 is the bridge to watch. Measured route-choice data would sharpen every result.");

// ==================================================================================================
// 13. ASSUMPTIONS
// ==================================================================================================
H1("13. Assumptions, Limitations, and Additional Data Required");
B("East-side counts split 50/50 between Northeast and Southeast.");
B("Gate and additional-demand route splits are assumptions, not measurements.");
B("500 pax/min Ghatkopar flow is assumed; +50/+100 are scenario inputs, not forecasts.");
B("FOB 3 width (6.0 m) is unverified; FOB 2 width (5.36 m) to be confirmed.");
B("Poisson arrivals ignore train-release platoons, so peak minutes are likely understated.");
TABLE("Assumptions register.", ["ID", "Assumption", "Value", "Evidence status"],
  assumptions.map((a) => [a.id, a.assumption, a.value, a.evidence_status]), [0.4, 1.5, 2.2, 1.4], { leftAll: true, source: "Full register: data/assumptions_register.csv." });
P("**Data needed:** gate-to-route counts; separate Northeast/Southeast counts; synchronised gate and FOB counts; verified clear widths; one-minute profiles with train times; a verified Ghatkopar source.");

// ==================================================================================================
// 14. CONCLUSION
// ==================================================================================================
H1("14. Conclusion");
P(`Under the stated assumptions, FOB 2 runs at about ${f(b2.mean_util_pct, 0)}% and FOB 3 at about ${f(b3.mean_util_pct, 0)}% of reference capacity at baseline, rising to about ${f(q2.mean_util_pct, 0)}% and ${f(q3.mean_util_pct, 0)}% with +100 pax/min. FOB 2 remains the more loaded bridge. Measured route-choice data are the key next step.`);

// ==================================================================================================
// 15. APPENDIX
// ==================================================================================================
H1("15. Reproducibility Appendix");
H2("15.1 Deliverables");
TABLE("Project files (folder kanjurmarg_fob_simulation/).", ["Path", "Content"], [
  ["anylogic/Kanjurmarg_FOB_Simulation/Kanjurmarg_FOB_Simulation.alp", "Native AnyLogic 8.8 project"],
  ["engine/FobEngine.java", "Stochastic core (embedded verbatim in the .alp)"],
  ["engine/RunnerMain.java, scripts/run_engine.sh", "Stand-alone batch runner"],
  ["python/fob_twin.py", "Independent Python re-implementation (cross-check)"],
  ["python/analyze.py, python/make_charts.py", "CSV export, verification checks, utilization charts"],
  ["scripts/build_alp.py, check_alp_code.py, render_preview.py", "Model generator, model-code check, screen preview"],
  ["data/*.csv", "observed_data, gate_route_splits, expected_route_allocation, scenario_summary, fob_time_series, replication_results, route_split_uncertainty, assumptions_register"],
  ["charts/*.png", "All figures in this report"], ["README.md, VALIDATION.md", "Instructions and verification record"],
], [2.6, 2.4], { leftAll: true });
H2("15.2 Reproducing the results");
md.push("```");
["scripts/run_engine.sh 30 60 1.30 1001 99      # replications, minutes, walk speed, base seed, noise kappa",
  "python3 python/analyze.py                      # CSVs + verification checks",
  "python3 python/make_charts.py                  # utilization figures",
  "python3 scripts/build_alp.py && python3 scripts/check_alp_code.py"].forEach((c) => {
  body.push(new Paragraph({ shading: { type: ShadingType.CLEAR, fill: "F1F4F7", color: "auto" }, spacing: { after: 0 },
    children: [new TextRun({ text: c, font: "Courier New", size: 17 })] }));
  md.push(c);
});
md.push("```\n");
body.push(new Paragraph({ spacing: { after: 160 }, children: [] }));
P("In AnyLogic: open the .alp from a folder AnyLogic can read (on macOS not Downloads, unless AnyLogic is allowed access), run the Simulation experiment, choose a scenario and press Run. 'Run replications' runs 30 seeds × 3 scenarios inside AnyLogic and reproduces data/scenario_summary.csv; output goes to anylogic_batch_results.csv in the model folder.");
H2("15.3 Verification summary");
TABLE("Automated checks.", ["Check", "Result"],
  tests.map((t) => [t.test, (t.passed ? "PASS — " : "FAIL — ") + t.detail.slice(0, 150) + (t.detail.length > 150 ? "…" : "")]).concat([
    ["Java engine vs Python twin, all 180 replications", "PASS — 0 mismatches in arrivals, route counts, noisy splits and per-minute crossings"],
    ["Model code compile (scripts/check_alp_code.py)", "PASS — all functions, events and 14 dynamic expressions compile against AnyLogic API stand-ins"],
    ["Model event logic executed headless", "PASS — identical to batch replication 1 (seed 1001); in-model replications reproduce scenario_summary.csv"],
    ["Opened and run in AnyLogic 8.8", "NOT YET CONFIRMED — to be checked on the user's computer"],
  ]), [2, 3], { leftAll: true });
H2("15.4 Software");
P("Java (OpenJDK 21), Python 3.13 with NumPy 2.5, pandas 3.0, SciPy 1.18 and Matplotlib 3.11. Target: AnyLogic 8.8 (Personal Learning Edition compatible; no paid libraries).");

// ==================================================================================================
// DOCUMENT
// ==================================================================================================
const footer = new Footer({ children: [new Paragraph({
  border: { top: { style: BorderStyle.SINGLE, size: 4, color: RULE, space: 6 } },
  tabStops: [{ type: TabStopType.RIGHT, position: CONTENT_W }],
  children: [new TextRun({ text: "Kanjurmarg FOB Utilization — IE 301 Technical Report", size: 16, color: MUTED }),
    new TextRun({ children: ["\tPage ", PageNumber.CURRENT, " of ", PageNumber.TOTAL_PAGES], size: 16, color: MUTED })],
})] });
const header = new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
  children: [new TextRun({ text: "Simplified conceptual model · demand scenarios are hypothetical", size: 15, color: MUTED, italics: true })] })] });

const doc = new Document({
  creator: "IE 301 project team", title: "Kanjurmarg Station: Stochastic Simulation of Foot Overbridge Utilization Under Increased Passenger Demand",
  styles: {
    default: { document: { run: { font: FONT, size: 21, color: INK } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 34, bold: true, font: FONT, color: INK }, paragraph: { spacing: { before: 120, after: 220 }, outlineLevel: 0,
          border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: TEAL, space: 6 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 25, bold: true, font: FONT, color: "0B7F7A" }, paragraph: { spacing: { before: 260, after: 120 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } },
      { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1080, hanging: 270 } } } }] },
    { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] },
  ] },
  sections: [
    { properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } }, titlePage: true },
      footers: { default: footer, first: new Footer({ children: [new Paragraph({ children: [] })] }) },
      headers: { default: header, first: new Header({ children: [new Paragraph({ children: [] })] }) },
      children: [...titlePage, ...body] },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(ROOT, "report", "Kanjurmarg_FOB_Simulation_Report.docx");
  fs.writeFileSync(out, buf);
  const mdText = md.join("\n");
  fs.writeFileSync(path.join(ROOT, "report", "Kanjurmarg_FOB_Simulation_Report.md"), mdText);
  // Google-Docs source: same text, figure images replaced by a pointer (images are in the DOCX/PDF)
  const gdoc = mdText.replace(/\n!\[Figure (\d+)\]\([^)]*\)\n\n\*\*Figure \d+\.\*\* ([^\n]*)/g,
    (m, n, cap) => `\n**Figure ${n}.** ${cap} *(Image in the PDF/Word version and the charts folder.)*`);
  fs.writeFileSync(path.join(ROOT, "report", "gdoc_source.md"), gdoc);
  console.log("wrote", out, buf.length, "bytes;", figN, "figures,", tabN, "tables; md", mdText.length, "chars");
});
