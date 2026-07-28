"""IA simple y estratégica para simular decisiones."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Callable

from simulador.cartas import Carta

if TYPE_CHECKING:
    from simulador.config import ConfigSimulacion
    from simulador.modelo import EstadoPartido, Jugador


def crear_ia(config: ConfigSimulacion) -> tuple[Callable, Callable]:
    if config.ia == "estrategica":
        return ia_accion_estrategica, ia_defensa_estrategica
    return ia_accion_simple, ia_defensa_simple


# --- IA simple (baseline anterior) ---


def ia_accion_simple(estado: EstadoPartido, portador: Jugador, es_receptor: bool = False):
    if es_receptor:
        companeros = estado.companeros(portador)
        return random.choice(companeros) if companeros else portador

    mano = portador.mano
    pases = estado.pases_en_jugada

    if Carta.DISPARO in mano:
        prob_disparo = 0.15 + min(pases, 4) * 0.12
        if random.random() < prob_disparo:
            return "disparo"

    if estado.reglamento and estado.reglamento.reventar_habilitado:
        if Carta.PASE not in mano:
            return "reventar"
        if random.random() < 0.10:
            return "reventar"
        if random.random() < 0.08:
            return "pasa_turno"
        return "pase"

    if Carta.PASE in mano and random.random() < 0.72:
        return "pase"
    if Carta.DISPARO in mano:
        return "disparo"
    if Carta.PASE in mano:
        return "pase"
    return "pasa_turno"


def ia_defensa_simple(estado: EstadoPartido, contexto: str = "pase"):
    return _defensa_base(estado, contexto, agresividad=1.0)


# --- IA estratégica ---


def ia_accion_estrategica(estado: EstadoPartido, portador: Jugador, es_receptor: bool = False):
    if es_receptor:
        companeros = estado.companeros(portador)
        if not companeros:
            return portador
        # Evitar compañero marcado si hay alternativa
        marca_id = estado.marca_sobre.get(estado.equipo_defensivo)
        sin_marca = [c for c in companeros if c.id != marca_id]
        pool = sin_marca if sin_marca else companeros
        return random.choice(pool)

    mano = portador.mano
    pases = estado.pases_en_jugada

    # Disparar con buena cadena de pases
    if Carta.DISPARO in mano:
        prob_disparo = 0.10 + min(pases, 4) * 0.18
        if pases >= 3:
            prob_disparo += 0.15
        if random.random() < prob_disparo:
            return "disparo"

    if estado.reglamento and estado.reglamento.reventar_habilitado:
        if Carta.PASE not in mano:
            return "reventar"

        prob_pasa_turno = _prob_pasa_turno_estrategica(estado, portador, pases)
        if random.random() < prob_pasa_turno:
            return "pasa_turno"

        if random.random() < 0.08:
            return "reventar"
        return "pase"

    # v0
    prob_pasa_turno = _prob_pasa_turno_estrategica(estado, portador, pases)
    if Carta.PASE in mano and random.random() < 0.65:
        return "pase"
    if Carta.DISPARO in mano and random.random() < 0.25 + min(pases, 3) * 0.1:
        return "disparo"
    if random.random() < prob_pasa_turno:
        return "pasa_turno"
    if Carta.PASE in mano:
        return "pase"
    return "pasa_turno"


def _prob_pasa_turno_estrategica(estado: EstadoPartido, portador: Jugador, pases: int) -> float:
    """Más probable cuando conviene armar trampa/marca o preparar disparo."""
    prob = 0.12
    if pases >= 1:
        prob += 0.10
    if pases >= 2 and Carta.DISPARO in portador.mano:
        prob += 0.14  # acumula pases antes de disparar
    if estado.offside_activo.get(estado.equipo_defensivo):
        prob -= 0.20  # no pasa de turno si hay offside pendiente
    if estado.marca_sobre.get(estado.equipo_defensivo) is not None:
        prob += 0.08  # ya hay marca, puede intentar pase al marcado
    return max(0.05, min(prob, 0.45))


def ia_defensa_estrategica(estado: EstadoPartido, contexto: str = "pase"):
    return _defensa_base(estado, contexto, agresividad=1.8)


def _defensa_base(estado: EstadoPartido, contexto: str, agresividad: float):
    defensores = estado.defensores()

    if contexto == "pasa_turno":
        candidatos = []
        for d in defensores:
            if d.tiene(Carta.TRAMPA_OFFSIDE) and random.random() < 0.35 * agresividad:
                candidatos.append((d, Carta.TRAMPA_OFFSIDE))
            if d.tiene(Carta.MARCA_PERSONAL) and random.random() < 0.40 * agresividad:
                candidatos.append((d, Carta.MARCA_PERSONAL))
            if estado.reglamento and estado.reglamento.motor_perfil == "v0" and d.tiene(Carta.TACKLE) and random.random() < 0.45 * agresividad:
                candidatos.append((d, Carta.TACKLE))
        if candidatos:
            return random.choice(candidatos)
        return None, None

    if contexto == "pase":
        candidatos = []
        for d in defensores:
            if estado.reglamento and estado.reglamento.motor_perfil == "v0" and d.tiene(Carta.CORTA_PASE) and random.random() < 0.35 * agresividad:
                candidatos.append((d, Carta.CORTA_PASE))
            elif estado.reglamento and estado.reglamento.motor_perfil == "v1" and d.tiene(Carta.ROBO_PELOTA) and random.random() < 0.42 * agresividad:
                candidatos.append((d, Carta.ROBO_PELOTA))
        return random.choice(candidatos) if candidatos else (None, None)

    return None, None


# Aliases para compatibilidad
ia_accion = ia_accion_simple
ia_defensa = ia_defensa_simple
