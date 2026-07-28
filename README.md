# fobal-facu

Simulador de partidos para un juego de cartas de fútbol creado en familia.  
Las **reglas y cartas están en español (Argentina)**; el código y esta intro van en inglés/español mixto para que ambos puedan usar el repo.

## Qué hay acá

| Carpeta / archivo | Contenido |
|-------------------|-----------|
| [`docs/reglamento-v0.md`](docs/reglamento-v0.md) | Reglas originales + mazo |
| [`docs/reglamento-v1.md`](docs/reglamento-v1.md) | Iteración 1 post playtesting + mazo |
| [`docs/proceso.md`](docs/proceso.md) | Cómo usamos la simulación para iterar |
| [`docs/ambiguedades.md`](docs/ambiguedades.md) | Reglas poco claras y supuestos del motor |
| [`docs/resultados-iniciales.md`](docs/resultados-iniciales.md) | Hallazgos de simulación, métricas, impacto de reglas |
| [`docs/index.html`](docs/index.html) | **Sitio web** para GitHub Pages (reglas + resultados) |
| [`simulador/`](simulador/) | Motor Python (v0 y v1) + IA simple |

## Requisitos

- Python 3.11+ (solo biblioteca estándar)

## Uso rápido

```bash
cd fobal-facu

# 100 partidos con reglas v1, 2 vs 2
python -m simulador run --reglas v1 --partidos 100

# Reglas originales (v0)
python -m simulador run --reglas v0 --partidos 100

# Comparar ambas versiones
python -m simulador compare

# Ver un partido turno a turno
python -m simulador run --reglas v1 --partidos 1 --verbose
```

## Sitio web (GitHub Pages)

Hay una página estática en [`docs/index.html`](docs/index.html) con reglas, mazos y resultados — pensada para compartir con el grupo.

**Publicar:** GitHub → Settings → Pages → Branch `main` → folder `/docs`.

Instrucciones completas: [`docs/GITHUB_PAGES.md`](docs/GITHUB_PAGES.md).

URL final: `https://TU_USUARIO.github.io/fobal-facu/`

## Versiones del juego

### v0 — mazo original

Pase, Corta pase, Tackle, Disparo al arco, Falta, Gambetear, La dejo pasar, Marca personal, Trampa de offside.

Mecánicas clave: **ceder el turno**, corte de pase vs **La dejo pasar**, tackle vs **Gambetear**.

### v1 — iteración 1

Pase, Robo pelota, Disparo al arco, Falta, Gambetear, Marca personal, Trampa de offside.

Cambios: **Reventar la pelota** (despeje), robo unificado, una sola reacción defensiva por carta ofensiva, rebote/palo en disparos, reposición al cambiar de equipo.

## Próximos pasos

- [x] Documentar hallazgos de simulación → [resultados-iniciales.md](./docs/resultados-iniciales.md)
- [ ] Validar supuestos con el grupo de playtesting
- [ ] Discutir estancamiento de **pasa de turno** en v0 (ver resultados)
- [ ] IA que use pasa de turno estratégicamente (evaluar Trampa/Marca)
- [ ] Modo interactivo para humanos vs bots

## Licencia

Uso privado / familiar — a definir.
