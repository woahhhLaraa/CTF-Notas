# Preparación para CTF offline (VM Kali)

Como el evento es **sin internet**, hay que descargar TODO antes. Haz esto desde la VM de Kali **con red**, días antes.

## 1. Actualiza e instala herramientas
```bash
sudo apt update && sudo apt -y full-upgrade

sudo apt -y install \
  nmap gobuster ffuf whatweb sqlmap hydra \
  binwalk foremost exiftool steghide zsteg pngcheck \
  tshark tcpflow \
  gdb radare2 ghidra \
  john hashcat hashid \
  python3-pip net-tools netcat-openbsd

# pip (quedan cacheados en la VM)
pip install --user pwntools sympy pycryptodome requests
```
> `zsteg` a veces va por gem: `sudo gem install zsteg`.
> Burp Suite Community y Wireshark ya vienen en Kali.

## 2. Diccionarios
```bash
# rockyou viene comprimido en Kali
sudo gunzip -k /usr/share/wordlists/rockyou.txt.gz
ls /usr/share/wordlists/      # dirb, dirbuster, seclists...
sudo apt -y install seclists  # colección grande de wordlists
```

## 3. Repos que conviene clonar (funcionan offline)
```bash
mkdir -p ~/tools && cd ~/tools
git clone https://github.com/Ganapati/RsaCtfTool
git clone https://github.com/gchq/CyberChef      # abre CyberChef_vX.html en el navegador, offline
git clone https://github.com/pwndbg/pwndbg && cd pwndbg && ./setup.sh && cd ..
git clone https://github.com/RsaCtfTool/RsaCtfTool 2>/dev/null
# ROPgadget / ropper
pip install --user ROPgadget ropper
```
- **StegSolve** (jar): descarga el `.jar` y guárdalo en `~/tools`.
- **Ghidra** ya viene; si no, descarga el zip oficial.

## 3b. Descargas que piden red HOY (evento offline mañana)
```bash
# ExploitDB local -> habilita searchsploit sin internet
sudo apt -y install exploitdb && searchsploit -u   # -u actualiza la base

# wpscan + su base de vulnerabilidades (si vas a tocar WordPress)
sudo apt -y install wpscan && wpscan --update

# Docs y payloads que funcionan offline (clónalos)
git clone --depth 1 https://github.com/danielmiessler/SecLists ~/tools/SecLists
git clone --depth 1 https://github.com/swisskyrepo/PayloadsAllTheThings ~/tools/PayloadsAllTheThings
git clone --depth 1 https://github.com/carlospolop/hacktricks ~/tools/hacktricks
# GTFOBins: clona el repo o guarda el sitio para consultar abusos de binarios SUID
git clone --depth 1 https://github.com/GTFOBins/GTFOBins.github.io ~/tools/GTFOBins
```
> Recuerda la **regla 5**: `wpscan`/`sqlmap` son zona gris; `searchsploit` es solo consulta local (ok). Confirma con los organizadores antes de usar los automáticos.

## 4. Verifica que todo corre SIN red
Antes del evento, desconecta la red de la VM y comprueba:
```bash
nmap --version && sqlmap --version && gdb --version
python3 -c "import pwn, Crypto, sympy; print('pwntools+cripto OK')"
python3 ~/Documents/CTF-Kit/scripts/decode.py "aGVsbG8="   # debe mostrar 'hello'
```

## 5. Copia este kit a la VM de Kali
Desde la VM, por carpeta compartida o USB:
```bash
cp -r /ruta/al/CTF-Kit ~/CTF-Kit
chmod +x ~/CTF-Kit/scripts/*.sh ~/CTF-Kit/scripts/*.py
```

## 6. Snapshot
Cuando todo funcione offline, toma un **snapshot** de la VM. Si algo se rompe durante el evento, vuelves al estado bueno en segundos.

---

## Checklist del día
- [ ] VM arranca y herramientas corren sin red
- [ ] Conozco el **formato de la flag**
- [ ] Carpeta por reto, con su `PLANTILLA-writeup.md`
- [ ] Empiezo por los retos de menos puntos
- [ ] Anoto cada intento (sirve para el write-up)
- [ ] No ataco la plataforma ni a otros equipos (salvo Attack-Defense)
- [ ] Si me atoro 30–45 min, cambio de reto y regreso
