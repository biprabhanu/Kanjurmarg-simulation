/*
 * FobEngine — stochastic core of the Kanjurmarg FOB utilization model (version 2, final assumptions).
 *
 * This exact source text is embedded in the AnyLogic model (Main → Additional class code)
 * and is also compiled stand-alone by scripts/run_engine.sh, so the CSV results come from the
 * same code that the AnyLogic model runs.
 *
 * Units used throughout:
 *   time   — seconds (the AnyLogic model time unit is also seconds)
 *   rates  — passengers per minute
 *   length — metres (simplified conceptual layout, NOT to scale)
 */
public static class FobEngine {

    // ---------------------------------------------------------------
    // 1. Gates and observed baseline demand (pax/min)
    // ---------------------------------------------------------------
    public static final int NAVAL_COLONY = 0, HUMA = 1, GANDHI_NAGAR = 2, NORTHEAST = 3, SOUTHEAST = 4;
    public static final int NUM_GATES = 5;
    public static final String[] GATE_NAMES = {"Naval Colony", "Huma", "Gandhi Nagar", "Northeast", "Southeast"};

    /** Entering rates. Northeast/Southeast = observed East-side 20 pax/min split 50/50 (ASSUMPTION). */
    public static final double[] ENTER_RATE = {10.00, 27.20, 33.33, 10.00, 10.00};
    /** Leaving rates. Northeast/Southeast = observed East-side 10 pax/min split 50/50 (ASSUMPTION). */
    public static final double[] LEAVE_RATE = {42.00, 50.00, 6.66, 5.00, 5.00};

    /** Additional (Ghatkopar-referenced) incoming demand is shared 80% Huma / 20% Gandhi Nagar. */
    public static final double EXTRA_SHARE_HUMA = 0.80;
    public static final double EXTRA_SHARE_GANDHI_NAGAR = 0.20;

    // ---------------------------------------------------------------
    // 2. Routes. FOB 1 is closed, so it is deliberately NOT a route.
    //    The skywalk is a connector between FOB 2 and FOB 3 on the east side, not an FOB.
    // ---------------------------------------------------------------
    public static final int ROUTE_PF1 = 0;      // direct level access to PF1/PF1A
    public static final int ROUTE_FOB2 = 1;     // via FOB 2
    public static final int ROUTE_FOB3 = 2;     // via FOB 3
    public static final int ROUTE_SKYWALK = 3;  // Northeast: along the skywalk, then across FOB 3 (counted on FOB 3)
    public static final int NUM_ROUTES = 4;
    public static final String[] ROUTE_NAMES = {"Direct PF1/PF1A", "FOB 2", "FOB 3", "Skywalk then FOB 3"};

    /** Baseline route-choice assumptions per gate {PF1, FOB 2, FOB 3, skywalk}. Used for entering AND leaving. */
    public static double[][] defaultGateSplits() {
        return new double[][] {
            {0.60, 0.25, 0.15, 0.00},   // Naval Colony
            {0.55, 0.30, 0.15, 0.00},   // Huma
            {0.60, 0.35, 0.05, 0.00},   // Gandhi Nagar
            {0.00, 0.95, 0.00, 0.05},   // Northeast
            {0.00, 0.30, 0.70, 0.00},   // Southeast
        };
    }

    /** Route shares of the ADDITIONAL (metro-related) incoming passengers: row 0 = Huma, row 1 = Gandhi Nagar. */
    public static double[][] defaultExtraSplits() {
        return new double[][] {
            {0.50, 0.35, 0.15, 0.00},   // Huma additional demand
            {0.40, 0.40, 0.20, 0.00},   // Gandhi Nagar additional demand
        };
    }

    /** Route split that applies to a stream: the gate split, or the additional-demand split for streams 10 and 11. */
    public static double[] splitForStream(int stream, double[][] gateSplits, double[][] extraSplits) {
        if (stream >= 10) return extraSplits[stream - 10];
        return gateSplits[gateOf(stream)];
    }

