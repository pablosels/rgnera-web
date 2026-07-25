# rgnera-web

Sitio estático de [rgnera.com](https://rgnera.com) — biblioteca digital de sustentabilidad.
Marca: olivo `#475323` · crema `#F5F1E6` · ámbar `#C58A2E`. Tipografía: Playfair Display + Poppins + Lora.

## Cómo publicar un artículo nuevo

1. Crear `content/posts/mi-articulo.md`:

```markdown
---
title: Título del artículo
date: 2026-08-01
categoria: energia
excerpt: Resumen corto para la tarjeta (opcional).
image: /assets/img/posts/mi-articulo/00.jpg
---

Texto del artículo en markdown…
```

Categorías válidas: `energia`, `agricultura`, `agua`, `residuos`, `clima-salud`, `sostenibilidad`.

2. Si lleva imágenes, ponerlas en `assets/img/posts/mi-articulo/`.
3. Compilar y publicar:

```
python build.py
git add -A && git commit -m "Nuevo articulo" && git push
```

GitHub Pages sirve la rama `gh-pages` (ver deploy.py) o `main:/docs` según configuración.

## Estructura

- `build.py` — generador (Python + librería `markdown`; sin más dependencias)
- `content/posts/*.json` — los 28 artículos migrados de Wix (2021-2023)
- `content/posts/*.md` — artículos nuevos
- `content/site.json` — configuración (base URL, Substack, Instagram, CNAME)
- `content/categorias.json` — taxonomía y mapeo de categorías
- `assets/` — CSS, logos, imágenes (localizadas desde Wix, optimizadas a ≤1200px)
- `docs/` — salida compilada (no editar a mano)

## La calculadora

`build.py` copia `C:\Users\minis\rgnera-huella\docs\index.html` a `docs/huella/`
(página nativa, mismo dominio). La página `/calculadora/` la muestra en iframe
same-origin con alto automático. El código fuente y la metodología viven en
[pablosels/rgnera-huella](https://github.com/pablosels/rgnera-huella).

## Newsletter

Cuando exista la publicación de Substack, poner su URL en `content/site.json`
(`"substack": "https://rgnera.substack.com"` o `https://news.rgnera.com`) y
recompilar: los formularios de suscripción se activan solos en todo el sitio.
