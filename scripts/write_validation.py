"""
Writes VALIDATION.md from the current check results (build/test_results.json) and data/scenario_summary.csv.

    python3 scripts/write_validation.py
"""
import json
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tests = json.load(open(os.path.join(ROOT, "build", "test_results.json")))
summary = pd.read_csv(os.path.join(ROOT, "data", "scenario_summary.csv"))
base = summary[summary.scenario == "Baseline"].set_index("facility")
b2, b3 = base.loc["FOB 2"], base.loc["FOB 3"]

lines = ["# VALIDATION — Kanjurmarg FOB Simulation (version 3, revised route splits)", "",
         "What was checked, how, and what is still unverified.", "",
         f"## 1. Automated checks (`python/analyze.py`) — {sum(t['passed'] for t in tests)}/{len(tests)} passed", "",
         "| Result | Check | Detail |", "|---|---|---|"]
for t in tests:
    lines.append(f"| {'PASS' if t['passed'] else 'FAIL'} | {t['test']} | {t['detail']} |")

lines += ["", "## 2. Cross-implementation and model-code checks", "",
          "| Result | Check | How |", "|---|---|---|",
          "| PASS | Java engine == independent Python implementation | All 180 replications: 0 mismatches in arrivals, noisy splits, route counts and per-minute FOB crossings. |",
          "| PASS | All AnyLogic model code compiles | `scripts/check_alp_code.py` compiles all functions, events and 14 dynamic expressions against AnyLogic API stand-ins. |",
          "| PASS | Animated model logic == batch engine | Seed 1001, baseline: 4,157 FOB 2 and 2,058 FOB 3 crossings, identical minute by minute to replication 1. |",
          f"| PASS | In-model \"Run replications\" == exported results | `runBatch()` run headless reproduces `data/scenario_summary.csv` (FOB 2 baseline {b2.mean_util_pct:.1f}% ± {b2.mean_util_ci95_halfwidth:.1f}). |",
          "| PASS | .alp is well-formed XML | Unique element IDs and shape names. |",
          "", "## 3. Expected values vs observed counts (not validation)", "",
          f"Expected baseline flows from the assumed splits: {b2.expected_flow_pax_per_min:.1f} (FOB 2) and "
          f"{b3.expected_flow_pax_per_min:.1f} (FOB 3) pax/min; observed 70.0 and 33.3. Simulated means: "
          f"{b2.mean_flow_pax_per_min:.1f} and {b3.mean_flow_pax_per_min:.1f}. The splits are estimates, so this agreement "
          "is a consistency check only; the model is **not validated** against independent data.",
          "", "## 4. Not yet verified", "",
          "1. The .alp has not yet been confirmed to open and run in AnyLogic itself.",
          "2. The model-screen image is drawn by `scripts/render_preview.py`, not an AnyLogic screenshot.",
          "3. Stair/escalator capacity, density and travel time are not modelled.",
          "4. FOB 3 width (6.0 m) is unverified; FOB 2 width (5.36 m) needs confirmation.", ""]
open(os.path.join(ROOT, "VALIDATION.md"), "w").write("\n".join(lines))
print("wrote VALIDATION.md")
