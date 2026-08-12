"""Interfaz de línea de comandos: ``python3 -m simulador``."""

from __future__ import annotations

import argparse
from pathlib import Path

from simulador import __version__
from simulador.estadisticas import (
    Escenario,
    formatear_resultado,
    formatear_tabla,
    simular,
)
from simulador.ia import IDS, catalogo as catalogo_perfiles, perfil
from simulador.reglamento import (
    ReglamentoInvalido,
    cargar,
    catalogo as catalogo_reglamentos,
)

EJEMPLOS = """\
ejemplos:
  python3 -m simulador web                        abre la interfaz para editar reglas y simular
  python3 -m simulador reglamentos                lista los reglamentos disponibles
  python3 -m simulador reglamentos v2             muestra las reglas que aplica v2
  python3 -m simulador simular v2 --partidos 500  corre 500 partidos y muestra las métricas
  python3 -m simulador comparar v1 v2             compara dos reglamentos en 3v3
  python3 -m simulador ver v2 --semilla 42        mira un partido jugada por jugada
"""


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="simulador",
        description="Simulador de partidos del juego de cartas Fobal Facu.",
        epilog=EJEMPLOS,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"fobal-facu {__version__}")
    sub = parser.add_subparsers(dest="comando", required=True)

    web = sub.add_parser("web", help="abrir la interfaz web para diseñar reglas y simular")
    web.add_argument("--puerto", type=int, default=8000, help="puerto (por defecto 8000)")
    web.add_argument(
        "--sin-navegador", action="store_true", help="no abrir el navegador automáticamente"
    )

    reglamentos = sub.add_parser(
        "reglamentos", help="listar los reglamentos o ver las reglas de uno"
    )
    reglamentos.add_argument(
        "id", nargs="?", help="id del reglamento (v1, v2, …); sin id, los lista todos"
    )

    sub.add_parser("perfiles", help="listar los perfiles de juego de la simulación")

    simular_cmd = sub.add_parser("simular", help="correr muchos partidos y ver las métricas")
    _agregar_escenario(simular_cmd)
    simular_cmd.add_argument("--partidos", type=int, default=200)
    simular_cmd.add_argument(
        "--semilla-base", type=int, default=0, help="primera semilla de la tanda"
    )

    comparar = sub.add_parser("comparar", help="comparar reglamentos y formatos lado a lado")
    comparar.add_argument(
        "reglamentos",
        nargs="*",
        help="ids a comparar (por defecto, todos los marcados como activos)",
    )
    comparar.add_argument(
        "--formatos",
        type=int,
        nargs="+",
        default=[3],
        metavar="N",
        help="jugadores por equipo a probar (por defecto 3)",
    )
    comparar.add_argument("--partidos", type=int, default=200)
    comparar.add_argument("--perfil", choices=IDS, default="estrategica")
    comparar.add_argument(
        "--detalle", action="store_true", help="además de la tabla, el informe de cada escenario"
    )

    ver = sub.add_parser("ver", help="mirar un partido jugada por jugada en la terminal")
    ver.add_argument("reglamento", nargs="?", default="v1")
    ver.add_argument("--formato", type=int, default=3, metavar="N", help="jugadores por equipo")
    ver.add_argument("--perfil", choices=IDS, default="estrategica")
    ver.add_argument("--perfil-equipo1", choices=IDS, default=None)
    ver.add_argument("--perfil-equipo2", choices=IDS, default=None)
    ver.add_argument(
        "--semilla", type=int, default=None, help="para repetir exactamente el mismo partido"
    )
    ver.add_argument(
        "--nombres", nargs="+", default=None, metavar="NOMBRE", help="nombres de los jugadores"
    )
    ver.add_argument(
        "--pausa", type=float, default=0.6, help="segundos entre jugadas (0 = sin pausa)"
    )
    ver.add_argument("--todo", action="store_true", help="mostrar también las tiradas de dado")
    ver.add_argument(
        "--grabar",
        type=Path,
        default=None,
        metavar="ARCHIVO.json",
        help="guardar el partido; con .html genera además una página para volver a verlo",
    )
    return parser


