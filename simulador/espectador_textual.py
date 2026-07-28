"""Backend Textual (opcional) para modo espectador."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Callable

from simulador.espectador_ui import (
    ULTIMAS_JUGADAS_VISIBLE,
    barra_comandos,
    filas_mano_fijas,
    filas_ultimas_fijas,
    formatear_linea_log,
    placa_marcador,
    slots_mano,
)
from simulador.eventos_espectador import EventoEspectador

if TYPE_CHECKING:
    from simulador.config import ConfigSimulacion
    from simulador.espectador import _UIBase
    from simulador.modelo import EstadoPartido


def disponible() -> bool:
    try:
        import textual  # noqa: F401

        return True
    except ImportError:
        return False


def _plain_log(ui: _UIBase) -> str:
    out: list[str] = []
    if ui._banner_gol:
        out.append(f"** {ui._banner_gol} **")
    for idx, ln in ui._ventana_log(24):
        if not ln:
            out.append("")
            continue
        fmt = formatear_linea_log(ln)
        mark = "> " if idx == ui._ultimo_log_idx else ""
        out.append(mark + fmt)
    return "\n".join(out) or "…"


def _plain_side(ui: _UIBase) -> str:
    from simulador.espectador import _cartas_ordenadas

    lines = ["[PLACA]", *placa_marcador(ui.estado), ""]
    p = ui.estado.portador
    slots = slots_mano(ui.estado)
    lines.append(f"[MANO/{p.nombre} ({len(p.mano)}/{slots})]")
    lines.append("G=def  O=atak")
    for num, carta in filas_mano_fijas(_cartas_ordenadas(p.mano), slots):
        if carta is None:
            lines.append(f" {num}. ---")
        else:
            mark = ">> " if ui._ultima_carta == (p.nombre, carta.value) else "   "
            lines.append(f"{mark}{num}. {carta.value}")
    lines.append("")
    lines.append(f"[ULTIMAS x{ULTIMAS_JUGADAS_VISIBLE}]")
    for i, item in enumerate(
        filas_ultimas_fijas(ui.estado.ultimas_cartas, ULTIMAS_JUGADAS_VISIBLE), start=1
    ):
        if item is None:
            lines.append(f" {i}. ---")
        else:
            j, c = item
            lines.append(f" {i}. {j} -> {c}")
    return "\n".join(lines)


def run_partido(
    ui: _UIBase,
    estado: EstadoPartido,
    config: ConfigSimulacion,
    *,
    intro_fn: Callable,
    correr_fn: Callable,
    final_fn: Callable,
    semilla: int,
    nombres_equipos: tuple,
    comando: str,
) -> None:
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.widgets import Footer, Header, Static

    wait = threading.Event()
    ui_holder: list[_UIBase] = []

    class EspectadorApp(App):
        TITLE = "FOBAL FACU"
        BINDINGS = [
            ("space", "advance", "Avanzar"),
            ("q", "quit", "Salir"),
            ("plus", "faster", "Mas rapido"),
            ("minus", "slower", "Mas lento"),
            ("p", "toggle_pause", "Auto"),
            ("f", "skip_moment", "Salto"),
        ]

        CSS = """
        Screen { background: #0a1612; }
        #log { width: 2fr; height: 1fr; background: #122820; border: solid #2a4a3a; padding: 1; }
        #side { width: 1fr; height: 1fr; background: #122820; border: solid #2a4a3a; padding: 1; }
        """

        def compose(self) -> ComposeResult:
            yield Header(show_clock=False)
            yield Horizontal(
                Static(id="log", markup=False),
                Vertical(Static(id="side", markup=False), id="sidebar"),
            )
            yield Footer()

        def on_mount(self) -> None:
            self.run_worker(self._partido, thread=True, exclusive=True)

        def _refresh(self) -> None:
            u = ui_holder[0]
            self.query_one("#log", Static).update(_plain_log(u))
            self.query_one("#side", Static).update(_plain_side(u))
            pausa = u.pausa_base_ms / 1000
            cmds = barra_comandos(pausa, auto=u.auto_pausa, velocidad=u.velocidad)
            self.sub_title = f"#{semilla} | {cmds[0].strip()}"

        def _partido(self) -> None:
            u = ui_holder[0]

            def redibujar(resaltar: bool = False) -> None:
                self.call_from_thread(self._refresh)

            def esperar(ev: EventoEspectador) -> None:
                if not u._debe_esperar(ev):
                    return
                ms = u._ms_espera(ev)
                wait.clear()
                if ms < 0:
                    wait.wait()
                    return
                if not wait.wait(timeout=ms / 1000.0):
                    return

            u._redibujar = redibujar  # type: ignore[method-assign]
            u._esperar = esperar  # type: ignore[method-assign]
            intro_fn(u, estado, semilla, nombres_equipos, comando)
            if not u.abortar:
                correr_fn(u, estado, config)
            final_fn(u, estado, semilla=semilla, comando=comando)
            self.call_from_thread(self.exit)

        def action_advance(self) -> None:
            wait.set()

        def action_quit(self) -> None:
            u = ui_holder[0]
            u.abortar = True
            u.estado.abortar = True
            wait.set()
            self.exit()

        def action_faster(self) -> None:
            ui_holder[0]._ajustar_velocidad(1)
            self._refresh()

        def action_slower(self) -> None:
            ui_holder[0]._ajustar_velocidad(-1)
            self._refresh()

        def action_toggle_pause(self) -> None:
            u = ui_holder[0]
            u.auto_pausa = not u.auto_pausa
            self._refresh()

        def action_skip_moment(self) -> None:
            ui_holder[0]._fast_forward = True
            wait.set()

    ui_holder.append(ui)
    EspectadorApp().run()
