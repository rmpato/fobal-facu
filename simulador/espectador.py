"""Modo espectador: un partido en terminal con paneles y pausa interactiva."""

from __future__ import annotations

import random
import sys
import textwrap
from pathlib import Path

try:  # curses no viene con Python en Windows
    import curses
except ImportError:  # pragma: no cover - depende del sistema
    curses = None

from simulador.config import ConfigSimulacion
from simulador.cartas import Carta, carta_por_nombre, rol_carta
from simulador.modelo import EstadoPartido
from simulador.motor import crear_partido, formatear_marcador, jugar_partido
from simulador.espectador_ui import (
    H_BL,
    H_BR,
    H_H,
    H_TL,
    H_TR,
    H_V,
    L_BL,
    L_BR,
    L_H,
    L_TL,
    L_TR,
    L_V,
    banner_titulo,
    barra_comandos,
    box_pesado,
    filas_mano_fijas,
    filas_ultimas_fijas,
    formatear_linea_log,
    intro_partido,
    pantalla_final,
    placa_marcador,
    slots_mano,
    ULTIMAS_JUGADAS_VISIBLE,
)
from simulador.ia import describir_ia_partido
from simulador.eventos_espectador import (
    VELOCIDADES,
    EventoEspectador,
    clasificar_evento,
    debe_pausar,
    pausa_para_evento,
)
from simulador.grabar_espectador import escribir_grabacion, exportar_html_replay

NOMBRES_DEFAULT = ["Facu", "Pato", "Manu", "Colo", "Ostu", "Joaco"]

# Colores de jugador: solo foreground brillante, sin fondo (evita bloques negros).
# Los valores son los mismos que define curses; se escriben acá para que el
# modulo se pueda importar aunque curses no exista (Windows).
_PALETA_FG = [6, 2, 3, 5, 1, 7]  # cyan, verde, amarillo, magenta, rojo, blanco

_ANSI_NOMBRE = [
    "\033[1;96m",  # bright cyan
    "\033[1;92m",  # bright green
    "\033[1;93m",  # bright yellow
    "\033[1;95m",  # bright magenta
    "\033[1;91m",  # bright red
    "\033[1;97m",  # bright white
]
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"

SIDEBAR_ANCHO = 44
FOOTER_FILAS = 4
HEADER_FILAS = 3

# Pares curses reservados (jugadores usan 1–6)
PAIR_CARTA_OFENSIVA = 20
PAIR_CARTA_DEFENSIVA = 21
PAIR_CARTA_NEUTRAL = 22
PAIR_UI_TITULO = 23
PAIR_UI_GOL = 24
PAIR_UI_DIM = 25

_ANSI_OFENSIVA = "\033[33m"  # amarillo (16 colores, mas compatible)
_ANSI_DEFENSIVA = "\033[32m"  # verde
_ANSI_NEUTRAL = "\033[37m"
_ANSI_CYAN = "\033[36m"
_ANSI_DORADO = "\033[33m"


def asignar_equipos(
    nombres: list[str],
    jugadores_por_equipo: int,
    *,
    equipo1: list[str] | None = None,
    equipo2: list[str] | None = None,
) -> tuple[list[str], list[str]]:
    if equipo1 is not None and equipo2 is not None:
        if len(equipo1) != jugadores_por_equipo or len(equipo2) != jugadores_por_equipo:
            raise ValueError(
                f"Cada equipo necesita {jugadores_por_equipo} jugadores "
                f"(recibidos {len(equipo1)} y {len(equipo2)})"
            )
        usados = set(equipo1) | set(equipo2)
        if len(usados) != jugadores_por_equipo * 2:
            raise ValueError("Los equipos no pueden compartir jugadores")
        return equipo1[:], equipo2[:]
    if len(nombres) != jugadores_por_equipo * 2:
        raise ValueError(
            f"Se necesitan {jugadores_por_equipo * 2} nombres "
            f"(recibidos {len(nombres)})"
        )
    barajados = nombres[:]
    random.shuffle(barajados)
    return barajados[:jugadores_por_equipo], barajados[jugadores_por_equipo:]


def _colorear_nombres(texto: str, colores: dict[str, int], usar_ansi: bool) -> str:
    if not colores or not usar_ansi:
        return texto
    if texto and texto[0] in "+|-=":
        return texto
    out = texto
    for nombre in sorted(colores.keys(), key=len, reverse=True):
        idx = colores[nombre] % len(_ANSI_NOMBRE)
        marcado = f"{_ANSI_NOMBRE[idx]}{nombre}{_RESET}" if usar_ansi else nombre
        out = out.replace(nombre, marcado)
    return out


def _partir_texto(texto: str, ancho: int) -> list[str]:
    if ancho < 4:
        return [texto[: max(0, ancho)]]
    return textwrap.wrap(texto, width=ancho) or [""]


def _init_colores_cartas() -> None:
    curses.init_pair(PAIR_CARTA_DEFENSIVA, curses.COLOR_GREEN, -1)
    curses.init_pair(PAIR_CARTA_NEUTRAL, curses.COLOR_WHITE, -1)
    curses.init_pair(PAIR_CARTA_OFENSIVA, curses.COLOR_YELLOW, -1)
    curses.init_pair(PAIR_UI_TITULO, curses.COLOR_CYAN, -1)
    curses.init_pair(PAIR_UI_GOL, curses.COLOR_YELLOW, -1)
    curses.init_pair(PAIR_UI_DIM, curses.COLOR_WHITE, -1)


