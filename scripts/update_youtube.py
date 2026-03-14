#!/usr/bin/env python3
"""
update_youtube.py
=================
Auto-actualiza la sección <!-- YOUTUBE:START / END --> del README.md.

- Si hay videos en el canal → muestra hasta 3 tarjetas con thumbnail.
- Si NO hay videos aún     → muestra una tarjeta "próximamente" bien diseñada.

⚠️  IMPORTANTE: Reemplaza YOUR_CHANNEL_ID_HERE con tu Channel ID real.
    Para encontrarlo: YouTube Studio → Configuración → Información del canal → ID del canal
    El ID empieza con "UC..."

Uso:
    python scripts/update_youtube.py
"""

import re
import requests
import xml.etree.ElementTree as ET

# ── Config ─────────────────────────────────────────────────────────────────────
# 👇 REEMPLAZA ESTO CON TU CHANNEL ID (empieza con UC...)
CHANNEL_ID  = "UCJDLlGf9h5hm3IM32Wr7auw"

HANDLE      = "abantofrank12"
YT_URL      = f"https://www.youtube.com/@{HANDLE}"
RSS_URL     = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
MAX_VIDEOS  = 3
README      = "README.md"
YT_START    = "<!-- YOUTUBE:START -->"
YT_END      = "<!-- YOUTUBE:END -->"

# Namespaces del RSS de YouTube
NS = {
    "atom":  "http://www.w3.org/2005/Atom",
    "yt":    "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def read_readme():
    with open(README, "r", encoding="utf-8") as f:
        return f.read()


def write_readme(content):
    with open(README, "w", encoding="utf-8") as f:
        f.write(content)


def inject_section(readme, start_marker, end_marker, new_content):
    pattern     = rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}"
    replacement = f"{start_marker}\n{new_content}\n{end_marker}"
    return re.sub(pattern, replacement, readme, flags=re.DOTALL)


# ── Fetch videos ───────────────────────────────────────────────────────────────

def fetch_videos():
    """Descarga el RSS de YouTube y devuelve una lista de dicts con los videos."""
    if CHANNEL_ID == "YOUR_CHANNEL_ID_HERE":
        print("⚠️  CHANNEL_ID no configurado — se mostrará el empty state.")
        return []
    try:
        r = requests.get(RSS_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        r.raise_for_status()
        root   = ET.fromstring(r.content)
        videos = []
        for entry in root.findall("atom:entry", NS)[:MAX_VIDEOS]:
            vid_id = entry.find("yt:videoId",  NS).text
            title  = entry.find("atom:title",  NS).text
            url    = entry.find("atom:link",   NS).attrib["href"]
            # Thumbnail de mayor calidad disponible
            thumb  = f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg"
            videos.append({"id": vid_id, "title": title, "url": url, "thumb": thumb})
        return videos
    except Exception as e:
        print(f"⚠️  Error al obtener el RSS: {e}")
        return []


# ── HTML builders ──────────────────────────────────────────────────────────────

def build_video_card(video):
    title = video["title"].replace('"', "'")
    url   = video["url"]
    thumb = video["thumb"]
    return f"""\
<td width="33%" align="center" valign="top">
<img src="https://capsule-render.vercel.app/api?type=waving&color=FF0000&height=35&section=header&reversal=true" width="100%" alt="cabecera">
<br>
<a href="{url}">
  <img src="{thumb}" width="100%" alt="{title}">
</a>
<br><br>
<a href="{url}">
  <sub><strong>▶ {title}</strong></sub>
</a>
<br><br>
<a href="{url}">
  <img src="https://img.shields.io/badge/Ver_Video-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="Ver Video">
</a>
<br><br>
</td>"""


def build_empty_state():
    return f"""\
<table border="0" width="100%" cellpadding="10" cellspacing="0">
<tr>
<td align="center" colspan="3">
<br>
<img src="https://capsule-render.vercel.app/api?type=waving&color=FF0000&height=35&section=header&reversal=true" width="100%" alt="cabecera">
<br><br>
<img src="https://cdn.simpleicons.org/youtube/FF0000" width="52" height="52" alt="YouTube">
<br><br>
<strong>¡Próximamente contenido en YouTube!</strong>
<br><br>
<sub>Estaré subiendo videos sobre desarrollo web, IA y mucho más.</sub>
<br>
<sub>¡Suscríbete para no perderte nada!</sub>
<br><br>
<a href="{YT_URL}">
  <img src="https://img.shields.io/badge/🔔_Suscribirse-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="Suscribirse">
</a>
<br><br>
</td>
</tr>
</table>"""


def generate_youtube_html(videos):
    if not videos:
        return build_empty_state()

    cards = [build_video_card(v) for v in videos]
    # Rellenar hasta 3 columnas
    while len(cards) < 3:
        cards.append('<td width="33%"></td>')

    row = "\n".join(cards)
    return (
        '<table border="0" width="100%" cellpadding="10" cellspacing="0">\n'
        f'<tr>\n{row}\n</tr>\n'
        '</table>'
    )


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("📺 Obteniendo videos de YouTube...")
    videos = fetch_videos()
    print(f"✅ {len(videos)} video(s) encontrado(s).")

    html   = generate_youtube_html(videos)
    readme = read_readme()
    readme = inject_section(readme, YT_START, YT_END, html)
    write_readme(readme)
    print("🎬 Sección YouTube actualizada en README.md.")
