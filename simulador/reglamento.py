"""Carga y resolución de reglamentos (rulesets) para el simulador."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

from simulador.cartas import Carta, construir_mazo

DECISIONES_SIN_CARTA = frozenset({"pasa_turno", "reventar"})
ETIQUETAS_DECISION = {
    "pasa_turno": "pasa de turno (decisión, sin carta)",
    "reventar": "reventar / despeje (decisión, sin carta)",
}

ROOT = Path(__file__).resolve().parent.parent
REGLAMENTOS_DIR = ROOT / "reglamentos"


@dataclass
class ReaccionesContexto:
    cartas: list[Carta]
    contra: dict[Carta, Carta]
    permitir_tackle: bool = False


@dataclass
class Reglamento:
    """Reglas aplicadas por el motor en una simulación."""

    id: str
    nombre: str
    version: str
    documento: str | None
    descripcion: str
    mazo: dict[Carta, int]
    jugadores_minimo_por_equipo: int = 2
    mano_inicial: int = 6
    goles_para_ganar: int = 3
    penales_si_marcador: tuple[int, int] = (2, 2)
    reposicion: str = "cambio_equipo"  # cambio_equipo | mano_vacia
    rebote_palo: bool = True
    acciones_ofensivas: list[str] = field(default_factory=list)
    reacciones_pase: ReaccionesContexto = field(
        default_factory=lambda: ReaccionesContexto(cartas=[], contra={})
    )
    reacciones_pasa_turno: ReaccionesContexto = field(
        default_factory=lambda: ReaccionesContexto(cartas=[], contra={})
    )
    trampa_marca_solo_en_pasa_turno: bool = True
    una_reaccion_defensiva_por_accion: bool = True
    pasa_turno_sin_respuesta: str = "nada"
    prob_falta_por_turno: float = 0.08
    reventar_habilitado: bool = True
    motor_perfil: str = "v1"

    @property
    def reglas(self) -> str:
        """Alias histórico (v0/v1) según perfil del motor."""
        return self.motor_perfil

    def construir_mazo(self) -> list[Carta]:
        return construir_mazo(self.mazo)

    def resumen_reglas(self) -> list[str]:
        """Lista legible de reglas que el simulador aplica."""
        con_carta = [a for a in self.acciones_ofensivas if a not in DECISIONES_SIN_CARTA]
        sin_carta = [a for a in self.acciones_ofensivas if a in DECISIONES_SIN_CARTA]
        if self.reventar_habilitado and "reventar" not in sin_carta:
            sin_carta.append("reventar")
        elif not self.reventar_habilitado and "reventar" in sin_carta:
            sin_carta = [a for a in sin_carta if a != "reventar"]

        lineas = [
            f"Documento: {self.documento or '(sin documento)'}",
            f"Mazo: {sum(self.mazo.values())} cartas ({len(self.mazo)} tipos)",
            f"Victoria: primer equipo en {self.goles_para_ganar} goles",
            f"Penales si marcador {list(self.penales_si_marcador)}",
            f"Reposición: {self.reposicion}",
            f"Disparo rebote/palo: {'sí' if self.rebote_palo else 'no'}",
            f"Acciones con carta: {', '.join(con_carta) or 'ninguna'}",
            f"Decisiones sin carta: {', '.join(sin_carta) or 'ninguna'}",
            f"Defensa al pase: {_nombres_cartas(self.reacciones_pase.cartas) or 'ninguna'}",
            f"Defensa al pasa de turno: {_nombres_cartas(self.reacciones_pasa_turno.cartas) or 'ninguna'}",
            f"Tackle en pasa de turno: {'sí' if self.reacciones_pasa_turno.permitir_tackle else 'no'}",
            f"Trampa/marca solo cuando ataque pasa de turno (decisión): {'sí' if self.trampa_marca_solo_en_pasa_turno else 'no'}",
            f"Una reacción defensiva por acción: {'sí' if self.una_reaccion_defensiva_por_accion else 'no'}",
            f"Pasa de turno sin respuesta: {self.pasa_turno_sin_respuesta}",
            f"Prob. falta oportunista/turno: {self.prob_falta_por_turno:.0%}",
            f"Perfil motor: {self.motor_perfil}",
        ]
        return lineas

    def with_overrides(self, **kwargs: Any) -> Reglamento:
        """Copia con campos sobreescritos (p. ej. desde CLI o variantes)."""
        data = {f.name: getattr(self, f.name) for f in fields(self)}
        for key, value in kwargs.items():
            if key in data and value is not None:
                data[key] = value
        return Reglamento(**data)


def _nombres_cartas(cartas: list[Carta]) -> str:
    return ", ".join(c.value for c in cartas)


def _carta_desde_nombre(nombre: str) -> Carta:
    for carta in Carta:
        if carta.value == nombre:
            return carta
    raise ValueError(f"Carta desconocida en reglamento: {nombre!r}")


def _parse_mazo(raw: dict[str, int]) -> dict[Carta, int]:
    return {_carta_desde_nombre(k): v for k, v in raw.items()}


def _parse_reacciones(raw: dict) -> ReaccionesContexto:
    cartas = [_carta_desde_nombre(c) for c in raw.get("cartas", [])]
    contra = {
        _carta_desde_nombre(k): _carta_desde_nombre(v)
        for k, v in raw.get("contra", {}).items()
    }
    return ReaccionesContexto(
        cartas=cartas,
        contra=contra,
        permitir_tackle=bool(raw.get("permitir_tackle", False)),
    )


def _reglamento_desde_dict(data: dict) -> Reglamento:
    partido = data.get("partido", {})
    reglas = data.get("reglas", {})
    disparo = data.get("disparo", {})
    reacciones = data.get("reacciones", {})

    penales = partido.get("penales_si_marcador", [2, 2])
    return Reglamento(
        id=data["id"],
        nombre=data.get("nombre", data["id"]),
        version=str(data.get("version", "0")),
        documento=data.get("documento"),
        descripcion=data.get("descripcion", ""),
        mazo=_parse_mazo(data["mazo"]),
        jugadores_minimo_por_equipo=partido.get("jugadores_minimo_por_equipo", 2),
        mano_inicial=partido.get("mano_inicial", 6),
        goles_para_ganar=partido.get("goles_para_ganar", 3),
        penales_si_marcador=(penales[0], penales[1]),
        reposicion=data.get("reposicion", "cambio_equipo"),
        rebote_palo=bool(disparo.get("rebote_palo", True)),
        acciones_ofensivas=list(data.get("acciones_ofensivas", [])),
        reacciones_pase=_parse_reacciones(reacciones.get("pase", {})),
        reacciones_pasa_turno=_parse_reacciones(reacciones.get("pasa_turno", {})),
        trampa_marca_solo_en_pasa_turno=bool(reglas.get("trampa_marca_solo_en_pasa_turno", True)),
        una_reaccion_defensiva_por_accion=bool(
            reglas.get("una_reaccion_defensiva_por_accion", True)
        ),
        pasa_turno_sin_respuesta=reglas.get("pasa_turno_sin_respuesta", "nada"),
        prob_falta_por_turno=float(reglas.get("prob_falta_por_turno", 0.08)),
        reventar_habilitado=bool(reglas.get("reventar_habilitado", True)),
        motor_perfil=data.get("motor_perfil", "v1"),
    )


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if key == "extends":
            continue
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _cargar_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolver_reglamento(data: dict, cache: dict[str, dict]) -> dict:
    extends = data.get("extends")
    if not extends:
        return data
    if extends not in cache:
        base_path = REGLAMENTOS_DIR / f"{extends}.json"
        if not base_path.exists():
            raise ValueError(f"Reglamento base {extends!r} no encontrado ({base_path})")
        cache[extends] = _cargar_json(base_path)
    base_resuelto = _resolver_reglamento(cache[extends], cache)
    merged = _deep_merge(base_resuelto, data)
    merged["id"] = data["id"]
    if "nombre" in data:
        merged["nombre"] = data["nombre"]
    if "version" in data:
        merged["version"] = data["version"]
    if "documento" in data:
        merged["documento"] = data["documento"]
    if "descripcion" in data:
        merged["descripcion"] = data["descripcion"]
    return merged


def cargar_reglamento(reglamento_id: str, *, dir_path: Path | None = None) -> Reglamento:
    """Carga un reglamento por id (p. ej. v1, v1.1) o ruta a JSON."""
    dir_path = dir_path or REGLAMENTOS_DIR
    path = Path(reglamento_id)
    if path.suffix == ".json" and path.exists():
        data = _cargar_json(path)
    else:
        candidato = dir_path / f"{reglamento_id}.json"
        if not candidato.exists():
            raise FileNotFoundError(
                f"Reglamento {reglamento_id!r} no encontrado. "
                f"Esperado: {candidato}. Usá `python -m simulador reglamentos list`."
            )
        data = _cargar_json(candidato)

    cache: dict[str, dict] = {data.get("id", reglamento_id): data}
    resuelto = _resolver_reglamento(data, cache)
    return _reglamento_desde_dict(resuelto)


def listar_reglamentos(*, dir_path: Path | None = None) -> list[dict[str, str]]:
    dir_path = dir_path or REGLAMENTOS_DIR
    indice = dir_path / "indice.json"
    if indice.exists():
        data = _cargar_json(indice)
        return list(data.get("reglamentos", []))

    entradas = []
    for path in sorted(dir_path.glob("*.json")):
        if path.name.startswith("_"):
            continue
        raw = _cargar_json(path)
        entradas.append(
            {
                "id": raw.get("id", path.stem),
                "archivo": path.name,
                "nombre": raw.get("nombre", path.stem),
                "documento": raw.get("documento", ""),
            }
        )
    return entradas


def formatear_reglamento(reg: Reglamento) -> str:
    lineas = [
        f"=== Reglamento {reg.id} · {reg.nombre} (v{reg.version}) ===",
        reg.descripcion,
        "",
        "Reglas aplicadas por el simulador:",
    ]
    lineas.extend(f"  · {linea}" for linea in reg.resumen_reglas())
    return "\n".join(lineas)


def formatear_lista_reglamentos() -> str:
    entradas = listar_reglamentos()
    lineas = ["=== Reglamentos disponibles ===", ""]
    for e in entradas:
        doc = e.get("documento") or ""
        lineas.append(f"  {e['id']:<8} {e['nombre']}")
        if doc:
            lineas.append(f"           → {doc}")
    lineas.extend(
        [
            "",
            "Simular:  python -m simulador run --reglamento v1",
            "Detalle:  python -m simulador reglamentos show v1",
            "Nuevo:    copiá reglamentos/_plantilla.json → reglamentos/vX.json",
        ]
    )
    return "\n".join(lineas)
