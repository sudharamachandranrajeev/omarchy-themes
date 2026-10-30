"""Halloween Night artwork: eight procedural Halloween scenes as SVG.

Every scene is a function scene(W, H, t) -> (static_svg_body, animated_svg_body).
t runs 0..1 over the intro video; t = 1 is the still wallpaper, so the intro
always settles exactly on the wallpaper. The static body never depends on t,
which lets the renderer rasterise it once and draw only the animated layer per
frame. All randomness is seeded, so output is reproducible.
"""
import math
import random

P = {
    "night": "#07050d", "dusk": "#160d24", "horizon": "#2b1640", "ember": "#ff7a1a",
    "moon_hi": "#fff6dc", "moon_lo": "#f0c97a", "crater": "#d9ad62",
    "far": "#1d112a", "mid": "#130b1d", "near": "#07050b",
    "pumpkin_hi": "#ff9b3d", "pumpkin_lo": "#9a3c08", "pumpkin_rim": "#5e2405",
    "glow": "#ffd36b", "fog": "#cbbbe8", "star": "#ece3d0", "toxic": "#9be564",
    "violet": "#b44dff", "window": "#ffcf6b", "bone": "#ece3d0",
}

DEFS = f"""<defs>
<radialGradient id="moon" cx="0.4" cy="0.38" r="0.75"><stop offset="0" stop-color="{P['moon_hi']}"/>
 <stop offset="1" stop-color="{P['moon_lo']}"/></radialGradient>
<radialGradient id="moonGlow"><stop offset="0.25" stop-color="#ffe9b0" stop-opacity="0.42"/>
 <stop offset="1" stop-color="#ffe9b0" stop-opacity="0"/></radialGradient>
<radialGradient id="pumpkin" cx="0.38" cy="0.32" r="0.85"><stop offset="0" stop-color="{P['pumpkin_hi']}"/>
 <stop offset="1" stop-color="{P['pumpkin_lo']}"/></radialGradient>
<radialGradient id="lanternGlow"><stop offset="0" stop-color="{P['glow']}" stop-opacity="0.55"/>
 <stop offset="1" stop-color="{P['ember']}" stop-opacity="0"/></radialGradient>
<radialGradient id="toxicGlow"><stop offset="0" stop-color="{P['toxic']}" stop-opacity="0.6"/>
 <stop offset="1" stop-color="{P['toxic']}" stop-opacity="0"/></radialGradient>
<radialGradient id="windowGlow"><stop offset="0" stop-color="{P['window']}" stop-opacity="0.5"/>
 <stop offset="1" stop-color="{P['window']}" stop-opacity="0"/></radialGradient>
<filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="40"/></filter>
<filter id="cloud" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="26"/></filter>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6" result="b"/>
 <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>"""


def ease_out(x):
    return 1 - (1 - x) ** 3


def sky(W, H, top, mid, low, haze_y=1.0, haze_opacity=0.32, haze=P["ember"]):
    return (f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{top}"/>'
            f'<stop offset="0.55" stop-color="{mid}"/><stop offset="1" stop-color="{low}"/></linearGradient>'
            f'<radialGradient id="haze" cx="0.5" cy="{haze_y}" r="0.75"><stop offset="0" stop-color="{haze}" stop-opacity="{haze_opacity}"/>'
            f'<stop offset="1" stop-color="{haze}" stop-opacity="0"/></radialGradient>'
            f'<rect width="{W}" height="{H}" fill="url(#sky)"/><rect width="{W}" height="{H}" fill="url(#haze)"/>')


def stars(rnd, W, ymax, n=380):
    out = []
    for _ in range(n):
        out.append(f'<circle cx="{rnd.uniform(0, W):.0f}" cy="{rnd.uniform(0, ymax):.0f}" '
                   f'r="{rnd.uniform(0.8, 3.0):.1f}" fill="{P["star"]}" opacity="{rnd.uniform(0.15, 0.85):.2f}"/>')
    return "".join(out)


