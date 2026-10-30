"""Monograph artwork: eight quiet typographic scenes as SVG.

Every scene is a function scene(W, H, t) -> (static_svg_body, animated_svg_body),
the same contract as halloween_night.py: t runs 0..1 over the intro video and
t = 1 is the still wallpaper. All type is set in Omarchy's default font,
JetBrainsMono Nerd Font, so the wallpapers match the terminal and the bar.
"""
from xml.sax.saxutils import escape

FONT = "JetBrainsMono Nerd Font"
P = {
    "paper": "#15171c", "paper_lo": "#0f1115", "rule": "#262a32", "faint": "#2e323b",
    "muted": "#7c8290", "dim": "#a9a59b", "ink": "#e8e4da", "brass": "#d4ad6a",
}

DEFS = f"""<defs>
<linearGradient id="paper" x1="0" y1="0" x2="0.3" y2="1"><stop offset="0" stop-color="{P['paper']}"/>
 <stop offset="1" stop-color="{P['paper_lo']}"/></linearGradient>
<radialGradient id="lamp" cx="0.3" cy="0.35" r="0.8"><stop offset="0" stop-color="#ffffff" stop-opacity="0.035"/>
 <stop offset="1" stop-color="#ffffff" stop-opacity="0"/></radialGradient>
</defs>"""


def clamp(x):
    return max(0.0, min(1.0, x))


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def text(x, y, s, size, fill=P["ink"], weight=400, anchor="start", opacity=1.0, extra=""):
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-family="{FONT}" font-size="{size:.0f}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}" opacity="{opacity:.3f}" xml:space="preserve" {extra}>{escape(s)}</text>')


def paper(W, H, grid=None):
    out = f'<rect width="{W}" height="{H}" fill="url(#paper)"/><rect width="{W}" height="{H}" fill="url(#lamp)"/>'
    if grid:
        out += "".join(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="{P["rule"]}" stroke-width="2"/>'
                       for y in range(grid, H, grid))
    return out


def typed(s, t, start=0.05, end=0.7):
    """The first part of s, as if typed between start and end."""
    return s[:round(len(s) * clamp((t - start) / (end - start)))]


def cursor(x, y, size, t):
    # Blinks during the intro, then stays on in the still.
    on = t >= 1 or int(t * 12) % 2 == 0
    w, h = size * 0.6, size * 0.95
    return f'<rect x="{x:.0f}" y="{y - h * 0.8:.0f}" width="{w:.0f}" height="{h:.0f}" fill="{P["brass"]}" opacity="{1 if on else 0}"/>'


# Advance of one JetBrains Mono glyph as a share of the font size.
ADVANCE = 0.6


