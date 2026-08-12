"""Reglamentos: las reglas que el motor aplica en una simulación.

Un reglamento es un archivo JSON en ``reglamentos/``. Describe el mazo, la mano,
cuándo se repone, la tabla de disparo, qué acciones puede hacer el ataque y con
qué cartas puede responder la defensa. El motor no tiene reglas propias: todo lo
que cambia entre una versión del juego y otra vive acá.

Un reglamento puede heredar de otro con ``"extends"`` y sobrescribir solo lo que
cambia; ver :func:`cargar`.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from simulador.cartas import TRAMPAS, Carta, construir_mazo, desde_nombre

RAIZ = Path(__file__).resolve().parent.parent
DIRECTORIO = RAIZ / "reglamentos"

ID_VALIDO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$")

#: Acciones que puede elegir quien tiene la pelota.
ACCIONES = ("pase", "disparo", "reventar", "pasa_turno")

#: Acciones que no gastan carta: siempre hay al menos una disponible.
ACCIONES_SIN_CARTA = ("reventar", "pasa_turno")

#: Cuándo los jugadores levantan cartas hasta el máximo de mano.
MOMENTOS_REPOSICION = (
    "cambio_equipo",  # cuando la pelota cambia de equipo
    "mano_vacia",  # cuando un jugador se queda sin cartas
    "fin_de_turno",  # al terminar cada turno
    "al_jugar_carta",  # apenas se juega una carta
    "nunca",  # no se repone: se juega hasta que se acaben las manos
)

#: Quiénes reponen cuando se cumple el momento.
ALCANCES_REPOSICION = ("todos", "equipo_con_pelota", "equipo_sin_pelota", "el_jugador")

#: Qué pasa si el ataque pasa de turno y la defensa no responde.
SIN_RESPUESTA = ("nada", "pasa_companero")


class ReglamentoInvalido(ValueError):
    """El JSON del reglamento tiene errores; ``errores`` los lista todos."""

    def __init__(self, id_reglamento: str, errores: list[str]) -> None:
        self.id_reglamento = id_reglamento
        self.errores = errores
        detalle = "\n".join(f"  - {e}" for e in errores)
        super().__init__(f"Reglamento {id_reglamento!r} inválido:\n{detalle}")


@dataclass(frozen=True)
class FranjaDisparo:
    """Rangos de dado para una cantidad de pases encadenados."""

    pases: int
    gol: tuple[int, int]
    ataja: tuple[int, int]

    def es_gol(self, dado: int) -> bool:
        return self.gol[0] <= dado <= self.gol[1]

    def es_atajada(self, dado: int) -> bool:
        return self.ataja[0] <= dado <= self.ataja[1]

    def a_dict(self) -> dict[str, Any]:
        return {"pases": self.pases, "gol": list(self.gol), "ataja": list(self.ataja)}


@dataclass(frozen=True)
class TablaDisparo:
    """Tabla completa de disparo, ordenada por cantidad de pases."""

    franjas: tuple[FranjaDisparo, ...]

    def para(self, pases: int) -> FranjaDisparo:
        elegida = self.franjas[0]
        for franja in self.franjas:
            if franja.pases <= pases:
                elegida = franja
        return elegida

    def a_lista(self) -> list[dict[str, Any]]:
        return [f.a_dict() for f in self.franjas]


@dataclass(frozen=True)
class Reaccion:
    """Cartas con las que la defensa puede responder, y su contra ofensiva."""

    cartas: tuple[Carta, ...] = ()
    contra: dict[Carta, Carta] = field(default_factory=dict)

    def contra_de(self, carta: Carta) -> Carta | None:
        return self.contra.get(carta)

    def a_dict(self) -> dict[str, Any]:
        return {
            "cartas": [c.value for c in self.cartas],
            "contra": {k.value: v.value for k, v in self.contra.items()},
        }


@dataclass(frozen=True)
class Reposicion:
    """Cuándo y quién levanta cartas hasta el máximo de mano."""

    momento: str = "cambio_equipo"
    quien: str = "todos"

    def a_dict(self) -> dict[str, Any]:
        return {"momento": self.momento, "quien": self.quien}


@dataclass(frozen=True)
class Reglamento:
    """Reglas completas y resueltas de una versión del juego."""

    id: str
    nombre: str
    version: str = "0"
    descripcion: str = ""
    documento: str | None = None
    activo: bool = True
    mazo: dict[Carta, int] = field(default_factory=dict)
    jugadores_minimo_por_equipo: int = 2
    mano_inicial: int = 6
    mano_maxima: int = 6
    goles_para_ganar: int = 3
    penales_si_marcador: tuple[int, int] = (2, 2)
    limite_turnos: int = 500
    reposicion: Reposicion = field(default_factory=Reposicion)
    rebote: bool = True
    palo: bool = True
    tabla_disparo: TablaDisparo = field(
        default_factory=lambda: TablaDisparo(
            tuple(
                FranjaDisparo(pases=i, gol=(1, 1 + i), ataja=(2 + i, 6))
                for i in range(5)
            )
        )
    )
    acciones_ofensivas: tuple[str, ...] = ("pase", "disparo", "reventar")
    reacciones: dict[str, Reaccion] = field(default_factory=dict)
    pasa_turno_sin_respuesta: str = "nada"
    prob_falta_por_jugador: float = 0.08
    reacciones_encadenables: bool = False

    # --- consultas que hace el motor -------------------------------------

    def permite(self, accion: str) -> bool:
        return accion in self.acciones_ofensivas

    def reaccion(self, contexto: str) -> Reaccion:
        return self.reacciones.get(contexto, Reaccion())

    def cartas_del_mazo(self) -> list[Carta]:
        return construir_mazo(self.mazo)

    @property
    def total_cartas(self) -> int:
        return sum(self.mazo.values())

    def con_cambios(self, **cambios: Any) -> Reglamento:
        """Copia con campos reemplazados (para overrides puntuales)."""
        return replace(self, **{k: v for k, v in cambios.items() if v is not None})

    # --- serialización ----------------------------------------------------

    def a_dict(self) -> dict[str, Any]:
        """Vuelca el reglamento resuelto al formato JSON del repositorio."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "version": self.version,
            "descripcion": self.descripcion,
            "documento": self.documento,
            "activo": self.activo,
            "mazo": {c.value: n for c, n in self.mazo.items()},
            "partido": {
                "jugadores_minimo_por_equipo": self.jugadores_minimo_por_equipo,
                "goles_para_ganar": self.goles_para_ganar,
                "penales_si_marcador": list(self.penales_si_marcador),
                "limite_turnos": self.limite_turnos,
            },
            "mano": {"inicial": self.mano_inicial, "maxima": self.mano_maxima},
            "reposicion": self.reposicion.a_dict(),
            "disparo": {
                "rebote": self.rebote,
                "palo": self.palo,
                "tabla": self.tabla_disparo.a_lista(),
            },
            "acciones_ofensivas": list(self.acciones_ofensivas),
            "reacciones": {k: v.a_dict() for k, v in self.reacciones.items()},
            "reglas": {
                "pasa_turno_sin_respuesta": self.pasa_turno_sin_respuesta,
                "prob_falta_por_jugador": self.prob_falta_por_jugador,
                "reacciones_encadenables": self.reacciones_encadenables,
            },
        }

    def resumen(self) -> list[str]:
        """Líneas legibles con las reglas que el simulador va a aplicar."""
        rep = self.reposicion
        pase = self.reaccion("pase")
        pasa_turno = self.reaccion("pasa_turno")
        contras = ", ".join(f"{k} → {v}" for k, v in _contras(self)) or "ninguna"
        return [
            f"Mazo: {self.total_cartas} cartas ({len(self.mazo)} tipos)",
            f"Mano: {self.mano_inicial} inicial, máximo {self.mano_maxima}",
            f"Reposición: {rep.momento} ({rep.quien})",
            f"Victoria: primer equipo en {self.goles_para_ganar} goles",
            f"Penales si el marcador llega a {'-'.join(map(str, self.penales_si_marcador))}",
            f"Acciones del ataque: {', '.join(self.acciones_ofensivas)}",
            f"Defensa al pase: {_nombres(pase.cartas)}",
            f"Defensa al pasa de turno: {_nombres(pasa_turno.cartas)}",
            f"Contras del ataque: {contras}",
            f"Reacciones encadenables: {'sí' if self.reacciones_encadenables else 'no'}",
            f"Pasa de turno sin respuesta: {self.pasa_turno_sin_respuesta}",
            f"Falta: {self.prob_falta_por_jugador:.0%} por jugador y turno",
            f"Disparo: rebote {'sí' if self.rebote else 'no'}, palo {'sí' if self.palo else 'no'}",
            f"Límite de turnos: {self.limite_turnos}",
        ]


