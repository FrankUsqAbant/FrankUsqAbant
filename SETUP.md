# 🤖 Guía de Setup — README con Automatización

Sigue estos pasos **en orden** y tu README se actualizará solo cada 6 horas. ⚡

---

## 📁 Paso 1 — Estructura de archivos

Sube estos archivos a tu repo `FrankUsqAbant/FrankUsqAbant` (el repo de perfil):

```
FrankUsqAbant/
├── README.md                          ← Reemplaza el existente
├── scripts/
│   ├── update_projects.py
│   └── update_youtube.py
└── .github/
    └── workflows/
        └── update-readme.yml
```

---

## ⭐ Paso 2 — Marcar tus proyectos como "featured"

Para que un proyecto aparezca automáticamente en tu README:

1. Abre el repositorio que quieras mostrar en GitHub
2. Haz clic en el **⚙️ engranaje** junto a "About" (lado derecho)
3. En el campo **Topics**, escribe `featured` y presiona Enter
4. Guarda los cambios

✅ Puedes marcar tantos repos como quieras. Aparecerán en grupos de 3.

---

## 📺 Paso 3 — Configurar tu Channel ID de YouTube

Tu Channel ID **no es** tu @handle. Para encontrarlo:

### Opción A — Desde YouTube Studio:
1. Ve a [studio.youtube.com](https://studio.youtube.com)
2. Haz clic en **Configuración** (ícono de engranaje, abajo a la izquierda)
3. Ve a **Información del canal**
4. Copia el **ID del canal** (empieza con `UC...`)

### Opción B — Desde tu perfil:
1. Ve a tu canal: `https://www.youtube.com/@abantofrank12`
2. Haz clic en **"Información"** (pestaña)
3. Haz clic en el ícono de compartir → **"Copiar ID del canal"**

### Ahora reemplázalo en el script:

Abre `scripts/update_youtube.py` y cambia esta línea:

```python
# ANTES
CHANNEL_ID = "YOUR_CHANNEL_ID_HERE"

# DESPUÉS (ejemplo)
CHANNEL_ID = "UCxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

> ⚠️ Mientras no configures el Channel ID, se mostrará el empty state de "Próximamente".
> Esto es intencional — así tu perfil se ve bonito desde el primer día.

---

## 🔐 Paso 4 — Dar permisos de escritura al workflow

1. Ve a tu repo `FrankUsqAbant` en GitHub
2. Haz clic en **Settings** (pestaña superior)
3. En el menú izquierdo: **Actions → General**
4. Baja hasta **"Workflow permissions"**
5. Selecciona **"Read and write permissions"**
6. Guarda ✅

---

## ▶️ Paso 5 — Ejecutar manualmente (primera vez)

1. Ve a tu repo → pestaña **Actions**
2. En el menú izquierdo, haz clic en **"🤖 Auto-update README"**
3. Haz clic en el botón **"Run workflow"** → **"Run workflow"**
4. Espera ~1 minuto y recarga tu perfil 🎉

---

## ⚙️ Frecuencia de actualización

El workflow corre automáticamente:

| Evento | Cuándo |
|--------|--------|
| 🕐 Programado | Cada 6 horas |
| 📤 Push a main | Cada vez que subes cambios |
| 🖱️ Manual | Desde la pestaña Actions |

---

## 🖼️ Formato recomendado para las imágenes en tus repos

Para que la imagen de preview se detecte correctamente, ponla como la **primera imagen** en el README de cada proyecto:

```markdown
<!-- Markdown -->
![Preview del proyecto](preview.png)

<!-- O HTML -->
<img src="preview.png" width="100%" alt="Mi Proyecto">
```

---

## 🌐 Formato recomendado para el link del sitio live

El script detecta automáticamente links con estas palabras clave:

```markdown
<!-- Cualquiera de estos formatos funciona -->
[🌐 Ver Sitio](https://mi-proyecto.vercel.app)
[Live Demo](https://mi-proyecto.netlify.app)
[Ver Página](https://usuario.github.io/repo)

<!-- O simplemente tener la URL en el README -->
🚀 Desplegado en: https://mi-proyecto.vercel.app
```

También detecta automáticamente URLs de:
- `.vercel.app`
- `.netlify.app`
- `.pages.dev`
- `.github.io`

---

## ❓ Preguntas frecuentes

**¿Cuántos proyectos puedo mostrar?**
Los que quieras — aparecen en filas de 3, sin límite.

**¿Qué pasa si un repo no tiene imagen en el README?**
Se usa la imagen social que genera GitHub automáticamente para ese repo.

**¿Qué pasa si un repo no tiene link live?**
Solo aparece el botón "⚡ Código" (sin botón "🌐 Ver Sitio"). Todo funciona igual.

**¿Puedo cambiar el orden de los proyectos?**
Sí — el orden es por última fecha de actualización del repo. El más reciente aparece primero.

---

¡Listo! Tu README está completamente automatizado. 🚀
