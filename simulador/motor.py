"""Motor de partido.

Resuelve un partido turno a turno aplicando lo que dice el reglamento. No tiene
reglas propias ni ramas por versión del juego: pregunta al reglamento qué es
legal, al agente qué quiere hacer, y tira los dados.

Un turno es siempre la misma secuencia:

1. cualquiera puede cortar la jugada con ``Falta``;
2. quien tiene la pelota elige entre las acciones que le permiten el reglamento
   y su mano (pase, disparo, reventar, pasa de turno);
3. las trampas puestas de antemano (offside, marca) se disparan;
4. la defensa reacciona con una carta, y el ataque puede contrarrestarla;
5. la pelota queda en alguien, y quien corresponda repone su mano.
"""

from __future__ import annotations

import random
from typing import NamedTuple

from simulador.cartas import Carta, INTERCEPCIONES, TRAMPAS
from simulador.ia import Agente, AgenteIA
from simulador.modelo import EstadoPartido, Jugador, Marcador, Observador
from simulador.reglamento import Reglamento, cargar

#: Tope de idas y vueltas defensa/ataque dentro de una misma acción.
LIMITE_CADENA = 20
#: Tope de repeticiones de una tirada empatada (palo, rebote, duelo).
LIMITE_TIRADAS = 20


def crear_partido(
    reglamento: Reglamento | str,
    *,
    jugadores_por_equipo: int = 3,
    semilla: int | None = None,
    nombres: list[str] | None = None,
    observador: Observador | None = None,
) -> EstadoPartido:
    """Reparte las manos y sortea quién arranca con la pelota."""
    reg = cargar(reglamento) if isinstance(reglamento, str) else reglamento
    if jugadores_por_equipo < reg.jugadores_minimo_por_equipo:
        raise ValueError(
            f"El reglamento {reg.id} necesita al menos "
            f"{reg.jugadores_minimo_por_equipo} jugadores por equipo"
        )
    total = jugadores_por_equipo * 2
    if nombres and len(nombres) != total:
        raise ValueError(f"Se esperaban {total} nombres y llegaron {len(nombres)}")

    # Sin semilla se sortea una y se guarda: cualquier partido se puede repetir.
    if semilla is None:
        semilla = random.randrange(1_000_000)
    rng = random.Random(semilla)
    mazo = reg.cartas_del_mazo()
    rng.shuffle(mazo)

    jugadores = []
    for equipo in (0, 1):
        for n in range(jugadores_por_equipo):
            indice = equipo * jugadores_por_equipo + n
            nombre = nombres[indice] if nombres else f"E{equipo + 1}-J{n + 1}"
            jugadores.append(Jugador(id=indice, equipo=equipo, nombre=nombre))

    estado = EstadoPartido(
        reglamento=reg,
        jugadores=jugadores,
        mazo=mazo,
        portador_id=0,
        rng=rng,
        semilla=semilla,
        marcador=Marcador(
            goles_para_ganar=reg.goles_para_ganar,
            penales_si_marcador=reg.penales_si_marcador,
        ),
        observador=observador,
    )
    for jugador in jugadores:
        estado.robar(jugador, reg.mano_inicial)

    inicia = rng.randint(0, 1)
    estado.portador_id = estado.elegir(estado.equipo(inicia)).id
    estado.emitir(
        "inicio",
        f"Reglamento {reg.id} · {jugadores_por_equipo} vs {jugadores_por_equipo} · "
        f"arranca {estado.portador.nombre}",
        jugadores=(estado.portador.nombre,),
    )
    return estado


