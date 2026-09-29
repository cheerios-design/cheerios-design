"""Generates on-brand SVG assets for the GitHub profile README (cheeriostudios.com design tokens).

    python scripts/profile_assets.py static [out_dir]   # README panels -> assets/
    python scripts/profile_assets.py stats  [out_dir]   # live GitHub stats card (needs GITHUB_TOKEN) -> dist/

Requires: pip install fonttools brotli. Fonts are fetched from google/fonts into scripts/.fonts on first run.
"""
import sys, os, io, json, base64, urllib.request, datetime
from xml.sax.saxutils import escape

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools import subset

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODE = sys.argv[1] if len(sys.argv) > 1 else "static"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "assets" if MODE == "static" else "dist")
os.makedirs(OUT, exist_ok=True)

# ---- tokens (from cheeriostudios.com CSS) ----
INK, INK2, INK3, GHOST = "#0C0D0A", "#151712", "#22251D", "#393B36"
LIME, MUTE, PAPER = "#D4FF1F", "#8D937F", "#EFF2E8"
W = 1200
PAD = 56

# ---- fonts ----
FD = os.path.join(HERE, ".fonts")
GF = "https://github.com/google/fonts/raw/main/ofl/"
FONT_FILES = {
    "grotesk.ttf": "spacegrotesk/SpaceGrotesk%5Bwght%5D.ttf",
    "inter.ttf": "inter/Inter%5Bopsz,wght%5D.ttf",
    "serif.ttf": "instrumentserif/InstrumentSerif-Regular.ttf",
    "serif-italic.ttf": "instrumentserif/InstrumentSerif-Italic.ttf",
    "mono.ttf": "spacemono/SpaceMono-Regular.ttf",
}
FONT_SPECS = {
    "grotesk": ("grotesk.ttf", {"wght": 700}),
    "grotesk-med": ("grotesk.ttf", {"wght": 500}),
    "inter": ("inter.ttf", {"wght": 400, "opsz": 14}),
    "inter-med": ("inter.ttf", {"wght": 500, "opsz": 14}),
    "serif": ("serif.ttf", None),
    "serif-it": ("serif-italic.ttf", None),
    "mono": ("mono.ttf", None),
}
os.makedirs(FD, exist_ok=True)
for fn, src in FONT_FILES.items():
    if not os.path.exists(os.path.join(FD, fn)):
        urllib.request.urlretrieve(GF + src, os.path.join(FD, fn))
FONTS = {}
for key, (fn, loc) in FONT_SPECS.items():
    f = TTFont(os.path.join(FD, fn))
    if loc:
        f = instancer.instantiateVariableFont(f, loc)
    FONTS[key] = f


def text_width(s, font, size, ls=0.0):
    f = FONTS[font]
    cmap, hmtx, upem = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    w = 0
    for ch in s:
        g = cmap.get(ord(ch))
        w += hmtx[g][0] if g else upem * 0.5
    return w * size / upem + ls * len(s)


def font_face(key, chars):
    buf = io.BytesIO()
    f = FONTS[key]
    tmp = io.BytesIO(); f.save(tmp); tmp.seek(0)
    f2 = TTFont(tmp)
    opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["kern", "liga"]
    opts.name_IDs = []; opts.notdef_outline = True
    s = subset.Subsetter(opts); s.populate(text="".join(sorted(chars)) + " "); s.subset(f2)
    f2.flavor = "woff2"; f2.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:'cs-{key}';src:url(data:font/woff2;base64,{b64}) format('woff2');}}"


