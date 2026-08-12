# Qué dicen las simulaciones

Todos los números de esta página salen de correr el simulador con los reglamentos
que están en el repositorio. Cada tabla trae el comando que la reproduce: corrido
de nuevo, da exactamente lo mismo.

**Cómo leerlos.** Son comparaciones entre versiones del juego, no predicciones de
una partida concreta. Una diferencia de veinte turnos es señal; una de dos, ruido.
Lo que el simulador no modela —engaño, presión social, olvidos— está anotado en
[como-funciona.md](como-funciona.md#qué-no-modela).

---

## v1 contra v2

```bash
python3 -m simulador comparar v1 v2 --formatos 3 4 --partidos 500
```

| Reglamento | Formato | Se definen | Goles | Turnos | Penales | Pase | Robo | Disparo |
|---|---|---|---|---|---|---|---|---|
| v1 | 3 vs 3 | 98,4 % | 3,98 | 189 | 32,4 % | 42 % | 16 % | 8 % |
| **v2** | **3 vs 3** | **99,6 %** | **3,87** | **171** | **26,8 %** | 47 % | 19 % | 9 % |
| v1 | 4 vs 4 | 96,2 % | 3,88 | 230 | 27,6 % | 42 % | 18 % | 7 % |
| v2 | 4 vs 4 | 95,8 % | 3,84 | 232 | 26,4 % | 46 % | 22 % | 7 % |

### En 3 vs 3, v2 es más ágil

Dura un 10 % menos (171 turnos contra 189), casi nunca queda trabado (99,6 %) y
llega a penales bastante menos seguido (26,8 % contra 32,4 %). Los goles quedan
igual.

La explicación está en el reparto: sacar el pasa de turno —que en v1 se llevaba
casi un 10 % de las jugadas— empuja ese tiempo hacia el pase y el robo. Se juega
más y se espera menos.

### En 4 vs 4 la ventaja desaparece

Con cuatro por equipo los dos reglamentos dan lo mismo (230 y 232 turnos) y los
dos empeoran: los partidos se alargan un 35 % y aparecen empates por límite de
turnos. Con más jugadores hay más manos, más cartas defensivas en juego y más
formas de cortar cada avance.

En 5 vs 5 el efecto se dispara: 299 turnos y solo 85 % de partidos definidos.

```bash
python3 -m simulador comparar v2 --formatos 2 3 4 5 --partidos 300
```

**Para la mesa:** 3 vs 3 es el formato en el que el juego está afinado. Si se
juega de a cuatro o cinco, conviene subir los goles necesarios o acortar el mazo,
porque el partido se hace largo.

---

## La marca personal casi nunca recupera la pelota

Es el hallazgo más útil para el diseño del mazo.

```bash
python3 -m simulador simular v2 --partidos 300
```

| Escenario | Marcas puestas | Recuperan la pelota | Desvían un pase |
|---|---|---|---|
| v2 · 3 vs 3 · Táctico | 14,8 | **0,00** | 13,4 |
| v1 · 3 vs 3 · Táctico | 8,7 | **0,00** | 8,9 |
| v2 · 2 vs 2 · Táctico | 12,2 | 2,52 | — |
| v2 · 3 vs 3 · Marcador | 20,4 | 11,81 | 2,2 |

Contra un ataque atento, la marca **no recupera nunca** la pelota: alcanza con
pasarle a otro. En 3 vs 3 siempre hay un compañero libre, así que marcar equivale
a tapar una de las dos opciones de pase. Solo empieza a cobrarse cuando el ataque
se queda sin alternativas (2 vs 2) o cuando alguien insiste en pasarle al marcado
(perfil Marcador, que es el techo teórico de la carta).

Eso no la vuelve una carta muerta: desvía trece pases por partido, y esos pases
van al receptor que la defensa eligió dejar libre. Pero es una carta de
**condicionamiento**, no de robo, y hoy el reglamento la presenta como si
recuperara la pelota.

La trampa de offside, en cambio, sí se cobra: se ponen 8,8 por partido y 4,7
terminan en offside, más de la mitad.

**Para la mesa:** ver si en la práctica se siente así. Si la marca decepciona,
hay tres caminos: que impida el pase a *cualquier* jugador durante un turno, que
cueste algo ponerla, o que se cobre aunque el ataque la esquive.

---

## v0 se traba: por qué existe v1

```bash
python3 -m simulador simular v0 --partidos 300
```

**Ningún partido de v0 se define.** Los 300 llegan al límite de turnos con un
promedio de 0,38 goles, y el 96 % de las jugadas son *pasar de turno*.

El motivo es la combinación de dos reglas: en v0 solo se reponen cartas cuando
alguien se queda sin ninguna, y pasar de turno no gasta carta. Cuando un jugador
se queda sin `Pase` puede quedarse quieto para siempre; nunca vacía la mano, nunca
repone, y el partido no avanza.

Es exactamente el problema que la iteración v1 resolvió, con dos cambios:
reponer al cambiar de equipo y agregar *reventar la pelota* como salida sin carta.
Vale como recordatorio de que el simulador encuentra este tipo de agujeros en
segundos, mientras que en la mesa se sienten como «una partida rara».

---

## Qué le hace cada palanca al juego

Todos estos cambios se hacen desde la pestaña **Reglas** de la interfaz, sin tocar
código. Base: v2, 3 vs 3, 300 partidos.

| Cambio | Se definen | Goles | Turnos | Penales | Disparo |
|---|---|---|---|---|---|
| *(v2 sin cambios)* | 99,3 % | 3,88 | 172 | 27,0 % | 8,5 % |
| `Disparo al arco` 12 → 18 | 99,7 % | 3,89 | **149** | 26,7 % | 10,8 % |
| `Falta` 7 → 3 | 100 % | 3,91 | **142** | 27,3 % | 9,3 % |
| `Robo pelota` 24 → 18 | 99,7 % | 3,97 | **145** | 31,0 % | 9,5 % |
| Mano de 6 → 8 cartas | 99,3 % | 3,81 | **197** | 23,3 % | 8,5 % |
| Reponer al jugar cada carta | 100 % | 3,86 | 174 | 27,3 % | 8,4 % |

Lo que se aprende:

- **Sacar cuatro `Falta` es el cambio más efectivo para acortar**: −30 turnos
  (−17 %) sin tocar nada más. Cada falta corta la jugada y devuelve el contador de
  pases a cero, así que su costo real es mayor que su frecuencia.
- **Más `Disparo al arco` acorta sin subir los goles**: se remata más seguido pero
  con jugadas más cortas, que la tabla castiga. Sube el ritmo, no el marcador.
- **Menos `Robo pelota` acorta y empata más**: el ataque llega mejor, los dos
  equipos convierten y aumentan los 2-2.
- **Manos más grandes alargan el partido**: con ocho cartas siempre hay con qué
  responder, y cada avance cuesta más. Es la palanca opuesta a bajar las faltas.
- **Cuándo se reponen las cartas casi no mueve la aguja** mientras se reponga
  seguido; lo que sí importa es que se reponga (comparar con v0).

---

## Los dos equipos ganan lo mismo

Control de sanidad: con el mismo perfil en los dos lados, las victorias reparten
parejo (48 % contra 52 % en 500 partidos de v2). Ni el equipo que arranca con la
pelota ni el orden de los jugadores dan ventaja.

---

## Reproducir todo

```bash
python3 -m simulador comparar v1 v2 --formatos 3 4 --partidos 500
python3 -m simulador simular v0 --partidos 300
python3 -m simulador simular v2 --partidos 300 --perfil marcador
```

Las mismas tandas se corren desde la interfaz, en la pestaña **Simular**, y se ven
con gráficos: `python3 -m simulador web`.

Qué conviene probar después de esto: [recomendaciones.md](recomendaciones.md).