def jugar_partido(
    reglamento: Reglamento | str = "v1",
    *,
    jugadores_por_equipo: int = 3,
    semilla: int | None = None,
    agente: Agente | None = None,
    nombres: list[str] | None = None,
    observador: Observador | None = None,
    estado: EstadoPartido | None = None,
) -> EstadoPartido:
    """Juega un partido completo y devuelve su estado final."""
    if estado is None:
        estado = crear_partido(
            reglamento,
            jugadores_por_equipo=jugadores_por_equipo,
            semilla=semilla,
            nombres=nombres,
            observador=observador,
        )
    agente = agente or AgenteIA(rng=estado.rng)
    reg = estado.reglamento

    while not estado.terminado:
        ganador = estado.marcador.ganador()
        if ganador is not None:
            _terminar(estado, f"Gana {estado.nombre_equipo(ganador)}", "victoria")
            break
        if estado.marcador.va_a_penales():
            _definir_por_penales(estado, agente)
            break
        if estado.turno >= reg.limite_turnos:
            _terminar(
                estado,
                f"Empate técnico: se llegó al límite de {reg.limite_turnos} turnos",
                "limite_turnos",
            )
            break

        estado.turno += 1
        estado.emitir(
            "turno",
            f"Turno {estado.turno} · pelota en {estado.portador.nombre} · "
            f"{estado.marcador.goles[0]}-{estado.marcador.goles[1]} · "
            f"{estado.pases} pases",
            jugadores=(estado.portador.nombre,),
        )
        jugar_turno(estado, agente)
        _reponer(estado, "fin_de_turno")
        _reponer(estado, "mano_vacia")

    return estado


def jugar_turno(estado: EstadoPartido, agente: Agente) -> None:
    """Resuelve un turno: una acción del ataque y la respuesta de la defensa."""
    if _falta_oportunista(estado):
        return

    posibles = acciones_posibles(estado)
    accion = agente.accion(estado, posibles)
    if accion not in posibles:
        accion = posibles[0]

    if accion == "pase":
        _pase(estado, agente)
    elif accion == "disparo":
        _disparo(estado)
    elif accion == "reventar":
        _reventar(estado)
    else:
        _pasa_turno(estado, agente)


def acciones_posibles(estado: EstadoPartido) -> list[str]:
    """Acciones que el reglamento y la mano del portador permiten ahora."""
    reg = estado.reglamento
    portador = estado.portador
    hay_companeros = bool(estado.companeros(portador))
    posibles = []
    if reg.permite("pase") and portador.tiene(Carta.PASE) and hay_companeros:
        posibles.append("pase")
    if reg.permite("disparo") and portador.tiene(Carta.DISPARO):
        posibles.append("disparo")
    if reg.permite("reventar") and hay_companeros:
        posibles.append("reventar")
    if reg.permite("pasa_turno"):
        posibles.append("pasa_turno")
    return posibles or ["pasa_turno"]


# --- acciones del ataque --------------------------------------------------


def _pase(estado: EstadoPartido, agente: Agente) -> None:
    portador = estado.portador
    defensa = estado.equipo_sin_pelota
    candidatos = estado.companeros(portador)
    marcado = estado.jugador_marcado_por(defensa)

    receptor = agente.receptor(estado, candidatos)
    if marcado in candidatos and receptor is not marcado:
        estado.registrar("marca_evitada")

    estado.jugar_carta(portador, Carta.PASE)
    estado.registrar("pase")
    _reponer(estado, "al_jugar_carta", jugador=portador)
    estado.emitir(
        "pase",
        f"{portador.nombre} le pasa a {receptor.nombre}",
        jugadores=(portador.nombre, receptor.nombre),
        carta=Carta.PASE,
    )

    if estado.offside[defensa]:
        estado.offside[defensa] = False
        estado.registrar("offside_efectivo")
        estado.emitir(
            "offside",
            f"  ¡Offside! {receptor.nombre} había picado antes: la pelota es de la defensa",
            jugadores=(receptor.nombre,),
        )
        _recuperar(estado, estado.elegir(estado.defensores()))
        return

    if marcado is receptor:
        estado.marca[defensa] = None
        contra = estado.reglamento.reaccion("pase").contra_de(Carta.MARCA_PERSONAL)
        anulada = bool(contra) and _jugar_contra(
            estado, agente, portador, receptor, contra, Carta.MARCA_PERSONAL
        )
        if not anulada:
            estado.registrar("marca_efectiva")
            estado.emitir(
                "marca",
                f"  {receptor.nombre} estaba marcado: la defensa se queda con la pelota",
                jugadores=(receptor.nombre,),
                carta=Carta.MARCA_PERSONAL,
            )
            _recuperar(estado, estado.elegir(estado.defensores()))
            return

    if _reacciones(estado, agente, "pase", receptor=receptor).prospera:
        _mover_pelota(estado, receptor, suma_pase=True)