    /** Additional-demand splits: rows sum to 1, no skywalk (Huma and Gandhi Nagar are west gates). */
    public static void validateExtraSplits(double[][] extra) {
        for (int i = 0; i < 2; i++) {
            double sum = 0;
            for (int r = 0; r < NUM_ROUTES; r++) {
                if (extra[i][r] < 0) throw new IllegalArgumentException("Negative additional-demand route probability");
                sum += extra[i][r];
            }
            if (Math.abs(sum - 1.0) > 1e-9) throw new IllegalArgumentException("Additional-demand route probabilities sum to " + sum);
            if (extra[i][ROUTE_SKYWALK] > 0) throw new IllegalArgumentException("Huma / Gandhi Nagar have no skywalk access");
        }
    }

    /** East gates cannot reach PF1 without crossing a bridge; west gates have no skywalk access. */
    public static void validateSplits(double[][] splits) {
        for (int g = 0; g < NUM_GATES; g++) {
            double sum = 0;
            for (int r = 0; r < NUM_ROUTES; r++) {
                if (splits[g][r] < 0) throw new IllegalArgumentException("Negative route probability at " + GATE_NAMES[g]);
                sum += splits[g][r];
            }
            if (Math.abs(sum - 1.0) > 1e-9) throw new IllegalArgumentException("Route probabilities at " + GATE_NAMES[g] + " sum to " + sum);
            if (isEastGate(g) && splits[g][ROUTE_PF1] > 0) throw new IllegalArgumentException(GATE_NAMES[g] + " has no direct PF1 access");
            if (!isEastGate(g) && splits[g][ROUTE_SKYWALK] > 0) throw new IllegalArgumentException(GATE_NAMES[g] + " has no skywalk access");
        }
    }

    public static boolean isEastGate(int gate) { return gate == NORTHEAST || gate == SOUTHEAST; }

    // ---------------------------------------------------------------
    // 3. Arrival streams
    //    s = 0..9 : gate (s / 2), entering if s is even, leaving if odd
    //    s = 10   : additional entering demand at Huma
    //    s = 11   : additional entering demand at Gandhi Nagar
    // ---------------------------------------------------------------
    public static final int NUM_STREAMS = 12;

    public static int gateOf(int stream) {
        if (stream < 10) return stream / 2;
        return stream == 10 ? HUMA : GANDHI_NAGAR;
    }

    public static boolean isEntering(int stream) { return stream >= 10 || stream % 2 == 0; }

    public static boolean isExtraStream(int stream) { return stream >= 10; }

    /** Mean rate (pax/min) of a stream for a given additional-demand scenario (0, 50 or 100 pax/min). */
    public static double ratePerMin(int stream, double additionalDemand) {
        if (stream == 10) return additionalDemand * EXTRA_SHARE_HUMA;
        if (stream == 11) return additionalDemand * EXTRA_SHARE_GANDHI_NAGAR;
        int g = gateOf(stream);
        return isEntering(stream) ? ENTER_RATE[g] : LEAVE_RATE[g];
    }

    /** Independent random-number stream for each arrival stream (results do not depend on event order). */
    public static java.util.Random newStreamRandom(long seed, int stream) {
        return new java.util.Random(seed * 1000L + stream);
    }

    /** Separate random stream used only for the route-split noise of a replication. */
    public static java.util.Random newSplitNoiseRandom(long seed) {
        return new java.util.Random(seed * 1000L + 500L);
    }

    /** Exponential inter-arrival time in seconds for a Poisson stream with rate lambda (pax/min). */
    public static double drawInterarrivalSec(java.util.Random rng, double lambdaPerMin) {
        double u = rng.nextDouble();
        return -StrictMath.log(1.0 - u) * 60.0 / lambdaPerMin;
    }

    /** Pick a route by inverse-CDF sampling of the gate's probabilities. */
    public static int drawRoute(java.util.Random rng, double[] probs) {
        double u = rng.nextDouble();
        double cumulative = 0.0;
        int last = 0;
        for (int r = 0; r < probs.length; r++) {
            if (probs[r] <= 0) continue;
            cumulative += probs[r];
            last = r;
            if (u < cumulative) return r;
        }
        return last; // guards against rounding when probabilities sum to 0.9999999
    }

