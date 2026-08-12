# El formato de un reglamento

Un reglamento es un archivo JSON en `reglamentos/`. Es lo único que el motor lee
para saber cómo se juega: el mazo, las manos, la tabla del dado, qué puede hacer
cada equipo. Cambiar el juego es cambiar este archivo.

Se puede editar de dos maneras, y son equivalentes:

- desde la interfaz (`python3 -m simulador web`, pestaña **Reglas**), que valida
  todo mientras se escribe;
- a mano con cualquier editor de texto, usando
  [`reglamentos/_plantilla.json`](../reglamentos/_plantilla.json) como base.

Para revisar que un archivo esté bien: `python3 -m simulador reglamentos <id>`.
Si algo está mal, el error dice qué y dónde.

---

## Ejemplo completo

```json
{
  "id": "v1",
  "nombre": "Iteración 1",
  "version": "1.0",
  "descripcion": "Qué cambia respecto de la versión anterior.",
  "documento": "docs/reglamento-v1.md",
  "activo": true,

  "mazo": {
    "Pase": 42, "Robo pelota": 24, "Gambetear": 15,
    "Disparo al arco": 12, "Falta": 7,
    "Marca personal": 5, "Trampa de offside": 3
  },

  "partido": {
    "jugadores_minimo_por_equipo": 2,
    "goles_para_ganar": 3,
    "penales_si_marcador": [2, 2],
    "limite_turnos": 500
  },

  "mano": { "inicial": 6, "maxima": 6 },
  "reposicion": { "momento": "cambio_equipo", "quien": "todos" },

  "disparo": {
    "rebote": true,
    "palo": true,
    "tabla": [
      { "pases": 0, "gol": [1, 1], "ataja": [2, 6] },
      { "pases": 1, "gol": [1, 2], "ataja": [3, 6] },
      { "pases": 2, "gol": [1, 3], "ataja": [4, 6] },
      { "pases": 3, "gol": [1, 4], "ataja": [5, 6] },
      { "pases": 4, "gol": [1, 5], "ataja": [6, 6] }
    ]
  },

  "acciones_ofensivas": ["pase", "disparo", "reventar", "pasa_turno"],

  "reacciones": {
    "pase":       { "cartas": ["Robo pelota"], "contra": { "Robo pelota": "Gambetear" } },
    "pasa_turno": { "cartas": ["Trampa de offside", "Marca personal"], "contra": {} }
  },

  "reglas": {
    "pasa_turno_sin_respuesta": "nada",
    "prob_falta_por_jugador": 0.08,
    "reacciones_encadenables": false
  }
}
```

---

## Campo por campo

### Identidad

| Campo | Qué es |
|---|---|
| `id` | Nombre del archivo y del reglamento (`v2` → `reglamentos/v2.json`). Letras, números, punto y guion. |
| `nombre` | Cómo se lo llama en las listas y los informes. |
| `version` | Ordena las listas: `1.0`, `1.1`, `2.0`. |
| `descripcion` | Qué cambia y por qué se probó. Aparece en la interfaz y en la terminal. |
| `documento` | Ruta a las reglas para jugar en mesa. Opcional. |
| `activo` | Si es `true`, entra por defecto en `comparar`. Las versiones viejas quedan en `false`. |
| `extends` | Hereda de otro reglamento (ver más abajo). |

### `mazo`

Cuántas copias de cada carta entran al mazo. Los nombres son los de las cartas
físicas y tienen que escribirse igual:

`Pase` · `Disparo al arco` · `Gambetear` · `La dejo pasar` · `Robo pelota` ·
`Corta pase` · `Tackle` · `Marca personal` · `Trampa de offside` · `Falta`

Es la palanca más directa del juego: subir `Disparo al arco` acorta los partidos,
bajar `Falta` los hace más fluidos, bajar `Robo pelota` favorece al ataque. Hay
mediciones de cada uno en [resultados.md](resultados.md).

Una carta que no está en el mazo no se puede usar en `reacciones`: el simulador
avisa si se pide algo así.

### `partido`

| Campo | Qué es |
|---|---|
| `jugadores_minimo_por_equipo` | Mínimo para que el reglamento tenga sentido (nunca menos de 2). |
| `goles_para_ganar` | El primero que llega, gana. |
| `penales_si_marcador` | Marcador que manda directo a penales, `[2, 2]` por ejemplo. Tiene que ser anterior a la victoria. |
| `limite_turnos` | Si se pasa, el partido se cuenta como **no definido**. Es el detector de reglas que traban el juego. |

### `mano` y `reposicion`

`mano.inicial` es cuánto reparte al empezar; `mano.maxima`, hasta dónde se
levanta después. Si son distintos, se arranca con menos cartas de las que se
pueden acumular.

`reposicion.momento` decide **cuándo** se levantan cartas:

| Valor | Cuándo |
|---|---|
| `cambio_equipo` | Cuando la pelota pasa de un equipo al otro (así juega v1 y v2). |
| `mano_vacia` | Cuando alguien se queda sin cartas (así jugaba v0). |
| `fin_de_turno` | Al terminar cada turno. |
| `al_jugar_carta` | Apenas se juega una carta, se repone esa carta. |
| `nunca` | No se repone: se juega hasta que se acaben las manos. |

