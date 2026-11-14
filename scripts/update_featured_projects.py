#!/usr/bin/env python3
"""Update only the README projects grid between PROJECTS markers.

Selects public, non-fork, non-archived repos with topic `portfolio` or
`featured`, newest push first, max 6. Stdlib only (no pip).
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

USERNAME = "FrankUsqAbant"
README = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "README.md")
if not os.path.isfile(README):
    README = "README.md"

START = "<!-- PROJECTS:START -->"
END = "<!-- PROJECTS:END -->"
MAX_PROJECTS = 6
TIMEOUT = 8

# Friendly titles for the current grid; new repos fall back to a prettified name.
TITLES = {
    "abanto.dev": "Portafolio",
    "chavez-originals": "Chavez Originals",
    "jireh-pasteleria": "JIRÉH Pastelería",
    "hostal-aguilar": "Hostal Aguilar",
    "extracto": "Extracto",
    "kasa-nord": "Kasa Nord",
}

DEMO_HINTS = (
    "proyecto demo",
    "proyecto de práctica",
    "proyecto de practica",
    "web demo",
    "app de práctica",
    "app de practica",
    "landing de práctica",
    "landing de practica",
    "de práctica",
    "de practica",
    "ficticia",
    "ficticio",
)

BADGE_CODE = (
    "https://img.shields.io/badge/C%C3%B3digo-0B1220"
    "?style=for-the-badge&logo=github&logoColor=22D3EE"
)
BADGE_WEB = "https://img.shields.io/badge/Web-22D3EE?style=for-the-badge&logoColor=0B1220"


def token() -> str:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""


def api(path: str, params: dict | None = None) -> object:
    url = "https://api.github.com" + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "FrankUsqAbant-profile-readme",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    t = token()
    if t:
        headers["Authorization"] = f"Bearer {t}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.load(resp)


def head_ok(url: str, max_bytes: int = 250_000) -> bool:
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "FrankUsqAbant-profile-readme"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            if getattr(resp, "status", 200) >= 400:
                return False
            length = resp.headers.get("Content-Length")
            if length and int(length) > max_bytes:
                return False
            return True
    except Exception:
        return False


def sanitize_homepage(url: str | None) -> str | None:
    if not url:
        return None
    url = url.strip()
    if not url:
        return None
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    host = urllib.parse.urlparse(url).netloc.lower().split(":")[0]
    if host in {"abanto.dev", "www.abanto.dev"}:
        return "https://abanto.pages.dev"
    return url


def list_featured() -> list[dict]:
    seen: dict[str, dict] = {}
    page = 1
    while page <= 3:
        repos = api(
            f"/users/{USERNAME}/repos",
            {
                "type": "owner",
                "sort": "pushed",
                "direction": "desc",
                "per_page": 100,
                "page": page,
            },
        )
        if not isinstance(repos, list) or not repos:
            break
        for repo in repos:
            if repo.get("fork") or repo.get("archived") or repo.get("private"):
                continue
            topics = {t.lower() for t in (repo.get("topics") or [])}
            if "portfolio" not in topics and "featured" not in topics:
                continue
            seen[repo["name"]] = repo
        if len(repos) < 100:
            break
        page += 1
    selected = sorted(seen.values(), key=lambda r: r.get("pushed_at") or "", reverse=True)
    return selected[:MAX_PROJECTS]


def display_title(repo: dict) -> str:
    name = repo["name"]
    if name in TITLES:
        return TITLES[name]
    return name.replace("-", " ").replace("_", " ").title()


def card_description(repo: dict) -> str:
    name = repo["name"]
    text = (repo.get("description") or "").strip()
    if name == "abanto.dev":
        return text or "Mi sitio personal: proyectos, perfil y contacto."
    if not text:
        text = display_title(repo)
    low = text.lower()
    if not any(hint in low for hint in DEMO_HINTS):
        text = text.rstrip(".") + " · Proyecto demo"
    return text


def thumbnail(repo: dict) -> str:
    name = repo["name"]
    branch = repo.get("default_branch") or "main"
    for path in ("preview.png", "og.png", "docs/preview.png", "docs/og.png"):
        url = f"https://raw.githubusercontent.com/{USERNAME}/{name}/{branch}/{path}"
        if head_ok(url):
            return url
    here = os.path.dirname(os.path.abspath(README))
    for ext in ("webp", "jpg", "png"):
        rel = f"assets/projects/{name}.{ext}"
        if os.path.isfile(os.path.join(here, rel)):
            return rel
    return f"https://opengraph.githubassets.com/1/{USERNAME}/{name}"


def render_card(repo: dict) -> str:
    name = repo["name"]
    title = display_title(repo)
    desc = card_description(repo)
    repo_url = repo.get("html_url") or f"https://github.com/{USERNAME}/{name}"
    web = sanitize_homepage(repo.get("homepage"))
    thumb = thumbnail(repo)
    link = web or repo_url
    alt = html.escape(title if name == "abanto.dev" else f"{title}, proyecto demo")
    web_badge = ""
    if web:
        web_badge = (
            f'\n  <a href="{html.escape(web)}">'
            f'<img src="{BADGE_WEB}" alt="Web"></a>'
        )
    return f"""<td width="33%" align="center" valign="top">
  <a href="{html.escape(link)}">
    <img src="{html.escape(thumb)}" width="600" height="375" loading="lazy" alt="{alt}">
  </a>
  <br>
  <strong>{html.escape(title)}</strong>
  <br>
  <sub>{html.escape(desc)}</sub>
  <br><br>
  <a href="{html.escape(repo_url)}"><img src="{BADGE_CODE}" alt="Código"></a>{web_badge}
</td>"""


def render_grid(repos: list[dict]) -> str:
    if not repos:
        return "<sub>Aún no hay repositorios con el topic <code>portfolio</code>.</sub>\n"
    rows = []
    for i in range(0, len(repos), 3):
        chunk = repos[i : i + 3]
        cells = "\n".join(render_card(r) for r in chunk)
        # Pad so a short last row does not stretch a single card.
        missing = 3 - len(chunk)
        pads = "\n<td width=\"33%\"></td>" * missing
        rows.append(f"<tr>\n{cells}{pads}\n</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def inject(readme: str, grid: str) -> str:
    if START not in readme or END not in readme:
        raise SystemExit("README.md no tiene los marcadores PROJECTS:START / PROJECTS:END")
    block = f"{START}\n{grid}\n{END}"
    return re.sub(
        re.escape(START) + r".*?" + re.escape(END),
        lambda _: block,
        readme,
        count=1,
        flags=re.DOTALL,
    )


def main() -> int:
    if len(sys.argv) > 1:
        global README
        README = sys.argv[1]
    repos = list_featured()
    grid = render_grid(repos)
    with open(README, "r", encoding="utf-8") as f:
        original = f.read()
    updated = inject(original, grid)
    if updated == original:
        print("Sin cambios en la sección de proyectos.")
        return 0
    with open(README, "w", encoding="utf-8") as f:
        f.write(updated)
    names = ", ".join(r["name"] for r in repos) or "(ninguno)"
    print(f"README actualizado: {names}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
