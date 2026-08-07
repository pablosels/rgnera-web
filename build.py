# -*- coding: utf-8 -*-
"""Generador estático de rgnera.com.

Flujo: lee content/ (posts en JSON migrados de Wix o .md nuevos con frontmatter),
aplica templates inline y escribe el sitio completo en docs/ (GitHub Pages).

Uso:  python build.py
"""
import json, os, re, shutil, unicodedata, html
from datetime import date
from pathlib import Path
from urllib.parse import unquote, quote

import markdown as md

RAIZ = Path(__file__).parent
CONT = RAIZ / "content"
DOCS = RAIZ / "docs"
ASSETS = RAIZ / "assets"

SITE = json.loads((CONT / "site.json").read_text(encoding="utf-8"))
if os.environ.get("RGNERA_BASE") is not None:
    SITE["base"] = os.environ["RGNERA_BASE"].rstrip("/")
CATS = json.loads((CONT / "categorias.json").read_text(encoding="utf-8"))
IMG_MAP = json.loads((CONT / "img_map.json").read_text(encoding="utf-8")) if (CONT / "img_map.json").exists() else {}

MESES = ["ene", "feb", "mar", "abr", "may", "jun",
         "jul", "ago", "sep", "oct", "nov", "dic"]


# ---------------------------------------------------------------- utilidades
def slugify(t: str) -> str:
    s = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:70]


def parse_fecha(s: str) -> date:
    s = (s or "").strip().lower()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.match(r"(\d{1,2})\s+([a-záéíóú]+)\.?\s+(\d{4})", s)
    if m:
        mes = next((i + 1 for i, n in enumerate(MESES) if m.group(2).startswith(n)), 1)
        return date(int(m.group(3)), mes, int(m.group(1)))
    return date(2021, 1, 1)


def fecha_bonita(d: date) -> str:
    return f"{d.day} {MESES[d.month - 1]} {d.year}"


def fecha_rfc(d: date) -> str:
    dias = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    meses_en = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{dias[d.weekday()]}, {d.day:02d} {meses_en[d.month-1]} {d.year} 08:00:00 GMT"


def limpia_wix(url: str) -> str:
    """Quita las transformaciones de wixstatic para obtener la imagen original."""
    if "static.wixstatic.com" in url and "/v1/" in url:
        return url.split("/v1/")[0]
    return url


def categoria_de(post: dict) -> str:
    if post.get("categoria") in CATS["canonicas"]:
        return post["categoria"]
    texto = " ".join(post.get("categories_guess", []) + [post["title"]]).lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    for clave, palabras in CATS["mapeo"].items():
        for p in palabras:
            if p in texto:
                return clave
    return CATS["default"]


def extracto_de(mkd: str, n=200) -> str:
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", mkd)
    t = re.sub(r"[#>*_\[\]`]", "", t)
    t = re.sub(r"\([^)]*\)", "", t)
    t = " ".join(t.split())
    return (t[:n].rsplit(" ", 1)[0] + "…") if len(t) > n else t


def min_lectura(post: dict) -> str:
    rm = str(post.get("read_minutes") or "")
    m = re.search(r"(\d+)", rm)
    if m:
        return f"{m.group(1)} min de lectura"
    palabras = len(post.get("full_text_markdown", "").split())
    return f"{max(1, round(palabras / 200))} min de lectura"


def e(s: str) -> str:
    return html.escape(str(s), quote=True)


