"""IA simple para simular decisiones humanas aproximadas."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from simulador.cartas import Carta

if TYPE_CHECKING:
    from simulador.modelo import EstadoPartido, Jugador


def ia_accion(estado, portador: Jugador, es_receptor: bool = False):
    if es_receptor:
        companeros = estado.companeros(portador)
        return random.choice(companeros) if companeros else portador

    mano = portador.mano
    pases = estado.pases_en_jugada

    # Más pases → más chance de disparar (mejor tabla)
    if Carta.DISPARO in mano:
        prob_disparo = 0.15 + min(pases, 4) * 0.12
        if random.random() < prob_disparo:
            return "disparo"

    if estado.reglas == "v1":
        if Carta.PASE not in mano:
            return "reventar"
        if random.random() < 0.10:
            return "reventar"
        if random.random() < 0.08:
            return "pasa_turno"
        return "pase"

    # v0
    if Carta.PASE in mano and random.random() < 0.72:
        return "pase"
    if Carta.DISPARO in mano:
        return "disparo"
    if Carta.PASE in mano:
        return "pase"
    return "pasa_turno"


def ia_defensa(estado, contexto: str = "pase"):
    defensores = estado.defensores()

    if contexto == "pasa_turno":
        candidatos = []
        for d in defensores:
            if d.tiene(Carta.TRAMPA_OFFSIDE) and random.random() < 0.25:
                candidatos.append((d, Carta.TRAMPA_OFFSIDE))
            elif d.tiene(Carta.MARCA_PERSONAL) and random.random() < 0.30:
                candidatos.append((d, Carta.MARCA_PERSONAL))
            elif estado.reglas == "v0" and d.tiene(Carta.TACKLE) and random.random() < 0.45:
                candidatos.append((d, Carta.TACKLE))
        return random.choice(candidatos) if candidatos else (None, None)

    if contexto == "pase":
        candidatos = []
        for d in defensores:
            if estado.reglas == "v0" and d.tiene(Carta.CORTA_PASE) and random.random() < 0.35:
                candidatos.append((d, Carta.CORTA_PASE))
            elif estado.reglas == "v1" and d.tiene(Carta.ROBO_PELOTA) and random.random() < 0.4:
                candidatos.append((d, Carta.ROBO_PELOTA))
        return random.choice(candidatos) if candidatos else (None, None)

    return None, None
