/*
 * Stand-alone batch runner. FobEngine.java is pasted inside this class at build time by
 * scripts/run_engine.sh (the same text that is embedded in the AnyLogic model), then compiled
 * with javac and executed. Writes raw replication outputs that the Python analysis summarises.
 *
 * Usage: java EngineRunner <outDir> <replications> <durationMin> <warmupMin> <walkSpeed> <baseSeed>
 */
    public static void main(String[] args) throws Exception {
        String outDir = args.length > 0 ? args[0] : ".";
        int reps = args.length > 1 ? Integer.parseInt(args[1]) : 30;
        int duration = args.length > 2 ? Integer.parseInt(args[2]) : 60;
        int warmup = args.length > 3 ? Integer.parseInt(args[3]) : 0;
        double speed = args.length > 4 ? Double.parseDouble(args[4]) : 1.30;
        long baseSeed = args.length > 5 ? Long.parseLong(args[5]) : 1001L;

        double third = 1.0 / 3.0;
        double[] cal = FobEngine.calibratedProbabilities();
        double fobShare = cal[1] + cal[2];
        double lowDirectPf1 = 0.20;
        String[] setNames = {"calibrated", "equal_split", "alt_fob_balanced", "alt_low_direct"};
        double[][] sets = {
            cal,
            {third, third, third},
            {cal[0], fobShare / 2.0, fobShare / 2.0},
            {lowDirectPf1, (1 - lowDirectPf1) * 70.0 / 103.3, (1 - lowDirectPf1) * 33.3 / 103.3}
        };
        String[] scenarioNames = {"Baseline", "+10%", "+20%"};
        double[] multipliers = {1.00, 1.10, 1.20};

        java.io.PrintWriter reps_w = new java.io.PrintWriter(outDir + "/raw_replications.csv");
        java.io.PrintWriter mins_w = new java.io.PrintWriter(outDir + "/raw_minutes.csv");
        java.io.PrintWriter sets_w = new java.io.PrintWriter(outDir + "/raw_route_sets.csv");
        reps_w.println("route_set,scenario,multiplier,replication,seed,gen_s0,gen_s1,gen_s2,gen_s3,gen_s4,gen_s5,"
                + "route_pf1,route_fob2,route_fob3,fob1_crossings,fob_not_reached_by_end");
        mins_w.println("route_set,scenario,multiplier,replication,seed,minute,fob2,fob3");
        sets_w.println("route_set,p_pf1,p_fob2,p_fob3");
        for (int k = 0; k < sets.length; k++) {
            sets_w.printf(java.util.Locale.ROOT, "%s,%.10f,%.10f,%.10f%n", setNames[k], sets[k][0], sets[k][1], sets[k][2]);
        }
        sets_w.close();

        for (int k = 0; k < sets.length; k++) {
            for (int sc = 0; sc < multipliers.length; sc++) {
                for (int r = 0; r < reps; r++) {
                    long seed = baseSeed + r; // common random numbers across scenarios
                    FobEngine.Result res = FobEngine.runReplication(seed, multipliers[sc], sets[k], duration, warmup, speed);
                    StringBuilder sb = new StringBuilder();
                    sb.append(setNames[k]).append(',').append(scenarioNames[sc]).append(',')
                      .append(multipliers[sc]).append(',').append(r + 1).append(',').append(seed);
                    for (int s = 0; s < FobEngine.NUM_STREAMS; s++) sb.append(',').append(res.generatedByStream[s]);
                    for (int route = 0; route < 3; route++) sb.append(',').append(res.routeTotal(route));
                    sb.append(',').append(res.fob1Crossings).append(',').append(res.crossingsAfterHorizon);
                    reps_w.println(sb);
                    for (int m = 0; m < duration; m++) {
                        mins_w.println(setNames[k] + "," + scenarioNames[sc] + "," + multipliers[sc] + "," + (r + 1)
                                + "," + seed + "," + (m + 1) + "," + res.fob2PerMinute[m] + "," + res.fob3PerMinute[m]);
                    }
                }
            }
        }
        reps_w.close();
        mins_w.close();
        System.out.println("Done: " + sets.length * multipliers.length * reps + " replications written to " + outDir);
    }