# ---------------------------------------------------------------- carga
def cargar_posts():
    posts = []
    for f in sorted((CONT / "posts").glob("*.json")):
        p = json.loads(f.read_text(encoding="utf-8"))
        if not p.get("full_text_markdown"):
            continue
        p["full_text_markdown"] = re.sub(
            r"(!\[[^\]]*\]\()(https?://[^)]+)(\))",
            lambda m: m.group(1) + (SITE["base"] + IMG_MAP[limpia_wix(m.group(2))]
                                    if limpia_wix(m.group(2)) in IMG_MAP else m.group(2)) + m.group(3),
            p["full_text_markdown"])
        # el template ya pone el H1: si el cuerpo migrado repite el título como H1,
        # se quita; cualquier otro H1 inicial se demota a H2
        mkd = p["full_text_markdown"].lstrip()
        m1 = re.match(r"#\s+([^\n]+)\n+", mkd)
        if m1:
            if slugify(m1.group(1)) == slugify(p["title"]):
                p["full_text_markdown"] = mkd[m1.end():]
            else:
                p["full_text_markdown"] = "## " + mkd[2:]
        p["slug"] = f.stem
        p["fecha"] = parse_fecha(p.get("date", ""))
        p["cat"] = categoria_de(p)
        p["extracto"] = p.get("excerpt") or extracto_de(p["full_text_markdown"])
        p["lectura"] = min_lectura(p)
        imgs = [limpia_wix(u) for u in p.get("image_urls", []) if "wixstatic" in u or u.startswith("http")]
        local = ASSETS / "img" / "posts" / p["slug"]
        locales = sorted(local.glob("*")) if local.exists() else []
        if locales:
            p["portada"] = f"{SITE['base']}/assets/img/posts/{p['slug']}/{locales[0].name}"
        else:
            p["portada"] = imgs[0] if imgs else ""
        posts.append(p)
    for f in sorted((CONT / "posts").glob("*.md")):
        raw = f.read_text(encoding="utf-8")
        m = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
        if not m:
            continue
        meta = {}
        for linea in m.group(1).splitlines():
            if ":" in linea:
                k, v = linea.split(":", 1)
                meta[k.strip()] = v.strip().strip('"')
        p = {
            "title": meta.get("title", f.stem), "date": meta.get("date", ""),
            "author": meta.get("author", "Pablo Seldner"),
            "full_text_markdown": m.group(2),
            "image_urls": [meta["image"]] if meta.get("image") else [],
            "categories_guess": [meta.get("categoria", "")],
            "slug": meta.get("slug") or slugify(meta.get("title", f.stem)),
        }
        p["fecha"] = parse_fecha(p["date"])
        p["cat"] = meta.get("categoria") if meta.get("categoria") in CATS["canonicas"] else categoria_de(p)
        p["extracto"] = meta.get("excerpt") or extracto_de(p["full_text_markdown"])
        p["lectura"] = min_lectura(p)
        # image con ruta raíz (/assets/...) hereda el dominio base, como los JSON
        img = meta.get("image", "")
        p["portada"] = SITE["base"] + img if img.startswith("/") else img
        posts.append(p)
    # posts programados: fecha futura no se publica (RGNERA_FUTUROS=1 para preview)
    if not os.environ.get("RGNERA_FUTUROS"):
        pendientes = [p for p in posts if p["fecha"] > date.today()]
        if pendientes:
            print("programados (aún no salen):",
                  ", ".join(f"{p['slug']} ({p['fecha']})" for p in sorted(pendientes, key=lambda p: p['fecha'])))
        posts = [p for p in posts if p["fecha"] <= date.today()]
    posts.sort(key=lambda p: p["fecha"], reverse=True)
    return posts


# ---------------------------------------------------------------- plantillas
def head(titulo, desc, ruta="", og_img="", og_type="website", noindex=False):
    canon = f"{SITE['base']}/{ruta}" if ruta else SITE["base"] + "/"
    og = og_img or f"{SITE['base']}/assets/img/og.png"
    robots = '<meta name="robots" content="noindex">\n' if noindex else f'<link rel="canonical" href="{canon}">\n'
    return f"""<!DOCTYPE html>
<html lang="es-MX">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(desc)}">
{robots}<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{og}">
<meta property="og:url" content="{canon}">
<meta property="og:type" content="{og_type}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(titulo)}">
<meta name="twitter:image" content="{og}">
<link rel="icon" type="image/png" sizes="32x32" href="{SITE['base']}/assets/img/favicon-32.png">
<link rel="apple-touch-icon" href="{SITE['base']}/assets/img/favicon-180.png">
<link rel="alternate" type="application/rss+xml" title="RGNERA" href="{SITE['base']}/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Poppins:wght@400;500;600&family=Lora:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{SITE['base']}/assets/estilo.css">
</head>
<body>
<a class="salto" href="#contenido">Saltar al contenido</a>"""


