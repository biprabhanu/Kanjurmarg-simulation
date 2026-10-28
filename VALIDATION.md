# VALIDATION — Kanjurmarg FOB Simulation (version 3, revised route splits)

What was checked, how, and what is still unverified.

## 1. Automated checks (`python/analyze.py`) — 25/25 passed

| Result | Check | Detail |
|---|---|---|
| PASS | Route probabilities sum to 100% for every gate (defaults) | Naval Colony 100%; Huma 100%; Gandhi Nagar 100%; Northeast 100%; Southeast 100% |
| PASS | Additional-demand route shares sum to 100% | Huma 50/35/15, Gandhi Nagar 40/40/20 |
| PASS | Route probabilities sum to 100% for every gate (noisy draws) | checked 90 replications x (5 gates + 2 additional-demand splits) |
| PASS | Impossible routes stay impossible under noise | routes with 0% default probability are never used |
| PASS | FOB 1 remains unavailable | FOB 1 crossings over 180 replications = 0 |
| PASS | Skywalk is a connector, not an FOB | only Northeast passengers use the skywalk (8361 in total); they are counted on FOB 3 and there is no skywalk crossing count |
| PASS | Direct PF1 passengers never counted; each FOB passenger counted at most once | every replication: FOB 2 + FOB 3 crossings + passengers still approaching at t=60 = FOB-route passengers |
| PASS | East-side rates conserve the observed aggregate | Northeast + Southeast entering = 10 + 10 = 20; leaving = 5 + 5 = 10 pax/min |
| PASS | Baseline gate totals | entering 90.53, leaving 108.66, total 199.19 pax/min |
| PASS | Additional demand total and 80/20 split (+50 pax/min) | Huma +40, Gandhi Nagar +10, total +50 pax/min; Huma entering 67.20, Gandhi Nagar entering 43.33 |
| PASS | Additional Huma arrivals are Poisson (+50 pax/min) | mean 2406.9 per hour vs expected 2400 (z = +0.77) |
| PASS | Additional Gandhi Nagar arrivals are Poisson (+50 pax/min) | mean 598.3 per hour vs expected 600 (z = -0.39) |
| PASS | Additional demand total and 80/20 split (+100 pax/min) | Huma +80, Gandhi Nagar +20, total +100 pax/min; Huma entering 107.20, Gandhi Nagar entering 53.33 |
| PASS | Additional Huma arrivals are Poisson (+100 pax/min) | mean 4792.5 per hour vs expected 4800 (z = -0.60) |
| PASS | Additional Gandhi Nagar arrivals are Poisson (+100 pax/min) | mean 1193.4 per hour vs expected 1200 (z = -1.04) |
| PASS | Expected additional routing +50 | PF1 +24, FOB 2 +18, FOB 3 +8 pax/min (expected values, reported separately from simulation) |
| PASS | Expected additional routing +100 | PF1 +48, FOB 2 +36, FOB 3 +16 pax/min (expected values, reported separately from simulation) |
| PASS | Baseline streams unchanged by scenarios (no multipliers) | with the same seed, all 10 baseline gate-direction streams generate identical arrivals in every scenario |
| PASS | Poisson arrival counts for the 10 baseline streams | z-scores of hourly means vs lambda x 60: +0.2, +0.9, +0.9, +1.4, +0.5, -0.6, -1.3, -0.9, +0.8, -2.5 |
| PASS | Per-passenger route choice follows each replication's split | pooled chi-square = 946.5 on 960 df, p = 0.616 (1,077,324 passengers) |
| PASS | Route-split noise has the intended size | SD of Naval Colony FOB 3 share (15%) across replications = 3.5 pp (theory 3.6 pp) |
| PASS | Different seeds generate different trajectories | 30 distinct arrival-count vectors from 30 seeds |
| PASS | Java engine reproduced by independent Python implementation | identical per-minute FOB 2 counts for sampled replications (full comparison of all 180 replications: 0 mismatches) |
| PASS | Capacity units | C2 = 5.36 m x 60 pax/m/min x 1 min = 321.6 pax; C3 = 6.0 x 60 x 1 = 360 pax |
| PASS | Simulated results recorded separately from expected values | baseline simulated minus expected flow: FOB 2 -2.25 pax/min, FOB 3 +0.81 pax/min |

## 2. Cross-implementation and model-code checks

| Result | Check | How |
|---|---|---|
| PASS | Java engine == independent Python implementation | All 180 replications: 0 mismatches in arrivals, noisy splits, route counts and per-minute FOB crossings. |
| PASS | All AnyLogic model code compiles | `scripts/check_alp_code.py` compiles all functions, events and 14 dynamic expressions against AnyLogic API stand-ins. |
| PASS | Animated model logic == batch engine | Seed 1001, baseline: 4,157 FOB 2 and 2,058 FOB 3 crossings, identical minute by minute to replication 1. |
| PASS | In-model "Run replications" == exported results | `runBatch()` run headless reproduces `data/scenario_summary.csv` (FOB 2 baseline 20.7% ± 0.5). |
| PASS | .alp is well-formed XML | Unique element IDs and shape names. |

## 3. Expected values vs observed counts (not validation)

Expected baseline flows from the assumed splits: 68.9 (FOB 2) and 32.6 (FOB 3) pax/min; observed 70.0 and 33.3. Simulated means: 66.7 and 33.4. The splits are estimates, so this agreement is a consistency check only; the model is **not validated** against independent data.

## 4. Not yet verified

1. The .alp has not yet been confirmed to open and run in AnyLogic itself.
2. The model-screen image is drawn by `scripts/render_preview.py`, not an AnyLogic screenshot.
3. Stair/escalator capacity, density and travel time are not modelled.
4. FOB 3 width (6.0 m) is unverified; FOB 2 width (5.36 m) needs confirmation.
