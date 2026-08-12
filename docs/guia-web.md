# La interfaz, pantalla por pantalla

```bash
python3 -m simulador web
```

Abre `http://localhost:8000`. La página corre en la propia computadora: no
necesita internet, no manda nada a ningún lado y los cambios se guardan como
archivos del repositorio, igual que si se editaran a mano.

Tres pestañas: **Reglas**, **Simular** y **Ver un partido**.

---

## Reglas

A la izquierda están los reglamentos que existen. El punto lleno (●) marca los que
entran por defecto en las comparaciones; el vacío (○), los que quedan como
referencia histórica.

A la derecha se edita el elegido. Mientras se escribe, el simulador valida: si
algo no cierra, aparece abajo un cartel rojo explicando qué arreglar.

### Mazo

Cuántas copias de cada carta. La barra muestra el peso de esa carta en el mazo y
el total se actualiza solo. Con la **×** se saca una carta del juego; abajo se
puede agregar cualquiera de las diez que existen.

Es el cambio más directo que se puede hacer: subir `Disparo al arco` acorta los
partidos, bajar `Falta` los hace más fluidos, bajar `Robo pelota` afloja la
presión defensiva. Hay mediciones de cada uno en [resultados.md](resultados.md).

### Manos y reposición

- **Cartas al empezar** y **máximo en la mano**: se pueden separar, para arrancar
  con menos de lo que después se puede acumular.
- **Cuándo se levantan cartas**: al cambiar de equipo, cuando alguien se queda sin
  cartas, al final de cada turno, apenas se juega una carta, o nunca.
- **Quién levanta**: todos, solo un equipo, o solo el jugador involucrado.

Debajo de los selectores queda escrita la regla en castellano, para confirmar que
dice lo que se quiso decir.

### Partido

Goles para ganar, marcador que manda a penales, mínimo de jugadores por equipo y
límite de turnos. El límite no es una regla de mesa: es el corte que usa el
simulador para detectar partidos trabados.

### Disparo al arco

La tabla del dado, que es donde se define cuántos goles caen. Cada fila dice, para
una cantidad de pases encadenados, con qué números entra la pelota y con cuáles
ataja el arquero. Se pueden agregar o sacar franjas; la última vale también para
cualquier cantidad mayor de pases.

Las dos casillas de arriba son el rebote (los dos aciertan → se vuelve a patear) y
el palo (dados iguales → se vuelve a patear).

### Qué puede hacer quien tiene la pelota

Pasar, patear, reventar, pasar de turno. Sacar el pasa de turno es, por ejemplo,
el cambio central de v2. Siempre tiene que quedar habilitada reventar o pasar de
turno: son las dos que no gastan carta.

### Cómo responde la defensa

Dos columnas, una para cuando el ataque pasa la pelota y otra para cuando pasa de
turno. Se marcan las cartas que la defensa puede jugar en cada caso y, debajo, con
qué carta las anula el ataque.

Mover `Marca personal` y `Trampa de offside` de una columna a la otra es
exactamente la diferencia entre v1 y v2.

### Guardar

- **Guardar** escribe el archivo en `reglamentos/`.
- **Guardar y simular** además salta a la pestaña Simular y corre la comparación.
- **Duplicar** (a la izquierda) hace una copia para probar una variante sin tocar
  el original: conviene cambiarle el id antes de guardar.
- **Descartar cambios** vuelve a lo último guardado.

---

## Simular

Un **escenario** es un reglamento, un formato (jugadores por equipo) y un estilo
de juego. Se agregan los que se quieran comparar y se elige cuántos partidos correr
por cada uno.

Todos los escenarios usan las mismas semillas, así que la diferencia entre ellos
es la regla y no la suerte. Doscientos partidos alcanzan para ver tendencias; con
quinientos las diferencias chicas dejan de moverse entre corrida y corrida.

Los resultados salen en cuatro bloques:

1. **Comparación**: partidos que se definen, goles, turnos y penales.
2. **En qué se va el juego**: el reparto de acciones de cada partido.
3. **Trampa de offside y marca personal**: cuántas se ponen y cuántas sirven.
   Una marca puede recuperar la pelota o, más seguido, obligar al ataque a buscar
   otro receptor: las dos cosas se miden por separado.
4. **Todos los números**: la tabla completa, para copiar a un informe.

Qué significa cada métrica: [como-funciona.md](como-funciona.md#qué-mide).

---

## Ver un partido

Un partido completo, jugada por jugada, con el marcador arriba. Sirve para
entender de dónde salen los números: si un reglamento da partidos larguísimos,
acá se ve por qué.

- **Semilla**: en blanco juega uno nuevo; con un número repite exactamente ese
  partido. La semilla usada queda escrita al terminar.
- **Nombres**: separados por coma, para reconocer a cada uno en el relato.
- **Mostrar tiradas de dado** agrega la resolución fina: cada dado, cada rebote,
  cada reposición.
- Reproducir, pausa, siguiente y velocidad para seguirlo al ritmo que uno quiera.

Desde la terminal, el mismo partido se puede grabar como página HTML para
compartir: `python3 -m simulador ver v2 --semilla 42 --grabar partido.html`.
