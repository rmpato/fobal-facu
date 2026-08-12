"""Eventos del partido.

El motor no escribe texto suelto: emite eventos con tipo y protagonistas. El
relato de terminal, la web y las grabaciones consumen la misma lista, así que
todos cuentan exactamente el mismo partido.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

#: Eventos que resumen el partido; el relato rápido muestra solo estos.
CLAVE = "clave"
#: Eventos de resolución fina (tiradas de dado, respuestas defensivas).
DETALLE = "detalle"

TIPOS = (
    "inicio",
    "turno",
    "pase",
    "disparo",
    "dado",
    "gol",
    "atajada",
    "reventar",
    "pasa_turno",
    "robo",
    "gambeta",
    "trampa",
    "marca",
    "offside",
    "falta",
    "cambio_equipo",
    "reposicion",
    "penales",
    "fin",
)

#: Tipos que solo interesan si se quiere ver la resolución completa.
DETALLADOS = frozenset({"dado", "reposicion", "cambio_equipo"})


def nivel_de(tipo: str) -> str:
    """El relato normal muestra los eventos clave; el detallado, todos."""
    return DETALLE if tipo in DETALLADOS else CLAVE


@dataclass(frozen=True)
class Evento:
    tipo: str
    texto: str
    nivel: str = DETALLE
    turno: int = 0
    jugadores: tuple[str, ...] = ()
    carta: str | None = None
    marcador: tuple[int, int] = (0, 0)
    datos: dict[str, Any] = field(default_factory=dict)

    def a_dict(self) -> dict[str, Any]:
        salida = {
            "tipo": self.tipo,
            "texto": self.texto,
            "nivel": self.nivel,
            "turno": self.turno,
            "jugadores": list(self.jugadores),
            "marcador": list(self.marcador),
        }
        if self.carta:
            salida["carta"] = self.carta
        if self.datos:
            salida["datos"] = self.datos
        return salida

    @classmethod
    def desde_dict(cls, data: dict[str, Any]) -> Evento:
        marcador = data.get("marcador", [0, 0])
        return cls(
            tipo=data.get("tipo", "otro"),
            texto=data.get("texto", ""),
            nivel=data.get("nivel", DETALLE),
            turno=int(data.get("turno", 0)),
            jugadores=tuple(data.get("jugadores", ())),
            carta=data.get("carta"),
            marcador=(int(marcador[0]), int(marcador[1])),
            datos=data.get("datos", {}),
        )