def _par_carta(rol: str) -> int:
    if rol == "ofensiva":
        return PAIR_CARTA_OFENSIVA
    if rol == "defensiva":
        return PAIR_CARTA_DEFENSIVA
    return PAIR_CARTA_NEUTRAL


def _ansi_carta(rol: str) -> str:
    if rol == "ofensiva":
        return _ANSI_OFENSIVA
    if rol == "defensiva":
        return _ANSI_DEFENSIVA
    return _ANSI_NEUTRAL


def _formatear_carta_ansi(carta: Carta) -> str:
    return f"{_ansi_carta(rol_carta(carta))}{carta.value}{_RESET}"


def _formatear_nombre_carta_ansi(nombre_carta: str) -> str:
    carta = carta_por_nombre(nombre_carta)
    if carta is None:
        return nombre_carta
    return _formatear_carta_ansi(carta)


def _cartas_ordenadas(mano: list[Carta]) -> list[Carta]:
    return sorted(mano, key=lambda c: c.value)


def _lineas_cartas_envueltas(cartas: list[Carta], ancho: int) -> list[list[Carta]]:
    """Agrupa cartas en líneas que entren en `ancho` caracteres (sin contar color)."""
    if not cartas:
        return [[]]
    lineas: list[list[Carta]] = [[]]
    largo = 0
    for carta in cartas:
        extra = len(carta.value) + (2 if lineas[-1] else 0)
        if lineas[-1] and largo + extra > ancho:
            lineas.append([carta])
            largo = len(carta.value)
        else:
            lineas[-1].append(carta)
            largo += extra
    return lineas


class _Grabacion:
    def __init__(
        self,
        path: Path | None,
        *,
        semilla: int,
        reglamento: str,
        equipos: tuple[list[str], list[str]],
        exportar_html: bool,
    ) -> None:
        self.path = path
        self.semilla = semilla
        self.reglamento = reglamento
        self.equipos = equipos
        self.exportar_html = exportar_html
        self.eventos: list[dict] = []
        self.comando = ""

    def registrar_evento(self, ev: EventoEspectador) -> None:
        self.eventos.append(ev.to_dict())

    def set_comando(self, comando: str) -> None:
        self.comando = comando

    def finalizar(self, estado: EstadoPartido) -> Path | None:
        if self.path is None:
            return None
        datos = {
            "v": 1,
            "semilla": self.semilla,
            "reglamento": self.reglamento,
            "equipos": list(self.equipos),
            "comando": self.comando,
            "marcador_final": list(estado.marcador.goles),
            "turnos": estado.turnos,
            "definido_por_penales": estado.definido_por_penales,
            "eventos": self.eventos,
        }
        escribir_grabacion(self.path, datos)
        html_path = None
        if self.exportar_html:
            html_path = exportar_html_replay(self.path, datos)
        return html_path


class _Transcript:
    def __init__(self, path: Path | None) -> None:
        self.path = path

    def iniciar(self) -> None:
        if self.path:
            self.path.write_text("", encoding="utf-8")

    def escribir(self, linea: str) -> None:
        if not linea or self.path is None:
            return
        with self.path.open("a", encoding="utf-8") as f:
            f.write(linea + "\n")


