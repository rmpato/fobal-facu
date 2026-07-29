# Guía rápida del simulador

Todo lo necesario para correr simulaciones, leer resultados y comparar reglamentos.  
Para el detalle del motor → [como-funciona-simulacion.md](./como-funciona-simulacion.md).

---

## Instalación

```bash
git clone https://github.com/rmpato/fobal-facu.git
cd fobal-facu
python3 --version   # 3.11 o superior
```

No hay dependencias externas.

---

## Comandos esenciales

### Correr partidos

```bash
# 200 partidos, reglamento v1, IA estratégica (default)
python3 -m simulador run --reglamento v1 --partidos 200

# Ver un partido turno a turno
python3 -m simulador run --reglamento v1 --partidos 1 --verbose
```

### Reglamentos

```bash
# Listar todos
python3 -m simulador reglamentos list

# Ver qué reglas aplica uno (mazo, victoria, reacciones…)
python3 -m simulador reglamentos show v1
python3 -m simulador reglamentos show v1.1
```

### Comparar versiones

```bash
# Todos los reglamentos del índice (v0, v1, v1.1…)
python3 -m simulador compare-reglamentos --partidos 200

# Solo v0 vs v1
python3 -m simulador compare --partidos 200

# Variantes desde configs/variantes.json
python3 -m simulador variantes --partidos 500
```

---

## Reglamentos implementados

| Id | Nombre | Motor | Reglas en mesa |
|----|--------|-------|----------------|
| `v0` | Reglamento original | [v0.json](../reglamentos/v0.json) | [reglamento-v0.md](./reglamento-v0.md) |
| `v1` | Iteración 1 (playtesting) | [v1.json](../reglamentos/v1.json) | [reglamento-v1.md](./reglamento-v1.md) |
| `v1.1` | Pasa al compañero *(extiende v1)* | [v1.1.json](../reglamentos/v1.1.json) | [reglamento-v1.1.md](./reglamento-v1.1.md) |
| `v2` | Iteración 2 (playtesting) | [v2.json](../reglamentos/v2.json) | [reglamento-v2.md](./reglamento-v2.md) |

**Diferencias clave:**

- **v0** — Corta pase, Tackle, La dejo pasar, **pasa de turno** (decisión, no carta); reposición cuando la mano queda vacía.
- **v1** — Robo pelota, Reventar la pelota, rebote/palo en disparos; Trampa/Marca solo en pasa de turno; reposición al cambiar de equipo.
- **v1.1** — Igual que v1, pero pasa de turno sin respuesta defensiva → la pelota pasa a un compañero.

```bash
python3 -m simulador reglamentos list
python3 -m simulador reglamentos show v1
python3 -m simulador run --reglamento v1.1 --partidos 200
```

Crear reglamento nuevo → [reglamentos-guia.md](./reglamentos-guia.md).

---

## Leer la salida

Cada reporte incluye:

1. **Reglamento** usado (id, nombre, documento).
2. **Reglas aplicadas** (lista explícita).
3. **Resultados:** victorias, empates técnicos (>500 turnos), penales, goles/turnos promedio.
4. **Acciones en %** — comparar con partidas reales en mesa.
5. **Cartas jugadas** — detectar dominancia o cartas muertas.

### Métricas clave

| Métrica | Qué indica |
|---------|------------|
| **Completados** | % partidos con ganador (no empate técnico) |
| **Empates técnicos** | Posible estancamiento de reglas |
| **Goles / partido** | Ritmo del juego |
| **Penales** | Cuántos llegan a 2-2 |
| **Pase / Despeje / Disparo %** | Perfil de juego |

Interpretación y señales de alerta → [como-funciona-simulacion.md](./como-funciona-simulacion.md#cómo-interpretar-resultados).

---

## Opciones útiles

| Flag | Default | Descripción |
|------|---------|-------------|
| `--reglamento` | `v1` | Id (`v0`, `v1`, `v1.1`) o ruta a `.json` |
| `--partidos` | `100` | Cuántos partidos simular |
| `--ia` | `estrategica` | Perfil de IA (ver tabla abajo) |
| `--jugadores-por-equipo` | `3` | Mínimo 2 (simulaciones batch usan 3 vs 3) |

Documentación completa de IA → **[perfiles-ia.md](./perfiles-ia.md)**.

### IA clásica (la del análisis original)

| Flag | Nombre | Uso |
|------|--------|-----|
| `--ia estrategica` | **Táctico** | Default. Usado en [resultados-iniciales.md](./resultados-iniciales.md). |
| `--ia simple` | **Directo** | Baseline histórico; casi no pasa de turno. |

### IA adicional (desde 2026)

También disponibles: `agresiva`, `paciente`, `gambler`, `conservador`, `adaptativo`, `marcador`, `contragolpista`. Nombres en UI y cuándo usar cada uno → [perfiles-ia.md](./perfiles-ia.md).

En modo espectador podés mezclar equipos:

```bash
python3 -m simulador ver --ia-equipo0 agresiva --ia-equipo1 conservador
```

Para comparaciones justas entre reglamentos, usá el mismo `--ia` en todas las corridas.

---

## Variantes vs reglamentos

| Concepto | Cuándo usar |
|----------|-------------|
| **Reglamento** (`v1`, `v1.1`, `v2`) | Cambio formal de reglas del juego |
| **Variante** (`configs/variantes.json`) | Experimento rápido sin crear reglamento nuevo |

Ejemplo: `v1.1` ya es el reglamento formal para “pasa al compañero si nadie reacciona al pasa de turno”. La variante en JSON sirve para probar lo mismo sobre v1 sin crear archivo.

---

## Dónde están las conclusiones

No hace falta correr nada para leer el análisis:

- **Números y corridas:** [resultados-iniciales.md](./resultados-iniciales.md)
- **Qué probar next:** [recomendaciones-diseno.md](./recomendaciones-diseno.md)
- **Supuestos del motor:** [ambiguedades.md](./ambiguedades.md)

---

## Estructura del código

```
simulador/
  __main__.py      CLI (run, compare, reglamentos, variantes)
  reglamento.py    Carga reglamentos JSON
  motor.py         Reglas del partido (turnos, goles, penales)
  ia.py            Decisiones ofensivas/defensivas
  estadisticas.py  Agrega y formatea resultados
  config.py        Config de corrida + variantes
  cartas.py        Tipos de carta y tablas de disparo
  modelo.py        Estado del partido

reglamentos/       v0.json, v1.json, v1.1.json, indice.json
configs/           variantes.json
```

Flujo de un turno y limitaciones → [como-funciona-simulacion.md](./como-funciona-simulacion.md).
