#!/usr/bin/env python3
# =========================================
# ESCRIBE EL BLOQUE DE CSS DE CADA PÁGINA
# =========================================
# Antes había un script (cargador-estilos.js) que, ya dentro del
# navegador, miraba la URL y escribía los <link> del CSS que esa página
# necesitaba. Funcionaba, pero costaba tiempo: el navegador tenía que
# pedir ese script y ejecutarlo ANTES de enterarse siquiera de que
# existía el CSS. Dos viajes de ida y vuelta al servidor antes de poder
# pintar nada, que en un móvil con mala cobertura eran ~200 ms de
# pantalla en blanco.
#
# Ahora los <link> van escritos en el <head> de cada página, así que el
# navegador los ve en cuanto le llega el HTML y los pide de inmediato.
# Los archivos de CSS siguen sueltos, uno por cosa, que es lo que hace
# que a partir de la segunda página casi todo salga de la caché.
#
# Para no tener que acordarse de qué lleva cada página, la lista se
# sigue decidiendo en UN SOLO SITIO: la función "hojas_de()" de aquí
# abajo. Esta herramienta la aplica a todas las páginas de golpe.
#
# TAMBIÉN PONE LA VERSIÓN ANTI-CACHÉ
# ----------------------------------
# El navegador se guarda el CSS y el JS para no volver a pedirlos, así
# que al subir cambios a Neocities quien ya había entrado en la web
# sigue viendo los viejos durante días. Por eso cada archivo va con su
# versión pegada a la dirección:
#
#     <link rel="stylesheet" href="/wiki/estilos/base.css?v=8f3a1c2d">
#
# Ese v= son los primeros ocho caracteres de un resumen (sha1) del
# CONTENIDO del archivo, así que cambia solo cuando el archivo cambia
# de verdad: el navegador se vuelve a bajar lo que has tocado y sigue
# usando de su caché todo lo demás.
#
# Esta herramienta escribe ese v= en dos sitios:
#   1. Los <link> del CSS y el <script> del cargador, en cada página.
#   2. La lista VERSIONES de scripts/cargador-scripts.js, que es de
#      donde salen los ?v= de los demás JS y de los fragmentos.
# Los JSON de datos/ no llevan v= a propósito: cambian cada vez que
# publicas algo y se piden con cache: "no-cache" (está explicado en
# cargador-scripts.js).
#
# EN ESTE REPOSITORIO la web es sitio/ y la wiki está en sitio/wiki/ (se
# ve en /wiki/, como en richi.blog/wiki/). Las direcciones que salen aquí
# ("/wiki/estilos/base.css") son las de la web, y el archivo es el mismo
# camino dentro de sitio/.
#
# CÓMO USARLO
# -----------
# Desde la carpeta raíz del repositorio:
#
#     python3 herramientas/3-generadores/actualizar-cabeceras.py
#
# Te dice qué páginas ha cambiado y cuáles ya estaban bien. Si solo
# quieres ver qué haría, sin tocar nada:
#
#     python3 herramientas/3-generadores/actualizar-cabeceras.py --probar
#
# CUÁNDO HAY QUE EJECUTARLO
# -------------------------
#   - SIEMPRE ANTES DE SUBIR, si has tocado algún CSS o algún JS. Es lo
#     que hace que el cambio se vea en la web sin que nadie tenga que
#     hacer ctrl+F5.
#   - Cuando creas un archivo de CSS nuevo, o borras uno.
#   - Cuando cambias qué páginas usan qué (por ejemplo, si un día la
#     página de accesibilidad pasa a usar portada.css).
#   - Cuando añades un tipo de página que no existía.
# Publicar una entrada o un relato no necesita que te acuerdes:
# nuevo.py y publicar.py la pasan ellos solos (la página nueva
# necesita su bloque de CSS de todas formas). Y subir fotos o añadir
# algo al portfolio tampoco hace falta: eso solo cambia los JSON de
# datos/, que no llevan v= justamente por esto.
#
# NOTA: esta carpeta "herramientas" es solo para ti — no hace falta
# subirla a Neocities.

import sys
from pathlib import Path

# comun.py vive un piso más arriba, en herramientas/, y Python solo busca
# los imports en la carpeta del propio archivo. Sin esta línea, al estar
# esto dentro de una subcarpeta, "from comun import ..." no lo encuentra.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "0-comun"))

import hashlib
import re

from comun import APPS_APARTE, leer_texto, escribir_texto
from comun import RAIZ as REPO
# Aquí RAIZ es la raíz de la WEB (sitio/): una dirección "/wiki/x" es el
# archivo RAIZ / "wiki/x".
from comun import WEB as RAIZ
# El CSS y el JS sin comentarios, que es lo que se sirve (ver ligero.py).
from ligero import sin_comentarios

# Las plantillas son páginas a medio hacer: no tienen URL propia, así
# que se les dice a mano qué tipo de página van a ser al copiarse.
PLANTILLAS = {
    "herramientas/plantillas/mundo-index.html": "/wiki/index.html",
    "herramientas/plantillas/mundo-pagina.html": "/wiki/lugares/una-pagina.html",
    "herramientas/plantillas/mundo-mapa.html": "/wiki/mapa_un_mapa.html",
    "herramientas/plantillas/mundo-linea.html": "/wiki/linea-de-tiempo/linea_de_tiempo.html",
}

# Lo que hay dentro de la web y no son páginas: los trozos de HTML que se
# copian dentro de las demás.
FUERA = {"fragmentos"} | APPS_APARTE


# =========================================
# QUÉ CSS LLEVA CADA PÁGINA
# =========================================
# Esta es la única lista que hay que tocar. El orden importa: se
# escriben en el mismo orden en el <head>, y el de más abajo gana si dos
# dicen cosas distintas sobre lo mismo.

# Hojas que van al FINAL de la lista de cualquier página, después de las
# de su sección. Cuando dos reglas pesan lo mismo gana la que se carga
# después, así que aquí abajo va lo que tiene que poder con lo que haya
# puesto cualquier página.
#
# Por ahora solo las ventanas que se plieguen: plegar una consiste en
# esconder todo lo que no sea su barra de título, y eso tiene que ganarle
# al display (flex, grid, block...) que su página le haya dado a esos
# trozos. Así se consigue sin inflar los selectores ni usar !important,
# que en esta web no aparece en ningún archivo.
ULTIMAS = [
    "/wiki/estilos/componentes/ventanas-plegables.css",
    # Cómo sale la web en papel. Va aquí abajo porque tiene que poder
    # con el estilo de cualquier página: en papel se quita el menú, los
    # botones y los fondos, salga de donde salga.
    "/wiki/estilos/componentes/impresion.css",
    # Y lo último de lo último: el mando de "dejarlo todo quieto". Tiene
    # que poder parar CUALQUIER animación o transición de cualquier
    # página, así que estando al final le gana a todas sin tener que
    # inflar sus selectores ni usar !important.
    "/wiki/estilos/componentes/sin-movimiento.css",
]


