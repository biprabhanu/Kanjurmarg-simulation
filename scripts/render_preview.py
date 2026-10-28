"""
Renders a static PNG preview of the AnyLogic model screen directly from the shapes stored in the
.alp file (rectangles, rounded rectangles, polylines, ovals, text). Passenger dots are positioned
from the simulation (seed 1001) at a chosen model time, and dynamic values (utilization, deck colours)
come from that same run. This is a preview drawn by this script — NOT a screenshot of AnyLogic.

    python3 scripts/render_preview.py [minute] [additional_demand]
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
OX, OY, PXM = 40, 150, 8.0
ROUTE_COL = {0: (217, 119, 6), 1: (0, 161, 155), 2: (37, 99, 235), 3: (124, 58, 237)}


def col(v, default=None):
    if v is None or v == "":
        return default
    v = int(v) & 0xFFFFFFFF
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255, (v >> 24) & 255)


def font(size, bold=False, mono=False):
    name = ("DejaVuSansMono" if mono else "DejaVuSans") + ("-Bold" if bold else "")
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}.ttf", int(size * SS * 1.05))


def heat(u):
    t = max(0.0, min(1.0, u / 60.0))
    low, mid, high = (205, 237, 236), (253, 214, 130), (239, 108, 96)
    a, b = (low, mid) if t < 0.5 else (mid, high)
    k = t / 0.5 if t < 0.5 else (t - 0.5) / 0.5
    return tuple(int(round(a[i] + (b[i] - a[i]) * k)) for i in range(3)) + (255,)


def snapshot(minute, seed=1001, additional=0.0):
    """Passenger positions (metres) at model time minute*60 s, using the same random streams as the engine."""
    T = minute * 60.0
    splits = tw.noisy_splits(tw.DEFAULT_SPLITS, 99.0, tw.JavaRandom(seed * 1000 + 500))
    pts = []
    for s in range(tw.NUM_STREAMS):
        lam = tw.rate(s, additional)
        if lam <= 0:
            continue
        rng = tw.JavaRandom(seed * 1000 + s)
        g, ent = tw.gate_of(s), tw.is_entering(s)
        t = -math.log(1 - rng.next_double()) * 60 / lam
        while t < 3600:
            r = tw.draw_route(rng, splits[g])
            if t <= T:
                path = tw.waypoints(g, ent, r)
                d = (T - t) * 1.30
                for i in range(len(path) - 1):
                    seg = math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])
                    if d <= seg:
                        f = d / seg
                        pts.append((path[i][0] + f * (path[i + 1][0] - path[i][0]),
                                    path[i][1] + f * (path[i + 1][1] - path[i][1]), ent))
                        break
                    d -= seg
            t += -math.log(1 - rng.next_double()) * 60 / lam
    return pts


def dashed(dr, a, b, color, width, dash, gap):
    (ax, ay), (bx, by) = a, b
    L = math.hypot(bx - ax, by - ay)
    if L == 0:
        return
    pos = 0
    while pos < L:
        e = min(L, pos + dash)
        dr.line([ax + (bx - ax) * pos / L, ay + (by - ay) * pos / L, ax + (bx - ax) * e / L, ay + (by - ay) * e / L],
                fill=color, width=width)
        pos += dash + gap


def main():
    minute = int(float(sys.argv[1])) if len(sys.argv) > 1 else 30
    additional = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    root = ET.parse(ALP).getroot()
    main_cls = [c for c in root.iter("ActiveObjectClass") if c.findtext("Name") == "Main"][0]
    W, H = 1480, 1100
    img = Image.new("RGB", (W * SS, H * SS), (244, 246, 249))
    dr = ImageDraw.Draw(img, "RGBA")

    pts = snapshot(minute, additional=additional)
    run = tw.run_replication(1001, additional)
    f2, f3 = run["fob2"][:minute], run["fob3"][:minute]
    u2 = [x / 321.6 * 100 for x in f2]
    u3 = [x / 360 * 100 for x in f3]
    label = {0: "Baseline", 50: "+50 pax/min", 100: "+100 pax/min"}[int(additional)]
    vals = {
        "txtScenario": f"{label}   ·   +{additional:.0f} pax/min extra",
        "txtClock": f"{minute:02d}:00 / 60:00",
        "txtCap2": "W 5.36 m · C = 321.6 pax/min", "txtCap3": "W 6.0 m · C = 360.0 pax/min",
        "txtNow2": f"{u2[-1]:.1f}%", "txtNow3": f"{u3[-1]:.1f}%",
        "txtMean2": f"{sum(u2) / len(u2):.1f}%", "txtMean3": f"{sum(u3) / len(u3):.1f}%",
        "txtPeak2": f"{max(u2):.1f}%", "txtPeak3": f"{max(u3):.1f}%",
        "txtBatchInfo": "",
    }
    bpath = os.path.join(ROOT, "build", "alpcheck", "batch_summary.txt")
    vals["txtBatch"] = open(bpath).read().rstrip() if os.path.exists(bpath) else ""
    bm = {}
    for line in vals["txtBatch"].splitlines()[1:]:
        parts = line.split()
        key = {"Base": "b", "+50": "p", "+100": "q"}[parts[0]]
        bm[f"cmpBar_{key}{parts[1]}"] = float(parts[2].rstrip("%"))
        vals[f"cmpVal_{key}{parts[1]}"] = f"{float(parts[2].rstrip('%')):.1f}%"
        continue
        u = float(line.split("%")[0].split()[-1])
        bm[f"cmpBar_{key}{'2' if ' 2 ' in line[:22] else '3'}"] = u
    widths = {"barU2": min(300, 300 * u2[-1] / 50), "barU3": min(300, 300 * u3[-1] / 50)}
    fills = {"fob2Deck": heat(u2[-1]), "fob3Deck": heat(u3[-1])}

    def S(v):
        return v * SS

    for el in list(main_cls.find("Presentation/Level/Presentation")):
        tag = el.tag
        name = el.findtext("Name") or ""
        x, y = float(el.findtext("X") or 0), float(el.findtext("Y") or 0)
        if tag in ("Rectangle", "RoundedRectangle"):
            w, h = float(el.findtext("Width")), float(el.findtext("Height"))
            if name in widths:
                w = widths[name]
            if name in bm:
                h = max(1, min(200, 200 * bm[name] / 50))
                y = y + 1 - h
            fill = fills.get(name, col(el.findtext("FillColor")))
            line = col(el.findtext("LineColor"))
            lw = float(el.findtext("LineWidth") or 1)
            style = el.findtext("LineStyle")
            box = [S(x), S(y), S(x + w), S(y + h)]
            if tag == "RoundedRectangle":
                rad = min(float(el.findtext("ArcRadius")), w / 2, h / 2)
                dr.rounded_rectangle(box, radius=S(rad), fill=fill, outline=None if (line is None or lw == 0) else line,
                                     width=max(1, int(S(lw))))
            else:
                dr.rectangle(box, fill=fill, outline=None if (line is None or lw == 0 or style == "DASHED") else line,
                             width=max(1, int(S(lw))))
                if style == "DASHED" and line:
                    for a, b in (((x, y), (x + w, y)), ((x, y + h), (x + w, y + h)), ((x, y), (x, y + h)), ((x + w, y), (x + w, y + h))):
                        dashed(dr, (S(a[0]), S(a[1])), (S(b[0]), S(b[1])), line, int(S(lw)), S(8), S(5))
        elif tag == "Polyline":
            pts_ = [(S(x + float(p.findtext("X"))), S(y + float(p.findtext("Y")))) for p in el.find("Points")]
            line = col(el.findtext("LineColor"))
            fill = col(el.findtext("FillColor"))
            lw = max(1, int(S(float(el.findtext("LineWidth") or 1))))
            style = el.findtext("LineStyle")
            if el.findtext("Closed") == "true":
                dr.polygon(pts_, fill=fill, outline=line)
            elif style in ("DOTTED", "DASHED"):
                d, g = (S(2), S(3)) if style == "DOTTED" else (S(8), S(6))
                for i in range(len(pts_) - 1):
                    dashed(dr, pts_[i], pts_[i + 1], line, lw, d, g)
            else:
                dr.line(pts_, fill=line, width=lw)
        elif tag == "Oval":
            r = float(el.findtext("RadiusX"))
            lw = max(1, int(S(float(el.findtext("LineWidth") or 1))))
            dr.ellipse([S(x - r), S(y - r), S(x + r), S(y + r)], fill=col(el.findtext("FillColor")),
                       outline=col(el.findtext("LineColor")), width=lw)
        elif tag == "Text":
            if name.startswith("cmpVal_") and name.replace("cmpVal_", "cmpBar_") in bm:
                y = y - max(1, min(200, 200 * bm[name.replace("cmpVal_", "cmpBar_")] / 50))
            s = el.findtext("Text") or ""
            if el.findtext("TextCode"):
                s = vals.get(name, s)
            fnt_el = el.find("Font")
            fnt = font(float(fnt_el.findtext("Size")), fnt_el.findtext("Style") == "1", fnt_el.findtext("Name") == "Monospaced")
            align = el.findtext("Alignment")
            c = col(el.findtext("Color"))
            for i, ln in enumerate(s.split("\n")):
                tw_ = dr.textlength(ln, font=fnt)
                tx = S(x) - (tw_ if align == "RIGHT" else tw_ / 2 if align == "CENTER" else 0)
                dr.text((tx, S(y) + i * fnt.size * 1.25), ln, font=fnt, fill=c, anchor="ls")
        elif tag == "Control":
            bp = el.find("BasicProperties")
            w, h = float(bp.get("Width")), float(bp.get("Height"))
            dr.rounded_rectangle([S(x), S(y), S(x + w), S(y + h)], radius=S(5), fill=(250, 250, 250), outline=(150, 158, 168), width=SS)
            dr.text((S(x + w / 2), S(y + h / 2)), el.findtext("ExtendedProperties/LabelText") or "", font=font(12, True),
                    fill=(31, 41, 51), anchor="mm")
        elif tag in ("TimePlot", "Histogram"):
            w, h = float(el.findtext("Width")), float(el.findtext("Height"))
            ox, oy, cw, ch = x + 40, y + 10, w - 60, h - 60
            dr.rectangle([S(ox), S(oy), S(ox + cw), S(oy + ch)], fill=(255, 255, 255), outline=(220, 225, 232))
            series = ((u2, (0, 161, 155), "FOB 2"), (u3, (37, 99, 235), "FOB 3"))
            if tag == "TimePlot":
                for g in range(0, 51, 10):
                    gy = oy + ch - ch * g / 50
                    dr.line([S(ox), S(gy), S(ox + cw), S(gy)], fill=(228, 231, 235), width=1)
                    dr.text((S(ox - 6), S(gy)), str(g), font=font(9), fill=(95, 107, 122), anchor="rm")
                for ser, c, _ in series:
                    pp = [(S(ox + cw * (i + 1) / 60), S(oy + ch - ch * v / 50)) for i, v in enumerate(ser)]
                    if len(pp) > 1:
                        dr.line(pp, fill=c, width=2 * SS)
            else:
                bins = 15
                for k, (ser, c, _) in enumerate(series):
                    cnt = [0] * bins
                    for v in ser:
                        cnt[min(bins - 1, int(v / 2))] += 1
                    for i, n in enumerate(cnt):
                        bw = cw / bins
                        bh = ch * n / max(1, len(ser)) * 1.6
                        bx = ox + i * bw + k * bw * 0.45
                        dr.rectangle([S(bx + 1), S(oy + ch - bh), S(bx + bw * 0.45), S(oy + ch)], fill=c)
                for g in range(0, 31, 10):
                    dr.text((S(ox + cw * g / 30), S(oy + ch + 10)), str(g), font=font(9), fill=(95, 107, 122), anchor="mm")
            for i, (_, c, lab) in enumerate(series):
                lx = ox + cw / 2 - 90 + i * 100
                dr.rectangle([S(lx), S(oy + ch + 25), S(lx + 14), S(oy + ch + 33)], fill=c)
                dr.text((S(lx + 20), S(oy + ch + 29)), lab, font=font(10), fill=(95, 107, 122), anchor="lm")
        elif tag == "EmbeddedObjectPresentation":
            for (mx, my, r) in pts:
                px, py = OX + mx * PXM, OY + my * PXM
                dr.ellipse([S(px - 3.2), S(py - 3.2), S(px + 3.2), S(py + 3.2)], fill=(217, 48, 37) if r else (37, 99, 235), outline=(255, 255, 255))
    img = img.resize((W, H), Image.LANCZOS)
    out = os.path.join(ROOT, "charts", "anylogic_screen_preview.png")
    img.save(out)
    print("saved", out, "passengers drawn:", len(pts))


if __name__ == "__main__":
    main()
