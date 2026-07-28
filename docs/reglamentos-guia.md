# Guía de reglamentos para el simulador

Cada simulación usa un **reglamento** identificable: reglas legibles para humanos (Markdown) + especificación que el motor interpreta (JSON).

## Estructura

```
reglamentos/
  indice.json          # catálogo de reglamentos
  v0.json              # reglamento completo
  v1.json
  v1.1.json            # extiende v1 (solo overrides)
  _plantilla.json      # copiar para crear uno nuevo

docs/
  reglamento-v0.md     # texto para jugar en mesa
  reglamento-v1.md
  reglamento-v1.1.md
  reglamento-v2.md     # (futuro)
```

## Crear un reglamento nuevo (ej. v1.2 o v2)

### 1. Documento humano

Creá `docs/reglamento-v1.2.md` (o `reglamento-v2.md`) con las reglas para jugar en mesa.

### 2. Especificación JSON

**Opción A — cambio chico sobre una versión existente:**

```json
{
  "id": "v1.2",
  "nombre": "Iteración 1.2",
  "version": "1.2",
  "documento": "docs/reglamento-v1.2.md",
  "descripcion": "Qué cambia respecto a v1.",
  "extends": "v1",
  "reglas": {
    "pasa_turno_sin_respuesta": "pasa_companero"
  }
}
```

Guardá como `reglamentos/v1.2.json`.

**Opción B — reglamento nuevo desde cero:**

Copiá `reglamentos/_plantilla.json` → `reglamentos/v2.json`, completá todos los campos y ajustá `motor_perfil` (`v0` o `v1`) según qué lógica de turno necesitás hoy.

### 3. Registrar en el índice

Agregá una entrada en `reglamentos/indice.json`:

```json
{
  "id": "v1.2",
  "archivo": "v1.2.json",
  "nombre": "Iteración 1.2",
  "documento": "docs/reglamento-v1.2.md"
}
```

### 4. Simular

```bash
python -m simulador reglamentos list
python -m simulador reglamentos show v1.2
python -m simulador run --reglamento v1.2 --partidos 500
python -m simulador compare-reglamentos --partidos 200
```

## Campos del JSON

| Sección | Qué controla |
|---------|----------------|
| `mazo` | Composición del mazo (nombre de carta → cantidad) |
| `partido` | Jugadores mínimos, mano inicial, goles para ganar, penales en 2-2 |
| `reposicion` | `cambio_equipo` (v1) o `mano_vacia` (v0) |
| `disparo.rebote_palo` | Rebote y palo en disparos |
| `acciones_ofensivas` | Incluye **decisiones sin carta** (`pasa_turno`, `reventar`) y acciones con carta (`pase`, `disparo`). No son tipos de carta del mazo. |
| `reacciones.pase` / `pasa_turno` | Cartas defensivas y contras |
| `reglas.*` | Comportamiento fino (faltas, pasa sin respuesta, etc.) |
| `motor_perfil` | `v0` o `v1`: motor de turno subyacente hasta que v2 sea 100 % declarativo |

## Reportes

Cada corrida incluye el id del reglamento, nombre, documento y lista de reglas aplicadas:

```
=== Simulación · reglamento v1 · Iteración 1 (playtesting) (200 partidos) ===
Documento: docs/reglamento-v1.md
Reglas aplicadas:
  · Victoria: primer equipo en 3 goles
  · ...
```

## Variantes vs reglamentos

- **Reglamento** (`reglamentos/*.json`): versión formal del juego (v1, v1.1, v2…).
- **Variantes** (`configs/variantes.json`): overrides de simulación sobre un reglamento base (IA, límites, etc.) sin crear un reglamento nuevo.

Para una variante que ya es regla de juego (como pasa al compañero), preferí un reglamento nuevo (`v1.1`) en lugar de un flag suelto en CLI.
