# Reglamento v0 (original)

> Versión inicial del juego, antes de la primera iteración de playtesting.

## Objetivo del juego

Partido al mejor de 5 goles. Si el marcador llega a **2-2**, va **inmediatamente** a penales.

## Equipos

Mínimo **2 jugadores por equipo** (2 vs 2).

## Reparto y reposición

- Cada jugador arranca con una mano de **6 cartas**.
- Cuando un jugador se queda en **0 cartas**, repone una mano nueva completa de 6.
- **Fin del mazo:** cuando ya no quedan cartas para repartir, se baraja todo el descarte y se reparte de nuevo. El partido sigue.

## Cómo se juega

La pelota siempre la tiene un jugador específico de la ofensiva. Solo ese jugador puede actuar.

### Acciones ofensivas

| Acción | Descripción |
|--------|-------------|
| **Patear al arco** | Jugar `Disparo al arco` → fase de disparo |
| **Pasar la pelota** | Jugar `Pase` → la pelota y el turno pasan a un compañero |
| **Ceder el turno / Pasa de turno** | Retener la pelota sin jugar carta de pase ni patear |

### Reacciones defensivas

| Si el ataque… | La defensa puede jugar… |
|---------------|-------------------------|
| Pasó la pelota | `Corta pase` |
| Pasó de turno (cedió) | `Tackle`, `Trampa de offside`, `Marca personal` |

> `Trampa de offside` y `Marca personal` **solo** se juegan cuando el ataque pasa de turno, no en respuesta a un pase.

### Contra-respuestas ofensivas

| Carta defensiva | Se anula con |
|-----------------|--------------|
| `Corta pase` | `La dejo pasar` |
| `Tackle` | `Gambetear` |

### Quién queda con la pelota

- Si la contra ofensiva funciona → la jugada sigue como si la defensa no hubiese hecho nada.
- Si la defensa recupera la pelota (corte de pase o tackle) → la pelota queda en manos del jugador defensivo que jugó la carta.

## Cartas

### Ofensivas

| Carta | Efecto |
|-------|--------|
| **Pase** | El jugador que tiene la pelota se la pasa a un compañero |
| **Disparo al arco** | Activa la fase de disparo al arco |
| **Gambetear** | Si la defensa juega `Tackle`, el portador elude y conserva la pelota |
| **La dejo pasar** | Si la defensa juega `Corta pase`, el receptor anticipa el corte y no pierde la pelota |

### Defensivas

| Carta | Efecto |
|-------|--------|
| **Corta pase** | Interrumpe un pase; te quedás con la pelota |
| **Tackle** | Si el ataque cedió el turno sin pasar, le quitás la pelota |
| **Trampa de offside** | Solo cuando el ataque pasa de turno. Queda activa; si el ataque pasa, es offside y pierde la pelota |
| **Marca personal** | Solo cuando el ataque pasa de turno. Se pone encima de un jugador; si recibe el pase, recuperás la pelota (salvo `La dejo pasar`) |
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

Cada vez que se roba la pelota o hay falta, el contador de pases vuelve a cero.

## Penales

Si el partido va 2 a 2:

1. Se patean tantos penales como jugadores por equipo (ej.: 3 vs 3).
2. Si la serie no se desempata, se patea un penal y el que erra pierde.
3. Luego de la primera serie se puede cambiar de arquero.

## Mazo v0

| Carta | Cantidad |
|-------|----------|
| Pase | 42 |
| Corta pase | 12 |
| Tackle | 12 |
| Disparo al arco | 12 |
| Falta | 7 |
| Gambetear | 8 |
| La dejo pasar | 7 |
| Marca personal | 5 |
| Trampa de offside | 3 |
| **Total** | **108** |