def _disparo(estado: EstadoPartido) -> None:
    reg = estado.reglamento
    portador = estado.portador
    estado.jugar_carta(portador, Carta.DISPARO)
    estado.registrar("disparo")
    _reponer(estado, "al_jugar_carta", jugador=portador)

    arquero = estado.elegir(estado.defensores())
    franja = reg.tabla_disparo.para(estado.pases)
    estado.emitir(
        "disparo",
        f"{portador.nombre} patea al arco (con {estado.pases} pases encadenados; "
        f"es gol con {_rango(franja.gol)}, ataja con {_rango(franja.ataja)})",
        jugadores=(portador.nombre, arquero.nombre),
        carta=Carta.DISPARO,
    )

    gol = False
    for _ in range(LIMITE_TIRADAS):
        dado_pateador, dado_arquero = estado.dado(), estado.dado()
        estado.emitir(
            "dado",
            f"  Dados: {portador.nombre} {dado_pateador}, {arquero.nombre} {dado_arquero}",
            jugadores=(portador.nombre, arquero.nombre),
            pateador=dado_pateador,
            arquero=dado_arquero,
        )
        marca_gol = franja.es_gol(dado_pateador)
        ataja = franja.es_atajada(dado_arquero)
        if reg.rebote and marca_gol and ataja:
            estado.emitir("dado", "  Rebote: se vuelve a patear")
            continue
        if reg.palo and dado_pateador == dado_arquero:
            estado.emitir("dado", "  Pega en el palo: se vuelve a patear")
            continue
        gol = marca_gol and not ataja
        break

    if gol:
        estado.marcador.anota(portador.equipo)
        estado.registrar("gol")
        estado.emitir(
            "gol",
            f"¡GOL de {portador.nombre}! {estado.marcador_texto()}",
            jugadores=(portador.nombre,),
        )
    else:
        estado.emitir(
            "atajada",
            f"  Ataja {arquero.nombre} (o se va afuera)",
            jugadores=(arquero.nombre,),
        )

    estado.pases = 0
    _mover_pelota(estado, estado.elegir(estado.defensores()))


def _reventar(estado: EstadoPartido) -> None:
    portador = estado.portador
    estado.registrar("reventar")
    estado.emitir(
        "reventar",
        f"{portador.nombre} la revienta",
        jugadores=(portador.nombre,),
    )
    # El que reventó no puede disputar la pelota; cada equipo elige a otro.
    ataque = estado.elegir(estado.companeros(portador))
    defensa = estado.elegir(estado.defensores())

    for _ in range(LIMITE_TIRADAS):
        dado_ataque, dado_defensa = estado.dado(), estado.dado()
        estado.emitir(
            "dado",
            f"  Disputa: {ataque.nombre} {dado_ataque} vs {defensa.nombre} {dado_defensa}",
            jugadores=(ataque.nombre, defensa.nombre),
        )
        if dado_ataque == dado_defensa:
            continue
        gana = ataque if dado_ataque > dado_defensa else defensa
        propio = gana.equipo == portador.equipo
        estado.emitir(
            "reventar",
            f"  La agarra {gana.nombre}" + (" (cuenta como pase)" if propio else ""),
            jugadores=(gana.nombre,),
        )
        _mover_pelota(estado, gana, suma_pase=propio)
        return
    _mover_pelota(estado, defensa)


