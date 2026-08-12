"""Servidor local de la interfaz web.

Levanta una página en ``http://localhost:8000`` para editar reglamentos, correr
simulaciones y mirar partidos. Usa solo la biblioteca estándar y escucha
únicamente en la máquina donde se ejecuta.

Las simulaciones corren en el mismo motor que la línea de comandos: lo que se ve
en la web y lo que imprime la terminal son siempre los mismos números.
"""

from __future__ import annotations

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from simulador import __version__
from simulador.cartas import Carta, rol
from simulador.estadisticas import ETIQUETAS, Escenario, agente_de, simular
from simulador.ia import catalogo as catalogo_perfiles
from simulador.motor import crear_partido, jugar_partido
from simulador.reglamento import (
    ACCIONES,
    ALCANCES_REPOSICION,
    DIRECTORIO,
    MOMENTOS_REPOSICION,
    SIN_RESPUESTA,
    ReglamentoInvalido,
    cargar,
    catalogo,
    desde_dict,
    guardar,
    ruta_de,
    validar,
)
from simulador.replay import grabacion

ESTATICOS = Path(__file__).resolve().parent / "estatico"
TIPOS_MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
}
CUERPO_MAXIMO = 1_000_000  # 1 MB: un reglamento no pesa ni 5 KB
PARTIDOS_MAXIMO = 5_000
ESCENARIOS_MAXIMO = 12


class Api:
    """Las operaciones que la página puede pedir, sin saber nada de HTTP."""

    def __init__(self, directorio: Path = DIRECTORIO, *, verboso: bool = False) -> None:
        self.directorio = directorio
        self.verboso = verboso
        self._candado = threading.Lock()

    def opciones(self) -> dict[str, Any]:
        return {
            "version": __version__,
            "reglamentos": catalogo(directorio=self.directorio),
            "perfiles": catalogo_perfiles(),
            "cartas": [
                {"nombre": c.value, "rol": rol(c)} for c in Carta
            ],
            "acciones": list(ACCIONES),
            "momentos_reposicion": list(MOMENTOS_REPOSICION),
            "alcances_reposicion": list(ALCANCES_REPOSICION),
            "pasa_turno_sin_respuesta": list(SIN_RESPUESTA),
            "etiquetas": ETIQUETAS,
        }

    def leer_reglamento(self, id_reglamento: str) -> dict[str, Any]:
        reg = cargar(id_reglamento, directorio=self.directorio)
        datos = reg.a_dict()
        datos["extends"] = self._extends_de(id_reglamento)
        return datos

    def validar_reglamento(self, datos: dict[str, Any]) -> dict[str, Any]:
        try:
            reg = desde_dict({k: v for k, v in datos.items() if k != "extends"})
        except ReglamentoInvalido as error:
            return {"valido": False, "errores": error.errores}
        return {"valido": True, "errores": validar(reg)}

    def guardar_reglamento(self, datos: dict[str, Any]) -> dict[str, Any]:
        heredado = datos.get("extends")
        with self._candado:
            reg = desde_dict({k: v for k, v in datos.items() if k != "extends"})
            ruta = guardar(reg, extends=heredado, directorio=self.directorio)
        return {"guardado": reg.id, "archivo": str(ruta), "errores": []}

    def borrar_reglamento(self, id_reglamento: str) -> dict[str, Any]:
        ruta = ruta_de(id_reglamento, directorio=self.directorio)
        if not ruta.exists():
            raise FileNotFoundError(f"No existe el reglamento {id_reglamento!r}")
        with self._candado:
            ruta.unlink()
        return {"borrado": id_reglamento}

    def simular(self, cuerpo: dict[str, Any]) -> dict[str, Any]:
        partidos = _entero(cuerpo.get("partidos", 200), 1, PARTIDOS_MAXIMO, "partidos")
        crudos = cuerpo.get("escenarios") or []
        if not crudos:
            raise ValueError("hay que indicar al menos un escenario")
        if len(crudos) > ESCENARIOS_MAXIMO:
            raise ValueError(f"como máximo {ESCENARIOS_MAXIMO} escenarios por corrida")
        escenarios = [Escenario.desde_dict(e) for e in crudos]
        for escenario in escenarios:
            _entero(escenario.jugadores_por_equipo, 2, 11, "jugadores por equipo")
        resultados = [simular(e, partidos) for e in escenarios]
        return {"partidos": partidos, "resultados": [r.a_dict() for r in resultados]}

    def partido(self, cuerpo: dict[str, Any]) -> dict[str, Any]:
        escenario = Escenario.desde_dict(cuerpo.get("escenario", {}))
        _entero(escenario.jugadores_por_equipo, 2, 11, "jugadores por equipo")
        semilla = cuerpo.get("semilla")
        semilla = int(semilla) if semilla not in (None, "") else None
        nombres = cuerpo.get("nombres") or None
        estado = crear_partido(
            cargar(escenario.reglamento, directorio=self.directorio),
            jugadores_por_equipo=escenario.jugadores_por_equipo,
            semilla=semilla,
            nombres=nombres,
        )
        agente = agente_de(escenario, rng=estado.rng)
        jugar_partido(estado=estado, agente=agente)
        datos = grabacion(estado, perfiles=agente.describir())
        datos["escenario"] = escenario.a_dict()
        return datos

    def _extends_de(self, id_reglamento: str) -> str | None:
        ruta = ruta_de(id_reglamento, directorio=self.directorio)
        if not ruta.exists():
            return None
        try:
            return json.loads(ruta.read_text(encoding="utf-8")).get("extends")
        except json.JSONDecodeError:
            return None


