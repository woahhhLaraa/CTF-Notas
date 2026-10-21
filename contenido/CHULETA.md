# Chuleta de 1 página (imprimible)

> Para usar bajo cronómetro, no para leer. Un vistazo → qué hacer. Lo demás
> está en Comandos y Guía explicada. **Formato de flag:** `flag{...}` /
> `CyberFEI{...}`.

## Primero, SIEMPRE (reflejo universal)
```bash
grabar <reto>                 # graba la sesión -> <reto>.txt limpio (writeup = 40 pts)
strings -n 6 ARCHIVO | grep -iE 'flag|cyberfei|ctf'
```

## Qué te dan → primer reflejo

| Te dan… | Haz esto primero |
|---|---|
| Archivo cualquiera | `file` → `strings -n6` → `exiftool` → `binwalk -e` |
| Imagen | `zsteg -a` (PNG) / `steghide extract` / `stegseek img rockyou` + Stegsolve |
| Audio | espectrograma (Audacity / Sonic Visualiser) |
| Texto raro | CyberChef **Magic**; ¿base64? ¿hex? ¿rot? |
| `.pcap` | Wireshark → Follow TCP Stream → Export Objects |
| URL / web | ver fuente, DevTools, `robots.txt`, `curl -I`, `feroxbuster` |
| Puerto / servicio | `nmap -sC -sV -p- OBJETIVO` |
| Binario ELF | `file` → `checksec` → `strings` → Ghidra |
| Dump de RAM | `vol -f dump.mem windows.info` → `pslist` / `cmdline` |
| Disco / imagen | `foremost -i disco.img -o salida/` / Sleuth Kit |
| Hash | `hashid 'HASH'` → `hashcat -m MODO` / `john` + rockyou |
| Login | manual primero; `hydra` solo si lo permiten (zona gris) |

## Web — detección manual (100 % estilo)
- SQLi: añade `'` → ¿error? · SSTI: `{{7*7}}` → ¿`49`? · LFI: `?file=../../../../etc/passwd`
- JWT `eyJ...`: decodifica las 3 partes en CyberChef · Cmd injection: `; id` / `| id`

## Comodín final (busca la flag en todo)
```bash
grep -raoiE '[A-Za-z0-9_]+\{[^}]+\}' .
```

## Reglas del día (no las olvides)
- **Sin internet** · solo la infra del reto · formato de flag en cada `grep`.
- **20 min** atorado → pide ayuda o cambia de reto · fácil primero por puntaje.
- **Zona gris** (`sqlmap`, `wpscan`, `hydra`, `nikto`/`nuclei`, Metasploit): pregunta;
  si dudas, hazlo **manual** y documéntalo.
- **Últimos 30 min:** congela exploración, pule writeups.