# ---- pixel type (5-row grid, rounded outer corners + concave fillets, like the site glyphs) ----
G = {
    "A": ["XXXXX", "X...X", "XXXXX", "X...X", "X...X"],
    "B": ["XXXX.", "X..XX", "XXXX.", "X..XX", "XXXX."],
    "C": ["XXXXX", "X....", "X....", "X....", "XXXXX"],
    "D": ["XXXX.", "X..XX", "X...X", "X..XX", "XXXX."],
    "E": ["XXXXX", "X....", "XXXX.", "X....", "XXXXX"],
    "F": ["XXXXX", "X....", "XXXX.", "X....", "X...."],
    "G": ["XXXXX", "X....", "X..XX", "X...X", "XXXXX"],
    "H": ["X...X", "X...X", "XXXXX", "X...X", "X...X"],
    "I": ["XXX", ".X.", ".X.", ".X.", "XXX"],
    "K": ["X..XX", "X.XX.", "XXX..", "X.XX.", "X..XX"],
    "L": ["X....", "X....", "X....", "X....", "XXXXX"],
    "M": ["X...X", "XX.XX", "XXXXX", "X.X.X", "X...X"],
    "N": ["XX..X", "XXX.X", "X.X.X", "X.XXX", "X..XX"],
    "O": ["XXXXX", "X...X", "X...X", "X...X", "XXXXX"],
    "P": ["XXXXX", "X...X", "XXXXX", "X....", "X...."],
    "R": ["XXXX.", "X..XX", "XXXX.", "X..XX", "X...X"],
    "S": ["XXXXX", "X....", "XXXXX", "....X", "XXXXX"],
    "T": ["XXXXX", "..X..", "..X..", "..X..", "..X.."],
    "U": ["X...X", "X...X", "X...X", "X...X", "XXXXX"],
    "V": ["X...X", "X...X", "X...X", "XX.XX", ".XXX."],
    "W": ["X...X", "X...X", "X.X.X", "X.X.X", "XXXXX"],
    "Y": ["X...X", "X...X", "XXXXX", "..X..", "..X.."],
    "'": ["X", "X", ".", ".", "."],
    " ": ["..", "..", "..", "..", ".."],
}
MASCOT = [
    ".XXXXXXX.",
    "XXXXXXXXX",
    "XXXXXXXXX",
    "XXX.X.XXX",
    "XXXXXXXXX",
    "X.XXXXX.X",
    "XXX...XXX",
    "XXXXXXXXX",
    ".XXXXXXX.",
]
PLUS = ["..XXX..", "..XXX..", "XXXXXXX", "XXXXXXX", "XXXXXXX", "..XXX..", "..XXX.."]


def f(n):
    return f"{n:.2f}".rstrip("0").rstrip(".")


def bitmap_path(rows, x0, y0, c, r=0.5):
    """Path for a bitmap of cells: outer corners rounded, inner corners filleted."""
    H, Wd = len(rows), max(len(x) for x in rows)
    on = lambda i, j: 0 <= i < H and 0 <= j < len(rows[i]) and rows[i][j] == "X"
    R = r * c
    d = []
    for i in range(-1, H + 1):
        for j in range(-1, Wd + 1):
            x, y = x0 + j * c, y0 + i * c
            if on(i, j):
                tl = R if not on(i - 1, j) and not on(i, j - 1) else 0
                tr = R if not on(i - 1, j) and not on(i, j + 1) else 0
                br = R if not on(i + 1, j) and not on(i, j + 1) else 0
                bl = R if not on(i + 1, j) and not on(i, j - 1) else 0
                p = f"M{f(x + tl)} {f(y)}H{f(x + c - tr)}"
                if tr: p += f"A{f(tr)} {f(tr)} 0 0 1 {f(x + c)} {f(y + tr)}"
                p += f"V{f(y + c - br)}"
                if br: p += f"A{f(br)} {f(br)} 0 0 1 {f(x + c - br)} {f(y + c)}"
                p += f"H{f(x + bl)}"
                if bl: p += f"A{f(bl)} {f(bl)} 0 0 1 {f(x)} {f(y + c - bl)}"
                p += f"V{f(y + tl)}"
                if tl: p += f"A{f(tl)} {f(tl)} 0 0 1 {f(x + tl)} {f(y)}"
                d.append(p + "Z")
            else:
                # concave fillets in empty cells whose corner is wrapped by filled cells
                for di, dj, px, py in ((-1, -1, x, y), (-1, 1, x + c, y), (1, 1, x + c, y + c), (1, -1, x, y + c)):
                    if on(i + di, j) and on(i, j + dj) and on(i + di, j + dj):
                        dx, dy = -dj, -di  # direction into this cell from the corner
                        sweep = 0 if dx * dy > 0 else 1
                        d.append(f"M{f(px)} {f(py)}H{f(px + dx * R)}A{f(R)} {f(R)} 0 0 {sweep} {f(px)} {f(py + dy * R)}Z")
    return "".join(d)


def pixel_width(s, c):
    return (sum(len(G[ch][0]) for ch in s) + len(s) - 1) * c


