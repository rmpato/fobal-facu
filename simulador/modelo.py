"""Estado del partido y jugadores."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from simulador.cartas import Carta

if TYPE_CHECKING:
    from simulador.config import ConfigSimulacion
    from simulador.reglamento import Reglamento


@dataclass
class Jugador:
    id: int
    equipo: int
    nombre: str
    mano: list[Carta] = field(default_factory=list)

    def tiene(self, carta: Carta) -> bool:
        return carta in self.mano

    def jugar(self, carta: Carta) -> None:
        self.mano.remove(carta)

    def repone_hasta(self, objetivo: int, mazo: list[Carta], descarte: list[Carta]) -> int:
        """Repone cartas hasta `objetivo`. Devuelve cuántas repuso."""
        repuestas = 0
        while len(self.mano) < objetivo:
            if not mazo:
                if not descarte:
                    break
                mazo.extend(descarte)
                descarte.clear()
            carta = mazo.pop()
            self.mano.append(carta)
            repuestas += 1
        return repuestas


@dataclass
class Marcador:
    goles: list[int] = field(default_factory=lambda: [0, 0])
    goles_para_ganar: int = 3
    penales_si_marcador: tuple[int, int] = (2, 2)

    def anota(self, equipo: int) -> None:
        self.goles[equipo] += 1

    def es_empate_penales(self) -> bool:
        return tuple(self.goles) == self.penales_si_marcador

    def es_empate_2_2(self) -> bool:
        return self.es_empate_penales()

    def hay_ganador(self) -> int | None:
        for i, g in enumerate(self.goles):
            if g >= self.goles_para_ganar:
                return i
        return None


@dataclass
class EstadoPartido:
    reglamento_id: str
    jugadores_por_equipo: int
    jugadores: list[Jugador]
    mazo: list[Carta]
    descarte: list[Carta]
    portador_id: int
    pases_en_jugada: int = 0
    turnos: int = 0
    barajadas_descarte: int = 0
    # Trampas activas: jugador marcado / offside activo por equipo defensor
    offside_activo: dict[int, bool] = field(default_factory=lambda: {0: False, 1: False})
    marca_sobre: dict[int, int | None] = field(default_factory=lambda: {0: None, 1: None})
    marcador: Marcador = field(default_factory=Marcador)
    log: list[str] = field(default_factory=list)
    cartas_jugadas: dict[str, int] = field(default_factory=dict)
    acciones: dict[str, int] = field(default_factory=dict)
    definido_por_penales: bool = False
    config: ConfigSimulacion | None = None
    reglamento: Reglamento | None = None

    @property
    def reglas(self) -> str:
        if self.reglamento:
            return self.reglamento.motor_perfil
        return self.reglamento_id

    @property
    def portador(self) -> Jugador:
        return self.jugadores[self.portador_id]

    @property
    def equipo_ofensivo(self) -> int:
        return self.portador.equipo

    @property
    def equipo_defensivo(self) -> int:
        return 1 - self.equipo_ofensivo

    def companeros(self, jugador: Jugador) -> list[Jugador]:
        return [j for j in self.jugadores if j.equipo == jugador.equipo and j.id != jugador.id]

    def rivales(self, jugador: Jugador) -> list[Jugador]:
        return [j for j in self.jugadores if j.equipo != jugador.equipo]

    def defensores(self) -> list[Jugador]:
        return [j for j in self.jugadores if j.equipo == self.equipo_defensivo]

    def registrar_carta(self, carta: Carta) -> None:
        clave = carta.value
        self.cartas_jugadas[clave] = self.cartas_jugadas.get(clave, 0) + 1

    def registrar_accion(self, accion: str) -> None:
        self.acciones[accion] = self.acciones.get(accion, 0) + 1

    def descartar(self, carta: Carta) -> None:
        self.descarte.append(carta)

    def cambiar_posesion(self, nuevo_portador_id: int, cambio_equipo: bool) -> None:
        if cambio_equipo:
            self._reposicion_cambio_equipo()
            self.pases_en_jugada = 0
            self.offside_activo = {0: False, 1: False}
            self.marca_sobre = {0: None, 1: None}
        self.portador_id = nuevo_portador_id

    def reset_pases(self) -> None:
        self.pases_en_jugada = 0

    def _reposicion_cambio_equipo(self) -> None:
        for j in self.jugadores:
            antes = len(j.mano)
            j.repone_hasta(6, self.mazo, self.descarte)
            if antes < 6 and not self.mazo and self.descarte:
                self.barajadas_descarte += 1

    def reposicion_v0_mano_vacia(self, jugador: Jugador) -> None:
        if len(jugador.mano) == 0:
            jugador.repone_hasta(6, self.mazo, self.descarte)

    def log_evento(self, msg: str) -> None:
        self.log.append(msg)