def moon(cx, cy, r, rnd, glow=2.4):
    out = [f'<circle cx="{cx}" cy="{cy}" r="{r * glow:.0f}" fill="url(#moonGlow)"/>',
           f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#moon)"/>']
    for _ in range(13):
        a, d = rnd.uniform(0, math.tau), rnd.uniform(0, r * 0.75)
        out.append(f'<circle cx="{cx + math.cos(a) * d:.0f}" cy="{cy + math.sin(a) * d:.0f}" '
                   f'r="{rnd.uniform(r * 0.03, r * 0.13):.0f}" fill="{P["crater"]}" opacity="0.26"/>')
    return "".join(out)


def cloud(cx, cy, w, rnd, colour="#231436", opacity=0.85):
    puffs = []
    for _ in range(9):
        puffs.append(f'<ellipse cx="{cx + rnd.uniform(-w / 2, w / 2):.0f}" cy="{cy + rnd.uniform(-w * 0.04, w * 0.04):.0f}" '
                     f'rx="{rnd.uniform(w * 0.12, w * 0.24):.0f}" ry="{rnd.uniform(w * 0.035, w * 0.07):.0f}"/>')
    return f'<g fill="{colour}" opacity="{opacity}" filter="url(#cloud)">{"".join(puffs)}</g>'


def hills(W, H, colour, base, amp, freq, phase):
    pts = [f"M0,{H}"]
    for x in range(0, W + 80, 80):
        y = base - amp * (math.sin(x * freq + phase) * 0.6 + math.sin(x * freq * 2.7 + phase * 1.3) * 0.4)
        pts.append(f"L{x},{y:.0f}")
    pts.append(f"L{W},{H} Z")
    return f'<path d="{" ".join(pts)}" fill="{colour}"/>'


def grass(W, H, base, rnd, colour=P["near"]):
    pts = [f"M0,{H}", f"L0,{base}"]
    x = 0
    while x < W:
        h = rnd.uniform(10, 46)
        pts.append(f"L{x + 9:.0f},{base - h:.0f} L{x + 18:.0f},{base:.0f}")
        x += rnd.uniform(14, 30)
    pts.append(f"L{W},{H} Z")
    return f'<path d="{" ".join(pts)}" fill="{colour}"/>'


def tree(x, y, size, rnd, colour=P["near"], lean=-0.08, depth=9):
    out = []

    def branch(x0, y0, ang, length, width, d):
        if d == 0 or length < 10:
            return
        x1, y1 = x0 + math.cos(ang) * length, y0 + math.sin(ang) * length
        cx = (x0 + x1) / 2 + rnd.uniform(-length, length) * 0.2
        cy = (y0 + y1) / 2 + rnd.uniform(-length, length) * 0.2
        out.append(f'<path d="M{x0:.0f},{y0:.0f} Q{cx:.0f},{cy:.0f} {x1:.0f},{y1:.0f}" '
                   f'stroke-width="{width:.1f}"/>')
        for _ in range(rnd.choice((2, 2, 3))):
            branch(x1, y1, ang + rnd.uniform(-0.8, 0.8), length * rnd.uniform(0.6, 0.78), width * 0.64, d - 1)

    branch(x, y, -math.pi / 2 + lean, size, size * 0.2, depth)
    roots = "".join(f'<path d="M{x:.0f},{y - 30:.0f} Q{x + s * 60:.0f},{y - 5:.0f} {x + s * 150:.0f},{y + 20:.0f}" '
                    f'stroke-width="{size * 0.05:.0f}"/>' for s in (-1, 1, -0.6, 0.7))
    return (f'<g stroke="{colour}" stroke-linecap="round" fill="none">{roots}{"".join(out)}</g>')


def tombstone(x, y, h, tilt, colour=P["mid"], edge="#2c1a3c", cross=False):
    if cross:
        d = f"M{x + 38},{y} v-{h} h-30 v-36 h30 v-30 h24 v30 h30 v36 h-30 v{h} z"
    else:
        d = f"M{x},{y} v-{h} a50,50 0 0 1 100,0 v{h} z"
    return f'<path d="{d}" fill="{colour}" stroke="{edge}" stroke-width="3" transform="rotate({tilt:.1f} {x} {y})"/>'


def pumpkin(x, y, s, seed, flicker=0.0, lit=True):
    r = random.Random(seed)
    g = [f'<g transform="translate({x:.0f},{y:.0f}) scale({s:.2f})">',
         '<ellipse cx="0" cy="66" rx="150" ry="18" fill="#000" opacity="0.55"/>']
    for dx, rx in ((-58, 66), (58, 66), (-28, 72), (28, 72), (0, 76)):
        g.append(f'<ellipse cx="{dx}" cy="0" rx="{rx}" ry="68" fill="url(#pumpkin)" stroke="{P["pumpkin_rim"]}" stroke-width="3"/>')
    g.append('<path d="M-6,-62 q2,-28 20,-36 l8,9 q-14,8 -14,27 z" fill="#2f2410"/>')
    if lit:
        eyes = r.choice(("M-52,-16 l22,-28 l22,28 z M8,-16 l22,-28 l22,28 z",
                         "M-50,-14 q20,-34 40,0 z M10,-14 q20,-34 40,0 z",
                         "M-50,-30 l40,10 l-30,12 z M50,-30 l-40,10 l30,12 z"))
        g.append(f'<path d="{eyes}" fill="{P["glow"]}" filter="url(#glow)"/>')
        g.append(f'<path d="M-58,12 Q0,66 58,12 Q0,32 -58,12 Z" fill="{P["glow"]}" filter="url(#glow)"/>')
        for i in range(r.randint(2, 3)):
            tx = -34 + i * 34
            g.append(f'<rect x="{tx - 8}" y="16" width="16" height="13" fill="url(#pumpkin)"/>')
    g.append('</g>')
    return "".join(g)


def lantern_glow(x, y, s, flicker=0.0):
    op = 0.75 + flicker
    return (f'<ellipse cx="{x:.0f}" cy="{y + 10 * s:.0f}" rx="{230 * s:.0f}" ry="{150 * s:.0f}" '
            f'fill="url(#lanternGlow)" opacity="{max(0.0, min(1.0, op)):.2f}"/>')


def bat(x, y, s, rot=0.0, flap=1.0, colour=P["near"]):
    wings = ("M0,0 C-8,-10 -22,-14 -40,-8 C-32,-4 -30,2 -34,8 C-26,4 -20,6 -16,12 "
             "C-12,6 -6,4 0,6 C6,4 12,6 16,12 C20,6 26,4 34,8 C30,2 32,-4 40,-8 C22,-14 8,-10 0,0 Z")
    head = "M-5,-1 L-4,-8 L-1,-3 L1,-3 L4,-8 L5,-1 Q0,5 -5,-1 Z"
    return (f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.0f}) scale({s:.2f})" fill="{colour}">'
            f'<path d="{wings}" transform="scale(1,{flap:.2f})"/><path d="{head}"/></g>')


