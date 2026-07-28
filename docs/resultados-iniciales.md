# Resultados de simulación

Hallazgos de corridas automáticas. Configuración habitual: **2 vs 2**, semillas `0…N-1`.  
Cómo reproducir → [guia-rapida.md](./guia-rapida.md). Qué probar next → [recomendaciones-diseno.md](./recomendaciones-diseno.md).

Última actualización: julio 2026.

---

## Resumen ejecutivo

| | v0 | v1 (IA simple) | v1 (IA estratégica) |
|---|-----|----------------|---------------------|
| **Partidos completados** | ~1% | 62,5% | **96,5%** |
| **Goles / partido** | 0,66 | 3,25 | **4,02** |
| **Empates técnicos** | 99% | 40% | **3,5%** |
| **Penales (2-2)** | 0% | 22,5% | **36,5%** |

**Conclusiones:**

1. **v0 no cierra** — casi todos los partidos superan 500 turnos; el pasa de turno sin respuesta estanca.
2. **v1 es jugable** — con IA estratégica (default) los partidos terminan y hay ~4 goles/partido.
3. **Trampa/Marca** solo importan si el ataque pasa de turno (~16×/partido con IA estratégica vs ~1× con IA simple).
4. **Variante v1.1** (pasa al compañero) casi no cambia números vs v1 baseline.
5. **Perfil de juego v1:** pase 35%, despeje 28%, robo 16%, disparo 8%, pasa turno 8%, falta 6%.

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

### v1 · IA estratégica (200 partidos)

| Métrica | IA simple (antes) | IA estratégica |
|---------|-------------------|----------------|
| Partidos completados | 62,5% | **96,5%** |
| Empates técnicos | 40% | **3,5%** |
| Goles promedio | 3,25 | **4,02** |
| Turnos promedio | 304 | **183** |
| Penales | 22,5% | **36,5%** |
| Pasa de turno / partido | ~1,2 | **16,3** |
| Trampa colocada / partido | ~0,9 | **3,65** |
| Marca colocada / partido | ~1,2 | **5,90** |

### Distribución de acciones (v1, IA estratégica)

| Acción | % del total |
|--------|-------------|
| Pase | 34,7% |
| Despeje | 28,2% |
| Robo | 15,5% |
| Disparo | 8,4% |
| Pasa de turno | 7,6% |
| Falta | 5,5% |

> **Para playtesting:** anotar en mesa cuántas veces ocurre cada acción por partido y comparar con esta tabla.

### Variante `pasa_companero` (200 partidos)

Si nadie reacciona al pasa de turno, la pelota pasa a un compañero.

| Métrica | baseline | pasa_companero |
|---------|----------|----------------|
| Completados | 96,5% | 97,5% |
| Goles promedio | 4,02 | 3,98 |
| Turnos promedio | 183 | 185 |
| Penales | 36,5% | 32,0% |

**Conclusión:** la variante `pasa_companero` apenas cambia el balance vs `nada` con IA estratégica. El estancamiento de v1 se debía más a la IA que a la regla.

Próximos experimentos → [recomendaciones-diseno.md](./recomendaciones-diseno.md).
