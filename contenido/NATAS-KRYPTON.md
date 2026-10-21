# OverTheWire Natas + Krypton — explicados

Recorrido razonado de dos wargames de OverTheWire:

- **Natas** — seguridad **web del lado del servidor** (se juega en el navegador: fuente HTML, cabeceras, cookies, parámetros, inyecciones). Herramientas: navegador, `curl`, proxy (ZAP/Burp).
- **Krypton** — **criptografía clásica** (se juega por **SSH**: lees archivos y descifras).

Convención: MAYÚSCULAS = lo cambias tú (tu contraseña, tu ruta). Cada nivel trae **Concepto · Técnica · Comando · Lección**.

Idea transversal que se repite en casi todo: **nunca confíes en datos que controla el cliente** (fuente, cabeceras, cookies, parámetros). La validación de seguridad va en el servidor.

---

## Natas (web — server-side)

Se accede por navegador con **HTTP Basic Auth**. Cada nivel:
`http://natasN.natas.labs.overthewire.org` · usuario `natasN` · la pass de `natasN` la sacaste en el nivel anterior. Las contraseñas también están en `/etc/natas_webpass/natasN` dentro del servidor.

Reflejo base en cada nivel **antes** de lanzar herramientas: mira la **página**, su **código fuente** (`Ctrl+U`), la **URL/parámetros**, las **cookies** y las **cabeceras**. Y si hay enlace **"View sourcecode"**, léelo: es el PHP del servidor.

### Natas 0 → 1 — pass en el código fuente
- **Concepto:** lo visible en la página no es todo lo que se envía al navegador.
- **Técnica:** ver el código fuente y buscar comentarios HTML `<!-- ... -->`.
- **Comando:** `Ctrl+U` en el navegador (o `curl -u natas0:natas0 http://natas0.natas.labs.overthewire.org/`).
- **Lección:** ocultar algo en un comentario no lo protege; el cliente recibe todo el HTML.

### Natas 1 → 2 — igual, con click derecho bloqueado
- **Concepto:** bloquear la UI (click derecho) ≠ proteger el dato.
- **Técnica:** `Ctrl+U` igualmente, o DevTools (`F12`). El bloqueo es solo cosmético.
- **Lección:** la seguridad del lado del cliente es una ilusión; se salta trivialmente.

### Natas 2 → 3 — directory listing (`/files/`)
- **Concepto:** no importa *el archivo* (un pixel 1×1 transparente, señuelo sin metadata), importa **de qué carpeta se carga**.
- **Técnica:** en el fuente aparece `<img src="files/pixel.png">`. Visitar la **carpeta** directa: `/files/`. El servidor tiene el **listado de directorios activado** → se ve `users.txt` con la pass.
- **Comando:** navegar a `http://natas2.natas.labs.overthewire.org/files/`
- **Lección:** el *directory listing* activado filtra archivos que no debían verse.

### Natas 3 → 4 — `robots.txt`
- **Concepto:** la pista *"Not even Google will find it"* apunta a cómo se le dice a los buscadores qué no indexar.
- **Técnica:** leer `robots.txt` (público). La línea `Disallow:` revela una carpeta "secreta" con `users.txt`.
- **Comando:** navegar a `http://natas3.natas.labs.overthewire.org/robots.txt`
- **Lección:** `robots.txt` es una lista **pública** de lo que quieres esconder. "Ocultar" revela.

### Natas 4 → 5 — falsificar la cabecera `Referer`
- **Concepto:** el servidor decide el acceso según la cabecera HTTP `Referer` ("vengo de esta página")... que la pone el **cliente**.
- **Técnica:** mandar un `Referer` falso con el valor exacto que pide el mensaje de error.
- **Comando:**
  ```bash
  curl -u natas4:TU_PASS -H "Referer: http://natas5.natas.labs.overthewire.org/" http://natas4.natas.labs.overthewire.org/ | grep -i pass
  ```