`reposicion.quien` decide **quiénes** levantan: `todos`, `equipo_con_pelota`,
`equipo_sin_pelota` o `el_jugador` (el que gatilló el momento).

Si el mazo se termina, se baraja el descarte y se sigue.

### `disparo`

La tabla es el corazón del juego: cuántos números hacen gol y cuántos ataja el
arquero, según los pases encadenados antes del remate.

```json
{ "pases": 2, "gol": [1, 3], "ataja": [4, 6] }
```

Con dos pases hechos, el pateador convierte sacando 1, 2 o 3, y el arquero ataja
sacando 4, 5 o 6. Los valores van de 1 a 6. La última franja también vale para
cualquier cantidad mayor de pases.

- `rebote`: si el pateador saca número de gol **y** el arquero de atajada, se
  vuelve a patear.
- `palo`: si los dos dados salen iguales, se vuelve a patear.

### `acciones_ofensivas`

Qué puede hacer quien tiene la pelota:

| Acción | Gasta carta | Qué hace |
|---|---|---|
| `pase` | `Pase` | La pelota va a un compañero y suma un pase a la jugada. |
| `disparo` | `Disparo al arco` | Se resuelve el remate con la tabla. |
| `reventar` | — | Duelo de dados entre los dos equipos por la pelota. |
| `pasa_turno` | — | Se queda la pelota sin hacer nada; le da pie a la defensa a poner trampas. |

Tiene que quedar habilitada `reventar` o `pasa_turno`: son las únicas que no
gastan carta, y sin alguna de las dos el ataque podría quedarse sin jugada legal.

### `reacciones`

Con qué cartas responde la defensa, según lo que hizo el ataque:

```json
"pase": {
  "cartas": ["Robo pelota", "Trampa de offside", "Marca personal"],
  "contra": { "Robo pelota": "Gambetear" }
}
```

- `cartas`: lo que la defensa puede jugar en ese momento. Solo una carta por
  acción del ataque, en todo el equipo.
- `contra`: con qué carta el ataque la anula. La contra la juega quien la tenga:
  el que tiene la pelota o el receptor del pase.

Hay dos contextos: `pase` y `pasa_turno`. Poner `Marca personal` y
`Trampa de offside` en uno o en otro es exactamente la diferencia entre v1 y v2.

Las trampas (`Marca personal`, `Trampa de offside`) no cortan la jugada: quedan
puestas y se cobran en el **próximo** pase del ataque. Como se cobran ahí, su
contra se declara en el contexto `pase`.

### `reglas`

| Campo | Qué hace |
|---|---|
| `pasa_turno_sin_respuesta` | Qué pasa si el ataque pasa de turno y la defensa no juega nada: `nada` o `pasa_companero`. |
| `prob_falta_por_jugador` | Chance de que un jugador con `Falta` en la mano la juegue en un turno dado (0 a 1). Con 0 la carta queda inerte. |
| `reacciones_encadenables` | Si es `true`, después de una contra la defensa puede volver a responder mientras le queden cartas. |

---

## Heredar de otro reglamento

Para probar un cambio chico no hace falta copiar todo el archivo:

```json
{
  "id": "v2.1",
  "nombre": "v2 con más disparos",
  "extends": "v2",
  "version": "2.1",
  "descripcion": "Igual que v2 pero con 18 copias de Disparo al arco.",
  "mazo": {
    "Pase": 42, "Robo pelota": 24, "Gambetear": 15,
    "Disparo al arco": 18, "Falta": 7,
    "Marca personal": 5, "Trampa de offside": 3
  }
}
```

Qué se hereda y qué se reemplaza:

- **Se completa lo que falta** en `partido`, `mano`, `reposicion`, `disparo` y
  `reglas`: se puede cambiar un solo campo y el resto viene del padre.
- **Se reemplaza entero** el `mazo`, las `acciones_ofensivas` y las `reacciones`.
  Es a propósito: si el mazo se fusionara, sacar una carta sería imposible.

Cuando se guarda desde la interfaz un reglamento que hereda, el archivo queda con
las diferencias nada más.

---

## Errores frecuentes

El simulador valida todo antes de correr y explica qué está mal:

| Mensaje | Qué pasó |
|---|---|
| `clave desconocida: 'x'` | Un campo mal escrito o de un formato viejo. |
| `Carta desconocida: 'X'` | El nombre de la carta no coincide con el impreso. |
| `el mazo (N) no alcanza para repartir` | Faltan cartas para las manos iniciales. |
| `el ataque se puede quedar sin jugada` | Ni `reventar` ni `pasa_turno` están habilitados. |
| `la defensa reacciona con X pero no hay copias en el mazo` | Una reacción usa una carta ausente. |
| `rango gol inválido` | La tabla de disparo se salió del 1–6. |
| `penales_si_marcador debe ser un marcador anterior a la victoria` | Ese marcador no se puede alcanzar nunca. |
