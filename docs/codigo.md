# Recorrido por el código

Esta guía es para quien quiera leer o modificar el simulador. No hace falta saber
Python de antes: el programa es chico (unas 2.000 líneas), no usa ninguna
biblioteca externa y cada archivo hace una sola cosa.

Antes de tocar código conviene revisar si el cambio se puede hacer desde la
interfaz o editando un JSON, que es lo normal:
[reglamentos-json.md](reglamentos-json.md).

---

## Los archivos

```
simulador/
  cartas.py        Qué cartas existen y cómo se arma el mazo
  reglamento.py    Lee y valida los archivos de reglamentos/
  modelo.py        El estado de un partido: jugadores, mazo, marcador
  eventos.py       Los eventos que va emitiendo el partido
  motor.py         Las reglas en acción: cómo se resuelve un turno
  ia.py            Los estilos de juego: cómo decide un jugador simulado
  estadisticas.py  Correr muchos partidos y sacar promedios
  espectador.py    Relato de un partido en la terminal
  replay.py        Guardar un partido y exportarlo como página HTML
  cli.py           Los comandos: simular, comparar, ver, web…
  web/
    servidor.py    Servidor local y API en JSON
    estatico/      La página: index.html, estilo.css, app.js
```

Las dependencias van siempre en una sola dirección, sin vueltas:

```
cartas → reglamento → modelo → motor → estadisticas → cli
                        ↑        ↑          ↑
                     eventos    ia      espectador / web
```

---

## Las cuatro ideas que explican el resto

### 1. Las reglas son datos, no código

`motor.py` no sabe qué es «v1» ni «v2». Sabe resolver *un* turno preguntándole al
reglamento qué está permitido. Por eso agregar una versión del juego no toca el
motor: se agrega un archivo en `reglamentos/`.

```python
if reg.permite("reventar"):        # ¿este reglamento deja reventar la pelota?
if carta in reg.reaccion("pase").cartas:   # ¿la defensa puede jugar esta carta al pase?
```

### 2. El motor decide qué es legal; el agente, qué hacer

El motor calcula la lista de acciones posibles y se la pasa al agente, que elige
una. El agente que viene incluido (`ia.py`) elige con probabilidades según un
perfil, pero cualquier objeto con esos cuatro métodos sirve —incluida, en el
futuro, una persona jugando desde la web:

```python
class Agente:
    def accion(self, estado, posibles): ...      # ¿pase, disparo, reventar…?
    def receptor(self, estado, candidatos): ...  # ¿a quién le paso?
    def reaccion(self, estado, contexto, opciones): ...  # ¿la defensa juega alguna carta?
    def contra(self, estado, jugador, contra, ante): ... # ¿gasto la contra para anularla?
```

### 3. El partido cuenta lo que hace

En vez de imprimir texto, el motor emite **eventos** (`eventos.py`): un tipo, un
texto en castellano, quiénes participaron y el marcador del momento. El relato de
la terminal, la web y las grabaciones leen esa misma lista, así que los tres
cuentan exactamente el mismo partido.

### 4. Cada partido tiene una semilla

El azar sale de un generador propio de cada partido (`estado.rng`), nunca del azar
global del programa. Con la misma semilla, el mismo partido se repite jugada por
jugada: por eso se pueden comparar dos reglamentos sin que la diferencia sea
suerte, y por eso una jugada rara se puede volver a mirar con calma.

---

## Cómo se resuelve un turno

Todo pasa en `motor.jugar_turno`. La secuencia es siempre la misma:

1. **Falta.** Cualquiera con `Falta` en la mano puede cortar la jugada. Si alguien
   la juega, la pelota se queda donde está, el contador de pases vuelve a cero y
   el turno termina ahí.
2. **Acción del ataque.** `acciones_posibles()` cruza lo que permite el reglamento
   con lo que hay en la mano. El agente elige una: pasar, patear, reventar o pasar
   de turno.
3. **Trampas puestas de antes.** Si hay una trampa de offside activa, el pase es
   offside. Si el receptor estaba marcado, la marca se cobra. Las dos se gastan al
   dispararse.
4. **Reacción de la defensa.** Una carta por acción del ataque. El ataque puede
   anularla con su contra (`Gambetear`, `La dejo pasar`). Si el reglamento permite
   encadenar, la defensa puede volver a responder.
5. **La pelota queda en alguien.** Si cambió de equipo, se limpian las trampas y
   el contador de pases vuelve a cero.
6. **Reposición.** Según el reglamento, se levantan cartas hasta el máximo de mano.

El partido termina cuando un equipo llega a los goles necesarios, cuando el
marcador toca el valor que manda a penales, o cuando se agota el límite de turnos
(eso se registra como partido *no definido*: es la señal de que una regla traba el
juego).

---

## Tareas típicas

### Cambiar un número del juego

No se toca código: es un campo del reglamento. Ver
[reglamentos-json.md](reglamentos-json.md).

### Agregar una carta nueva

Solo hace falta código si la carta hace algo que el motor todavía no sabe hacer.
Si es una carta que corta un pase, que se anula con otra o que se pone como
trampa, alcanza con el JSON.

Si es un efecto nuevo:

1. Agregar el nombre en `cartas.py` (`class Carta`) y clasificarla en `OFENSIVAS`
   o `DEFENSIVAS`. Si corta acciones, sumarla a `INTERCEPCIONES`; si queda puesta
   esperando el próximo pase, a `TRAMPAS`.
2. Darle efecto en `motor.py`, en el paso que corresponda de la secuencia de
   arriba.
3. Sumarla al mazo de un reglamento (desde la interfaz o editando el JSON).
4. Escribir una prueba en `tests/test_motor.py` que la ponga en la mano de alguien
   y verifique qué pasa. Los tests de `TrampasTest` sirven de molde.

### Agregar un estilo de juego

En `ia.py`, agregar un `Perfil` a la lista `PERFILES` con sus tendencias. Aparece
solo en la interfaz, en `--perfil` y en las comparaciones.

### Agregar una métrica

1. En `motor.py`, llamar a `estado.registrar("mi_metrica")` donde ocurra.
2. En `estadisticas.py`, sumarla a `ACCIONES` (si es una acción del juego) o a
   `TRAMPAS`, y ponerle un nombre legible en `ETIQUETAS`.
3. Queda disponible sola en el informe de la terminal y en la API de la web.

---

## Pruebas

```bash
python3 -m unittest discover          # todo
python3 -m unittest tests.test_motor  # un archivo
python3 -m unittest tests.test_motor.TrampasTest -v   # un grupo
```

Las pruebas usan `unittest`, que viene con Python: no hay que instalar nada. Un
cambio en las reglas del motor debería romper alguna prueba; si no rompe ninguna,
probablemente falte una.

Las de `tests/test_motor.py` son las más útiles para entender el motor: arman un
partido, le ponen cartas concretas en la mano a alguien y verifican qué pasa.

---

## Estilo

- Todo en castellano: nombres, comentarios y mensajes.
- Funciones cortas, una idea por función; el guion bajo adelante (`_pase`) marca
  lo que es interno del archivo.
- Los comentarios explican **por qué**, no qué hace la línea siguiente.
- Nada de dependencias externas: si algo se puede hacer con la biblioteca
  estándar, se hace así.
