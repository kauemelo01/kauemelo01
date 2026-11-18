"""Generate the profile's SVG assets (banner + project previews) in light and dark themes.

Run from the repo root:  python3 tools/gen_assets.py
"""
import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

THEMES = {
    "dark": dict(bg="#0d1117", border="#30363d", grid="#161b22", text="#f0f6fc",
                 muted="#9198a1", panel="#161b22", empty="#21262d",
                 green="#3fb950", red="#f85149", orange="#f0883e", blue="#58a6ff"),
    "light": dict(bg="#ffffff", border="#d1d9e0", grid="#f0f3f6", text="#1f2328",
                  muted="#59636e", panel="#f6f8fa", empty="#eaeef2",
                  green="#1a7f37", red="#cf222e", orange="#bc4c00", blue="#0969da"),
}

# Prime Radiant palette (from the app's mark)
PR_PURPLE, PR_ORANGE, PR_YELLOW = "#9b6cf2", "#f68013", "#fbba1f"


def svg(w, h, label, body, t):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{label}">\n'
            f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>\n'
            f'{body}</svg>\n')


def grid(w, h, step, t):
    out = [f'<line x1="{x}" y1="1" x2="{x}" y2="{h-1}" stroke="{t["grid"]}"/>' for x in range(step, w, step)]
    out += [f'<line x1="1" y1="{y}" x2="{w-1}" y2="{y}" stroke="{t["grid"]}"/>' for y in range(step, h, step)]
    return "\n".join(out) + "\n"


def text(x, y, s, size, fill, weight=400, anchor="start"):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}">{s}</text>\n')


