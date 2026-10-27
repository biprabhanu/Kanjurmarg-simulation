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
const sens = readCsv(DATA("route_sensitivity.csv"));
const assumptions = readCsv(DATA("assumptions_register.csv"));
const tests = JSON.parse(fs.readFileSync(path.join(ROOT, "build", "test_results.json"), "utf8"));
const f = (v, d = 2) => Number(v).toFixed(d);
const S = (sc, fac) => summary.find((r) => r.scenario === sc && r.facility === fac);
const SE = (rs, sc) => sens.find((r) => r.route_set === rs && r.scenario === sc);

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
  body.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: body.length > 0, children: [new TextRun(t)] }));
  md.push(`\n## ${t}\n`);
}
function H2(t) {
  lastWasN = false;
  body.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] }));
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
// TITLE PAGE
// ==================================================================================================
const titlePage = [
  new Paragraph({ spacing: { before: 1800 }, children: [new TextRun({ text: "IE 301 · OPERATIONAL ANALYSIS OF MULTIMODAL INTERCHANGE HUBS", bold: true, size: 20, color: TEAL, characterSpacing: 40 })] }),
  new Paragraph({ spacing: { before: 240, after: 240 }, border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: TEAL, space: 12 } },
    children: [new TextRun({ text: "Kanjurmarg Station: Stochastic Simulation of Foot Overbridge Utilization Under Increased Passenger Demand", bold: true, size: 48, color: INK, font: FONT })] }),
  new Paragraph({ spacing: { before: 200, after: 120 }, children: [new TextRun({ text: "Technical report — model, experiments, results and limitations", size: 26, color: MUTED })] }),
  new Paragraph({ spacing: { before: 600 }, children: [new TextRun({ text: "Department of Industrial Engineering and Operations Research, IIT Bombay", size: 22, color: INK })] }),
  new Paragraph({ spacing: { before: 60 }, children: [new TextRun({ text: "IE 301 project team  ·  October 2026", size: 22, color: INK })] }),
  new Paragraph({ spacing: { before: 900 }, children: [] }),
];
md.push("# Kanjurmarg Station: Stochastic Simulation of Foot Overbridge Utilization Under Increased Passenger Demand\n");
md.push("*IE 301 · Operational Analysis of Multimodal Interchange Hubs — Technical report · Department of IEOR, IIT Bombay · October 2026*\n");

