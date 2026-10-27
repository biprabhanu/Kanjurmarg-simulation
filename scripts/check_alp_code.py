"""
Static compile check of every Java snippet inside the .alp file.

AnyLogic is not available in the build environment, so this script extracts the code that
AnyLogic would compile (startup code, functions, events, dynamic events, dynamic text and
colour expressions, button actions, experiment parameter expressions) and compiles it with javac
against a minimal stub of the AnyLogic API (Agent, Engine, ShapeRectangle, HistogramData...).
This catches Java syntax and type errors in the model code. It does NOT prove that the
AnyLogic runtime behaves identically to the stubs.

    python3 scripts/check_alp_code.py
"""
import os
import subprocess
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALP = os.path.join(ROOT, "anylogic", "Kanjurmarg_FOB_Simulation", "Kanjurmarg_FOB_Simulation.alp")
BUILD = os.path.join(ROOT, "build", "alpcheck")

STUB = """
package kanjurmarg_fob_simulation;
import java.awt.Color;
import java.util.*;

class SpeedUnits { }
class Engine {
    enum State { IDLE, RUNNING, PAUSED, FINISHED }
    State getState() { return State.RUNNING; }
    void pause() { }
    void run() { }
}
class ShapeRectangle {
    void setWidth(double w) { } void setHeight(double h) { } void setY(double y) { } void setFillColor(Color c) { }
}
class HistogramData { void add(double v) { } }
class AgentList<T> extends ArrayList<T> { }
abstract class AgentStub {
    static final SpeedUnits MPS = new SpeedUnits();
    double time() { return 0; }
    void traceln(String fmt, Object... args) { }
    void traceln(Object o) { }
    void moveTo(double x, double y) { }
    void jumpTo(double x, double y) { }
    void setSpeed(double v, SpeedUnits u) { }
    Engine getEngine() { return new Engine(); }
}
"""


SCHED = """
    double now = 0; long seq = 0;
    PriorityQueue<double[]> q = new PriorityQueue<>((a, b) -> a[0] != b[0] ? Double.compare(a[0], b[0]) : Double.compare(a[1], b[1]));
    Map<Long, Runnable> acts = new HashMap<>();
    @Override double time() { return now; }
    void schedule(double dt, Runnable r) { long id = seq++; acts.put(id, r); q.add(new double[]{now + dt, id}); }
    /** Runs the model logic headless: start-up, events, minute ticks (cyclic, first at 60 s). */
    public static void main(String[] a) {
        Main m = new Main();
        m.onStartup();
        double nextTick = 60;
        while (!m.runFinished) {
            double tq = m.q.isEmpty() ? Double.MAX_VALUE : m.q.peek()[0];
            if (nextTick <= tq) { m.now = nextTick; m.event_minuteTick(); nextTick += 60; continue; }
            double[] e = m.q.poll(); m.now = e[0]; m.acts.remove((long) e[1]).run();
        }
        System.out.println("ANIM generated=" + m.generated + " pf1=" + m.routeCount[0] + " fob2=" + m.routeCount[1] + " fob3=" + m.routeCount[2]
            + " fob2Crossings=" + m.fob2Total + " fob3Crossings=" + m.fob3Total + " fob1=" + m.fob1Total
            + " completed=" + m.completed + " stillWalking=" + m.passengers.size() + " peakU2=" + m.peakU2);
        System.out.println("ANIM fob2PerMin=" + Arrays.toString(m.fob2PerMin));
        m.runBatch();
        System.out.println(m.batchSummary);
    }
"""


