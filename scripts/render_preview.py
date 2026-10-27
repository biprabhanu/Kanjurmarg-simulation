"""
Renders a static PNG preview of the AnyLogic model screen directly from the shapes stored in the
.alp file (rectangles, polylines, ovals, text). Passenger dots are positioned from the simulation
(seed 1001, baseline) at a chosen model time. Dynamic texts show values from that same run.
This is a preview drawn by this script — NOT a screenshot of AnyLogic.

    python3 scripts/render_preview.py [minute]
"""
import math
import os
import sys
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))
import fob_twin as tw  # noqa: E402

ALP = os.path.join(ROOT, "anylogic", "Kanjurmarg_FOB_Simulation", "Kanjurmarg_FOB_Simulation.alp")
SS = 2  # supersampling


def col(v, default=None):
    if v is None or v == "":
        return default
    v = int(v) & 0xFFFFFFFF
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255, (v >> 24) & 255)


def font(size, bold=False, mono=False):
    name = "DejaVuSansMono" if mono else "DejaVuSans"
    if bold:
        name += "-Bold"
    for d in ("/usr/share/fonts/truetype/dejavu/",):
        p = os.path.join(d, name + ".ttf")
        if os.path.exists(p):
            return ImageFont.truetype(p, int(size * SS * 1.05))
    return ImageFont.load_default()


def snapshot(minute, seed=1001, mult=1.0):
    """Passenger positions (metres) at model time minute*60 s and dashboard values from the run."""
    probs = tw.calibrated_probabilities()
    T = minute * 60.0
    pts = []
    gen = [0, 0, 0]
    for s in range(6):
        rng = tw.JavaRandom(seed * 1000 + s)
        lam = tw.stream_rate(s) * mult
        e, ent = s // 2, s % 2 == 0
        t = -math.log(1 - rng.next_double()) * 60 / lam
        while t < 3600:
            r = tw.draw_route(rng, probs)
            if t <= T:
                gen[r] += 1
                path = tw.waypoints(e, ent, r)
                d = (T - t) * 1.30
                for i in range(len(path) - 1):
                    seg = math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])
                    if d <= seg:
                        f = d / seg
                        pts.append((path[i][0] + f * (path[i + 1][0] - path[i][0]),
                                    path[i][1] + f * (path[i + 1][1] - path[i][1]), r))
                        break
                    d -= seg
            t += -math.log(1 - rng.next_double()) * 60 / lam
    return pts, gen


