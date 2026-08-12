# Cómo funciona la simulación

El simulador juega partidos de verdad: reparte cartas, las gasta, tira los dados y
respeta el reglamento que se le indique. No estima con fórmulas ni con
probabilidades: por eso los números salen del juego y no de un modelo aparte.

```
reglamento (JSON) → repartir → turno, turno, turno… → final → métricas
```

---

## Un turno

Cada turno lo juega quien tiene la pelota. La secuencia es siempre la misma, y lo
que cambia entre versiones del juego es qué está permitido en cada paso.

**1. Falta.** Cualquiera de los dos equipos puede jugar `Falta` y cortar la
jugada. La pelota se queda en el mismo equipo y el contador de pases vuelve a
cero. El reglamento fija con qué frecuencia pasa (`prob_falta_por_jugador`: la
chance de que un jugador que tiene la carta la juegue en ese turno).

**2. La acción del ataque.** El que tiene la pelota elige entre lo que el
reglamento permite y lo que tiene en la mano:

| Acción | Cómo se resuelve |
|---|---|
| **Pase** | Elige un compañero, gasta la carta `Pase`, y si la jugada prospera suma un pase a la cadena. |
| **Disparo al arco** | Gasta `Disparo al arco`. Pateador y arquero tiran un dado y se resuelve con la tabla del reglamento, según cuántos pases traía la jugada. |
| **Reventar la pelota** | Sin carta. Un jugador de cada equipo —nunca el que reventó— tira un dado: el más alto se queda con la pelota. Si la gana el mismo equipo, cuenta como pase. |
| **Pasar de turno** | Sin carta. Se queda con la pelota sin hacer nada, y le da a la defensa la chance de poner trampas. |

**3. Las trampas puestas de antes.** Si la defensa había armado la trampa de
offside, el pase es offside y la pelota cambia de manos. Si el receptor estaba
marcado, la marca se cobra. Las dos se gastan al dispararse, y en algunos
reglamentos el ataque las puede anular (`La dejo pasar`).

**4. La respuesta de la defensa.** Una carta por acción del ataque, en todo el
equipo. Puede cortar la jugada (`Robo pelota`, `Corta pase`, `Tackle`) o dejar
puesta una trampa para el próximo pase (`Marca personal`, `Trampa de offside`).
El ataque puede anular el corte con su contra (`Gambetear`). Si el reglamento
permite encadenar, la defensa puede volver a responder mientras le queden cartas.

**5. Dónde queda la pelota.** Si cambió de equipo, se limpian las trampas y el
contador de pases vuelve a cero.

**6. Reposición.** Según el reglamento, se levantan cartas hasta el máximo de
mano. Si el mazo se acaba, se baraja el descarte y se sigue.

## Un partido

Se reparten las manos iniciales, se sortea qué equipo arranca y se juegan turnos
hasta que pase una de tres cosas:

- **Un equipo llega a los goles necesarios.** Gana.
- **El marcador toca el valor de penales** (2-2 en las versiones actuales). Se
  define ahí mismo: una tanda de tantos penales como jugadores por equipo y, si
  siguen iguales, muerte súbita.
- **Se agota el límite de turnos.** El partido queda **sin definir**. No es una
  regla de mesa: es el detector de reglas que traban el juego. Cuando ese número
  sube, hay algo en el reglamento que permite dar vueltas sin avanzar nunca.

---

## Quién decide

El motor calcula qué es legal; **quién decide es un perfil de juego**. Un perfil
es un conjunto de tendencias —cuánto le gusta disparar, cuánto arriesga en
defensa, cuánto guarda las contras— que se traduce en pesos para cada opción
disponible.

Como el perfil cambia los resultados tanto como una regla, las comparaciones se
corren siempre con el mismo perfil en los dos equipos. La lista completa está en
[perfiles.md](perfiles.md).

---

## Semillas: por qué los números son repetibles

Cada partido tiene un número de semilla del que sale todo su azar: la mezcla del
mazo, los dados, las decisiones. Con la misma semilla el partido se repite jugada
por jugada.

Una tanda de simulación usa semillas consecutivas (0, 1, 2…), y todos los
escenarios de una comparación usan las mismas. Así, cuando dos reglamentos dan
números distintos, la diferencia es la regla y no la suerte. Correr el mismo
comando dos veces da exactamente el mismo resultado; para ver otra muestra hay que
cambiar la semilla base.

---

## Qué mide

### Del partido

| Métrica | Qué significa |
|---|---|
| **Partidos que se definen** | Los que terminaron antes del límite de turnos. Si baja, el reglamento traba el juego. |
| **Goles por partido** | Los dos equipos juntos, sin contar penales. |
| **Turnos por partido** | Cuánto dura. Es la medida de ritmo más directa. |
| **Definidos por penales** | Cuántos llegaron al marcador de penales. Si es muy alto, el partido se define afuera del juego. |
| **Victorias por equipo** | Sirve de control: con perfiles iguales tiene que dar parejo. |
| **Barajadas del descarte** | Cuántas veces se agotó el mazo. Si es alto, el mazo queda chico para el formato. |

### De las acciones

El reparto porcentual de todo lo que pasó: pase, recuperación de la defensa,
reventar, disparo al arco, falta y pasa de turno. Es el retrato del juego: dice
si es un juego de posesión, de transición o de pelotazos.

### De trampa y marca

| Métrica | Qué significa |
|---|---|
| **Trampas de offside puestas** | Veces que la defensa armó el offside. |
| **Offsides cobrados** | De esas, cuántas efectivamente cortaron un pase. |
| **Marcas personales puestas** | Veces que la defensa marcó a alguien. |
| **Marcas que recuperaron la pelota** | De esas, cuántas terminaron en recuperación. |
| **Pases desviados por una marca** | Veces que el ataque tuvo que buscar otro receptor porque uno estaba marcado. |

Las dos últimas van juntas a propósito: una carta puede ser útil sin llegar a
ejecutarse nunca, y sin medir las dos cosas parece muerta cuando no lo está. Ver
[resultados.md](resultados.md#la-marca-personal-casi-nunca-recupera-la-pelota).

---

## Qué no modela

Vale la pena tenerlo presente antes de tomar una decisión de diseño solo con
estos números:

- **No hay engaño ni faroleo.** Nadie guarda una carta para el momento justo ni
  simula no tenerla.
- **No hay lectura del rival.** Los perfiles no aprenden ni se adaptan al estilo
  del otro equipo (salvo el perfil adaptativo, que solo mira el marcador).
- **No hay conversación.** En la mesa se pasa de turno por presión social o para
  hacer tiempo; acá solo por probabilidad.
- **No hay cansancio ni errores.** No se olvida una regla ni se juega mal una
  carta, cosa que en la mesa pasa todo el tiempo.

Por eso los números sirven para **comparar** dos reglamentos entre sí, no para
predecir cómo va a salir una partida concreta. Las diferencias grandes y
consistentes son señal; las de un punto porcentual, ruido.

Los supuestos que el motor tuvo que tomar donde la regla escrita no alcanzaba
están anotados en [ambiguedades.md](ambiguedades.md).