def header(activo=""):
    def cl(k):
        return ' class="activo"' if k == activo else ""
    b = SITE["base"]
    temas = "".join(f'<a href="{b}/articulos/{ck}/">{e(cn)}</a>'
                    for ck, cn in CATS["canonicas"].items())
    return f"""
<header class="topbar">
 <div class="shell">
  <a class="marca" href="{b}/"><img src="{b}/assets/img/emblema.png" alt="" width="34" height="34"><b>RGNERA</b></a>
  <nav class="nav" id="nav" aria-label="Principal">
   <a href="{b}/"{cl('inicio')}>Inicio</a>
   <div class="has-sub">
    <a href="{b}/articulos/"{cl('articulos')} aria-haspopup="true">Artículos <span class="flecha" aria-hidden="true">▾</span></a>
    <div class="submenu">
     <a href="{b}/articulos/" class="sub-todos">Todos los Artículos</a>
     {temas}
    </div>
   </div>
   <a href="{b}/videos/"{cl('videos')}>Videos</a>
   <a href="{b}/acerca/"{cl('acerca')}>Acerca</a>
  </nav>
  <span class="empuje"></span>
  <a class="btn-calc" href="{b}/calculadora/">Calcular mi huella</a>
  <button class="menu-btn" aria-label="Abrir menú" onclick="document.getElementById('nav').classList.toggle('abierto')">☰</button>
 </div>
</header>
<main id="contenido">"""


def form_news(centro=False):
    sub = SITE.get("substack", "")
    if sub:
        return f"""<form class="news-form" onsubmit="event.preventDefault();location.href='{sub}/subscribe?email='+encodeURIComponent(this.correo.value)">
   <input type="email" name="correo" required placeholder="tu@correo.com" aria-label="Tu correo">
   <button class="btn-olivo" type="submit">Suscribirme</button></form>"""
    return f"""<a class="btn-olivo" style="display:inline-block" href="{SITE['instagram']}" target="_blank" rel="noopener">Sígueme en Instagram — el newsletter viene en camino</a>"""


def footer():
    b = SITE["base"]
    return f"""
</main>
<footer>
 <div class="shell">
  <div>
   <a class="marca" href="{b}/"><img src="{b}/assets/img/emblema_cream.png" alt="" width="34" height="34"><b>RGNERA</b></a>
   <p class="tag">Biblioteca digital de sustentabilidad. Artículos, herramientas y datos para darle un respiro al planeta.</p>
  </div>
  <div>
   <h4>Explora</h4>
   <ul><li><a href="{b}/articulos/">Artículos</a></li>
   <li><a href="{b}/calculadora/">Calculadora de huella</a></li>
   <li><a href="{b}/videos/">Videos</a></li>
   <li><a href="{b}/acerca/">Acerca</a></li></ul>
  </div>
  <div>
   <h4>Conecta</h4>
   <ul><li><a href="{SITE['instagram']}" target="_blank" rel="noopener">Instagram</a></li>
   <li><a href="{SITE['repo_calc']}" target="_blank" rel="noopener">Metodología de la calculadora</a></li>
   <li><a href="{b}/feed.xml">RSS</a></li></ul>
  </div>
 </div>
 <div class="pie-legal"><div class="shell">
  <span>© {date.today().year} CAMVIO · RGNERA</span><span>Hecho con 💚 en México</span>
 </div></div>
</footer>
</body></html>"""


def tarjeta(p):
    b = SITE["base"]
    img = f'<img src="{e(p["portada"])}" alt="{e(p["title"])}" loading="lazy">' if p["portada"] else ""
    return f"""<a class="tarjeta" href="{b}/articulos/{p['slug']}/">
 <div class="thumb">{img}</div>
 <div class="cuerpo">
  <span class="pill">{e(CATS['canonicas'][p['cat']])}</span>
  <h3>{e(p['title'])}</h3>
  <p class="extracto">{e(p['extracto'])}</p>
  <span class="meta">{fecha_bonita(p['fecha'])} · {p['lectura']}</span>
 </div></a>"""


