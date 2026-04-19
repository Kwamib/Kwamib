#!/usr/bin/env python3
"""Generate a terminal-style contribution heatmap SVG."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


GRAPHQL_URL = "https://api.github.com/graphql"

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

BG = "#0A0A0A"
FG = "#C9C9C9"
DIM = "#6e7681"
ACCENT = "#E8713A"

HEAT = ["#1a1a1a", "#3a2a22", "#7a4428", "#b75d2f", "#E8713A"]


def bucket(count: int) -> str:
    if count == 0:
        return HEAT[0]
    if count <= 2:
        return HEAT[1]
    if count <= 5:
        return HEAT[2]
    if count <= 9:
        return HEAT[3]
    return HEAT[4]


@dataclass
class Day:
    date: datetime
    count: int


def fetch_contributions(login, token):
    to = datetime.now(timezone.utc)
    from_ = to - timedelta(days=365)
    payload = json.dumps({
        "query": QUERY,
        "variables": {"login": login, "from": from_.isoformat(), "to": to.isoformat()},
    }).encode("utf-8")
    req = urllib.request.Request(
        GRAPHQL_URL, data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "kwamib-contrib-terminal",
        }, method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    if "errors" in data:
        print(f"GraphQL errors: {data['errors']}", file=sys.stderr)
        raise SystemExit(1)
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    total = cal["totalContributions"]
    days = []
    for week in cal["weeks"]:
        for d in week["contributionDays"]:
            days.append(Day(
                date=datetime.fromisoformat(d["date"]).replace(tzinfo=timezone.utc),
                count=d["contributionCount"],
            ))
    return total, days


def compute_streaks(days):
    longest = 0
    run = 0
    for d in days:
        if d.count > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    current = 0
    for d in reversed(days):
        if d.count > 0:
            current += 1
        else:
            break
    return current, longest


def most_active_weekday(days):
    totals = [0] * 7
    for d in days:
        totals[d.date.weekday()] += d.count
    names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return names[totals.index(max(totals))]


CELL = 12
GAP = 3
PAD_X = 28
PAD_Y = 24
HEADER_H = 150
FOOTER_H = 70
GRID_W = 53 * (CELL + GAP)
GRID_H = 7 * (CELL + GAP)
WIDTH = PAD_X * 2 + GRID_W + 50
HEIGHT = PAD_Y * 2 + HEADER_H + GRID_H + FOOTER_H


def t(x, y, text, *, fill=FG, size=12, anchor="start"):
    return (f'<text x="{x}" y="{y}" fill="{fill}" '
            f'font-family="Space Mono, SF Mono, Menlo, Consolas, monospace" '
            f'font-size="{size}" text-anchor="{anchor}">{text}</text>')


def render_svg(login, total, days):
    current_streak, longest_streak = compute_streaks(days)
    active_day = most_active_weekday(days)
    p = []
    p.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
             f'width="{WIDTH}" height="{HEIGHT}" role="img" aria-label="Contribution terminal">')
    p.append(f'<rect x="0.5" y="0.5" width="{WIDTH-1}" height="{HEIGHT-1}" rx="10" fill="{BG}" stroke="#1f1f1f"/>')
    bar_h = 32
    p.append(f'<rect x="0.5" y="0.5" width="{WIDTH-1}" height="{bar_h}" rx="10" fill="#141414"/>')
    p.append('<circle cx="20" cy="16" r="5" fill="#ff5f56"/>')
    p.append('<circle cx="38" cy="16" r="5" fill="#ffbd2e"/>')
    p.append('<circle cx="56" cy="16" r="5" fill="#27c93f"/>')
    p.append(t(WIDTH/2, 21, f"{login}@github — contrib", fill=DIM, size=11, anchor="middle"))
    y = bar_h + PAD_Y
    p.append(t(PAD_X, y, f"{login}@github", fill=ACCENT, size=13))
    po = PAD_X + (len(login) + 7) * 7.8
    p.append(t(po, y, ":", fill=DIM, size=13))
    p.append(t(po + 7, y, "~", fill="#4a90e2", size=13))
    p.append(t(po + 15, y, "$", fill=DIM, size=13))
    p.append(t(po + 27, y, f"contrib --year --user {login}", fill=FG, size=13))
    y += 28
    p.append(t(PAD_X, y, f"total          {total} contributions", size=12))
    y += 18
    p.append(t(PAD_X, y, f"current streak {current_streak} days", size=12))
    y += 18
    p.append(t(PAD_X, y, f"longest streak {longest_streak} days", size=12))
    y += 18
    p.append(t(PAD_X, y, f"most active    {active_day}", size=12))
    y += 22
    p.append(f'<line x1="{PAD_X}" y1="{y}" x2="{WIDTH-PAD_X}" y2="{y}" stroke="#1f1f1f"/>')
    y += 20
    p.append(t(PAD_X, y, "heatmap · last 52 weeks", fill=DIM, size=11))
    grid_top = y + 16
    for row, lbl in {0: "Mon", 2: "Wed", 4: "Fri"}.items():
        p.append(t(PAD_X, grid_top + row*(CELL+GAP) + CELL - 2, lbl, fill=DIM, size=9))
    grid_left = PAD_X + 32
    if not days:
        weeks = []
    else:
        first_wd = days[0].date.weekday()
        cells = [None]*first_wd + list(days)
        while len(cells) % 7 != 0:
            cells.append(None)
        weeks = [cells[i:i+7] for i in range(0, len(cells), 7)]
    weeks = weeks[-53:]
    prev_m = None
    for col, wk in enumerate(weeks):
        fd = next((d for d in wk if d is not None), None)
        if fd is None:
            continue
        if prev_m is None or fd.date.month != prev_m:
            if prev_m is not None:
                p.append(t(grid_left + col*(CELL+GAP), grid_top - 4,
                           fd.date.strftime("%b"), fill=DIM, size=9))
            prev_m = fd.date.month
    today = days[-1].date.date() if days else None
    for col, wk in enumerate(weeks):
        for row, d in enumerate(wk):
            if d is None:
                continue
            x = grid_left + col*(CELL+GAP)
            cy = grid_top + row*(CELL+GAP)
            stroke = f' stroke="{ACCENT}" stroke-width="1"' if today and d.date.date() == today else ""
            p.append(f'<rect x="{x}" y="{cy}" width="{CELL}" height="{CELL}" rx="2" fill="{bucket(d.count)}"{stroke}/>')
    ya = grid_top + 7*(CELL+GAP) + 22
    p.append(t(PAD_X, ya, "legend ·", fill=DIM, size=10))
    lx = PAD_X + 56
    for color, lbl in zip(HEAT, ["0","1-2","3-5","6-9","10+"]):
        p.append(f'<rect x="{lx}" y="{ya-9}" width="10" height="10" rx="2" fill="{color}"/>')
        p.append(t(lx+14, ya, lbl, fill=DIM, size=10))
        lx += 48
    yp = ya + 26
    p.append(t(PAD_X, yp, f"{login}@github", fill=ACCENT, size=13))
    p.append(t(po, yp, ":", fill=DIM, size=13))
    p.append(t(po+7, yp, "~", fill="#4a90e2", size=13))
    p.append(t(po+15, yp, "$", fill=DIM, size=13))
    p.append(f'<rect x="{po+27}" y="{yp-11}" width="8" height="13" fill="{ACCENT}">'
             f'<animate attributeName="opacity" values="1;1;0;0" dur="1.1s" repeatCount="indefinite"/></rect>')
    p.append("</svg>")
    return "\n".join(p)


def main():
    login = os.environ.get("GITHUB_LOGIN") or os.environ.get("GITHUB_REPOSITORY_OWNER")
    token = os.environ.get("GITHUB_TOKEN")
    if not login or not token:
        print("Set GITHUB_LOGIN and GITHUB_TOKEN.", file=sys.stderr)
        return 1
    total, days = fetch_contributions(login, token)
    svg = render_svg(login, total, days)
    out = Path("assets")
    out.mkdir(exist_ok=True)
    (out / "contrib-terminal.svg").write_text(svg, encoding="utf-8")
    print(f"Wrote assets/contrib-terminal.svg · {total} contributions · {len(days)} days")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