def _pasa_turno(estado: EstadoPartido, agente: Agente) -> None:
    portador = estado.portador
    estado.registrar("pasa_turno")
    estado.emitir(
        "pasa_turno",
        f"{portador.nombre} pasa de turno y se queda con la pelota",
        jugadores=(portador.nombre,),
    )
    respuesta = _reacciones(estado, agente, "pasa_turno")
    if respuesta.prospera and not respuesta.hubo_carta:
        if estado.reglamento.pasa_turno_sin_respuesta == "pasa_companero":
            companeros = estado.companeros(portador)
            if companeros:
                siguiente = estado.elegir(companeros)
                estado.emitir(
                    "pase",
                    f"  Sin respuesta de la defensa: la pelota queda en {siguiente.nombre}",
                    jugadores=(siguiente.nombre,),
                )
                _mover_pelota(estado, siguiente)


# --- respuestas de la defensa ---------------------------------------------


class Respuesta(NamedTuple):
    """Cómo terminó la reacción de la defensa a una acción del ataque."""

    prospera: bool  # la acción del ataque sigue en pie
    hubo_carta: bool  # la defensa llegó a jugar alguna carta


def _reacciones(
    estado: EstadoPartido,
    agente: Agente,
    contexto: str,
    *,
    receptor: Jugador | None = None,
) -> Respuesta:
    """Deja reaccionar a la defensa.

    La defensa juega una sola carta por acción del ataque. Si el reglamento
    permite encadenar, una contra del ataque le devuelve el turno a la defensa.
    """
    reaccion = estado.reglamento.reaccion(contexto)
    if not reaccion.cartas:
        return Respuesta(prospera=True, hubo_carta=False)
    portador = estado.portador
    hubo_carta = False

    for _ in range(LIMITE_CADENA):
        opciones = [
            (defensor, carta)
            for defensor in estado.defensores()
            for carta in reaccion.cartas
            if defensor.tiene(carta)
        ]
        elegida = agente.reaccion(estado, contexto, opciones) if opciones else None
        if elegida is None:
            return Respuesta(prospera=True, hubo_carta=hubo_carta)

        defensor, carta = elegida
        hubo_carta = True
        estado.jugar_carta(defensor, carta)
        _reponer(estado, "al_jugar_carta", jugador=defensor)

        if carta in TRAMPAS:
            _colocar_trampa(estado, defensor, carta, receptor)
            return Respuesta(prospera=True, hubo_carta=True)

        if carta in INTERCEPCIONES:
            contra = reaccion.contra_de(carta)
            if contra and _jugar_contra(estado, agente, portador, receptor, contra, carta):
                if estado.reglamento.reacciones_encadenables:
                    continue
                return Respuesta(prospera=True, hubo_carta=True)
            estado.emitir(
                "robo",
                f"  {defensor.nombre} corta con {carta.value}",
                jugadores=(defensor.nombre,),
                carta=carta,
            )
            _recuperar(estado, defensor)
            return Respuesta(prospera=False, hubo_carta=True)

        return Respuesta(prospera=True, hubo_carta=True)
    return Respuesta(prospera=True, hubo_carta=hubo_carta)


def _colocar_trampa(
    estado: EstadoPartido, defensor: Jugador, carta: Carta, receptor: Jugador | None
) -> None:
    equipo = defensor.equipo
    if carta is Carta.TRAMPA_OFFSIDE:
        estado.offside[equipo] = True
        estado.registrar("trampa_colocada")
        estado.emitir(
            "trampa",
            f"  {defensor.nombre} arma la trampa de offside",
            jugadores=(defensor.nombre,),
            carta=carta,
        )
        return

    # La marca se pone sobre un rival que todavía no tiene la pelota.
    candidatos = [
        j
        for j in estado.equipo(1 - equipo)
        if j is not estado.portador and j is not receptor
    ] or [j for j in estado.equipo(1 - equipo) if j is not estado.portador]
    objetivo = estado.elegir(candidatos)
    estado.marca[equipo] = objetivo.id
    estado.registrar("marca_colocada")
    estado.emitir(
        "marca",
        f"  {defensor.nombre} marca a {objetivo.nombre}",
        jugadores=(defensor.nombre, objetivo.nombre),
        carta=carta,
    )


