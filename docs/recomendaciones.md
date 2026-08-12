# Qué conviene probar después

Lista de cambios candidatos, ordenados por lo que se sabe hoy. Cada uno viene con
la evidencia que lo motiva y con la forma de probarlo. Nada de esto es una
conclusión de mesa: el simulador dice qué pasa con las reglas escritas, no si el
juego es divertido.

Las mediciones que se citan están en [resultados.md](resultados.md).

---

## Para la próxima partida en mesa

Antes de tocar nada, hay tres cosas que solo se pueden responder jugando:

1. **¿La `Marca personal` se siente útil?** En simulación no recupera la pelota
   nunca contra un ataque atento: obliga a pasarle a otro y nada más. Vale la pena
   anotar, en tres o cuatro partidas, cuántas veces se puso y cuántas sirvió de
   algo.
2. **¿Molestan las faltas?** Son el 8 % de las jugadas y son lo que más alarga el
   partido. Si en la mesa se sienten como una interrupción, hay margen para bajar
   copias.
3. **¿Los 2-2 son emocionantes o cansan?** Uno de cada cuatro partidos se define
   por penales; con estilos parejos, seis de cada diez. Es mucha definición fuera
   del juego.

Sirve contar las acciones de una partida real y compararlas con el reparto
simulado: si difieren mucho, el modelo de decisión está lejos de cómo juegan las
personas y conviene ajustarlo antes de seguir sacando conclusiones.

---

## Cambios de mazo, en orden de impacto

Todos se prueban desde la pestaña **Reglas**, duplicando v2 y cambiando un número.

### 1. Bajar `Falta` de 7 a 3 copias

**Por qué:** es el cambio que más acorta el partido (−17 % de turnos) sin tocar
goles ni penales. Cada falta corta la jugada y borra los pases acumulados, así que
pesa más de lo que parece por su frecuencia.

**Riesgo:** la falta es la única carta que puede jugar el equipo sin la pelota
fuera de su turno. Bajarla mucho le saca al juego su único recurso de interrupción.

**Alternativa:** dejarla en 7 pero limitarla a una por jugada.

### 2. Subir `Disparo al arco` de 12 a 18

**Por qué:** acorta un 13 % y sube los remates de 8,5 % a 10,8 % de las jugadas,
sin inflar el marcador. Hoy el disparo es la única forma de hacer un gol y es solo
el 11 % del mazo.

**Riesgo:** con más disparos en mano se remata de lejos, con pocos pases; si la
gracia del juego es armar la jugada, puede empobrecerla. Mirar los goles por
partido: si suben mucho, la tabla del dado está compensando de más.

### 3. Bajar `Robo pelota` de 24 a 18

**Por qué:** acorta y hace llegar más al ataque.

**Riesgo:** sube los penales de 27 % a 31 %, porque los dos equipos convierten más
y el 2-2 aparece antes. Conviene combinarlo con el punto siguiente.

---

## Cambios de regla

### Revisar cómo termina el partido

Es la decisión más importante que queda abierta. Hoy: gana el que llega a 3 goles,
pero un 2-2 manda directo a penales, así que en la práctica muchos partidos se
deciden afuera del juego. Dos opciones para simular:

- **Subir a 4 goles** manteniendo penales en 2-2.
- **Correr los penales a 3-3**, que es lo mismo que decir «se define jugando».

Las dos se prueban cambiando dos números en la pestaña **Reglas → Partido**.

### Ajustar la `Marca personal`

Hoy es una carta de condicionamiento disfrazada de recuperación. Tres variantes
para probar, de menos a más agresiva:

- Que la marca **también valga como corte** si el ataque le pasa a cualquier otro
  jugador (es decir, que tape una opción de verdad).
- Que quede puesta **más de un pase**, en vez de gastarse en el primero.
- Que se pueda poner **sobre el que tiene la pelota**, no solo sobre un receptor.

Las dos primeras necesitan un cambio de código chico en `motor.py`; el recorrido
está en [codigo.md](codigo.md#agregar-una-carta-nueva).

### Definir qué pasa en 4 vs 4 y 5 vs 5

Con más jugadores el partido se alarga mucho (+35 % en 4 vs 4, +75 % en 5 vs 5) y
empiezan a aparecer partidos que no se definen. Si el grupo juega seguido de a
cuatro, conviene que el reglamento lo contemple en vez de dejarlo librado al azar:
por ejemplo, más goles para ganar o una mano más chica cuando son más.

---

## Ideas de cartas nuevas

Ninguna está simulada todavía: son huecos que se ven en los números.

| Carta | Qué haría | Qué hueco llena |
|---|---|---|
| **Centro** | Un pase que no puede ser cortado con `Robo pelota` (sí por una marca ya puesta) | Rompe el bucle pase → robo → gambeta, que es la mitad del juego |
| **Presión** | Jugable cuando el ataque pasa de turno: le obliga a pasar o rematar el turno siguiente | Le da a la defensa algo que hacer contra la espera, sin duplicar la marca |
| **Achique** | En el disparo, el arquero ataja con un número más | Válvula para bajar goles sin tocar la tabla entera |
| **Amonestación** | Cancela una `Falta` rival | Controla las faltas sin sacarlas del mazo |
| **Contragolpe** | Al recuperar la pelota, se puede rematar de inmediato | Acorta las transiciones, que son lo más largo del partido |

Para probar cualquiera hace falta darle efecto en el motor
([codigo.md](codigo.md#agregar-una-carta-nueva)) y después compararla con v2 en la
pestaña **Simular**.

---

## Cosas que ya se descartaron

- **v1.1 (la pelota pasa a un compañero si nadie responde al pasa de turno):**
  simulado, casi sin efecto (193 turnos contra 189 de v1). El problema de v1 no
  era ese.
- **Volver a `Corta pase` y `Tackle` como cartas separadas (v0):** unificarlas en
  `Robo pelota` simplificó el juego sin cambiar el balance.
- **Cambiar cuándo se reponen las cartas:** mientras se reponga seguido, mueve muy
  poco. Lo que importa es que se reponga: v0 no lo hacía y no terminaba nunca.
