# Reglas sin cerrar y supuestos del motor

Las reglas escritas no siempre alcanzan para simular: en la mesa se resuelven
mirándose y siguiendo. El simulador tiene que tomar una decisión sí o sí, y acá
quedan anotadas todas.

Si alguna no coincide con cómo se juega, se ajusta: casi todas son un campo del
reglamento ([reglamentos-json.md](reglamentos-json.md)) o unas líneas de
`motor.py`.

---

## Confirmado en playtesting

Esto ya está decidido y el simulador lo respeta:

- **Mínimo 2 jugadores por equipo.**
- **El 2-2 va directo a penales**, sin seguir jugando.
- **Reventar la pelota:** cada equipo elige quién tira el dado, y no puede ser el
  que reventó. El simulador elige al azar entre los que pueden.
- **Pasar de turno y reventar no son cartas**, son decisiones: no hace falta tener
  nada en la mano para hacerlas.
- **Trampa de offside y marca personal se ponen y quedan esperando**: surten
  efecto en el próximo pase del ataque. En v1 se juegan cuando el ataque pasa de
  turno; en v2, como respuesta a un pase.

---

## Supuestos que tomó el simulador

### Cómo se gana

**La regla dice:** «partido al mejor de 5 goles; si empatan 2-2, van a penales».

**El simulador asume:** gana el primero que llega a **3 goles**; si el marcador
llega a **2-2**, penales inmediatos.

«Al mejor de 5» admite otra lectura (jugar cinco goles completos). Si en la mesa
se juega distinto, son dos números en **Reglas → Partido**.

### Los penales

**La regla dice:** una ronda de tres penales por equipo; si siguen iguales, uno
por equipo y el que erra pierde.

**El simulador asume:** tantos penales como jugadores por equipo (tres en 3 vs 3),
resueltos con la tabla de cero pases, y después muerte súbita de a un penal por
lado. También aplica el rebote y el palo si el reglamento los tiene, igual que en
el juego.

### Cuándo se juega la `Falta`

**El simulador asume:** en cualquier momento del turno, por cualquiera de los dos
equipos, antes de resolver la acción. Efecto: la pelota se queda en el mismo
equipo y el contador de pases vuelve a cero.

La frecuencia es un número del reglamento: la chance de que alguien que tiene la
carta la juegue en ese turno (8 % por defecto). Es el supuesto más difícil de
calibrar sin datos de mesa, y el que más afecta la duración del partido.

### A quién se marca

**El simulador asume:** la marca se pone sobre un rival que **no** tiene la
pelota. Si después le pasan a ese jugador, la defensa recupera.

Queda abierto si debería poder marcarse al que tiene la pelota, y si la marca
tendría que durar más de un pase. Ver
[recomendaciones.md](recomendaciones.md#ajustar-la-marca-personal).

### Cuántas cartas responde la defensa

**El simulador asume:** una carta por acción del ataque, en todo el equipo. Si el
reglamento permite encadenar (v2), después de una gambeta la defensa puede volver
a responder mientras le queden cartas.

### En qué orden se resuelve un pase

Cuando hay varias cosas en juego a la vez, el orden es:

1. las trampas puestas de antes (offside, marca);
2. la reacción de la defensa (robo, o poner una trampa nueva);
3. la contra del ataque;
4. la pelota llega al receptor.

Consecuencia: si el pase ya estaba condenado por una trampa, la defensa no gasta
además una carta de robo.

### Quién juega la contra

**El simulador asume:** la juega quien la tenga en la mano, y si la tienen los
dos, prefiere al receptor del pase. `Gambetear` la juega normalmente el que tiene
la pelota; `La dejo pasar`, el que la recibe.

### La reposición

**La regla dice (v1):** «cuando la pelota pasa de un equipo al otro».

**El simulador asume:** reponen **todos** los jugadores, no solo el equipo que
recuperó. Es configurable en **Reglas → Manos y reposición**.

### Cuando se termina el mazo

**El simulador asume:** se baraja el descarte y se sigue repartiendo. Si tampoco
hay descarte, ese jugador levanta menos cartas y el partido continúa.

### Partidos que no terminan

**El simulador asume:** a los 500 turnos corta y lo registra como partido **sin
definir**. No es una regla de mesa: es el detector de reglas que traban el juego.
Cuando ese número sube, hay algo que permite dar vueltas sin avanzar (le pasaba a
v0: ningún partido terminaba).

---

## Lo que el simulador no puede responder

Ninguna simulación va a decir si el juego es divertido, si una carta se entiende
sin explicarla o si la mesa se ríe. Los números sirven para descartar reglas rotas
y comparar variantes; el resto se decide jugando.