class _UIBase:
    def __init__(
        self,
        estado: EstadoPartido,
        *,
        semilla: int,
        pausa_seg: float,
        comando_repetir: str,
        transcript: _Transcript,
        grabacion: _Grabacion | None,
        colores: dict[str, int],
        velocidad: str = "normal",
    ) -> None:
        self.estado = estado
        self.semilla = semilla
        self.pausa_base_ms = max(0, int(pausa_seg * 1000))
        self.velocidad = velocidad if velocidad in VELOCIDADES else "normal"
        self.auto_pausa = True
        self.comando_repetir = comando_repetir
        self.transcript = transcript
        self.grabacion = grabacion
        self.colores = colores
        self.log: list[str] = []
        self.abortar = False
        self._resaltar_score = False
        self.log_scroll = 0
        self._ultimo_log_idx = -1
        self._turno_actual: int | None = None
        self._banner_gol: str | None = None
        self._fast_forward = False
        self._ultima_carta: tuple[str, str] | None = None

    def _separar_antes(self, msg: str) -> bool:
        if not self.log or self.log[-1] == "":
            return False
        return msg.startswith(
            ("T", "** GOL", "Fin", ">>", "Empate", "---", "===", "Partido detenido", "[FIN]")
        )

    def _ventana_log(self, max_lines: int) -> list[tuple[int, str]]:
        """Lineas visibles con indice global en el log completo."""
        if not self.log:
            return []
        if self.log_scroll <= 0:
            slice_log = self.log[-max_lines:]
            offset = max(0, len(self.log) - len(slice_log))
            return [(offset + i, ln) for i, ln in enumerate(slice_log)]
        end = max(0, len(self.log) - self.log_scroll)
        start = max(0, end - max_lines)
        return [(i, self.log[i]) for i in range(start, end)]

    def _registrar_evento(self, msg: str) -> EventoEspectador:
        ev = clasificar_evento(msg, turno=self._turno_actual)
        if ev.tipo == "turno" and ev.turno is not None:
            self._turno_actual = ev.turno
        if ev.tipo == "gol":
            self._banner_gol = msg.strip().lstrip("*").strip()
        elif ev.tipo == "turno":
            self._banner_gol = None
        if self.estado.ultimas_cartas:
            self._ultima_carta = self.estado.ultimas_cartas[-1]
        if self.grabacion:
            self.grabacion.registrar_evento(ev)
        return ev

    def _registrar(self, linea: str, *, resaltar: bool = False) -> None:
        if self._separar_antes(linea):
            self.log.append("")
        self.log.append(linea)
        self._ultimo_log_idx = len(self.log) - 1
        if len(self.log) > 600:
            trimmed = len(self.log) - 500
            self.log = self.log[-500:]
            self._ultimo_log_idx = max(0, self._ultimo_log_idx - trimmed)
            self.log_scroll = max(0, self.log_scroll - trimmed)
        self.transcript.escribir(linea)
        self._registrar_evento(linea)
        self._resaltar_score = resaltar or linea.startswith("** GOL")
        self._redibujar(resaltar=self._resaltar_score)

    def _contenido_marcador(self) -> list[str]:
        return placa_marcador(self.estado)

    def _contenido_mano(self) -> list[str]:
        """Texto plano (sin color) — preferir paneles coloreados en pantalla."""
        p = self.estado.portador
        cartas = ", ".join(c.value for c in _cartas_ordenadas(p.mano))
        if not cartas:
            cartas = "(sin cartas)"
        return [
            f"{len(p.mano)} cartas en mano:",
            "G=def | O=atak",
            cartas,
        ]

    def _mano_lineas_ansi(self) -> list[str]:
        p = self.estado.portador
        slots = slots_mano(self.estado)
        filas = filas_mano_fijas(_cartas_ordenadas(p.mano), slots)
        lineas = [f"G=def  O=atak  ({len(p.mano)}/{slots} cartas)"]
        for num, carta in filas:
            if carta is None:
                lineas.append(f" {num}. ---")
            else:
                lineas.append(f" {num}. {_formatear_carta_ansi(carta)}")
        return lineas

    def _ultimas_lineas_ansi(self) -> list[str]:
        filas = filas_ultimas_fijas(self.estado.ultimas_cartas, ULTIMAS_JUGADAS_VISIBLE)
        lineas: list[str] = []
        for i, item in enumerate(filas, start=1):
            if item is None:
                lineas.append(f" {i}. ---")
            else:
                jugador, carta = item
                nj = _colorear_nombres(jugador, self.colores, True)
                nc = _formatear_nombre_carta_ansi(carta)
                lineas.append(f" {i}. {nj} -> {nc}")
        return lineas

    def _esperar(self, ev: EventoEspectador) -> None:
        raise NotImplementedError

    def _redibujar(self, resaltar: bool = False) -> None:
        raise NotImplementedError

    def esperar_tecla(self) -> None:
        """Pausa interactiva al final del partido."""
        ev = EventoEspectador(texto="", tier="moment", tipo="fin")
        self._esperar(ev)

    def _ajustar_velocidad(self, delta: int) -> None:
        orden = list(VELOCIDADES)
        idx = orden.index(self.velocidad) if self.velocidad in orden else 1
        idx = max(0, min(len(orden) - 1, idx + delta))
        self.velocidad = orden[idx]

    def _debe_esperar(self, ev: EventoEspectador) -> bool:
        if self._fast_forward:
            if ev.tier == "moment":
                self._fast_forward = False
                return True
            return False
        return debe_pausar(
            ev,
            velocidad=self.velocidad,
            auto_pausa=self.auto_pausa,
            pausa_base_ms=self.pausa_base_ms,
        )

    def _ms_espera(self, ev: EventoEspectador) -> int:
        if not self.auto_pausa:
            return -1
        return pausa_para_evento(ev, self.pausa_base_ms, velocidad=self.velocidad)

    def bloque(self, lineas: list[str], *, resaltar: bool = False) -> None:
        for linea in lineas:
            if self.abortar or self.estado.abortar:
                return
            self._registrar(linea, resaltar=resaltar)
            ev = clasificar_evento(linea, turno=self._turno_actual)
            if self._debe_esperar(ev):
                self._esperar(ev)
            if self.abortar or self.estado.abortar:
                return

    def evento(self, msg: str) -> None:
        if self.abortar or self.estado.abortar:
            return
        resaltar = msg.startswith("** GOL") or msg.startswith("Fin")
        self._registrar(msg, resaltar=resaltar)
        ev = clasificar_evento(msg, turno=self._turno_actual)
        if self._debe_esperar(ev):
            self._esperar(ev)

    def on_reposicion(self) -> None:
        """Sidebar se actualiza en cada redibujado; el log ya registra la reposición."""
        self._redibujar()


