# Wiki Cralëa

La wiki de **Cralëa**, el mundo homebrew de Richi: sus países, sus lugares, su gente, su historia y sus mapas. Se lee en **[richi.blog/wiki/](https://richi.blog/wiki/)**.

Es un sitio estático hecho a mano (HTML, CSS y JavaScript, sin librerías ni herramientas de compilación, con las letras incluidas), con su propia portada y su propio menú. Lo usan dos cosas:

- **El blog** ([rperezbarreda/richiblog](https://github.com/rperezbarreda/richiblog)) copia `sitio/wiki/` tal cual y lo publica en `richi.blog/wiki/`.
- **Una app privada de escritura** abre las páginas de `wiki/` tal y como están.

## Qué hay en cada carpeta

| Carpeta | Qué es |
| --- | --- |
| `wiki/` | **Las fuentes.** Una página por archivo `.md`, en carpetas por tema (`Mapamundi/`, `Cosmología/`, `Religiones/`…). Las imágenes originales están en `_imagenes/` y las plantillas de cada tipo de página en `_system/templates/`. |
| `sitio/wiki/` | **Lo publicado**: las páginas generadas, el CSS, el JS, las imágenes y los datos. Todo cuelga de `/wiki/`, igual que en la web. |
| `herramientas/` | Los scripts de Python que pasan las fuentes a la web y lo comprueban. Están explicados en `herramientas/LEEME.txt`. |

## El formato de las páginas

Cada página es un archivo Markdown, y el nombre del archivo es el título de la página (`Reino de Prunia.md`). Arriba lleva un *frontmatter* YAML con la ficha:

```markdown
---
title: "Reino de Prunia"
tags: [Mapamundi, Azarasia]
región: "[[Azarasia]]"
bandera: reino_prunia.webp
infobox: "País"
capital: "*por decidir*"
---

**Reino de Prunia** está en [[Azarasia]].

## Historia
<!-- Una nota que no se publica. -->
```

- `[[Otra página]]`, `[[Otra página|con otro texto]]` y `[[Otra página#Apartado]]` enlazan con otras páginas.
- `![[imagen.webp]]` pone una imagen, que se busca por su nombre dentro de `_imagenes/`.
- `||spoiler||` sale tapado y se destapa al pulsarlo.
- `{{insert: Página}}` mete dentro otra página.
- `<!-- … -->` son notas que no salen en la web.
- Los campos de la ficha que dicen `*por decidir*` o que están vacíos no se publican.
- Los mapas son archivos `.cmap` (JSON, el formato de Chronicler ampliado: sitios, caminos, ríos, regiones, escala…) junto a la página de la que son. El mapamundi es `wiki/Mapamundi de Cralëa.cmap`.
- Los años se cuentan **AEM** (antes de la Era Muda) y **DEM** (después).

Todo lo que entiende el conversor está escrito, con ejemplos, en `wiki/Cómo se escribe esto.md`, que también se publica.

## Pasar la wiki a la web y verla

Se ejecuta desde la carpeta raíz del repositorio y hace falta Python 3 con Pillow (`pip install pillow`):

```
python herramientas/3-generadores/generar-mundo.py
python -m http.server 8000 -d sitio
```

Después se abre `http://localhost:8000/wiki/`. Antes de subir algo, conviene pasar las comprobaciones de `herramientas/4-comprobar/`.

## Accesibilidad

La wiki usa los mismos diez temas de color y los mismos ajustes que richi.blog (tamaño de letra, interlineado, letra más legible y menos movimiento). Se puede usar entera con el teclado y con lector de pantalla, y el contraste se mide con APCA.

## Licencia

Todavía por decidir.
