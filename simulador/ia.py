"""Perfiles de juego: cómo deciden los jugadores simulados.

El motor nunca decide: calcula qué es legal y le pregunta al agente. Un perfil
es una tabla de tendencias (cuánto le gusta disparar, cuánto arriesga en
defensa) que se traduce en pesos para cada opción disponible.

Cambiar de perfil cambia el resultado de la simulación tanto como cambiar una
regla, así que las comparaciones entre reglamentos se corren siempre con el
mismo perfil en los dos equipos.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Protocol

from simulador.cartas import Carta
from simulador.modelo import EstadoPartido, Jugador

Opcion = tuple[Jugador, Carta]


@dataclass(frozen=True)
class Perfil:
    """Tendencias de un estilo de juego."""

    id: str
    nombre: str
    descripcion: str
    pase: float = 0.72
    disparo_base: float = 0.12
    disparo_por_pase: float = 0.15
    reventar: float = 0.08
    pasa_turno: float = 0.10
    defensa: float = 1.0
    contra: float = 0.6
    evita_marca: bool = True
    busca_marca: bool = False
    adapta: bool = False

    def prob_disparo(self, pases: int) -> float:
        return min(0.9, self.disparo_base + self.disparo_por_pase * min(pases, 4))


PERFILES: dict[str, Perfil] = {
    p.id: p
    for p in (
        Perfil(
            id="simple",
            nombre="Directo",
            descripcion="Pasa casi siempre y dispara cuando le toca la carta.",
            pase=0.82,
            disparo_base=0.15,
            disparo_por_pase=0.12,
            pasa_turno=0.04,
            defensa=1.0,
            contra=0.5,
        ),
        Perfil(
            id="estrategica",
            nombre="Táctico",
            descripcion="Encadena pases y dispara cuando la tabla lo favorece.",
            pase=0.75,
            disparo_base=0.10,
            disparo_por_pase=0.18,
            pasa_turno=0.12,
            defensa=1.8,
            contra=0.6,
        ),
        Perfil(
            id="agresiva",
            nombre="Presionante",
            descripcion="Dispara temprano y reacciona con todo en defensa.",
            pase=0.70,
            disparo_base=0.25,
            disparo_por_pase=0.15,
            reventar=0.12,
            pasa_turno=0.03,
            defensa=2.2,
            contra=0.7,
        ),
        Perfil(
            id="paciente",
            nombre="Posicional",
            descripcion="Acumula pases antes de rematar; usa el pasa de turno.",
            pase=0.68,
            disparo_base=0.04,
            disparo_por_pase=0.16,
            pasa_turno=0.28,
            defensa=1.4,
            contra=0.6,
        ),
        Perfil(
            id="gambler",
            nombre="Arriesgado",
            descripcion="Dispara y revienta más de lo razonable.",
            pase=0.55,
            disparo_base=0.20,
            disparo_por_pase=0.14,
            reventar=0.18,
            pasa_turno=0.15,
            defensa=2.0,
            contra=0.75,
            evita_marca=False,
        ),
        Perfil(
            id="conservador",
            nombre="Conservador",
            descripcion="Guarda cartas, casi no dispara y defiende poco.",
            pase=0.88,
            disparo_base=0.04,
            disparo_por_pase=0.09,
            reventar=0.05,
            pasa_turno=0.05,
            defensa=0.7,
            contra=0.45,
        ),
        Perfil(
            id="marcador",
            nombre="Marcador",
            descripcion="Prioriza Marca personal y busca al jugador marcado.",
            pase=0.72,
            disparo_base=0.12,
            disparo_por_pase=0.15,
            pasa_turno=0.30,
            defensa=1.6,
            contra=0.6,
            evita_marca=False,
            busca_marca=True,
        ),
        Perfil(
            id="contragolpista",
            nombre="Contragolpista",
            descripcion="Remata apenas recupera, sin construir la jugada.",
            pase=0.50,
            disparo_base=0.40,
            disparo_por_pase=0.05,
            reventar=0.15,
            pasa_turno=0.06,
            defensa=1.5,
            contra=0.65,
        ),
        Perfil(
            id="adaptativo",
            nombre="Adaptativo",
            descripcion="Ataca si va perdiendo y se repliega si va ganando.",
            adapta=True,
            defensa=1.8,
            contra=0.6,
        ),
    )
}

IDS = tuple(PERFILES)

#: Cuánto tienta a la defensa cada carta antes de aplicar el perfil.
ATRACTIVO_DEFENSA: dict[Carta, float] = {
    Carta.ROBO_PELOTA: 0.42,
    Carta.CORTA_PASE: 0.35,
    Carta.TACKLE: 0.45,
    Carta.TRAMPA_OFFSIDE: 0.35,
    Carta.MARCA_PERSONAL: 0.40,
}


def perfil(id_perfil: str) -> Perfil:
    if id_perfil not in PERFILES:
        raise ValueError(
            f"Perfil desconocido: {id_perfil!r}. Disponibles: {', '.join(IDS)}"
        )
    return PERFILES[id_perfil]


def catalogo() -> list[dict[str, str]]:
    return [
        {"id": p.id, "nombre": p.nombre, "descripcion": p.descripcion}
        for p in PERFILES.values()
    ]


class Agente(Protocol):
    """Lo que el motor le pregunta a un jugador (simulado o humano)."""

    def accion(self, estado: EstadoPartido, posibles: list[str]) -> str: ...

    def receptor(self, estado: EstadoPartido, candidatos: list[Jugador]) -> Jugador: ...

    def reaccion(
        self, estado: EstadoPartido, contexto: str, opciones: list[Opcion]
    ) -> Opcion | None: ...

    def contra(
        self, estado: EstadoPartido, jugador: Jugador, contra: Carta, ante: Carta
    ) -> bool: ...


class AgenteIA:
    """Agente que juega según un perfil, o dos perfiles distintos por equipo."""

    def __init__(
        self,
        base: str = "estrategica",
        *,
        equipo0: str | None = None,
        equipo1: str | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self.base = perfil(base).id
        self.por_equipo = {
            0: perfil(equipo0).id if equipo0 else self.base,
            1: perfil(equipo1).id if equipo1 else self.base,
        }
        self.rng = rng or random.Random()

    def perfil_de(self, estado: EstadoPartido, equipo: int) -> Perfil:
        p = perfil(self.por_equipo[equipo])
        if not p.adapta:
            return p
        propios, rivales = estado.marcador.goles[equipo], estado.marcador.goles[1 - equipo]
        if propios < rivales:
            return perfil("agresiva")
        if propios > rivales:
            return perfil("conservador")
        return perfil("estrategica")

    def describir(self) -> str:
        if self.por_equipo[0] == self.por_equipo[1]:
            return perfil(self.base).nombre
        return f"{perfil(self.por_equipo[0]).nombre} vs {perfil(self.por_equipo[1]).nombre}"

    # --- decisiones -------------------------------------------------------

    def accion(self, estado: EstadoPartido, posibles: list[str]) -> str:
        opciones = pesos_ataque(estado, self.perfil_de(estado, estado.equipo_con_pelota), posibles)
        return _sortear([(a, p) for a, p, _ in opciones], self.rng)

    def receptor(self, estado: EstadoPartido, candidatos: list[Jugador]) -> Jugador:
        p = self.perfil_de(estado, estado.equipo_con_pelota)
        marcado = estado.jugador_marcado_por(estado.equipo_sin_pelota)
        if marcado is not None and marcado in candidatos:
            if p.busca_marca and self.rng.random() < 0.7:
                return marcado
            libres = [j for j in candidatos if j is not marcado]
            if p.evita_marca and libres:
                return self.rng.choice(libres)
        return self.rng.choice(candidatos)

    def reaccion(
        self, estado: EstadoPartido, contexto: str, opciones: list[Opcion]
    ) -> Opcion | None:
        p = self.perfil_de(estado, estado.equipo_sin_pelota)
        tentadoras = [
            (jugador, carta)
            for jugador, carta in opciones
            if self.rng.random() < min(0.95, ATRACTIVO_DEFENSA.get(carta, 0.3) * p.defensa)
        ]
        if not tentadoras:
            return None
        if p.busca_marca:
            marcas = [o for o in tentadoras if o[1] is Carta.MARCA_PERSONAL]
            if marcas:
                return self.rng.choice(marcas)
        return self.rng.choice(tentadoras)

    def contra(
        self, estado: EstadoPartido, jugador: Jugador, contra: Carta, ante: Carta
    ) -> bool:
        p = self.perfil_de(estado, jugador.equipo)
        return self.rng.random() < p.contra


def pesos_ataque(
    estado: EstadoPartido, p: Perfil, posibles: list[str]
) -> list[tuple[str, float, str]]:
    """Peso y motivo de cada acción disponible. Lo usa la IA y lo muestra la web."""
    pases = estado.pases
    salida: list[tuple[str, float, str]] = []
    for accion in posibles:
        if accion == "disparo":
            salida.append((accion, p.prob_disparo(pases), f"{pases} pases encadenados"))
        elif accion == "pase":
            peso = p.pase
            nota = "sigue la jugada"
            if estado.offside.get(estado.equipo_sin_pelota):
                peso *= 0.35
                nota = "hay trampa de offside puesta"
            salida.append((accion, peso, nota))
        elif accion == "reventar":
            peso = p.reventar if "pase" in posibles else 1.0
            nota = "despeje" if "pase" in posibles else "sin Pase en la mano"
            salida.append((accion, peso, nota))
        elif accion == "pasa_turno":
            peso = p.pasa_turno
            nota = "espera mejor jugada"
            if estado.offside.get(estado.equipo_sin_pelota):
                peso += 0.15
                nota = "evita el offside"
            salida.append((accion, peso, nota))
    salida.sort(key=lambda x: -x[1])
    return salida


def _sortear(opciones: list[tuple[str, float]], rng: random.Random) -> str:
    total = sum(max(0.0, peso) for _, peso in opciones)
    if total <= 0:
        return rng.choice([accion for accion, _ in opciones])
    tirada = rng.random() * total
    acumulado = 0.0
    for accion, peso in opciones:
        acumulado += max(0.0, peso)
        if tirada <= acumulado:
            return accion
    return opciones[-1][0]