    // ---------------------------------------------------------------
    // 4. Route-split noise: the gate splits are estimates, so each replication draws its own
    //    split from a Dirichlet distribution centred on the estimates. Concentration kappa = 99
    //    gives a standard deviation of about 3 percentage points for a 10% share.
    //    Zero shares stay zero (impossible routes remain impossible). kappa <= 0 switches noise off.
    // ---------------------------------------------------------------
    public static double[][] noisySplits(double[][] base, double kappa, java.util.Random rng) {
        double[][] out = new double[base.length][NUM_ROUTES];
        for (int g = 0; g < base.length; g++) {
            if (kappa <= 0) { out[g] = base[g].clone(); continue; }
            double total = 0;
            for (int r = 0; r < NUM_ROUTES; r++) {
                out[g][r] = base[g][r] > 0 ? drawGamma(rng, kappa * base[g][r]) : 0.0;
                total += out[g][r];
            }
            for (int r = 0; r < NUM_ROUTES; r++) out[g][r] /= total;
        }
        return out;
    }

    /** Standard normal by Box–Muller using two uniforms from rng. */
    public static double drawNormal(java.util.Random rng) {
        double u1 = rng.nextDouble();
        double u2 = rng.nextDouble();
        return StrictMath.sqrt(-2.0 * StrictMath.log(1.0 - u1)) * StrictMath.cos(2.0 * Math.PI * u2);
    }

    /** Gamma(shape, 1) by Marsaglia–Tsang (valid for shape >= 1; all shapes here are >= 4.95). */
    public static double drawGamma(java.util.Random rng, double shape) {
        if (shape < 1) throw new IllegalArgumentException("shape must be >= 1");
        double d = shape - 1.0 / 3.0;
        double c = 1.0 / StrictMath.sqrt(9.0 * d);
        while (true) {
            double x = drawNormal(rng);
            double v = 1.0 + c * x;
            if (v <= 0) continue;
            v = v * v * v;
            double u = rng.nextDouble();
            if (u < 1.0 - 0.0331 * x * x * x * x) return d * v;
            if (StrictMath.log(u) < 0.5 * x * x + d * (1.0 - v + StrictMath.log(v))) return d * v;
        }
    }

    // ---------------------------------------------------------------
    // 5. Simplified geometry (metres). Conceptual — not survey grade.
    //    x grows eastward, y grows southward (north is up on screen).
    // ---------------------------------------------------------------
    public static final double X_WEST_GATE = 4;   // west-side street gates
    public static final double X_CONCOURSE = 12;  // west footpath / foot of FOB stairs
    public static final double X_PF1 = 24;        // PF1 / PF1A centre line
    public static final double X_FOB_MID = 36;    // FOB deck mid-point over the tracks: crossings are counted here
    public static final double X_PF2 = 48;        // PF2 (island platform) centre line
    public static final double X_SKYWALK = 70;    // east skywalk linking FOB 2 and FOB 3
    public static final double X_EAST_GATE = 78;  // Northeast / Southeast skywalk exits
    public static final double[] GATE_Y = {16, 46, 78, 8, 80};   // Northeast exit sits at the north end, beside (outside) the closed FOB 1
    public static final double Y_FOB1 = 8;        // closed
    public static final double Y_FOB2 = 32;
    public static final double Y_FOB3 = 62;
    public static final double LANDING = 6;       // stair from FOB deck down to the platform

    public static double gateX(int gate) { return isEastGate(gate) ? X_EAST_GATE : X_WEST_GATE; }