def _nombres(cartas: tuple[Carta, ...]) -> str:
    return ", ".join(c.value for c in cartas) or "ninguna"


def _contras(reg: Reglamento) -> list[tuple[str, str]]:
    vistos: list[tuple[str, str]] = []
    for reaccion in reg.reacciones.values():
        for carta, contra in reaccion.contra.items():
            par = (carta.value, contra.value)
            if par not in vistos:
                vistos.append(par)
    return vistos


# --- lectura del JSON -----------------------------------------------------

_CLAVES_RAIZ = {
    "id",
    "nombre",
    "version",
    "descripcion",
    "documento",
    "activo",
    "extends",
    "mazo",
    "partido",
    "mano",
    "reposicion",
    "disparo",
    "acciones_ofensivas",
    "reacciones",
    "reglas",
}
_CLAVES_PARTIDO = {
    "jugadores_minimo_por_equipo",
    "goles_para_ganar",
    "penales_si_marcador",
    "limite_turnos",
}
_CLAVES_REGLAS = {
    "pasa_turno_sin_respuesta",
    "prob_falta_por_jugador",
    "reacciones_encadenables",
}


def desde_dict(data: dict[str, Any]) -> Reglamento:
    """Construye un reglamento ya resuelto (sin ``extends``) desde un dict."""
    errores = _claves_desconocidas(data)
    if "id" not in data:
        errores.append("falta la clave 'id'")
    if errores:
        raise ReglamentoInvalido(str(data.get("id", "?")), errores)

    partido = data.get("partido", {})
    mano = data.get("mano", {})
    disparo = data.get("disparo", {})
    reglas = data.get("reglas", {})
    rep = data.get("reposicion", {})
    penales = partido.get("penales_si_marcador", [2, 2])

    reg = Reglamento(
        id=str(data["id"]),
        nombre=data.get("nombre", str(data["id"])),
        version=str(data.get("version", "0")),
        descripcion=data.get("descripcion", ""),
        documento=data.get("documento"),
        activo=bool(data.get("activo", True)),
        mazo={desde_nombre(k): int(v) for k, v in data.get("mazo", {}).items()},
        jugadores_minimo_por_equipo=int(partido.get("jugadores_minimo_por_equipo", 2)),
        mano_inicial=int(mano.get("inicial", 6)),
        mano_maxima=int(mano.get("maxima", mano.get("inicial", 6))),
        goles_para_ganar=int(partido.get("goles_para_ganar", 3)),
        penales_si_marcador=(int(penales[0]), int(penales[1])),
        limite_turnos=int(partido.get("limite_turnos", 500)),
        reposicion=Reposicion(
            momento=rep.get("momento", "cambio_equipo"),
            quien=rep.get("quien", "todos"),
        ),
        rebote=bool(disparo.get("rebote", True)),
        palo=bool(disparo.get("palo", True)),
        tabla_disparo=_tabla_desde_lista(disparo.get("tabla")),
        acciones_ofensivas=tuple(data.get("acciones_ofensivas", ())),
        reacciones={
            contexto: _reaccion_desde_dict(valor)
            for contexto, valor in data.get("reacciones", {}).items()
        },
        pasa_turno_sin_respuesta=reglas.get("pasa_turno_sin_respuesta", "nada"),
        prob_falta_por_jugador=float(reglas.get("prob_falta_por_jugador", 0.08)),
        reacciones_encadenables=bool(reglas.get("reacciones_encadenables", False)),
    )
    errores = validar(reg)
    if errores:
        raise ReglamentoInvalido(reg.id, errores)
    return reg


