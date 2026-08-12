"""Servidor de la interfaz gráfica.

Levanta una página en http://localhost:8000 para armar los equipos, editar los
reglamentos y correr simulaciones sin escribir un solo comando. Usa solo la
biblioteca estándar y escucha únicamente en la máquina donde se ejecuta.

Las simulaciones corren en el mismo motor que la línea de comandos: los números
de la pantalla y los de la terminal son siempre los mismos.
"""

from __future__ import annotations

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from simulador.cartas import Carta, rol_carta
from simulador.config import ConfigSimulacion
from simulador.estadisticas import ACCIONES_REPORTE, ETIQUETAS_ACCION, simular_lote
from simulador.eventos_espectador import clasificar_evento
from simulador.ia import IDS_IA, nombre_ia
from simulador.motor import crear_partido, jugar_partido
from simulador.reglamento import REGLAMENTOS_DIR
from simulador.web import equipos as equipos_io
from simulador.web import reglamentos_io as reglas

ESTATICOS = Path(__file__).resolve().parent / "estatico"
TIPOS_MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
}
CUERPO_MAXIMO = 1_000_000
PARTIDOS_MAXIMO = 3_000
ESCENARIOS_MAXIMO = 8
JUGADORES_MAXIMO = 8


class Api:
    """Lo que la página puede pedir, sin saber nada de HTTP."""

    def __init__(self, directorio: Path = REGLAMENTOS_DIR, *, verboso: bool = False) -> None:
        self.directorio = directorio
        self.verboso = verboso
        self._candado = threading.Lock()

    # --- datos para armar la pantalla ------------------------------------

    def opciones(self) -> dict[str, Any]:
        return {
            "reglamentos": reglas.catalogo(self.directorio),
            "perfiles": [
                {"id": i, "nombre": nombre_ia(i)} for i in IDS_IA
            ],
            "cartas": [
                {"nombre": c.value, "rol": rol_carta(c)} for c in Carta
            ],
            "cartas_defensivas": [c.value for c in reglas.CARTAS_DEFENSIVAS],
            "cartas_contra": [c.value for c in reglas.CARTAS_CONTRA],
            "acciones": list(reglas.ACCIONES),
            "reposiciones": list(reglas.REPOSICIONES),
            "sin_respuesta": list(reglas.SIN_RESPUESTA),
            "tabla_disparo": reglas.tabla_disparo(),
            "etiquetas_accion": {
                accion: ETIQUETAS_ACCION.get(accion, accion) for accion in ACCIONES_REPORTE
            },
            "acciones_reporte": list(ACCIONES_REPORTE),
            "equipos": equipos_io.leer(),
        }

    # --- equipos ----------------------------------------------------------

    def guardar_equipos(self, cuerpo: dict[str, Any]) -> dict[str, Any]:
        with self._candado:
            return equipos_io.guardar(cuerpo, maximo=JUGADORES_MAXIMO)

    # --- reglamentos ------------------------------------------------------

    def leer_reglamento(self, id_reglamento: str) -> dict[str, Any]:
        return reglas.leer(id_reglamento, self.directorio)

    def plantilla(self) -> dict[str, Any]:
        return reglas.plantilla()

    def revisar_reglamento(self, datos: dict[str, Any]) -> dict[str, Any]:
        return {"problemas": reglas.revisar(datos)}

    def guardar_reglamento(self, datos: dict[str, Any]) -> dict[str, Any]:
        with self._candado:
            ruta = reglas.guardar(datos, self.directorio)
        return {"guardado": datos["id"], "archivo": str(ruta)}

    def borrar_reglamento(self, id_reglamento: str) -> dict[str, Any]:
        with self._candado:
            reglas.borrar(id_reglamento, self.directorio)
        return {"borrado": id_reglamento}

    # --- simulaciones -----------------------------------------------------

    def simular(self, cuerpo: dict[str, Any]) -> dict[str, Any]:
        partidos = _entero(cuerpo.get("partidos", 200), 1, PARTIDOS_MAXIMO, "partidos")
        crudos = cuerpo.get("escenarios") or []
        if not crudos:
            raise ValueError("Hay que elegir al menos un reglamento para simular.")
        if len(crudos) > ESCENARIOS_MAXIMO:
            raise ValueError(f"Como maximo {ESCENARIOS_MAXIMO} comparaciones por vez.")

        resultados = []
        for crudo in crudos:
            config = _config(crudo)
            resultado = simular_lote(partidos=partidos, config=config)
            resultados.append(_resultado_a_dict(resultado, config))
        return {"partidos": partidos, "resultados": resultados}

    def partido(self, cuerpo: dict[str, Any]) -> dict[str, Any]:
        config = _config(cuerpo.get("escenario", {}))
        equipos = cuerpo.get("equipos") or equipos_io.leer()
        nombres = _nombres_por_equipo(equipos, config.jugadores_por_equipo)
        semilla = cuerpo.get("semilla")
        semilla = int(semilla) if str(semilla or "").strip() else _semilla_al_azar()

        estado = crear_partido(config, semilla=semilla, nombres_por_equipo=nombres)
        eventos: list[dict[str, Any]] = []
        turno = 0

        def registrar(mensaje: str) -> None:
            nonlocal turno
            evento = clasificar_evento(mensaje, turno=turno)
            if evento.turno is not None:
                turno = evento.turno
            datos = evento.to_dict()
            # La mano del que tiene la pelota, para poder mostrarla mientras
            # se mira el partido, y cuántas cartas tiene cada uno.
            portador = estado.portador
            datos["portador"] = portador.nombre
            datos["mano"] = [carta.value for carta in portador.mano]
            datos["cartas_por_jugador"] = {j.nombre: len(j.mano) for j in estado.jugadores}
            datos["pases"] = estado.pases_en_jugada
            eventos.append(datos)

        estado.on_evento = registrar
        jugar_partido(config=config, estado=estado, verbose=True)

        return {
            "semilla": semilla,
            "reglamento": config.reglamento,
            "equipos": [list(nombres[0]), list(nombres[1])],
            "nombres_equipos": [
                equipos.get("equipo1", {}).get("nombre", "Equipo 1"),
                equipos.get("equipo2", {}).get("nombre", "Equipo 2"),
            ],
            "marcador_final": list(estado.marcador.goles),
            "turnos": estado.turnos,
            "definido_por_penales": estado.definido_por_penales,
            "eventos": eventos,
        }


