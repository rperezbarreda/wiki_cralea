#!/usr/bin/env python3
# =========================================
# EL MENÚ DE LA WIKI
# =========================================
# La wiki va sola, sin el menú del blog, así que lleva el suyo: el mismo
# componente (la barra lateral que se pliega con ☰ y que en el móvil es un
# cajón) con lo de la wiki dentro. Se escribe en
#
#     fragmentos/menu-wiki.html
#
# y actualizar-cabeceras.py lo copia en cada página de la wiki, con la
# página en la que estás marcada y su apartado abierto (igual que el del
# blog). NO SE TOCA A MANO: sale de los datos de la wiki, así que una
# sección con su primera página, un mapa nuevo o una utilidad nueva
# aparecen solos al pasar esto (lo pasa generar-mundo.py).
#
# QUÉ LLEVA, de arriba abajo:
#     buscar en la wiki     un formulario de verdad: manda a la portada
#                           con ?buscar=, que ya sabe buscar
#     portada
#     el mundo              cada parte del mundo (el
#                           "orden" de Mapamundi en mundo-categorias.json)
#     secciones             las de mundo-categorias.json que tengan alguna
#                           página; abren su ventana en la portada
#                           (#seccion-…). Las vacías no salen: un menú no
#                           es una lista de deseos (en la portada sí salen)
#     el tiempo             la línea de tiempo, el calendario y el conversor
#     mapas                 todos los mapas, el mapamundi primero
#     herramientas          las utilidades y «cómo se escribe esto»
#     ← richi.blog          el único enlace al blog, abajo y discreto
#
# Con --probar enseña el menú y no escribe nada.
import html
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "0-comun"))
from comun import WEB, WIKI_WEB, RAIZ  # noqa: E402

# Dónde vive la wiki en la web (comun.URL).
from comun import URL  # noqa: E402
PORTADA = URL + "index.html"
SALIDA_WEB = WIKI_WEB
INDICE = WEB / "wiki" / "datos" / "mundo.json"
CATEGORIAS = WEB / "wiki" / "datos" / "mundo-categorias.json"
DESTINO = WIKI_WEB / "fragmentos" / "menu-wiki.html"

NOMBRE = "WIKI CRALËA"
# La wiki se publica DENTRO de richi.blog, así que el blog es la raíz.
BLOG = "/"

# Lo que va en su propio apartado y no en «secciones».
APARTE = {"mapamundi", "mapas", "herramientas"}