def _claves_desconocidas(data: dict[str, Any]) -> list[str]:
    errores = []
    for clave in set(data) - _CLAVES_RAIZ:
        errores.append(f"clave desconocida: {clave!r}")
    for clave in set(data.get("partido", {})) - _CLAVES_PARTIDO:
        errores.append(f"clave desconocida en 'partido': {clave!r}")
    for clave in set(data.get("reglas", {})) - _CLAVES_REGLAS:
        errores.append(f"clave desconocida en 'reglas': {clave!r}")
    return errores


def _tabla_desde_lista(raw: list[dict[str, Any]] | None) -> TablaDisparo:
    if not raw:
        return Reglamento.__dataclass_fields__["tabla_disparo"].default_factory()
    franjas = []
    for fila in raw:
        gol = fila.get("gol", [1, 1])
        ataja = fila.get("ataja", [2, 6])
        franjas.append(
            FranjaDisparo(
                pases=int(fila.get("pases", 0)),
                gol=(int(gol[0]), int(gol[1])),
                ataja=(int(ataja[0]), int(ataja[1])),
            )
        )
    franjas.sort(key=lambda f: f.pases)
    return TablaDisparo(tuple(franjas))


def _reaccion_desde_dict(raw: dict[str, Any]) -> Reaccion:
    return Reaccion(
        cartas=tuple(desde_nombre(c) for c in raw.get("cartas", [])),
        contra={
            desde_nombre(k): desde_nombre(v) for k, v in raw.get("contra", {}).items()
        },
    )


