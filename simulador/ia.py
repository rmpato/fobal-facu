"""Perfiles de IA para simular decisiones ofensivas y defensivas.

Documentación: docs/perfiles-ia.md
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Callable

from simulador.cartas import Carta

if TYPE_CHECKING:
    from simulador.config import ConfigSimulacion
    from simulador.modelo import EstadoPartido, Jugador

IDS_IA: tuple[str, ...] = (
    "simple",
    "estrategica",
    "agresiva",
    "paciente",
    "gambler",
    "conservador",
    "adaptativo",
    "marcador",
    "contragolpista",
)

NOMBRES_IA: dict[str, str] = {
    "simple": "Directo",
    "estrategica": "Táctico",
    "agresiva": "Presionante",
    "paciente": "Posicional",
    "gambler": "Arriesgado",
    "conservador": "Conservador",
    "adaptativo": "Adaptativo",
    "marcador": "Marcador",
    "contragolpista": "Contragolpista",
}


def nombre_ia(ia_id: str) -> str:
    return NOMBRES_IA.get(ia_id, ia_id)


def describir_ia_partido(config: ConfigSimulacion) -> str:
    if config.ia_equipo0 or config.ia_equipo1:
        n0 = nombre_ia(config.ia_de_equipo(0))
        n1 = nombre_ia(config.ia_de_equipo(1))
        return f"E1 {n0} vs E2 {n1}"
    return nombre_ia(config.ia)


def _adaptativo_resuelve(estado: EstadoPartido, equipo: int) -> str:
    g0, g1 = estado.marcador.goles
    propios = g0 if equipo == 0 else g1
    rivales = g1 if equipo == 0 else g0
    if propios < rivales:
        return "agresiva"
    if propios > rivales:
        return "conservador"
    return "estrategica"


def ia_resuelta(config: ConfigSimulacion, estado: EstadoPartido, equipo: int) -> str:
    ia_id = config.ia_de_equipo(equipo)
    if ia_id == "adaptativo":
        return _adaptativo_resuelve(estado, equipo)
    return ia_id


def agresividad_defensa(ia_id: str) -> float:
    return {
        "simple": 1.0,
        "estrategica": 1.8,
        "agresiva": 2.2,
        "paciente": 1.4,
        "gambler": 2.0,
        "conservador": 0.7,
        "adaptativo": 1.8,
        "marcador": 1.6,
        "contragolpista": 1.5,
    }.get(ia_id, 1.0)


def _elegir_receptor(
    estado: EstadoPartido,
    portador: Jugador,
    *,
    evitar_marcado: bool = True,
    preferir_marcado: bool = False,
) -> Jugador:
    companeros = estado.companeros(portador)
    if not companeros:
        return portador
    marca_id = estado.marca_sobre.get(estado.equipo_defensivo)
    if preferir_marcado and marca_id is not None:
        marcados = [c for c in companeros if c.id == marca_id]
        if marcados and random.random() < 0.70:
            return random.choice(marcados)
    if evitar_marcado and marca_id is not None:
        sin_marca = [c for c in companeros if c.id != marca_id]
        if sin_marca:
            return random.choice(sin_marca)
    return random.choice(companeros)


def _prob_disparo(estado: EstadoPartido, ia_id: str) -> float:
    pases = estado.pases_en_jugada
    if ia_id == "agresiva":
        return 0.25 + min(pases, 3) * 0.15
    if ia_id == "paciente":
        if pases < 3:
            return 0.05
        return 0.08 + min(pases - 2, 4) * 0.10
    if ia_id == "gambler":
        return 0.20 + min(pases, 4) * 0.14
    if ia_id == "conservador":
        if pases < 4:
            return 0.04
        return 0.35
    if ia_id == "contragolpista":
        if pases <= 1:
            return 0.45
        return 0.12 + min(pases, 3) * 0.08
    if ia_id == "estrategica":
        prob = 0.10 + min(pases, 4) * 0.18
        if pases >= 3:
            prob += 0.15
        return prob
    return 0.15 + min(pases, 4) * 0.12


def _prob_pasa_turno(estado: EstadoPartido, portador: Jugador, ia_id: str) -> float:
    pases = estado.pases_en_jugada
    if ia_id == "agresiva":
        return 0.03
    if ia_id == "paciente":
        prob = 0.22
        if pases >= 1:
            prob += 0.12
        if Carta.DISPARO in portador.mano:
            prob += 0.10
        return min(prob, 0.50)
    if ia_id == "gambler":
        return 0.15
    if ia_id == "conservador":
        return 0.05
    if ia_id == "marcador":
        if estado.marca_sobre.get(estado.equipo_defensivo) is None:
            return 0.38
        return 0.18
    if ia_id == "contragolpista":
        return 0.06 if pases <= 1 else 0.12
    if ia_id == "estrategica":
        prob = 0.12
        if pases >= 1:
            prob += 0.10
        if pases >= 2 and Carta.DISPARO in portador.mano:
            prob += 0.14
        if estado.offside_activo.get(estado.equipo_defensivo):
            prob -= 0.20
        if estado.marca_sobre.get(estado.equipo_defensivo) is not None:
            prob += 0.08
        return max(0.05, min(prob, 0.45))
    if estado.reglamento and estado.reglamento.reventar_habilitado:
        return 0.08
    return 0.0


def _prob_pase_base(ia_id: str) -> float:
    return {
        "simple": 0.82,
        "estrategica": 0.75,
        "agresiva": 0.70,
        "paciente": 0.68,
        "gambler": 0.55,
        "conservador": 0.88,
        "marcador": 0.72,
        "contragolpista": 0.50,
    }.get(ia_id, 0.72)


def _prob_reventar(ia_id: str, pases: int) -> float:
    if ia_id == "gambler":
        return 0.18
    if ia_id == "contragolpista" and pases <= 1:
        return 0.22
    if ia_id == "agresiva":
        return 0.12
    return 0.08


def pesos_ataque(
    estado: EstadoPartido, ia_id: str
) -> list[tuple[str, float, str]]:
    """Pesos aproximados para el panel de anticipo (accion, prob, nota)."""
    portador = estado.portador
    mano = portador.mano
    reg = estado.reglamento
    pases = estado.pases_en_jugada
    opciones: list[tuple[str, float, str]] = []
    permite_pasa_turno = not reg or reg.accion_ofensiva_permitida("pasa_turno")

    if Carta.DISPARO in mano:
        opciones.append(("disparo", _prob_disparo(estado, ia_id), f"cadena {pases}"))

    if reg and reg.reventar_habilitado:
        if Carta.PASE not in mano:
            opciones.append(("reventar", 1.0, "sin Pase"))
        else:
            opciones.append(("pase", _prob_pase_base(ia_id), "sigue jugada"))
            opciones.append(("reventar", _prob_reventar(ia_id, pases), "despeje"))
            if permite_pasa_turno:
                opciones.append(
                    ("pasa turno", _prob_pasa_turno(estado, portador, ia_id), "trampa/marca")
                )
    else:
        if Carta.PASE in mano:
            pase_p = 0.72 if ia_id == "simple" else _prob_pase_base(ia_id)
            opciones.append(("pase", pase_p, "mantiene"))
        if permite_pasa_turno:
            pt = _prob_pasa_turno(estado, portador, ia_id)
            if pt > 0:
                opciones.append(("pasa turno", pt, "armar trampa"))
        if Carta.DISPARO in mano and ia_id in ("estrategica", "gambler", "agresiva"):
            extra = _prob_disparo(estado, ia_id)
            opciones.append(("disparo", extra, f"cadena {pases}"))

    if not opciones:
        if Carta.PASE in mano:
            opciones.append(("pase", 0.5, ""))
        elif Carta.DISPARO in mano:
            opciones.append(("disparo", 0.5, ""))
        else:
            opciones.append(("pasa turno", 0.5, ""))

    opciones.sort(key=lambda x: x[1], reverse=True)
    return opciones[:3]


def _accion_ofensiva(
    estado: EstadoPartido, portador: Jugador, ia_id: str, *, es_receptor: bool
):
    if es_receptor:
        return _elegir_receptor(
            estado,
            portador,
            evitar_marcado=ia_id not in ("marcador", "gambler"),
            preferir_marcado=ia_id == "marcador",
        )

    mano = portador.mano
    pases = estado.pases_en_jugada
    reg = estado.reglamento
    permite_pasa_turno = not reg or reg.accion_ofensiva_permitida("pasa_turno")

    if Carta.DISPARO in mano and random.random() < _prob_disparo(estado, ia_id):
        return "disparo"

    if reg and reg.reventar_habilitado:
        if Carta.PASE not in mano:
            return "reventar"
        if permite_pasa_turno:
            pt = _prob_pasa_turno(estado, portador, ia_id)
            if random.random() < pt:
                return "pasa_turno"
        if random.random() < _prob_reventar(ia_id, pases):
            return "reventar"
        if Carta.PASE in mano:
            return "pase"
        return "reventar"

    pt = _prob_pasa_turno(estado, portador, ia_id)
    if Carta.PASE in mano and random.random() < _prob_pase_base(ia_id):
        return "pase"
    if Carta.DISPARO in mano and random.random() < _prob_disparo(estado, ia_id):
        return "disparo"
    if permite_pasa_turno and random.random() < pt:
        return "pasa_turno"
    if Carta.PASE in mano:
        return "pase"
    if reg and reg.reventar_habilitado:
        return "reventar"
    return "pasa_turno" if permite_pasa_turno else "reventar"


def _defensa_base(
    estado: EstadoPartido,
    contexto: str,
    *,
    agresividad: float,
    favorecer_marca: bool = False,
):
    defensores = estado.defensores()

    if contexto == "pasa_turno":
        candidatos = []
        for d in defensores:
            if d.tiene(Carta.TRAMPA_OFFSIDE) and random.random() < 0.35 * agresividad:
                candidatos.append((d, Carta.TRAMPA_OFFSIDE))
            prob_marca = (0.70 if favorecer_marca else 0.40) * agresividad
            if d.tiene(Carta.MARCA_PERSONAL) and random.random() < prob_marca:
                candidatos.append((d, Carta.MARCA_PERSONAL))
            if (
                estado.reglamento
                and estado.reglamento.motor_perfil == "v0"
                and d.tiene(Carta.TACKLE)
                and random.random() < 0.45 * agresividad
            ):
                candidatos.append((d, Carta.TACKLE))
        if candidatos:
            return random.choice(candidatos)
        return None, None

    if contexto == "pase":
        candidatos = []
        cartas_pase = (
            estado.reglamento.reacciones_pase.cartas
            if estado.reglamento
            else [Carta.ROBO_PELOTA]
        )
        for d in defensores:
            for carta in cartas_pase:
                if not d.tiene(carta):
                    continue
                if carta == Carta.CORTA_PASE and estado.reglamento and estado.reglamento.motor_perfil == "v0":
                    prob = 0.35 * agresividad
                elif carta == Carta.ROBO_PELOTA:
                    prob = 0.42 * agresividad
                elif carta in (Carta.TRAMPA_OFFSIDE, Carta.MARCA_PERSONAL):
                    prob = 0.35 * agresividad
                else:
                    prob = 0.30 * agresividad
                if random.random() < prob:
                    candidatos.append((d, carta))
        return random.choice(candidatos) if candidatos else (None, None)

    return None, None


def _defensa_perfil(estado: EstadoPartido, contexto: str, ia_id: str):
    fav_marca = ia_id == "marcador"
    return _defensa_base(
        estado,
        contexto,
        agresividad=agresividad_defensa(ia_id),
        favorecer_marca=fav_marca,
    )


def _perfil_ia(ia_id: str) -> tuple[Callable, Callable]:
    def accion(estado: EstadoPartido, portador: Jugador, es_receptor: bool = False):
        return _accion_ofensiva(estado, portador, ia_id, es_receptor=es_receptor)

    def defensa(estado: EstadoPartido, contexto: str = "pase"):
        return _defensa_perfil(estado, contexto, ia_id)

    return accion, defensa


_PERFILES: dict[str, tuple[Callable, Callable]] = {
    ia_id: _perfil_ia(ia_id) for ia_id in IDS_IA if ia_id != "adaptativo"
}


def crear_ia(config: ConfigSimulacion) -> tuple[Callable, Callable]:
    usadas = {config.ia, config.ia_equipo0, config.ia_equipo1} - {None}
    for ia_id in usadas:
        if ia_id not in IDS_IA:
            raise ValueError(f"IA desconocida: {ia_id}")
        if ia_id != "adaptativo" and ia_id not in _PERFILES:
            _PERFILES[ia_id] = _perfil_ia(ia_id)

    def accion(estado: EstadoPartido, portador: Jugador, es_receptor: bool = False):
        ia_id = ia_resuelta(config, estado, portador.equipo)
        accion_fn, _ = _PERFILES.get(ia_id, _perfil_ia("estrategica"))
        return accion_fn(estado, portador, es_receptor)

    def defensa(estado: EstadoPartido, contexto: str = "pase"):
        ia_id = ia_resuelta(config, estado, estado.equipo_defensivo)
        _, defensa_fn = _PERFILES.get(ia_id, _perfil_ia("estrategica"))
        return defensa_fn(estado, contexto)

    return accion, defensa


# Aliases históricos
ia_accion_simple = _perfil_ia("simple")[0]
ia_defensa_simple = _perfil_ia("simple")[1]
ia_accion_estrategica = _perfil_ia("estrategica")[0]
ia_defensa_estrategica = _perfil_ia("estrategica")[1]
ia_accion = ia_accion_simple
ia_defensa = ia_defensa_simple
