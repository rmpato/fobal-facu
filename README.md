# Fobal Facu

Simulador de partidos para un juego de cartas de fútbol (familia). Corre miles de partidos en segundos para comparar reglamentos y ver si el juego cierra, estanca o se desbalancea.

**Requisito:** Python 3.11+ (solo biblioteca estándar).

---

## Empezar en 2 minutos

```bash
git clone https://github.com/rmpato/fobal-facu.git
cd fobal-facu

# Ver reglamentos disponibles
python3 -m simulador reglamentos list

# Correr 200 partidos con el reglamento actual (v1)
python3 -m simulador run --reglamento v1 --partidos 200

# Comparar v1 y v2 en 3v3 y 4v4
python3 -m simulador compare-formatos --partidos 200 --ia estrategica

# Comparar v1 vs v2 en un solo formato (default 3v3)
python3 -m simulador compare-reglamentos --partidos 200
```

Cada corrida imprime métricas y **qué reglas aplicó** ese reglamento. Para entender los comandos y el flujo completo → [`docs/guia-rapida.md`](docs/guia-rapida.md).

---

## Ver un partido en la terminal

El modo espectador muestra el partido jugada por jugada, con la mano de cada
jugador, las últimas cartas y el marcador arriba. Es la forma más rápida de
entender qué hace una regla nueva.

```bash
# Un partido con el reglamento que se está probando
python3 -m simulador ver --reglamento v2 --equipo1 Facu Pato Manu --equipo2 Colo Ostu Joaco
```

**Para que se vea lindo**, conviene instalar dos bibliotecas opcionales. Sin
ellas funciona igual, pero con paneles más básicos:

```bash
pip install rich textual
```

Este repositorio ya trae un entorno con las dos instaladas, así que también sirve:

```bash
.venv/bin/python -m simulador ver --reglamento v2 --equipo1 Facu Pato Manu --equipo2 Colo Ostu Joaco
```

### Mientras corre

| Tecla | Qué hace |
|-------|----------|
| **Espacio** | avanzar ya a la próxima jugada |
| **+** / **−** | acelerar o frenar el relato |
| **P** | pausa automática sí / no |
| **Q** | salir del partido |

### Opciones que valen la pena

```bash
# Repetir exactamente el mismo partido (el de la página web)
python3 -m simulador ver --reglamento v2 --semilla 138 --equipo1 Facu Pato Manu --equipo2 Colo Ostu Joaco

# Elegir la interfaz: textual (la más completa), rich, curses o simple
python3 -m simulador ver --reglamento v2 --ui textual

# Ritmo del relato y segundos entre jugadas
python3 -m simulador ver --reglamento v2 --velocidad rapido --pausa 2

# Enfrentar dos estilos de juego distintos
python3 -m simulador ver --reglamento v2 --ia-equipo0 agresiva --ia-equipo1 conservador

# Guardar el partido y generar una página para volver a verlo
python3 -m simulador ver --reglamento v2 --semilla 138 --grabar partido.json --exportar-html
```

Todas las opciones: `python3 -m simulador ver --help`. Necesita una terminal de
verdad: si la salida se manda a un archivo, cae al modo simple y no responde al
teclado.

---

## Reglamentos implementados

Estos son los que el simulador puede correr hoy (`reglamentos/indice.json`):

| Id | Nombre | Qué cambia respecto al anterior | Reglas en mesa | Motor |
|----|--------|-----------------------------------|----------------|-------|
| **`v0`** | Reglamento original | — *(histórico, no en simulación batch)* | [reglamento-v0.md](docs/reglamento-v0.md) | [v0.json](reglamentos/v0.json) |
| **`v1`** | Iteración 1 (playtesting) | Robo unificado, Reventar, rebote/palo, reposición al cambio de equipo | [reglamento-v1.md](docs/reglamento-v1.md) | [v1.json](reglamentos/v1.json) |
| **`v1.1`** | Pasa al compañero | *(histórico, no en simulación batch)* | [reglamento-v1.1.md](docs/reglamento-v1.1.md) | [v1.1.json](reglamentos/v1.1.json) |
| **`v2`** | Iteración 2 (playtesting) | Sin pasa de turno; trampa/marca al pase; reacciones encadenables | [reglamento-v2.md](docs/reglamento-v2.md) | [v2.json](reglamentos/v2.json) |

