#!/usr/bin/env python3
"""Animated boot unlock screen (Plymouth) with your own text.

Usage:
  generators/boot_unlock.py build <slug> <out_dir>     write the Plymouth theme
  generators/boot_unlock.py get <slug> text|font       print a setting (your value or the default)
  generators/boot_unlock.py set <slug> text|font <v>   save a setting
  generators/boot_unlock.py get-name | set-name <v>    your name, for {name} and {NAME}
  generators/boot_unlock.py show <slug>                print the text as it will appear

Each theme's look comes from plymouth/<slug>.toml: a style (plymouth/<style>.script,
for example spooky or calm) and a default text and font. Your own text, font and
name live in $XDG_CONFIG_HOME/omarchy-themes/settings.toml and are only ever
drawn on this computer. Colours come from themes/<slug>/colors.toml.

Needs ImageMagick (magick), rsvg-convert, fontconfig and an Omarchy install
(for the stock password-box images).
"""
import json
import os
import pwd
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib

OMARCHY = os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLYMOUTH = os.path.join(ROOT, "plymouth")
INSTALL_DIR = "/usr/share/plymouth/themes/omarchy-themes"
SETTINGS = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"),
                        "omarchy-themes", "settings.toml")
TEXT_OK = re.compile(r"^[\w .,!?'&:+-]{1,32}$")
NAME_OK = re.compile(r"^[\w' -]{1,20}$")
FONT_OK = re.compile(r"^[\w .,:=+-]{1,80}$")
SLUG_OK = re.compile(r"^[a-z0-9][a-z0-9-]*$")

W = 1100           # canvas width; wide so a long line of text stays tall enough to read
TEXT_MAX_H = 120
GLOW_PAD = 40
ROOM = {"spooky": 70, "calm": 40}  # space under the letters: drips hang here, the rule sits here
BAT = ("M0,0 C-8,-10 -22,-14 -40,-8 C-32,-4 -30,2 -34,8 C-26,4 -20,6 -16,12 C-12,6 -6,4 0,6 "
       "C6,4 12,6 16,12 C20,6 26,4 34,8 C30,2 32,-4 40,-8 C22,-14 8,-10 0,0 Z")
BAT_HEAD = "M-5,-1 L-4,-8 L-1,-3 L1,-3 L4,-8 L5,-1 Q0,5 -5,-1 Z"


