"""El motor: invariantes de un partido, trampas y reposición."""

import unittest
from collections import Counter

from simulador.cartas import Carta
from simulador.ia import AgenteIA
from simulador.motor import acciones_posibles, crear_partido, jugar_partido, jugar_turno
from simulador.reglamento import Reposicion, cargar

REGLAMENTOS = [entrada["id"] for entrada in __import__(
    "simulador.reglamento", fromlist=["catalogo"]).catalogo()]


class AgenteFijo:
    """Agente de laboratorio: hace siempre lo mismo, sin azar."""

    def __init__(self, accion="pase", reacciona=False, contra=False):
        self._accion = accion
        self._reacciona = reacciona
        self._contra = contra

    def accion(self, estado, posibles):
        return self._accion if self._accion in posibles else posibles[0]

    def receptor(self, estado, candidatos):
        return candidatos[0]

    def reaccion(self, estado, contexto, opciones):
        return opciones[0] if (self._reacciona and opciones) else None

    def contra(self, estado, jugador, contra, ante):
        return self._contra


def cartas_en_juego(estado) -> Counter:
    total = Counter(estado.mazo) + Counter(estado.descarte)
    for jugador in estado.jugadores:
        total += Counter(jugador.mano)
    return total


class PartidoTest(unittest.TestCase):
    def test_la_misma_semilla_da_el_mismo_partido(self):
        primero = jugar_partido("v2", semilla=1234)
        segundo = jugar_partido("v2", semilla=1234)
        self.assertEqual(primero.relato, segundo.relato)
        self.assertEqual(primero.marcador.goles, segundo.marcador.goles)

    def test_semillas_distintas_dan_partidos_distintos(self):
        relatos = {tuple(jugar_partido("v2", semilla=s).relato) for s in range(5)}
        self.assertGreater(len(relatos), 1)

    def test_sin_semilla_igual_queda_registrada_para_repetir(self):
        estado = jugar_partido("v1")
        self.assertIsNotNone(estado.semilla)
        repetido = jugar_partido("v1", semilla=estado.semilla)
        self.assertEqual(estado.relato, repetido.relato)

    def test_todos_los_reglamentos_terminan_y_respetan_el_marcador(self):
        for id_reglamento in REGLAMENTOS:
            reg = cargar(id_reglamento)
            for semilla in (0, 1, 2):
                with self.subTest(reglamento=id_reglamento, semilla=semilla):
                    estado = jugar_partido(reg, semilla=semilla)
                    self.assertTrue(estado.terminado)
                    self.assertLessEqual(estado.turno, reg.limite_turnos)
                    self.assertLessEqual(max(estado.marcador.goles), reg.goles_para_ganar)

    def test_no_se_pierden_ni_se_inventan_cartas(self):
        reg = cargar("v1")
        estado = crear_partido(reg, semilla=3)
        esperado = Counter(reg.cartas_del_mazo())
        self.assertEqual(cartas_en_juego(estado), esperado)
        jugar_partido(estado=estado)
        self.assertEqual(cartas_en_juego(estado), esperado)

    def test_nadie_supera_el_maximo_de_mano(self):
        reg = cargar("v1")
        estado = jugar_partido(reg, semilla=8)
        for jugador in estado.jugadores:
            self.assertLessEqual(len(jugador.mano), reg.mano_maxima)

    def test_los_nombres_propios_llegan_al_relato(self):
        estado = jugar_partido("v1", semilla=2, nombres=["A", "B", "C", "D", "E", "F"])
        self.assertIn("A", " ".join(estado.relato))

    def test_el_formato_tiene_que_respetar_el_minimo_del_reglamento(self):
        with self.assertRaises(ValueError):
            crear_partido("v1", jugadores_por_equipo=1)


class AccionesTest(unittest.TestCase):
    def test_sin_pase_en_la_mano_no_se_ofrece_pasar(self):
        estado = crear_partido("v2", semilla=5)
        estado.portador.mano = [Carta.GAMBETEAR]
        self.assertNotIn("pase", acciones_posibles(estado))
        self.assertIn("reventar", acciones_posibles(estado))

    def test_v2_no_ofrece_pasar_de_turno(self):
        estado = crear_partido("v2", semilla=5)
        self.assertNotIn("pasa_turno", acciones_posibles(estado))

    def test_v1_si_lo_ofrece(self):
        estado = crear_partido("v1", semilla=5)
        self.assertIn("pasa_turno", acciones_posibles(estado))

    def test_el_pase_encadenado_sube_el_contador_y_el_cambio_de_equipo_lo_baja(self):
        estado = crear_partido("v2", semilla=5)
        estado.portador.mano = [Carta.PASE, Carta.PASE]
        jugar_turno(estado, AgenteFijo("pase"))
        self.assertEqual(estado.pases, 1)
        estado.portador.mano = [Carta.PASE]
        jugar_turno(estado, AgenteFijo("pase", reacciona=True))  # la defensa roba
        self.assertEqual(estado.pases, 0)