def pixel_text(s, x, y, c, fill, animate=True, delay0=0.0):
    out, cx = [], x
    for k, ch in enumerate(s):
        rows = G[ch]
        if ch != " ":
            style = f' style="animation-delay:{delay0 + k * 0.06:.2f}s"' if animate else ""
            cls = ' class="px"' if animate else ""
            out.append(f'<path{cls}{style} d="{bitmap_path(rows, cx, y, c)}" fill="{fill}" stroke="{fill}" stroke-width="0.6"/>')
        cx += (len(rows[0]) + 1) * c
    return "".join(out)


def bitmap(rows, x, y, c, fill, extra=""):
    return f'<path{extra} d="{bitmap_path(rows, x, y, c)}" fill="{fill}" stroke="{fill}" stroke-width="0.6"/>'


def arrow_ne(cx, cy, s, color, sw=2.4):
    return (f'<path d="M{f(cx - s)} {f(cy + s)}L{f(cx + s)} {f(cy - s)}M{f(cx - s * 0.35)} {f(cy - s)}H{f(cx + s)}V{f(cy + s * 0.35)}" '
            f'fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')


# ---- svg builder ----
class Svg:
    def __init__(self, w, h, panel=True, bg=INK, radius=24):
        self.w, self.h, self.body, self.chars, self.css = w, h, [], {}, []
        if panel:
            self.body.append(f'<rect width="{w}" height="{h}" rx="{radius}" fill="{bg}"/>')

    def text(self, x, y, s, font, size, fill, anchor="start", ls=0.0, extra=""):
        self.chars.setdefault(font, set()).update(s)
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        l = f' letter-spacing="{f(ls)}"' if ls else ""
        self.body.append(f'<text x="{f(x)}" y="{f(y)}" font-family="cs-{font}" font-size="{f(size)}" fill="{fill}"{a}{l}{extra}>{escape(s)}</text>')

    def tspans(self, x, y, parts, font, size, extra=""):
        """parts: list of (text, fill, fontkey or None)"""
        spans = []
        for s, fill, fk in parts:
            fk = fk or font
            self.chars.setdefault(fk, set()).update(s)
            spans.append(f'<tspan fill="{fill}" font-family="cs-{fk}">{escape(s)}</tspan>')
        self.body.append(f'<text x="{f(x)}" y="{f(y)}" font-family="cs-{font}" font-size="{f(size)}"{extra}>{"".join(spans)}</text>')

    def add(self, s):
        self.body.append(s)

    def save(self, name, title):
        faces = "".join(font_face(k, v) for k, v in self.chars.items())
        css = faces + "text{font-kerning:none}" + "".join(self.css)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{escape(title)}">'
               f"<title>{escape(title)}</title><style>{css}</style>{''.join(self.body)}</svg>")
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
            fh.write(svg)
        print(f"{name}: {len(svg) / 1024:.1f} KB")


REVEAL = ("@keyframes rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}"
          ".px{animation:rise .6s cubic-bezier(.2,.8,.2,1) both}")


def wrap(s, font, size, maxw):
    lines, cur = [], ""
    for word in s.split():
        t = (cur + " " + word).strip()
        if text_width(t, font, size) > maxw and cur:
            lines.append(cur); cur = word
        else:
            cur = t
    return lines + [cur]


def label(svg, x, y, num, name, color=LIME):
    svg.text(x, y, f"( {num} ) — {name}", "mono", 13, color, ls=2)


def section_head(svg, num, name, title, aside, cell=10, y=56):
    label(svg, PAD, y + 14, num, name)
    svg.text(W - PAD, y + 14, aside, "serif", 22, MUTE, anchor="end")
    svg.add(pixel_text(title, PAD, y + 44, cell, PAPER))
    return y + 44 + 5 * cell