```bash
python3 -m simulador run --reglamento v1 --partidos 200   # default actual
python3 -m simulador reglamentos show v1.1                # detalle de reglas aplicadas
```

Para crear uno nuevo: copiá [`reglamentos/_plantilla.json`](reglamentos/_plantilla.json) → [`docs/reglamentos-guia.md`](docs/reglamentos-guia.md).

---

## Conclusiones (sin correr nada)

| Querés saber… | Leé |
|---------------|-----|
| **v1 vs v2 · 3v3 y 4v4** | [`docs/comparacion-v1-v2-formatos.md`](docs/comparacion-v1-v2-formatos.md) |
| **Qué encontramos** (histórico) | [`docs/resultados-iniciales.md`](docs/resultados-iniciales.md) |
| **Qué probar next** (mazo, cartas, reglas trabadas) | [`docs/recomendaciones-diseno.md`](docs/recomendaciones-diseno.md) |
| **Reglas para jugar en mesa** | [`docs/reglamento-v1.md`](docs/reglamento-v1.md) (actual) · [`docs/reglamento-v0.md`](docs/reglamento-v0.md) (original) |

**Resumen en una frase:** simulaciones activas **v1 vs v2** en **3v3 y 4v4** — v2 gana ritmo en 3v3; en 4v4 Trampa/Marca escalan fuerte. Informe → [`docs/comparacion-v1-v2-formatos.md`](docs/comparacion-v1-v2-formatos.md).

---

## Cómo funciona (idea general)

```
Reglamento (JSON + MD)  →  Simulador  →  Métricas  →  Comparar versiones
```

- **Entrada:** un reglamento (`v1`, `v1.1`, …) definido en [`reglamentos/`](reglamentos/).
- **Salida:** goles, turnos, % de acciones (pase, robo, despeje…), penales, cartas jugadas.
- **Código:** carpeta [`simulador/`](simulador/) — detalle en [`docs/como-funciona-simulacion.md`](docs/como-funciona-simulacion.md).

---

## Mapa de documentación

Índice completo → [`docs/README.md`](docs/README.md).

| Documento | Para qué |
|-----------|----------|
| [`docs/guia-rapida.md`](docs/guia-rapida.md) | Comandos, reglamentos, variantes |
| [`docs/perfiles-ia.md`](docs/perfiles-ia.md) | Perfiles de IA (clásicos y nuevos), `--ia`, espectador |
| [`docs/resultados-iniciales.md`](docs/resultados-iniciales.md) | Hallazgos de simulación |
| [`docs/recomendaciones-diseno.md`](docs/recomendaciones-diseno.md) | Análisis y próximos experimentos |
| [`docs/como-funciona-simulacion.md`](docs/como-funciona-simulacion.md) | Motor, turnos, IA, limitaciones |
| [`docs/reglamentos-guia.md`](docs/reglamentos-guia.md) | Crear reglamento v1.2 / v2 |
| [`docs/ambiguedades.md`](docs/ambiguedades.md) | Reglas no cerradas y supuestos del motor |

---

## Estructura del repo

```
reglamentos/     Reglas que el motor aplica (JSON)
simulador/       Motor Python + CLI
configs/         Variantes de simulación (JSON)
docs/            Reglamentos humanos, resultados, guías
```

---

## Sitio web

**[rmpato.github.io/fobal-facu](https://rmpato.github.io/fobal-facu/)** — el juego
contado para alguien que no lo conoce: el mazo, la tabla del dado para probar
tirando, un partido que se reproduce solo y los números de las simulaciones. Las
reglas completas para jugar están en
[reglas.html](https://rmpato.github.io/fobal-facu/reglas.html).

Sale de la carpeta [`docs/`](docs/) de esta rama. No hace falta para correr
simulaciones. Cómo se publica y cómo se actualiza el partido de ejemplo:
[`docs/GITHUB_PAGES.md`](docs/GITHUB_PAGES.md).

---

## Licencia

Uso privado / familiar — a definir.
