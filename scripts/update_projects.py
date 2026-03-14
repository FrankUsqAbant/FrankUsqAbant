#!/usr/bin/env python3
"""
update_projects.py
==================
Auto-actualiza dos secciones del README.md:

  1. <!-- PROJECTS:START / END -->
     Busca todos tus repos públicos que tengan el topic "featured"
     y genera tarjetas HTML con imagen, descripción, lenguaje,
     botón de repo y botón de sitio live.

  2. <!-- LANGUAGES:START / END -->
     Recoge los lenguajes de TODOS tus repos públicos y actualiza
     los iconos de skillicons.dev automáticamente.

Uso:
    GITHUB_TOKEN=<tu_token> python scripts/update_projects.py
"""

import os
import re
import base64
import requests

# ── Config ─────────────────────────────────────────────────────────────────────
TOKEN    = os.environ.get("GITHUB_TOKEN", "")
USERNAME = "FrankUsqAbant"
README   = "README.md"

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}
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

# Herramientas fijas que siempre aparecen (aunque no sean "lenguajes")
FIXED_TOOLS = ["react", "nextjs", "tailwind", "sass",
               "figma", "git", "github", "vscode", "vercel", "notion"]


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
    """Reemplaza el contenido entre dos marcadores."""
    pattern = rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}"
    replacement = f"{start_marker}\n{new_content}\n{end_marker}"
    return re.sub(pattern, replacement, readme, flags=re.DOTALL)


# ── 1. Featured Projects ───────────────────────────────────────────────────────

def get_featured_repos():
    """Devuelve los repos con topic 'featured', o los más estrellados/recientes si no hay ninguno."""
    repos, page = [], 1
    featured_repos = []
    all_public_repos = []

    while True:
        url = (f"https://api.github.com/users/{USERNAME}/repos"
               f"?type=public&sort=updated&per_page=100&page={page}")
        data = get(url)
        if not data:
            break
        for repo in data:
            all_public_repos.append(repo)
            # Solo pedimos topics si estamos buscando destacados
            t = get(
                f"https://api.github.com/repos/{USERNAME}/{repo['name']}/topics",
                headers=HEADERS_TOPICS,
            )
            if "featured" in t.get("names", []):
                featured_repos.append(repo)
        page += 1
        if len(data) < 100:
            break
    
    if featured_repos:
        return featured_repos
    
    # Fallback: Top 6 repos públicos más recientes
    print("⚠️ No se encontraron repos con topic 'featured'. Seleccionando automáticos...")
    return all_public_repos[:6]


def fetch_readme_text(repo_name):
    """Descarga y decodifica el README de un repo."""
    try:
        data = get(f"https://api.github.com/repos/{USERNAME}/{repo_name}/readme")
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    except Exception:
        return ""


def to_absolute(url, repo_name, default_branch="main"):
    """Convierte URL relativa a raw.githubusercontent.com."""
    if url.startswith("http"):
        return url
    clean = url.lstrip("./")
    return f"https://raw.githubusercontent.com/{USERNAME}/{repo_name}/{default_branch}/{clean}"


def extract_image(readme_text, repo_name, branch="main"):
    """Extrae la imagen más representativa del README."""
    # Buscar patrones de imagen (Markdown o HTML)
    patterns = [
        r'<img[^>]+src=["\']([^"\']+)["\']',     # HTML img
        r'!\[[^\]]*\]\(([^)\s]+)'                  # Markdown img
    ]
    
    for p in patterns:
        matches = re.finditer(p, readme_text, re.IGNORECASE)
        for m in matches:
            img_url = m.group(1)
            # Ignorar insignias/badges comunes
            if any(x in img_url.lower() for x in ["img.shields.io", "badge", "skillicons.dev", "github-readme-stats"]):
                continue
            return to_absolute(img_url, repo_name, branch)
            
    # Fallback: imagen social de GitHub
    return f"https://opengraph.githubassets.com/1/{USERNAME}/{repo_name}"


def extract_live_url(readme_text, repo_homepage=None):
    """Encuentra el link live, priorizando el homepage del repo."""
    if repo_homepage and "github.com" not in repo_homepage:
        return repo_homepage

    # Patrón 1: texto tipo [Live Demo](https://...)
    p1 = re.compile(
        r'\[(?:[^\]]{0,40}(?:live|demo|sitio|ver|visit|web|página|page|despliegue)[^\]]{0,40})\]'
        r'\((https?://(?!github\.com)[^)]+)\)',
        re.IGNORECASE,
    )
    # Patrón 2: icono/palabra clave seguida de URL
    p2 = re.compile(
        r'(?:live demo|live site|ver sitio|demo|🌐|👉|deployed|desplegado en)[^\n]{0,60}'
        r'(https?://(?!github\.com)[^\s)"\']+)',
        re.IGNORECASE,
    )
    # Patrón 3: dominios conocidos de deploy
    p3 = re.compile(
        r'https?://[^\s<>"\']+\.(?:vercel\.app|netlify\.app|pages\.dev|github\.io)[^\s<>"\']*'
    )
    for pattern in (p1, p2):
        m = pattern.search(readme_text)
        if m:
            return m.group(1).rstrip(".,)")
    m = p3.search(readme_text)
    if m:
        return m.group(0).rstrip(".,)")
    return None


