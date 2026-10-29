# -*- coding: utf-8 -*-
"""Genera 'chinampa-NN para pegar.html' y '.txt' desde chinampa-NN.md.

Uso:  python chinampa_pegar.py 11 12

El .html (se abre en el navegador; Ctrl+A, Ctrl+C, Ctrl+V en Substack conserva h3, cita,
negritas y links) y el .txt van a Escritorio\\La Chinampa y a Dropbox\\RGNERA\\La Chinampa;
el .txt también se queda en este repo. Reproduce byte por byte el formato de la edición 10.
"""
import html
import re
import shutil
import sys
from pathlib import Path

import markdown

WEB = Path(__file__).resolve().parent
DESTINOS = [Path(r"C:\Users\minis\Dropbox\RGNERA\La Chinampa"),
            Path(r"C:\Users\minis\OneDrive\Desktop\La Chinampa")]

CABEZA = """<!doctype html><meta charset="utf-8"><title>La Chinampa #{n} — para pegar</title>
<style>body{{font:17px/1.6 Georgia,serif;max-width:680px;margin:32px auto;padding:0 16px}}
.aviso{{font:14px system-ui;background:#fff4d6;border:1px solid #e0c060;padding:10px 14px;border-radius:6px;margin-bottom:24px}}
blockquote{{border-left:3px solid #999;margin-left:0;padding-left:16px;color:#333}}</style>
<div class="datos" style="font:14px system-ui;background:#eef6ee;border:1px solid #9c9;padding:10px 14px;border-radius:6px;margin-bottom:12px"><b>Para copiar en los campos de Substack</b> (no van dentro del cuerpo):<br><b>Título:</b> {titulo}<br><b>Subtítulo:</b> {subtitulo}<br><b>Sección:</b> {seccion}<br><b>Programar:</b> {programar}</div>
<div class="aviso">Haz clic en el texto de abajo, <b>Ctrl+A</b> (selecciona todo el artículo), <b>Ctrl+C</b> y pégalo en Substack con <b>Ctrl+V</b>. Los subtítulos, la cita y las negritas se pegan ya con formato. Este recuadro amarillo no se copia si seleccionas desde el texto.</div>
<article contenteditable="true">"""
PIE = """</article>
<script>document.querySelector('article').addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key==='a'){e.preventDefault();const r=document.createRange();r.selectNodeContents(e.target);const s=getSelection();s.removeAllRanges();s.addRange(r);}});</script>"""


def seccion(texto: str, titulo: str) -> str:
    m = re.search(rf"^## {re.escape(titulo)}\s*\n(.*?)(?=^## |\Z)", texto, re.S | re.M)
    return m.group(1).strip()


def generar(n: str):
    md = (WEB / f"chinampa-{n}.md").read_text(encoding="utf-8")
    titulo = seccion(md, "Título")
    subtitulo = seccion(md, "Subtítulo")
    sec = re.search(r"\*\*Sección:\*\*\s*([^·\n]+?)\s*·", md).group(1)
    dia = re.search(r"^# La Chinampa #\d+ — (.+)$", md, re.M).group(1).strip()
    anio = re.search(r"\*\*Programar:\*\*[^\n]*?(\d{4})", md).group(1)
    programar = f"{dia} de {anio}, 8:00 a.m. (hora de Ciudad de México)"
    cuerpo = re.sub(r"\n-{3,}\s*$", "", seccion(md, "Cuerpo")).strip()
    pagina = CABEZA.format(n=n, titulo=html.escape(titulo), subtitulo=html.escape(subtitulo),
                           seccion=html.escape(sec), programar=html.escape(programar))
    txt = WEB / f"chinampa-{n} para pegar.txt"
    txt.write_text(cuerpo + "\n", encoding="utf-8")
    for d in DESTINOS:
        d.mkdir(parents=True, exist_ok=True)
        (d / f"chinampa-{n} para pegar.html").write_text(pagina + markdown.markdown(cuerpo) + PIE,
                                                          encoding="utf-8")
        shutil.copy2(txt, d / txt.name)
    print(f"chinampa-{n}: {programar} · {len(cuerpo.split())} palabras -> {', '.join(map(str, DESTINOS))}")


if __name__ == "__main__":
    for n in sys.argv[1:] or sys.exit(__doc__):
        generar(n)
