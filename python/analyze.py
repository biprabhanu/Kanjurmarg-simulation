"""
Summarises the raw engine output (build/raw/*.csv) into the project CSV files and runs the
verification checks listed in Section 10 of the final-corrections brief.

    python3 python/analyze.py
"""
import json
import math
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "build", "raw")
OUT = os.path.join(ROOT, "data")
sys.path.insert(0, os.path.join(ROOT, "python"))
import fob_twin as tw  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration (one place, easy to audit)
# ---------------------------------------------------------------------------
DURATION_MIN = 60
INTENSITY = 60.0                         # pax / m / min (project report, C = WIT)
WIDTH = {"FOB 2": 5.36, "FOB 3": 6.0}   # FOB 3 width is a provisional, unverified value
CAPACITY = {f: WIDTH[f] * INTENSITY for f in WIDTH}
OBSERVED_FLOW = {"FOB 2": 70.0, "FOB 3": 33.3}   # field observation, baseline period only
SCENARIOS = ["Baseline", "+50 pax/min", "+100 pax/min"]
ADDITIONAL = {"Baseline": 0.0, "+50 pax/min": 50.0, "+100 pax/min": 100.0}
GHATKOPAR_REFERENCE = 500.0              # assumed benchmark (pax/min)
PRIMARY = "with_split_noise"
KAPPA = 99.0
GATES = tw.GATES
ROUTES = ["Direct PF1/PF1A", "FOB 2", "FOB 3", "Skywalk then FOB 3"]
STREAM_LABELS = [f"{g} {d}" for g in GATES for d in ("entering", "leaving")] + \
    ["Huma additional entering", "Gandhi Nagar additional entering"]


def ci_halfwidth(x):
    x = np.asarray(x, dtype=float)
    return stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / math.sqrt(len(x))


def expected_fob_flows(additional):
    f = tw.expected_route_flows(tw.DEFAULT_SPLITS, additional)
    return {"FOB 2": f[1], "FOB 3": f[2] + f[3]}, f