def lang_badge(language):
    """Genera un badge shields.io para el lenguaje."""
    if not language:
        return ""
    if ldef build_project_card(repo):
    """Genera el HTML de una tarjeta de proyecto Premium en Español v3."""
    name         = repo["name"]
    display      = name.replace("-", " ").replace("_", " ").title()
    description  = (repo.get("description") or "Sin descripción del proyecto.").replace('"', "'")
    if len(description) > 60:
        description = description[:57] + "..."
    
    language     = repo.get("language") or ""
    repo_url     = repo["html_url"]
    repo_homepage = repo.get("homepage")

    readme_text  = fetch_readme_text(name)
    image_url    = extract_image(readme_text, name)
    live_url     = extract_live_url(readme_text, repo_homepage)

    # Botones estilizados y compactos
    repo_btn = (
        f'<a href="{repo_url}">'
        f'<img src="https://img.shields.io/badge/Código-121212?style=for-the-badge&logo=github&logoColor=white" alt="Repo">'
        f'</a>'
    )
    
    live_btn = ""
    if live_url:
        live_btn = (
            f'&nbsp;&nbsp;'
            f'<a href="{live_url}">'
            f'<img src="https://img.shields.io/badge/Web-00d8ff?style=for-the-badge&logo=vercel&logoColor=black" alt="Web">'
            f'</a>'
        )

    # Usamos una cabecera más estable sin texto dinámico pesado para evitar broken images
    # El brillo (shimmer) se mantiene para la "iluminación"
    return f"""\
<td width="33.33%" align="center" valign="top">
<div style="border: 2px solid #00d8ff; border-radius: 15px; background: #0d1117; padding: 0 0 15px 0; overflow: hidden; margin: 5px;">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=00d8ff&height=40&section=header&reversal=true&animation=shimmer" width="100%" alt="shimmer">
  <br>
  <h4 align="center" style="margin: 5px 0;">{display}</h4>
  <a href="{live_url or repo_url}">
    <img src="{image_url}" width="90%" height="140px" style="border-radius:10px; object-fit: cover; border: 1px solid #30363d;" alt="{display}">
  </a>
  <br>
  <div style="height: 45px; overflow: hidden; padding: 0 10px;">
    <small>{description}</small>
  </div>
  <p align="center">
    {lang_badge(language)}
  </p>
  <hr style="border: 0.1px solid #30363d; margin: 10px;">
  <p align="center">
    {repo_btn}{live_btn}
  </p>
</div>
</td>"""


def generate_projects_html(repos):
    if not repos:
        return (
            '<p align="center">'
            '<em>No hay proyectos destacados aún.<br>'
            'Agrega el topic <code>featured</code> a tus repositorios de GitHub '
            'para que aparezcan aquí automáticamente.</em>'
            '</p>'
        )

    cards = [build_project_card(r) for r in repos]
    rows  = ""
    for i in range(0, len(cards), 3):
        chunk = cards[i:i+3]
        while len(chunk) < 3:
            chunk.append('<td width="33.33%"></td>')
        rows += "<tr>\n" + "\n".join(chunk) + "\n</tr>\n"

    return f'<table border="0" width="100%" cellpadding="0" cellspacing="15">\n{rows}</table>'


# ── 2. Language Icons ──────────────────────────────────────────────────────────

def get_all_languages():
    """Recolecta lenguajes únicos de todos los repos públicos."""
    try:
        data = get(
            f"https://api.github.com/users/{USERNAME}/repos"
            "?type=public&per_page=100"
        )
    except Exception:
        return []
    langs = set()
    for repo in data:
        lang = repo.get("language")
        if lang and lang in LANG_DATA:
            langs.add(LANG_DATA[lang][2])   # nombre en skillicons
    return sorted(langs)


def generate_languages_html():
    # Definición de categorías según la imagen del usuario
    categories = {
        "Frontend": ["html", "css", "js", "ts", "react", "nextjs", "tailwind", "sass", "redux", "vite", "figma"],
        "Backend": ["py", "nodejs", "mongodb"],
        "Tools": ["git", "github", "vscode", "vercel", "notion", "postman"]
    }
    
    html = '<table border="0" width="100%" cellpadding="0" cellspacing="20">\n<tr>\n'
    
    for title, icons in categories.items():
        icons_str = ",".join(icons)
        html += f"""\
<td width="33.33%" valign="top" align="center">
  <div style="background: #0d1117; border: 2px solid #30363d; border-radius: 12px; padding: 20px; min-height: 180px;">
    <h3 align="center" style="margin-top: 0; color: #00d8ff;">{title}</h3>
    <br>
    <p align="center">
      <img src="https://skillicons.dev/icons?i={icons_str}&perline=3&theme=dark" alt="{title}">
    </p>
  </div>
</td>
"""
    
    html += "</tr>\n</table>"
    return html
dding="0" cellspacing="10">\n<tr>\n'
    
    for title, icons in categories.items():
        icons_str = ",".join(icons)
        html += f"""\
<td width="33.33%" valign="top">
  <div style="background: #0d1117; border: 1px solid #30363d; border-radius: 10px; padding: 15px; height: 100%;">
    <h4 align="center" style="margin-top: 0; color: #00d8ff;">{title}</h4>
    <p align="center">
      <img src="https://skillicons.dev/icons?i={icons_str}&perline=4&theme=dark" alt="{title}">
    </p>
  </div>
</td>
"""
    
    html += "</tr>\n</table>"
    return html


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    readme = read_readme()

    # ── Proyectos
    print(f'🔍 Buscando repositorios para @{USERNAME}...')
    repos = get_featured_repos()
    print(f"✅ {len(repos)} repositorios encontrados.")
    projects_html = generate_projects_html(repos)
    readme = inject_section(readme, PROJ_START, PROJ_END, projects_html)

    # ── Lenguajes
    print("🎨 Actualizando tecnologías e iconos...")
    langs_html = generate_languages_html()
    readme = inject_section(readme, LANG_START, LANG_END, langs_html)

    write_readme(readme)
    print("🚀 README.md actualizado con éxito y localizado. ¡Todo listo!")