- **Trampa habitual:** las `\` de continuación de línea **solo** valen si pulsas Enter tras cada una. En una sola línea, quita todas las `\` (si no: `curl: (3) URL rejected: Malformed input`).
- **Lección:** `Referer`, `User-Agent`, cookies... los controla el cliente y se falsean. No sirven para autorizar.

### Natas 5 → 6 — cookie de sesión falsificable
- **Concepto:** dice "no estás logueado" sin formulario → lo decide una **cookie**.
- **Técnica:** ver `Set-Cookie` (con `curl -i`), ves `loggedin=0`; cámbiala a `1`.
- **Comando:**
  ```bash
  curl -i -u natas5:TU_PASS http://natas5.natas.labs.overthewire.org/        # ver la cookie
  curl -u natas5:TU_PASS -b "loggedin=1" http://natas5.natas.labs.overthewire.org/ | grep -i pass
  ```
- **Lección:** una cookie sin firmar (`loggedin=0/1`) es trivial de manipular. Las sesiones reales usan tokens firmados (HMAC) o aleatorios.

### Natas 6 → 7 — leer el fuente PHP (archivo incluido accesible)
- **Concepto:** primer nivel donde hay que **leer la lógica del servidor**. El PHP hace `include "includes/secret.inc"` y compara tu input con `$secret`.
- **Técnica:** pedir el archivo incluido directamente. Si sale en blanco (PHP no imprime), míralo con `Ctrl+U` o `curl`.
- **Comando:** `curl -u natas6:TU_PASS http://natas6.natas.labs.overthewire.org/includes/secret.inc` → metes el secreto en el formulario.
- **Lección:** separar un secreto en otro fichero no sirve si ese fichero es descargable. Los secretos van fuera del webroot o en config protegida.

### Natas 7 → 8 — LFI (Local File Inclusion)
- **Concepto:** primera inyección real. La web usa `index.php?page=home` metiendo el parámetro directo en un `include`.
- **Técnica:** cambiar `page` por la ruta del archivo a leer (la pista del fuente da la ruta exacta).
- **Comando:**
  ```bash
  curl -u natas7:TU_PASS "http://natas7.natas.labs.overthewire.org/index.php?page=/etc/natas_webpass/natas8"
  ```
- **Lección:** nunca metas input del usuario en una ruta/`include` sin validar. LFI permite leer archivos arbitrarios (`/etc/passwd`, contraseñas...).

### Natas 8 → 9 — codificación reversible (hex + strrev + base64)
- **Concepto:** el secreto está "escondido" con `bin2hex(strrev(base64_encode($secret)))`. Codificación, **no** cifrado: sin clave, reversible.
- **Técnica:** deshacer cada paso en orden inverso: `hex2bin` → `strrev` → `base64_decode`.
- **Comando:**
  ```bash
  echo "3d3d516343746d4d6d6c315669563362" | xxd -r -p | rev | base64 -d
  # o: php -r 'echo base64_decode(strrev(hex2bin("3d3d...")));'
  ```
- **Lección:** codificar ≠ cifrar. Base64/hex/invertir no protegen nada: no hay clave.

### Natas 9 → 10 — command injection
- **Concepto:** `passthru("grep -i $key dictionary.txt")` mete tu texto **tal cual** en un comando de shell.
- **Técnica:** cerrar el comando y encadenar el tuyo con `;`.
- **Comando (en el campo de búsqueda):** `; cat /etc/natas_webpass/natas10 ;`
- **Lección:** nunca construyas comandos de shell concatenando input. Lleva a RCE (ejecución remota de código), el peor caso.

### Natas 10 → 11 — blacklist incompleta (abusar de grep)
- **Concepto:** mismo bug, pero filtran `; | &` con `preg_match('/[;|&]/',$key)`. Ya no encadenas... pero **el grep sigue siendo tuyo**.
- **Técnica:** pasar un patrón que casa con todo (`.*`) + un segundo archivo. Grep imprime, por cada archivo, las líneas que coinciden.
- **Comando (en el campo):** `.* /etc/natas_webpass/natas11`
  → se ejecuta `grep -i .* /etc/natas_webpass/natas11 dictionary.txt`
- **Lección:** las blacklists casi siempre fallan; dejan mil formas de abusar lo permitido. Mejor whitelist estricta o no tocar la shell.

### Natas 11 → 12 — XOR con clave reutilizada (known-plaintext)
- **Concepto:** la cookie `data` = `base64(xor_encrypt(json))`. Necesitas `showpassword=yes`, pero la clave XOR está censurada.
- **Técnica (ataque de texto plano conocido):** conoces el **plano por defecto** (`{"showpassword":"no","bgcolor":"#ffffff"}`) y tienes el **cifrado** (tu cookie). Propiedad del XOR: `cifrado XOR plano = clave`. Recuperas la clave (se repite) y fabricas tu cookie con `yes`.
- **Comando (PHP):**
  ```php
  <?php
  function xc($in,$k){$o="";for($i=0;$i<strlen($in);$i++)$o.=$in[$i]^$k[$i%strlen($k)];return $o;}
  $cif = base64_decode("TU_COOKIE");
  $clave = xc($cif, json_encode(array("showpassword"=>"no","bgcolor"=>"#ffffff")));
  echo base64_encode(xc(json_encode(array("showpassword"=>"yes","bgcolor"=>"#ffffff")), $clave))."\n";
  ```
  Pones esa cookie nueva (`F12 → Cookies` o `curl -b "data=..."`) y recargas.
