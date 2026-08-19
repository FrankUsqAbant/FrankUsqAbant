#!/usr/bin/env python3
"""
update_projects.py
==================
Auto-actualiza dos secciones del README.md:

  1. <!-- PROJECTS:START / END -->
     Busca repos públicos con topic "featured" (o los más recientes)
     y genera tarjetas HTML Premium compactas y estilizadas.

  2. <!-- LANGUAGES:START / END -->
     Categoriza herramientas en Frontend, Backend y Tools con diseño de cajas.

Uso:
    GITHUB_TOKEN=<tu_token> python scripts/update_projects.py
"""

import os
import re
import html
import base64
import requests
from urllib.parse import urlparse

# ── Config ─────────────────────────────────────────────────────────────────────
TOKEN    = os.environ.get("GITHUB_TOKEN", "")
USERNAME = "FrankUsqAbant"
README   = "README.md"

HEADERS = {
    "Accept": "application/vnd.github.v3+json",
}
if TOKEN:
    HEADERS["Authorization"] = f"token {TOKEN}"

HEADERS_TOPICS = {
    **HEADERS,
    "Accept": "application/vnd.github.mercy-preview+json",
}

# Marcadores en el README
PROJ_START = "<!-- PROJECTS:START -->"
PROJ_END   = "<!-- PROJECTS:END -->"
LANG_START = "<!-- LANGUAGES:START -->"
LANG_END   = "<!-- LANGUAGES:END -->"

# Mapeo: lenguaje GitHub → (color hex, nombre en shields.io logo, nombre en skillicons)
LANG_DATA = {
    "JavaScript": ("F7DF1E", "javascript",  "js"),
    "TypeScript": ("3178C6", "typescript",  "ts"),
    "Python":     ("3572A5", "python",      "py"),
    "HTML":       ("E34F26", "html5",       "html"),
    "CSS":        ("1572B6", "css3",        "css"),
    "Vue":        ("42B883", "vuedotjs",    "vue"),
    "Svelte":     ("FF3E00", "svelte",      "svelte"),
    "Go":         ("00ADD8", "go",          "go"),
    "Rust":       ("DEA584", "rust",        "rust"),
    "Swift":      ("FA7343", "swift",       "swift"),
    "Kotlin":     ("7F52FF", "kotlin",      "kotlin"),
    "Java":       ("007396", "java",        "java"),
    "PHP":        ("777BB4", "php",         "php"),
    "Ruby":       ("CC342D", "ruby",        "ruby"),
    "Dart":       ("00B4AB", "dart",        "dart"),
    "C":          ("A8B9CC", "c",           "c"),
    "C++":        ("00599C", "cplusplus",   "cpp"),
    "C#":         ("239120", "csharp",      "cs"),
    "Shell":      ("4EAA25", "gnubash",     "bash"),
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def get(url, headers=HEADERS):
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()

def read_readme():
    with open(README, "r", encoding="utf-8") as f:
        return f.read()

def write_readme(content):
    with open(README, "w", encoding="utf-8") as f:
        f.write(content)

def inject_section(readme, start_marker, end_marker, new_content):
    pattern = rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}"
    replacement = f"{start_marker}\n{new_content}\n{end_marker}"
    return re.sub(pattern, replacement, readme, flags=re.DOTALL)

# ── 1. Featured Projects ───────────────────────────────────────────────────────

def _repo_score(repo, readme_text, live_url):
    """Puntúa cada repo para decidir cuáles merecen estar en destacados."""
    score = 0
    has_desc = bool((repo.get("description") or "").strip())
    has_live = bool(live_url)
    has_image = bool(readme_text)  # si tiene README con contenido

    # Premios fuertes: descripción y demo online (lo que más valora el lector)
    if has_desc: score += 30
    if has_live:  score += 25
    if has_image: score += 5

    # Repos con estrellas o forks reciben bonus (indica interés real)
    score += min(repo.get("stargazers_count", 0), 10)
    score += min(repo.get("forks_count", 0), 5)

    # Bonus pequeño por tamaño (descarta proyectos vacíos de 1 archivo)
    size_kb = repo.get("size", 0)
    if size_kb > 50: score += 5
    if size_kb > 500: score += 3

    return score, has_desc, has_live

