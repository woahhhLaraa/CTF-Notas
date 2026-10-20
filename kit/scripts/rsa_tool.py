#!/usr/bin/env python3
"""rsa_tool.py — ayudas de RSA para estudiar en casa.

⚠️ Regla 3 de CyberFEI: para el evento, haz el razonamiento TÚ y documenta
cada paso en el writeup. Esto es para entender los casos típicos de RSA de
CTF, no para resolver el reto de forma automática el día del evento.

Casos cubiertos (los más comunes en retos fáciles/medios):
  - Tienes p, q, e, c  -> descifra.
  - Tienes n pequeño   -> intenta factorizar por fuerza simple.
  - e = 3 y mensaje chico -> raíz cúbica entera (sin padding).

Uso:
    python3 rsa_tool.py --p 61 --q 53 --e 17 --c 2790
    python3 rsa_tool.py --n 3233 --e 17 --c 2790
    python3 rsa_tool.py --e 3 --c 123456789 --cuberoot
"""
import argparse
from math import isqrt


def inverso_mod(a: int, m: int) -> int:
    """Inverso modular por Euclides extendido."""
    g, x, _ = _egcd(a, m)
    if g != 1:
        raise ValueError("no existe inverso modular (a y m no son coprimos)")
    return x % m


def _egcd(a: int, b: int):
    if b == 0:
        return a, 1, 0
    g, x, y = _egcd(b, a % b)
    return g, y, x - (a // b) * y


def factoriza_simple(n: int):
    """Busca un factor por división de prueba hasta sqrt(n). Solo n chico."""
    for p in range(2, isqrt(n) + 1):
        if n % p == 0:
            return p, n // p
    return None


def raiz_cubica_entera(c: int):
    """Raíz cúbica entera exacta de c, o None si no es cubo perfecto."""
    lo, hi = 0, 1 << ((c.bit_length() // 3) + 2)
    while lo <= hi:
        mid = (lo + hi) // 2
        cubo = mid ** 3
        if cubo == c:
            return mid
        if cubo < c:
            lo = mid + 1
        else:
            hi = mid - 1
    return None


def descifra(p: int, q: int, e: int, c: int) -> int:
    n = p * q
    phi = (p - 1) * (q - 1)
    d = inverso_mod(e, phi)
    return pow(c, d, n)


def a_texto(m: int) -> str:
    """Pasa un entero a bytes legibles si se puede."""
    try:
        bs = m.to_bytes((m.bit_length() + 7) // 8, "big")
        return bs.decode("utf-8", "replace")
    except (ValueError, OverflowError):
        return "<no decodificable como texto>"


def main() -> int:
    ap = argparse.ArgumentParser(description="Ayudas de RSA para estudiar.")
    ap.add_argument("--p", type=int)
    ap.add_argument("--q", type=int)
    ap.add_argument("--n", type=int)
    ap.add_argument("--e", type=int, default=65537)
    ap.add_argument("--c", type=int, required=True)
    ap.add_argument("--cuberoot", action="store_true",
                    help="asume e chico y saca raíz e-ésima (sin padding)")
    args = ap.parse_args()

    if args.cuberoot:
        r = raiz_cubica_entera(args.c)
        if r is None:
            print("c no es cubo perfecto; el mensaje quizá tenía padding o e!=3.")
            return 1
        print(f"m = {r}")
        print(f"texto = {a_texto(r)!r}")
        return 0

    p, q = args.p, args.q
    if (p is None or q is None) and args.n is not None:
        res = factoriza_simple(args.n)
        if res is None:
            print("no pude factorizar n por división de prueba (demasiado grande).")
            return 1
        p, q = res
        print(f"factorizado: p={p} q={q}")

    if p is None or q is None:
        ap.error("da --p y --q, o --n para factorizar, o usa --cuberoot")

    m = descifra(p, q, args.e, args.c)
    print(f"m = {m}")
    print(f"texto = {a_texto(m)!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
