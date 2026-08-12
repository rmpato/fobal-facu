"""Grabación de partidos y página HTML para volver a verlos."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from simulador.eventos import Evento
from simulador.motor import jugar_partido
from simulador.replay import grabacion, guardar


class GrabacionTest(unittest.TestCase):
    def setUp(self):
        self.directorio = Path(tempfile.mkdtemp())
        self.estado = jugar_partido("v2", semilla=21, nombres=list("ABCDEF"))

    def tearDown(self):
        shutil.rmtree(self.directorio)

    def test_la_grabacion_describe_el_partido(self):
        datos = grabacion(self.estado, perfiles="Táctico")
        self.assertEqual(datos["semilla"], 21)
        self.assertEqual(datos["equipos"], [["A", "B", "C"], ["D", "E", "F"]])
        self.assertEqual(datos["marcador_final"], self.estado.marcador.goles)
        self.assertEqual(len(datos["eventos"]), len(self.estado.eventos))

    def test_los_eventos_van_y_vuelven_del_json(self):
        for evento in self.estado.eventos[:50]:
            self.assertEqual(Evento.desde_dict(evento.a_dict()), evento)

    def test_guardar_json(self):
        (ruta,) = guardar(self.estado, self.directorio / "partido.json")
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        self.assertEqual(datos["turnos"], self.estado.turno)

    def test_guardar_html_deja_una_pagina_que_se_abre_sola(self):
        rutas = guardar(self.estado, self.directorio / "partido.html")
        self.assertEqual({r.suffix for r in rutas}, {".json", ".html"})
        html = (self.directorio / "partido.html").read_text(encoding="utf-8")
        self.assertIn("<!DOCTYPE html>", html)
        self.assertNotIn("/*DATOS*/null", html)  # los datos quedaron embebidos
        self.assertIn('"semilla": 21', html.replace("\n", ""))


if __name__ == "__main__":
    unittest.main()
