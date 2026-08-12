"""Relato de un partido en la terminal, jugada por jugada.

Imprime los eventos a medida que ocurren, con una pausa que se puede ajustar.
Sirve para entender qué hace el motor con un reglamento nuevo antes de tirarle
mil partidos encima.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from simulador.estadisticas import Escenario, agente_de
from simulador.eventos import CLAVE, Evento
from simulador.modelo import EstadoPartido
from simulador.motor import crear_partido, jugar_partido
from simulador.reglamento import cargar

NOMBRES_SUGERIDOS = ("Facu", "Pato", "Manu", "Colo", "Ostu", "Joaco", "Tincho", "Nacho")

RESET = "\033[0m"
COLORES = {
    "gol": "\033[1;33m",
    "turno": "\033[1;34m",
    "inicio": "\033[1;34m",
    "fin": "\033[1;32m",
    "penales": "\033[1;35m",
    "robo": "\033[0;31m",
    "offside": "\033[0;31m",
    "marca": "\033[0;31m",
    "gambeta": "\033[0;36m",
    "falta": "\033[0;33m",
    "dado": "\033[0;90m",
    "reposicion": "\033[0;90m",
    "cambio_equipo": "\033[0;90m",
}


def ver_partido(
    *,
    reglamento: str = "v1",
    jugadores_por_equipo: int = 3,
    perfil: str = "estrategica",
    perfil_equipo1: str | None = None,
    perfil_equipo2: str | None = None,
    semilla: int | None = None,
    nombres: list[str] | None = None,
    pausa: float = 0.6,
    todo: bool = False,
    grabar: Path | None = None,
    salida=sys.stdout,
) -> EstadoPartido:
    """Juega un partido mostrándolo en la terminal y devuelve el estado final."""
    reg = cargar(reglamento)
    escenario = Escenario(
        reglamento=reg.id,
        jugadores_por_equipo=jugadores_por_equipo,
        perfil=perfil,
        perfil_equipo1=perfil_equipo1,
        perfil_equipo2=perfil_equipo2,
    )
    nombres = _nombres(nombres, jugadores_por_equipo)
    color = _color_activo(salida)

    estado = crear_partido(
        reg, jugadores_por_equipo=jugadores_por_equipo, semilla=semilla, nombres=nombres
    )
    agente = agente_de(escenario, rng=estado.rng)
    semilla = estado.semilla

    def mostrar(evento: Evento) -> None:
        if evento.nivel != CLAVE and not todo:
            return
        print(_pintar(evento, color), file=salida, flush=True)
        if pausa > 0:
            time.sleep(pausa if evento.nivel == CLAVE else pausa / 3)

    print(_encabezado(estado, agente.describir(), semilla, color), file=salida)
    estado.observador = mostrar
    jugar_partido(estado=estado, agente=agente)
    print(_cierre(estado, semilla, color), file=salida)

    if grabar:
        from simulador.replay import guardar

        for ruta in guardar(estado, grabar, perfiles=agente.describir()):
            print(f"Guardado: {ruta}", file=salida)
    return estado


def _nombres(nombres: list[str] | None, jugadores_por_equipo: int) -> list[str]:
    total = jugadores_por_equipo * 2
    if nombres:
        if len(nombres) != total:
            raise ValueError(f"Se necesitan {total} nombres y llegaron {len(nombres)}")
        return list(nombres)
    if total <= len(NOMBRES_SUGERIDOS):
        return list(NOMBRES_SUGERIDOS[:total])
    return [f"J{i + 1}" for i in range(total)]


def _color_activo(salida) -> bool:
    return hasattr(salida, "isatty") and salida.isatty()


def _pintar(evento: Evento, color: bool) -> str:
    if not color:
        return evento.texto
    codigo = COLORES.get(evento.tipo, "")
    return f"{codigo}{evento.texto}{RESET}" if codigo else evento.texto


def _encabezado(estado: EstadoPartido, perfiles: str, semilla: int, color: bool) -> str:
    reg = estado.reglamento
    ancho = 64
    lineas = [
        "═" * ancho,
        f"  {reg.nombre} ({reg.id})".ljust(ancho - 20)
        + f"semilla {semilla}".rjust(18),
        f"  {estado.plantel(0)}",
        f"  contra {estado.plantel(1)}",
        f"  Perfil de juego: {perfiles} · primero en {reg.goles_para_ganar} goles",
        "═" * ancho,
    ]
    texto = "\n".join(lineas)
    return f"\033[1m{texto}{RESET}" if color else texto


def _cierre(estado: EstadoPartido, semilla: int, color: bool) -> str:
    cartas = ", ".join(f"{carta} ×{n}" for carta, n in estado.cartas_jugadas.most_common(4))
    lineas = [
        "─" * 64,
        f"  {estado.marcador_texto()}  ·  {estado.turno} turnos"
        + ("  ·  definido por penales" if estado.definido_por_penales else ""),
        f"  Cartas más jugadas: {cartas}",
        f"  Para repetir este partido: --semilla {semilla}",
        "─" * 64,
    ]
    texto = "\n".join(lineas)
    return f"\033[1m{texto}{RESET}" if color else texto