def bat_flock(rnd, n, region, t, scale=(1.0, 2.6), entry="left", colour=P["near"]):
    """Bats fly in from off-canvas and settle on their wallpaper positions at t=1."""
    x0, y0, x1, y1 = region
    out = []
    for i in range(n):
        fx, fy = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        s, rot = rnd.uniform(*scale), rnd.uniform(-20, 20)
        delay = rnd.uniform(0, 0.35)
        phase = rnd.uniform(0, math.tau)
        k = ease_out(max(0.0, min(1.0, (t - delay) / (1 - delay))))
        sx = -400 if entry == "left" else x1 + 1600
        sy = fy + rnd.uniform(300, 900)
        x = sx + (fx - sx) * k
        y = sy + (fy - sy) * k + math.sin(t * 18 + phase) * 60 * (1 - k)
        flap = 1.0 if k >= 1 else 0.55 + 0.45 * abs(math.cos(t * 40 + phase))
        out.append(bat(x, y, s, rot * k, flap, colour))
    return "".join(out)


def fog(rnd, W, y0, y1, t, n=5, opacity=0.1, colour=P["fog"], drift=700):
    out = []
    for i in range(n):
        dx = (1 - ease_out(t)) * drift * (1 if i % 2 else -1)
        out.append(f'<ellipse cx="{rnd.uniform(0, W) + dx:.0f}" cy="{rnd.uniform(y0, y1):.0f}" '
                   f'rx="{rnd.uniform(W * 0.18, W * 0.36):.0f}" ry="{rnd.uniform(60, 130):.0f}" '
                   f'fill="{colour}" opacity="{opacity}" filter="url(#soft)"/>')
    return "".join(out)


def flicker(rnd, t):
    """Lantern flicker that fades out so the last frame matches the wallpaper."""
    return (math.sin(t * 47 + rnd.uniform(0, 9)) * 0.5 + math.sin(t * 113) * 0.3) * 0.35 * (1 - ease_out(t))


