# Comandos

Todo se corre desde la carpeta del repositorio, con Python 3.11 o más nuevo. No
hay que instalar nada.

```bash
python3 -m simulador --help          # la lista completa
python3 -m simulador <comando> --help
```

---

## `web` — la interfaz

```bash
python3 -m simulador web
python3 -m simulador web --puerto 9000 --sin-navegador
```

Abre el banco de pruebas en `http://localhost:8000`: editar reglas, simular y
mirar partidos. Solo escucha en la máquina donde se ejecuta. Se corta con Ctrl+C.
Detalle de cada pantalla: [guia-web.md](guia-web.md).

---

## `reglamentos` — qué reglas hay

```bash
python3 -m simulador reglamentos       # lista
python3 -m simulador reglamentos v2    # el detalle de uno
```

El detalle muestra las reglas que la simulación va a aplicar y el mazo completo.
Sirve para confirmar que un reglamento nuevo quedó como se esperaba.

---

## `simular` — muchos partidos de una versión

```bash
python3 -m simulador simular v2 --partidos 500
python3 -m simulador simular v2 --formato 4
python3 -m simulador simular v1 --perfil-equipo1 agresiva --perfil-equipo2 conservador
```

| Opción | Qué hace | Por defecto |
|---|---|---|
| `--partidos N` | Cuántos partidos correr | 200 |
| `--formato N` | Jugadores por equipo | 3 |
| `--perfil ID` | Estilo de juego de los dos equipos | `estrategica` |
| `--perfil-equipo1` / `--perfil-equipo2` | Un estilo distinto para cada equipo | igual a `--perfil` |
| `--semilla-base N` | Primera semilla de la tanda | 0 |

Imprime las reglas aplicadas y después las métricas: partidos definidos, goles,
turnos, penales, reparto de acciones, trampas y cartas jugadas. Qué significa cada
número está en [como-funciona.md](como-funciona.md#qué-mide).

Dos tandas con la misma orden dan exactamente el mismo resultado. Para ver otra
muestra, cambiar `--semilla-base`.

---

## `comparar` — dos versiones lado a lado

```bash
python3 -m simulador comparar                      # todos los activos, 3 vs 3
python3 -m simulador comparar v1 v2 --formatos 3 4
python3 -m simulador comparar v1 v2 --partidos 500 --detalle
```

Una fila por combinación de reglamento y formato, con las mismas semillas en
todas: la diferencia entre filas es la regla, no la suerte.

| Opción | Qué hace | Por defecto |
|---|---|---|
| `--formatos N [N…]` | Qué formatos probar | 3 |
| `--partidos N` | Partidos por celda | 200 |
| `--perfil ID` | Estilo de juego | `estrategica` |
| `--detalle` | Agrega el informe completo de cada escenario | — |

Sin argumentos compara los reglamentos marcados como activos.

---

## `ver` — un partido, jugada por jugada

```bash
python3 -m simulador ver v2
python3 -m simulador ver v2 --semilla 42 --pausa 0
python3 -m simulador ver v2 --todo                       # con las tiradas de dado
python3 -m simulador ver v2 --nombres Facu Pato Manu Colo Ostu Joaco
python3 -m simulador ver v2 --grabar partidos/final.html
```

| Opción | Qué hace | Por defecto |
|---|---|---|
| `--semilla N` | Repite exactamente ese partido | una al azar, que se imprime al final |
| `--pausa S` | Segundos entre jugadas; `0` lo imprime de una | 0.6 |
| `--todo` | Muestra también los dados y las reposiciones | — |
| `--nombres …` | Nombres de los jugadores | Facu, Pato, Manu, Colo, Ostu, Joaco |
| `--formato N`, `--perfil ID` | Igual que en `simular` | 3, `estrategica` |
| `--grabar ARCHIVO` | Guarda el partido en `.json`; con `.html` deja además una página para volver a verlo | — |

Al terminar imprime la semilla: con ese número el partido se repite igual, útil
para revisar una jugada rara con calma o para mostrársela a alguien.

---

## `perfiles` — los estilos de juego

```bash
python3 -m simulador perfiles
```

Los estilos con los que juegan los equipos simulados. Cambiar el perfil cambia los
resultados tanto como cambiar una regla, así que las comparaciones se corren
siempre con el mismo perfil en los dos equipos. Detalle:
[perfiles.md](perfiles.md).

---

## Pruebas

```bash
python3 -m unittest discover
```

Conviene correrlas después de tocar el código: verifican que los partidos
terminen, que no se pierdan cartas y que la misma semilla dé siempre el mismo
partido.
