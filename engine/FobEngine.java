/*
 * FobEngine — stochastic core of the Kanjurmarg FOB utilization model.
 *
 * This exact source text is embedded in the AnyLogic model (Main → Additional class code)
 * and is also compiled stand-alone by scripts/run_engine.sh, so the numbers in the CSV
 * files come from the same code that the AnyLogic model runs.
 *
 * Units used throughout:
 *   time   — seconds (the AnyLogic model time unit is also seconds)
 *   rates  — passengers per minute (as recorded in the project report)
 *   length — metres (simplified conceptual layout, NOT to scale)
 */
public static class FobEngine {

    // ---------------------------------------------------------------
    // 1. Observed inputs (IE 301 project report, Section 2.2 / 2.3)
    // ---------------------------------------------------------------
    public static final String[] ENTRANCE_NAMES = {"Naval Colony", "Huma", "Gandhi Nagar"};
    /** Entering rates, passengers/min, per entrance (observed). */
    public static final double[] ENTER_RATE = {10.00, 27.20, 33.33};
    /** Leaving rates, passengers/min, per entrance (observed). */
    public static final double[] LEAVE_RATE = {42.00, 50.00, 6.66};

    /** Route indices. FOB 1 is closed, so it is deliberately NOT a route. */
    public static final int ROUTE_PF1 = 0;
    public static final int ROUTE_FOB2 = 1;
    public static final int ROUTE_FOB3 = 2;
    public static final String[] ROUTE_NAMES = {"Direct PF1", "FOB 2", "FOB 3"};

    /** Aggregate-calibrated route probabilities (exact fractions, Section 6 of the brief). */
    public static double[] calibratedProbabilities() {
        double total = 169.19;
        return new double[] {65.89 / total, 70.00 / total, 33.30 / total};
    }

    // ---------------------------------------------------------------
    // 2. Stream definition: 6 streams = 3 entrances x 2 directions
    //    stream s: entrance = s / 2, entering if s % 2 == 0
    // ---------------------------------------------------------------
    public static final int NUM_STREAMS = 6;

    public static int entranceOf(int stream) { return stream / 2; }
    public static boolean isEntering(int stream) { return stream % 2 == 0; }

    public static double baseRatePerMin(int stream) {
        int e = entranceOf(stream);
        return isEntering(stream) ? ENTER_RATE[e] : LEAVE_RATE[e];
    }

    /** Independent random-number stream for each arrival stream, so results do not depend on event interleaving. */
    public static java.util.Random newStreamRandom(long seed, int stream) {
        return new java.util.Random(seed * 1000L + stream);
    }

    /** Exponential inter-arrival time in seconds for a Poisson stream with rate lambda (pax/min). */
    public static double drawInterarrivalSec(java.util.Random rng, double lambdaPerMin) {
        double u = rng.nextDouble();
        return -StrictMath.log(1.0 - u) * 60.0 / lambdaPerMin;
    }

    /** Pick a route by inverse-CDF sampling of the configured probabilities. */
    public static int drawRoute(java.util.Random rng, double[] probs) {
        double u = rng.nextDouble();
        double cumulative = 0.0;
        for (int r = 0; r < probs.length; r++) {
            cumulative += probs[r];
            if (u < cumulative) return r;
        }
        return probs.length - 1; // guards against rounding when probabilities sum to 0.9999999
    }

    // ---------------------------------------------------------------
    // 3. Simplified geometry (metres). Conceptual — not survey grade.
    //    x grows eastward, y grows southward (north is up on screen).
    // ---------------------------------------------------------------
    public static final double X_ENTRANCE = 4;   // west-side street entrances
    public static final double X_CONCOURSE = 12; // west footpath / foot of FOB stairs
    public static final double X_PF1 = 24;       // centre line of PF1 / 1A
    public static final double X_FOB_MID = 36;   // FOB deck mid-point over the tracks (crossing counted here)
    public static final double X_PF2 = 48;       // centre line of PF2 (island platform)
    public static final double[] ENTRANCE_Y = {16, 46, 78}; // Naval Colony (N-W), Huma (C-W), Gandhi Nagar (S-W)
    public static final double Y_FOB1 = 10;      // closed
    public static final double Y_FOB2 = 32;
    public static final double Y_FOB3 = 62;
    public static final double PLATFORM_LANDING = 6; // distance from FOB stair top to platform landing

    public static double fobY(int route) { return route == ROUTE_FOB2 ? Y_FOB2 : Y_FOB3; }

