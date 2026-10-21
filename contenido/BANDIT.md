# Comandos de OverTheWire Bandit — explicados

> Todos los comandos que Bandit te hace usar, con qué hacen y la trampa típica.
> Pensado para leer bajo presión: buscas el comando, ves el ejemplo, lo copias.
> La contraseña de cada nivel casi siempre es **una sola cadena de ~32
> caracteres**; si lo que ves es más largo, aún no es la flag.

## 0. Moverte y mirar

```bash
ls              # lista archivos de la carpeta actual
ls -a           # TAMBIÉN los ocultos (empiezan con punto: .file2)
ls -la          # ocultos + detalles (tamaño, permisos, dueño)
ls -la --color  # colorea; útil cuando hay archivos con nombres raros
cd carpeta      # entra a una CARPETA (no a un archivo)
cd ..           # sube un nivel
cd ~            # vuelve a tu home
cd -            # vuelve a la carpeta anterior
pwd             # dice en qué carpeta estás
```

- **`cd` solo entra a carpetas.** Para ver un archivo usa `cat`, no `cd`.
- Un archivo que empieza con `.` está **oculto**: no sale en `ls` normal, sí en `ls -a`.

## 1. Nombres de archivo raros (la trampa de Bandit)

Bandit te da archivos como `-`, `-file1`, `spaces in this filename`, `.hidden`.
El problema es que el nombre confunde al comando.

```bash
cat ./-file1                 # nombre que empieza con "-": antepón ./
cat -- -file1                # alternativa: -- dice "ya no hay más opciones"
cat "spaces in this file"    # nombre con espacios: entre comillas
cat spaces\ in\ this\ file   # o escapando cada espacio con \
cat ./.hidden                # archivo oculto: va con su punto
```

- Si un nombre empieza con `-`, el comando cree que es una **opción**. Antepón
  `./` o usa `--`.
