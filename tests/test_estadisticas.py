"""Simulación en lote, métricas y salida de texto."""

import unittest

from simulador.estadisticas import (
    ACCIONES,
    Escenario,
    formatear_resultado,
    formatear_tabla,
    simular,
)


class SimulacionTest(unittest.TestCase):
    def test_una_tanda_es_repetible(self):
        escenario = Escenario(reglamento="v2", jugadores_por_equipo=3)
        primera = simular(escenario, 20)
        segunda = simular(escenario, 20)
        self.assertEqual(primera.a_dict(), segunda.a_dict())

    def test_las_semillas_distintas_cambian_el_resultado(self):
        escenario = Escenario(reglamento="v2")
        self.assertNotEqual(
            simular(escenario, 20).goles,
            simular(escenario, 20, semilla_base=500).goles,
        )

    def test_el_reparto_de_acciones_suma_cien(self):
        reparto = simular(Escenario(reglamento="v1"), 20).reparto_acciones()
        self.assertAlmostEqual(sum(reparto.values()), 100.0, places=6)
        self.assertEqual(set(reparto), set(ACCIONES))

    def test_las_cuentas_cierran(self):
        resultado = simular(Escenario(reglamento="v2"), 30)
        self.assertEqual(resultado.partidos, 30)
        self.assertLessEqual(sum(resultado.victorias) + resultado.sin_definir, 30)
        self.assertGreater(resultado.turnos_promedio, 0)
        self.assertGreaterEqual(resultado.pct_completados, 0)
        self.assertLessEqual(resultado.pct_completados, 100)

    def test_el_perfil_cambia_como_se_juega(self):
        conservador = simular(Escenario(reglamento="v1", perfil="conservador"), 30)
        agresiva = simular(Escenario(reglamento="v1", perfil="agresiva"), 30)
        self.assertGreater(
            agresiva.reparto_acciones()["disparo"],
            conservador.reparto_acciones()["disparo"],
        )

    def test_la_etiqueta_describe_el_escenario(self):
        escenario = Escenario(reglamento="v2", jugadores_por_equipo=4, perfil="agresiva")
        self.assertIn("v2", escenario.etiqueta)
        self.assertIn("4v4", escenario.etiqueta)
        self.assertIn("Presionante", escenario.etiqueta)

    def test_el_escenario_va_y_vuelve_desde_json(self):
        escenario = Escenario(reglamento="v1", jugadores_por_equipo=5, perfil="paciente")
        self.assertEqual(Escenario.desde_dict(escenario.a_dict()), escenario)


class SalidaTest(unittest.TestCase):
    def test_el_informe_menciona_las_reglas_y_los_numeros(self):
        texto = formatear_resultado(simular(Escenario(reglamento="v2"), 10))
        for esperado in ("Reglas aplicadas", "Goles por partido", "Cartas jugadas"):
            self.assertIn(esperado, texto)

    def test_la_tabla_tiene_una_fila_por_escenario(self):
        resultados = [simular(Escenario(reglamento=r), 10) for r in ("v1", "v2")]
        texto = formatear_tabla(resultados, "prueba")
        self.assertIn("prueba", texto)
        self.assertEqual(texto.count("\nv1"), 1)
        self.assertEqual(texto.count("\nv2"), 1)

    def test_la_tabla_sin_resultados_no_explota(self):
        self.assertIn("sin resultados", formatear_tabla([], "vacío"))


if __name__ == "__main__":
    unittest.main()
