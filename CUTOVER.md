# Plan de cutover: rgnera.com de Wix → GitHub Pages + Substack

Decisión (25-jul-2026): sitio en GitHub Pages (este repo) + newsletter en Substack
(`news.rgnera.com`). Costo recurrente: $0/mes. Único pago: $50 USD (una vez) por el
dominio custom en Substack. Se cancela el plan de sitio de Wix (~$200-500 USD/año de ahorro).

Dato del dominio: rgnera.com está registrado vía Wix (reseller de GoDaddy),
nameservers `ns2/ns3.wixdns.net`, expira 2027-01-18. El correo @rgnera.com usa
Google Workspace con MX en el DNS de Wix — **no tocar MX ni SPF**.

## Fase 1 — Respaldo (PABLO, antes que nada)

1. En el dashboard de Wix: **Contacts → exportar CSV** (filtrando "Subscribed") — es la
   lista para importar a Substack después.
2. **Forms & Submissions → exportar** cada formulario.
3. **Media Manager → descargar** los 2 videos propios ("Plástico como recurso" ES y EN),
   más cualquier logo/imagen original que quieras conservar.
4. Subir esos 2 videos a un canal de YouTube de RGNERA (los videos hosteados en Wix
   mueren al cancelar; en YouTube los embebemos gratis en /videos/).

## Fase 2 — Publicar el sitio en staging (PABLO 1 min + CLAUDE)

5. [PABLO] Crear el repo en GitHub: <https://github.com/new> → Owner `pablosels`,
   nombre **`rgnera-web`**, público, SIN readme/gitignore. (O autorizar a Claude a
   crearlo con la credencial git guardada.)
6. [CLAUDE] Push del sitio + rama `gh-pages`; verificar que quede en vivo en
   `https://pablosels.github.io/rgnera-web/`. Si Pages no se activa solo:
   [PABLO] repo → Settings → Pages → Branch `gh-pages` / root.
7. [PABLO] Revisar el staging y dar visto bueno al diseño.

## Fase 3 — Newsletter (PABLO ~20 min, con guía)

8. Crear la publicación en <https://substack.com> con p.seldners@gmail.com:
   nombre "RGNERA", subir logo (assets/img/emblema.png de este repo), acento olivo.
   Crear secciones = categorías del sitio.
9. (Opcional, recomendado) Pagar los $50 USD del custom domain y configurar
   `news.rgnera.com`; Substack entrega un CNAME target — guardarlo para la fase 4.
10. Importar el CSV de contactos de Wix (Settings → Import).
11. [CLAUDE] Poner la URL de Substack en `content/site.json` → recompilar → los
    formularios de suscripción del sitio se activan.

## Fase 4 — Cambio de DNS (PABLO ~15 min, con Claude verificando)

En Wix: Dashboard → Domains → rgnera.com → **Manage DNS Records**. NO transferir
el dominio todavía; solo editar registros. **No tocar MX (Google) ni TXT SPF.**

12. Borrar el/los registros **A** del apex (@) que apuntan a Wix y poner los 4 de
    GitHub Pages: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`.
13. Cambiar el **CNAME de www** (hoy `cdn1.wixdns.net`) → `pablosels.github.io`.
14. Agregar **CNAME news** → el target que dio Substack (paso 9).
15. [CLAUDE] Actualizar `content/site.json`: `"cname": "rgnera.com"` y
    `"base": "https://rgnera.com"` → rebuild → push. En GitHub: Settings → Pages →
    Custom domain `rgnera.com` + Enforce HTTPS (cuando emita el certificado).
16. [CLAUDE] Verificación completa: home, artículos, /calculadora/, redirects de URLs
    viejas (/post/…), feed.xml, y que el correo @rgnera.com siga vivo.

## Fase 5 — Cierre (PABLO)

17. Con todo verificado unos días, **cancelar el plan de sitio de Wix** (el dominio
    sigue registrado y gestionable en Wix; solo se cancela el plan del sitio).
    Confirmar que el panel DNS sigue accesible después de cancelar.
18. (Opcional, antes de oct-2026 y NUNCA en los 30 días previos al vencimiento
    2027-01-18) Transferir el registro a Cloudflare/Namecheap (~$10-12/año):
    recrear ahí TODOS los registros (A, CNAME, MX de Google, SPF) antes de cambiar.

## Riesgos y mitigaciones

- **Correo**: cualquier error con MX tumba @rgnera.com → captura de pantalla de los
  registros actuales ANTES de editar; Claude verifica MX después de cada cambio.
- **Propagación**: hasta 48 h (TTL 1 h); hacer el cambio de DNS en un momento tranquilo.
- **Contactos Wix**: exportar ANTES de cancelar; después no hay acceso.
- **Rutina editorial**: las ediciones nuevas se escriben en Substack (newsletter);
  el sitio publica evergreen vía markdown + `python build.py` + push.