def _jugar_contra(
    estado: EstadoPartido,
    agente: Agente,
    portador: Jugador,
    receptor: Jugador | None,
    contra: Carta,
    ante: Carta,
) -> bool:
    """El ataque anula una carta defensiva si tiene la contra y quiere gastarla."""
    candidatos = [j for j in (receptor, portador) if j is not None and j.tiene(contra)]
    if not candidatos:
        return False
    quien = candidatos[0]
    if not agente.contra(estado, quien, contra, ante):
        return False
    estado.jugar_carta(quien, contra)
    estado.registrar("contra")
    _reponer(estado, "al_jugar_carta", jugador=quien)
    estado.emitir(
        "gambeta",
        f"  {quien.nombre} responde con {contra.value} y anula {ante.value}",
        jugadores=(quien.nombre,),
        carta=contra,
    )
    return True


def _falta_oportunista(estado: EstadoPartido) -> bool:
    """Cualquiera puede jugar Falta: la pelota no cambia de equipo y se cortan los pases.

    No pasa por el agente: la frecuencia la fija el reglamento
    (``prob_falta_por_jugador``), porque en la mesa la falta se juega por reflejo
    y no como parte de un plan.
    """
    prob = estado.reglamento.prob_falta_por_jugador
    if prob <= 0:
        return False
    jugadores = list(estado.jugadores)
    estado.rng.shuffle(jugadores)
    for jugador in jugadores:
        if jugador.tiene(Carta.FALTA) and estado.rng.random() < prob:
            estado.jugar_carta(jugador, Carta.FALTA)
            estado.registrar("falta")
            _reponer(estado, "al_jugar_carta", jugador=jugador)
            estado.pases = 0
            estado.emitir(
                "falta",
                f"Falta de {jugador.nombre}: la pelota sigue en el mismo equipo y "
                f"la jugada arranca de cero",
                jugadores=(jugador.nombre,),
                carta=Carta.FALTA,
            )
            return True
    return False


# --- pelota y reposición ---------------------------------------------------


def _mover_pelota(estado: EstadoPartido, nuevo: Jugador, *, suma_pase: bool = False) -> None:
    cambia_de_equipo = nuevo.equipo != estado.equipo_con_pelota
    if cambia_de_equipo:
        estado.pases = 0
        estado.offside = {0: False, 1: False}
        estado.marca = {0: None, 1: None}
        estado.portador_id = nuevo.id
        estado.emitir(
            "cambio_equipo",
            f"  La pelota cambia de equipo: ataca {estado.nombre_equipo(nuevo.equipo)} "
            f"con {nuevo.nombre}",
            jugadores=(nuevo.nombre,),
        )
        _reponer(estado, "cambio_equipo", jugador=nuevo)
        return
    if suma_pase:
        estado.pases += 1
    estado.portador_id = nuevo.id


def _recuperar(estado: EstadoPartido, defensor: Jugador) -> None:
    estado.registrar("robo")
    _mover_pelota(estado, defensor)


def _reponer(estado: EstadoPartido, momento: str, *, jugador: Jugador | None = None) -> None:
    """Levanta cartas si el reglamento repone en este momento."""
    rep = estado.reglamento.reposicion
    if rep.momento != momento:
        return
    objetivos = _alcanzados(estado, rep.quien, jugador)
    if momento == "mano_vacia":
        objetivos = [j for j in objetivos if not j.mano]
    total = 0
    for objetivo in objetivos:
        total += estado.robar(objetivo, estado.reglamento.mano_maxima)
    if total:
        cartas = "1 carta" if total == 1 else f"{total} cartas"
        estado.emitir(
            "reposicion",
            f"  Reposición: se levantan {cartas} (máximo {estado.reglamento.mano_maxima} en mano)",
            cartas=total,
        )


