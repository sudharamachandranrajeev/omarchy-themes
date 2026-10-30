#!/usr/bin/env python3
"""Check collection themes before they are committed.

Usage: tools/check.py [themes/<slug> ...]   (default: every theme)
Exits non-zero on any error. Warnings do not fail the check.
"""
import os
import re
import struct
import subprocess
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED = ["colors.toml", "icons.theme", "preview.png", "backgrounds"]
RECOMMENDED = ["unlock.png", "preview-unlock.png", "btop.theme", "shell.lock.toml"]
COLOUR_KEYS = ["accent", "background", "foreground", "selection", "red", "yellow", "orange",
               "green", "cyan", "blue", "magenta"]
# Omarchy 3 files that Omarchy 4 no longer reads; shipping them means the theme is stale.
STALE = ["waybar.css", "walker.css", "hyprlock.conf", "mako.ini", "swayosd.css", "wofi.css"]
IMAGE = re.compile(r"\.(png|jpe?g|webp)$", re.I)


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def icon_theme_ok(name, slug):
    if os.path.isfile(os.path.join(ROOT, "icons", slug, name, "index.theme")):
        return True, "ships with this collection"
    for base in ("/usr/share/icons", os.path.expanduser("~/.local/share/icons")):
        if os.path.isfile(os.path.join(base, name, "index.theme")):
            return True, f"installed in {base}"
    if re.fullmatch(r"Yaru(-[a-z]+)?(-dark)?", name):
        return True, "stock Omarchy Yaru variant (not installed here, so not verified)"
    return False, "not an installed icon theme"


def check(theme_dir):
    slug = os.path.basename(os.path.normpath(theme_dir))
    errors, warnings = [], []
    for name in REQUIRED:
        if not os.path.exists(os.path.join(theme_dir, name)):
            errors.append(f"missing {name}")
    for name in RECOMMENDED:
        if not os.path.exists(os.path.join(theme_dir, name)):
            warnings.append(f"no {name}")
    for name in STALE:
        if os.path.exists(os.path.join(theme_dir, name)):
            errors.append(f"{name} is an Omarchy 3 file; remove it")

    colours = os.path.join(theme_dir, "colors.toml")
    if os.path.isfile(colours):
        try:
            with open(colours, "rb") as f:
                c = tomllib.load(f)
            for key in COLOUR_KEYS:
                if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(c.get(key, ""))):
                    errors.append(f"colors.toml: {key} missing or not #rrggbb")
            result = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "contrast.py"), colours],
                                    capture_output=True, text=True)
            if result.returncode:
                errors += [f"contrast: {line}" for line in result.stdout.splitlines() if line.startswith("FAIL")]
        except tomllib.TOMLDecodeError as e:
            errors.append(f"colors.toml does not parse: {e}")

    icons = os.path.join(theme_dir, "icons.theme")
    if os.path.isfile(icons):
        name = open(icons).read().strip()
        ok, why = icon_theme_ok(name, slug)
        (warnings if ok and "not verified" in why else errors if not ok else []).append(f"icons.theme '{name}': {why}")
        if os.path.isdir(os.path.join(ROOT, "icons", slug, name)):
            errors.append("icons.theme must name a stock icon theme; install.sh switches to the overlay")

    bg = os.path.join(theme_dir, "backgrounds")
    if os.path.isdir(bg):
        images = sorted(f for f in os.listdir(bg) if IMAGE.search(f))
        if not images:
            errors.append("backgrounds/ has no images")
        for f in images:
            size = png_size(os.path.join(bg, f))
            if size and size[0] < 1920:
                warnings.append(f"backgrounds/{f} is only {size[0]}px wide")
        intros = os.path.join(bg, "intros")
        if os.path.isdir(intros):
            stems = {os.path.splitext(f)[0] for f in images}
            for f in os.listdir(intros):
                if os.path.splitext(f)[0] not in stems:
                    errors.append(f"intros/{f} has no matching background")

    art = os.path.join(theme_dir, "screensaver.txt")
    if os.path.isfile(art):
        widest = max((len(line) for line in open(art, encoding="utf-8").read().splitlines()), default=0)
        if widest > 100:
            warnings.append(f"screensaver.txt is {widest} columns wide; small screens will wrap it")

    for root, _, files in os.walk(theme_dir):
        for f in files:
            if os.path.islink(os.path.join(root, f)):
                errors.append(f"{os.path.relpath(os.path.join(root, f), theme_dir)} is a symlink; Omarchy skips it")
    return errors, warnings


def main(paths):
    if not paths:
        paths = sorted(os.path.join(ROOT, "themes", d) for d in os.listdir(os.path.join(ROOT, "themes")))
    failed = False
    for path in paths:
        errors, warnings = check(path)
        print(f"{os.path.basename(os.path.normpath(path))}: {'FAIL' if errors else 'ok'}")
        for e in errors:
            print(f"  error: {e}")
        for w in warnings:
            print(f"  warning: {w}")
        failed |= bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