def validar(reg: Reglamento) -> list[str]:
    """Devuelve la lista de problemas del reglamento (vacía si está bien)."""
    errores: list[str] = []

    if not ID_VALIDO.match(reg.id):
        errores.append(
            f"id inválido: {reg.id!r} (letras, números, punto, guion; hasta 32)"
        )
    if not reg.mazo:
        errores.append("el mazo está vacío")
    for carta, cantidad in reg.mazo.items():
        if cantidad < 0:
            errores.append(f"cantidad negativa de {carta.value}: {cantidad}")
    if reg.mano_inicial < 1:
        errores.append("la mano inicial debe ser de al menos 1 carta")
    if reg.mano_maxima < reg.mano_inicial:
        errores.append("el máximo de mano no puede ser menor que la mano inicial")
    if reg.jugadores_minimo_por_equipo < 2:
        errores.append("se necesitan al menos 2 jugadores por equipo")
    minimo_cartas = reg.mano_inicial * reg.jugadores_minimo_por_equipo * 2
    if reg.total_cartas < minimo_cartas:
        errores.append(
            f"el mazo ({reg.total_cartas}) no alcanza para repartir "
            f"{reg.mano_inicial} cartas a {reg.jugadores_minimo_por_equipo * 2} jugadores"
        )
    if reg.goles_para_ganar < 1:
        errores.append("goles_para_ganar debe ser al menos 1")
    if any(g >= reg.goles_para_ganar for g in reg.penales_si_marcador):
        errores.append(
            "penales_si_marcador debe ser un marcador anterior a la victoria "
            f"({reg.goles_para_ganar} goles)"
        )
    if reg.limite_turnos < 1:
        errores.append("limite_turnos debe ser positivo")
    if reg.reposicion.momento not in MOMENTOS_REPOSICION:
        errores.append(
            f"reposicion.momento debe ser uno de: {', '.join(MOMENTOS_REPOSICION)}"
        )
    if reg.reposicion.quien not in ALCANCES_REPOSICION:
        errores.append(
            f"reposicion.quien debe ser uno de: {', '.join(ALCANCES_REPOSICION)}"
        )
    if reg.pasa_turno_sin_respuesta not in SIN_RESPUESTA:
        errores.append(
            f"pasa_turno_sin_respuesta debe ser uno de: {', '.join(SIN_RESPUESTA)}"
        )
    if not 0.0 <= reg.prob_falta_por_jugador <= 1.0:
        errores.append("prob_falta_por_jugador debe estar entre 0 y 1")

    desconocidas = [a for a in reg.acciones_ofensivas if a not in ACCIONES]
    if desconocidas:
        errores.append(
            f"acciones desconocidas: {', '.join(desconocidas)} "
            f"(válidas: {', '.join(ACCIONES)})"
        )
    if not any(a in reg.acciones_ofensivas for a in ACCIONES_SIN_CARTA):
        errores.append(
            "el ataque se puede quedar sin jugada: habilitá 'reventar' o 'pasa_turno', "
            "que no gastan carta"
        )
    if "reventar" in reg.acciones_ofensivas and reg.jugadores_minimo_por_equipo < 2:
        errores.append("reventar necesita al menos 2 jugadores por equipo")

    for contexto, reaccion in reg.reacciones.items():
        if contexto not in ("pase", "pasa_turno"):
            errores.append(f"contexto de reacción desconocido: {contexto!r}")
        for carta in reaccion.cartas:
            if reg.mazo.get(carta, 0) == 0:
                errores.append(
                    f"la defensa reacciona con {carta.value} pero no hay copias en el mazo"
                )
        for carta, contra in reaccion.contra.items():
            # Las trampas se colocan en un contexto y se disparan en otro, así
            # que su contra puede declararse donde surte efecto.
            if carta not in reaccion.cartas and carta not in TRAMPAS:
                errores.append(
                    f"contra de {carta.value} en '{contexto}' pero esa carta no se juega ahí"
                )
            if reg.mazo.get(contra, 0) == 0:
                errores.append(
                    f"{contra.value} anula a {carta.value} pero no hay copias en el mazo"
                )

    if not reg.tabla_disparo.franjas:
        errores.append("la tabla de disparo está vacía")
    for franja in reg.tabla_disparo.franjas:
        for etiqueta, (desde, hasta) in (("gol", franja.gol), ("ataja", franja.ataja)):
            if not 1 <= desde <= hasta <= 6:
                errores.append(
                    f"tabla de disparo (pases {franja.pases}): rango {etiqueta} "
                    f"inválido {desde}-{hasta}, debe estar entre 1 y 6"
                )
    return errores


