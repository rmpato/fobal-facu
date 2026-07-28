# Cómo funciona la simulación

Qué hace el motor por dentro: turnos, IA, métricas y limitaciones.  
Para correr simulaciones → [guia-rapida.md](./guia-rapida.md). Para conclusiones → [resultados-iniciales.md](./resultados-iniciales.md).

---

## Arquitectura

```
simulador/
├── cartas.py       → tipos de carta y tablas de disparo
├── reglamento.py   → carga reglamentos JSON
├── config.py       → configuración y variantes
├── modelo.py       → jugadores, marcador, estado
├── motor.py        → reglas (turnos, pases, goles, penales)
├── ia.py           → decisiones ofensivas y defensivas
├── estadisticas.py → agregar resultados
└── __main__.py     → CLI

reglamentos/        → v0.json, v1.json, v1.1.json, …
```

Cada partido usa semilla `0…N-1` → corridas reproducibles.

---

## Ciclo de un partido

1. **Setup:** baraja mazo, 6 cartas por jugador, sorteo de posesión inicial.
2. **Bucle** hasta ganador, 2-2→penales, o 500 turnos:
   - Portador elige acción (IA)
   - Defensa reacciona según reglamento
   - Actualiza posesión, marcador, manos
   - Reposición según reglamento (`mano_vacia` en v0, `cambio_equipo` en v1)
3. **Fin:** registra goles, turnos, acciones, cartas.

Parámetros de corrida → [guia-rapida.md](./guia-rapida.md#opciones-útiles). Reglamentos → [reglamentos-guia.md](./reglamentos-guia.md).

---

## Acciones que modela el motor

### Con carta en mano

| Acción | Carta |
|--------|-------|
| **Pase** | `Pase` |
| **Disparo al arco** | `Disparo al arco` |
| **Gambetear** | `Gambetear` (contra-respuesta) |

### Decisiones sin carta (habilitadas por regla)

| Decisión | v0 | v1 |
|----------|----|----|
| **Pasa de turno** | ✓ | ✓ |
| **Reventar / despeje** | — | ✓ |

No hay carta “Pasa de turno” ni “Reventar” en el mazo. El portador **elige** esas acciones, como dice el reglamento en mesa.

### Defensivas (como reacción)

| Trigger | v0 | v1 |
|---------|----|----|
| Pase | Corta pase | Robo pelota |
| Pasa de turno | Tackle, Trampa, Marca | Trampa, Marca |

### Contra-respuestas

- v0: La dejo pasar vs corte; Gambetear vs tackle
- v1: Gambetear vs robo

### Dados

- **Disparo:** 1d6 cada uno; tabla según pases en la jugada
- **Reventarla:** 1d6 por equipo (no tira el reventor)
- **Penales:** como disparo con 0 pases
- v1: rebote y palo → se repite el tiro

---

## Perfiles de IA

| Perfil | Comportamiento |
|--------|----------------|
| `simple` | Probabilidades fijas; casi no usa pasa de turno |
| `estrategica` | **Default.** Pasa de turno táctico, evita marcado, defensa activa |

Usar siempre el mismo perfil al comparar reglamentos.

---

## Métricas registradas

**Por partido:** goles, turnos, penales, acciones (`pase`, `disparo`, `robo`, `despeje`, `pasa_turno`, `falta`), trampa/marca, cartas jugadas.

**Agregadas:** % victorias, empates técnicos, promedios, distribución de acciones.

---

## Cómo interpretar resultados

| Señal | Posible lectura |
|-------|-----------------|
| Muchos empates técnicos (>500 turnos) | Reglas o IA que estancan |
| Una carta domina (>40/partido) | Posible desbalance |
| Trampa/Marca ~0 con IA simple | La IA no pasa de turno |
| Penales muy frecuentes | Muchos partidos a 2-2 |

Análisis de diseño → [recomendaciones-diseno.md](./recomendaciones-diseno.md).

---

## Supuestos y limitaciones

Reglas confirmadas y pendientes → [ambiguedades.md](./ambiguedades.md).

**No modela (todavía):** bluff, charla, coordinación de equipo, decisiones óptimas, tiempo real.

Los números son **comparativos entre reglamentos**, no predicción exacta de mesa.

---

## Un turno v1 (resumen)

```
Portador elige (IA)
  ├─ Falta (prob.) → reset pases
  ├─ Disparo → dados → gol o saque arquero
  ├─ Reventar → duelo dados → nuevo portador
  ├─ Pasa de turno → Trampa / Marca / (v0: Tackle)
  └─ Pase → offside/marca activa → robo
            → defensa Robo → Gambetear? → pase o robo
            → pase completado
```

---

## Relacionado

- [guia-rapida.md](./guia-rapida.md) — comandos
- [resultados-iniciales.md](./resultados-iniciales.md) — números
- [reglamentos-guia.md](./reglamentos-guia.md) — crear v1.2 / v2
