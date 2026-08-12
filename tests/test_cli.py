"""La línea de comandos: que cada subcomando corra y diga algo útil."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from simulador.cli import main


def correr(*argumentos):
    salida = io.StringIO()
    with redirect_stdout(salida):
        codigo = main(list(argumentos))
    return codigo, salida.getvalue()


class CliTest(unittest.TestCase):
    def test_lista_de_reglamentos(self):
        codigo, texto = correr("reglamentos")
        self.assertEqual(codigo, 0)
        self.assertIn("v1", texto)
        self.assertIn("v2", texto)

    def test_detalle_de_un_reglamento(self):
        codigo, texto = correr("reglamentos", "v2")
        self.assertEqual(codigo, 0)
        self.assertIn("Mazo", texto)
        self.assertIn("Reglas que aplica", texto)

    def test_lista_de_perfiles(self):
        _, texto = correr("perfiles")
        self.assertIn("estrategica", texto)
        self.assertIn("Táctico", texto)

    def test_simular(self):
        codigo, texto = correr("simular", "v1", "--partidos", "5")
        self.assertEqual(codigo, 0)
        self.assertIn("Goles por partido", texto)

    def test_comparar_dos_reglamentos_en_dos_formatos(self):
        codigo, texto = correr(
            "comparar", "v1", "v2", "--partidos", "5", "--formatos", "3", "4"
        )
        self.assertEqual(codigo, 0)
        self.assertEqual(texto.count("\nv1"), 2)
        self.assertEqual(texto.count("\nv2"), 2)

    def test_ver_un_partido_sin_pausa(self):
        codigo, texto = correr("ver", "v2", "--semilla", "3", "--pausa", "0")
        self.assertEqual(codigo, 0)
        self.assertIn("Para repetir este partido: --semilla 3", texto)

    def test_un_reglamento_que_no_existe_da_un_error_claro(self):
        error = io.StringIO()
        with self.assertRaises(SystemExit) as caso, redirect_stderr(error):
            correr("simular", "no-existe")
        self.assertEqual(caso.exception.code, 2)
        self.assertIn("Disponibles", error.getvalue())

    def test_un_perfil_que_no_existe_lo_ataja_el_parser(self):
        error = io.StringIO()
        with self.assertRaises(SystemExit), redirect_stderr(error):
            correr("simular", "v1", "--perfil", "inventado")
        self.assertIn("invalid choice", error.getvalue())


if __name__ == "__main__":
    unittest.main()
