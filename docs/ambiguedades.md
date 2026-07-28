# Ambigüedades y supuestos del simulador

Reglas confirmadas en playtesting y supuestos que aún faltan cerrar.

## Confirmado por el grupo

### Equipos

- Mínimo **2 jugadores por equipo**.

### Marcador 2-2

- Si el marcador llega a **2-2**, el partido va **inmediatamente a penales** (sin seguir jugando).

### Trampa de offside y Marca personal

- **Solo** se pueden jugar cuando el ataque **pasa de turno** (cede el turno / retiene la pelota sin pasar ni disparar).
- **No** se juegan en respuesta a un pase.
- Una vez colocadas, surten efecto en el **próximo pase** del ataque (offside o marca al receptor).

### Reventarla — quién tira el dado

- Cada equipo **elige** quién tira — **cualquier jugador**, salvo el que reventó la pelota.
- El simulador elige al azar entre los compañeros del reventor (equipo atacante) y cualquier defensor (equipo rival).

### Pasa de turno — no es una carta

- **Pasa de turno** (v0: ceder el turno) es una **decisión** del portador: retener la pelota sin jugar `Pase` ni `Disparo al arco`.
- No existe carta “Pasa de turno” en el mazo. La regla **habilita** la acción, igual que **Reventar la pelota** en v1.
- Trampa de offside y Marca personal solo se juegan cuando la defensa **reacciona** a esa decisión.

## Objetivo del partido

**Texto:** "Partido al mejor de 5 goles, si empatan 2-2 va a penales."

**Supuesto del simulador:**

- Si un equipo llega a **3 goles** → gana el partido (3-0, 3-1, 3-2, etc.).
- Si el marcador llega a **2-2** → **penales inmediatos**.

> ⚠️ "Mejor de 5" puede interpretarse distinto. Si en la mesa juegan otro criterio, avisen y lo ajustamos.

## Penales

**Texto:** ronda de 3 penales por equipo; si empatan, un penal y el que erra pierde.

**Supuesto:**

- Cada penal = un dado del pateador vs un dado del arquero, con tabla de 0 pases en la jugada.
- Serie de 3: anota quien gana más de los 3.
- Empate en la serie → **muerte súbita**: un penal por ronda hasta que uno anote y el otro no.

## Marca personal — receptor

**Supuesto:** el pase va a un compañero **elegido** por el atacante. Si ese compañero está marcado, la defensa recupera (salvo `La dejo pasar` en v0).

## Falta — cuándo se puede jugar

**Supuesto:** en cualquier momento del turno, por cualquier jugador de cualquier equipo, **antes** de resolver la acción ofensiva o como interrupción. Efecto: pelota no cambia de equipo, contador de pases = 0.

## Robo vs Gambetear — orden de respuesta

**Supuesto:** defensa juega robo → atacante puede responder Gambetear **inmediatamente** si tiene la carta. Si no, pierde la pelota.

## Reventarla (v1)

Ver regla confirmada arriba. El motor elige tiradores al azar entre los jugadores elegibles (equivalente a una elección libre en mesa).

## Reposición v1

**Texto:** "cuando la pelota pasa de un equipo al otro"

**Supuesto:** **todos** los jugadores del juego repone hasta 6, no solo el equipo que ganó la pelota.

## Fin del mazo

**Supuesto:** al repone, si el mazo está vacío se baraja el descarte y sigue. Si no hay descarte, ese jugador repone menos cartas.

## Límite de turnos

**Supuesto:** si un partido supera **500 turnos** sin definirse, se declara empate técnico y se registra en estadísticas (señal de posible loop de reglas).
