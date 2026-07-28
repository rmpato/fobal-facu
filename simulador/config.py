"""Configuración de simulación y variantes de reglas."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from pathlib import Path


@dataclass
class ConfigSimulacion:
    reglas: str = "v1"
    jugadores_por_equipo: int = 2
    ia: str = "estrategica"  # simple | estrategica
    pasa_turno_sin_respuesta: str = "nada"  # nada | pasa_companero
    limite_turnos: int = 500
    prob_falta: float = 0.08
    nombre_variante: str = "default"

    def __post_init__(self) -> None:
        if self.jugadores_por_equipo < 2:
            raise ValueError("Se requieren al menos 2 jugadores por equipo")
        if self.reglas not in ("v0", "v1"):
            raise ValueError("reglas debe ser v0 o v1")
        if self.ia not in ("simple", "estrategica"):
            raise ValueError("ia debe ser simple o estrategica")
        if self.pasa_turno_sin_respuesta not in ("nada", "pasa_companero"):
            raise ValueError("pasa_turno_sin_respuesta debe ser nada o pasa_companero")

    @classmethod
    def from_dict(cls, data: dict) -> ConfigSimulacion:
        valid = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid})

    def to_dict(self) -> dict:
        return {
            "reglas": self.reglas,
            "jugadores_por_equipo": self.jugadores_por_equipo,
            "ia": self.ia,
            "pasa_turno_sin_respuesta": self.pasa_turno_sin_respuesta,
            "limite_turnos": self.limite_turnos,
            "prob_falta": self.prob_falta,
            "nombre_variante": self.nombre_variante,
        }


def cargar_variantes(path: Path | str) -> list[ConfigSimulacion]:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    base = ConfigSimulacion.from_dict(data.get("base", {}))
    variantes = []
    for v in data["variantes"]:
        merged = {**base.to_dict(), **v}
        variantes.append(ConfigSimulacion.from_dict(merged))
    return variantes