def tipo_de(ruta):
    """Qué clase de página de la wiki es: "portada", "mapa", "linea"
    (la línea de tiempo entera) o "articulo" (todo lo demás: las páginas
    de la wiki y las de cada evento)."""
    if ruta in ("/wiki/", "/wiki/index.html"):
        return "portada"
    if re.search(r"/mapa_[^/]+\.html$", ruta):
        return "mapa"
    if ruta.endswith("/linea_de_tiempo.html"):
        return "linea"
    return "articulo"


def hojas_de(ruta):
    """ruta es la dirección pública de la página, tal cual sale en la
    barra del navegador: "/wiki/index.html", "/wiki/cosmologia/el_sol.html"..."""
    hojas = [
        # Base: la necesita cualquier página.
        "/wiki/estilos/base.css",
        "/wiki/estilos/base.responsive.css",
        "/wiki/estilos/componentes/visor-imagenes.css",
        # El aviso emergente es un componente: va en la base (como el
        # visor) para que cualquier página pueda montar uno.
        "/wiki/estilos/componentes/aviso.css",
        "/wiki/estilos/componentes/aviso.responsive.css",
        # La cabecera de ventana falsa (−■✕).
        "/wiki/estilos/componentes/cabecera-ventana.css",
        # El botón flotante de "volver arriba".
        "/wiki/estilos/componentes/subir.css",
        # El botón "Aa" que abre la ventana de accesibilidad.
        "/wiki/estilos/componentes/ajustes.css",
    ]
    tipo = tipo_de(ruta)
    hojas += ["/wiki/estilos/paginas/mundo.css"]
    if tipo == "portada":
        # El buscador de la portada y la ventana donde se abre cada
        # sección (el mapamundi, la historia…).
        hojas += [
            "/wiki/estilos/componentes/buscador.css",
            "/wiki/estilos/componentes/ventana-modal.css",
            "/wiki/estilos/componentes/ventana-modal.responsive.css",
        ]
    if tipo == "mapa":
        hojas += ["/wiki/estilos/paginas/mundo-mapa.css"]
    if tipo == "linea":
        hojas += ["/wiki/estilos/paginas/mundo-linea.css"]
    # Un ARTÍCULO lleva la lupa: sus imágenes (el mapa de situación, las
    # fotos de la ficha) se ven en grande al pulsarlas.
    if tipo == "articulo":
        hojas += ["/wiki/estilos/componentes/lupa.css"]
    hojas += ["/wiki/estilos/paginas/mundo.responsive.css"]
    if tipo == "mapa":
        hojas += ["/wiki/estilos/paginas/mundo-mapa.responsive.css"]
    if tipo == "linea":
        hojas += ["/wiki/estilos/paginas/mundo-linea.responsive.css"]
    # El menú de la wiki (la barra lateral de siempre con lo de la wiki:
    # generar-menu-wiki.py) va DESPUÉS de la hoja de la página, como en el
    # blog: su regla de "nav" tiene que ganarle a la de la página.
    hojas += [
        "/wiki/estilos/componentes/barra-lateral.css",
        "/wiki/estilos/componentes/barra-lateral.responsive.css",
        "/wiki/estilos/componentes/menu-wiki.css",
    ]
    return hojas + ULTIMAS


def scripts_de(ruta):
    """Igual que hojas_de(), pero con el JS. Van todos con defer, en este
    orden."""
    js = [
        # Los comunes (van en el paquete): el menú, el tema, la ventana Aa,
        # las ventanas que se pliegan, los enlaces de fuera, el visor…
        "/wiki/scripts/componentes/cargador-fragmentos.js",
        "/wiki/scripts/componentes/barra-lateral.js",
        "/wiki/scripts/tema.js",
        "/wiki/scripts/componentes/ajustes.js",
        "/wiki/scripts/componentes/botones-ventana.js",
        "/wiki/scripts/componentes/ventanas-plegables.js",
        "/wiki/scripts/componentes/rastro-cursor.js",
        "/wiki/scripts/componentes/chispas-botones.js",
        "/wiki/scripts/componentes/enlaces-fuera.js",
        "/wiki/scripts/componentes/visor-imagenes.js",
        "/wiki/scripts/componentes/aviso.js",
        "/wiki/scripts/componentes/subir.js",
        "/wiki/scripts/componentes/teclado-scroll.js",
    ]
    tipo = tipo_de(ruta)
    # Un MAPA no lleva mundo.js: no tiene índice que pintar ni spoilers que
    # destapar, y lo suyo está en mundo-mapa.js.
    if tipo == "mapa":
        js.append("/wiki/scripts/paginas/mundo-mapa.js")
        return js
    if tipo == "portada":
        js += ["/wiki/scripts/componentes/buscador.js",
               "/wiki/scripts/componentes/ventana-modal.js"]
    elif tipo == "articulo":
        # La lupa, ANTES que mundo.js: es él quien la usa para ampliar las
        # imágenes, y mira si está nada más cargar.
        js += ["/wiki/scripts/componentes/lupa.js"]
    js.append("/wiki/scripts/paginas/mundo.js")
    return js


# =========================================
# LA VERSIÓN DE CADA ARCHIVO
# =========================================

CARGADOR = "/wiki/scripts/cargador-scripts.js"

# Lo que entra en la lista de cargador-scripts.js: lo que el navegador
# pide por su cuenta después de cargar la página. Hoy son solo los
# fragmentos de HTML (la barra lateral y las frases), que se piden con
# fetch() desde el propio navegador.
#
# El JS ya no está aquí: desde que cada página lleva sus <script>
# escritos en el <head>, su ?v= lo pone esta misma herramienta al
# escribirlos, igual que el del CSS. La lista pasó de 40 líneas a dos, y
# eso se nota: cargador-scripts.js es lo único que bloquea el pintado.
#
# Los JSON de datos/ tampoco están (ver la explicación de arriba).
VERSIONADAS = {
    "wiki/fragmentos": (".html",),
}


def version_de(ruta_publica):
    """Resumen corto del contenido, o "" si el archivo no está.

    Los saltos de línea de Windows (\\r\\n) cuentan como los de siempre
    (\\n): si no, el mismo archivo daba otro ?v= según el ordenador (git
    en Windows los cambia al bajarlos), y pasar esto allí cambiaba la
    cabecera de las doscientas páginas sin haber tocado nada."""
    # Una copia de ligero/ puede no estar escrita todavía (con --probar no
    # se escribe nada): su versión sale de lo que se va a escribir.
    for servida, texto in LIGERAS.values():
        if servida == ruta_publica:
            return hashlib.sha1(texto.replace("\r\n", "\n").encode("utf-8")).hexdigest()[:8]
    archivo = RAIZ / ruta_publica.lstrip("/")
    if not archivo.is_file():
        return ""
    return hashlib.sha1(archivo.read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:8]


