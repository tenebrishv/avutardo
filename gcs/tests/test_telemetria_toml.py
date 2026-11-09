"""El formato de telemetría está bien formado.

Es la única fuente del formato: si tiene un nombre repetido, un tipo
desconocido o una unidad que no es SI, todo lo que lo lee falla después.
"""

import re
import tomllib
from pathlib import Path

import pytest

TOML = Path(__file__).resolve().parents[2] / "protocolo" / "telemetria.toml"

# Bytes que ocupa cada tipo en el paquete (big-endian, campo por campo).
TAMANIO = {"uint8": 1, "int16": 2, "uint16": 2, "int32": 4, "uint32": 4}
TIPOS = set(TAMANIO)

# Partes fijas del paquete, fuera de los campos.
CABECERA_CCSDS = 6  # cabecera primaria CCSDS 133.0-B-2, sin secundaria
VERSION_FORMATO = 1
CRC = 2  # CRC-16/CCITT-FALSE
LARGO_PAQUETE = 61  # acordado en la #10
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


def test_el_paquete_mide_61_bytes(campos):
    largo = CABECERA_CCSDS + VERSION_FORMATO + sum(TAMANIO[c["tipo"]] for c in campos) + CRC
    assert largo == LARGO_PAQUETE


# La tabla acordada en la #10, copiada a mano: (nombre, tipo, divisor).
# Cambiar el formato obliga a cambiar esta tabla (y a subir la versión).
FORMATO_V1 = [
    ("estado_fsw", "uint8", 1),
    ("hora", "uint32", 1),
    ("tiempo_mision", "uint16", 1),
    ("altitud", "int16", 10),
    ("presion", "uint32", 1),
    ("temperatura", "int16", 100),
    ("tension", "uint16", 1000),
    ("corriente", "int16", 1000),
    ("panel", "uint16", 1000),
    ("acel_x", "int16", 100),
    ("acel_y", "int16", 100),
    ("acel_z", "int16", 100),
    ("rot_x", "int16", 10),
    ("rot_y", "int16", 10),
    ("rot_z", "int16", 10),
    ("gps_hora", "uint32", 1),
    ("gps_latitud", "int32", 10_000_000),
    ("gps_longitud", "int32", 10_000_000),
    ("gps_altitud", "int32", 10),
    ("gps_satelites", "uint8", 1),
    ("eco_comando", "uint16", 1),
]


def test_campos_en_el_orden_y_con_el_tipo_acordados(campos):
    leidos = [(c["nombre"], c["tipo"], c.get("divisor", 1)) for c in campos]
    assert leidos == FORMATO_V1


OBLIGATORIAS = {"nombre", "tipo", "unidad", "requisito", "descripcion"}
OPCIONALES = {"divisor", "valores", "mostrar", "reservado"}
# Un código del Anexo A v2: letras y número (G3, X5, SN1); varios, separados por espacio.
REQUISITO = re.compile(r"[A-Z]+[0-9]+( [A-Z]+[0-9]+)*")


def test_sin_claves_desconocidas(campos):
    for c in campos:
        sobran = c.keys() - OBLIGATORIAS - OPCIONALES
        assert not sobran, f"{c['nombre']}: claves desconocidas {sobran}"


def test_divisor_entero_positivo(campos):
    for c in campos:
        divisor = c.get("divisor", 1)
        assert type(divisor) is int and divisor >= 1, f"{c['nombre']}: divisor {divisor!r}"


def test_requisito_es_un_codigo_del_anexo(campos):
    for c in campos:
        assert REQUISITO.fullmatch(c["requisito"]), f"{c['nombre']}: {c['requisito']!r}"


def test_valores_solo_en_uint8_sin_pisar_el_centinela(campos):
    for c in campos:
        if "valores" in c:
            assert c["tipo"] == "uint8", c["nombre"]
            # 255 es "sin dato": no puede ser el código de un valor.
            assert 0 < len(c["valores"]) < 255, c["nombre"]
            assert all(isinstance(v, str) and v for v in c["valores"]), c["nombre"]


def test_mostrar_hora_utc_solo_en_uint32_en_segundos(campos):
    for c in campos:
        if "mostrar" in c:
            assert c["mostrar"] == "hora_utc", c["nombre"]
            assert c["tipo"] == "uint32" and c["unidad"] == "s", c["nombre"]


def test_reservado_es_booleano(campos):
    for c in campos:
        if "reservado" in c:
            assert c["reservado"] is True, c["nombre"]


def test_claves_opcionales_acordadas(campos):
    por_nombre = {c["nombre"]: c for c in campos}
    assert por_nombre["estado_fsw"]["valores"] == [
        "BOOT",
        "STANDBY",
        "ASCENT",
        "DESCENT 1",
        "DESCENT 2",
        "LANDED",
    ]
    assert por_nombre["hora"]["mostrar"] == "hora_utc"
    assert por_nombre["gps_hora"]["mostrar"] == "hora_utc"
    assert por_nombre["eco_comando"]["reservado"] is True


def test_version_del_formato_es_1(formato):
    assert type(formato["version"]) is int
    assert formato["version"] == 1


def test_ya_no_es_provisorio(formato):
    assert "provisorio" not in formato
    assert "paquete" not in formato  # la sección del formato ASCII viejo


def test_enlace(formato):
    assert formato["enlace"] == {
        "codificacion": "binario",
        "crc": "CRC-16/CCITT-FALSE",
        "linea_puente": "<hex>,<rssi>,<snr>\n",
    }


def test_apid_106_en_11_bits(formato):
    apid = formato["cabecera"]["apid"]
    assert apid == 106
    assert 0 <= apid < 0x7FF  # 0x7FF es el APID de relleno (idle) de CCSDS


# "Sin dato": el mínimo del tipo si es con signo, el máximo si es sin signo.
# Escrito a mano; el decodificador tiene que dar lo mismo.
CENTINELA = {
    "uint8": 255,
    "int16": -32_768,
    "uint16": 65_535,
    "int32": -2_147_483_648,
    "uint32": 4_294_967_295,
}


def test_cada_tipo_tiene_centinela(campos):
    assert CENTINELA.keys() == TAMANIO.keys()
    for c in campos:
        assert c["tipo"] in CENTINELA, c["nombre"]


def test_el_centinela_es_el_extremo_del_tipo():
    for tipo, centinela in CENTINELA.items():
        bits = 8 * TAMANIO[tipo]
        if tipo.startswith("u"):
            assert centinela == 2**bits - 1, tipo
        else:
            assert centinela == -(2 ** (bits - 1)), tipo