# ======================= hero =======================
def hero():
    H = 560
    s = Svg(W, H)
    s.css.append(REVEAL + "@keyframes blink{0%,92%,100%{transform:scaleY(0)}95%{transform:scaleY(1)}}"
                 ".lid{transform-box:fill-box;transform-origin:center;animation:blink 5s infinite}")
    s.add(f'<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="24"/></clipPath></defs>')
    label(s, PAD, 76, "00", "STUDIO")
    s.text(W - PAD, 78, "One voice. One visual. One studio.", "serif", 22, MUTE, anchor="end")

    c = 15
    s.add(pixel_text("SAM", PAD, 128, c, PAPER))
    s.add(pixel_text("DARAMROEI", PAD, 128 + 6.4 * c, c, LIME, delay0=0.18))

    mc = 24
    mx, my = W - PAD - 9 * mc, 118
    s.add(f'<g class="px" style="animation-delay:.5s">{bitmap(MASCOT, mx, my, mc, LIME)}'
          f'<rect class="lid" x="{mx + 3 * mc - 2}" y="{my + 3 * mc - 2}" width="{mc + 4}" height="{mc + 4}" fill="{LIME}"/>'
          f'<rect class="lid" x="{mx + 5 * mc - 2}" y="{my + 3 * mc - 2}" width="{mc + 4}" height="{mc + 4}" fill="{LIME}"/></g>')

    y = 374
    lines = [
        [("Most businesses confuse having a website with", MUTE, None)],
        [("having a presence. ", MUTE, None), ("I founded Cheerio Studios", PAPER, None)],
        [("to work in the gap between the two.", PAPER, None)],
    ]
    for ln in lines:
        s.tspans(PAD, y, ln, "inter", 20)
        y += 31
    s.text(PAD, y + 22, "FOUNDER · SOFTWARE DEVELOPER · DESIGNER", "mono", 13, MUTE, ls=2)

    # pill CTA
    pw, ph = 292, 72
    px_, py_ = W - PAD - pw, 386
    s.add(f'<rect x="{px_}" y="{py_}" width="{pw}" height="{ph}" rx="{ph / 2}" fill="{LIME}"/>')
    s.text(px_ + 34, py_ + ph / 2 + 5, "VISIT THE STUDIO", "grotesk", 14, INK, ls=2.2)
    cx, cy = px_ + pw - ph / 2, py_ + ph / 2
    s.add(f'<circle cx="{cx}" cy="{cy}" r="{ph / 2 - 8}" fill="{INK}"/>' + arrow_ne(cx, cy, 7, LIME))

    s.add(f'<g clip-path="url(#c)"><polygon points="560,{H} {W},{H - 44} {W},{H}" fill="{LIME}"/></g>')
    s.save("hero.svg", "Sam Daramroei — Founder of Cheerio Studios. We build digital presence.")


# ======================= marquee =======================
def marquee():
    H, size, gap = 96, 34, 32
    items = ["Brand Identity", "Web Design & Development", "Strategy & Consulting",
             "Digital Design", "Asset Management", "Maintenance & Support"]
    s = Svg(W, H, bg=LIME)
    pc = 4  # plus icon cell
    parts, x = [], 0.0
    for it in items:
        t = it.upper()
        parts.append(("t", x + gap, t))
        x += gap + text_width(t, "grotesk", size, -0.5) + gap
        parts.append(("p", x, None))
        x += 7 * pc
    loop = x
    s.css.append(f"@keyframes run{{to{{transform:translateX(-{f(loop)}px)}}}}.run{{animation:run 36s linear infinite}}")
    s.add(f'<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="24"/></clipPath></defs><g clip-path="url(#c)"><g class="run">')
    for rep in range(3):
        off = rep * loop
        for kind, px_, t in parts:
            if kind == "t":
                s.text(px_ + off, H / 2 + size * 0.36, t, "grotesk", size, INK, ls=-0.5)
            else:
                s.add(bitmap(PLUS, px_ + off, H / 2 - 3.5 * pc, pc, INK))
    s.add("</g></g>")
    s.save("marquee.svg", "Brand Identity · Web Design & Development · Strategy & Consulting · Digital Design · Asset Management · Maintenance & Support")


# ======================= about =======================
def about():
    H = 500
    s = Svg(W, H)
    s.css.append(REVEAL)
    y = section_head(s, "01", "ABOUT", "WHO I AM", "Design × technology.")
    y += 84
    s.tspans(PAD, y, [("I don't just design. I build systems", PAPER, None)], "serif", 44)
    s.tspans(PAD, y + 50, [("that make your brand ", PAPER, None), ("inevitable.", LIME, "serif-it")], "serif", 44)

    vals = [("Intentional", "Every pixel and every line of code I ship earns its place."),
            ("Systems first", "I build reusable systems, not one-off solutions."),
            ("Bold, but flexible", "I hold strong opinions and build to adapt."),
            ("In it for the long run", "I look for partnerships, not transactions.")]
    colw = (W - 2 * PAD) / 4
    vy = y + 118
    s.add(f'<rect x="{PAD}" y="{vy - 34}" width="{W - 2 * PAD}" height="1" fill="{GHOST}"/>')
    for k, (t, d) in enumerate(vals):
        x = PAD + k * colw
        s.text(x, vy, f"0{k + 1}", "mono", 13, LIME, ls=1)
        s.text(x, vy + 34, t, "grotesk", 21, PAPER, ls=-0.3)
        for n, ln in enumerate(wrap(d, "inter", 15, colw - 36)):
            s.text(x, vy + 62 + n * 22, ln, "inter", 15, MUTE)
    s.save("about.svg", "About — I don't just design. I build systems that make your brand inevitable.")