- **Lección:** reutilizar clave en XOR es un desastre: con parte del plano conocido se recupera la clave. Y una cookie decide permisos → mal. Cookies firmadas/autenticadas.

---

## Krypton (cripto clásica)

Se juega por **SSH**: `ssh kryptonN@krypton.labs.overthewire.org -p 2231`. Los archivos están en `/krypton/kryptonN/`. Truco mental: te conectas como `kryptonN`, pero la pass de `kryptonN` se obtiene descifrando los datos del reto de `krypton(N-1)`; los nombres de archivo apuntan al nivel **destino**.

### Krypton 0 → 1 — Base64
- **Concepto:** la pass viene codificada en **Base64** (texto A–Z a–z 0–9 `+` `/`, suele acabar en `=`). Codificación, no cifrado.
- **Técnica/Comando:** `echo "S1JZUFRPTklTR1JFQVQ=" | base64 -d` → da la pass en MAYÚSCULAS.
- **Lección:** reconocer y decodificar Base64 al instante; es la primera capa típica en CTF.

### Krypton 1 → 2 — César / ROT13 (clave conocida)
- **Concepto:** cifrado César (desplaza cada letra N posiciones). ROT13 = desplazamiento 13; como 13 es la mitad de 26, **es su propia inversa** (cifrar y descifrar es la misma operación).
- **Técnica/Comando:** `cat krypton2 | tr 'A-Za-z' 'N-ZA-Mn-za-m'`
  - Ej.: `YRIRY GJB CNFFJBEQ EBGGRA` → `LEVEL TWO PASSWORD ROTTEN` (pass = `ROTTEN`).
- **Lección:** ROT13/César es ofuscación, no seguridad: solo 25 desplazamientos, se rompe a mano.

### Krypton 2 → 3 — César con clave desconocida (oráculo de cifrado)
- **Concepto:** César pero **no sabes el desplazamiento**. La clave: hay un binario `encrypt` que cifra lo que le des (clave en `keyfile.dat`, que no puedes leer).
- **Técnica (chosen-plaintext / oráculo):** cifras un texto **que tú eliges** (el alfabeto completo) y observas la salida → obtienes la tabla de sustitución entera sin leer la clave. Luego inviertes sobre el archivo de la pass.
- **Comando:**
  ```bash
  mkdir /tmp/mio; cd /tmp/mio
  ln -s /krypton/krypton2/keyfile.dat            # encrypt lo busca en el CWD
  echo "ABCDEFGHIJKLMNOPQRSTUVWXYZ" > plano.txt
  /krypton/krypton2/encrypt plano.txt            # genera ciphertext.out
  cat ciphertext.out                             # tu tabla: p.ej. A->N (resultó ROT13)
  cat /krypton/krypton2/krypton3 | tr 'CIFRADO' 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'   # invertir
  ```
  (Si la tabla sale `NOPQ...`, es ROT13: descifras con el mismo `tr 'A-Za-z' 'N-ZA-Mn-za-m'`.)
- **Lección:** tener acceso a la función de cifrado rompe los cifrados débiles. La cripto moderna se diseña para resistir incluso *chosen-plaintext*.

---

## Patrones y lecciones (resumen)

- **No confíes en el cliente:** fuente HTML, `Referer`, `User-Agent`, cookies y parámetros los controla el usuario → se falsean. Autoriza en el servidor.
- **Ocultar ≠ proteger:** comentarios, `robots.txt`, directory listing, archivos "incluidos" accesibles... todo filtra.
- **Codificar ≠ cifrar:** Base64, hex, invertir, ROT13 no tienen clave → reversibles por cualquiera.
- **Input sin validar = inyección:** en rutas/`include` → LFI; en comandos de shell → command injection/RCE. Blacklists fallan; usa whitelist o evita la shell.
- **Cripto débil cae con texto conocido/elegido:** XOR con clave reutilizada (known-plaintext) y César con oráculo (chosen-plaintext).
- **Reconocer formatos:** `=` final → Base64; texto en MAYÚSCULAS desplazado → César/ROT.