def compartir(p):
    """Botones de compartir del artículo. Instagram no tiene URL de compartir
    web (su API no lo permite), así que ese caso se cubre con 'copiar enlace':
    el link se pega en stories o en la bio."""
    url = f"{SITE['base']}/articulos/{p['slug']}/"
    texto = p["title"]
    u, t = quote(url, safe=""), quote(texto, safe="")
    redes = [
        ("X", f"https://twitter.com/intent/tweet?url={u}&text={t}",
         '<path d="M18.2 2H21l-6.6 7.5L22 22h-6.1l-4.8-6.2L5.6 22H2.8l7-8L2 2h6.2l4.3 5.7L18.2 2Zm-1 18h1.7L7.9 3.8H6.1L17.2 20Z"/>'),
        ("Facebook", f"https://www.facebook.com/sharer/sharer.php?u={u}",
         '<path d="M22 12a10 10 0 1 0-11.6 9.9v-7H7.9V12h2.5V9.8c0-2.5 1.5-3.9 3.8-3.9 1.1 0 2.2.2 2.2.2v2.5h-1.3c-1.2 0-1.6.8-1.6 1.6V12h2.8l-.4 2.9h-2.4v7A10 10 0 0 0 22 12Z"/>'),
        ("LinkedIn", f"https://www.linkedin.com/sharing/share-offsite/?url={u}",
         '<path d="M6.9 21H3.4V9.2h3.5V21ZM5.1 7.6a2 2 0 1 1 0-4.1 2 2 0 0 1 0 4.1ZM21 21h-3.5v-5.7c0-1.4 0-3.1-1.9-3.1s-2.2 1.5-2.2 3v5.8H9.9V9.2h3.3v1.6h.1a3.7 3.7 0 0 1 3.3-1.8c3.5 0 4.2 2.3 4.2 5.3V21Z"/>'),
        ("WhatsApp", f"https://api.whatsapp.com/send?text={t}%20{u}",
         '<path d="M12 2a10 10 0 0 0-8.6 15L2 22l5.2-1.4A10 10 0 1 0 12 2Zm5.8 14.2c-.2.7-1.4 1.3-2 1.4-.5.1-1.1.1-1.8-.1-.4-.1-1-.3-1.7-.6-3-1.3-4.9-4.3-5-4.5-.2-.2-1.2-1.6-1.2-3s.7-2.1 1-2.4c.2-.3.5-.4.7-.4h.5c.2 0 .4 0 .6.5l.8 2c.1.2.1.3 0 .5l-.4.5-.3.3c-.1.1-.2.3 0 .5.2.3.8 1.3 1.7 2.1 1.1 1 2 1.3 2.3 1.4.2.1.4.1.5-.1l.7-.9c.2-.2.3-.2.5-.1l2 .9c.2.1.4.2.4.3.1.1.1.6-.1 1.2Z"/>'),
    ]
    botones = "".join(
        f'<a class="red" href="{href}" target="_blank" rel="noopener" aria-label="Compartir en {n}" title="Compartir en {n}">'
        f'<svg viewBox="0 0 24 24" width="17" height="17" fill="currentColor" aria-hidden="true">{svg}</svg></a>'
        for n, href, svg in redes)
    # Instagram no admite compartir por URL desde la web: su botón copia el
    # enlace para pegarlo en una story o en la bio.
    ig = ('<path d="M12 2.2c3.2 0 3.6 0 4.9.1 1.2.1 1.8.2 2.2.4.6.2 1 .5 1.4.9.4.4.7.8.9 1.4.2.4.4 1 .4 2.2.1 1.3.1 1.7.1 4.9s0 3.6-.1 4.9c-.1 1.2-.2 1.8-.4 2.2a3.9 3.9 0 0 1-2.3 2.3c-.4.2-1 .4-2.2.4-1.3.1-1.7.1-4.9.1s-3.6 0-4.9-.1c-1.2-.1-1.8-.2-2.2-.4a3.9 3.9 0 0 1-2.3-2.3c-.2-.4-.4-1-.4-2.2C2.2 15.6 2.2 15.2 2.2 12s0-3.6.1-4.9c.1-1.2.2-1.8.4-2.2A3.9 3.9 0 0 1 5 2.6c.4-.2 1-.4 2.2-.4C8.4 2.2 8.8 2.2 12 2.2Zm0 1.8c-3.1 0-3.5 0-4.7.1-1.1.05-1.7.2-2.1.4-.5.2-.9.4-1.3.8-.4.4-.6.8-.8 1.3-.2.4-.35 1-.4 2.1-.1 1.2-.1 1.6-.1 4.7s0 3.5.1 4.7c.05 1.1.2 1.7.4 2.1.2.5.4.9.8 1.3.4.4.8.6 1.3.8.4.2 1 .35 2.1.4 1.2.1 1.6.1 4.7.1s3.5 0 4.7-.1c1.1-.05 1.7-.2 2.1-.4.5-.2.9-.4 1.3-.8.4-.4.6-.8.8-1.3.2-.4.35-1 .4-2.1.1-1.2.1-1.6.1-4.7s0-3.5-.1-4.7c-.05-1.1-.2-1.7-.4-2.1a3.5 3.5 0 0 0-.8-1.3 3.5 3.5 0 0 0-1.3-.8c-.4-.2-1-.35-2.1-.4-1.2-.1-1.6-.1-4.7-.1Zm0 3.1a4.9 4.9 0 1 1 0 9.8 4.9 4.9 0 0 1 0-9.8Zm0 8.1a3.2 3.2 0 1 0 0-6.4 3.2 3.2 0 0 0 0 6.4Zm6.3-8.3a1.15 1.15 0 1 1-2.3 0 1.15 1.15 0 0 1 2.3 0Z"/>')
    return f"""
<div class="compartir">
 <span class="etiqueta">¿Te sirvió? Compártelo</span>
 <div class="redes">
  <button class="red copiar" type="button" data-url="{url}" data-aviso="Copiado — pégalo en tu story"
    aria-label="Copiar enlace para Instagram" title="Instagram — copia el enlace para pegarlo en tu story o en la bio">
   <svg viewBox="0 0 24 24" width="17" height="17" fill="currentColor" aria-hidden="true">{ig}</svg>
   <span class="copiado" hidden></span>
  </button>{botones}
  <button class="red copiar" type="button" data-url="{url}" data-aviso="¡Copiado!"
    aria-label="Copiar enlace" title="Copiar enlace">
   <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M6 15H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v1"/></svg>
   <span class="copiado" hidden></span>
  </button>
 </div>
</div>"""


