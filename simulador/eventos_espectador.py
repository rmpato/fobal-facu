"""Clasificación de eventos del relato para pausas, grabación y replay."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Tier = Literal["moment", "detail", "noise"]
TipoEvento = Literal[
    "turno",
    "gol",
    "pase",
    "disparo",
    "pasa_turno",
    "reventar",
    "robo",
    "defensa",
    "dado",
    "cambio_equipo",
    "penales",
    "fin",
    "empate",
    "info",
    "intro",
    "otro",
]

VELOCIDADES = ("lento", "normal", "rapido", "turbo")


@dataclass
class EventoEspectador:
    texto: str
    tier: Tier
    tipo: TipoEvento
    turno: int | None = None
    jugadores: list[str] = field(default_factory=list)
    carta: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_TURNO = re.compile(r"^T(\d+) \|")
_GOL = re.compile(r"\*\* GOL de (\w+)")


def _extraer_jugadores(msg: str) -> list[str]:
    nombres: list[str] = []
    for m in re.finditer(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", msg):
        token = m.group(1)
        if token in ("Marcador", "Fin", "Empate", "Serie", "Semilla", "Reglamento", "Equipo"):
            continue
        if token not in nombres:
            nombres.append(token)
    return nombres


def clasificar_evento(msg: str, *, turno: int | None = None) -> EventoEspectador:
    texto = msg.strip()
    if not texto:
        return EventoEspectador(texto=msg, tier="noise", tipo="otro")

    m_turno = _TURNO.match(texto)
    if m_turno:
        t = int(m_turno.group(1))
        return EventoEspectador(
            texto=msg,
            tier="moment",
            tipo="turno",
            turno=t,
            jugadores=_extraer_jugadores(texto),
        )

    if texto.startswith("** GOL") or "Penal convertido" in texto:
        m = _GOL.search(texto)
        jugador = m.group(1) if m else None
        return EventoEspectador(
            texto=msg,
            tier="moment",
            tipo="gol",
            turno=turno,
            jugadores=[jugador] if jugador else _extraer_jugadores(texto),
        )

    if texto.startswith("Fin") or texto.startswith("[FIN]"):
        return EventoEspectador(texto=msg, tier="moment", tipo="fin", turno=turno)

    if texto.startswith("Empate") or texto.startswith("Fin en penales"):
        return EventoEspectador(texto=msg, tier="moment", tipo="empate", turno=turno)

    if texto.startswith("--- Penales"):
        return EventoEspectador(texto=msg, tier="moment", tipo="penales", turno=turno)

    if texto.startswith(">> Cambio"):
        return EventoEspectador(texto=msg, tier="moment", tipo="cambio_equipo", turno=turno)

    if texto.startswith("Partido detenido"):
        return EventoEspectador(texto=msg, tier="moment", tipo="fin", turno=turno)

    if texto.startswith(">>") or texto.startswith("> "):
        return EventoEspectador(texto=msg, tier="moment", tipo="info", turno=turno)

    if texto.startswith("===") or texto[0] in "+|-=" or texto.startswith("  +"):
        return EventoEspectador(texto=msg, tier="noise", tipo="intro")

    if msg.startswith("  "):
        if any(
            k in texto
            for k in (
                "Disparo:",
                "Despeje:",
                "Rebote:",
                "Palo:",
                "Penal atajado",
                "Muerte súbita",
                "Tiran el dado",
            )
        ):
            return EventoEspectador(
                texto=msg,
                tier="detail",
                tipo="dado",
                turno=turno,
                jugadores=_extraer_jugadores(texto),
            )
        if any(
            k in texto
            for k in (
                "recupera la pelota",
                "coloca Trampa",
                "marca a",
                "gambetea",
                "La dejo pasar",
                "Offside",
                "Falta de",
                "Sin respuesta",
                "Gana ",
            )
        ):
            return EventoEspectador(
                texto=msg,
                tier="detail",
                tipo="defensa",
                turno=turno,
                jugadores=_extraer_jugadores(texto),
            )
        return EventoEspectador(texto=msg, tier="detail", tipo="otro", turno=turno)

    if " dispara al arco" in texto:
        return EventoEspectador(
            texto=msg,
            tier="moment",
            tipo="disparo",
            turno=turno,
            jugadores=_extraer_jugadores(texto),
            carta="Disparo al arco",
        )

    if " pasa a " in texto:
        return EventoEspectador(
            texto=msg,
            tier="moment",
            tipo="pase",
            turno=turno,
            jugadores=_extraer_jugadores(texto),
            carta="Pase",
        )

    if " pasa de turno" in texto:
        return EventoEspectador(
            texto=msg,
            tier="moment",
            tipo="pasa_turno",
            turno=turno,
            jugadores=_extraer_jugadores(texto),
        )

    if " revienta la pelota" in texto:
        return EventoEspectador(
            texto=msg,
            tier="moment",
            tipo="reventar",
            turno=turno,
            jugadores=_extraer_jugadores(texto),
        )

    if texto in ("Atajada o fuera",):
        return EventoEspectador(texto=msg, tier="detail", tipo="disparo", turno=turno)

    return EventoEspectador(
        texto=msg,
        tier="moment",
        tipo="otro",
        turno=turno,
        jugadores=_extraer_jugadores(texto),
    )


def debe_pausar(
    ev: EventoEspectador,
    *,
    velocidad: str,
    auto_pausa: bool,
    pausa_base_ms: int,
) -> bool:
    if not auto_pausa:
        return True
    if ev.tier == "noise":
        return False
    if velocidad == "lento":
        return True
    if velocidad == "normal":
        return ev.tier in ("moment", "detail")
    if velocidad == "rapido":
        return ev.tier == "moment"
    if velocidad == "turbo":
        if pausa_base_ms <= 0:
            return False
        return ev.tipo in ("gol", "fin", "turno", "penales", "empate", "cambio_equipo")
    return ev.tier == "moment"


def pausa_para_evento(
    ev: EventoEspectador,
    pausa_base_ms: int,
    *,
    velocidad: str,
) -> int:
    if pausa_base_ms <= 0:
        return 0
    mult = {"lento": 2.0, "normal": 1.0, "rapido": 0.5, "turbo": 0.25}.get(velocidad, 1.0)
    base = int(pausa_base_ms * mult)
    if ev.tipo == "gol":
        return int(base * 2.5)
    if ev.tipo == "turno":
        return int(base * 0.6)
    if ev.tier == "detail":
        return int(base * 0.4)
    return base