def house(x, y, s, lit_seed):
    r = random.Random(lit_seed)
    c = P["near"]
    body = (f"M0,0 V-420 L-40,-420 L160,-640 L360,-420 L320,-420 V0 Z "
            f"M300,-420 V-560 L360,-660 L420,-560 V-300 L320,-300 Z "
            f"M-40,-200 V-330 L-120,-330 L-20,-430 L60,-330 V-200 Z "
            f"M250,-600 h30 v-90 h-30 Z")
    out = [f'<g transform="translate({x:.0f},{y:.0f}) scale({s:.2f})">', f'<path d="{body}" fill="{c}"/>']
    windows = [(40, -360), (220, -360), (40, -200), (220, -200), (130, -520), (345, -520), (-60, -300)]
    for wx, wy in windows:
        if r.random() < 0.7:
            out.append(f'<circle cx="{wx + 24}" cy="{wy + 30}" r="110" fill="url(#windowGlow)"/>')
            out.append(f'<rect x="{wx}" y="{wy}" width="48" height="66" rx="4" fill="{P["window"]}"/>'
                       f'<path d="M{wx + 24},{wy} v66 M{wx},{wy + 33} h48" stroke="{c}" stroke-width="6"/>')
    out.append(f'<rect x="135" y="-120" width="60" height="120" rx="30" fill="#140a06"/></g>')
    return "".join(out)


def fence(W, y, rnd, colour=P["near"]):
    out = [f'<rect x="0" y="{y - 70}" width="{W}" height="10" fill="{colour}"/>',
           f'<rect x="0" y="{y - 140}" width="{W}" height="10" fill="{colour}"/>']
    x = 0
    while x < W:
        h = rnd.uniform(170, 210)
        out.append(f'<path d="M{x},{y} v-{h:.0f} l9,-24 l9,24 v{h:.0f} z" fill="{colour}" '
                   f'transform="rotate({rnd.uniform(-4, 4):.1f} {x} {y})"/>')
        x += 56
    return "".join(out)


def witch(x, y, s, wind=0.0):
    """Witch on a broom, facing right. wind (0..1) ripples the cloak while flying."""
    w = wind * 30
    parts = [
        # broom handle and bristles
        '<path d="M-310,6 L270,-24" stroke-width="16" stroke-linecap="round" fill="none" stroke="currentColor"/>',
        '<path d="M-300,0 C-360,-40 -430,-60 -470,-40 C-440,-20 -450,0 -480,10 C-440,14 -440,36 -470,56 '
        'C-420,60 -360,40 -296,14 Z"/>',
        '<path d="M-310,-6 l-8,26 l20,0 l-6,-26 Z"/>',
        # cloak streaming back
        f'<path d="M-50,4 C-60,-60 -40,-120 -10,-150 C-80,-150 -150,{-130 + w:.0f} -250,{-110 + w:.0f} '
        f'C-210,{-90 - w:.0f} -230,{-70 + w:.0f} -300,{-50 + w:.0f} C-220,-30 -140,-10 -50,4 Z"/>',
        # body
        '<path d="M-60,4 C-70,-70 -40,-140 0,-160 C40,-150 50,-100 40,-40 C36,-16 20,0 -60,4 Z"/>',
        # arm reaching to the broom
        '<path d="M10,-130 C50,-100 80,-60 96,-22" stroke-width="22" stroke-linecap="round" fill="none" stroke="currentColor"/>',
        # leg and pointed boot
        '<path d="M-20,0 C10,20 40,40 70,44 L112,40 L86,56 L60,60 C30,56 0,40 -30,16 Z"/>',
        # head, nose, chin
        '<circle cx="14" cy="-186" r="30"/>',
        '<path d="M38,-196 L68,-178 L40,-176 Z M30,-164 L48,-150 L26,-158 Z"/>',
        # hair streaming back
        f'<path d="M-10,-200 C-60,{-200 + w:.0f} -100,{-170 - w:.0f} -150,{-180 + w:.0f} C-110,-150 -60,-150 -14,-160 Z"/>',
        # hat: wide brim and a crooked cone bent back by the wind
        '<ellipse cx="10" cy="-210" rx="92" ry="14" transform="rotate(-10 10 -210)"/>',
        f'<path d="M-36,-214 C-20,-260 -10,-300 -40,-350 C-60,-380 -90,{-390 + w:.0f} -120,{-380 + w:.0f} '
        'C-80,-370 -40,-330 -10,-300 C10,-270 40,-240 54,-220 Z"/>',
    ]
    return (f'<g transform="translate({x:.0f},{y:.0f}) scale({s:.2f}) rotate(-8)" fill="{P["near"]}" '
            f'color="{P["near"]}">{"".join(parts)}</g>')


