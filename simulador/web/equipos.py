"""Los equipos que se usan en los partidos: nombre y jugadores.

No son parte de las reglas del juego, así que viven aparte de los reglamentos,
en ``configs/equipos.json``. Se editan desde la pantalla de equipos.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent.parent
ARCHIVO = RAIZ / "configs" / "equipos.json"

POR_DEFECTO: dict[str, Any] = {
    "equipo1": {"nombre": "Equipo 1", "jugadores": ["Facu", "Pato", "Manu"]},
    "equipo2": {"nombre": "Equipo 2", "jugadores": ["Colo", "Ostu", "Joaco"]},
}


def leer(archivo: Path | None = None) -> dict[str, Any]:
    archivo = archivo or ARCHIVO
    if not archivo.exists():
        return json.loads(json.dumps(POR_DEFECTO))
    try:
        datos = json.loads(archivo.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return json.loads(json.dumps(POR_DEFECTO))
    return _normalizar(datos)


def guardar(datos: dict[str, Any], *, maximo: int = 8, archivo: Path | None = None) -> dict[str, Any]:
    archivo = archivo or ARCHIVO
    limpio = _normalizar(datos)
    for clave in ("equipo1", "equipo2"):
        jugadores = limpio[clave]["jugadores"]
        if len(jugadores) < 2:
            raise ValueError(f"{limpio[clave]['nombre']}: hacen falta al menos 2 jugadores.")
        if len(jugadores) > maximo:
            raise ValueError(f"{limpio[clave]['nombre']}: como maximo {maximo} jugadores.")

    repetidos = set(_apodos(limpio["equipo1"])) & set(_apodos(limpio["equipo2"]))
    if repetidos:
        raise ValueError("Hay nombres repetidos en los dos equipos: " + ", ".join(sorted(repetidos)))

    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text(json.dumps(limpio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return limpio


def _apodos(equipo: dict[str, Any]) -> list[str]:
    return [j.lower() for j in equipo["jugadores"]]


def _normalizar(datos: dict[str, Any]) -> dict[str, Any]:
    salida: dict[str, Any] = {}
    for clave, base in POR_DEFECTO.items():
        crudo = datos.get(clave) or {}
        nombre = str(crudo.get("nombre", base["nombre"])).strip() or base["nombre"]
        jugadores = [
            str(j).strip()[:20] for j in (crudo.get("jugadores") or []) if str(j).strip()
        ]
        salida[clave] = {"nombre": nombre[:30], "jugadores": jugadores or list(base["jugadores"])}
    return salida