# --- catálogo en disco ----------------------------------------------------


def ruta_de(id_reglamento: str, *, directorio: Path | None = None) -> Path:
    """Ruta del JSON de un id, validando que no se escape del directorio."""
    if not ID_VALIDO.match(id_reglamento):
        raise ValueError(f"Id de reglamento inválido: {id_reglamento!r}")
    return (directorio or DIRECTORIO) / f"{id_reglamento}.json"


def _leer_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReglamentoInvalido(path.stem, [f"JSON mal formado: {exc}"]) from None


#: Bloques donde heredar completa lo que el hijo no menciona. El resto de las
#: claves (el mazo, las reacciones) se reemplazan enteras, así un reglamento
#: hijo puede sacar una carta y no solo cambiarle la cantidad.
CLAVES_FUSIONABLES = ("partido", "mano", "reposicion", "disparo", "reglas")


def _fusionar(base: dict[str, Any], encima: dict[str, Any]) -> dict[str, Any]:
    resultado = dict(base)
    for clave, valor in encima.items():
        if clave == "extends":
            continue
        if (
            clave in CLAVES_FUSIONABLES
            and isinstance(valor, dict)
            and isinstance(resultado.get(clave), dict)
        ):
            resultado[clave] = {**resultado[clave], **valor}
        else:
            resultado[clave] = valor
    return resultado


