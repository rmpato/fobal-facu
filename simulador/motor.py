"""Motor de partido: lógica compartida y variantes v0/v1."""

from __future__ import annotations

import random
from typing import Callable

from simulador.cartas import (
    Carta,
    construir_mazo,
    tabla_para_pases,
)
from simulador.config import ConfigSimulacion
from simulador.modelo import EstadoPartido, Jugador, Marcador

LIMITE_TURNOS = 500
MANO_INICIAL = 6


def etiqueta_equipo(estado: EstadoPartido, equipo: int) -> str:
    return ", ".join(j.nombre for j in estado.jugadores_equipo(equipo))


def formatear_marcador(estado: EstadoPartido) -> str:
    g0, g1 = estado.marcador.goles
    return f"{etiqueta_equipo(estado, 0)} {g0} - {g1} {etiqueta_equipo(estado, 1)}"


def _log_gol(estado: EstadoPartido, goleador: Jugador) -> None:
    estado.marcador.anota(goleador.equipo)
    eq = etiqueta_equipo(estado, goleador.equipo)
    estado.log_evento(
        f"** GOL de {goleador.nombre} ({eq})! Marcador: {formatear_marcador(estado)}"
    )


def _mano_inicial(config: ConfigSimulacion) -> int:
    return config.reglamento_resuelto.mano_inicial