def run(*cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def rsvg(svg_text, out):
    run("rsvg-convert", "-o", out, input=svg_text.encode())


# ----------------------------------------------------------------- settings


def defaults(slug):
    if not SLUG_OK.match(slug) or not os.path.isfile(os.path.join(PLYMOUTH, f"{slug}.toml")):
        sys.exit(f"No boot screen for a theme called '{slug}'.")
    with open(os.path.join(PLYMOUTH, f"{slug}.toml"), "rb") as f:
        return tomllib.load(f)


def load():
    try:
        with open(SETTINGS, "rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        return {}
    except tomllib.TOMLDecodeError as e:
        sys.exit(f"Could not read {SETTINGS}: {e}")


def save(settings):
    """Rewrite the whole file. Only the keys this tool knows are kept."""
    lines = ["# Settings for omarchy-themes. Change them with ./customise.sh, or edit this file",
             "# and run ./boot-unlock.sh again to rebuild the boot screen.", ""]
    if "name" in settings:
        lines += ["# Your name, for {name} and {NAME} in the boot text.", f"name = {json.dumps(settings['name'])}", ""]
    for slug, values in sorted(settings.get("boot_unlock", {}).items()):
        if isinstance(values, dict):
            lines.append(f"[boot_unlock.{slug}]")
            lines += [f"{key} = {json.dumps(values[key])}" for key in ("text", "font") if key in values]
            lines.append("")
    os.makedirs(os.path.dirname(SETTINGS), exist_ok=True)
    with open(SETTINGS, "w") as f:
        f.write("\n".join(lines))


def account_name():
    """First word of the account's full name, else the login name with a capital."""
    entry = pwd.getpwuid(os.getuid())
    full = entry.pw_gecos.split(",")[0].strip()
    return full.split()[0] if full else entry.pw_name.capitalize()


def get(slug, key):
    values = load().get("boot_unlock", {}).get(slug, {})
    return values.get(key, defaults(slug)[key])


def get_name():
    return load().get("name") or account_name()


def check_text(template):
    # Placeholders are checked as a plain word; the name is checked on its own.
    if not TEXT_OK.match(template.replace("{NAME}", "A").replace("{name}", "A")):
        sys.exit("Text must be 1 to 32 letters, digits, spaces or . , ! ? ' & : + - (plus {name} or {NAME}).")


def set_value(slug, key, value):
    defaults(slug)
    if key == "text":
        check_text(value)
        name = get_name()
        if len(value.replace("{NAME}", name).replace("{name}", name)) > 32:
            sys.exit(f"With your name ({name}) that is over 32 characters. Use a shorter text.")
    elif key == "font":
        if not FONT_OK.match(value):
            sys.exit("That does not look like a font name.")
    else:
        sys.exit("Only text and font can be set.")
    settings = load()
    settings.setdefault("boot_unlock", {}).setdefault(slug, {})[key] = value
    save(settings)


def set_name(value):
    if not NAME_OK.match(value):
        sys.exit("A name is 1 to 20 letters, spaces, hyphens or apostrophes.")
    settings = load()
    settings["name"] = value
    save(settings)


def shown_text(slug):
    template = get(slug, "text")
    check_text(template)
    name = get_name()
    text = template.replace("{NAME}", name.upper()).replace("{name}", name)
    if not TEXT_OK.match(text):
        sys.exit(f"'{text}' is too long: the text and name together must fit in 32 characters.")
    return text


def font_pattern(font):
    """'omarchy' or 'omarchy:bold' means the font Omarchy uses right now."""
    family, _, style = font.partition(":")
    if family == "omarchy":
        family = run("omarchy", "font", "current", capture_output=True, text=True).stdout.strip() or "monospace"
    return f"{family}:{style}" if style else family


# ------------------------------------------------------------------- render


def letters(text, font, room, tmp):
    """White glyphs on a W x (text + room) canvas, plus the alpha bytes to find letter feet."""
    font_file = run("fc-match", "-f", "%{file}", font_pattern(font), capture_output=True, text=True).stdout
    raw, mark = os.path.join(tmp, "raw.png"), os.path.join(tmp, "mark.png")
    # The text was checked against TEXT_OK, so no ImageMagick escapes (@file, %[...]) can reach label:.
    run("magick", "-background", "none", "-fill", "white", "-font", font_file, "-pointsize", "200",
        f"label:{text}", "-trim", "+repage", "-resize", f"{W - 40}x{TEXT_MAX_H}", raw)
    text_w, text_h = map(int, run("magick", "identify", "-format", "%w %h", raw,
                                  capture_output=True, text=True).stdout.split())
    H = text_h + room
    run("magick", raw, "-background", "none", "-gravity", "north", "-extent", f"{W}x{H}", mark)
    alpha = run("magick", mark, "-alpha", "extract", "-depth", "8", "gray:-", capture_output=True).stdout
    return mark, H, text_w, text_h, alpha


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


def glow(mark, colour, blur, out):
    """A soft halo from the glyphs, padded so the blur is not clipped."""
    run("magick", mark, "-bordercolor", "none", "-border", str(GLOW_PAD), "-fill", colour,
        "-colorize", "100", "-channel", "A", "-blur", f"0x{blur}", "-evaluate", "multiply", "1.6",
        "+channel", out)


def spooky(c, mark, H, text_w, text_h, alpha, out, tmp):
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
    glow(mark, c["accent"], 14, os.path.join(out, "glow.png"))

    rsvg(f'<svg xmlns="http://www.w3.org/2000/svg" width="8" height="64"><rect width="8" height="64" '
         f'fill="{c["green"]}"/></svg>', os.path.join(out, "stem.png"))
    rsvg(f'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><circle cx="16" cy="16" r="15" '
         f'fill="{c["green"]}"/><circle cx="11" cy="11" r="4" fill="#fff" opacity="0.35"/></svg>',
         os.path.join(out, "drop.png"))
    for name, flap in (("bat-up", 1.0), ("bat-down", -0.6)):
        rsvg(f'<svg xmlns="http://www.w3.org/2000/svg" width="168" height="72" viewBox="-42 -30 84 36">'
             f'<g fill="{c["muted"]}"><path d="{BAT}" transform="scale(1,{flap})"/><path d="{BAT_HEAD}"/></g></svg>',
             os.path.join(out, f"{name}.png"))

    # Drip lengths and timings vary per foot so they never fall in step.
    lengths, periods = [26, 44, 18, 36, 52, 22, 40, 30], [3.1, 4.3, 3.7, 5.2, 2.9, 4.7, 3.4, 4.0]
    drips = []
    for i, (a, b, y) in enumerate(spots):
        width = 8 if b - a < 20 else 10
        drips.append(f"drip[{i}].x = {(a + b) / 2 - width / 2:.0f}; drip[{i}].y = {y}; drip[{i}].w = {width}; "
                     f"drip[{i}].len = {min(lengths[i], ROOM['spooky'] - 18)}; drip[{i}].period = {periods[i]}; "
                     f"drip[{i}].phase = {(i * 0.37) % 1:.2f};")
    return {"@DRIP_COUNT@": str(len(drips)), "@DRIPS@": "\n".join(drips)}


def calm(c, mark, H, text_w, text_h, alpha, out, tmp):
    # logo.png: the text in the theme's brightest text colour, nothing else.
    run("magick", mark, "-fill", c["bright_foreground"], "-colorize", "100", os.path.join(out, "logo.png"))
    glow(mark, c["accent"], 22, os.path.join(out, "glow.png"))
    rule_w = min(W, text_w + 40)
    rsvg(f'<svg xmlns="http://www.w3.org/2000/svg" width="{rule_w}" height="3"><rect width="{rule_w}" height="3" '
         f'fill="{c["accent"]}"/></svg>', os.path.join(out, "rule.png"))
    cursor_w, cursor_h = max(8, text_h // 3), int(text_h * 0.9)
    rsvg(f'<svg xmlns="http://www.w3.org/2000/svg" width="{cursor_w}" height="{cursor_h}"><rect width="{cursor_w}" '
         f'height="{cursor_h}" fill="{c["accent"]}"/></svg>', os.path.join(out, "cursor.png"))
    return {"@RULE_Y@": str(text_h + 22), "@CURSOR_X@": str((W + text_w) // 2 + max(10, text_h // 6)),
            "@CURSOR_Y@": str(text_h - cursor_h)}


STYLES = {"spooky": spooky, "calm": calm}


def build(slug, out):
    style = defaults(slug)["style"]
    with open(os.path.join(PLYMOUTH, f"{style}.script")) as f:
        style_script = f.read()
    with open(os.path.join(PLYMOUTH, "common.script")) as f:
        script = f.read().replace("@STYLE@", style_script)
    with open(os.path.join(ROOT, "themes", slug, "colors.toml"), "rb") as f:
        c = tomllib.load(f)
    text = shown_text(slug)
    os.makedirs(out, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        mark, H, text_w, text_h, alpha = letters(text, get(slug, "font"), ROOM[style], tmp)
        values = STYLES[style](c, mark, H, text_w, text_h, alpha, out, tmp)

    for asset in ("bullet.png", "entry.png", "lock.png", "progress_box.png", "progress_bar.png"):
        shutil.copy(os.path.join(OMARCHY, "default", "plymouth", asset), os.path.join(out, asset))
    for asset in ("bullet.png", "entry.png", "lock.png"):
        path = os.path.join(out, asset)
        run("magick", path, "-channel", "RGB", "+level-colors", f'{c["foreground"]},{c["foreground"]}', path)
    path = os.path.join(out, "progress_bar.png")
    run("magick", path, "-channel", "RGB", "+level-colors", f'{c["accent"]},{c["accent"]}', path)

    bg = c["background"].lstrip("#")
    r, g, b = (int(bg[i:i + 2], 16) / 255 for i in (0, 2, 4))
    values.update({"@BACKGROUND@": f"{r:.3f}, {g:.3f}, {b:.3f}", "@GLOW_PAD@": str(GLOW_PAD)})
    for key, value in values.items():
        script = script.replace(key, value)
    with open(os.path.join(out, "omarchy-themes.script"), "w") as f:
        f.write(script)
    with open(os.path.join(out, "omarchy-themes.plymouth"), "w") as f:
        f.write("[Plymouth Theme]\nName=omarchy-themes\nDescription=Animated boot unlock screen from omarchy-themes.\n"
                f"ModuleName=script\n\n[script]\nImageDir={INSTALL_DIR}\nScriptFile={INSTALL_DIR}/omarchy-themes.script\n"
                f"ConsoleLogBackgroundColor=0x{bg}\n")
    print(text)


def main(args):
    match args:
        case ["build", slug, out]:
            build(slug, out)
        case ["get", slug, ("text" | "font") as key]:
            print(get(slug, key))
        case ["set", slug, key, value]:
            set_value(slug, key, value)
        case ["get-name"]:
            print(get_name())
        case ["set-name", value]:
            set_name(value)
        case ["show", slug]:
            print(shown_text(slug))
        case _:
            sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