def get_featured_repos():
    """Devuelve los 6 mejores repos públicos para destacar de forma rápida y optimizada."""
    url = f"https://api.github.com/users/{USERNAME}/repos?type=public&sort=updated&per_page=30"
    try:
        repos = get(url, headers=HEADERS_TOPICS)
    except Exception:
        repos = []

    featured = []
    candidates = []
    EXCLUDE_NAMES = {USERNAME.lower(), "username.github.io", "frankusqabant"}

    for r in repos:
        name_lower = r["name"].lower()
        if name_lower in EXCLUDE_NAMES or r.get("fork"):
            continue
        topics = r.get("topics", [])
        if "featured" in topics:
            featured.append(r)
        else:
            candidates.append(r)

    if len(featured) >= 6:
        return featured[:6]

    # Completar con los más recientemente actualizados
    for c in candidates:
        if c not in featured:
            featured.append(c)
        if len(featured) == 6:
            break

    return featured[:6]
    TRIVIAL_HINTS = ("curso", "ejercicio", "starter", "template", "test", "demo",
                     "youtube-git", "scripts-main", "css-basico", "javascript")

    candidates = []
    for repo in all_public_repos:
        name_lower = repo["name"].lower()

        # Excluir el repo del README del perfil
        if name_lower in EXCLUDE_NAMES: continue
        # Excluir forks
        if repo.get("fork"): continue
        # Excluir candidatos triviales por nombre
        if any(hint in name_lower for hint in TRIVIAL_HINTS): continue

        # Precálculo de info del README (para puntuar y para build_project_card)
        readme_text = fetch_readme_text(repo["name"])
        live_url = extract_live_url(readme_text, repo.get("homepage"))
        score, has_desc, has_live = _repo_score(repo, readme_text, live_url)

        # Guardamos lo precalculado para no volver a pedirlo al construir la card
        repo["_readme_text"] = readme_text
        repo["_live_url"] = live_url
        repo["_score"] = score
        repo["_has_desc"] = has_desc
        repo["_has_live"] = has_live

        candidates.append(repo)

    # 3) Ordenar: primero por score, luego por fecha de actualización
    candidates.sort(key=lambda r: (r["_score"], r.get("updated_at", "")), reverse=True)

    # 4) Rotación: si hay más de 6 candidatos buenos, rotar para que varíen
    top = candidates[:6] if len(candidates) <= 6 else _rotate(candidates)

    # 5) Si sobran candidatos con baja calidad (sin descripción ni web),
    #    igual los incluimos para no tener menos de 6 tarjetas.
    if len(top) < 6:
        for c in candidates[6:]:
            if c not in top:
                top.append(c)
            if len(top) >= 6: break

    return top[:6]

