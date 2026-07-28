"""Agregación de estadísticas de simulaciones."""

from __future__ import annotations

from dataclasses import dataclass, field

from simulador.motor import jugar_partido


@dataclass
class ResultadosSimulacion:
    reglas: str
    partidos: int
    victorias: list[int] = field(default_factory=lambda: [0, 0])
    empates_tecnicos: int = 0
    penales: int = 0
    turnos_total: int = 0
    goles_total: int = 0
    barajadas_total: int = 0
    cartas_jugadas: dict[str, int] = field(default_factory=dict)

    @property
    def turnos_promedio(self) -> float:
        return self.turnos_total / self.partidos if self.partidos else 0

    @property
    def goles_promedio(self) -> float:
        return self.goles_total / self.partidos if self.partidos else 0


def simular_lote(
    reglas: str,
    partidos: int,
    jugadores_por_equipo: int = 2,
    verbose: bool = False,
) -> ResultadosSimulacion:
    res = ResultadosSimulacion(reglas=reglas, partidos=partidos)

    for i in range(partidos):
        estado = jugar_partido(
            reglas=reglas,
            jugadores_por_equipo=jugadores_por_equipo,
            semilla=i,
            verbose=verbose,
        )
        goles = estado.marcador.goles
        res.goles_total += sum(goles)
        res.turnos_total += estado.turnos
        res.barajadas_total += estado.barajadas_descarte

        if estado.definido_por_penales:
            res.penales += 1

        if estado.turnos >= 500:
            res.empates_tecnicos += 1
        else:
            if goles[0] > goles[1]:
                res.victorias[0] += 1
            elif goles[1] > goles[0]:
                res.victorias[1] += 1

        for carta, n in estado.cartas_jugadas.items():
            res.cartas_jugadas[carta] = res.cartas_jugadas.get(carta, 0) + n

    return res


def formatear_reporte(res: ResultadosSimulacion) -> str:
    lineas = [
        f"=== Simulación {res.reglas.upper()} ({res.partidos} partidos) ===",
        f"Victorias equipo 0: {res.victorias[0]} ({100 * res.victorias[0] / res.partidos:.1f}%)",
        f"Victorias equipo 1: {res.victorias[1]} ({100 * res.victorias[1] / res.partidos:.1f}%)",
        f"Empates técnicos (>{500} turnos): {res.empates_tecnicos}",
        f"Partidos definidos por penales: {res.penales}",
        f"Turnos promedio: {res.turnos_promedio:.1f}",
        f"Goles promedio: {res.goles_promedio:.2f}",
        f"Barajadas de descarte (total): {res.barajadas_total}",
        "",
        "Cartas jugadas (top):",
    ]
    top = sorted(res.cartas_jugadas.items(), key=lambda x: -x[1])
    for carta, n in top:
        por_partido = n / res.partidos
        lineas.append(f"  {carta}: {n} ({por_partido:.2f}/partido)")
    return "\n".join(lineas)
