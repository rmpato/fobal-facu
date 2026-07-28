"""Motor de partido: lógica compartida y variantes v0/v1."""

from __future__ import annotations

import random
from typing import Callable

from simulador.cartas import (
    MAZO_V0,
    MAZO_V1,
    Carta,
    construir_mazo,
    tabla_para_pases,
)
from simulador.modelo import EstadoPartido, Jugador, Marcador

LIMITE_TURNOS = 500
MANO_INICIAL = 6


def crear_partido(
    reglas: str,
    jugadores_por_equipo: int = 2,
    semilla: int | None = None,
) -> EstadoPartido:
    if jugadores_por_equipo < 2:
        raise ValueError("Se requieren al menos 2 jugadores por equipo")
    if semilla is not None:
        random.seed(semilla)

    config = MAZO_V0 if reglas == "v0" else MAZO_V1
    mazo = construir_mazo(config)
    random.shuffle(mazo)

    jugadores: list[Jugador] = []
    jid = 0
    for equipo in (0, 1):
        for n in range(jugadores_por_equipo):
            jugadores.append(Jugador(id=jid, equipo=equipo, nombre=f"E{equipo}-J{n + 1}"))
            jid += 1

    for j in jugadores:
        for _ in range(MANO_INICIAL):
            if mazo:
                j.mano.append(mazo.pop())

    equipo_inicio = random.randint(0, 1)
    portador_id = random.choice([j.id for j in jugadores if j.equipo == equipo_inicio])
    return EstadoPartido(
        reglas=reglas,
        jugadores_por_equipo=jugadores_por_equipo,
        jugadores=jugadores,
        mazo=mazo,
        descarte=[],
        portador_id=portador_id,
    )


def _dado() -> int:
    return random.randint(1, 6)


def _es_gol(dado: int, pases: int) -> bool:
    t = tabla_para_pases(pases)
    return t.gol_min <= dado <= t.gol_max


def _es_atajada(dado: int, pases: int) -> bool:
    t = tabla_para_pases(pases)
    return t.ataja_min <= dado <= t.ataja_max


def fase_disparo(
    estado: EstadoPartido,
    pateador: Jugador,
    arquero: Jugador,
    pases: int,
    rebote_palo: bool,
) -> bool:
    """Devuelve True si hubo gol."""
    for _ in range(15):
        d_p = _dado()
        d_a = _dado()
        estado.log_evento(
            f"  Disparo: {pateador.nombre}={d_p}, arquero {arquero.nombre}={d_a} "
            f"(pases={pases})"
        )
        gol = _es_gol(d_p, pases)
        ataja = _es_atajada(d_a, pases)

        if rebote_palo and gol and ataja:
            estado.log_evento("  Rebote: se vuelve a patear")
            continue
        if rebote_palo and d_p == d_a:
            estado.log_evento("  Palo: se vuelve a patear")
            continue
        if gol and not ataja:
            return True
        return False
    return False


def resolver_penales(estado: EstadoPartido, rebote_palo: bool) -> int:
    """Devuelve índice del equipo ganador."""
    n = estado.jugadores_por_equipo
    estado.log_evento("--- Penales ---")

    def ronda(cantidad: int) -> tuple[int, int]:
        goles = [0, 0]
        for i in range(cantidad):
            for equipo in (0, 1):
                pateadores = [j for j in estado.jugadores if j.equipo == equipo]
                arqueros = [j for j in estado.jugadores if j.equipo != equipo]
                p = pateadores[i % len(pateadores)]
                a = arqueros[i % len(arqueros)]
                if fase_disparo(estado, p, a, pases=0, rebote_palo=rebote_palo):
                    goles[equipo] += 1
                    estado.log_evento(f"  Penal convertido: {p.nombre}")
                else:
                    estado.log_evento(f"  Penal atajado/errado: {p.nombre}")
        return goles[0], goles[1]

    g0, g1 = ronda(n)
    estado.log_evento(f"  Serie: {g0}-{g1}")
    if g0 != g1:
        return 0 if g0 > g1 else 1

    # Muerte súbita
    intentos = 0
    while intentos < 20:
        intentos += 1
        for equipo in (0, 1):
            pateadores = [j for j in estado.jugadores if j.equipo == equipo]
            arqueros = [j for j in estado.jugadores if j.equipo != equipo]
            p = random.choice(pateadores)
            a = random.choice(arqueros)
            convierte = fase_disparo(estado, p, a, pases=0, rebote_palo=rebote_palo)
            otro = 1 - equipo
            p2 = random.choice([j for j in estado.jugadores if j.equipo == otro])
            a2 = random.choice([j for j in estado.jugadores if j.equipo != otro])
            convierte2 = fase_disparo(estado, p2, a2, pases=0, rebote_palo=rebote_palo)
            if convierte and not convierte2:
                return equipo
            if convierte2 and not convierte:
                return otro
        estado.log_evento("  Muerte súbita: empate, otra ronda")
    return random.randint(0, 1)


