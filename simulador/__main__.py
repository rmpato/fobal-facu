"""CLI del simulador."""

from __future__ import annotations

import argparse
from pathlib import Path

from simulador.config import ConfigSimulacion, cargar_variantes
from simulador.estadisticas import (
    formatear_comparacion_variantes,
    formatear_reporte,
    simular_lote,
    simular_variantes,
)
from simulador.motor import jugar_partido

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VARIANTES = ROOT / "configs" / "variantes.json"


def _config_desde_args(args) -> ConfigSimulacion:
    return ConfigSimulacion(
        reglas=args.reglas,
        jugadores_por_equipo=args.jugadores_por_equipo,
        ia=args.ia,
        pasa_turno_sin_respuesta=args.pasa_turno_sin_respuesta,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulador de partidos — juego de cartas de fútbol (fobal-facu)"
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    run = sub.add_parser("run", help="Correr simulaciones en lote")
    run.add_argument("--reglas", choices=["v0", "v1"], default="v1")
    run.add_argument("--partidos", type=int, default=100)
    run.add_argument("--jugadores-por-equipo", type=int, default=2, help="Mínimo 2")
    run.add_argument("--ia", choices=["simple", "estrategica"], default="estrategica")
    run.add_argument(
        "--pasa-turno-sin-respuesta",
        choices=["nada", "pasa_companero"],
        default="nada",
        dest="pasa_turno_sin_respuesta",
    )
    run.add_argument("--verbose", action="store_true")

    compare = sub.add_parser("compare", help="Comparar v0 vs v1")
    compare.add_argument("--partidos", type=int, default=200)
    compare.add_argument("--ia", choices=["simple", "estrategica"], default="estrategica")

    variantes = sub.add_parser("variantes", help="Comparar variantes de reglas desde JSON")
    variantes.add_argument("--partidos", type=int, default=500)
    variantes.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_VARIANTES,
        help="Archivo JSON con variantes",
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
        for reglas in ("v0", "v1"):
            config = ConfigSimulacion(reglas=reglas, ia=args.ia)
            res = simular_lote(partidos=args.partidos, config=config)
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


if __name__ == "__main__":
    main()
