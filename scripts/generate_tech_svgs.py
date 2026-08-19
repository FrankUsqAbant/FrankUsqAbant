#!/usr/bin/env python3
"""
generate_tech_svgs.py
=====================
Auto-detecta tecnologías desde los repos de GitHub del usuario y genera
un único SVG compacto (assets/tech-stack.svg) con iconos pequeños (48px)
y animaciones flotantes dinámicas.

Uso:
    # Con GitHub API (en GitHub Actions):
    GITHUB_TOKEN=<token> python scripts/generate_tech_svgs.py

    # Local con lista manual:
    python scripts/generate_tech_svgs.py --techs html,css,js,ts,react,py,nodejs
"""

import os
import re
import sys
import math
import json
import urllib.request

# ── Config ─────────────────────────────────────────────────────────────────────
USERNAME = os.environ.get("GITHUB_USERNAME", "FrankUsqAbant")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUTPUT = "assets/tech-stack.svg"

# ── Mapeos ─────────────────────────────────────────────────────────────────────
# Lenguaje de GitHub → slug de skillicons.dev
LANG_MAP = {
    "JavaScript": "js", "TypeScript": "ts", "Python": "py",
    "HTML": "html", "CSS": "css", "SCSS": "sass", "Sass": "sass",
    "Java": "java", "C": "c", "C++": "cpp", "C#": "cs",
    "Go": "go", "Rust": "rust", "Ruby": "ruby", "PHP": "php",
    "Swift": "swift", "Kotlin": "kotlin", "Dart": "dart",
    "Shell": "bash", "Lua": "lua", "R": "r", "Scala": "scala",
    "Perl": "perl", "Haskell": "haskell", "Elixir": "elixir",
    "Vue": "vue", "Svelte": "svelte", "Astro": "astro",
    "Dockerfile": "docker",
}

# Topic de GitHub → slug de skillicons.dev
TOPIC_MAP = {
    "react": "react", "reactjs": "react",
    "nextjs": "nextjs", "next-js": "nextjs", "next": "nextjs",
    "vuejs": "vue", "vue": "vue",
    "svelte": "svelte", "angular": "angular",
    "tailwindcss": "tailwind", "tailwind": "tailwind",
    "sass": "sass", "scss": "sass",
    "redux": "redux", "vite": "vite",
    "docker": "docker", "mongodb": "mongodb", "mongo": "mongodb",
    "postgresql": "postgres", "postgres": "postgres",
    "mysql": "mysql", "redis": "redis",
    "firebase": "firebase", "supabase": "supabase",
    "graphql": "graphql",
    "express": "express", "expressjs": "express",
    "django": "django", "flask": "flask",
    "spring": "spring", "laravel": "laravel",
    "figma": "figma", "vercel": "vercel", "netlify": "netlify",
    "astro": "astro", "electron": "electron",
    "webpack": "webpack", "pnpm": "pnpm",
    "threejs": "threejs", "three-js": "threejs",
    "prisma": "prisma", "jest": "jest",
    "cypress": "cypress", "styledcomponents": "styledcomponents",
    "materialui": "materialui",
}

# Si se detecta slug X → agregar también Y
INFER_MAP = {
    "js": ["nodejs"],
    "ts": ["nodejs"],
}

# Siempre agregar si el usuario tiene repos
ALWAYS_ADD = ["git", "github"]


# ── GitHub API ─────────────────────────────────────────────────────────────────

def github_get(url):
    """GET a la API de GitHub con autenticación opcional."""
    headers = {"User-Agent": "readme-tech-bot/1.0"}
    if TOKEN:
        headers["Authorization"] = f"token {TOKEN}"
        headers["Accept"] = "application/vnd.github.mercy-preview+json"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ⚠️ API error: {e}")
        return None


def detect_technologies():
    """Detecta tecnologías desde los repos públicos del usuario."""
    detected = set()
    page = 1

    while True:
        url = (f"https://api.github.com/users/{USERNAME}/repos"
               f"?type=public&per_page=100&page={page}")
        repos = github_get(url)
        if not repos:
            break

        for repo in repos:
            name = repo.get("name", "")
            if repo.get("fork"):
                continue

            # Lenguaje primario
            lang = repo.get("language")
            if lang and lang in LANG_MAP:
                detected.add(LANG_MAP[lang])

            # Todos los lenguajes del repo
            langs = github_get(
                f"https://api.github.com/repos/{USERNAME}/{name}/languages"
            )
            if langs:
                for l in langs:
                    if l in LANG_MAP:
                        detected.add(LANG_MAP[l])

            # Topics del repo
            topics = github_get(
                f"https://api.github.com/repos/{USERNAME}/{name}/topics"
            )
            if topics:
                for t in topics.get("names", []):
                    t_low = t.lower()
                    if t_low in TOPIC_MAP:
                        detected.add(TOPIC_MAP[t_low])

        page += 1
        if len(repos) < 100:
            break

    # Inferir herramientas asociadas
    for slug in list(detected):
        if slug in INFER_MAP:
            detected.update(INFER_MAP[slug])

    # Agregar herramientas universales
    if detected:
        detected.update(ALWAYS_ADD)

    return sorted(detected)