def _transferir_pelota(
    estado: EstadoPartido,
    nuevo_portador: Jugador,
    incrementar_pase: bool = False,
    limpiar_trampas: bool = True,
) -> None:
    cambio_equipo = nuevo_portador.equipo != estado.equipo_ofensivo
    if incrementar_pase and not cambio_equipo:
        estado.pases_en_jugada += 1
    if limpiar_trampas and not cambio_equipo:
        estado.marca_sobre[estado.equipo_defensivo] = None
    estado.cambiar_posesion(nuevo_portador.id, cambio_equipo=cambio_equipo)


def _robo_pelota(estado: EstadoPartido, defensor: Jugador) -> None:
    estado.log_evento(f"  {defensor.nombre} recupera la pelota")
    estado.reset_pases()
    _transferir_pelota(estado, defensor, incrementar_pase=False)


def _intentar_falta(
    estado: EstadoPartido,
    candidatos: list[Jugador],
    probabilidad: float,
) -> bool:
    """Si alguien juega Falta, resetea pases y termina la acción."""
    for j in candidatos:
        if j.tiene(Carta.FALTA) and random.random() < probabilidad:
            j.jugar(Carta.FALTA)
            estado.descartar(Carta.FALTA)
            estado.registrar_carta(Carta.FALTA)
            estado.reset_pases()
            estado.log_evento(f"  Falta de {j.nombre}: pelota sigue en el mismo equipo")
            return True
    return False


def _disparo_al_arco(estado: EstadoPartido, rebote_palo: bool) -> None:
    portador = estado.portador
    portador.jugar(Carta.DISPARO)
    estado.descartar(Carta.DISPARO)
    estado.registrar_carta(Carta.DISPARO)
    arquero = random.choice(estado.defensores())
    pases = estado.pases_en_jugada
    estado.log_evento(f"{portador.nombre} dispara al arco")
    if fase_disparo(estado, portador, arquero, pases, rebote_palo):
        estado.marcador.anota(portador.equipo)
        estado.log_evento(f"¡GOL! Marcador: {estado.marcador.goles}")
    else:
        estado.log_evento("Atajada o fuera")
    # Tras disparo: saque del arquero (equipo defensor)
    nuevo = random.choice(estado.defensores())
    estado.reset_pases()
    _transferir_pelota(estado, nuevo)


def _duelo_reventar(estado: EstadoPartido, portador: Jugador) -> None:
    estado.log_evento(f"{portador.nombre} revienta la pelota")
    atacantes = [j for j in estado.companeros(portador) if j.id != portador.id]
    defensores = estado.defensores()
    if not atacantes:
        atacantes = [portador]  # fallback 1v1 sim
    a = random.choice(atacantes) if atacantes else portador
    d = random.choice(defensores)
    for _ in range(20):
        da = _dado()
        dd = _dado()
        estado.log_evento(f"  Despeje: {a.nombre}={da} vs {d.nombre}={dd}")
        if da == dd:
            continue
        ganador = a if da > dd else d
        mismo_equipo = ganador.equipo == portador.equipo
        if mismo_equipo:
            estado.pases_en_jugada += 1
        estado.log_evento(f"  Gana {ganador.nombre}" + (" (cuenta como pase)" if mismo_equipo else ""))
        _transferir_pelota(estado, ganador, incrementar_pase=False)
        return
    _transferir_pelota(estado, random.choice(defensores))


