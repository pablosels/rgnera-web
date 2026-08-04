# -*- coding: utf-8 -*-
"""Genera portadas 1200x675 para los 3 articulos nuevos de rgnera.com
con la identidad RGNERA (brand.py de la factory)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WEB = Path(r"C:\Users\minis\rgnera-web")
FONTS = Path(r"C:\Users\minis\rgnera-factory\assets\fonts")
EMBLEM = WEB / "assets" / "img" / "emblema_cream.png"

W, H = 1200, 675
DARK_CENTER = (43, 52, 25)    # #2B3419
DARK_EDGE = (25, 31, 14)      # #191F0E
CREAM = (245, 241, 230)       # #F5F1E6
AMBER = (197, 138, 46)        # #C58A2E
SAGE_LIGHT = (174, 185, 140)  # #AEB98C

playfair = lambda s: ImageFont.truetype(str(FONTS / "PlayfairDisplay-Regular.ttf"), s)
poppins_m = lambda s: ImageFont.truetype(str(FONTS / "Poppins-Medium.ttf"), s)
poppins_b = lambda s: ImageFont.truetype(str(FONTS / "Poppins-Bold.ttf"), s)


def fondo():
    """Gradiente radial DARK_CENTER -> DARK_EDGE, calibrado al sample IG."""
    img = Image.new("RGB", (W, H))
    px = img.load()
    cx, cy = W / 2, H / 2
    maxd = (cx ** 2 + cy ** 2) ** 0.5
    for y in range(H):
        for x in range(W):
            t = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / maxd
            px[x, y] = tuple(round(c + (e - c) * t) for c, e in zip(DARK_CENTER, DARK_EDGE))
    return img


def portada(slug, kicker, lineas, title_size=88):
    img = fondo()
    d = ImageDraw.Draw(img)
    mx = 90
    # emblema
    emb = Image.open(EMBLEM).convert("RGBA")
    eh = 68
    emb = emb.resize((round(emb.width * eh / emb.height), eh), Image.LANCZOS)
    img.paste(emb, (mx, 74), emb)
    # kicker (categoria) en ambar
    d.text((mx, 178), kicker, font=poppins_b(26), fill=AMBER)
    # titulo Playfair crema
    f = playfair(title_size)
    y = 232
    for linea in lineas:
        d.text((mx, y), linea, font=f, fill=CREAM)
        y += round(title_size * 1.18)
    # regla ambar
    d.rectangle([mx, y + 26, mx + 110, y + 32], fill=AMBER)
    # masthead abajo
    d.text((mx, H - 74), "RGNERA · biblioteca sustentable", font=poppins_m(26), fill=SAGE_LIGHT)
    out = WEB / "assets" / "img" / "posts" / slug
    out.mkdir(parents=True, exist_ok=True)
    img.save(out / "00.jpg", "JPEG", quality=88, optimize=True)
    print("OK", out / "00.jpg")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(
        description="Portada de marca 1200x675 para un artículo. "
                    'Ej: python portada.py mi-slug "AGUA" "Cosecha de lluvia:|el agua de tu techo" --size 76')
    ap.add_argument("slug", help="carpeta destino en assets/img/posts/<slug>/00.jpg")
    ap.add_argument("kicker", help="categoría en mayúsculas")
    ap.add_argument("lineas", help="título con | separando las líneas")
    ap.add_argument("--size", type=int, default=88, help="tamaño del título (default 88)")
    a = ap.parse_args()
    portada(a.slug, a.kicker, a.lineas.split("|"), a.size)
