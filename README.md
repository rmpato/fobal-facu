# Fobal Facu

Fobal Facu es un juego de cartas de fútbol que se juega en mesa, por equipos, con
un mazo y un dado. Este repositorio no es el juego: es el **banco de pruebas** que
se usa para diseñarlo.

Antes de imprimir una tanda nueva de cartas o de cambiar una regla, conviene saber
qué pasa si se cambia. Acá se escribe la regla, se corren mil partidos en unos
segundos y se mira qué cambió: si los partidos se terminan o se traban, cuántos
goles caen, cuántas veces sirve cada carta.

```
Reglamento (JSON)  →  motor  →  1000 partidos  →  métricas  →  decidir qué probar en mesa
```

- **Nada que instalar:** Python 3.11 o más nuevo, y nada más. Sin dependencias.
- **Las reglas son datos:** cambiar el juego es editar un archivo, no programar.
- **Repetible:** cada partido tiene una semilla; con el mismo número sale igual.

---

## Instalación

Lo único que hace falta es **Python 3.11 o más nuevo**. No hay dependencias que
instalar: el simulador usa solo la biblioteca estándar, así que no lleva `pip`, ni
entornos virtuales, ni nada que actualizar.

Los scripts de abajo comprueban que Python esté y sea suficientemente nuevo,
explican cómo instalarlo si falta, corren las pruebas y muestran cómo seguir.

### macOS y Linux

En la Terminal (funciona igual en zsh, bash o sh):

```sh
git clone https://github.com/rmpato/fobal-facu.git
cd fobal-facu
./instalar.sh
```

### Windows

En PowerShell o en el Símbolo del sistema:

```bat
git clone https://github.com/rmpato/fobal-facu.git
cd fobal-facu
.\instalar.bat
```

Si `git` no está instalado, se puede bajar el repositorio como ZIP desde el botón
verde **Code** de GitHub, descomprimirlo y entrar a la carpeta con `cd`.

Para instalar y abrir la interfaz de una sola vez: `./instalar.sh --web` o
`.\instalar.bat --web`.

---

## Cómo se usa

### La interfaz

```sh
python3 -m simulador web          # macOS y Linux
py -3 -m simulador web            # Windows
```

Abre `http://localhost:8000` con tres pestañas:

| Pestaña | Para qué |
|---|---|
| **Reglas** | Editar un reglamento: el mazo carta por carta, el tamaño de la mano, cuándo se reponen cartas, la tabla del dado, qué puede hacer cada equipo. Se guarda como un archivo del repositorio. |
| **Simular** | Correr cientos de partidos de dos o más reglamentos y compararlos en la misma pantalla. |
| **Ver un partido** | Mirar un partido jugada por jugada, para entender por qué salieron esos números. |

Se cierra con Ctrl+C en la terminal.

### La terminal

Todo lo que hace la página se puede hacer también con comandos. En Windows,
cambiar `python3` por `py -3`:

```sh
python3 -m simulador reglamentos                      # qué versiones del juego hay
python3 -m simulador reglamentos v2                   # qué reglas aplica una versión
python3 -m simulador simular v2 --partidos 500        # correr 500 partidos y ver las métricas
python3 -m simulador comparar v1 v2 --formatos 3 4    # comparar dos versiones y dos formatos
python3 -m simulador ver v2 --semilla 42              # un partido, jugada por jugada
python3 -m simulador ver v2 --grabar partido.html     # y guardarlo para compartir
python3 -m simulador perfiles                         # los estilos de juego disponibles
python3 -m simulador --help                           # todos los comandos
```

### Las pruebas

```sh
python3 -m unittest discover
```

Ochenta pruebas, un segundo y medio. Conviene correrlas después de tocar el
código: verifican que los partidos terminen, que no se pierdan cartas y que la
misma semilla dé siempre el mismo partido.

Guía completa de comandos: [`docs/guia-cli.md`](docs/guia-cli.md).

---

## Las reglas del juego

Las reglas para jugar en mesa —las de verdad, en castellano, para leer entre
todos— están en `docs/`:

| Versión | Qué introdujo | Estado |
|---|---|---|
| [v0](docs/reglamento-v0.md) | El juego original: `Corta pase`, `Tackle`, `La dejo pasar`. | Histórico |
| [v1](docs/reglamento-v1.md) | `Robo pelota` unifica los cortes, aparece *reventar la pelota*, se repone al cambiar de equipo. | En uso |
| [v1.1](docs/reglamento-v1.1.md) | Variante de v1: si nadie responde al pasa de turno, la pelota va a un compañero. | Variante |
| [v2](docs/reglamento-v2.md) | Sin pasa de turno; trampa y marca se juegan contra el pase; robo y gambeta se encadenan. | En prueba |