def s_hello(W, H, t):
    size = H * 0.2
    x, y = W * 0.12, H * 0.68
    word = typed("hello.", t)
    anim = text(x, y, word, size, weight=700) + cursor(x + len(word) * size * ADVANCE + size * 0.08, y, size, t)
    anim += text(x + 6, y + size * 0.42, "welcome to omarchy", size * 0.16, P["muted"], opacity=ease((t - 0.7) / 0.25))
    return paper(W, H, grid=H // 18), anim


def s_specimen(W, H, t):
    static = paper(W, H) + text(W * 0.08, H * 0.72, "Aa", H * 0.56, weight=700)
    rows = ["ABCDEFGHIJKLM", "NOPQRSTUVWXYZ", "abcdefghijklm", "nopqrstuvwxyz", "0123456789", "& ? ! { } [ ] ~ $"]
    anim = ""
    for i, row in enumerate(rows):
        a = ease((t - 0.08 * i) / 0.4)
        anim += text(W * 0.56, H * 0.3 + i * H * 0.085 + (1 - a) * 40, row, H * 0.05,
                     P["brass"] if i == 5 else P["dim"], opacity=a)
    static += text(W * 0.56, H * 0.2, "JetBrains Mono — Bold, Regular", H * 0.022, P["muted"])
    return static, anim


def s_metrics(W, H, t):
    size = H * 0.42
    x, base = W * 0.18, H * 0.66
    lines = [("cap height", base - size * 0.73),
             ("x-height", base - size * 0.55), ("baseline", base), ("descender", base + size * 0.23)]
    static = paper(W, H) + text(x, base, "Hxgy", size, weight=700)
    anim = ""
    for i, (label, y) in enumerate(lines):
        k = ease((t - 0.1 * i) / 0.45)
        colour = P["brass"] if label == "baseline" else P["faint"]
        anim += f'<line x1="{W * 0.1:.0f}" y1="{y:.0f}" x2="{W * 0.1 + W * 0.8 * k:.0f}" y2="{y:.0f}" stroke="{colour}" stroke-width="3"/>'
        anim += text(W * 0.9, y - 14, label, H * 0.018, P["muted"], anchor="end", opacity=k)
    return static, anim


def s_ampersand(W, H, t):
    k = ease(t / 0.8)
    static = paper(W, H) + text(W * 0.1, H * 0.86, "and so it begins", H * 0.025, P["muted"])
    anim = text(W * 0.62, H * 0.86, "&", H * (0.9 + 0.1 * (1 - k)), P["brass"], weight=700, anchor="middle",
                opacity=0.85 * k)
    return static, anim


def s_prompt(W, H, t):
    cell = H // 27
    static = paper(W, H)
    static += "".join(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="{P["rule"]}" stroke-width="1"/>'
                      for x in range(0, W, round(cell * ADVANCE * 2)))
    static += "".join(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="{P["rule"]}" stroke-width="1"/>'
                      for y in range(0, H, cell))
    size = H * 0.07
    x, y = W * 0.14, H * 0.55
    command = typed("omarchy", t, 0.15, 0.75)
    anim = (text(x, y, "~", size, P["brass"], weight=700) + text(x + size * ADVANCE * 2, y, "$", size, P["muted"])
            + text(x + size * ADVANCE * 4, y, command, size, weight=700)
            + cursor(x + size * ADVANCE * (4 + len(command)) + size * 0.05, y, size, t))
    return static, anim


def s_alphabet(W, H, t):
    letters = "abcdefghijklmnopqrstuvwxyz"
    size = H * 0.085
    cols, rows = int((W - size * 0.8) / (size * 0.55 * ADVANCE * 2)) + 1, int(H / (size * 1.25)) + 1
    static = paper(W, H)
    # The middle row's "o" nearest the centre.
    r = rows // 2
    c = min((c for c in range(cols) if letters[(r * 7 + c) % 26] == "o"), key=lambda c: abs(c - cols / 2))
    for i in range(rows):
        row = "".join(letters[(i * 7 + j) % 26] for j in range(cols))
        static += text(size * 0.4, size * (1.0 + i * 1.25), " ".join(row), size * 0.55, P["faint"])
    # One letter lights up: the o of omarchy, found as the sweep passes over it.
    x, y = size * 0.4 + c * size * 0.55 * ADVANCE * 2, size * (1.0 + r * 1.25)
    k = ease((t - 0.4) / 0.5)
    sweep = W * ease(t / 0.6)
    anim = f'<rect x="0" y="{y - size * 0.6:.0f}" width="{sweep:.0f}" height="{size * 0.8:.0f}" fill="{P["brass"]}" opacity="{0.06 * (1 - k):.3f}"/>'
    anim += text(x, y, "o", size * 0.55, P["brass"], weight=700, opacity=k)
    return static, anim


def s_braces(W, H, t):
    k = ease(t / 0.75)
    size = H * 0.7
    gap = W * 0.18 + (1 - k) * W * 0.25
    stroke = f'stroke="{P["dim"]}" stroke-width="4"'
    anim = (text(W / 2 - gap, H * 0.72, "{", size, "none", weight=300, anchor="middle", extra=stroke)
            + text(W / 2 + gap, H * 0.72, "}", size, "none", weight=300, anchor="middle", extra=stroke)
            + text(W / 2, H * 0.53, "welcome", H * 0.06, P["brass"], weight=700, anchor="middle",
                   opacity=ease((t - 0.55) / 0.35)))
    return paper(W, H), anim


def s_numerals(W, H, t):
    size = H * 0.16
    digits = "0123456789"
    step = W * 0.08
    x0 = W / 2 - step * 4.5
    static = paper(W, H)
    static += "".join(f'<line x1="{x0 - step / 2 + i * step:.0f}" y1="{H * 0.32:.0f}" x2="{x0 - step / 2 + i * step:.0f}" '
                      f'y2="{H * 0.62:.0f}" stroke="{P["rule"]}" stroke-width="2"/>' for i in range(11))
    static += text(W / 2, H * 0.74, "tabular figures · every digit the same width", H * 0.02, P["muted"], anchor="middle")
    anim = ""
    for i, d in enumerate(digits):
        a = ease((t - 0.05 * i) / 0.35)
        anim += text(x0 + i * step, H * 0.53 + (1 - a) * 60, d, size, P["brass"] if d == "0" else P["ink"],
                     weight=700, anchor="middle", opacity=a)
    return static, anim


SCENES = [
    ("1-hello", s_hello),
    ("2-specimen", s_specimen),
    ("3-metrics", s_metrics),
    ("4-ampersand", s_ampersand),
    ("5-prompt", s_prompt),
    ("6-alphabet", s_alphabet),
    ("7-braces", s_braces),
    ("8-numerals", s_numerals),
]


def svg(W, H, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">{DEFS}{body}</svg>')
