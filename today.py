#!/usr/bin/env python3
"""Regenerate dark_mode.svg and light_mode.svg with fresh GitHub stats.

Runs daily via GitHub Actions. Standard library only, no pip installs.
Needs a token in GH_TOKEN (or GITHUB_TOKEN) with read access to all owned
repos, private included, so the repo split and line counts stay truthful.
"""
import html
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

USER = "hafizmnazman"
ROOT = Path(__file__).parent
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""

# ---------------------------------------------------------------- GitHub API

def api(path):
    url = path if path.startswith("http") else "https://api.github.com" + path
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER,
    }
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read().decode("utf-8")
        return r.status, (json.loads(body) if body.strip() else None)


def all_repos():
    repos, page = [], 1
    while True:
        _, batch = api(f"/user/repos?per_page=100&affiliation=owner&page={page}")
        repos.extend(batch or [])
        if not batch or len(batch) < 100:
            return repos
        page += 1


def repo_contrib(repo_name, attempts=6):
    """My summed additions, deletions, commits in one repo. Retries while 202."""
    for i in range(attempts):
        status, data = api(f"/repos/{USER}/{repo_name}/stats/contributors")
        if status == 202 or data is None:
            time.sleep(6)
            continue
        a = d = c = 0
        for entry in data:
            if (entry.get("author") or {}).get("login") == USER:
                for w in entry.get("weeks", []):
                    a += w["a"]
                    d += w["d"]
                    c += w["c"]
        return a, d, c
    print(f"  warning: stats never ready for {repo_name}, counted as 0")
    return 0, 0, 0


def all_langs(repos):
    """Total bytes per language across my non-fork repos."""
    totals = {}
    for r in repos:
        if r.get("fork"):
            continue
        _, langs = api(f"/repos/{r['full_name']}/languages")
        for name, size in (langs or {}).items():
            totals[name] = totals.get(name, 0) + size
    return totals

# ------------------------------------------------------------------- helpers

def compact(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}m"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return f"{n:,}"


