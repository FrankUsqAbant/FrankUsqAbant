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

def get_featured_repos():
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
            try:
                t = get(f"https://api.github.com/repos/{USERNAME}/{repo['name']}/topics", headers=HEADERS_TOPICS)
                if "featured" in t.get("names", []):
                    featured_repos.append(repo)
            except: pass
        page += 1
        if len(data) < 100: break
    
    return featured_repos if featured_repos else all_public_repos[:6]

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
    if repo_homepage and "github.com" not in repo_homepage: return repo_homepage
    p3 = re.compile(r'https?://[^\s<>"\']+\.(?:vercel\.app|netlify\.app|pages\.dev|github\.io)[^\s<>"\']*')
    m = p3.search(readme_text)
    return m.group(0).rstrip(".,)") if m else None

def lang_badge(language):
    if not language or language not in LANG_DATA: return ""
    color, logo, _ = LANG_DATA[language]
    return f'<img src="https://img.shields.io/badge/{language}-{color}?style=flat-square&logo={logo}&logoColor=white" alt="{language}">'

def build_project_card(repo):
    name, display = repo["name"], repo["name"].replace("-", " ").replace("_", " ").title()
    desc = (repo.get("description") or "Sin descripción del proyecto.").replace('"', "'")
    desc = desc[:57] + "..." if len(desc) > 60 else desc
    
    readme_text = fetch_readme_text(name)
    image_url = extract_image(readme_text, name)
    live_url = extract_live_url(readme_text, repo.get("homepage"))

    repo_btn = f'<a href="{repo["html_url"]}"><img src="https://img.shields.io/badge/Código-121212?style=for-the-badge&logo=github&logoColor=white" alt="Repo"></a>'
    live_btn = f'&nbsp;&nbsp;<a href="{live_url}"><img src="https://img.shields.io/badge/Web-00d8ff?style=for-the-badge&logo=vercel&logoColor=black" alt="Web"></a>' if live_url else ""

    return f"""\
<td width="33.33%" align="center" valign="top">
<div style="border: 2px solid #00d8ff; border-radius: 15px; background: #0d1117; padding: 0 0 15px 0; overflow: hidden; margin: 5px;">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=00d8ff&height=40&section=header&reversal=true&animation=shimmer" width="100%" alt="shimmer">
  <br>
  <h4 align="center" style="margin: 5px 0;">{display}</h4>
  <a href="{live_url or repo["html_url"]}">
    <img src="{image_url}" width="90%" height="140px" style="border-radius:10px; object-fit: cover; border: 1px solid #30363d;" alt="{display}">
  </a>
  <br>
  <div style="height: 45px; overflow: hidden; padding: 0 10px;">
    <small>{desc}</small>
  </div>
  <p align="center">{lang_badge(repo.get("language"))}</p>
  <hr style="border: 0.1px solid #30363d; margin: 10px;">
  <p align="center">{repo_btn}{live_btn}</p>
</div>
</td>"""

def generate_projects_html(repos):
    cards = [build_project_card(r) for r in repos]
    rows = ""
    for i in range(0, len(cards), 3):
        chunk = cards[i:i+3]
        while len(chunk) < 3: chunk.append('<td width="33.33%"></td>')
        rows += "<tr>\n" + "\n".join(chunk) + "\n</tr>\n"
    return f'<table border="0" width="100%" cellpadding="0" cellspacing="15">\n{rows}</table>'

# ── 2. Language Icons ──────────────────────────────────────────────────────────

def generate_languages_html():
    # Categorías con iluminación Premium
    categories = {
        "🎨 FRONTEND": ["html", "css", "js", "ts", "react", "nextjs", "tailwind", "sass", "redux", "vite", "figma"],
        "⚙️ BACKEND": ["py", "nodejs", "mongodb"],
        "🛠️ TOOLS": ["git", "github", "vscode", "vercel", "notion", "postman"]
    }
    
    html = '<table border="0" width="100%" cellpadding="0" cellspacing="15">\n<tr>\n'
    
    for title, icons in categories.items():
        icons_str = ",".join(icons)
        html += f"""\
<td width="33.33%" valign="top">
  <div style="border: 2px solid #00d8ff; border-radius: 15px; background: #0d1117; overflow: hidden; height: 100%;">
    <img src="https://capsule-render.vercel.app/api?type=waving&color=00d8ff&height=40&section=header&reversal=true&animation=shimmer&text={title.split()[-1]}&fontSize=18&fontAlignY=60" width="100%" alt="light">
    <div style="padding: 15px; text-align: center;">
      <p align="center" style="color: #00d8ff; margin-bottom: 10px;"><strong>{title}</strong></p>
      <img src="https://skillicons.dev/icons?i={icons_str}&perline=3&theme=dark" alt="icons">
    </div>
  </div>
</td>
"""
    
    html += "</tr>\n</table>"
    return html

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
