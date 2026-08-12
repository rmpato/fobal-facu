# Documentación — Fobal Facu

Guía de qué leer según lo que necesites. El README del repo tiene el [quickstart](../README.md).

---

## Si querés…

| Objetivo | Documento |
|----------|-----------|
| **Elegir / comparar perfiles de IA** | [perfiles-ia.md](./perfiles-ia.md) |
| **Correr simulaciones ya** | [guia-rapida.md](./guia-rapida.md) |
| **Comparar v1 vs v2 (3v3 / 4v4)** | [comparacion-v1-v2-formatos.md](./comparacion-v1-v2-formatos.md) |
| **Ver conclusiones y números** | [resultados-iniciales.md](./resultados-iniciales.md) |
| **Saber qué cambiar en el juego** | [recomendaciones-diseno.md](./recomendaciones-diseno.md) |
| **Entender el motor por dentro** | [como-funciona-simulacion.md](./como-funciona-simulacion.md) |
| **Crear reglamento v1.2 / v2** | [reglamentos-guia.md](./reglamentos-guia.md) |
| **Jugar en mesa (reglas humanas)** | [reglamento-v1.md](./reglamento-v1.md) · [reglamento-v0.md](./reglamento-v0.md) |
| **Reglas ambiguas / supuestos** | [ambiguedades.md](./ambiguedades.md) |
| **Publicar el sitio web** | [GITHUB_PAGES.md](./GITHUB_PAGES.md) *(opcional)* |

---

## Flujo de trabajo recomendado

1. Leer [resultados-iniciales.md](./resultados-iniciales.md) (conclusiones).
2. Correr `python3 -m simulador compare-reglamentos --partidos 200` (reproducir o actualizar).
3. Discutir en mesa → proponer cambio → nuevo reglamento JSON (ver [reglamentos-guia.md](./reglamentos-guia.md)).
4. Comparar de nuevo → documentar en resultados o recomendaciones.

---

## Reglamentos implementados

| Id | Nombre | Reglas en mesa | Motor |
|----|--------|----------------|-------|
| `v0` | Reglamento original | [reglamento-v0.md](./reglamento-v0.md) | [v0.json](../reglamentos/v0.json) |
| `v1` | Iteración 1 (playtesting) | [reglamento-v1.md](./reglamento-v1.md) | [v1.json](../reglamentos/v1.json) |
| `v1.1` | Pasa al compañero *(extiende v1)* | [reglamento-v1.1.md](./reglamento-v1.1.md) | [v1.1.json](../reglamentos/v1.1.json) |
| `v2` | Iteración 2 (playtesting) | [reglamento-v2.md](./reglamento-v2.md) | [v2.json](../reglamentos/v2.json) |

`v1` es el default del simulador. `v1.1` solo cambia qué pasa si nadie reacciona al pasa de turno.

```bash
python3 -m simulador reglamentos list
python3 -m simulador compare-reglamentos --partidos 200
```

Nuevo reglamento → [reglamentos-guia.md](./reglamentos-guia.md).

---

## Sitio HTML

Versión navegable (mismos contenidos, más visual): [index.html](./index.html).  
No reemplaza esta carpeta MD — es complemento para compartir con el grupo.
