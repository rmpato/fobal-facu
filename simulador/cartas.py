"""Tipos de carta y configuración de mazos (español argentino)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Carta(str, Enum):
    PASE = "Pase"
    CORTA_PASE = "Corta pase"
    ROBO_PELOTA = "Robo pelota"
    TACKLE = "Tackle"
    DISPARO = "Disparo al arco"
    FALTA = "Falta"
    GAMBETEAR = "Gambetear"
    LA_DEJO_PASAR = "La dejo pasar"
    MARCA_PERSONAL = "Marca personal"
    TRAMPA_OFFSIDE = "Trampa de offside"


MAZO_V0: dict[Carta, int] = {
    Carta.PASE: 42,
    Carta.CORTA_PASE: 12,
    Carta.TACKLE: 12,
    Carta.DISPARO: 12,
    Carta.FALTA: 7,
    Carta.GAMBETEAR: 8,
    Carta.LA_DEJO_PASAR: 7,
    Carta.MARCA_PERSONAL: 5,
    Carta.TRAMPA_OFFSIDE: 3,
}

MAZO_V1: dict[Carta, int] = {
    Carta.PASE: 42,
    Carta.ROBO_PELOTA: 24,
    Carta.DISPARO: 12,
    Carta.FALTA: 7,
    Carta.GAMBETEAR: 15,
    Carta.MARCA_PERSONAL: 5,
    Carta.TRAMPA_OFFSIDE: 3,
}


@dataclass(frozen=True)
class TablaDisparo:
    """Rangos de gol/atajada según pases en la jugada."""

    pases: int
    gol_min: int
    gol_max: int
    ataja_min: int
    ataja_max: int


TABLAS_DISPARO: list[TablaDisparo] = [
    TablaDisparo(0, 1, 1, 2, 6),
    TablaDisparo(1, 1, 2, 3, 6),
    TablaDisparo(2, 1, 3, 4, 6),
    TablaDisparo(3, 1, 4, 5, 6),
    TablaDisparo(4, 1, 5, 6, 6),
]


def tabla_para_pases(pases: int) -> TablaDisparo:
    if pases >= 4:
        return TABLAS_DISPARO[4]
    return TABLAS_DISPARO[pases]


def construir_mazo(config: dict[Carta, int]) -> list[Carta]:
    mazo: list[Carta] = []
    for carta, cantidad in config.items():
        mazo.extend([carta] * cantidad)
    return mazo
