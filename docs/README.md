# Documentación

Todo lo escrito del proyecto, ordenado por para qué se busca.

## Jugar

| Documento | Qué es |
|---|---|
| [reglamento-v1.md](reglamento-v1.md) | Las reglas completas de la versión en uso |
| [reglamento-v2.md](reglamento-v2.md) | Los cambios que se están probando |
| [reglamento-v1.1.md](reglamento-v1.1.md) | Una variante chica de v1 |
| [reglamento-v0.md](reglamento-v0.md) | El juego original, antes del playtesting |

## Usar el simulador

| Documento | Qué es |
|---|---|
| [guia-web.md](guia-web.md) | La interfaz, pantalla por pantalla |
| [guia-cli.md](guia-cli.md) | Todos los comandos de la terminal |
| [reglamentos-json.md](reglamentos-json.md) | El formato de un reglamento, campo por campo |
| [perfiles.md](perfiles.md) | Los estilos de juego con los que simula |

## Entender qué hace

| Documento | Qué es |
|---|---|
| [como-funciona.md](como-funciona.md) | Cómo resuelve un turno el motor, qué mide y qué no modela |
| [codigo.md](codigo.md) | Recorrido por el código, para leerlo o modificarlo |
| [ambiguedades.md](ambiguedades.md) | Reglas sin cerrar y supuestos que tuvo que tomar |

## Decidir

| Documento | Qué es |
|---|---|
| [resultados.md](resultados.md) | Qué dicen las simulaciones, con los comandos para reproducirlas |
| [recomendaciones.md](recomendaciones.md) | Qué conviene probar después, en mesa y en simulación |

---

## Cómo se trabaja

```
jugar en mesa  →  anotar qué molestó  →  escribir la regla nueva en la interfaz
      ↑                                              ↓
      └────  decidir con los números  ←  comparar contra la versión anterior
```

Cada versión del juego existe dos veces: como texto para leer entre todos
(`docs/reglamento-*.md`) y como archivo que lee el motor (`reglamentos/*.json`).
Conviene que las dos cambien juntas; el JSON tiene un campo `documento` que apunta
al texto correspondiente.

---

## El sitio

Esta carpeta también es un sitio web navegable —[index.html](index.html)— pensado
para compartir con quien no va a abrir una terminal: las reglas, los resultados y
un partido grabado para mirar.

Se publica solo con GitHub Pages: en **Settings → Pages** del repositorio, elegir
la rama `main` y la carpeta `/docs`. Cada vez que se sube un cambio, el sitio se
actualiza en un par de minutos. El archivo `.nojekyll` está para que se sirvan
todos los archivos tal cual.

El sitio no corre simulaciones: para eso hay que levantar el banco de pruebas en
la propia computadora con `python3 -m simulador web`.