def _resolver(data: dict[str, Any], directorio: Path, vistos: tuple[str, ...] = ()) -> dict[str, Any]:
    base_id = data.get("extends")
    if not base_id:
        return data
    if base_id in vistos:
        cadena = " → ".join([*vistos, base_id])
        raise ReglamentoInvalido(str(data.get("id", "?")), [f"herencia circular: {cadena}"])
    ruta = ruta_de(base_id, directorio=directorio)
    if not ruta.exists():
        raise ReglamentoInvalido(
            str(data.get("id", "?")), [f"el reglamento base {base_id!r} no existe ({ruta})"]
        )
    base = _resolver(_leer_json(ruta), directorio, (*vistos, str(data.get("id", "?"))))
    return _fusionar(base, data)


def cargar(id_o_ruta: str, *, directorio: Path | None = None) -> Reglamento:
    """Carga un reglamento por id (``v1``) o por ruta a un archivo ``.json``."""
    directorio = directorio or DIRECTORIO
    ruta = Path(id_o_ruta)
    if ruta.suffix == ".json":
        if not ruta.exists():
            raise FileNotFoundError(f"No existe el archivo {ruta}")
    else:
        ruta = ruta_de(id_o_ruta, directorio=directorio)
        if not ruta.exists():
            disponibles = ", ".join(r["id"] for r in catalogo(directorio=directorio))
            raise FileNotFoundError(
                f"No existe el reglamento {id_o_ruta!r}. Disponibles: {disponibles}"
            )
    return desde_dict(_resolver(_leer_json(ruta), directorio))


def catalogo(*, directorio: Path | None = None, solo_activos: bool = False) -> list[dict[str, Any]]:
    """Lista los reglamentos del directorio, ordenados por versión."""
    directorio = directorio or DIRECTORIO
    entradas = []
    for ruta in sorted(directorio.glob("*.json")):
        if ruta.name.startswith("_"):
            continue
        try:
            reg = cargar(ruta.stem, directorio=directorio)
        except (ReglamentoInvalido, ValueError):
            continue
        if solo_activos and not reg.activo:
            continue
        entradas.append(
            {
                "id": reg.id,
                "nombre": reg.nombre,
                "version": reg.version,
                "descripcion": reg.descripcion,
                "documento": reg.documento,
                "activo": reg.activo,
                "cartas": reg.total_cartas,
            }
        )
    entradas.sort(key=lambda e: _clave_version(e["version"]))
    return entradas


def _clave_version(version: str) -> tuple[int, ...]:
    partes = []
    for trozo in str(version).split("."):
        partes.append(int(trozo) if trozo.isdigit() else 0)
    return tuple(partes)


def guardar(reg: Reglamento, *, extends: str | None = None, directorio: Path | None = None) -> Path:
    """Escribe el reglamento a disco.

    Si ``extends`` apunta a otro reglamento, guarda solo las diferencias contra
    él, de modo que el archivo quede corto y siga heredando cambios de la base.
    """
    directorio = directorio or DIRECTORIO
    errores = validar(reg)
    if errores:
        raise ReglamentoInvalido(reg.id, errores)

    data = reg.a_dict()
    if extends:
        if extends == reg.id:
            raise ReglamentoInvalido(reg.id, ["un reglamento no puede heredar de sí mismo"])
        base = cargar(extends, directorio=directorio).a_dict()
        data = _diferencias(base, data)
        data = {"id": reg.id, "nombre": reg.nombre, "extends": extends, **data}

    ruta = ruta_de(reg.id, directorio=directorio)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return ruta


def _diferencias(base: dict[str, Any], nuevo: dict[str, Any]) -> dict[str, Any]:
    """Subconjunto de ``nuevo`` que difiere de ``base`` (recursivo en dicts)."""
    salida: dict[str, Any] = {}
    for clave, valor in nuevo.items():
        anterior = base.get(clave)
        if clave in CLAVES_FUSIONABLES and isinstance(valor, dict) and isinstance(anterior, dict):
            sub = {k: v for k, v in valor.items() if anterior.get(k) != v}
            if sub:
                salida[clave] = sub
        elif valor != anterior:
            salida[clave] = valor
    return salida
