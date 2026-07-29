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

# Comparar v0, v1 y v1.1 entre sí
python3 -m simulador compare-reglamentos --partidos 200
```

Cada corrida imprime métricas y **qué reglas aplicó** ese reglamento. Para entender los comandos y el flujo completo → [`docs/guia-rapida.md`](docs/guia-rapida.md).

---

## Reglamentos implementados

Estos son los que el simulador puede correr hoy (`reglamentos/indice.json`):

| Id | Nombre | Qué cambia respecto al anterior | Reglas en mesa | Motor |
|----|--------|-----------------------------------|----------------|-------|
| **`v0`** | Reglamento original | — | [reglamento-v0.md](docs/reglamento-v0.md) | [v0.json](reglamentos/v0.json) |
| **`v1`** | Iteración 1 (playtesting) | Robo unificado, Reventar, rebote/palo, reposición al cambio de equipo | [reglamento-v1.md](docs/reglamento-v1.md) | [v1.json](reglamentos/v1.json) |
| **`v1.1`** | Pasa al compañero | Extiende **v1**: si nadie reacciona al pasa de turno → pelota a un compañero | [reglamento-v1.1.md](docs/reglamento-v1.1.md) | [v1.1.json](reglamentos/v1.1.json) |
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
| **Qué encontramos** (números, tablas) | [`docs/resultados-iniciales.md`](docs/resultados-iniciales.md) |
| **Qué probar next** (mazo, cartas, reglas trabadas) | [`docs/recomendaciones-diseno.md`](docs/recomendaciones-diseno.md) |
| **Reglas para jugar en mesa** | [`docs/reglamento-v1.md`](docs/reglamento-v1.md) (actual) · [`docs/reglamento-v0.md`](docs/reglamento-v0.md) (original) |

**Resumen en una frase:** v0 estanca en 3v3 (~74% empates técnicos); v1 cierra ~99% con IA estratégica; **v2** cierra todos los partidos, acorta duración y activa Trampa/Marca al pase. Simulaciones batch: **3 vs 3** por defecto.

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

## Sitio web (opcional)

Hay una versión HTML de resultados y reglas en [`docs/`](docs/) (GitHub Pages). No hace falta para correr simulaciones. Publicación: [`docs/GITHUB_PAGES.md`](docs/GITHUB_PAGES.md).

---

## Licencia

Uso privado / familiar — a definir.