def banda_calculadora():
    b = SITE["base"]
    return f"""
<section class="shell"><div class="banda-calc">
 <div><h2>¿Cuánto CO₂e emites al mes?</h2>
 <p>Calcula tu huella de carbono personal con datos mexicanos oficiales (INEGI + INECC). Toma un minuto y te dice por dónde empezar.</p></div>
 <a class="btn-primario" href="{b}/calculadora/">Calcular mi huella →</a>
</div></section>"""


# ---------------------------------------------------------------- páginas
def pagina_home(posts, videos):
    b = SITE["base"]
    ultimos = posts[:4]
    out = [head("RGNERA — Biblioteca sustentable", SITE["descripcion"]), header("inicio")]
    out.append(f"""
<section class="shell hero">
 <p class="eyebrow">Biblioteca sustentable</p>
 <h1>Dale un respiro al planeta</h1>
 <p>Artículos claros sobre sustentabilidad, energía y consumo — y una calculadora que estima tu huella de carbono con datos mexicanos en un minuto.</p>
 <div class="acciones">
  <a class="btn-primario" href="{b}/calculadora/">Calcular mi huella →</a>
  <a class="link-sec" href="{b}/articulos/">Leer artículos</a>
 </div>
 <div class="news-banda">
  <div class="texto"><b>{"No te pierdas ni un artículo" if SITE.get("substack") else "Únete a la comunidad"}</b>
  <span>{"Lo nuevo de RGNERA, directo a tu correo. Sin spam." if SITE.get("substack") else "El newsletter viene en camino; mientras tanto, lo nuevo sale primero en Instagram."}</span></div>
  {form_news()}
 </div>
</section>""")
    out.append(f"""
<section class="shell fila">
 <div class="fila-cab"><h2>Lo último</h2><a class="ver-todo" href="{b}/articulos/">Ver todo →</a></div>
 <div class="grid g4">{''.join(tarjeta(p) for p in ultimos)}</div>
</section>""")
    out.append(banda_calculadora())
    usados = {p["slug"] for p in ultimos}
    for ckey, cnombre in CATS["canonicas"].items():
        del_cat = [p for p in posts if p["cat"] == ckey and p["slug"] not in usados]
        if len(del_cat) < 3:
            del_cat = [p for p in posts if p["cat"] == ckey]
        if len(del_cat) < 3:
            continue
        fila = del_cat[:3]
        usados.update(p["slug"] for p in fila)
        out.append(f"""
<section class="shell fila">
 <div class="fila-cab"><h2>{e(cnombre)}</h2><a class="ver-todo" href="{b}/articulos/{ckey}/">Ver todo →</a></div>
 <div class="grid">{''.join(tarjeta(p) for p in fila)}</div>
</section>""")
    if videos:
        vids = "".join(f"""<div><div class="video-marco">
<iframe src="https://www.youtube-nocookie.com/embed/{v['id']}" title="{e(v['titulo'])}" loading="lazy" allowfullscreen></iframe>
</div><p class="video-titulo">{e(v['titulo'])}</p></div>""" for v in videos[:2])
        out.append(f"""
<section class="shell fila">
 <div class="fila-cab"><h2>Videos</h2><a class="ver-todo" href="{b}/videos/">Ver todo →</a></div>
 <div class="grid" style="grid-template-columns:repeat(2,minmax(0,1fr))">{vids}</div>
</section>""")
    out.append(footer())
    return "".join(out)


