#!/usr/bin/env python3
"""decode.py — decodificador rápido para estudiar en casa.

⚠️ Regla 3 de CyberFEI: en el evento escribe TÚ los comandos. Este script
es solo para PRACTICAR y entender las transformaciones; no lo pegues en el
writeup como si fuera trabajo propio del día.

Prueba varias decodificaciones comunes sobre un texto y muestra las que
producen algo legible (letras/números/signos imprimibles).

Uso:
    python3 decode.py "V0VsY29tZQ=="
    echo "48 65 6c 6c 6f" | python3 decode.py
"""
import base64
import binascii
import codecs
import string
import sys


LEGIBLE = set(string.printable) - {"\x0b", "\x0c"}


def es_legible(s: str, umbral: float = 0.85) -> bool:
    """True si la mayoría de los caracteres son imprimibles."""
    if not s:
        return False
    buenos = sum(1 for c in s if c in LEGIBLE)
    return buenos / len(s) >= umbral


def intentos(dato: str):
    """Genera pares (nombre, resultado) de cada decodificación que funcione."""
    bruto = dato.strip()

    # base64 (con relleno tolerante)
    try:
        pad = bruto + "=" * (-len(bruto) % 4)
        yield "base64", base64.b64decode(pad).decode("utf-8", "replace")
    except (binascii.Error, ValueError):
        pass

    # base32
    try:
        pad = bruto.upper() + "=" * (-len(bruto) % 8)
        yield "base32", base64.b32decode(pad).decode("utf-8", "replace")
    except (binascii.Error, ValueError):
        pass

    # hex (con o sin espacios)
    try:
        limpio = bruto.replace(" ", "").replace("0x", "")
        yield "hex", bytes.fromhex(limpio).decode("utf-8", "replace")
    except ValueError:
        pass

    # ROT13
    yield "rot13", codecs.encode(bruto, "rot_13")

    # César: las 25 rotaciones
    for n in range(1, 26):
        corrido = "".join(
            chr((ord(c) - base + n) % 26 + base)
            if c.isalpha() else c
            for c, base in ((c, ord("A") if c.isupper() else ord("a")) for c in bruto)
        )
        yield f"cesar+{n}", corrido


def main() -> int:
    if len(sys.argv) > 1:
        dato = " ".join(sys.argv[1:])
    else:
        dato = sys.stdin.read()

    for nombre, salida in intentos(dato):
        if es_legible(salida):
            print(f"[{nombre:>8}] {salida!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
