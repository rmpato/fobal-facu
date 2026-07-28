# Perfiles de IA

El simulador no juega en mesa por vos: usa **perfiles de IA** que eligen acciones ofensivas (pase, disparo, pasa de turno, reventar) y reacciones defensivas (robo, trampa, marca, etc.) según probabilidades y heurísticas.

Implementación: [`simulador/ia.py`](../simulador/ia.py).

Para correr simulaciones → [guia-rapida.md](./guia-rapida.md). Para el flujo del motor → [como-funciona-simulacion.md](./como-funciona-simulacion.md).

---

## Perfiles clásicos (desde el inicio del proyecto)

Estos dos perfiles existían **antes** de agregar los estilos nuevos. Son los que aparecen en [resultados-iniciales.md](./resultados-iniciales.md) y en casi todas las comparaciones publicadas hasta jul 2026.

| Flag CLI | Nombre en UI | Rol |
|----------|--------------|-----|
| `--ia simple` | **Directo** | Baseline histórico: decisiones mayormente aleatorias, **casi no usa pasa de turno**. Sirve para ver por qué v1 parecía estancarse y por qué Trampa/Marca no se evaluaban bien. |
| `--ia estrategica` | **Táctico** | **Default del simulador.** Pasa de turno a propósito, arma cadenas de pase antes de disparar, defiende activo, evita pasar al jugador marcado. Es el perfil usado en las corridas “IA estratégica” del análisis de balance. |

```bash
# Comparación histórica reproducible
python3 -m simulador run --reglamento v1 --partidos 200 --ia simple
python3 -m simulador run --reglamento v1 --partidos 200 --ia estrategica
```

**Importante:** al comparar reglamentos (`compare`, `compare-reglamentos`, `variantes`), usá **el mismo** `--ia` en todas las corridas. Los números de `resultados-iniciales.md` asumen `--ia estrategica` salvo donde se indica “IA simple”.

---

## Perfiles disponibles (lista completa)

| Flag CLI | Nombre en UI | Estilo resumido |
|----------|--------------|-----------------|
| `simple` | Directo | Aleatorio, poco pasa de turno *(clásico)* |
| `estrategica` | Táctico | Cadena de pases, trampa/marca, defensa activa *(clásico, default)* |
| `agresiva` | Presionante | Dispara antes, defiende fuerte, casi no pasa de turno |
| `paciente` | Posicional | Muchos pases, espera cadena larga, usa pasa de turno para armar trampa/marca |
| `gambler` | Arriesgado | Alta varianza, más reventar y decisiones impredecibles |
| `conservador` | Conservador | Mucho pase, pocos disparos hasta cadena ≥ 4, defensa cautelosa |
| `adaptativo` | Adaptativo | **Dinámico:** si va perdiendo → Presionante; si va ganando → Conservador; empate → Táctico |
| `marcador` | Marcador | Prioriza colocar marca personal y atraer pases al marcado |
| `contragolpista` | Contragolpista | Dispara/revierte rápido al inicio de la posesión (`pases_en_jugada` bajo) |

Listado en terminal:

```bash
python3 -m simulador run --help    # tabla de --ia
python3 -m simulador ver --help     # incluye --ia-equipo0 / --ia-equipo1
```

---

## Cómo usar `--ia`

### Mismo perfil para ambos equipos (lo habitual en batch)

```bash
python3 -m simulador run --reglamento v1 --partidos 200 --ia paciente
python3 -m simulador compare-reglamentos --partidos 200 --ia estrategica
python3 -m simulador compare --partidos 200 --ia agresiva
```

Comandos que aceptan `--ia`:

| Comando | `--ia` | Notas |
|---------|--------|-------|
| `run` | sí | Simulación en lote |
| `compare` | sí | v0 vs v1 |
| `compare-reglamentos` | sí | Todos los reglamentos del índice |
| `ver` | sí | Modo espectador (ver abajo) |
| `variantes` | vía JSON | Perfil en `configs/variantes.json` → campo `"ia"` |

### Perfil distinto por equipo (solo `ver`)

Útil para ver en el espectador dos estilos enfrentados:

```bash
python3 -m simulador ver --semilla 42 \
  --ia-equipo0 agresiva \
  --ia-equipo1 conservador
```

- `--ia` sigue siendo el default si no pasás override de equipo.
- `--ia-equipo0` / `--ia-equipo1` aplican solo al equipo 1 y 2 respectivamente.
- En el panel **Anticipo IA** del espectador se muestra `E1: …` / `E2: …` cuando difieren.

`adaptativo` se resuelve **en vivo** según el marcador (no hace falta otro flag).

---

## Modo espectador (`ver`)

Además de elegir IA por CLI, el espectador muestra un panel **Anticipo IA** (debajo de “Últimas x4”):

- Reglamento activo (`v0`, `v1`, `v1.1`, …)
- Nombre del perfil (p. ej. **Táctico**, **Presionante**)
- Probabilidades aproximadas de la próxima acción del portador y reacciones defensivas posibles

Es una **pista**, no una predicción exacta: la IA sigue usando azar.

```bash
# Espectador con IA Posicional
python3 -m simulador ver --semilla 42 --pausa 3 --ia paciente

# Rich / Textual (requiere venv con rich + textual)
python3 -m simulador ver --semilla 42 --ui textual --ia marcador
```

---

## Cuál elegir

| Objetivo | Perfil sugerido |
|----------|-----------------|
| Reproducir análisis del repo | `estrategica` (Táctico) |
| Baseline “sin táctica” | `simple` (Directo) |
| Partidos más goleadores / rápidos | `agresiva`, `gambler`, `contragolpista` |
| Partidos largos, muchas trampas | `paciente`, `marcador` |
| Simular “cerrar el partido” | `conservador`, `adaptativo` |
| Experimento visual 1 vs 1 | `ver --ia-equipo0 X --ia-equipo1 Y` |

Los perfiles nuevos **no** reemplazan a los clásicos: son complementos para explorar estilos. Las conclusiones de balance en `resultados-iniciales.md` siguen referidas a **Directo** vs **Táctico**.

---

## Relación con variantes JSON

En [`configs/variantes.json`](../configs/variantes.json) cada variante puede fijar `"ia": "estrategica"` (u otro id válido). Eso no crea un perfil nuevo: elige uno de la tabla anterior.

---

## Ver también

- [guia-rapida.md](./guia-rapida.md) — comandos y flags
- [como-funciona-simulacion.md](./como-funciona-simulacion.md) — turnos, métricas, limitaciones
- [resultados-iniciales.md](./resultados-iniciales.md) — números con IA clásica