# ======================= services =======================
def services():
    H = 660
    s = Svg(W, H)
    s.css.append(REVEAL)
    y = section_head(s, "02", "SERVICES", "WHAT I DO", "Six disciplines. One studio.") + 40
    items = [("Brand Identity", "I craft identity systems that stay consistent across every platform."),
             ("Web Design & Development", "I build fast, responsive, scalable sites on a modern stack."),
             ("Strategy & Consulting", "I align your digital presence with real business goals."),
             ("Digital Design", "I design user-centered experiences where aesthetics meet function."),
             ("Asset Management", "I keep your assets centralized, organized and always on-brand."),
             ("Maintenance & Support", "I stay on for ongoing care and long-term partnership.")]
    gap = 20
    cw, ch = (W - 2 * PAD - 2 * gap) / 3, 196
    for k, (t, d) in enumerate(items):
        x = PAD + (k % 3) * (cw + gap)
        yy = y + (k // 3) * (ch + gap)
        s.add(f'<rect x="{f(x)}" y="{f(yy)}" width="{f(cw)}" height="{ch}" rx="16" fill="{INK2}" stroke="{INK3}"/>')
        s.text(x + 28, yy + 44, f"0{k + 1}", "mono", 13, MUTE, ls=1)
        s.add(bitmap(PLUS, x + cw - 28 - 21, yy + 28, 3, LIME))
        s.text(x + 28, yy + 104, t, "grotesk", 23, PAPER, ls=-0.4)
        for n, ln in enumerate(wrap(d, "inter", 15, cw - 56)):
            s.text(x + 28, yy + 136 + n * 22, ln, "inter", 15, MUTE)
    s.save("services.svg", "Services — Brand Identity, Web Design & Development, Strategy & Consulting, Digital Design, Asset Management, Maintenance & Support")


# ======================= work =======================
def work():
    H = 666
    s = Svg(W, H)
    s.css.append(REVEAL)
    y = section_head(s, "03", "WORK", "SELECTED WORK", "Things in the making.") + 40
    projects = [
        ("COMMUNITY PORTAL", "SDMT", "Cinema & digital media community portal for BAIBU.", ["NEXT.JS", "SUPABASE"], "sdmt"),
        ("WEB PLATFORM", "RisingGen", "Empowering young adults across Central Europe.", ["REACT", "NEXT.JS"], "rising"),
        ("DESIGN STUDIO", "Cheerio Studios", "My full-service brand, UI/UX and web studio.", ["BRAND", "WEB"], "cheerio"),
    ]
    gap = 20
    cw, ch, vh = (W - 2 * PAD - 2 * gap) / 3, 424, 200
    for k, (tag, name, desc, chips, vis) in enumerate(projects):
        x = PAD + k * (cw + gap)
        s.add(f'<rect x="{f(x)}" y="{y}" width="{f(cw)}" height="{ch}" rx="16" fill="{INK2}" stroke="{INK3}"/>')
        # visual
        vx, vy, vw = x + 12, y + 12, cw - 24
        if vis == "sdmt":
            s.add(f'<rect x="{f(vx)}" y="{vy}" width="{f(vw)}" height="{vh}" rx="10" fill="{LIME}"/>')
            c = 9; s.add(pixel_text("SDMT", vx + (vw - pixel_width("SDMT", c)) / 2, vy + (vh - 5 * c) / 2, c, INK, animate=False))
        elif vis == "rising":
            s.add(f'<rect x="{f(vx)}" y="{vy}" width="{f(vw)}" height="{vh}" rx="10" fill="{INK3}"/>')
            c = 7
            s.add(pixel_text("RISING", vx + (vw - pixel_width("RISING", c)) / 2, vy + vh / 2 - 5 * c - 5, c, PAPER, animate=False))
            s.add(pixel_text("GEN", vx + (vw - pixel_width("GEN", c)) / 2, vy + vh / 2 + 5, c, LIME, animate=False))
        else:
            s.add(f'<rect x="{f(vx)}" y="{vy}" width="{f(vw)}" height="{vh}" rx="10" fill="{GHOST}"/>')
            c = 14; s.add(bitmap(MASCOT, vx + (vw - 9 * c) / 2, vy + (vh - 9 * c) / 2, c, LIME))
        s.text(vx + 8, y + vh + 12 + 40, f"0{k + 1} — {tag}", "mono", 12, MUTE, ls=1.5)
        s.text(vx + 8, y + vh + 12 + 80, name, "grotesk", 28, PAPER, ls=-0.6)
        dl = wrap(desc, "inter", 15, vw - 24)
        for n, ln in enumerate(dl):
            s.text(vx + 8, y + vh + 12 + 110 + n * 22, ln, "inter", 15, MUTE)
        cy_ = y + vh + 12 + 132 + (len(dl) - 1) * 22
        cxp = vx + 8
        for chip in chips:
            tw = text_width(chip, "mono", 11, 1.2)
            s.add(f'<rect x="{f(cxp)}" y="{cy_}" width="{f(tw + 24)}" height="28" rx="14" fill="none" stroke="{GHOST}"/>')
            s.text(cxp + 12, cy_ + 18, chip, "mono", 11, PAPER, ls=1.2)
            cxp += tw + 32
    s.save("work.svg", "Selected work — SDMT, RisingGen, Cheerio Studios")


# ======================= small section headers =======================
def header(name, num, lbl, title, aside):
    s = Svg(W, 170)
    s.css.append(REVEAL)
    section_head(s, num, lbl, title, aside)
    s.save(name, f"{lbl.title()} — {title.title()}")


# ======================= contact =======================
def contact():
    H = 330
    s = Svg(W, H)
    s.css.append(REVEAL)
    label(s, PAD, 70, "06", "CONTACT")
    s.text(W - PAD, 72, "Have a project in mind?", "serif", 22, MUTE, anchor="end")
    c = 16
    s.add(pixel_text("LET'S", PAD, 110, c, PAPER))
    s.add(pixel_text("TALK", PAD + pixel_width("LET'S", c) + 2 * c, 110, c, LIME, delay0=0.3))
    s.tspans(PAD, 110 + 5 * c + 64, [("Brand systems, web builds, or just a good conversation — ", MUTE, None),
                                    ("my inbox is open.", PAPER, None)], "inter", 19)
    s.add(f'<g class="px" style="animation-delay:.6s">{bitmap(MASCOT, W - PAD - 9 * 12, 110 + 5 * c - 9 * 12, 12, LIME)}</g>')
    s.save("contact.svg", "Let's talk")


def pill(name, text, primary):
    ph = 64
    tw = text_width(text, "grotesk", 14, 2.2)
    pw = 32 + tw + 22 + ph - 8
    s = Svg(int(pw) + 2, ph + 2, panel=False)
    fill, fg, stroke = (LIME, INK, LIME) if primary else (INK, PAPER, GHOST)
    s.add(f'<rect x="1" y="1" width="{int(pw)}" height="{ph}" rx="{ph / 2}" fill="{fill}" stroke="{stroke}"/>')
    s.text(33, 1 + ph / 2 + 5, text, "grotesk", 14, fg, ls=2.2)
    cx, cy = 1 + int(pw) - ph / 2, 1 + ph / 2
    s.add(f'<circle cx="{cx}" cy="{cy}" r="{ph / 2 - 8}" fill="{INK if primary else LIME}"/>' + arrow_ne(cx, cy, 6.5, LIME if primary else INK))
    s.save(name, text.title())


def footer():
    H = 120
    s = Svg(W, H)
    c = 6
    s.add(bitmap(MASCOT, PAD, (H - 9 * c) / 2, c, LIME))
    s.text(PAD + 9 * c + 24, H / 2 + 8, "One voice. One visual. One studio.", "serif", 26, PAPER)
    s.text(W - PAD, H / 2 + 5, "© 2026 CHEERIO STUDIOS", "mono", 12, MUTE, anchor="end", ls=2)
    s.save("footer.svg", "One voice. One visual. One studio. — Cheerio Studios")


# ======================= live stats (GitHub API) =======================
STATS_QUERY = """query($login: String!) { user(login: $login) {
  pullRequests { totalCount }
  contributionsCollection { contributionCalendar { totalContributions } }
  repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
    totalCount
    nodes { stargazerCount languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name } } } }
  }
} }"""


def fetch_stats(login, token):
    req = urllib.request.Request("https://api.github.com/graphql",
                                 data=json.dumps({"query": STATS_QUERY, "variables": {"login": login}}).encode(),
                                 headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    user = json.load(urllib.request.urlopen(req))["data"]["user"]
    repos = user["repositories"]
    langs = {}
    for r in repos["nodes"]:
        for e in r["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    return {
        "contributions": user["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "repos": repos["totalCount"],
        "prs": user["pullRequests"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos["nodes"]),
        "langs": sorted(langs.items(), key=lambda kv: -kv[1]),
    }


def stats_card(data):
    H = 350
    s = Svg(W, H)
    blocks = [("CONTRIBUTIONS · 12 MO", data["contributions"]), ("PUBLIC REPOS", data["repos"]),
              ("PULL REQUESTS", data["prs"]), ("STARS EARNED", data["stars"])]
    colw = (W - 2 * PAD) / 4
    for k, (lbl, n) in enumerate(blocks):
        x = PAD + k * colw
        if k:
            s.add(f'<rect x="{f(x - 24)}" y="52" width="1" height="104" fill="{GHOST}"/>')
        s.text(x, 72, lbl, "mono", 12, MUTE, ls=1.5)
        s.text(x, 146, f"{n:,}", "grotesk", 64, LIME if k == 0 else PAPER, ls=-2)
    s.add(f'<rect x="{PAD}" y="192" width="{W - 2 * PAD}" height="1" fill="{GHOST}"/>')

    label(s, PAD, 236, "LANG", "MOST USED")
    s.text(W - PAD, 236, "UPDATED " + datetime.date.today().strftime("%d %b %Y").upper(), "mono", 12, MUTE, anchor="end", ls=1.5)
    total = sum(v for _, v in data["langs"]) or 1
    top = data["langs"][:5]
    rest = total - sum(v for _, v in top)
    if rest / total >= 0.005:
        top.append(("Other", rest))
    colors = [LIME, PAPER, "#A6CC17", MUTE, "#5B6150", GHOST]
    bw, bx, by = W - 2 * PAD, float(PAD), 256
    s.add(f'<defs><clipPath id="bar"><rect x="{PAD}" y="{by}" width="{bw}" height="14" rx="7"/></clipPath></defs><g clip-path="url(#bar)">')
    for (name, v), col in zip(top, colors):
        w = bw * v / total
        s.add(f'<rect x="{f(bx)}" y="{by}" width="{f(w + 0.5)}" height="14" fill="{col}"/>')
        bx += w
    s.add("</g>")
    lx = float(PAD)
    for (name, v), col in zip(top, colors):
        pct = f"{100 * v / total:.1f}%"
        s.add(f'<rect x="{f(lx)}" y="302" width="12" height="12" rx="3" fill="{col}"/>')
        s.text(lx + 22, 313, name, "grotesk-med", 17, PAPER)
        nx = lx + 22 + text_width(name, "grotesk-med", 17) + 10
        s.text(nx, 313, pct, "mono", 12, MUTE)
        lx = nx + text_width(pct, "mono", 12) + 36
    s.save("stats.svg", f"GitHub stats — {data['contributions']} contributions in the last year, {data['repos']} public repos")


if MODE == "stats":
    stats_card(fetch_stats(os.environ.get("GITHUB_USER", "cheerios-design"), os.environ["GITHUB_TOKEN"]))
else:
    hero(); marquee(); about(); services(); work()
    header("toolkit.svg", "04", "TOOLKIT", "TOOLKIT", "Design to deploy.")
    header("activity.svg", "05", "ACTIVITY", "IN MOTION", "Shipping, daily.")
    contact()
    pill("btn-website.svg", "CHEERIOSTUDIOS.COM", True)
    pill("btn-linkedin.svg", "LINKEDIN", False)
    pill("btn-instagram.svg", "INSTAGRAM", False)
    pill("btn-email.svg", "EMAIL", False)
    footer()