def eyes(x, y, s, colour, opacity=1.0):
    return (f'<g transform="translate({x:.0f},{y:.0f}) scale({s:.2f})" fill="{colour}" opacity="{opacity:.2f}" filter="url(#glow)">'
            '<path d="M-26,0 q12,-14 24,0 q-12,8 -24,0 Z M6,0 q12,-14 24,0 q-12,8 -24,0 Z"/></g>')


def web(cx, cy, radius, start, sweep, colour, rings=7, spokes=9, width=3):
    out = []
    angs = [math.radians(start + sweep * i / (spokes - 1)) for i in range(spokes)]
    for a in angs:
        out.append(f'M{cx},{cy} L{cx + math.cos(a) * radius:.0f},{cy + math.sin(a) * radius:.0f}')
    for k in range(1, rings + 1):
        r = radius * k / rings
        pts = [(cx + math.cos(a) * r, cy + math.sin(a) * r) for a in angs]
        seg = f"M{pts[0][0]:.0f},{pts[0][1]:.0f}"
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            mx, my = (ax + bx) / 2, (ay + by) / 2
            sag = 0.88
            seg += f" Q{cx + (mx - cx) * sag:.0f},{cy + (my - cy) * sag:.0f} {bx:.0f},{by:.0f}"
        out.append(seg)
    return f'<path d="{" ".join(out)}" stroke="{colour}" stroke-width="{width}" fill="none" opacity="0.55"/>'


def spider(x, y, s, colour=P["near"]):
    legs = "".join(f'<path d="M0,0 q{sx * 40},{-30 + i * 14} {sx * 70},{-10 + i * 22}" stroke="{colour}" stroke-width="6" fill="none"/>'
                   for sx in (-1, 1) for i in range(4))
    return (f'<g transform="translate({x:.0f},{y:.0f}) scale({s:.2f})">{legs}'
            f'<ellipse cx="0" cy="0" rx="26" ry="34" fill="{colour}"/><circle cx="0" cy="-36" r="16" fill="{colour}"/>'
            f'<circle cx="-6" cy="-38" r="3.5" fill="#ff5f5f"/><circle cx="6" cy="-38" r="3.5" fill="#ff5f5f"/></g>')


def cauldron(x, y, s, t, rnd):
    out = [f'<g transform="translate({x:.0f},{y:.0f}) scale({s:.2f})">',
           '<ellipse cx="0" cy="-160" rx="420" ry="280" fill="url(#toxicGlow)"/>',
           '<path d="M-150,40 L-190,120 M150,40 L190,120 M0,60 L0,130" stroke="#07050b" stroke-width="22"/>',
           '<path d="M-60,110 q30,-80 60,-140 q30,60 60,140 z" fill="#ff7a1a" filter="url(#glow)"/>',
           '<path d="M-100,115 q20,-50 40,-90 q20,40 40,90 z M20,115 q20,-50 40,-90 q20,40 40,90 z" fill="#ffd36b" filter="url(#glow)"/>',
           '<path d="M-210,-90 C-230,40 -120,90 0,90 C120,90 230,40 210,-90 Z" fill="#07050b"/>',
           '<ellipse cx="0" cy="-92" rx="230" ry="40" fill="#0d0a12" stroke="#1d1428" stroke-width="12"/>',
           f'<ellipse cx="0" cy="-96" rx="200" ry="28" fill="{P["toxic"]}" filter="url(#glow)"/>']
    for i in range(9):
        phase = rnd.uniform(0, 1)
        speed = rnd.uniform(0.7, 1.4)
        life = (phase + t * speed * 3) % 1.0 if t < 1 else phase
        bx = rnd.uniform(-150, 150) + math.sin(life * 8 + i) * 20
        by = -110 - life * 420
        r = rnd.uniform(10, 26) * (1 - life * 0.5)
        out.append(f'<circle cx="{bx:.0f}" cy="{by:.0f}" r="{r:.0f}" fill="none" stroke="{P["toxic"]}" '
                   f'stroke-width="4" opacity="{(1 - life) * 0.9:.2f}"/>')
    out.append('</g>')
    return "".join(out)


# ---------------------------------------------------------------- scenes


