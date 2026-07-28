# Recomendaciones de diseño

Análisis basado en simulaciones (v0, v1, v1.1), reglamentos documentados y limitaciones conocidas del motor.  
**No es verdad de mesa** — hay que validar con playtesting humano.

Última actualización: julio 2026.

---

## Modelo de trabajo

```
Reglamento (JSON + MD)  →  Simulador (N partidos, IA fija)  →  Métricas
                                                              ↘
                    Comparar con otros reglamentos  ←──────────┘
```

Cada propuesta debería probarse como reglamento nuevo y compararse con `compare-reglamentos`. Cómo correr simulaciones → [guia-rapida.md](./guia-rapida.md).

---

## Lo que ya funciona (v1)

| Aspecto | Evidencia |
|---------|-----------|
| Partidos que cierran | ~96,5% completados con IA estratégica (vs 60% IA simple) |
| Ritmo goleador | ~4 goles/partido, ~183 turnos — razonable para cartas |
| Robo + Gambetear | Loop claro: pase → robo → gambetear (~15% + contra-respuesta frecuente) |
| Reventar la pelota | ~28% de acciones; resuelve deadlocks cuando no hay Pase |
| Balance entre equipos | Victorias simétricas en corridas largas |
| Trampa / Marca | Con IA estratégica aparecen ~9,5 veces/partido (colocadas); antes eran cartas muertas |

**Conclusión:** v1 es una base sólida. Los problemas restantes son de **afinado** (mazo, umbrales, reglas situacionales), no de reescribir el juego entero.

---

## Reglas y situaciones que estancan el juego

### 1. Pasa de turno sin respuesta (v0 crítico, v1 menor)

**Problema:** Si el ataque retiene la pelota y la defensa no juega Trampa/Marca/Tackle, en v0 la pelota **queda en el mismo jugador**. Eso explica el 99% de empates técnicos en v0.

**Opciones a probar:**

| Reglamento | Cambio | Simulación |
|------------|--------|------------|
| `v1.1` | Pelota pasa a un compañero | Casi sin efecto vs baseline con IA estratégica |
| Propuesta `v1.2` | Límite de 2 pases de turno seguidos → obligatorio pase, disparo o reventar | Por simular |
| Propuesta | Tras pasa de turno sin respuesta, la defensa roba automáticamente si tiene Robo (sin gastar carta) | Más agresivo; probar balance |

### 2. Demasiado despeje, poco arco

Con IA estratégica, **despeje (28%) ≈ pase (35%)** pero **disparo solo 8,4%**. Mucha pelota “en el aire” sin acercarse al gol.

**Hipótesis:** sin Pase en mano, reventar es la salida por defecto → partidos largos en transición, pocos tiros.

**Ideas:**

- Subir levemente `Disparo al arco` (12 → 14) o bajar umbrales de gol con 3+ pases
- Penalizar reventar consecutivo (misma regla que pasa de turno)
- Carta nueva: **Salida limpia** — pase que no puede ser robado (1 por mano / carta rara)

### 3. Falta oportunista

La simulación modela `Falta` con ~8% de chance por turno por jugador (~5,5% de acciones totales). Efecto: **resetea pases** sin cambiar posesión → puede alargar jugadas o frenar disparos.

**Validar en mesa:** ¿la Falta se juega tan seguido? ¿Es divertida o molesta?

**Si molesta:** bajar copias (7 → 4), o regla “máximo 1 falta por equipo por ronda de posesión”.

### 4. 2-2 → penales muy frecuente

~36,5% de partidos van a penales con IA estratégica. Puede ser deseable (dramático) o agotador.

**Opciones:**

- Clarificar “mejor de 5” vs “primero en 3” ([ambiguedades.md](./ambiguedades.md))
- Subir meta a 4 goles antes de penales
- Penales solo si empatan 2-2 **y** ambos equipos tuvieron al menos X disparos al arco

### 5. Muerte por límite de turnos (500)

Señal de loop. Con IA estratégica en v1 bajó al ~3,5%. Si en mesa sigue pasando, buscar qué acción humana repite (¿pasa de turno en cadena?, ¿faltas?, ¿no disparar nunca?).

---

## Composición del mazo (v1)

Mazo actual: **108 cartas**, 7 tipos.

| Carta | Cantidad | % mazo | Uso simulado (IA estratégica) |
|-------|----------|--------|-------------------------------|
| Pase | 42 | 39% | Motor del juego; ~35% acciones |
| Robo pelota | 24 | 22% | Muy activa; ~15% acciones + respuestas |
| Gambetear | 15 | 14% | Contra-robo frecuente |
| Disparo al arco | 12 | 11% | ~8% acciones; **única vía de gol** |
| Falta | 7 | 6% | ~5,5% acciones |
| Marca personal | 5 | 5% | Solo vía pasa de turno |
| Trampa de offside | 3 | 3% | Solo vía pasa de turno |

### Observaciones

1. **Pase domina** — coherente con un juego de posesión, pero comprime el espacio para otras identidades.
2. **Disparo es escaso** para ser el climax del partido. Considerar 12 → 14.
3. **Trampa + Marca = 8 cartas** (~7% del mazo) activadas por una acción que es solo ~7,6% del juego. Diseño intencional (cartas de setup), pero frágil: si nadie pasa de turno, el mazo se siente más chico.
4. **Robo vs Gambetear (24 vs 15)** — ratio ~1,6:1. Si en mesa el robo se siente opresivo, subir Gambetear a 18 o bajar Robo a 20.

### Propuesta de mazo v1.2 (para simular, no definitiva)

