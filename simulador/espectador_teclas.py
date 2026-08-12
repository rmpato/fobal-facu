"""Entrada de teclado compartida para backends del espectador."""

from __future__ import annotations

import sys


def leer_tecla(timeout_sec: float | None) -> str | None:
    """
    Lee una tecla sin esperar el Enter.
    None = paso el tiempo sin que se apretara nada; str = tecla apretada.
    """
    if not sys.stdin.isatty():
        if timeout_sec is not None and timeout_sec > 0:
            import time

            time.sleep(timeout_sec)
        return None
    if sys.platform == "win32":
        return _leer_tecla_windows(timeout_sec)
    return _leer_tecla_unix(timeout_sec)


def _leer_tecla_unix(timeout_sec: float | None) -> str | None:
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


def _leer_tecla_windows(timeout_sec: float | None) -> str | None:
    """En Windows no hay select() sobre la consola: se pregunta cada tanto."""
    import time

    import msvcrt

    limite = None if timeout_sec is None else time.monotonic() + timeout_sec
    while limite is None or time.monotonic() < limite:
        if msvcrt.kbhit():
            tecla = msvcrt.getwch()
            if tecla in ("\x00", "\xe0"):  # teclas especiales: llegan de a dos
                msvcrt.getwch()
                continue
            return tecla
        time.sleep(0.02)
    return None