def s_graveyard_moon(W, H, t):
    r = random.Random(101)
    st = [sky(W, H, P["night"], P["dusk"], "#3a1a3a"), stars(r, W, H * 0.6)]
    mx = W * 0.68
    st.append(moon(mx, 760, 430, r))
    for _ in range(4):
        st.append(cloud(r.uniform(W * 0.4, W * 0.95), r.uniform(560, 1080), r.uniform(700, 1100), r))
    st.append(hills(W, H, P["far"], 1640, 120, 0.0011, 1.0))
    st.append(hills(W, H, P["mid"], 1800, 90, 0.0017, 2.4))
    for _ in range(10):
        st.append(tombstone(r.uniform(W * 0.38, W * 0.92), 1830 + r.uniform(-20, 30), r.uniform(90, 170),
                            r.uniform(-7, 7), cross=r.random() < 0.25))
    st.append(hills(W, H, P["near"], 1960, 50, 0.0023, 0.7))
    st.append(tree(W * 0.14, 1990, 470, r, lean=-0.12))
    pk = [(W * 0.33, 1930, 1.25, 1), (W * 0.41, 1985, 0.85, 2), (W * 0.86, 1965, 1.0, 3)]
    for x, y, s, seed in pk:
        st.append(pumpkin(x, y, s, seed))
    st.append(grass(W, H, 2070, r))
    a = random.Random(102)
    an = [lantern_glow(x, y, s, flicker(a, t)) for x, y, s, _ in pk]
    an.append(fog(a, W, 1880, 2150, t))
    an.append(bat_flock(a, 11, (W * 0.5, 300, W * 0.88, 1200), t))
    return "".join(st), "".join(an)


def s_haunted_house(W, H, t):
    r = random.Random(201)
    st = [sky(W, H, "#050409", "#140b22", "#2a1238", haze_opacity=0.22), stars(r, W, H * 0.55)]
    st.append(moon(W * 0.62, 640, 360, r))
    st.append(cloud(W * 0.55, 820, 1200, r, opacity=0.9))
    st.append(hills(W, H, P["far"], 1500, 70, 0.0009, 2.0))
    s = 1.15
    hx, top = W * 0.5 - 160 * s, 1470
    st.append(tree(W * 0.32, 1840, 300, r, lean=0.3, depth=8))
    st.append(tree(W * 0.68, 1860, 270, r, lean=-0.3, depth=8))
    st.append(f'<path d="M0,1930 C{W * 0.3:.0f},1910 {W * 0.38:.0f},{top - 20} {W / 2:.0f},{top - 20} '
              f'C{W * 0.62:.0f},{top - 20} {W * 0.7:.0f},1910 {W},1930 L{W},{H} L0,{H} Z" fill="{P["near"]}"/>')
    st.append(house(hx, top + 10, s, 7))
    door = hx + 165 * s
    st.append(f'<path d="M{door:.0f},{top + 12} C{door + 60:.0f},1700 {door - 260:.0f},1880 {door - 60:.0f},{H}" '
              f'stroke="#2a1838" stroke-width="34" fill="none" opacity="0.8"/>')
    st.append(fence(W, 2160, r))
    a = random.Random(202)
    an = [fog(a, W, 1500, 1900, t, n=6, opacity=0.09)]
    an.append(bat_flock(a, 14, (W * 0.3, 260, W * 0.8, 900), t, scale=(0.8, 2.0), entry="right"))
    return "".join(st), "".join(an)


