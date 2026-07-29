# Comparación v1 vs v2 · 3v3 y 4v4

Informe de simulación batch — **200 partidos** por celda · IA **estrategica** · julio 2026.

Reglamentos activos en el simulador: **v1** y **v2** (`reglamentos/indice.json`). **v0** y **v1.1** siguen en el repo como referencia histórica, pero no entran en `compare-reglamentos` ni en este informe.

```bash
python3 -m simulador compare-formatos --partidos 200 --ia estrategica
python3 -m simulador compare-reglamentos --partidos 200 --jugadores-por-equipo 3
```

---

## Tabla resumen

| Reg | Formato | Compl. | Goles | Turnos | Pen. | Pase% | Desp% | Robo% | Trampa | Marca |
|-----|---------|--------|-------|--------|------|-------|-------|-------|--------|-------|
| v1 | 3v3 | 99,0% | 4,03 | 179 | 35,0% | 40,3% | 15,8% | 19,1% | 4,38 | 7,49 |
| v2 | 3v3 | **100%** | 3,85 | **151** | **24,0%** | 44,6% | 16,3% | 22,4% | 7,15 | 11,95 |
| v1 | 4v4 | 98,0% | 3,86 | 212 | 26,0% | 40,6% | 12,1% | 22,4% | 5,55 | 10,06 |
| v2 | 4v4 | 97,0% | 3,85 | 219 | 29,5% | 43,8% | 13,0% | 26,4% | 12,61 | 20,93 |

---

## 1. v1 vs v2 (mismo formato)

### 3 vs 3 — **v2 gana en ritmo y cierre**

| | v1 | v2 | Δ |
|---|----|----|---|
| Completados | 99% | 100% | +1 pp |
| Turnos | 179 | 151 | **−16%** |
| Penales | 35% | 24% | −11 pp |
| Trampa + Marca / partido | ~12 | ~19 | +58% |
| Goles | 4,03 | 3,85 | −0,18 |

**Lectura:** en 3v3, v2 es más corto, cierra siempre, baja la tasa de 2-2 y hace mucho más trabajo Trampa/Marca (reactivas al **pase**, no al pasa de turno). El ritmo ofensivo sube (más pase y robo). Goles apenas bajan.

**Para mesa:** 3v3 + v2 parece el sweet spot de la simulación.

### 4 vs 4 — **empate en goles, v2 mucho más táctico**

| | v1 | v2 | Δ |
|---|----|----|---|
| Completados | 98% | 97% | −1 pp |
| Turnos | 212 | 219 | +3% |
| Penales | 26% | 30% | +4 pp |
| Trampa + Marca / partido | ~16 | **~34** | +113% |
| Goles | 3,86 | 3,85 | ≈0 |

**Lectura:** con más jugadores, v2 **no** acorta el partido respecto a v1 — ambos rondan ~210–220 turnos. v2 concentra el juego en pase → robo → trampa/marca encadenables: **el doble** de colocaciones Trampa+Marca que v1. Aparecen algunos empates técnicos en v2 (3%).

**Para mesa:** 4v4 + v2 puede sentirse denso o lento; validar si ~34 eventos Trampa/Marca por partido es demasiado.

---

## 2. 3v3 vs 4v4 (mismo reglamento)

### v1

| | 3v3 | 4v4 | Δ |
|---|-----|-----|---|
| Turnos | 179 | 212 | **+18%** |
| Penales | 35% | 26% | −9 pp |
| Goles | 4,03 | 3,86 | −0,17 |
| Robo % | 19% | 22% | +3 pp |

Más jugadores → partidos más largos, menos 2-2, ritmo de pase estable (~40%). La defensiva (robo) gana peso.

### v2

| | 3v3 | 4v4 | Δ |
|---|-----|-----|---|
| Turnos | 151 | 219 | **+45%** |
| Completados | 100% | 97% | −3 pp |
| Trampa + Marca | ~19 | **~34** | +79% |
| Penales | 24% | 30% | +6 pp |

**Hallazgo clave:** v2 **escala mal** a 4v4 en duración: de ~151 a ~219 turnos (+45%), pierde cierre perfecto y multiplica Trampa/Marca. En 3v3 v2 era el reglamento más ágil; en 4v4 pierde esa ventaja frente a v1.

---

## 3. Perfil de acciones (IA estratégica)

### v1 · 3v3
Pase 40% · Robo 19% · Despeje 16% · Disparo 9% · Pasa turno 9% · Falta 7%

### v2 · 3v3
Pase 45% · Robo 22% · Despeje 16% · Disparo 9% · Pasa turno 0% · Falta 8%

### v1 · 4v4
Pase 41% · Robo 22% · Despeje 12% · Disparo 9% · Pasa turno 9% · Falta 8%

### v2 · 4v4
Pase 44% · Robo 26% · Despeje 13% · Disparo 9% · Pasa turno 0% · Falta 8%

Sin pasa de turno, v2 redistribuye ese ~9% hacia pase/robo. En 4v4 el robo sube fuerte (26% en v2).

---

## 4. Conclusiones para playtesting

1. **Reglamento recomendado en simulación:** **v2 en 3v3** — cierra siempre, ~151 turnos, Trampa/Marca activas sin ser abrumadoras (~19 colocaciones/partido).
2. **v1 en 3v3** sigue viable — ~4 goles, un poco más lento y más penales; útil como baseline si querés pasa de turno en mesa.
3. **4v4 + v2** — revisar en mesa: Trampa/Marca al pase escalan mucho (~34/partido); partidos largos y algunos estancamientos.
4. **4v4 + v1** — ritmo intermedio; menos extremo que v2 en defensa situacional.
5. **v0** — no usar para evaluar el juego actual; conservar solo como archivo histórico.

---

## 5. Reproducir

```bash
# Matriz completa v1/v2 × 3v3/4v4
python3 -m simulador compare-formatos --partidos 200 --ia estrategica

# Solo un formato
python3 -m simulador compare-reglamentos --partidos 200 --jugadores-por-equipo 3
python3 -m simulador run --reglamento v2 --jugadores-por-equipo 4 --partidos 200
```

Sitio: [resultados.html](./resultados.html#compare-formatos) · Reglas: [reglamento-v1.md](./reglamento-v1.md) · [reglamento-v2.md](./reglamento-v2.md)
