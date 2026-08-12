# Estilos de juego

El simulador no juega «bien» ni «mal»: juega con un estilo. Un perfil es un
conjunto de tendencias —cuánto le gusta rematar, cuánto arriesga en defensa,
cuánto guarda las contras— que decide entre las jugadas que el reglamento
permite.

Elegir un perfil importa tanto como elegir una regla. Por eso las comparaciones
entre reglamentos se corren siempre con el mismo perfil en los dos equipos, y por
eso conviene mirar dos o tres perfiles antes de decidir un cambio: si una regla
solo mejora el juego con un estilo, en la mesa va a depender de quién esté
sentado.

```bash
python3 -m simulador perfiles
python3 -m simulador simular v2 --perfil paciente
python3 -m simulador simular v2 --perfil-equipo1 agresiva --perfil-equipo2 conservador
```

---

## Los nueve perfiles

| Perfil | `--perfil` | Cómo juega |
|---|---|---|
| **Directo** | `simple` | Pasa casi siempre y patea cuando le toca la carta. La referencia más neutra. |
| **Táctico** | `estrategica` | Encadena pases y remata cuando la tabla lo favorece. Es el que se usa por defecto. |
| **Presionante** | `agresiva` | Remata temprano y responde con todo en defensa. |
| **Posicional** | `paciente` | Acumula pases antes de rematar y usa mucho el pasa de turno. |
| **Arriesgado** | `gambler` | Patea y revienta más de lo razonable; no esquiva las marcas. |
| **Conservador** | `conservador` | Guarda las cartas, casi no patea, defiende poco. |
| **Marcador** | `marcador` | Prioriza `Marca personal` y busca al jugador marcado. |
| **Contragolpista** | `contragolpista` | Remata apenas recupera, sin construir la jugada. |
| **Adaptativo** | `adaptativo` | Ataca si va perdiendo y se repliega si va ganando. |

---

## Qué le hace cada uno al juego

Reglamento v2, 3 vs 3, 300 partidos con el mismo perfil en los dos equipos:

| Perfil | Se definen | Goles | Turnos | Penales | Pase | Disparo | Robo | Reventar |
|---|---|---|---|---|---|---|---|---|
| Directo | 99,0 % | 4,07 | 207 | 35,7 % | 46 % | 9 % | 18 % | 19 % |
| Táctico | 99,3 % | 3,88 | 172 | 27,0 % | 47 % | 9 % | 19 % | 17 % |
| Presionante | 99,3 % | 3,85 | 188 | 26,0 % | 43 % | 11 % | 18 % | 19 % |
| Posicional | 99,3 % | 4,00 | 181 | 31,7 % | 47 % | 7 % | 18 % | 19 % |
| Arriesgado | 98,3 % | 3,84 | 229 | 23,7 % | 40 % | 10 % | 18 % | 24 % |
| Conservador | 98,3 % | 4,05 | 212 | 33,0 % | 46 % | 6 % | 15 % | 26 % |
| Marcador | 97,0 % | 3,83 | 232 | 26,3 % | 45 % | 8 % | 21 % | 18 % |
| Contragolpista | 95,3 % | 3,93 | 260 | 31,3 % | 40 % | 13 % | 16 % | 23 % |
| Adaptativo | 98,0 % | 4,52 | 203 | 62,7 % | 46 % | 8 % | 18 % | 20 % |

Tres cosas que se leen en esa tabla:

- **El estilo mueve el ritmo más que el marcador.** Entre Táctico y
  Contragolpista hay 88 turnos de diferencia (+51 %) y casi los mismos goles. El
  juego aguanta estilos muy distintos sin romperse.
- **Rematar poco no baja los goles, alarga el partido.** Conservador patea la
  mitad que Presionante y termina con más goles: los hace más tarde. Lo que se
  paga es duración.
- **Cuando los dos equipos se adaptan, el partido se empareja solo.** Adaptativo
  llega a penales en 6 de cada 10 partidos: el que va perdiendo ataca, el que va
  ganando se cierra, y el marcador converge al 2-2. Es la señal más clara de que
  la regla del 2-2 es la que define el juego, más que los 3 goles.

El perfil **Marcador** sirve para lo contrario que los demás: no para comparar
reglamentos, sino para estirar una carta al máximo y ver qué daría si todos la
jugaran bien. Es el que se usa para medir el techo de `Marca personal` en
[resultados.md](resultados.md#la-marca-personal-casi-nunca-recupera-la-pelota).

---

## Agregar un perfil

En `simulador/ia.py`, la lista `PERFILES`. Cada uno es una línea con sus
tendencias:

```python
Perfil(
    id="tiquitaca",
    nombre="Toque",
    descripcion="Pasa hasta cansar y solo remata con la jugada armada.",
    pase=0.90,
    disparo_base=0.02,
    disparo_por_pase=0.20,
    reventar=0.03,
    pasa_turno=0.05,
    defensa=1.2,   # multiplica las ganas de responder con una carta
    contra=0.7,    # chance de gastar Gambetear o La dejo pasar
)
```

Queda disponible solo en la interfaz, en `--perfil` y en las comparaciones.
