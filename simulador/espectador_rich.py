"""Backend Rich (opcional) para modo espectador."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from simulador.cartas import Carta, carta_por_nombre, rol_carta
from simulador.espectador_log_style import rich_linea_log, rich_placa_linea
from simulador.espectador_panel_guia import rich_panel_guia
from simulador.espectador_teclas import leer_tecla
from simulador.espectador_ui import (
    ULTIMAS_JUGADAS_VISIBLE,
    banner_titulo,
    barra_comandos,
    filas_mano_fijas,
    filas_ultimas_fijas,
    formatear_linea_log,
    placa_marcador,
    slots_mano,
)
from simulador.eventos_espectador import EventoEspectador

if TYPE_CHECKING:
    from simulador.espectador import _UIBase

_NOMBRE_STYLES = [
    "bold cyan",
    "bold green",
    "bold yellow",
    "bold magenta",
    "bold red",
    "bold white",
]
_CARTA_STYLES = {
    "ofensiva": "yellow",
    "defensiva": "green",
    "neutral": "white",
}


def disponible() -> bool:
    try:
        import rich  # noqa: F401

        return True
    except ImportError:
        return False


def _texto_nombres(texto: str, colores: dict[str, int]) -> Any:
    from rich.text import Text

    out = Text()
    pos = 0
    nombres = sorted(colores.keys(), key=len, reverse=True)
    while pos < len(texto):
        match = next((n for n in nombres if texto.startswith(n, pos)), None)
        if match:
            idx = colores[match] % len(_NOMBRE_STYLES)
            out.append(match, style=_NOMBRE_STYLES[idx])
            pos += len(match)
        else:
            out.append(texto[pos])
            pos += 1
    return out


def _texto_carta(carta: Carta, *, resaltar: bool = False) -> Any:
    from rich.text import Text

    style = _CARTA_STYLES.get(rol_carta(carta), "white")
    if resaltar:
        style = f"reverse {style}"
    return Text(carta.value, style=style)


class PantallaRich:
    """UI con rich.live; hereda comportamiento de _UIBase via composicion minima."""

    def __init__(self, base: _UIBase) -> None:
        self._b = base
        from rich.console import Console
        from rich.live import Live

        self.console = Console()
        self._live = Live(
            self._render(),
            console=self.console,
            refresh_per_second=12,
            screen=True,
        )
        self._live.start()

    def close(self) -> None:
        self._live.stop()

    def __getattr__(self, name: str):
        return getattr(self._b, name)

    def _redibujar(self, resaltar: bool = False) -> None:
        self._live.update(self._render())

    def _render_log(self) -> Any:
        from rich.panel import Panel
        from rich.console import Group
        from rich.text import Text

        lineas: list[Any] = []
        if self._b._banner_gol:
            lineas.append(
                Panel(
                    Text(self._b._banner_gol, style="bold yellow"),
                    title="GOL",
                    border_style="yellow",
                )
            )
        for idx, ln in self._b._ventana_log(24):
            if not ln:
                lineas.append(Text(""))
                continue
            fmt = formatear_linea_log(ln)
            sep, line = rich_linea_log(
                ln,
                fmt,
                colores=self._b.colores,
            )
            if sep:
                lineas.append(sep)
            lineas.append(line)
        body = Group(*lineas) if lineas else Text("…", style="dim")
        return Panel(body, title="Relato del partido", border_style="bright_cyan")

    def _render_sidebar(self) -> Any:
        from rich.panel import Panel
        from rich.console import Group
        from rich.text import Text

        placa_lines = [
            rich_placa_linea(ln, self._b.colores) for ln in placa_marcador(self._b.estado)
        ]
        placa = Panel(Group(*placa_lines), title="Placa", border_style="bright_white")

        portador = self._b.estado.portador.nombre
        slots = slots_mano(self._b.estado)
        mano_lines: list[Any] = [Text("G=def  O=atak", style="dim")]
        from simulador.espectador import _cartas_ordenadas

        for num, carta in filas_mano_fijas(_cartas_ordenadas(self._b.estado.portador.mano), slots):
            line = Text(f" {num}. ")
            if carta is None:
                line.append("---", style="dim")
            else:
                resaltar = (
                    self._b._ultima_carta is not None
                    and self._b._ultima_carta[0] == portador
                    and self._b._ultima_carta[1] == carta.value
                )
                line.append(_texto_carta(carta, resaltar=resaltar))
            mano_lines.append(line)
        mano = Panel(
            Group(*mano_lines),
            title=f"Mano/{portador} ({len(self._b.estado.portador.mano)}/{slots})",
            border_style="green",
        )

        ult_lines: list[Any] = []
        for i, item in enumerate(
            filas_ultimas_fijas(self._b.estado.ultimas_cartas, ULTIMAS_JUGADAS_VISIBLE),
            start=1,
        ):
            line = Text(f" {i}. ")
            if item is None:
                line.append("---", style="dim")
            else:
                jugador, carta_nombre = item
                line.append_text(_texto_nombres(jugador, self._b.colores))
                line.append(" → ", style="dim")
                carta = carta_por_nombre(carta_nombre)
                if carta:
                    line.append_text(_texto_carta(carta))
                else:
                    line.append(carta_nombre)
            ult_lines.append(line)
        ult = Panel(
            Group(*ult_lines),
            title=f"Ultimas x{ULTIMAS_JUGADAS_VISIBLE}",
            border_style="blue",
        )
        guia = rich_panel_guia(self._b.estado, self._b.colores)
        return Group(placa, mano, ult, guia)

    def _render(self) -> Any:
        from rich.layout import Layout
        from rich.panel import Panel

        reg = self._b.estado.reglamento
        reg_id = reg.id if reg else self._b.estado.reglamento_id
        header = Panel(
            "\n".join(banner_titulo(reg_id, self._b.semilla, 78)[1:2]),
            title=f"⚽ FOBAL FACU | {reg_id.upper()} | #{self._b.semilla}",
            border_style="bright_cyan",
        )
        pausa_show = self._b.pausa_base_ms / 1000
        footer_txt = "\n".join(
            barra_comandos(
                pausa_show,
                auto=self._b.auto_pausa,
                velocidad=self._b.velocidad,
            )
        )
        footer = Panel(footer_txt, border_style="dim green")
        layout = Layout()
        layout.split_column(
            Layout(header, size=5),
            Layout(name="body"),
            Layout(footer, size=4),
        )
        layout["body"].split_row(
            Layout(self._render_log(), ratio=3),
            Layout(self._render_sidebar(), ratio=2),
        )
        return layout

    def _esperar(self, ev: EventoEspectador) -> None:
        if not self._b._debe_esperar(ev):
            return
        ms = self._b._ms_espera(ev)
        timeout = None if ms < 0 else ms / 1000.0
        while True:
            ch = leer_tecla(timeout)
            if ch is None and timeout is not None:
                return
            if ch is None and timeout is None:
                continue
            if ch in ("q", "Q"):
                self._b.abortar = True
                self._b.estado.abortar = True
                return
            if ch in (" ", "\n", "\r"):
                return
            if ch in ("+", "="):
                self._b._ajustar_velocidad(1)
                self._redibujar()
                timeout = None if ms < 0 else ms / 1000.0
                continue
            if ch in ("-", "_"):
                self._b._ajustar_velocidad(-1)
                self._redibujar()
                continue
            if ch in ("p", "P"):
                self._b.auto_pausa = not self._b.auto_pausa
                self._redibujar()
                continue
            if ch in ("f", "F"):
                self._b._fast_forward = True
                return


def envolver(base: _UIBase) -> PantallaRich:
    rich_ui = PantallaRich(base)
    base._redibujar = rich_ui._redibujar  # type: ignore[method-assign]
    base._esperar = rich_ui._esperar  # type: ignore[method-assign]
    return rich_ui