def con_version(ruta_publica):
    version = version_de(ruta_publica)
    return f"{ruta_publica}?v={version}" if version else ruta_publica


def rutas_versionadas():
    for carpeta, extensiones in sorted(VERSIONADAS.items()):
        base = RAIZ / carpeta
        if not base.is_dir():
            continue
        for archivo in sorted(base.rglob("*")):
            if not archivo.is_file() or archivo.suffix not in extensiones:
                continue
            ruta = "/" + archivo.relative_to(RAIZ).as_posix()
            if ruta != CARGADOR:
                yield ruta


# =========================================
# LO QUE SE SIRVE: LAS COPIAS SIN COMENTARIOS
# =========================================
# Las páginas no piden estilos/paginas/notas-rol.css sino
# ligero/estilos/paginas/notas-rol.css: el mismo archivo sin comentarios,
# que eran entre la mitad y tres cuartas partes de lo que se bajaba (el
# porqué y el cómo, en ligero.py). Los originales son la documentación y
# no se tocan; ligero/ se escribe entero aquí y no se edita a mano.
#
# Cada copia lleva arriba "fuente: <el original>": así sabe
# 4-comprobar/enlaces-rotos.py que el original se usa (igual que con los
# paquetes), y quien la abra en el navegador sabe de dónde sale.
LIGERO = "/wiki/ligero"
LIGERAS = {}  # ruta original -> (ruta servida, texto)
CABECERA_LIGERA = (
    "/* Copia sin comentarios. La escribe actualizar-cabeceras.py: no se edita.\n"
    "   fuente: %s\n"
    "*/\n"
)


def servida(ruta_publica):
    """Lo que piden las páginas en lugar de 'ruta_publica'. Los paquetes
    se piden tal cual (ya salen sin comentarios); lo demás, su copia."""
    if ruta_publica in DESTINOS_DE_PAQUETES or not ruta_publica.endswith((".css", ".js")):
        return ruta_publica
    if ruta_publica not in LIGERAS:
        archivo = RAIZ / ruta_publica.lstrip("/")
        if not archivo.is_file():
            return ruta_publica
        texto = CABECERA_LIGERA % ruta_publica + sin_comentarios(
            ruta_publica, archivo.read_text(encoding="utf-8"))
        # /wiki/estilos/x.css se sirve como /wiki/ligero/estilos/x.css.
        LIGERAS[ruta_publica] = (LIGERO + ruta_publica[len("/wiki"):], texto)
    return LIGERAS[ruta_publica][0]


def escribir_ligeras(probar=False):
    """Escribe las copias que han cambiado y quita de ligero/ las que ya
    no pide nadie. Devuelve (escritas, quitadas)."""
    escritas, quitadas = [], []
    deben = set()
    for servida_, texto in LIGERAS.values():
        destino = RAIZ / servida_.lstrip("/")
        deben.add(destino)
        antes = destino.read_text(encoding="utf-8") if destino.is_file() else None
        if antes != texto:
            escritas.append(servida_)
            if not probar:
                destino.parent.mkdir(parents=True, exist_ok=True)
                escribir_texto(destino, texto)
    carpeta = RAIZ / LIGERO.lstrip("/")
    if carpeta.is_dir():
        for archivo in sorted(carpeta.rglob("*")):
            if archivo.is_file() and archivo not in deben:
                quitadas.append("/" + archivo.relative_to(RAIZ).as_posix())
                if not probar:
                    archivo.unlink()
        if not probar:
            for sub in sorted(carpeta.rglob("*"), key=lambda x: -len(x.parts)):
                if sub.is_dir() and not any(sub.iterdir()):
                    sub.rmdir()
    return escritas, quitadas


ABRE_VERSIONES = "        // ==== generado ===="
CIERRA_VERSIONES = "        // ==== fin del generado ===="


def escribir_versiones():
    """Rellena la lista VERSIONES de cargador-scripts.js. Devuelve
    cuántos archivos ha apuntado, o None si no encuentra las marcas."""
    archivo = RAIZ / CARGADOR.lstrip("/")
    texto, crlf = leer_texto(archivo)
    if ABRE_VERSIONES not in texto or CIERRA_VERSIONES not in texto:
        return None

    lineas = [
        f'        "{ruta}": "{version_de(ruta)}",' for ruta in rutas_versionadas()
    ]
    nuevo = "\n".join([ABRE_VERSIONES, *lineas, CIERRA_VERSIONES])
    antes, resto = texto.split(ABRE_VERSIONES, 1)
    _, despues = resto.split(CIERRA_VERSIONES, 1)
    salida = antes + nuevo + despues
    if salida != texto:
        escribir_texto(archivo, salida, crlf)
    return len(lineas)



# =========================================
# LOS PAQUETES
# =========================================
# Hay once hojas de estilo y quince scripts que lleva LA MISMA página,
# todas: la base, el aviso, la ventana de ajustes, la barra lateral... En
# la cabecera eso eran veintiséis líneas iguales en los 38 archivos, y
# veintiséis viajes del navegador.
#
# Así que se juntan: la herramienta escribe tres archivos pegando los de
# dentro, y en la cabecera va uno en vez de once.
#
# POR QUÉ TRES Y NO UNO SOLO
# --------------------------
# Porque el ORDEN del CSS decide quién gana: en esta web hay unas cuantas
# reglas que se apoyan en cargarse después de otra (la regla de "nav" de
# la barra lateral, los "[hidden]" de las notas de rol...). Los comunes no
# van todos seguidos: ocho van SIEMPRE antes de la hoja de la página y
# tres SIEMPRE después. Si se juntaran en uno, esos tres adelantarían a la
# hoja de la página y cambiaría lo que se ve. Son dos paquetes porque son
# dos sitios distintos de la cascada.
#
# Y POR QUÉ NO UN PAQUETE POR PÁGINA
# ----------------------------------
# Medido: hay 19 combinaciones distintas de CSS para 31 páginas, así que
# serían 19 paquetes de ~200 KB (3,8 MB) y cada página se bajaría el suyo
# entero en vez de reaprovechar la base que ya tenía de la anterior.
# Juntar solo lo común deja la caché compartida intacta.
#
# SI AÑADES O QUITAS ALGO de estas listas, hay que cambiarlo también en
# hojas_de() o scripts_de(): el paquete es lo que se pide, pero esas
# funciones siguen siendo las que dicen qué lleva cada página. La
# herramienta avisa si no cuadran.
#
# UNA PÁGINA QUE NO LOS LLEVE TODOS SEGUIDOS se queda con sus archivos
# sueltos y no pasa nada: es lo que le ocurre al 404, que no lleva ni
# barra lateral ni tema.

