#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""publicar.py — publica en rgnera.com lo que ya tocó por calendario.

Flujo (idempotente — si no hay nada nuevo no comitea nada):
  1. git pull --ff-only en main
  2. python build.py   (excluye posts con fecha futura, ver cargar_posts)
  3. sincroniza docs/ al worktree de gh-pages y hace commit+push si hay cambios

GitHub Pages sirve la rama gh-pages (raíz), NO main:/docs — por eso el paso 3.
Pensado para correrse L/M/V desde la tarea programada, o a mano cuando quieras.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).parent
DOCS = RAIZ / "docs"
WORKTREE = RAIZ.parent / "rgnera-ghpages"


def run(*cmd, cwd=RAIZ, check=True):
    r = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if check and r.returncode != 0:
        print(r.stdout)
        print(r.stderr)
        sys.exit(f"FALLO: {' '.join(cmd)}")
    return (r.stdout or "").strip()


def main():
    print(run("git", "pull", "--ff-only"))

    salida = run(sys.executable, "build.py")
    print(salida)

    if not WORKTREE.exists():
        run("git", "worktree", "add", str(WORKTREE), "gh-pages")
    run("git", "fetch", "origin", cwd=WORKTREE)
    run("git", "reset", "--hard", "origin/gh-pages", cwd=WORKTREE)

    # espejo: docs/ -> worktree (se conserva solo .git)
    for hijo in WORKTREE.iterdir():
        if hijo.name == ".git":
            continue
        shutil.rmtree(hijo) if hijo.is_dir() else hijo.unlink()
    shutil.copytree(DOCS, WORKTREE, dirs_exist_ok=True)

    run("git", "add", "-A", cwd=WORKTREE)
    cambios = run("git", "status", "--porcelain", cwd=WORKTREE)
    if not cambios:
        print("sin cambios: no hay nada que publicar hoy")
        return

    # "A  articulos/<slug>/index.html" = página nueva; se excluyen los índices de categoría
    cats = set(json.loads((RAIZ / "content" / "categorias.json").read_text(encoding="utf-8"))["canonicas"])
    nuevos = sorted({m.group(1) for l in cambios.splitlines()
                     for m in [re.match(r"A\s+articulos/([^/]+)/index\.html$", l)]
                     if m and m.group(1) not in cats})
    msg = ("Publicación programada: " + ", ".join(nuevos)) if nuevos else "Rebuild del sitio"
    run("git", "commit", "-m", msg, cwd=WORKTREE)
    print(run("git", "push", "origin", "gh-pages", cwd=WORKTREE))

    if nuevos:
        print("PUBLICADO:")
        for n in nuevos:
            print(f"  https://rgnera.com/articulos/{n}/")
    else:
        print("PUBLICADO: cambios generales del sitio (sin artículo nuevo)")


if __name__ == "__main__":
    main()
