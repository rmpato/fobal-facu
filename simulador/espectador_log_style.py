"""Estilos compartidos para el relato (Rich + Textual)."""

from __future__ import annotations

from simulador.eventos_espectador import EventoEspectador, clasificar_evento

_MARKUP_COLORES = ["cyan", "green", "yellow", "magenta", "red", "white"]

_RICH_ESTILO: dict[str, str] = {
    "gol": "bold yellow",
    "turno": "bold bright_cyan",
    "pase": "green",
    "disparo": "yellow",
    "pasa_turno": "white",
    "reventar": "bright_white",
    "robo": "magenta",
    "defensa": "dim cyan",
    "dado": "dim italic",
    "cambio_equipo": "bold magenta",
    "penales": "bold red",
    "fin": "bold yellow",
    "empate": "bold yellow",
    "info": "cyan",
    "intro": "dim",
    "otro": "white",
}

_MARKUP_ESTILO: dict[str, str] = {
    "gol": "bold yellow",
    "turno": "bold cyan",
    "pase": "green",
    "disparo": "yellow",
    "pasa_turno": "white",
    "reventar": "white",
    "robo": "magenta",
    "defensa": "dim cyan",
    "dado": "dim italic",
    "cambio_equipo": "bold magenta",
    "penales": "bold red",
    "fin": "bold yellow",
    "empate": "bold yellow",
    "info": "cyan",
    "intro": "dim",
    "otro": "white",
}

_SEPARADOR_TIPOS = frozenset({"turno", "gol", "penales", "cambio_equipo", "fin", "empate"})


def _esc_markup(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace("[", "\\[")


def _aplicar_nombres_markup(texto: str, colores: dict[str, int]) -> str:
    if not colores:
        return _esc_markup(texto)
    out = texto
    for nombre in sorted(colores.keys(), key=len, reverse=True):
        idx = colores[nombre] % len(_MARKUP_COLORES)
        color = _MARKUP_COLORES[idx]
        marcado = f"[bold {color}]{_esc_markup(nombre)}[/]"
        out = out.replace(nombre, marcado)
    return _esc_markup(out) if out == texto else out


def estilo_evento(ev: EventoEspectador) -> str:
    return _RICH_ESTILO.get(ev.tipo, _RICH_ESTILO["otro"])


def necesita_separador(ev: EventoEspectador) -> bool:
    return ev.tipo in _SEPARADOR_TIPOS


def rich_linea_log(
    raw: str,
    fmt: str,
    *,
    colores: dict[str, int],
) -> tuple[object | None, object]:
    """Devuelve (separador opcional, linea Rich Text)."""
    from rich.text import Text

    ev = clasificar_evento(raw)
    sep = None
    if necesita_separador(ev):
        sep = Text("─" * 52, style="dim")

    base = estilo_evento(ev)

    t = Text()
    prefijos = {
        "gol": "⚽ ",
        "turno": "▶ ",
        "pase": "→ ",
        "disparo": "! ",
        "pasa_turno": "○ ",
        "defensa": "· ",
        "dado": "  ",
        "cambio_equipo": "⇄ ",
        "penales": "PK ",
    }
    pref = prefijos.get(ev.tipo, "  ")
    t.append(pref, style="dim")
    t.append_text(_rich_nombres(fmt, colores, base_style=base))
    return sep, t


def _rich_nombres(texto: str, colores: dict[str, int], base_style: str) -> object:
    from rich.text import Text

    estilos = [
        "bold cyan",
        "bold green",
        "bold yellow",
        "bold magenta",
        "bold red",
        "bold white",
    ]
    out = Text()
    pos = 0
    nombres = sorted(colores.keys(), key=len, reverse=True)
    while pos < len(texto):
        match = next((n for n in nombres if texto.startswith(n, pos)), None)
        if match:
            idx = colores[match] % len(estilos)
            out.append(match, style=estilos[idx])
            pos += len(match)
        else:
            ch = texto[pos]
            out.append(ch, style=base_style)
            pos += 1
    return out


def markup_linea_log(
    raw: str,
    fmt: str,
    *,
    colores: dict[str, int],
) -> str:
    ev = clasificar_evento(raw)
    partes: list[str] = []
    if necesita_separador(ev):
        partes.append("[dim]" + "─" * 48 + "[/]")
    estilo = _MARKUP_ESTILO.get(ev.tipo, "white")
    prefijos = {
        "gol": "⚽ ",
        "turno": "▶ ",
        "pase": "→ ",
        "disparo": "! ",
        "pasa_turno": "○ ",
        "defensa": "· ",
        "dado": "  ",
        "cambio_equipo": "⇄ ",
        "penales": "PK ",
    }
    pref = prefijos.get(ev.tipo, "  ")
    cuerpo = _aplicar_nombres_markup(fmt, colores)
    if cuerpo == _esc_markup(fmt):
        cuerpo = f"[{estilo}]{_esc_markup(fmt)}[/]"
    else:
        cuerpo = f"[{estilo}]{cuerpo}[/]"
    partes.append(f"[dim]{pref}[/]{cuerpo}")
    return "\n".join(partes)


def rich_placa_linea(linea: str, colores: dict[str, int]) -> object:
    from rich.text import Text

    t = Text()
    if linea.strip().startswith("*"):
        t.append("● ", style="bold yellow")
    elif "bola:" in linea:
        t.append("⚽ ", style="yellow")
    elif "def:" in linea:
        t.append("🛡 ", style="cyan")
    elif "trampa:" in linea:
        t.append("!", style="magenta")
    t.append_text(_rich_nombres(linea.rstrip(), colores, base_style="white"))
    return t


def markup_placa(lineas: list[str], colores: dict[str, int]) -> str:
    out: list[str] = []
    for ln in lineas:
        if ln.strip().startswith("*"):
            out.append(f"[bold yellow]●[/] {_aplicar_nombres_markup(ln.rstrip(), colores)}")
        elif "bola:" in ln:
            out.append(f"[yellow]⚽[/] {_aplicar_nombres_markup(ln.rstrip(), colores)}")
        elif "GOL" in ln or ln.strip()[0:1].isdigit():
            out.append(f"[bold white]{_aplicar_nombres_markup(ln.rstrip(), colores)}[/]")
        else:
            out.append(_aplicar_nombres_markup(ln.rstrip(), colores))
    return "\n".join(out)
