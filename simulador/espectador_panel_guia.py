"""Panel lateral: reglamento, IA y anticipo de jugadas."""

from __future__ import annotations

from simulador.cartas import Carta
from simulador.ia import agresividad_defensa, ia_resuelta, nombre_ia, pesos_ataque
from simulador.modelo import EstadoPartido


def _pct(prob: float) -> str:
    return f"{max(0, min(100, int(round(prob * 100))))}%"


def _nombres_cartas(cartas: list[Carta], *, corto: bool = False) -> str:
    if not cartas:
        return "—"
    if corto:
        abrev = {
            Carta.TRAMPA_OFFSIDE: "Offside",
            Carta.MARCA_PERSONAL: "Marca",
            Carta.ROBO_PELOTA: "Robo",
            Carta.CORTA_PASE: "Corta",
            Carta.DISPARO: "Disparo",
        }
        return ", ".join(abrev.get(c, c.value) for c in cartas)
    return ", ".join(c.value for c in cartas)


def _encabezado_panel(estado: EstadoPartido) -> list[str]:
    reg = estado.reglamento
    reg_id = reg.id if reg else estado.reglamento_id
    cfg = estado.config
    lineas = [f"Reglamento {reg_id}"]
    if cfg is None:
        lineas.append(f"IA: {nombre_ia('estrategica')}")
        return lineas

    ia0 = cfg.ia_de_equipo(0)
    ia1 = cfg.ia_de_equipo(1)
    distintas = ia0 != ia1 or cfg.ia_equipo0 or cfg.ia_equipo1
    if distintas:
        n0 = nombre_ia(ia_resuelta(cfg, estado, 0))
        n1 = nombre_ia(ia_resuelta(cfg, estado, 1))
        lineas.append(f"E1: {n0}")
        lineas.append(f"E2: {n1}")
    else:
        ia_efectiva = ia_resuelta(cfg, estado, estado.portador.equipo)
        etiqueta = nombre_ia(ia_efectiva)
        if ia0 == "adaptativo" and ia_efectiva != "adaptativo":
            etiqueta = f"{nombre_ia('adaptativo')} -> {etiqueta}"
        lineas.append(f"IA: {etiqueta}")
    return lineas


def _anticipo_ataque(estado: EstadoPartido) -> list[str]:
    cfg = estado.config
    ia_id = (
        ia_resuelta(cfg, estado, estado.portador.equipo)
        if cfg
        else "estrategica"
    )
    portador = estado.portador
    opciones = pesos_ataque(estado, ia_id)
    lineas = [f"{portador.nombre} (bola):"]
    for accion, prob, nota in opciones:
        extra = f" ({nota})" if nota else ""
        lineas.append(f" · {accion} ~{_pct(prob)}{extra}")
    return lineas


def _anticipo_defensa(estado: EstadoPartido) -> list[str]:
    cfg = estado.config
    ia_id = (
        ia_resuelta(cfg, estado, estado.equipo_defensivo)
        if cfg
        else "estrategica"
    )
    reg = estado.reglamento
    if not reg:
        return []

    agres = agresividad_defensa(ia_id)
    lineas: list[str] = []

    for d in estado.defensores():
        for carta in reg.reacciones_pase.cartas:
            if not d.tiene(carta):
                continue
            if carta == Carta.CORTA_PASE and reg.motor_perfil == "v0":
                prob = 0.35 * agres
            elif carta == Carta.ROBO_PELOTA and reg.motor_perfil == "v1":
                prob = 0.42 * agres
            else:
                prob = 0.30 * agres
            lineas.append(
                f" si pase: {d.nombre} {_nombres_cartas([carta], corto=True)} ~{_pct(prob)}"
            )

    fav_marca = 0.70 if ia_id == "marcador" else 0.40
    for d in estado.defensores():
        for carta in reg.reacciones_pasa_turno.cartas:
            if not d.tiene(carta):
                continue
            if carta == Carta.TRAMPA_OFFSIDE:
                prob = 0.35 * agres
            elif carta == Carta.MARCA_PERSONAL:
                prob = fav_marca * agres
            elif carta == Carta.TACKLE and reg.motor_perfil == "v0":
                prob = 0.45 * agres
            else:
                prob = 0.30 * agres
            lineas.append(
                f" si pasa turno: {d.nombre} {_nombres_cartas([carta], corto=True)} ~{_pct(prob)}"
            )

    if not lineas:
        return [" def: sin cartas reactivas"]
    return [" def podria:"] + lineas[:4]


def panel_guia(estado: EstadoPartido, *, ancho: int = 40) -> list[str]:
    """Lineas cortas para el panel de anticipo IA."""
    lineas = _encabezado_panel(estado)
    lineas.append("---")
    lineas.extend(_anticipo_ataque(estado))
    lineas.extend(_anticipo_defensa(estado))
    if ancho > 0:
        return [ln[:ancho] for ln in lineas]
    return lineas


def rich_panel_guia(estado: EstadoPartido, colores: dict[str, int]) -> object:
    from rich.console import Group
    from rich.panel import Panel
    from rich.text import Text

    from simulador.espectador_log_style import _rich_nombres

    lineas_rich: list[Text] = []
    for ln in panel_guia(estado, ancho=0):
        if ln.startswith("Reglamento "):
            lineas_rich.append(Text(ln, style="bold white"))
            continue
        if ln.startswith(("IA: ", "E1: ", "E2: ")):
            lineas_rich.append(Text(ln, style="bold magenta"))
            continue
        if ln == "---":
            lineas_rich.append(Text("─" * 28, style="dim"))
            continue
        if ln.endswith("(bola):"):
            nombre = ln[: -len("(bola):")].strip()
            t = Text()
            t.append_text(_rich_nombres(nombre, colores, base_style="bold white"))
            t.append(" (bola):", style="white")
            lineas_rich.append(t)
            continue
        if ln.startswith(" · "):
            lineas_rich.append(Text(ln, style="green"))
            continue
        if ln.startswith(" si ") or ln.startswith(" def"):
            lineas_rich.append(Text(ln, style="cyan"))
            continue
        lineas_rich.append(Text(ln, style="white"))
    return Panel(Group(*lineas_rich), title="Anticipo IA", border_style="magenta")
