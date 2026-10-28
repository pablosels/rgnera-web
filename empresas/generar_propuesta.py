# -*- coding: utf-8 -*-
"""Genera la propuesta de una página (PDF tamaño carta) de RGNERA para empresas.

Lee content/empresas.json (los mismos textos y precios de rgnera.com/empresas)
y escribe assets/empresas/rgnera-huella-empresas.pdf, que build.py publica y la
página enlaza. Requiere Playwright con Chromium (el de rgnera-factory).

Uso:  python empresas/generar_propuesta.py
"""
import html
import json
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
EMP = json.loads((RAIZ / "content" / "empresas.json").read_text(encoding="utf-8"))
FUENTES = RAIZ.parent / "rgnera-factory" / "assets" / "fonts"
EMBLEMA = RAIZ / "assets" / "img" / "emblema_cream.png"
SALIDA = RAIZ / "assets" / "empresas" / "rgnera-huella-empresas.pdf"


def e(s):
    return html.escape(s, quote=True)


def documento():
    h, c = EMP["hero"], EMP["caso"]
    recibes = "".join(f"<li><b>{e(r['titulo'])}.</b> {e(r['texto'])}</li>" for r in EMP["recibes"])
    pasos = "".join(f"<li><b>{e(p['titulo'])}.</b> {e(p['texto'])}</li>" for p in EMP["pasos"])
    datos = "".join(f"<div class='dato'><b>{e(d['cifra'])}</b><span>{e(d['texto'])}</span></div>"
                    for d in c["datos"])
    def primera(texto):     # en el PDF, solo la primera oración
        return texto.split(". ")[0].rstrip(".") + "."
    porque = "".join(f"<li><b>{e(p['titulo'])}.</b> {e(primera(p['texto']))}</li>" for p in EMP["porque"])
    precios = "".join(
        f"<div class='precio{' destacado' if p.get('destacado') else ''}'>"
        f"<h3>{e(p['nombre'])}</h3>"
        f"<p class='monto'>{e(p['precio'])} <small>{e(p['periodo'] + ' ') if p.get('periodo') else ''}+ IVA</small></p>"
        f"<p class='para'>{e(p['para'])}</p></div>"
        for p in EMP["paquetes"])
    f = FUENTES.as_uri()
    return f"""<!DOCTYPE html><html lang="es-MX"><head><meta charset="utf-8">
<style>
@font-face{{font-family:Playfair;src:url('{f}/PlayfairDisplay-Regular.ttf')}}
@font-face{{font-family:Poppins;src:url('{f}/Poppins-Regular.ttf');font-weight:400}}
@font-face{{font-family:Poppins;src:url('{f}/Poppins-Medium.ttf');font-weight:500}}
@font-face{{font-family:Poppins;src:url('{f}/Poppins-Bold.ttf');font-weight:700}}
@page{{size:Letter;margin:0}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:8.5in;height:11in;background:#F5F1E6;color:#20261A;font-family:Poppins;font-size:8.8pt;
  line-height:1.4;display:flex;flex-direction:column}}
.cab{{background:#475323;color:#F5F1E6;padding:22px 44px 18px;position:relative;overflow:hidden;flex-shrink:0}}
.cab:after{{content:"CO₂e";position:absolute;right:-6px;top:-30px;font-family:Playfair;font-size:118pt;
  font-weight:700;opacity:.07}}
.marca{{display:flex;align-items:center;gap:9px;font-weight:700;letter-spacing:2.5px;font-size:10.5pt}}
.marca img{{width:28px;height:28px}}
.eyebrow{{margin-top:12px;font-size:8pt;letter-spacing:2.5px;text-transform:uppercase;color:#AEB98C;font-weight:500}}
h1{{font-family:Playfair;font-weight:700;font-size:21pt;line-height:1.12;margin-top:4px;max-width:600px}}
.cab p.sub{{color:#e8e4d6;margin-top:9px;max-width:600px;font-size:10.2pt}}
main{{padding:18px 44px 0;display:grid;grid-template-columns:1.08fr 1fr;gap:26px;flex:1}}
h2{{font-family:Playfair;font-weight:700;color:#475323;font-size:13pt;margin:0 0 5px}}
ul,ol{{padding-left:15px}} li{{margin-bottom:3px}} li b{{color:#20261A}}
.bloque+.bloque{{margin-top:11px}}
.caso{{background:#FFFDF7;border:1px solid #E3DCCB;border-radius:12px;padding:12px 15px}}.caso p.intro{{font-size:8.8pt;color:#5d6352;margin-bottom:9px}}
.datos{{display:grid;grid-template-columns:1fr 1fr;gap:10px 14px}}
.dato b{{display:block;font-family:Playfair;font-weight:700;font-size:17pt;color:#C58A2E;line-height:1.05}}
.dato span{{font-size:8.6pt;color:#3c4233}}
.caso .nota{{margin-top:10px;font-size:8.6pt;color:#5d6352;border-top:1px solid #E3DCCB;padding-top:8px}}
.precios{{padding:12px 44px 0;flex-shrink:0}}
.fila-precios{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}
.precio{{background:#FFFDF7;border:1px solid #E3DCCB;border-radius:11px;padding:11px 14px}}
.precio.destacado{{border:2px solid #C58A2E}}
.precio h3{{font-family:Playfair;color:#475323;font-size:12pt}}
.monto{{font-family:Playfair;font-weight:700;font-size:19pt;line-height:1.15}}
.monto small{{font-family:Poppins;font-size:8pt;font-weight:500;color:#6b6f60}}
.para{{font-size:8.4pt;color:#5d6352}}
.notas{{margin-top:9px;font-size:8.5pt;color:#3c4233}}
.lanz{{margin-top:7px;background:#fbf0dc;border:1px solid #ecd3a4;border-radius:8px;padding:6px 11px;
  font-size:8.8pt;color:#3d2907;font-weight:500}}
.pie{{flex-shrink:0;margin-top:auto;background:#20261A;color:#F5F1E6;padding:10px 44px;display:flex;
  justify-content:space-between;align-items:center;font-size:9.4pt}}
.pie b{{color:#C58A2E}}
</style></head><body>
<header class="cab">
 <div class="marca"><img src="{EMBLEMA.as_uri()}" alt="">RGNERA</div>
 <p class="eyebrow">{e(h['eyebrow'])}</p>
 <h1>{e(h['titulo'])}</h1>
 <p class="sub">{e(h['texto'])}</p>
</header>
<main>
 <div>
  <div class="bloque"><h2>Qué recibes</h2><ul>{recibes}</ul></div>
  <div class="bloque"><h2>Cómo funciona</h2><ol>{pasos}</ol></div>
 </div>
 <div>
  <div class="bloque caso"><h2>{e(c['titulo'])}</h2><p class="intro">{e(c['texto'])}</p>
   <div class="datos">{datos}</div><p class="nota">{e(c['nota'])}</p></div>
  <div class="bloque"><h2>Por qué RGNERA</h2><ul>{porque}</ul></div>
 </div>
</main>
<section class="precios">
 <h2>Precios</h2>
 <div class="fila-precios">{precios}</div>
 <p class="notas">En pesos mexicanos, más IVA. {e(EMP['verificacion'])}</p>
 <p class="lanz">{e(EMP['lanzamiento'])}</p>
</section>
<footer class="pie"><span><b>Pablo Seldner</b> · {e(EMP['contacto'])}</span><span>rgnera.com/empresas</span></footer>
</body></html>"""


def main():
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        fuente = Path(tmp) / "propuesta.html"
        fuente.write_text(documento(), encoding="utf-8")
        with sync_playwright() as p:
            try:
                nav = p.chromium.launch()
            except Exception:       # sin Chromium de Playwright: usa el Edge de Windows
                nav = p.chromium.launch(channel="msedge")
            pag = nav.new_page()
            pag.goto(fuente.as_uri())
            pag.wait_for_timeout(400)
            alto = pag.evaluate("document.documentElement.scrollHeight")
            cols = pag.evaluate("[...document.querySelectorAll('main > div')]"
                                ".map(d => Math.round(d.getBoundingClientRect().height))")
            pag.pdf(path=str(SALIDA), format="Letter", print_background=True,
                    margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
            if "--png" in sys.argv:
                pag.set_viewport_size({"width": 816, "height": 1056})
                pag.screenshot(path=str(SALIDA.with_suffix(".png")), full_page=True)
            nav.close()
    print(f"OK: {SALIDA} (alto del contenido {alto}px; una carta = 1056px; columnas {cols})")


if __name__ == "__main__":
    main()