| Carta | v1 | v1.2 propuesto | Motivo |
|-------|-----|----------------|--------|
| Pase | 42 | 40 | Libera slots |
| Robo pelota | 24 | 22 | Menos presión constante |
| Gambetear | 15 | 16 | Mejor respuesta al robo |
| Disparo al arco | 12 | 14 | Más definición |
| Falta | 7 | 5 | Menos resets |
| Marca personal | 5 | 5 | — |
| Trampa de offside | 3 | 4 | Un poco más visible |
| **Nueva: Regate** | — | 2 | Ver sección cartas nuevas |

---

## Cartas redundantes o solapadas

### v0 → v1 (ya resuelto en gran parte)

| v0 | v1 | Notas |
|----|-----|-------|
| Corta pase + Tackle | Robo pelota | Unificación acertada; menos reglas que memorizar |
| La dejo pasar | Gambetear (parcial) | “La dejo pasar” era contra corte en receptor; en v1 la marca no se evita igual. **No hace falta reintroducirla** salvo que vuelva Corta pase |
| Ceder el turno | Pasa de turno | Mismo concepto, mejor nombre |

### Dentro de v1

| Par | ¿Redundante? | Recomendación |
|-----|--------------|---------------|
| Trampa vs Marca | No — offside vs marca a jugador | Mantener ambas; son las únicas defensas “de setup” |
| Gambetear vs “no tener Robo” | Parcial | Gambetear solo contra Robo; si el robo domina, Gambetear es obligatoria en mano — OK |
| Falta vs Pasa de turno | Sí, en espíritu | Ambas retienen pelota / resetean ritmo. Considerar fusionar en v2 o restringir Falta |

**No recomendamos** sacar Trampa/Marca todavía: con IA estratégica ya aportan ~9 efectos/partido. El problema era de **frecuencia de pasa de turno**, no de diseño de carta.

---

## Ideas de cartas nuevas

Cartas que podrían **llenar huecos** detectados en simulación:

### 1. Regate (ofensiva, común)

- **Efecto:** como Gambetear pero solo si tenés la pelota y la defensa intenta Robo; o: jugarla proactivamente para avanzar un “pase sin pase” (cuenta como pase en la jugada).
- **Por qué:** más herramientas ofensivas sin subir Pase; reduce deadlocks.

### 2. Presión / Anticipación (defensiva, poco común)

- **Efecto:** jugable cuando el rival **pasa de turno** además de Trampa/Marca; o: “el próximo pase del rival puede ser robado con +1 en el dado”.
- **Por qué:** da a la defensa otra razón para esperar el pasa de turno sin duplicar Trampa/Marca.

### 3. Centro / Envío (ofensiva)

- **Efecto:** Pase que **no puede ser robado** por Robo pelota (solo Marca si ya estaba colocada).
- **Por qué:** rompe el loop pase–robo–gambetear; premia armar jugada con pases previos.

### 4. Arquero sale (defensiva, rara)

- **Efecto:** en fase de disparo, el arquero tira con ventaja (ej. ataja con 5–6 en vez de 4–6 según tabla).
- **Por qué:** si suben los goles demasiado, válvula de escape sin tocar la tabla principal.

### 5. Tarjeta / Amonestación (neutral o defensiva)

- **Efecto:** cancela una Falta rival o impide otra Falta del mismo equipo esta ronda.
- **Por qué:** controla spam de Falta si en mesa resulta tedioso.

### 6. Contraataque (trigger, rara)

- **Efecto:** al robar la pelota, podés jugar inmediatamente un Disparo al arco sin tener la carta (o con descuento de pases).
- **Por qué:** acorta transiciones; más goles desde transición.

**Prioridad para prototipar:** Centro/Envío o Regate primero (afectan el cuello de botella pase–robo). Probar en `reglamentos/v1.2.json` con 2–4 copias.

---

## Reglas que faltan cerrar

Antes de un `v2` grande, conviene resolver en mesa:

1. **Victoria:** ¿3 goles, 5 goles, o solo 2-2 → penales?
2. **Pasa de turno sin respuesta** — baseline vs v1.1 (ya simulado: poco impacto con IA buena; igual importa en humanos)
3. **Falta:** timing exacto y límites
4. **Reposición:** ¿todos repone al cambio de equipo o solo el equipo que recupera?
5. **Rebote/palo:** ¿en mesa se siente justo o alarga disparos?

Ver [ambiguedades.md](./ambiguedades.md).

---

## Qué considerar a continuación (priorizado)

### Corto plazo (próximas sesiones de mesa)

1. **Contar acciones en 3–5 partidos reales** y comparar con la tabla de [resultados-iniciales.md](./resultados-iniciales.md) (pase %, despeje %, penales).
2. **Decidir pasa de turno sin respuesta** — quedarse en baseline o adoptar v1.1 formalmente.
3. **Clarificar condición de victoria** (3 vs 5 goles).

### Mediano plazo (reglamento v1.2)

1. Simular **mazo v1.2** (más Disparo, menos Falta/Robo).
2. Probar **límite de pases de turno consecutivos**.
3. Opcional: 2 copias de **Regate** o **Centro**.

### Largo plazo (v2)

1. Motor más declarativo (menos `motor_perfil v0/v1`).
2. Cartas de **identidad de equipo** o roles (arquero designado con cartas extra).
3. Modo interactivo humano vs simulador en la web.

---

## Limitaciones de este análisis

- La IA **no blefea** ni guarda cartas para momentos clave.
- Los humanos pueden pasar de turno por **táctica social**, no solo probabilidad.
- Números son **comparativos entre reglamentos**, no predicción exacta.
- Cualquier carta nueva requiere JSON + MD + corrida `compare-reglamentos`.

---

## Enlaces

- [Resultados de simulación](./resultados-iniciales.md)
- [Guía de reglamentos](./reglamentos-guia.md)
- [Ambigüedades](./ambiguedades.md)
- [Guía rápida del simulador](./guia-rapida.md)