def _semilla_al_azar() -> int:
    import random

    return random.randrange(1_000_000)


def _config(crudo: dict[str, Any]) -> ConfigSimulacion:
    jugadores = _entero(
        crudo.get("jugadores_por_equipo", 3), 2, JUGADORES_MAXIMO, "jugadores por equipo"
    )
    kwargs: dict[str, Any] = {
        "reglamento": str(crudo.get("reglamento", "v1")),
        "jugadores_por_equipo": jugadores,
        "ia": str(crudo.get("ia", "estrategica")),
    }
    if crudo.get("ia_equipo0"):
        kwargs["ia_equipo0"] = str(crudo["ia_equipo0"])
    if crudo.get("ia_equipo1"):
        kwargs["ia_equipo1"] = str(crudo["ia_equipo1"])
    return ConfigSimulacion(**kwargs)


def _nombres_por_equipo(equipos: dict[str, Any], jugadores: int) -> tuple[list[str], list[str]]:
    salida = []
    for clave, prefijo in (("equipo1", "E1"), ("equipo2", "E2")):
        nombres = [str(n).strip() for n in (equipos.get(clave, {}).get("jugadores") or []) if str(n).strip()]
        while len(nombres) < jugadores:
            nombres.append(f"{prefijo}-J{len(nombres) + 1}")
        salida.append(nombres[:jugadores])
    return salida[0], salida[1]


def _resultado_a_dict(resultado, config: ConfigSimulacion) -> dict[str, Any]:
    partidos = resultado.partidos or 1
    completados = resultado.partidos - resultado.empates_tecnicos
    reparto = resultado.pct_acciones()
    return {
        "reglamento": resultado.reglamento,
        "etiqueta": f"{resultado.reglamento} · {config.jugadores_por_equipo}v"
                    f"{config.jugadores_por_equipo} · {nombre_ia(config.ia)}",
        "jugadores_por_equipo": config.jugadores_por_equipo,
        "ia": config.ia,
        "partidos": resultado.partidos,
        "victorias": list(resultado.victorias),
        "sin_definir": resultado.empates_tecnicos,
        "pct_completados": round(100 * completados / partidos, 1),
        "pct_penales": round(100 * resultado.penales / partidos, 1),
        "goles_promedio": round(resultado.goles_promedio, 2),
        "turnos_promedio": round(resultado.turnos_promedio, 1),
        "reparto_acciones": {a: round(reparto.get(a, 0.0), 1) for a in ACCIONES_REPORTE},
        "por_partido": {
            clave: round(resultado.acciones.get(clave, 0) / partidos, 2)
            for clave in (
                *ACCIONES_REPORTE,
                "trampa_colocada",
                "marca_colocada",
                "offside_efectivo",
                "marca_efectiva",
            )
        },
        "cartas": {
            carta: round(veces / partidos, 2)
            for carta, veces in sorted(resultado.cartas_jugadas.items(), key=lambda x: -x[1])
        },
    }


def _entero(valor: Any, minimo: int, maximo: int, nombre: str) -> int:
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{nombre}: se esperaba un numero.") from None
    if not minimo <= numero <= maximo:
        raise ValueError(f"{nombre}: tiene que estar entre {minimo} y {maximo}.")
    return numero