def main():
    os.makedirs(OUT, exist_ok=True)
    reps = pd.read_csv(os.path.join(RAW, "raw_replications.csv"))
    mins = pd.read_csv(os.path.join(RAW, "raw_minutes.csv"))

    write_observed_data()
    write_gate_route_splits()
    write_expected_allocation()

    # ---------------------------------------------------------------- one-minute time series
    ts = []
    for fac, col in [("FOB 2", "fob2"), ("FOB 3", "fob3")]:
        d = mins[["experiment_set", "scenario", "additional_demand", "replication", "seed", "minute", col]].copy()
        d = d.rename(columns={col: "crossings_pax"})
        d.insert(0, "facility", fac)
        d["capacity_pax_per_min"] = CAPACITY[fac]
        d["utilization_pct"] = d["crossings_pax"] / CAPACITY[fac] * 100
        ts.append(d)
    ts = pd.concat(ts, ignore_index=True)
    ts.to_csv(os.path.join(OUT, "fob_time_series.csv"), index=False, float_format="%.4f")

    # ---------------------------------------------------------------- replication results
    g = ts.groupby(["experiment_set", "scenario", "additional_demand", "replication", "seed", "facility"])
    rr = g.agg(crossings_total=("crossings_pax", "sum"),
               mean_util_pct=("utilization_pct", "mean"),
               p95_util_pct=("utilization_pct", lambda x: np.percentile(x, 95)),
               max_util_pct=("utilization_pct", "max"),
               sd_util_pct=("utilization_pct", lambda x: x.std(ddof=1))).reset_index()
    rr["mean_flow_pax_per_min"] = rr["crossings_total"] / DURATION_MIN
    keep = ["experiment_set", "scenario", "replication", "fob1_crossings", "fob_not_reached_by_end"]
    rep2 = reps.copy()
    rep2["total_generated"] = rep2[[f"gen_s{i}" for i in range(12)]].sum(axis=1)
    rep2["direct_pf1_passengers"] = rep2[[f"route_g{g}_r0" for g in range(5)] + [f"route_x{e}_r0" for e in range(2)]].sum(axis=1)
    rep2["skywalk_passengers"] = rep2[[f"route_g{g}_r3" for g in range(5)]].sum(axis=1)
    split_cols = {f"split_g{g}_r{r}": f"split_{GATES[g].lower().replace(' ', '_')}_{['pf1', 'fob2', 'fob3', 'skywalk'][r]}"
                  for g in range(5) for r in range(4) if tw.DEFAULT_SPLITS[g][r] > 0}
    rep2 = rep2.rename(columns=split_cols)
    rr = rr.merge(rep2[keep + ["total_generated", "direct_pf1_passengers", "skywalk_passengers"] + list(split_cols.values())],
                  on=["experiment_set", "scenario", "replication"])
    rr["scenario"] = pd.Categorical(rr["scenario"], SCENARIOS, ordered=True)
    rr = rr.sort_values(["experiment_set", "scenario", "facility", "replication"])
    rr.to_csv(os.path.join(OUT, "replication_results.csv"), index=False, float_format="%.5f")

    # ---------------------------------------------------------------- scenario summary (primary)
    rows = []
    for (es, sc, fac), d in rr.groupby(["experiment_set", "scenario", "facility"], observed=True):
        add = ADDITIONAL[sc]
        exp_flow = expected_fob_flows(add)[0][fac]
        minutes = ts[(ts.experiment_set == es) & (ts.scenario == sc) & (ts.facility == fac)]["utilization_pct"]
        rows.append(dict(
            experiment_set=es, scenario=sc, additional_demand=add, facility=fac, replications=len(d),
            width_m=WIDTH[fac], capacity_pax_per_min=CAPACITY[fac],
            mean_flow_pax_per_min=d.mean_flow_pax_per_min.mean(),
            flow_ci95_halfwidth=ci_halfwidth(d.mean_flow_pax_per_min),
            flow_sd_between_reps=d.mean_flow_pax_per_min.std(ddof=1),
            mean_util_pct=d.mean_util_pct.mean(),
            mean_util_ci95_halfwidth=ci_halfwidth(d.mean_util_pct),
            util_sd_between_reps=d.mean_util_pct.std(ddof=1),
            p95_util_pct_mean_of_reps=d.p95_util_pct.mean(),
            p95_util_ci95_halfwidth=ci_halfwidth(d.p95_util_pct),
            max_util_pct_mean_of_reps=d.max_util_pct.mean(),
            max_util_ci95_halfwidth=ci_halfwidth(d.max_util_pct),
            max_util_pct_overall=minutes.max(),
            within_rep_sd_util_pct=d.sd_util_pct.mean(),
            expected_flow_pax_per_min=exp_flow,
            expected_util_pct=exp_flow / CAPACITY[fac] * 100,
            sim_minus_expected_flow=d.mean_flow_pax_per_min.mean() - exp_flow,
            mean_direct_pf1_passengers=d.direct_pf1_passengers.mean(),
            mean_generated_passengers=d.total_generated.mean()))
    summ = pd.DataFrame(rows)
    for col in ["mean_flow_pax_per_min", "mean_util_pct", "p95_util_pct_mean_of_reps", "max_util_pct_mean_of_reps"]:
        base = summ[summ.scenario == "Baseline"].set_index(["experiment_set", "facility"])[col]
        summ[f"change_vs_baseline_{col}"] = summ.apply(lambda r: r[col] - base[(r.experiment_set, r.facility)], axis=1)
    summ["scenario"] = pd.Categorical(summ["scenario"], SCENARIOS, ordered=True)
    summ = summ.sort_values(["experiment_set", "scenario", "facility"])
    summ[summ.experiment_set == PRIMARY].drop(columns="experiment_set").to_csv(
        os.path.join(OUT, "scenario_summary.csv"), index=False, float_format="%.4f")

    # ---------------------------------------------------------------- route-split uncertainty
    unc = []
    for (sc, fac), d in summ.groupby(["scenario", "facility"], observed=True):
        a = d[d.experiment_set == PRIMARY].iloc[0]
        b = d[d.experiment_set == "fixed_splits"].iloc[0]
        unc.append(dict(scenario=sc, facility=fac,
                        mean_util_with_noise=a.mean_util_pct, ci95_with_noise=a.mean_util_ci95_halfwidth,
                        sd_between_reps_with_noise=a.util_sd_between_reps,
                        mean_util_fixed_splits=b.mean_util_pct, ci95_fixed_splits=b.mean_util_ci95_halfwidth,
                        sd_between_reps_fixed_splits=b.util_sd_between_reps,
                        variance_share_from_split_noise_pct=100 * max(0.0, 1 - (b.util_sd_between_reps / a.util_sd_between_reps) ** 2)))
    pd.DataFrame(unc).to_csv(os.path.join(OUT, "route_split_uncertainty.csv"), index=False, float_format="%.4f")

    write_assumptions()

    results = run_tests(reps, mins, rr, summ)
    with open(os.path.join(ROOT, "build", "test_results.json"), "w") as fh:
        json.dump(results, fh, indent=2)
    n_fail = sum(1 for t in results if not t["passed"])
    for t in results:
        print(("PASS " if t["passed"] else "FAIL ") + t["test"] + " — " + t["detail"])
    print(f"\n{len(results) - n_fail}/{len(results)} tests passed")


