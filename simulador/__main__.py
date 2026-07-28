"""CLI del simulador."""

from __future__ import annotations

import argparse
from pathlib import Path

from simulador.config import ConfigSimulacion, cargar_variantes
from simulador.estadisticas import (
    formatear_comparacion_reglamentos,
    formatear_comparacion_variantes,
    formatear_reporte,
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

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VARIANTES = ROOT / "configs" / "variantes.json"


def _config_desde_args(args) -> ConfigSimulacion:
    reglamento = getattr(args, "reglamento", None) or getattr(args, "reglas", "v1")
    kwargs = {
        "reglamento": reglamento,
        "jugadores_por_equipo": args.jugadores_por_equipo,
        "ia": args.ia,
    }
    if getattr(args, "pasa_turno_sin_respuesta", None) is not None:
        kwargs["pasa_turno_sin_respuesta"] = args.pasa_turno_sin_respuesta
    return ConfigSimulacion(**kwargs)


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
    run.add_argument("--jugadores-por-equipo", type=int, default=2, help="Mínimo 2")
    run.add_argument("--ia", choices=["simple", "estrategica"], default="estrategica")
    run.add_argument(
        "--pasa-turno-sin-respuesta",
        choices=["nada", "pasa_companero"],
        default=None,
        dest="pasa_turno_sin_respuesta",
        help="Override puntual (preferir reglamento v1.1)",
    )
    run.add_argument("--verbose", action="store_true")

    compare = sub.add_parser("compare", help="Comparar v0 vs v1 (alias histórico)")
    compare.add_argument("--partidos", type=int, default=200)
    compare.add_argument("--ia", choices=["simple", "estrategica"], default="estrategica")

    compare_reg = sub.add_parser(
        "compare-reglamentos",
        help="Comparar todos los reglamentos del índice",
    )
    compare_reg.add_argument("--partidos", type=int, default=200)
    compare_reg.add_argument("--ia", choices=["simple", "estrategica"], default="estrategica")

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
        for reg_id in ("v0", "v1"):
            config = ConfigSimulacion(reglamento=reg_id, ia=args.ia)
            res = simular_lote(partidos=args.partidos, config=config)
            print(formatear_reporte(res))
            print()

    elif args.comando == "compare-reglamentos":
        configs = [
            ConfigSimulacion(reglamento=e["id"], ia=args.ia) for e in listar_reglamentos()
        ]
        resultados = simular_variantes(configs, partidos=args.partidos)
        print(formatear_comparacion_reglamentos(resultados))
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


if __name__ == "__main__":
    main()
