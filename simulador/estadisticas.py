"""Agregación de estadísticas de simulaciones."""

from __future__ import annotations

from dataclasses import dataclass, field

from simulador.config import ConfigSimulacion
from simulador.motor import jugar_partido

ACCIONES_REPORTE = ("pase", "disparo", "robo", "despeje", "pasa_turno", "falta")
ETIQUETAS_ACCION = {
    "pasa_turno": "pasa de turno (decisión)",
    "despeje": "reventar / despeje (decisión)",
}
ACCIONES_TRAMPA = ("trampa_colocada", "marca_colocada", "offside_efectivo", "marca_efectiva")


@dataclass
class ResultadosSimulacion:
    reglamento: str
    partidos: int
    config: ConfigSimulacion | None = None
    victorias: list[int] = field(default_factory=lambda: [0, 0])
    empates_tecnicos: int = 0
    penales: int = 0
    turnos_total: int = 0
    goles_total: int = 0
    barajadas_total: int = 0
    cartas_jugadas: dict[str, int] = field(default_factory=dict)
    acciones: dict[str, int] = field(default_factory=dict)

    @property
    def reglas(self) -> str:
        """Alias histórico."""
        return self.reglamento

    @property
    def turnos_promedio(self) -> float:
        return self.turnos_total / self.partidos if self.partidos else 0

    @property
    def goles_promedio(self) -> float:
        return self.goles_total / self.partidos if self.partidos else 0

    @property
    def limite_turnos(self) -> int:
        return self.config.limite_turnos if self.config else 500

    def pct_acciones(self) -> dict[str, float]:
        total = sum(self.acciones.get(a, 0) for a in ACCIONES_REPORTE)
        if total == 0:
            return {a: 0.0 for a in ACCIONES_REPORTE}
        return {a: 100 * self.acciones.get(a, 0) / total for a in ACCIONES_REPORTE}


def simular_lote(
    reglas: str = "v1",
    reglamento: str | None = None,
    partidos: int = 100,
    jugadores_por_equipo: int = 3,
    verbose: bool = False,
    config: ConfigSimulacion | None = None,
) -> ResultadosSimulacion:
    if config is None:
        config = ConfigSimulacion(
            reglamento=reglamento or reglas,
            jugadores_por_equipo=jugadores_por_equipo,
        )
    reglamento_id = config.reglamento
    res = ResultadosSimulacion(reglamento=reglamento_id, partidos=partidos, config=config)

    for i in range(partidos):
        estado = jugar_partido(config=config, semilla=i, verbose=verbose)
        goles = estado.marcador.goles
        res.goles_total += sum(goles)
        res.turnos_total += estado.turnos
        res.barajadas_total += estado.barajadas_descarte

        if estado.definido_por_penales:
            res.penales += 1

        if estado.turnos >= config.limite_turnos:
            res.empates_tecnicos += 1
        else:
            if goles[0] > goles[1]:
                res.victorias[0] += 1
            elif goles[1] > goles[0]:
                res.victorias[1] += 1

        for carta, n in estado.cartas_jugadas.items():
            res.cartas_jugadas[carta] = res.cartas_jugadas.get(carta, 0) + n
        for accion, n in estado.acciones.items():
            res.acciones[accion] = res.acciones.get(accion, 0) + n

    return res


def simular_variantes(
    configs: list[ConfigSimulacion],
    partidos: int,
) -> list[ResultadosSimulacion]:
    return [simular_lote(partidos=partidos, config=c) for c in configs]