def sin_tildes(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def id_de(texto):
    """Como idDeSubMundo en mundo.js, sin el «mundo-» de delante."""
    return re.sub(r"[^a-z0-9]+", "-", sin_tildes(str(texto)).lower()).strip("-")


def e(texto):
    return html.escape(str(texto), quote=True)


def enlace(url, texto, sangria, marca=None):
    """marca: la carpeta cuyas páginas marcan este enlace en el menú (las
    secciones, que llevan a la portada y no tienen dirección propia)."""
    extra = ' data-marca="%s"' % e(marca) if marca else ""
    return '%s<a href="%s"%s>%s</a>' % (" " * sangria, e(url), extra, e(texto))


def grupo(nombre, enlaces, sangria=12):
    """Un apartado plegable, con las mismas clases que el menú del blog
    (barra-lateral.js lo abre y lo cierra, y actualizar-cabeceras.py lo
    deja abierto si estás en una de sus páginas)."""
    if not enlaces:
        return ""
    s = " " * sangria
    lineas = [
        s + '<div class="nav-group">',
        s + '    <button class="nav-toggle" type="button" aria-expanded="false">',
        s + "        <span>%s</span>" % e(nombre),
        s + '        <span class="arrow" aria-hidden="true">+</span>',
        s + "    </button>",
        "",
        s + '    <div class="submenu">',
    ]
    lineas += [enlace(*cosa[:2], sangria + 8, *cosa[2:]) for cosa in enlaces]
    lineas += [s + "    </div>", s + "</div>", ""]
    return "\n".join(lineas)


def titulo_de(ficha):
    return (ficha.get("titulo") or Path(ficha.get("url", "")).stem.replace("_", " ")).strip()


def los_mapas(por_url):
    """(url, nombre) de cada mapa publicado: el mapamundi primero y los
    demás por el nombre de su página («Reino de Prunia»)."""
    mapas = []
    for archivo in SALIDA_WEB.rglob("mapa_*.html"):
        relativo = archivo.relative_to(SALIDA_WEB).as_posix()
        url = URL + relativo
        # La página de la que es el mapa: el mismo nombre sin «mapa_».
        pagina = url[: url.rfind("/") + 1] + archivo.name[len("mapa_"):]
        ficha = por_url.get(pagina) or por_url.get(url)
        if ficha:
            nombre = titulo_de(ficha)
        else:
            nombre = archivo.stem[len("mapa_"):].replace("_", " ").capitalize()
        mapas.append((url, nombre))
    mapas.sort(key=lambda m: (0 if "mapamundi" in m[0].rsplit("/", 1)[-1] else 1, sin_tildes(m[1]).lower()))
    return mapas


def montar():
    fichas = json.loads(INDICE.read_text(encoding="utf-8"))
    categorias = json.loads(CATEGORIAS.read_text(encoding="utf-8"))
    por_url = {f["url"]: f for f in fichas if f.get("url")}
    por_titulo = {sin_tildes(titulo_de(f)).lower(): f for f in fichas}

    def busca(*trozos):
        """La primera ficha cuya dirección lleve todos esos trozos."""
        for f in fichas:
            if all(t in f.get("url", "") for t in trozos):
                return f
        return None

    # EL MUNDO: sus partes. Una parte con página lleva a ella; la que no
    # la tiene (Archipiélagos) abre su parte en la portada. El mapamundi va
    # el primero de «mapas» (dos veces el mismo enlace en un menú es
    # ruido para quien lo escucha).
    mundo = []
    orden = next((c.get("orden", []) for c in categorias if c["nombre"].lower() == "mapamundi"), [])
    for parte in orden:
        ficha = por_titulo.get(sin_tildes(parte).lower())
        if ficha:
            mundo.append((ficha["url"], parte))
        else:
            # Sin página: abre su parte en la portada, y sus páginas (las de
            # su carpeta) la marcan en el menú.
            carpeta = "mapamundi/" + id_de(parte).replace("-", "_") + "/"
            marca = URL + carpeta if (SALIDA_WEB / carpeta).is_dir() else None
            mundo.append((PORTADA + "#mundo-" + id_de(parte), parte, marca))

    # SECCIONES: las que tienen algo, en el orden del archivo.
    cuantas = {}
    for f in fichas:
        g = (f.get("grupo") or "lo demás").strip().lower()
        cuantas[g] = cuantas.get(g, 0) + 1
    ayuda = busca("como_se_escribe_esto")
    if ayuda and cuantas.get("lo demás"):
        cuantas["lo demás"] -= 1          # va en herramientas
    nombres = [c["nombre"] for c in categorias] + ["lo demás"]
    # La carpeta de cada sección: donde tiene más páginas, si ninguna otra
    # sección tiene páginas ahí dentro (religiones/panteon/ sí; la raíz de
    # la wiki, no). Es lo que hace que en una deidad se marque «religiones».
    paginas_en = {}
    for f in fichas:
        g = (f.get("grupo") or "lo demás").strip().lower()
        carpeta = f["url"][: f["url"].rfind("/") + 1]
        paginas_en.setdefault(g, {}).setdefault(carpeta, 0)
        paginas_en[g][carpeta] += 1

    def marca_de(g):
        if not paginas_en.get(g):
            return None
        c = max(paginas_en[g].items(), key=lambda par: par[1])[0]
        ajenas = any(carpeta.startswith(c) for o, cs in paginas_en.items() if o != g for carpeta in cs)
        return None if c == URL or ajenas else c

    secciones = []
    for nombre in dict.fromkeys(nombres):
        if nombre.lower() in APARTE or not cuantas.get(nombre.lower()):
            continue
        secciones.append((PORTADA + "#seccion-" + id_de(nombre), nombre, marca_de(nombre.lower())))

    # EL TIEMPO
    tiempo = []
    for trozos, texto in ((("linea_de_tiempo.html",), "línea de tiempo"),
                          (("/calendario/",), "calendario"),
                          (("conversor_de_fechas",), "conversor de fechas")):
        f = busca(*trozos)
        if f:
            tiempo.append((f["url"], texto))
    puestas = {u for u, _ in tiempo}

    # HERRAMIENTAS: las utilidades que no están ya en «el tiempo».
    herramientas = sorted(
        ((f["url"], titulo_de(f).lower()) for f in fichas
         if (f.get("grupo") or "").lower() == "herramientas" and f["url"] not in puestas),
        key=lambda h: sin_tildes(h[1]))
    if ayuda:
        herramientas.append((ayuda["url"], "cómo se escribe esto"))

    mapas = los_mapas(por_url)

    partes = [
        '<header class="mobile-topbar">',
        '    <button id="sidebar-toggle" class="sidebar-toggle" type="button" aria-expanded="false" aria-controls="sidebar">',
        '        <span aria-hidden="true">☰</span>',
        '        <span class="visually-hidden">Abrir menú</span>',
        "    </button>",
        '    <p class="mobile-topbar-title"><span aria-hidden="true">·🜏·</span> %s</p>' % NOMBRE,
        "</header>",
        "",
        "<!--! fragmento: ajustes -->",
        "",
        '<div id="sidebar-backdrop" class="sidebar-backdrop" hidden></div>',
        "",
        '<aside class="sidebar" id="sidebar" aria-label="Menú de la wiki">',
        '    <div class="sidebar-logo">',
        '        <p><span aria-hidden="true">·🜏·</span> %s</p>' % NOMBRE,
        "    </div>",
        '    <button id="lateral-plegar" class="lateral-plegar" type="button"',
        '            aria-expanded="true" aria-controls="sidebar-menu" title="Plegar el menú">',
        '        <span aria-hidden="true">☰</span>',
        '        <span class="visually-hidden">Menú</span>',
        "    </button>",
        '    <div class="sidebar-top" id="sidebar-menu">',
        '        <form class="menu-wiki-buscar" role="search" action="%s" method="get">' % e(PORTADA),
        '            <label class="visually-hidden" for="menu-wiki-q">Buscar en la wiki</label>',
        '            <input id="menu-wiki-q" name="buscar" type="search" placeholder="buscar…"',
        '                   autocomplete="off" spellcheck="false">',
        '            <button type="submit">',
        '                <span class="buscar-lupa" aria-hidden="true"></span>',
        '                <span class="visually-hidden">Buscar</span>',
        "            </button>",
        "        </form>",
        "",
        "        <nav>",
        enlace(PORTADA, "portada", 12),
        grupo("el mundo", mundo),
        grupo("secciones", secciones),
        grupo("el tiempo", tiempo),
        grupo("mapas", mapas),
        grupo("herramientas", herramientas),
        "        </nav>",
        "",
        '        <p class="menu-wiki-blog"><a href="%s">' % BLOG
        + '<span aria-hidden="true">← </span>richi.blog</a></p>',
        "    </div>",
        "</aside>",
    ]
    return "\n".join(p for p in partes if p != "") + "\n"


def main():
    menu = montar()
    if "--probar" in sys.argv:
        print(menu)
        return
    viejo = DESTINO.read_text(encoding="utf-8") if DESTINO.is_file() else None
    if viejo == menu:
        print("  El menú de la wiki ya estaba al día.")
        return
    DESTINO.write_text(menu, encoding="utf-8", newline="\n")
    print("  Escrito fragmentos/menu-wiki.html.")


if __name__ == "__main__":
    main()
