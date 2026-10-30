#!/usr/bin/env python3
"""Hallowed Night branding: unlock logo, screensaver art and theme previews.

Usage: generators/hallowed_branding.py <theme_dir> <icons_dir>
Run after render.py has written <theme_dir>/backgrounds/1-graveyard-moon.png
and hallowed_icons.py has written <icons_dir>/Hallowed-Night-Icons.

Writes into <theme_dir>: unlock.png, screensaver.txt, preview.png,
preview-unlock.png. Needs rsvg-convert, ImageMagick (magick) and an Omarchy
install (for the stock wordmark and `omarchy transcode ascii`).
Previews are mock-ups drawn from the palette, never screenshots, so they
cannot leak anything from the machine that renders them.
"""
import base64
import os
import subprocess
import sys
import tempfile
import tomllib
from xml.sax.saxutils import escape

OMARCHY = os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")
WORDMARK = os.path.join(OMARCHY, "themes", "catppuccin", "unlock.png")
FONT = "JetBrainsMono Nerd Font"


def run(*cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def data_uri(path, mime):
    with open(path, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"


def render(svg_text, out, width):
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False) as f:
        f.write(svg_text)
    try:
        run("rsvg-convert", "-w", str(width), "-o", out, f.name)
    finally:
        os.unlink(f.name)


# ------------------------------------------------------------ unlock.png


def unlock(theme, c):
    """Omarchy wordmark in a pumpkin gradient with toxic slime dripping off it."""
    W, H, mark_h = 800, 188, 150
    with tempfile.TemporaryDirectory() as tmp:
        mark = os.path.join(tmp, "mark.png")
        # White glyphs: an SVG mask reads luminance, so the stock blue would dim the gradient.
        run("magick", WORDMARK, "-resize", f"x{mark_h}", "-background", "none", "-gravity", "north",
            "-extent", f"{W}x{H}", "-fill", "white", "-colorize", "100", mark)
        alpha = subprocess.run(["magick", mark, "-alpha", "extract", "-depth", "8", "gray:-"],
                               check=True, capture_output=True).stdout
        mark_uri = data_uri(mark, "image/png")
    # Lowest opaque row per column; runs of columns sharing a bottom edge are letter feet.
    bottom = []
    for x in range(W):
        rows = [y for y in range(H) if alpha[y * W + x] > 128]
        bottom.append(max(rows) if rows else -1)
    feet, start = [], 0
    for x in range(1, W + 1):
        if x == W or abs(bottom[x] - bottom[start]) > 2 or bottom[x] < 0:
            if bottom[start] > mark_h * 0.8 and x - start >= 8:
                feet.append((start, x - 1, bottom[start]))
            start = x
    drips = []
    lengths = [14, 30, 8, 22, 34, 12, 26, 18, 32, 10]
    for i, (a, b, y) in enumerate(feet):
        if i % 2:  # every other foot, so it drips rather than melts
            continue
        x = (a + b) / 2
        length = min(lengths[i % len(lengths)], H - y - 8)
        w = min(12, (b - a) * 0.6)
        drips.append(f'<path d="M{x - w / 2:.1f},{y - 3} v{length} a{w / 2:.1f},{w / 2:.1f} 0 0 0 {w:.1f},0 v-{length} z" fill="{c["green"]}"/>')
        drips.append(f'<rect x="{a:.0f}" y="{y - 3}" width="{b - a + 1}" height="5" rx="2.5" fill="{c["green"]}"/>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">'
           f'<defs><linearGradient id="g" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="{mark_h}">'
           f'<stop offset="0" stop-color="#ffc061"/><stop offset="1" stop-color="{c["accent"]}"/></linearGradient>'
           f'<mask id="m"><image width="{W}" height="{H}" href="{mark_uri}"/></mask></defs>'
           f'<rect width="{W}" height="{H}" fill="url(#g)" mask="url(#m)"/>{"".join(drips)}</svg>')
    out = os.path.join(theme, "unlock.png")
    render(svg, out, W)
    return out


# ------------------------------------------------------- screensaver.txt


def screensaver(theme):
    """A jack-o'-lantern flanked by bats, as braille art for the TTE screensaver."""
    bat = ("M0,0 C-8,-10 -22,-14 -40,-8 C-32,-4 -30,2 -34,8 C-26,4 -20,6 -16,12 C-12,6 -6,4 0,6 "
           "C6,4 12,6 16,12 C20,6 26,4 34,8 C30,2 32,-4 40,-8 C22,-14 8,-10 0,0 Z")
    pumpkin = "".join(f'<ellipse cx="{400 + dx}" cy="220" rx="{rx}" ry="150"/>'
                      for dx, rx in ((-95, 110), (95, 110), (-48, 120), (48, 120), (0, 128)))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400" viewBox="0 0 800 400">'
           f'<rect width="800" height="400" fill="#fff"/><g fill="#000">{pumpkin}'
           f'<path d="M390,80 q4,-50 36,-66 l14,16 q-26,16 -26,50 z"/>'
           f'<path d="{bat}" transform="translate(95,90) scale(2.2) rotate(-8)"/>'
           f'<path d="{bat}" transform="translate(715,70) scale(1.7) rotate(12)"/>'
           f'<path d="{bat}" transform="translate(705,250) scale(1.2) rotate(-10)"/></g>'
           f'<g fill="#fff"><path d="M300,190 l40,-60 l40,60 z M420,190 l40,-60 l40,60 z"/>'
           f'<path d="M280,250 Q400,350 520,250 Q400,290 280,250 Z"/></g>'
           f'<g fill="#000"><rect x="346" y="254" width="30" height="24"/><rect x="424" y="254" width="30" height="24"/></g></svg>')
    out = os.path.join(theme, "screensaver.txt")
    with tempfile.TemporaryDirectory() as tmp:
        png = os.path.join(tmp, "art.png")
        render(svg, png, 800)
        run("omarchy", "transcode", "ascii", png, out, "--width", "80", "--mode", "braille")
    return out