class TrampasTest(unittest.TestCase):
    """La marca y el offside son el punto más delicado del reglamento."""

    def preparar(self, id_reglamento="v2", jugadores=2):
        # Sin faltas de por medio, el turno resuelve el pase sí o sí.
        reg = cargar(id_reglamento).con_cambios(prob_falta_por_jugador=0.0)
        estado = crear_partido(reg, jugadores_por_equipo=jugadores, semilla=11)
        estado.portador.mano = [Carta.PASE]
        return estado

    def test_una_marca_sobre_el_receptor_le_da_la_pelota_a_la_defensa(self):
        estado = self.preparar()
        defensa = estado.equipo_sin_pelota
        companero = estado.companeros(estado.portador)[0]
        estado.marca[defensa] = companero.id

        jugar_turno(estado, AgenteFijo("pase"))

        self.assertEqual(estado.equipo_con_pelota, defensa)
        self.assertEqual(estado.acciones["marca_efectiva"], 1)
        self.assertIsNone(estado.marca[defensa])

    def test_la_marca_sigue_puesta_despues_de_un_pase_a_otro_jugador(self):
        """Regresión: la marca se borraba sola al completarse el pase."""
        estado = self.preparar(jugadores=3)
        defensa = estado.equipo_sin_pelota
        companeros = estado.companeros(estado.portador)
        estado.marca[defensa] = companeros[1].id

        jugar_turno(estado, AgenteFijo("pase"))  # el pase va al primer compañero

        self.assertEqual(estado.equipo_con_pelota, 1 - defensa)
        self.assertEqual(estado.marca[defensa], companeros[1].id)
        self.assertEqual(estado.acciones["marca_evitada"], 1)

    def test_la_trampa_de_offside_se_cobra_en_el_pase_siguiente(self):
        estado = self.preparar()
        defensa = estado.equipo_sin_pelota
        estado.offside[defensa] = True

        jugar_turno(estado, AgenteFijo("pase"))

        self.assertEqual(estado.equipo_con_pelota, defensa)
        self.assertEqual(estado.acciones["offside_efectivo"], 1)

    def test_las_trampas_se_limpian_cuando_cambia_el_equipo(self):
        estado = self.preparar()
        defensa = estado.equipo_sin_pelota
        estado.offside[defensa] = True
        estado.marca[defensa] = estado.companeros(estado.portador)[0].id

        jugar_turno(estado, AgenteFijo("pase"))  # el offside devuelve la pelota

        self.assertFalse(any(estado.offside.values()))
        self.assertTrue(all(v is None for v in estado.marca.values()))

    def test_en_v0_la_dejo_pasar_anula_la_marca(self):
        estado = self.preparar("v0")
        defensa = estado.equipo_sin_pelota
        companero = estado.companeros(estado.portador)[0]
        estado.marca[defensa] = companero.id
        companero.mano = [Carta.LA_DEJO_PASAR]

        jugar_turno(estado, AgenteFijo("pase", contra=True))

        self.assertEqual(estado.equipo_con_pelota, 1 - defensa)
        self.assertEqual(estado.acciones["marca_efectiva"], 0)


class ReposicionTest(unittest.TestCase):
    def test_con_reposicion_al_jugar_carta_la_mano_se_mantiene_llena(self):
        reg = cargar("v1").con_cambios(
            reposicion=Reposicion(momento="al_jugar_carta", quien="el_jugador")
        )
        estado = jugar_partido(reg, semilla=4)
        manos = [len(j.mano) for j in estado.jugadores]
        self.assertTrue(all(m == reg.mano_maxima for m in manos), manos)

    def test_sin_reposicion_las_manos_se_van_vaciando(self):
        reg = cargar("v1").con_cambios(reposicion=Reposicion(momento="nunca", quien="todos"))
        estado = jugar_partido(reg, semilla=4)
        self.assertLess(sum(len(j.mano) for j in estado.jugadores), reg.mano_inicial * 6)
        self.assertTrue(estado.terminado)

    def test_la_mano_vacia_se_repone_como_en_v0(self):
        reg = cargar("v0")
        estado = jugar_partido(reg, semilla=4)
        self.assertTrue(all(j.mano for j in estado.jugadores))

    def test_se_puede_repartir_una_mano_mas_grande(self):
        reg = cargar("v1").con_cambios(mano_inicial=10, mano_maxima=10)
        estado = crear_partido(reg, semilla=1)
        self.assertTrue(all(len(j.mano) == 10 for j in estado.jugadores))


class PerfilesTest(unittest.TestCase):
    def test_cada_perfil_juega_un_partido_completo(self):
        from simulador.ia import IDS

        for id_perfil in IDS:
            with self.subTest(perfil=id_perfil):
                estado = crear_partido("v2", semilla=6)
                jugar_partido(estado=estado, agente=AgenteIA(id_perfil, rng=estado.rng))
                self.assertTrue(estado.terminado)

    def test_dos_perfiles_distintos_por_equipo(self):
        estado = crear_partido("v2", semilla=6)
        agente = AgenteIA("estrategica", equipo0="agresiva", equipo1="conservador", rng=estado.rng)
        self.assertIn("vs", agente.describir())
        jugar_partido(estado=estado, agente=agente)
        self.assertTrue(estado.terminado)


if __name__ == "__main__":
    unittest.main()
