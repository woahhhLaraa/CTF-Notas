# Dejar Kali listo para CYBERFEI 3.0 (offline)

Evento: **21 oct 2026 · Salón Cristal · 3.5 h · SIN internet.**
Haz TODO esto HOY, con red. Mañana no se instala ni se descarga nada.
Orden: instala → descarga offline → verifica sin red → snapshot.

---

## 0. Actualiza Kali
```bash
sudo apt update && sudo apt -y full-upgrade
```

## 1. Instala lo que pueda faltar
Kali trae casi todo, pero asegura estos (los usamos en la guía):
```bash
sudo apt -y install \
  nmap wireshark tshark tcpdump netcat-openbsd socat \
  ffuf gobuster feroxbuster whatweb hydra wpscan exploitdb \
  binwalk foremost exiftool steghide stegseek zsteg pngcheck zbar-tools sleuthkit \
  gdb radare2 ltrace strace ghidra \
  john hashcat hashid \
  python3-pip pipx jq imagemagick poppler-utils qpdf audacity \
  metasploit-framework seclists
```
> Si uno no existe con ese nombre: `apt search <palabra>`. `zsteg` a veces va por gem: `sudo gem install zsteg`.

## 2. Librerías de Python (por apt — Kali bloquea pip por PEP 668)
```bash
sudo apt -y install python3-pwntools python3-pycryptodome python3-sympy python3-requests python3-pil
```
> `pip install` da error `externally-managed-environment` en Kali. Instala por apt (arriba). Si una librería no existe por apt, solo para esa: `pip install --user --break-system-packages NOMBRE`.

**Volatility 3** (forense de memoria) no viene por apt; instálalo con pipx (aislado, sin romper PEP 668):
```bash
pipx install volatility3
pipx ensurepath   # añade ~/.local/bin al PATH; abre una terminal nueva después
```
> Esto deja el comando `vol` disponible. La verificación del paso 7 corre `vol -h`; si no instalas esto, ese comando falla.

## 3. Wordlists
```bash
# rockyou viene comprimido en Kali: descomprímelo
sudo gunzip -k /usr/share/wordlists/rockyou.txt.gz
```
```bash
# confirma que están rockyou y SecLists
ls /usr/share/wordlists/ ; ls /usr/share/seclists/
```

## 4. Bases de datos de exploits (que funcionen offline)
```bash
# ExploitDB local -> searchsploit sin internet
searchsploit -u
```
```bash
# wpscan: descarga su base de vulnerabilidades (si tocarás WordPress)
wpscan --update
```
```bash
# Metasploit: inicia la base de datos (una vez)
sudo msfdb init
```

## 5. Documentación offline (clónala hoy)
```bash
mkdir -p ~/tools && cd ~/tools
git clone --depth 1 https://github.com/carlospolop/hacktricks
git clone --depth 1 https://github.com/swisskyrepo/PayloadsAllTheThings
git clone --depth 1 https://github.com/GTFOBins/GTFOBins.github.io
git clone --depth 1 https://github.com/gchq/CyberChef
```
- **CyberChef offline:** abre `~/tools/CyberChef/CyberChef_vXX.html` en el navegador; funciona sin red (operación *Magic* para decodificar).
- **StegSolve** (para estego visual): descarga el `.jar` y guárdalo en `~/tools`.
- **Ghidra** ya viene en Kali (`ghidra`).

## 6. Copia el kit a la VM
El kit vive en la carpeta `kit/` de este repo (scripts de **estudio**, no para el evento). Desde donde tengas el repo:
```bash
cp -r kit ~/CTF-Kit && chmod +x ~/CTF-Kit/scripts/*.py
```

---

## 7. ⚠️ Verificación OFFLINE (lo que casi nadie hace)
**Desconecta el wifi** y comprueba que todo abre sin red:
```bash
nmap --version && sqlmap --version && gdb --version && hashcat --version && vol -h | head -1
```
```bash
python3 -c "import pwn, Crypto, sympy; print('pwntools+cripto OK')"
```
```bash
searchsploit apache 2.4.49
```
- Abre **CyberChef** desde el HTML local en el navegador → decodifica un base64 de prueba.
- Abre **Wireshark** y **Ghidra** (que arranquen).
- Resuelve 1–2 retos fáciles de picoGym por categoría **sin internet** para confirmar que sabes usar cada herramienta.

## 8. Snapshot
Con todo funcionando offline, toma un **snapshot** de la VM. Si mañana algo se rompe, vuelves al estado bueno en segundos.

---

## Checklist final (marca antes de dormir)
- [ ] Kali actualizado y herramientas instaladas
- [ ] rockyou descomprimido + SecLists presente
- [ ] `searchsploit -u`, `wpscan --update`, `msfdb init` hechos
- [ ] HackTricks, PayloadsAllTheThings, GTFOBins y CyberChef clonados
- [ ] Verificado TODO con el wifi apagado
- [ ] Kit copiado a `~/CTF-Kit`
- [ ] **Snapshot** tomado
- [ ] Sé el formato de la flag: `flag{...}` / `CyberFEI{...}`
- [ ] Recuerdo la regla: comandos propios, no scripts de terceros ni IA

## Zona gris — pregunta a los organizadores antes de usar
`sqlmap`, `wpscan`, `hydra`, `nikto`/`nuclei`, Metasploit. Si dudan, hazlo manual y documéntalo.