PAQUETES = (
    (
        "/wiki/estilos/paquete-comun.css",
        [
            "/wiki/estilos/base.css",
            "/wiki/estilos/base.responsive.css",
            "/wiki/estilos/componentes/visor-imagenes.css",
            "/wiki/estilos/componentes/aviso.css",
            "/wiki/estilos/componentes/aviso.responsive.css",
            "/wiki/estilos/componentes/cabecera-ventana.css",
            "/wiki/estilos/componentes/subir.css",
            "/wiki/estilos/componentes/ajustes.css",
        ],
    ),
    (
        "/wiki/estilos/paquete-cierre.css",
        [
            # El menú y las tres últimas (ULTIMAS) van al final de todas
            # las páginas, así que entran también.
            "/wiki/estilos/componentes/barra-lateral.css",
            "/wiki/estilos/componentes/barra-lateral.responsive.css",
            "/wiki/estilos/componentes/menu-wiki.css",
            "/wiki/estilos/componentes/ventanas-plegables.css",
            "/wiki/estilos/componentes/impresion.css",
            "/wiki/estilos/componentes/sin-movimiento.css",
        ],
    ),
    (
        "/wiki/scripts/paquete-comun.js",
        [
            "/wiki/scripts/componentes/cargador-fragmentos.js",
            "/wiki/scripts/componentes/barra-lateral.js",
            "/wiki/scripts/tema.js",
            "/wiki/scripts/componentes/ajustes.js",
            "/wiki/scripts/componentes/botones-ventana.js",
            "/wiki/scripts/componentes/ventanas-plegables.js",
            "/wiki/scripts/componentes/rastro-cursor.js",
            "/wiki/scripts/componentes/chispas-botones.js",
            "/wiki/scripts/componentes/enlaces-fuera.js",
            "/wiki/scripts/componentes/visor-imagenes.js",
            "/wiki/scripts/componentes/aviso.js",
            "/wiki/scripts/componentes/subir.js",
            "/wiki/scripts/componentes/teclado-scroll.js",
        ],
    ),
)


DESTINOS_DE_PAQUETES = {destino for destino, _ in PAQUETES}


def escribir_paquetes(probar=False):
    """Escribe los tres paquetes pegando sus archivos. Devuelve los que
    ha tenido que reescribir."""
    rehechos = []
    for destino, miembros in PAQUETES:
        trozos = [
            "/* ARCHIVO GENERADO — NO LO EDITES.\n"
            "   Lo escribe herramientas/3-generadores/actualizar-cabeceras.py\n"
            "   pegando los archivos de abajo, que son los que lleva TODA\n"
            "   página del sitio. Para cambiar algo se toca el archivo de\n"
            "   verdad y se vuelve a pasar la herramienta.\n"
            "\n"
            + "".join("   fuente: %s\n" % m for m in miembros)
            + "*/\n"
        ]
        for miembro in miembros:
            archivo = RAIZ / miembro.lstrip("/")
            if not archivo.is_file():
                print(f"  AVISO: el paquete {destino} nombra {miembro}, que no está.")
                continue
            trozos.append("\n/* ======== %s ======== */\n" % miembro)
            # Sin comentarios, como todo lo que se sirve (ver ligero.py).
            trozos.append(sin_comentarios(miembro, archivo.read_text(encoding="utf-8")))
        texto = "".join(trozos)
        # En JavaScript los /* */ también valen, así que el separador
        # sirve igual para los dos; lo que no vale es dejar un archivo sin
        # salto de línea pegado al siguiente.
        if not texto.endswith("\n"):
            texto += "\n"

        salida = RAIZ / destino.lstrip("/")
        antes = salida.read_text(encoding="utf-8") if salida.is_file() else None
        if antes != texto:
            rehechos.append(destino)
            if not probar:
                # Con escribir_texto, y no con write_text, por los saltos
                # de línea: es lo que usa todo lo demás del proyecto para
                # no dejar un archivo con los saltos cambiados.
                escribir_texto(salida, texto)
    return rehechos


def repasar_paquetes():
    """Que lo que dicen los paquetes siga cuadrando con lo que piden las
    páginas. Si alguien añade una hoja común en hojas_de() y se olvida de
    meterla en el paquete, o al revés, esto lo canta aquí en vez de
    dejarlo pasar."""
    avisos = []
    for destino, miembros in PAQUETES:
        usan, sueltas = 0, []
        for _, ruta in paginas():
            lista = hojas_de(ruta) if destino.endswith(".css") else scripts_de(ruta)
            if con_paquetes(lista) != lista:
                if destino in con_paquetes(lista):
                    usan += 1
                    continue
            if set(miembros) <= set(lista):
                # Los lleva todos pero no seguidos: el paquete ya no vale
                # para esa página y se queda con los archivos sueltos.
                sueltas.append(ruta)
        if not usan:
            avisos.append("  AVISO: el paquete %s no lo usa ninguna página."
                          " ¿Han cambiado hojas_de()/scripts_de()?" % destino)
        if sueltas:
            avisos.append(
                "  AVISO: %d página(s) llevan todo lo de %s pero no seguido,"
                " así que se quedan con los archivos sueltos: %s"
                % (len(sueltas), destino, ", ".join(sueltas[:3]))
            )
    return avisos


def con_paquetes(lista):
    """Cambia cada tirada de archivos de un paquete por el paquete. Lo
    que no esté entero y seguido se queda como está."""
    salida = list(lista)
    for destino, miembros in PAQUETES:
        n = len(miembros)
        for i in range(len(salida) - n + 1):
            if salida[i:i + n] == miembros:
                salida[i:i + n] = [destino]
                break
    return salida


# =========================================
# EL BLOQUE QUE SE ESCRIBE EN EL <head>
# =========================================

ABRE = "<!-- ==== CSS ===="
CIERRA = "<!-- ==== fin del CSS ==== -->"

# LAS MARCAS VAN SOLAS, SIN EXPLICACIÓN. Esto se escribe en todas las
# páginas, así que cada línea de explicación se copiaba treinta y tantas
# veces y la bajaba cada visita. El porqué de cada cosa está AQUÍ, que es
# donde se toca, y en herramientas/LEEME.txt («LA CABECERA DE LAS
# PÁGINAS»): ahí pone que este bloque lo escribe la herramienta y no se
# toca a mano. Las marcas se quedan porque son como esta herramienta
# encuentra el bloque la vez siguiente (y quitar-comentarios.py las
# respeta por eso, ver MARCAS allí).
CABECERA = f"""    {ABRE} -->
"""


