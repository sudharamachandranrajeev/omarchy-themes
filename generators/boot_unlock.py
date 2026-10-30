#!/usr/bin/env python3
"""Animated boot unlock screen (Plymouth) with your own text.

Usage: generators/boot_unlock.py <theme_dir> <text> <font> <out_dir>

Writes a complete Plymouth theme called omarchy-themes into <out_dir>:
the text in a candle-lit gradient, slime that drips off the letters, bats
that fly past, and Omarchy's password box and progress bar. Colours come from
<theme_dir>/colors.toml. Needs ImageMagick (magick), rsvg-convert, fontconfig
and an Omarchy install (for the stock password-box images).
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib

OMARCHY = os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "plymouth", "omarchy-themes.script")
INSTALL_DIR = "/usr/share/plymouth/themes/omarchy-themes"
TEXT_OK = re.compile(r"^[\w .,!?'&:+-]{1,32}$")

W = 1100           # canvas width; wide so a long line of text stays tall enough to read
TEXT_MAX_H = 120
DRIP_ROOM = 70     # space under the letters for the drips to hang into
GLOW_PAD = 40
BAT = ("M0,0 C-8,-10 -22,-14 -40,-8 C-32,-4 -30,2 -34,8 C-26,4 -20,6 -16,12 C-12,6 -6,4 0,6 "
       "C6,4 12,6 16,12 C20,6 26,4 34,8 C30,2 32,-4 40,-8 C22,-14 8,-10 0,0 Z")
BAT_HEAD = "M-5,-1 L-4,-8 L-1,-3 L1,-3 L4,-8 L5,-1 Q0,5 -5,-1 Z"


def run(*cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def rsvg(svg_text, out):
    run("rsvg-convert", "-o", out, input=svg_text.encode())


def letters(text, font, tmp):
    """White glyphs on a W x (text + drip room) canvas, plus the alpha bytes to find letter feet."""
    font_file = run("fc-match", "-f", "%{file}", font, capture_output=True, text=True).stdout
    raw, mark = os.path.join(tmp, "raw.png"), os.path.join(tmp, "mark.png")
    # The text was checked against TEXT_OK, so no ImageMagick escapes (@file, %[...]) can reach label:.
    run("magick", "-background", "none", "-fill", "white", "-font", font_file, "-pointsize", "200",
        f"label:{text}", "-trim", "+repage", "-resize", f"{W - 40}x{TEXT_MAX_H}", raw)
    text_h = int(run("magick", "identify", "-format", "%h", raw, capture_output=True, text=True).stdout)
    H = text_h + DRIP_ROOM
    run("magick", raw, "-background", "none", "-gravity", "north", "-extent", f"{W}x{H}", mark)
    alpha = run("magick", mark, "-alpha", "extract", "-depth", "8", "gray:-", capture_output=True).stdout
    return mark, H, text_h, alpha


def feet(alpha, H, text_h):
    """Runs of columns whose lowest ink sits on the baseline: the places slime can drip from."""
    bottom = []
    for x in range(W):
        rows = [y for y in range(H) if alpha[y * W + x] > 128]
        bottom.append(max(rows) if rows else -1)
    found, start = [], 0
    for x in range(1, W + 1):
        if x == W or abs(bottom[x] - bottom[start]) > 2 or bottom[x] < 0:
            if bottom[start] > text_h * 0.8 and x - start >= 6:
                found.append((start, x - 1, bottom[start]))
            start = x
    return found


def main(theme, text, font, out):
    if not TEXT_OK.match(text):
        sys.exit("Text must be 1 to 32 letters, digits, spaces or . , ! ? ' & : + -")
    with open(os.path.join(theme, "colors.toml"), "rb") as f:
        c = tomllib.load(f)
    os.makedirs(out, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        mark, H, text_h, alpha = letters(text, font, tmp)
        found = feet(alpha, H, text_h) or [(W // 2 - 5, W // 2 + 5, text_h)]
        # At most 8 drips, spread along the whole line.
        spots = [found[round(i * (len(found) - 1) / 7)] for i in range(8)] if len(found) > 8 else found
        spots = sorted(set(spots))

        # logo.png: the text in a candle gradient with a slime lip on each dripping foot.
        lips = "".join(f'<ellipse cx="{(a + b) / 2:.0f}" cy="{y}" rx="9" ry="3" fill="{c["green"]}"/>'
                       for a, b, y in spots)
        grad = os.path.join(tmp, "grad.png")
        rsvg(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">'
             f'<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="{text_h}" gradientUnits="userSpaceOnUse">'
             f'<stop offset="0" stop-color="{c["yellow"]}"/><stop offset="1" stop-color="{c["accent"]}"/>'
             f'</linearGradient></defs><rect width="{W}" height="{H}" fill="url(#g)"/></svg>', grad)
        lit = os.path.join(tmp, "lit.png")
        run("magick", grad, mark, "-compose", "CopyOpacity", "-composite", lit)
        lip_png = os.path.join(tmp, "lips.png")
        rsvg(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">{lips}</svg>', lip_png)
        run("magick", lit, lip_png, "-composite", os.path.join(out, "logo.png"))

        # flare.png: a brighter copy laid over the text; its opacity flickers like a candle.
        run("magick", mark, "-fill", c["bright_yellow"], "-colorize", "100", os.path.join(out, "flare.png"))

        # glow.png: a soft halo behind the text, padded so the blur is not clipped.
        run("magick", mark, "-bordercolor", "none", "-border", str(GLOW_PAD), "-fill", c["accent"],
            "-colorize", "100", "-channel", "A", "-blur", "0x14", "-evaluate", "multiply", "1.6",
            "+channel", os.path.join(out, "glow.png"))

    rsvg(f'<svg xmlns="http://www.w3.org/2000/svg" width="8" height="64"><rect width="8" height="64" '
         f'fill="{c["green"]}"/></svg>', os.path.join(out, "stem.png"))
    rsvg(f'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><circle cx="16" cy="16" r="15" '
         f'fill="{c["green"]}"/><circle cx="11" cy="11" r="4" fill="#fff" opacity="0.35"/></svg>',
         os.path.join(out, "drop.png"))
    for name, flap in (("bat-up", 1.0), ("bat-down", -0.6)):
        rsvg(f'<svg xmlns="http://www.w3.org/2000/svg" width="168" height="72" viewBox="-42 -30 84 36">'
             f'<g fill="{c["muted"]}"><path d="{BAT}" transform="scale(1,{flap})"/><path d="{BAT_HEAD}"/></g></svg>',
             os.path.join(out, f"{name}.png"))

    for asset in ("bullet.png", "entry.png", "lock.png", "progress_box.png", "progress_bar.png"):
        shutil.copy(os.path.join(OMARCHY, "default", "plymouth", asset), os.path.join(out, asset))
    for asset in ("bullet.png", "entry.png", "lock.png"):
        path = os.path.join(out, asset)
        run("magick", path, "-channel", "RGB", "+level-colors", f'{c["foreground"]},{c["foreground"]}', path)
    path = os.path.join(out, "progress_bar.png")
    run("magick", path, "-channel", "RGB", "+level-colors", f'{c["accent"]},{c["accent"]}', path)

    # Drip lengths and timings vary per foot so they never fall in step.
    lengths, periods = [26, 44, 18, 36, 52, 22, 40, 30], [3.1, 4.3, 3.7, 5.2, 2.9, 4.7, 3.4, 4.0]
    drips = []
    for i, (a, b, y) in enumerate(spots):
        width = 8 if b - a < 20 else 10
        drips.append(f"drip[{i}].x = {(a + b) / 2 - width / 2:.0f}; drip[{i}].y = {y}; drip[{i}].w = {width}; "
                     f"drip[{i}].len = {min(lengths[i], DRIP_ROOM - 18)}; drip[{i}].period = {periods[i]}; "
                     f"drip[{i}].phase = {(i * 0.37) % 1:.2f};")

    bg = c["background"].lstrip("#")
    r, g, b = (int(bg[i:i + 2], 16) / 255 for i in (0, 2, 4))
    with open(SCRIPT) as f:
        script = f.read()
    script = (script.replace("@BACKGROUND@", f"{r:.3f}, {g:.3f}, {b:.3f}")
              .replace("@GLOW_PAD@", str(GLOW_PAD))
              .replace("@DRIP_COUNT@", str(len(drips)))
              .replace("@DRIPS@", "\n".join(drips)))
    with open(os.path.join(out, "omarchy-themes.script"), "w") as f:
        f.write(script)
    with open(os.path.join(out, "omarchy-themes.plymouth"), "w") as f:
        f.write("[Plymouth Theme]\nName=omarchy-themes\nDescription=Animated boot unlock screen from omarchy-themes.\n"
                f"ModuleName=script\n\n[script]\nImageDir={INSTALL_DIR}\nScriptFile={INSTALL_DIR}/omarchy-themes.script\n"
                f"ConsoleLogBackgroundColor=0x{bg}\n")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
