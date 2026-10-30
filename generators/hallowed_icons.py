#!/usr/bin/env python3
"""Hallowed Night icon overlay: pumpkin folders, a cauldron bin, a bat terminal.

Usage: generators/hallowed_icons.py <out_dir>
Writes a freedesktop icon theme that inherits Yaru-dark for everything else.
"""
import os
import sys

NAME = "Hallowed-Night-Icons"
INK = "#2a1838"
GLOW = "#ffd36b"
TOXIC = "#9be564"

DEFS = """<defs>
<linearGradient id="body" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffa448"/><stop offset="1" stop-color="#e2600c"/></linearGradient>
<linearGradient id="back" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c4500c"/><stop offset="1" stop-color="#8f3a08"/></linearGradient>
<linearGradient id="pot" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3b2752"/><stop offset="1" stop-color="#140e1c"/></linearGradient>
<linearGradient id="screen" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#221830"/><stop offset="1" stop-color="#0a0710"/></linearGradient>
<filter id="g" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="1.6" result="b"/>
<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>"""


def svg(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">{DEFS}{body}</svg>\n'


def folder(emblem="", lit=False):
    shape = ('<path d="M10,26 q0,-6 6,-6 h30 l10,10 h56 q6,0 6,6 v66 q0,6 -6,6 H16 q-6,0 -6,-6 Z" fill="url(#back)"/>'
             '<path d="M8,44 q0,-6 6,-6 h100 q6,0 6,6 v58 q0,8 -8,8 H16 q-8,0 -8,-8 Z" fill="url(#body)"/>'
             '<path d="M8,44 q0,-6 6,-6 h100 q6,0 6,6 v4 H8 Z" fill="#ffc07a" opacity="0.5"/>')
    if lit:  # plain folder: a carved jack-o'-lantern face
        emblem = (f'<g fill="{GLOW}" filter="url(#g)"><path d="M38,66 l10,-12 l10,12 z M70,66 l10,-12 l10,12 z"/>'
                  f'<path d="M36,80 Q64,104 92,80 Q64,90 36,80 Z"/></g>')
    return svg(shape + emblem)


def ink(d, extra=""):
    return f'<path d="{d}" fill="{INK}" {extra}/>'


EMBLEMS = {
    "user-home": ink("M64,56 l22,18 h-6 v18 h-10 v-12 h-12 v12 h-10 v-18 h-6 Z M78,58 h5 v9 l-5,-4 Z"),
    "user-desktop": ink("M42,58 h44 q3,0 3,3 v24 q0,3 -3,3 h-17 v6 h8 v4 h-26 v-4 h8 v-6 h-17 q-3,0 -3,-3 v-24 q0,-3 3,-3 Z M46,62 v22 h36 v-22 Z"),
    "folder-documents": ink("M50,54 h20 l10,10 v32 h-30 Z M70,54 v10 h10 M55,72 h20 v3 h-20 Z M55,80 h20 v3 h-20 Z M55,88 h14 v3 h-14 Z", 'fill-rule="evenodd"'),
    "folder-download": ink("M58,54 h12 v20 h10 l-16,18 l-16,-18 h10 Z M46,94 h36 v5 h-36 Z"),
    "folder-music": ink("M58,58 l24,-6 v34 a8,7 0 1 1 -5,-6 v-18 l-14,4 v24 a8,7 0 1 1 -5,-6 Z"),
    "folder-pictures": ink("M44,96 l14,-20 l10,12 l6,-8 l12,16 Z") + f'<circle cx="78" cy="64" r="8" fill="{GLOW}"/>',
    "folder-videos": ink("M44,64 h40 v32 h-40 Z M44,56 l38,-6 l2,6 l-38,6 Z M56,72 l14,8 l-14,8 Z", 'fill-rule="evenodd"'),
    "folder-templates": ink("M48,56 h32 v40 h-32 Z M52,62 h24 v4 h-24 Z M52,70 h24 v4 h-24 Z M52,78 h16 v4 h-16 Z", 'fill-rule="evenodd"'),
    "folder-publicshare": ink("M50,76 a6,6 0 1 0 0.1,0 Z M78,60 a6,6 0 1 0 0.1,0 Z M78,92 a6,6 0 1 0 0.1,0 Z") +
        f'<path d="M50,76 L78,60 M50,76 L78,92" stroke="{INK}" stroke-width="4"/>',
    "folder-remote": ink("M64,54 a20,20 0 1 0 0.1,0 Z M64,58 a16,16 0 1 1 -0.1,0 Z M48,74 h32 v3 h-32 Z M63,56 h3 v36 h-3 Z", 'fill-rule="evenodd"'),
}


def cauldron(full):
    bubbles = ""
    if full:
        bubbles = (f'<ellipse cx="64" cy="46" rx="40" ry="9" fill="{TOXIC}" filter="url(#g)"/>'
                   f'<g fill="none" stroke="{TOXIC}" stroke-width="3"><circle cx="52" cy="32" r="6"/>'
                   f'<circle cx="72" cy="24" r="4"/><circle cx="80" cy="36" r="5"/></g>')
    return svg(
        '<path d="M34,104 l-8,14 M94,104 l8,14" stroke="#140e1c" stroke-width="7" stroke-linecap="round"/>'
        '<path d="M22,50 C16,96 40,112 64,112 C88,112 112,96 106,50 Z" fill="url(#pot)" stroke="#3b2752" stroke-width="2"/>'
        f'<ellipse cx="64" cy="50" rx="46" ry="10" fill="#0a0710" stroke="#5d4b72" stroke-width="4"/>{bubbles}'
        '<path d="M40,74 q8,-6 16,0" stroke="#ff7a1a" stroke-width="3" fill="none" opacity="0.7"/>')


def terminal():
    return svg(
        '<rect x="8" y="16" width="112" height="96" rx="12" fill="url(#screen)" stroke="#ff7a1a" stroke-width="3"/>'
        '<rect x="8" y="16" width="112" height="16" rx="12" fill="#3b2752"/><rect x="8" y="26" width="112" height="6" fill="#3b2752"/>'
        '<circle cx="22" cy="24" r="3" fill="#ff5f5f"/><circle cx="32" cy="24" r="3" fill="#ffe05c"/><circle cx="42" cy="24" r="3" fill="#9be564"/>'
        '<path d="M24,56 l16,12 l-16,12" stroke="#ff7a1a" stroke-width="7" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        '<rect x="48" y="76" width="26" height="7" rx="3" fill="#ece3d0"/>'
        '<path d="M92,46 C88,40 80,38 72,42 C76,44 76,48 74,50 C78,48 82,49 84,52 C86,49 88,48 92,49 '
        'C96,48 98,49 100,52 C102,49 106,48 110,50 C108,48 108,44 112,42 C104,38 96,40 92,46 Z" fill="#ff7a1a"/>')


INDEX = f"""[Icon Theme]
Name={NAME}
Comment=Hallowed Night overlay: pumpkin folders, cauldron bin, bat terminal. Everything else comes from Yaru-dark.
Inherits=Yaru-dark,hicolor
Directories=scalable/places,scalable/apps

[scalable/places]
Context=Places
Size=128
MinSize=8
MaxSize=512
Type=Scalable

[scalable/apps]
Context=Applications
Size=128
MinSize=8
MaxSize=512
Type=Scalable
"""


def main(out):
    theme = os.path.join(out, NAME)
    places = os.path.join(theme, "scalable", "places")
    apps = os.path.join(theme, "scalable", "apps")
    os.makedirs(places, exist_ok=True)
    os.makedirs(apps, exist_ok=True)
    files = {os.path.join(places, "folder.svg"): folder(lit=True),
             os.path.join(places, "folder-open.svg"): folder(lit=True),
             os.path.join(places, "user-trash.svg"): cauldron(False),
             os.path.join(places, "user-trash-full.svg"): cauldron(True),
             os.path.join(apps, "utilities-terminal.svg"): terminal(),
             os.path.join(apps, "org.gnome.Terminal.svg"): terminal(),
             os.path.join(theme, "index.theme"): INDEX}
    for name, emblem in EMBLEMS.items():
        files[os.path.join(places, f"{name}.svg")] = folder(emblem)
    for path, text in files.items():
        with open(path, "w") as f:
            f.write(text)
    print(theme)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
