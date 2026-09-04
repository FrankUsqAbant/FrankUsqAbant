#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_projects.py
==================
Auto-actualiza las secciones de proyectos destacados y tecnologías en el README.md:

1. <!-- PROJECTS:START / END -->
   - Busca repositorios públicos.
   - REGLA CLAVE: Si el repositorio NO tiene imagen válida, se ignora por completo.
   - Extrae la imagen directa (priorizando formato .webp para máxima ligereza y velocidad).
   - Extrae el demo en vivo (GitHub Pages, Vercel, Netlify, etc.) y descripción.
   - Genera tarjetas limpias, rápidas y nítidas directamente en el README.

2. <!-- LANGUAGES:START / END -->
   - Muestra la sección de tecnologías.
"""

import os
import sys
import re
import html
import base64
import requests
from urllib.parse import urlparse

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

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

PROJ_START = "<!-- PROJECTS:START -->"
PROJ_END   = "<!-- PROJECTS:END -->"
LANG_START = "<!-- LANGUAGES:START -->"
LANG_END   = "<!-- LANGUAGES:END -->"

EXCLUDE_NAMES = {USERNAME.lower(), "username.github.io", "frankusqabant", "frankusqabant.github.io"}

# ── Helpers ────────────────────────────────────────────────────────────────────

def get(url, headers=HEADERS):
    r = requests.get(url, headers=headers, timeout=12)
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

def _safe_url(url):
    if not url:
        return None
    try:
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            return url
    except Exception:
        pass
    return None

def fetch_readme_text(repo_name):
    try:
        data = get(f"https://api.github.com/repos/{USERNAME}/{repo_name}/readme")
        return base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
    except Exception:
        return ""

def extract_image(readme_text, repo_name, default_branch="main"):
    """
    Busca una imagen válida en el README o en rutas conocidas del repositorio.
    Prioriza imágenes .webp para que la carga sea rápida y ligera.
    Si no encuentra ninguna imagen real, retorna None (se ignora el repositorio).
    """
    imgs = []
    
    # 1. Buscar en markdown ![alt](url)
    for m in re.finditer(r'!\[[^\]]*\]\(([^)\s]+)\)', readme_text):
        u = m.group(1).strip()
        if not any(x in u.lower() for x in ['shields.io', 'badge', 'skillicons', 'github-readme-stats', 'simpleicons', 'komarev', 'readme-typing-svg', 'travis-ci', 'qrserver.com', 'api.iconify.design']):
            imgs.append(u)

    # 2. Buscar en HTML <img src='url'>
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', readme_text, re.IGNORECASE):
        u = m.group(1).strip()
        if not any(x in u.lower() for x in ['shields.io', 'badge', 'skillicons', 'github-readme-stats', 'simpleicons', 'komarev', 'readme-typing-svg', 'travis-ci', 'qrserver.com', 'api.iconify.design']):
            imgs.append(u)

    # Priorizar imágenes que tengan extensión .webp
    webp_imgs = [i for i in imgs if '.webp' in i.lower()]
    other_imgs = [i for i in imgs if not '.webp' in i.lower()]
    candidates = webp_imgs + other_imgs

    for cand in candidates:
        cand = cand.strip().strip("'\"")
        if cand.startswith("http://") or cand.startswith("https://"):
            return cand
        clean = cand.lstrip("./")
        return f"https://raw.githubusercontent.com/{USERNAME}/{repo_name}/{default_branch}/{clean}"

    # 3. Revisar rutas estándar de preview si no se encontró en el README
    for path in ['img/preview.webp', 'preview.webp', 'docs/preview.webp', 'assets/preview.webp', 'imagenes/readme/preview-vertice.webp']:
        test_url = f"https://raw.githubusercontent.com/{USERNAME}/{repo_name}/{default_branch}/{path}"
        try:
            r = requests.head(test_url, timeout=4)
            if r.status_code == 200:
                return test_url
        except Exception:
            pass

    return None

def extract_live_url(readme_text, repo_name, homepage=None):
    if homepage and "github.com" not in homepage:
        return homepage.strip()
    
    # Buscar en README URLs a GitHub Pages, Vercel o Netlify
    p = re.compile(r'https?://[^\s<>"\]\)]+\.(?:github\.io/[^\s<>"\]\)]*|vercel\.app[^\s<>"\]\)]*|netlify\.app[^\s<>"\]\)]*)')
    m = p.search(readme_text)
    if m:
        return m.group(0).rstrip(".,)\"]")
    
    # Probar si el repositorio tiene GitHub Pages por convención
    gh_pages = f"https://{USERNAME.lower()}.github.io/{repo_name}/"
    try:
        r = requests.head(gh_pages, timeout=3)
        if r.status_code == 200:
            return gh_pages
    except Exception:
        pass

    return None

# ── Selección de Proyectos ─────────────────────────────────────────────────────

VERIFIED_FALLBACK = [
    {
        "name": "parallax",
        "title": "Parallax Experience",
        "desc": "Experiencia visual interactiva con efecto parallax a 60+ FPS impulsada por Lax.js.",
        "image_url": "https://raw.githubusercontent.com/FrankUsqAbant/parallax/master/img/preview.webp",
        "repo_url": "https://github.com/FrankUsqAbant/parallax",
        "live_url": "https://frankusqabant.github.io/parallax/",
    },
    {
        "name": "vertice-moda",
        "title": "Vértice Moda",
        "desc": "Moda masculina contemporánea. Sitio web premium dark-theme con acentos cobre.",
        "image_url": "https://raw.githubusercontent.com/FrankUsqAbant/vertice-moda/main/imagenes/readme/preview-vertice.webp",
        "repo_url": "https://github.com/FrankUsqAbant/vertice-moda",
        "live_url": "https://frankusqabant.github.io/vertice-moda/",
    },
    {
        "name": "OpenGravity",
        "title": "OpenGravity Bot",
        "desc": "Proyecto de bot inteligente para Telegram con arquitectura moderna y asíncrona.",
        "image_url": "https://raw.githubusercontent.com/FrankUsqAbant/OpenGravity/main/docs/preview.webp",
        "repo_url": "https://github.com/FrankUsqAbant/OpenGravity",
        "live_url": "https://frankusqabant.github.io/OpenGravity/",
    },
    {
        "name": "PokeAPI",
        "title": "PokeAPI Explorer",
        "desc": "Pokedex interactiva consumiendo PokeAPI con búsqueda en tiempo real.",
        "image_url": "https://raw.githubusercontent.com/FrankUsqAbant/PokeAPI/main/img/preview.webp",
        "repo_url": "https://github.com/FrankUsqAbant/PokeAPI",
        "live_url": "https://frankusqabant.github.io/PokeAPI/",
    },
    {
        "name": "Portafolio-Frank-Abanto",
        "title": "Portafolio Web",
        "desc": "Portafolio interactivo, limpio y minimalista desarrollado en HTML, CSS y JavaScript.",
        "image_url": "https://raw.githubusercontent.com/FrankUsqAbant/Portafolio-Frank-Abanto/main/assets/preview.webp",
        "repo_url": "https://github.com/FrankUsqAbant/Portafolio-Frank-Abanto",
        "live_url": "https://frankusqabant.github.io/Portafolio-Frank-Abanto/",
    },
    {
        "name": "astro-sitio-web",
        "title": "Astro Sitio Web",
        "desc": "Sitio web moderno desarrollado con Astro Framework y componentes de alto rendimiento.",
        "image_url": "https://raw.githubusercontent.com/FrankUsqAbant/astro-sitio-web/main/Readmee.png",
        "repo_url": "https://github.com/FrankUsqAbant/astro-sitio-web",
        "live_url": "https://frankusqabant.github.io/astro-sitio-web/",
    }
]

def get_qualified_projects():
    """
    Obtiene los repositorios del usuario y filtra únicamente los que
    cumplen con tener una imagen válida (priorizando .webp).
    """
    url = f"https://api.github.com/users/{USERNAME}/repos?type=public&sort=updated&per_page=40"
    try:
        repos = get(url, headers=HEADERS_TOPICS)
    except Exception as e:
        print(f"⚠️ Aviso: API GitHub en límite o sin token ({e}). Usando proyectos verificados.")
        return VERIFIED_FALLBACK[:6]

    qualified = []

    for r in repos:
        name = r.get("name", "")
        name_lower = name.lower()

        # Exclusiones
        if name_lower in EXCLUDE_NAMES or r.get("fork"):
            continue

        branch = r.get("default_branch", "main")
        readme_text = fetch_readme_text(name)

        # 1. VERIFICAR IMAGEN: Si no tiene imagen, se ignora el repo
        image_url = extract_image(readme_text, name, branch)
        if not image_url:
            print(f"  ⏩ Ignorado (sin imagen): {name}")
            continue

        # 2. Obtener Demo en vivo y Descripción
        live_url = extract_live_url(readme_text, name, r.get("homepage"))
        desc = (r.get("description") or "").strip()
        if not desc:
            # Buscar una frase corta del README si no hay descripción en el repo
            for line in readme_text.splitlines():
                clean_line = line.strip().lstrip("#*- ").strip()
                if len(clean_line) > 15 and not clean_line.startswith("<") and not clean_line.startswith("!"):
                    desc = clean_line[:110] + "..."
                    break
        if not desc:
            desc = "Proyecto de desarrollo web moderno y de alto rendimiento."

        topics = r.get("topics", [])
        is_featured = "featured" in topics
        is_webp = ".webp" in image_url.lower()

        qualified.append({
            "name": name,
            "title": name.replace("-", " ").replace("_", " ").title(),
            "desc": desc,
            "image_url": image_url,
            "repo_url": r.get("html_url") or f"https://github.com/{USERNAME}/{name}",
            "live_url": live_url,
            "is_featured": is_featured,
            "is_webp": is_webp,
            "updated_at": r.get("updated_at", "")
        })

        print(f"  ✅ Calificado: {name} (WebP: {is_webp}, Demo: {bool(live_url)})")

        if len(qualified) >= 6:
            break

    return qualified[:6]

# ── Generación de HTML ─────────────────────────────────────────────────────────

def build_project_card(p):
    display = html.escape(p["title"])
    desc = html.escape(p["desc"])
    card_link = p["live_url"] or p["repo_url"]
    repo_url = p["repo_url"]
    live_url = p["live_url"]
    img_url = p["image_url"]

    repo_btn = f'<a href="{repo_url}"><img src="https://img.shields.io/badge/C%C3%B3digo-121212?style=for-the-badge&logo=github&logoColor=white" alt="Repo" loading="lazy"></a>'
    live_btn = f'&nbsp;&nbsp;<a href="{live_url}"><img src="https://img.shields.io/badge/Web-00d8ff?style=for-the-badge&logo=vercel&logoColor=black" alt="Web" loading="lazy"></a>' if live_url else ""

    return f"""<td width="33.33%" align="center" valign="top" style="word-break: break-word;">
  <a href="{card_link}" target="_blank">
    <img src="{img_url}" width="100%" alt="{display}" loading="lazy" decoding="async" style="width: 100%; height: auto; max-height: 175px; object-fit: cover; border-radius: 10px; display: block;">
  </a>
  <p align="center" style="margin-top: 8px; margin-bottom: 4px;">
    <strong>{display}</strong>
  </p>
  <p align="center" style="margin-top: 0; margin-bottom: 10px;">
    <sub>{desc}</sub>
  </p>
  <p align="center" style="margin-top: 4px; margin-bottom: 0;">
    {repo_btn}{live_btn}
  </p>
</td>"""

def generate_projects_html(projects):
    if not projects:
        return "<p align='center'><em>No se encontraron proyectos destacados con imagen.</em></p>"

    cards = [build_project_card(p) for p in projects]
    rows = ""
    for i in range(0, len(cards), 3):
        chunk = cards[i:i+3]
        while len(chunk) < 3:
            chunk.append('<td width="33.33%"></td>')
        rows += "<tr>\n" + "\n".join(chunk) + "\n</tr>\n"
    return f'<table border="0" width="100%" cellpadding="0" cellspacing="10" style="table-layout: fixed; width: 100%;">\n{rows}</table>'

def generate_languages_html():
    return '''<div align="center">
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
        
        projects = get_qualified_projects()
        print(f"📦 Total de proyectos destacados seleccionados: {len(projects)}")
        
        projects_html = generate_projects_html(projects)
        readme = inject_section(readme, PROJ_START, PROJ_END, projects_html)
        
        langs_html = generate_languages_html()
        readme = inject_section(readme, LANG_START, LANG_END, langs_html)
        
        write_readme(readme)
        print("🚀 README.md actualizado con éxito con imágenes directas y optimizadas.")
    except Exception as e:
        print(f"❌ Error: {e}")