    /** Way-points of a passenger's path in walking order (entering direction reversed for leaving). */
    public static double[][] waypoints(int gate, boolean entering, int route) {
        double gy = GATE_Y[gate];
        double[][] path;
        if (!isEastGate(gate)) {
            if (route == ROUTE_PF1) {
                path = new double[][] {{X_WEST_GATE, gy}, {X_CONCOURSE, gy}, {X_PF1, gy}};
            } else {
                double fy = (route == ROUTE_FOB2) ? Y_FOB2 : Y_FOB3;
                path = new double[][] {{X_WEST_GATE, gy}, {X_CONCOURSE, gy}, {X_CONCOURSE, fy},
                    {X_FOB_MID, fy}, {X_PF2, fy}, {X_PF2, fy + LANDING}};
            }
        } else {
            // East gates: along the skywalk to the chosen bridge, then west across it to PF1/PF1A.
            boolean viaFob2 = (route == ROUTE_FOB2);
            double fy = viaFob2 ? Y_FOB2 : Y_FOB3;
            double landingY = viaFob2 ? fy + LANDING : fy - LANDING;
            path = new double[][] {{X_EAST_GATE, gy}, {X_SKYWALK, gy}, {X_SKYWALK, fy},
                {X_FOB_MID, fy}, {X_PF1, fy}, {X_PF1, landingY}};
        }
        if (!entering) {
            double[][] reversed = new double[path.length][];
            for (int i = 0; i < path.length; i++) reversed[i] = path[path.length - 1 - i];
            path = reversed;
        }
        return path;
    }

    /** Index of the FOB mid-point way-point, or -1 for the direct PF1 route. */
    public static int crossingIndex(double[][] path) {
        for (int i = 0; i < path.length; i++) if (path[i][0] == X_FOB_MID) return i;
        return -1;
    }

    /** Which FOB a route is counted on: 2, 3, or 0 (none). */
    public static int fobOf(int route) {
        if (route == ROUTE_FOB2) return 2;
        if (route == ROUTE_FOB3 || route == ROUTE_SKYWALK) return 3;
        return 0;
    }

    public static double segmentLength(double[] a, double[] b) {
        return Math.hypot(b[0] - a[0], b[1] - a[1]);
    }

    /** Walking time (s) from appearing in the model until reaching the FOB mid-point (-1 if none). */
    public static double crossingDelaySec(int gate, boolean entering, int route, double walkSpeedMps) {
        double[][] path = waypoints(gate, entering, route);
        int k = crossingIndex(path);
        if (k < 0) return -1;
        double distance = 0;
        for (int i = 0; i < k; i++) distance += segmentLength(path[i], path[i + 1]);
        return distance / walkSpeedMps;
    }

    // ---------------------------------------------------------------
    // 6. Capacity: C = W x I x T  (per one-minute interval, T = 1)
    // ---------------------------------------------------------------
    public static double capacityPerMin(double widthM, double intensityPaxPerMPerMin) {
        return widthM * intensityPaxPerMPerMin;
    }

    /** Expected (mean) route flows in pax/min before random variation, for given splits. */
    public static double[] expectedRouteFlows(double[][] splits, double[][] extraSplits, double additionalDemand) {
        double[] flow = new double[NUM_ROUTES];
        for (int s = 0; s < NUM_STREAMS; s++) {
            double lambda = ratePerMin(s, additionalDemand);
            double[] p = splitForStream(s, splits, extraSplits);
            for (int r = 0; r < NUM_ROUTES; r++) flow[r] += lambda * p[r];
        }
        return flow;
    }

    // ---------------------------------------------------------------
    // 7. One replication
    // ---------------------------------------------------------------
    public static class Result {
        public long seed;
        public double additionalDemand;
        public int durationMin;
        public double[][] splitsUsed;           // gate splits drawn for this replication
        public double[][] extraSplitsUsed;      // additional-demand splits drawn for this replication
        public int[] generatedByStream = new int[NUM_STREAMS];
        public int[][] routeByGate = new int[NUM_GATES][NUM_ROUTES];   // baseline streams only
        public int[][] routeExtra = new int[2][NUM_ROUTES];            // additional streams: 0 = Huma, 1 = Gandhi Nagar
        public int fob1Crossings = 0;           // must stay 0: FOB 1 is closed
        public int[] fob2PerMinute;
        public int[] fob3PerMinute;
        public int crossingsAfterHorizon = 0;   // FOB passengers not yet at the mid-point when the run ends