class PantallaEspectador(_UIBase):
    def __init__(self, stdscr, estado: EstadoPartido, **kwargs) -> None:
        super().__init__(estado, **kwargs)
        self.stdscr = stdscr
        self.pares: dict[str, int] = {}
        self.log_win = None
        self.side_win = None
        self.foot_win = None
        self._setup_curses()

    def _setup_curses(self) -> None:
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        self.stdscr.keypad(True)
        for i, fg in enumerate(_PALETA_FG, start=1):
            curses.init_pair(i, fg, -1)
        _init_colores_cartas()
        for nombre, idx in self.colores.items():
            self.pares[nombre] = (idx % len(_PALETA_FG)) + 1
        self._crear_ventanas()

    def _crear_ventanas(self) -> None:
        h, w = self.stdscr.getmaxyx()
        sidebar_w = min(SIDEBAR_ANCHO, max(26, w // 3))
        log_w = max(24, w - sidebar_w)
        content_h = max(8, h - HEADER_FILAS - FOOTER_FILAS)
        self.log_win = curses.newwin(content_h, log_w, HEADER_FILAS, 0)
        self.side_win = curses.newwin(content_h, sidebar_w, HEADER_FILAS, log_w)
        self.foot_win = curses.newwin(FOOTER_FILAS, w, h - FOOTER_FILAS, 0)
        self.log_win.keypad(True)
        self.side_win.keypad(True)
        self.foot_win.keypad(True)

    def _safe_addstr(self, win, y: int, x: int, texto: str, attr: int = 0) -> None:
        try:
            h, w = win.getmaxyx()
            if y < 0 or y >= h or x >= w - 1:
                return
            win.addstr(y, x, texto[: max(0, w - x - 1)], attr)
        except curses.error:
            pass

    def _colorear_en(self, win, y: int, x: int, texto: str, attr: int = 0) -> None:
        nombres = sorted(self.colores.keys(), key=len, reverse=True)
        pos = 0
        while pos < len(texto):
            match = next((n for n in nombres if texto.startswith(n, pos)), None)
            if match:
                par = self.pares.get(match, 0)
                a = curses.color_pair(par) if par else attr
                self._safe_addstr(win, y, x, match, a)
                x += len(match)
                pos += len(match)
            else:
                self._safe_addstr(win, y, x, texto[pos], attr)
                x += 1
                pos += 1

    def _dibujar_caja(self, win, y: int, lineas: list[str]) -> int:
        for i, linea in enumerate(lineas):
            self._safe_addstr(win, y + i, 0, linea[: win.getmaxyx()[1] - 1], curses.A_NORMAL)
        return y + len(lineas)

    def _dibujar_carta(self, win, y: int, x: int, carta: Carta, sep: str = "") -> int:
        if sep:
            self._safe_addstr(win, y, x, sep, curses.A_DIM)
            x += len(sep)
        rol = rol_carta(carta)
        attr = curses.color_pair(_par_carta(rol))
        self._safe_addstr(win, y, x, carta.value, attr)
        return x + len(carta.value)

    def _dibujar_panel_mano(self, win, y: int, sw: int) -> int:
        inner = max(4, sw - 2)
        portador = self.estado.portador.nombre
        mano = _cartas_ordenadas(self.estado.portador.mano)
        slots = slots_mano(self.estado)
        titulo = f" MANO/{portador} ({len(mano)}/{slots}) "
        if len(titulo) > inner:
            titulo = titulo[:inner]
        top = L_TL + titulo + L_H * max(0, inner - len(titulo)) + L_TR
        self._safe_addstr(win, y, 0, top[: sw - 1])
        y += 1
        self._safe_addstr(
            win, y, 0, L_V + " G=def  O=atak".ljust(inner)[:inner] + L_V, curses.A_DIM
        )
        y += 1
        for num, carta in filas_mano_fijas(mano, slots):
            self._safe_addstr(win, y, 0, L_V, curses.A_DIM)
            pref = f" {num}. "
            self._safe_addstr(win, y, 2, pref, curses.A_DIM)
            if carta is None:
                self._safe_addstr(win, y, 2 + len(pref), "---", curses.A_DIM)
            else:
                resaltar_carta = (
                    self._ultima_carta is not None
                    and self._ultima_carta[0] == portador
                    and self._ultima_carta[1] == carta.value
                )
                attr_extra = curses.A_REVERSE if resaltar_carta else 0
                rol = rol_carta(carta)
                attr = curses.color_pair(_par_carta(rol)) | attr_extra
                self._safe_addstr(win, y, 2 + len(pref), carta.value, attr)
            y += 1
        self._safe_addstr(win, y, 0, (L_BL + L_H * inner + L_BR)[: sw - 1])
        return y + 1

    def _dibujar_panel_ultimas(self, win, y: int, sw: int) -> int:
        inner = max(4, sw - 2)
        titulo = f" ULTIMAS x{ULTIMAS_JUGADAS_VISIBLE} "
        if len(titulo) > inner:
            titulo = titulo[:inner]
        top = L_TL + titulo + L_H * max(0, inner - len(titulo)) + L_TR
        self._safe_addstr(win, y, 0, top[: sw - 1])
        y += 1
        for i, item in enumerate(
            filas_ultimas_fijas(self.estado.ultimas_cartas, ULTIMAS_JUGADAS_VISIBLE), start=1
        ):
            self._safe_addstr(win, y, 0, L_V, curses.A_DIM)
            self._safe_addstr(win, y, 2, f"{i}. ", curses.A_DIM)
            if item is None:
                self._safe_addstr(win, y, 5, "---", curses.A_DIM)
            else:
                jugador, carta_nombre = item
                self._colorear_en(win, y, 5, jugador, curses.A_NORMAL)
                self._safe_addstr(win, y, 5 + len(jugador), " -> ", curses.A_DIM)
                carta = carta_por_nombre(carta_nombre)
                if carta:
                    self._dibujar_carta(win, y, 5 + len(jugador) + 4, carta)
                else:
                    self._safe_addstr(win, y, 5 + len(jugador) + 4, carta_nombre)
            y += 1
        self._safe_addstr(win, y, 0, (L_BL + L_H * inner + L_BR)[: sw - 1])
        return y + 1

    def _dibujar_panel_guia(self, win, y: int, sw: int) -> int:
        inner = max(4, sw - 2)
        titulo = " ANTICIPO IA "
        if len(titulo) > inner:
            titulo = titulo[:inner]
        top = L_TL + titulo + L_H * max(0, inner - len(titulo)) + L_TR
        self._safe_addstr(win, y, 0, top[: sw - 1])
        y += 1
        for ln in panel_guia(self.estado, ancho=inner):
            self._safe_addstr(win, y, 0, L_V, curses.A_DIM)
            contenido = ln[:inner].ljust(inner)
            if ln.endswith("(bola):"):
                nombre = ln[: -len("(bola):")].strip()
                self._colorear_en(win, y, 2, nombre, curses.A_BOLD)
                self._safe_addstr(
                    win, y, 2 + len(nombre), " (bola):"[: inner - len(nombre)], curses.A_NORMAL
                )
            elif ln.startswith("Reglamento "):
                self._safe_addstr(win, y, 2, contenido, curses.A_BOLD)
            elif ln.startswith("IA: "):
                self._safe_addstr(win, y, 2, contenido, curses.color_pair(PAIR_UI_TITULO))
            elif ln.startswith(("E1: ", "E2: ")):
                self._safe_addstr(win, y, 2, contenido, curses.color_pair(PAIR_UI_TITULO))
            elif ln.startswith(" · "):
                self._safe_addstr(win, y, 2, contenido, curses.color_pair(PAIR_UI_TITULO))
            elif ln.startswith((" si ", " def")):
                self._safe_addstr(win, y, 2, contenido, curses.color_pair(PAIR_UI_DIM))
            elif ln == "---":
                self._safe_addstr(win, y, 2, L_H * min(inner, 28), curses.A_DIM)
            else:
                self._safe_addstr(win, y, 2, contenido, curses.A_NORMAL)
            self._safe_addstr(win, y, len(L_V) + inner, L_V, curses.A_DIM)
            y += 1
        self._safe_addstr(win, y, 0, (L_BL + L_H * inner + L_BR)[: sw - 1])
        return y + 1

    def _attr_linea_log(self, linea_fmt: str) -> int:
        if linea_fmt.startswith("**") or linea_fmt.startswith("[FIN]"):
            return curses.color_pair(PAIR_UI_GOL) | curses.A_BOLD
        if linea_fmt.startswith(">>"):
            return curses.color_pair(PAIR_UI_TITULO) | curses.A_BOLD
        if linea_fmt.startswith("====") or linea_fmt.startswith(">> Cambio"):
            return curses.A_BOLD
        return curses.color_pair(PAIR_UI_DIM)

    def _redibujar(self, resaltar: bool = False) -> None:
        self._crear_ventanas()
        h, w = self.stdscr.getmaxyx()
        reg = self.estado.reglamento
        reg_id = reg.id if reg else self.estado.reglamento_id

        self.stdscr.erase()
        for i, ln in enumerate(banner_titulo(reg_id, self.semilla, w)):
            if i >= HEADER_FILAS:
                break
            attr = curses.color_pair(PAIR_UI_TITULO) | curses.A_BOLD
            if resaltar and i == 0:
                attr |= curses.A_BLINK
            self._safe_addstr(self.stdscr, i, 0, ln[: w - 1], attr)

        # Panel lateral (HUD)
        self.side_win.erase()
        sw = self.side_win.getmaxyx()[1]
        y = 0
        for ln in box_pesado("PLACA", placa_marcador(self.estado), sw):
            if len(ln) >= 3 and ln[0] == H_V and ln[1] == " ":
                contenido = ln[1:-1]
                self._safe_addstr(self.side_win, y, 0, H_V, curses.A_NORMAL)
                self._colorear_en(self.side_win, y, 1, contenido.rstrip(), curses.A_NORMAL)
                self._safe_addstr(self.side_win, y, len(ln) - 1, H_V, curses.A_NORMAL)
            else:
                self._safe_addstr(self.side_win, y, 0, ln[: sw - 1])
            y += 1
        y += 1
        y = self._dibujar_panel_mano(self.side_win, y, sw)
        y += 1
        y = self._dibujar_panel_ultimas(self.side_win, y, sw)
        y += 1
        self._dibujar_panel_guia(self.side_win, y, sw)

        # Feed de acciones (marco + contenido)
        self.log_win.erase()
        lh, lw = self.log_win.getmaxyx()
        inner_w = max(4, lw - 2)
        self._safe_addstr(
            self.log_win, 0, 0,
            L_TL + " RELATO DEL PARTIDO " + L_H * max(0, inner_w - 20) + L_TR,
            curses.color_pair(PAIR_UI_TITULO) | curses.A_BOLD,
        )
        max_lines = max(0, lh - 3)
        start_row = 1
        if self._banner_gol:
            banner = f" ** {self._banner_gol[: max(0, inner_w - 6)]} ** "
            self._safe_addstr(
                self.log_win,
                1,
                0,
                L_V + banner.center(inner_w)[:inner_w] + L_V,
                curses.color_pair(PAIR_UI_GOL) | curses.A_BOLD,
            )
            start_row = 2
            max_lines = max(0, max_lines - 1)
        row = start_row
        for idx, linea in self._ventana_log(max_lines):
            if row >= lh - 2:
                break
            if not linea:
                row += 1
                continue
            fmt = formatear_linea_log(linea)
            line_attr = self._attr_linea_log(fmt)
            self._safe_addstr(self.log_win, row, 0, L_V, curses.A_DIM)
            self._colorear_en(self.log_win, row, 1, fmt[: inner_w], line_attr)
            row += 1
        # Relleno lateral del marco
        for r in range(row, lh - 1):
            self._safe_addstr(self.log_win, r, 0, L_V, curses.A_DIM)
        self._safe_addstr(
            self.log_win, lh - 1, 0,
            L_BL + L_H * inner_w + L_BR,
            curses.A_DIM,
        )

        # Barra de comandos
        self.foot_win.erase()
        pausa_show = self.pausa_base_ms / 1000
        cmds = barra_comandos(
            pausa_show,
            auto=self.auto_pausa,
            velocidad=self.velocidad,
        )
        self._safe_addstr(
            self.foot_win, 0, 0,
            H_TL + cmds[0].strip().center(max(0, w - 2))[: w - 2] + H_TR,
            curses.color_pair(PAIR_UI_TITULO),
        )
        scroll_hint = f" scroll:{self.log_scroll}" if self.log_scroll else ""
        self._safe_addstr(
            self.foot_win, 1, 0,
            (cmds[1] + scroll_hint)[: w - 1],
            curses.A_DIM,
        )
        self._safe_addstr(
            self.foot_win, 2, 0,
            f" replay: {self.comando_repetir}"[: w - 1],
            curses.A_DIM,
        )
        self._safe_addstr(self.foot_win, 3, 0, " "[: w - 1], curses.A_DIM)

        self.stdscr.refresh()
        self.log_win.refresh()
        self.side_win.refresh()
        self.foot_win.refresh()

    def _esperar(self, ev: EventoEspectador) -> None:
        win = self.log_win or self.stdscr
        timeout = self._ms_espera(ev)
        win.timeout(timeout if timeout > 0 else -1)
        while True:
            key = win.getch()
            if key in (ord("q"), ord("Q")):
                self.abortar = True
                self.estado.abortar = True
                return
            if key in (ord(" "), ord("\n"), curses.KEY_ENTER, 10):
                return
            if key in (ord("+"), ord("=")):
                self._ajustar_velocidad(1)
                self._redibujar()
                continue
            if key in (ord("-"), ord("_")):
                self._ajustar_velocidad(-1)
                self._redibujar()
                continue
            if key in (ord("p"), ord("P")):
                self.auto_pausa = not self.auto_pausa
                self._redibujar()
                continue
            if key in (ord("f"), ord("F")):
                self._fast_forward = True
                return
            if key == curses.KEY_UP:
                self.log_scroll = min(self.log_scroll + 1, max(0, len(self.log) - 1))
                self._redibujar()
                continue
            if key == curses.KEY_DOWN:
                self.log_scroll = max(0, self.log_scroll - 1)
                self._redibujar()
                continue
            if key == curses.KEY_PPAGE:
                self.log_scroll = min(self.log_scroll + 10, max(0, len(self.log) - 1))
                self._redibujar()
                continue
            if key == curses.KEY_NPAGE:
                self.log_scroll = max(0, self.log_scroll - 10)
                self._redibujar()
                continue
            if timeout > 0 and key == -1:
                return


class PantallaSimple(_UIBase):
    """Fallback sin curses."""

    def _imprimir_banner(self, ancho: int = 72) -> None:
        for ln in banner_titulo(
            self.estado.reglamento.id if self.estado.reglamento else self.estado.reglamento_id,
            self.semilla,
            ancho,
        ):
            print(f"{_ANSI_CYAN}{_BOLD}{ln}{_RESET}")

    def _imprimir_caja(self, titulo: str, lineas: list[str], ancho: int = 44) -> None:
        for ln in box_pesado(titulo, lineas, ancho):
            if ln[0] in "+|=":
                print(ln)
            else:
                print(_colorear_nombres(ln, self.colores, sys.stdout.isatty()))

    def _imprimir_caja_raw(self, titulo: str, lineas: list[str], ancho: int = 40) -> None:
        inner = max(4, ancho - 2)
        t = f" {titulo} "
        print(f"{L_TL}{t}{L_H * max(0, inner - len(t))}{L_TR}")
        for ln in lineas:
            if "\033" in ln:
                print(f"{L_V} {ln} {L_V}")
            else:
                print(f"{L_V} {ln:<{inner}} {L_V}")
        print(f"{L_BL}{L_H * inner}{L_BR}")

    def _redibujar(self, resaltar: bool = False) -> None:
        print("\033[2J\033[H", end="")
        self._imprimir_banner()
        print()

        if self._banner_gol:
            print(f"{_ANSI_DORADO}{_BOLD} ** {self._banner_gol} ** {_RESET}")
        log_vis = self._ventana_log(16)
        ancho_log = 58
        print(f"{_BOLD}{L_TL}{' RELATO DEL PARTIDO '.center(ancho_log - 2, L_H)}{L_TR}{_RESET}")
        for idx, ln in log_vis:
            fmt = formatear_linea_log(ln)
            prefix = f"{_ANSI_DORADO}" if fmt.startswith("**") or fmt.startswith("[FIN]") else ""
            print(
                f"{L_V} {_colorear_nombres(prefix + fmt + _RESET, self.colores, sys.stdout.isatty()):<{ancho_log - 4}} {L_V}"
            )
        print(f"{L_BL}{L_H * (ancho_log - 2)}{L_BR}")
        print()

        sw = 44
        self._imprimir_caja("PLACA", placa_marcador(self.estado), sw)
        print()
        self._imprimir_caja_raw(
            f"MANO/{self.estado.portador.nombre} ({len(self.estado.portador.mano)}/{slots_mano(self.estado)})",
            self._mano_lineas_ansi(),
            sw,
        )
        print()
        self._imprimir_caja_raw(f"ULTIMAS x{ULTIMAS_JUGADAS_VISIBLE}", self._ultimas_lineas_ansi(), sw)
        print()
        self._imprimir_caja("ANTICIPO IA", panel_guia(self.estado, ancho=sw - 4), sw)
        print()

        pausa_show = self.pausa_base_ms / 1000
        for ln in barra_comandos(pausa_show, auto=self.auto_pausa, velocidad=self.velocidad):
            print(f"{_DIM}{ln}{_RESET}")
        print(f"{_DIM}replay: {self.comando_repetir}{_RESET}")

    def _esperar(self, ev: EventoEspectador) -> None:
        if not self._debe_esperar(ev):
            return
        ms = self._ms_espera(ev)
        if not self.auto_pausa:
            ms = -1
        if ms == 0 and self.auto_pausa:
            return
        try:
            import select
            import termios
            import tty

            if not sys.stdin.isatty():
                if ms > 0:
                    import time
                    time.sleep(ms / 1000.0)
                return
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setcbreak(fd)
                timeout = None if ms < 0 else ms / 1000.0
                r, _, _ = select.select([sys.stdin], [], [], timeout)
                if r:
                    ch = sys.stdin.read(1)
                    if ch in ("q", "Q"):
                        self.abortar = True
                        self.estado.abortar = True
                    elif ch in ("+", "="):
                        self._ajustar_velocidad(1)
                    elif ch in ("-", "_"):
                        self._ajustar_velocidad(-1)
                    elif ch in ("p", "P"):
                        self.auto_pausa = not self.auto_pausa
                    elif ch in ("f", "F"):
                        self._fast_forward = True
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except (ImportError, OSError, ValueError):
            import time

            if ms > 0:
                time.sleep(ms / 1000.0)


def _comando_repetir(
    semilla: int,
    reglamento: str,
    jugadores_por_equipo: int,
    ia: str,
    pausa: float,
) -> str:
    return (
        f"python3 -m simulador ver --semilla {semilla} "
        f"--reglamento {reglamento} --jugadores-por-equipo {jugadores_por_equipo} "
        f"--ia {ia} --pausa {pausa:g}"
    )


def preparar_partido(
    config: ConfigSimulacion,
    *,
    semilla: int | None,
    nombres: list[str] | None,
    equipo1: list[str] | None = None,
    equipo2: list[str] | None = None,
) -> tuple[EstadoPartido, int, tuple[list[str], list[str]], dict[str, int]]:
    usada = semilla if semilla is not None else random.randint(0, 999_999)
    random.seed(usada)

    lista = nombres or NOMBRES_DEFAULT
    eq0, eq1 = asignar_equipos(
        lista, config.jugadores_por_equipo, equipo1=equipo1, equipo2=equipo2
    )
    nombres_por_equipo = (eq0, eq1)

    colores: dict[str, int] = {}
    orden_colores = lista if equipo1 is None else eq0 + eq1
    for i, nombre in enumerate(orden_colores):
        colores[nombre] = i % len(_PALETA_FG)

    estado = crear_partido(config, nombres_por_equipo=nombres_por_equipo)
    return estado, usada, nombres_por_equipo, colores


def _mostrar_final(
    ui: _UIBase,
    estado: EstadoPartido,
    *,
    semilla: int,
    comando: str,
) -> None:
    for ln in pantalla_final(
        estado,
        semilla=semilla,
        comando_repetir=comando,
        abortado=bool(estado.abortar or ui.abortar),
    ):
        if ui._separar_antes(ln):
            ui.log.append("")
        ui.log.append(ln)
        ui._ultimo_log_idx = len(ui.log) - 1
        ui.transcript.escribir(ln)
        ui._registrar_evento(ln)
    ui._redibujar(resaltar=True)
    ui.esperar_tecla()


def _intro(
    ui: _UIBase,
    estado: EstadoPartido,
    semilla: int,
    nombres_por_equipo: tuple[list[str], list[str]],
    comando: str,
) -> None:
    reg = estado.reglamento
    total_cartas = sum(reg.mazo.values()) if reg else len(estado.mazo) + len(estado.descarte)
    eq0 = ", ".join(nombres_por_equipo[0])
    eq1 = ", ".join(nombres_por_equipo[1])
    intro = intro_partido(
        semilla,
        reg.id if reg else estado.reglamento_id,
        describir_ia_partido(estado.config) if estado.config else "Táctico",
        f"{estado.jugadores_por_equipo} vs {estado.jugadores_por_equipo}",
        eq0,
        eq1,
        total_cartas,
        reg.mano_inicial if reg else 6,
        estado.portador.nombre,
    )
    ui.bloque(intro)


def _correr_con_ui(ui: _UIBase, estado: EstadoPartido, config: ConfigSimulacion) -> EstadoPartido:
    estado.on_evento = ui.evento
    estado.on_cambio_equipo = ui.on_reposicion
    return jugar_partido(config=config, estado=estado, verbose=False)


def _run_curses(
    stdscr,
    estado: EstadoPartido,
    config: ConfigSimulacion,
    *,
    semilla: int,
    nombres_por_equipo: tuple[list[str], list[str]],
    colores: dict[str, int],
    pausa: float,
    comando: str,
    transcript: _Transcript,
    grabacion: _Grabacion | None,
    velocidad: str,
) -> None:
    ui = PantallaEspectador(
        stdscr,
        estado,
        semilla=semilla,
        pausa_seg=pausa,
        comando_repetir=comando,
        transcript=transcript,
        grabacion=grabacion,
        colores=colores,
        velocidad=velocidad,
    )
    _intro(ui, estado, semilla, nombres_por_equipo, comando)
    if not ui.abortar:
        _correr_con_ui(ui, estado, config)
    _mostrar_final(ui, estado, semilla=semilla, comando=comando)


def _run_rich(
    estado: EstadoPartido,
    config: ConfigSimulacion,
    *,
    semilla: int,
    nombres_por_equipo: tuple[list[str], list[str]],
    colores: dict[str, int],
    pausa: float,
    comando: str,
    transcript: _Transcript,
    grabacion: _Grabacion | None,
    velocidad: str,
) -> None:
    from simulador.espectador_rich import envolver

    ui = _UIBase(
        estado,
        semilla=semilla,
        pausa_seg=pausa,
        comando_repetir=comando,
        transcript=transcript,
        grabacion=grabacion,
        colores=colores,
        velocidad=velocidad,
    )
    pantalla = envolver(ui)
    try:
        _intro(ui, estado, semilla, nombres_por_equipo, comando)
        if not ui.abortar:
            _correr_con_ui(ui, estado, config)
        _mostrar_final(ui, estado, semilla=semilla, comando=comando)
    finally:
        pantalla.close()


def _run_textual(
    estado: EstadoPartido,
    config: ConfigSimulacion,
    *,
    semilla: int,
    nombres_por_equipo: tuple[list[str], list[str]],
    colores: dict[str, int],
    pausa: float,
    comando: str,
    transcript: _Transcript,
    grabacion: _Grabacion | None,
    velocidad: str,
) -> None:
    from simulador.espectador_textual import run_partido

    ui = _UIBase(
        estado,
        semilla=semilla,
        pausa_seg=pausa,
        comando_repetir=comando,
        transcript=transcript,
        grabacion=grabacion,
        colores=colores,
        velocidad=velocidad,
    )
    run_partido(
        ui,
        estado,
        config,
        intro_fn=_intro,
        correr_fn=_correr_con_ui,
        final_fn=_mostrar_final,
        semilla=semilla,
        nombres_equipos=nombres_por_equipo,
        comando=comando,
    )


def ver_partido(
    config: ConfigSimulacion,
    *,
    semilla: int | None = None,
    nombres: list[str] | None = None,
    equipo1: list[str] | None = None,
    equipo2: list[str] | None = None,
    pausa: float = 5.0,
    grabar: Path | None = None,
    sin_pausa: bool = False,
    velocidad: str = "normal",
    exportar_html: bool = False,
    ui: str = "auto",
) -> EstadoPartido:
    from simulador.espectador_backend import resolver_ui, validar_ui

    backend = validar_ui(resolver_ui(ui))
    estado, semilla_usada, nombres_equipos, colores = preparar_partido(
        config,
        semilla=semilla,
        nombres=nombres,
        equipo1=equipo1,
        equipo2=equipo2,
    )
    velocidad_efectiva = "turbo" if sin_pausa else velocidad
    pausa_ui = 0.0 if sin_pausa else pausa
    comando = _comando_repetir(
        semilla_usada,
        config.reglamento,
        config.jugadores_por_equipo,
        config.ia,
        pausa,
    )

    grabacion: _Grabacion | None = None
    transcript_path: Path | None = grabar
    if grabar is not None and grabar.suffix.lower() == ".json":
        grabacion = _Grabacion(
            grabar,
            semilla=semilla_usada,
            reglamento=config.reglamento,
            equipos=nombres_equipos,
            exportar_html=exportar_html,
        )
        grabacion.set_comando(comando)
        transcript_path = None

    transcript = _Transcript(transcript_path)
    transcript.iniciar()
    transcript.escribir(comando)

    kwargs_ui = dict(
        semilla=semilla_usada,
        nombres_por_equipo=nombres_equipos,
        colores=colores,
        pausa=pausa_ui,
        comando=comando,
        transcript=transcript,
        grabacion=grabacion,
        velocidad=velocidad_efectiva,
    )

    if backend == "curses":
        curses.wrapper(_run_curses, estado, config, **kwargs_ui)
    elif backend == "rich":
        _run_rich(estado, config, **kwargs_ui)
    elif backend == "textual":
        _run_textual(estado, config, **kwargs_ui)
    else:
        ui_obj = PantallaSimple(
            estado,
            semilla=semilla_usada,
            pausa_seg=pausa_ui,
            comando_repetir=comando,
            transcript=transcript,
            grabacion=grabacion,
            colores=colores,
            velocidad=velocidad_efectiva,
        )
        _intro(ui_obj, estado, semilla_usada, nombres_equipos, comando)
        if not ui_obj.abortar:
            _correr_con_ui(ui_obj, estado, config)
        _mostrar_final(ui_obj, estado, semilla=semilla_usada, comando=comando)

    html_path = grabacion.finalizar(estado) if grabacion else None
    if grabar and grabar.suffix.lower() != ".json":
        print(f"\nTranscripción guardada en {grabar}")
    if grabacion:
        print(f"\nGrabación JSON: {grabacion.path}")
    if html_path:
        print(f"Replay HTML: {html_path}")

    return estado