def formatear_reporte(res: ResultadosSimulacion) -> str:
    reg = res.config.reglamento_resuelto if res.config else None
    titulo = f"=== Simulación · reglamento {res.reglamento}"
    if reg:
        titulo += f" · {reg.nombre}"
    titulo += f" ({res.partidos} partidos)"
    if res.config:
        titulo += (
            f" · {res.config.jugadores_por_equipo}v{res.config.jugadores_por_equipo}"
            f" · {res.config.nombre_variante} · ia={res.config.ia}"
        )
    titulo += " ==="

    lineas = [titulo]
    if reg:
        if reg.documento:
            lineas.append(f"Documento: {reg.documento}")
        lineas.extend(["Reglas aplicadas:"])
        for item in reg.resumen_reglas()[1:]:  # omitir doc duplicado
            lineas.append(f"  · {item}")
        lineas.append("")

    lineas.extend(
        [
            f"Victorias equipo 0: {res.victorias[0]} ({100 * res.victorias[0] / res.partidos:.1f}%)",
            f"Victorias equipo 1: {res.victorias[1]} ({100 * res.victorias[1] / res.partidos:.1f}%)",
            f"Empates técnicos (>{res.limite_turnos} turnos): {res.empates_tecnicos}",
            f"Partidos definidos por penales: {res.penales}",
            f"Turnos promedio: {res.turnos_promedio:.1f}",
            f"Goles promedio: {res.goles_promedio:.2f}",
            f"Barajadas de descarte (total): {res.barajadas_total}",
            "",
            "Acciones (% del total):",
        ]
    )
    pct = res.pct_acciones()
    for accion in ACCIONES_REPORTE:
        n = res.acciones.get(accion, 0)
        por_partido = n / res.partidos if res.partidos else 0
        etiqueta = ETIQUETAS_ACCION.get(accion, accion)
        lineas.append(f"  {etiqueta}: {pct[accion]:5.1f}%  ({por_partido:.2f}/partido)")

    trampa_total = sum(res.acciones.get(a, 0) for a in ACCIONES_TRAMPA)
    if trampa_total:
        lineas.extend(["", "Trampa / Marca:"])
        for accion in ACCIONES_TRAMPA:
            n = res.acciones.get(accion, 0)
            if n:
                lineas.append(f"  {accion}: {n} ({n / res.partidos:.2f}/partido)")

    lineas.extend(["", "Cartas jugadas (top):"])
    top = sorted(res.cartas_jugadas.items(), key=lambda x: -x[1])
    for carta, n in top:
        por_partido = n / res.partidos
        lineas.append(f"  {carta}: {n} ({por_partido:.2f}/partido)")
    return "\n".join(lineas)


def formatear_comparacion_variantes(resultados: list[ResultadosSimulacion]) -> str:
    jpe = resultados[0].config.jugadores_por_equipo if resultados and resultados[0].config else 3
    lineas = [
        "=== Comparación de variantes ===",
        f"({jpe} vs {jpe} · {resultados[0].partidos if resultados else 0} partidos c/u)",
        "",
    ]
    header = f"{'Variante':<18} {'Compl.':>7} {'Goles':>6} {'Turnos':>7} {'Pen.':>5} {'Pase%':>6} {'PasaT%':>7} {'Trampa':>7}"
    lineas.append(header)
    lineas.append("-" * len(header))

    for res in resultados:
        completados = res.partidos - res.empates_tecnicos
        pct_compl = 100 * completados / res.partidos if res.partidos else 0
        pct = res.pct_acciones()
        trampa = res.acciones.get("trampa_colocada", 0) / res.partidos
        nombre = res.config.nombre_variante if res.config else "?"
        lineas.append(
            f"{nombre:<18} {pct_compl:6.1f}% {res.goles_promedio:6.2f} {res.turnos_promedio:7.1f} "
            f"{100 * res.penales / res.partidos:4.1f}% {pct['pase']:5.1f}% {pct['pasa_turno']:6.1f}% {trampa:7.2f}"
        )
    return "\n".join(lineas)


def formatear_comparacion_reglamentos(resultados: list[ResultadosSimulacion]) -> str:
    jpe = resultados[0].config.jugadores_por_equipo if resultados and resultados[0].config else 3
    lineas = [
        "=== Comparación de reglamentos ===",
        f"({jpe} vs {jpe} · {resultados[0].partidos if resultados else 0} partidos c/u)",
        "",
    ]
    header = (
        f"{'Reglamento':<10} {'Compl.':>7} {'Goles':>6} {'Turnos':>7} "
        f"{'Pen.':>5} {'Pase%':>6} {'PasaT%':>7} {'Trampa':>7}"
    )
    lineas.append(header)
    lineas.append("-" * len(header))

    for res in resultados:
        completados = res.partidos - res.empates_tecnicos
        pct_compl = 100 * completados / res.partidos if res.partidos else 0
        pct = res.pct_acciones()
        trampa = res.acciones.get("trampa_colocada", 0) / res.partidos
        lineas.append(
            f"{res.reglamento:<10} {pct_compl:6.1f}% {res.goles_promedio:6.2f} {res.turnos_promedio:7.1f} "
            f"{100 * res.penales / res.partidos:4.1f}% {pct['pase']:5.1f}% {pct['pasa_turno']:6.1f}% {trampa:7.2f}"
        )
    return "\n".join(lineas)
