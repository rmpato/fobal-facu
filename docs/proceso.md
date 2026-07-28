# Proceso de simulación

Este documento describe cómo estamos usando la simulación para iterar el juego.

## Objetivo

Jugar partidos repetidos de forma automática para detectar:

- Reglas ambiguas o contradictorias
- Cartas dominantes o inútiles
- Partidos demasiado largos o cortos
- Estrategias abusivas
- Diferencias de balance entre v0 y v1

## Versiones

| Versión | Reglas | Mazo |
|---------|--------|------|
| **v0** | [reglamento-v0.md](./reglamento-v0.md) | Pase-heavy, `Corta pase`, `Tackle`, `La dejo pasar` |
| **v1** | [reglamento-v1.md](./reglamento-v1.md) | `Robo pelota` unifica robo, **Reventarla**, **Pasa de turno** |

Los cambios principales de v0 → v1:

1. **Ceder el turno / Pasa de turno** → en v1 también existe **Reventar la pelota** (duelo de dados)
2. **Corta pase + Tackle** → **Robo pelota** (solo contra pases)
3. **La dejo pasar** eliminada; solo **Gambetear** contra robo
4. Reposición: de "mano vacía" a "al cambiar de equipo"
5. Una sola reacción defensiva por carta ofensiva
6. Rebote y palo en disparos al arco
7. **Trampa de offside / Marca personal:** solo cuando el ataque pasa de turno (confirmado en playtesting)

## Cómo correr simulaciones

```bash
# Instalar dependencias (solo stdlib; ver requirements.txt)
python -m venv .venv && source .venv/bin/activate

# 100 partidos con reglas v1, 2 vs 2
python -m simulador run --reglas v1 --partidos 100 --jugadores-por-equipo 2

# Comparar v0 vs v1
python -m simulador run --reglas v0 --partidos 500 --jugadores-por-equipo 2
python -m simulador run --reglas v1 --partidos 500 --jugadores-por-equipo 2

# Ver registro detallado de un partido
python -m simulador run --reglas v1 --partidos 1 --verbose
```

## Resultados

Los hallazgos de cada corrida se documentan en [resultados-iniciales.md](./resultados-iniciales.md) y en el [sitio web](./index.html) (GitHub Pages).

## Supuestos del simulador

Algunas reglas no están 100% definidas en el PDF. El motor implementa supuestos documentados en [ambiguedades.md](./ambiguedades.md). Cada supuesto es configurable para probar variantes.

## Métricas que reportamos

- Goles por partido y duración (turnos)
- Frecuencia de cada carta jugada
- % de partidos que van a penales
- % de posesiones que terminan en disparo / pase / robo / despeje
- Veces que se barajó el descarte (fin de mazo)
- Partidos que exceden límite de turnos (posible loop)

## Próximos pasos

- [ ] Validar supuestos con el grupo de playtesting
- [ ] Discutir estancamiento de **ceder el turno** en v0 (ver [resultados-iniciales.md](./resultados-iniciales.md))
- [ ] Agregar estrategias de IA más humanas (conservar `Falta`, marcar delanteros, etc.)
- [ ] Modo interactivo para humanos vs bots
- [ ] Dashboard de comparación v0 vs v1