def main():
    os.makedirs(os.path.join(BUILD, "kanjurmarg_fob_simulation"), exist_ok=True)
    root = ET.parse(ALP).getroot()
    classes = {c.findtext("Name"): c for c in root.iter("ActiveObjectClass") if c.findtext("Name")}
    main = classes["Main"]
    pas = classes["Passenger"]

    def members(cls):
        out = []
        for v in cls.find("Variables").findall("Variable"):
            name = v.findtext("Name")
            props = v.find("Properties")
            typ = props.findtext("Type")
            init = props.findtext("DefaultValue/Code") or props.findtext("InitialValue/Code")
            out.append(f"    public {typ} {name}" + (f" = {init};" if init else ";"))
        return "\n".join(out)

    m = []
    m.append("package kanjurmarg_fob_simulation;\nimport java.awt.Color;\nimport java.util.*;\n")
    m.append("public class Main extends AgentStub {")
    m.append(main.findtext("AdditionalClassCode"))
    m.append(members(main))
    # shapes referenced from code
    for r in main.iter("Rectangle"):
        m.append(f"    ShapeRectangle {r.findtext('Name')} = new ShapeRectangle();")
    for h in main.iter("HistogramData"):
        m.append(f"    HistogramData {h.findtext('Name')} = new HistogramData();")
    m.append("    AgentList<Passenger> passengers = new AgentList<>();")
    m.append("    Passenger add_passengers() { Passenger p = new Passenger(); p.main = this; passengers.add(p); return p; }")
    m.append("    void remove_passengers(Passenger p) { passengers.remove(p); }")
    m.append("    void onStartup() {\n" + main.findtext("StartupCode") + "\n    }")
    for f in main.find("Functions").findall("Function"):
        ret = f.findtext("ReturnType") if f.findtext("ReturnModificator") == "RETURNS_VALUE" else "void"
        params = ", ".join(f"{p.findtext('Type')} {p.findtext('Name')}" for p in f.findall("Parameter"))
        m.append(f"    {ret} {f.findtext('Name')}({params}) {{\n{f.findtext('Body')}\n    }}")
    for e in main.find("Events").findall("Event"):
        m.append(f"    void event_{e.findtext('Name')}() {{\n{e.findtext('Action')}\n    }}")
    for d in main.find("DynamicEvents").findall("DynamicEventClass"):
        ps = [(p.findtext("Type"), p.findtext("Name")) for p in d.findall("Parameter")]
        sig = ", ".join(f"{t} {n}" for t, n in ps)
        args = ", ".join(n for t, n in ps)
        m.append(f"    void create_{d.findtext('Name')}(double dt, {sig}) {{ schedule(dt, () -> action_{d.findtext('Name')}({args})); }}")
        m.append(f"    void action_{d.findtext('Name')}({sig}) {{\n{d.findtext('Action')}\n    }}")
    k = 0
    for t in main.iter("Text"):
        code = t.findtext("TextCode")
        if code:
            k += 1
            m.append(f"    Object textCode{k}() {{ return {code}; }}")
    for c in main.iter("Control"):
        a = c.findtext("BasicProperties/ActionCode")
        if a:
            k += 1
            m.append(f"    void action{k}() {{ {a} }}")
    for ds in main.iter("DatasetExpression"):
        k += 1
        m.append(f"    double plot{k}() {{ return {ds.findtext('Expression2')}; }}")
    m.append(SCHED)
    m.append("}")

    p = ["package kanjurmarg_fob_simulation;\nimport java.awt.Color;\n",
         "public class Passenger extends AgentStub {", "    Main main;", members(pas)]
    for o in pas.iter("Oval"):
        p.append(f"    Color fill() {{ return {o.findtext('FillColorCode')}; }}")
    p.append("}")

    # experiment parameter expressions
    exp = root.find(".//SimulationExperiment")
    e = ["package kanjurmarg_fob_simulation;\n", "public class Simulation {", members(exp), "    void setup(Main root) {"]
    for prm in exp.find("Parameters").findall("Parameter"):
        code = prm.findtext("ParameterValue/Code")
        if code:
            e.append(f"        root.{prm.findtext('ParameterName')} = {code};")
    e += ["    }", "}"]

    files = {"stubs.java": STUB, "Main.java": "\n".join(m), "Passenger.java": "\n".join(p), "Simulation.java": "\n".join(e)}
    paths = []
    for name, src in files.items():
        path = os.path.join(BUILD, "kanjurmarg_fob_simulation", name if name != "stubs.java" else "AnyLogicStubs.java")
        with open(path, "w") as fh:
            fh.write(src)
        paths.append(path)
    r = subprocess.run(["javac", "-Xlint:none", "-d", os.path.join(BUILD, "classes")] + paths,
                       capture_output=True, text=True)
    out = "\n".join(l for l in (r.stdout + r.stderr).splitlines() if "JAVA_TOOL_OPTIONS" not in l)
    print(out if out else "javac: all model code compiled without errors")
    print("text expressions + actions + plot expressions checked:", k)
    if r.returncode == 0:
        run = subprocess.run(["java", "-cp", os.path.join(BUILD, "classes"), "kanjurmarg_fob_simulation.Main"],
                             capture_output=True, text=True, cwd=BUILD)
        print("\n".join(l for l in (run.stdout + run.stderr).splitlines() if "JAVA_TOOL_OPTIONS" not in l))
    return r.returncode


if __name__ == "__main__":
    raise SystemExit(main())