def _alcanzados(estado: EstadoPartido, quien: str, jugador: Jugador | None) -> list[Jugador]:
    if quien == "el_jugador":
        return [jugador] if jugador else []
    if quien == "equipo_con_pelota":
        return estado.equipo(estado.equipo_con_pelota)
    if quien == "equipo_sin_pelota":
        return estado.equipo(estado.equipo_sin_pelota)
    return list(estado.jugadores)


# --- final del partido -----------------------------------------------------


def _terminar(estado: EstadoPartido, texto: str, motivo: str) -> None:
    estado.terminado = True
    estado.motivo_fin = motivo
    estado.emitir("fin", f"{texto} · {estado.marcador_texto()}")


def _definir_por_penales(estado: EstadoPartido, agente: Agente) -> None:
    reg = estado.reglamento
    estado.definido_por_penales = True
    estado.emitir(
        "penales",
        f"Marcador {'-'.join(map(str, reg.penales_si_marcador))}: se define por penales",
    )
    ganador = _tanda_de_penales(estado)
    estado.marcador.goles = [
        reg.goles_para_ganar if ganador == 0 else reg.penales_si_marcador[0],
        reg.goles_para_ganar if ganador == 1 else reg.penales_si_marcador[1],
    ]
    _terminar(estado, f"Gana {estado.nombre_equipo(ganador)} por penales", "penales")


def _tanda_de_penales(estado: EstadoPartido) -> int:
    """Serie de tantos penales como jugadores por equipo, más muerte súbita."""
    franja = estado.reglamento.tabla_disparo.para(0)
    por_equipo = estado.jugadores_por_equipo

    def patea(equipo: int, indice: int) -> bool:
        pateadores = estado.equipo(equipo)
        arqueros = estado.equipo(1 - equipo)
        pateador = pateadores[indice % len(pateadores)]
        arquero = arqueros[indice % len(arqueros)]
        for _ in range(LIMITE_TIRADAS):
            dado_pateador, dado_arquero = estado.dado(), estado.dado()
            if estado.reglamento.rebote and franja.es_gol(dado_pateador) and franja.es_atajada(dado_arquero):
                continue
            if estado.reglamento.palo and dado_pateador == dado_arquero:
                continue
            convierte = franja.es_gol(dado_pateador) and not franja.es_atajada(dado_arquero)
            break
        else:
            convierte = False
        estado.emitir(
            "penales",
            f"  Penal de {pateador.nombre}: {'gol' if convierte else 'lo ataja ' + arquero.nombre}",
            jugadores=(pateador.nombre, arquero.nombre),
        )
        return convierte

    serie = [0, 0]
    for indice in range(por_equipo):
        for equipo in (0, 1):
            serie[equipo] += int(patea(equipo, indice))
    estado.emitir(
        "penales",
        f"  Serie: {estado.nombre_equipo(0)} {serie[0]} - {serie[1]} {estado.nombre_equipo(1)}",
    )
    if serie[0] != serie[1]:
        return 0 if serie[0] > serie[1] else 1

    estado.emitir("penales", "  Muerte súbita: patea uno cada equipo")
    for ronda in range(LIMITE_TIRADAS):
        primero, segundo = patea(0, ronda), patea(1, ronda)
        if primero != segundo:
            return 0 if primero else 1
    return estado.rng.randint(0, 1)


def _rango(rango: tuple[int, int]) -> str:
    return str(rango[0]) if rango[0] == rango[1] else f"{rango[0]}-{rango[1]}"
