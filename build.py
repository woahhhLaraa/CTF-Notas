#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador del sitio de apuntes CTF.

QUÉ HACE:
  Lee los archivos .md listados en FUENTES (en la carpeta contenido/) y los
  convierte en un SOLO archivo HTML autocontenido (index.html) que puedes
  abrir sin internet (doble clic / file://).

CÓMO EXPANDIRLO (es la gracia de que sea escalable):
  1) Edita cualquier .md de la carpeta contenido/, o
  2) Crea un .md nuevo en contenido/ y añádelo a la lista FUENTES de abajo
     con su (archivo, título, emoji, id).
  3) Vuelve a correr:  python3 build.py
  El menú lateral se arma solo a partir de los encabezados ## y ### de cada .md.

No usa librerías externas: trae un conversor de Markdown mínimo pero suficiente
para estos apuntes (encabezados, código ```, `inline`, **negrita**, listas,
checkboxes, citas >, tablas, líneas ---, enlaces).
"""

import html
import json
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent         # raíz del repo
CONTENIDO = RAIZ / "contenido"                  # aquí viven los .md
SALIDA = RAIZ / "index.html"

# ---- Lista de secciones. Para añadir contenido, agrega una tupla aquí. ----
# (nombre_de_archivo_en_contenido, título visible, emoji, id_seccion)
FUENTES = [
    ("CHULETA.md",                "Chuleta (1 página)",  "⚡", "chuleta"),
    ("COMANDOS.md",               "Comandos",            "⌨️", "comandos"),
    ("BANDIT.md",                 "Bandit (comandos)",   "🎯", "bandit"),
    ("NATAS-KRYPTON.md",          "Natas + Krypton",     "🕸️", "natas-krypton"),
    ("GUIA-EXPLICADA.md",         "Guía explicada",      "📖", "guia"),
    ("WRITEUP.md",                "Writeup",             "📝", "writeup"),
    ("PREPARACION-OFFLINE.md",    "Preparación offline", "📦", "preparacion"),
]

# ---------------------- Inteligencia del buscador -------------------------
# SINONIMOS: lo que el usuario podría ESCRIBIR  ->  términos que SÍ aparecen
# en el contenido (herramientas, banderas, palabras). Así una búsqueda por
# concepto ("osint", "escaneo de puertos") encuentra las secciones aunque esas
# palabras no estén en el título. Las claves se normalizan (minúsculas, sin acentos).
# Para ampliarlo: agrega una entrada aquí y regenera.
SINONIMOS = {
    "osint": ["osint", "whois", "exiftool", "metadatos", "metadata", "geolocalizacion",
              "coordenadas", "gps", "dork", "google", "shodan", "usuario", "email", "foto"],
    "escaneo de puertos": ["nmap", "puertos", "puerto", "-p-", "servicios", "servicio",
                           "banner", "-sv", "-sc", "open", "filtered"],
    "escaneo": ["nmap", "gobuster", "feroxbuster", "ffuf", "enumerar", "descubrir"],
    "red": ["nmap", "nc", "netcat", "tshark", "tcpdump", "pcap", "puertos", "servicios"],
    "conexion ssh": ["ssh", "hydra", "nc", "netcat", "reverse shell", "/dev/tcp", "22"],
    "ssh": ["ssh", "hydra", "sftp", "22", "clave", "id_rsa"],
    "fuerza bruta": ["hydra", "hashcat", "john", "rockyou", "diccionario", "wordlist"],
    "contrasena": ["hashcat", "john", "hashid", "rockyou", "hash", "password", "clave", "crack"],
    "hash": ["hashid", "hashcat", "john", "md5", "sha1", "sha256", "bcrypt", "ntlm"],
    "estego": ["zsteg", "steghide", "stegseek", "binwalk", "exiftool", "lsb",
               "stegsolve", "espectrograma", "audacity", "oculto"],
    "esteganografia": ["zsteg", "steghide", "stegseek", "binwalk", "lsb", "stegsolve", "espectrograma"],
    "imagen": ["zsteg", "steghide", "exiftool", "binwalk", "stegsolve", "png", "jpg"],
    "audio": ["espectrograma", "audacity", "wav", "sonido"],
    "trafico": ["wireshark", "tshark", "tcpdump", "pcap", "follow tcp", "stream", "captura"],
    "pcap": ["wireshark", "tshark", "tcpdump", "follow tcp", "stream"],
    "web": ["curl", "feroxbuster", "gobuster", "ffuf", "sqlmap", "ssti", "lfi", "sql",
            "jwt", "cookie", "http", "header"],
    "sql": ["sqlmap", "union", "order by", "inyeccion", "injection", "' or", "admin'--"],
    "inyeccion": ["sql", "sqlmap", "ssti", "command injection", "lfi", "xss", "payload"],
    "reversing": ["gdb", "radare2", "ghidra", "ltrace", "strace", "checksec", "strings", "elf", "binario"],
    "binario": ["gdb", "radare2", "ghidra", "checksec", "elf", "ltrace", "pwn"],
    "pwn": ["gdb", "checksec", "rop", "ret2libc", "buffer", "overflow", "pwntools"],
    "forense": ["volatility", "vol", "foremost", "sleuthkit", "carving", "autopsy", "binwalk"],
    "memoria": ["volatility", "vol", "dump", "pslist", "cmdline", "mem", "raw"],
    "disco": ["foremost", "sleuthkit", "carving", "img", "recuperar", "borrado"],
    "shell": ["nc", "netcat", "reverse shell", "/dev/tcp", "bash -i", "web shell", "listener", "4444"],
    "reverse shell": ["nc", "netcat", "/dev/tcp", "bash -i", "listener", "4444", "python3"],
    "escalada": ["sudo -l", "gtfobins", "suid", "root", "privilegios", "find"],
    "decodificar": ["base64", "hex", "rot", "cyberchef", "magic", "xxd", "decode"],
    "cripto": ["rsa", "base64", "cyberchef", "xor", "aes", "rot", "rsactftool"],
    "flag": ["grep", "flag{", "cyberfei{", "bandera"],
    "triage": ["file", "strings", "exiftool", "binwalk", "xxd", "magic bytes"],
    "logs": ["grep", "logs", "access.log", "auth.log", "blue team"],
    "wordpress": ["wpscan", "wp", "plugin", "tema"],
    "exploit": ["searchsploit", "exploitdb", "msfconsole", "metasploit", "cve"],
}

# CATEGORIAS para los chips: (etiqueta visible, consulta que dispara).
CATEGORIAS = [
    ("OSINT",           "osint"),
    ("Red / Escaneo",   "escaneo de puertos"),
    ("Web",             "web"),
    ("Cripto / Estego", "estego"),
    ("Forense",         "forense"),
    ("Pwn / Rev",       "reversing"),
    ("Contraseñas",     "contrasena"),
    ("Shell",           "shell"),
]

# HERRAMIENTAS conocidas: se detectan en el cuerpo aunque no sean la 1ª palabra.
HERRAMIENTAS = {
    "nmap", "nc", "netcat", "curl", "wget", "feroxbuster", "gobuster", "ffuf", "dirb",
    "whatweb", "sqlmap", "hydra", "hashcat", "john", "hashid", "zsteg", "steghide",
    "stegseek", "stegsolve", "binwalk", "foremost", "exiftool", "tshark", "tcpdump",
    "wireshark", "gdb", "radare2", "r2", "ghidra", "ltrace", "strace", "checksec",
    "strings", "xxd", "file", "volatility", "vol", "searchsploit", "wpscan", "msfconsole",
    "metasploit", "cyberchef", "rsactftool", "pwntools", "ropgadget", "ropper", "grep",
    "zip2john", "ssh", "ftp", "smbclient", "bash", "python3",
}

def normaliza(texto):
    """minúsculas + sin acentos (para comparar sin importar tildes)."""
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.lower()

# ------------------------- Conversor Markdown ------------------------------

_slug_counts = {}

def slugify(text):
    text = re.sub(r"<[^>]+>", "", text)          # quita html
    text = re.sub(r"[`*_]", "", text)            # quita marcas md
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s]+", "-", text).strip("-")
    if not text:
        text = "sec"
    base = text
    n = _slug_counts.get(base, 0)
    _slug_counts[base] = n + 1
    return base if n == 0 else f"{base}-{n}"

