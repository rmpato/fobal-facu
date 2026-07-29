# Resultados de simulación

Hallazgos de corridas automáticas. Configuración habitual: **3 vs 3**, semillas `0…N-1`, IA estratégica.
Cómo reproducir → [guia-rapida.md](./guia-rapida.md). Perfiles de IA → [perfiles-ia.md](./perfiles-ia.md). Qué probar next → [recomendaciones-diseno.md](./recomendaciones-diseno.md).

Última actualización: julio 2026.

---

## Resumen ejecutivo

| | v0 (3v3) | v1 simple (3v3) | v1 estratégica (3v3) |
|---|-----|----------------|---------------------|
| **Partidos completados** | ~26% | 99,5% | **99,0%** |
| **Goles / partido** | 1,89 | 4,08 | **4,03** |
| **Empates técnicos** | 74% | 0,5% | **1,0%** |
| **Penales (2-2)** | 8,5% | 35,5% | **35,0%** |

**Conclusiones:**

1. **v0 no cierra bien** — ~74% empates técnicos en 3v3 (mejor que 2v2, pero sigue mal).
2. **v1 es jugable** — ~99% completados con IA estratégica; ~4 goles/partido.
3. **Trampa/Marca en v1** — ~12 colocaciones/partido (3v3); la estratégica usa más pasa de turno que la simple.
4. **Variante v1.1** (pasa al compañero) casi no cambia números vs v1 baseline.
5. **v2** (sin pasa turno, trampa al pase): 100% completados, ~151 turnos, más pase y Trampa/Marca (~19 colocaciones/partido).
6. **Perfil de juego v1 (3v3):** pase 40%, despeje 16%, robo 19%, disparo 9%, pasa turno 9%, falta 7%.

---

## Reglas confirmadas en el motor

| Regla | Comportamiento |
|-------|----------------|
| Equipos | Mínimo 2 jugadores por equipo |
| Marcador 2-2 | Penales inmediatos |
| Trampa / Marca | Solo cuando el ataque **pasa de turno** |

Detalle y supuestos pendientes → [ambiguedades.md](./ambiguedades.md).

---

## Metodología

```bash
python3 -m simulador compare-reglamentos --partidos 200
python3 -m simulador run --reglamento v1 --partidos 200
python3 -m simulador run --reglamento v1 --partidos 1 --verbose
```

- **Empate técnico:** >500 turnos sin ganador → señal de estancamiento.
- **Partido completado:** ≥3 goles o penales tras 2-2.

---

## Resumen comparativo (200 partidos c/u, reglas actuales)

| Métrica | v0 | v1 |
|---------|----|----|
| Partidos completados | 2 (1,0%) | 120 (60,0%) |
| Empates técnicos (>500 turnos) | 198 (99,0%) | 80 (40,0%) |
| Victorias equipo 0 / 1 | 1 / 1 | 65 / 55 |
| Goles promedio por partido | 0,66 | 3,25 |
| Turnos promedio | 495,5 | 303,9 |
| Partidos resueltos por penales | 0 | 45 (22,5%) |
| Barajadas de descarte (total) | 5 | 145 |

### Lectura rápida

- **v0 no termina:** casi todos los partidos chocan contra el límite de 500 turnos con menos de 1 gol de promedio.
- **v1 sí cierra partidos** en ~60% de los casos, con ~3,2 goles por partido y ~23% yendo a penales.
- **Balance v1** entre equipos: 32,5% vs 27,5% (resto empates técnicos). Simétrico dentro de lo esperable.

---

## Impacto de aclarar Trampa / Marca (solo en pasa de turno)

Antes de la aclaración, v1 permitía jugar **Trampa de offside** y **Marca personal** de forma proactiva “entre pases”. Eso **no** coincide con la regla de mesa. Corrida anterior (200 partidos, lógica vieja):

| Métrica | v1 (lógica vieja) | v1 (regla corregida) | Δ |
|---------|-------------------|----------------------|---|
| Partidos completados | 188 (94%) | 120 (60%) | −36 pp |
| Empates técnicos | 12 (6%) | 80 (40%) | +34 pp |
| Goles promedio | 4,06 | 3,25 | −0,81 |
| Turnos promedio | 207,1 | 303,9 | +96,8 |
| Penales | 82 (41%) | 45 (22,5%) | −18,5 pp |
| Marca personal / partido | ~9,74 | ~1,22 | −87% |
| Trampa offside / partido | ~5,84 | ~0,92 | −84% |

### Interpretación