# ── Fetch & Parse de skillicons.dev ────────────────────────────────────────────

def fetch_skillicons_svg(slugs):
    """Descarga SVG con todos los iconos desde skillicons.dev (una sola fila)."""
    icons_str = ",".join(slugs)
    url = (f"https://skillicons.dev/icons"
           f"?i={icons_str}&perline={len(slugs)}&theme=dark")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse_icons(svg_content):
    """Extrae cada SVG de icono individual desde el SVG combinado de skillicons."""
    icons = []
    pos = 0
    while True:
        # Buscar bloque: <g transform="translate(...)"> ... </svg> ... </g>
        start = svg_content.find('<g transform="translate(', pos)
        if start == -1:
            break
        svg_start = svg_content.find('<svg', start)
        if svg_start == -1:
            break
        # Encontrar el cierre correcto (puede haber <svg> anidados)
        depth = 0
        search_pos = svg_start
        svg_end = -1
        while search_pos < len(svg_content):
            next_open = svg_content.find('<svg', search_pos + 1)
            next_close = svg_content.find('</svg>', search_pos + 1)
            if next_close == -1:
                break
            if next_open != -1 and next_open < next_close:
                depth += 1
                search_pos = next_open
            else:
                if depth == 0:
                    svg_end = next_close + 6  # len('</svg>')
                    break
                depth -= 1
                search_pos = next_close
        if svg_end == -1:
            break
        icon_svg = svg_content[svg_start:svg_end]
        icons.append(icon_svg)
        pos = svg_end
    return icons


# ── Generación del SVG unificado ───────────────────────────────────────────────

ANIMATION_CSS = """
      .ic {
        transform-origin: 24px 24px;
        transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), filter 0.2s ease;
        cursor: pointer;
      }
      svg:hover .ic {
        animation-duration: 1.2s !important;
      }
      .ic:hover {
        transform: scale(1.28) translateY(-4px) !important;
        filter: drop-shadow(0 0 10px #00d8ff) brightness(1.25);
      }

      @keyframes drift-a {
        0%, 100% { transform: translate(0,0) rotate(0deg) scale(1); }
        20% { transform: translate(6px,-8px) rotate(5deg) scale(1.05); }
        40% { transform: translate(-5px,3px) rotate(-4deg) scale(0.96); }
        60% { transform: translate(7px,6px) rotate(4deg) scale(1.04); }
        80% { transform: translate(-3px,-6px) rotate(-5deg) scale(0.97); }
      }
      @keyframes drift-b {
        0%, 100% { transform: translate(0,0) rotate(0deg) scale(1); }
        25% { transform: translate(-8px,5px) rotate(-6deg) scale(1.05); }
        50% { transform: translate(6px,-7px) rotate(4deg) scale(0.95); }
        75% { transform: translate(-4px,-5px) rotate(-3deg) scale(1.03); }
      }
      @keyframes drift-c {
        0%, 100% { transform: translate(0,0) rotate(0deg) scale(1); }
        30% { transform: translate(3px,-9px) rotate(6deg) scale(1.06); }
        60% { transform: translate(-3px,5px) rotate(-4deg) scale(0.95); }
      }
      @keyframes drift-d {
        0%, 100% { transform: translate(0,0) rotate(0deg) scale(1); }
        20% { transform: translate(8px,3px) rotate(-4deg) scale(1.03); }
        40% { transform: translate(-6px,-5px) rotate(5deg) scale(0.97); }
        60% { transform: translate(4px,7px) rotate(-3deg) scale(1.04); }
        80% { transform: translate(-7px,-2px) rotate(4deg) scale(0.96); }
      }
      @keyframes drift-e {
        0%, 100% { transform: translate(0,0) rotate(0deg) scale(1); }
        25% { transform: translate(-4px,8px) rotate(7deg) scale(1.05); }
        50% { transform: translate(7px,2px) rotate(-5deg) scale(0.96); }
        75% { transform: translate(2px,-7px) rotate(3deg) scale(1.02); }
      }
      @keyframes drift-f {
        0%, 100% { transform: translate(0,0) rotate(0deg) scale(1); }
        33% { transform: translate(-7px,-5px) rotate(-5deg) scale(1.04); }
        66% { transform: translate(5px,8px) rotate(4deg) scale(0.97); }
      }
"""