def crear_partido(
    config: ConfigSimulacion | None = None,
    *,
    reglas: str | None = None,
    reglamento: str | None = None,
    jugadores_por_equipo: int | None = None,
    semilla: int | None = None,
    nombres_por_equipo: tuple[list[str], list[str]] | None = None,
) -> EstadoPartido:
    if config is None:
        config = ConfigSimulacion(
            reglamento=reglamento or reglas or "v1",
            jugadores_por_equipo=jugadores_por_equipo or 2,
        )
    elif reglas is not None or reglamento is not None or jugadores_por_equipo is not None:
        data = config.to_dict()
        if reglamento is not None:
            data["reglamento"] = reglamento
        elif reglas is not None:
            data["reglamento"] = reglas
        if jugadores_por_equipo is not None:
            data["jugadores_por_equipo"] = jugadores_por_equipo
        config = ConfigSimulacion.from_dict(data)

    reg = config.reglamento_resuelto
    if config.jugadores_por_equipo < reg.jugadores_minimo_por_equipo:
        raise ValueError(
            f"Se requieren al menos {reg.jugadores_minimo_por_equipo} jugadores por equipo"
        )
    if semilla is not None:
        random.seed(semilla)

    jugadores_por_equipo = config.jugadores_por_equipo
    mazo = reg.construir_mazo()
    random.shuffle(mazo)
    mano_inicial = reg.mano_inicial

    jugadores: list[Jugador] = []
    jid = 0
    for equipo in (0, 1):
        for n in range(jugadores_por_equipo):
            if nombres_por_equipo:
                nombre = nombres_por_equipo[equipo][n]
            else:
                nombre = f"E{equipo}-J{n + 1}"
            jugadores.append(Jugador(id=jid, equipo=equipo, nombre=nombre))
            jid += 1

    for j in jugadores:
        for _ in range(mano_inicial):
            if mazo:
                j.mano.append(mazo.pop())

    equipo_inicio = random.randint(0, 1)
    portador_id = random.choice([j.id for j in jugadores if j.equipo == equipo_inicio])
    marcador = Marcador(
        goles_para_ganar=reg.goles_para_ganar,
        penales_si_marcador=reg.penales_si_marcador,
    )
    return EstadoPartido(
        reglamento_id=reg.id,
        jugadores_por_equipo=jugadores_por_equipo,
        jugadores=jugadores,
        mazo=mazo,
        descarte=[],
        portador_id=portador_id,
        marcador=marcador,
        config=config,
        reglamento=reg,
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
                    eq = etiqueta_equipo(estado, equipo)
                    estado.log_evento(f"  ** Penal convertido: {p.nombre} ({eq})")
                else:
                    estado.log_evento(f"  Penal atajado/errado: {p.nombre}")
        return goles[0], goles[1]

    g0, g1 = ronda(n)
    estado.log_evento(f"  Serie: {etiqueta_equipo(estado, 0)} {g0} - {g1} {etiqueta_equipo(estado, 1)}")
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
    estado.registrar_accion("robo")
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
            estado.registrar_carta(Carta.FALTA, j)
            estado.registrar_accion("falta")
            estado.reset_pases()
            estado.log_evento(f"  Falta de {j.nombre}: pelota sigue en el mismo equipo")
            return True
    return False


def _disparo_al_arco(estado: EstadoPartido, rebote_palo: bool) -> None:
    portador = estado.portador
    portador.jugar(Carta.DISPARO)
    estado.descartar(Carta.DISPARO)
    estado.registrar_carta(Carta.DISPARO, portador)
    estado.registrar_accion("disparo")
    arquero = random.choice(estado.defensores())
    pases = estado.pases_en_jugada
    estado.log_evento(f"{portador.nombre} dispara al arco")
    if fase_disparo(estado, portador, arquero, pases, rebote_palo):
        _log_gol(estado, portador)
    else:
        estado.log_evento("Atajada o fuera")
    # Tras disparo: saque del arquero (equipo defensor)
    nuevo = random.choice(estado.defensores())
    estado.reset_pases()
    _transferir_pelota(estado, nuevo)


def _duelo_reventar(estado: EstadoPartido, portador: Jugador) -> None:
    estado.registrar_accion("despeje")
    estado.log_evento(f"{portador.nombre} revienta la pelota")
    # Cada equipo elige quién tira; el reventor no puede tirar
    tiradores_ataque = estado.companeros(portador)
    tiradores_defensa = estado.defensores()
    if not tiradores_ataque:
        raise ValueError("Se requieren al menos 2 jugadores por equipo para reventar")
    a = random.choice(tiradores_ataque)
    d = random.choice(tiradores_defensa)
    estado.log_evento(f"  Tiran el dado: {a.nombre} vs {d.nombre}")
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
    _transferir_pelota(estado, random.choice(tiradores_defensa))


def _normalizar_accion_ofensiva(estado: EstadoPartido, portador: Jugador, accion: str) -> str:
    reg = estado.reglamento
    if reg is None or reg.accion_ofensiva_permitida(accion):
        return accion
    if accion != "pasa_turno":
        return accion
    if reg.reventar_habilitado:
        return "reventar"
    if portador.tiene(Carta.PASE):
        return "pase"
    if portador.tiene(Carta.DISPARO):
        return "disparo"
    return "reventar" if reg.reventar_habilitado else "pase"


def _colocar_trampa_offside(estado: EstadoPartido, defensor: Jugador) -> None:
    defensor.jugar(Carta.TRAMPA_OFFSIDE)
    estado.descartar(Carta.TRAMPA_OFFSIDE)
    estado.registrar_carta(Carta.TRAMPA_OFFSIDE, defensor)
    estado.registrar_accion("trampa_colocada")
    estado.offside_activo[estado.equipo_defensivo] = True
    estado.log_evento(f"  {defensor.nombre} coloca Trampa de offside")


def _colocar_marca_personal(
    estado: EstadoPartido, defensor: Jugador, portador: Jugador, receptor: Jugador
) -> None:
    objetivo = random.choice(
        estado.companeros(receptor) or estado.companeros(portador) or estado.jugadores
    )
    defensor.jugar(Carta.MARCA_PERSONAL)
    estado.descartar(Carta.MARCA_PERSONAL)
    estado.registrar_carta(Carta.MARCA_PERSONAL, defensor)
    estado.registrar_accion("marca_colocada")
    estado.marca_sobre[estado.equipo_defensivo] = objetivo.id
    estado.log_evento(f"  {defensor.nombre} marca a {objetivo.nombre}")


def _resolver_reacciones_pase(
    estado: EstadoPartido,
    portador: Jugador,
    receptor: Jugador,
    elegir_defensa: Callable,
) -> bool:
    """Reacciones defensivas al pase. True = el pase llega al receptor."""
    reg = estado.reglamento
    encadenar = bool(reg and reg.reacciones_encadenables)
    max_rondas = 24 if encadenar else 1

    for _ in range(max_rondas):
        defensor, carta_def = elegir_defensa(estado, contexto="pase")
        if not defensor or not carta_def:
            return True

        if carta_def == Carta.TRAMPA_OFFSIDE:
            _colocar_trampa_offside(estado, defensor)
            return True

        if carta_def == Carta.MARCA_PERSONAL:
            _colocar_marca_personal(estado, defensor, portador, receptor)
            return True

        if carta_def == Carta.CORTA_PASE:
            defensor.jugar(Carta.CORTA_PASE)
            estado.descartar(Carta.CORTA_PASE)
            estado.registrar_carta(Carta.CORTA_PASE, defensor)
            if receptor.tiene(Carta.LA_DEJO_PASAR) and random.random() < 0.7:
                receptor.jugar(Carta.LA_DEJO_PASAR)
                estado.descartar(Carta.LA_DEJO_PASAR)
                estado.registrar_carta(Carta.LA_DEJO_PASAR, receptor)
                estado.log_evento(f"  {receptor.nombre}: La dejo pasar")
                return True
            _robo_pelota(estado, defensor)
            return False

        if carta_def == Carta.ROBO_PELOTA:
            defensor.jugar(Carta.ROBO_PELOTA)
            estado.descartar(Carta.ROBO_PELOTA)
            estado.registrar_carta(Carta.ROBO_PELOTA, defensor)
            contra = (
                reg.reacciones_pase.contra.get(Carta.ROBO_PELOTA, Carta.GAMBETEAR)
                if reg
                else Carta.GAMBETEAR
            )
            if (
                contra == Carta.GAMBETEAR
                and portador.tiene(Carta.GAMBETEAR)
                and random.random() < 0.55
            ):
                portador.jugar(Carta.GAMBETEAR)
                estado.descartar(Carta.GAMBETEAR)
                estado.registrar_carta(Carta.GAMBETEAR, portador)
                estado.registrar_accion("gambetear")
                estado.log_evento(f"  {portador.nombre} gambetea el robo")
                if encadenar:
                    continue
                return True
            _robo_pelota(estado, defensor)
            return False

        return True

    return True


def _resolver_pasa_de_turno(
    estado: EstadoPartido,
    portador: Jugador,
    elegir_defensa: Callable,
    *,
    permitir_tackle: bool,
) -> None:
    """Ataque retiene la pelota sin pasar ni disparar. Defensa puede trampa/marca (y tackle en v0)."""
    estado.registrar_accion("pasa_turno")
    estado.log_evento(f"{portador.nombre} pasa de turno")
    defensor, carta_def = elegir_defensa(estado, contexto="pasa_turno")
    hubo_respuesta = False

    if defensor and carta_def == Carta.TRAMPA_OFFSIDE:
        hubo_respuesta = True
        defensor.jugar(Carta.TRAMPA_OFFSIDE)
        estado.descartar(Carta.TRAMPA_OFFSIDE)
        estado.registrar_carta(Carta.TRAMPA_OFFSIDE, defensor)
        estado.registrar_accion("trampa_colocada")
        estado.offside_activo[estado.equipo_defensivo] = True
        estado.log_evento(f"  {defensor.nombre} coloca Trampa de offside")
        return

    if defensor and carta_def == Carta.MARCA_PERSONAL:
        hubo_respuesta = True
        objetivo = random.choice(estado.companeros(portador) or estado.jugadores)
        defensor.jugar(Carta.MARCA_PERSONAL)
        estado.descartar(Carta.MARCA_PERSONAL)
        estado.registrar_carta(Carta.MARCA_PERSONAL, defensor)
        estado.registrar_accion("marca_colocada")
        estado.marca_sobre[estado.equipo_defensivo] = objetivo.id
        estado.log_evento(f"  {defensor.nombre} marca a {objetivo.nombre}")
        return

    if permitir_tackle and defensor and carta_def == Carta.TACKLE:
        hubo_respuesta = True
        defensor.jugar(Carta.TACKLE)
        estado.descartar(Carta.TACKLE)
        estado.registrar_carta(Carta.TACKLE, defensor)
        if portador.tiene(Carta.GAMBETEAR) and random.random() < 0.6:
            portador.jugar(Carta.GAMBETEAR)
            estado.descartar(Carta.GAMBETEAR)
            estado.registrar_carta(Carta.GAMBETEAR, portador)
            estado.registrar_accion("gambetear")
            estado.log_evento(f"  {portador.nombre} gambetea el tackle")
            return
        _robo_pelota(estado, defensor)
        return

    if not hubo_respuesta:
        sin_respuesta = "nada"
        if estado.reglamento:
            sin_respuesta = estado.reglamento.pasa_turno_sin_respuesta
        elif estado.config and estado.config.pasa_turno_sin_respuesta:
            sin_respuesta = estado.config.pasa_turno_sin_respuesta
        if sin_respuesta == "pasa_companero":
            companeros = estado.companeros(portador)
            if companeros:
                siguiente = random.choice(companeros)
                estado.log_evento(f"  Sin respuesta: la pelota pasa a {siguiente.nombre}")
                _transferir_pelota(estado, siguiente, incrementar_pase=False, limpiar_trampas=False)


# --- v0 ---


def turno_v0(estado: EstadoPartido, elegir_accion: Callable, elegir_defensa: Callable) -> None:
    portador = estado.portador
    accion = elegir_accion(estado, portador)

    # Falta oportunista
    todos = estado.jugadores[:]
    random.shuffle(todos)
    if _intentar_falta(
        estado,
        todos,
        probabilidad=estado.reglamento.prob_falta_por_turno if estado.reglamento else 0.08,
    ):
        return

    if accion == "disparo":
        if portador.tiene(Carta.DISPARO):
            rebote = estado.reglamento.rebote_palo if estado.reglamento else False
            _disparo_al_arco(estado, rebote_palo=rebote)
        return

    if accion == "pasa_turno":
        permitir_tackle = (
            estado.reglamento.reacciones_pasa_turno.permitir_tackle
            if estado.reglamento
            else True
        )
        _resolver_pasa_de_turno(estado, portador, elegir_defensa, permitir_tackle=permitir_tackle)
        return

    # Pase
    if not portador.tiene(Carta.PASE):
        rebote = estado.reglamento.rebote_palo if estado.reglamento else False
        if portador.tiene(Carta.DISPARO):
            _disparo_al_arco(estado, rebote_palo=rebote)
        else:
            permitir_tackle = (
                estado.reglamento.reacciones_pasa_turno.permitir_tackle
                if estado.reglamento
                else True
            )
            _resolver_pasa_de_turno(estado, portador, elegir_defensa, permitir_tackle=permitir_tackle)
        return

    if estado.offside_activo.get(estado.equipo_defensivo):
        estado.offside_activo[estado.equipo_defensivo] = False
        estado.log_evento("  ¡Offside! Pierde la pelota")
        estado.registrar_accion("offside_efectivo")
        _robo_pelota(estado, random.choice(estado.defensores()))
        return

    receptor = elegir_accion(estado, portador, es_receptor=True)
    portador.jugar(Carta.PASE)
    estado.descartar(Carta.PASE)
    estado.registrar_carta(Carta.PASE, portador)
    estado.registrar_accion("pase")
    estado.log_evento(f"{portador.nombre} pasa a {receptor.nombre}")

    marca_id = estado.marca_sobre.get(estado.equipo_defensivo)
    if marca_id is not None and receptor.id == marca_id:
        estado.marca_sobre[estado.equipo_defensivo] = None
        estado.registrar_accion("marca_efectiva")
        if receptor.tiene(Carta.LA_DEJO_PASAR) and random.random() < 0.7:
            receptor.jugar(Carta.LA_DEJO_PASAR)
            estado.descartar(Carta.LA_DEJO_PASAR)
            estado.registrar_carta(Carta.LA_DEJO_PASAR, receptor)
            estado.log_evento(f"  {receptor.nombre}: La dejo pasar")
        else:
            d = random.choice(estado.defensores())
            _robo_pelota(estado, d)
            return

    defensor, carta_def = elegir_defensa(estado, contexto="pase")
    if defensor and carta_def == Carta.CORTA_PASE:
        defensor.jugar(Carta.CORTA_PASE)
        estado.descartar(Carta.CORTA_PASE)
        estado.registrar_carta(Carta.CORTA_PASE, defensor)
        if receptor.tiene(Carta.LA_DEJO_PASAR) and random.random() < 0.7:
            receptor.jugar(Carta.LA_DEJO_PASAR)
            estado.descartar(Carta.LA_DEJO_PASAR)
            estado.registrar_carta(Carta.LA_DEJO_PASAR, receptor)
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
    if _intentar_falta(
        estado,
        todos,
        probabilidad=estado.reglamento.prob_falta_por_turno if estado.reglamento else 0.08,
    ):
        return

    accion = elegir_accion(estado, portador)
    accion = _normalizar_accion_ofensiva(estado, portador, accion)

    rebote = estado.reglamento.rebote_palo if estado.reglamento else True
    reventar = estado.reglamento.reventar_habilitado if estado.reglamento else True

    if accion == "disparo":
        if portador.tiene(Carta.DISPARO):
            _disparo_al_arco(estado, rebote_palo=rebote)
        return

    if accion == "reventar" and reventar:
        _duelo_reventar(estado, portador)
        return

    if accion == "pasa_turno":
        permitir_tackle = (
            estado.reglamento.reacciones_pasa_turno.permitir_tackle
            if estado.reglamento
            else False
        )
        _resolver_pasa_de_turno(estado, portador, elegir_defensa, permitir_tackle=permitir_tackle)
        return

    if not portador.tiene(Carta.PASE):
        if portador.tiene(Carta.DISPARO):
            _disparo_al_arco(estado, rebote_palo=rebote)
        elif reventar:
            _duelo_reventar(estado, portador)
        return

    if estado.offside_activo.get(estado.equipo_defensivo):
        estado.offside_activo[estado.equipo_defensivo] = False
        estado.log_evento("  ¡Offside! Pierde la pelota")
        estado.registrar_accion("offside_efectivo")
        _robo_pelota(estado, random.choice(estado.defensores()))
        return

    receptor = elegir_accion(estado, portador, es_receptor=True)
    portador.jugar(Carta.PASE)
    estado.descartar(Carta.PASE)
    estado.registrar_carta(Carta.PASE, portador)
    estado.registrar_accion("pase")
    estado.log_evento(f"{portador.nombre} pasa a {receptor.nombre}")

    marca_previa = estado.marca_sobre.get(estado.equipo_defensivo)
    if marca_previa is not None and receptor.id == marca_previa:
        estado.marca_sobre[estado.equipo_defensivo] = None
        estado.registrar_accion("marca_efectiva")
        d = random.choice(estado.defensores())
        _robo_pelota(estado, d)
        return

    if _resolver_reacciones_pase(estado, portador, receptor, elegir_defensa):
        marca_id = estado.marca_sobre.get(estado.equipo_defensivo)
        if marca_id is not None and receptor.id == marca_id:
            estado.marca_sobre[estado.equipo_defensivo] = None
            estado.registrar_accion("marca_efectiva")
            d = random.choice(estado.defensores())
            _robo_pelota(estado, d)
            return
        _transferir_pelota(estado, receptor, incrementar_pase=True)


def jugar_partido(
    reglas: str = "v1",
    reglamento: str | None = None,
    jugadores_por_equipo: int = 2,
    semilla: int | None = None,
    verbose: bool = False,
    config: ConfigSimulacion | None = None,
    elegir_accion=None,
    elegir_defensa=None,
    estado: EstadoPartido | None = None,
) -> EstadoPartido:
    from simulador.ia import crear_ia

    if config is None:
        config = ConfigSimulacion(
            reglamento=reglamento or reglas,
            jugadores_por_equipo=jugadores_por_equipo,
        )
    else:
        jugadores_por_equipo = config.jugadores_por_equipo

    reg = config.reglamento_resuelto
    if estado is None:
        estado = crear_partido(config, semilla=semilla)
    if elegir_accion is None or elegir_defensa is None:
        accion_fn, defensa_fn = crear_ia(config)
        accion_fn = elegir_accion or accion_fn
        defensa_fn = elegir_defensa or defensa_fn
    else:
        accion_fn, defensa_fn = elegir_accion, elegir_defensa

    turno_fn = turno_v0 if reg.motor_perfil == "v0" else turno_v1
    limite = config.limite_turnos

    if verbose:
        estado.log_evento(
            f"Inicio reglamento={reg.id} ({reg.nombre}) [{config.nombre_variante}, ia={config.ia}]: "
            f"{jugadores_por_equipo}v{jugadores_por_equipo}, portador={estado.portador.nombre}"
        )

    while estado.turnos < limite:
        if estado.abortar:
            estado.log_evento("Partido detenido por el espectador (Q)")
            break
        ganador = estado.marcador.hay_ganador()
        if ganador is not None:
            estado.log_evento(
                f"Fin: gana {etiqueta_equipo(estado, ganador)} | {formatear_marcador(estado)}"
            )
            break
        if estado.marcador.es_empate_penales():
            g0, g1 = reg.penales_si_marcador
            estado.log_evento(
                f"Empate {g0}-{g1}: se define por penales | {formatear_marcador(estado)}"
            )
            ganador_penales = resolver_penales(estado, rebote_palo=reg.rebote_palo)
            estado.definido_por_penales = True
            estado.log_evento(
                f"Fin en penales: gana {etiqueta_equipo(estado, ganador_penales)} | "
                f"{formatear_marcador(estado)}"
            )
            g0, g1 = reg.penales_si_marcador
            estado.marcador.goles = [
                reg.goles_para_ganar if ganador_penales == 0 else g0,
                reg.goles_para_ganar if ganador_penales == 1 else g1,
            ]
            break

        estado.turnos += 1
        if verbose or estado.on_evento:
            estado.log_evento(
                f"T{estado.turnos} | {estado.portador.nombre} | "
                f"marcador {estado.marcador.goles[0]}-{estado.marcador.goles[1]} | "
                f"pases={estado.pases_en_jugada}"
            )
        turno_fn(estado, accion_fn, defensa_fn)

        if reg.reposicion == "mano_vacia":
            for j in estado.jugadores:
                estado.reposicion_v0_mano_vacia(j)

    if estado.turnos >= limite:
        estado.log_evento("Empate técnico: límite de turnos")

    return estado
