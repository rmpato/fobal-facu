"""Simulación en lote y métricas.

Un escenario es una combinación de reglamento, formato (jugadores por equipo) y
perfiles de juego. Simular un escenario muchas veces con semillas consecutivas
da números repetibles: la misma orden produce siempre el mismo resultado.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from simulador.ia import AgenteIA, perfil
from simulador.motor import crear_partido, jugar_partido
from simulador.reglamento import Reglamento, cargar

#: Acciones del ataque y de la defensa que suman al reparto porcentual.
ACCIONES = ("pase", "disparo", "reventar", "pasa_turno", "robo", "falta")

#: Eventos de trampa y marca, que se informan aparte.
TRAMPAS = (
    "trampa_colocada",
    "offside_efectivo",
    "marca_colocada",
    "marca_efectiva",
    "marca_evitada",
)

ETIQUETAS = {
    "pase": "pase",
    "disparo": "disparo al arco",
    "reventar": "reventar (decisión)",
    "pasa_turno": "pasa de turno (decisión)",
    "robo": "recuperación de la defensa",
    "falta": "falta",
    "trampa_colocada": "trampas de offside puestas",
    "offside_efectivo": "offsides cobrados",
    "marca_colocada": "marcas personales puestas",
    "marca_efectiva": "marcas que recuperaron la pelota",
    "marca_evitada": "pases desviados por la marca",
    "contra": "contras del ataque (Gambetear / La dejo pasar)",
    "gol": "goles en juego",
}


@dataclass(frozen=True)
class Escenario:
    """Qué se simula: un reglamento, un formato y unos perfiles."""

    reglamento: str = "v1"
    jugadores_por_equipo: int = 3
    perfil: str = "estrategica"
    perfil_equipo1: str | None = None
    perfil_equipo2: str | None = None

    @property
    def formato(self) -> str:
        return f"{self.jugadores_por_equipo}v{self.jugadores_por_equipo}"

    @property
    def etiqueta(self) -> str:
        nombre = lambda p: perfil(p).nombre  # noqa: E731
        perfiles = nombre(self.perfil)
        if self.perfil_equipo1 or self.perfil_equipo2:
            perfiles = (
                f"{nombre(self.perfil_equipo1 or self.perfil)} vs "
                f"{nombre(self.perfil_equipo2 or self.perfil)}"
            )
        return f"{self.reglamento} · {self.formato} · {perfiles}"

    def a_dict(self) -> dict[str, Any]:
        return {
            "reglamento": self.reglamento,
            "jugadores_por_equipo": self.jugadores_por_equipo,
            "perfil": self.perfil,
            "perfil_equipo1": self.perfil_equipo1,
            "perfil_equipo2": self.perfil_equipo2,
            "formato": self.formato,
            "etiqueta": self.etiqueta,
        }

    @classmethod
    def desde_dict(cls, data: dict[str, Any]) -> Escenario:
        return cls(
            reglamento=str(data.get("reglamento", "v1")),
            jugadores_por_equipo=int(data.get("jugadores_por_equipo", 3)),
            perfil=str(data.get("perfil", "estrategica")),
            perfil_equipo1=data.get("perfil_equipo1") or None,
            perfil_equipo2=data.get("perfil_equipo2") or None,
        )


@dataclass
class Resultado:
    """Lo que dejó una tanda de partidos."""

    escenario: Escenario
    partidos: int = 0
    victorias: list[int] = field(default_factory=lambda: [0, 0])
    sin_definir: int = 0
    penales: int = 0
    turnos: int = 0
    goles: int = 0
    barajadas: int = 0
    acciones: Counter[str] = field(default_factory=Counter)
    cartas: Counter[str] = field(default_factory=Counter)

    @property
    def turnos_promedio(self) -> float:
        return self.turnos / self.partidos if self.partidos else 0.0

    @property
    def goles_promedio(self) -> float:
        return self.goles / self.partidos if self.partidos else 0.0

    @property
    def pct_completados(self) -> float:
        if not self.partidos:
            return 0.0
        return 100 * (self.partidos - self.sin_definir) / self.partidos

    @property
    def pct_penales(self) -> float:
        return 100 * self.penales / self.partidos if self.partidos else 0.0

    def por_partido(self, clave: str) -> float:
        return self.acciones.get(clave, 0) / self.partidos if self.partidos else 0.0

    def reparto_acciones(self) -> dict[str, float]:
        """Porcentaje de cada acción sobre el total de acciones."""
        total = sum(self.acciones.get(a, 0) for a in ACCIONES)
        if not total:
            return {a: 0.0 for a in ACCIONES}
        return {a: 100 * self.acciones.get(a, 0) / total for a in ACCIONES}

    def a_dict(self) -> dict[str, Any]:
        return {
            "escenario": self.escenario.a_dict(),
            "partidos": self.partidos,
            "victorias": self.victorias,
            "sin_definir": self.sin_definir,
            "penales": self.penales,
            "pct_completados": round(self.pct_completados, 1),
            "pct_penales": round(self.pct_penales, 1),
            "turnos_promedio": round(self.turnos_promedio, 1),
            "goles_promedio": round(self.goles_promedio, 2),
            "barajadas_por_partido": round(
                self.barajadas / self.partidos if self.partidos else 0, 2
            ),
            "reparto_acciones": {k: round(v, 1) for k, v in self.reparto_acciones().items()},
            "por_partido": {
                clave: round(self.por_partido(clave), 2)
                for clave in (*ACCIONES, *TRAMPAS, "contra", "gol")
            },
            "cartas": dict(self.cartas.most_common()),
        }


def simular(
    escenario: Escenario,
    partidos: int = 200,
    *,
    semilla_base: int = 0,
    progreso: Callable[[int, int], None] | None = None,
) -> Resultado:
    """Corre ``partidos`` partidos del escenario con semillas consecutivas."""
    reg = cargar(escenario.reglamento)
    res = Resultado(escenario=escenario, partidos=partidos)

    for i in range(partidos):
        estado = crear_partido(
            reg,
            jugadores_por_equipo=escenario.jugadores_por_equipo,
            semilla=semilla_base + i,
        )
        jugar_partido(estado=estado, agente=agente_de(escenario, rng=estado.rng))
        _acumular(res, estado, reg)
        if progreso and (i + 1) % 25 == 0:
            progreso(i + 1, partidos)

    if progreso:
        progreso(partidos, partidos)
    return res


def _acumular(res: Resultado, estado, reg: Reglamento) -> None:
    goles = estado.marcador.goles
    res.goles += sum(goles)
    res.turnos += estado.turno
    res.barajadas += estado.barajadas
    res.acciones.update(estado.acciones)
    res.cartas.update(estado.cartas_jugadas)
    if estado.definido_por_penales:
        res.penales += 1
    if estado.motivo_fin == "limite_turnos":
        res.sin_definir += 1
    elif goles[0] != goles[1]:
        res.victorias[0 if goles[0] > goles[1] else 1] += 1


def simular_varios(
    escenarios: Iterable[Escenario],
    partidos: int = 200,
    *,
    semilla_base: int = 0,
    progreso: Callable[[int, int], None] | None = None,
) -> list[Resultado]:
    return [
        simular(e, partidos, semilla_base=semilla_base, progreso=progreso)
        for e in escenarios
    ]


# --- salida de texto -------------------------------------------------------


def formatear_resultado(res: Resultado, *, con_reglas: bool = True) -> str:
    reg = cargar(res.escenario.reglamento)
    lineas = [
        f"=== {reg.nombre} ({reg.id}) · {res.escenario.formato} · "
        f"{res.partidos} partidos · perfil {perfil(res.escenario.perfil).nombre} ===",
    ]
    if con_reglas:
        lineas.append("")
        lineas.append("Reglas aplicadas:")
        lineas += [f"  · {linea}" for linea in reg.resumen()]

    total_victorias = sum(res.victorias)
    reparto_victorias = ""
    if total_victorias:
        reparto_victorias = (
            f"  ({100 * res.victorias[0] / total_victorias:.0f}% / "
            f"{100 * res.victorias[1] / total_victorias:.0f}%)"
        )
    lineas += [
        "",
        f"Partidos definidos      {res.pct_completados:5.1f}%  "
        f"({res.partidos - res.sin_definir} de {res.partidos})",
        f"Definidos por penales   {res.pct_penales:5.1f}%",
        f"Goles por partido       {res.goles_promedio:5.2f}",
        f"Turnos por partido      {res.turnos_promedio:5.1f}",
        f"Victorias equipo 1 / 2  {res.victorias[0]} / {res.victorias[1]}{reparto_victorias}",
        f"Barajadas del descarte  {res.barajadas / res.partidos:5.2f} por partido"
        if res.partidos
        else "Barajadas del descarte  —",
        "",
        "Acciones (reparto y frecuencia por partido):",
    ]
    reparto = res.reparto_acciones()
    for accion in ACCIONES:
        lineas.append(
            f"  {ETIQUETAS[accion]:<28} {reparto[accion]:5.1f}%   "
            f"{res.por_partido(accion):6.2f} por partido"
        )

    trampas = [t for t in TRAMPAS if res.acciones.get(t)]
    if trampas:
        lineas += ["", "Trampa de offside y marca personal:"]
        for clave in trampas:
            lineas.append(f"  {ETIQUETAS[clave]:<38} {res.por_partido(clave):6.2f} por partido")

    lineas += ["", "Cartas jugadas por partido:"]
    for carta, veces in res.cartas.most_common():
        lineas.append(f"  {carta:<20} {veces / res.partidos:6.2f}")
    return "\n".join(lineas)


COLUMNAS = (
    ("Reglamento", 12, lambda r: r.escenario.reglamento),
    ("Formato", 8, lambda r: r.escenario.formato),
    ("Definidos", 10, lambda r: f"{r.pct_completados:.1f}%"),
    ("Goles", 7, lambda r: f"{r.goles_promedio:.2f}"),
    ("Turnos", 8, lambda r: f"{r.turnos_promedio:.1f}"),
    ("Penales", 8, lambda r: f"{r.pct_penales:.1f}%"),
    ("Pase", 7, lambda r: f"{r.reparto_acciones()['pase']:.0f}%"),
    ("Robo", 7, lambda r: f"{r.reparto_acciones()['robo']:.0f}%"),
    ("Disparo", 8, lambda r: f"{r.reparto_acciones()['disparo']:.0f}%"),
    ("Trampas", 9, lambda r: f"{r.por_partido('trampa_colocada'):.1f}"),
    ("Marcas", 8, lambda r: f"{r.por_partido('marca_colocada'):.1f}"),
    ("Marcas OK", 10, lambda r: f"{r.por_partido('marca_efectiva'):.1f}"),
)


def formatear_tabla(resultados: list[Resultado], titulo: str = "Comparación") -> str:
    """Tabla de una fila por escenario, para comparar de un vistazo."""
    if not resultados:
        return f"{titulo}: sin resultados"
    encabezado = "".join(nombre.ljust(ancho) for nombre, ancho, _ in COLUMNAS)
    lineas = [
        f"=== {titulo} ({resultados[0].partidos} partidos por escenario) ===",
        "",
        encabezado,
        "-" * len(encabezado),
    ]
    for res in resultados:
        lineas.append("".join(str(valor(res)).ljust(ancho) for _, ancho, valor in COLUMNAS))
    lineas += [
        "",
        "Definidos = partidos que terminaron antes del límite de turnos.",
        "Marcas OK = marcas personales que efectivamente recuperaron la pelota.",
    ]
    return "\n".join(lineas)


def agente_de(escenario: Escenario, rng=None) -> AgenteIA:
    return AgenteIA(
        escenario.perfil,
        equipo0=escenario.perfil_equipo1,
        equipo1=escenario.perfil_equipo2,
        rng=rng,
    )
