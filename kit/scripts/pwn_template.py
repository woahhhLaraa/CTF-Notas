#!/usr/bin/env python3
"""pwn_template.py — esqueleto de pwntools para estudiar en casa.

⚠️ Regla 3 de CyberFEI: en el evento, escribe tu propio exploit y explica
cada decisión en el writeup. Esta plantilla es para PRACTICAR el flujo
local/remoto de pwntools, no para pegarla tal cual el día del reto.

Edita BINARIO, HOST y PORT. Corre:
    python3 pwn_template.py         # local
    python3 pwn_template.py REMOTE  # contra HOST:PORT
"""
import sys

try:
    from pwn import ELF, context, process, remote
except ImportError:
    sys.exit("Falta pwntools. En Kali: sudo apt -y install python3-pwntools")

BINARIO = "./reto"
HOST = "127.0.0.1"
PORT = 1337

context.update(arch="amd64", os="linux", log_level="info")


def conecta():
    """Abre el proceso local o la conexión remota según el argumento."""
    if len(sys.argv) > 1 and sys.argv[1].upper() == "REMOTE":
        return remote(HOST, PORT)
    return process(BINARIO)


def main() -> int:
    elf = ELF(BINARIO, checksec=True)  # imprime protecciones (NX, PIE, canary)
    io = conecta()

    # --- plantilla de desbordamiento de buffer ---
    offset = 40                    # distancia real: pattern_create / cyclic
    ret = b"\x90" * 0              # dirección de retorno en little-endian
    payload = b"A" * offset + ret

    io.sendline(payload)

    # Pistas útiles del binario (si existen):
    if "win" in elf.symbols:
        print(f"[i] symbol 'win' en {hex(elf.symbols['win'])}")

    io.interactive()               # te deja la shell / la salida del reto
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
