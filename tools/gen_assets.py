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


def main():
    (OUT / "projects").mkdir(parents=True, exist_ok=True)
    for name, t in THEMES.items():
        (OUT / f"banner-{name}.svg").write_text(banner(t), encoding="utf-8")
        for slug, fn in [("prime-radiant", prime_radiant), ("trade-viz", trade_viz),
                         ("political-compass", political_compass), ("cadastro", cadastro)]:
            (OUT / "projects" / f"{slug}-{name}.svg").write_text(fn(t), encoding="utf-8")
    print("assets written to", OUT)


if __name__ == "__main__":
    main()
