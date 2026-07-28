"""CLI del simulador."""

from __future__ import annotations

import argparse

from simulador.estadisticas import formatear_reporte, simular_lote
from simulador.motor import jugar_partido


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulador de partidos — juego de cartas de fútbol (fobal-facu)"
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    run = sub.add_parser("run", help="Correr simulaciones en lote")
    run.add_argument("--reglas", choices=["v0", "v1"], default="v1")
    run.add_argument("--partidos", type=int, default=100)
    run.add_argument("--jugadores-por-equipo", type=int, default=2, help="Mínimo 2")
    run.add_argument("--verbose", action="store_true")

    sub.add_parser("compare", help="Comparar v0 vs v1 con la misma cantidad de partidos")

    args = parser.parse_args()

    if args.comando == "run":
        if args.jugadores_por_equipo < 2:
            parser.error("Se requieren al menos 2 jugadores por equipo")
        res = simular_lote(
            reglas=args.reglas,
            partidos=args.partidos,
            jugadores_por_equipo=args.jugadores_por_equipo,
            verbose=args.verbose,
        )
        print(formatear_reporte(res))
        if args.verbose and args.partidos == 1:
            estado = jugar_partido(args.reglas, args.jugadores_por_equipo, semilla=0, verbose=True)
            print("\n--- Log del partido ---")
            print("\n".join(estado.log))

    elif args.comando == "compare":
        n = 200
        for reglas in ("v0", "v1"):
            res = simular_lote(reglas, n, jugadores_por_equipo=2)
            print(formatear_reporte(res))
            print()


if __name__ == "__main__":
    main()