def s_pumpkin_patch(W, H, t):
    r = random.Random(301)
    st = [sky(W, H, "#0b0612", "#2a1230", "#7a2e1a", haze_y=1.05, haze_opacity=0.55), stars(r, W, H * 0.4, 220)]
    st.append(moon(W * 0.2, 520, 220, r, glow=3.0))
    st.append(hills(W, H, "#2a1226", 1420, 60, 0.0012, 0.4))
    st.append(hills(W, H, "#1a0c1c", 1560, 50, 0.0019, 1.9))
    # scarecrow
    sx = W * 0.74
    st.append(f'<g fill="{P["near"]}" stroke="{P["near"]}"><rect x="{sx - 12:.0f}" y="1080" width="24" height="520"/>'
              f'<rect x="{sx - 260:.0f}" y="1180" width="520" height="22"/>'
              f'<path d="M{sx - 90:.0f},1190 L{sx + 90:.0f},1190 L{sx + 60:.0f},1430 L{sx - 60:.0f},1430 Z"/>'
              f'<path d="M{sx - 260:.0f},1190 l-30,70 l40,-20 l10,40 l20,-60 Z M{sx + 260:.0f},1190 l30,70 l-40,-20 l-10,40 l-20,-60 Z"/>'
              f'<circle cx="{sx:.0f}" cy="1120" r="62"/><path d="M{sx - 120:.0f},1080 L{sx + 120:.0f},1080 L{sx + 30:.0f},960 L{sx - 40:.0f},990 Z"/></g>')
    st.append(eyes(sx, 1115, 1.4, P["ember"]))
    st.append(hills(W, H, "#0c0610", 1700, 40, 0.0027, 1.2))
    vines = []
    for _ in range(14):
        x0 = r.uniform(0, W)
        vines.append(f'M{x0:.0f},{r.uniform(1750, 2150):.0f} q{r.uniform(-300, 300):.0f},{r.uniform(-120, 120):.0f} {r.uniform(-600, 600):.0f},{r.uniform(-60, 60):.0f}')
    st.append(f'<path d="{" ".join(vines)}" stroke="#1d2a12" stroke-width="12" fill="none"/>')
    pk = []
    for i in range(16):
        y = r.uniform(1700, 2100)
        s = 0.5 + (y - 1700) / 400 * 1.1
        pk.append((r.uniform(60, W - 60), y, s, 30 + i, r.random() < 0.6))
    pk.sort(key=lambda p: p[1])
    for x, y, s, seed, lit in pk:
        st.append(pumpkin(x, y, s, seed, lit=lit))
    a = random.Random(302)
    an = [lantern_glow(x, y, s, flicker(a, t)) for x, y, s, _, lit in pk if lit]
    an.append(fog(a, W, 1600, 1800, t, n=4, opacity=0.08, colour="#ffb98a"))
    an.append(bat_flock(a, 7, (W * 0.08, 250, W * 0.45, 800), t, scale=(0.8, 1.6)))
    return "".join(st), "".join(an)


def s_witch_moon(W, H, t):
    r = random.Random(401)
    st = [sky(W, H, "#06040b", "#12091d", "#1f0f2e", haze_opacity=0.12, haze=P["violet"]), stars(r, W, H, 520)]
    mx, my, mr = W * 0.5, 1000, 700
    st.append(moon(mx, my, mr, r, glow=2.0))
    for _ in range(3):
        st.append(cloud(r.uniform(W * 0.2, W * 0.8), r.uniform(1300, 1700), r.uniform(900, 1400), r, opacity=0.9))
    a = random.Random(402)
    k = ease_out(t)
    wx = (-600) + (mx + 80 - (-600)) * k
    wy = 1500 + (my - 40 - 1500) * k + math.sin(t * 9) * 40 * (1 - k)
    an = [witch(wx, wy, 1.6, wind=abs(math.sin(t * 30)) * (1 - k))]
    an.append(bat_flock(a, 9, (mx - mr * 1.4, my - mr, mx + mr * 1.4, my + mr * 0.6), t, scale=(0.8, 1.8)))
    return "".join(st), "".join(an)


def s_forest_fog(W, H, t):
    r = random.Random(501)
    st = [sky(W, H, "#030507", "#0b1310", "#172418", haze_opacity=0.3, haze=P["toxic"])]
    st.append(moon(W * 0.5, 520, 180, r, glow=4.0))
    layers = [("#16241a", 1500, 0.55, 18), ("#0f1912", 1700, 0.75, 14), ("#070c08", 1950, 1.0, 9)]
    a = random.Random(502)
    for i, (colour, base, size, n) in enumerate(layers):
        for _ in range(n):
            st.append(tree(r.uniform(-100, W + 100), base + r.uniform(-40, 60), r.uniform(260, 460) * size, r,
                           colour=colour, lean=r.uniform(-0.2, 0.2), depth=7))
        st.append(f'<rect x="0" y="{base - 200}" width="{W}" height="{H - base + 200}" fill="#9be564" opacity="0.03" filter="url(#soft)"/>')
    st.append(grass(W, H, 2080, r, colour="#030503"))
    pairs = [(r.uniform(W * 0.1, W * 0.9), r.uniform(1500, 1950), r.uniform(0.8, 1.6)) for _ in range(9)]
    an = [fog(a, W, 1450, 2100, t, n=8, opacity=0.12, colour="#b8e8a0")]
    for i, (x, y, s) in enumerate(pairs):
        blink = 1.0 if t >= 1 else (0.0 if (t * 6 + i * 0.37) % 1 < 0.12 else 1.0) * min(1.0, t * 3 + i * 0.05)
        an.append(eyes(x, y, s, P["toxic"] if i % 3 else P["ember"], blink))
    return "".join(st), "".join(an)


