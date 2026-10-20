# CTF-Kit — scripts de estudio

⚠️ **Solo para practicar en casa.** Regla 3 de CyberFEI 3.0: el código propio
puntúa 100 % de estilo, un snippet de terceros 50 %, y la sospecha de IA
descalifica. **No pegues estos scripts en el writeup como trabajo del día.**
Úsalos para *entender* cada transformación; en el evento escribe tú los
comandos.

- `scripts/decode.py` — prueba base64/base32/hex/rot/César y muestra lo legible.
- `scripts/rsa_tool.py` — RSA típico de CTF: p·q·e·c, factorizar n chico, raíz e-ésima.
- `scripts/pwn_template.py` — esqueleto de pwntools (local/remoto) para desbordamientos.

## Copiar a la VM (como dice la preparación offline)

```bash
cp -r kit ~/CTF-Kit && chmod +x ~/CTF-Kit/scripts/*.py
```

Todos corren con Python 3. `pwn_template.py` necesita `python3-pwntools`
(instalado en el paso 2 de la preparación offline).
