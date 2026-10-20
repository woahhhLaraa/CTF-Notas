# 🚩 CTF-Notas

Apuntes de CTF (orientados a **CyberFEI 3.0**) en una web navegable que funciona **sin internet**.

- **`index.html`** — el sitio ya generado. Ábrelo con doble clic o `xdg-open index.html`. Un solo archivo, sin dependencias.
- **`contenido/`** — la fuente real: los apuntes en Markdown.
- **`build.py`** — generador que convierte `contenido/*.md` en `index.html`.

## Ver los apuntes

Abre `index.html` en cualquier navegador. No necesita servidor ni conexión.

El sitio trae: menú lateral por secciones, buscador, resaltado de la sección activa al hacer scroll, botón de copiar en cada bloque de comandos y tema claro/oscuro.

## Expandir / editar (es escalable)

1. Edita cualquier `.md` dentro de `contenido/`, **o** crea uno nuevo ahí.
2. Si añadiste un archivo nuevo, regístralo en la lista `FUENTES` de `build.py`
   con su `(archivo, título, emoji, id)`.
3. Regenera el sitio:

   ```bash
   python3 build.py
   ```

El menú lateral se reconstruye solo a partir de los encabezados `##` y `###`.
No usa librerías externas (solo Python 3).

## Estructura

```
CTF-Notas/
├── index.html          # sitio generado (no editar a mano)
├── build.py            # generador
├── contenido/
│   ├── CHULETA.md            # chuleta de 1 página (imprimible)
│   ├── COMANDOS.md
│   ├── GUIA-EXPLICADA.md
│   ├── WRITEUP.md            # plantilla de writeup
│   └── PREPARACION-OFFLINE.md
├── kit/                # scripts de ESTUDIO (no para el evento)
│   ├── README.md
│   └── scripts/
│       ├── decode.py
│       ├── rsa_tool.py
│       └── pwn_template.py
└── README.md
```
