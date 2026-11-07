"""El formato de telemetría está bien formado.

Es la única fuente del formato: si tiene un nombre repetido, un tipo
desconocido o una unidad que no es SI, todo lo que lo lee falla después.
"""

import tomllib
from pathlib import Path

import pytest

TOML = Path(__file__).resolve().parents[2] / "protocolo" / "telemetria.toml"

TIPOS = {"int", "float", "str"}
# Unidades SI y las aceptadas para uso con el SI (°, °C). Vacía = sin unidad.
UNIDADES = {"", "s", "m", "Pa", "°C", "V", "A", "W", "m/s", "m/s²", "°", "°/s", "dB", "dBm"}


@pytest.fixture(scope="module")
def formato() -> dict:
    with TOML.open("rb") as f:
        return tomllib.load(f)


@pytest.fixture(scope="module")
def campos(formato: dict) -> list[dict]:
    return formato["campo"]


def test_tiene_campos(campos):
    assert len(campos) > 0


def test_nombres_unicos(campos):
    nombres = [c["nombre"] for c in campos]
    repetidos = {n for n in nombres if nombres.count(n) > 1}
    assert not repetidos, f"nombres repetidos: {repetidos}"


def test_nombres_son_identificadores(campos):
    for c in campos:
        assert c["nombre"].isidentifier(), c["nombre"]


def test_cada_campo_tiene_lo_obligatorio(campos):
    for c in campos:
        faltan = {"nombre", "tipo", "unidad", "requisito", "descripcion"} - c.keys()
        assert not faltan, f"{c.get('nombre')}: faltan {faltan}"


def test_tipos_conocidos(campos):
    for c in campos:
        assert c["tipo"] in TIPOS, f"{c['nombre']}: tipo {c['tipo']!r}"


def test_unidades_si(campos):
    for c in campos:
        assert c["unidad"] in UNIDADES, f"{c['nombre']}: unidad {c['unidad']!r}"


def test_contador_es_el_primer_campo(campos):
    # El conteo de perdidos (F1) se apoya en el contador.
    assert campos[0]["nombre"] == "contador"
    assert campos[0]["tipo"] == "int"


def test_paquete_definido(formato):
    paquete = formato["paquete"]
    assert paquete["separador"]
    assert paquete["fin_de_linea"]