def _agregar_escenario(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("reglamento", nargs="?", default="v1", help="id del reglamento")
    parser.add_argument(
        "--formato", type=int, default=3, metavar="N", help="jugadores por equipo (mínimo 2)"
    )
    parser.add_argument("--perfil", choices=IDS, default="estrategica")
    parser.add_argument("--perfil-equipo1", choices=IDS, default=None)
    parser.add_argument("--perfil-equipo2", choices=IDS, default=None)


def main(argv: list[str] | None = None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)
    try:
        return _ejecutar(args)
    except (ReglamentoInvalido, FileNotFoundError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")


def _ejecutar(args) -> int:
    if args.comando == "web":
        from simulador.web import servir

        servir(puerto=args.puerto, abrir_navegador=not args.sin_navegador)
        return 0

    if args.comando == "reglamentos":
        print(_reglamentos(args.id))
        return 0

    if args.comando == "perfiles":
        print(_perfiles())
        return 0

    if args.comando == "simular":
        escenario = Escenario(
            reglamento=args.reglamento,
            jugadores_por_equipo=args.formato,
            perfil=args.perfil,
            perfil_equipo1=args.perfil_equipo1,
            perfil_equipo2=args.perfil_equipo2,
        )
        resultado = simular(escenario, args.partidos, semilla_base=args.semilla_base)
        print(formatear_resultado(resultado))
        return 0

    if args.comando == "comparar":
        ids = args.reglamentos or [e["id"] for e in catalogo_reglamentos(solo_activos=True)]
        if not ids:
            raise ValueError(
                "no hay reglamentos activos; pasá ids explícitos, por ejemplo: comparar v1 v2"
            )
        escenarios = [
            Escenario(reglamento=rid, jugadores_por_equipo=formato, perfil=args.perfil)
            for formato in args.formatos
            for rid in ids
        ]
        resultados = [simular(e, args.partidos) for e in escenarios]
        titulo = " vs ".join(ids) + f" · perfil {perfil(args.perfil).nombre}"
        print(formatear_tabla(resultados, titulo))
        if args.detalle:
            for resultado in resultados:
                print()
                print(formatear_resultado(resultado, con_reglas=False))
        return 0

    if args.comando == "ver":
        from simulador.espectador import ver_partido

        ver_partido(
            reglamento=args.reglamento,
            jugadores_por_equipo=args.formato,
            perfil=args.perfil,
            perfil_equipo1=args.perfil_equipo1,
            perfil_equipo2=args.perfil_equipo2,
            semilla=args.semilla,
            nombres=args.nombres,
            pausa=args.pausa,
            todo=args.todo,
            grabar=args.grabar,
        )
        return 0

    return 1


def _reglamentos(id_reglamento: str | None) -> str:
    if id_reglamento:
        reg = cargar(id_reglamento)
        lineas = [
            f"{reg.nombre} ({reg.id}, versión {reg.version})",
            "",
            reg.descripcion,
            "",
            "Reglas que aplica la simulación:",
        ]
        lineas += [f"  · {linea}" for linea in reg.resumen()]
        lineas += ["", "Mazo:"]
        for carta, cantidad in sorted(reg.mazo.items(), key=lambda x: -x[1]):
            lineas.append(f"  {cantidad:>3}  {carta.value}")
        if reg.documento:
            lineas += ["", f"Reglas para jugar en mesa: {reg.documento}"]
        return "\n".join(lineas)

    entradas = catalogo_reglamentos()
    lineas = ["Reglamentos disponibles:", ""]
    for entrada in entradas:
        marca = "●" if entrada["activo"] else "○"
        lineas.append(f"  {marca} {entrada['id']:<6} {entrada['nombre']}")
        lineas.append(f"      {entrada['descripcion']}")
    lineas += [
        "",
        "● se compara por defecto    ○ queda como referencia histórica",
        "",
        "Ver uno:   python3 -m simulador reglamentos v2",
        "Crear uno: python3 -m simulador web   (o copiar reglamentos/_plantilla.json)",
    ]
    return "\n".join(lineas)


def _perfiles() -> str:
    lineas = ["Perfiles de juego:", ""]
    for entrada in catalogo_perfiles():
        lineas.append(f"  {entrada['id']:<15} {entrada['nombre']}")
        lineas.append(f"      {entrada['descripcion']}")
    lineas += [
        "",
        "Se usan con --perfil, o con --perfil-equipo1 / --perfil-equipo2 para enfrentar dos estilos.",
    ]
    return "\n".join(lineas)