- Si el nombre tiene **espacios**, ponlo entre `"comillas"` o escapa con `\`.
- Truco: escribe las primeras letras y pulsa **Tab**; la terminal completa y
  escapa el nombre por ti.

## 2. Leer el contenido de un archivo

```bash
cat archivo         # vuelca TODO el archivo a la pantalla
less archivo        # lo abre paginado (flechas para moverte, q para salir)
head archivo        # primeras 10 líneas
head -1 archivo     # solo la primera línea (útil si hay relleno debajo)
tail archivo        # últimas 10 líneas
tail -5 archivo     # últimas 5 líneas
```

- Si `cat` saca "basura" (binario), no es texto: pásalo por `file` primero.
- Si el archivo trae la flag arriba y relleno abajo, `head -1` te la deja sola.

## 3. ¿Qué tipo de archivo es?

```bash
file archivo              # dice qué es: ASCII text, ELF, gzip, data...
file ./*                  # el tipo de TODOS los de la carpeta
find . -type f -exec file {} +   # el tipo de todos, incluso en subcarpetas
```

- Antes de romperte la cabeza, `file` te dice si es texto, imagen, comprimido o
  ejecutable. Marca el siguiente paso.

## 4. `find` — buscar archivos por características

El comando estrella de Bandit. Busca por nombre, tamaño, dueño, permisos.

```bash
find .                        # lista todo bajo la carpeta actual (recursivo)
find . -type f                # solo archivos (no carpetas)
find . -name "*.txt"          # por nombre / extensión
find . -iname "FLAG*"         # -i = sin distinguir mayúsculas

# Por TAMAÑO (la 'c' = bytes exactos):
find . -size 1033c            # exactamente 1033 bytes
find . -size +1k -size -1M    # entre 1 KiB y 1 MiB

# Por DUEÑO y PERMISOS (nivel típico de Bandit):
find / -user bandit7 -group bandit6 -size 33c 2>/dev/null
find / -type f -perm -u=s 2>/dev/null     # archivos con SETUID (-perm -u=s)
```

- **`-size`**: `c` = bytes, `k` = KiB, `M` = MiB. **Sin la `c` cuenta en bloques
  de 512 bytes** y no encuentras nada. Es el error más común.
- **`2>/dev/null`**: tira los errores de "permiso denegado" para que solo veas
  los resultados buenos. Imprescindible al buscar en `/`.
- **`-exec ... {} +`**: ejecuta un comando sobre cada resultado. `{}` es el
  archivo encontrado.
- Para ejecutar un binario SETUID que encontraste: `/ruta/al/binario`.

## 5. `grep` — buscar texto DENTRO de archivos

```bash
grep "palabra" archivo        # líneas que contienen "palabra"
grep -i flag archivo          # -i = sin distinguir mayúsculas
grep -r flag .                # -r = recursivo, busca en toda la carpeta
grep -v basura archivo        # -v = al revés: líneas que NO la tienen
grep millionth data.txt       # nivel típico: la línea con una palabra clave
```

- En Bandit hay un nivel donde la contraseña está en **la única línea** que
  contiene cierta palabra: `grep palabra archivo`.

## 6. `sort` y `uniq` — ordenar y contar repetidos

Van casi siempre juntos. **`uniq` solo junta repetidos que están PEGADOS**, así
que primero `sort`.

```bash
sort archivo                  # ordena las líneas alfabéticamente
sort -n archivo               # orden numérico (no "10" antes que "2")
sort -u archivo               # ordena Y quita duplicados

uniq archivo                  # colapsa líneas repetidas CONSECUTIVAS
sort archivo | uniq           # lo correcto: ordenar y luego quitar repetidos
sort archivo | uniq -c        # -c = cuenta cuántas veces sale cada línea
sort archivo | uniq -u        # -u = solo las que aparecen UNA vez (¡la flag!)
sort archivo | uniq -d        # -d = solo las que SÍ se repiten
```

- Nivel típico: "la contraseña es la única línea que aparece una sola vez" →
  `sort data.txt | uniq -u`.
- Nivel típico: "la línea que se repite N veces" → `sort data.txt | uniq -c`.

## 7. `strings` — texto legible dentro de un binario

```bash
strings archivo               # saca las cadenas de texto de un binario
strings -n 8 archivo          # solo cadenas de 8+ caracteres (menos ruido)
strings data.txt | grep -i password   # busca la pista entre el ruido
```

- Cuando `file` dice que es "data" o binario pero sabes que esconde texto.

## 8. Decodificar y transformar texto

```bash
# base64 (texto tipo "cGFzc3dvcmQ=")
base64 -d archivo             # -d = decodificar
cat archivo | base64 -d

# hex / volcado byte a byte
xxd archivo                   # muestra el archivo en hexadecimal
xxd -r -p archivo             # -r -p = de hex de vuelta a binario

# ROT13 y similares con tr (traduce/rota caracteres)
cat archivo | tr 'A-Za-z' 'N-ZA-Mn-za-m'   # ROT13
cat archivo | tr 'a-z' 'A-Z'               # a mayúsculas
```

- Bandit tiene un nivel ROT13 y otro base64: reconoce el patrón y aplica el de
  arriba.

## 9. Descomprimir (el nivel de las capas)

Un nivel te da un archivo comprimido muchas veces. `file` te dice de qué tipo es
cada capa; descomprimes, vuelves a hacer `file`, y repites.

```bash
file data                     # ¿qué tipo es esta capa?

# según lo que diga file:
gzip -d archivo.gz            # gzip        (o: zcat archivo.gz)
bzip2 -d archivo.bz2          # bzip2
tar xf archivo.tar            # tar (desempaqueta)
tar xzf archivo.tar.gz        # tar + gzip
mv data data.gz               # si no tiene la extensión, pónsela antes
```

- Bucle: `file` → descomprimir según el tipo → `file` otra vez → hasta que salga
  "ASCII text". Esa es la flag.

## 10. Conectarte a servicios (red)

```bash
# SSH a otra máquina/puerto (así entras a cada nivel de Bandit)
ssh bandit0@bandit.labs.overthewire.org -p 2220
ssh usuario@host -p PUERTO -i clave_privada   # -i = con llave en vez de pass

# nc / ncat / telnet: hablar con un puerto a mano
nc localhost 30000            # te conecta; escribes y lees respuestas
ncat --ssl host 30001         # --ssl: el puerto usa cifrado
openssl s_client -connect host:30001   # igual, conexión cifrada manual
```

- Varios niveles piden **mandar la contraseña actual a un puerto** y te devuelve
  la siguiente. Si el puerto es cifrado, usa `ncat --ssl` u `openssl s_client`.
- `scp` copia archivos por SSH (útil para bajarte una llave privada):
  `scp -P 2220 usuario@host:/ruta/archivo .`

## 11. Comparar y recortar

```bash
diff archivo1 archivo2        # muestra en qué se diferencian dos archivos
cut -d: -f1 archivo           # corta columnas; -d= separador, -f= campo nº
cut -c1-32 archivo            # corta por caracteres (los primeros 32)
md5sum archivo                # huella del archivo (para comparar)
```

- Nivel típico: "la contraseña está en el archivo que se diferencia del resto" →
  `diff`.

## 12. Permisos y llaves SSH

```bash
chmod 600 clave               # una llave privada debe ser SOLO tuya...
chmod 700 carpeta             # ...o SSH la rechaza ("permissions too open")
ssh usuario@host -i clave -p 2220
```

- Si al usar una llave privada SSH se queja de permisos, `chmod 600` a la llave.

## 13. Reflejos para Bandit (resumen)

| Pista en el enunciado | Comando |
|---|---|
| "archivo oculto" | `ls -a`, `cat ./.oculto` |
| "nombre raro / con guion / espacios" | `cat ./-file`, `cat "con espacios"` |
| "humano / legible" (human-readable) | `file`, `cat`, `strings` |
| "de 1033 bytes, no ejecutable, legible" | `find . -size 1033c ! -executable` |
| "propiedad del usuario X" | `find / -user X 2>/dev/null` |
| "la única línea que no se repite" | `sort f \| uniq -u` |
| "la línea que se repite" | `sort f \| uniq -d` (o `-c`) |
| "texto codificado tipo ==" | `base64 -d` |
| "letras corridas 13 posiciones" | `tr` (ROT13) |
| "comprimido muchas veces" | `file` → descomprimir → repetir |
| "manda la contraseña a un puerto" | `nc host puerto` / `ncat --ssl` |
