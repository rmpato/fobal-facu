"""CLI del simulador."""

from __future__ import annotations

import argparse
from pathlib import Path

from simulador.config import ConfigSimulacion, cargar_variantes
from simulador.estadisticas import (
    formatear_comparacion_formatos,
    formatear_comparacion_reglamentos,
    formatear_comparacion_variantes,
    formatear_reporte,
    simular_comparacion_formatos,
    simular_lote,
    simular_variantes,
)
from simulador.motor import jugar_partido
from simulador.reglamento import (
    cargar_reglamento,
    formatear_lista_reglamentos,
    formatear_reglamento,
    listar_reglamentos,
)
from simulador.espectador import ver_partido
from simulador.eventos_espectador import VELOCIDADES
from simulador.ia import IDS_IA, nombre_ia

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VARIANTES = ROOT / "configs" / "variantes.json"
_IA_HELP = ", ".join(f"{i} ({nombre_ia(i)})" for i in IDS_IA)


def _config_desde_args(args) -> ConfigSimulacion:
    reglamento = getattr(args, "reglamento", None) or getattr(args, "reglas", "v1")
    kwargs = {
        "reglamento": reglamento,
        "jugadores_por_equipo": args.jugadores_por_equipo,
        "ia": args.ia,
    }
    if getattr(args, "ia_equipo0", None) is not None:
        kwargs["ia_equipo0"] = args.ia_equipo0
    if getattr(args, "ia_equipo1", None) is not None:
        kwargs["ia_equipo1"] = args.ia_equipo1
    if getattr(args, "pasa_turno_sin_respuesta", None) is not None:
        kwargs["pasa_turno_sin_respuesta"] = args.pasa_turno_sin_respuesta
    return ConfigSimulacion(**kwargs)


def _add_ia_args(parser, *, default: str = "estrategica", per_equipo: bool = False) -> None:
    parser.add_argument(
        "--ia",
        choices=list(IDS_IA),
        default=default,
        help=f"Perfil de IA: {_IA_HELP}",
    )
    if per_equipo:
        parser.add_argument(
            "--ia-equipo0",
            choices=list(IDS_IA),
            default=None,
            help="IA solo del equipo 1 (override de --ia)",
        )
        parser.add_argument(
            "--ia-equipo1",
            choices=list(IDS_IA),
            default=None,
            help="IA solo del equipo 2 (override de --ia)",
        )