def pagina_articulos(posts, cat=None):
    b = SITE["base"]
    lista = [p for p in posts if p["cat"] == cat] if cat else posts
    titulo = CATS["canonicas"][cat] if cat else "Todos los artículos"
    filtros = [f'<a href="{b}/articulos/"{"" if cat else " class=\"activo\""}>Todos</a>']
    for ck, cn in CATS["canonicas"].items():
        n = sum(1 for p in posts if p["cat"] == ck)
        if n:
            act = ' class="activo"' if ck == cat else ""
            filtros.append(f'<a href="{b}/articulos/{ck}/"{act}>{e(cn)} ({n})</a>')
    out = [head(f"{titulo} — RGNERA", f"Artículos de RGNERA: {titulo.lower()}.",
                f"articulos/{cat + '/' if cat else ''}"), header("articulos")]
    out.append(f"""
<section class="shell cab-seccion">
 <h1>{e(titulo)}</h1>
 <p>{f"{len(lista)} artículo{'s' if len(lista) != 1 else ''} sobre {titulo.lower()}." if cat else f"El archivo completo de la biblioteca: {len(lista)} artículo{'s' if len(lista) != 1 else ''}."}</p>
 <div class="filtros">{''.join(filtros)}</div>
</section>
<section class="shell fila"><div class="grid">{''.join(tarjeta(p) for p in lista)}</div></section>""")
    out.append(footer())
    return "".join(out)


def pagina_post(p, ant, sig):
    b = SITE["base"]
    cuerpo = md.markdown(p["full_text_markdown"], extensions=["extra"])
    cuerpo = re.sub(r"<!--.*?-->", "", cuerpo, flags=re.S)
    portada = f'<div class="portada"><img src="{e(p["portada"])}" alt="{e(p["title"])}"></div>' if p["portada"] else ""
    nav = ""
    if ant or sig:
        izq = f'<a href="{b}/articulos/{ant["slug"]}/">← {e(ant["title"])}</a>' if ant else "<span></span>"
        der = f'<a href="{b}/articulos/{sig["slug"]}/" style="text-align:right">{e(sig["title"])} →</a>' if sig else "<span></span>"
        nav = f'<nav class="prevnext">{izq}{der}</nav>'
    out = [head(f"{p['title']} — RGNERA", p["extracto"], f"articulos/{p['slug']}/", p["portada"], og_type="article"),
           header("articulos")]
    out.append(f"""
<article class="articulo">
 <a class="migas" href="{b}/articulos/">← Artículos</a>
 <h1>{e(p['title'])}</h1>
 <div class="meta-post">
  <span>{e(p.get('author') or 'Pablo Seldner')}</span><span class="sep">·</span>
  <span>{fecha_bonita(p['fecha'])}</span><span class="sep">·</span>
  <span>{p['lectura']}</span><span class="sep">·</span>
  <span class="pill">{e(CATS['canonicas'][p['cat']])}</span>
 </div>
 {portada}
 <div class="prosa">{cuerpo}</div>
 {compartir(p)}
 <div class="caja-sub"><b>¿Te sirvió este artículo?</b>
 <span>{"Recibe lo nuevo de RGNERA directo en tu correo." if SITE.get("substack") else "Sígueme en Instagram para no perderte lo que viene."}</span>{form_news(True)}</div>
</article>
{nav}""")
    out.append("""
<script>
document.querySelectorAll('.compartir .copiar').forEach(function(b){
  b.addEventListener('click', function(){
    var url = b.dataset.url, aviso = b.querySelector('.copiado');
    aviso.textContent = b.dataset.aviso || '¡Copiado!';
    function ok(){ aviso.hidden = false; setTimeout(function(){ aviso.hidden = true; }, 2200); }
    function respaldo(){
      var ta = document.createElement('textarea');
      ta.value = url; ta.setAttribute('readonly', '');
      ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); } catch(e) {}
      document.body.removeChild(ta); ok();
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(ok).catch(respaldo);
    } else { respaldo(); }
  });
});
</script>""")
    out.append(footer())
    return "".join(out)


