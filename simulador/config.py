"""Configuración de simulación y variantes de reglas."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simulador.reglamento import Reglamento


@dataclass
class ConfigSimulacion:
    reglamento: str = "v1"
    jugadores_por_equipo: int = 2
    ia: str = "estrategica"  # simple | estrategica
    limite_turnos: int = 500
    prob_falta: float | None = None  # None = usar valor del reglamento
    nombre_variante: str = "default"
    # Override puntual (preferir reglamento dedicado, p. ej. v1.1)
    pasa_turno_sin_respuesta: str | None = None
    _reglamento_resuelto: Reglamento | None = field(default=None, repr=False)

    @property
    def reglas(self) -> str:
        """Alias histórico: perfil del motor (v0/v1) del reglamento cargado."""
        return self.reglamento_resuelto.motor_perfil

    @property
    def reglamento_resuelto(self) -> Reglamento:
        if self._reglamento_resuelto is None:
            from simulador.reglamento import cargar_reglamento

            reg = cargar_reglamento(self.reglamento)
            overrides: dict = {}
            if self.pasa_turno_sin_respuesta is not None:
                overrides["pasa_turno_sin_respuesta"] = self.pasa_turno_sin_respuesta
            if self.prob_falta is not None:
                overrides["prob_falta_por_turno"] = self.prob_falta
            if overrides:
                reg = reg.with_overrides(**overrides)
            self._reglamento_resuelto = reg
        return self._reglamento_resuelto

    def __post_init__(self) -> None:
        if self.jugadores_por_equipo < 2:
            raise ValueError("Se requieren al menos 2 jugadores por equipo")
        if self.ia not in ("simple", "estrategica"):
            raise ValueError("ia debe ser simple o estrategica")
        if self.pasa_turno_sin_respuesta is not None and self.pasa_turno_sin_respuesta not in (
            "nada",
            "pasa_companero",
        ):
            raise ValueError("pasa_turno_sin_respuesta debe ser nada o pasa_companero")
        # Valida que el reglamento exista y cumple mínimos
        reg = self.reglamento_resuelto
        if self.jugadores_por_equipo < reg.jugadores_minimo_por_equipo:
            raise ValueError(
                f"El reglamento {reg.id} requiere al menos "
                f"{reg.jugadores_minimo_por_equipo} jugadores por equipo"
            )

    @classmethod
    def from_dict(cls, data: dict) -> ConfigSimulacion:
        valid = {f.name for f in fields(cls) if not f.name.startswith("_")}
        normalizado = dict(data)
        if "reglas" in normalizado and "reglamento" not in normalizado:
            reglas = normalizado.pop("reglas")
            if reglas in ("v0", "v1"):
                normalizado["reglamento"] = reglas
            else:
                normalizado["reglamento"] = reglas
        return cls(**{k: v for k, v in normalizado.items() if k in valid})

    def to_dict(self) -> dict:
        d = {
            "reglamento": self.reglamento,
            "jugadores_por_equipo": self.jugadores_por_equipo,
            "ia": self.ia,
            "limite_turnos": self.limite_turnos,
            "nombre_variante": self.nombre_variante,
        }
        if self.pasa_turno_sin_respuesta is not None:
            d["pasa_turno_sin_respuesta"] = self.pasa_turno_sin_respuesta
        if self.prob_falta is not None:
            d["prob_falta"] = self.prob_falta
        return d


def cargar_variantes(path: Path | str) -> list[ConfigSimulacion]:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    base = ConfigSimulacion.from_dict(data.get("base", {}))
    variantes = []
    for v in data["variantes"]:
        merged = {**base.to_dict(), **v}
        variantes.append(ConfigSimulacion.from_dict(merged))
    return variantes
