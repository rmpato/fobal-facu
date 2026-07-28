"""Entrada de teclado compartida para backends del espectador."""

from __future__ import annotations

import sys


def leer_tecla(timeout_sec: float | None) -> str | None:
    """
    Lee una tecla en modo cbreak.
    None = timeout; str = tecla; lanza si no hay TTY utilizable.
    """
    if not sys.stdin.isatty():
        if timeout_sec is not None and timeout_sec > 0:
            import time

            time.sleep(timeout_sec)
        return None
    import select
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        r, _, _ = select.select([sys.stdin], [], [], timeout_sec)
        if not r:
            return None
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