def pagina_calculadora():
    b = SITE["base"]
    out = [head("¿Sabes cuál es tu huella de carbono? Calcúlala en 1 minuto — RGNERA",
                "Gratis y con datos oficiales de México (INEGI + INECC). Descubre cuánto pesa tu estilo de vida y por dónde empezar a bajarlo.",
                "calculadora/",
                og_img=f"{SITE['base']}/assets/img/og-calculadora.png"), header("")]
    out.append(f"""
<section class="shell calc-intro">
 <h1>Calcula tu huella de carbono</h1>
 <p>Responde con tus gastos del mes y obtén tu huella en CO₂e con metodología insumo-producto y datos oficiales mexicanos (MIP 2018 de INEGI + inventario INECC). Toma un minuto.</p>
</section>
<iframe id="marco-calc" src="{b}/huella/" title="Calculadora de huella de carbono RGNERA" height="5400"></iframe>
<p class="calc-nota">Metodología abierta — <a href="{SITE['repo_calc']}" target="_blank" rel="noopener">ver el código y las fuentes en GitHub</a></p>
<script>
(function(){{
 var f=document.getElementById('marco-calc'),previa=0,estable=0,timer=null;
 function ajusta(){{try{{var d=f.contentDocument||f.contentWindow.document;
  if(d&&d.documentElement){{var h=d.documentElement.scrollHeight;
   if(h===previa){{if(++estable>=6&&timer){{clearInterval(timer);timer=null;}}}}
   else{{previa=h;estable=0;f.style.height=(h+40)+'px';}}}}}}catch(e){{}}}}
 function arranca(){{estable=0;if(!timer)timer=setInterval(ajusta,800);ajusta();}}
 f.addEventListener('load',arranca);
 window.addEventListener('resize',arranca);
}})();
</script>""")
    out.append(footer())
    return "".join(out)


def pagina_acerca(texto_md):
    cuerpo = md.markdown(texto_md, extensions=["extra"])
    out = [head("Acerca de RGNERA", "Qué es RGNERA y quién está detrás.", "acerca/"), header("acerca")]
    out.append(f"""
<article class="articulo">
 <h1>Acerca de RGNERA</h1>
 <div class="prosa">{cuerpo}</div>
 <div class="caja-sub"><b>Únete a la comunidad</b>
 <span>{"Recibe lo nuevo de RGNERA directo en tu correo." if SITE.get("substack") else "Lo nuevo de RGNERA sale primero en Instagram."}</span>{form_news(True)}</div>
</article>""")
    out.append(footer())
    return "".join(out)


def pagina_videos(videos):
    b = SITE["base"]
    out = [head("Videos — RGNERA", "Videos de RGNERA sobre sustentabilidad.", "videos/"), header("videos")]
    if videos:
        vids = "".join(f"""<div><div class="video-marco">
<iframe src="https://www.youtube-nocookie.com/embed/{v['id']}" title="{e(v['titulo'])}" loading="lazy" allowfullscreen></iframe>
</div><p class="video-titulo">{e(v['titulo'])}</p></div>""" for v in videos)
        cuerpo = f"""<section class="shell fila"><div class="grid" style="grid-template-columns:repeat(2,minmax(0,1fr))">{vids}</div></section>"""
    else:
        cuerpo = f"""<section class="shell fila"><div class="news-banda">
 <div class="texto"><b>Los videos están en mudanza</b>
 <span>Estamos moviendo «Plástico como recurso» a su nuevo canal. Vuelve pronto — mientras, te espera todo el archivo de la biblioteca.</span></div>
 <a class="btn-olivo" style="display:inline-block" href="{b}/articulos/">Ver artículos</a>
</div></section>"""
    out.append(f"""
<section class="shell cab-seccion"><h1>Videos</h1>
<p>Contenido audiovisual de RGNERA.</p></section>
{cuerpo}""")
    out.append(footer())
    return "".join(out)


def pagina_404():
    b = SITE["base"]
    out = [head("Página no encontrada — RGNERA", "Esta página no existe.", "404.html", noindex=True), header("")]
    out.append(f"""
<section class="shell cab-seccion" style="text-align:center;padding-bottom:60px">
 <h1>No encontramos esa página</h1>
 <p style="margin:14px auto">Quizá el artículo cambió de dirección con el sitio nuevo.</p>
 <p style="margin-top:20px"><a class="btn-primario" href="{b}/articulos/">Ver todos los artículos</a></p>
</section>""")
    out.append(footer())
    return "".join(out)


def redirect_stub(destino):
    return f"""<!DOCTYPE html><html lang="es-MX"><head><meta charset="utf-8">
<meta http-equiv="refresh" content="0; url={destino}">
<link rel="canonical" href="{destino}"><title>RGNERA</title></head>
<body><a href="{destino}">Este artículo se movió aquí</a></body></html>"""


