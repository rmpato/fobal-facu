"""Leer, revisar y guardar reglamentos desde la interfaz gráfica.

El motor lee los reglamentos pero no sabe escribirlos ni revisarlos: eso hace
falta solo cuando alguien los edita a mano o desde la pantalla de reglas.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from simulador.cartas import Carta, TABLAS_DISPARO, carta_por_nombre
from simulador.reglamento import (
    REGLAMENTOS_DIR,
    Reglamento,
    cargar_reglamento,
    listar_reglamentos,
)

ID_VALIDO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$")

ACCIONES = ("pase", "disparo", "reventar", "pasa_turno")
ACCIONES_SIN_CARTA = ("reventar", "pasa_turno")
REPOSICIONES = ("cambio_equipo", "mano_vacia")
SIN_RESPUESTA = ("nada", "pasa_companero")
CONTEXTOS = ("pase", "pasa_turno")

#: Cartas que se pueden jugar en defensa, para armar las listas de la pantalla.
CARTAS_DEFENSIVAS = (
    Carta.ROBO_PELOTA,
    Carta.CORTA_PASE,
    Carta.TACKLE,
    Carta.MARCA_PERSONAL,
    Carta.TRAMPA_OFFSIDE,
)
CARTAS_CONTRA = (Carta.GAMBETEAR, Carta.LA_DEJO_PASAR)


class ReglamentoInvalido(ValueError):
    def __init__(self, id_reglamento: str, errores: list[str]) -> None:
        self.id_reglamento = id_reglamento
        self.errores = errores
        super().__init__(f"El reglamento {id_reglamento!r} tiene problemas: " + "; ".join(errores))


def ruta_de(id_reglamento: str, directorio: Path | None = None) -> Path:
    if not ID_VALIDO.match(id_reglamento or ""):
        raise ValueError(
            f"Id invalido: {id_reglamento!r}. Solo letras, numeros, punto y guion."
        )
    return (directorio or REGLAMENTOS_DIR) / f"{id_reglamento}.json"


def a_dict(reg: Reglamento) -> dict[str, Any]:
    """Vuelca un reglamento ya resuelto al formato de los archivos JSON."""
    return {
        "id": reg.id,
        "nombre": reg.nombre,
        "version": reg.version,
        "descripcion": reg.descripcion,
        "documento": reg.documento,
        "mazo": {carta.value: cantidad for carta, cantidad in reg.mazo.items()},
        "partido": {
            "jugadores_minimo_por_equipo": reg.jugadores_minimo_por_equipo,
            "mano_inicial": reg.mano_inicial,
            "goles_para_ganar": reg.goles_para_ganar,
            "penales_si_marcador": list(reg.penales_si_marcador),
        },
        "reposicion": reg.reposicion,
        "disparo": {"rebote_palo": reg.rebote_palo},
        "acciones_ofensivas": list(reg.acciones_ofensivas),
        "reacciones": {
            "pase": _reaccion_a_dict(reg.reacciones_pase),
            "pasa_turno": _reaccion_a_dict(reg.reacciones_pasa_turno),
        },
        "reglas": {
            "trampa_marca_solo_en_pasa_turno": reg.trampa_marca_solo_en_pasa_turno,
            "una_reaccion_defensiva_por_accion": reg.una_reaccion_defensiva_por_accion,
            "pasa_turno_sin_respuesta": reg.pasa_turno_sin_respuesta,
            "prob_falta_por_turno": reg.prob_falta_por_turno,
            "reventar_habilitado": reg.reventar_habilitado,
            "reacciones_encadenables": reg.reacciones_encadenables,
        },
        "motor_perfil": reg.motor_perfil,
    }


def _reaccion_a_dict(reaccion) -> dict[str, Any]:
    return {
        "cartas": [c.value for c in reaccion.cartas],
        "contra": {k.value: v.value for k, v in reaccion.contra.items()},
        "permitir_tackle": reaccion.permitir_tackle,
    }


def leer(id_reglamento: str, directorio: Path | None = None) -> dict[str, Any]:
    """Devuelve el reglamento resuelto (con lo que hereda ya aplicado)."""
    datos = a_dict(cargar_reglamento(id_reglamento, dir_path=directorio))
    datos["activo"] = _esta_activo(id_reglamento, directorio)
    return datos


def catalogo(directorio: Path | None = None) -> list[dict[str, Any]]:
    entradas = []
    for entrada in listar_reglamentos(dir_path=directorio):
        try:
            reg = cargar_reglamento(entrada["id"], dir_path=directorio)
        except (FileNotFoundError, ValueError, KeyError):
            continue
        entradas.append(
            {
                "id": reg.id,
                "nombre": reg.nombre,
                "version": reg.version,
                "descripcion": reg.descripcion,
                "cartas": sum(reg.mazo.values()),
                "activo": bool(entrada.get("simulacion", True)),
            }
        )
    return entradas


def revisar(datos: dict[str, Any]) -> list[str]:
    """Lista todo lo que está mal en un reglamento. Vacía = está bien."""
    problemas: list[str] = []
    id_reglamento = str(datos.get("id", "")).strip()
    if not ID_VALIDO.match(id_reglamento):
        problemas.append("El id solo puede tener letras, numeros, punto y guion.")
    if not str(datos.get("nombre", "")).strip():
        problemas.append("Falta el nombre del reglamento.")

    mazo = datos.get("mazo") or {}
    if not mazo:
        problemas.append("El mazo esta vacio.")
    for nombre, cantidad in mazo.items():
        if carta_por_nombre(nombre) is None:
            problemas.append(f"No existe la carta {nombre!r}.")
        if not isinstance(cantidad, int) or cantidad < 0:
            problemas.append(f"La cantidad de {nombre} tiene que ser un numero positivo.")

    partido = datos.get("partido") or {}
    minimo = int(partido.get("jugadores_minimo_por_equipo", 2) or 2)
    mano = int(partido.get("mano_inicial", 6) or 6)
    goles = int(partido.get("goles_para_ganar", 3) or 3)
    penales = partido.get("penales_si_marcador") or [2, 2]

    if minimo < 2:
        problemas.append("Hacen falta al menos 2 jugadores por equipo.")
    if mano < 1:
        problemas.append("La mano inicial tiene que ser de al menos 1 carta.")
    total = sum(v for v in mazo.values() if isinstance(v, int))
    if total < mano * minimo * 2:
        problemas.append(
            f"El mazo ({total} cartas) no alcanza para repartir {mano} a "
            f"{minimo * 2} jugadores."
        )
    if goles < 1:
        problemas.append("Hace falta al menos 1 gol para ganar.")
    if any(int(g) >= goles for g in penales):
        problemas.append(
            f"El marcador que va a penales tiene que ser menor a los {goles} goles de la victoria."
        )

    acciones = list(datos.get("acciones_ofensivas") or [])
    desconocidas = [a for a in acciones if a not in ACCIONES]
    if desconocidas:
        problemas.append("Acciones que el motor no conoce: " + ", ".join(desconocidas))
    reglas = datos.get("reglas") or {}
    puede_reventar = bool(reglas.get("reventar_habilitado", True))
    salidas = [a for a in acciones if a in ACCIONES_SIN_CARTA]
    if "reventar" in salidas and not puede_reventar:
        salidas.remove("reventar")
    if not salidas:
        problemas.append(
            "El ataque se puede quedar sin jugada: habilita reventar o pasar de turno."
        )

    if datos.get("reposicion") not in REPOSICIONES:
        problemas.append("La reposicion tiene que ser cambio_equipo o mano_vacia.")
    if reglas.get("pasa_turno_sin_respuesta") not in SIN_RESPUESTA:
        problemas.append("Si nadie responde al pasa de turno: nada o pasa_companero.")
    prob = reglas.get("prob_falta_por_turno", 0.08)
    if not isinstance(prob, (int, float)) or not 0 <= prob <= 1:
        problemas.append("La chance de falta tiene que estar entre 0 y 1.")

    reacciones = datos.get("reacciones") or {}
    for contexto in CONTEXTOS:
        bloque = reacciones.get(contexto) or {}
        for nombre in bloque.get("cartas", []):
            if carta_por_nombre(nombre) is None:
                problemas.append(f"No existe la carta {nombre!r}.")
            elif not mazo.get(nombre):
                problemas.append(
                    f"La defensa responde con {nombre} pero no hay copias en el mazo."
                )
        for carta, contra in (bloque.get("contra") or {}).items():
            if not mazo.get(contra):
                problemas.append(
                    f"{contra} anula a {carta} pero no hay copias en el mazo."
                )
    if datos.get("motor_perfil") not in ("v0", "v1"):
        problemas.append("El perfil del motor tiene que ser v0 o v1.")
    return problemas


def guardar(datos: dict[str, Any], directorio: Path | None = None) -> Path:
    """Guarda el reglamento y lo anota en el índice para que aparezca en las listas."""
    problemas = revisar(datos)
    if problemas:
        raise ReglamentoInvalido(str(datos.get("id", "?")), problemas)

    directorio = directorio or REGLAMENTOS_DIR
    id_reglamento = str(datos["id"]).strip()
    ruta = ruta_de(id_reglamento, directorio)

    # Se guarda completo, sin heredar de otro: así lo que se ve en pantalla es
    # exactamente lo que dice el archivo.
    salida = {clave: datos[clave] for clave in (
        "id", "nombre", "version", "descripcion", "documento", "mazo", "partido",
        "reposicion", "disparo", "acciones_ofensivas", "reacciones", "reglas",
        "motor_perfil",
    ) if clave in datos}
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(salida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _anotar_en_indice(
        id_reglamento,
        nombre=str(datos.get("nombre", id_reglamento)),
        documento=datos.get("documento") or "",
        activo=bool(datos.get("activo", True)),
        directorio=directorio,
    )
    return ruta


def borrar(id_reglamento: str, directorio: Path | None = None) -> None:
    directorio = directorio or REGLAMENTOS_DIR
    ruta = ruta_de(id_reglamento, directorio)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el reglamento {id_reglamento!r}")
    ruta.unlink()
    indice = directorio / "indice.json"
    if indice.exists():
        datos = json.loads(indice.read_text(encoding="utf-8"))
        datos["reglamentos"] = [
            e for e in datos.get("reglamentos", []) if e.get("id") != id_reglamento
        ]
        indice.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def plantilla() -> dict[str, Any]:
    """Un reglamento nuevo, listo para editar, con los valores más usados."""
    base = a_dict(cargar_reglamento("v2"))
    base.update(
        id="",
        nombre="",
        version="1.0",
        descripcion="",
        documento=None,
        activo=True,
    )
    return base


def tabla_disparo() -> list[dict[str, Any]]:
    """La tabla de gol y atajada. Es fija en el motor: se muestra como referencia."""
    return [
        {
            "pases": t.pases,
            "gol": [t.gol_min, t.gol_max],
            "ataja": [t.ataja_min, t.ataja_max],
        }
        for t in TABLAS_DISPARO
    ]


def _esta_activo(id_reglamento: str, directorio: Path | None = None) -> bool:
    for entrada in listar_reglamentos(dir_path=directorio):
        if entrada.get("id") == id_reglamento:
            return bool(entrada.get("simulacion", True))
    return True


def _anotar_en_indice(
    id_reglamento: str,
    *,
    nombre: str,
    documento: str,
    activo: bool,
    directorio: Path,
) -> None:
    indice = directorio / "indice.json"
    datos = {"reglamentos": []}
    if indice.exists():
        datos = json.loads(indice.read_text(encoding="utf-8"))
    entradas = datos.setdefault("reglamentos", [])
    nueva = {
        "id": id_reglamento,
        "archivo": f"{id_reglamento}.json",
        "nombre": nombre,
        "documento": documento,
        "simulacion": activo,
    }
    for i, entrada in enumerate(entradas):
        if entrada.get("id") == id_reglamento:
            entradas[i] = nueva
            break
    else:
        entradas.append(nueva)
    indice.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
