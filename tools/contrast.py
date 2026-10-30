#!/usr/bin/env python3
"""Check a theme's colors.toml against WCAG contrast targets.

Usage: tools/contrast.py themes/<slug>/colors.toml
Exits non-zero when any pair falls below its target.
"""
import sys
import tomllib

# (foreground key, background key, minimum ratio)
TEXT = 4.5
UI = 3.0
PAIRS = [
    *[(k, "background", TEXT) for k in (
        "foreground", "dark_foreground", "light_foreground", "bright_foreground", "accent",
        "red", "yellow", "orange", "green", "cyan", "blue", "magenta",
        "bright_red", "bright_yellow", "bright_green", "bright_cyan", "bright_blue", "bright_magenta")],
    *[(k, "lighter_background", TEXT) for k in ("foreground", "accent", "green", "yellow")],
    ("foreground", "selection", TEXT),
    ("muted", "background", UI),
    ("brown", "background", UI),
]


def luminance(hex_colour):
    h = hex_colour.lstrip("#")
    channels = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def ratio(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def hue(hex_colour):
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    mx, mn = max(r, g, b), min(r, g, b)
    if mx == mn:
        return 0.0
    d = mx - mn
    if mx == r:
        return (60 * ((g - b) / d)) % 360
    if mx == g:
        return 60 * ((b - r) / d) + 120
    return 60 * ((r - g) / d) + 240


def main(path):
    with open(path, "rb") as f:
        colours = tomllib.load(f)
    failed = 0
    for fg, bg, target in PAIRS:
        if fg not in colours or bg not in colours:
            continue
        r = ratio(colours[fg], colours[bg])
        ok = r >= target
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {fg:18} on {bg:18} {r:5.2f} (>= {target})")
    # Yellow, green and orange must stay apart by hue, not just brightness.
    for a, b in (("yellow", "green"), ("orange", "yellow"), ("red", "orange")):
        if a in colours and b in colours:
            gap = abs(hue(colours[a]) - hue(colours[b]))
            gap = min(gap, 360 - gap)
            ok = gap >= 20
            failed += not ok
            print(f"{'ok  ' if ok else 'FAIL'} hue gap {a}/{b} {gap:5.1f} deg (>= 20)")
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