class Manejador(BaseHTTPRequestHandler):
    server_version = "FobalFacu"
    api: Api

    def do_GET(self) -> None:  # noqa: N802 (nombre impuesto por la biblioteca)
        ruta = self.path.split("?")[0]
        if ruta == "/api/opciones":
            return self._json_de(self.api.opciones)
        if ruta == "/api/reglamentos/_nuevo":
            return self._json_de(self.api.plantilla)
        if ruta.startswith("/api/reglamentos/"):
            id_reglamento = ruta.removeprefix("/api/reglamentos/")
            return self._json_de(lambda: self.api.leer_reglamento(id_reglamento))
        if ruta.startswith("/api/"):
            return self._error(404, "No existe ese recurso.")
        return self._estatico(ruta)

    def do_POST(self) -> None:  # noqa: N802
        ruta = self.path.split("?")[0]
        cuerpo = self._cuerpo()
        if cuerpo is None:
            return
        rutas = {
            "/api/simular": self.api.simular,
            "/api/partido": self.api.partido,
            "/api/revisar": self.api.revisar_reglamento,
            "/api/reglamentos": self.api.guardar_reglamento,
            "/api/equipos": self.api.guardar_equipos,
        }
        operacion = rutas.get(ruta)
        if not operacion:
            return self._error(404, "No existe ese recurso.")
        return self._json_de(lambda: operacion(cuerpo))

    def do_DELETE(self) -> None:  # noqa: N802
        ruta = self.path.split("?")[0]
        if ruta.startswith("/api/reglamentos/"):
            id_reglamento = ruta.removeprefix("/api/reglamentos/")
            return self._json_de(lambda: self.api.borrar_reglamento(id_reglamento))
        return self._error(404, "No existe ese recurso.")

    # --- plomería ---------------------------------------------------------

    def _json_de(self, operacion) -> None:
        try:
            datos = operacion()
        except reglas.ReglamentoInvalido as error:
            return self._json(400, {"error": str(error), "problemas": error.errores})
        except FileNotFoundError as error:
            return self._json(404, {"error": str(error)})
        except (ValueError, KeyError) as error:
            return self._json(400, {"error": str(error)})
        except Exception as error:  # pragma: no cover - red de seguridad
            self.log_error("error inesperado: %r", error)
            return self._json(500, {"error": f"Error inesperado: {error}"})
        self._json(200, datos)

    def _cuerpo(self) -> dict[str, Any] | None:
        longitud = int(self.headers.get("Content-Length") or 0)
        if longitud > CUERPO_MAXIMO:
            self._error(413, "El pedido es demasiado grande.")
            return None
        crudo = self.rfile.read(longitud) if longitud else b"{}"
        try:
            datos = json.loads(crudo or b"{}")
        except json.JSONDecodeError as error:
            self._error(400, f"JSON invalido: {error}")
            return None
        if not isinstance(datos, dict):
            self._error(400, "Se esperaba un objeto JSON.")
            return None
        return datos

    def _estatico(self, ruta: str) -> None:
        relativa = "index.html" if ruta in ("/", "") else ruta.lstrip("/")
        destino = (ESTATICOS / relativa).resolve()
        if not destino.is_relative_to(ESTATICOS) or not destino.is_file():
            return self._error(404, "Archivo no encontrado.")
        if destino.suffix not in TIPOS_MIME:
            return self._error(403, "Tipo de archivo no permitido.")
        contenido = destino.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", TIPOS_MIME[destino.suffix])
        self.send_header("Content-Length", str(len(contenido)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(contenido)

    def _json(self, codigo: int, datos: dict[str, Any]) -> None:
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def _error(self, codigo: int, mensaje: str) -> None:
        self._json(codigo, {"error": mensaje})

    def log_message(self, formato: str, *args: Any) -> None:
        if not self.api.verboso or not args:
            return
        primera = str(args[0])
        if primera.startswith(("POST /api/simular", "POST /api/partido")):
            print(f"  · {primera}")


def crear_servidor(
    puerto: int = 8000, directorio: Path = REGLAMENTOS_DIR, *, verboso: bool = False
) -> ThreadingHTTPServer:
    manejador = type("ManejadorConApi", (Manejador,), {"api": Api(directorio, verboso=verboso)})
    return ThreadingHTTPServer(("127.0.0.1", puerto), manejador)


def servir(
    puerto: int = 8000,
    *,
    abrir_navegador: bool = True,
    directorio: Path = REGLAMENTOS_DIR,
) -> None:
    """Levanta la interfaz hasta que se corte con Ctrl+C."""
    try:
        servidor = crear_servidor(puerto, directorio, verboso=True)
    except OSError as error:
        raise SystemExit(
            f"No se pudo usar el puerto {puerto} ({error}).\n"
            f"Proba con otro:  python3 -m simulador web --puerto {puerto + 1}"
        ) from None

    direccion = f"http://localhost:{servidor.server_port}"
    print(f"Fobal Facu · interfaz en {direccion}")
    print(f"Reglamentos en: {directorio}")
    print("Ctrl+C para cerrar.\n")
    if abrir_navegador:
        threading.Timer(0.5, lambda: webbrowser.open(direccion)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nListo.")
    finally:
        servidor.server_close()