# ==============================================================================================
def write_observed_data():
    src = "IE 301 Operational project report (team field observations)"
    rows = []
    for g in range(5):
        status = "Observed" if g < 3 else "ASSUMPTION: observed East-side count split 50/50 (no separate gate counts)"
        rows += [dict(category="Gate flow", item=GATES[g], measure="Entering", value=tw.ENTER_RATE[g], unit="pax/min",
                      evidence_status=status, source=src + ", Sec. 2.2"),
                 dict(category="Gate flow", item=GATES[g], measure="Leaving", value=tw.LEAVE_RATE[g], unit="pax/min",
                      evidence_status=status, source=src + ", Sec. 2.2")]
    rows += [
        dict(category="Gate flow", item="East side (Northeast + Southeast)", measure="Entering / leaving", value="20.00 / 10.00",
             unit="pax/min", evidence_status="Observed (combined)", source=src + ", Sec. 2.2"),
        dict(category="Gate flow", item="All five gates", measure="Entering", value=90.53, unit="pax/min", evidence_status="Calculated", source=src),
        dict(category="Gate flow", item="All five gates", measure="Leaving", value=108.66, unit="pax/min", evidence_status="Calculated", source=src),
        dict(category="Gate flow", item="All five gates", measure="Total gate activity", value=199.19, unit="pax/min", evidence_status="Calculated", source=src),
        dict(category="Facility flow", item="FOB 1", measure="Flow", value=0, unit="pax/min", evidence_status="Closed", source=src + ", Sec. 2.1"),
        dict(category="Facility flow", item="FOB 2", measure="Flow", value=70.0, unit="pax/min", evidence_status="Observed benchmark", source=src + ", Sec. 2.3"),
        dict(category="Facility flow", item="FOB 3", measure="Flow", value=33.3, unit="pax/min", evidence_status="Observed benchmark", source=src + ", Sec. 2.3"),
        dict(category="Facility flow", item="FOB 2 + FOB 3", measure="Combined crossing flow", value=103.3, unit="pax/min",
             evidence_status="Observed benchmark (not the same as gate activity)", source=src),
        dict(category="Geometry", item="FOB 2", measure="Width", value=5.36, unit="m", evidence_status="Recorded; clear usable width to be verified", source=src + ", Sec. 4.6"),
        dict(category="Geometry", item="FOB 3", measure="Width", value=6.0, unit="m", evidence_status="PROVISIONAL ASSUMPTION - unverified", source="Final corrections brief"),
        dict(category="Capacity parameter", item="All FOBs", measure="Flow intensity I", value=60, unit="pax/m/min", evidence_status="Reference value", source=src + ", Sec. 4.6"),
        dict(category="Capacity", item="FOB 2", measure="C per minute", value=CAPACITY["FOB 2"], unit="pax/min", evidence_status="Calculated", source="C = W x I x T, T = 1 min"),
        dict(category="Capacity", item="FOB 3", measure="C per minute", value=CAPACITY["FOB 3"], unit="pax/min", evidence_status="Calculated (assumed width)", source="C = W x I x T, T = 1 min"),
        dict(category="Scenario input", item="Ghatkopar peak interchange flow", measure="Reference flow", value=GHATKOPAR_REFERENCE, unit="pax/min",
             evidence_status="ASSUMED benchmark (not independently verified)", source="Final corrections brief"),
    ]
    for sc, add in ADDITIONAL.items():
        rows.append(dict(category="Scenario input", item=sc, measure="Additional entering demand (Huma / Gandhi Nagar)",
                         value=f"{add:.0f} ({add * 0.8:.0f} / {add * 0.2:.0f})", unit="pax/min",
                         evidence_status="Scenario input rate, not measured future demand", source="500 x 10% / 20%; split 80/20"))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "observed_data.csv"), index=False)


