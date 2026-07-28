# Reglamento v1 (iteración 1)

> Cambios surgidos del playtesting con amigos. Reemplaza varias mecánicas de v0.

## Objetivo del juego

Partido al mejor de 5 goles. Si el marcador llega a **2-2**, va **inmediatamente** a penales.

## Inicio

Se tira la moneda para ver qué equipo inicia con la pelota. El equipo decide qué jugador comienza con la posesión.

## Equipos

Mínimo **2 jugadores por equipo** (2 vs 2).

## Reparto y reposición

- Cada jugador arranca con una mano de **6 cartas**.
- Cuando la pelota **pasa de un equipo al otro**, cada jugador repone las cartas que le falten para llegar a 6.
- **Fin del mazo:** cuando ya no quedan cartas para repartir, se baraja todo el descarte y se reparte de nuevo. El partido sigue.

## Cómo se juega

La pelota siempre la tiene un jugador específico de la ofensiva. Solo ese jugador puede actuar.

### Acciones ofensivas

> **Pasa de turno** y **Reventar la pelota** son **decisiones del jugador**, no cartas del mazo. No necesitás una carta en la mano para hacerlas.

#### Con carta

| Acción | Carta | Descripción |
|--------|-------|-------------|
| **Patear al arco** | `Disparo al arco` | Fase de disparo |
| **Pasar la pelota** | `Pase` | La pelota y el turno pasan a un compañero |

#### Decisiones (sin carta)

| Decisión | Descripción |
|----------|-------------|
| **Pasa de turno** | Retener la pelota sin pasar ni disparar (como v0). Habilitada por regla. |
| **Reventar la pelota** | Despeje — ver sección abajo |

### Reacciones defensivas

| Si el ataque… | La defensa puede jugar… |
|---------------|-------------------------|
| Pasó la pelota | `Robo pelota` |
| Pasó de turno | `Trampa de offside`, `Marca personal` |

> `Trampa de offside` y `Marca personal` **solo** se juegan cuando el ataque pasa de turno, no en respuesta a un pase.

> **Importante:** la defensa solo puede reaccionar con **una carta por acción del ataque** (carta jugada o decisión como pasa de turno / reventar). Tras un pase, una sola respuesta defensiva en todo el equipo hasta la próxima acción ofensiva.

### Contra-respuesta ofensiva

| Carta defensiva | Se anula con |
|-----------------|--------------|
| `Robo pelota` | `Gambetear` |

### Quién queda con la pelota

Si la defensa robó la pelota y la ofensiva no respondió con otra carta, el jugador defensivo que recuperó la pelota pasa a ser dueño y su equipo queda en ofensiva.

## Cartas

### Ofensivas

| Carta | Efecto |
|-------|--------|
| **Pase** | El jugador que tiene la pelota se la pasa a un compañero |
| **Disparo al arco** | Activa la fase de disparo al arco |
| **Gambetear** | Si la defensa juega `Robo pelota`, el portador elude y conserva la pelota |

> `Gambetear` es carta; **pasa de turno** y **reventar** no lo son — figuran arriba como decisiones.

### Defensivas

| Carta | Efecto |
|-------|--------|
| **Robo pelota** | Interrumpe un pase; te quedás con la pelota |
| **Trampa de offside** | Solo cuando el ataque pasa de turno. Queda activa; si el ataque pasa, es offside y pierde la pelota |
| **Marca personal** | Solo cuando el ataque pasa de turno. Se pone encima de un jugador adversario; si recibe el pase, recuperás la pelota |
| **Falta** | La puede jugar cualquiera de los dos equipos. La pelota se queda en el equipo que la tenía. El contador de pases vuelve a cero |

## Fase de disparo al arco

El pateador y un arquero rival tiran cada uno un dado.

| Pases hechos | Hace gol con | Ataja con |
|--------------|--------------|-----------|
| 0 | 1 | 2 al 6 |
| 1 | 1 al 2 | 3 al 6 |
| 2 | 1 al 3 | 4 al 6 |
| 3 | 1 al 4 | 5 al 6 |
| 4 (o más) | 1 al 5 | 6 |

### Rebote y palo

- Si el pateador saca número de gol **y** el arquero saca número de atajada **al mismo tiempo** → **rebote**. Se vuelve a patear.
- Si ambos dados salen el **mismo número** → **palo**. Se vuelve a patear.

Cada vez que se roba la pelota o hay falta, el contador de pases vuelve a cero.

## Reventarla (despeje)

Cuando un jugador con la pelota no tiene opciones de pase (o cuando quiera) puede decir **"La reviento"** o **"La despejo"**:

1. Cada equipo **elige** quién tira el dado — puede ser **cualquier jugador del equipo**, excepto el que dijo "la reviento" / reventó la pelota.
2. El número más alto se queda con la pelota.
3. Si la conserva el mismo equipo que reventó, cuenta como **un pase completado**.
4. La pelota la conserva el **jugador que tiró el dado y ganó** el duelo.

## Penales

Si el partido va 2 a 2:

1. Se patean tantos penales como jugadores por equipo (ej.: 3 vs 3).
2. Si la serie no se desempata, se patea un penal y el que erra pierde.
3. Luego de la primera serie se puede cambiar de arquero.

## Mazo v1

| Carta | Cantidad |
|-------|----------|
| Pase | 42 |
| Robo pelota | 24 |
| Disparo al arco | 12 |
| Falta | 7 |
| Gambetear | 15 |
| Marca personal | 5 |
| Trampa de offside | 3 |
| **Total** | **108** |
