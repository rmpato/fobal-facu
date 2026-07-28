"""Elementos visuales ASCII para modo espectador (compatible con cualquier terminal)."""

from __future__ import annotations

from simulador.modelo import EstadoPartido

# Solo ASCII 7-bit: evita "P" y basura por UTF-8 / fuentes rotas
H_TL, H_TR, H_BL, H_BR, H_H, H_V = "+", "+", "+", "+", "=", "|"
L_TL, L_TR, L_BL, L_BR, L_H, L_V = "+", "+", "+", "+", "-", "|"

_BOX_CHARS = set("+-=| ")

ULTIMAS_JUGADAS_VISIBLE = 4
MANO_VISIBLE_DEFAULT = 6


def banner_titulo(reg_id: str, semilla: int, ancho: int) -> list[str]:
    ancho = max(50, ancho)
    inner = ancho - 2
    titulo = f" FOBAL FACU  |  {reg_id.upper()}  |  LIVE  |  #{semilla} "
    if len(titulo) > inner:
        titulo = titulo[:inner]
    pad = max(0, inner - len(titulo))
    linea = H_TL + H_H + titulo + H_H * pad + H_TR
    sub = " Simulador de cartas - modo espectador "
    sub = sub.center(inner)[:inner]
    return [linea, H_V + sub + H_V, H_BL + H_H * inner + H_BR]


def box_pesado(titulo: str, lineas: list[str], ancho: int) -> list[str]:
    ancho = max(12, ancho)
    inner = ancho - 2
    t = f" {titulo} "
    if len(t) > inner:
        t = t[:inner]
    top = H_TL + H_H + t + H_H * max(0, inner - len(t)) + H_TR
    out = [top]
    for ln in lineas:
        out.append(H_V + ln[:inner].ljust(inner) + H_V)
    out.append(H_BL + H_H * inner + H_BR)
    return out


def box_ligero(titulo: str, lineas: list[str], ancho: int) -> list[str]:
    ancho = max(12, ancho)
    inner = ancho - 2
    t = f" {titulo} "
    if len(t) > inner:
        t = t[:inner]
    top = L_TL + t + L_H * max(0, inner - len(t)) + L_TR
    out = [top]
    for ln in lineas:
        out.append(L_V + ln[:inner].ljust(inner) + L_V)
    out.append(L_BL + L_H * inner + L_BR)
    return out


def _nombres_equipo(estado: EstadoPartido, equipo: int) -> str:
    return ", ".join(j.nombre for j in estado.jugadores_equipo(equipo))


def _nombre_jugador(estado: EstadoPartido, jid: int | None) -> str | None:
    if jid is None:
        return None
    for j in estado.jugadores:
        if j.id == jid:
            return j.nombre
    return None


def _estado_trampas(estado: EstadoPartido) -> str:
    partes: list[str] = []
    eq_def = estado.equipo_defensivo
    if estado.offside_activo.get(eq_def):
        partes.append("offside activo")
    marca_id = estado.marca_sobre.get(eq_def)
    if marca_id is not None:
        nombre = _nombre_jugador(estado, marca_id)
        if nombre:
            partes.append(f"marca:{nombre}")
    return " | ".join(partes) if partes else "ninguna"


def placa_marcador(estado: EstadoPartido) -> list[str]:
    g0, g1 = estado.marcador.goles
    eq0 = _nombres_equipo(estado, 0)
    eq1 = _nombres_equipo(estado, 1)
    pelota = estado.portador.equipo
    marca0 = "*" if pelota == 0 else " "
    marca1 = "*" if pelota == 1 else " "
    meta = estado.marcador.goles_para_ganar
    defensores = ", ".join(j.nombre for j in estado.defensores())
    mazo = len(estado.mazo)
    descarte = len(estado.descarte)
    # Una linea por equipo; * = tiene la pelota (sin corchetes que rompen en algunas fuentes)
    return [
        f" {marca0} E1 {eq0[:24]:<24} {g0}",
        f" {marca1} E2 {eq1[:24]:<24} {g1}",
        f" meta {meta}   turno {estado.turnos:>3}",
        f" bola: {estado.portador.nombre}",
        f" def: {defensores[:28]}",
        f" pases: {estado.pases_en_jugada}",
        f" trampa: {_estado_trampas(estado)[:28]}",
        f" mazo: {mazo}  descarte: {descarte}",
    ]


def slots_mano(estado: EstadoPartido) -> int:
    if estado.reglamento:
        return estado.reglamento.mano_inicial
    return MANO_VISIBLE_DEFAULT


def filas_mano_fijas(cartas: list, slots: int) -> list[tuple[int, object | None]]:
    """Lista de (numero, carta|None) con tamano fijo."""
    ordenadas = sorted(cartas, key=lambda c: c.value)
    filas: list[tuple[int, object | None]] = []
    for i in range(slots):
        carta = ordenadas[i] if i < len(ordenadas) else None
        filas.append((i + 1, carta))
    return filas