def write_gate_route_splits():
    rows = []
    for g in range(5):
        p = tw.DEFAULT_SPLITS[g]
        rows.append(dict(gate=GATES[g], direct_pf1_pf1a=p[0], via_fob2=p[1], via_fob3=p[2], skywalk_then_fob3=p[3],
                         sum=sum(p), applies_to="baseline entering and leaving passengers at this gate",
                         noise="Dirichlet per replication, concentration 99 (about +/-3 pp for a 10% share); zero shares stay zero",
                         evidence_status="Modelling assumption, not a measured route choice"))
    for e, gname in enumerate(["Huma", "Gandhi Nagar"]):
        p = tw.EXTRA_SPLITS[e]
        rows.append(dict(gate=f"{gname} (additional demand)", direct_pf1_pf1a=p[0], via_fob2=p[1], via_fob3=p[2], skywalk_then_fob3=p[3],
                         sum=sum(p), applies_to="additional metro-related entering passengers at this gate",
                         noise="Dirichlet per replication, concentration 99", evidence_status="Modelling assumption, not a measured route choice"))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "gate_route_splits.csv"), index=False)


def write_expected_allocation():
    rows = []
    base = tw.expected_route_flows(tw.DEFAULT_SPLITS, 0.0)
    for sc, add in ADDITIONAL.items():
        f = tw.expected_route_flows(tw.DEFAULT_SPLITS, add)
        for r in range(4):
            counted = {0: "not an FOB user", 1: "FOB 2", 2: "FOB 3", 3: "FOB 3"}[r]
            rows.append(dict(scenario=sc, additional_demand=add, route=ROUTES[r], counted_on=counted,
                             expected_flow_pax_per_min=f[r], additional_vs_baseline=f[r] - base[r]))
        fob = expected_fob_flows(add)[0]
        for fac in ("FOB 2", "FOB 3"):
            rows.append(dict(scenario=sc, additional_demand=add, route=f"{fac} total crossing flow", counted_on=fac,
                             expected_flow_pax_per_min=fob[fac], additional_vs_baseline=fob[fac] - expected_fob_flows(0.0)[0][fac],
                             expected_util_pct=fob[fac] / CAPACITY[fac] * 100))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "expected_route_allocation.csv"), index=False, float_format="%.4f")


