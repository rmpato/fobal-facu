"""Estado de un partido: jugadores, mazo, marcador y trampas en juego."""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass, field
from typing import Callable

from simulador.cartas import Carta
from simulador.eventos import Evento, nivel_de
from simulador.reglamento import Reglamento

Observador = Callable[[Evento], None]


@dataclass
class Jugador:
    id: int
    equipo: int
    nombre: str
    mano: list[Carta] = field(default_factory=list)

    def tiene(self, carta: Carta) -> bool:
        return carta in self.mano

    def descartar(self, carta: Carta) -> None:
        self.mano.remove(carta)


@dataclass
class Marcador:
    goles_para_ganar: int = 3
    penales_si_marcador: tuple[int, int] = (2, 2)
    goles: list[int] = field(default_factory=lambda: [0, 0])

    def anota(self, equipo: int) -> None:
        self.goles[equipo] += 1

    def ganador(self) -> int | None:
        for equipo, goles in enumerate(self.goles):
            if goles >= self.goles_para_ganar:
                return equipo
        return None

    def va_a_penales(self) -> bool:
        return tuple(self.goles) == self.penales_si_marcador


@dataclass
class EstadoPartido:
    """Todo lo que hace falta para seguir jugando un partido."""

    reglamento: Reglamento
    jugadores: list[Jugador]
    mazo: list[Carta]
    portador_id: int
    rng: random.Random
    semilla: int | None = None
    descarte: list[Carta] = field(default_factory=list)
    marcador: Marcador = field(default_factory=Marcador)
    turno: int = 0
    pases: int = 0
    barajadas: int = 0
    # Trampas en juego, indexadas por el equipo que las colocó (el defensor).
    offside: dict[int, bool] = field(default_factory=lambda: {0: False, 1: False})
    marca: dict[int, int | None] = field(default_factory=lambda: {0: None, 1: None})
    eventos: list[Evento] = field(default_factory=list)
    acciones: Counter[str] = field(default_factory=Counter)
    cartas_jugadas: Counter[str] = field(default_factory=Counter)
    terminado: bool = False
    motivo_fin: str = ""
    definido_por_penales: bool = False
    observador: Observador | None = field(default=None, repr=False)

    # --- consultas --------------------------------------------------------

    @property
    def portador(self) -> Jugador:
        return self.jugadores[self.portador_id]

    @property
    def equipo_con_pelota(self) -> int:
        return self.portador.equipo

    @property
    def equipo_sin_pelota(self) -> int:
        return 1 - self.equipo_con_pelota

    @property
    def jugadores_por_equipo(self) -> int:
        return len(self.jugadores) // 2

    def equipo(self, numero: int) -> list[Jugador]:
        return [j for j in self.jugadores if j.equipo == numero]

    def companeros(self, jugador: Jugador) -> list[Jugador]:
        return [j for j in self.jugadores if j.equipo == jugador.equipo and j is not jugador]

    def defensores(self) -> list[Jugador]:
        return self.equipo(self.equipo_sin_pelota)

    def nombre_equipo(self, numero: int) -> str:
        return f"Equipo {numero + 1}"

    def plantel(self, numero: int) -> str:
        return ", ".join(j.nombre for j in self.equipo(numero))

    def marcador_texto(self) -> str:
        g0, g1 = self.marcador.goles
        return f"{self.nombre_equipo(0)} {g0} - {g1} {self.nombre_equipo(1)}"

    def jugador_marcado_por(self, equipo_defensor: int) -> Jugador | None:
        jid = self.marca.get(equipo_defensor)
        return self.jugadores[jid] if jid is not None else None

    # --- eventos ----------------------------------------------------------

    def emitir(
        self,
        tipo: str,
        texto: str,
        *,
        nivel: str | None = None,
        jugadores: tuple[str, ...] = (),
        carta: Carta | None = None,
        **datos: object,
    ) -> None:
        evento = Evento(
            tipo=tipo,
            texto=texto,
            nivel=nivel or nivel_de(tipo),
            turno=self.turno,
            jugadores=jugadores,
            carta=carta.value if carta else None,
            marcador=(self.marcador.goles[0], self.marcador.goles[1]),
            datos=dict(datos),
        )
        self.eventos.append(evento)
        if self.observador:
            self.observador(evento)

    @property
    def relato(self) -> list[str]:
        """El partido como líneas de texto."""
        return [e.texto for e in self.eventos]

    # --- manipulación de cartas ------------------------------------------

    def registrar(self, accion: str) -> None:
        self.acciones[accion] += 1

    def jugar_carta(self, jugador: Jugador, carta: Carta) -> None:
        """Saca la carta de la mano, la descarta y la cuenta."""
        jugador.descartar(carta)
        self.descarte.append(carta)
        self.cartas_jugadas[carta.value] += 1

    def robar(self, jugador: Jugador, hasta: int) -> int:
        """Levanta cartas hasta ``hasta``. Devuelve cuántas levantó."""
        levantadas = 0
        while len(jugador.mano) < hasta:
            if not self.mazo:
                if not self.descarte:
                    break
                self.mazo = self.descarte
                self.descarte = []
                self.rng.shuffle(self.mazo)
                self.barajadas += 1
            jugador.mano.append(self.mazo.pop())
            levantadas += 1
        return levantadas

    def dado(self) -> int:
        return self.rng.randint(1, 6)

    def elegir(self, opciones: list[Jugador]) -> Jugador:
        return self.rng.choice(opciones)