ABRE_JS = "<!-- ==== JS ===="
CIERRA_JS = "<!-- ==== fin del JS ==== -->"

CABECERA_JS = f"""    {ABRE_JS} -->
"""


BARRA_LATERAL = "/wiki/fragmentos/menu-wiki.html"

# EL ADELANTO DEL MENÚ (ya no se usa)
#
# Hasta el 16-10-2026, cada página pedía el menú en el <head> con un
# <script> escrito a pelo (window.adelantoDeFragmentos) para no esperar a
# barra-lateral.js. Ahora el menú va escrito dentro de la página (ver LA
# BARRA LATERAL, aquí abajo) y no hay nada que pedir. La marca se sigue
# reconociendo (YA_PUESTO) para quitárselo a las páginas que aún lo
# lleven.
ABRE_ADELANTO = "<!-- ==== ADELANTO DEL MENÚ ===="


# =========================================
# LA BARRA LATERAL, ESCRITA EN CADA PÁGINA
# =========================================
# fragmentos/barra-lateral.html es el menú de todo el sitio, escrito UNA
# vez. Antes lo pedía el navegador al cargar cada página (con el adelanto
# de arriba) y el menú aparecía 200-250 ms después que lo demás; ahora
# esta herramienta lo copia dentro de cada página, entre dos marcas:
#
#     <div id="sidebar-container" data-fragmento="barra-lateral">
#     <!-- ==== BARRA LATERAL ==== -->
#     …el menú…
#     <!-- ==== fin de la BARRA LATERAL ==== -->
#     </div>
#
# y ya está desde el primer momento, aunque falle el JavaScript. SE SIGUE
# TOCANDO SOLO EL FRAGMENTO: al pasar esto se reescribe en todas.
#
# De paso se deja marcado dónde se está (el enlace de esta página con
# class="active" y aria-current, y su apartado abierto), lo mismo que hace
# scripts/componentes/barra-lateral.js al arrancar (initializeActivePage):
# así el submenú no se abre de golpe un momento después.
#
# Las plantillas (herramientas/plantillas/) se quedan con el contenedor
# vacío: no son ninguna página, y lo que salga de ellas se pasa por aquí
# después. Si una página llega sin menú, el script lo pide como antes.
#
# UN FRAGMENTO PUEDE LLEVAR OTROS DENTRO, con una línea así:
#
#     <!--! fragmento: ajustes -->
#
# que aquí se cambia por fragmentos/ajustes.html (el «!» es para que
# quitar-comentarios.py no la borre del fragmento). Así el menú
# (barra-lateral.html) lleva dentro la ventana de accesibilidad
# (ajustes.html) y la de buscar (buscar.html), cada una en su archivo.
#
# Y UNA PÁGINA PUEDE PEDIR UN FRAGMENTO SUELTO con un contenedor
#
#     <div id="lo-que-sea" data-fragmento="ajustes"></div>
#
# que esta herramienta rellena entre sus marcas. Es lo que hace el 404,
# que no tiene menú pero sí el botón Aa.
FRAGMENTOS = RAIZ / "wiki" / "fragmentos"
RE_INCLUIR = re.compile(r"[ \t]*<!--!\s*fragmento:\s*([\w-]+)\s*-->")


def abre_fragmento(nombre):
    return "<!-- ==== FRAGMENTO %s ==== -->" % nombre


def cierra_fragmento(nombre):
    return "<!-- ==== fin del FRAGMENTO %s ==== -->" % nombre


def fragmento(nombre, vistos=()):
    """El HTML de fragmentos/<nombre>.html con los que lleve dentro ya
    puestos. Un fragmento que se incluyera a sí mismo (o en círculo) se
    canta y se deja fuera."""
    if nombre in vistos:
        print("  AVISO: el fragmento %s se incluye a sí mismo (%s)." % (nombre, " → ".join(vistos)))
        return ""
    archivo = FRAGMENTOS / (nombre + ".html")
    if not archivo.is_file():
        print("  AVISO: no hay ningún fragmentos/%s.html." % nombre)
        return ""
    texto = archivo.read_text(encoding="utf-8").strip("\n")
    return RE_INCLUIR.sub(lambda m: fragmento(m.group(1), tuple(vistos) + (nombre,)), texto)


# Las marcas de antes de que hubiera más fragmentos que el menú: se
# reconocen para cambiarlas por las nuevas.
ABRE_BARRA = "<!-- ==== BARRA LATERAL ==== -->"
CIERRA_BARRA = "<!-- ==== fin de la BARRA LATERAL ==== -->"
RE_CONTENEDOR = re.compile(
    r'<div id="sidebar-container"[^>]*>(?:\s*(?:' + re.escape(ABRE_BARRA) + r'|'
    + re.escape(abre_fragmento("barra-lateral")) + r').*?(?:' + re.escape(CIERRA_BARRA) + r'|'
    + re.escape(cierra_fragmento("barra-lateral")) + r'))?\s*</div>', re.S)
RE_SUELTO = re.compile(
    r'<div id="([\w-]+)" data-fragmento="([\w-]+)">(?:\s*<!-- ==== FRAGMENTO [\w-]+ ==== -->.*?'
    r'<!-- ==== fin del FRAGMENTO [\w-]+ ==== -->)?\s*</div>', re.S)


def _normalizar(camino):
    if len(camino) > 1 and camino.endswith("/"):
        camino = camino[:-1]
    if camino.endswith("/index.html"):
        camino = camino[: -len("index.html")]
    return camino or "/"


