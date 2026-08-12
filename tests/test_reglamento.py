"""Carga, herencia, validación y guardado de reglamentos."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from simulador import reglamento as R


class CargaTest(unittest.TestCase):
    def test_todos_los_reglamentos_del_repo_cargan(self):
        entradas = R.catalogo()
        self.assertGreaterEqual(len(entradas), 2)
        for entrada in entradas:
            reg = R.cargar(entrada["id"])
            self.assertEqual(reg.id, entrada["id"])
            self.assertEqual(R.validar(reg), [])

    def test_hay_al_menos_un_reglamento_activo(self):
        self.assertTrue(R.catalogo(solo_activos=True))

    def test_la_herencia_completa_lo_que_no_se_repite(self):
        v1, v2 = R.cargar("v1"), R.cargar("v2")
        self.assertEqual(v2.mazo, v1.mazo)  # heredado
        self.assertNotIn("pasa_turno", v2.acciones_ofensivas)  # sobrescrito
        self.assertTrue(v2.reacciones_encadenables)
        self.assertFalse(v1.reacciones_encadenables)

    def test_el_reglamento_pedido_por_ruta_tambien_carga(self):
        reg = R.cargar(str(R.DIRECTORIO / "v1.json"))
        self.assertEqual(reg.id, "v1")

    def test_reglamento_inexistente_avisa_cuales_hay(self):
        with self.assertRaises(FileNotFoundError) as caso:
            R.cargar("no-existe")
        self.assertIn("Disponibles", str(caso.exception))

    def test_no_se_puede_salir_del_directorio(self):
        for id_malicioso in ("../secreto", "/etc/passwd", "a/b"):
            with self.assertRaises(ValueError):
                R.ruta_de(id_malicioso)


class ValidacionTest(unittest.TestCase):
    def base(self, **cambios):
        datos = R.cargar("v1").a_dict()
        datos.update(cambios)
        return datos

    def test_clave_desconocida_se_reporta(self):
        with self.assertRaises(R.ReglamentoInvalido) as caso:
            R.desde_dict(self.base(reventar_habilitado=True))
        self.assertIn("reventar_habilitado", " ".join(caso.exception.errores))

    def test_carta_desconocida_se_reporta(self):
        with self.assertRaises(ValueError) as caso:
            R.desde_dict(self.base(mazo={"Chilena": 4}))
        self.assertIn("Chilena", str(caso.exception))

    def test_el_ataque_siempre_tiene_una_salida_sin_carta(self):
        errores = R.validar(R.cargar("v1").con_cambios(acciones_ofensivas=("pase", "disparo")))
        self.assertTrue(any("sin jugada" in e for e in errores))

    def test_la_defensa_no_puede_usar_cartas_que_no_estan_en_el_mazo(self):
        reg = R.cargar("v1")
        sin_robo = {c: n for c, n in reg.mazo.items() if c.value != "Robo pelota"}
        errores = R.validar(reg.con_cambios(mazo=sin_robo))
        self.assertTrue(any("Robo pelota" in e for e in errores))

    def test_tabla_de_disparo_fuera_del_dado(self):
        reg = R.cargar("v1")
        tabla = R.TablaDisparo((R.FranjaDisparo(pases=0, gol=(1, 9), ataja=(2, 6)),))
        errores = R.validar(reg.con_cambios(tabla_disparo=tabla))
        self.assertTrue(any("entre 1 y 6" in e for e in errores))

    def test_el_mazo_tiene_que_alcanzar_para_repartir(self):
        reg = R.cargar("v1")
        errores = R.validar(reg.con_cambios(mazo={R.Carta.PASE: 4}))
        self.assertTrue(any("no alcanza" in e for e in errores))

    def test_penales_despues_de_la_victoria_no_tiene_sentido(self):
        errores = R.validar(R.cargar("v1").con_cambios(penales_si_marcador=(3, 3)))
        self.assertTrue(any("penales_si_marcador" in e for e in errores))

    def test_mano_maxima_menor_que_la_inicial(self):
        errores = R.validar(R.cargar("v1").con_cambios(mano_inicial=6, mano_maxima=4))
        self.assertTrue(any("máximo de mano" in e for e in errores))


class GuardadoTest(unittest.TestCase):
    def setUp(self):
        self.directorio = Path(tempfile.mkdtemp())
        for nombre in ("v1.json", "v2.json"):
            shutil.copy(R.DIRECTORIO / nombre, self.directorio / nombre)

    def tearDown(self):
        shutil.rmtree(self.directorio)

    def test_ida_y_vuelta_conserva_las_reglas(self):
        original = R.cargar("v1", directorio=self.directorio)
        copia = original.con_cambios(id="prueba", mano_maxima=8)
        R.guardar(copia, directorio=self.directorio)
        leido = R.cargar("prueba", directorio=self.directorio)
        self.assertEqual(leido.a_dict(), copia.a_dict())

    def test_guardar_heredando_escribe_solo_las_diferencias(self):
        base = R.cargar("v1", directorio=self.directorio)
        hijo = base.con_cambios(id="v1.9", mano_inicial=4)
        R.guardar(hijo, extends="v1", directorio=self.directorio)

        crudo = json.loads((self.directorio / "v1.9.json").read_text(encoding="utf-8"))
        self.assertEqual(crudo["extends"], "v1")
        self.assertNotIn("mazo", crudo)  # el mazo no cambió: se hereda
        self.assertEqual(crudo["mano"], {"inicial": 4})  # 'maxima' no cambió: se hereda

        leido = R.cargar("v1.9", directorio=self.directorio)
        self.assertEqual(leido.mazo, base.mazo)
        self.assertEqual(leido.mano_inicial, 4)
        self.assertEqual(leido.mano_maxima, base.mano_maxima)

    def test_sacar_una_carta_del_mazo_sobrevive_a_la_herencia(self):
        base = R.cargar("v1", directorio=self.directorio)
        sin_falta = {c: n for c, n in base.mazo.items() if c is not R.Carta.FALTA}
        R.guardar(base.con_cambios(id="sin-falta", mazo=sin_falta), extends="v1",
                  directorio=self.directorio)
        leido = R.cargar("sin-falta", directorio=self.directorio)
        self.assertNotIn(R.Carta.FALTA, leido.mazo)

    def test_no_se_guarda_un_reglamento_invalido(self):
        roto = R.cargar("v1", directorio=self.directorio).con_cambios(id="roto", mazo={})
        with self.assertRaises(R.ReglamentoInvalido):
            R.guardar(roto, directorio=self.directorio)
        self.assertFalse((self.directorio / "roto.json").exists())

    def test_herencia_circular(self):
        (self.directorio / "a.json").write_text(
            json.dumps({"id": "a", "extends": "b"}), encoding="utf-8"
        )
        (self.directorio / "b.json").write_text(
            json.dumps({"id": "b", "extends": "a"}), encoding="utf-8"
        )
        with self.assertRaises(R.ReglamentoInvalido):
            R.cargar("a", directorio=self.directorio)


if __name__ == "__main__":
    unittest.main()
