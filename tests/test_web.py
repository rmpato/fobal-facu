"""La interfaz web: rutas, validación y guardado sobre un directorio de prueba."""

import json
import shutil
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from simulador.reglamento import DIRECTORIO
from simulador.web.servidor import crear_servidor


class ServidorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directorio = Path(tempfile.mkdtemp())
        for nombre in ("v1.json", "v2.json"):
            shutil.copy(DIRECTORIO / nombre, cls.directorio / nombre)
        cls.servidor = crear_servidor(0, cls.directorio)
        cls.base = f"http://127.0.0.1:{cls.servidor.server_port}"
        cls.hilo = threading.Thread(target=cls.servidor.serve_forever, daemon=True)
        cls.hilo.start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()
        cls.servidor.server_close()
        cls.hilo.join(timeout=5)
        shutil.rmtree(cls.directorio)

    def pedir(self, ruta, datos=None, metodo=None):
        cuerpo = json.dumps(datos).encode() if datos is not None else None
        pedido = urllib.request.Request(
            self.base + ruta, data=cuerpo, method=metodo or ("POST" if datos else "GET"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(pedido, timeout=30) as respuesta:
            return json.loads(respuesta.read())

    def esperar_error(self, ruta, datos=None, metodo=None):
        with self.assertRaises(urllib.error.HTTPError) as caso:
            self.pedir(ruta, datos, metodo)
        return caso.exception.code, json.loads(caso.exception.read())

    # --- páginas ---------------------------------------------------------

    def test_la_pagina_principal_se_sirve(self):
        with urllib.request.urlopen(self.base + "/", timeout=10) as respuesta:
            html = respuesta.read().decode()
        self.assertIn("Fobal Facu", html)
        self.assertIn("app.js", html)

    def test_no_se_pueden_leer_archivos_de_afuera(self):
        codigo, _ = self.esperar_error("/../../reglamentos/v1.json")
        self.assertIn(codigo, (400, 403, 404))

    # --- reglamentos ------------------------------------------------------

    def test_opciones_trae_todo_lo_que_la_pagina_necesita(self):
        datos = self.pedir("/api/opciones")
        for clave in ("reglamentos", "perfiles", "cartas", "acciones", "momentos_reposicion"):
            self.assertIn(clave, datos)
        self.assertLessEqual({"v1", "v2"}, {r["id"] for r in datos["reglamentos"]})

    def test_leer_un_reglamento(self):
        datos = self.pedir("/api/reglamentos/v2")
        self.assertEqual(datos["id"], "v2")
        self.assertEqual(datos["extends"], "v1")
        self.assertIn("Pase", datos["mazo"])

    def test_leer_uno_que_no_existe(self):
        codigo, _ = self.esperar_error("/api/reglamentos/fantasma")
        self.assertEqual(codigo, 404)

    def test_validar_avisa_los_problemas_sin_guardar(self):
        datos = self.pedir("/api/reglamentos/v1")
        datos["mazo"] = {"Pase": 4}
        respuesta = self.pedir("/api/validar", datos)
        self.assertTrue(respuesta["errores"])
        self.assertFalse((self.directorio / "roto.json").exists())

    def test_guardar_y_volver_a_leer(self):
        datos = self.pedir("/api/reglamentos/v1")
        datos.update(id="prueba", nombre="Prueba", extends=None)
        datos["mano"] = {"inicial": 8, "maxima": 9}
        respuesta = self.pedir("/api/reglamentos", datos)
        self.assertEqual(respuesta["guardado"], "prueba")

        leido = self.pedir("/api/reglamentos/prueba")
        self.assertEqual(leido["mano"], {"inicial": 8, "maxima": 9})
        self.assertIn("prueba", [r["id"] for r in self.pedir("/api/opciones")["reglamentos"]])

    def test_no_se_guarda_un_reglamento_invalido(self):
        datos = self.pedir("/api/reglamentos/v1")
        datos.update(id="invalido", acciones_ofensivas=["pase"])
        codigo, cuerpo = self.esperar_error("/api/reglamentos", datos)
        self.assertEqual(codigo, 400)
        self.assertTrue(cuerpo["errores"])
        self.assertFalse((self.directorio / "invalido.json").exists())

    def test_borrar(self):
        datos = self.pedir("/api/reglamentos/v1")
        datos.update(id="descartable", extends=None)
        self.pedir("/api/reglamentos", datos)
        self.pedir("/api/reglamentos/descartable", metodo="DELETE")
        self.assertFalse((self.directorio / "descartable.json").exists())

    def test_un_id_con_rutas_no_toca_el_disco(self):
        codigo, _ = self.esperar_error("/api/reglamentos/..%2F..%2Fsecreto", metodo="DELETE")
        self.assertIn(codigo, (400, 404))

    # --- simulación -------------------------------------------------------

    def test_simular_dos_escenarios(self):
        datos = self.pedir("/api/simular", {
            "escenarios": [{"reglamento": "v1"}, {"reglamento": "v2", "jugadores_por_equipo": 4}],
            "partidos": 10,
        })
        self.assertEqual(len(datos["resultados"]), 2)
        primero = datos["resultados"][0]
        self.assertEqual(primero["partidos"], 10)
        self.assertIn("reparto_acciones", primero)
        self.assertIn("marca_efectiva", primero["por_partido"])

    def test_no_se_aceptan_tandas_gigantes(self):
        codigo, cuerpo = self.esperar_error(
            "/api/simular", {"escenarios": [{"reglamento": "v1"}], "partidos": 999_999}
        )
        self.assertEqual(codigo, 400)
        self.assertIn("partidos", cuerpo["error"])

    def test_hace_falta_al_menos_un_escenario(self):
        codigo, _ = self.esperar_error("/api/simular", {"escenarios": [], "partidos": 5})
        self.assertEqual(codigo, 400)

    def test_un_partido_devuelve_el_relato_completo(self):
        datos = self.pedir("/api/partido", {
            "escenario": {"reglamento": "v2"},
            "semilla": 77,
            "nombres": ["A", "B", "C", "D", "E", "F"],
        })
        self.assertEqual(datos["semilla"], 77)
        self.assertEqual(datos["equipos"][0], ["A", "B", "C"])
        self.assertTrue(datos["eventos"])
        self.assertEqual(datos["eventos"][-1]["tipo"], "fin")

    def test_sin_semilla_devuelve_la_que_uso(self):
        datos = self.pedir("/api/partido", {"escenario": {"reglamento": "v1"}})
        self.assertIsInstance(datos["semilla"], int)

    def test_un_pedido_roto_no_tira_el_servidor(self):
        pedido = urllib.request.Request(
            self.base + "/api/simular", data=b"{no es json",
            method="POST", headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(urllib.error.HTTPError) as caso:
            urllib.request.urlopen(pedido, timeout=10)
        self.assertEqual(caso.exception.code, 400)
        self.assertEqual(self.pedir("/api/opciones")["version"][:1], "2")


if __name__ == "__main__":
    unittest.main()