def _entero(valor: Any, minimo: int, maximo: int, nombre: str) -> int:
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{nombre}: se esperaba un número") from None
    if not minimo <= numero <= maximo:
        raise ValueError(f"{nombre}: tiene que estar entre {minimo} y {maximo}")
    return numero


class Manejador(BaseHTTPRequestHandler):
    server_version = f"FobalFacu/{__version__}"
    api: Api

    # --- rutas ------------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802 (nombre impuesto por la biblioteca)
        ruta = self.path.split("?")[0]
        if ruta == "/api/opciones":
            return self._responder_json(self.api.opciones)
        if ruta.startswith("/api/reglamentos/"):
            id_reglamento = ruta.removeprefix("/api/reglamentos/")
            return self._responder_json(lambda: self.api.leer_reglamento(id_reglamento))
        if ruta.startswith("/api/"):
            return self._error(404, "no existe ese recurso")
        return self._servir_estatico(ruta)

    def do_POST(self) -> None:  # noqa: N802
        ruta = self.path.split("?")[0]
        cuerpo = self._leer_json()
        if cuerpo is None:
            return
        if ruta == "/api/simular":
            return self._responder_json(lambda: self.api.simular(cuerpo))
        if ruta == "/api/partido":
            return self._responder_json(lambda: self.api.partido(cuerpo))
        if ruta == "/api/validar":
            return self._responder_json(lambda: self.api.validar_reglamento(cuerpo))
        if ruta == "/api/reglamentos":
            return self._responder_json(lambda: self.api.guardar_reglamento(cuerpo))
        return self._error(404, "no existe ese recurso")

    def do_DELETE(self) -> None:  # noqa: N802
        ruta = self.path.split("?")[0]
        if ruta.startswith("/api/reglamentos/"):
            id_reglamento = ruta.removeprefix("/api/reglamentos/")
            return self._responder_json(lambda: self.api.borrar_reglamento(id_reglamento))
        return self._error(404, "no existe ese recurso")

    # --- utilidades -------------------------------------------------------

    def _responder_json(self, operacion) -> None:
        try:
            datos = operacion()
        except ReglamentoInvalido as error:
            return self._json(400, {"error": str(error), "errores": error.errores})
        except FileNotFoundError as error:
            return self._json(404, {"error": str(error)})
        except (ValueError, KeyError) as error:
            return self._json(400, {"error": str(error)})
        except Exception as error:  # pragma: no cover - red de seguridad
            self.log_error("error inesperado: %r", error)
            return self._json(500, {"error": f"error inesperado: {error}"})
        self._json(200, datos)

    def _leer_json(self) -> dict[str, Any] | None:
        longitud = int(self.headers.get("Content-Length") or 0)
        if longitud > CUERPO_MAXIMO:
            self._error(413, "el cuerpo del pedido es demasiado grande")
            return None
        crudo = self.rfile.read(longitud) if longitud else b"{}"
        try:
            datos = json.loads(crudo or b"{}")
        except json.JSONDecodeError as error:
            self._error(400, f"JSON inválido: {error}")
            return None
        if not isinstance(datos, dict):
            self._error(400, "se esperaba un objeto JSON")
            return None
        return datos

    def _servir_estatico(self, ruta: str) -> None:
        relativa = "index.html" if ruta in ("/", "") else ruta.lstrip("/")
        destino = (ESTATICOS / relativa).resolve()
        if not destino.is_relative_to(ESTATICOS) or not destino.is_file():
            return self._error(404, "archivo no encontrado")
        if destino.suffix not in TIPOS_MIME:
            return self._error(403, "tipo de archivo no permitido")
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
        # La consola muestra solo lo que le sirve a quien está simulando.
        if not self.api.verboso or not args:
            return
        if str(args[0]).startswith(("POST /api/simular", "POST /api/partido")):
            print(f"  · {args[0]}")


def crear_servidor(
    puerto: int = 8000, directorio: Path = DIRECTORIO, *, verboso: bool = False
) -> ThreadingHTTPServer:
    manejador = type("ManejadorConApi", (Manejador,), {"api": Api(directorio, verboso=verboso)})
    return ThreadingHTTPServer(("127.0.0.1", puerto), manejador)


def servir(
    puerto: int = 8000,
    *,
    abrir_navegador: bool = True,
    directorio: Path = DIRECTORIO,
) -> None:
    """Levanta la interfaz web hasta que se corte con Ctrl+C."""
    try:
        servidor = crear_servidor(puerto, directorio, verboso=True)
    except OSError as error:
        raise SystemExit(
            f"No se pudo abrir el puerto {puerto} ({error}). "
            f"Probá con otro: python3 -m simulador web --puerto {puerto + 1}"
        ) from None

    direccion = f"http://localhost:{servidor.server_port}"
    print(f"Fobal Facu · interfaz web en {direccion}")
    print("Reglamentos en:", directorio)
    print("Ctrl+C para cerrar.\n")
    if abrir_navegador:
        threading.Timer(0.5, lambda: webbrowser.open(direccion)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nListo.")
    finally:
        servidor.server_close()