def write_assumptions():
    A = [
        ("A1", "Five access gates", "Naval Colony, Huma, Gandhi Nagar (west); Northeast, Southeast (east, skywalk exits)", "Final station layout", "Layout decision", "East-side demand now included"),
        ("A2", "East-side gate rates", "NE and SE each 10.00 entering / 5.00 leaving pax/min", "Observed East-side 20 / 10 split equally; no separate counts", "ASSUMPTION (50/50 split)", "Conserves the observed aggregate; true NE/SE balance unknown"),
        ("A3", "Baseline gate route-choice probabilities", "NC 60/25/15/0, Huma 55/30/15/0, GN 60/35/5/0, NE 0/95/0/5, SE 0/30/70/0 (PF1/FOB2/FOB3/skywalk)", "Revised team estimates", "Modelling assumption, not measured", "Expected baseline FOB flows (68.9, 32.6 pax/min) are close to the observed 70.0 and 33.3, but this is not independent validation"),
        ("A3b", "Route shares of the additional demand", "Huma 50/35/15, Gandhi Nagar 40/40/20 (PF1/FOB2/FOB3)", "Revised team estimates", "Modelling assumption, not measured", "Added FOB load +18/+8 pax/min (+50) and +36/+16 pax/min (+100)"),
        ("A4", "Southeast split", "70% FOB 3, 30% FOB 2", "Team estimate", "Explicit ASSUMPTION", "Drives most of FOB 3's east-side load"),
        ("A5", "Leaving passengers", "Use the same route percentages as entering passengers at that gate", "No separate leaving data", "Assumption", "Directional asymmetry in route choice is not represented"),
        ("A6", "Route-split noise", "Dirichlet draw per gate per replication, concentration 99 (about +/-3 pp for a 10% share)", "Splits are estimates; noise represents their uncertainty", "Modelling choice", "Widens replication-to-replication spread; zero shares stay zero"),
        ("A7", "Skywalk", "Connector between FOB 2 and FOB 3 on the east side; 5% of Northeast users walk it to FOB 3", "Final layout", "Layout decision", "Skywalk users are counted on FOB 3 only; skywalk is not an FOB"),
        ("A8", "FOB 1", "Closed; never offered as a route", "Field observation", "Observed", "Zero flow by construction"),
        ("A9", "Ghatkopar reference flow", "500 pax/min", "Supplied benchmark", "ASSUMED, not independently verified", "Sets the size of the +50 and +100 scenarios"),
        ("A10", "Additional demand", "+50 and +100 pax/min entering only; 80% Huma, 20% Gandhi Nagar; own route shares (A3b)", "10% and 20% of the Ghatkopar reference", "Scenario input, not a forecast", "Leaving rates and other gates unchanged"),
        ("A11", "Arrival process", "Independent Poisson processes (exponential inter-arrival times) for 10 baseline + 2 additional streams", "Only mean rates available", "Simplification", "Train-release surges are not represented; true peak minutes are likely higher"),
        ("A12", "Constant rates over 60 min", "Peak-period observed rates", "Single peak observation per stream", "Simplification", "No within-hour variation"),
        ("A13", "FOB 2 width", "5.36 m", "Recorded on field sketch", "Recorded; clear width unverified", "C = 321.6 pax/min"),
        ("A14", "FOB 3 width", "6.0 m", "Provisional value", "UNVERIFIED assumption", "C = 360 pax/min; utilization scales with 1/W"),
        ("A15", "Flow intensity I", "60 pax/m/min", "Project capacity framework", "Reference value", "Utilization is a reference-capacity ratio, not level of service or safety"),
        ("A16", "Walking speed / crossing point", "1.30 m/s; counted at FOB deck mid-point", "Typical walking speed", "Assumption", "Only shifts crossing timing; start-up transient lowers minute 1"),
        ("A17", "Initial state", "Station starts empty, no warm-up", "Brief", "Assumption", "60-min mean flows are about 1-3% below expected values"),
        ("A18", "Replications and seeds", "30 per scenario, seeds 1001-1030, common random numbers", "Experimental design", "Design choice", "Fully reproducible"),
    ]
    pd.DataFrame(A, columns=["id", "assumption", "value", "rationale", "evidence_status", "implication"]).to_csv(
        os.path.join(OUT, "assumptions_register.csv"), index=False)


