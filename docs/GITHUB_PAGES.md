# Publicar el sitio

El sitio público sale de esta carpeta: **Settings → Pages → rama `Fobal3`,
carpeta `/docs`**. Cada push actualiza el sitio en un par de minutos.

## Qué hay

| Archivo | Qué es |
|---|---|
| `index.html` | La página principal: el juego, el mazo, la tabla del dado, un partido y los datos |
| `reglas.html` | Las reglas completas para jugar |
| `assets/css/estilo.css` · `assets/js/sitio.js` | Todo el diseño y la interacción, sin dependencias |
| `replays/partido.json` | El partido que se reproduce en la página |

## Actualizar el partido de ejemplo

```bash
python3 -m simulador ver --reglamento v2 --semilla 138 --sin-pausa \
    --equipo1 Facu Pato Manu --equipo2 Colo Ostu Joaco \
    --grabar docs/replays/partido.json
```

## Actualizar los números

Los de la sección «Los datos» salen de:

```bash
python3 -m simulador compare-formatos --partidos 300
```

Están escritos a mano en `index.html`: si se vuelven a correr las
simulaciones, hay que actualizarlos ahí.

## No aparece en buscadores

Todas las páginas llevan `noindex`. La dirección es pública, pero hay que
conocerla.
