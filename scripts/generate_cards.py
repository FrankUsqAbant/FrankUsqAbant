#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_cards.py
==================
Generador de Tarjetas SVG Premium Ultra-Ligeras (<15KB) para GitHub README.
Diseño Estático Profesional, Rápido y Nítido:
- Marco negro puro (#000000) con acento cyan superior.
- Nombre del proyecto en grande.
- Imagen del proyecto nítida con esquinas redondeadas.
- Pequeño resumen descriptivo limpio.
- Botones de acción directa (Código y Web).
"""

import os
import io
import re
import html
import base64
import requests
from PIL import Image
from urllib.parse import urlparse

OUTPUT_DIR = "assets/cards"
USERNAME = "FrankUsqAbant"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

HEADERS = {"Accept": "application/vnd.github.v3+json"}
if TOKEN:
    HEADERS["Authorization"] = f"token {TOKEN}"

DEFAULT_PROJECTS = [
    {
        "id": "card-1",
        "title": "Astro Sitio Web",
        "desc": "Sitio web moderno de alto rendimiento optimizado con Astro Framework y arquitectura por componentes.",
        "image_url": "https://raw.githubusercontent.com/FrankUsqAbant/astro-sitio-web/main/Readmee.png",
        "repo_url": "https://github.com/FrankUsqAbant/astro-sitio-web",
        "live_url": "https://frankusqabant.github.io/astro-sitio-web/"
    },
    {
        "id": "card-2",
        "title": "Pagina Maquetacion Cv",
        "desc": "Maquetación profesional de currículum interactivo con diseño responsive, limpio y estructurado.",
        "image_url": "https://user-images.githubusercontent.com/90288287/167520099-5f4d7a65-5cd2-49bf-848e-f17bbbf4f085.png",
        "repo_url": "https://github.com/FrankUsqAbant/pagina-maquetacion-cv",
        "live_url": "https://frankusqabant.github.io/pagina-maquetacion-cv/"
    },
    {
        "id": "card-3",
        "title": "Simple Yoga Elite",
        "desc": "Santuario de Yoga Elite: Plataforma interactiva de bienestar con experiencia visual inmersiva.",
        "image_url": "https://raw.githubusercontent.com/FrankUsqAbant/simple-yoga-elite/main/protocol-aurora/public/hero_meditation.png",
        "repo_url": "https://github.com/FrankUsqAbant/simple-yoga-elite",
        "live_url": "https://simple-yoga-elite.netlify.app/"
    },
    {
        "id": "card-4",
        "title": "Frankusqabant.Github.Io",
        "desc": "Tarjeta digital interactiva con enlaces directos a proyectos, redes y perfil profesional.",
        "image_url": "https://raw.githubusercontent.com/FrankUsqAbant/astro-sitio-web/main/Readmee.png",
        "repo_url": "https://github.com/FrankUsqAbant/FrankUsqAbant.github.io",
        "live_url": "https://frankusqabant.github.io"
    },
    {
        "id": "card-5",
        "title": "Frank Taller Maquetacion",
        "desc": "Colección de componentes y experimentos de maquetación avanzada en CSS moderno.",
        "image_url": "https://opengraph.githubassets.com/1/FrankUsqAbant/frank-taller-maquetacion",
        "repo_url": "https://github.com/FrankUsqAbant/frank-taller-maquetacion",
        "live_url": "https://FrankUsqAbant.github.io/frank-taller-maquetacion/portafolio"
    },
    {
        "id": "card-6",
        "title": "Nexus Ascii Generator",
        "desc": "Generador de arte ASCII y banners estilizados para terminales y personalización.",
        "image_url": "https://raw.githubusercontent.com/FrankUsqAbant/NEXUS-ASCII-Generator/main/Pantalla.png",
        "repo_url": "https://github.com/FrankUsqAbant/NEXUS-ASCII-Generator",
        "live_url": "https://frankusqabant.github.io/NEXUS-ASCII-Generator/"
    }
]

def get_image_data_uri(img_source):
    """Descarga y comprime la imagen a JPEG optimizado para ultra-ligereza (<15KB)."""
    if not img_source:
        return ""
    try:
        resp = requests.get(img_source, timeout=10)
        if resp.status_code == 200:
            im = Image.open(io.BytesIO(resp.content))
            if im.mode in ("RGBA", "P"):
                im = im.convert("RGB")
            im.thumbnail((400, 260), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            im.save(buffer, format="JPEG", quality=80, optimize=True)
            b64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return f"data:image/jpeg;base64,{b64_data}"
    except Exception as e:
        print(f"  ⚠️ Error procesando imagen {img_source}: {e}")
    return ""

def generate_svg_card(p):
    p_id = p.get("id", "card")
    title = html.escape(p.get("title", "Proyecto"))
    desc = html.escape(p.get("desc", "Proyecto de desarrollo web moderno y alto rendimiento."))
    image_url = p.get("image_url", "")
    
    image_data = get_image_data_uri(image_url) if image_url else ""
    if image_data:
        img_tag = f'<image href="{image_data}" x="16" y="52" width="248" height="175" preserveAspectRatio="xMidYMid slice" clip-path="url(#clipImg-{p_id})" />'
    else:
        img_tag = f'<rect x="16" y="52" width="248" height="175" rx="8" fill="#161b22" /><text x="140" y="140" fill="#58a6ff" font-family="sans-serif" font-size="14" font-weight="700" text-anchor="middle">{title}</text>'

    words = desc.split(" ")
    lines = []
    curr = []
    for w in words:
        if len(" ".join(curr + [w])) <= 34:
            curr.append(w)
        else:
            lines.append(" ".join(curr))
            curr = [w]
    if curr:
        lines.append(" ".join(curr))

    desc_tspan = ""
    y_start = 250
    for i, line in enumerate(lines[:3]):
        desc_tspan += f'<tspan x="140" y="{y_start + i * 19}" text-anchor="middle">{line}</tspan>'

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 280 310" width="100%" height="100%">
  <defs>
    <linearGradient id="shimmerLine" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00d8ff" />
      <stop offset="50%" stop-color="#bd34fe" />
      <stop offset="100%" stop-color="#00d8ff" />
    </linearGradient>

    <filter id="cardShadow" x="-10%" y="-10%" width="130%" height="130%">
      <feDropShadow dx="0" dy="6" stdDeviation="6" flood-color="#000000" flood-opacity="0.9" />
    </filter>

    <clipPath id="clipImg-{p_id}">
      <rect x="16" y="52" width="248" height="175" rx="8" />
    </clipPath>

    <style>
      .card-bg {{
        fill: #0d1117;
        stroke: #000000;
        stroke-width: 2.5;
      }}
      .title-text {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-weight: 700;
        fill: #e6edf3;
        font-size: 14.5px;
      }}
      .desc-text {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 11.5px;
        fill: #8b949e;
        line-height: 1.5;
      }}
    </style>
  </defs>

  <!-- Marco Base Negro -->
  <rect x="4" y="4" width="272" height="302" rx="14" class="card-bg" filter="url(#cardShadow)" />
  
  <!-- Barra Shimmer Superior -->
  <rect x="5" y="5" width="270" height="4" rx="2" fill="url(#shimmerLine)" />

  <!-- Título del Proyecto -->
  <text x="140" y="34" class="title-text" text-anchor="middle">{title}</text>

  <!-- Imagen del Proyecto -->
  <rect x="16" y="52" width="248" height="175" rx="8" fill="#090d13" stroke="#21262d" stroke-width="1" />
  {img_tag}

  <!-- Pequeño Resumen Descriptivo -->
  <text class="desc-text">
    {desc_tspan}
  </text>
</svg>"""

def generate_cards_from_repos(repos=None):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if not repos:
        items = DEFAULT_PROJECTS
    else:
        items = []
        for i, r in enumerate(repos[:6]):
            p_id = f"card-{i+1}"
            raw_name = r.get("name", f"project-{i+1}")
            title = raw_name.replace("-", " ").replace("_", " ").title()
            desc = r.get("description") or "Proyecto de desarrollo web moderno y de alto rendimiento."
            img_url = r.get("_image_url") or f"https://opengraph.githubassets.com/1/{USERNAME}/{raw_name}"
            repo_url = r.get("html_url") or f"https://github.com/{USERNAME}/{raw_name}"
            live_url = r.get("_live_url") or r.get("homepage") or ""
            items.append({
                "id": p_id,
                "title": title,
                "desc": desc,
                "image_url": img_url,
                "repo_url": repo_url,
                "live_url": live_url
            })

    print("🚀 Generando Tarjetas Estáticas Ultra-Ligeras y Rápidas...")
    for p in items:
        filename = f"{p['id']}.svg"
        filepath = os.path.join(OUTPUT_DIR, filename)
        svg_content = generate_svg_card(p)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(svg_content)
        size_kb = os.path.getsize(filepath) / 1024
        print(f"  ✨ Creada {filepath} ({size_kb:.1f} KB)")

def main():
    generate_cards_from_repos()

if __name__ == "__main__":
    main()
