# Writeup — plantilla y reflejos

> El writeup vale **40 pts** y el estilo otro **40**: juntos son el **70 %** de
> la rúbrica, más que la bandera (30). Esta es la parte con mayor ROI y la más
> fácil de dejar lista de antemano. Copia el esqueleto por cada reto.

## Reflejo cero: graba la sesión
Antes de tocar el reto, en la terminal:
```bash
grabar <reto>
```
Graba **todos** los comandos y salidas. Escribe `exit` (o Ctrl-D) para cerrar.
Deja `<reto>.txt` ya limpio de colores (y `<reto>.raw` con los colores, por si
acaso). Así el writeup se escribe casi solo: copias de `<reto>.txt` el comando y
la salida exactos.

> Nota: NO uses `script -t sesion.log`. En esta versión de `script` esa opción
> manda los tiempos a la pantalla y el log sale ilegible. Usa `grabar`.

## Esqueleto (uno por reto)

```markdown
# <Nombre del reto>  ·  <Categoría>  ·  <Puntos>

## Reconocimiento
- Qué me dieron (archivo, URL, puerto, hash...).
- Primer vistazo: `file`, `strings`, `nmap`, lo que aplique + salida clave.

## Hipótesis
- Qué creo que es y por qué (una o dos frases).

## Pasos
1. Comando ejecutado
   ```
   <comando + salida relevante, pegada de sesion.log>
   ```
   Qué me dijo este paso y qué decidí hacer después.
2. ...

## Flag
`flag{...}` / `CyberFEI{...}`

## Notas
- Qué me atoró y cómo salí (suma estilo).
- Herramienta manual usada en vez de automática (suma estilo).
```

## Reglas para que puntúe el estilo (40 pts)
- **Comando + salida reales**, pegados de `sesion.log`, no reescritos de memoria.
- Explica el **porqué** de cada paso, no solo el qué.
- Inyección/explotación **a mano** > herramienta automática: pega el request
  exacto y la respuesta con la flag.
- Si una salida no la entendiste, **documéntala igual**: a veces la flag está
  ahí y la ves al releer.
- Código propio = 100 % de estilo. Snippet de terceros = 50 %. Sospecha de IA =
  descalificación.

## Al cerrar cada reto
- Último 30 min del evento: **congela exploración y pule writeups**.
- Revisa que cada reto resuelto tenga su flag, sus pasos y su `sesion.log`.