# -------------------------------------------------- preview-unlock.png


def preview_unlock(theme, c):
    W, H = 1920, 1080
    logo = data_uri(os.path.join(theme, "unlock.png"), "image/png")
    lock = ("M-9,-2 v-6 a9,9 0 0 1 18,0 v6 h3 v16 h-24 v-16 Z M-5,-2 h10 v-6 a5,5 0 0 0 -10,0 Z")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">'
           f'<rect width="{W}" height="{H}" fill="{c["background"]}"/>'
           f'<image x="{(W - 800) / 2}" y="400" width="800" height="188" href="{logo}"/>'
           f'<path d="{lock}" transform="translate(800,652) scale(1.3)" fill="{c["foreground"]}" fill-rule="evenodd"/>'
           f'<rect x="830" y="630" width="290" height="40" fill="{c["lighter_background"]}" stroke="{c["foreground"]}" stroke-width="2"/>'
           f'<text x="846" y="658" font-family="{FONT}" font-size="22" fill="{c["foreground"]}">••••</text></svg>')
    out = os.path.join(theme, "preview-unlock.png")
    render(svg, out, W)
    return out


# --------------------------------------------------------- preview.png

CODE = [
    [("kw", "local "), ("fg", "spooky "), ("op", "= "), ("fn", "require"), ("op", "("), ("str", '"hallowed.night"'), ("op", ")")],
    [],
    [("com", "-- carve a lantern for every guest at the door")],
    [("kw", "function "), ("fg", "spooky."), ("fn", "carve"), ("op", "("), ("par", "pumpkin"), ("op", ", "), ("par", "guests"), ("op", ")")],
    [("fg", "  "), ("kw", "if "), ("fg", "pumpkin.size "), ("op", "< "), ("num", "3 "), ("kw", "then")],
    [("fg", "    "), ("kw", "return "), ("con", "nil"), ("op", ", "), ("str", '"too small to carve"')],
    [("fg", "  "), ("kw", "end")],
    [("fg", "  "), ("kw", "local "), ("fg", "lantern "), ("op", "= { "), ("par", "glow "), ("op", "= "), ("str", '"#ff7a1a"'), ("op", ", "), ("par", "candles "), ("op", "= "), ("num", "13 "), ("op", "}")],
    [("fg", "  "), ("kw", "for "), ("fg", "i "), ("op", "= "), ("num", "1"), ("op", ", #"), ("fg", "guests "), ("kw", "do")],
    [("fg", "    lantern[i] "), ("op", "= "), ("fn", "treat"), ("op", "("), ("fg", "guests[i]"), ("op", ") .. "), ("str", '" boo!"')],
    [("fg", "  "), ("kw", "end")],
    [("fg", "  "), ("kw", "return "), ("fg", "lantern")],
    [("kw", "end")],
    [],
    [("kw", "return "), ("fg", "spooky")],
]