def _resolver_pasa_de_turno(
    estado: EstadoPartido,
    portador: Jugador,
    elegir_defensa: Callable,
    *,
    permitir_tackle: bool,
) -> None:
    """Ataque retiene la pelota sin pasar ni disparar. Defensa puede trampa/marca (y tackle en v0)."""
    estado.log_evento(f"{portador.nombre} pasa de turno")
    defensor, carta_def = elegir_defensa(estado, contexto="pasa_turno")

    if defensor and carta_def == Carta.TRAMPA_OFFSIDE:
        defensor.jugar(Carta.TRAMPA_OFFSIDE)
        estado.descartar(Carta.TRAMPA_OFFSIDE)
        estado.registrar_carta(Carta.TRAMPA_OFFSIDE)
        estado.offside_activo[estado.equipo_defensivo] = True
        estado.log_evento(f"  {defensor.nombre} coloca Trampa de offside")
        return

    if defensor and carta_def == Carta.MARCA_PERSONAL:
        objetivo = random.choice(estado.companeros(portador) or estado.jugadores)
        defensor.jugar(Carta.MARCA_PERSONAL)
        estado.descartar(Carta.MARCA_PERSONAL)
        estado.registrar_carta(Carta.MARCA_PERSONAL)
        estado.marca_sobre[estado.equipo_defensivo] = objetivo.id
        estado.log_evento(f"  {defensor.nombre} marca a {objetivo.nombre}")
        return

    if permitir_tackle and defensor and carta_def == Carta.TACKLE:
        defensor.jugar(Carta.TACKLE)
        estado.descartar(Carta.TACKLE)
        estado.registrar_carta(Carta.TACKLE)
        if portador.tiene(Carta.GAMBETEAR) and random.random() < 0.6:
            portador.jugar(Carta.GAMBETEAR)
            estado.descartar(Carta.GAMBETEAR)
            estado.registrar_carta(Carta.GAMBETEAR)
            estado.log_evento(f"  {portador.nombre} gambetea el tackle")
            return
        _robo_pelota(estado, defensor)


# --- v0 ---


def turno_v0(estado: EstadoPartido, elegir_accion: Callable, elegir_defensa: Callable) -> None:
    portador = estado.portador
    accion = elegir_accion(estado, portador)

    # Falta oportunista
    todos = estado.jugadores[:]
    random.shuffle(todos)
    if _intentar_falta(estado, todos, probabilidad=0.08):
        return

    if accion == "disparo":
        if portador.tiene(Carta.DISPARO):
            _disparo_al_arco(estado, rebote_palo=False)
        return

    if accion == "pasa_turno":
        _resolver_pasa_de_turno(estado, portador, elegir_defensa, permitir_tackle=True)
        return

    # Pase
    if not portador.tiene(Carta.PASE):
        if portador.tiene(Carta.DISPARO):
            _disparo_al_arco(estado, rebote_palo=False)
        else:
            _resolver_pasa_de_turno(estado, portador, elegir_defensa, permitir_tackle=True)
        return

    if estado.offside_activo.get(estado.equipo_defensivo):
        estado.offside_activo[estado.equipo_defensivo] = False
        estado.log_evento("  ¡Offside! Pierde la pelota")
        _robo_pelota(estado, random.choice(estado.defensores()))
        return

    receptor = elegir_accion(estado, portador, es_receptor=True)
    portador.jugar(Carta.PASE)
    estado.descartar(Carta.PASE)
    estado.registrar_carta(Carta.PASE)
    estado.log_evento(f"{portador.nombre} pasa a {receptor.nombre}")

    marca_id = estado.marca_sobre.get(estado.equipo_defensivo)
    if marca_id is not None and receptor.id == marca_id:
        estado.marca_sobre[estado.equipo_defensivo] = None
        defensor_marca = next(d for d in estado.defensores() if True)
        if receptor.tiene(Carta.LA_DEJO_PASAR) and random.random() < 0.7:
            receptor.jugar(Carta.LA_DEJO_PASAR)
            estado.descartar(Carta.LA_DEJO_PASAR)
            estado.registrar_carta(Carta.LA_DEJO_PASAR)
            estado.log_evento(f"  {receptor.nombre}: La dejo pasar")
        else:
            d = random.choice(estado.defensores())
            _robo_pelota(estado, d)
            return

    defensor, carta_def = elegir_defensa(estado, contexto="pase")
    if defensor and carta_def == Carta.CORTA_PASE:
        defensor.jugar(Carta.CORTA_PASE)
        estado.descartar(Carta.CORTA_PASE)
        estado.registrar_carta(Carta.CORTA_PASE)
        if receptor.tiene(Carta.LA_DEJO_PASAR) and random.random() < 0.7:
            receptor.jugar(Carta.LA_DEJO_PASAR)
            estado.descartar(Carta.LA_DEJO_PASAR)
            estado.registrar_carta(Carta.LA_DEJO_PASAR)
            estado.log_evento(f"  {receptor.nombre}: La dejo pasar")
            _transferir_pelota(estado, receptor, incrementar_pase=True)
        else:
            _robo_pelota(estado, defensor)
        return

    _transferir_pelota(estado, receptor, incrementar_pase=True)


# --- v1 ---


