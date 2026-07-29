# Reglamento v2 (iteración 2)

> Cambios surgidos del playtesting con amigos. Parte de **v1** con estas modificaciones.

Para reglas completas de mazo, disparo, penales y reventar, ver [reglamento-v1.md](./reglamento-v1.md). Acá solo lo que **cambia** respecto a v1.

## Resumen de cambios

| Tema | v1 | v2 |
|------|----|----|
| **Pasa de turno** | Decisión permitida (sin carta) | **Eliminado** — solo se puede **reventar** si no hay pase/disparo |
| **Trampa / Marca** | Solo cuando el ataque pasa de turno | Se pueden jugar **al reaccionar a un pase** |
| **Reacciones defensivas** | Una por acción del ataque | Igual: **una carta por acción** (no robo + marca a la vez) |
| **Robo vs Gambetear** | Un intento de gambetear | **Encadenables**: robo → gambetear → robo → … mientras haya cartas |

## Acciones ofensivas (v2)

### Con carta

Igual que v1: **Pase**, **Disparo al arco**.

### Decisiones (sin carta)

| Decisión | v2 |
|----------|-----|
| **Pasa de turno** | ❌ No existe |
| **Reventar la pelota** | ✅ Sí (despeje por dado) |

## Reacciones defensivas (v2)

| Si el ataque… | La defensa puede jugar… |
|---------------|-------------------------|
| Pasó la pelota | `Robo pelota`, `Trampa de offside`, `Marca personal` |
| Pasó de turno | *(no aplica — acción eliminada)* |

- Solo **una** reacción defensiva por acción ofensiva (una carta en todo el equipo).
- **Robo pelota** puede encadenarse con **Gambetear** del portador, y la defensa puede volver a reaccionar con otro robo si el reglamento lo permite y tiene cartas.

### Contra-respuesta ofensiva

Igual que v1: `Robo pelota` se anula con `Gambetear` (con posibilidad de seguir encadenando en v2).

## Mazo

Igual que v1 (108 cartas). Ver tabla en [reglamento-v1.md](./reglamento-v1.md).

## Simulador

```bash
python3 -m simulador reglamentos show v2
python3 -m simulador run --reglamento v2 --partidos 200 --ia estrategica
python3 -m simulador compare-reglamentos --partidos 200 --ia estrategica
```

Simulaciones batch: **3 vs 3** por defecto (`--jugadores-por-equipo 3`).

Especificación JSON: [`reglamentos/v2.json`](../reglamentos/v2.json).
