#!/usr/bin/env python3
"""Monograph branding: unlock logo, screensaver art and theme previews.

Usage: generators/monograph_branding.py <theme_dir>
Run after render.py has written <theme_dir>/backgrounds/1-hello.png.

Writes into <theme_dir>: unlock.png, screensaver.txt, preview.png,
preview-unlock.png. The static unlock.png says WELCOME only; the animated boot
screen (boot-unlock.sh) adds your name on your own computer. Previews are
mock-ups drawn from the palette, never screenshots.
"""
import os
import sys
import tempfile
import tomllib
from xml.sax.saxutils import escape

from halloween_branding import data_uri, render, run
from monograph import FONT


def unlock(theme, c):
    W, H = 800, 188
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">'
           f'<text x="{W / 2}" y="112" font-family="{FONT}" font-size="104" font-weight="700" '
           f'fill="{c["bright_foreground"]}" text-anchor="middle">WELCOME</text>'
           f'<rect x="{W / 2 - 270}" y="146" width="540" height="4" fill="{c["accent"]}"/></svg>')
    out = os.path.join(theme, "unlock.png")
    render(svg, out, W)
    return out


def screensaver(theme):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="800" height="240"><rect width="800" height="240" fill="#fff"/>'
           f'<text x="40" y="170" font-family="{FONT}" font-size="150" font-weight="700" fill="#000">hello.</text>'
           '<rect x="650" y="52" width="80" height="140" fill="#000"/></svg>')
    out = os.path.join(theme, "screensaver.txt")
    with tempfile.TemporaryDirectory() as tmp:
        png = os.path.join(tmp, "art.png")
        render(svg, png, 800)
        run("omarchy", "transcode", "ascii", png, out, "--width", "80", "--mode", "braille")
    return out


def preview_unlock(theme, c):
    W, H = 1920, 1080
    logo = data_uri(os.path.join(theme, "unlock.png"), "image/png")
    lock = "M-9,-2 v-6 a9,9 0 0 1 18,0 v6 h3 v16 h-24 v-16 Z M-5,-2 h10 v-6 a5,5 0 0 0 -10,0 Z"
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">'
           f'<rect width="{W}" height="{H}" fill="{c["background"]}"/>'
           f'<image x="{(W - 800) / 2}" y="400" width="800" height="188" href="{logo}"/>'
           f'<path d="{lock}" transform="translate(800,652) scale(1.3)" fill="{c["foreground"]}" fill-rule="evenodd"/>'
           f'<rect x="830" y="630" width="290" height="40" fill="{c["lighter_background"]}" stroke="{c["foreground"]}" stroke-width="2"/>'
           f'<text x="846" y="658" font-family="{FONT}" font-size="22" fill="{c["foreground"]}">••••</text></svg>')
    out = os.path.join(theme, "preview-unlock.png")
    render(svg, out, W)
    return out


CODE = [
    [("com", "# set the page, then get out of the way")],
    [("kw", "def "), ("fn", "typeset"), ("op", "("), ("par", "text"), ("op", ", "), ("par", "size"), ("op", "="), ("num", "16"), ("op", "):")],
    [("fg", "    lines "), ("op", "= "), ("fg", "text."), ("fn", "splitlines"), ("op", "()")],
    [("fg", "    "), ("kw", "for "), ("fg", "n"), ("op", ", "), ("fg", "line "), ("kw", "in "), ("fn", "enumerate"), ("op", "("), ("fg", "lines"), ("op", "):")],
    [("fg", "        "), ("kw", "yield "), ("fg", "n "), ("op", "* "), ("fg", "size "), ("op", "* "), ("num", "1.5"), ("op", ", "), ("fg", "line")],
    [],
    [("fg", "page "), ("op", "= "), ("fn", "typeset"), ("op", "("), ("str", '"hello.\\nwelcome to omarchy"'), ("op", ")")],
    [("kw", "assert "), ("fn", "len"), ("op", "("), ("fn", "list"), ("op", "("), ("fg", "page"), ("op", ")) == "), ("num", "2")],
]


