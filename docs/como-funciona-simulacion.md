# Cómo funciona la simulación

Este documento explica qué hace el motor automático, paso a paso, para que se pueda interpretar los resultados y compararlos con partidas reales.

## Objetivo

Simular muchos partidos de **Fobal Facu** sin jugar a mano, para detectar:

- Partidos que no terminan o duran demasiado
- Cartas dominantes o inútiles
- Efecto de cambios de reglas (variantes)
- Distribución de acciones (pase, robo, despeje, etc.)

No reemplaza el playtesting humano: la IA es una aproximación. Los números sirven para **comparar** versiones de reglas entre sí.

---

## Arquitectura

```
simulador/
├── cartas.py       → tipos de carta y mazos v0/v1
├── config.py       → configuración y variantes (JSON)
├── modelo.py       → jugadores, marcador, estado del partido
├── motor.py        → reglas del juego (turnos, pases, goles, penales)
├── ia.py           → decisiones ofensivas y defensivas
├── estadisticas.py → agregar resultados de muchos partidos
└── __main__.py     → comandos de terminal (run, compare, variantes)
```

Cada **partido** es independiente. Se usa una semilla numérica (`0, 1, 2…`) para que las corridas sean reproducibles.

---

## Configuración de una corrida

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `reglas` | `v1` | `v0` o `v1` |
| `jugadores_por_equipo` | `2` | Mínimo 2 |
| `ia` | `estrategica` | `simple` o `estrategica` |
| `pasa_turno_sin_respuesta` | `nada` | `nada` o `pasa_companero` (variante) |
| `limite_turnos` | `500` | Si se supera → empate técnico |
| `prob_falta` | `0.08` | Probabilidad de que alguien juegue `Falta` en un turno |

Las variantes se pueden definir en [`configs/variantes.json`](../configs/variantes.json).

---

## Ciclo de un partido

1. **Setup:** se baraja el mazo, cada jugador recibe 6 cartas, un equipo inicia con la pelota.
2. **Bucle de turnos** (hasta ganador, 2-2→penales, o límite de turnos):
   - ¿Hay ganador (≥3 goles)? → fin
   - ¿Marcador 2-2? → penales → fin
   - El portador de la pelota elige una acción (IA)
   - La defensa puede reaccionar según la acción
   - Se actualiza posesión, marcador, cartas en mano
   - v0: repone mano si un jugador queda en 0 cartas
   - v1: repone al cambiar de equipo
3. **Fin:** se registran goles, turnos, acciones y cartas jugadas.

---

## Acciones que modela el motor

### Ofensivas

| Acción | v0 | v1 | Efecto en sim |
|--------|----|----|---------------|
| **Pase** | ✓ | ✓ | Pasa a compañero; puede ser robado/cortado |
| **Disparo al arco** | ✓ | ✓ | Dados pateador vs arquero; tabla según pases en la jugada |
| **Pasa de turno** | ✓ | ✓ | Defensa puede Trampa/Marca (v0 también Tackle) |
| **Reventar / despeje** | — | ✓ | Duelo de dados entre un jugador de cada equipo |

### Defensivas (como reacción)

| Trigger | v0 | v1 |
|---------|----|----|
| Pase | `Corta pase` | `Robo pelota` |
| Pasa de turno | `Tackle`, `Trampa`, `Marca` | `Trampa`, `Marca` |

### Contra-respuestas

- v0: `La dejo pasar` vs corte; `Gambetear` vs tackle
- v1: `Gambetear` vs robo

### Dados 🎲

- **Disparo:** cada uno tira 1d6; rangos de gol/atajada según pases acumulados en la jugada
- **Reventarla:** un jugador de cada equipo tira 1d6 (no el que reventó); gana el más alto
- **Penales:** misma lógica que disparo con 0 pases en la jugada
- v1: **rebote** (gol y atajada a la vez) y **palo** (mismo número) → se repite el tiro

---

## Perfiles de IA

### Simple (`--ia simple`)

Decisiones mayormente aleatorias con probabilidades fijas. Útil como baseline; **casi no usa pasa de turno**, por lo que Trampa/Marca rara vez aparecen.

### Estratégica (`--ia estrategica`, default)

Aproximación a decisiones más humanas:

**Ataque:**

- Dispara más cuando hay varios pases acumulados (mejor tabla de gol)
- Usa **pasa de turno** para armar jugada o provocar Trampa/Marca (~8–45% según contexto)
- Al pasar, evita compañero marcado si puede

**Defensa:**

- Más agresiva con Trampa/Marca cuando el rival pasa de turno
- Roba/corta pases con probabilidad moderada

---

## Métricas registradas

### Por partido

- Goles, turnos, si hubo penales
- Contador de **acciones:** `pase`, `disparo`, `robo`, `despeje`, `pasa_turno`, `falta`
- Eventos de trampa/marca: colocadas y efectivas
- Cartas jugadas (por tipo)

### Agregadas (lote de N partidos)

- % victorias, empates técnicos, penales
- Goles y turnos promedio
- **Distribución de acciones en %** (para comparar con mesa)
- Cartas por partido

---

## Variantes de reglas

Permiten probar reglas alternativas sin cambiar código.

**Ejemplo:** `pasa_turno_sin_respuesta`

| Valor | Comportamiento |
|-------|----------------|
| `nada` | Si nadie reacciona al pasa de turno, la pelota queda en el mismo jugador |
| `pasa_companero` | Sin respuesta defensiva → la pelota pasa a un compañero al azar |

Correr comparación:

```bash
python3 -m simulador variantes --partidos 500
```

---

## Supuestos y limitaciones

### Supuestos documentados

Ver [ambiguedades.md](./ambiguedades.md). Los principales:

- 2-2 → penales inmediatos
- Trampa/Marca solo en pasa de turno
- Reventarla: elige quién tira el dado (no el reventor)
- Falta: cualquier jugador, probabilidad fija por turno

### Lo que NO modela (todavía)

- Negociación, bluff, charla en mesa
- Decisiones óptimas (la IA no “piensa” como un humano experto)
- Tiempo real, fatiga, emociones
- Estrategia de equipo coordinada
- Cambios de mazo mid-partido

### Cómo interpretar resultados

| Señal | Posible lectura |
|-------|-----------------|
| Muchos empates técnicos (>500 turnos) | Reglas o IA que estancan el juego |
| Una carta domina (>40/partido) | Posible desbalance |
| Trampa/Marca ~0 con IA simple | La IA no pasa de turno → no evalúa esas cartas |
| Penales muy frecuentes | Muchos partidos llegan a 2-2 |

---

## Flujo resumido (un turno v1)

```
Portador elige acción (IA)
    │
    ├─ Falta (prob. global)? → reset pases, fin turno
    │
    ├─ Disparo → dados → gol? → marcador / saque arquero
    │
    ├─ Reventar → duelo dados → nuevo portador
    │
    ├─ Pasa de turno → defensa: Trampa / Marca / (v0: Tackle)
    │       └─ sin respuesta → (variante) pasa a compañero o nada
    │
    └─ Pase → ¿offside/trampa activa? → robo
              → ¿marca al receptor? → robo
              → defensa: Robo → ¿Gambetear? → pase ok o robo
              → pase completado → nuevo portador
```

---

## Relacionado

- [proceso.md](./proceso.md) — cómo usamos la simulación para iterar
- [resultados-iniciales.md](./resultados-iniciales.md) — números de corridas
- [simulador.html](./simulador.html) — comandos para correr localmente
