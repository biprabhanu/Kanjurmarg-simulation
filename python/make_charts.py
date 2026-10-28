"""
Utilization charts for the report. Every value is read from the exported CSV files in data/.
Two charts only: FOB 2 vs FOB 3 by scenario, and utilization over the hour.

    python3 python/make_charts.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "charts")

TEAL, BLUE, RED, GREY = "#00A19B", "#2563EB", "#D93025", "#8E99A6"
INK, MUTED, GRID, SURFACE = "#1F2933", "#5F6B7A", "#E4E7EB", "#FFFFFF"
FOB_COL = {"FOB 2": TEAL, "FOB 3": BLUE}
SCEN = ["Baseline", "+50 pax/min", "+100 pax/min"]
SCEN_TICK = ["Baseline\n+0", "+50\npax/min", "+100\npax/min"]
OBS_UTIL = {"FOB 2": 70.0 / 321.6 * 100, "FOB 3": 33.3 / 360 * 100}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": "#C7CDD4", "axes.linewidth": 0.8,
    "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED, "axes.titleweight": "bold",
    "axes.titlesize": 12, "axes.titlecolor": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7,
    "axes.axisbelow": True, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "legend.frameon": False,
    "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 200,
})


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print("saved", name)


def fig_comparison(s):
    """Simple grouped bars: mean utilization of FOB 2 vs FOB 3 in each scenario (95% CI)."""
    fig, ax = plt.subplots(figsize=(9, 4.6))
    x = np.arange(3)
    w = 0.36
    for k, fac in enumerate(["FOB 2", "FOB 3"]):
        d = s[s.facility == fac].set_index("scenario").loc[SCEN]
        xs = x + (k - 0.5) * w
        cap = d.capacity_pax_per_min.iloc[0]
        ax.bar(xs, d.mean_util_pct, width=w * 0.92, color=FOB_COL[fac], zorder=2,
               label=f"{fac}  (W = {d.width_m.iloc[0]:.2f} m, C = {cap:.1f} pax/min)")
        ax.errorbar(xs, d.mean_util_pct, yerr=d.mean_util_ci95_halfwidth, fmt="none", ecolor=INK, capsize=4, lw=1.1, zorder=3)
        for xi, v, ci in zip(xs, d.mean_util_pct, d.mean_util_ci95_halfwidth):
            ax.text(xi, v + ci + 0.6, f"{v:.1f}%", ha="center", va="bottom", fontsize=10, fontweight="bold", color=INK)
    ax.set_xticks(x, ["Baseline", "+50 pax/min", "+100 pax/min"])
    ax.set_ylabel("Mean one-minute utilization (%)")
    ax.set_ylim(0, 40)
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left", fontsize=9)
    ax.set_title("FOB 2 vs FOB 3 utilization by scenario (mean of 30 replications, bars = 95% CI)", loc="left", fontsize=11.5)
    save(fig, "fig2_fob_comparison.png")


def fig_timeseries(ts):
    c = ts[ts.experiment_set == "with_split_noise"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.9), sharey=True)
    for ax, fac in zip(axes, ["FOB 2", "FOB 3"]):
        for sc, ls, alpha in (("Baseline", "-", 0.12), ("+100 pax/min", "--", 0.08)):
            d = c[(c.facility == fac) & (c.scenario == sc)].groupby("minute").utilization_pct
            m, lo, hi = d.mean(), d.quantile(0.05), d.quantile(0.95)
            ax.fill_between(m.index, lo, hi, color=FOB_COL[fac], alpha=alpha, lw=0)
            ax.plot(m.index, m.values, color=FOB_COL[fac], lw=2, ls=ls, label=f"{sc} (mean)")
        ax.axhline(OBS_UTIL[fac], color=RED, ls=":", lw=1.2)
        ax.text(59, OBS_UTIL[fac] + 0.7, "observed baseline", color=RED, fontsize=8.5, ha="right")
        ax.set_title(fac, color=FOB_COL[fac])
        ax.set_xlabel("Minute of simulated peak hour")
        ax.set_xlim(0, 61)
        ax.set_ylim(0, 50)
        ax.legend(loc="upper left", fontsize=8.5)
    axes[0].set_ylabel("One-minute utilization (%)")
    fig.suptitle("Utilization over the hour (band = 5th–95th percentile across 30 replications)", fontweight="bold",
                 color=INK, x=0.02, ha="left", y=1.02)
    fig.tight_layout()
    save(fig, "fig3_utilization_timeseries.png")


def main():
    s = pd.read_csv(os.path.join(DATA, "scenario_summary.csv"))
    ts = pd.read_csv(os.path.join(DATA, "fob_time_series.csv"))
    for old in ("fig2_scenario_utilization.png", "fig3_utilization_variability.png", "fig4_utilization_timeseries.png", "fig5_replication_spread.png", "fig6_utilization_increase.png",
                "fig4_baseline_timeseries.png", "fig6_route_sensitivity.png", "fig7_flow_vs_reference.png"):
        p = os.path.join(OUT, old)
        if os.path.exists(p):
            os.remove(p)
    fig_comparison(s)
    fig_timeseries(ts)


if __name__ == "__main__":
    main()