def turno_v1(estado: EstadoPartido, elegir_accion: Callable, elegir_defensa: Callable) -> None:
    portador = estado.portador

    todos = estado.jugadores[:]
    random.shuffle(todos)
    if _intentar_falta(estado, todos, probabilidad=0.08):
        return

    accion = elegir_accion(estado, portador)

    if accion == "disparo":
        if portador.tiene(Carta.DISPARO):
            _disparo_al_arco(estado, rebote_palo=True)
        return

    if accion == "reventar":
        _duelo_reventar(estado, portador)
        return

    if accion == "pasa_turno":
        _resolver_pasa_de_turno(estado, portador, elegir_defensa, permitir_tackle=False)
        return

    if not portador.tiene(Carta.PASE):
        if portador.tiene(Carta.DISPARO):
            _disparo_al_arco(estado, rebote_palo=True)
        else:
            _duelo_reventar(estado, portador)
        return

    if estado.offside_activo.get(estado.equipo_defensivo):
        estado.offside_activo[estado.equipo_defensivo] = False
        estado.log_evento("  ¡Offside! Pierde la pelota")
        _robo_pelota(estado, random.choice(estado.defensores()))
        return

    receptor = elegir_accion(estado, portador, es_receptor=True)
    portador.jugar(Carta.PASE)
    estado.descartar(Carta.PASE)
    estado.registrar_carta(Carta.PASE)
    estado.log_evento(f"{portador.nombre} pasa a {receptor.nombre}")

    marca_id = estado.marca_sobre.get(estado.equipo_defensivo)
    if marca_id is not None and receptor.id == marca_id:
        estado.marca_sobre[estado.equipo_defensivo] = None
        d = random.choice(estado.defensores())
        _robo_pelota(estado, d)
        return

    # Una sola reacción defensiva
    defensor, carta_def = elegir_defensa(estado, contexto="pase")
    if defensor and carta_def == Carta.ROBO_PELOTA:
        defensor.jugar(Carta.ROBO_PELOTA)
        estado.descartar(Carta.ROBO_PELOTA)
        estado.registrar_carta(Carta.ROBO_PELOTA)
        if portador.tiene(Carta.GAMBETEAR) and random.random() < 0.55:
            portador.jugar(Carta.GAMBETEAR)
            estado.descartar(Carta.GAMBETEAR)
            estado.registrar_carta(Carta.GAMBETEAR)
            estado.log_evento(f"  {portador.nombre} gambetea el robo")
            _transferir_pelota(estado, receptor, incrementar_pase=True)
        else:
            _robo_pelota(estado, defensor)
        return

    _transferir_pelota(estado, receptor, incrementar_pase=True)


def jugar_partido(
    reglas: str,
    jugadores_por_equipo: int = 2,
    semilla: int | None = None,
    verbose: bool = False,
    elegir_accion=None,
    elegir_defensa=None,
) -> EstadoPartido:
    from simulador.ia import ia_accion, ia_defensa

    estado = crear_partido(reglas, jugadores_por_equipo, semilla)
    accion_fn = elegir_accion or ia_accion
    defensa_fn = elegir_defensa or ia_defensa
    turno_fn = turno_v0 if reglas == "v0" else turno_v1

    if verbose:
        estado.log_evento(
            f"Inicio {reglas}: {jugadores_por_equipo}v{jugadores_por_equipo}, "
            f"portador={estado.portador.nombre}"
        )

    while estado.turnos < LIMITE_TURNOS:
        ganador = estado.marcador.hay_ganador()
        if ganador is not None:
            estado.log_evento(f"Fin: gana equipo {ganador} {estado.marcador.goles}")
            break
        if estado.marcador.es_empate_2_2():
            ganador_penales = resolver_penales(estado, rebote_palo=(reglas == "v1"))
            estado.definido_por_penales = True
            estado.log_evento(f"Fin en penales: gana equipo {ganador_penales}")
            estado.marcador.goles = [3 if ganador_penales == 0 else 2, 3 if ganador_penales == 1 else 2]
            break

        estado.turnos += 1
        if verbose:
            estado.log_evento(
                f"T{estado.turnos} [{estado.marcador.goles}] {estado.portador.nombre} "
                f"(pases={estado.pases_en_jugada})"
            )
        turno_fn(estado, accion_fn, defensa_fn)

        if reglas == "v0":
            for j in estado.jugadores:
                estado.reposicion_v0_mano_vacia(j)

    if estado.turnos >= LIMITE_TURNOS:
        estado.log_evento("Empate técnico: límite de turnos")

    return estado