ANIM_NAMES = ["drift-a", "drift-b", "drift-c", "drift-d", "drift-e", "drift-f"]
BASE_DURATIONS = [3.0, 3.4, 3.8, 3.2, 3.6, 2.8]


def optimal_cols(n):
    """Calcula columnas óptimas para que la última fila esté balanceada."""
    if n <= 6:
        return n
    for c in range(min(n, 10), 3, -1):
        rows = math.ceil(n / c)
        last_row = n - (rows - 1) * c
        if last_row >= c * 0.4:
            return c
    return min(n, 6)


def build_unified_svg(icons):
    """Construye el SVG unificado con grid compacto y animaciones."""
    n = len(icons)
    if not n:
        return ('<svg viewBox="0 0 200 40" xmlns="http://www.w3.org/2000/svg">'
                '<text x="10" y="25" fill="#8b949e" font-size="14">'
                'No technologies detected</text></svg>')

    icon_size = 48
    gap = 14
    cell = icon_size + gap
    pad = 20
    cols = optimal_cols(n)
    rows = math.ceil(n / cols)

    vb_w = cols * cell - gap + pad * 2
    vb_h = rows * cell - gap + pad * 2

    # Generar CSS de animaciones por icono
    icon_css = ""
    for i in range(n):
        anim = ANIM_NAMES[i % len(ANIM_NAMES)]
        dur = BASE_DURATIONS[i % len(BASE_DURATIONS)] + (i * 0.13)
        delay = (i * 0.32) % 3.5
        icon_css += (f"      .ic-{i} {{ animation: {anim} {dur:.1f}s "
                     f"ease-in-out infinite; animation-delay: {delay:.2f}s; }}\n")

    # Construir los iconos posicionados
    icons_svg = ""
    for i, icon_svg in enumerate(icons):
        col = i % cols
        row_idx = i // cols

        # Centrar la última fila si tiene menos iconos
        items_in_row = min(cols, n - row_idx * cols)
        row_offset = (cols - items_in_row) * cell / 2

        x = pad + col * cell + row_offset
        y = pad + row_idx * cell

        # Redimensionar solo el tag <svg> raíz (no los <rect> internos)
        modified = re.sub(
            r'(<svg\b[^>]*?)\bwidth="256"',
            f'\\1width="{icon_size}"',
            icon_svg,
            count=1,
        )
        modified = re.sub(
            r'(<svg\b[^>]*?)\bheight="256"',
            f'\\1height="{icon_size}"',
            modified,
            count=1,
        )

        icons_svg += (f'  <g transform="translate({x:.0f},{y})">'
                      f'<g class="ic ic-{i}">'
                      f'{modified}'
                      f'</g></g>\n')

    half = icon_size // 2
    return f'''<svg viewBox="0 0 {vb_w} {vb_h}" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .ic {{ transform-origin: {half}px {half}px; }}
{ANIMATION_CSS}{icon_css}    </style>
  </defs>
{icons_svg}</svg>'''


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    # Opción: --techs html,css,js,...
    manual_techs = None
    for i, arg in enumerate(sys.argv):
        if arg == "--techs" and i + 1 < len(sys.argv):
            manual_techs = [s.strip() for s in sys.argv[i + 1].split(",") if s.strip()]

    if manual_techs:
        slugs = manual_techs
        print(f"📋 Usando lista manual: {', '.join(slugs)}")
    elif TOKEN:
        print(f"🔍 Detectando tecnologías de @{USERNAME} vía GitHub API...")
        slugs = detect_technologies()
        print(f"📦 Detectadas ({len(slugs)}): {', '.join(slugs)}")
    else:
        print("⚠️ Sin GITHUB_TOKEN ni --techs. Nada que generar.")
        print("   Uso: python scripts/generate_tech_svgs.py --techs html,css,js,ts")
        sys.exit(1)

    if not slugs:
        print("❌ No se detectaron tecnologías.")
        sys.exit(1)

    print(f"🎨 Descargando {len(slugs)} iconos desde skillicons.dev...")
    raw_svg = fetch_skillicons_svg(slugs)
    icons = parse_icons(raw_svg)

    if len(icons) != len(slugs):
        print(f"⚠️ Esperados {len(slugs)} iconos, obtenidos {len(icons)}")

    print(f"⚙️ Generando SVG unificado ({len(icons)} iconos)...")
    final_svg = build_unified_svg(icons)

    os.makedirs(os.path.dirname(OUTPUT) or ".", exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(final_svg)

    size_kb = len(final_svg) / 1024
    print(f"✅ Generado: {OUTPUT} ({len(icons)} iconos, {size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
