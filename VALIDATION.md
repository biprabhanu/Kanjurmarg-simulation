# VALIDATION — Kanjurmarg FOB Simulation

This file records what was checked, how, and what remains unverified. "Calibration" and "validation" are kept separate.

## 1. Automated verification tests (`python/analyze.py`) — 21/21 passed

| Result | Check | Detail |
|---|---|---|
| PASS | FOB 1 never selected and carries zero flow | sum of FOB 1 crossings over 360 replications = 0; routes available = PF1, FOB 2, FOB 3 only |
| PASS | Route probabilities sum to 1 (calibrated) | sum = 1.000000000000 |
| PASS | Route probabilities sum to 1 (equal_split) | sum = 0.999999999900 |
| PASS | Route probabilities sum to 1 (alt_fob_balanced) | sum = 1.000000000000 |
| PASS | Route probabilities sum to 1 (alt_low_direct) | sum = 1.000000000000 |
| PASS | Poisson arrival count: Naval Colony entering | mean 600.9 vs expected 600.0 (z = +0.21); variance/mean = 0.89 (Poisson ~ 1) |
| PASS | Poisson arrival count: Naval Colony leaving | mean 2527.9 vs expected 2520.0 (z = +0.86); variance/mean = 1.13 (Poisson ~ 1) |
| PASS | Poisson arrival count: Huma entering | mean 1638.8 vs expected 1632.0 (z = +0.93); variance/mean = 1.08 (Poisson ~ 1) |
| PASS | Poisson arrival count: Huma leaving | mean 3014.1 vs expected 3000.0 (z = +1.41); variance/mean = 0.82 (Poisson ~ 1) |
| PASS | Poisson arrival count: Gandhi Nagar entering | mean 2004.1 vs expected 1999.8 (z = +0.53); variance/mean = 1.40 (Poisson ~ 1) |
| PASS | Poisson arrival count: Gandhi Nagar leaving | mean 397.4 vs expected 399.6 (z = -0.59); variance/mean = 1.11 (Poisson ~ 1) |
| PASS | Demand multiplier applied (+10%) | generated ratio vs baseline = 1.0996 (target 1.1) |
| PASS | Demand multiplier applied (+20%) | generated ratio vs baseline = 1.1995 (target 1.2) |
| PASS | Same route probabilities used at every entrance/direction | chi-square homogeneity across 6 streams p = 0.344; observed shares by stream: Naval Colony entering 41.6% FOB2; Naval Colony leaving 41.3% FOB2; Huma entering 41.5% FOB2; Huma leaving 41.2% FOB2; Gandhi Nagar entering 41.8% FOB2; Gandhi Nagar leaving 41.4% FOB2 |
| PASS | Route assignment reproduces configured probabilities | simulated shares PF1/FOB2/FOB3 = 38.87/41.42/19.72% vs 38.94/41.37/19.68% |
| PASS | Direct PF1 passengers never counted on an FOB; each FOB passenger counted at most once | for every replication: FOB crossings + passengers still approaching at t=60 = FOB-assigned passengers |
| PASS | Different seeds generate different counts | 30 distinct count vectors from 30 seeds |
| PASS | Java engine reproduced by independent Python implementation | identical route counts for sampled replications (full 360-replication comparison run separately: 0 mismatches) |
| PASS | Capacity calculation units | C2 = 5.36 m x 60 pax/m/min = 321.6 pax/min; C3 = 6.0 x 60 = 360 pax/min |
| PASS | Simulated flows are generated, not copied from observations | baseline differences vs reference: FOB 2 -0.26 pax/min, FOB 3 -0.07 pax/min |
| PASS | Calibration consistency (expected to hold by construction) | baseline simulated vs observed: FOB 2 69.74 vs 70.00, FOB 3 33.23 vs 33.30 — calibration, not validation |

## 2. Cross-implementation and model-code checks

| Result | Check | How |
|---|---|---|
| PASS | Java engine == independent Python implementation | All 360 replications (4 route splits × 3 scenarios × 30 seeds): 0 mismatches in generated counts, route counts and every per-minute FOB crossing count. `python/fob_twin.py` re-implements `java.util.Random` and the full logic separately. |
| PASS | All AnyLogic model code compiles | `scripts/check_alp_code.py` extracts start-up code, 10 functions, 1 cyclic event, 3 dynamic events, 27 dynamic text/colour/chart/button expressions and the experiment parameter expressions from the .alp and compiles them with javac against stand-ins for the AnyLogic API. |
| PASS | Animated model logic == batch engine | The model's own event code (Arrival → Waypoint → Crossing → minuteTick) was executed by a minimal event scheduler. For seed 1001, baseline: 10,295 passengers, 4,244 FOB 2 and 2,027 FOB 3 crossings, FOB 1 = 0 — identical, minute by minute, to replication 1 of the batch. |
| PASS | In-model "Run replications" == exported results | `runBatch()` executed headless reproduces `data/scenario_summary.csv` (e.g. FOB 2 baseline 69.74 ± 0.49 pax/min, 21.68% mean utilization). |
| PASS | .alp is well-formed XML | 276 unique element IDs, no duplicates; structure follows real AnyLogic 8.8.3 project files (AlpVersion 8.8.3). |
| PASS | Report numbers come from the data | The report builder reads `data/scenario_summary.csv`, `route_sensitivity.csv`, `assumptions_register.csv` and `build/test_results.json` directly; figures are drawn from the CSVs by `python/make_charts.py`. |

## 3. Calibration (not validation)

Route probabilities were derived from the observed FOB flows, so the simulated baseline means (FOB 2 69.74, FOB 3 33.23
pax/min) agreeing with the observations (70.0, 33.3) is expected **by construction**. The small shortfall (−0.4%, −0.2%)
comes from the empty-start transient in minute 1. No independent data were available, so **the model has not been
independently validated**.

## 4. Not yet verified / remaining issues

1. **The .alp has not been opened or run inside AnyLogic.** AnyLogic was not available in the build environment, and
   access to the AnyLogic folder on the user's Mac was not granted. The compile check uses stand-ins for AnyLogic's own
   classes, so AnyLogic-specific details (e.g. element defaults, chart/control rendering, `moveTo` speed units) are
   untested. Opening the model in AnyLogic 8.8 is the outstanding check; any error message can be fixed quickly.
2. The model screen image in the report (`charts/anylogic_screen_preview.png`) is a rendering of the .alp shapes drawn by
   `scripts/render_preview.py`, **not** an AnyLogic screenshot.
3. Pedestrian Library blocks were not used (core agents + events instead) because their internal file references could
   not be checked without AnyLogic. Pedestrian density/speed/travel-time results are therefore not reported.
4. FOB 3 width (6.0 m) is an unverified assumption; FOB 2 width (5.36 m) needs confirmation as clear usable width.
5. The Google Doc version of the report contains all text and tables but not the figure images (the connector can only
   upload text); the images are in the PDF/Word version and `charts/`.
