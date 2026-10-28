# Kanjurmarg Station — FOB Utilization Simulation (IE 301)

Stochastic simulation of **FOB 2 and FOB 3 utilization** at Kanjurmarg station with **five gates**
(Naval Colony, Huma, Gandhi Nagar, Northeast, Southeast), a route split per gate, a closed FOB 1 and an east-side
**skywalk connecting FOB 2 and FOB 3** (a connector, not an FOB). Scenarios: baseline, **+50** and **+100 pax/min**
of extra entering demand (10% / 20% of an assumed 500 pax/min Ghatkopar reference), entering 80% via Huma and 20% via
Gandhi Nagar. Simplified conceptual layout — not to scale.

## Folder contents

| Path | What it is |
|---|---|
| `anylogic/Kanjurmarg_FOB_Simulation/Kanjurmarg_FOB_Simulation.alp` | **Native AnyLogic 8.8 project** |
| `engine/FobEngine.java` | Stochastic core; the same text is embedded inside the .alp |
| `engine/RunnerMain.java`, `scripts/run_engine.sh` | Runs all replications outside AnyLogic with plain Java |
| `python/fob_twin.py` | Independent Python re-implementation (cross-check) |
| `python/analyze.py` | Builds the CSV files and runs the verification checks |
| `python/make_charts.py` | Utilization charts for the report |
| `scripts/build_alp.py` | Generates the .alp file |
| `scripts/check_alp_code.py` | Compiles all model code against AnyLogic API stand-ins and runs the model logic headless |
| `scripts/render_preview.py` | Draws a preview image of the model screen from the .alp shapes |
| `data/*.csv` | `observed_data`, `gate_route_splits`, `expected_route_allocation`, `scenario_summary`, `fob_time_series`, `replication_results`, `route_split_uncertainty`, `assumptions_register` |
| `charts/*.png` | Station layout, FOB 2 vs FOB 3 comparison, utilization over time, model-screen preview |
| `report/` | Technical report (`.pdf`, `.docx`, `.md`) and the script that builds it |
| `VALIDATION.md` | What was checked, results, and what is still unverified |

## Opening and running the AnyLogic model

1. Put the `Kanjurmarg_FOB_Simulation` folder somewhere AnyLogic can read — on macOS **not** `Downloads`, unless
   AnyLogic has been allowed access (System Settings → Privacy & Security → Files and Folders).
2. Open **AnyLogic 8.8** → `File → Open…` → `Kanjurmarg_FOB_Simulation.alp`.
3. Right-click **Simulation** → **Run**. Choose the scenario (Baseline / +50 / +100 pax/min), seed, number of
   replications, run duration, FOB 3 width and route-split noise, then press **Run**.
4. Passengers are **red when entering** and **blue when leaving**. FOB 2 and FOB 3 decks change colour every minute
   with live utilization. The dashboard shows FOB 2 and FOB 3 gauges (now / mean / peak) and a utilization-over-time plot.
5. **Run replications** runs all three scenarios × N seeds inside AnyLogic (about a second), prints the results to the
   console and writes `anylogic_batch_results.csv`. With seed 1001 and 30 replications it reproduces `data/scenario_summary.csv`.

**"Cannot read the array length because the return value of java.io.File.listFiles() is null"** means AnyLogic is not
allowed to read the folder — see step 1. For any other error, send the message or a screenshot.

## Reproducing all results without AnyLogic

Requirements: Java 11+, Python 3.10+ with numpy, pandas, scipy, matplotlib; Node.js with `docx` for the report.

```bash
scripts/run_engine.sh 30 60 1.30 1001 99   # replications, minutes, walking speed (m/s), base seed, noise kappa
python3 python/analyze.py                   # -> data/*.csv and PASS/FAIL checks
python3 python/make_charts.py               # -> charts/*.png
python3 scripts/build_alp.py                # -> the .alp model
python3 scripts/check_alp_code.py           # compile + headless run of the model code
python3 scripts/render_preview.py 30 0      # model-screen preview at minute 30, baseline
python3 scripts/write_validation.py         # -> VALIDATION.md
node report/build_report.js                 # -> report/*.docx and *.md
```

## Key assumptions (full list in `data/assumptions_register.csv` and report Section 13)

- Baseline demand: observed rates; the East-side count (20 in / 10 out) is **split 50/50** between Northeast and Southeast.
- Route split per gate {PF1, FOB 2, FOB 3, skywalk}: Naval Colony 60/25/15/0, Huma 55/30/15/0, Gandhi Nagar 60/35/5/0,
  Northeast 0/95/0/5, Southeast 0/30/70/0 — **modelling assumptions**, used for entering and leaving passengers.
- Additional demand route split {PF1, FOB 2, FOB 3}: Huma 50/35/15, Gandhi Nagar 40/40/20.
- **Route-split noise:** each replication draws its gate splits from a Dirichlet distribution around these values
  (κ = 99, about ±3 percentage points for a 10–15% share).
- Northeast skywalk users walk the skywalk and cross FOB 3 (counted on FOB 3). The Northeast exit sits at the north
  end beside, but outside, the closed FOB 1.
- Poisson arrivals; capacity `C = W × 60 pax/m/min`; FOB 2 W = 5.36 m (recorded), FOB 3 W = 6.0 m (**unverified**).
- 60-minute runs, 30 replications, seeds 1001–1030 (common random numbers), empty start, no warm-up.
- Results describe loading under these assumptions; they are not ridership forecasts. The assumed splits give expected
  FOB flows (68.9 and 32.6 pax/min) close to the observed 70.0 and 33.3 — a consistency check, not validation.

## Results (mean one-minute utilization, 30 replications)

| Scenario | FOB 2 | FOB 3 |
|---|---:|---:|
| Baseline | 20.7% | 9.3% |
| +50 pax/min | 26.3% | 11.6% |
| +100 pax/min | 31.9% | 13.8% |