def lerp_hex(a, b, f):
    a, b = [int(a[i:i+2], 16) for i in (1, 3, 5)], [int(b[i:i+2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * f):02x}" for x, y in zip(a, b))


def fire_ramp(v, t):
    """0..1 -> empty -> purple -> orange -> yellow."""
    stops = [t["empty"], PR_PURPLE, PR_ORANGE, PR_YELLOW]
    v = max(0.0, min(1.0, v)) * (len(stops) - 1)
    i = min(int(v), len(stops) - 2)
    return lerp_hex(stops[i], stops[i + 1], v - i)


def fire_data(years, seed=7):
    """Synthetic burning activity: dry-season peak Aug-Oct, a few anomalous years."""
    rnd = random.Random(seed)
    hot = {2, 5, 10, 14, 19, 23}
    data = []
    for y in range(years):
        boost = 1.35 if y in hot else 1.0
        row = []
        for m in range(12):
            season = math.exp(-((m - 8.2) ** 2) / 3.2)
            row.append(min(1.0, (0.06 + 0.82 * season * boost) * rnd.uniform(0.8, 1.15)))
        data.append(row)
    return data


# ---------------------------------------------------------------- banner
def banner(t):
    w, h = 1200, 320
    rnd = random.Random(42)
    body = grid(w, h, 40, t)
    # P&L-style chart on the right: bars + animated cumulative line
    x0, x1, base = 700, 1150, 200
    n = 24
    bw = (x1 - x0) / n
    vals = [rnd.gauss(0.45, 1.0) for _ in range(n)]
    cum, pts = 0.0, []
    for i, v in enumerate(vals):
        bh = v * 28
        color = t["green"] if v >= 0 else t["red"]
        y = base - bh if v >= 0 else base
        body += (f'<rect x="{x0 + i*bw + 3:.1f}" y="{y:.1f}" width="{bw - 6:.1f}" height="{abs(bh):.1f}" '
                 f'rx="2" fill="{color}" fill-opacity="0.75"/>\n')
        cum += v
        pts.append((x0 + i * bw + bw / 2, base - cum * 11))
    body += f'<line x1="{x0}" y1="{base}" x2="{x1}" y2="{base}" stroke="{t["border"]}" stroke-width="1.5"/>\n'
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    body += (f'<path d="{d}" fill="none" stroke="{t["orange"]}" stroke-width="3" stroke-linejoin="round" '
             f'stroke-linecap="round" stroke-dasharray="1400" stroke-dashoffset="1400">'
             f'<animate attributeName="stroke-dashoffset" from="1400" to="0" dur="2.4s" fill="freeze"/></path>\n')
    lx, ly = pts[-1]
    body += (f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="6" fill="{t["bg"]}" stroke="{t["orange"]}" stroke-width="3" opacity="0">'
             f'<animate attributeName="opacity" from="0" to="1" begin="2.3s" dur="0.3s" fill="freeze"/></circle>\n')
    body += text(64, 138, "Kauê Melo", 52, t["text"], 700)
    body += text(64, 186, "Data / Python Developer", 26, t["muted"])
    body += text(64, 226, "Senior Data Analytics  ·  Pricing  ·  Revenue Management", 19, t["muted"])
    body += text(64, 256, "São Paulo, Brazil", 19, t["muted"])
    return svg(w, h, "Kauê Melo, Data / Python Developer", body, t)


# ---------------------------------------------------------------- Prime Radiant (featured, wide)
def prime_radiant(t):
    w, h = 1200, 420
    body = grid(w, h, 30, t)
    years = 25
    data = fire_data(years)
    # Radiant: polar year-by-month view
    cx, cy, r0, r1 = 230, 210, 34, 178
    ring = (r1 - r0) / years
    months = "JFMAMJJASOND"
    for yi, row in enumerate(data):
        ra, rb = r0 + yi * ring, r0 + (yi + 1) * ring - 0.6
        for m, v in enumerate(row):
            a0 = math.radians(m * 30 - 90 + 0.8)
            a1 = math.radians((m + 1) * 30 - 90 - 0.8)
            p = [(cx + r * math.cos(a), cy + r * math.sin(a)) for r, a in ((rb, a0), (rb, a1), (ra, a1), (ra, a0))]
            body += (f'<path d="M{p[0][0]:.1f},{p[0][1]:.1f} A{rb:.1f},{rb:.1f} 0 0 1 {p[1][0]:.1f},{p[1][1]:.1f} '
                     f'L{p[2][0]:.1f},{p[2][1]:.1f} A{ra:.1f},{ra:.1f} 0 0 0 {p[3][0]:.1f},{p[3][1]:.1f} Z" '
                     f'fill="{fire_ramp(v, t)}"/>\n')
    for m, ch in enumerate(months):
        a = math.radians(m * 30 - 75)
        body += text(f"{cx + (r1 + 16) * math.cos(a):.1f}", f"{cy + (r1 + 16) * math.sin(a) + 5:.1f}",
                     ch, 13, t["muted"], 600, "middle")
    # Mark in the center
    body += (f'<g transform="translate({cx - 19},{cy - 28}) scale(0.14)">'
             f'<g transform="translate(-118,-52)"><path id="prf" d="M256 62C302 138 384 196 384 300c0 78-56 146-128 146S128 378 128 300c0-52 28-88 56-114 6 38 26 58 44 64-12-62 2-128 28-188z" fill="{PR_ORANGE}"/>'
             f'<circle cx="256" cy="344" r="52" fill="{PR_YELLOW}"/></g></g>\n')
    # Calendar grid: last 12 years x 12 months + median row
    gx, gy, cs = 500, 64, 22
    body += text(gx, gy - 22, "Burning calendar · fire-cell-days", 15, t["muted"], 600)
    shown = data[-12:]
    for m, ch in enumerate(months):
        body += text(gx + 52 + m * (cs + 4) + cs / 2, gy, ch, 12, t["muted"], 600, "middle")
    for r, row in enumerate(shown):
        y = gy + 10 + r * (cs + 4)
        body += text(gx + 40, y + 16, str(2014 + r), 12, t["muted"], 400, "end")
        for m, v in enumerate(row):
            body += f'<rect x="{gx + 52 + m*(cs+4)}" y="{y}" width="{cs}" height="{cs}" rx="4" fill="{fire_ramp(v, t)}"/>\n'
    med = [sorted(col)[len(col) // 2] for col in zip(*data)]
    y = gy + 14 + 12 * (cs + 4)
    body += text(gx + 40, y + 16, "median", 12, t["text"], 600, "end")
    for m, v in enumerate(med):
        body += (f'<rect x="{gx + 52 + m*(cs+4)}" y="{y}" width="{cs}" height="{cs}" rx="4" fill="{fire_ramp(v, t)}" '
                 f'stroke="{t["text"]}" stroke-width="1.2"/>\n')
    # Sensor harmonization panel
    px, py = 900, 64
    body += text(px, py - 22, "Sensor harmonization", 15, t["muted"], 600)
    sensors = [("MODIS", t["muted"], "× R"), ("VIIRS S-NPP", PR_PURPLE, "reference"),
               ("VIIRS NOAA-20", PR_ORANGE, "× K"), ("Harmonized", PR_YELLOW, "one series")]
    for i, (name, color, note) in enumerate(sensors):
        y = py + 10 + i * 58
        body += f'<rect x="{px}" y="{y}" width="250" height="46" rx="8" fill="{t["panel"]}" stroke="{t["border"]}"/>\n'
        body += f'<circle cx="{px + 22}" cy="{y + 23}" r="7" fill="{color}"/>\n'
        body += text(px + 40, y + 28, name, 15, t["text"], 600)
        body += text(px + 236, y + 28, note, 13, t["muted"], 400, "end")
    body += text(px, py + 262, "NASA FIRMS · MODIS C6.1 + VIIRS 375 m", 13, t["muted"])
    body += text(px, py + 284, "Anomalies vs. multi-year baseline", 13, t["muted"])
    body += text(px, py + 306, "Live season from NRT data", 13, t["muted"])
    return svg(w, h, "Prime Radiant: harmonized MODIS and VIIRS burning calendar", body, t)


# ---------------------------------------------------------------- Solaria (featured, wide)
SOL_BLUE, SOL_VIOLET, SOL_AMBER = "#5b8cff", "#a78bfa", "#ffb547"


def galaxy_points(n, seed=5):
    """Synthetic spiral galaxy: (x, y, brightness) in unit coords, tilted ellipse."""
    rnd = random.Random(seed)
    pts = []
    for _ in range(n):
        if rnd.random() < 0.35:  # bulge
            r = abs(rnd.gauss(0, 0.16))
            a = rnd.uniform(0, 2 * math.pi)
        else:  # two arms
            r = rnd.uniform(0.08, 1.0)
            a = r * 4.2 + (math.pi if rnd.random() < 0.5 else 0) + rnd.gauss(0, 0.32)
        x, y = r * math.cos(a), r * math.sin(a) * 0.42
        ca, sa = math.cos(-0.5), math.sin(-0.5)
        pts.append((x * ca - y * sa, x * sa + y * ca, max(0.15, 1 - r)))
    return pts


def solaria(t):
    w, h = 1200, 420
    rnd = random.Random(21)
    body = grid(w, h, 30, t)
    dark = t["bg"] == "#0d1117"
    sky = "#05070d" if dark else "#0b1020"
    # Viewer: full image with rulers and a zoom box
    vx, vy, vw, vh = 40, 56, 470, 300
    body += text(vx, vy - 22, "Explore · Andromeda (M31)", 15, t["muted"], 600)
    body += f'<rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" rx="10" fill="{sky}" stroke="{t["border"]}"/>\n'
    for _ in range(90):
        body += (f'<circle cx="{vx + rnd.uniform(6, vw - 6):.1f}" cy="{vy + rnd.uniform(6, vh - 6):.1f}" '
                 f'r="{rnd.uniform(0.4, 1.3):.1f}" fill="#ffffff" fill-opacity="{rnd.uniform(0.25, 0.8):.2f}"/>\n')
    gcx, gcy, gs = vx + vw / 2, vy + vh / 2, 205
    for x, y, b in galaxy_points(900):
        c = lerp_hex(SOL_VIOLET, "#fff4dc", b)
        body += (f'<circle cx="{gcx + x * gs:.1f}" cy="{gcy + y * gs:.1f}" r="{0.6 + b * 1.4:.1f}" '
                 f'fill="{c}" fill-opacity="{0.25 + b * 0.6:.2f}"/>\n')
    for i in range(1, 8):  # pixel ruler ticks
        x = vx + i * vw / 8
        body += f'<line x1="{x:.0f}" y1="{vy}" x2="{x:.0f}" y2="{vy + 7}" stroke="#ffffff" stroke-opacity="0.5"/>\n'
    zx, zy, zw, zh = gcx + 38, gcy - 30, 70, 44
    body += (f'<rect x="{zx:.0f}" y="{zy:.0f}" width="{zw}" height="{zh}" fill="none" stroke="{SOL_AMBER}" '
             f'stroke-width="2" rx="3"/>\n')
    # Zoomed inset: tiles loading in
    ix, iy, iw, ih = 560, 56, 300, 300
    body += text(ix, iy - 22, "Deep zoom · 256 px tiles", 15, t["muted"], 600)
    body += (f'<path d="M{zx + zw:.0f},{zy:.0f} L{ix},{iy} M{zx + zw:.0f},{zy + zh:.0f} L{ix},{iy + ih}" '
             f'stroke="{SOL_AMBER}" stroke-opacity="0.55" stroke-dasharray="4 4"/>\n')
    body += f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" rx="10" fill="{sky}" stroke="{t["border"]}"/>\n'
    for x, y, b in galaxy_points(700, seed=9):
        px, py = ix + iw * 0.35 + x * 520, iy + ih * 0.6 + y * 520
        if ix + 4 < px < ix + iw - 4 and iy + 4 < py < iy + ih - 4:
            c = lerp_hex(SOL_VIOLET, "#fff4dc", b)
            body += f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{1 + b * 2.2:.1f}" fill="{c}" fill-opacity="{0.3 + b * 0.6:.2f}"/>\n'
    n = 4
    ts = iw / n
    for r in range(n):
        for c in range(n):
            # Tiles start covered and fade in one by one; the static (end) state shows the image.
            delay, fade = 0.4 + 0.15 * (r + c), 0.5
            k = delay / (delay + fade)
            body += (f'<rect x="{ix + c * ts:.0f}" y="{iy + r * ts:.0f}" width="{ts:.0f}" height="{ts:.0f}" '
                     f'fill="{sky}" fill-opacity="0" stroke="{SOL_BLUE}" stroke-opacity="0.35">'
                     f'<animate attributeName="fill-opacity" values="1;1;0" keyTimes="0;{k:.3f};1" '
                     f'dur="{delay + fade:.2f}s" fill="freeze"/></rect>\n')
    body += f'<circle cx="{ix + 196}" cy="{iy + 112}" r="6" fill="{SOL_AMBER}" stroke="{sky}" stroke-width="2"/>\n'
    body += (f'<rect x="{ix + 208}" y="{iy + 100}" width="80" height="24" rx="6" fill="{t["panel"]}" '
             f'stroke="{t["border"]}"/>\n')
    body += text(ix + 248, iy + 117, "Bulge", 12, t["text"], 600, "middle")
    # Feature panel
    px, py = 910, 64
    body += text(px, py - 22, "Ways in", 15, t["muted"], 600)
    feats = [("Journeys", SOL_AMBER, "guided tours"), ("Compare", SOL_BLUE, "1995 / 2014"),
             ("Light", SOL_VIOLET, "7 SDO bands"), ("Labels", t["muted"], "validated")]
    for i, (name, color, note) in enumerate(feats):
        y = py + 10 + i * 58
        body += f'<rect x="{px}" y="{y}" width="250" height="46" rx="8" fill="{t["panel"]}" stroke="{t["border"]}"/>\n'
        body += f'<circle cx="{px + 22}" cy="{y + 23}" r="7" fill="{color}"/>\n'
        body += text(px + 40, y + 28, name, 15, t["text"], 600)
        body += text(px + 236, y + 28, note, 13, t["muted"], 400, "end")
    body += text(px, py + 262, "Hubble · HiRISE · SDO gigapixel images", 13, t["muted"])
    body += text(px, py + 284, "OpenSeadragon tile pyramids on R2", 13, t["muted"])
    body += text(px, py + 306, "Shareable view in the URL", 13, t["muted"])
    return svg(w, h, "Solaria: deep-zoom viewer for very large NASA images", body, t)


# ---------------------------------------------------------------- Elasticity & WSB (Power BI)
def elasticity_wsb(t):
    import json
    d = json.loads((Path(__file__).parent / "elasticity_wsb.json").read_text())
    w, h = 600, 340
    body = grid(w, h, 30, t)
    ccol = {1: t["red"], 2: t["orange"], 3: t["muted"], 4: t["blue"], 5: t["green"]}
    # Left: weekly markup vs. conversion for one True Elastic lane
    x0, y0, pw, ph = 52, 70, 220, 200
    pk = d["pick"]
    lane = pk["lane"].replace("->", "→")
    body += text(24, 34, "Scatter Plot", 16, t["text"], 700)
    body += text(24, 54, f'{lane} · dry van · {pk["C"]} weeks', 12, t["muted"])
    xs = [p[0] for p in pk["pts"]]; ys = [p[1] for p in pk["pts"]]
    xa, xb = min(xs), max(xs); ya, yb = 0, max(ys) * 1.05
    sx = lambda v: x0 + (v - xa) / (xb - xa) * pw
    sy = lambda v: y0 + ph - (v - ya) / (yb - ya) * ph
    body += f'<rect x="{x0}" y="{y0}" width="{pw}" height="{ph}" fill="{t["panel"]}" stroke="{t["border"]}"/>\n'
    for x, y in pk["pts"]:
        body += f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="3.2" fill="{t["red"]}" fill-opacity="0.6"/>\n'
    n = len(xs); mx, my = sum(xs) / n, sum(ys) / n
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    body += f'<clipPath id="ewc"><rect x="{x0}" y="{y0}" width="{pw}" height="{ph}"/></clipPath>\n'
    body += (f'<line x1="{sx(xa):.1f}" y1="{sy(my + b * (xa - mx)):.1f}" x2="{sx(xb):.1f}" y2="{sy(my + b * (xb - mx)):.1f}" '
             f'stroke="{t["text"]}" stroke-width="2" stroke-dasharray="5 4" clip-path="url(#ewc)"/>\n')
    body += text(x0 + pw / 2, y0 + ph + 18, "markup over ECOH %", 11, t["muted"], 400, "middle")
    body += (f'<text x="{x0 - 10}" y="{y0 + ph / 2}" font-family="{FONT}" font-size="11" fill="{t["muted"]}" '
             f'text-anchor="middle" transform="rotate(-90 {x0 - 10} {y0 + ph / 2})">conversion %</text>\n')
    body += f'<rect x="{x0}" y="{y0 + ph + 30}" width="{pw}" height="30" rx="6" fill="{t["panel"]}" stroke="{t["border"]}"/>\n'
    body += text(x0 + 10, y0 + ph + 50, f'Elasticity {pk["el"]:+.2f}'.replace("-", "−"), 12, t["text"], 600)
    body += text(x0 + pw - 10, y0 + ph + 50, "True Elastic", 12, t["red"], 700, "end")
    # Right: clusterization of all KMA lanes
    cx0, cy0, cw, chh = 330, 70, 246, 200
    body += text(cx0, 34, "Clusterization", 16, t["text"], 700)
    body += text(cx0, 54, f'{len(d["dots"])} KMA lanes · Pearson vs. rank', 12, t["muted"])
    body += f'<rect x="{cx0}" y="{cy0}" width="{cw}" height="{chh}" fill="{t["panel"]}" stroke="{t["border"]}"/>\n'
    ex, ey = 0.3, 0.75
    px = lambda v: cx0 + (max(-ex, min(ex, v)) + ex) / (2 * ex) * cw
    py = lambda v: cy0 + chh - (max(-ey, min(ey, v)) + ey) / (2 * ey) * chh
    body += f'<line x1="{px(0):.1f}" y1="{cy0}" x2="{px(0):.1f}" y2="{cy0 + chh}" stroke="{t["border"]}"/>\n'
    body += f'<line x1="{cx0}" y1="{py(0):.1f}" x2="{cx0 + cw}" y2="{py(0):.1f}" stroke="{t["border"]}"/>\n'
    for el, rho, c, _ in sorted(d["dots"], key=lambda r: -r[3]):
        body += f'<circle cx="{px(el):.1f}" cy="{py(rho):.1f}" r="2.4" fill="{ccol[int(c)]}" fill-opacity="0.7"/>\n'
    labels = {1: "True Elastic", 2: "Semi Elastic", 4: "Semi Inelastic", 5: "True Inelastic"}
    for i, c in enumerate([1, 2, 4, 5]):
        lx, ly = cx0 + (i % 2) * 128, cy0 + chh + 24 + (i // 2) * 22
        body += f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{ccol[c]}"/>\n'
        body += text(lx + 16, ly, f'{labels[c]} {d["counts"][str(c)]}', 12, t["text"])
    return svg(w, h, "Elasticity and WSB: freight price elasticity clusters in Power BI", body, t)


# ---------------------------------------------------------------- Trade-Viz
def trade_viz(t):
    w, h = 600, 340
    rnd = random.Random(3)
    body = grid(w, h, 30, t)
    kpis = [("Trades", "128"), ("P&amp;L", "+$4.2k"), ("Win rate", "61%"), ("W / L", "78 / 50")]
    for i, (k, v) in enumerate(kpis):
        x = 24 + i * 140
        body += f'<rect x="{x}" y="22" width="128" height="62" rx="8" fill="{t["panel"]}" stroke="{t["border"]}"/>\n'
        body += text(x + 12, 44, k, 12, t["muted"])
        body += text(x + 12, 72, v, 20, t["green"] if i == 1 else t["text"], 700)
    x0, x1, base, n = 30, 570, 230, 30
    bw = (x1 - x0) / n
    cum, pts = 0.0, []
    for i in range(n):
        v = rnd.gauss(0.35, 1.0)
        bh = v * 22
        body += (f'<rect x="{x0 + i*bw + 2:.1f}" y="{base - bh if v >= 0 else base:.1f}" width="{bw - 4:.1f}" '
                 f'height="{abs(bh):.1f}" rx="2" fill="{t["green"] if v >= 0 else t["red"]}" fill-opacity="0.8"/>\n')
        cum += v
        pts.append((x0 + i * bw + bw / 2, base - cum * 8))
    body += f'<line x1="{x0}" y1="{base}" x2="{x1}" y2="{base}" stroke="{t["border"]}"/>\n'
    body += (f'<path d="M' + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) +
             f'" fill="none" stroke="{t["orange"]}" stroke-width="2.5" stroke-linejoin="round"/>\n')
    for i, (ts, ev) in enumerate([("14:02:11.418", "signal discarded: spread"), ("14:05:37.092", "feed reconnected")]):
        y = 286 + i * 24
        body += text(30, y, ts, 12, t["muted"])
        body += text(140, y, ev, 12, t["text"])
    return svg(w, h, "Trade-Viz dashboard preview", body, t)


# ---------------------------------------------------------------- Political Compass
def political_compass(t):
    w, h = 600, 340
    rnd = random.Random(11)
    body = grid(w, h, 30, t)
    cx, cy = 300, 180
    axes = [((-1, 0), "Unitary", "Subsidiary"), ((0.55, 0.6), "Sovereignism", "Globalism"), ((0, -1), "Jusnaturalism", "Legalism")]
    L = 140
    for (dx, dy), neg, pos in axes:
        body += (f'<line x1="{cx - dx*L:.0f}" y1="{cy - dy*L*0.85:.0f}" x2="{cx + dx*L:.0f}" y2="{cy + dy*L*0.85:.0f}" '
                 f'stroke="{t["border"]}" stroke-width="1.5"/>\n')
    body += text(cx + L + 6, cy + 4, "Unitary", 12, t["muted"])
    body += text(cx - L - 6, cy + 4, "Subsidiary", 12, t["muted"], 400, "end")
    body += text(cx, cy - L * 0.85 - 8, "Legalism", 12, t["muted"], 400, "middle")
    body += text(cx, cy + L * 0.85 + 18, "Jusnaturalism", 12, t["muted"], 400, "middle")
    body += text(cx + 0.55 * L + 6, cy + 0.6 * L * 0.85 + 4, "Globalism", 12, t["muted"])
    body += text(cx - 0.55 * L - 6, cy - 0.6 * L * 0.85 + 4, "Sovereignism", 12, t["muted"], 400, "end")
    pts = []
    for _ in range(46):
        a, b, c, d = (max(-0.8, min(0.8, rnd.gauss(0, 0.38))) for _ in range(4))
        x = cx - a * L + b * 0.55 * L
        y = cy - c * L * 0.85 + b * 0.6 * L * 0.85
        pts.append((b, x, y, d))
    for b, x, y, d in sorted(pts):
        color = lerp_hex(t["blue"], t["orange"], (d + 1) / 2)
        body += (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{6 + b * 2:.1f}" fill="{color}" fill-opacity="0.85" '
                 f'stroke="{t["bg"]}" stroke-width="1.5"/>\n')
    body += f'<defs><linearGradient id="pc" x1="0" x2="1"><stop offset="0" stop-color="{t["blue"]}"/><stop offset="1" stop-color="{t["orange"]}"/></linearGradient></defs>\n'
    body += f'<rect x="440" y="52" width="130" height="10" rx="5" fill="url(#pc)"/>\n'
    body += text(440, 40, "4th axis (color)", 12, t["muted"])
    body += text(30, 40, "4D compass", 16, t["text"], 700)
    body += text(30, 60, "each axis scored −1 … +1", 12, t["muted"])
    return svg(w, h, "4D Political Compass scatterplot preview", body, t)


# ---------------------------------------------------------------- Cadastro (sponsorship app)
def cadastro(t):
    w, h = 600, 340
    body = grid(w, h, 30, t)
    # phone frame
    fx, fy, fw, fh = 200, 18, 200, 304
    body += f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="22" fill="{t["panel"]}" stroke="{t["border"]}" stroke-width="2"/>\n'
    body += f'<rect x="{fx + 76}" y="{fy + 10}" width="48" height="6" rx="3" fill="{t["border"]}"/>\n'
    body += f'<rect x="{fx + 14}" y="{fy + 28}" width="{fw - 28}" height="24" rx="6" fill="{t["bg"]}" stroke="{t["border"]}"/>\n'
    body += text(fx + 24, fy + 45, "Nº registro: 0142", 11, t["muted"])
    kids = [("#d63384", "Ana, 6 anos", "Padrinho: Marcos", True), ("#0969da", "Davi, 2 anos", "Cadastrar padrinho", False),
            ("#0969da", "Lucas, 10 anos", "Padrinho: Júlia", True)]
    for i, (ic, name, sub, done) in enumerate(kids):
        y = fy + 64 + i * 58
        body += f'<rect x="{fx + 14}" y="{y}" width="{fw - 28}" height="50" rx="8" fill="{t["bg"]}" stroke="{t["border"]}"/>\n'
        body += f'<circle cx="{fx + 36}" cy="{y + 25}" r="13" fill="{ic}" fill-opacity="0.18" stroke="{ic}" stroke-width="1.5"/>\n'
        body += text(fx + 36, y + 30, name[0], 13, ic, 700, "middle")
        body += text(fx + 56, y + 22, name, 12, t["text"], 700)
        body += text(fx + 56, y + 39, sub, 11, t["green"] if done else t["blue"], 600 if not done else 400)
    y = fy + 246
    body += text(fx + 14, y, "Apadrinhadas 68%", 11, t["muted"])
    body += f'<rect x="{fx + 14}" y="{y + 8}" width="{fw - 28}" height="8" rx="4" fill="{t["empty"]}"/>\n'
    body += f'<rect x="{fx + 14}" y="{y + 8}" width="{(fw - 28) * 0.68:.0f}" height="8" rx="4" fill="{t["green"]}"/>\n'
    # side notes
    body += text(30, 120, "Streamlit", 16, t["text"], 700)
    body += text(30, 142, "mobile-first", 12, t["muted"])
    body += text(30, 200, "Google Drive", 16, t["text"], 700)
    body += text(30, 222, "cadastro.xlsx", 12, t["muted"])
    body += f'<path d="M140 205 L190 170" stroke="{t["border"]}" stroke-width="1.5" stroke-dasharray="4 4"/>\n'
    for i, (lbl, v) in enumerate([("0–3", 0.55), ("4–8", 0.74), ("9+", 0.70)]):
        y = 110 + i * 46
        body += text(430, y, f"{lbl} anos", 12, t["muted"])
        body += f'<rect x="430" y="{y + 8}" width="140" height="10" rx="5" fill="{t["empty"]}"/>\n'
        body += f'<rect x="430" y="{y + 8}" width="{140 * v:.0f}" height="10" rx="5" fill="{t["green"]}"/>\n'
    return svg(w, h, "Pastoral Social sponsorship app preview", body, t)

# ---------------------------------------------------------------- "live" badges (shields "for-the-badge" look + pulsing red dot)
NASA_LOGO = "data:image/svg+xml;base64,PHN2ZyBmaWxsPSJ3aGl0ZSIgcm9sZT0iaW1nIiB2aWV3Qm94PSIwIDAgMjQgMjQiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHRpdGxlPk5BU0E8L3RpdGxlPjxwYXRoIGQ9Ik00LjM0NCAxMy41OThjLjA3NS4yODEuMTk1LjM5LjQwNy4zOS4yMiAwIC4zMzUtLjEzMi4zMzUtLjM5VjguODA0aDEuMzc5djQuNzk0YzAgLjY3NS0uMDg4Ljk2OC0uNDMgMS4zMS0uMjQ3LjI0OC0uNzAzLjQzOS0xLjI3OC40MzktLjQ2NCAwLS45MDktLjE1NC0xLjE5Mi0uNDM4LS4yNDktLjI1LS4zODYtLjUwNS0uNTk5LTEuMzExbC0uODQ2LTMuMTk2Yy0uMDc0LS4yODEtLjE5NC0uMzktLjQwNi0uMzktLjIyIDAtLjMzNi4xMzItLjMzNi4zOXY0Ljc5NEgwdi00Ljc5NGMwLS42NzUuMDg4LS45NjguNDMtMS4zMS4yNDctLjI0OC43MDMtLjQzOSAxLjI3OC0uNDM5LjQ2NCAwIC45MDkuMTU0IDEuMTkyLjQzOC4yNDkuMjUuMzg1LjUwNS41OTkgMS4zMTF6TTIyLjU3NSAxNS4xOTZsLTEuNTkxLTQuOThhLjQxNS40MTUgMCAwMC0uMDYtLjEzMi4yMjYuMjI2IDAgMDAtLjE4Ni0uMDgyLjIyNi4yMjYgMCAwMC0uMTg1LjA4Mi40MTQuNDE0IDAgMDAtLjA2LjEzMmwtMS41OTEgNC45OGgtMS40MjVsMS43MzktNS40NGMuMDktLjI4My4yMi0uNTI0LjM4NC0uNjg0LjI4Mi0uMjc1LjYxNC0uNDE5IDEuMTM4LS40MTkuNTI1IDAgLjg1Ny4xNDQgMS4xMzkuNDIuMTY0LjE2LjI5NC40LjM4NC42ODNMMjQgMTUuMTk2aC0xLjQyNXpNMTUuNTMxIDE1LjE5NmMuOTAzIDAgMS4zNDQtLjE5MiAxLjY5Mi0uNTM4LjM4NS0uMzgzLjU2OS0uODAyLjU2OS0xLjQyNyAwLS41NTMtLjIwMi0xLjA2NC0uNTEtMS4zNy0uNDAzLS40LS45MDMtLjUyNy0xLjcxOS0uNTI3aC0xLjE0MmMtLjQzNiAwLS42MS0uMDUzLS43NDgtLjE4OC0uMDk0LS4wOTMtLjEzOS0uMjMtLjEzOS0uMzkzIDAtLjE2OC4wNC0uMzM0LjE1Ni0uNDQ4LjEwMy0uMS4yNDMtLjE0Ny41MTEtLjE0N2gzLjMwMVY4LjgwNGgtMy4wNDljLS45MDMgMC0xLjM0My4xOTItMS42OTEuNTM4LS4zODUuMzgzLS41Ny44MDItLjU3IDEuNDI3IDAgLjU1My4yMDMgMS4wNjQuNTEgMS4zNy40MDQuNC45MDQuNTI3IDEuNzIuNTI3aDEuMTQxYy40MzcgMCAuNjEuMDUzLjc0OC4xODguMDk1LjA5My4xNC4yMy4xNC4zOTMgMCAuMTY5LS4wNDEuMzM1LS4xNTcuNDQ4LS4xMDIuMS0uMjQyLjE0Ny0uNTEuMTQ3aC0zLjQwNWwtMS4zMDYtNC4wODZjLS4wOS0uMjgzLS4yMi0uNTI0LS4zODQtLjY4NC0uMjgyLS4yNzUtLjYxNS0uNDE5LTEuMTM5LS40MTlzLS44NTcuMTQ0LTEuMTM4LjQyYy0uMTY1LjE2LS4yOTQuNC0uMzg1LjY4M2wtMS43MzggNS40NGgxLjQyNGwxLjU5Mi00Ljk4YS40MTUuNDE1IDAgMDEuMDYtLjEzMi4yMjYuMjI2IDAgMDEuMTg1LS4wODJjLjA4MiAwIC4xNDIuMDI4LjE4Ni4wODJhLjQxMy40MTMgMCAwMS4wNi4xMzJsMS41OTEgNC45OGg0LjE0NHoiLz48L3N2Zz4="
LIVE_BADGES = {  # slug: (label, label segment width, label text length) — geometry from shields.io
    "prime-radiant": ("PRIME RADIANT", 138.25, 97.25),
    "solaria": ("SOLARIA", 94.75, 53.75),
}


def live_badge(label, seg, tlen):
    w = seg + 22
    cx = seg + 6
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="28" role="img" aria-label="{label}: live">'
            f'<title>{label}: live</title>'
            f'<defs><filter id="g" x="-2" y="-2" width="5" height="5"><feGaussianBlur stdDeviation="1.6"/></filter></defs>'
            f'<rect width="{w}" height="28" fill="#555" shape-rendering="crispEdges"/>'
            f'<image x="9" y="7" width="14" height="14" href="{NASA_LOGO}"/>'
            f'<text x="{(seg + 23) / 2 + 2.5:.2f}" y="17.5" fill="#fff" text-anchor="middle" font-size="10" '
            f'font-family="Verdana,Geneva,DejaVu Sans,sans-serif" textLength="{tlen}" text-rendering="geometricPrecision">{label}</text>'
            f'<circle cx="{cx}" cy="14" r="4" fill="#ff3b30" opacity="0.6">'
            f'<animate attributeName="r" values="4;9;4" dur="1.6s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.6;0;0" keyTimes="0;0.7;1" dur="1.6s" repeatCount="indefinite"/></circle>'
            f'<circle cx="{cx}" cy="14" r="5" fill="#ff3b30" filter="url(#g)">'
            f'<animate attributeName="opacity" values="1;0.35;1" dur="1.6s" repeatCount="indefinite"/></circle>'
            f'<circle cx="{cx}" cy="14" r="3.5" fill="#ff453a"/>'
            f'</svg>\n')


def main():
    (OUT / "projects").mkdir(parents=True, exist_ok=True)
    for name, t in THEMES.items():
        (OUT / f"banner-{name}.svg").write_text(banner(t), encoding="utf-8")
        for slug, fn in [("prime-radiant", prime_radiant), ("solaria", solaria), ("trade-viz", trade_viz),
                         ("political-compass", political_compass), ("cadastro", cadastro),
                         ("elasticity-wsb", elasticity_wsb)]:
            (OUT / "projects" / f"{slug}-{name}.svg").write_text(fn(t), encoding="utf-8")
    (OUT / "badges").mkdir(exist_ok=True)
    for slug, args in LIVE_BADGES.items():
        (OUT / "badges" / f"{slug}-live.svg").write_text(live_badge(*args), encoding="utf-8")
    print("assets written to", OUT)


if __name__ == "__main__":
    main()