def _rotate(candidates):
    """Rota los puestos 4-6 según el día del mes para que cada corrida
    del workflow muestre un conjunto distinto. Los 3 mejores siempre
    se mantienen fijos (son los más representativos)."""
    import datetime
    if len(candidates) <= 6:
        return candidates
    # Los 3 mejores siempre fijos
    fixed = candidates[:3]
    # Pool para rotar: del puesto 4 al 12
    pool = candidates[3:12]
    if len(pool) <= 3:
        return fixed + pool
    day = datetime.datetime.utcnow().day
    # Rotar 3 del pool cada ~5 días
    span = 3
    max_offset = len(pool) - span + 1
    offset = (day // 5) % max_offset
    return fixed + pool[offset:offset+span]

def fetch_readme_text(repo_name):
    try:
        data = get(f"https://api.github.com/repos/{USERNAME}/{repo_name}/readme")
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    except: return ""

def extract_image(readme_text, repo_name):
    patterns = [r'<img[^>]+src=["\']([^"\']+)["\']', r'!\[[^\]]*\]\(([^)\s]+)']
    for p in patterns:
        for m in re.finditer(p, readme_text, re.IGNORECASE):
            img_url = m.group(1)
            if any(x in img_url.lower() for x in ["img.shields.io", "badge", "skillicons.dev", "github-readme-stats"]): continue
            if img_url.startswith("http"): return img_url
            clean = img_url.lstrip("./")
            return f"https://raw.githubusercontent.com/{USERNAME}/{repo_name}/main/{clean}"
    return f"https://opengraph.githubassets.com/1/{USERNAME}/{repo_name}"

def extract_live_url(readme_text, repo_homepage=None):
    if repo_homepage and "github.com" not in repo_homepage:
        return repo_homepage.strip()
    # Excluir ] y ) del trailing para evitar capturar paréntesis/corchetes
    # rotos (bug del README de PredictorDePartidos que tenía ]( anidados)
    p3 = re.compile(r'https?://[^\s<>"\]\)]+\.(?:vercel\.app|netlify\.app|pages\.dev|github\.io)[^\s<>"\]\)]*')
    m = p3.search(readme_text)
    return m.group(0).rstrip(".,") if m else None

def lang_badge(language):
    if not language or language not in LANG_DATA: return ""
    color, logo, _ = LANG_DATA[language]
    return f'<img src="https://img.shields.io/badge/{language}-{color}?style=flat-square&logo={logo}&logoColor=white" alt="{language}">'

def _safe_url(url):
    """Valida que una URL sea http(s):// para prevenir inyección de
    esquemas peligrosos (javascript:, data:, vbscript:)."""
    if not url:
        return None
    try:
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            return url
    except Exception:
        pass
def build_project_card(repo, index=1):
    raw_name = repo["name"]
    display = html.escape(raw_name.replace("-", " ").replace("_", " ").title())
    
    readme_text = repo.get("_readme_text")
    if readme_text is None:
        readme_text = fetch_readme_text(raw_name)
    
    live_url = repo.get("_live_url")
    if live_url is None:
        live_url = extract_live_url(readme_text, repo.get("homepage"))
    live_url = _safe_url(live_url)
    repo_url = _safe_url(repo.get("html_url")) or f"https://github.com/{USERNAME}/{raw_name}"
    
    card_link = live_url or repo_url
    svg_filename = f"card-{index}.svg"
    
    repo_btn = f'<a href="{repo_url}"><img src="https://img.shields.io/badge/Código-121212?style=for-the-badge&logo=github&logoColor=white" alt="Repo"></a>'
    live_btn = f'&nbsp;&nbsp;<a href="{live_url}"><img src="https://img.shields.io/badge/Web-00d8ff?style=for-the-badge&logo=vercel&logoColor=black" alt="Web"></a>' if live_url else ""
    
    return f"""<td width="33.33%" align="center" valign="top">
  <a href="{card_link}" target="_blank">
    <img src="./assets/cards/{svg_filename}" width="100%" alt="{display}">
  </a>
  <p align="center" style="margin-top: 8px;">
    {repo_btn}{live_btn}
  </p>
</td>"""


def generate_projects_html(repos):
    try:
        import generate_cards
        generate_cards.generate_cards_from_repos(repos)
    except Exception as e:
        print(f"  ⚠️ Error en generate_cards: {e}")
        
    cards = [build_project_card(r, i + 1) for i, r in enumerate(repos)]
    rows = ""
    for i in range(0, len(cards), 3):
        chunk = cards[i:i+3]
        while len(chunk) < 3: chunk.append('<td width="33.33%"></td>')
        rows += "<tr>\n" + "\n".join(chunk) + "\n</tr>\n"
    return f'<table border="0" width="100%" cellpadding="0" cellspacing="15">\n{rows}</table>'

# ── 2. Language Icons ──────────────────────────────────────────────────────────

def generate_languages_html():
    return '''\
<div align="center">
  <div style="border: 2px solid #000000; border-radius: 15px; background: #0d1117; overflow: hidden; box-shadow: 0 0 12px rgba(0,0,0,0.8); display: inline-block; width: 100%;">
    <img src="./assets/shimmer-header.svg" width="100%" height="12" alt="shimmer">
    <div style="padding: 25px 20px;">
      <img src="./assets/tech-stack.svg" width="90%" alt="Tech Stack">
    </div>
  </div>
</div>'''

# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        readme = read_readme()
        print(f"🔍 Analizando perfil de @{USERNAME}...")
        
        repos = get_featured_repos()
        projects_html = generate_projects_html(repos)
        readme = inject_section(readme, PROJ_START, PROJ_END, projects_html)
        
        langs_html = generate_languages_html()
        readme = inject_section(readme, LANG_START, LANG_END, langs_html)
        
        write_readme(readme)
        print("🚀 Perfil actualizado correctamente.")
    except Exception as e:
        print(f"❌ Error: {e}")