def plural(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")


def ymd_since(start, now):
    y, m, d = now.year - start.year, now.month - start.month, now.day - start.day
    if d < 0:
        m -= 1
        d += (now.replace(day=1) - timedelta(days=1)).day
    if m < 0:
        y -= 1
        m += 12
    return y, m, d

# ------------------------------------------------------------------ the card

THEMES = {
    "dark": {
        "fg": "#e6edf3", "muted": "#8b949e", "accent": "#4493f8", "art": "#e6edf3",
        "pos": "#3fb950", "neg": "#f85149",
        "bg": "#0d1117", "border": "#30363d",
        "bar": ["#f85149", "#db6d28", "#d29922", "#3fb950", "#39c5cf", "#4493f8", "#ab7df8", "#8b949e"],
        "langs": ["#4493f8", "#39c5cf", "#3fb950", "#d29922", "#db6d28", "#f85149", "#ab7df8", "#8b949e"],
    },
    "light": {
        "fg": "#1f2328", "muted": "#667085", "accent": "#0969da", "art": "#24292f",
        "pos": "#1a7f37", "neg": "#cf222e",
        "bg": "#ffffff", "border": "#d0d7de",
        "bar": ["#cf222e", "#bc4c00", "#9a6700", "#1a7f37", "#1b7c83", "#0969da", "#8250df", "#667085"],
        "langs": ["#0969da", "#1b7c83", "#1a7f37", "#9a6700", "#bc4c00", "#cf222e", "#8250df", "#667085"],
    },
}

TAGLINE = "your friendly neighbourhood developer"
W, H = 850, 540
ART_X, ART_Y0, ART_LEN, ART_FS = 24, 78, 405, 13.5
ART_LH = 17.9
LBL_X, VAL_X = 460, 566
MONO = "ui-monospace,'SFMono-Regular','SF Mono',Menlo,Consolas,'Liberation Mono',monospace"


def build(theme, art, groups, sync):
    t = THEMES[theme]
    p = []
    p.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Hafiz Azman, ASCII portrait with GitHub stats">')
    p.append(f"""<style>
    text {{ font-family: {MONO}; }}
    .art {{ font-size: {ART_FS}px; fill: {t['art']}; white-space: pre; }}
    .fg  {{ fill: {t['fg']}; font-size: 14px; }}
    .mut {{ fill: {t['muted']}; font-size: 14px; }}
    .acc {{ fill: {t['accent']}; font-size: 14px; }}
    .pos {{ fill: {t['pos']}; font-size: 14px; }}
    .neg {{ fill: {t['neg']}; font-size: 14px; }}
    .b   {{ font-weight: 600; }}
    .sm  {{ font-size: 12px; }}
    </style>""")
    for i, line in enumerate(art):
        y = ART_Y0 + i * ART_LH
        p.append(f'<text class="art" x="{ART_X}" y="{y:.1f}" textLength="{ART_LEN}" lengthAdjust="spacing" xml:space="preserve">{line}</text>')
    p.append(f'<text x="{LBL_X}" y="52" xml:space="preserve"><tspan class="acc b">hafiz@github</tspan><tspan class="mut">:~$</tspan><tspan class="fg"> neofetch</tspan><tspan class="acc">▊<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.2s" repeatCount="indefinite"/></tspan></text>')
    p.append(f'<text class="mut" x="{LBL_X}" y="78" font-style="italic">{TAGLINE}</text>')
    p.append(f'<line x1="{LBL_X}" y1="92" x2="826" y2="92" stroke="{t["muted"]}" stroke-opacity="0.45" stroke-width="1"/>')
    y = 114
    for group in groups:
        for k, v, extra in group:
            if isinstance(extra, tuple):
                added, deleted = extra
                suffix = (f'<tspan class="mut"> (</tspan><tspan class="pos">{added}</tspan>'
                          f'<tspan class="mut"> · </tspan><tspan class="neg">{deleted}</tspan>'
                          f'<tspan class="mut">)</tspan>')
            elif extra:
                suffix = f'<tspan class="mut">{extra}</tspan>'
            else:
                suffix = ""
            p.append(f'<text class="fg" x="{VAL_X}" y="{y}" xml:space="preserve"><tspan class="acc" x="{LBL_X}">{k}</tspan><tspan x="{VAL_X}">{v}</tspan>{suffix}</text>')
            y += 20
        y += 8
    y -= 4
    for i, c in enumerate(t["bar"]):
        p.append(f'<rect x="{LBL_X + i * 22}" y="{y - 10}" width="16" height="10" rx="2" fill="{c}"/>')
    p.append(f'<text class="mut sm" x="{LBL_X}" y="{y + 26}">last sync {sync} · auto-updates daily</text>')
    p.append("</svg>")
    return "\n".join(p)


LANGS_W, LANGS_H = 420, 195


def build_langs(theme, totals):
    """Small self-hosted 'most used languages' card, same look as the big card."""
    t = THEMES[theme]
    colors = t["langs"]
    total_all = sum(totals.values()) or 1
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    top = [kv for kv in ranked if kv[1] / total_all >= 0.005][:8]
    total = sum(v for _, v in top) or 1
    p = []
    p.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {LANGS_W} {LANGS_H}" width="{LANGS_W}" height="{LANGS_H}" role="img" aria-label="Most used languages">')
    p.append(f"""<style>
    text {{ font-family: {MONO}; }}
    .fg  {{ fill: {t['fg']}; font-size: 13px; }}
    .mut {{ fill: {t['muted']}; font-size: 13px; }}
    .acc {{ fill: {t['accent']}; font-size: 13px; }}
    .b   {{ font-weight: 600; }}
    </style>""")
    p.append(f'<rect x="0.5" y="0.5" width="{LANGS_W - 1}" height="{LANGS_H - 1}" rx="6" fill="{t["bg"]}" stroke="{t["border"]}"/>')
    p.append('<text x="20" y="30" xml:space="preserve"><tspan class="acc b">hafiz@github</tspan><tspan class="mut">:~$</tspan><tspan class="fg"> tokei</tspan></text>')
    bar_x, bar_y, bar_w, bar_h = 20, 46, LANGS_W - 40, 10
    p.append(f'<clipPath id="bar"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="5"/></clipPath>')
    x = float(bar_x)
    for i, (_, size) in enumerate(top):
        w = bar_w * size / total
        p.append(f'<rect clip-path="url(#bar)" x="{x:.1f}" y="{bar_y}" width="{w + 1:.1f}" height="{bar_h}" fill="{colors[i]}"/>')
        x += w
    for i, (name, size) in enumerate(top):
        col, row = i % 2, i // 2
        lx = 20 + col * 200
        ly = 86 + row * 27
        pct = 100 * size / total
        p.append(f'<circle cx="{lx + 4}" cy="{ly - 4.5}" r="4.5" fill="{colors[i]}"/>')
        p.append(f'<text x="{lx + 17}" y="{ly}"><tspan class="fg">{html.escape(name.lower())}</tspan><tspan class="mut"> {pct:.1f}%</tspan></text>')
    p.append("</svg>")
    return "\n".join(p)


def main():
    if not TOKEN:
        print("no token in GH_TOKEN or GITHUB_TOKEN, refusing to write stale stats")
        return 1

    print("fetching profile ...")
    _, me = api("/user")
    followers = me["followers"]
    created = datetime.fromisoformat(me["created_at"].replace("Z", "+00:00"))

    print("fetching repos ...")
    repos = all_repos()
    pub = [r for r in repos if not r["private"]]
    priv = [r for r in repos if r["private"]]
    stars = sum(r["stargazers_count"] for r in pub)
    if not priv:
        print("warning: token sees no private repos, counts would be wrong, aborting")
        return 1

    print(f"summing languages across {len(repos)} repos ...")
    totals = all_langs(repos)

    print(f"summing contributions across {len(repos)} repos ...")
    tot_a = tot_d = tot_c = 0
    for r in repos:
        a, d, c = repo_contrib(r["name"])
        tot_a += a
        tot_d += d
        tot_c += c
    print(f"  additions={tot_a:,} deletions={tot_d:,} commits={tot_c:,}")

    now = datetime.now(timezone.utc)
    uy, um, ud = ymd_since(created, now)

    groups = [
        [
            ("os", "arch linux", ""),
            ("host", "lenovo legion 5", ""),
            ("editor", "vs code", ""),
            ("stack", "typescript · react · python", ""),
            ("keyboard", "rk m75", ""),
            ("headphones", "sony ult wear", ""),
            ("printer", "bambu lab x2d", ""),
        ],
        [
            ("linkedin", "in/hafizmnazman", ""),
            ("instagram", "@hafizmnazman", ""),
            ("discord", "@hafizmnazman", ""),
            ("portfolio", "hafizazman.com", ""),
            ("builds", "hafizbuilds.me", ""),
        ],
        [
            ("repos", f"{len(pub)} public · {len(priv)} private", ""),
            ("stars", f"{stars}", ""),
            ("followers", f"{followers}", ""),
            ("commits", f"{tot_c:,}", ""),
            ("lines", f"{tot_a - tot_d:,}", (f"{compact(tot_a)}++", f"{compact(tot_d)}--")),
            ("uptime", f"{plural(uy, 'yr')} {plural(um, 'mo')} {plural(ud, 'day')}", ""),
        ],
    ]

    sync = now.strftime("%Y-%m-%d")
    for theme in ("dark", "light"):
        art = (ROOT / "art" / f"{theme}.txt").read_text(encoding="utf-8").splitlines()
        svg = build(theme, art, groups, sync)
        (ROOT / f"{theme}_mode.svg").write_text(svg, encoding="utf-8", newline="\n")
        print(f"wrote {theme}_mode.svg")
        langs_svg = build_langs(theme, totals)
        (ROOT / f"langs_{theme}.svg").write_text(langs_svg, encoding="utf-8", newline="\n")
        print(f"wrote langs_{theme}.svg")
    return 0


if __name__ == "__main__":
    sys.exit(main())