def s_cauldron(W, H, t):
    r = random.Random(601)
    st = [sky(W, H, "#05030a", "#0e0817", "#1a0d24", haze_opacity=0.25, haze=P["toxic"]), stars(r, W, H * 0.5, 260)]
    st.append(moon(W * 0.82, 420, 200, r))
    st.append(tree(W * 0.08, 2000, 520, r, lean=0.1))
    st.append(tree(W * 0.93, 2000, 480, r, lean=-0.15))
    st.append(hills(W, H, P["near"], 1960, 30, 0.002, 0.3))
    for i in range(7):
        ang = math.pi + i * math.pi / 6
        st.append(f'<ellipse cx="{W / 2 + math.cos(ang) * 620:.0f}" cy="{1990 + math.sin(ang) * -60:.0f}" rx="70" ry="34" fill="#140d1c" stroke="#2c1a3c" stroke-width="4"/>')
    a = random.Random(602)
    an = [cauldron(W / 2, 1880, 1.6, t, a)]
    an.append(fog(a, W, 1900, 2150, t, n=5, opacity=0.1, colour="#b8e8a0"))
    an.append(bat_flock(a, 6, (W * 0.25, 300, W * 0.75, 900), t, scale=(0.8, 1.5)))
    return "".join(st), "".join(an)


def s_lone_lantern(W, H, t):
    """Minimal: one lantern, lots of quiet space for windows and the bar."""
    r = random.Random(701)
    st = [f'<radialGradient id="vignette" cx="0.5" cy="0.62" r="0.7"><stop offset="0" stop-color="#2a1636"/>'
          f'<stop offset="1" stop-color="#08050c"/></radialGradient><rect width="{W}" height="{H}" fill="url(#vignette)"/>']
    st.append(stars(r, W, H, 160))
    st.append(f'<ellipse cx="{W / 2}" cy="1520" rx="900" ry="80" fill="#000" opacity="0.5" filter="url(#soft)"/>')
    st.append(pumpkin(W / 2, 1400, 2.4, 5))
    a = random.Random(702)
    an = [lantern_glow(W / 2, 1400, 2.4, flicker(a, t))]
    an.append(bat_flock(a, 3, (W * 0.58, 700, W * 0.72, 1000), t, scale=(1.2, 1.8)))
    return "".join(st), "".join(an)


def s_spider_web(W, H, t):
    """Minimal: corner webs and a dangling spider on plain night violet."""
    r = random.Random(801)
    st = [f'<rect width="{W}" height="{H}" fill="#140e1c"/>', stars(r, W, H, 120)]
    st.append(web(0, 0, 1100, 0, 90, P["bone"]))
    st.append(web(W, 0, 800, 90, 90, P["bone"], rings=6, spokes=7))
    st.append(web(W, H, 520, 180, 90, P["bone"], rings=5, spokes=6, width=2))
    a = random.Random(802)
    k = ease_out(t)
    drop = 300 + 780 * k + math.sin(t * 14) * 40 * (1 - k)
    sx = 780
    an = [f'<path d="M{sx},380 L{sx},{drop:.0f}" stroke="{P["bone"]}" stroke-width="3" opacity="0.6"/>',
          spider(sx, drop + 30, 1.4)]
    an.append(bat_flock(a, 4, (W * 0.6, 500, W * 0.85, 900), t, scale=(1.0, 1.6), entry="right"))
    return "".join(st), "".join(an)


SCENES = [
    ("1-graveyard-moon", s_graveyard_moon),
    ("2-haunted-house", s_haunted_house),
    ("3-pumpkin-patch", s_pumpkin_patch),
    ("4-witch-moon", s_witch_moon),
    ("5-forest-fog", s_forest_fog),
    ("6-cauldron", s_cauldron),
    ("7-lone-lantern", s_lone_lantern),
    ("8-spider-web", s_spider_web),
]


def svg(W, H, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">{DEFS}{body}</svg>')