Cada versión existe dos veces: como texto para jugar (`docs/reglamento-*.md`) y
como archivo que lee el simulador (`reglamentos/*.json`).

---

## Qué se aprendió simulando

Números de 500 partidos por escenario, con el mismo estilo de juego en los dos
equipos ([detalle y cómo reproducirlos](docs/resultados.md)):

| Reglamento | Formato | Partidos que se definen | Goles | Turnos | Van a penales |
|---|---|---|---|---|---|
| v1 | 3 vs 3 | 98,4 % | 3,98 | 189 | 32,4 % |
| **v2** | **3 vs 3** | **99,6 %** | **3,87** | **171** | **26,8 %** |
| v1 | 4 vs 4 | 96,2 % | 3,88 | 230 | 27,6 % |
| v2 | 4 vs 4 | 95,8 % | 3,84 | 232 | 26,4 % |

Tres conclusiones que sirven para la mesa:

1. **v2 en 3 vs 3 es la versión más ágil**: dura un 10 % menos que v1 y casi nunca
   queda trabada.
2. **Ninguna de las dos escala bien a 4 vs 4**: los partidos se alargan ~35 % y
   aparecen más empates por límite de turnos.
3. **`Marca personal` casi nunca recupera la pelota**: se pone unas 15 veces por
   partido y funciona como amenaza —obliga a buscar otro receptor— más que como
   robo. Vale la pena mirarla en mesa antes de imprimir más copias.

---

## Cómo está organizado el repositorio

```
reglamentos/     Las reglas que aplica el motor, un archivo JSON por versión
simulador/       El motor, la línea de comandos y la interfaz web
  web/           Servidor local y página del banco de pruebas
tests/           Pruebas automáticas (python3 -m unittest discover)
docs/            Reglas de mesa, guías, resultados y el sitio publicado
```

Para entender el código por dentro —qué hace cada archivo, cómo se resuelve un
turno, dónde tocar para agregar una carta nueva— hay un recorrido comentado en
[`docs/codigo.md`](docs/codigo.md).

---

## Cambiar el juego sin escribir código

La mayoría de los cambios no necesitan programar nada:

| Quiero… | Dónde |
|---|---|
| Sacar o agregar copias de una carta | Pestaña **Reglas → Mazo** |
| Cambiar cuántas cartas tiene cada uno | **Reglas → Manos y reposición** |
| Cambiar cuándo se levantan cartas | **Reglas → Manos y reposición** |
| Hacer más fácil o más difícil el gol | **Reglas → Disparo al arco** |
| Sacar el pasa de turno, permitir reventar | **Reglas → Qué puede hacer quien tiene la pelota** |
| Que la defensa responda con otra carta | **Reglas → Cómo responde la defensa** |

Se guarda, se simula y se compara con la versión anterior. Lo único que pide
código es **una carta nueva con un efecto que el motor todavía no conoce**; ese
caso está explicado paso a paso en [`docs/codigo.md`](docs/codigo.md).

---

## Documentación

| Documento | De qué trata |
|---|---|
| [docs/guia-web.md](docs/guia-web.md) | La interfaz, pantalla por pantalla |
| [docs/guia-cli.md](docs/guia-cli.md) | Todos los comandos de la terminal |
| [docs/reglamentos-json.md](docs/reglamentos-json.md) | El formato de un reglamento, campo por campo |
| [docs/como-funciona.md](docs/como-funciona.md) | Cómo resuelve un turno el motor y qué mide |
| [docs/perfiles.md](docs/perfiles.md) | Los estilos de juego con los que simula |
| [docs/codigo.md](docs/codigo.md) | Recorrido por el código y cómo modificarlo |
| [docs/resultados.md](docs/resultados.md) | Qué dicen las simulaciones |
| [docs/recomendaciones.md](docs/recomendaciones.md) | Qué conviene probar después |
| [docs/ambiguedades.md](docs/ambiguedades.md) | Reglas sin cerrar y supuestos del motor |

Hay además una versión navegable en
[rmpato.github.io/fobal-facu](https://rmpato.github.io/fobal-facu/), pensada para
compartir con quien no va a abrir la terminal. Las mismas páginas están en
[`docs/`](docs/index.html) para leerlas sin conexión.

---

## Licencia

Juego y reglas: de sus autores. El código del simulador se puede usar y modificar
libremente dentro del proyecto.
