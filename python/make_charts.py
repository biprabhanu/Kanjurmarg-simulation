"""
Presentation charts for the report. Every value is read from the exported CSV files in data/.

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

TEAL, BLUE, AMBER, RED = "#00A19B", "#2563EB", "#D97706", "#D93025"
INK, MUTED, GRID, SURFACE = "#1F2933", "#5F6B7A", "#E4E7EB", "#FFFFFF"
FOB_COL = {"FOB 2": TEAL, "FOB 3": BLUE}
SCEN = ["Baseline", "+10%", "+20%"]

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


def fig_scenarios(s):
    """Mean one-minute utilization with 95% CI, plus mean p95 and max markers."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    for ax, fac in zip(axes, ["FOB 2", "FOB 3"]):
        d = s[s.facility == fac].set_index("scenario").loc[SCEN]
        x = np.arange(3)
        ax.bar(x, d.mean_util_pct, width=0.55, color=FOB_COL[fac], zorder=2, label="Mean 1-min utilization")
        ax.errorbar(x, d.mean_util_pct, yerr=d.mean_util_ci95_halfwidth, fmt="none", ecolor=INK, capsize=5, lw=1.2, zorder=3)
        ax.scatter(x, d.p95_util_pct_mean_of_reps, marker="D", s=40, color=INK, zorder=4, label="95th percentile (mean of reps)")
        ax.scatter(x, d.max_util_pct_mean_of_reps, marker="^", s=48, facecolor="white", edgecolor=INK, zorder=4,
                   label="Maximum minute (mean of reps)")
        ax.scatter(x, d.reference_util_pct, marker="_", s=500, color=RED, lw=2, zorder=5, label="Deterministic reference")
        for i, v in enumerate(d.mean_util_pct):
            ax.text(i, v / 2, f"{v:.1f}%", ha="center", va="center", color="white", fontweight="bold", fontsize=10)
        ax.set_xticks(x, ["Baseline\n×1.00", "+10%\n×1.10", "+20%\n×1.20"])
        ax.set_title(f"{fac}  (C = {d.capacity_pax_per_min.iloc[0]:.1f} pax/min)", color=FOB_COL[fac])
        ax.set_ylim(0, 40)
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("Utilization of reference capacity (%)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.06), fontsize=9)
    fig.suptitle("One-minute FOB utilization by demand scenario (30 replications, 95% CI)", fontweight="bold", color=INK, x=0.02, ha="left", y=1.04)
    save(fig, "fig2_scenario_utilization.png")


def fig_distribution(ts):
    """Distribution of all one-minute utilization values (variability)."""
    c = ts[ts.route_set == "calibrated"]
    fig, ax = plt.subplots(figsize=(10, 4.2))
    pos, data, cols = [], [], []
    for i, sc in enumerate(SCEN):
        for j, fac in enumerate(["FOB 2", "FOB 3"]):
            pos.append(i * 3 + j)
            data.append(c[(c.scenario == sc) & (c.facility == fac) & (c.minute > 1)].utilization_pct.values)
            cols.append(FOB_COL[fac])
    vp = ax.violinplot(data, positions=pos, widths=0.85, showextrema=False)
    for b, col in zip(vp["bodies"], cols):
        b.set_facecolor(col)
        b.set_alpha(0.35)
        b.set_edgecolor(col)
    bp = ax.boxplot(data, positions=pos, widths=0.22, patch_artist=True, whis=(5, 95), showfliers=False,
                    medianprops=dict(color="white", lw=1.6))
    for patch, col in zip(bp["boxes"], cols):
        patch.set_facecolor(col)
        patch.set_edgecolor(col)
    for k in ("whiskers", "caps"):
        for line, col in zip(bp[k], np.repeat(cols, 2)):
            line.set_color(col)
    ax.set_xticks([0.5, 3.5, 6.5], ["Baseline", "+10%", "+20%"])
    ax.set_ylabel("One-minute utilization (%)")
    ax.set_ylim(0, 40)
    ax.grid(axis="x", visible=False)
    ax.plot([], [], color=TEAL, lw=8, label="FOB 2")
    ax.plot([], [], color=BLUE, lw=8, label="FOB 3")
    ax.legend(loc="upper left", ncol=2)
    ax.set_title("Variability of one-minute utilization  (box = IQR, whiskers = 5th–95th percentile; minutes 2–60, 30 reps)",
                 loc="left", fontsize=11)
    save(fig, "fig3_utilization_variability.png")


def fig_timeseries(ts):
    """Mean one-minute flow over the hour with 5–95% replication band (baseline)."""
    c = ts[(ts.route_set == "calibrated") & (ts.scenario == "Baseline")]
    fig, ax = plt.subplots(figsize=(10, 4))
    for fac in ["FOB 2", "FOB 3"]:
        d = c[c.facility == fac].groupby("minute").crossings_pax
        m, lo, hi = d.mean(), d.quantile(0.05), d.quantile(0.95)
        ax.fill_between(m.index, lo, hi, color=FOB_COL[fac], alpha=0.15, lw=0)
        ax.plot(m.index, m.values, color=FOB_COL[fac], lw=2)
        ax.text(61, m.iloc[1:].mean(), f"{fac}\nmean {m.iloc[1:].mean():.1f}\n(min 2–60)", color=INK, va="center", fontsize=9)
    ax.axhline(70.0, color=TEAL, ls=":", lw=1)
    ax.axhline(33.3, color=BLUE, ls=":", lw=1)
    ax.annotate("Minute 1: start-up transient\n(model starts empty)", xy=(1, 36), xytext=(6, 12), fontsize=9, color=MUTED,
                arrowprops=dict(arrowstyle="->", color=MUTED))
    ax.set_xlim(0, 68)
    ax.set_ylim(0, 110)
    ax.set_xlabel("Minute of simulated peak hour")
    ax.set_ylabel("Crossings per minute (pax/min)")
    ax.set_title("Baseline: mean one-minute FOB flow across 30 replications (band = 5th–95th percentile; dotted = observed)",
                 loc="left", fontsize=11)
    save(fig, "fig4_baseline_timeseries.png")


def fig_replications(rr):
    """Replication-to-replication variation of the hourly mean flow."""
    c = rr[rr.route_set == "calibrated"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    for ax, fac in zip(axes, ["FOB 2", "FOB 3"]):
        for i, sc in enumerate(SCEN):
            v = c[(c.facility == fac) & (c.scenario == sc)].mean_flow_pax_per_min.values
            jitter = np.linspace(-0.18, 0.18, len(v))
            ax.scatter(i + jitter, v, s=18, color=FOB_COL[fac], alpha=0.75, edgecolor="white", lw=0.5, zorder=3)
            ax.hlines(v.mean(), i - 0.28, i + 0.28, color=INK, lw=2, zorder=4)
        ax.set_xticks(range(3), SCEN)
        ax.set_title(fac, color=FOB_COL[fac])
        ax.grid(axis="x", visible=False)
        ax.set_ylabel("Hourly mean flow (pax/min)")
    fig.suptitle("Replication-level hourly mean flow (each dot = one seed; bar = mean of 30)", fontweight="bold",
                 color=INK, x=0.02, ha="left")
    fig.tight_layout()
    save(fig, "fig5_replication_spread.png")


def fig_sensitivity(sens):
    order = ["calibrated", "equal_split", "alt_fob_balanced", "alt_low_direct"]
    labels = ["Calibrated\n38.9 / 41.4 / 19.7", "Equal split\n33.3 / 33.3 / 33.3",
              "Alt A: FOB-balanced\n38.9 / 30.5 / 30.5", "Alt B: low direct\n20.0 / 54.2 / 25.8"]
    b = sens[sens.scenario == "Baseline"].set_index("route_set").loc[order]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw=dict(width_ratios=[1.6, 1]))
    ax = axes[0]
    x = np.arange(len(order))
    w = 0.36
    for k, (fac, colm, cim) in enumerate([("FOB 2", "fob2_mean_util_pct", "fob2_flow_ci95"),
                                           ("FOB 3", "fob3_mean_util_pct", "fob3_flow_ci95")]):
        vals = b[colm].values
        ax.bar(x + (k - 0.5) * (w + 0.02), vals, width=w, color=FOB_COL[fac], label=fac, zorder=2)
        for xi, v in zip(x, vals):
            ax.text(xi + (k - 0.5) * (w + 0.02), v + 0.5, f"{v:.1f}", ha="center", fontsize=8.5, color=INK)
    ax.set_xticks(x, labels, fontsize=8.5)
    ax.set_ylabel("Mean 1-min utilization (%)")
    ax.set_ylim(0, 35)
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left", ncol=2)
    ax.set_title("Baseline utilization under alternative route splits\n(PF1 / FOB 2 / FOB 3 %)", loc="left", fontsize=11)
    ax = axes[1]
    for rs, lab, col, ls in zip(order, ["Calibrated", "Equal split", "Alt A", "Alt B"], [INK, MUTED, "#8E99A6", AMBER],
                                ["-", "--", ":", "-."]):
        d = sens[sens.route_set == rs].set_index("scenario").loc[SCEN]
        ax.plot(range(3), d.util_gap_fob2_minus_fob3_pct, marker="o", color=col, ls=ls, lw=2, label=lab)
    ax.set_xticks(range(3), SCEN)
    ax.set_ylabel("FOB 2 minus FOB 3 utilization (pp)")
    ax.axhline(0, color="#C7CDD4", lw=1)
    ax.legend(fontsize=8.5, loc="center right")
    ax.grid(axis="x", visible=False)
    ax.set_title("Relative loading gap vs demand", loc="left", fontsize=11)
    fig.tight_layout()
    save(fig, "fig6_route_sensitivity.png")


def fig_benchmark(s):
    """Simulated mean flow vs deterministic proportional reference."""
    fig, ax = plt.subplots(figsize=(10, 3.6))
    x = np.arange(3)
    for k, fac in enumerate(["FOB 2", "FOB 3"]):
        d = s[s.facility == fac].set_index("scenario").loc[SCEN]
        off = (k - 0.5) * 0.38
        ax.bar(x + off, d.mean_flow_pax_per_min, width=0.34, color=FOB_COL[fac], label=f"{fac} simulated", zorder=2)
        ax.errorbar(x + off, d.mean_flow_pax_per_min, yerr=d.flow_ci95_halfwidth, fmt="none", ecolor=INK, capsize=4, zorder=3)
        ax.scatter(x + off, d.reference_flow_proportional, marker="_", s=380, color=RED, lw=2, zorder=4,
                   label="Deterministic reference" if k == 0 else None)
        for xi, v, r in zip(x + off, d.mean_flow_pax_per_min, d.reference_flow_proportional):
            ax.text(xi, v + 4, f"{v:.1f}\n(ref {r:.1f})", ha="center", fontsize=8, color=INK)
    ax.set_xticks(x, SCEN)
    ax.set_ylim(0, 105)
    ax.set_ylabel("Flow (pax/min)")
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left", ncol=3, fontsize=9)
    ax.set_title("Simulated hourly mean FOB flow vs proportional reference (calibration check, not validation)",
                 loc="left", fontsize=11)
    save(fig, "fig7_flow_vs_reference.png")


def main():
    s = pd.read_csv(os.path.join(DATA, "scenario_summary.csv"))
    ts = pd.read_csv(os.path.join(DATA, "fob_time_series.csv"))
    rr = pd.read_csv(os.path.join(DATA, "replication_results.csv"))
    sens = pd.read_csv(os.path.join(DATA, "route_sensitivity.csv"))
    fig_scenarios(s)
    fig_distribution(ts)
    fig_timeseries(ts)
    fig_replications(rr)
    fig_sensitivity(sens)
    fig_benchmark(s)


if __name__ == "__main__":
    main()