def _add_reglamento_arg(parser, default: str = "v1") -> None:
    parser.add_argument(
        "--reglamento",
        "--reglas",
        dest="reglamento",
        default=default,
        metavar="ID",
        help="Id del reglamento (v0, v1, v1.1, …) o ruta a .json",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulador de partidos — juego de cartas de fútbol (fobal-facu)"
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    run = sub.add_parser("run", help="Correr simulaciones en lote")
    _add_reglamento_arg(run)
    run.add_argument("--partidos", type=int, default=100)
    run.add_argument("--jugadores-por-equipo", type=int, default=3, help="Mínimo 2 (default: 3)")
    _add_ia_args(run)
    run.add_argument(
        "--pasa-turno-sin-respuesta",
        choices=["nada", "pasa_companero"],
        default=None,
        dest="pasa_turno_sin_respuesta",
        help="Override puntual (preferir reglamento v1.1)",
    )
    run.add_argument("--verbose", action="store_true")

    compare = sub.add_parser("compare", help="Comparar v1 vs v2 (alias rápido)")
    compare.add_argument("--partidos", type=int, default=200)
    compare.add_argument("--jugadores-por-equipo", type=int, default=3, help="Jugadores por equipo (default: 3)")
    _add_ia_args(compare)

    compare_reg = sub.add_parser(
        "compare-reglamentos",
        help="Comparar reglamentos activos en simulación (v1, v2)",
    )
    compare_reg.add_argument("--partidos", type=int, default=200)
    compare_reg.add_argument("--jugadores-por-equipo", type=int, default=3, help="Jugadores por equipo (default: 3)")
    _add_ia_args(compare_reg)

    compare_fmt = sub.add_parser(
        "compare-formatos",
        help="Comparar v1 vs v2 en 3v3 y 4v4 (u otros formatos)",
    )
    compare_fmt.add_argument("--partidos", type=int, default=200)
    compare_fmt.add_argument(
        "--formatos",
        type=int,
        nargs="+",
        default=[3, 4],
        metavar="N",
        help="Jugadores por equipo a probar (default: 3 4)",
    )
    _add_ia_args(compare_fmt)

    variantes = sub.add_parser("variantes", help="Comparar variantes de reglas desde JSON")
    variantes.add_argument("--partidos", type=int, default=500)
    variantes.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_VARIANTES,
        help="Archivo JSON con variantes",
    )

    reglamentos = sub.add_parser("reglamentos", help="Listar o inspeccionar reglamentos")
    reglamentos_sub = reglamentos.add_subparsers(dest="subcomando", required=True)
    reglamentos_sub.add_parser("list", help="Listar reglamentos disponibles")
    show = reglamentos_sub.add_parser("show", help="Mostrar reglas que aplica un reglamento")
    show.add_argument("id", help="Id del reglamento (p. ej. v1, v1.1)")

    ver = sub.add_parser("ver", help="Ver un partido en vivo (modo espectador)")
    _add_reglamento_arg(ver, default="v1")
    ver.add_argument("--jugadores-por-equipo", type=int, default=3, help="Jugadores por equipo")
    _add_ia_args(ver, per_equipo=True)
    ver.add_argument(
        "--semilla",
        type=int,
        default=None,
        help="Semilla para reproducir el mismo partido (se imprime si no se pasa)",
    )
    ver.add_argument(
        "--pausa",
        type=float,
        default=5.0,
        help="Segundos entre acciones; Espacio avanza antes",
    )
    ver.add_argument(
        "--grabar",
        type=Path,
        default=None,
        metavar="ARCHIVO",
        help="Guardar transcripción (.txt) o grabación JSON (.json)",
    )
    ver.add_argument(
        "--exportar-html",
        action="store_true",
        help="Con --grabar partido.json, genera replay HTML embebido",
    )
    ver.add_argument(
        "--velocidad",
        choices=list(VELOCIDADES),
        default="normal",
        help="Ritmo del relato: lento/normal/rapido/turbo",
    )
    ver.add_argument(
        "--equipo1",
        nargs=3,
        metavar="N",
        default=None,
        help="Tres nombres del equipo 1 (requiere --equipo2)",
    )
    ver.add_argument(
        "--equipo2",
        nargs=3,
        metavar="N",
        default=None,
        help="Tres nombres del equipo 2 (requiere --equipo1)",
    )
    ver.add_argument(
        "--nombres",
        nargs=6,
        metavar="N",
        default=None,
        help="Seis nombres (default: Facu Pato Manu Colo Ostu Joaco)",
    )
    ver.add_argument(
        "--sin-pausa",
        action="store_true",
        help="Sin espera entre líneas (útil para pruebas o generar transcripción)",
    )
    ver.add_argument(
        "--ui",
        choices=["auto", "textual", "rich", "curses", "simple"],
        default="auto",
        help="Backend de terminal: auto elige textual>rich>curses (default: auto)",
    )

    args = parser.parse_args()

    if args.comando == "run":
        if args.jugadores_por_equipo < 2:
            parser.error("Se requieren al menos 2 jugadores por equipo")
        config = _config_desde_args(args)
        res = simular_lote(partidos=args.partidos, config=config, verbose=args.verbose)
        print(formatear_reporte(res))
        if args.verbose and args.partidos == 1:
            estado = jugar_partido(config=config, semilla=0, verbose=True)
            print("\n--- Log del partido ---")
            print("\n".join(estado.log))

    elif args.comando == "compare":
        for reg_id in ("v1", "v2"):
            config = ConfigSimulacion(
                reglamento=reg_id,
                ia=args.ia,
                jugadores_por_equipo=args.jugadores_por_equipo,
            )
            res = simular_lote(partidos=args.partidos, config=config)
            print(formatear_reporte(res))
            print()

    elif args.comando == "compare-reglamentos":
        configs = [
            ConfigSimulacion(
                reglamento=e["id"],
                ia=args.ia,
                jugadores_por_equipo=args.jugadores_por_equipo,
            )
            for e in listar_reglamentos(solo_simulacion=True)
        ]
        resultados = simular_variantes(configs, partidos=args.partidos)
        print(formatear_comparacion_reglamentos(resultados))
        print()
        for res in resultados:
            print(formatear_reporte(res))
            print()

    elif args.comando == "compare-formatos":
        reg_ids = [e["id"] for e in listar_reglamentos(solo_simulacion=True)]
        resultados = simular_comparacion_formatos(
            reglamentos=reg_ids,
            formatos=args.formatos,
            partidos=args.partidos,
            ia=args.ia,
        )
        print(formatear_comparacion_formatos(resultados))
        print()
        for res in resultados:
            print(formatear_reporte(res))
            print()

    elif args.comando == "variantes":
        configs = cargar_variantes(args.config)
        resultados = simular_variantes(configs, partidos=args.partidos)
        print(formatear_comparacion_variantes(resultados))
        print()
        for res in resultados:
            print(formatear_reporte(res))
            print()

    elif args.comando == "reglamentos":
        if args.subcomando == "list":
            print(formatear_lista_reglamentos())
        elif args.subcomando == "show":
            print(formatear_reglamento(cargar_reglamento(args.id)))

    elif args.comando == "ver":
        if args.jugadores_por_equipo < 2:
            parser.error("Se requieren al menos 2 jugadores por equipo")
        if args.nombres and len(args.nombres) != args.jugadores_por_equipo * 2:
            parser.error(
                f"--nombres requiere exactamente {args.jugadores_por_equipo * 2} nombres"
            )
        if args.equipo1 and not args.equipo2:
            parser.error("--equipo1 requiere --equipo2")
        if args.equipo2 and not args.equipo1:
            parser.error("--equipo2 requiere --equipo1")
        config = _config_desde_args(args)
        ver_partido(
            config,
            semilla=args.semilla,
            nombres=args.nombres,
            equipo1=args.equipo1,
            equipo2=args.equipo2,
            pausa=args.pausa,
            grabar=args.grabar,
            sin_pausa=args.sin_pausa,
            velocidad=args.velocidad,
            exportar_html=args.exportar_html,
            ui=args.ui,
        )


if __name__ == "__main__":
    main()
