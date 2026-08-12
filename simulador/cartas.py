"""Cartas del juego y armado del mazo.

Los nombres coinciden con los de las cartas físicas: son la clave que usan los
reglamentos JSON, las estadísticas y la interfaz web.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum


class Carta(str, Enum):
    PASE = "Pase"
    DISPARO = "Disparo al arco"
    GAMBETEAR = "Gambetear"
    LA_DEJO_PASAR = "La dejo pasar"
    ROBO_PELOTA = "Robo pelota"
    CORTA_PASE = "Corta pase"
    TACKLE = "Tackle"
    MARCA_PERSONAL = "Marca personal"
    TRAMPA_OFFSIDE = "Trampa de offside"
    FALTA = "Falta"

    def __str__(self) -> str:  # pragma: no cover - azúcar para logs
        return self.value


#: Cartas que juega el equipo con la pelota.
OFENSIVAS: frozenset[Carta] = frozenset(
    {Carta.PASE, Carta.DISPARO, Carta.GAMBETEAR, Carta.LA_DEJO_PASAR}
)

#: Cartas que juega el equipo sin la pelota.
DEFENSIVAS: frozenset[Carta] = frozenset(
    {
        Carta.ROBO_PELOTA,
        Carta.CORTA_PASE,
        Carta.TACKLE,
        Carta.MARCA_PERSONAL,
        Carta.TRAMPA_OFFSIDE,
    }
)

#: Cartas que corta una acción sin quedarse con la pelota.
INTERCEPCIONES: frozenset[Carta] = frozenset(
    {Carta.ROBO_PELOTA, Carta.CORTA_PASE, Carta.TACKLE}
)

#: Cartas que quedan en juego esperando el próximo pase.
TRAMPAS: frozenset[Carta] = frozenset({Carta.MARCA_PERSONAL, Carta.TRAMPA_OFFSIDE})


def rol(carta: Carta) -> str:
    """Devuelve ``ofensiva``, ``defensiva`` o ``neutral``."""
    if carta in OFENSIVAS:
        return "ofensiva"
    if carta in DEFENSIVAS:
        return "defensiva"
    return "neutral"


def desde_nombre(nombre: str) -> Carta:
    """Convierte el nombre impreso en la carta. Lanza ``ValueError`` si no existe."""
    try:
        return Carta(nombre)
    except ValueError:
        conocidas = ", ".join(c.value for c in Carta)
        raise ValueError(f"Carta desconocida: {nombre!r}. Conocidas: {conocidas}") from None


def construir_mazo(composicion: Mapping[Carta, int]) -> list[Carta]:
    """Expande ``{carta: cantidad}`` a la lista de cartas del mazo."""
    mazo: list[Carta] = []
    for carta, cantidad in composicion.items():
        mazo.extend([carta] * cantidad)
    return mazo