const b2 = S("Baseline", "FOB 2"), b3 = S("Baseline", "FOB 3"), q2 = S("+20%", "FOB 2"), q3 = S("+20%", "FOB 3"), p2 = S("+10%", "FOB 2"), p3 = S("+10%", "FOB 3");
const kpis = [
  ["FOB 2 baseline utilization", `${f(b2.mean_util_pct, 1)}%`, `→ ${f(q2.mean_util_pct, 1)}% at +20% demand`, TEAL],
  ["FOB 3 baseline utilization", `${f(b3.mean_util_pct, 1)}%`, `→ ${f(q3.mean_util_pct, 1)}% at +20% demand`, BLUE],
  ["Highest simulated minute", `${f(q2.max_util_pct_overall, 1)}%`, "FOB 2, +20% demand (of reference capacity)", INK],
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
const titleNote = "Utilization = one-minute FOB crossings ÷ reference capacity (W × 60 pax/m/min). Mean of 30 stochastic replications per scenario. Demand increases are hypothetical scenarios, not ridership forecasts. Station layout is a simplified conceptual representation — not to scale.";
titlePage.push(new Paragraph({ spacing: { before: 300 }, children: [new TextRun({ text: titleNote, size: 17, italics: true, color: MUTED })] }));
md.push(`*${titleNote}*\n`);
titlePage.push(new Paragraph({ children: [new PageBreak()] }));
titlePage.push(new Paragraph({ children: [new TextRun({ text: "Contents", bold: true, size: 32, color: INK })], spacing: { after: 200 } }));
["1. Executive Summary", "2. Problem Definition and Objectives", "3. Scope and Simplified Station Layout", "4. Observed Data and Input Parameters", "5. Aggregate-Calibrated Route Distribution", "6. Stochastic Arrival and Route-Choice Model", "7. Capacity and Utilization Calculations", "8. AnyLogic Implementation", "9. Experimental Design", "10. Simulation Results", "11. Route Sensitivity Analysis", "12. Interpretation and Operational Implications", "13. Assumptions, Limitations, and Additional Data Required", "14. Conclusion", "15. Reproducibility Appendix"].forEach((t) =>
  titlePage.push(new Paragraph({ spacing: { after: 90 }, border: { bottom: { style: BorderStyle.DOTTED, size: 4, color: "DCE1E8", space: 4 } }, children: [new TextRun({ text: t, size: 22, color: INK })] })));
titlePage.push(new Paragraph({ children: [new PageBreak()] }));

// ==================================================================================================
// 1. EXECUTIVE SUMMARY
// ==================================================================================================
H1("1. Executive Summary");
P(`This report builds and analyses a stochastic simulation of how peak-period passengers at Kanjurmarg railway station reach the platforms through three west-side entrances (Naval Colony, Huma and Gandhi Nagar) using one of three routes: direct level access to PF1, foot overbridge (FOB) 2, or FOB 3. FOB 1 is closed and is never available. The model was used to test baseline demand and hypothetical demand increases of 10% and 20%, motivated by possible future metro integration.`);
P(`Passenger arrivals are modelled as six independent Poisson processes (three entrances × entering/leaving) at the rates observed by the project team. Each passenger then chooses a route at random using an **aggregate-calibrated split**: 38.944% direct PF1, 41.374% FOB 2 and 19.682% FOB 3. These shares were derived from the observed flows, so reproducing the observed FOB flows is **calibration, not independent validation**. Thirty independent replications of a 60-minute peak period were run for each scenario.`);
P("**Principal findings**");
B(`**Baseline loading is low relative to the reference capacity.** FOB 2 carries ${f(b2.mean_flow_pax_per_min)} ± ${f(b2.flow_ci95_halfwidth)} pax/min (mean one-minute utilization ${f(b2.mean_util_pct, 1)}%) and FOB 3 carries ${f(b3.mean_flow_pax_per_min)} ± ${f(b3.flow_ci95_halfwidth)} pax/min (${f(b3.mean_util_pct, 1)}%), 95% confidence intervals.`);
B(`**Demand growth raises utilization proportionally.** At +10% demand the means are ${f(p2.mean_util_pct, 1)}% (FOB 2) and ${f(p3.mean_util_pct, 1)}% (FOB 3); at +20% they are ${f(q2.mean_util_pct, 1)}% and ${f(q3.mean_util_pct, 1)}%. The 95th-percentile minute on FOB 2 rises from ${f(b2.p95_util_pct_mean_of_reps, 1)}% to ${f(q2.p95_util_pct_mean_of_reps, 1)}%, and the single busiest simulated minute across all runs reaches ${f(q2.max_util_pct_overall, 1)}%.`);
B(`**Minute-to-minute randomness matters more than replication-to-replication randomness.** Within a run, one-minute FOB 2 utilization varies with a standard deviation of about ${f(b2.within_rep_sd_util_pct, 1)} percentage points, while the hourly mean varies between replications by only ±${f(b2.mean_util_ci95_halfwidth, 2)} points (95% CI).`);
B(`**The relative loading of the two FOBs does not change with demand in this model.** FOB 2 carries ${f(SE("calibrated", "Baseline").fob2_share_of_fob_flow_pct, 1)}% of the combined FOB flow in every scenario (≈ ${f(SE("calibrated", "Baseline").fob2_to_fob3_ratio, 2)} times FOB 3). This is a direct consequence of holding route probabilities fixed; the absolute gap between the two FOBs widens from ${f(SE("calibrated", "Baseline").util_gap_fob2_minus_fob3_pct, 1)} to ${f(SE("calibrated", "+20%").util_gap_fob2_minus_fob3_pct, 1)} percentage points.`);
B(`**Conclusions about the FOB balance depend strongly on the route split, but conclusions about adequacy do not.** Under an equal one-third split FOB 2 and FOB 3 are nearly balanced (${f(SE("equal_split", "Baseline").fob2_mean_util_pct, 1)}% vs ${f(SE("equal_split", "Baseline").fob3_mean_util_pct, 1)}%); if fewer passengers use direct PF1 access (Alt B), FOB 2 rises to ${f(SE("alt_low_direct", "Baseline").fob2_mean_util_pct, 1)}%. In no tested case does a one-minute value approach 100% of reference capacity.`);
CALLOUT("Interpretation.", "Under the 60 pax/m/min reference intensity and the recorded or assumed widths, neither operational FOB approaches its reference capacity even with 20% more demand. However, utilization here is a reference-capacity ratio, not a level-of-service or safety assessment; train-release platoons, stair and escalator bottlenecks and the unverified FOB 3 width are not captured, so the result should be read as a screening-level indication rather than proof of adequacy.");

// ==================================================================================================
// 2. PROBLEM
// ==================================================================================================
H1("2. Problem Definition and Objectives");
P("Kanjurmarg (Central Line suburban station) is expected to become an interchange with Metro Lines 4 and 6. The project report recorded that the station has three FOBs, of which one (FOB 1, at the Naval Colony end) is closed, so all bridge movement between the west side and the island platform currently relies on FOB 2 and FOB 3. Metro integration could raise peak pedestrian demand, and the question is how the operational FOBs would be loaded if that happens.");
P("The study answers six questions:");
N("How is passenger demand distributed between direct PF1 access, FOB 2 and FOB 3?");
N("What are the baseline utilization levels of FOB 2 and FOB 3?");
N("What changes under +10% and +20% passenger demand?");
N("How much do results vary because passenger arrivals and route choices are stochastic?");
N("How sensitive are the results to the assumed route distribution?");
N("Does the demand increase change the relative loading of the two operational FOBs?");
CALLOUT("Scope note.", "The +10% and +20% demand levels are hypothetical scenarios motivated by possible metro integration. They are not forecasts of post-metro ridership.", BLUE);

// ==================================================================================================
// 3. SCOPE
// ==================================================================================================
H1("3. Scope and Simplified Station Layout");
P("The layout follows the team's hand-drawn station sketch. Along the west side, from north to south, the order is: Naval Colony entrance, FOB 2, Huma entrance, FOB 3, Gandhi Nagar entrance. FOB 1 lies at the northern (Naval Colony) end and is closed. PF1/1A is the platform adjacent to the west-side entrances; PF2 is the island platform beyond the tracks. The east side (skywalk and the north-east/south-east entrances) is drawn for context only.");
FIG("fig1_station_layout.png", "Simplified conceptual layout used in the AnyLogic model (not to scale). Dots are simulated passengers at minute 30 of the baseline run (seed 1001): amber = direct PF1, teal = via FOB 2, blue = via FOB 3. Dotted lines mark where FOB crossings are counted.", 5.4);
TABLE("Model scope.", ["Included", "Excluded"], [
  ["Three west entrances: Naval Colony, Huma, Gandhi Nagar", "East-side entrances (NE/SE) as passenger sources"],
  ["Entering and leaving streams at each entrance (6 streams)", "Ticket counters and queues, buses, autos"],
  ["Routes: direct PF1, FOB 2, FOB 3", "Metro train operations, other stations"],
  ["FOB 1 shown as closed (never selectable)", "Stair/escalator capacity, density, speed, queuing"],
  ["One-minute FOB crossing counts and utilization", "Interventions or redesigns"],
], [1, 1], { leftAll: true });
P("All three routes are physically available from every modelled entrance in the simplified network: entrances open onto a west-side footpath that runs the full length of PF1 and meets the western stairs of both FOBs. Direct PF1 access is an alternative pedestrian route, not an additional bridge.");

// ==================================================================================================
// 4. OBSERVED DATA
// ==================================================================================================
H1("4. Observed Data and Input Parameters");
P("All numerical inputs come from the team's field observations recorded in the IE 301 project report (Sections 2.2, 2.3 and 4.6). Values are peak-period rates in passengers per minute.");
TABLE("Observed entrance flows (pax/min).", ["Entrance", "Entering", "Leaving", "Total activity"], [
  ["Naval Colony", "10.00", "42.00", "52.00"], ["Huma", "27.20", "50.00", "77.20"], ["Gandhi Nagar", "33.33", "6.66", "39.99"],
  ["**Total**", "**70.53**", "**98.66**", "**169.19**"],
], [2, 1, 1, 1], { source: "Source: IE 301 project report, Section 2.2 (team field counts). The east-side grouped count (20 in / 10 out) is outside the model scope." });
TABLE("Observed facility flows and physical parameters.", ["Facility", "Observed flow (pax/min)", "Share of FOB 2+3", "Width (m)", "Width status"], [
  ["FOB 1", "Closed", "–", "–", "Not in use"],
  ["FOB 2", "70.0", "67.76%", "5.36", "Recorded on sketch; clear width to be verified"],
  ["FOB 3", "33.3", "32.24%", "6.0", "**Provisional assumption — not measured**"],
  ["FOB 2 + FOB 3", "103.3", "100%", "–", "–"],
], [1.1, 1.3, 1.1, 0.8, 2.4], { source: "Source: project report Sections 2.3, 4.4 and 4.6; FOB 3 width specified as a provisional value for this study." });
CALLOUT("Data limitation.", "The total recorded entrance activity (169.19 pax/min) exceeds the combined FOB flow (103.3 pax/min) by 65.89 pax/min. The project data do not establish that entrance and FOB counts were taken synchronously across a common boundary, so this difference cannot be proven to be the actual direct-PF1 flow.", RED);

// ==================================================================================================
// 5. ROUTE DISTRIBUTION
// ==================================================================================================
H1("5. Aggregate-Calibrated Route Distribution");
P("There is no measured route-choice matrix by entrance. The model therefore uses one aggregate split for every entrance and direction, obtained by dividing each route's reference flow by the total entrance activity:");
EQ("p_PF1 = 65.89 / 169.19 = 0.389444", "5.1");
EQ("p_FOB2 = 70.00 / 169.19 = 0.413736", "5.2");
EQ("p_FOB3 = 33.30 / 169.19 = 0.196820", "5.3");
P("The exact fractions are used in the code (not rounded percentages). By construction 169.19 × p_FOB2 = 70.00 and 169.19 × p_FOB3 = 33.30, so the **expected** FOB flows reproduce the observations before random variation.");
TABLE("Route probabilities applied to every entrance and direction.", ["Entrance", "Direct PF1", "Via FOB 2", "Via FOB 3", "Via FOB 1"], [
  ["Naval Colony", "38.944%", "41.374%", "19.682%", "0% (closed)"], ["Huma", "38.944%", "41.374%", "19.682%", "0% (closed)"],
  ["Gandhi Nagar", "38.944%", "41.374%", "19.682%", "0% (closed)"],
], [1.4, 1, 1, 1, 1]);
CALLOUT("What this distribution is — and is not.", "The 65.89 pax/min direct-PF1 flow is an **inferred residual**, not an observation. Because the route shares were chosen from the observed FOB flows, agreement between simulated and observed FOB flows is **calibration, not independent validation**. Identical shares at every entrance is an assumption of convenience: in reality Naval Colony users may favour FOB 2 and Gandhi Nagar users FOB 3. Identifying true entrance-specific route choices requires origin–route counts at each entrance (Section 13).", RED);

// ==================================================================================================
// 6. STOCHASTIC MODEL
// ==================================================================================================
H1("6. Stochastic Arrival and Route-Choice Model");
H2("6.1 Distributions chosen");
P("Two random processes drive the model, and each was chosen as the simplest defensible first approximation for the available data:");
TABLE("Probability distributions and modelling choices.", ["Model element", "Distribution / rule", "Parameters", "Why chosen"], [
  ["Passenger arrivals (each of 6 streams)", "Poisson process: N(t) ~ Poisson(λt)", "λ = observed rate × scenario multiplier", "Many independent pedestrians; only a mean rate is known"],
  ["Inter-arrival times", "Exponential", "Mean 60/λ seconds", "Equivalent to a Poisson process"],
  ["Route choice per passenger", "Categorical (multinomial) draw by inverse CDF", "p = (0.3894, 0.4137, 0.1968)", "Only aggregate route shares are known"],
  ["Walking speed", "Deterministic", "1.30 m/s", "Affects only crossing timing (14–60 s)"],
  ["Random numbers", "java.util.Random, one stream per arrival stream", "seed × 1000 + stream index", "Reproducible, independent streams"],
], [1.5, 1.6, 1.6, 1.8], { leftAll: true });
H2("6.2 Poisson arrivals");
P("For a stream with mean rate λ (pax/min), the number of arrivals in t minutes and the time between arrivals are:");
EQ("N(t) ~ Poisson(λt),   P(N(t) = k) = e^(−λt) (λt)^k / k!", "6.1");
EQ("Δt ~ Exponential(λ),   E[Δt] = 1/λ min = 60/λ s", "6.2");
EQ("Δt = −ln(1 − U) · 60/λ   with  U ~ Uniform(0, 1)", "6.3");
const rates = [["Naval Colony", "Entering", 10.00], ["Naval Colony", "Leaving", 42.00], ["Huma", "Entering", 27.20], ["Huma", "Leaving", 50.00], ["Gandhi Nagar", "Entering", 33.33], ["Gandhi Nagar", "Leaving", 6.66]];
TABLE("The six Poisson arrival streams (baseline).", ["Entrance", "Direction", "λ (pax/min)", "Mean inter-arrival (s)", "Expected per hour", "+10% λ", "+20% λ"],
  rates.map(([e, d, l]) => [e, d, f(l), f(60 / l, 2), f(l * 60, 0), f(l * 1.1), f(l * 1.2)]), [1.4, 1, 1, 1.3, 1.1, 0.9, 0.9]);
P("Why Poisson: with many passengers arriving independently from a large catchment, the superposition of their arrivals is well approximated by a Poisson process, and it needs only the mean rate, which is all the field data provide. Its variance equals its mean, so it carries a natural level of minute-to-minute randomness.");
P("Why it is only a first approximation: suburban stations receive passengers in **platoons** when a train unloads, and peak-period rates rise and fall within the hour. Both effects make real one-minute peaks larger and more clustered than a constant-rate Poisson process predicts. The simulated 95th-percentile and maximum minutes should therefore be read as lower bounds on true peak-minute loading.");
H2("6.3 Route choice and crossing count");
P("Immediately after arriving, each passenger draws a uniform random number U and takes the first route whose cumulative probability exceeds U (direct PF1 if U < 0.3894, FOB 2 if U < 0.8032, otherwise FOB 3). FOB 1 is not in the route list, so it can never be selected. A passenger on an FOB route is counted **once**, in the one-minute interval in which they reach the FOB deck mid-point (the count line between PF1 and PF2). Direct-PF1 passengers never touch an FOB count.");
H2("6.4 Estimating variability across replications");
P("Each replication uses a different seed and gives one value of each performance measure (for example the hourly mean flow). Across n = 30 replications the mean and its 95% confidence interval are:");
EQ("x̄ ± t(0.975, n−1) · s / √n,   with t(0.975, 29) = 2.045", "6.4");
P("The same 30 seeds (1001–1030) are used in every scenario (**common random numbers**), so scenario differences are not obscured by different random draws. The model starts empty with no warm-up period, as required; the effect of this is quantified in Section 10.");

// ==================================================================================================
// 7. CAPACITY
// ==================================================================================================
H1("7. Capacity and Utilization Calculations");
P("Following the project's capacity framework, the reference pedestrian capacity of a facility is:");
EQ("C = W × I × T", "7.1");
P("where W is the effective usable width (m), I the reference flow intensity (60 pax/m/min) and T the interval (min). For a one-minute interval C = 60W. Utilization of an interval is the observed or simulated crossing count Q in that same minute divided by C:");
EQ("U = Q / C × 100%", "7.2");
TABLE("Reference capacities and observed-flow benchmarks.", ["Facility", "W (m)", "C (pax/min)", "Observed Q (pax/min)", "Benchmark U"], [
  ["FOB 2", "5.36", "321.6", "70.0", "21.77%"], ["FOB 3", "6.0 (assumed)", "360.0", "33.3", "9.25%"],
], [1.2, 1.2, 1, 1.3, 1]);
TABLE("Deterministic observed-flow benchmark (proportional scaling — NOT simulation output).", ["Scenario", "FOB 2 flow", "FOB 2 U", "FOB 3 flow", "FOB 3 U"], [
  ["Baseline", "70.00", "21.77%", "33.30", "9.25%"], ["+10%", "77.00", "23.94%", "36.63", "10.18%"], ["+20%", "84.00", "26.12%", "39.96", "11.10%"],
], [1.2, 1, 1, 1, 1], { source: "Calculated as observed flow × demand multiplier ÷ capacity. Reported separately from the stochastic results in Section 10." });
CALLOUT("Limits of the capacity proxy.", "C = WIT with I = 60 pax/m/min is a theoretical reference intensity, not a measured capacity. The resulting U is a reference-capacity ratio, not a pedestrian level-of-service or safety assessment. It ignores stairs and escalators (often the real bottleneck), counter-flow, platoon arrivals, obstructions that reduce clear width, and crowd density. FOB 2's width must be verified as clear usable width, and FOB 3's 6.0 m is an assumption: U scales with 1/W, so if FOB 3's clear width were, say, 4.0 m its utilization would be 1.5 times higher.", RED);

// ==================================================================================================
// 8. ANYLOGIC
// ==================================================================================================
H1("8. AnyLogic Implementation");
P("The model is a native AnyLogic 8.8 project (Kanjurmarg_FOB_Simulation.alp, model time unit = seconds). It uses core AnyLogic agent-based elements rather than Pedestrian Library blocks, so that every arrival, route choice and crossing is explicit in code that can be inspected and tested.");
TABLE("Model structure.", ["Element", "Type", "Role"], [
  ["Main", "Top-level agent", "Station layout, parameters, statistics, dashboard"],
  ["passengers (Passenger)", "Agent population", "One dot per passenger, coloured by route, walking the layout"],
  ["Arrival(stream)", "Dynamic event", "Poisson arrival: draw route, create passenger, schedule next arrival"],
  ["Waypoint(p)", "Dynamic event", "Moves a passenger to its next way-point"],
  ["Crossing(route)", "Dynamic event", "Counts an FOB crossing in the current minute"],
  ["minuteTick", "Cyclic event (60 s)", "Closes each minute: flow, utilization, charts"],
  ["FobEngine", "Java class (Additional class code)", "Stochastic core shared by animation and batch runs"],
  ["runBatch()", "Function + button", "30 replications × 3 scenarios inside AnyLogic, with 95% CIs; writes CSV"],
], [1.4, 1.4, 3], { leftAll: true });
P("**Interface.** The start page offers scenario selection (Baseline, +10%, +20%), random seed, number of replications, run duration and FOB 3 width. The run screen shows the animated layout with FOB 1 clearly marked closed, a live clock, generated/completed/walking passenger counters, FOB 2 and FOB 3 crossing counts, live one-minute utilization bars, the configured and realised route split, a time plot of one-minute utilization, a histogram of utilization variability, and a scenario-comparison chart filled by the replication button. Start, pause and reset are also available on AnyLogic's standard toolbar.");
FIG("anylogic_screen_preview.png", "Model screen design, drawn from the shapes stored in the .alp file with values from the baseline run at minute 30 (seed 1001). This is a rendering of the model's layout for the report — not a screenshot taken in AnyLogic.", 6.5);
CALLOUT("Verification status.", "AnyLogic was not available in the environment where the model was built, so the .alp has **not yet been opened or run in AnyLogic**. All model code was compiled with javac against stand-ins for the AnyLogic functions it uses, and the model's event logic was executed headless. It reproduced replication 1 of the batch exactly (4,244 FOB 2 and 2,027 FOB 3 crossings, identical minute by minute). Opening the project in AnyLogic 8.8 is the remaining check (Appendix).", BLUE);

// ==================================================================================================
// 9. EXPERIMENTAL DESIGN
// ==================================================================================================
H1("9. Experimental Design");
TABLE("Experiments.", ["Factor", "Setting"], [
  ["Demand scenarios", "Baseline ×1.00, +10% ×1.10, +20% ×1.20 applied to all six stream rates"],
  ["Held constant", "Route probabilities, layout, widths, capacity parameters, walking speed"],
  ["Run length", "60 minutes (configurable)"],
  ["Replications", "30 per scenario (configurable); seeds 1001–1030; common random numbers"],
  ["Initial state", "Empty station, no warm-up (configurable in engine)"],
  ["Route sensitivity", "4 route splits × 3 scenarios × 30 replications (Section 11)"],
  ["Total runs", "360 replications (12 configurations × 30)"],
], [1.3, 4], { leftAll: true });
P("**Outputs per FOB and replication:** hourly mean crossing flow; mean, 95th-percentile and maximum one-minute utilization; standard deviation of one-minute utilization; plus the number of passengers assigned to direct PF1 and the count on FOB 1 (always zero). Utilization is calculated minute by minute from the actual crossings in that minute, not from the hourly total.");

// ==================================================================================================
// 10. RESULTS
// ==================================================================================================
H1("10. Simulation Results");
H2("10.1 Flow allocation");
P(`On average a baseline replication generates ${Math.round(b2.mean_generated_passengers).toLocaleString("en-US")} passengers in 60 minutes, of whom ${Math.round(b2.mean_direct_pf1_passengers).toLocaleString("en-US")} (${f(100 * b2.mean_direct_pf1_passengers / b2.mean_generated_passengers, 1)}%) take the direct PF1 route. These passengers are reported for transparency and never contribute to FOB counts. FOB 1 recorded zero crossings in all 360 replications.`);
H2("10.2 FOB flow and utilization by scenario");
const resRows = [];
for (const sc of ["Baseline", "+10%", "+20%"]) for (const fac of ["FOB 2", "FOB 3"]) {
  const r = S(sc, fac);
  resRows.push([sc, fac, `${f(r.mean_flow_pax_per_min)} ± ${f(r.flow_ci95_halfwidth)}`, `${f(r.mean_util_pct)} ± ${f(r.mean_util_ci95_halfwidth)}`,
    `${f(r.p95_util_pct_mean_of_reps)} ± ${f(r.p95_util_ci95_halfwidth)}`, `${f(r.max_util_pct_mean_of_reps)} ± ${f(r.max_util_ci95_halfwidth)}`,
    f(r.max_util_pct_overall), f(r.within_rep_sd_util_pct)]);
}
TABLE("Stochastic simulation results (mean ± 95% CI half-width over 30 replications).", ["Scenario", "FOB", "Flow (pax/min)", "Mean U (%)", "P95 U (%)", "Max-minute U (%)", "Highest minute, all reps (%)", "Within-run SD of U (pp)"],
  resRows, [1, 0.85, 1.3, 1.3, 1.3, 1.3, 1.2, 1.1], { source: "Source: data/scenario_summary.csv. P95 and Max are computed within each replication and then averaged.", highlightRows: [0, 1] });
FIG("fig2_scenario_utilization.png", "Mean one-minute utilization (bars, 95% CI), mean within-run 95th percentile and maximum minute, against the deterministic reference (red).");
const chg = [];
for (const fac of ["FOB 2", "FOB 3"]) for (const sc of ["+10%", "+20%"]) {
  const r = S(sc, fac);
  chg.push([fac, sc, `+${f(r.change_vs_baseline_mean_flow_pax_per_min)}`, `+${f(r.change_vs_baseline_mean_util_pct)}`, `+${f(r.change_vs_baseline_p95_util_pct_mean_of_reps)}`, `+${f(r.change_vs_baseline_max_util_pct_mean_of_reps)}`]);
}
TABLE("Change from baseline.", ["FOB", "Scenario", "Δ Flow (pax/min)", "Δ Mean U (pp)", "Δ P95 U (pp)", "Δ Max-minute U (pp)"], chg, [1, 1, 1.2, 1.2, 1.2, 1.3]);
H2("10.3 Variability");
P(`Two kinds of variability appear. **Within a run**, one-minute FOB 2 flow fluctuates around its mean with a standard deviation of about ${f(b2.within_rep_sd_util_pct, 1)} percentage points of utilization (Figure 4), which is why the busiest minute is ${f(b2.max_util_pct_mean_of_reps - b2.mean_util_pct, 1)} points above the hourly mean on average. **Between runs**, the hourly mean flow differs from seed to seed with a standard deviation of ${f(b2.flow_sd_between_reps, 2)} pax/min for FOB 2 and ${f(b3.flow_sd_between_reps, 2)} pax/min for FOB 3 (Figure 5), giving narrow confidence intervals. Thirty replications were therefore sufficient; increasing them was not necessary.`);
FIG("fig3_utilization_variability.png", "Distribution of one-minute utilization (minutes 2–60, all 30 replications). Boxes show the interquartile range, whiskers the 5th–95th percentiles.");
FIG("fig5_replication_spread.png", "Hourly mean flow in each replication. The spread shows the replication-to-replication variation used for the confidence intervals.");
H2("10.4 Time profile and start-up transient");
FIG("fig4_baseline_timeseries.png", "Baseline mean one-minute flow over the simulated hour (band = 5th–95th percentile across replications; dotted lines = observed values).");
P("Because the model starts empty, FOB-bound passengers need 14–60 seconds to reach the count line, so minute 1 records only about half the steady flow (36.4 vs ≈ 70 pax/min on FOB 2). This lowers the 60-minute mean by roughly 0.8%. Excluding minute 1, the baseline means are 70.30 (FOB 2) and 33.45 pax/min (FOB 3). The no-warm-up setting was kept as specified; the warm-up length is a configurable engine parameter.");
H2("10.5 Comparison with the observed benchmark");
FIG("fig7_flow_vs_reference.png", "Simulated hourly mean flow (95% CI) against the deterministic proportional reference.");
P(`Simulated baseline means differ from the observed values by ${f(b2.diff_vs_reference_flow)} pax/min (FOB 2, ${f(b2.diff_vs_reference_pct)}%) and ${f(b3.diff_vs_reference_flow)} pax/min (FOB 3, ${f(b3.diff_vs_reference_pct)}%), mainly because of the start-up transient. This close agreement is **expected by construction** and confirms the implementation is consistent. It is calibration, not evidence that the model reproduces real passenger behaviour.`);

// ==================================================================================================
// 11. SENSITIVITY
// ==================================================================================================
H1("11. Route Sensitivity Analysis");
P("To test how much the conclusions depend on the assumed split, three alternative distributions were simulated with the same seeds and all three demand scenarios. These are **sensitivity assumptions, not observed behaviour**.");
const sensRows = [];
const labels = { calibrated: "Calibrated (primary)", equal_split: "Equal split", alt_fob_balanced: "Alt A: FOB-balanced", alt_low_direct: "Alt B: low direct PF1" };
for (const rs of ["calibrated", "equal_split", "alt_fob_balanced", "alt_low_direct"]) {
  const b = SE(rs, "Baseline"), q = SE(rs, "+20%");
  sensRows.push([labels[rs], `${f(100 * b.p_direct_pf1, 1)} / ${f(100 * b.p_fob2, 1)} / ${f(100 * b.p_fob3, 1)}`, f(b.fob2_mean_util_pct), f(b.fob3_mean_util_pct), f(q.fob2_mean_util_pct), f(q.fob3_mean_util_pct), f(q.fob2_max_util_pct), f(b.fob2_share_of_fob_flow_pct, 1)]);
}
TABLE("Route-split sensitivity (mean one-minute utilization, %).", ["Route split", "PF1 / FOB2 / FOB3 (%)", "FOB 2 base", "FOB 3 base", "FOB 2 +20%", "FOB 3 +20%", "FOB 2 max-min. +20%", "FOB 2 share of FOB flow (%)"],
  sensRows, [1.5, 1.5, 0.8, 0.8, 0.8, 0.8, 1, 1.1], { source: "Source: data/route_sensitivity.csv. Alt A keeps the inferred PF1 share and splits the FOB share equally; Alt B assumes only 20% use direct PF1 and keeps the observed 67.8 : 32.2 FOB ratio.", highlightRows: [0] });
FIG("fig6_route_sensitivity.png", "Left: baseline utilization under four route splits. Right: gap between FOB 2 and FOB 3 utilization as demand rises.");
P("**Findings.** (i) The **balance** between the FOBs is entirely driven by the route split: with equal FOB shares the two bridges are within about 2 percentage points of each other (FOB 3 is slightly lower only because its assumed width is larger). (ii) The **absolute level** depends mainly on how many passengers are assumed to bypass the bridges via direct PF1 access: if only 20% do (Alt B), FOB 2 reaches 28.3% at baseline and its busiest minute averages 41.8% at +20%. (iii) In every case utilization rises linearly with demand and stays far below 100% of reference capacity. Aggregate calibration establishes consistency with the selected observations; it does not identify the true entrance-specific probabilities.");

// ==================================================================================================
// 12. INTERPRETATION
// ==================================================================================================
H1("12. Interpretation and Operational Implications");
P("**Q1 — Demand distribution.** Under the calibrated assumption about 39% of west-side movements use direct PF1 access, 41% FOB 2 and 20% FOB 3. Only the FOB shares are anchored in observation; the PF1 share is a residual.");
P(`**Q2 — Baseline utilization.** FOB 2 ≈ ${f(b2.mean_util_pct, 1)}% and FOB 3 ≈ ${f(b3.mean_util_pct, 1)}% of reference capacity on average, with typical peak minutes (95th percentile) of ${f(b2.p95_util_pct_mean_of_reps, 1)}% and ${f(b3.p95_util_pct_mean_of_reps, 1)}%.`);
P(`**Q3 — Effect of demand growth.** Each 10% of demand adds about ${f(p2.change_vs_baseline_mean_util_pct, 1)} points to FOB 2's mean utilization and ${f(p3.change_vs_baseline_mean_util_pct, 1)} to FOB 3's; FOB 2's 95th-percentile minute reaches ${f(q2.p95_util_pct_mean_of_reps, 1)}% at +20%. The response is linear because the model contains no congestion feedback.`);
P(`**Q4 — Stochastic variation.** Minute-scale randomness is substantial: the busiest minute of a run averages ${f(100 * (b2.max_util_pct_mean_of_reps / b2.mean_util_pct - 1), 0)}% (FOB 2) and ${f(100 * (b3.max_util_pct_mean_of_reps / b3.mean_util_pct - 1), 0)}% (FOB 3) above the hourly mean, while hourly means are stable across replications (95% CI ±${f(b2.mean_util_ci95_halfwidth, 2)} points or less). Operational planning should therefore look at peak minutes, not hourly averages — and real platoon arrivals will make peaks sharper than modelled here.`);
P("**Q5 — Sensitivity to route split.** High for the FOB 2 : FOB 3 balance and moderate for absolute levels; low for the qualitative conclusion that both FOBs remain well below reference capacity.");
P(`**Q6 — Relative loading.** No change: FOB 2 carries ${f(SE("calibrated", "Baseline").fob2_share_of_fob_flow_pct, 1)}% of FOB flow in all scenarios. This is an assumption-driven result (fixed route probabilities), not an empirical finding. The absolute gap grows (${f(SE("calibrated", "Baseline").util_gap_fob2_minus_fob3_pct, 1)} → ${f(SE("calibrated", "+20%").util_gap_fob2_minus_fob3_pct, 1)} pp), so any future imbalance problem would appear on FOB 2 first. If metro passengers arrive mainly via Gandhi Nagar (the shortest proposed metro connection, about 238 m, is to Gandhi Nagar Metro), FOB 3's share could increase — this cannot be tested without entrance-specific route data.`);
CALLOUT("Operational implications.", "(1) Bridge deck width does not appear to be the binding constraint under the reference benchmark, consistent with the project report's aggregate V/C of 0.23. (2) Attention should go to the elements this model excludes: staircases and escalators at FOB landings (the report observed 81.7% of one vertical pair using the escalator), train-release surges, and route choice. (3) Re-opening FOB 1 or redirecting flows is not supported or rejected by this analysis, because route choice is fixed by assumption.");

// ==================================================================================================
// 13. ASSUMPTIONS
// ==================================================================================================
H1("13. Assumptions, Limitations, and Additional Data Required");
H2("13.1 Assumptions register");
TABLE("Assumptions, evidence status and implications.", ["ID", "Assumption", "Value", "Evidence status", "Implication"],
  assumptions.map((a) => [a.id, a.assumption, a.value, a.evidence_status, a.implication]), [0.4, 1.4, 1.6, 1.2, 2], { leftAll: true, source: "Full register with rationale: data/assumptions_register.csv." });
H2("13.2 Assumptions with the strongest influence on interpretation");
B("**Route split (A1–A3):** sets both FOB balance and absolute loading; the PF1 share is a residual of possibly non-synchronous counts.");
B("**FOB widths (A8–A9):** utilization scales with 1/W; FOB 3's width is unmeasured.");
B("**Poisson, constant-rate arrivals (A4–A5):** understate peak-minute loading when trains release platoons.");
B("**Capacity proxy (A10):** a reference ratio, not level of service or safety.");
H2("13.3 Additional data required");
N("Synchronised counts across a closed boundary (all entrances, both FOBs, direct PF1 access) over the same intervals.");
N("Entrance-by-route counts or a short intercept survey (entrance → route → platform) to estimate entrance-specific route probabilities.");
N("Clear usable widths of FOB 2 and FOB 3, and of their stairs and escalators.");
N("Five-minute or one-minute count profiles across the peak, with train arrival times, to model platoons and time-varying rates.");
N("Density and speed observations on FOB decks and landings (P in a known area A, q and W over the same interval).");
N("Independent hold-out counts (a different day) for genuine validation.");

// ==================================================================================================
// 14. CONCLUSION
// ==================================================================================================
H1("14. Conclusion");
P(`A reproducible stochastic simulation of Kanjurmarg's west-side pedestrian access was built in AnyLogic and run for baseline, +10% and +20% demand with 30 replications each. Using the aggregate-calibrated route split, FOB 2 operates at about ${f(b2.mean_util_pct, 0)}% and FOB 3 at about ${f(b3.mean_util_pct, 0)}% of the reference capacity at baseline, rising to about ${f(q2.mean_util_pct, 0)}% and ${f(q3.mean_util_pct, 0)}% at +20%. Peak one-minute values remain well below 50%. The relative loading of the two bridges is unchanged by demand growth, a direct consequence of the fixed route-choice assumption.`);
P("The results are calibrated to the observed FOB flows, not independently validated. The most valuable next steps are synchronised and entrance-specific counts, measured clear widths, and arrival profiles that capture train-release surges. Those data would allow the model to move from a screening tool to a validated decision aid for metro-integration planning.");

// ==================================================================================================
// 15. APPENDIX
// ==================================================================================================
H1("15. Reproducibility Appendix");
H2("15.1 Deliverables");
TABLE("Project files (folder kanjurmarg_fob_simulation/).", ["Path", "Content"], [
  ["anylogic/Kanjurmarg_FOB_Simulation/Kanjurmarg_FOB_Simulation.alp", "Native AnyLogic 8.8 project"],
  ["engine/FobEngine.java", "Stochastic core (embedded verbatim in the .alp)"],
  ["engine/RunnerMain.java, scripts/run_engine.sh", "Stand-alone batch runner for all 360 replications"],
  ["python/fob_twin.py", "Independent Python re-implementation used for cross-checking"],
  ["python/analyze.py, python/make_charts.py", "Summary statistics, CSV export, tests, figures"],
  ["scripts/build_alp.py, scripts/check_alp_code.py", "Model generator and model-code compile/headless check"],
  ["data/*.csv (6 files)", "observed_data, scenario_summary, fob_time_series, replication_results, assumptions_register, route_sensitivity"],
  ["charts/*.png", "All figures in this report"], ["README.md, VALIDATION.md", "Instructions and verification record"],
], [2.6, 2.4], { leftAll: true });
H2("15.2 Reproducing the results");
md.push("```");
["scripts/run_engine.sh 30 60 0 1.30 1001     # replications, minutes, warm-up, walk speed, base seed",
  "python3 python/analyze.py                    # CSVs + 21 verification tests",
  "python3 python/make_charts.py                # figures",
  "python3 scripts/build_alp.py && python3 scripts/check_alp_code.py"].forEach((c) => {
  body.push(new Paragraph({ shading: { type: ShadingType.CLEAR, fill: "F1F4F7", color: "auto" }, spacing: { after: 0 },
    children: [new TextRun({ text: c, font: "Courier New", size: 17 })] }));
  md.push(c);
});
md.push("```\n");
body.push(new Paragraph({ spacing: { after: 160 }, children: [] }));
P("In AnyLogic: open the .alp, run the Simulation experiment, choose a scenario and press Run; press 'Run replications' on the model screen to run 30 seeds × 3 scenarios. The in-model replication runs use the same engine and seeds and reproduce data/scenario_summary.csv; their output is written to anylogic_batch_results.csv in the model folder.");
H2("15.3 Verification summary");
TABLE("Automated checks (all from python/analyze.py unless noted).", ["Check", "Result"],
  tests.map((t) => [t.test, (t.passed ? "PASS — " : "FAIL — ") + t.detail.slice(0, 140) + (t.detail.length > 140 ? "…" : "")]).concat([
    ["Java engine vs Python twin, all 360 replications", "PASS — 0 mismatches in route counts and per-minute crossings"],
    ["Model code compile (scripts/check_alp_code.py)", "PASS — all functions, events, 27 dynamic expressions compile against AnyLogic API stand-ins"],
    ["Model event logic executed headless", "PASS — identical to batch replication 1 (seed 1001)"],
    ["Opened and run in AnyLogic 8.8", "NOT YET PERFORMED — AnyLogic unavailable in build environment"],
  ]), [2, 3], { leftAll: true });
H2("15.4 Software");
P("Java (OpenJDK 21), Python 3.13 with NumPy 2.5, pandas 3.0, SciPy 1.18 and Matplotlib 3.11. Target modelling environment: AnyLogic 8.8 (Personal Learning Edition compatible; no paid libraries used).");

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
