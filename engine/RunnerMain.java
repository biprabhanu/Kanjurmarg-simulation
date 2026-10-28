/*
 * Stand-alone batch runner. FobEngine.java is pasted inside this class at build time by
 * scripts/run_engine.sh (the same text that is embedded in the AnyLogic model), then compiled
 * with javac and executed. Writes raw replication outputs that python/analyze.py summarises.
 *
 * Usage: java EngineRunner <outDir> <replications> <durationMin> <walkSpeed> <baseSeed> <kappa>
 *
 * Two experiment sets are run with the same seeds (common random numbers):
 *   "with_split_noise" — primary results, route splits drawn per replication (kappa)
 *   "fixed_splits"     — same model with the route splits held at the estimates (kappa = 0),
 *                        used only to show how much of the variability comes from split uncertainty
 */
    public static void main(String[] args) throws Exception {
        String outDir = args.length > 0 ? args[0] : ".";
        int reps = args.length > 1 ? Integer.parseInt(args[1]) : 30;
        int duration = args.length > 2 ? Integer.parseInt(args[2]) : 60;
        double speed = args.length > 3 ? Double.parseDouble(args[3]) : 1.30;
        long baseSeed = args.length > 4 ? Long.parseLong(args[4]) : 1001L;
        double kappa = args.length > 5 ? Double.parseDouble(args[5]) : 99.0;

        double[][] base = FobEngine.defaultGateSplits();
        double[][] extra = FobEngine.defaultExtraSplits();
        String[] setNames = {"with_split_noise", "fixed_splits"};
        double[] kappas = {kappa, 0.0};
        String[] scenarioNames = {"Baseline", "+50 pax/min", "+100 pax/min"};
        double[] additional = {0.0, 50.0, 100.0};

        java.io.PrintWriter repsW = new java.io.PrintWriter(outDir + "/raw_replications.csv");
        java.io.PrintWriter minsW = new java.io.PrintWriter(outDir + "/raw_minutes.csv");
        StringBuilder head = new StringBuilder("experiment_set,scenario,additional_demand,replication,seed");
        for (int s = 0; s < FobEngine.NUM_STREAMS; s++) head.append(",gen_s").append(s);
        for (int g = 0; g < FobEngine.NUM_GATES; g++)
            for (int r = 0; r < FobEngine.NUM_ROUTES; r++) head.append(",route_g").append(g).append("_r").append(r);
        for (int g = 0; g < FobEngine.NUM_GATES; g++)
            for (int r = 0; r < FobEngine.NUM_ROUTES; r++) head.append(",split_g").append(g).append("_r").append(r);
        for (int e = 0; e < 2; e++)
            for (int r = 0; r < FobEngine.NUM_ROUTES; r++) head.append(",route_x").append(e).append("_r").append(r);
        for (int e = 0; e < 2; e++)
            for (int r = 0; r < FobEngine.NUM_ROUTES; r++) head.append(",split_x").append(e).append("_r").append(r);
        head.append(",fob1_crossings,fob_not_reached_by_end");
        repsW.println(head);
        minsW.println("experiment_set,scenario,additional_demand,replication,seed,minute,fob2,fob3");

        for (int k = 0; k < setNames.length; k++) {
            for (int sc = 0; sc < additional.length; sc++) {
                for (int r = 0; r < reps; r++) {
                    long seed = baseSeed + r;
                    FobEngine.Result res = FobEngine.runReplication(seed, additional[sc], base, extra, kappas[k], duration, speed);
                    StringBuilder sb = new StringBuilder();
                    sb.append(setNames[k]).append(',').append(scenarioNames[sc]).append(',').append(additional[sc])
                      .append(',').append(r + 1).append(',').append(seed);
                    for (int s = 0; s < FobEngine.NUM_STREAMS; s++) sb.append(',').append(res.generatedByStream[s]);
                    for (int g = 0; g < FobEngine.NUM_GATES; g++)
                        for (int q = 0; q < FobEngine.NUM_ROUTES; q++) sb.append(',').append(res.routeByGate[g][q]);
                    for (int g = 0; g < FobEngine.NUM_GATES; g++)
                        for (int q = 0; q < FobEngine.NUM_ROUTES; q++)
                            sb.append(',').append(String.format(java.util.Locale.ROOT, "%.8f", res.splitsUsed[g][q]));
                    for (int e = 0; e < 2; e++)
                        for (int q = 0; q < FobEngine.NUM_ROUTES; q++) sb.append(',').append(res.routeExtra[e][q]);
                    for (int e = 0; e < 2; e++)
                        for (int q = 0; q < FobEngine.NUM_ROUTES; q++)
                            sb.append(',').append(String.format(java.util.Locale.ROOT, "%.8f", res.extraSplitsUsed[e][q]));
                    sb.append(',').append(res.fob1Crossings).append(',').append(res.crossingsAfterHorizon);
                    repsW.println(sb);
                    for (int m = 0; m < duration; m++) {
                        minsW.println(setNames[k] + "," + scenarioNames[sc] + "," + additional[sc] + "," + (r + 1) + ","
                                + seed + "," + (m + 1) + "," + res.fob2PerMinute[m] + "," + res.fob3PerMinute[m]);
                    }
                }
            }
        }
        repsW.close();
        minsW.close();
        System.out.println("Done: " + setNames.length * additional.length * reps + " replications written to " + outDir);
    }