def barra_para(ruta, fragmento):
    """El menú con el enlace de esta página marcado y su apartado abierto
    (mismas reglas que initializeActivePage en barra-lateral.js)."""
    actual = _normalizar(ruta)
    # Solo los del menú (dentro del <aside>): las ventanas de buscar y de
    # accesibilidad, que van en el mismo fragmento, no cuentan.
    desde = fragmento.find('<aside class="sidebar"')
    hasta = fragmento.find("</aside>", desde)
    enlaces = [(m, _normalizar(m.group(2))) for m in
               re.finditer(r'<a ([^>]*?)href="(/[^"#]*)(?:#[^"]*)?"([^>]*)>', fragmento)
               if desde != -1 and desde < m.start() < hasta]
    elegido, tipo = None, "page"
    for m, camino in enlaces:
        if camino == actual:
            elegido = m
            break
    if elegido is None:
        tipo, mejor = "true", ""
        for m, camino in enlaces:
            # Un MAPA solo se marca estando en él: la página de un país vive
            # en la misma carpeta que su mapa, y marcar el mapa diría que
            # estás en el mapa. Así se marca su parte del mundo.
            if camino.rsplit("/", 1)[-1].startswith("mapa_"):
                continue
            carpeta = camino[: camino.rfind("/") + 1] if camino.rfind("/") > 0 else "/"
            # Un enlace sin dirección propia (una sección de la wiki, que
            # abre su ventana en la portada) dice con data-marca de qué
            # carpeta son sus páginas.
            marca = re.search(r'data-marca="(/[^"]*)"', m.group(1) + m.group(3))
            if marca:
                carpeta = marca.group(1)
            if carpeta != "/" and (actual + "/").startswith(carpeta) and len(carpeta) > len(mejor):
                elegido, mejor = m, carpeta
    if elegido is None:
        return fragmento
    antes, despues = elegido.group(1), elegido.group(3)
    clase = re.search(r'class="([^"]*)"', antes + despues)
    nueva = elegido.group(0)
    if clase:
        nueva = nueva.replace(clase.group(0), 'class="%s active"' % clase.group(1), 1)
    else:
        nueva = nueva.replace("<a ", '<a class="active" ', 1)
    nueva = nueva[:-1] + ' aria-current="%s">' % tipo
    # Los apartados que lo contienen: los <div class="nav-group"> que
    # siguen abiertos (sin cerrar) al llegar al enlace.
    pila = []
    for t in re.finditer(r"<(/?)div\b[^>]*>", fragmento[: elegido.start()]):
        if t.group(1):
            if pila:
                pila.pop()
        else:
            pila.append(t)
    grupos = sorted((t for t in pila if 'class="nav-group"' in t.group(0)), key=lambda t: -t.start())
    texto = fragmento[: elegido.start()] + nueva + fragmento[elegido.end():]
    for g in grupos:
        # Desde el final hacia el principio, para no mover lo que queda
        # por cambiar.
        trozo = texto[g.start():]
        trozo = trozo.replace('<div class="nav-group">', '<div class="nav-group open">', 1)
        trozo = re.sub(r'(<button class="nav-toggle"[^>]*?)aria-expanded="false"', r'\1aria-expanded="true"',
                       trozo, count=1)
        trozo = re.sub(r'(<span class="arrow" aria-hidden="true">)\+(</span>)', "\\1\u2212\\2", trozo, count=1)
        texto = texto[: g.start()] + trozo
    return texto


def con_barra_lateral(texto, ruta):
    if not RE_CONTENEDOR.search(texto):
        return texto
    # El menú de la wiki (lo escribe generar-menu-wiki.py), en el mismo
    # contenedor y con el mismo componente que el del blog.
    menu = barra_para(ruta, fragmento("menu-wiki"))
    if not menu:
        return texto
    lleno = ('<div id="sidebar-container" data-fragmento="barra-lateral">\n%s\n%s\n%s\n    </div>'
             % (abre_fragmento("barra-lateral"), menu, cierra_fragmento("barra-lateral")))
    return RE_CONTENEDOR.sub(lambda m: lleno, texto, count=1)


def con_fragmentos_sueltos(texto):
    """Los <div id="…" data-fragmento="…"> que no son el menú, rellenos."""
    def rellenar(m):
        ident, nombre = m.group(1), m.group(2)
        if ident == "sidebar-container":
            return m.group(0)
        dentro = fragmento(nombre)
        if not dentro:
            return m.group(0)
        return ('<div id="%s" data-fragmento="%s">\n%s\n%s\n%s\n    </div>'
                % (ident, nombre, abre_fragmento(nombre), dentro, cierra_fragmento(nombre)))
    return RE_SUELTO.sub(rellenar, texto)


def bloque(ruta):
    links = "\n".join(
        f'    <link rel="stylesheet" href="{con_version(servida(h))}">'
        for h in con_paquetes(hojas_de(ruta))
    )
    # El cargador va SIN defer y antes que los demás: es quien pone el
    # tamaño del texto, la letra y el filtro CRT antes del primer
    # pintado, y quien deja preparado window.conVersion() para los que
    # vienen detrás.
    cargador = f'    <script src="{con_version(servida(CARGADOR))}"></script>'
    defer = "\n".join(
        f'    <script defer src="{con_version(servida(s))}"></script>'
        for s in con_paquetes(scripts_de(ruta))
    )
    # Ya no hay adelanto que valga: la barra lateral va escrita dentro de
    # cada página (ver con_barra_lateral, abajo). Las páginas que aún lo
    # llevan lo pierden al pasar esto (YA_PUESTO se lo traga).
    adelanto = ""

    return (
        f"{adelanto}{CABECERA}{links}\n    {CIERRA}\n{cargador}\n"
        f"{CABECERA_JS}{defer}\n    {CIERRA_JS}"
    )


# =========================================
# EL TEMA, ANTES DE PINTAR NADA
# =========================================
# Las primeras líneas de cada página ponen el tema elegido en el <html>
# ANTES del primer pintado. Tiene que ir ahí, escrito a pelo: si esperara
# a scripts/tema.js (que va con defer, o sea al final), la página se
# pintaría con el tema de fábrica y daría un fogonazo al cambiar.
#
# ANTES ESTABA COPIADO EN LAS 38 PÁGINAS, cincuenta líneas cada una, y
# añadir un tema significaba tocarlas todas a mano —de ahí que exista
# herramientas/4-comprobar/temas-completos.py, para cazar las que se
# quedaban sin él—. Ahora lo escribe esta herramienta leyendo la lista de
# scripts/tema.js: los temas se tocan ahí y aquí no hay que acordarse de
# nada.
#
# Sale compacto a propósito: es código generado, se repite 38 veces y no
# se lee ni se toca a mano. El porqué de cada cosa está en scripts/tema.js
# y en herramientas/LEEME.txt.

TEMA_JS = RAIZ / "wiki" / "scripts" / "tema.js"
ABRE_TEMA = "<!-- ==== TEMA ===="

# El color con el que arranca la barra del navegador en el móvil: el del
# tema de fábrica. El script de abajo lo cambia si hay otro puesto.
COLOR_DE_FABRICA = "#12091c"


def _entre(texto, desde, hasta):
    i = texto.find(desde)
    if i == -1:
        return ""
    i += len(desde)
    j = texto.find(hasta, i)
    return texto[i:j] if j != -1 else texto[i:]


def temas_del_sitio():
    """{clave: [atributo, color de la barra]} sacado de scripts/tema.js,
    que es donde vive la lista. El tema de fábrica no entra: es el que
    sale cuando no hay ninguno puesto, así que no tiene nada que poner."""
    js = TEMA_JS.read_text(encoding="utf-8")
    atributos = dict(re.findall(
        r'"?([\w-]+)"?\s*:\s*"([^"]*)"', _entre(js, "const TEMA_ATRIBUTO = {", "};")))
    barras = dict(re.findall(
        r'"?([\w-]+)"?\s*:\s*"([^"]*)"', _entre(js, "const COLOR_BARRA = {", "};")))
    claves = re.findall(r'"([^"]+)"', _entre(js, "const TEMAS = [", "];"))
    salida = []
    for clave in claves:
        atributo = atributos.get(clave, "")
        if not atributo:
            continue
        salida.append((clave, atributo, barras.get(clave, COLOR_DE_FABRICA)))
    return salida


