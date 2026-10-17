"""Builds assets/heatmap.svg from real GitHub contribution data (GraphQL API).
Needs env GITHUB_TOKEN and LOGIN. No data is invented; the token is never written to any file."""
import json, os, sys, urllib.request
from datetime import date

QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
totalContributions weeks{contributionDays{date contributionCount contributionLevel weekday}}}}}}"""
COLORS = {"NONE": "#2A1520", "FIRST_QUARTILE": "#701A3D", "SECOND_QUARTILE": "#9A4A6B",
          "THIRD_QUARTILE": "#C77B9B", "FOURTH_QUARTILE": "#E5B5C7"}

def fetch(login, token):
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "heatmap-script"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data: sys.exit(str(data["errors"]))
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

def render(cal, login):
    cell, gap, left, top = 12, 3, 40, 52
    weeks = cal["weeks"]
    W = left + len(weeks) * (cell + gap) + 24
    H = top + 7 * (cell + gap) + 52
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="ie-heat-t">',
         f'<title id="ie-heat-t">GitHub contributions for {login}: {cal["totalContributions"]} in the last year</title>',
         f'<rect width="{W}" height="{H}" rx="14" fill="#190B12" stroke="#451126"/>',
         f'<text x="24" y="32" font-family="Georgia,serif" font-size="16" fill="#E5B5C7">{cal["totalContributions"]} contributions in the last year</text>']
    last_m = None
    for i, w in enumerate(weeks):
        x = left + i * (cell + gap)
        m = w["contributionDays"][0]["date"][5:7]
        if m != last_m:
            name = date(2000, int(m), 1).strftime("%b")
            o.append(f'<text x="{x}" y="{top-8}" font-family="Courier New,monospace" font-size="10" fill="#C77B9B">{name}</text>')
            last_m = m
        for d in w["contributionDays"]:
            y = top + d["weekday"] * (cell + gap)
            c = COLORS.get(d["contributionLevel"], COLORS["NONE"])
            o.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{c}"><title>{d["date"]}: {d["contributionCount"]}</title></rect>')
    for i, lab in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        o.append(f'<text x="8" y="{top + i*(cell+gap) + 10}" font-family="Courier New,monospace" font-size="10" fill="#C77B9B">{lab}</text>')
    ly = H - 22
    o.append(f'<text x="{W-232}" y="{ly+9}" font-family="Courier New,monospace" font-size="10" fill="#C77B9B">Less</text>')
    for i, k in enumerate(COLORS):
        o.append(f'<rect x="{W-196+i*18}" y="{ly}" width="12" height="12" rx="3" fill="{COLORS[k]}"/>')
    o.append(f'<text x="{W-100}" y="{ly+9}" font-family="Courier New,monospace" font-size="10" fill="#C77B9B">More</text>')
    o.append('</svg>')
    return "\n".join(o) + "\n"

if __name__ == "__main__":
    login, token = os.environ["LOGIN"], os.environ["GITHUB_TOKEN"]
    out = os.environ.get("OUT", "assets/heatmap.svg")
    open(out, "w", encoding="utf-8").write(render(fetch(login, token), login))
    print("wrote", out)