# ---------------------------------------------------------------- feed y mapas
def feed_rss(posts):
    items = []
    for p in posts[:30]:
        items.append(f"""<item><title>{e(p['title'])}</title>
<link>{SITE['base']}/articulos/{p['slug']}/</link>
<guid>{SITE['base']}/articulos/{p['slug']}/</guid>
<pubDate>{fecha_rfc(p['fecha'])}</pubDate>
<description>{e(p['extracto'])}</description></item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>RGNERA</title>
<link>{SITE['base']}</link>
<description>{e(SITE['descripcion'])}</description>
<language>es-mx</language>
{''.join(items)}</channel></rss>"""


def sitemap(rutas):
    urls = "".join(f"<url><loc>{SITE['base']}/{r}</loc></url>" for r in rutas)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>"""


# ---------------------------------------------------------------- build
def main():
    posts = cargar_posts()
    videos = json.loads((CONT / "videos.json").read_text(encoding="utf-8")) if (CONT / "videos.json").exists() else []
    acerca_md = (CONT / "acerca.md").read_text(encoding="utf-8") if (CONT / "acerca.md").exists() else "Próximamente."

    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir()
    shutil.copytree(ASSETS, DOCS / "assets")
    (DOCS / ".nojekyll").write_text("")

    rutas = ["", "articulos/", "calculadora/", "acerca/", "videos/"]

    (DOCS / "index.html").write_text(pagina_home(posts, videos), encoding="utf-8")
    (DOCS / "articulos").mkdir()
    (DOCS / "articulos" / "index.html").write_text(pagina_articulos(posts), encoding="utf-8")
    for ck in CATS["canonicas"]:
        if any(p["cat"] == ck for p in posts):
            d = DOCS / "articulos" / ck
            d.mkdir()
            d.joinpath("index.html").write_text(pagina_articulos(posts, ck), encoding="utf-8")
            rutas.append(f"articulos/{ck}/")
    for i, p in enumerate(posts):
        ant = posts[i + 1] if i + 1 < len(posts) else None
        sig = posts[i - 1] if i > 0 else None
        d = DOCS / "articulos" / p["slug"]
        d.mkdir()
        d.joinpath("index.html").write_text(pagina_post(p, ant, sig), encoding="utf-8")
        rutas.append(f"articulos/{p['slug']}/")
        # stub de redirect desde la URL vieja de Wix (/post/<slug-viejo>)
        vieja = p.get("url", "")
        m = re.search(r"/post/(.+)$", vieja)
        if m:
            dv = DOCS / "post" / unquote(m.group(1))
            dv.mkdir(parents=True, exist_ok=True)
            dv.joinpath("index.html").write_text(
                redirect_stub(f"{SITE['base']}/articulos/{p['slug']}/"), encoding="utf-8")

    (DOCS / "calculadora").mkdir()
    (DOCS / "calculadora" / "index.html").write_text(pagina_calculadora(), encoding="utf-8")
    (DOCS / "acerca").mkdir()
    (DOCS / "acerca" / "index.html").write_text(pagina_acerca(acerca_md), encoding="utf-8")
    (DOCS / "videos").mkdir()
    (DOCS / "videos" / "index.html").write_text(pagina_videos(videos), encoding="utf-8")
    (DOCS / "404.html").write_text(pagina_404(), encoding="utf-8")
    (DOCS / "feed.xml").write_text(feed_rss(posts), encoding="utf-8")
    (DOCS / "sitemap.xml").write_text(sitemap(rutas), encoding="utf-8")
    (DOCS / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE['base']}/sitemap.xml\n", encoding="utf-8")

    # calculadora nativa: copia el build del repo hermano a /huella/
    calc = Path(SITE["calc_local"]) if SITE.get("calc_local") else None
    if calc and calc.exists():
        (DOCS / "huella").mkdir()
        chtml = calc.read_text(encoding="utf-8")
        chtml = chtml.replace("</head>",
            f'<link rel="canonical" href="{SITE["base"]}/calculadora/">\n</head>', 1)
        (DOCS / "huella" / "index.html").write_text(chtml, encoding="utf-8")
    if SITE.get("cname"):
        (DOCS / "CNAME").write_text(SITE["cname"] + "\n", encoding="utf-8")

    print(f"OK: {len(posts)} posts, {len(rutas)} rutas -> {DOCS}")


if __name__ == "__main__":
    main()