def bloque_del_tema():
    temas = temas_del_sitio()
    if not temas:
        print("  AVISO: no encuentro los temas en scripts/tema.js;"
              " dejo el pre-pintado como estaba.")
        return None
    # Una clave por línea pero sin comentarios: así sigue siendo legible
    # en el inspector del navegador sin ocupar media pantalla. Las comillas
    # de la clave solo hacen falta si lleva un guion, pero se ponen siempre:
    # cuesta dos caracteres y evita tener que pensarlo.
    filas = ",\n".join(
        '            "%s": ["%s", "%s"]' % (clave, atributo, barra)
        for clave, atributo, barra in temas
    )
    # LA CLASE "js" del <html>: una marca de que el JavaScript funciona,
    # puesta ANTES del primer pintado. Sirve para que una hoja de estilo
    # pueda decir "esto solo si hay JavaScript": un spoiler tapado, por
    # ejemplo, que sin JavaScript sería texto perdido y con él se destapa
    # al pulsarlo. Va aquí porque es el único script que corre antes de
    # pintar: puesto más tarde habría fogonazo. (El comentario estaba
    # dentro del script y se copiaba en cada página; vive aquí.)
    #
    # Y LA BARRA LATERAL PLEGADA ("lateral-plegada" en el <html>), por lo
    # mismo: el botón ☰ de al lado del título la pliega y lo apunta en
    # richi-lateral; si se pusiera al cargar el menú, en cada página se
    # vería la barra entera un momento y luego plegarse.
    return f"""    {ABRE_TEMA} -->
    <meta name="theme-color" content="{COLOR_DE_FABRICA}">
    <script>
      (function () {{
        document.documentElement.classList.add("js");
        try {{
          var temas = {{
{filas}
          }};
          var guardado = localStorage.getItem("richi-theme");
          var elegido = temas[guardado];
          if (!elegido && !guardado &&
              window.matchMedia("(prefers-color-scheme: light)").matches) {{
            elegido = temas.claro;
          }}
          if (elegido) {{
            document.documentElement.setAttribute("data-theme", elegido[0]);
            var barra = document.querySelector('meta[name="theme-color"]');
            if (barra) {{ barra.setAttribute("content", elegido[1]); }}
          }}
          if (localStorage.getItem("richi-lateral") === "plegada") {{
            document.documentElement.classList.add("lateral-plegada");
          }}
        }} catch (e) {{}}
      }})();
    </script>
"""


# Lo que hay que sustituir: el bloque viejo (el que empezaba con el
# comentario del color de la barra) o el nuevo. Los dos terminan en el
# </script> del pre-pintado.
TEMA_PUESTO = re.compile(
    r"[ \t]*(?:<!-- Color de la barra del navegador|"
    + re.escape(ABRE_TEMA) + r").*?</script>\n",
    re.S,
)


# La línea del cargador, con o sin su ?v=: hay que reconocer las dos
# para no dejar de encontrar el bloque justo cuando ya está bien.
LINEA_CARGADOR = (
    r'[ \t]*<script src="/wiki(?:/ligero)?/wiki/scripts/cargador-scripts\.js(?:\?v=[^"]*)?"></script>'
)

# Lo que había antes de pasar esta herramienta por primera vez: el
# cargador de scripts, el comentario viejo y el cargador de estilos.
VIEJO = re.compile(
    LINEA_CARGADOR + r"\n"
    r'(?:[ \t]*<!-- ==== CSS ==== -->\n)?'
    r'[ \t]*<script src="/wiki/scripts/cargador-estilos\.js"></script>'
)

# Lo que hay a partir de la segunda vez. El bloque del JS va con "?":
# las páginas que todavía no lo tengan (la primera vez que se pasa la
# herramienta después de este cambio) se reconocen igual y lo reciben.
YA_PUESTO = re.compile(
    # El adelanto del menú, si ya está puesto: va delante del CSS y
    # también hay que sustituirlo (su ?v= cambia al tocar el fragmento).
    # Se reconocen las dos formas, la de antes y la de ahora: si solo
    # valiera la nueva, la primera vez que se pasara esto después de
    # acortar los comentarios quedarían los dos, el viejo y el nuevo.
    r"(?:[ \t]*(?:<!-- El menú, pedido LO PRIMERO\.|"
    + re.escape(ABRE_ADELANTO) + r").*?</script>\n)?"
    r"[ \t]*" + re.escape(ABRE) + r".*?" + re.escape(CIERRA) + r"\n" + LINEA_CARGADOR
    + r"(?:\n[ \t]*" + re.escape(ABRE_JS) + r".*?" + re.escape(CIERRA_JS) + r")?",
    re.S,
)


# =========================================
# LA POLÍTICA DE SEGURIDAD (Content-Security-Policy)
# =========================================
# Una segunda red debajo de lo que ya protege la web (todo lo que se pinta
# va escapado y las direcciones se comprueban; ver
# 4-comprobar/inyecciones.py). Le dice al navegador de dónde puede venir
# cada cosa, y así, aunque un día se colara un <script> en una página,
# el navegador no lo ejecutaría.
#
# Neocities no deja poner cabeceras, así que va en un <meta>, el PRIMERO
# del <head> después del charset: lo que hubiera antes no lo cubriría.
#
# LOS SCRIPTS ESCRITOS EN LA PÁGINA (el pre-pintado del tema, el adelanto
# del menú, el del dibujo de la portada) se permiten uno a uno por su
# HUELLA (sha256 de su texto exacto), que esta herramienta calcula al
# escribir la cabecera. Por eso:
#
#     SI TOCAS A MANO UN <script> ESCRITO EN UNA PÁGINA, PASA ESTO DETRÁS.
#
# Si no, su huella ya no cuadra y el navegador no lo ejecuta (lo dice en la
# consola, F12). Los scripts de archivo (/wiki/ligero/..., los paquetes) no
# necesitan nada: valen todos los de esta misma web.
#
# Lo demás:
#   - estilos: los de la web y los escritos en línea (style="..."). Meter
#     estilos no ejecuta nada, y el mapa de la wiki y «sobre mí» llevan
#     style= dentro;
#   - imágenes: las de la web y las "data:" (la flechita de los enlaces de
#     fuera está dibujada así en el CSS);
#   - peticiones: solo las de la web (los JSON de la wiki);
#   - ni plugins, ni <base>, ni formularios que manden a otra web, ni
#     marcos (iframes).
RE_SCRIPT_EN_LINEA = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.S)
RE_CSP = re.compile(r'[ \t]*<meta http-equiv="Content-Security-Policy"[^>]*>\n')
RE_CHARSET = re.compile(r'(<meta charset="[^"]*">\n)', re.I)


