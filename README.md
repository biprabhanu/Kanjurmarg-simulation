# Kanjurmarg Station — FOB Utilization Simulation (IE 301)

Stochastic simulation of how peak-period passengers at Kanjurmarg station use **direct PF1 access, FOB 2 and FOB 3**
(FOB 1 closed) from the three west entrances **Naval Colony, Huma and Gandhi Nagar**, under baseline, +10% and +20%
hypothetical demand. Simplified conceptual layout — not to scale.

## What is in this folder

| Path | What it is |
|---|---|
| `anylogic/Kanjurmarg_FOB_Simulation/Kanjurmarg_FOB_Simulation.alp` | **Native AnyLogic 8.8 project** (open this in AnyLogic) |
| `engine/FobEngine.java` | The stochastic core. The same text is embedded inside the .alp |
| `engine/RunnerMain.java`, `scripts/run_engine.sh` | Runs all 360 replications outside AnyLogic with plain Java |
| `python/fob_twin.py` | Independent Python re-implementation (cross-check) |
| `python/analyze.py` | Builds the six CSV files and runs 21 verification tests |
| `python/make_charts.py` | Builds the report figures from the CSVs |
| `scripts/build_alp.py` | Generates the .alp file |
| `scripts/check_alp_code.py` | Compiles all model code against AnyLogic API stand-ins and runs the model logic headless |
| `scripts/render_preview.py` | Draws a preview image of the model screen from the .alp shapes |
| `data/*.csv` | `observed_data`, `scenario_summary`, `fob_time_series`, `replication_results`, `assumptions_register`, `route_sensitivity` |
| `charts/*.png` | Figures (fig1–fig7) and the model-screen preview |
| `report/` | Technical report: `.docx`, `.pdf`, `.md` (+ the script that builds it) |
| `VALIDATION.md` | What was checked, results, and what is still unverified |

## Opening and running the AnyLogic model

1. Open **AnyLogic 8.8** (Personal Learning Edition is fine — no paid libraries are used).
2. `File → Open…` and choose `Kanjurmarg_FOB_Simulation.alp` (keep it inside its own folder).
3. In the Projects tree, right-click **Simulation** → **Run**.
4. On the start page choose the **scenario** (Baseline / +10% / +20%), the **seed**, the **number of replications**,
   the **run duration** and the **FOB 3 width**, then press the blue **Run** button.
5. Watch the passengers walk: **amber = direct PF1, teal = FOB 2, blue = FOB 3**. The dashboard shows the clock,
   counters, FOB crossings, one-minute utilization bars, the route split, a utilization time plot and a histogram.
   The run pauses automatically at the end of the horizon (60 min by default).
6. Press **Run replications** to run all three scenarios × N seeds inside AnyLogic (about a second). The table and
   comparison bars appear on screen and `anylogic_batch_results.csv` is written to the model folder.
   With the default seed 1001 and 30 replications this reproduces `data/scenario_summary.csv`.

Start/pause/stop/reset are also on AnyLogic's standard toolbar; speed up the animation with the speed buttons.

**If AnyLogic reports an error when opening or compiling**, copy the message (or a screenshot) — the model was
generated programmatically and has not yet been opened in AnyLogic itself (see `VALIDATION.md`).

## Reproducing all results without AnyLogic

Requirements: Java 11+ (javac), Python 3.10+ with numpy, pandas, scipy, matplotlib; Node.js with `docx` for the report.

```bash
scripts/run_engine.sh 30 60 0 1.30 1001   # replications, minutes, warm-up (min), walking speed (m/s), base seed
python3 python/analyze.py                  # -> data/*.csv and 21 PASS/FAIL tests
python3 python/make_charts.py              # -> charts/*.png
python3 scripts/build_alp.py               # -> anylogic/.../Kanjurmarg_FOB_Simulation.alp
python3 scripts/check_alp_code.py          # compile + headless run of the model code
python3 scripts/render_preview.py 30       # model-screen preview at minute 30
node report/build_report.js                # -> report/*.docx and *.md
```

## Key modelling choices (details in the report, Sections 5–7 and 13)

- Six independent **Poisson** arrival streams (exponential inter-arrival times), rates from the project report.
- **Aggregate-calibrated route split** at every entrance: PF1 65.89/169.19, FOB 2 70.00/169.19, FOB 3 33.30/169.19.
  The PF1 share is an inferred residual. Matching observed FOB flows is calibration, not validation.
- Capacity `C = W × 60 pax/m/min` per minute; FOB 2 W = 5.36 m (recorded), FOB 3 W = 6.0 m (**assumed**).
- 60-minute runs, 30 replications, seeds 1001–1030 (common random numbers), empty start, no warm-up.