def preview(theme, icons, c):
    W, H, bar, gap = 1800, 1012, 30, 12
    colour = {"kw": c["magenta"], "fg": c["foreground"], "op": c["light_foreground"], "fn": c["blue"],
              "str": c["green"], "com": c["dark_foreground"], "par": c["cyan"], "num": c["orange"],
              "con": c["red"]}
    wall = data_uri(os.path.join(theme, "backgrounds", "1-graveyard-moon.png"), "image/png")
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="{FONT}">',
         '<defs><linearGradient id="border" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ff7a1a"/>'
         '<stop offset="1" stop-color="#b44dff"/></linearGradient></defs>',
         f'<image width="{W}" height="{H}" href="{wall}" preserveAspectRatio="xMidYMid slice"/>',
         f'<rect width="{W}" height="{bar}" fill="{c["background"]}"/>']
    for i in range(1, 6):
        fill = c["accent"] if i == 1 else c["foreground"]
        o.append(f'<text x="{14 + (i - 1) * 22}" y="20" font-size="14" fill="{fill}">{i}</text>')
    o.append(f'<text x="{W / 2}" y="20" font-size="14" fill="{c["foreground"]}" text-anchor="middle">Saturday 21:13</text>')
    o.append(f'<text x="{W - 14}" y="20" font-size="14" fill="{c["foreground"]}" text-anchor="end">\U000f0a4d  \U000f05a9  \U000f0079  \U000f0425</text>')

    def window(x, y, w, h, active):
        stroke = "url(#border)" if active else "#3b2752"
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c["background"]}" fill-opacity="0.96" '
                f'stroke="{stroke}" stroke-width="2"/>')

    lx, ly, lw, lh = gap, bar + gap, 1000, H - bar - 2 * gap
    o.append(window(lx, ly, lw, lh, True))
    for n, line in enumerate(CODE):
        y = ly + 34 + n * 26
        o.append(f'<text x="{lx + 14}" y="{y}" font-size="16" fill="{c["muted"]}">{n + 1:>3}</text>')
        x = lx + 64
        tspans = "".join(f'<tspan fill="{colour[k]}">{escape(t)}</tspan>' for k, t in line)
        o.append(f'<text x="{x}" y="{y}" font-size="16" xml:space="preserve">{tspans}</text>')
    sy = ly + lh - 30
    o.append(f'<rect x="{lx + 2}" y="{sy}" width="{lw - 4}" height="28" fill="{c["dark_background"]}"/>')
    o.append(f'<rect x="{lx + 2}" y="{sy}" width="92" height="28" fill="{c["accent"]}"/>')
    o.append(f'<text x="{lx + 16}" y="{sy + 19}" font-size="14" font-weight="bold" fill="{c["background"]}">NORMAL</text>')
    o.append(f'<text x="{lx + 110}" y="{sy + 19}" font-size="14" fill="{c["foreground"]}">spooky.lua</text>')
    o.append(f'<text x="{lx + lw - 16}" y="{sy + 19}" font-size="14" fill="{c["dark_foreground"]}" text-anchor="end">lua  13:13</text>')

    rx, rw = lx + lw + gap, W - (lx + lw + gap) - gap
    th = 330
    o.append(window(rx, ly, rw, th, False))
    term = [
        [(c["accent"], "~/crypt "), (c["green"], "❯ "), (c["foreground"], "ls")],
        [(c["blue"], "bats  cauldron  graves  potions  "), (c["foreground"], "spells.txt  "), (c["green"], "summon.sh")],
        [(c["accent"], "~/crypt "), (c["green"], "❯ "), (c["foreground"], "grep -c hex spells.txt")],
        [(c["foreground"], "13")],
        [(c["accent"], "~/crypt "), (c["green"], "❯ "), (c["foreground"], "./summon.sh --quietly")],
        [(c["magenta"], "  summoning "), (c["yellow"], "▰▰▰▰▰▰▰▱▱▱ "), (c["foreground"], "70%")],
        [(c["accent"], "~/crypt "), (c["green"], "❯ "), (c["foreground"], "█")],
    ]
    for n, line in enumerate(term):
        tspans = "".join(f'<tspan fill="{col}">{escape(t)}</tspan>' for col, t in line)
        o.append(f'<text x="{rx + 16}" y="{ly + 34 + n * 30}" font-size="16" xml:space="preserve">{tspans}</text>')

    fy, fh = ly + th + gap, lh - th - gap
    o.append(window(rx, fy, rw, fh, False))
    o.append(f'<rect x="{rx + 2}" y="{fy + 2}" width="{rw - 4}" height="44" fill="{c["dark_background"]}"/>')
    o.append(f'<text x="{rx + rw / 2}" y="{fy + 30}" font-size="16" fill="{c["foreground"]}" text-anchor="middle" font-family="sans-serif" font-weight="bold">Home</text>')
    side = ["Home", "Recent", "Starred", "Network", "Trash"]
    o.append(f'<rect x="{rx + 2}" y="{fy + 46}" width="170" height="{fh - 48}" fill="{c["dark_background"]}" fill-opacity="0.6"/>')
    for n, s in enumerate(side):
        if n == 0:
            o.append(f'<rect x="{rx + 10}" y="{fy + 60}" width="154" height="30" rx="6" fill="{c["selection"]}"/>')
        o.append(f'<text x="{rx + 24}" y="{fy + 81 + n * 40}" font-size="15" font-family="sans-serif" fill="{c["foreground"]}">{s}</text>')
    places = os.path.join(icons, "Hallowed-Night-Icons", "scalable", "places")
    grid = [("user-desktop", "Desktop"), ("folder-documents", "Documents"), ("folder-download", "Downloads"),
            ("folder-music", "Music"), ("folder-pictures", "Pictures"), ("folder-videos", "Videos"),
            ("folder", "Spells"), ("user-trash-full", "Trash")]
    for n, (icon, label) in enumerate(grid):
        gx = rx + 196 + (n % 4) * 150
        gy = fy + 70 + (n // 4) * 170
        o.append(f'<image x="{gx}" y="{gy}" width="96" height="96" href="{data_uri(os.path.join(places, icon + ".svg"), "image/svg+xml")}"/>')
        o.append(f'<text x="{gx + 48}" y="{gy + 124}" font-size="15" font-family="sans-serif" fill="{c["foreground"]}" text-anchor="middle">{label}</text>')
    o.append("</svg>")
    out = os.path.join(theme, "preview.png")
    render("".join(o), out, W)
    return out


def main(theme, icons):
    with open(os.path.join(theme, "colors.toml"), "rb") as f:
        c = tomllib.load(f)
    for path in (unlock(theme, c), screensaver(theme), preview_unlock(theme, c), preview(theme, icons, c)):
        print(path)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
