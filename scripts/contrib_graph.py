"""
Gráfico de contribuições do último ano, no estilo dos cartões do README.

Busca o calendário de contribuições na API GraphQL do GitHub e desenha
dois SVGs (tema claro e escuro) em roxo, combinando com os cartões do
github-cool-readme.

Uso:
    GITHUB_TOKEN=... python scripts/contrib_graph.py --user TiagoRodriguesskt --out cards
    python scripts/contrib_graph.py --sample --out preview   # dados de exemplo, sem token

Gera: contributions-light.svg e contributions-dark.svg
"""
import argparse
import json
import os
import random
import urllib.request
from datetime import date, timedelta
from pathlib import Path

# ---------------------------------------------------------------- aparência
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"

THEMES = {
    # mesmas cores do color: purple do github-cool-readme
    "light": {
        "text": "#1f2328", "muted": "#818b98", "accent": "#8250df",
        "levels": ["#eff2f5", "#d8b9ff", "#a475f9", "#6639ba", "#4c2889"],
    },
    "dark": {
        "text": "#f0f6fc", "muted": "#7d8590", "accent": "#a371f7",
        "levels": ["#151b23", "#2e1a4f", "#553098", "#8957e5", "#c297ff"],
    },
}

MONTHS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
WEEKDAYS = {1: "Seg", 3: "Qua", 5: "Sex"}       # domingo = 0, como no GitHub
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
          "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

CELL, GAP = 12, 3                 # quadrado e espaço entre eles
STEP = CELL + GAP
WIDTH, HEIGHT = 900, 255          # viewBox; no README é mostrado com width="808"
LEFT, TOP = 58, 106                # onde começa a grade


# ---------------------------------------------------------------- dados
QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}
"""


def fetch(user: str, token: str) -> dict:
    """Calendário do último ano: {'total': int, 'weeks': [[(date, count, level), ...], ...]}."""
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if "errors" in data:
        raise SystemExit(f"Erro da API: {data['errors']}")
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [
        [(date.fromisoformat(d["date"]), d["contributionCount"], LEVELS[d["contributionLevel"]])
         for d in w["contributionDays"]]
        for w in cal["weeks"]
    ]
    return {"total": cal["totalContributions"], "weeks": weeks}


def sample() -> dict:
    """Dados inventados, só para ver a aparência."""
    rnd = random.Random(7)
    today = date.today()
    start = today - timedelta(days=364)
    start -= timedelta(days=(start.weekday() + 1) % 7)       # volta até um domingo
    weeks, week, total = [], [], 0
    d = start
    while d <= today:
        n = rnd.choice([0] * 12 + [1, 1, 2, 3, 5, 8])
        level = 0 if n == 0 else 1 if n < 2 else 2 if n < 4 else 3 if n < 7 else 4
        week.append((d, n, level))
        total += n
        if len(week) == 7:
            weeks.append(week)
            week = []
        d += timedelta(days=1)
    if week:
        weeks.append(week)
    return {"total": total, "weeks": weeks}


# ---------------------------------------------------------------- desenho
def svg(cal: dict, theme: str) -> str:
    t = THEMES[theme]
    weeks = cal["weeks"]
    total = cal["total"]
    parts = []

    # cabeçalho, no mesmo estilo dos cartões
    parts.append(f'<text x="{LEFT - 30}" y="30" class="col">CONTRIBUIÇÕES · CONTRIBUTIONS</text>')
    parts.append(
        f'<text x="{LEFT - 30}" y="62" class="big"><tspan fill="{t["accent"]}">{total}</tspan>'
        f' contribuições no último ano</text>'
    )

    # meses: o rótulo fica na semana em que o mês começa
    labels = []
    for i, week in enumerate(weeks):
        month = week[0][0].month if i == 0 else next((d.month for d, _, _ in week if d.day == 1), None)
        if month:
            labels.append((i, month))
    if len(labels) > 1 and labels[1][0] - labels[0][0] < 3:
        labels.pop(0)                      # mês incompleto no início: some, como no GitHub
    for i, month in labels:
        parts.append(f'<text x="{LEFT + i * STEP}" y="{TOP - 9}" class="small muted">{MONTHS[month - 1]}</text>')

    # dias da semana
    for wd, name in WEEKDAYS.items():
        y = TOP + wd * STEP + CELL - 2
        parts.append(f'<text x="{LEFT - 30}" y="{y}" class="small muted">{name}</text>')

    # quadrados, entrando coluna por coluna
    for i, week in enumerate(weeks):
        cells = []
        for d, n, level in week:
            wd = (d.weekday() + 1) % 7
            plural = "contribuição" if n == 1 else "contribuições"
            cells.append(
                f'<rect x="{LEFT + i * STEP}" y="{TOP + wd * STEP}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{t["levels"][level]}"><title>{n} {plural} em {d.strftime("%d/%m/%Y")}</title></rect>'
            )
        parts.append(f'<g class="w" style="animation-delay:{i * 12}ms">{"".join(cells)}</g>')

    # legenda
    ly = TOP + 7 * STEP + 14
    lx = LEFT + len(weeks) * STEP - 5 * STEP - 6
    parts.append(f'<text x="{lx - 8}" y="{ly + CELL - 2}" class="small muted" text-anchor="end">Menos</text>')
    for k, colour in enumerate(t["levels"]):
        parts.append(f'<rect x="{lx + k * STEP}" y="{ly}" width="{CELL}" height="{CELL}" rx="2" fill="{colour}"/>')
    parts.append(f'<text x="{lx + 5 * STEP + 5}" y="{ly + CELL - 2}" class="small muted">Mais</text>')

    body = "\n".join(parts)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" fill="none" role="img" aria-labelledby="title">
<title id="title">{total} contribuições no último ano</title>
<style>
  text {{ font-family: {FONT}; fill: {t["text"]}; }}
  .col {{ font-size: 12px; fill: {t["muted"]}; letter-spacing: 0.04em; }}
  .big {{ font-size: 22px; font-weight: 600; }}
  .small {{ font-size: 12px; }}
  .muted {{ fill: {t["muted"]}; }}
  .w {{ animation: entra 0.5s ease-out both; }}
  @keyframes entra {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
  @media (prefers-reduced-motion: reduce) {{ .w {{ animation: none; }} }}
</style>
{body}
</svg>
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--user", default="TiagoRodriguesskt")
    ap.add_argument("--out", default="cards")
    ap.add_argument("--sample", action="store_true", help="usar dados de exemplo (sem token)")
    args = ap.parse_args()

    if args.sample:
        cal = sample()
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise SystemExit("Defina GITHUB_TOKEN (ou use --sample).")
        cal = fetch(args.user, token)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        (out / f"contributions-{theme}.svg").write_text(svg(cal, theme), encoding="utf-8")
    print(f"{cal['total']} contribuições -> {out}/contributions-light.svg e contributions-dark.svg")


if __name__ == "__main__":
    main()
