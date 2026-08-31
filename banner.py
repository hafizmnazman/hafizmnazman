#!/usr/bin/env python3
"""Generate banner_dark.svg and banner_light.svg, the ANSI Shadow name banner.

Run once by hand whenever the name or colors change; the output is committed.
Standard library only, same rules as today.py.
"""
from pathlib import Path

ROOT = Path(__file__).parent
NAME = "HAFIZ AZMAN"

# ANSI Shadow figlet glyphs, 6 rows each, every row of a glyph the same width.
GLYPHS = {
    "H": [
        "██╗  ██╗",
        "██║  ██║",
        "███████║",
        "██╔══██║",
        "██║  ██║",
        "╚═╝  ╚═╝",
    ],
    "A": [
        " █████╗ ",
        "██╔══██╗",
        "███████║",
        "██╔══██║",
        "██║  ██║",
        "╚═╝  ╚═╝",
    ],
    "F": [
        "███████╗",
        "██╔════╝",
        "█████╗  ",
        "██╔══╝  ",
        "██║     ",
        "╚═╝     ",
    ],
    "I": [
        "██╗",
        "██║",
        "██║",
        "██║",
        "██║",
        "╚═╝",
    ],
    "Z": [
        "███████╗",
        "╚══███╔╝",
        "  ███╔╝ ",
        " ███╔╝  ",
        "███████╗",
        "╚══════╝",
    ],
    "M": [
        "███╗   ███╗",
        "████╗ ████║",
        "██╔████╔██║",
        "██║╚██╔╝██║",
        "██║ ╚═╝ ██║",
        "╚═╝     ╚═╝",
    ],
    "N": [
        "███╗   ██╗",
        "████╗  ██║",
        "██╔██╗ ██║",
        "██║╚██╗██║",
        "██║ ╚████║",
        "╚═╝  ╚═══╝",
    ],
    " ": [
        "   ",
        "   ",
        "   ",
        "   ",
        "   ",
        "   ",
    ],
}

# Vertical gradient, top to bottom, in each theme's accent range.
THEMES = {
    "dark": ["#79c0ff", "#4493f8", "#39c5cf"],
    "light": ["#218bff", "#0969da", "#1b7c83"],
}

W = 850
PAD = 24
FS = 14.5
LH = 15.4
ROWS = 6


def render_lines():
    lines = []
    for row in range(ROWS):
        lines.append(" ".join(GLYPHS[ch][row] for ch in NAME))
    widths = {len(l) for l in lines}
    assert len(widths) == 1, f"ragged banner rows: {widths}"
    return lines


def build(theme, lines):
    stops = THEMES[theme]
    h = round(2 * PAD + FS + (ROWS - 1) * LH)
    text_len = W - 2 * PAD
    p = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" '
        f'width="{W}" height="{h}" role="img" aria-label="{NAME}">'
    )
    p.append(
        f'<defs><linearGradient id="ramp" gradientUnits="userSpaceOnUse" '
        f'x1="0" y1="{PAD}" x2="0" y2="{h - PAD}">'
        f'<stop offset="0" stop-color="{stops[0]}"/>'
        f'<stop offset="0.55" stop-color="{stops[1]}"/>'
        f'<stop offset="1" stop-color="{stops[2]}"/>'
        f"</linearGradient></defs>"
    )
    p.append(
        "<style>text { font-family: ui-monospace,'SFMono-Regular','SF Mono',"
        "Menlo,Consolas,'Liberation Mono',monospace; font-size: "
        f"{FS}px; fill: url(#ramp); white-space: pre; }}</style>"
    )
    for i, line in enumerate(lines):
        y = PAD + FS + i * LH
        p.append(
            f'<text x="{PAD}" y="{y:.1f}" textLength="{text_len}" '
            f'lengthAdjust="spacing" xml:space="preserve">{line}</text>'
        )
    p.append("</svg>")
    return "\n".join(p)


def main():
    lines = render_lines()
    for theme in THEMES:
        svg = build(theme, lines)
        out = ROOT / f"banner_{theme}.svg"
        out.write_text(svg, encoding="utf-8", newline="\n")
        print(f"wrote {out.name} ({len(lines[0])} cols)")


if __name__ == "__main__":
    main()