1. **La lógica vieja inflaba artificialmente el ritmo del juego.** Trampa/Marca en cada posesión aceleraban robos y cambios de equipo → más goles y más penales.
2. **Con la regla real, Trampa y Marca son cartas de nicho** (~1 vez por partido cada una). Dependen de que el ataque **pase de turno**, algo que la IA hace poco (~8% en v1).
3. **v1 sigue siendo jugable** respecto a v0, pero **más lento y menos goleador** de lo que sugería la simulación incorrecta.
4. **Para evaluar bien Trampa/Marca** hace falta IA que use **pasa de turno** de forma estratégica (ej. para provocar la trampa o ganar tempo).

---

## Uso de cartas por partido

### v0 (reglas actuales)

| Carta | Total (200 pj) | Por partido |
|-------|----------------|-------------|
| Pase | 3.508 | 17,54 |
| Disparo al arco | 1.013 | 5,07 |
| Corta pase | 861 | 4,30 |
| Tackle | 776 | 3,88 |
| Falta | 731 | 3,65 |
| Marca personal | 377 | 1,89 |
| Gambetear | 260 | 1,30 |
| La dejo pasar | 246 | 1,23 |
| Trampa de offside | 210 | 1,05 |

### v1 (reglas actuales)

| Carta | Total (200 pj) | Por partido |
|-------|----------------|-------------|
| Pase | 11.084 | 55,42 |
| Robo pelota | 5.075 | 25,38 |
| Disparo al arco | 3.050 | 15,25 |
| Gambetear | 1.927 | 9,63 |
| Falta | 1.814 | 9,07 |
| Marca personal | 244 | 1,22 |
| Trampa de offside | 183 | 0,92 |

### Observaciones sobre cartas

| Carta | v0 | v1 |
|-------|----|----|
| **Pase** | Motor de juego, pero pocos goles | Muy alta frecuencia; circulación constante |
| **Robo / Corta pase** | ~4,3/partido | Robo ~25/partido — defensa muy activa en v1 |
| **Disparo al arco** | ~5/partido, poco efectivo (pocos goles) | ~15/partido; principal vía de gol |
| **Gambetear** | ~1,3/partido | ~9,6/partido — central en v1 vs robo |
| **Marca / Trampa** | ~1,9 / ~1,0 (solo pasa de turno) | ~1,2 / ~0,9 — poco uso; cartas “situacionales” |
| **Falta** | ~3,7/partido | ~9/partido |

---

## Hallazgos por versión

### v0 — estancamiento

**Síntoma:** 99% de partidos superan 500 turnos; 0,66 goles/partido; casi nunca se llega a 2-2 ni a penales.

**Hipótesis principal:** **Pasa de turno** deja la pelota en el mismo jugador si la defensa no responde. El partido puede girar en círculos sin acercarse al arco. La reposición por mano vacía también alarga el mazo sin forzar resolución.

**Posibles líneas de diseño (para discutir en mesa):**

- Si nadie reacciona al pasa de turno → el turno pasa a un compañero
- Límite de pases de turno consecutivos antes de obligar despeje
- Ajustar tabla de disparo o frecuencia de robo para que v0 sea más goleador

### v1 — partidos más dinámicos, pero 40% aún se estancan

**Lo positivo:**

- 60% de partidos terminan con ganador
- ~3,2 goles/partido es un ritmo razonable para un juego de cartas
- **Reventar la pelota** y **Robo pelota** generan cambios de posesión constantes
- Balance entre equipos aceptable

**Lo preocupante:**

- 40% de empates técnicos → muchos partidos aún no cierran
- Trampa/Marca casi no aparecen con IA actual → difícil evaluar si valen su slot en el mazo (5 + 3 cartas)
- 22,5% de partidos van a penales → verificar si en mesa 2-2 es tan frecuente

---

## Preguntas abiertas para playtesting

1. **Pasa de turno sin respuesta defensiva** — ¿la pelota sigue igual? ¿Pasa a un compañero?
2. **Frecuencia real de pasa de turno** en humanos — define cuánto se ven Marca/Trampa.
3. **¿3 goles cierran el partido además del 2-2?** El simulador usa ambos criterios (ver [ambiguedades.md](./ambiguedades.md)).
4. **¿40% de partidos “colgados” en v1** pasa también en mesa, o es artefacto de la IA?

---

## Limitaciones

- La IA no blefea ni juega como humanos expertos.
- Números **comparativos** entre reglamentos, no predicción exacta de mesa.
- Re-correr tras cambios: `python3 -m simulador compare-reglamentos`.