def filas_ultimas_fijas(
    ultimas: list[tuple[str, str]], slots: int = ULTIMAS_JUGADAS_VISIBLE
) -> list[tuple[str, str] | None]:
    recientes = ultimas[-slots:]
    filas: list[tuple[str, str] | None] = [None] * slots
    offset = slots - len(recientes)
    for i, item in enumerate(recientes):
        filas[offset + i] = item
    return filas


def barra_comandos(pausa_seg: float, *, auto: bool = True, velocidad: str = "normal") -> list[str]:
    auto_txt = "ON" if auto else "OFF"
    return [
        f" [ESP] avanzar [Q] salir [+/-] vel [P] auto:{auto_txt} [{velocidad}] {pausa_seg:.1f}s ",
        " [F] salto a momento  [^v] scroll relato  ",
        " " + "-" * 48,
    ]


def pantalla_final(
    estado: EstadoPartido,
    *,
    semilla: int,
    comando_repetir: str,
    abortado: bool,
) -> list[str]:
    g0, g1 = estado.marcador.goles
    eq0 = _nombres_equipo(estado, 0)
    eq1 = _nombres_equipo(estado, 1)
    goles = estado.acciones.get("disparo", 0)
    pases = estado.acciones.get("pase", 0)
    titulo = "PARTIDO DETENIDO" if abortado else "FIN DEL PARTIDO"
    penales = " (penales)" if estado.definido_por_penales else ""
    return [
        "",
        "+======================================+",
        f"|     {titulo:<30}|",
        "+======================================+",
        "",
        f"  {eq0}",
        f"       {g0}  -  {g1}{penales}",
        f"  {eq1}",
        "",
        f"  Turnos: {estado.turnos}  |  Pases: {pases}  |  Disparos: {goles}",
        f"  Semilla #{semilla}",
        "",
        "  [ESPACIO] para salir",
        "",
        f"  replay: {comando_repetir}",
        "",
    ]


def _es_linea_decorativa(msg: str) -> bool:
    if not msg:
        return False
    if msg[0] in _BOX_CHARS:
        return True
    return msg.startswith("  +") or msg.startswith("  |")


def formatear_linea_log(msg: str) -> str:
    """Convierte evento crudo en linea estilo feed de juego (ASCII)."""
    if not msg:
        return ""
    if _es_linea_decorativa(msg):
        return msg
    if msg.startswith("==="):
        return msg
    if msg.startswith("T") and " | " in msg and "marcador" in msg:
        return f">> {msg.replace('T', 'TURNO ', 1)}"
    if msg.startswith("** GOL") or msg.startswith("GOAL"):
        return f"** {msg.lstrip('* ')}"
    if msg.startswith("Fin"):
        return f"[FIN] {msg}"
    if msg.startswith("Partido detenido"):
        return f"[STOP] {msg}"
    if msg.startswith(">> Cambio") or msg.startswith(">> Reposicion"):
        return msg
    if msg.startswith("Empate"):
        return f"[!] {msg}"
    if msg.startswith("--- Penales"):
        return "========== PENALES =========="
    if "dispara al arco" in msg and not msg.startswith(" "):
        return f"!! {msg}"
    if " pasa a " in msg and not msg.startswith(" "):
        return f"-> {msg}"
    if " pasa de turno" in msg:
        return f"o  {msg}"
    if " revienta" in msg:
        return f"^  {msg}"
    if "recupera la pelota" in msg:
        return f"<> {msg}"
    if "coloca Trampa" in msg or " marca a " in msg:
        return f"D  {msg.strip()}"
    if "gambetea" in msg.lower():
        return f"*  {msg.strip()}"
    if "Offside" in msg:
        return f"X  {msg.strip()}"
    if "Falta de" in msg:
        return f"F  {msg.strip()}"
    if "Disparo:" in msg or "Despeje:" in msg or "Penal" in msg:
        return f"   d6 {msg.strip()}"
    if "GOL de" in msg or "Gana " in msg:
        return f"   + {msg.strip()}"
    if msg.startswith("  "):
        return f"     {msg.strip()}"
    if msg.startswith("Semilla") or msg.startswith("Reglamento") or msg.startswith("Equipo"):
        return f"> {msg}"
    return f". {msg}"


def intro_partido(
    semilla: int,
    reg_id: str,
    ia: str,
    formacion: str,
    eq0: str,
    eq1: str,
    total_cartas: int,
    mano: int,
    saque: str,
) -> list[str]:
    return [
        "",
        "+======================================+",
        "|     KICK OFF  -  FOBAL FACU          |",
        "+======================================+",
        "",
        f"  Semilla #{semilla}  |  Reglamento {reg_id}  |  IA {ia}",
        f"  Formacion {formacion}",
        "",
        "  +-- EQUIPO 1 ---------------------+",
        f"  | {eq0:<31}|",
        "  +--------------------------------+",
        "  +-- EQUIPO 2 ---------------------+",
        f"  | {eq1:<31}|",
        "  +--------------------------------+",
        "",
        f"  [MAZO] Barajado ({total_cartas} cartas, mano {mano})",
        f"  [BOLA] Saque: {saque}",
        "",
        "  >>  Comienza el partido!",
        "",
    ]