        public int totalGenerated() {
            int n = 0;
            for (int x : generatedByStream) n += x;
            return n;
        }
        public int routeTotal(int route) {
            int n = 0;
            for (int g = 0; g < NUM_GATES; g++) n += routeByGate[g][route];
            n += routeExtra[0][route] + routeExtra[1][route];
            return n;
        }
    }

    /**
     * Runs one replication: 12 independent Poisson streams (10 baseline gate-direction streams plus
     * 2 additional-demand streams), route splits drawn once per replication (noise), and a
     * random route per passenger. Each FOB crossing is counted once, in the minute the passenger
     * reaches the FOB deck mid-point.
     */
    public static Result runReplication(long seed, double additionalDemand, double[][] baseSplits, double[][] extraSplits,
                                        double kappa, int durationMin, double walkSpeedMps) {
        validateSplits(baseSplits);
        validateExtraSplits(extraSplits);
        Result res = new Result();
        res.seed = seed;
        res.additionalDemand = additionalDemand;
        res.durationMin = durationMin;
        java.util.Random noise = newSplitNoiseRandom(seed);
        res.splitsUsed = noisySplits(baseSplits, kappa, noise);
        res.extraSplitsUsed = noisySplits(extraSplits, kappa, noise);
        res.fob2PerMinute = new int[durationMin];
        res.fob3PerMinute = new int[durationMin];
        double horizonSec = durationMin * 60.0;

        for (int s = 0; s < NUM_STREAMS; s++) {
            double lambda = ratePerMin(s, additionalDemand);
            if (lambda <= 0) continue;                    // e.g. no additional demand in the baseline
            java.util.Random rng = newStreamRandom(seed, s);
            int gate = gateOf(s);
            boolean entering = isEntering(s);
            double t = drawInterarrivalSec(rng, lambda);
            while (t < horizonSec) {
                int route = drawRoute(rng, splitForStream(s, res.splitsUsed, res.extraSplitsUsed));
                res.generatedByStream[s]++;
                if (isExtraStream(s)) res.routeExtra[s - 10][route]++;
                else res.routeByGate[gate][route]++;
                int fob = fobOf(route);
                if (fob != 0) {
                    double crossTime = t + crossingDelaySec(gate, entering, route, walkSpeedMps);
                    if (crossTime < horizonSec) {
                        int minute = (int) Math.floor(crossTime / 60.0);
                        if (fob == 2) res.fob2PerMinute[minute]++;
                        else res.fob3PerMinute[minute]++;
                    } else {
                        res.crossingsAfterHorizon++;
                    }
                }
                t += drawInterarrivalSec(rng, lambda);
            }
        }
        return res;
    }

    // ---------------------------------------------------------------
    // 8. Small statistics helpers used by the model dashboard
    // ---------------------------------------------------------------
    public static double mean(double[] x) {
        double s = 0;
        for (double v : x) s += v;
        return x.length == 0 ? Double.NaN : s / x.length;
    }

    public static double sampleStdDev(double[] x) {
        if (x.length < 2) return Double.NaN;
        double m = mean(x), ss = 0;
        for (double v : x) ss += (v - m) * (v - m);
        return Math.sqrt(ss / (x.length - 1));
    }

    /** Percentile with linear interpolation between order statistics (same rule as numpy's default). */
    public static double percentile(double[] x, double p) {
        double[] sorted = x.clone();
        java.util.Arrays.sort(sorted);
        double pos = (sorted.length - 1) * p / 100.0;
        int lo = (int) Math.floor(pos);
        int hi = (int) Math.ceil(pos);
        return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
    }

    /** Two-sided 95% Student-t critical value for df degrees of freedom. */
    public static double t95(int df) {
        double[] table = {12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228,
                          2.201, 2.179, 2.160, 2.145, 2.131, 2.120, 2.110, 2.101, 2.093, 2.086,
                          2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042};
        if (df < 1) return Double.NaN;
        if (df <= 30) return table[df - 1];
        if (df <= 40) return 2.021;
        if (df <= 60) return 2.000;
        if (df <= 120) return 1.980;
        return 1.960;
    }
}