def inline(text):
    """Formato en línea: escapa html y aplica `code`, **bold**, *italic*, [a](b)."""
    # Proteger spans de código inline primero
    codes = []
    def _stash(m):
        codes.append(m.group(1))
        return f"\x00{len(codes)-1}\x00"
    text = re.sub(r"`([^`]+)`", _stash, text)

    text = html.escape(text, quote=False)

    # enlaces [texto](url)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: f'<a href="{html.escape(m.group(2), quote=True)}" target="_blank" rel="noopener">{m.group(1)}</a>',
        text,
    )
    # negrita y cursiva
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)([^*]+)\*(?!\*)", r"<em>\1</em>", text)

    # restaurar code inline
    def _pop(m):
        c = html.escape(codes[int(m.group(1))], quote=False)
        return f"<code>{c}</code>"
    text = re.sub(r"\x00(\d+)\x00", _pop, text)
    return text

def _plano(texto):
    """Texto plano para indexar: quita marcas md, enlaces y comentarios html."""
    texto = re.sub(r"<!--.*?-->", " ", texto)
    texto = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", texto)  # [a](b) -> a
    texto = re.sub(r"[`*_>#|]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()

def _herramientas(texto):
    """Nombres de herramientas conocidas que aparezcan en el texto."""
    found = set()
    for tok in re.findall(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", texto):
        if tok.lower() in HERRAMIENTAS:
            found.add(tok.lower())
    return found

def convert(md, headings, secindex):
    """Convierte markdown a html.

    - Rellena `headings` con (nivel, texto, slug).
    - Rellena `secindex[slug] = {text:[...], tools:set(), tags:[...]}` con el
      cuerpo de cada sección (para el buscador).
    """
    lines = md.split("\n")
    out = []
    i = 0
    n = len(lines)

    current = None  # slug de la sección en curso

    def idx(texto="", tools=None, tags=None):
        if current is None:
            return
        e = secindex.setdefault(current, {"text": [], "tools": set(), "tags": []})
        if texto:
            e["text"].append(_plano(texto))
        if tools:
            e["tools"].update(tools)
        if tags:
            e["tags"].extend(tags)

    def close_list(stack):
        while stack:
            out.append("</ul>")
            stack.pop()

    list_stack = []  # niveles de indentación abiertos

    while i < n:
        line = lines[i]

        # Comentario de etiquetas:  <!-- tags: a, b, c -->  (no se renderiza)
        m = re.match(r"^\s*<!--\s*tags:\s*(.*?)\s*-->\s*$", line, re.IGNORECASE)
        if m:
            tags = [t.strip() for t in re.split(r"[,;]", m.group(1)) if t.strip()]
            idx(" ".join(tags), tags=tags)
            i += 1
            continue

        # Bloque de código ```
        m = re.match(r"^```(.*)$", line)
        if m:
            close_list(list_stack)
            lang = m.group(1).strip()
            buf = []
            i += 1
            while i < n and not re.match(r"^```", lines[i]):
                buf.append(lines[i])
                i += 1
            i += 1  # saltar cierre
            raw = "\n".join(buf)
            idx(raw, tools=_herramientas(raw))
            code = html.escape(raw, quote=False)
            cls = f' data-lang="{html.escape(lang, quote=True)}"' if lang else ""
            out.append(f'<div class="code"><button class="copy" title="Copiar">copiar</button><pre{cls}><code>{code}</code></pre></div>')
            continue

        # Encabezados
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            close_list(list_stack)
            level = len(m.group(1))
            text = m.group(2).strip()
            slug = slugify(text)
            if level in (1, 2, 3):
                clean = re.sub(r"[`*_]", "", text)
                headings.append((level, clean, slug))
                current = slug
                e = secindex.setdefault(slug, {"text": [], "tools": set(), "tags": []})
                e["text"].append(_plano(clean))
                e["tools"].update(_herramientas(clean))
            out.append(f'<h{level} id="{slug}">{inline(text)}<a class="anchor" href="#{slug}">#</a></h{level}>')
            i += 1
            continue

        # Separador ---
        if re.match(r"^\s*---\s*$", line):
            close_list(list_stack)
            out.append("<hr>")
            i += 1
            continue

        # Cita >
        if re.match(r"^\s*>\s?", line):
            close_list(list_stack)
            buf = []
            while i < n and re.match(r"^\s*>\s?", lines[i]):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            texto = " ".join(buf)
            idx(texto, tools=_herramientas(texto))
            out.append(f'<blockquote>{inline(texto)}</blockquote>')
            continue

        # Tabla (| a | b |)
        if "|" in line and i + 1 < n and re.match(r"^\s*\|?[\s:\-|]+\|?\s*$", lines[i + 1]) and "|" in lines[i + 1]:
            close_list(list_stack)
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            th = "".join(f"<th>{inline(c)}</th>" for c in header)
            trs = ""
            for r in rows:
                tds = "".join(f"<td>{inline(c)}</td>" for c in r)
                trs += f"<tr>{tds}</tr>"
                idx(" ".join(r), tools=_herramientas(" ".join(r)))
            idx(" ".join(header))
            out.append(f'<div class="tablewrap"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>')
            continue

        # Listas (con checkbox y anidación por indentación de 2 espacios)
        m = re.match(r"^(\s*)[-*+]\s+(.*)$", line)
        if m:
            indent = len(m.group(1))
            depth = indent // 2
            content = m.group(2)
            while len(list_stack) <= depth:
                out.append("<ul>")
                list_stack.append(len(list_stack))
            while len(list_stack) - 1 > depth:
                out.append("</ul>")
                list_stack.pop()
            cb = re.match(r"^\[([ xX])\]\s+(.*)$", content)
            if cb:
                checked = "checked" if cb.group(1).lower() == "x" else ""
                idx(cb.group(2), tools=_herramientas(cb.group(2)))
                out.append(f'<li class="task"><input type="checkbox" disabled {checked}>{inline(cb.group(2))}</li>')
            else:
                idx(content, tools=_herramientas(content))
                out.append(f"<li>{inline(content)}</li>")
            i += 1
            continue

        # Línea en blanco
        if line.strip() == "":
            close_list(list_stack)
            i += 1
            continue

        # Párrafo (juntar líneas hasta blanco/estructura)
        close_list(list_stack)
        buf = [line]
        i += 1
        while i < n and lines[i].strip() != "" and not re.match(r"^(#{1,6}\s|```|\s*>|\s*[-*+]\s|\s*---\s*$)", lines[i]):
            buf.append(lines[i])
            i += 1
        texto = " ".join(buf)
        idx(texto, tools=_herramientas(texto))
        out.append(f"<p>{inline(texto)}</p>")

    close_list(list_stack)
    return "\n".join(out)

# ------------------------------ Ensamblado ---------------------------------

def main():
    docs = []     # (id, titulo, emoji, html, headings)
    index = []    # entradas del buscador (se vuelca a JS)
    for fname, titulo, emoji, sec_id in FUENTES:
        path = CONTENIDO / fname
        if not path.exists():
            print(f"  ! falta {fname} — se omite")
            continue
        md = path.read_text(encoding="utf-8")
        headings = []
        secindex = {}
        body = convert(md, headings, secindex)
        docs.append((sec_id, titulo, emoji, body, headings))

        # Entradas del índice: una por encabezado nivel 2 y 3.
        for level, text, slug in headings:
            if level == 1:
                continue
            e = secindex.get(slug, {"text": [], "tools": set(), "tags": []})
            cuerpo = " ".join(e["text"])
            tools = sorted(e["tools"])
            tags = e["tags"]
            # texto buscable (normalizado): título + cuerpo + tags + herramientas
            blob = normaliza(" ".join([text, cuerpo, " ".join(tags), " ".join(tools)]))
            snippet = cuerpo.strip()
            if len(snippet) > 140:
                snippet = snippet[:140].rsplit(" ", 1)[0] + "…"
            index.append({
                "slug": slug, "title": text, "sec": sec_id, "secTitle": titulo,
                "secEmoji": emoji, "level": level, "tools": tools,
                "snippet": snippet, "text": blob,
            })
        print(f"  ok {fname}  ({len(headings)} encabezados)")

    # Menú lateral
    nav = []
    for sec_id, titulo, emoji, body, headings in docs:
        subs = []
        for level, text, slug in headings:
            if level == 1:
                continue  # el H1 es el título del doc, ya está en el grupo
            cls = "lvl2" if level == 2 else "lvl3"
            subs.append(f'<a class="{cls}" href="#{slug}" data-slug="{slug}">{html.escape(text, quote=False)}</a>')
        nav.append(
            f'<div class="navgroup" data-sec="{sec_id}">'
            f'<button class="navhead" aria-expanded="true">'
            f'<span class="ico">{emoji}</span><span>{html.escape(titulo)}</span>'
            f'<span class="chev">▾</span></button>'
            f'<div class="navlinks">{"".join(subs)}</div></div>'
        )
    nav_html = "\n".join(nav)

    # Chips de categoría
    chips = "".join(
        f'<button class="chip" data-q="{html.escape(q, quote=True)}">{html.escape(label)}</button>'
        for label, q in CATEGORIAS
    )

    # Datos para el buscador (normalizamos las claves de sinónimos por si acaso)
    syn = {normaliza(k): [normaliza(x) for x in v] for k, v in SINONIMOS.items()}
    def jdump(obj):
        # Escapar "<" evita que un "</script>" dentro del contenido cierre el
        # bloque <script> y rompa la página (se decodifica igual en JS).
        return json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c")
    data_js = (
        "window.__IDX__=" + jdump(index) + ";"
        "window.__SYN__=" + jdump(syn) + ";"
    )

    # Contenido
    sections = []
    for sec_id, titulo, emoji, body, headings in docs:
        sections.append(f'<section class="doc" id="sec-{sec_id}" data-sec="{sec_id}">\n{body}\n</section>')
    content_html = "\n".join(sections)

    html_out = (TEMPLATE
                .replace("{{NAV}}", nav_html)
                .replace("{{CHIPS}}", chips)
                .replace("{{DATA}}", data_js)
                .replace("{{CONTENT}}", content_html))
    SALIDA.write_text(html_out, encoding="utf-8")
    print(f"\n==> generado: {SALIDA}  ({len(index)} entradas en el índice)")
    print("   ábrelo con doble clic o: xdg-open index.html")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Apuntes CTF</title>
<style>
:root{
  --bg:#0f1115; --panel:#171a21; --panel2:#1d212b; --text:#e6e8ee; --muted:#9aa3b2;
  --accent:#5bd1a0; --accent2:#6aa8ff; --border:#2a2f3a; --code:#0b0d12; --code-text:#d7e3ff;
  --mark:#ffd86b;
}
@media (prefers-color-scheme: light){
  :root:not([data-theme="dark"]){
    --bg:#f6f7f9; --panel:#ffffff; --panel2:#eef1f5; --text:#1b1e24; --muted:#5a6475;
    --accent:#128a5c; --accent2:#2563eb; --border:#dde1e8; --code:#11151c; --code-text:#d7e3ff;
    --mark:#ffe08a;
  }
}
:root[data-theme="dark"]{
  --bg:#0f1115; --panel:#171a21; --panel2:#1d212b; --text:#e6e8ee; --muted:#9aa3b2;
  --accent:#5bd1a0; --accent2:#6aa8ff; --border:#2a2f3a; --code:#0b0d12; --code-text:#d7e3ff;
  --mark:#ffd86b;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0; background:var(--bg); color:var(--text);
  font:16px/1.65 system-ui,-apple-system,"Segoe UI",Roboto,Ubuntu,sans-serif;
  -webkit-text-size-adjust:100%;
}
a{color:var(--accent2); text-decoration:none}
a:hover{text-decoration:underline}

/* Layout */
.wrap{display:flex; min-height:100vh}
.sidebar{
  width:300px; flex:0 0 300px; background:var(--panel); border-right:1px solid var(--border);
  position:sticky; top:0; height:100vh; overflow-y:auto; padding:0 0 40px;
}
.main{flex:1 1 auto; min-width:0; padding:0 0 120px}
.inner{max-width:900px; margin:0 auto; padding:0 24px}

/* Topbar */
.topbar{
  position:sticky; top:0; z-index:20; background:var(--bg);
  border-bottom:1px solid var(--border); padding:12px 24px;
  display:flex; align-items:center; gap:12px;
}
.topbar h1{font-size:17px; margin:0; font-weight:650}
.topbar .sp{flex:1}
.btn{
  background:var(--panel2); color:var(--text); border:1px solid var(--border);
  border-radius:8px; padding:7px 11px; cursor:pointer; font-size:13px;
}
.btn:hover{border-color:var(--accent)}
.menu-toggle{display:none}

/* Sidebar brand + search */
.brand{padding:16px 18px 10px; display:flex; align-items:center; gap:10px; border-bottom:1px solid var(--border)}
.brand .logo{font-size:22px}
.brand .t{font-weight:700}
.brand .s{font-size:12px; color:var(--muted)}
.searchbox{padding:12px 14px; border-bottom:1px solid var(--border)}
.searchbox input{
  width:100%; padding:9px 11px; border-radius:8px; border:1px solid var(--border);
  background:var(--bg); color:var(--text); font-size:14px;
}
.searchbox input::placeholder{color:var(--muted)}

/* Nav */
.navgroup{border-bottom:1px solid var(--border)}
.navhead{
  width:100%; text-align:left; background:none; border:0; color:var(--text);
  padding:11px 14px; display:flex; align-items:center; gap:9px; cursor:pointer;
  font-size:14px; font-weight:650;
}
.navhead:hover{background:var(--panel2)}
.navhead .ico{font-size:16px}
.navhead .chev{margin-left:auto; color:var(--muted); transition:transform .15s}
.navhead[aria-expanded="false"] .chev{transform:rotate(-90deg)}
.navlinks{display:flex; flex-direction:column; padding:2px 0 8px}
.navgroup[aria-collapsed="true"] .navlinks{display:none}
.navlinks a{
  color:var(--muted); padding:5px 14px 5px 36px; font-size:13.5px; border-left:2px solid transparent;
}
.navlinks a.lvl3{padding-left:52px; font-size:12.5px; opacity:.9}
.navlinks a:hover{color:var(--text); text-decoration:none; background:var(--panel2)}
.navlinks a.active{color:var(--accent); border-left-color:var(--accent); background:var(--panel2)}
.navlinks a.hide{display:none}

/* Chips de categoría */
.chips{display:flex; flex-wrap:wrap; gap:6px; margin-top:10px}
.chip{
  background:var(--bg); color:var(--muted); border:1px solid var(--border);
  border-radius:999px; padding:4px 10px; font-size:12px; cursor:pointer; line-height:1.4;
}
.chip:hover{color:var(--text); border-color:var(--accent)}
.chip.active{background:var(--accent); color:#06231a; border-color:var(--accent); font-weight:650}

/* Panel de resultados del buscador */
#results{display:none}
#results.show{display:block}
#nav.hide{display:none}
.res-group{border-bottom:1px solid var(--border); padding:6px 0 10px}
.res-grouphead{
  display:flex; align-items:center; gap:7px; padding:9px 14px 4px;
  font-size:11px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; color:var(--muted);
}
.res-item{display:block; padding:7px 14px 8px; border-left:2px solid transparent; cursor:pointer}
.res-item:hover{background:var(--panel2); text-decoration:none; border-left-color:var(--accent)}
.res-title{color:var(--text); font-size:14px; font-weight:600}
.res-item.lvl3 .res-title{font-weight:500}
.res-snippet{color:var(--muted); font-size:12px; margin-top:2px; line-height:1.45}
.res-tools{margin-top:5px; display:flex; flex-wrap:wrap; gap:4px}
.res-tools .pill{
  font-size:10.5px; background:var(--panel2); color:var(--accent); border:1px solid var(--border);
  border-radius:5px; padding:1px 6px; font-family:ui-monospace,Menlo,Consolas,monospace;
}
.res-empty{color:var(--muted); font-size:13px; padding:20px 14px; text-align:center}
.res-item mark, .res-snippet mark{background:var(--mark); color:#111; padding:0 1px; border-radius:2px}

/* Content */
.doc{padding-top:8px}
.doc h1{font-size:28px; margin:34px 0 8px; padding-bottom:8px; border-bottom:2px solid var(--border)}
.doc h2{font-size:22px; margin:40px 0 10px; scroll-margin-top:70px}
.doc h3{font-size:18px; margin:26px 0 8px; scroll-margin-top:70px; color:var(--accent)}
.doc h4{font-size:15.5px; margin:20px 0 6px; color:var(--muted); text-transform:uppercase; letter-spacing:.03em}
.doc h1,.doc h2,.doc h3{scroll-margin-top:70px}
.anchor{opacity:0; margin-left:8px; color:var(--muted); font-weight:400; text-decoration:none}
h1:hover .anchor,h2:hover .anchor,h3:hover .anchor{opacity:.6}
.doc p{margin:10px 0}
.doc ul{margin:8px 0; padding-left:22px}
.doc li{margin:4px 0}
.doc li.task{list-style:none; margin-left:-22px; display:flex; gap:8px; align-items:flex-start}
.doc li.task input{margin-top:5px}
blockquote{
  margin:12px 0; padding:10px 14px; border-left:3px solid var(--accent);
  background:var(--panel); border-radius:0 8px 8px 0; color:var(--muted);
}
hr{border:0; border-top:1px solid var(--border); margin:28px 0}

/* code */
code{
  background:var(--panel2); padding:2px 6px; border-radius:5px; font-size:.9em;
  font-family:"JetBrains Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
.code{position:relative; margin:14px 0}
.code pre{
  background:var(--code); color:var(--code-text); padding:14px 16px; border-radius:10px;
  overflow:auto; border:1px solid var(--border); margin:0;
}
.code pre code{background:none; padding:0; color:inherit; font-size:13.5px; line-height:1.6}
.code pre[data-lang]::before{
  content:attr(data-lang); position:absolute; top:0; left:14px; transform:translateY(-50%);
  font-size:11px; color:var(--muted); background:var(--bg); padding:0 6px; border-radius:4px;
}
.copy{
  position:absolute; top:8px; right:8px; z-index:2; font-size:11px; padding:4px 8px;
  background:var(--panel2); color:var(--muted); border:1px solid var(--border);
  border-radius:6px; cursor:pointer; opacity:0; transition:opacity .12s;
}
.code:hover .copy{opacity:1}
.copy:hover{color:var(--text); border-color:var(--accent)}
.copy.done{color:var(--accent); border-color:var(--accent)}

/* tables */
.tablewrap{overflow-x:auto; margin:14px 0}
table{border-collapse:collapse; width:100%; font-size:14px}
th,td{border:1px solid var(--border); padding:8px 10px; text-align:left; vertical-align:top}
th{background:var(--panel2)}

mark{background:var(--mark); color:#111; padding:0 2px; border-radius:3px}

.empty{display:none; color:var(--muted); padding:30px 24px; text-align:center}

/* scroll-to-top */
.totop{
  position:fixed; right:18px; bottom:18px; z-index:30; width:42px; height:42px; border-radius:50%;
  background:var(--accent); color:#06231a; border:0; font-size:20px; cursor:pointer;
  box-shadow:0 4px 14px rgba(0,0,0,.3); display:none;
}
.totop.show{display:block}

/* responsive */
@media (max-width:860px){
  .menu-toggle{display:inline-flex}
  .sidebar{
    position:fixed; left:0; top:0; z-index:40; height:100vh; transform:translateX(-100%);
    transition:transform .2s; box-shadow:4px 0 20px rgba(0,0,0,.35);
  }
  body.nav-open .sidebar{transform:translateX(0)}
  .backdrop{
    display:none; position:fixed; inset:0; background:rgba(0,0,0,.5); z-index:35;
  }
  body.nav-open .backdrop{display:block}
  .inner{padding:0 16px}
  .topbar{padding:12px 16px}
}
</style>
</head>
<body>
<div class="wrap">
  <aside class="sidebar" id="sidebar">
    <div class="brand">
      <span class="logo">🚩</span>
      <div>
        <div class="t">Apuntes CTF</div>
        <div class="s">CyberFEI 3.0 · kit offline</div>
      </div>
    </div>
    <div class="searchbox">
      <input id="search" type="search" placeholder="Buscar: osint, nmap, ssh, estego…" autocomplete="off" title="Atajo: pulsa /">
      <div class="chips">{{CHIPS}}</div>
    </div>
    <nav id="nav">
      {{NAV}}
    </nav>
    <div id="results"></div>
  </aside>

  <div class="backdrop" id="backdrop"></div>

  <main class="main">
    <div class="topbar">
      <button class="btn menu-toggle" id="menuToggle" aria-label="Menú">☰</button>
      <h1>🚩 Apuntes CTF</h1>
      <span class="sp"></span>
      <button class="btn" id="themeBtn" title="Tema claro/oscuro">🌓</button>
    </div>
    <div class="inner">
      {{CONTENT}}
    </div>
  </main>
</div>

<button class="totop" id="totop" title="Arriba">↑</button>

<script>{{DATA}}</script>
<script>
(function(){
  // --- Tema ---
  var themeBtn = document.getElementById('themeBtn');
  try{ var saved = localStorage.getItem('ctf-theme'); if(saved){ document.documentElement.setAttribute('data-theme', saved); } }catch(e){}
  themeBtn.addEventListener('click', function(){
    var cur = document.documentElement.getAttribute('data-theme');
    var isDark = cur ? cur==='dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
    var next = isDark ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try{ localStorage.setItem('ctf-theme', next); }catch(e){}
  });

  // --- Menú móvil ---
  var body = document.body;
  var mt = document.getElementById('menuToggle');
  var bd = document.getElementById('backdrop');
  function closeNav(){ body.classList.remove('nav-open'); }
  mt.addEventListener('click', function(){ body.classList.toggle('nav-open'); });
  bd.addEventListener('click', closeNav);

  // --- Grupos plegables ---
  document.querySelectorAll('.navhead').forEach(function(h){
    h.addEventListener('click', function(){
      var g = h.closest('.navgroup');
      var open = g.getAttribute('aria-collapsed') !== 'true';
      g.setAttribute('aria-collapsed', open ? 'true' : 'false');
      h.setAttribute('aria-expanded', open ? 'false' : 'true');
    });
  });

  // --- Links: cerrar menú en móvil al navegar ---
  var links = Array.prototype.slice.call(document.querySelectorAll('.navlinks a'));
  links.forEach(function(a){ a.addEventListener('click', function(){ if(window.innerWidth<=860) closeNav(); }); });

  // --- Copiar bloques de código ---
  document.querySelectorAll('.code .copy').forEach(function(btn){
    btn.addEventListener('click', function(){
      var code = btn.parentElement.querySelector('pre code');
      var text = code ? code.innerText : '';
      function ok(){ btn.textContent='copiado'; btn.classList.add('done'); setTimeout(function(){ btn.textContent='copiar'; btn.classList.remove('done'); },1200); }
      if(navigator.clipboard && navigator.clipboard.writeText){
        navigator.clipboard.writeText(text).then(ok, fallback);
      } else { fallback(); }
      function fallback(){
        try{ var ta=document.createElement('textarea'); ta.value=text; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta); ok(); }catch(e){}
      }
    });
  });

  // --- Buscador inteligente ---
  var search  = document.getElementById('search');
  var nav      = document.getElementById('nav');
  var results  = document.getElementById('results');
  var chips    = Array.prototype.slice.call(document.querySelectorAll('.chip'));
  var IDX = window.__IDX__ || [];
  var SYN = window.__SYN__ || {};

  function norm(s){
    return (s||'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase();
  }
  // ¿`text` contiene `term` como palabra (no incrustado en otra)? Evita que
  // "22" o "nc" casen dentro de "2022" o "once". Términos con símbolos
  // (/dev/tcp, -p-, flag{) se buscan como subcadena.
  function has(text, term){
    if(!term) return false;
    var alnum = /[a-z0-9]/.test(term), from=0, p;
    while((p=text.indexOf(term, from))>=0){
      if(!alnum) return true;
      var b = p>0 ? text[p-1] : ' ';
      var a = (p+term.length<text.length) ? text[p+term.length] : ' ';
      if(!/[a-z0-9]/.test(b) && !/[a-z0-9]/.test(a)) return true;
      from = p+1;
    }
    return false;
  }
  function esc(s){ return s.replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }

  // Resalta en `texto` los términos (ya normalizados) sin romper acentos visibles.
  function resaltar(texto, terms){
    if(!terms.length) return esc(texto);
    var ntext = norm(texto), out='', used=new Array(texto.length).fill(false);
    terms.forEach(function(t){
      if(!t) return;
      var from=0, p;
      while((p=ntext.indexOf(t, from))>=0){
        for(var k=p;k<p+t.length;k++) used[k]=true;
        from=p+t.length;
      }
    });
    var open=false;
    for(var i=0;i<texto.length;i++){
      if(used[i] && !open){ out+='<mark>'; open=true; }
      if(!used[i] && open){ out+='</mark>'; open=false; }
      out+=esc(texto[i]);
    }
    if(open) out+='</mark>';
    return out;
  }

  // Expande el query: tokens propios + sinónimos de las claves que coincidan.
  function expandir(q){
    var tokens = q.split(/\s+/).filter(Boolean);
    var terms = {};           // término -> true (para resaltar/buscar)
    tokens.forEach(function(t){ terms[t]=true; });
    // frases completas y tokens contra el diccionario de sinónimos
    Object.keys(SYN).forEach(function(key){
      if(q.indexOf(key)>=0 || tokens.indexOf(key)>=0){
        SYN[key].forEach(function(x){ terms[x]=true; });
      }
    });
    return { tokens: tokens, terms: Object.keys(terms) };
  }

  function buscar(q){
    q = norm(q.trim());
    if(!q){ mostrarMenu(); return; }
    var ex = expandir(q);
    var hits = [];
    IDX.forEach(function(e){
      // Frase-concepto: si el query contiene una clave multi-palabra del
      // diccionario (ej. "escaneo de puertos"), basta con que la entrada
      // tenga alguno de sus sinónimos.
      var phraseHit = Object.keys(SYN).some(function(key){
        return key.indexOf(' ')>=0 && q.indexOf(key)>=0
            && SYN[key].some(function(x){ return has(e.text, x); });
      });
      // Si no, cada token del query debe estar satisfecho (él o un sinónimo suyo).
      var ok = phraseHit || ex.tokens.every(function(tok){
        if(has(e.text, tok)) return true;
        var syn = SYN[tok]; // sinónimos exactos de ese token
        if(syn && syn.some(function(x){ return has(e.text, x); })) return true;
        return false;
      });
      if(!ok) return;
      // score: título pesa más; + por término encontrado; + por herramienta
      var score=0, title=norm(e.title);
      ex.terms.forEach(function(t){
        if(!t) return;
        if(has(title, t)) score+=5;
        if(has(e.text, t)) score+=1;
        if(e.tools.indexOf(t)>=0) score+=2;
      });
      hits.push({e:e, score:score});
    });
    hits.sort(function(a,b){ return b.score-a.score || a.e.level-b.e.level; });
    render(hits.map(function(h){ return h.e; }), ex.terms);
  }

  function render(items, terms){
    nav.classList.add('hide');
    results.classList.add('show');
    if(!items.length){
      results.innerHTML = '<div class="res-empty">Sin resultados.<br>Prueba otra palabra o un chip de categoría.</div>';
      return;
    }
    // agrupar por sección respetando el orden del índice (= orden de FUENTES)
    var order=[], groups={};
    items.forEach(function(e){
      if(!groups[e.sec]){ groups[e.sec]={emoji:e.secEmoji, title:e.secTitle, items:[]}; order.push(e.sec); }
      groups[e.sec].items.push(e);
    });
    var htmlout='';
    order.forEach(function(sec){
      var g=groups[sec];
      htmlout += '<div class="res-group"><div class="res-grouphead"><span>'+g.emoji+'</span><span>'+esc(g.title)+'</span></div>';
      g.items.forEach(function(e){
        var tools = e.tools.filter(function(t){ return terms.indexOf(t)>=0; }).slice(0,6);
        if(!tools.length) tools = e.tools.slice(0,4);
        var pills = tools.length ? '<div class="res-tools">'+tools.map(function(t){ return '<span class="pill">'+esc(t)+'</span>'; }).join('')+'</div>' : '';
        var snip = e.snippet ? '<div class="res-snippet">'+resaltar(e.snippet, terms)+'</div>' : '';
        htmlout += '<a class="res-item '+(e.level===3?'lvl3':'')+'" href="#'+e.slug+'" data-slug="'+e.slug+'">'
                 +   '<div class="res-title">'+resaltar(e.title, terms)+'</div>'+snip+pills
                 + '</a>';
      });
      htmlout += '</div>';
    });
    results.innerHTML = htmlout;
    // clic en resultado: cerrar menú en móvil
    results.querySelectorAll('.res-item').forEach(function(a){
      a.addEventListener('click', function(){ if(window.innerWidth<=860) closeNav(); });
    });
  }

  function mostrarMenu(){
    results.classList.remove('show');
    results.innerHTML='';
    nav.classList.remove('hide');
  }

  search.addEventListener('input', function(){
    chips.forEach(function(c){ if(norm(c.getAttribute('data-q'))!==norm(search.value)) c.classList.remove('active'); });
    buscar(search.value);
  });

  // Chips: clic ejecuta la consulta (o la limpia si ya estaba activa)
  chips.forEach(function(c){
    c.addEventListener('click', function(){
      var q = c.getAttribute('data-q');
      if(c.classList.contains('active')){
        c.classList.remove('active'); search.value=''; mostrarMenu(); return;
      }
      chips.forEach(function(x){ x.classList.remove('active'); });
      c.classList.add('active');
      search.value = q;
      buscar(q);
    });
  });

  // Atajos: "/" enfoca, Esc limpia, Enter salta al primer resultado
  document.addEventListener('keydown', function(ev){
    if(ev.key==='/' && document.activeElement!==search){ ev.preventDefault(); search.focus(); search.select(); }
    else if(ev.key==='Escape' && document.activeElement===search){ search.value=''; chips.forEach(function(x){x.classList.remove('active');}); mostrarMenu(); search.blur(); }
    else if(ev.key==='Enter' && document.activeElement===search){
      var first=results.querySelector('.res-item');
      if(first){ ev.preventDefault(); first.click(); location.hash=first.getAttribute('data-slug'); if(window.innerWidth<=860) closeNav(); }
    }
  });

  // --- Resaltar sección activa al hacer scroll (scrollspy) ---
  var map = {};
  links.forEach(function(a){ var s=a.getAttribute('data-slug'); if(s) map[s]=a; });
  var targets = Object.keys(map).map(function(s){ return document.getElementById(s); }).filter(Boolean);
  var current = null;
  if('IntersectionObserver' in window){
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(en){
        if(en.isIntersecting){
          var a = map[en.target.id];
          if(a && a!==current){
            if(current) current.classList.remove('active');
            a.classList.add('active');
            current = a;
            // asegurar que el grupo esté abierto
            var g=a.closest('.navgroup'); if(g && g.getAttribute('aria-collapsed')==='true'){ /* no forzamos */ }
          }
        }
      });
    }, {rootMargin:'-60px 0px -70% 0px', threshold:0});
    targets.forEach(function(t){ io.observe(t); });
  }

  // --- Botón arriba ---
  var totop = document.getElementById('totop');
  window.addEventListener('scroll', function(){
    totop.classList.toggle('show', window.scrollY>400);
  });
  totop.addEventListener('click', function(){ window.scrollTo({top:0,behavior:'smooth'}); });
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