---

## Historial de corridas

| Fecha | Cambio | Archivo / comando |
|-------|--------|-------------------|
| Jul 2026 | Primera corrida (v1 con Trampa/Marca proactivas) | Ver sección “Impacto de aclarar Trampa / Marca” |
| Jul 2026 | Reglas confirmadas: 2-2 → penales; Trampa/Marca solo en pasa de turno; mín. 2 jugadores | Este documento, `python3 -m simulador compare` |

---

## IA estratégica + variantes (jul 2026)

Corridas con `--ia estrategica` (default) y comando `python3 -m simulador variantes --partidos 200`.

### v1 · IA estratégica (200 partidos · 3 vs 3)

| Métrica | IA simple (3v3) | IA estratégica (3v3) |
|---------|-----------------|----------------------|
| Partidos completados | 99,5% | **99,0%** |
| Empates técnicos | 0,5% | **1,0%** |
| Goles promedio | 4,08 | **4,03** |
| Turnos promedio | 180 | **179** |
| Penales | 35,5% | **35,0%** |
| Pasa de turno / partido | ~8 | **19** |
| Trampa colocada / partido | ~1,8 | **4,38** |
| Marca colocada / partido | ~3,0 | **7,49** |

### Distribución de acciones (v1, 3 vs 3, IA estratégica)

| Acción | % del total |
|--------|-------------|
| Pase | 40,3% |
| Robo | 19,1% |
| Despeje | 15,8% |
| Disparo | 8,6% |
| Pasa de turno | 8,8% |
| Falta | 7,4% |

> **Para playtesting:** anotar en mesa cuántas veces ocurre cada acción por partido y comparar con esta tabla.

### Variante `pasa_companero` (200 partidos · 3 vs 3)

Si nadie reacciona al pasa de turno, la pelota pasa a un compañero.

| Métrica | baseline | pasa_companero |
|---------|----------|----------------|
| Completados | 99,0% | 99,0% |
| Goles promedio | 4,03 | 4,01 |
| Turnos promedio | 179 | 169 |
| Penales | 35,0% | 35,5% |

**Conclusión:** la variante `pasa_companero` apenas cambia el balance vs `nada` con IA estratégica. El estancamiento de v1 se debía más a la IA que a la regla.

Próximos experimentos → [recomendaciones-diseno.md](./recomendaciones-diseno.md).

---

## Reglamento v2 (jul 2026 · 3 vs 3)

Corridas con `--ia estrategica` y `python3 -m simulador compare-reglamentos --partidos 200`.

Cambios vs v1: sin pasa de turno; Trampa/Marca al reaccionar a un pase; robo ↔ gambetear encadenables.

### Comparación rápida (3 vs 3)

| Reglamento | Compl. | Goles | Turnos | Pen. | Pase% | PasaT% | Trampa |
|------------|--------|-------|--------|------|-------|--------|--------|
| v0 | 26,0% | 1,89 | 392,1 | 8,5% | 8,2% | 84,9% | 1,94 |
| v1 | 99,0% | 4,03 | 179,0 | 35,0% | 40,3% | 8,8% | 4,38 |
| v1.1 | 99,0% | 4,01 | 168,9 | 35,5% | 40,4% | 8,8% | 4,09 |
| **v2** | **100%** | **3,85** | **151,3** | **24,0%** | **44,6%** | **0%** | **7,15** |

### Distribución de acciones (v2, 3 vs 3, IA estratégica)

| Acción | % del total |
|--------|-------------|
| Pase | 44,6% |
| Robo | 22,4% |
| Despeje | 16,3% |
| Disparo | 8,8% |
| Falta | 8,0% |
| Pasa de turno | 0% |

### Trampa / Marca (v2 · 3 vs 3)

| Evento | Por partido |
|--------|-------------|
| Trampa colocada | 7,15 |
| Marca colocada | 11,95 |
| Offside efectivo | 4,67 |

**Conclusión:** v2 cierra todos los partidos, acorta la duración (~15% menos turnos que v1 en 3v3), sube pase y uso de Trampa/Marca (reactivas al pase). Menos penales que v1 (~24% vs ~35%). Balance 48% / 52% victorias.

Reglas → [reglamento-v2.md](./reglamento-v2.md). Sitio → [resultados.html](./resultados.html#compare-cli).

> Corridas anteriores en **2 vs 2** quedaron obsoletas; el simulador usa **3 vs 3** por defecto desde jul 2026.
