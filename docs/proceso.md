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

## Resultados

Los hallazgos de cada corrida se documentan en [resultados-iniciales.md](./resultados-iniciales.md), el [sitio web](./index.html) ([resultados.html](./resultados.html)) y GitHub Pages.

## Cómo correr simulaciones

```bash
# 100 partidos v1 con IA estratégica (default)
python3 -m simulador run --reglas v1 --partidos 100

# IA simple (comportamiento anterior)
python3 -m simulador run --reglas v1 --partidos 100 --ia simple

# Variante: si nadie reacciona al pasa de turno → pelota al compañero
python3 -m simulador run --reglas v1 --partidos 100 --pasa-turno-sin-respuesta pasa_companero

# Comparar variantes desde configs/variantes.json (500 partidos c/u)
python3 -m simulador variantes --partidos 500

# Comparar v0 vs v1
python3 -m simulador compare --partidos 200

# Ver registro detallado de un partido
python3 -m simulador run --reglas v1 --partidos 1 --verbose
```

## IA

| Perfil | Descripción |
|--------|-------------|
| `simple` | Decisiones probabilísticas fijas (baseline inicial) |
| `estrategica` | **Default.** Usa pasa de turno para armar jugada, evita pasar al marcado, defensa activa con Trampa/Marca |

## Variantes de reglas

Archivo [`configs/variantes.json`](../configs/variantes.json):

| Variante | `pasa_turno_sin_respuesta` |
|----------|---------------------------|
| `baseline` | `nada` — pelota queda en el mismo jugador |
| `pasa_companero` | `pasa_companero` — pasa a un compañero si la defensa no reacciona |

## Supuestos del simulador

Ver [ambiguedades.md](./ambiguedades.md). Explicación del motor: [como-funciona-simulacion.md](./como-funciona-simulacion.md) · [como-funciona.html](./como-funciona.html).

## Métricas que reportamos

- Goles por partido y duración (turnos)
- **Acciones (%):** pase, disparo, robo, despeje, pasa de turno, falta
- Trampa/Marca: colocadas y efectivas
- Frecuencia de cada carta jugada
- % de partidos que van a penales
- Partidos que exceden límite de turnos

## Próximos pasos

- [x] IA estratégica con pasa de turno intencional
- [x] Métricas por acción
- [x] Variantes configurables
- [ ] Validar % de acciones en mesa vs simulación
- [ ] Modo interactivo para humanos vs bots
