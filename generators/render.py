#!/usr/bin/env python3
"""Render a theme's wallpapers and intro videos.

Usage:
  generators/render.py wallpapers <theme> <out_dir> [--width 3840] [--only NAME]
  generators/render.py intros     <theme> <out_dir> [--only NAME]

Needs: rsvg-convert (librsvg), ffmpeg. <theme> is a module in generators/
(for example halloween_night) that exposes SCENES and svg().
"""
import argparse
import importlib
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor

H = 2160
INTRO_W, INTRO_H, FPS, SECONDS = 2560, 1440, 30, 6


def rsvg(svg_text, out_png, width):
    # Written next to the output so relative hrefs (the intro's static.png) resolve.
    out_png = os.path.abspath(out_png)
    src = out_png + ".svg"
    with open(src, "w") as f:
        f.write(svg_text)
    try:
        subprocess.run(["rsvg-convert", "-w", str(width), "-o", out_png, src], check=True)
    finally:
        os.unlink(src)


def selected(mod, only):
    scenes = [(n, f) for n, f in mod.SCENES if not only or n == only]
    if not scenes:
        sys.exit(f"no scene named {only}")
    return scenes


def wallpapers(mod, out_dir, width, only):
    os.makedirs(out_dir, exist_ok=True)
    W = width  # 3840 for 16:9, 5120 for 21:9 ultrawide; height stays 2160
    for name, scene in selected(mod, only):
        static, anim = scene(W, H, 1.0)
        out = os.path.join(out_dir, f"{name}.png")
        rsvg(mod.svg(W, H, static + anim), out, width)
        print(out)


def _frame(args):
    theme, name, i, frames, tmp = args
    mod = importlib.import_module(theme)
    scene = dict(mod.SCENES)[name]
    t = i / (frames - 1)
    _, anim = scene(3840, H, t)
    body = f'<image x="0" y="0" width="3840" height="{H}" href="static.png"/>' + anim
    rsvg(mod.svg(3840, H, body), os.path.join(tmp, f"f{i:04d}.png"), INTRO_W)


def intros(theme, mod, out_dir, only):
    os.makedirs(out_dir, exist_ok=True)
    frames = FPS * SECONDS
    for name, scene in selected(mod, only):
        tmp = tempfile.mkdtemp(prefix="intro-")
        try:
            static, _ = scene(3840, H, 0.0)
            rsvg(mod.svg(3840, H, static), os.path.join(tmp, "static.png"), INTRO_W)
            # Blur filters at 2560px use ~1 GB each; more workers get OOM-killed.
            with ProcessPoolExecutor(max_workers=3) as pool:
                list(pool.map(_frame, [(theme, name, i, frames, tmp) for i in range(frames)]))
            out = os.path.join(out_dir, f"{name}.mp4")
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS),
                            "-i", os.path.join(tmp, "f%04d.png"), "-c:v", "libx264", "-preset", "slow",
                            "-crf", "24", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", out],
                           check=True)
            print(out)
        finally:
            shutil.rmtree(tmp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=("wallpapers", "intros"))
    ap.add_argument("theme")
    ap.add_argument("out_dir")
    ap.add_argument("--width", type=int, default=3840)
    ap.add_argument("--only")
    a = ap.parse_args()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    mod = importlib.import_module(a.theme)
    if a.kind == "wallpapers":
        wallpapers(mod, a.out_dir, a.width, a.only)
    else:
        intros(a.theme, mod, a.out_dir, a.only)


if __name__ == "__main__":
    main()