def preview(theme, c):
    W, H, bar, gap = 1800, 1012, 30, 12
    colour = {"kw": c["accent"], "fg": c["foreground"], "op": c["dark_foreground"], "fn": c["blue"],
              "str": c["green"], "com": c["muted"], "par": c["cyan"], "num": c["orange"]}
    wall = data_uri(os.path.join(theme, "backgrounds", "1-hello.png"), "image/png")
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="{FONT}">',
         f'<image width="{W}" height="{H}" href="{wall}" preserveAspectRatio="xMidYMid slice"/>',
         f'<rect width="{W}" height="{bar}" fill="{c["background"]}"/>']
    for i in range(1, 6):
        fill = c["accent"] if i == 1 else c["foreground"]
        o.append(f'<text x="{14 + (i - 1) * 22}" y="20" font-size="14" fill="{fill}">{i}</text>')
    o.append(f'<text x="{W / 2}" y="20" font-size="14" fill="{c["foreground"]}" text-anchor="middle">Monday 09:00</text>')
    o.append(f'<text x="{W - 14}" y="20" font-size="14" fill="{c["foreground"]}" text-anchor="end">\U000f0a4d  \U000f05a9  \U000f0079  \U000f0425</text>')

    def window(x, y, w, h, active):
        stroke = c["accent"] if active else c["selection"]
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c["background"]}" fill-opacity="0.97" '
                f'stroke="{stroke}" stroke-width="2"/>')

    # Editor on the right half, so the wallpaper's "hello." stays visible on the left.
    ex, ey, ew = W // 2 + gap // 2, bar + gap, W // 2 - gap - gap // 2
    eh = 560
    o.append(window(ex, ey, ew, eh, True))
    for n, line in enumerate(CODE):
        y = ey + 34 + n * 28
        o.append(f'<text x="{ex + 14}" y="{y}" font-size="16" fill="{c["muted"]}">{n + 1:>3}</text>')
        tspans = "".join(f'<tspan fill="{colour[k]}">{escape(t)}</tspan>' for k, t in line)
        o.append(f'<text x="{ex + 64}" y="{y}" font-size="16" xml:space="preserve">{tspans}</text>')
    sy = ey + eh - 30
    o.append(f'<rect x="{ex + 2}" y="{sy}" width="{ew - 4}" height="28" fill="{c["dark_background"]}"/>')
    o.append(f'<rect x="{ex + 2}" y="{sy}" width="92" height="28" fill="{c["accent"]}"/>')
    o.append(f'<text x="{ex + 16}" y="{sy + 19}" font-size="14" font-weight="bold" fill="{c["background"]}">NORMAL</text>')
    o.append(f'<text x="{ex + 110}" y="{sy + 19}" font-size="14" fill="{c["foreground"]}">typeset.py</text>')

    ty, th = ey + eh + gap, H - (ey + eh + gap) - gap
    o.append(window(ex, ty, ew, th, False))
    term = [
        [(c["accent"], "~/type "), (c["green"], "❯ "), (c["foreground"], "python typeset.py")],
        [(c["dark_foreground"], "0.0  hello.")],
        [(c["dark_foreground"], "24.0  welcome to omarchy")],
        [(c["accent"], "~/type "), (c["green"], "❯ "), (c["foreground"], "git commit -m "), (c["green"], '"set the page"')],
        [(c["foreground"], "[main 1a2b3c4] set the page")],
        [(c["accent"], "~/type "), (c["green"], "❯ "), (c["foreground"], "█")],
    ]
    for n, line in enumerate(term):
        tspans = "".join(f'<tspan fill="{col}">{escape(t)}</tspan>' for col, t in line)
        o.append(f'<text x="{ex + 16}" y="{ty + 34 + n * 30}" font-size="16" xml:space="preserve">{tspans}</text>')
    o.append("</svg>")
    out = os.path.join(theme, "preview.png")
    render("".join(o), out, W)
    return out


def main(theme):
    with open(os.path.join(theme, "colors.toml"), "rb") as f:
        c = tomllib.load(f)
    for path in (unlock(theme, c), screensaver(theme), preview_unlock(theme, c), preview(theme, c)):
        print(path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
