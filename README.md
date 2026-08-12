# Fobal Facu

Simulador de partidos para un juego de cartas de fútbol (familia). Corre miles de partidos en segundos para comparar reglamentos y ver si el juego cierra, estanca o se desbalancea.

**Requisito:** Python 3.11 o más nuevo. Nada más.

---

## Instalación

Los scripts revisan que Python esté, preparan un entorno propio en la carpeta
`.venv` y dejan todo listo. No tocan nada del sistema.

### macOS y Linux

En la Terminal (funciona igual en zsh, bash o sh):

```sh
git clone https://github.com/rmpato/fobal-facu.git
cd fobal-facu
./instalar.sh --web
```

### Windows

En PowerShell o en el Símbolo del sistema:

```bat
git clone https://github.com/rmpato/fobal-facu.git
cd fobal-facu
.\instalar.bat --web
```

Con `--web` abre la interfaz al terminar; con `--ver` muestra un partido en la
terminal; sin nada, deja todo instalado y explica cómo seguir.

Si no tenés `git`, el repositorio se puede bajar como ZIP desde el botón verde
**Code** de GitHub.

---

## La interfaz

```sh
.venv/bin/python -m simulador web            # macOS y Linux
.venv\Scripts\python -m simulador web        # Windows
```

Abre `http://localhost:8000` con tres pasos, pensados para no tocar la terminal:

| Pantalla | Para qué |
|---|---|
| **1 · Equipos** | Los nombres de los dos equipos y de sus jugadores. Se guardan en `configs/equipos.json`. |
| **2 · Reglas** | Editar el mazo carta por carta, cuántos goles hacen falta, qué puede hacer el ataque y con qué responde la defensa. Se puede crear un reglamento nuevo, duplicar uno existente o borrarlo. Avisa en el momento si algo no cierra. |
| **3 · Simular** | Correr cientos de partidos de una o varias versiones y comparar los resultados con gráficos. Abajo, un partido completo jugada por jugada, con **la mano del que tiene la pelota** y cuántas cartas le quedan a cada uno. |

Lo que se guarda desde la interfaz son los mismos archivos que lee la línea de
comandos: un reglamento creado ahí se puede simular después con `run` o
`compare-formatos`.

---

## Desde la terminal

```bash
# Ver reglamentos disponibles
python3 -m simulador reglamentos list

# Correr 200 partidos con el reglamento actual (v1)
python3 -m simulador run --reglamento v1 --partidos 200

# Comparar v1 y v2 en 3v3 y 4v4
python3 -m simulador compare-formatos --partidos 200 --ia estrategica

# Comparar v1 vs v2 en un solo formato (default 3v3)
python3 -m simulador compare-reglamentos --partidos 200
```

En Windows, donde dice `python3` va `.venv\Scripts\python` (o `py -3`).

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

**Para que se vea lindo** hacen falta dos bibliotecas opcionales, `rich` y
`textual`. El script de instalación ya las deja puestas en `.venv`, así que el
comando de todos los días es:

```bash
.venv/bin/python -m simulador ver --reglamento v2          # macOS y Linux
.venv\Scripts\python -m simulador ver --reglamento v2 --ui textual   # Windows
```

**En Windows conviene agregar `--ui textual`:** `curses`, que es lo que usa la
interfaz por defecto en macOS y Linux, no viene con Python en Windows. Con
`textual` instalado se ve igual o mejor; sin ninguna de las dos, el simulador
cae a un modo simple que imprime el relato sin paneles.

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

Para crear uno nuevo, lo más cómodo es la interfaz: **2 · Reglas → + Nuevo**,
o duplicar uno que ya exista. A mano también se puede: copiá
[`reglamentos/_plantilla.json`](reglamentos/_plantilla.json) →
[`docs/reglamentos-guia.md`](docs/reglamentos-guia.md).

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
simulador/       Motor Python + línea de comandos
  web/           Interfaz gráfica: servidor y página
configs/         Equipos y variantes de simulación (JSON)
docs/            Reglamentos humanos, resultados y el sitio publicado
instalar.sh      Instalación en macOS y Linux
instalar.bat     Instalación en Windows
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