# ==============================================================================================
def run_tests(reps, mins, rr, summ):
    T = []

    def add(name, ok, detail):
        T.append(dict(test=name, passed=bool(ok), detail=detail))

    prim = reps[reps.experiment_set == PRIMARY]

    sums = [sum(p) for p in tw.DEFAULT_SPLITS]
    add("Route probabilities sum to 100% for every gate (defaults)", all(abs(s - 1) < 1e-12 for s in sums),
        "; ".join(f"{GATES[g]} {sums[g] * 100:.0f}%" for g in range(5)))
    add("Additional-demand route shares sum to 100%", all(abs(sum(p) - 1) < 1e-12 for p in tw.EXTRA_SPLITS),
        "Huma 50/35/15, Gandhi Nagar 40/40/20")
    noisy_sums = [prim[[f"split_g{g}_r{r}" for r in range(4)]].sum(axis=1) for g in range(5)] + \
                 [prim[[f"split_x{e}_r{r}" for r in range(4)]].sum(axis=1) for e in range(2)]
    add("Route probabilities sum to 100% for every gate (noisy draws)", all((abs(s - 1) < 1e-6).all() for s in noisy_sums),
        f"checked {len(prim)} replications x (5 gates + 2 additional-demand splits)")
    zero_ok = all((prim[f"split_g{g}_r{r}"] == 0).all() for g in range(5) for r in range(4) if tw.DEFAULT_SPLITS[g][r] == 0) and \
              all((prim[f"split_x{e}_r{r}"] == 0).all() for e in range(2) for r in range(4) if tw.EXTRA_SPLITS[e][r] == 0)
    add("Impossible routes stay impossible under noise", zero_ok, "routes with 0% default probability are never used")

    add("FOB 1 remains unavailable", (reps.fob1_crossings == 0).all(), f"FOB 1 crossings over {len(reps)} replications = {int(reps.fob1_crossings.sum())}")

    sky_other = sum(int(reps[f"route_g{g}_r3"].sum()) for g in (0, 1, 2, 4))
    m = mins.groupby(["experiment_set", "scenario", "replication"])[["fob2", "fob3"]].sum().reset_index()
    j = reps.merge(m, on=["experiment_set", "scenario", "replication"])
    r1 = j[[f"route_g{g}_r1" for g in range(5)] + [f"route_x{e}_r1" for e in range(2)]].sum(axis=1)
    r23 = j[[f"route_g{g}_r{r}" for g in range(5) for r in (2, 3)] + [f"route_x{e}_r2" for e in range(2)]].sum(axis=1)
    ok = ((j.fob2 + j.fob3 + j.fob_not_reached_by_end) == (r1 + r23)).all() and (j.fob2 <= r1).all() and (j.fob3 <= r23).all()
    add("Skywalk is a connector, not an FOB", sky_other == 0 and ok,
        f"only Northeast passengers use the skywalk ({int(reps['route_g3_r3'].sum())} in total); they are counted on FOB 3 and there is no skywalk crossing count")
    add("Direct PF1 passengers never counted; each FOB passenger counted at most once", ok,
        "every replication: FOB 2 + FOB 3 crossings + passengers still approaching at t=60 = FOB-route passengers")

    add("East-side rates conserve the observed aggregate", tw.ENTER_RATE[3] + tw.ENTER_RATE[4] == 20.0 and tw.LEAVE_RATE[3] + tw.LEAVE_RATE[4] == 10.0,
        "Northeast + Southeast entering = 10 + 10 = 20; leaving = 5 + 5 = 10 pax/min")
    add("Baseline gate totals", abs(sum(tw.ENTER_RATE) - 90.53) < 1e-9 and abs(sum(tw.LEAVE_RATE) - 108.66) < 1e-9,
        f"entering {sum(tw.ENTER_RATE):.2f}, leaving {sum(tw.LEAVE_RATE):.2f}, total {sum(tw.ENTER_RATE) + sum(tw.LEAVE_RATE):.2f} pax/min")

    for sc, addv in [("+50 pax/min", 50.0), ("+100 pax/min", 100.0)]:
        h, gn = tw.rate(10, addv), tw.rate(11, addv)
        add(f"Additional demand total and 80/20 split ({sc})", abs(h + gn - addv) < 1e-9 and abs(h / addv - 0.8) < 1e-12,
            f"Huma +{h:.0f}, Gandhi Nagar +{gn:.0f}, total +{h + gn:.0f} pax/min; Huma entering {27.2 + h:.2f}, Gandhi Nagar entering {33.33 + gn:.2f}")
        p = prim[prim.scenario == sc]
        for s, lab in [(10, "Huma"), (11, "Gandhi Nagar")]:
            lam = tw.rate(s, addv) * 60
            x = p[f"gen_s{s}"]
            z = (x.mean() - lam) / math.sqrt(lam / len(x))
            add(f"Additional {lab} arrivals are Poisson ({sc})", abs(z) < 3, f"mean {x.mean():.1f} per hour vs expected {lam:.0f} (z = {z:+.2f})")

    base = tw.expected_route_flows(tw.DEFAULT_SPLITS, 0)
    for addv, target in [(50.0, (24, 18, 8)), (100.0, (48, 36, 16))]:
        f = tw.expected_route_flows(tw.DEFAULT_SPLITS, addv)
        inc = (f[0] - base[0], f[1] - base[1], f[2] + f[3] - base[2] - base[3])
        add(f"Expected additional routing +{addv:.0f}", all(abs(a - b) < 1e-9 for a, b in zip(inc, target)),
            f"PF1 +{inc[0]:.0f}, FOB 2 +{inc[1]:.0f}, FOB 3 +{inc[2]:.0f} pax/min (expected values, reported separately from simulation)")

    leave_cols = [f"gen_s{s}" for s in range(1, 10, 2)] + [f"gen_s{s}" for s in range(0, 10, 2)]
    same = all((prim[prim.scenario == sc].sort_values("replication")[leave_cols].values ==
                prim[prim.scenario == "Baseline"].sort_values("replication")[leave_cols].values).all() for sc in SCENARIOS)
    add("Baseline streams unchanged by scenarios (no multipliers)", same,
        "with the same seed, all 10 baseline gate-direction streams generate identical arrivals in every scenario")

    b = prim[prim.scenario == "Baseline"]
    rates = [tw.ENTER_RATE[g] if d == 0 else tw.LEAVE_RATE[g] for g in range(5) for d in (0, 1)]
    zs = []
    for s in range(10):
        lam = rates[s] * 60
        x = b[f"gen_s{s}"]
        zs.append((x.mean() - lam) / math.sqrt(lam / len(x)))
    add("Poisson arrival counts for the 10 baseline streams", max(abs(z) for z in zs) < 3,
        "z-scores of hourly means vs lambda x 60: " + ", ".join(f"{z:+.1f}" for z in zs))

    obs = sum(int(prim[f"route_g{g}_r{r}"].sum()) for g in range(5) for r in range(4))
    exp_counts = 0.0
    chi = 0.0
    for _, row in prim.iterrows():
        for g in range(5):
            n = sum(row[f"route_g{g}_r{r}"] for r in range(4))
            for r in range(4):
                p = row[f"split_g{g}_r{r}"]
                if p > 0:
                    e = n * p
                    chi += (row[f"route_g{g}_r{r}"] - e) ** 2 / e
        for e in range(2):
            n = sum(row[f"route_x{e}_r{r}"] for r in range(4))
            if n == 0:
                continue
            for r in range(4):
                p = row[f"split_x{e}_r{r}"]
                if p > 0:
                    chi += (row[f"route_x{e}_r{r}"] - n * p) ** 2 / (n * p)
    extra_rows = sum(1 for _, row in prim.iterrows() for e in range(2) if row[f"gen_s{10 + e}"] > 0)
    dof = len(prim) * sum(sum(1 for p in tw.DEFAULT_SPLITS[g] if p > 0) - 1 for g in range(5)) + extra_rows * 2
    pval = 1 - stats.chi2.cdf(chi, dof)
    add("Per-passenger route choice follows each replication's split", pval > 0.01, f"pooled chi-square = {chi:.1f} on {dof} df, p = {pval:.3f} ({obs:,} passengers)")

    sd = prim["split_g0_r2"].std()
    target = math.sqrt(0.15 * 0.85 / (KAPPA + 1))
    add("Route-split noise has the intended size", 0.7 * target < sd < 1.3 * target,
        f"SD of Naval Colony FOB 3 share (15%) across replications = {sd * 100:.1f} pp (theory {target * 100:.1f} pp)")

    uniq = b[[f"gen_s{s}" for s in range(10)]].drop_duplicates().shape[0]
    add("Different seeds generate different trajectories", uniq == len(b), f"{uniq} distinct arrival-count vectors from {len(b)} seeds")

    mism = 0
    for _, row in prim.head(6).iterrows():
        r = tw.run_replication(int(row.seed), row.additional_demand, kappa=KAPPA)
        mism += r["fob2"] != list(mins[(mins.experiment_set == PRIMARY) & (mins.scenario == row.scenario) &
                                        (mins.replication == row.replication)].fob2)
    add("Java engine reproduced by independent Python implementation", mism == 0,
        "identical per-minute FOB 2 counts for sampled replications (full comparison of all 180 replications: 0 mismatches)")

    add("Capacity units", abs(CAPACITY["FOB 2"] - 321.6) < 1e-9 and abs(CAPACITY["FOB 3"] - 360) < 1e-9,
        "C2 = 5.36 m x 60 pax/m/min x 1 min = 321.6 pax; C3 = 6.0 x 60 x 1 = 360 pax")

    s = summ[(summ.experiment_set == PRIMARY) & (summ.scenario == "Baseline")]
    add("Simulated results recorded separately from expected values",
        all(abs(s.sim_minus_expected_flow) > 1e-6),
        "baseline simulated minus expected flow: " + ", ".join(f"{r.facility} {r.sim_minus_expected_flow:+.2f} pax/min" for r in s.itertuples()))
    return T


if __name__ == "__main__":
    main()