def main():
    minute = float(sys.argv[1]) if len(sys.argv) > 1 else 30.0
    root = ET.parse(ALP).getroot()
    main_cls = [c for c in root.iter("ActiveObjectClass") if c.findtext("Name") == "Main"][0]
    W, H = 1460, 1090
    img = Image.new("RGB", (W * SS, H * SS), (244, 246, 249))
    dr = ImageDraw.Draw(img, "RGBA")

    pts, gen = snapshot(minute)
    run = tw.run_replication(1001, 1.0, tw.calibrated_probabilities())
    m = int(minute)
    f2, f3 = run["fob2"][:m], run["fob3"][:m]
    u2 = [x / 321.6 * 100 for x in f2]
    u3 = [x / 360 * 100 for x in f3]
    vals = {
        "txtScenario": "Baseline   ·   demand × 1.00",
        "txtClock": f"{m:02d}:00 / 60:00 min",
        "kpi0": f"{sum(gen):,}", "kpi1": f"{sum(gen) - len(pts):,}", "kpi2": f"{len(pts):,}", "kpi3": f"{gen[0]:,}",
        "txtCap2": "Capacity C = W × 60 = 321.6 pax/min", "txtCap3": "Capacity C = W × 60 = 360.0 pax/min",
        "txtTot2": f"{sum(f2):,}", "txtTot3": f"{sum(f3):,}",
        "txtLast2": f"{f2[-1]} pax", "txtLast3": f"{f3[-1]} pax",
        "txtU2": f"{u2[-1]:.1f}%  ·  {sum(u2)/len(u2):.1f}%  ·  {max(u2):.1f}%",
        "txtU3": f"{u3[-1]:.1f}%  ·  {sum(u3)/len(u3):.1f}%  ·  {max(u3):.1f}%",
        "txtFob1": "crossings: 0",
        "txtP0": "38.944% configured", "txtP1": "41.374% configured", "txtP2": "19.682% configured",
        "txtR0": f"{gen[0]/sum(gen)*100:.2f}% realised", "txtR1": f"{gen[1]/sum(gen)*100:.2f}% realised",
        "txtR2": f"{gen[2]/sum(gen)*100:.2f}% realised",
        "txtBatchInfo": "30 replications × 3 scenarios, seeds 1001–1030, 60 min each. Results → anylogic_batch_results.csv",
    }
    batch_path = os.path.join(ROOT, "build", "alpcheck", "batch_summary.txt")
    vals["txtBatch"] = open(batch_path).read() if os.path.exists(batch_path) else ""
    widths = {"barU2": min(250, 250 * u2[-1] / 50), "barU3": min(250, 250 * u3[-1] / 50),
              "barRoutePF1": 250 * 0.38944, "barRouteFOB2": 250 * 0.41374, "barRouteFOB3": 250 * 0.19682}
    bm = {"cmpBar_b2": 21.68, "cmpBar_b3": 9.23, "cmpBar_p2": 23.83, "cmpBar_p3": 10.14, "cmpBar_q2": 26.03, "cmpBar_q3": 11.05}

    def S(v):
        return v * SS

    level_pres = main_cls.find("Presentation/Level/Presentation")
    for el in list(level_pres):
        tag = el.tag
        name = el.findtext("Name") or ""
        x, y = float(el.findtext("X") or 0), float(el.findtext("Y") or 0)
        if tag == "Rectangle":
            w, h = float(el.findtext("Width")), float(el.findtext("Height"))
            if name in widths:
                w = widths[name]
            if name in bm:
                h = 150 * bm[name] / 40
                y = y + 1 - h
            fill = col(el.findtext("FillColor"))
            line = col(el.findtext("LineColor"))
            lw = float(el.findtext("LineWidth") or 1)
            dashed = el.findtext("LineStyle") == "DASHED"
            dr.rectangle([S(x), S(y), S(x + w), S(y + h)], fill=fill,
                         outline=None if (line is None or dashed or lw == 0) else line, width=max(1, int(S(lw))))
            if dashed and line:
                for (ax, ay, bx, by) in ((x, y, x + w, y), (x, y + h, x + w, y + h), (x, y, x, y + h), (x + w, y, x + w, y + h)):
                    L = math.hypot(bx - ax, by - ay)
                    n = int(L // 8)
                    for i in range(0, n, 2):
                        dr.line([S(ax + (bx - ax) * i / n), S(ay + (by - ay) * i / n),
                                 S(ax + (bx - ax) * (i + 1) / n), S(ay + (by - ay) * (i + 1) / n)], fill=line, width=int(S(lw)))
        elif tag == "Polyline":
            pts_ = [(S(x + float(p.findtext("X"))), S(y + float(p.findtext("Y")))) for p in el.find("Points")]
            line = col(el.findtext("LineColor"))
            fill = col(el.findtext("FillColor"))
            lw = float(el.findtext("LineWidth") or 1)
            if el.findtext("Closed") == "true":
                dr.polygon(pts_, fill=fill, outline=line)
            elif el.findtext("LineStyle") == "DOTTED":
                (ax, ay), (bx, by) = pts_[0], pts_[-1]
                n = 12
                for i in range(0, n, 2):
                    dr.line([ax + (bx - ax) * i / n, ay + (by - ay) * i / n, ax + (bx - ax) * (i + 1) / n,
                             ay + (by - ay) * (i + 1) / n], fill=line, width=int(S(lw)))
            else:
                dr.line(pts_, fill=line, width=max(1, int(S(lw))))
        elif tag == "Oval":
            r = float(el.findtext("RadiusX"))
            dr.ellipse([S(x - r), S(y - r), S(x + r), S(y + r)], fill=col(el.findtext("FillColor")),
                       outline=col(el.findtext("LineColor")))
        elif tag == "Text":
            s = el.findtext("Text") or ""
            if el.findtext("TextCode"):
                s = vals.get(name, s)
            f = el.find("Font")
            fnt = font(float(f.findtext("Size")), f.findtext("Style") == "1", f.findtext("Name") == "Monospaced")
            align = el.findtext("Alignment")
            c = col(el.findtext("Color"))
            for i, line_ in enumerate(s.split("\n")):
                tw_ = dr.textlength(line_, font=fnt)
                tx = S(x) - (tw_ if align == "RIGHT" else tw_ / 2 if align == "CENTER" else 0)
                dr.text((tx, S(y) + i * fnt.size * 1.25), line_, font=fnt, fill=c, anchor="ls")
        elif tag == "Control":
            bp = el.find("BasicProperties")
            w, h = float(bp.get("Width")), float(bp.get("Height"))
            dr.rounded_rectangle([S(x), S(y), S(x + w), S(y + h)], radius=S(5), fill=(250, 250, 250), outline=(150, 158, 168), width=SS)
            lab = el.findtext("ExtendedProperties/LabelText") or ""
            fnt = font(12, True)
            dr.text((S(x + w / 2), S(y + h / 2)), lab, font=fnt, fill=(31, 41, 51), anchor="mm")
        elif tag == "TimePlot":
            w, h = float(el.findtext("Width")), float(el.findtext("Height"))
            ox, oy, cw, ch = x + 40, y + 10, w - 60, h - 60
            dr.rectangle([S(ox), S(oy), S(ox + cw), S(oy + ch)], fill=(255, 255, 255), outline=(220, 225, 232))
            for g in range(0, 41, 10):
                gy = oy + ch - ch * g / 40
                dr.line([S(ox), S(gy), S(ox + cw), S(gy)], fill=(228, 231, 235), width=1)
                dr.text((S(ox - 6), S(gy)), str(g), font=font(9), fill=(95, 107, 122), anchor="rm")
            for series, c in ((u2, (0, 161, 155)), (u3, (37, 99, 235))):
                pp = [(S(ox + cw * (i + 1) / 60), S(oy + ch - ch * v / 40)) for i, v in enumerate(series)]
                if len(pp) > 1:
                    dr.line(pp, fill=c, width=2 * SS)
            for i, (lab, c) in enumerate((("FOB 2", (0, 161, 155)), ("FOB 3", (37, 99, 235)))):
                lx = ox + 60 + i * 90
                dr.line([S(lx), S(oy + ch + 30), S(lx + 18), S(oy + ch + 30)], fill=c, width=3 * SS)
                dr.text((S(lx + 24), S(oy + ch + 30)), lab, font=font(10), fill=(95, 107, 122), anchor="lm")
        elif tag == "Histogram":
            w, h = float(el.findtext("Width")), float(el.findtext("Height"))
            ox, oy, cw, ch = x + 40, y + 10, w - 60, h - 60
            dr.rectangle([S(ox), S(oy), S(ox + cw), S(oy + ch)], fill=(255, 255, 255), outline=(220, 225, 232))
            bins = 16
            for series, c, off in ((u2, (0, 161, 155), 0), (u3, (37, 99, 235), 0.5)):
                cnt = [0] * bins
                for v in series:
                    cnt[min(bins - 1, int(v / 2.5))] += 1
                for i, n in enumerate(cnt):
                    bw = cw / bins
                    bh = ch * (n / max(1, len(series))) * 1.8
                    bx = ox + i * bw + off * bw * 0.45
                    dr.rectangle([S(bx + 1), S(oy + ch - bh), S(bx + bw * 0.45), S(oy + ch)], fill=c)
            for g in range(0, 41, 10):
                gx = ox + cw * g / 40
                dr.text((S(gx), S(oy + ch + 10)), str(g), font=font(9), fill=(95, 107, 122), anchor="mm")
            for i, (lab, c) in enumerate((("FOB 2", (0, 161, 155)), ("FOB 3", (37, 99, 235)))):
                lx = ox + 60 + i * 90
                dr.rectangle([S(lx), S(oy + ch + 25), S(lx + 12), S(oy + ch + 35)], fill=c)
                dr.text((S(lx + 18), S(oy + ch + 30)), lab, font=font(10), fill=(95, 107, 122), anchor="lm")
        elif tag == "EmbeddedObjectPresentation":
            colors = {0: (217, 119, 6), 1: (0, 161, 155), 2: (37, 99, 235)}
            for (mx, my, r) in pts:
                px, py = 40 + mx * 8, 150 + my * 8
                dr.ellipse([S(px - 3.2), S(py - 3.2), S(px + 3.2), S(py + 3.2)], fill=colors[r], outline=(255, 255, 255))
    img = img.resize((W, H), Image.LANCZOS)
    out = os.path.join(ROOT, "charts", "anylogic_screen_preview.png")
    img.save(out)
    print("saved", out, "passengers drawn:", len(pts))


if __name__ == "__main__":
    main()