def politica(texto):
    import base64
    sin = RE_CSP.sub("", texto)
    huellas = sorted({
        "'sha256-%s'" % base64.b64encode(hashlib.sha256(m.group(1).encode("utf-8")).digest()).decode()
        for m in RE_SCRIPT_EN_LINEA.finditer(sin)
    })
    return "; ".join([
        "default-src 'self'",
        "script-src 'self'" + "".join(" " + h for h in huellas),
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data:",
        "font-src 'self'",
        "connect-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-src 'none'",
    ])


def poner_csp(texto):
    """La página con su <meta> de seguridad al día, justo después del
    charset. Si no tiene charset (no es una página entera), tal cual."""
    if not RE_CHARSET.search(texto):
        return texto
    sin = RE_CSP.sub("", texto)
    meta = '    <meta http-equiv="Content-Security-Policy" content="%s">\n' % politica(sin)
    return RE_CHARSET.sub(lambda m: m.group(1) + meta, sin, count=1)


def paginas():
    """Todas las páginas del sitio (con su dirección pública) más las
    plantillas (con el tipo de página que van a ser)."""
    for clave, ruta in PLANTILLAS.items():
        if (REPO / clave).is_file():
            yield REPO / clave, ruta
    for archivo in sorted((RAIZ / "wiki").rglob("*.html")):
        rel = archivo.relative_to(RAIZ)
        if FUERA.intersection(rel.parts):
            continue
        yield archivo, "/" + rel.as_posix()


def nombre_de(archivo):
    """Cómo se nombra un archivo al contarlo: desde la web si es una
    página (wiki/…) o desde el repositorio si es una plantilla."""
    try:
        return archivo.relative_to(RAIZ).as_posix()
    except ValueError:
        return archivo.relative_to(REPO).as_posix()


def montar_pagina(texto, ruta, tema=None, con_menu=True):
    """Una página con su cabecera al día: el pre-pintado del tema, el
    bloque de CSS y JS, el menú (si con_menu) y la política de seguridad.
    None si no es una página completa. Lo usa main() con cada archivo, y
    el editor para la vista previa de un personaje (que no se escribe en
    ningún sitio: se sirve tal cual)."""
    if tema is None:
        tema = bloque_del_tema()
    nuevo = bloque(ruta)

    # El pre-pintado del tema, que vive en las primeras líneas y es
    # igual en todas las páginas.
    if tema and TEMA_PUESTO.search(texto):
        texto = TEMA_PUESTO.sub(lambda m: tema, texto, count=1)

    # Las dos expresiones se tragan la sangría de la primera línea,
    # así que el bloque nuevo se pone entero, con la suya.
    if YA_PUESTO.search(texto):
        salida = YA_PUESTO.sub(lambda m: nuevo, texto, count=1)
    elif VIEJO.search(texto):
        salida = VIEJO.sub(lambda m: nuevo, texto, count=1)
    else:
        return None

    # El menú, escrito dentro (no en las plantillas: ver
    # con_barra_lateral).
    if con_menu:
        if "/wiki/scripts/componentes/barra-lateral.js" in scripts_de(ruta):
            salida = con_barra_lateral(salida, ruta)
        salida = con_fragmentos_sueltos(salida)

    # Lo último, cuando ya está todo escrito: la política de seguridad
    # lleva las huellas de los scripts que haya quedado en la página.
    return poner_csp(salida)


def main():
    probar = "--probar" in sys.argv

    # Primero la lista de versiones y después las páginas: el <head>
    # lleva el v= de cargador-scripts.js, y ese archivo acaba de
    # cambiar al escribirle la lista dentro.
    # Lo PRIMERO: los paquetes. El ?v= de cada uno sale de su contenido,
    # así que tienen que estar escritos antes de ponerle la dirección a
    # ninguna página.
    rehechos = escribir_paquetes(probar)
    if rehechos:
        print("Paquetes rehechos: %s" % ", ".join(rehechos))
    for aviso in repasar_paquetes():
        print(aviso)

    if not probar:
        cuantas = escribir_versiones()
        if cuantas is None:
            print(
                f"  AVISO: no encuentro las marcas de la lista de versiones en"
                f" {CARGADOR}.\n"
                "         Los CSS llevarán su ?v=, pero los demás JS y los"
                " fragmentos no."
            )
        else:
            print(f"Versiones apuntadas en el cargador: {cuantas} archivo(s).")

    # El pre-pintado del tema: es el mismo para todas las páginas, así que
    # se arma una sola vez y no una por archivo.
    tema = bloque_del_tema()

    cambiadas, iguales, saltadas = [], [], []
    for archivo, ruta in paginas():
        texto, crlf = leer_texto(archivo)
        # Lo que había al abrir el archivo: es contra esto contra lo que
        # hay que comparar al final para saber si ha cambiado algo. Sin
        # guardarlo, una página a la que solo le cambiara el pre-pintado
        # se daba por "ya estaba al día" y no se escribía.
        original = texto
        salida = montar_pagina(texto, ruta, tema, FUERA.isdisjoint(Path(nombre_de(archivo)).parts))
        if salida is None:
            # Un fragmento suelto (barra-lateral.html, frases.html) o
            # algo que no es una página completa: ni se toca.
            saltadas.append(nombre_de(archivo))
            continue

        if salida == original:
            iguales.append(nombre_de(archivo))
        else:
            cambiadas.append(
                (nombre_de(archivo), len(hojas_de(ruta)))
            )
            if not probar:
                escribir_texto(archivo, salida, crlf)

    escritas, quitadas = escribir_ligeras(probar)
    if escritas:
        print(("Copias sin comentarios escritas en ligero/: %d" if not probar
               else "Copias sin comentarios que se escribirían: %d") % len(escritas))
    if quitadas:
        print("Quitadas de ligero/ (ya no las pide nadie): %s" % ", ".join(quitadas))

    if cambiadas:
        print("Actualizadas:" if not probar else "Se actualizarían:")
        for nombre, cuantas in cambiadas:
            print(f"  {nombre}  ({cuantas} hojas de estilo)")
    if iguales:
        print(f"Ya estaban al día: {len(iguales)} página(s).")
    if saltadas:
        print(f"Sin cabecera (no son páginas completas): {', '.join(saltadas)}")
    if not cambiadas and not iguales:
        print("No he encontrado ninguna página. ¿Estás en la carpeta raíz?")
        sys.exit(1)


if __name__ == "__main__":
    main()
