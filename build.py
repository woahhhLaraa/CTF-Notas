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
import re
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent         # raíz del repo
CONTENIDO = RAIZ / "contenido"                  # aquí viven los .md
SALIDA = RAIZ / "index.html"

# ---- Lista de secciones. Para añadir contenido, agrega una tupla aquí. ----
# (nombre_de_archivo_en_Descargas, título visible, emoji, id_seccion)
FUENTES = [
    ("COMANDOS.md",               "Comandos",            "⌨️", "comandos"),
    ("GUIA-EXPLICADA.md",         "Guía explicada",      "📖", "guia"),
    ("PREPARACION-OFFLINE.md",    "Preparación offline", "📦", "preparacion"),
]

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

def convert(md, headings):
    """Convierte markdown a html. Rellena `headings` con (nivel, texto, slug)."""
    lines = md.split("\n")
    out = []
    i = 0
    n = len(lines)

    def close_list(stack):
        while stack:
            out.append("</ul>")
            stack.pop()

    list_stack = []  # niveles de indentación abiertos

    while i < n:
        line = lines[i]

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
            code = html.escape("\n".join(buf), quote=False)
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
                headings.append((level, re.sub(r"[`*_]", "", text), slug))
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
            out.append(f'<blockquote>{inline(" ".join(buf))}</blockquote>')
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
                out.append(f'<li class="task"><input type="checkbox" disabled {checked}>{inline(cb.group(2))}</li>')
            else:
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
        out.append(f"<p>{inline(' '.join(buf))}</p>")

    close_list(list_stack)
    return "\n".join(out)

# ------------------------------ Ensamblado ---------------------------------

def main():
    docs = []  # (id, titulo, emoji, html, headings)
    for fname, titulo, emoji, sec_id in FUENTES:
        path = CONTENIDO / fname
        if not path.exists():
            print(f"  ! falta {fname} — se omite")
            continue
        md = path.read_text(encoding="utf-8")
        headings = []
        body = convert(md, headings)
        docs.append((sec_id, titulo, emoji, body, headings))
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

    # Contenido
    sections = []
    for sec_id, titulo, emoji, body, headings in docs:
        sections.append(f'<section class="doc" id="sec-{sec_id}" data-sec="{sec_id}">\n{body}\n</section>')
    content_html = "\n".join(sections)

    html_out = TEMPLATE.replace("{{NAV}}", nav_html).replace("{{CONTENT}}", content_html)
    SALIDA.write_text(html_out, encoding="utf-8")
    print(f"\n==> generado: {SALIDA}")
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
      <input id="search" type="search" placeholder="Buscar en el menú…" autocomplete="off">
    </div>
    <nav id="nav">
      {{NAV}}
    </nav>
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

  // --- Buscador del menú ---
  var search = document.getElementById('search');
  search.addEventListener('input', function(){
    var q = search.value.trim().toLowerCase();
    document.querySelectorAll('.navgroup').forEach(function(g){
      var any=false;
      g.querySelectorAll('.navlinks a').forEach(function(a){
        var match = !q || a.textContent.toLowerCase().indexOf(q)>=0;
        a.classList.toggle('hide', !match);
        if(match) any=true;
      });
      g.style.display = any ? '' : 'none';
    });
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