    /**
     * Way-points of a passenger's path in walking order. For FOB routes the way-point
     * with index crossingIndex(...) is the FOB deck mid-point.
     */
    public static double[][] waypoints(int entrance, boolean entering, int route) {
        double ye = ENTRANCE_Y[entrance];
        double[][] path;
        if (route == ROUTE_PF1) {
            path = new double[][] {{X_ENTRANCE, ye}, {X_CONCOURSE, ye}, {X_PF1, ye}};
        } else {
            double yf = fobY(route);
            path = new double[][] {
                {X_ENTRANCE, ye}, {X_CONCOURSE, ye}, {X_CONCOURSE, yf},
                {X_FOB_MID, yf}, {X_PF2, yf}, {X_PF2, yf + PLATFORM_LANDING}};
        }
        if (!entering) { // leaving passengers walk the same path in reverse
            double[][] reversed = new double[path.length][];
            for (int i = 0; i < path.length; i++) reversed[i] = path[path.length - 1 - i];
            path = reversed;
        }
        return path;
    }

    /** Index of the FOB mid-point way-point, or -1 for the direct PF1 route. */
    public static int crossingIndex(boolean entering, int route) {
        if (route == ROUTE_PF1) return -1;
        return entering ? 3 : 2;
    }

    public static double segmentLength(double[] a, double[] b) {
        return Math.hypot(b[0] - a[0], b[1] - a[1]);
    }

    /** Walking time (s) from appearing in the model until reaching the FOB mid-point. */
    public static double crossingDelaySec(int entrance, boolean entering, int route, double walkSpeedMps) {
        int k = crossingIndex(entering, route);
        if (k < 0) return -1;
        double[][] path = waypoints(entrance, entering, route);
        double distance = 0;
        for (int i = 0; i < k; i++) distance += segmentLength(path[i], path[i + 1]);
        return distance / walkSpeedMps;
    }

    // ---------------------------------------------------------------
    // 4. Capacity: C = W x I x T  (per one-minute interval, T = 1)
    // ---------------------------------------------------------------
    public static double capacityPerMin(double widthM, double intensityPaxPerMPerMin) {
        return widthM * intensityPaxPerMPerMin;
    }

    // ---------------------------------------------------------------
    // 5. One replication
    // ---------------------------------------------------------------
    public static class Result {
        public long seed;
        public double multiplier;
        public int durationMin;
        public int warmupMin;
        public int[] generatedByStream = new int[NUM_STREAMS];
        public int[][] routeByStream = new int[NUM_STREAMS][3];
        public int fob1Crossings = 0;           // must stay 0: FOB 1 is closed
        public int[] fob2PerMinute;
        public int[] fob3PerMinute;
        public int crossingsAfterHorizon = 0;   // FOB passengers who had not yet reached the mid-point at the end

        public int totalGenerated() {
            int n = 0;
            for (int g : generatedByStream) n += g;
            return n;
        }
        public int routeTotal(int route) {
            int n = 0;
            for (int s = 0; s < NUM_STREAMS; s++) n += routeByStream[s][route];
            return n;
        }
    }

    /**
     * Runs one replication: six independent Poisson streams, random route per passenger,
     * FOB crossing counted once, in the one-minute interval in which the passenger
     * reaches the FOB mid-point.
     */
    public static Result runReplication(long seed, double demandMultiplier, double[] routeProbs,
                                        int durationMin, int warmupMin, double walkSpeedMps) {
        Result res = new Result();
        res.seed = seed;
        res.multiplier = demandMultiplier;
        res.durationMin = durationMin;
        res.warmupMin = warmupMin;
        res.fob2PerMinute = new int[durationMin];
        res.fob3PerMinute = new int[durationMin];
        double horizonSec = durationMin * 60.0;

        for (int s = 0; s < NUM_STREAMS; s++) {
            java.util.Random rng = newStreamRandom(seed, s);
            double lambda = baseRatePerMin(s) * demandMultiplier;
            int entrance = entranceOf(s);
            boolean entering = isEntering(s);
            double t = drawInterarrivalSec(rng, lambda);
            while (t < horizonSec) {
                int route = drawRoute(rng, routeProbs);
                res.generatedByStream[s]++;
                res.routeByStream[s][route]++;
                if (route != ROUTE_PF1) {
                    double crossTime = t + crossingDelaySec(entrance, entering, route, walkSpeedMps);
                    if (crossTime < horizonSec) {
                        int minute = (int) Math.floor(crossTime / 60.0);
                        if (route == ROUTE_FOB2) res.fob2PerMinute[minute]++;
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
    // 6. Small statistics helpers used by the model dashboard
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

    /** Two-sided 95% Student-t critical value for df degrees of freedom (table + normal limit). */
    public static double t95(int df) {
        double[] table = {12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228,
                          2.201, 2.179, 2.160, 2.145, 2.131, 2.120, 2.110, 2.101, 2.093, 2.086,
                          2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042};
        if (df < 1) return Double.NaN;
        if (df <= 30) return table[df - 1];
        if (df <= 60) return 2.000;
        if (df <= 120) return 1.980;
        return 1.960;
    }
}
