"""Seleccion de backend de terminal para modo espectador."""

from __future__ import annotations

import os
import sys

UI_CHOICES = ("auto", "textual", "rich", "curses", "simple")


def tty_disponible() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty() and "dumb" not in os.environ.get(
        "TERM", ""
    )


def rich_disponible() -> bool:
    from simulador.espectador_rich import disponible

    return disponible()


def textual_disponible() -> bool:
    from simulador.espectador_textual import disponible

    return disponible()


def resolver_ui(preferencia: str = "auto") -> str:
    pref = preferencia if preferencia in UI_CHOICES else "auto"
    if pref != "auto":
        return pref
    if tty_disponible():
        if textual_disponible():
            return "textual"
        if rich_disponible():
            return "rich"
        return "curses"
    if rich_disponible():
        return "rich"
    return "simple"


def validar_ui(elegido: str) -> str:
    if elegido == "textual" and not textual_disponible():
        raise SystemExit("Textual no instalado. Prueba: pip install textual")
    if elegido == "rich" and not rich_disponible():
        raise SystemExit("Rich no instalado. Prueba: pip install rich")
    if elegido == "curses" and not tty_disponible():
        raise SystemExit("Curses requiere una terminal interactiva.")
    return elegido
